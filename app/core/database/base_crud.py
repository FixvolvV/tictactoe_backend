from typing import Generic, TypeVar, Dict, Any
from pydantic import BaseModel

from sqlalchemy import (
    select,
    inspect
)
from sqlalchemy.sql import Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    selectinload,
    joinedload,
    class_mapper,
    RelationshipProperty,
)

from core.database.model import Base

T = TypeVar("T")


class BaseCrud(Generic[T]):
    model: type[T]  # Устанавливается в наследниках

    # EAGER LOAD RELATIONSHIPS: joinedload/selectinload for lazy loading

    @classmethod
    def _get_relationship_load_options(cls):
        load_options = []
        mapper = class_mapper(cls.model)
        for rel in mapper.relationships:
            if rel.lazy == "selectin":
                load_options.append(selectinload(getattr(cls.model, rel.key)))
            elif rel.lazy == "joined":
                load_options.append(joinedload(getattr(cls.model, rel.key)))
        return load_options

    # ПРИМЕНЕНИЕ ФИЛЬТРОВ из Pydantic-модели (в том числе по связям)
    @classmethod
    def _apply_filters_from_pydantic(
        cls,
        base_stmt: Select,
        filters: BaseModel | None
    ) -> Select:
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}

        stmt = base_stmt
        model_filters: Dict[str, Any] = {}
        relation_filters: Dict[str, Dict[str, Any]] = {}

        for key, value in filter_dict.items():
            if '_' in key:
                rel_name, rel_field = key.split('_', 1)
                relation_filters.setdefault(rel_name, {})[rel_field] = value
            else:
                model_filters[key] = value

        if model_filters:
            stmt = stmt.filter_by(**model_filters)

        for rel_name, rel_fields in relation_filters.items():
            rel_attr = getattr(cls.model, rel_name, None)
            if rel_attr is not None:
                stmt = stmt.where(rel_attr.has(**rel_fields))

        return stmt

    # ОБНОВЛЕНИЕ ORM-модели (в том числе вложенных relationships)
    @classmethod
    def _update_model_from_dict(cls, instance, values_dict: dict):
        inspect(instance).mapper

        for key, value in values_dict.items():
            if not hasattr(instance, key):
                continue

            prop = getattr(type(instance), key, None)
            if not prop or not hasattr(prop, 'property'):
                continue

            if isinstance(prop.property, RelationshipProperty):
                cls._handle_relationship(instance, key, value, prop)
            else:
                setattr(instance, key, value)


    @classmethod
    def _handle_relationship(cls, instance, key, value, prop):
        if not isinstance(value, dict):
            return

        rel_obj = getattr(instance, key, None)

        if rel_obj:
            cls._update_model_from_dict(rel_obj, value)
        else:
            related_cls = prop.property.mapper.class_
            new_obj = related_cls(**value)
            setattr(instance, key, new_obj)

    # CRUD-МЕТОДЫ
    @classmethod
    async def find_one_or_none_by_id(cls, session: AsyncSession, data_id: str):
        try:
            stmt = select(cls.model).where(getattr(cls.model, "id") == data_id)

            for opt in cls._get_relationship_load_options():
                stmt = stmt.options(opt)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        try:
            stmt = cls._apply_filters_from_pydantic(select(cls.model), filters)

            for opt in cls._get_relationship_load_options():
                stmt = stmt.options(opt)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None = None):
        try:
            stmt = cls._apply_filters_from_pydantic(select(cls.model), filters)

            for opt in cls._get_relationship_load_options():
                stmt = stmt.options(opt)

            result = await session.execute(stmt)
            return result.scalars().all()

        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        values_dict = values.model_dump()
        instance = cls.model(**values_dict)
        session.add(instance)
        try:
            await session.flush()
            return instance
        except SQLAlchemyError as e:
            await session.rollback()
            raise e

    @classmethod
    async def update_one_by_id(cls, session: AsyncSession, data_id: str, values: BaseModel):
        values_dict = values.model_dump(exclude_unset=True)
        try:
            record = await session.get(cls.model, data_id)
            if not record:
                return None

            cls._update_model_from_dict(record, values_dict)

            await session.flush()
            return record

        except SQLAlchemyError as e:
            await session.rollback()
            raise e

    @classmethod
    async def delete_one_by_id(cls, data_id: str, session: AsyncSession):
        try:
            data = await session.get(cls.model, data_id)
            if data:
                await session.delete(data)
                await session.flush()
        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise
