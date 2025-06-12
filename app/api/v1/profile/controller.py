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



