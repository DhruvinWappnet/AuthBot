# Chat message model
# app/models/message.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, nullable=False)  # "user" or "bot"
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, index=True)  # Optional: to track conversations per user
