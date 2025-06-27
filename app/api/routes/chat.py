# app/api/routes/chat.py
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

#=================PREVIOUS WORKING=======================================#
# @router.post("/query")
# def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
#     # Block if someone mistakenly uses pdf session here
#     if request.session_id.startswith("pdf_"):
#         raise HTTPException(status_code=400, detail="This is a PDF chat session. Use /pdf-query instead.")

#     # Save user message
#     user_msg = MessageCreate(
#         sender="user",
#         content=request.question,
#         session_id=request.session_id
#     )
#     save_message(db, user_msg)

#     # Generate general response
#     answer = get_groq_response(request.question)

#     # Save bot response
#     bot_msg = MessageCreate(
#         sender="bot",
#         content=answer,
#         session_id=request.session_id
#     )
#     save_message(db, bot_msg)

#     return {"answer": answer}

#========================================================================#

#============UPDATION=================#

@router.post("/query")
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_token)  # ✅ Get user email
):
    if request.session_id.startswith("pdf_"):
        raise HTTPException(status_code=400, detail="This is a PDF chat session. Use /pdf-query instead.")

    # ✅ Save user message
    user_msg = MessageCreate(
        sender="user",
        content=request.question,
        session_id=request.session_id
    )
    save_message(db, user_msg)

    # ✅ Get answer + token usage
    answer, token_usage = get_groq_response(request.question)

    # ✅ Save bot response
    bot_msg = MessageCreate(
        sender="bot",
        content=answer,
        session_id=request.session_id
    )
    save_message(db, bot_msg)

    # ✅ Log token usage in DB
    if token_usage:
        usage_record = TokenUsage(
            user_email=current_user.email,
            session_id=request.session_id,
            prompt_tokens=token_usage["prompt_tokens"],
            completion_tokens=token_usage["completion_tokens"],
            total_tokens=token_usage["total_tokens"],
            message=request.question
        )
        db.add(usage_record)
        db.commit()

    return {
        "answer": answer,
        "token_usage": token_usage
    }
#==================PREVIOUS WORKING=======================#

# @router.post("/pdf-query")
# async def chat_with_pdf(file: UploadFile = File(...), question: str = Form(...)):
#     # Read and extract text
#     content = await file.read()
#     text = extract_text_from_pdf(content)

#     if not question.strip():
#         return {"answer": "Please provide a question to answer from the PDF."}

#     # Chunk and filter by relevance
#     chunks = chunk_text(text)
#     top_chunks = get_top_k_chunks(chunks, question)
#     context = "\n".join(top_chunks)

#     # Generate response using only context
#     prompt = f"""Answer the following question using ONLY the context below:\n\n{context}\n\nQuestion: {question}\nAnswer:"""
#     answer = get_groq_response(prompt)

#     return {"answer": answer}
#========================================================

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
router = APIRouter()
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
