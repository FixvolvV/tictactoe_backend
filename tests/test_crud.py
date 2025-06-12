from datetime import datetime
from pydantic import create_model
import pytest

import uuid

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.api.v1.crud import (
    lobby_add,
    lobby_delete,
    lobby_get,
    lobby_get_all,
    lobby_get_by_id,
    lobby_update,
    profile_reset,
    profile_update,
    user_add,
    user_get_by_id,
    user_get,
    user_get_all,
    user_update,
    user_delete
)

from app.core.schemes import (
    UsersSchema,
    LobbySchema,
    LobbiesSchema,
    ProfileSchema,
    RegisterSchema,
)
from app.core.utils import (
    lobbystage,
    gametype
)



# Создание Pydantic объекта для нового пользователя
user_data = RegisterSchema(
    username="Balbes22",
    password="123456",
    email="test@test.com"  # Добавляем обязательные поля
)

Filters = create_model('VV', username=(str, ...))
Empty_Filters = create_model('VVVV')
empty = Empty_Filters()

@pytest.mark.asyncio
async def test_user_crud(test_session_getter: AsyncSession):

    # Create 
    created_user_id = await user_add(test_session_getter, user_data)
    assert created_user_id is not None 


    # Read by ID
    fetched_user = await user_get_by_id(test_session_getter, created_user_id)
    assert fetched_user is not None
    assert fetched_user.username == "Balbes22"
    assert fetched_user.profile.wins == 0


    # Read by filter
    filters = Filters(username="Balbes22")
    found_user = await user_get(test_session_getter, filters)
    assert found_user.id == created_user_id


    # Get All 
    all_users = await user_get_all(test_session_getter, empty)

    assert isinstance(all_users, UsersSchema)
    assert created_user_id in [u.id for u in all_users.users]


    # Update
    filters = Filters(username="BalbesUpdated")
    await user_update(test_session_getter, created_user_id, filters)
    updated_user = await user_get_by_id(test_session_getter, created_user_id)
    assert updated_user.username == "BalbesUpdated"


    # Delete
    await user_delete(test_session_getter, created_user_id)
    all_users = await user_get_all(test_session_getter, empty)
    assert len(all_users.users) == 0 



# Создание Pydantic объекта для нового пользователя
user_data2 = RegisterSchema(
    username="Fixvolvo",
    password="megahardpassword1",
    email="sosat@syki.com"  # Добавляем обязательные поля
)


profile_data = ProfileSchema(
    icon="/data/icons/134421sosal",
    wins=99,
    loses=1,
    visibility=False,
)


@pytest.mark.asyncio
async def test_profile_crud(test_session_getter: AsyncSession):

    # Create
    created_user_id = await user_add(test_session_getter, user_data2)
    assert created_user_id is not None 

    # Update 
    await profile_update(session=test_session_getter, userid=created_user_id, update_data=profile_data)
    fetched_user = await user_get_by_id(test_session_getter, created_user_id)
    assert fetched_user is not None
    assert fetched_user.profile.icon == "/data/icons/134421sosal"
    assert fetched_user.profile.visibility == False
    assert fetched_user.profile.wins == 99
    assert fetched_user.profile.loses == 1

    # Reset
    await profile_reset(session=test_session_getter, userid=created_user_id)

    fetched_user = await user_get_by_id(test_session_getter, created_user_id)
    assert fetched_user is not None
    assert fetched_user.profile.icon == None
    assert fetched_user.profile.visibility == True
    assert fetched_user.profile.wins == 0
    assert fetched_user.profile.loses == 0


test_lobby_id = uuid.uuid4()
test_player_id = uuid.uuid4()
test_player2_id = uuid.uuid4()


lobby_data = LobbySchema(
    id = str(test_lobby_id),
    name = "Test lobby",
    players=[str(test_player_id), str(test_player2_id)],
    field={"X": "1 1", "O": "1 2"},
    gametype=gametype.INFINITY_TIC_TAC_TOE,
    state=lobbystage.COMPLETED,
    time_create=datetime.now()
)

Filter2 = create_model("VVV", name=(str, ...))

@pytest.mark.asyncio
async def test_lobby_crud(test_session_getter: AsyncSession):

    # Create 
    created_lobby_id = await lobby_add(test_session_getter, lobby_data)
    assert created_lobby_id is not None


    # Read by ID
    fetched_lobby = await lobby_get_by_id(test_session_getter, created_lobby_id)
    assert fetched_lobby is not None
    assert fetched_lobby.name == "Test lobby"


    # Read by filter
    filters = Filter2(name="Test lobby")
    found_lobby = await lobby_get(test_session_getter, filters)
    assert found_lobby.id == created_lobby_id


    # Get All 
    all_lobbies = await lobby_get_all(test_session_getter, empty)
    assert isinstance(all_lobbies, LobbiesSchema)
    assert created_lobby_id in [u.id for u in all_lobbies.lobbies] #pyright:ignore


    # Update
    updated = Filter2(name="Test abobys")

    await lobby_update(test_session_getter, created_lobby_id, updated)
    updated_lobby = await lobby_get_by_id(test_session_getter, created_lobby_id)
    assert updated_lobby.name == "Test abobys"


    # Delete
    await lobby_delete(test_session_getter, created_lobby_id)
    all_lobbies = await lobby_get_all(test_session_getter, empty)
    assert len(all_lobbies.lobbies) == 0 