from fastapi import Depends,APIRouter
from requests import Session
from app.core.auth import get_current_user_token
from app.db.database import get_db

router = APIRouter()
@router.get("/usage")
def get_usage_data(current_user=Depends(get_current_user_token), db: Session = Depends(get_db)):
    from app.models.token_usage import TokenUsage

    usage = db.query(TokenUsage)\
              .filter(TokenUsage.user_email == current_user.email)\
              .order_by(TokenUsage.timestamp.asc())\
              .all()

    return [{
        "timestamp": u.timestamp.isoformat(),
        "total_tokens": u.total_tokens,
        "message": u.message
    } for u in usage]
