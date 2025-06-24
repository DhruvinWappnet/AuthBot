# Chat request/response schemas
# app/schemas/message.py
from pydantic import BaseModel
from datetime import datetime

class MessageCreate(BaseModel):
    sender: str
    content: str
    session_id: str

class MessageResponse(MessageCreate):
    timestamp: datetime
