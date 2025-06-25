from fastapi import APIRouter, Depends, HTTPException
from google_auth_oauthlib.flow import InstalledAppFlow
from app.core.auth import get_current_user_token
from app.db.database import SessionLocal
from app.models.user import User
import os, json

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
