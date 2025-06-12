from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from .profile import Profile


class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    role: Mapped[roles] = mapped_column(default=roles.USER, server_default=text("'USER'"))
    isActive: Mapped[bool] = mapped_column(default=True, server_default=text("'True'"))
    time_create: Mapped[datetime] = mapped_column(server_default=func.now())

    profile: Mapped["Profile"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="joined"
    )