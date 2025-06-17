import json
import asyncio
from typing import (
    Annotated,
    Optional
)
from fastapi import APIRouter, Request
from fastapi.params import Depends
from fastapi.responses import StreamingResponse
from fastapi.responses import (
    JSONResponse
)
from fastapi.security import HTTPBearer
from sqlalchemy.sql.functions import current_user
from starlette import status

from api.v1.validators import get_current_active_auth_user

from core.schemes import (
    UserSchema
)

from core.database import (
    db_control,
)

from core.utils import (
    connectionstate
)

from api.v1.logic.manager import lobby_manager

# Create http bearer for auto documentation
http_bearer = HTTPBearer(auto_error=False)


# Init auth router
router = APIRouter(
    tags=["Lobby"],
    dependencies=[Depends(http_bearer)]
)


# Lobby POST ------<  plug
@router.post(
    "/create",
)
async def lobby_create(
    lobbyname: str,
    verify: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ]
):

    lobby_id = lobby_manager.create_lobby(lobby_name=lobbyname) 

    return lobby_id


def select_lobby(query_name: str | None):
    current_lobbies = []
    lobby = {}
    lobbies = lobby_manager.get_lobbies()
    
    for value in lobbies.values():
        if value.state != connectionstate.WAITING:
            continue

        if query_name is not None:
            if query_name.lower != value.name.lower:
                continue

        lobby = {
            "id": value.id,
            "name": value.name,
            "gametype": value.game_type,
            "owner": value.owner_username
        }

        current_lobbies.append(lobby)
    return current_lobbies


async def lobbies_checker(request: Request, query_name: str | None):
    message_id = 0
    try:
        while True:
            # Проверяем, не отключился ли клиент
            if await request.is_disconnected():
                break

            event_data = select_lobby(query_name) # Отправляем весь текущий список
        
            # 3. Форматируем сообщение в SSE
            message = (
                f"id: {message_id}\n"
                f"event: lobby_update\n" # Указываем тип события
                f"data: {json.dumps(event_data)}\n\n" # Две новые строки в конце!
            )
            yield message
            message_id += 1

            # 4. Задержка перед следующим обновлением
            await asyncio.sleep(1) # Отправляем обновления каждые 1 секунду

    except asyncio.CancelledError:
        raise
    except Exception as e:
        print(e)

# Lobby GET(SSE) ------<  plug
@router.get(
    "/all/wait",
    response_class=StreamingResponse
)
async def lobby_all_get(
    request: Request,
    verify: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    query_name: Optional[str] = None
):

    return StreamingResponse(lobbies_checker(request, query_name), media_type="text/event-stream")