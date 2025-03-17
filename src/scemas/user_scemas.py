from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    username: str
    password: str
    games: Dict[str, int] = Field(default= {
        "total": 0,
        "wins": 0,
        "loses": 0
    })

    @field_validator("id", mode='before')
    def to_str(cls, value):
        if value:
            return str(value)

class UserOnlyDataAuth(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    username: str
    password: str

    @field_validator("id", mode='before')
    def to_str(cls, value):
        if value:
            return str(value)

class UserOnlyUP(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    password: str

    @field_validator('username')
    def username_validator(cls, value):
        str(value)
            
        if len(value) > 64:
            raise ValueError(f"Nickname to big. The nickname for the maximum length is 64")
        elif len(value) < 2:
            raise ValueError(f"Nickname to small. The nickname for the minimum length is 2")
        return value

    @field_validator('password')
    def password_validator(cls, value):
        str(value)  

        if len(value) > 64:
            raise ValueError(f"Password to big. The password for the maximum length is 64")
        elif len(value) < 6:
            raise ValueError(f"Password to small. The password for the minimum length is 6")
        return value

class UserOnlyUsername(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str

class Users(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: list[User]