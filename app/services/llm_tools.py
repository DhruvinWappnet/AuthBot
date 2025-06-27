from app.services.groq_service import get_groq_response

def classify_email(content: str) -> str:
    prompt = f"""
You are an email classifier. Read the following email content and classify it into one of the following categories:
[Interview, Money, Reminder, General].

Respond with **only** one of the category names.

Email Content:
\"\"\"
{content}
\"\"\"
"""
    result,_ = get_groq_response(prompt)
    return result.strip().split("\n")[0]  # In case model adds explanation


def summarize_email(content: str) -> tuple[str, dict]:
    prompt = f"""
Summarize the following email in 1-2 concise sentences for a user interface display.

Email:
\"\"\"
{content}
\"\"\"
"""
    summary, token_usage = get_groq_response(prompt)
    return summary.strip(), token_usage
