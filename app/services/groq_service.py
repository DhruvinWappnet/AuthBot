from groq import Groq
from app.core.config import settings  # assuming you already use this pattern
import quadrant 

client = Groq(api_key=settings.groq_api_key)

# def get_groq_response(prompt: str) -> str:
#     try:
#         completion = client.chat.completions.create(
#             model="meta-llama/llama-4-scout-17b-16e-instruct",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_completion_tokens=1024,
#             top_p=1,
#             stream=True,
#             stop=None,
#         )
#         response = ""
#         for chunk in completion:
#             response += chunk.choices[0].delta.content or ""
#         return response.strip()

#     except Exception as e:
#         return f"Error: {str(e)}"

#==================UPDATION=================#

def get_groq_response(prompt: str):
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

        response = completion.choices[0].message.content

        token_usage = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        }

        return response.strip(), token_usage

    except Exception as e:
        return f"Error: {str(e)}", None
#===================================================================

def get_embedding(text: str) -> list:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

quadrant.api_key = settings.QUADRANT_API_KEY

def store_vector(user_id: str, email_id: str, text: str, embedding: list):
    quadrant.upsert(vectors=[{
        "id": f"{user_id}_{email_id}",
        "values": embedding,
        "metadata": {
            "user_id": user_id,
            "email_id": email_id,
            "text": text
        }
    }])

def search_similar_emails(user_id: str, query: str, top_k: int = 5):
    embedding = get_embedding(query)
    results = quadrant.query(
        vector=embedding,
        top_k=top_k,
        filter={"user_id": user_id}
    )
    return results.matches
