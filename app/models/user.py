# SQLAlchemy User model
import datetime
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    gmail_token = Column(JSON, nullable=True)  # ✅ Add this line

