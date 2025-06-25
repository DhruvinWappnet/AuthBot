from groq import Groq
from app.core.config import settings  # assuming you already use this pattern

client = Groq(api_key=settings.groq_api_key)

def get_groq_response(prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        response = ""
        for chunk in completion:
            response += chunk.choices[0].delta.content or ""
        return response.strip()

    except Exception as e:
        return f"Error: {str(e)}"
