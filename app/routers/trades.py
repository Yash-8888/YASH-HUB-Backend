import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Trade, TradeRedemption
from app.models.enums import RedemptionStatus
from app.schemas.trade import (
    TradeCreate,
    TradePublic,
    TradeRedemptionPublic,
    ClaimResponse,
    VerifyCouponRequest,
)
from app.services.deps import get_current_user, require_admin
from app.utils.security import generate_coupon_code

router = APIRouter(prefix="/api/trades", tags=["trades"])

DISCORD_INVITE_URL = "https://discord.gg/YOUR_INVITE_HERE"  # TODO: replace with real invite


@router.get("", response_model=list[TradePublic])
def list_trades(db: Session = Depends(get_db)):
    return db.query(Trade).filter(Trade.active == True).order_by(Trade.points_cost.asc()).all()


@router.post("/{trade_id}/claim", response_model=ClaimResponse)
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

    coupon_code = generate_coupon_code()
    while db.query(TradeRedemption).filter(TradeRedemption.coupon_code == coupon_code).first():
        coupon_code = generate_coupon_code()

    redemption = TradeRedemption(
        trade_id=trade.id,
        user_id=current_user.id,
        coupon_code=coupon_code,
        status=RedemptionStatus.pending,
    )

    db.add(current_user)
    db.add(redemption)
    db.commit()
    db.refresh(redemption)

    message = (
        f"You redeemed '{trade.title}' for {trade.points_cost} points! "
        f"Your coupon code is {coupon_code}. "
        f"Join our Discord server ({DISCORD_INVITE_URL}) and show this code to a mod "
        f"to verify it and receive your trade."
    )

    return ClaimResponse(redemption=TradeRedemptionPublic.model_validate(redemption), message=message)


@router.get("/redemptions/mine", response_model=list[TradeRedemptionPublic])
def my_redemptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(TradeRedemption)
        .filter(TradeRedemption.user_id == current_user.id)
        .order_by(TradeRedemption.created_at.desc())
        .all()
    )


@router.get("/redemptions/pending", response_model=list[TradeRedemptionPublic])
def pending_redemptions(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(TradeRedemption)
        .filter(TradeRedemption.status == RedemptionStatus.pending)
        .order_by(TradeRedemption.created_at.asc())
        .all()
    )


@router.post("/redemptions/verify", response_model=TradeRedemptionPublic)
def verify_coupon(
    payload: VerifyCouponRequest,
    mod: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    redemption = (
        db.query(TradeRedemption)
        .filter(TradeRedemption.coupon_code == payload.coupon_code.strip().upper())
        .first()
    )
    if not redemption:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon code not found")

    if redemption.status == RedemptionStatus.verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon already verified")

    redemption.status = RedemptionStatus.verified
    redemption.verified_by = mod.id
    redemption.verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(redemption)
    return redemption