import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)

    roblox_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discord_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.member, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    entries: Mapped[list["GiveawayEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    redeemed_rewards: Mapped[list["UserReward"]] = relationship(back_populates="user", cascade="all, delete-orphan")
