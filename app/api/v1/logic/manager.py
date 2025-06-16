from typing import Dict, Optional
from fastapi import WebSocket
from uuid import uuid4
from datetime import datetime, timezone

from .game_type import InfiniteTicTacToe

from core.utils import (
    connectionstate,
    gametype
) 

from core.schemes import (
    UserSchema,
    InitLobbySchema
)


class PlayerConnection:
    def __init__(self, websocket: WebSocket, symbol: str, user_data: UserSchema):
        self.websocket = websocket
        self.user = user_data
        self.symbol = symbol
        self.last_pong: datetime = datetime.now(timezone.utc)
        self.is_ready = False

class Lobby:
    def __init__(self, lobby_data: InitLobbySchema):
        self.state: connectionstate = connectionstate.WAITING
        self.lobby_data = lobby_data
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

        self.game: InfiniteTicTacToe

    def start_game(self):
        self.game = InfiniteTicTacToe()
        self.start_time = datetime.now(timezone.utc)
        self.state = connectionstate.PLAYING

    def end_game(self):
        self.end_time = datetime.now(timezone.utc)
        self.state = connectionstate.FINISHED

    def duration(self):
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

class LobbyManager:
    def __init__(self):
        self.lobbies: Dict[str, Lobby] = {}

    def create_lobby(self, lobby_name) -> str:
        lobby = InitLobbySchema(id=str(uuid4()), name=lobby_name, gametype=gametype.INFINITY_TIC_TAC_TOE)
        self.lobbies[lobby.id] = Lobby(lobby)
        return lobby.id

    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        return self.lobbies.get(lobby_id)

    def get_lobbies(self) -> Dict[str, Lobby]:
        return self.lobbies

    def remove_lobby(self, lobby_id: str):
        if lobby_id in self.lobbies:
            del self.lobbies[lobby_id]


lobby_manager = LobbyManager()