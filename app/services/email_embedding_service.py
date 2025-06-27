import httpx
from app.services.gmail_service import get_gmail_service, fetch_recent_emails, get_gmail_service_email
from app.services.groq_service import get_embedding, store_vector
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

def embed_and_store_emails(user_id: str, gmail_token: dict):
    print("============================================")
    print("EMBED GMAIL SERVICE CALLED")
    print("============================================")
    service = get_gmail_service_email(gmail_token)
    print("============================================")
    print("FETCH RECENT EMAILS CALLED")
    print("============================================")
    emails = fetch_recent_emails(service, max_results=50)
    print("============================================")
    print("EMBED SERVICE CALLED")
    print("============================================")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    for email in emails:
        try:
            email_date = parsedate_to_datetime(email["date"])
        except Exception:
            continue  # skip invalid date

        if email_date < cutoff_date:
            continue  # skip old emails

        text = f"{email['subject']} - {email['snippet']} - {email['body']}"

        vector = get_embedding(text)

        # 🔁 Store in Pinecone or Quadrant
        store_vector(user_id=user_id, email_id=email["id"], text=text, embedding=vector)

API_BASE_URL = "http://localhost:8000"


def trigger_embedding_background(token):
    print("======================================")
    print("EMAIL EMBEDDING CALLED")
    print("======================================")

    try:
        res = httpx.post(
            f"{API_BASE_URL}/email_router/embed",
            headers={"Authorization": f"Bearer {token}"},  timeout=120
        )
        if res.status_code == 200:
            print("✅ Email embedding completed in background.")
        else:
            print(f"⚠️ Embedding failed: {res.text}")
    except Exception as e:
        print(f"❌ Embedding background error: {e}")
