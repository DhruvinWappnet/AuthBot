# app/api/routes/chat.py
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from requests import Session
from app.schemas.chat import MessageCreate
from app.services.chat_service import save_message
from app.services.groq_service import get_groq_response
from app.db.database import get_db
from app.services.pdf_service import extract_text_from_pdf,chunk_text,get_top_k_chunks  # database session dependency
router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    session_id: str  # required to identify conversation

# @router.post("/query")
# def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
#     # Save user message
#     user_msg = MessageCreate(
#         sender="user",
#         content=request.question,
#         session_id=request.session_id
#     )
#     save_message(db, user_msg)

#     # Generate response
#     answer = get_groq_response(request.question)

#     # Save bot response
#     bot_msg = MessageCreate(
#         sender="bot",
#         content=answer,
#         session_id=request.session_id
#     )
#     save_message(db, bot_msg)

#     return {"answer": answer}

# # app/api/routes/chat.py

# @router.post("/pdf-query")
# async def chat_with_pdf(file: UploadFile = File(...), question: str = ""):
#     content = await file.read()
#     text = extract_text_from_pdf(content)
#     chunks = chunk_text(text)
#     top_chunks = get_top_k_chunks(chunks, question)
#     context = "\n".join(top_chunks)

#     prompt = f"Answer the following question using ONLY the context below:\n\n{context}\n\nQuestion: {question}\nAnswer:"
#     answer = get_groq_response(prompt)
#     return {"answer": answer}

@router.post("/query")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    # Block if someone mistakenly uses pdf session here
    if request.session_id.startswith("pdf_"):
        raise HTTPException(status_code=400, detail="This is a PDF chat session. Use /pdf-query instead.")

    # Save user message
    user_msg = MessageCreate(
        sender="user",
        content=request.question,
        session_id=request.session_id
    )
    save_message(db, user_msg)

    # Generate general response
    answer = get_groq_response(request.question)

    # Save bot response
    bot_msg = MessageCreate(
        sender="bot",
        content=answer,
        session_id=request.session_id
    )
    save_message(db, bot_msg)

    return {"answer": answer}

from fastapi import UploadFile, File, Form

@router.post("/pdf-query")
async def chat_with_pdf(file: UploadFile = File(...), question: str = Form(...)):
    # Read and extract text
    content = await file.read()
    text = extract_text_from_pdf(content)

    if not question.strip():
        return {"answer": "Please provide a question to answer from the PDF."}

    # Chunk and filter by relevance
    chunks = chunk_text(text)
    top_chunks = get_top_k_chunks(chunks, question)
    context = "\n".join(top_chunks)

    # Generate response using only context
    prompt = f"""Answer the following question using ONLY the context below:\n\n{context}\n\nQuestion: {question}\nAnswer:"""
    answer = get_groq_response(prompt)

    return {"answer": answer}
