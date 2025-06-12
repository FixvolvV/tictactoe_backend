from typing import Annotated
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.authentication.validation import get_current_active_auth_user
from core.schemes import (
    UserSchema,
    UserUpdateSchema
)

from core.database import (
    db_control,
)

from api.v1.crud import (
    user_delete,
    user_get_by_id,
    user_update
)

from core.utils import (
    hash_password
)


# Create http bearer for auto documentation
http_bearer = HTTPBearer(auto_error=False)


# Init auth router
router = APIRouter(
    tags=["User"],
    dependencies=[Depends(http_bearer)]
)


# User GET ------<
@router.get(
    "/",
    response_model=UserSchema
)
async def user_get(
    user: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ]
):
    return user


# User PATCH ------<
@router.patch(
    "/",
    response_model=UserSchema
)
async def user_updated(

    update: UserUpdateSchema,
    user: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
):
    
    if update.password:
        update.password = hash_password(update.password).decode()

    await user_update(session=session, userid=user.id, update_data=update)

    return await user_get_by_id(session=session, userid=user.id) 


# User DELETE ------<
@router.delete(
    "/",
    response_class=JSONResponse
)
async def user_deleted(
    user: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
):

    await user_delete(session=session, userid=user.id)
    return JSONResponse(
        status_code=200,
        content="User successfully deleted"
    )

