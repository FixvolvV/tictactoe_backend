import uuid
from datetime import datetime

from typing import (
    List,
    Dict,
    Any
)

from sqlalchemy import (
    ARRAY,
    UUID,
    String,
    text,
    func,
    JSON,
) 

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .base import Base
from core.utils import (
    lobbystage,
    gametype
)

class Lobby(Base):
    __tablename__ = 'lobbies'

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    players: Mapped[list[str]] = mapped_column(ARRAY(String))
    field: Mapped[dict] = mapped_column(JSON)
    gametype: Mapped[gametype]
    state: Mapped[lobbystage] = mapped_column(default=lobbystage.COMPLETED, server_default=text("'COMPLETED'"))
    time_create: Mapped[datetime] = mapped_column(default=func.now())
