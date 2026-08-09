from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user import LeaderboardEntry

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
def leaderboard(limit: int = 100, db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .filter(User.is_banned.is_(False))
        .order_by(desc(User.points))
        .limit(limit)
        .all()
    )
    return [
        LeaderboardEntry(rank=i + 1, roblox_username=u.roblox_username, points=u.points, wins=u.wins)
        for i, u in enumerate(users)
    ]
