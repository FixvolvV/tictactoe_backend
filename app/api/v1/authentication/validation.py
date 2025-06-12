from typing import Annotated
from fastapi import Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from pydantic import (
    create_model,
    BaseModel
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.schemes.user_schemes import LoginSchema, RegisterSchema
from api.v1.crud import (
    user_get_by_id,
    user_get,
    user_get_all
)

from .genjwt import (
    TOKEN_TYPE_FIELD,
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
)
from core.utils import (
    validate_password,
    decode_jwt
)
from core.database import db_control
from core.schemes import (
    UserSchema,
    UsersSchema
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/authentication/login/",
)


async def get_users_data(
    filters: BaseModel,
    session: AsyncSession
) -> bool:

    if UsersSchema.model_dump (
        await user_get_all (
            session=session,
            filters=filters
        )
    )['users']:
        return True
    return False


async def check_register_data(
    user: RegisterSchema,
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
) -> RegisterSchema:

    filters = create_model("", username=(str|None, None), email=(str|None, None))

    exception = HTTPException (
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this username or mail already exists"
        )

    #username check
    if await get_users_data(filters=filters(username=user.username), session=session):
        raise exception

    #email check
    if await get_users_data(filters=filters(email=user.email), session=session):
        raise exception

    return user

def get_current_token_payload(
    token: str = Depends(oauth2_scheme),
) -> dict:
    try:
        payload = decode_jwt(
            token=token,
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token error: {e}",
        )
    return payload


def validate_token_type(
    payload: dict,
    token_type: str,
) -> bool:
    current_token_type = payload.get(TOKEN_TYPE_FIELD)
    if current_token_type == token_type:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"invalid token type {current_token_type!r} expected {token_type!r}",
    )


async def get_user_by_token_sub(
    payload: dict,
    session: AsyncSession
) -> UserSchema:
    userid: str | None = payload.get("sub")
    if user := await user_get_by_id(session=session, userid=str(userid)):
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="token invalid (user not found)",
    )


class UserGetterFromToken:
    def __init__(self, token_type: str):
        self.token_type = token_type

    async def __call__(
        self,
        payload: dict = Depends(get_current_token_payload),
        session: AsyncSession = Depends(db_control.session_getter),
    ):
        validate_token_type(payload, self.token_type)
        return await get_user_by_token_sub(payload, session)


get_current_auth_user = UserGetterFromToken(ACCESS_TOKEN_TYPE)
get_current_auth_user_for_refresh = UserGetterFromToken(REFRESH_TOKEN_TYPE)


def get_current_active_auth_user(
    user: UserSchema = Depends(get_current_auth_user),
):
    if user.isActive:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="inactive user",
    )


async def validate_auth_user(
    userdata: LoginSchema,
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
) -> UserSchema:
    unauthed_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid username or password",
    )

    filters = create_model("username", username=(str, ...)); filters = filters(username=userdata.username)

    if not (user := await user_get(session=session, filters=filters)):
        raise unauthed_exc

    if not validate_password(
        password=userdata.password,
        hashed_password=user.password,
    ):
        raise unauthed_exc

    if not user.isActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user inactive",
        )

    return user