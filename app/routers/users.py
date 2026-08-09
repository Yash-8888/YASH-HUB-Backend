from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.user import UserProfile, UserProfileUpdate, LeaderboardEntry
from app.services.deps import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/profile", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/profile", response_model=UserProfile)
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.roblox_username is not None:
        current_user.roblox_username = payload.roblox_username
    if payload.discord_id is not None:
        current_user.discord_id = payload.discord_id

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
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
