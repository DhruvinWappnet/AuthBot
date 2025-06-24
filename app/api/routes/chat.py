# app/api/routes/chat.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.groq_service import get_groq_response

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/query")
def chat_endpoint(request: ChatRequest):
    answer = get_groq_response(request.question)
    return {"answer": answer}
