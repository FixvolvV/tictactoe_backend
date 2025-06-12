from datetime import datetime
from typing import (
    List,
    Dict,
) 

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)

from core.utils import (
    lobbystage,
    gametype
)


class LobbySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    players: List[str]
    field: Dict[str, str]
    gametype: gametype
    state: lobbystage
    time_create: datetime

    @field_validator("id", mode='before')
    def to_str(cls, value):
        if value:
            return str(value)

class LobbiesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lobbies: list[LobbySchema | None]

class InitLobbySchema(BaseModel):

    name: str
    players: List[str]
    gametype: gametype

    @field_validator('name')
    def username_validator(cls, value):
        if len(value) > 40:
            raise ValueError("Lobby Name to big. The nickname for the maximum length is 64")
        elif len(value) < 2:
            raise ValueError("Lobby Name to small. The nickname for the minimum length is 2")
        return value