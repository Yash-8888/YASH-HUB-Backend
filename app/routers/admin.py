from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, GiveawayEntry
from app.schemas.admin import AdjustPointsRequest, BanUserRequest, ResetEntriesRequest
from app.schemas.user import UserProfile
from app.services.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserProfile])
def search_users(
    q: str | None = None,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter((User.email.ilike(like)) | (User.roblox_username.ilike(like)))
    return query.order_by(User.created_at.desc()).limit(200).all()


@router.post("/users/ban", response_model=UserProfile)
def ban_user(
    payload: BanUserRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_banned = payload.banned
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/points", response_model=UserProfile)
def adjust_points(
    payload: AdjustPointsRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.points = max(0, user.points + payload.amount)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/reset-entries", status_code=status.HTTP_204_NO_CONTENT)
def reset_entries(
    payload: ResetEntriesRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(GiveawayEntry).filter(GiveawayEntry.user_id == payload.user_id)
    if payload.giveaway_id:
        query = query.filter(GiveawayEntry.giveaway_id == payload.giveaway_id)
    query.delete(synchronize_session=False)
    db.commit()
