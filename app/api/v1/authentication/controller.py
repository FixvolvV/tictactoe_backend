from typing import Annotated
from fastapi import APIRouter, Request, Response
from fastapi.params import Depends
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from api.v1.authentication.genjwt import (
    create_access_token,
    create_refresh_token,
)

from api.v1.validators import(
    validate_auth_user,
    get_current_auth_user_for_refresh,
    check_recurring_data
) 

from core.schemes import (
    RegisterSchema,
    JWTCreateSchema,
    UserSchema,
)

from core.database import (
    db_control,
)

from core.config import (
    settings
)

from api.v1.crud import (
    user_add,
    user_get_by_id
)

from core.utils import (
    hash_password
)

"""
Роутер который отвечает на все попытки аутентификации и авторизации на сайте
"""

# Create http bearer for auto documentation
http_bearer = HTTPBearer(auto_error=False)
oauth2_scheme_refresh = OAuth2PasswordBearer(tokenUrl="authentication/refresh")


# Token Model 
class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    # Указываем корневой домен с точкой в начале
    COOKIE_DOMAIN = ".fixvolvv.ru" # <<< ИЗМЕНЕНО ДЛЯ ПОДДОМЕНОВ!

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.jwt.access_token_expire_minutes, # 1 hour for access token
        path="/",
        domain=COOKIE_DOMAIN # Используем корневой домен
    )
    
    response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.jwt.refresh_token_expire_days, # 7 days for refresh token
            path="/",
            domain=COOKIE_DOMAIN # Используем корневой домен
        )

# Helper to clear cookies
def clear_auth_cookies(response: Response):
    COOKIE_DOMAIN = ".fixvolvv.ru" # <<< ИЗМЕНЕНО ДЛЯ ПОДДОМЕНОВ!
    response.delete_cookie(key="access_token", domain=COOKIE_DOMAIN)
    response.delete_cookie(key="refresh_token", domain=COOKIE_DOMAIN)


# Init auth router
router = APIRouter(
    tags=["Authentication"],
    dependencies=[Depends(http_bearer)]
)


# Register POST ------<
@router.post(
    '/register',
    response_model=TokenInfo
)
async def get_register_data(
    userdata: Annotated[
        RegisterSchema,
        Depends(check_recurring_data)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ],
    response: Response
):
    
    userdata.password = hash_password(userdata.password).decode()

    userid: str = await user_add(session=session, userdata=userdata)
    
    user: UserSchema = UserSchema.model_validate(
        await user_get_by_id(session=session, userid=userid)
    ) 

    access_token = create_access_token(JWTCreateSchema.model_validate(user))
    refresh_token = create_refresh_token(JWTCreateSchema.model_validate(user))

    set_auth_cookies(response, access_token, refresh_token) 

    return TokenInfo (
        access_token=access_token,
        refresh_token=refresh_token,
    )


# Login POST ------<
@router.post(
    '/login',
    response_model=TokenInfo
)
async def get_login_data(
    user: Annotated[
        UserSchema,
        Depends(validate_auth_user)
    ],
    response: Response
):
    access_token = create_access_token(JWTCreateSchema.model_validate(user))
    refresh_token = create_refresh_token(JWTCreateSchema.model_validate(user))

    set_auth_cookies(response, access_token, refresh_token) 

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# Refresh POST ------<
@router.post(
    '/refresh',
    response_model=TokenInfo,
    response_model_exclude_none=True
)
async def refresh_token(
    user: Annotated[
        UserSchema,
        Depends(get_current_auth_user_for_refresh)
    ],
    response: Response
):
    access_token = create_access_token(JWTCreateSchema.model_validate(user))
    refresh_token = create_refresh_token(JWTCreateSchema.model_validate(user))

    set_auth_cookies(response, access_token, refresh_token) 

    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post('/logout')
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}