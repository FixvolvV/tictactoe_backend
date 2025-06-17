import asyncio
from datetime import (
    datetime,
    timezone,
    timedelta
)

from typing import Annotated, Optional
from fastapi import (
    APIRouter,
    WebSocket,
    Depends
)
from fastapi import WebSocketDisconnect

# ИСПРАВЛЕНИЕ: Удаляем WebSocketCloseCode из импорта
from starlette.websockets import WebSocketState 

from api.v1.logic.manager import lobby_manager, PlayerConnection, Lobby
from api.v1.validators import get_current_active_auth_user_ws
from core.schemes.user_schemes import UserSchema

from api.v1.logic import (
    handlers
)

PING_INTERVAL = 10
PING_TIMEOUT = 20

router = APIRouter(
    tags=["Game"]
)

async def ping_client_task(player: PlayerConnection):
    """Задача, которая периодически отправляет пинги клиенту и проверяет ответы."""
    try:
        while True:
            if player.websocket.client_state != WebSocketState.CONNECTED:
                print(f"Ping task: WebSocket for {player.user.username} not connected (state: {player.websocket.client_state}), exiting.")
                break
            
            await player.websocket.send_json({"event": "ping"})
            await asyncio.sleep(PING_INTERVAL)

            now = datetime.now(timezone.utc)
            if player.last_pong is None or (now - player.last_pong) > timedelta(seconds=PING_TIMEOUT):
                print(f"Ping timeout for {player.user.username}. Closing connection.")
                if player.websocket.client_state == WebSocketState.CONNECTED:
                    # ИСПРАВЛЕНИЕ: Используем числовой код 1008
                    await player.websocket.close(code=1008) 
                break

    except WebSocketDisconnect:
        print(f"Ping task: WebSocket for {player.user.username} disconnected cleanly.")
    except asyncio.CancelledError:
        print(f"Ping task for {player.user.username} cancelled.")
    except Exception as e:
        print(f"Ping task for {player.user.username} encountered an error: {e}")
    finally:
        if player.lobby: 
            await handlers.handle_disconnect(player.lobby, player)


@router.websocket(
    "/{lobby_id}"
)
async def websocket_game(
    websocket: WebSocket,
    lobby_id: str,
    user: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user_ws)
    ]
):
    await websocket.accept()
    
    lobby: Optional[Lobby] = lobby_manager.get_lobby(lobby_id)

    if not lobby:
        print(f"Lobby {lobby_id} not found for user {user.username}.")
        try:
            await websocket.send_json({"error": "Lobby not found."})
        except RuntimeError: 
            pass
        # ИСПРАВЛЕНИЕ: Используем числовой код 1000
        await websocket.close(code=1000) 
        return

    player_to_handle: Optional[PlayerConnection] = None
    existing_player_found = False

    for p_conn in lobby.players:
        if p_conn.user.id == user.id:
            player_to_handle = p_conn
            player_to_handle.websocket = websocket
            player_to_handle.last_pong = datetime.now(timezone.utc)
            player_to_handle.lobby = lobby 
            existing_player_found = True
            print(f"Player {user.username} reconnected to lobby {lobby_id}.")
            break
    
    if not existing_player_found:
        if len(lobby.players) >= 2:
            print(f"Lobby {lobby_id} is full. User {user.username} cannot join.")
            try:
                await websocket.send_json({"error": "Lobby is full."})
            except RuntimeError:
                pass
            # ИСПРАВЛЕНИЕ: Используем числовой код 1003
            await websocket.close(code=1003) 
            return
        
        assigned_symbol = "X"
        current_symbols = {p.symbol for p in lobby.players}
        if "X" in current_symbols:
            assigned_symbol = "O"
        
        if "X" in current_symbols and "O" in current_symbols:
            print(f"Lobby {lobby_id}: No available symbols for user {user.username}.")
            try:
                await websocket.send_json({"error": "No available symbols."})
            except RuntimeError:
                pass
            # ИСПРАВЛЕНИЕ: Используем числовой код 1003
            await websocket.close(code=1003) 
            return

        player_to_handle = PlayerConnection(websocket, assigned_symbol, user, lobby) 
        lobby.players.append(player_to_handle)
        print(f"Player {user.username} ({assigned_symbol}) joined lobby {lobby_id}.")
        
        lobby.set_owner_if_not_set()

    if player_to_handle:
        ping_task = asyncio.create_task(ping_client_task(player_to_handle))

        try:
            await lobby.broadcast_state("game:joined") 

            while True:
                data = await websocket.receive_json()
                action = data.get("action")

                if action == "ping":
                    player_to_handle.last_pong = datetime.now(timezone.utc) 
                    pass 

                elif action == "ready":
                    await handlers.handle_ready(lobby, player_to_handle)

                elif action == "move":
                    await handlers.handle_move(lobby, player_to_handle, data)

                elif action == "leave":
                    await handlers.handle_disconnect(lobby, player_to_handle)
                    break 

        except WebSocketDisconnect:
            print(f"WebSocket for {user.username} disconnected.")
            await handlers.handle_disconnect(lobby, player_to_handle)
        except Exception as e:
            print(f"Error in WebSocket for {user.username}: {e}")
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json({"error": f"An unexpected error occurred: {e}"})
                except RuntimeError:
                    pass 
            await handlers.handle_disconnect(lobby, player_to_handle)
        finally:
            ping_task.cancel()
    else:
        print(f"Critical error: player_to_handle is None after connection attempt for {user.username}.")
        try:
            await websocket.send_json({"error": "Internal server error."})
        except RuntimeError:
            pass
        # ИСПРАВЛЕНИЕ: Используем числовой код 1011
        await websocket.close(code=1011) 
