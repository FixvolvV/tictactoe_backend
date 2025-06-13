from uuid import UUID
from typing import Annotated
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.responses import (
    Response,
    JSONResponse
)
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from pydantic import create_model

from api.v1.validation import get_current_active_auth_user

from core.schemes import (
    LobbySchema,
    LobbiesSchema,
    UserSchema
)

from core.database import (
    db_control,
)

from api.v1.crud import (
    lobby_add
)


# Create http bearer for auto documentation
http_bearer = HTTPBearer(auto_error=False)


# Init auth router
router = APIRouter(
    tags=["Lobby"],
    dependencies=[Depends(http_bearer)]
)


# Lobby POST ------<  plug
@router.post(
    "/create",
    response_class=JSONResponse
)
async def lobby_create(
    lobbyname: str,
    verify: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ]
):

    #TODO Link to Lobby Manager class

    return JSONResponse(
        content=f"The lobby was created successfully\n Lobby Name: {lobbyname}",
        status_code=status.HTTP_200_OK
    )


# Lobby GET(SSE) ------<  plug
@router.get(
    "/all/wait",
    response_class=JSONResponse # Expected Model LobbiesSchema
)
async def lobby_all_get(
    query_name: str,
    verify: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ]
):

    #TODO this route is SSE connection (Server Site Events). 
    # Now this route is plug. 
    
    #TODO Link to Lobby Manager class

    return JSONResponse(
        content="The lobby list" if query_name else f"The lobby list for {query_name} parametr",
        status_code=status.HTTP_200_OK
    )