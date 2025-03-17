from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession

from src.databaseM.bases.basemodels import UserBDM, LobbyBDM
from src.databaseM.sessionGen import connection



@connection(commit=True)
async def add_one_user(user_data: BaseModel, session: AsyncSession):
    new_user = await UserBDM.add(session=session, values=user_data)
    return new_user.id


@connection(commit=True)
async def add_one_lobby(lobby_data: BaseModel, session: AsyncSession):
    new_lobby = await LobbyBDM.add(session=session, values=lobby_data)
    return new_lobby.id