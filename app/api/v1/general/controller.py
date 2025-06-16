from typing import (
    Annotated
)
from fastapi import APIRouter
from fastapi.params import Depends
from fastapi.responses import (
    JSONResponse
)
from fastapi.security import HTTPBearer

from pydantic import BaseModel

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util.compat import importlib_metadata_get

from api.v1.validators import get_current_active_auth_user
from api.v1.logic.manager import lobby_manager

from api.v1.crud import (
    lobby_get_all
)

from core.schemes import (
    UserSchema,
    LobbiesSchema
)

from core.database import (
    db_control,
)

class Games(BaseModel):
    active: int
    total: int

http_bearer = HTTPBearer(auto_error=False)

# Init auth router
router = APIRouter(
    tags=["General"],
    dependencies=[Depends(http_bearer)]
)


@router.get(
    "/games",
    response_model=Games
)
async def get_all_games(
    verify: Annotated[
        UserSchema,
        Depends(get_current_active_auth_user)
    ],
    session: Annotated[
        AsyncSession,
        Depends(db_control.session_getter)
    ]
):

    active_games: int = len(lobby_manager.get_lobbies())
    total_games: int = len(LobbiesSchema.model_dump(await lobby_get_all(session=session, filters=None)))

    return Games(
        active=active_games,
        total=total_games
    )


#TODO Не забыть добавить metrics и patchs (Вообще впринципе сделать реализацию patchs)