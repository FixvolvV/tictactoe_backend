import asyncio
from datetime import (
    datetime,
    timezone,
    timedelta
)

from typing import Annotated
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends
)

from fastapi.security import HTTPBearer

from api.v1.logic.manager import lobby_manager, PlayerConnection
from api.v1.validators import get_current_active_auth_user_ws
from core.schemes.user_schemes import UserSchema

from api.v1.logic.handlers import (
    handle_ready,
    handle_move,
    handle_disconnect
)

from core.utils.enums import connectionstate


PING_INTERVAL = 10
PING_TIMEOUT = 20


# Create http bearer for auto documentation


# Init auth router
router = APIRouter(
    tags=["Game"]
)

async def ping_client(player: PlayerConnection):
    while True:
        try:
            await player.websocket.send_json({"event": "ping"})
            await asyncio.sleep(PING_INTERVAL)

            # Проверка Pong
            now = datetime.now(timezone.utc)
            if player.last_pong and (now - player.last_pong) > timedelta(seconds=PING_TIMEOUT):
                await player.websocket.close()
                break

        except Exception:
            break

@router.websocket("/game/{lobby_id}")
async def websocket_game(
    websocket: WebSocket,
    lobby_id: str,
    user: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user_ws)
    ]):
    
    await websocket.accept()

    lobby = lobby_manager.get_lobby(lobby_id)

    if not lobby:
        await websocket.send_json({"error": "Lobby not found"})
        await websocket.close()
        return

    if len(lobby.lobby_data.players) >= 2:
        await websocket.send_json({"error": "Lobby is full"})
        await websocket.close()
        return


    symbol = "X" if not lobby.lobby_data.players else "O"

    player = PlayerConnection(websocket, symbol, user)
    lobby.lobby_data.players.append(player)

    # Немедленно отправим статус
    await websocket.send_json({
        "event": "joined",
        "symbol": player.symbol,
        "state": lobby.state,
    })

    # Создаем задачу пинга
    ping_task = asyncio.create_task(ping_client(player))

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "ping":
                player.last_pong = datetime.now(timezone.utc)
                await websocket.send_json({"event": "pong"})

            elif action == "ready":
                await handle_ready(lobby, player)

            elif action == "move":
                await handle_move(lobby, player, data)

            elif action == "leave":
                await handle_disconnect(lobby, player)

    except WebSocketDisconnect:
        await handle_disconnect(lobby, player)

    finally:
        ping_task.cancel()