from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.dialects.postgresql import UUID

from .base import Base

metadata = MetaData()

user_lobby_association = Table(
    'user_lobby_association',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('lobby_id', UUID(as_uuid=True), ForeignKey('lobbies.id'), primary_key=True)
)