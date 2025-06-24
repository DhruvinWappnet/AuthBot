# app/core/session_store.py
import hashlib
import uuid

session_store = {}

def generate_session_token(email: str) -> str:
    token = str(uuid.uuid4())
    hashed = hashlib.sha256((email + token).encode()).hexdigest()
    session_store[hashed] = {"email": email}
    return hashed

def get_session_data(token: str):
    return session_store.get(token)
