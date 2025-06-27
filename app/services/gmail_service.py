# app/services/gmail_service.py

import json
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import httpx

from app.models.user import User

def is_token_expired(expiry_str: str):
    if not expiry_str:
        return True
    expiry = datetime.fromisoformat(expiry_str).replace(tzinfo=timezone.utc)
    return expiry <= datetime.now(timezone.utc)

def refresh_google_token(refresh_token: str, client_id: str, client_secret: str):
    response = httpx.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to refresh Gmail token: {response.text}")




def get_gmail_service_email(gmail_token_dict: dict, db=None, user=None):
    creds = Credentials.from_authorized_user_info(gmail_token_dict)
    return build("gmail", "v1", credentials=creds)
def get_gmail_service(gmail_token_dict: dict, db=None, user=None):
    print("📦 Received token:", gmail_token_dict)  # 🔍 Add debug log

    if is_token_expired(gmail_token_dict.get("expiry", "")):
        print("🔁 Token expired. Refreshing...")
        refreshed = refresh_google_token(
            refresh_token=gmail_token_dict["refresh_token"],
            client_id=gmail_token_dict["client_id"],
            client_secret=gmail_token_dict["client_secret"]
        )
        print("✅ Refreshed token:", refreshed)

        gmail_token_dict["token"] = refreshed["access_token"]
        gmail_token_dict["expiry"] = (
            datetime.now(timezone.utc) + timedelta(seconds=refreshed["expires_in"])
        ).isoformat()

        if db and user:
            print("💾 Saving refreshed token to DB")
            # 👇 Re-fetch user from current session to avoid session conflict
            user_in_db = db.query(User).filter(User.email == user.email).first()
            user_in_db.gmail_token = json.dumps(gmail_token_dict)
            db.commit()
            print("✅ Updated token in DB:", user_in_db.gmail_token)

    creds = Credentials.from_authorized_user_info(gmail_token_dict)
    return build("gmail", "v1", credentials=creds)


import base64
import quopri

def extract_email_body(payload):
    def decode_data(data, encoding="base64"):
        if encoding == "base64":
            return base64.urlsafe_b64decode(data).decode('utf-8', errors="ignore")
        elif encoding == "quoted-printable":
            return quopri.decodestring(data).decode('utf-8', errors="ignore")
        return data

    if payload.get("mimeType") == "text/plain":
        return decode_data(payload.get("body", {}).get("data", ""), "base64")

    elif payload.get("mimeType") == "multipart/alternative":
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                return decode_data(part.get("body", {}).get("data", ""), "base64")

    elif payload.get("mimeType") == "multipart/mixed":
        for part in payload.get("parts", []):
            if part.get("mimeType") == "multipart/alternative":
                return extract_email_body(part)

    return "[No plain text body found]"

def fetch_recent_emails(service, max_results=10):
    result = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = result.get('messages', [])

    emails = []
    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        snippet = msg_detail.get("snippet", "")
        payload = msg_detail.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        subject = headers.get("Subject", "")
        sender = headers.get("From", "")
        date = headers.get("Date", "")
        body = extract_email_body(payload)

        emails.append({"id": msg["id"], "subject": subject, "from": sender, "date": date, "snippet": snippet,"body": body })
    return emails

    
# def fetch_recent_emails(service, days_back=10, max_results=50):
#     after_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y/%m/%d")
#     query = f"after:{after_date}"

#     results = service.users().messages().list(
#         userId='me',
#         q=query,
#         maxResults=max_results
#     ).execute()
#     messages = results.get("messages", [])

#     emails = []
#     for msg in messages:
#         msg_data = service.users().messages().get(userId='me', id=msg["id"], format="full").execute()
#         snippet = msg_data.get("snippet", "")
#         headers = msg_data.get("payload", {}).get("headers", [])
#         headers = {h["name"]: h["value"] for h in headers}
#         emails.append({
#             "id": msg["id"],
#             "subject": headers.get("Subject", ""),
#             "from": headers.get("From", ""),
#             "date": headers.get("Date", ""),
#             "snippet": snippet
#         })
#     return emails
