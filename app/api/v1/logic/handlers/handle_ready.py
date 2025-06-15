from core.utils import ConnectionState

from api.v1.lobby.manager import (
    Lobby,
    PlayerConnection
)


async def handle_ready(lobby: Lobby, player: PlayerConnection):
    player.is_ready = True

    await player.websocket.send_json({"event": "you_ready"})

    if lobby.state == ConnectionState.WAITING and all(p.is_ready for p in lobby.players.values()):
        lobby.state = ConnectionState.READY

        # Переход в PLAYING
        lobby.start_game()

        for p in lobby.players.values():
            await p.websocket.send_json({
                "event": "start",
                "symbol": p.symbol,
                "state": lobby.state
            })