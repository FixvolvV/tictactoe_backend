from sqlalchemy import JSON, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.databaseM.database import Base
from src.utils.enums import lobbystage, winners


class User(Base):
    __tablename__ = 'users'

    username: Mapped[str]
    password: Mapped[str]
    games: Mapped[dict | None] = mapped_column(JSON)


class Lobby(Base):
    __tablename__ = 'lobbies'

    lobbyname: Mapped[str]
    players: Mapped[dict | None] = mapped_column(JSON)
    stage: Mapped[lobbystage] = mapped_column(default=lobbystage.WAITING, server_default=text("'WAITING'"))
    winner: Mapped[winners | None] = mapped_column(default=winners.NODEFINED, server_default=text("'NODEFINED'"))


class Patch(Base):
    __tablename__ = 'patches'

    number: Mapped[str]
    info: Mapped[str | None]




