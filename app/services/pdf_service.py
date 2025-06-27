# app/services/processing.py

from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from io import BytesIO
import numpy as np
import torch
import re

# Use efficient model
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    all_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            all_text += "\n" + text
    return all_text

def chunk_text(text, chunk_size=500, overlap=50):
    # Clean and split into sentences
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) < chunk_size:
            current += sentence + " "
        else:
            chunks.append(current.strip())
            current = sentence + " "
    if current:
        chunks.append(current.strip())

    # Add overlap
    final_chunks = []
    for i in range(0, len(chunks), max(1, chunk_size // 10)):
        chunk = " ".join(chunks[i:i+3])
        final_chunks.append(chunk)
    return final_chunks

def get_top_k_chunks(chunks, question, k=5):
    if not chunks:
        return []

    chunk_embeddings = embedder.encode(chunks, convert_to_tensor=True)
    question_embedding = embedder.encode([question], convert_to_tensor=True)

    scores = torch.nn.functional.cosine_similarity(question_embedding, chunk_embeddings)
    k = min(k, len(chunks)) 
    top_k_indices = torch.topk(scores, k=k).indices

    return [chunks[i] for i in top_k_indices]
