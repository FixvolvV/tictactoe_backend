from core.utils import connectionstate
from manager import (
    lobby_manager,
    Lobby,
    PlayerConnection
)

async def handle_disconnect(lobby: Lobby, user_id: str):
    player = lobby.players.pop(user_id, None)
    if not player:
        return

    if not lobby.players:
        lobby_manager.remove_lobby(lobby.id)
    else:
        for other in lobby.players.values():
            await other.websocket.send_json({"info": "Игрок отключился"})