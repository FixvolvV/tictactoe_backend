from typing import Annotated
from fastapi import (
    Depends,
    HTTPException,
    WebSocket,
)
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from .validhttp import (
    get_current_token_payload,
    validate_token_type,
    get_user_by_token_sub,
)

from core.database import db_control
from core.schemes import UserSchema
from api.v1.authentication.genjwt import ACCESS_TOKEN_TYPE, REFRESH_TOKEN_TYPE


WEBSOCKET_ACCESS_TOKEN_COOKIE_NAME = "token"

async def get_websocket_token_from_cookie(
    websocket: WebSocket,
    token_cookie_name: str = WEBSOCKET_ACCESS_TOKEN_COOKIE_NAME
) -> str:
    token = websocket.cookies.get(token_cookie_name)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing access token cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token cookie",
        )
    return token

class WebSocketUserGetter:
    def __init__(self, token_type: str):
        self.token_type = token_type

    async def __call__(
        self,
        websocket: WebSocket,
        token: Annotated[
            str,
            Depends(get_websocket_token_from_cookie)
        ],
        session: Annotated[
            AsyncSession,
            Depends(db_control.session_getter)
        ],
    ) -> UserSchema:
        try:
            payload = get_current_token_payload(token)
            validate_token_type(payload, self.token_type)
            user = await get_user_by_token_sub(payload, session)
            return user

        except HTTPException as e:

            ws_close_code = status.WS_1008_POLICY_VIOLATION

            await websocket.close(code=ws_close_code, reason=e.detail)
            raise e


get_current_auth_user_ws = WebSocketUserGetter(ACCESS_TOKEN_TYPE)
get_current_auth_user_for_refresh_ws = WebSocketUserGetter(REFRESH_TOKEN_TYPE)

async def get_current_active_auth_user_ws(
    websocket: WebSocket,
    user: Annotated[
        UserSchema,
        Depends(get_current_auth_user_ws)
    ],
) -> UserSchema:

    if user.isActive:
        return user
    
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Inactive user")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Inactive user",
    )