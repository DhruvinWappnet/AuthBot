# app/services/gmail_service.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def get_gmail_service(gmail_token_dict: dict):
    creds = Credentials.from_authorized_user_info(gmail_token_dict)
    return build("gmail", "v1", credentials=creds)


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
        emails.append({"id": msg["id"], "subject": subject, "from": sender, "date": date, "snippet": snippet})
    return emails
