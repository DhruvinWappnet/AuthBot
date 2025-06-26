# app/api/routes/email.py

from fastapi import APIRouter, Depends, HTTPException
from requests import Session
from app.db.database import get_db
from app.models.email import EmailSummary
from app.models.user import User
from app.services.gmail_service import get_gmail_service, fetch_recent_emails
from app.services.llm_tools import classify_email, summarize_email
from app.core.auth import get_current_user_token

router = APIRouter()

import json

GMAIL_LABELS = {
    "INBOX": "Inbox",
    "SPAM": "Spam",
    "CATEGORY_PERSONAL": "Personal",
    "CATEGORY_PROMOTIONS": "Promotions",
    "CATEGORY_SOCIAL": "Social",
    "IMPORTANT": "Important",
    "UNREAD": "Unread",
}

@router.post("/list")
def list_emails(current_user = Depends(get_current_user_token)):
    if not current_user.gmail_token:
        raise HTTPException(status_code=400, detail="Gmail not connected for this user.")

    # Deserialize token if needed
    token_data = current_user.gmail_token
    if isinstance(token_data, str):
        token_data = json.loads(token_data)

    try:
        service = get_gmail_service(token_data)
        raw_emails = fetch_recent_emails(service)

        emails = []
        for email in raw_emails:
            label = classify_email(email["snippet"])
            emails.append({**email, "label": label})
        return {"emails": emails}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#==========================PREVIOUS WORKING========================
# @router.post("/summarize")
# def summarize(email_id: str, current_user = Depends(get_current_user_token)):
#     if not current_user.gmail_token:
#         raise HTTPException(status_code=400, detail="Gmail not connected for this user.")

#     service = get_gmail_service(current_user.gmail_token)
#     msg = service.users().messages().get(userId='me', id=email_id, format='full').execute()
#     full_text = msg.get("snippet", "")
#     summary = summarize_email(full_text)
#     return {"summary": summary}
#===============================================================

#=====================UPDATED=============================
@router.post("/summarize")
def summarize(
    email_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_token)
):
    if not current_user.gmail_token:
        raise HTTPException(status_code=400, detail="Gmail not connected for this user.")

    service = get_gmail_service(current_user.gmail_token)
    msg = service.users().messages().get(userId='me', id=email_id, format='full').execute()
    full_text = msg.get("snippet", "")

    # 🔄 Summarize the email and track usage
    summary, token_usage = summarize_email(full_text)  # <-- must return (summary, token_usage)

    # ✅ Save email summary to DB
    email_summary = EmailSummary(
        email_id=email_id,
        user_email=current_user.email,
        full_text=full_text,
        summary=summary
    )
    db.add(email_summary)

    # ✅ Save token usage if available
    if token_usage:
        from app.models.token_usage import TokenUsage  # import if not already

        usage_entry = TokenUsage(
            user_email=current_user.email,
            session_id=f"email_{email_id}",
            prompt_tokens=token_usage.get("prompt_tokens", 0),
            completion_tokens=token_usage.get("completion_tokens", 0),
            total_tokens=token_usage.get("total_tokens", 0),
            message=f"Summarized email: {email_id}"
        )
        db.add(usage_entry)

    db.commit()

    return {"summary": summary}

# ===========================================================

@router.get("/gmail/fetch-emails")
def fetch_emails(current_user = Depends(get_current_user_token)):
    if not current_user.gmail_token:
        raise HTTPException(status_code=400, detail="Gmail not connected for this user.")

    try:
        service = get_gmail_service(current_user.gmail_token)
        results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=5).execute()
        messages = results.get("messages", [])

        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            snippet = msg_data["snippet"]
            headers = msg_data["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
            from_ = next((h["value"] for h in headers if h["name"] == "From"), "")
            emails.append({"subject": subject, "from": from_, "snippet": snippet})

        return {"emails": emails}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Query

import json

@router.get("/gmail/status")
def check_gmail_status(email: str = Query(...), db: Session = Depends(get_db)):
    print("_____________________GMAIL STATUS ENTERED : --------------------",email)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Do NOT raise 404 → return "connected: false" instead
        return {"connected": False}

    token_data = user.gmail_token

    if not token_data:
        return {"connected": False}

    # Ensure token_data is a dict
    if isinstance(token_data, str):
        try:
            token_data = json.loads(token_data)
        except json.JSONDecodeError:
            return {"connected": False}

    return {"connected": bool(token_data.get("token"))}
