from typing import TYPE_CHECKING

from sqlalchemy import (
    UUID,
    ForeignKey,
) 

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base

if TYPE_CHECKING:
    from .user import User

class Profile(Base):
    __tablename__ = 'profiles'

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True
    )
    icon: Mapped[str | None] # если image = файл, обычно хранят путь или бинарные данные
    wins: Mapped[int] = mapped_column(default=0)
    loses: Mapped[int] = mapped_column(default=0)
    visibility: Mapped[bool] = mapped_column(default=True)

    # Обратная сторона связи
    user: Mapped["User"] = relationship("User", back_populates="profile")

    