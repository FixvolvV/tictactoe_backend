from typing import (
    TYPE_CHECKING,
    Optional,
    List
)

import uuid
from datetime import datetime

from sqlalchemy import (
    UUID,
    text,
    func,
) 

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base
from core.utils.enums import roles
from .association import user_lobby_association

if TYPE_CHECKING:
    from .profile import Profile
    from .lobby import Lobby


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[roles] = mapped_column(default=roles.USER, server_default=text("'USER'"))
    isActive: Mapped[bool] = mapped_column(default=True, server_default=text("'True'"))
    time_create: Mapped[datetime] = mapped_column(server_default=func.now())

    profile: Mapped[Optional["Profile"]] = relationship( # Добавил Optional для профиля, если он может быть пустым
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="joined"
    )

    lobbies: Mapped[List["Lobby"]] = relationship(
        secondary=user_lobby_association,
        back_populates="players"
    )

    won_lobbies: Mapped[List["Lobby"]] = relationship(
        back_populates="winner_user",
        foreign_keys="[Lobby.winner_id]"
    )