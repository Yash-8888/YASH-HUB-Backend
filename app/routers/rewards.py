import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Reward, UserReward
from app.schemas.reward import RewardCreate, RewardPublic
from app.services.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/rewards", tags=["rewards"])


@router.get("", response_model=list[RewardPublic])
def list_rewards(db: Session = Depends(get_db)):
    return db.query(Reward).order_by(Reward.points.asc()).all()


@router.post("/{reward_id}/redeem", response_model=RewardPublic)
def redeem_reward(
    reward_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reward not found")

    if current_user.points < reward.points:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough points")

    current_user.points -= reward.points
    db.add(UserReward(reward_id=reward.id, user_id=current_user.id))
    db.commit()
    db.refresh(reward)
    return reward


@router.post("", response_model=RewardPublic, status_code=status.HTTP_201_CREATED)
def create_reward(
    payload: RewardCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reward = Reward(**payload.model_dump())
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return reward


@router.delete("/{reward_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reward(
    reward_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reward = db.query(Reward).filter(Reward.id == reward_id).first()
    if not reward:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reward not found")
    db.delete(reward)
    db.commit()
