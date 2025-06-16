from core.utils import connectionstate
from ..manager import (
    lobby_manager,
    Lobby,
    PlayerConnection
)

async def handle_move(lobby: Lobby, player: PlayerConnection, data: dict):
    if lobby.state != connectionstate.PLAYING:
        await player.websocket.send_json({"error": "Игра ещё не началась!"})
        return

    if lobby.game.current_player != player.symbol:
        await player.websocket.send_json({"error": "Не ваш ход"})
        return

    row = data.get("row")
    col = data.get("col")
    try:
        result = lobby.game.make_move(row, col)
    except ValueError as e:
        await player.websocket.send_json({"error": str(e)})
        return

    payload = {
        "row": row,
        "col": col,
        "board": lobby.game.get_board(),
        "symbol": player.symbol,
        **result
    }

    for p in lobby.lobby_data.players:
        await p.websocket.send_json(payload)

    # Проверить победу
    if "winner" in result:
        lobby.end_game()

        for p in lobby.lobby_data.players:
            event = "win" if p.symbol == player.symbol else "lose"
            await p.websocket.send_json({"event": event})
            await p.websocket.close()

        lobby_manager.remove_lobby(lobby.lobby_data.id)