from groq import Groq
from app.core.config import settings  # assuming you already use this pattern
from app.core.pinecone_setup import index
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
from sentence_transformers import SentenceTransformer

# ✅ Load model globally (efficient)
model = SentenceTransformer("aspire/acge_text_embedding")

def get_embedding(text: str) -> list:
    embedding = model.encode([text])[0]  # encode returns a list of arrays
    return embedding.tolist()  # convert NumPy array to plain list for storage/serialization


def store_vector(user_id: str, email_id: str, text: str, embedding: list):
    vector_id = f"{user_id}_{email_id}"

    # 🛑 Check if vector already exists
    existing = index.fetch(ids=[vector_id])
    if existing and existing.vectors:  # ✅ Correct way to check
        print(f"⚠️ Skipping duplicate: {vector_id}")
        return

    # ✅ Upsert to Pinecone
    index.upsert(vectors=[
        {
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "user_id": user_id,
                "email_id": email_id,
                "text": text
            }
        }
    ])



def search_similar_emails(user_id: str, query: str, top_k: int = 5):
    query_embedding = get_embedding(query)
    
    result = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter={"user_id": {"$eq": user_id}}  # Pinecone supports metadata filtering
    )
    
    return result.matches
