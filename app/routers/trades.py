import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Trade
from app.schemas.trade import TradeCreate, TradePublic
from app.services.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("", response_model=list[TradePublic])
def list_trades(db: Session = Depends(get_db)):
    return db.query(Trade).filter(Trade.active == True).order_by(Trade.points_cost.asc()).all()


@router.post("/{trade_id}/claim", response_model=TradePublic)
def claim_trade(
    trade_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.active == True).first()
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")

    if current_user.points < trade.points_cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not enough points")

    current_user.points -= trade.points_cost
    db.add(current_user)
    db.commit()
    db.refresh(trade)
    return trade


@router.post("", response_model=TradePublic, status_code=status.HTTP_201_CREATED)
def create_trade(
    payload: TradeCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    trade = Trade(**payload.model_dump())
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trade(
    trade_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    trade.active = False
    db.commit()