from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(UUID(as_uuid=True), primary_key=True)
    chat_id = Column(String, unique=True)
    current_target_id = Column(UUID(as_uuid=True), nullable=True)
    date = Column(DateTime(timezone=True), server_default=func.now())

    current_target = relationship("Target", uselist=False, back_populates="chat")


class Target(Base):
    __tablename__ = 'targets'

    id = Column(UUID(as_uuid=True), primary_key=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey('chats.id'))
    name = Column(String)
    target_value = Column(Integer)
    current_value = Column(Integer, default=0)
    date_creation = Column(DateTime(timezone=True), server_default=func.now())
    date_edit = Column(DateTime(timezone=True), onupdate=func.now())

    chat = relationship("Chat", back_populates="current_target")
    steps = relationship("Step", back_populates="target")


class Step(Base):
    __tablename__ = 'steps'

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(String)
    target_id = Column(UUID(as_uuid=True), ForeignKey('targets.id'))
    date = Column(Date)
    steps = Column(Integer)
    date_creation = Column(DateTime(timezone=True), server_default=func.now())
    date_edit = Column(DateTime(timezone=True), onupdate=func.now())

    target = relationship("Target", back_populates="steps")
