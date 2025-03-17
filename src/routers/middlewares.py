from fastapi import Request
from fastapi.responses import JSONResponse

import re

import jwt
from jwt.exceptions import PyJWTError

from src.utils.config import settings

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.authentication import AuthenticationBackend, AuthCredentials, SimpleUser

from src.databaseM.methods.select_methods import get_user_by_id

from src.scemas.token_shemas import Token


CONF_JWT_DATA = Token.model_validate((settings.get_jwt_conf())) 

PATTERN_AUTH = r"^\/api\/auth(\/.*)?$"
PATTERN_GAME = r"^\/api\/game(\/.*)?$"
PUBLIC_ROUTES = ["/docs", "/redoc", "/openapi.json", "/api/get/global"]

#Создание класса MiddleWareJwt для проверки токенов каждый раз при взаимодействии с сайтом

class JWTAuthMiddleware(AuthenticationBackend):
    async def authenticate(self, conn):
        # Проверяем, является ли соединение WebSocket

        if conn.url.path in PUBLIC_ROUTES:
            return

        match = re.match(PATTERN_AUTH, conn.url.path)
        if match:
            return

        match = re.match(PATTERN_GAME, conn.url.path)
        if match:
            return

        auth_header = conn.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            conn.state.error = {"status_code": 403, "detail": "Missing Authorization header"}
            return None

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, CONF_JWT_DATA.token, algorithms=[CONF_JWT_DATA.token_type])
            user_id = payload.get("id")

            if not user_id:
                conn.state.error = {"status_code": 401, "detail": "Invalid token"}
                return None

            user_data = await get_user_by_id(id=user_id) #pyright:ignore
            return AuthCredentials(["authenticated"]), SimpleUser(str(user_data.id))

        except PyJWTError:
            conn.state.error = {"status_code": 401, "detail": "Invalid token"}
            return None


class JWTErrorHandlingMiddleware(BaseHTTPMiddleware):
    #Middleware для обработки ошибок аутентификации

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if hasattr(request.state, "error") and request.state.error:
            error = request.state.error
            return JSONResponse(status_code=error["status_code"], content={ "msg": error["detail"] })

        return response


