from src.databaseM.database import async_session_maker
from functools import wraps
from typing import Optional
from sqlalchemy import text

def connection(commit: bool = True):
    """
    Декоратор для управления сессией с возможностью настройки коммита.
    Параметры:
    - `commit`: если `True`, выполняется коммит после вызова метода.
    """
    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            async with async_session_maker() as session:
                try:
                    result = await method(*args, session=session, **kwargs)
                    if commit:
                        await session.commit()
                    return result
                except Exception as e:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        return wrapper
    return decorator