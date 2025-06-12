from fastapi import APIRouter

from .authentication.controller import router as auth_router
from .user.controller import router as user_router
from core.config import settings

router = APIRouter(
    prefix=settings.api.v1.prefix,
)
router.include_router(router=auth_router, prefix="/authentication")
router.include_router(router=user_router, prefix="/user")