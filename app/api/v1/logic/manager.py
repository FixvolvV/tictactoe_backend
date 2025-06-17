from typing import Dict, Optional, List, Any
from fastapi import WebSocket
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, ConfigDict
from fastapi import WebSocketDisconnect
# ИСПРАВЛЕНИЕ: Удаляем WebSocketCloseCode из импорта
from starlette.websockets import WebSocketState 

from .game_type import InfiniteTicTacToe

from core.utils import (
    connectionstate,
    gametype
) 

from core.schemes import (
    UserSchema,
    InitLobbySchema
)

class PlayerFrontendSchema(BaseModel):
    id: str
    username: str
    symbol: str
    isReady: bool
    wins: int | None

    model_config = ConfigDict(from_attributes=True)


class GameBoardCellSchema(BaseModel):
    x: int
    y: int
    symbol: str

    model_config = ConfigDict(from_attributes=True)


class PlayerConnection:
    def __init__(self, websocket: WebSocket, symbol: str, user_data: UserSchema, lobby_instance: 'Lobby'):
        self.websocket: WebSocket = websocket
        self.user: UserSchema = user_data
        self.symbol: str = symbol
        self.last_pong: datetime = datetime.now(timezone.utc)
        self.is_ready: bool = False
        self.lobby: 'Lobby' = lobby_instance

    def to_frontend_dict(self) -> Dict[str, Any]:
        wins_val = 0
        if hasattr(self.user, 'profile') and self.user.profile:
            wins_val = self.user.profile.wins

        return PlayerFrontendSchema(
            id=str(self.user.id),
            username=self.user.username,
            symbol=self.symbol,
            isReady=self.is_ready,
            wins=wins_val
        ).model_dump()


class Lobby:
    def __init__(self, lobby_id: str, name: str, game_type: gametype):
        self.id: str = lobby_id
        self.name: str = name
        self.owner_username: Optional[str] = None

        self.game_type: gametype = game_type
        self.players: List[PlayerConnection] = []
        self.state: connectionstate = connectionstate.WAITING

        self.game: Optional[InfiniteTicTacToe] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        self.last_move: Optional[Dict[str, Any]] = None
        self.win_line: List[Dict[str, int]] = []
        self.winner_symbol: Optional[str] = None

    def set_owner_if_not_set(self):
        if not self.owner_username and self.players:
            self.owner_username = self.players[0].user.username
            print(f"Lobby {self.id}: Owner set to {self.owner_username}")


    def start_game(self):
        self.game = InfiniteTicTacToe()
        self.start_time = datetime.now(timezone.utc)
        self.state = connectionstate.PLAYING

    def end_game(self, winner_symbol: Optional[str] = None):
        self.end_time = datetime.now(timezone.utc)
        self.state = connectionstate.FINISHED
        self.winner_symbol = winner_symbol

    def reset_game(self):
        self.game = None
        self.state = connectionstate.WAITING
        self.start_time = None
        self.end_time = None
        self.last_move = None
        self.win_line = []
        self.winner_symbol = None
        for p in self.players:
            p.is_ready = False

    def get_game_board_for_frontend(self) -> List[Dict[str, Any]]:
        if not self.game or not self.game.board:
            return []
        
        frontend_board = []
        for coord_str, symbol in self.game.board.items():
            x_str, y_str = coord_str.split(',')
            frontend_board.append(GameBoardCellSchema(x=int(x_str), y=int(y_str), symbol=symbol).model_dump())
        return frontend_board

    async def broadcast_state(self, event_type: str = "lobby_state_update", exclude_ws: Optional[WebSocket] = None):
        frontend_players = [p.to_frontend_dict() for p in self.players]
        
        base_message = {
            "event": event_type,
            "id": self.id,
            "name": self.name,
            "owner": self.owner_username,
            "gametype": self.game_type.value,
            "players": frontend_players,
            "state": self.state.value,
            "board_state": self.get_game_board_for_frontend(),
            "last_move": self.last_move,
            "win_line": self.win_line,
            "winner_symbol": self.winner_symbol,
            "current_turn_symbol": self.game.current_player if self.game else None,
        }

        for player_conn in self.players:
            if player_conn.websocket != exclude_ws and player_conn.websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await player_conn.websocket.send_json(base_message)
                except RuntimeError:
                    print(f"Failed to send broadcast to {player_conn.user.username} (likely already closed).")
                except Exception as e:
                    print(f"Error broadcasting to {player_conn.user.username}: {e}")

class LobbyManager:
    def __init__(self):
        self.lobbies: Dict[str, Lobby] = {}

    def create_lobby(self, lobby_name: str) -> str:
        new_id = str(uuid4())
        self.lobbies[new_id] = Lobby(new_id, lobby_name, gametype.INFINITY_TIC_TAC_TOE)
        return new_id

    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        return self.lobbies.get(lobby_id)

    def get_lobbies(self) -> Dict[str, Lobby]:
        return self.lobbies

    async def remove_lobby(self, lobby_id: str): # async def уже был, это хорошо
        if lobby_id in self.lobbies:
            lobby = self.lobbies[lobby_id]
            for p in list(lobby.players): 
                if p.websocket.client_state == WebSocketState.CONNECTED:
                    try:
                        # ИСПРАВЛЕНИЕ: Используем числовой код 1000
                        await p.websocket.close(code=1000) 
                        print(f"Closed lingering WS for {p.user.username} in lobby {lobby_id}.")
                    except RuntimeError:
                        pass
                try:
                    lobby.players.remove(p)
                except ValueError:
                    pass
            del self.lobbies[lobby_id]
            print(f"Lobby {lobby_id} completely removed.")

lobby_manager = LobbyManager()
