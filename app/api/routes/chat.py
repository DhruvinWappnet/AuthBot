# app/api/routes/chat.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from requests import Session
from app.schemas.chat import MessageCreate
from app.services.chat_service import save_message
from app.services.groq_service import get_groq_response
from app.db.database import get_db  # database session dependency
router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    session_id: str  # required to identify conversation

@router.post("/query")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # Save user message
    user_msg = MessageCreate(
        sender="user",
        content=request.question,
        session_id=request.session_id
    )
    save_message(db, user_msg)

    # Generate response
    answer = get_groq_response(request.question)

    # Save bot response
    bot_msg = MessageCreate(
        sender="bot",
        content=answer,
        session_id=request.session_id
    )
    save_message(db, bot_msg)

    return {"answer": answer}
