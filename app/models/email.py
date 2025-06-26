# app/models/email.py
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.db.database import Base
from sqlalchemy.orm import relationship


# class Email(Base):
#     __tablename__ = "emails"
#     id = Column(Integer, primary_key=True, index=True)
#     email_id = Column(String, unique=True, index=True)  # Gmail Message ID
#     user_id = Column(Integer, ForeignKey("users.id"))
#     subject = Column(String)
#     sender = Column(String)
#     snippet = Column(Text)
#     full_text = Column(Text)
#     label = Column(String)
#     date = Column(DateTime)
#     embedding = Column(JSON)  # or store in a separate vector DB

#     user = relationship("User", back_populates="emails")

from sqlalchemy import Column, String, Text, DateTime, Integer
from datetime import datetime
from app.db.database import Base

class EmailSummary(Base):
    __tablename__ = "email_summaries"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, index=True)
    user_email = Column(String, index=True)
    full_text = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
