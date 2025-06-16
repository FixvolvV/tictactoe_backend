from core.utils import connectionstate

from ..manager import (
    Lobby,
    PlayerConnection
)


async def handle_ready(lobby: Lobby, player: PlayerConnection):
    player.is_ready = True

    await player.websocket.send_json({"event": "you_ready"})

    if lobby.state == connectionstate.WAITING and all(p.is_ready for p in lobby.lobby_data.players):
        lobby.state = connectionstate.READY

        # Переход в PLAYING
        lobby.start_game()

        for p in lobby.lobby_data.players:
            await p.websocket.send_json({
                "event": "start",
                "symbol": p.symbol,
                "state": lobby.state
            })