from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from fastapi.responses import (
    Response,
    JSONResponse
)
from fastapi.security import HTTPBearer
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from pydantic import BaseModel, create_model

from api.v1.validators import(
    get_current_active_auth_user
) 

from core.schemes import (
    UserSchema,
    UsersSchema,
    UserChangePass,
    UserUpdateSchema
)

from core.database import (
    db_control,
)

from api.v1.crud import (
    user_delete,
    user_get_all,
    user_get_by_id,
    user_update
)

from core.utils import (
    hash_password,
    validate_password
)


#TODO Add endpoints for Admin. Update endpoints for Admin usability 


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


# User/All GET ------<
@router.get(
    "/all",
    response_model=UsersSchema
)
async def user_all_get(
    verify: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
):

    filters = create_model("", profile_visibility=(bool, ...)); filters = filters(profile_visibility=True)

    users = await user_get_all(session=session, filters=filters)

    return users


# User{id} GET ------<
@router.get(
    "/{id}",
    response_model=UserSchema
)
async def user_get_id(
    id: UUID,
    verify: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
):

    no_content_response = Response(
        status_code=status.HTTP_204_NO_CONTENT
    )

    user = await user_get_by_id(session=session, userid=str(id))

    if not user:
        return no_content_response

    if not user.profile.visibility:
        return no_content_response

    user = user.model_copy(update={"password": "", "email": ""})

    return user

@router.post(
    "/change_password",
    response_model=UserSchema
)
async def user_change_password(
    data: UserChangePass,
    user: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
):

    if not validate_password(password=data.old_password, hashed_password=user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong Password"
        )

    update = create_model("", password=(str, ...)); update = update(password=hash_password(data.new_password).decode())

    await user_update(session=session, userid=user.id, update_data=update)

    return await user_get_by_id(session=session, userid=user.id) 

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

    await user_update(session=session, userid=user.id, update_data=update)

    return await user_get_by_id(session=session, userid=user.id) 


# User DELETE ------<
@router.delete(
    "/",
    response_class=JSONResponse
)
async def user_deleted(
    password: str,
    user: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
):

    if not validate_password(password=password, hashed_password=user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong Password"
        )

    await user_delete(session=session, userid=user.id)
    return JSONResponse(
        status_code=200,
        content="User successfully deleted"
    )

