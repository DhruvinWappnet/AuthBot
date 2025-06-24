from sqlalchemy.orm import Session
from app.schemas.auth import UserCreate, UserLogin, Token
from app.models.user import User
from app.db.database import SessionLocal
from app.core.security import hash_password, verify_password, create_access_token
from app.core.session_store import generate_session_token
from fastapi import HTTPException
from datetime import timedelta

def register_user(user_data: UserCreate):
    db: Session = SessionLocal()

    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    session_token = generate_session_token(new_user.email)

    return {
        "access_token": access_token,
        "session_token": session_token,
        "token_type": "bearer"
    }

def login_user(user_data: UserLogin):
    db: Session = SessionLocal()

    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.email})
    session_token = generate_session_token(user.email)

    return {
        "access_token": access_token,
        "session_token": session_token,
        "token_type": "bearer"
    }
