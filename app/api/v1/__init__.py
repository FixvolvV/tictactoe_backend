from fastapi import APIRouter

from .authentication.controller import router as auth_router
from .user.controller import router as user_router
from .lobby.controller import router as lobby_router
from .game.controller import router as game_router
from .general.controller import router as general_router
from core.config import settings

router = APIRouter(
    prefix=settings.api.v1.prefix,
)

router.include_router(router=auth_router, prefix="/authentication")
router.include_router(router=user_router, prefix="/user")
router.include_router(router=lobby_router, prefix="/lobby")
router.include_router(router=game_router, prefix="/game")
router.include_router(router=general_router, prefix="/general")