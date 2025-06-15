from typing import Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
)

class ProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str | None = None
    icon: str | None
    wins: int | None = 0
    loses: int | None = 0
    visibility: bool | None = True

    @field_validator("user_id", mode='before')
    def to_str(cls, value):
        if value:
            return str(value)

class ProfileUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    icon: str | None = None
    visibility: bool | None = None

class AdminProfileUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    icon: str | None = None
    wins: int | None = None
    loses: int | None = None
    visibility: bool | None = None