# Environment/config settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    groq_api_key: str
    SQLALCHEMY_DATABASE_URL :str


    class Config:
        env_file = ".env"

settings = Settings()