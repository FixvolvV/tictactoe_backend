from core.utils import connectionstate
from ..manager import (
    lobby_manager,
    Lobby,
    PlayerConnection
)

async def handle_disconnect(lobby: Lobby, user: PlayerConnection):
    player = lobby.lobby_data.players.remove(user)
    if not player:
        return

    if not lobby.lobby_data.players:
        lobby_manager.remove_lobby(lobby.lobby_data.id)
    else:
        for other in lobby.lobby_data.players:
            await other.websocket.send_json({"info": "Игрок отключился"})