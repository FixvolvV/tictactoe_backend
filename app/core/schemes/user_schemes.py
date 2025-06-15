from datetime import datetime, timezone
from fastapi import WebSocket
from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator
)

from core.utils import roles
from .profile_schemes import (
    ProfileSchema,
    ProfileUpdateSchema,
    AdminProfileUpdateSchema
)

class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    password: str
    email: str
    isActive: bool
    role: roles
    time_create: datetime
    profile: ProfileSchema

    @field_validator("id", mode='before')
    def to_str(cls, value):
        if value:
            return str(value)

class UsersSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    users: list[UserSchema]


class RegisterSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password: str
    email: str

    @field_validator('username')
    def username_validator(cls, value):
            
        if len(value) > 64:
            raise ValueError("Nickname to big. The nickname for the maximum length is 64")
        elif len(value) < 2:
            raise ValueError("Nickname to small. The nickname for the minimum length is 2")
        return value

    @field_validator('password')
    def password_validator(cls, value):

        if len(value) > 64:
            raise ValueError("Password to big. The password for the maximum length is 64")
        elif len(value) < 6:
            raise ValueError("Password to small. The password for the minimum length is 6")
        return value

class LoginSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password: str

class JWTCreateSchema(LoginSchema):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: roles

    @field_validator("id", mode='before')
    def to_str(cls, value):
        if value:
            return str(value)

class UserUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str | None = None
    password: str | None = None
    email: str | None = None
    profile: ProfileUpdateSchema | None = None

class AdminUserUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str | None = None
    password: str | None = None
    email: str | None = None
    isActive: bool | None = None
    role: roles | None = None 
    time_create: datetime | None = None
    profile: AdminProfileUpdateSchema | None = None

