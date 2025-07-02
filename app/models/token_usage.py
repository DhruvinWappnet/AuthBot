from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from sqlalchemy import Float

class TokenUsage(Base):
    __tablename__ = "token_usage"
    id = Column(Integer, primary_key=True)
    user_email = Column(String)
    session_id = Column(String)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    message = Column(String)
    cost = Column(Float)  # 🆕
    model = Column(String)  # 🆕
    groq_duration = Column(Float)  # 🆕 add this
    api_duration = Column(Float)  # 🆕 add this
    timestamp = Column(DateTime, default=datetime.utcnow)
