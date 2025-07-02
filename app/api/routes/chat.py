# app/api/routes/chat.py
import time
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from requests import Session
from app.core.auth import get_current_user_token
from app.prompt import email_prompt
from app.schemas.chat import MessageCreate
from app.services.chat_service import save_message
from app.services.groq_service import get_groq_response
from app.db.database import get_db
from fastapi import UploadFile, File, Form
from app.models.token_usage import TokenUsage
from app.services.pdf_service import extract_text_from_pdf,chunk_text,get_top_k_chunks  # database session dependency
from sentence_transformers import SentenceTransformer
from app.core.pinecone_setup import index

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    session_id: str  # required to identify conversation


@router.post("/query")
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_token)
):
    if request.session_id.startswith("pdf_"):
        raise HTTPException(status_code=400, detail="This is a PDF chat session. Use /pdf-query instead.")
    
    api_start = time.time()

    # Save user message
    user_msg = MessageCreate(
        sender="user",
        content=request.question,
        session_id=request.session_id
    )
    save_message(db, user_msg)

    # Get answer from Groq
    groq_start = time.time()
    answer, token_usage = get_groq_response(request.question)
    groq_duration = time.time() - groq_start

    # Save bot message
    bot_msg = MessageCreate(
        sender="bot",
        content=answer,
        session_id=request.session_id
    )
    save_message(db, bot_msg)

    model_used = token_usage.get("model", "unknown") if token_usage else "unknown"
    cost = token_usage.get("cost", 0.0) if token_usage else 0.0

    api_duration = time.time() - api_start  # ✅ must happen before using it

    # Save token usage
    if token_usage:
        usage_record = TokenUsage(
            user_email=current_user.email,
            session_id=request.session_id,
            prompt_tokens=token_usage["prompt_tokens"],
            completion_tokens=token_usage["completion_tokens"],
            total_tokens=token_usage["total_tokens"],
            message=request.question,
            model=model_used,
            cost=cost,
            groq_duration=round(groq_duration, 4),
            api_duration=round(api_duration, 4),
        )
        db.add(usage_record)
        db.commit()

    return {
        "answer": answer,
        "token_usage": token_usage,
        "groq_duration": round(groq_duration, 4),
        "api_duration": round(api_duration, 4),
        "model": model_used,
        "cost": round(cost, 6),
    }

#==================UPDATED=====================
@router.post("/pdf-query")
async def chat_with_pdf(
    file: UploadFile = File(...),
    question: str = Form(...),
    session_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_token)
):
    # Validate input
    if not question.strip():
        return {"answer": "Please provide a question to answer from the PDF."}

    # Read and extract PDF content
    content = await file.read()
    text = extract_text_from_pdf(content)

    # Chunk and select relevant parts
    chunks = chunk_text(text)
    top_chunks = get_top_k_chunks(chunks, question)
    context = "\n".join(top_chunks)

    # Compose the prompt for Groq
    prompt = f"""Answer the following question using ONLY the context below:\n\n{context}\n\nQuestion: {question}\nAnswer:"""

    # Get Groq response and token usage
    answer, token_usage = get_groq_response(prompt)

    # ✅ Save user message
    user_msg = MessageCreate(
        sender="user",
        content=f"[PDF Q] {question}",
        session_id=session_id
    )
    save_message(db, user_msg)

    # ✅ Save bot message
    bot_msg = MessageCreate(
        sender="bot",
        content=answer,
        session_id=session_id
    )
    save_message(db, bot_msg)

    # ✅ Store token usage
    if token_usage:
        usage_record = TokenUsage(
            user_email=current_user.email,
            session_id=session_id,
            prompt_tokens=token_usage["prompt_tokens"],
            completion_tokens=token_usage["completion_tokens"],
            total_tokens=token_usage["total_tokens"],
            message=question
        )
        db.add(usage_record)
        db.commit()

    # ✅ Return response and usage
    return {
        "answer": answer,
        "token_usage": token_usage
    }



# =======================================
model = SentenceTransformer("aspire/acge_text_embedding")

@router.post("/query-email")
def query_email_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_token)
):
    user_id = current_user.email
    question = request.question
    session_id = request.session_id

    if not question.strip():
        raise HTTPException(status_code=400, detail="Please provide a valid question.")

    # ✅ Embed the user question
    query_embedding = model.encode([question])[0].tolist()

    # ✅ Query Pinecone
    pinecone_response = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True,
        filter={"user_id": {"$eq": user_id}}
    )

    matches = pinecone_response.get("matches", [])
    if not matches:
        answer = "Sorry, I couldn't find any emails related to your question."
        save_message(db, MessageCreate(sender="user", content=question, session_id=session_id))
        save_message(db, MessageCreate(sender="bot", content=answer, session_id=session_id))
        return {"answer": answer, "token_usage": None}

    # ✅ Build context from top email matches
    context = "\n".join([f"- {match['metadata']['text']}" for match in matches])

    # ✅ Ask LLM
    prompt = email_prompt.email_prompts(context=context,question=question)
    answer, token_usage = get_groq_response(prompt)

    # ✅ Save messages
    save_message(db, MessageCreate(sender="user", content=question, session_id=session_id))
    save_message(db, MessageCreate(sender="bot", content=answer, session_id=session_id))

    # ✅ Store token usage
    if token_usage:
        usage_record = TokenUsage(
            user_email=user_id,
            session_id=session_id,
            prompt_tokens=token_usage["prompt_tokens"],
            completion_tokens=token_usage["completion_tokens"],
            total_tokens=token_usage["total_tokens"],
            message=question
        )
        db.add(usage_record)
        db.commit()

    return {
        "answer": answer,
        "token_usage": token_usage
    }
