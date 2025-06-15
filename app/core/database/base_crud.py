import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


import uuid
from typing import (
    Generic,
    TypeVar,
    Dict,
    Any,
    Union,
    List,
    cast
)

from pydantic import BaseModel

from sqlalchemy import (
    select,
)
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    selectinload,
    joinedload,
    class_mapper,
    RelationshipProperty,
    MapperProperty
)
from sqlalchemy.orm.relationships import RelationshipProperty as SQLAlchemyRelationshipProperty


from core.database.model import Base


# Определяем Enum для типов свойств, чтобы упростить логику
class PropertyType:
    COLUMN = 1
    RELATIONSHIP_SCALAR = 2
    RELATIONSHIP_COLLECTION = 3
    UNKNOWN = 4

# Ограничиваем T так, чтобы это был подкласс Base, что позволит MyPy лучше работать
T = TypeVar("T", bound=Base)

# Определяем Union для ID, так как UUID может приходить как str
UUID_OR_STR = Union[uuid.UUID, str]


class BaseCrud(Generic[T]):
    model: type[T]  # Устанавливается в наследниках (например, UserCrud.model = User)

    @classmethod
    def _get_relationship_load_options(cls) -> List[Any]:
        """
        Генерирует опции для "жадной" загрузки (eager loading) связанных объектов.
        Автоматически использует selectinload для 'selectin' и joinedload для 'joined' стратегий,
        определенных в моделях SQLAlchemy.
        """
        load_options = []
        mapper = class_mapper(cls.model)
        for rel in mapper.relationships:
            if rel.lazy == "selectin":
                load_options.append(selectinload(getattr(cls.model, rel.key)))
            elif rel.lazy == "joined":
                load_options.append(joinedload(getattr(cls.model, rel.key)))
        return load_options

    # --- Функции для _apply_filters_from_pydantic ---
    @classmethod
    def _split_filters(cls, filters: BaseModel | None) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Разделяет фильтры из Pydantic-модели на:
        1. Прямые фильтры для основной модели (например, 'username').
        2. Фильтры для связанных моделей (например, 'profile_bio').
        Использует соглашение: фильтры для связей содержат символ '_'.
        """
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        model_filters: Dict[str, Any] = {}
        relation_filters: Dict[str, Dict[str, Any]] = {}

        for key, value in filter_dict.items():
            if '_' in key:
                rel_name, rel_field = key.split('_', 1)
                relation_filters.setdefault(rel_name, {})[rel_field] = value
            else:
                model_filters[key] = value
        return model_filters, relation_filters

    @classmethod
    def _apply_direct_filters(cls, stmt: Select, model_filters: Dict[str, Any]) -> Select:
        """Применяет прямые фильтры для основной модели к SQL-запросу."""
        if model_filters:
            stmt = stmt.filter_by(**model_filters)
        return stmt

    @classmethod
    def _apply_relationship_filter(cls, stmt: Select, mapper, rel_name: str, rel_fields: Dict[str, Any]) -> Select:
        """
        Применяет фильтры для одного отношения к SQL-запросу.
        Различает скалярные отношения (has()) и коллекции (any()).
        """
        rel_attr = getattr(cls.model, rel_name, None)
        if rel_attr is None:
            # Если атрибута отношения нет, выводим предупреждение и возвращаем исходный запрос
            print(f"Warning: Relationship '{rel_name}' not found on model {cls.model.__name__} for filtering.")
            return stmt

        rel_prop = mapper.relationships.get(rel_name)
        if rel_prop is None:
            # Если это не ORM-отношение (возможно, поле с '_' в названии), выводим предупреждение
            print(f"Warning: '{rel_name}' is not an ORM relationship on {cls.model.__name__}.")
            return stmt

        if rel_prop.uselist:  # Это коллекция (One-to-Many или Many-to-Many)
            # Используем .any() для поиска хотя бы одного связанного объекта, соответствующего условиям
            for field, value in rel_fields.items():
                related_model_class = rel_prop.mapper.class_
                if hasattr(related_model_class, field):
                    stmt = stmt.where(rel_attr.any(getattr(related_model_class, field) == value))
                else:
                    print(f"Warning: Field '{field}' not found on related model {related_model_class.__name__} for filtering '{rel_name}'.")
        else:  # Это скалярное отношение (One-to-One или Many-to-One)
            # Используем .has() для проверки характеристик единственного связанного объекта
            stmt = stmt.where(rel_attr.has(**rel_fields))
        return stmt

    @classmethod
    def _apply_filters_from_pydantic(
        cls,
        base_stmt: Select,
        filters: BaseModel | None
    ) -> Select:
        """
        Основной метод применения фильтров из Pydantic-модели к SQL-запросу.
        Оркестрирует вызовы вспомогательных функций.
        """
        model_filters, relation_filters = cls._split_filters(filters)
        stmt = cls._apply_direct_filters(base_stmt, model_filters)

        mapper = class_mapper(cls.model)
        for rel_name, rel_fields in relation_filters.items():
            stmt = cls._apply_relationship_filter(stmt, mapper, rel_name, rel_fields)

        return stmt

    # --- Функции для _update_model_from_dict ---
    @classmethod
    def _classify_property(cls, mapper: Any, key: str) -> tuple[int, Union[MapperProperty, None]]:
        """
        Классифицирует тип свойства по данному ключу:
        - COLUMN (обычный столбец)
        - RELATIONSHIP_SCALAR (скалярное отношение: One-to-One, Many-to-One)
        - RELATIONSHIP_COLLECTION (отношение-коллекция: One-to-Many, Many-to-Many)
        - UNKNOWN (неизвестный/несуществующий атрибут)
        Возвращает кортеж (PropertyType, MapperProperty | None).
        """
        # Попытка найти как столбец
        prop = mapper.get_property(key)
        
        logger.debug(f"Classifying property for key: '{key}' on model: '{mapper.class_.__name__}'")
        logger.debug(f"  Raw prop from mapper.get_property: {prop} (type: {type(prop)})")

        if prop is None:
            logger.debug(f"  Key '{key}' not found as ORM property.")
            return PropertyType.UNKNOWN, None

        if isinstance(prop, SQLAlchemyRelationshipProperty): # Используем импортированный SQLAlchemyRelationshipProperty
            if prop.uselist:
                logger.debug("  Classified as RELATIONSHIP_COLLECTION (uselist=True).")
                return PropertyType.RELATIONSHIP_COLLECTION, prop
            else:
                logger.debug("  Classified as RELATIONSHIP_SCALAR (uselist=False).")
                return PropertyType.RELATIONSHIP_SCALAR, prop
        else:
            logger.debug("  Classified as COLUMN (not a RelationshipProperty).")
            return PropertyType.COLUMN, prop

    @classmethod
    async def _handle_scalar_relationship_update(
        cls,
        instance: T,
        key: str,
        value: Any,
        prop: SQLAlchemyRelationshipProperty,
        session: AsyncSession
    ):
        """
        Обрабатывает обновление скалярного отношения (One-to-One, Many-to-One).
        """
        related_cls = prop.mapper.class_

        if value is None:
            setattr(instance, key, None)
        elif isinstance(value, dict):
            rel_obj = getattr(instance, key, None)
            if rel_obj:
                await cls._update_model_from_dict(rel_obj, value, session)
            else:
                new_obj = related_cls(**value)
                setattr(instance, key, new_obj)
        elif isinstance(value, (uuid.UUID, str)):
            related_id = uuid.UUID(value) if isinstance(value, str) else value
            related_instance = await session.get(related_cls, related_id)
            if related_instance:
                setattr(instance, key, related_instance)
            else:
                raise ValueError(f"Related object {related_cls.__name__} with ID {related_id} not found for relationship '{key}'.")
        else:
            raise ValueError(f"Unsupported value type for scalar relationship '{key}': {type(value)}. Expected dict, UUID, str (UUID), or None.")


    @classmethod
    async def _update_model_from_dict(cls, instance: T, values_dict: dict, session: AsyncSession):
        """
        Основной метод для рекурсивного обновления ORM-экземпляра из словаря.
        Использует _classify_property для определения типа атрибута.
        """
        mapper = class_mapper(type(instance))

        for key, value in values_dict.items():
            if not hasattr(instance, key):
                logger.debug(f"Skipping key '{key}' as it's not an attribute of model {type(instance).__name__}.")
                continue

            prop_type, prop = cls._classify_property(mapper, key)

            logger.debug(f"Handling update for key: '{key}', value: '{value}' (type: {type(value)}), classified as: {prop_type}")

            if prop_type == PropertyType.COLUMN:
                logger.debug(f"  Setting column '{key}' directly.")
                setattr(instance, key, value) # <-- Здесь происходит ошибка
            elif prop_type == PropertyType.RELATIONSHIP_SCALAR:
                logger.debug(f"  Handling scalar relationship '{key}'.")
                await cls._handle_scalar_relationship_update(
                    instance, key, value, cast(SQLAlchemyRelationshipProperty, prop), session
                )
            elif prop_type == PropertyType.RELATIONSHIP_COLLECTION:
                logger.debug(f"  Skipping collection relationship '{key}'.")
                print(f"Warning: Collection relationship '{key}' update skipped by generic BaseCrud._update_model_from_dict. Handle this in specific CRUD methods.")

    # --- CRUD-МЕТОДЫ ---
    @classmethod
    async def find_one_or_none_by_id(cls, session: AsyncSession, data_id: uuid.UUID) -> Union[T, None]:
        """Находит одну запись по её первичному ключу (ID) с "жадной" загрузкой."""
        try:
            stmt = select(cls.model).where(getattr(cls.model, "id") == data_id)

            for opt in cls._get_relationship_load_options():
                stmt = stmt.options(opt)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            print(f"Error occurred during find_one_or_none_by_id: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel) -> Union[T, None]:
        """Находит одну запись на основе Pydantic-фильтров с "жадной" загрузкой."""
        try:
            stmt = cls._apply_filters_from_pydantic(select(cls.model), filters)

            for opt in cls._get_relationship_load_options():
                stmt = stmt.options(opt)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            print(f"Error occurred during find_one_or_none: {e}")
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None = None) -> List[T]:
        """Находит все записи, соответствующие Pydantic-фильтрам, с "жадной" загрузкой."""
        try:
            stmt = cls._apply_filters_from_pydantic(select(cls.model), filters)

            for opt in cls._get_relationship_load_options():
                stmt = stmt.options(opt)

            result = await session.execute(stmt)
            return result.scalars(cls.model).all() #pyright:ignore

        except SQLAlchemyError as e:
            print(f"Error occurred during find_all: {e}")
            raise

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel) -> T:
        """Добавляет новую запись на основе Pydantic-значений, "флашит" её для получения ID."""
        values_dict = values.model_dump()
        instance = cls.model(**values_dict)
        session.add(instance)
        try:
            await session.flush()
            # Инстанс теперь будет иметь свой ID и другие сгенерированные БД значения
            return instance
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Error occurred during add: {e}")
            raise e

    @classmethod
    async def update_one_by_id(cls, session: AsyncSession, data_id: uuid.UUID, values: BaseModel) -> Union[T, None]:
        """Обновляет запись по ID на основе Pydantic-значений, "флашит" изменения."""
        values_dict = values.model_dump(exclude_unset=True) # Включаем только установленные поля
        try:
            record = await session.get(cls.model, data_id) # Используем session.get для поиска по первичному ключу
            if not record:
                return None

            await cls._update_model_from_dict(record, values_dict, session)

            await session.flush()
            # Commit не происходит здесь; BaseCrud только делает flush,
            # вызывающий код (например, CRUDService) должен сделать commit
            return record

        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Error occurred during update_one_by_id: {e}")
            raise e

    @classmethod
    async def delete_one_by_id(cls, session: AsyncSession, data_id: uuid.UUID) -> bool:
        """Удаляет запись по ID, "флашит" изменения."""
        try:
            data = await session.get(cls.model, data_id)
            if data:
                await session.delete(data)
                await session.flush()
                return True
            return False # Запись не найдена
        except SQLAlchemyError as e:
            print(f"Error occurred during delete_one_by_id: {e}")
            raise