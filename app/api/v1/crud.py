import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import List

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

    # Переопределяем метод add специально для Lobby, чтобы обрабатывать отношение 'players'
    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        values_dict = values.model_dump(exclude_unset=True)

        player_ids_from_schema: List[uuid.UUID] = values_dict.pop("players", [])
        player_objects: List[model.User] = []
        if player_ids_from_schema:
            stmt_players = select(model.User).where(model.User.id.in_(player_ids_from_schema))
            result_players = await session.execute(stmt_players)
            player_objects = list(result_players.scalars().all())

            if len(player_objects) != len(player_ids_from_schema):
                print(f"Warning: Not all players found for lobby creation. Expected {len(player_ids_from_schema)}, found {len(player_objects)}")
        values_dict["players"] = player_objects 

        instance = cls.model(**values_dict)
        session.add(instance)
        try:
            await session.flush() 
            await session.commit() 
            await session.refresh(instance) 
            return instance
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"Error occurred during LobbyCrud.add: {e}")
            raise e



# Crud Добавление User и Profile
async def user_add(session: AsyncSession, userdata: BaseModel) -> str:
    user = await UserCrud.add(session=session, values=userdata)

    profile = create_model("Profile", user_id=(str, str(user.id)))
    await ProfileCrud.add(session=session, values=profile())
    
    await session.commit()
    return str(user.id)


# Crud Операции для users
async def user_get_by_id(session: AsyncSession, userid: str) -> UserSchema | None:
    user = await UserCrud.find_one_or_none_by_id(session=session, data_id=uuid.UUID(userid))
    if not user:
        return None
    return UserSchema.model_validate(user)

async def user_get(session: AsyncSession, filters: BaseModel) -> UserSchema | None:
    user = await UserCrud.find_one_or_none(session=session, filters=filters)
    if not user:
        return None
    return UserSchema.model_validate(user)

async def user_get_all(session: AsyncSession, filters: BaseModel | None) -> UsersSchema:
    users = await UserCrud.find_all(session=session, filters=filters)
    return UsersSchema(users=[UserSchema.model_validate(user) for user in users])

async def user_update(session: AsyncSession, userid: str, update_data: BaseModel) -> None:
    await UserCrud.update_one_by_id(session=session, data_id=uuid.UUID(userid), values=update_data)
    await session.commit()


async def user_delete(session: AsyncSession, userid: str)  -> None:
    await UserCrud.delete_one_by_id(session=session, data_id=uuid.UUID(userid))
    await session.commit()


# Crud Операции для Profile
"""
 Outdate. Я добавил relationship к base_crud. И теперь профили по сути как User и всегда подсасываються.
"""

# Crud Операции для lobbies
async def lobby_add(session: AsyncSession, lobbydata: BaseModel) -> str:
    lobby = await LobbyCrud.add(session=session, values=lobbydata)
    await session.commit()
    return str(lobby.id)


async def lobby_get_by_id(session: AsyncSession, lobbyid: str) -> LobbySchema | None:
    lobby = await LobbyCrud.find_one_or_none_by_id(session=session, data_id=uuid.UUID(lobbyid))
    await session.commit()
    return LobbySchema.model_validate(lobby)

async def lobby_get(session: AsyncSession, lobbydata: BaseModel) -> LobbySchema | None:
    lobby = await LobbyCrud.find_one_or_none(session=session, filters=lobbydata)
    await session.commit()
    return LobbySchema.model_validate(lobby)

async def lobby_get_all(session: AsyncSession, filters: BaseModel | None) -> LobbiesSchema:
    lobbies = await LobbyCrud.find_all(session=session, filters=filters)
    return LobbiesSchema(lobbies=[LobbySchema.model_validate(lobby) for lobby in lobbies])


async def lobby_update(session: AsyncSession, lobbyid: str, update_data: BaseModel) -> None:
    await LobbyCrud.update_one_by_id(session=session, data_id=uuid.UUID(lobbyid), values=update_data)
    await session.commit()


async def lobby_delete(session: AsyncSession, lobbyid: str) -> None:
    await LobbyCrud.delete_one_by_id(session=session, data_id=uuid.UUID(lobbyid))
    await session.commit()