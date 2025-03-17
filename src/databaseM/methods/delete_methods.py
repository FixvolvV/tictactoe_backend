from sqlalchemy.ext.asyncio import AsyncSession

from src.databaseM.sessionGen import connection
from src.databaseM.bases.basemodels import UserBDM, LobbyBDM


@connection(commit=True)
async def delete_user_by_id(session: AsyncSession, user_id: int):
    await UserBDM.delete_one_by_id(session=session, data_id=user_id)


@connection(commit=True)
async def delete_lobby_by_id(session: AsyncSession, lobby_id: int):
    await LobbyBDM.delete_one_by_id(session=session, data_id=lobby_id)
