from fastapi import APIRouter, Depends, HTTPException
from google_auth_oauthlib.flow import InstalledAppFlow
from app.core.auth import get_current_user_token
from app.db.database import SessionLocal
from app.models.user import User
import os, json

from app.services.groq_service import search_similar_emails
from app.services.llm_tools import summarize_email

router = APIRouter()
CREDENTIALS_FILE = "credential/google_oauth_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

@router.get("/connect-gmail")
def connect_gmail(current_user: User = Depends(get_current_user_token)):
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)  # Opens browser to login to Gmail

    # Save token to DB
    db = SessionLocal()
    db_user = db.query(User).filter(User.id == current_user.id).first()
    db_user.gmail_token = json.loads(creds.to_json())  # Store dict format
    db.commit()
    return {"message": "Gmail connected successfully"}

@router.get("/connect-gmail-dev")
def connect_gmail_dev(email: str):
    from app.db.database import SessionLocal
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    user.gmail_token = json.loads(creds.to_json())
    db.commit()

    return {"message": "Gmail connected successfully for dev user"}

from app.services.email_embedding_service import embed_and_store_emails

# @router.get("/connect-gmail-dev")
# def connect_gmail_dev(email: str):
#     db = SessionLocal()
#     user = db.query(User).filter(User.email == email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
#     creds = flow.run_local_server(port=0)

#     token_dict = json.loads(creds.to_json())
#     user.gmail_token = token_dict
#     db.commit()

#     # 📩 Fetch & embed last 10 days of emails
#     embed_and_store_emails(user_id=str(user.id), gmail_token=token_dict)

#     return {"message": "Gmail connected & emails embedded"}


@router.post("/embed")
def embed_user_emails(current_user=Depends(get_current_user_token)):
    if not current_user.gmail_token:
        raise HTTPException(status_code=400, detail="Gmail not connected.")
    try:
        embed_and_store_emails(user_id=str(current_user.id), gmail_token=current_user.gmail_token)
        return {"message": "Embeddings stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search-emails")
def search_emails_by_query(query: str, current_user=Depends(get_current_user_token)):
    if not current_user.gmail_token:
        raise HTTPException(status_code=400, detail="Gmail not connected.")
    try:
        matches = search_similar_emails(user_id=str(current_user.id), query=query)
        formatted = [{
            "summary": summarize_email(m.metadata["text"]),
            "gmail_link": f"https://mail.google.com/mail/u/0/#inbox/{m.metadata['email_id']}"
        } for m in matches]
        return {"results": formatted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
