import uuid
from datetime import (
    datetime,
    time,
    timedelta,
    timezone
)
from typing import (
    Any,
    List,
    Dict,
) 

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)

from core.schemes.user_schemes import UserSchema
from core.utils import (
    gametype,
    connectionstate
)


class LobbySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    winner_id: uuid.UUID
    field: Dict[str, str]
    gametype: gametype
    gametime: str
    timecreate: datetime | None = None
    players: List[UserSchema | uuid.UUID] # <-- Список UUID-ов игроков
    
    @field_validator("gametime", mode="before")
    def parse_duration(cls, v: timedelta) -> str:
        if isinstance(v, str): # Если приходит уже строка, ничего не делаем
            return v
        total_seconds = int(v.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

class LobbiesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lobbies: list[LobbySchema]

class InitLobbySchema(BaseModel):

    id: str
    name: str
    players: List[Any] = []
    field: Dict[str, str] = {}
    gametype: gametype 

    @field_validator('name')
    def username_validator(cls, value):
        if len(value) > 40:
            raise ValueError("Lobby Name to big. The nickname for the maximum length is 64")
        elif len(value) < 2:
            raise ValueError("Lobby Name to small. The nickname for the minimum length is 2")
        return value


