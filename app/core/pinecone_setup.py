import os
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings  # ensure your settings have the below fields

# Constants
INDEX_NAME = settings.PINECONE_INDEX_NAME
EMBEDDING_DIM = 1536  # update as per your model (e.g., text-embedding-3-small)
METRIC = "cosine"

# ✅ Initialize Pinecone client
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# 🔍 Check and create index if not exists
if INDEX_NAME not in pc.list_indexes().names():
    print(f"🛠️ Creating index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=1792,
        metric=METRIC,
        spec=ServerlessSpec(
            cloud="aws",         # or "gcp"
            region="us-east-1"   # or your target region
        )
    )
else:
    print(f"✅ Index '{INDEX_NAME}' already exists")

# 🌐 Connect to index
index = pc.Index(INDEX_NAME)
