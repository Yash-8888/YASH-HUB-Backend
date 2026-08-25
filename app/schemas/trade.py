import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TradeType, RedemptionStatus


class TradeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    trade_type: TradeType
    value: str = Field(min_length=1, max_length=200)
    points_cost: int = Field(ge=1)
    image: str | None = None


class TradePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    trade_type: TradeType
    value: str
    points_cost: int
    image: str | None
    active: bool
    created_at: datetime


class TradeRedemptionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trade_id: uuid.UUID
    user_id: uuid.UUID
    coupon_code: str
    status: RedemptionStatus
    verified_by: uuid.UUID | None
    verified_at: datetime | None
    created_at: datetime


class ClaimResponse(BaseModel):
    redemption: TradeRedemptionPublic
    message: str


class VerifyCouponRequest(BaseModel):
    coupon_code: str = Field(min_length=1, max_length=32)