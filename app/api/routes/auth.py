# Signup, login routes
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import UserCreate, UserLogin, Token
# app/api/routes/auth.py
from app.services.auth_service import register_user, login_user

router = APIRouter()

@router.post("/signup", response_model=Token)
def signup(user: UserCreate):
    return register_user(user)

@router.post("/login", response_model=Token)
def login(user: UserLogin):
    return login_user(user)

