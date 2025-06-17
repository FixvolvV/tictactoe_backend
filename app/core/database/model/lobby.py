import uuid

from typing import (
    TYPE_CHECKING,
    Optional,
    List
)

from datetime import datetime


from sqlalchemy import (
    UUID,
    func,
    JSON,
    ForeignKey,
) 

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from .base import Base
from core.utils import (
    gametype
)

from .association import user_lobby_association

if TYPE_CHECKING:
    from .user import User

class Lobby(Base):
    __tablename__ = 'lobbies'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    
    winner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    winner_user: Mapped[Optional["User"]] = relationship(
        back_populates="won_lobbies",
        foreign_keys=[winner_id],
        lazy="joined"
    )

    field: Mapped[dict] = mapped_column(JSON)
    gametype: Mapped[gametype]
    gametime: Mapped[str]
    time_create: Mapped[datetime] = mapped_column(default=func.now())

    players: Mapped[List["User"]] = relationship(
        secondary=user_lobby_association,
        back_populates="lobbies",
        lazy="joined"
    )
