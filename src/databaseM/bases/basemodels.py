from src.databaseM.bases.base import BaseDatabaseMethods
from src.databaseM.model.models import User, Lobby, Patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


class UserBDM(BaseDatabaseMethods[User]):
    model = User

class LobbyBDM(BaseDatabaseMethods[Lobby]):
    model = Lobby


class PatchBDM(BaseDatabaseMethods[Patch]):
    model = Patch

