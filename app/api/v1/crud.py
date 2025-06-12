from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import (
    BaseModel,
    create_model
)

from core.database import (
    BaseCrud,
    model
)

from core.schemes import (
    UserSchema,
    UsersSchema,
    ProfileSchema,
    LobbySchema,
    LobbiesSchema,
)


# Объявления классов для работы с таблицами
class UserCrud(BaseCrud[model.User]):
    model = model.User

class ProfileCrud(BaseCrud[model.Profile]):
    model = model.Profile

class LobbyCrud(BaseCrud[model.Lobby]):
    model = model.Lobby


# Crud Добавление User и Profile
async def user_add(session: AsyncSession, userdata: BaseModel) -> str:
    user = await UserCrud.add(session=session, values=userdata)

    profile = create_model("Profile", user_id=(str, str(user.id)))
    await ProfileCrud.add(session=session, values=profile())
    
    await session.commit()
    return str(user.id)


# Crud Операции для users
async def user_get_by_id(session: AsyncSession, userid: str) -> UserSchema | None:
    user = await UserCrud.find_one_or_none_by_id(session=session, data_id=userid)
    if not user:
        return None
    return UserSchema.model_validate(user)

async def user_get(session: AsyncSession, filters: BaseModel) -> UserSchema | None:
    user = await UserCrud.find_one_or_none(session=session, filters=filters)
    if not user:
        return None
    return UserSchema.model_validate(user)

async def user_get_all(session: AsyncSession, filters: BaseModel) -> UsersSchema:
    users = await UserCrud.find_all(session=session, filters=filters)
    return UsersSchema(users=[UserSchema.model_validate(user) for user in users])

async def user_update(session: AsyncSession, userid: str, update_data: BaseModel) -> None:
    await UserCrud.update_one_by_id(session=session, data_id=userid, values=update_data)
    await session.commit()


async def user_delete(session: AsyncSession, userid: str)  -> None:
    await UserCrud.delete_one_by_id(session=session, data_id=userid)
    await session.commit()


# Crud Операции для Profile
async def profile_reset(session: AsyncSession, userid: str) -> None:

    update_data = ProfileSchema(
        user_id=userid,
        icon=None,
        wins=0,
        loses=0,
        visibility=True,
    )

    await ProfileCrud.update_one_by_id(session=session, data_id=userid, values=update_data)
    await session.commit()


async def profile_update(session: AsyncSession, userid: str, update_data: BaseModel) -> None:
    await ProfileCrud.update_one_by_id(session=session, data_id=userid, values=update_data)
    await session.commit()


# Crud Операции для lobbies
async def lobby_add(session: AsyncSession, lobbydata: BaseModel) -> str:
    lobby = await LobbyCrud.add(session=session, values=lobbydata)
    await session.commit()
    return str(lobby.id)


async def lobby_get_by_id(session: AsyncSession, lobbyid: str) -> LobbySchema:
    lobby = await LobbyCrud.find_one_or_none_by_id(session=session, data_id=lobbyid)
    await session.commit()
    return LobbySchema.model_validate(lobby)

async def lobby_get(session: AsyncSession, lobbydata: BaseModel) -> LobbySchema:
    lobby = await LobbyCrud.find_one_or_none(session=session, filters=lobbydata)
    await session.commit()
    return LobbySchema.model_validate(lobby)

async def lobby_get_all(session: AsyncSession, filters: BaseModel) -> LobbiesSchema:
    lobbies = await LobbyCrud.find_all(session=session, filters=filters)
    return LobbiesSchema(lobbies=[LobbySchema.model_validate(lobby) for lobby in lobbies])


async def lobby_update(session: AsyncSession, lobbyid: str, update_data: BaseModel) -> None:
    await LobbyCrud.update_one_by_id(session=session, data_id=lobbyid, values=update_data)
    await session.commit()


async def lobby_delete(session: AsyncSession, lobbyid: str) -> None:
    await LobbyCrud.delete_one_by_id(session=session, data_id=lobbyid)
    await session.commit()