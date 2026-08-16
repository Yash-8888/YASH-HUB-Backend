from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AdClick
from app.services.deps import get_current_user

router = APIRouter(prefix="/api/ads", tags=["ads"])

COOLDOWN_MINUTES = 60
POINTS_PER_CLICK = 5
MAX_CLICKS_PER_DAY = 5


@router.post("/click")
def register_ad_click(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    last_click = (
        db.query(AdClick)
        .filter(AdClick.user_id == current_user.id)
        .order_by(AdClick.created_at.desc())
        .first()
    )
    if last_click and (now - last_click.created_at) < timedelta(minutes=COOLDOWN_MINUTES):
        wait_minutes = COOLDOWN_MINUTES - int((now - last_click.created_at).total_seconds() // 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Wait {wait_minutes} more minute(s) before earning again",
        )

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    clicks_today = (
        db.query(AdClick)
        .filter(AdClick.user_id == current_user.id, AdClick.created_at >= today_start)
        .count()
    )
    if clicks_today >= MAX_CLICKS_PER_DAY:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Daily limit reached")

    current_user.points += POINTS_PER_CLICK
    db.add(AdClick(user_id=current_user.id, points_awarded=POINTS_PER_CLICK))
    db.commit()

    return {"points_awarded": POINTS_PER_CLICK, "total_points": current_user.points, "clicks_today": clicks_today + 1}