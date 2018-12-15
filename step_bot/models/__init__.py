from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(UUID(as_uuid=True), primary_key=True)
    chat_id = Column(String, unique=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    current_target = Column(UUID, ForeignKey('targets.id'), nullable=True)


class Target(Base):
    __tablename__ = 'targets'

    id = Column(UUID, primary_key=True)
    chat = Column(UUID, ForeignKey('chats.id'))
    name = Column(String)
    date = Column(DateTime)
    taget_value = Column(Integer)
    current_value = Column(Integer)


class Step(Base):
    __tablename__ = 'steps'

    id = Column(UUID, primary_key=True)
    user_id = Column(String)
    target = Column(UUID, ForeignKey('targets.id'))
    date = Column(DateTime)
    steps = Column(Integer)
