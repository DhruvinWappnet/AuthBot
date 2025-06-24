# Chat logic/AI integration
# app/services/message_service.py
from sqlalchemy.orm import Session
from app.models.chat import Message
from app.schemas.chat import MessageCreate

def save_message(db: Session, message: MessageCreate):
    db_message = Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message
