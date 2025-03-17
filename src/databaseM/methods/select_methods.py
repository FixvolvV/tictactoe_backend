from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.databaseM.sessionGen import connection
from src.databaseM.bases.basemodels import UserBDM, LobbyBDM


@connection(commit=False)
async def get_user_by_id(session: AsyncSession, id: int):
    return await UserBDM.find_one_or_none_by_id(session=session, data_id=id)

@connection(commit=False)
async def get_user_by_username(session: AsyncSession, filters: BaseModel):
    return await UserBDM.find_one_or_none(session=session, filters=filters)

@connection(commit=False)
async def get_all_users(session: AsyncSession, filters: BaseModel | None):
    return await UserBDM.find_all(session=session, filters=filters)

@connection(commit=False)
async def get_lobby_by_id(session: AsyncSession, id: int):
    return await LobbyBDM.find_one_or_none_by_id(session=session, data_id=id)

@connection(commit=False)
async def get_all_lobbies(session: AsyncSession, filters: None):
    return await LobbyBDM.find_all(session=session, filters=filters)


