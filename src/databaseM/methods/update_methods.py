from pydantic import create_model

from sqlalchemy.ext.asyncio import AsyncSession

from src.databaseM.bases.basemodels import LobbyBDM, UserBDM
from src.databaseM.sessionGen import connection

from src.utils.enums import lobbystage, winners


# @connection(commit=True) ### В РАЗРАБОТКЕ..............................
# async def update_user(session: AsyncSession, user_id: int, newvalues: dict):
#     ValueModel = create_model('ValueModel', players=(dict[str, str], ...))
#     await LobbyBDM.update_one_by_id(session=session, data_id=user_id, values=ValueModel(players=newvalues))


@connection(commit=True)
async def update_usergames(session: AsyncSession, user_id: int, newvalues: dict):
    ValueModel = create_model('ValueModel', games=(dict[str, int], ...))
    await UserBDM.update_one_by_id(session=session, data_id=user_id, values=ValueModel(games=newvalues))


@connection(commit=True)
async def update_lobbyplayers(session: AsyncSession, lobby_id: int, newvalues: dict):
    ValueModel = create_model('ValueModel', players=(dict[str, str], ...))
    await LobbyBDM.update_one_by_id(session=session, data_id=lobby_id, values=ValueModel(players=newvalues))


@connection(commit=True)
async def update_lobbystage(session: AsyncSession, lobby_id: int, newstage: lobbystage):
    ValueModel = create_model('ValueModel', stage=(lobbystage, ...))
    await LobbyBDM.update_one_by_id(session=session, data_id=lobby_id, values=ValueModel(stage=newstage))


@connection(commit=True)
async def update_lobbywinner(session: AsyncSession, lobby_id: int, winner: winners):
    ValueModel = create_model('ValueModel', winner=(winners, ...))
    await LobbyBDM.update_one_by_id(session=session, data_id=lobby_id, values=ValueModel(winner=winner))
