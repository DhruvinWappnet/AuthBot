# DB connection setup
from requests import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy.orm import declarative_base

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()