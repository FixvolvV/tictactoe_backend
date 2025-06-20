from datetime import timedelta

from core.schemes import JWTCreateSchema

from core.utils import (
    encode_jwt,
)

from core.config import settings



TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_jwt(
    token_type: str,
    token_data: dict,
    expire_minutes: int = settings.jwt.access_token_expire_minutes,
    expire_timedelta: timedelta | None = None,
) -> str:
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(token_data)
    return encode_jwt(
        payload=jwt_payload,
        expire_minutes=expire_minutes,
        expire_timedelta=expire_timedelta,
    )


def create_access_token(user: JWTCreateSchema) -> str:
    jwt_payload = {
        # subject
        "sub": user.id,
        "username": user.username,
        "role": user.role
        # "logged_in_at"
    }
    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_minutes=settings.jwt.access_token_expire_minutes,
    )


def create_refresh_token(user: JWTCreateSchema) -> str:
    jwt_payload = {
        "sub": user.id,
        # "username": user.username,
    }
    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_timedelta=timedelta(days=settings.jwt.refresh_token_expire_days),
    )