from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.ext.asyncio import AsyncAttrs

# Базовый класс для всех моделей
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True