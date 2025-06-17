import asyncio
from core.utils import connectionstate
from .manager import (
    lobby_manager,
    Lobby,
    PlayerConnection
)
# ИСПРАВЛЕНИЕ: Удаляем WebSocketCloseCode из импорта
from starlette.websockets import WebSocketState 

async def safe_send_json(websocket, message: dict):
    if websocket.client_state == WebSocketState.CONNECTED:
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            print(f"Failed to send JSON (connection likely closed): {e}")
        except Exception as e:
            print(f"Unexpected error sending JSON: {e}")

async def handle_disconnect(lobby: Lobby, player_to_disconnect: PlayerConnection):
    print(f"handle_disconnect called for {player_to_disconnect.user.username} in lobby {lobby.id}.")

    if lobby.id not in lobby_manager.lobbies or player_to_disconnect not in lobby.players:
        print(f"Player {player_to_disconnect.user.username} or lobby {lobby.id} already handled/removed.")
        return

    was_playing = (lobby.state == connectionstate.PLAYING)
    
    try:
        lobby.players.remove(player_to_disconnect)
        print(f"Player {player_to_disconnect.user.username} removed from lobby {lobby.id}'s player list.")
    except ValueError:
        print(f"Player {player_to_disconnect.user.username} not found in lobby {lobby.id}'s player list during remove operation.")

    if was_playing:
        if len(lobby.players) == 1:
            remaining_player = lobby.players[0]
            print(f"Player {player_to_disconnect.user.username} disconnected during game. Player {remaining_player.user.username} wins by forfeit.")
            
            lobby.end_game(remaining_player.symbol) 
            lobby.win_line = [] 

            await safe_send_json(remaining_player.websocket, {"event": "win", "message": "Your opponent left the game."})
            
            await lobby.broadcast_state("lobby_state_update")

            await asyncio.sleep(2) 
            
            if remaining_player.websocket.client_state == WebSocketState.CONNECTED:
                # ИСПРАВЛЕНИЕ: Используем числовой код 1000
                await remaining_player.websocket.close(code=1000)
            
            await lobby_manager.remove_lobby(lobby.id)
            print(f"Lobby {lobby.id} removed due to forfeit.")
            return

        elif len(lobby.players) == 0:
            if lobby.id in lobby_manager.lobbies:
                # ИСПРАВЛЕНИЕ: Используем числовой код 1000 внутри remove_lobby
                await lobby_manager.remove_lobby(lobby.id) 
                print(f"Lobby {lobby.id} removed as both players disconnected during game or last player left.")
            return

    if not lobby.players:
        if lobby.id in lobby_manager.lobbies:
            # ИСПРАВЛЕНИЕ: Используем числовой код 1000 внутри remove_lobby
            await lobby_manager.remove_lobby(lobby.id) 
            print(f"Lobby {lobby.id} removed as all players disconnected (not during active game).")
    else:
        if lobby.state == connectionstate.PLAYING or lobby.state == connectionstate.READY:
            lobby.reset_game()
            print(f"Game in lobby {lobby.id} reset due to player disconnect (not a forfeit).")
            
        await lobby.broadcast_state("lobby_state_update")
        print(f"Remaining players in lobby {lobby.id}: {len(lobby.players)}")


async def handle_move(lobby: Lobby, player: PlayerConnection, data: dict):
    if lobby.state != connectionstate.PLAYING:
        await safe_send_json(player.websocket, {"error": "Игра ещё не началась!"})
        return

    if not lobby.game:
        await safe_send_json(player.websocket, {"error": "Ошибка: Игровая логика не инициализирована."})
        return

    if lobby.game.current_player != player.symbol:
        await safe_send_json(player.websocket, {"error": "Не ваш ход"})
        return

    row = data.get("row")
    col = data.get("col")

    if row is None or col is None:
        await safe_send_json(player.websocket, {"error": "Неверные данные хода: отсутствуют row или col."})
        await lobby.broadcast_state("lobby_state_update")
        return

    try:
        game_result = lobby.game.make_move(row, col)
    except ValueError as e:
        await safe_send_json(player.websocket, {"error": str(e)})
        await lobby.broadcast_state("lobby_state_update")
        return

    lobby.last_move = {'x': row, 'y': col, 'symbol': player.symbol}

    if "winner" in game_result:
        lobby.end_game(game_result["winner"])
        lobby.win_line = game_result["win_line"]

        await lobby.broadcast_state("lobby_state_update")

        for p in lobby.players:
            if p.symbol == game_result["winner"]:
                await safe_send_json(p.websocket, {"event": "win", "win_line": lobby.win_line})
            else:
                await safe_send_json(p.websocket, {"event": "lose", "win_line": lobby.win_line})
        
        await asyncio.sleep(2) 
        
        for p in lobby.players:
            if p.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    # ИСПРАВЛЕНИЕ: Используем числовой код 1000
                    await p.websocket.close(code=1000)
                except RuntimeError:
                    pass
        
        if lobby.id in lobby_manager.lobbies:
            # ИСПРАВЛЕНИЕ: Используем числовой код 1000 внутри remove_lobby
            await lobby_manager.remove_lobby(lobby.id)
            print(f"Lobby {lobby.id} removed after game finished.")

    else:
        await lobby.broadcast_state("lobby_state_update")


async def handle_ready(lobby: Lobby, player: PlayerConnection):
    player.is_ready = not player.is_ready
    print(f"Player {player.user.username} (Lobby {lobby.id}) is now ready: {player.is_ready}")

    ready_players_count = sum(1 for p in lobby.players if p.is_ready)
    
    if len(lobby.players) == 2 and ready_players_count == 2 and lobby.state == connectionstate.WAITING:
        for p in lobby.players:
            await safe_send_json(p.websocket, {
                "event": "start",
                "symbol": p.symbol,
                "state": lobby.state.value
            })

        lobby.start_game()
        print(f"Lobby {lobby.id}: Game started!")
        
        await asyncio.sleep(0.05) 
        
        await lobby.broadcast_state("lobby_state_update")
    else:
        await lobby.broadcast_state("lobby_state_update")
