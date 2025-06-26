from app.services.gmail_service import get_gmail_service, fetch_recent_emails
from app.services.groq_service import get_embedding,store_vector

def embed_and_store_emails(user_id: str, gmail_token: dict):
    service = get_gmail_service(gmail_token)
    emails = fetch_recent_emails(service, days_back=10)

    for email in emails:
        text = f"{email['subject']} - {email['snippet']}"
        vector = get_embedding(text)
        store_vector(user_id=user_id, email_id=email["id"], text=text, embedding=vector)
