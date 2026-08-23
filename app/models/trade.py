import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import TradeType


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    trade_type: Mapped[TradeType] = mapped_column(Enum(TradeType), nullable=False)
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    points_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)