from typing import Annotated
from fastapi import APIRouter, Request
from fastapi.params import Depends
from fastapi.security import HTTPBearer
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

# Token Model 
class TokenInfo(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "Bearer"


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
    ]
):
    
    userdata.password = hash_password(userdata.password).decode()

    userid: str = await user_add(session=session, userdata=userdata)
    
    user: UserSchema = UserSchema.model_validate(
        await user_get_by_id(session=session, userid=userid)
    ) 

    access_token = create_access_token(JWTCreateSchema.model_validate(user))
    refresh_token = create_refresh_token(JWTCreateSchema.model_validate(user))

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
    ]
):
    access_token = create_access_token(JWTCreateSchema.model_validate(user))
    refresh_token = create_refresh_token(JWTCreateSchema.model_validate(user))
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
    ]
):
    access_token = create_access_token(JWTCreateSchema.model_validate(user))
    return TokenInfo(
        access_token=access_token,
    )