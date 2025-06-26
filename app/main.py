# FastAPI app entry point
from fastapi import FastAPI
from app.api.routes import analytics, auth, chat, email_router, gmail
from app.db.database import engine
from app.models import user, chat as chat_models

# Create tables
# user.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth.router, prefix="/auth")
app.include_router(chat.router, prefix="/chat")
app.include_router(email_router.router, prefix="/email_router")
app.include_router(gmail.router,prefix="/gmail")
app.include_router(analytics.router,prefix="/analytics")