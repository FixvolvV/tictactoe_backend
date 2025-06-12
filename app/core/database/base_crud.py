from typing import Generic, TypeVar
from pydantic import BaseModel

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload, class_mapper, RelationshipProperty

from core.database.model import Base

T = TypeVar("T", bound=Base)

class BaseCrud(Generic[T]):
    model: type[T]  # Устанавливается в дочернем классе

    @classmethod
    def _get_relationship_load_options(cls):
        """
        Собираем опции подгрузки для relationships с lazy='selectin' или 'joined'
        """
        load_options = []
        mapper = class_mapper(cls.model)

        for rel in mapper.relationships:
            if rel.lazy == "selectin":
                load_options.append(selectinload(getattr(cls.model, rel.key)))
            elif rel.lazy == "joined":
                load_options.append(joinedload(getattr(cls.model, rel.key)))
        return load_options

    @classmethod
    async def find_one_or_none_by_id(cls, session: AsyncSession, data_id: str):
        try:
            stmt = select(cls.model).where(getattr(cls.model, "id") == data_id)

            # Добавляем eager загрузку зависимости, если она есть
            for option in cls._get_relationship_load_options():
                stmt = stmt.options(option)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        filter_dict = filters.model_dump(exclude_unset=True)
        try:
            stmt = select(cls.model).filter_by(**filter_dict)

            for option in cls._get_relationship_load_options():
                stmt = stmt.options(option)

            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise

    @classmethod
    async def find_all(cls, session: AsyncSession, filters: BaseModel | None):
        filter_dict = filters.model_dump(exclude_unset=True) if filters else {}
        try:
            stmt = select(cls.model).filter_by(**filter_dict)

            for option in cls._get_relationship_load_options():
                stmt = stmt.options(option)

            result = await session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error occurred: {e}")
            raise


    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        # Добавить одну запись
        values_dict = values.model_dump()
        new_instance = cls.model(**values_dict)
        session.add(new_instance)
        try:
            await session.flush()
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
        return new_instance

    @classmethod
    async def update_one_by_id(cls, session: AsyncSession, data_id: str, values: BaseModel):
        values_dict = values.model_dump(exclude_unset=True)
        try:
            record = await session.get(cls.model, data_id)
            for key, value in values_dict.items():
                setattr(record, key, value)
            await session.flush()
        except SQLAlchemyError as e:
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

