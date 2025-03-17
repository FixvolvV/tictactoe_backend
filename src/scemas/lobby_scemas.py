from pydantic import BaseModel, ConfigDict, field_validator, Field
from pydantic.types import UUID4
from src.utils.enums import lobbystage, winners


class Lobby(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lobbyname: str
    players: dict[str, str] = Field(default={
        "player1": "",
        "player2": ""
    })
    stage: lobbystage = Field(default=lobbystage.WAITING)
    winner: winners = Field(default=winners.NODEFINED)

    @field_validator('lobbyname')
    def username_validator(cls, value):
        str(value)
            
        if len(value) > 64:
            raise ValueError(f"Lobby Name to big. The nickname for the maximum length is 64")
        elif len(value) < 2:
            raise ValueError(f"Lobby Name to small. The nickname for the minimum length is 2")
        return value

class LobbyWithId(Lobby):
    model_config = ConfigDict(from_attributes=True)

    id: str

    @field_validator("id", mode='before')
    def to_str(cls, value):
        return str(value)

class LobbyOnlyId(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str

    @field_validator("id", mode='before')
    def to_str(cls, value):
        return str(value)

class Lobbies(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lobbylist: list[LobbyWithId | None]