import asyncio
from datetime import datetime, timezone, timedelta
import uuid


from sqlalchemy import PrimaryKeyConstraint

from core.utils import connectionstate
from .manager import (
    lobby_manager,
    Lobby,
    PlayerConnection
)
from starlette.websockets import WebSocketState

from core.database import db_control
from api.v1 import crud 
from pydantic import create_model 

# Импортируем измененную LobbySchema
from core.schemes import (
    LobbySchema,
    AdminUserUpdateSchema 
)
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
        print(f"Player {player_to_disconnect.user.username} not found in lobby {lobby.id}'s player list during disconnect attempt.")

    if was_playing:
        if len(lobby.players) == 1:
            remaining_player = lobby.players[0]
            print(f"Player {player_to_disconnect.user.username} disconnected during game. Player {remaining_player.user.username} wins by forfeit.")
            
            lobby.end_game(remaining_player.symbol) 
            lobby.win_line = [] 

            await safe_send_json(remaining_player.websocket, {"event": "win", "message": "Your opponent left the game."})
            
            await lobby.broadcast_state("lobby_state_update")

            await save_game_results(lobby)


            await asyncio.sleep(2) 
            
            if remaining_player.websocket.client_state == WebSocketState.CONNECTED:
                await remaining_player.websocket.close(code=1000)
            
            await lobby_manager.remove_lobby(lobby.id)
            print(f"Lobby {lobby.id} removed due to forfeit.")
            return

        elif len(lobby.players) == 0:
            if was_playing and lobby.game and lobby.start_time:
                lobby.end_game(None) 
                await save_game_results(lobby) 
                print(f"Lobby {lobby.id} game ended inconclusively and results saved due to no players remaining.")

            if lobby.id in lobby_manager.lobbies:
                await lobby_manager.remove_lobby(lobby.id)
                print(f"Lobby {lobby.id} removed as both players disconnected during game or last player left.")
            return

    if not lobby.players:
        if lobby.id in lobby_manager.lobbies:
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
        
        await save_game_results(lobby)

        await asyncio.sleep(2) 
        
        for p in lobby.players:
            if p.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await p.websocket.close(code=1000)
                except RuntimeError:
                    pass
        
        if lobby.id in lobby_manager.lobbies:
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


async def save_game_results(lobby: Lobby):
    """
    Сохраняет результаты завершенной игры (победа/поражение/выход) в БД,
    используя существующие CRUD-операции и create_model,
    используя UUID-строки для игроков и победителя.
    """
    if not lobby.game or not lobby.start_time or lobby.state != connectionstate.FINISHED:
        if lobby.state != connectionstate.FINISHED:
            print(f"Game {lobby.id} not in FINISHED state, skipping save_game_results.")
            return
        if not lobby.game or not lobby.start_time:
             print(f"Game {lobby.id} has no game/start_time, skipping save_game_results.")
             return

    async with db_control.session_factory() as session:
        try:
            # 1. Обновляем счетчики побед/поражений игроков
            for player_conn in lobby.players:
                current_user_id = str(player_conn.user.id)
                
                # Обновляем профиль игрока
                current_profile_wins = player_conn.user.profile.wins or 0
                current_profile_loses = player_conn.user.profile.loses or 0
                
                profile_update_data = {"profile": {}}

                if player_conn.symbol == lobby.winner_symbol:
                    profile_update_data["profile"]["wins"] = current_profile_wins + 1
                    print(f"Player {player_conn.user.username} wins incremented.")
                elif lobby.winner_symbol is not None: 
                    profile_update_data["profile"]["loses"] = current_profile_loses + 1
                    print(f"Player {player_conn.user.username} loses incremented.")
                
                if profile_update_data:

                    user_update_schema = AdminUserUpdateSchema.model_validate(profile_update_data)
                    
                    # ИСПОЛЬЗУЕМ user_update, как ты и сказал, что он работает с profile_ префиксами
                    await crud.user_update(session, current_user_id, user_update_schema)
                    print(f"Profile for {player_conn.user.username} updated via user_update.")
            
            # 2. Сохраняем запись о лобби
            if lobby.players and lobby.start_time:
                players_ids = [uuid.UUID(p.user.id) for p in lobby.players]
                
                winner_id = None
                if lobby.winner_symbol:
                    for p_conn in lobby.players:
                        if p_conn.symbol == lobby.winner_symbol:
                            winner_id = uuid.UUID(p_conn.user.id)
                            break

                game_duration = timedelta(seconds=0)
                if lobby.start_time and lobby.end_time:
                    game_duration = lobby.end_time - lobby.start_time

                lobby_data = {
                    "id": uuid.UUID(lobby.id),
                    "name": lobby.name,
                    "winner_id": winner_id, #pyright:ignore
                    "field": lobby.game.board if lobby.game and lobby.game.board else {},
                    "gametype": lobby.game_type,        
                    "gametime": game_duration,
                    "players": players_ids,           # player_ids[0] if len(player_ids) > 0 else None,          
                }
                
                # Динамически создаем Pydantic модель, соответствующую LobbySchema
                # (которая теперь использует строковые ID для игроков/победителя)
                
                lobby_add_schema = LobbySchema(**lobby_data)
                
                await crud.lobby_add(session, lobby_add_schema)
                print(f"Game results for lobby {lobby.id} saved to DB.")

            else:
                print(f"Lobby {lobby.id} has no players or start_time, skipping lobby record save.")

        except Exception as e:
            print(f"Error saving game results for lobby {lobby.id}: {e}")
            import traceback
            traceback.print_exc()