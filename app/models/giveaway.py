import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import GiveawayStatus


class Giveaway(Base):
    __tablename__ = "giveaways"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)

    prize: Mapped[str | None] = mapped_column(String(200), nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list, kept simple for MVP
    max_winners: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sub_goal: Mapped[int | None] = mapped_column(Integer, nullable=True)

    winner_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[GiveawayStatus] = mapped_column(Enum(GiveawayStatus), default=GiveawayStatus.active, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    entries: Mapped[list["GiveawayEntry"]] = relationship(back_populates="giveaway", cascade="all, delete-orphan")

    @property
    def entry_count(self) -> int:
        return len(self.entries)


class GiveawayEntry(Base):
    __tablename__ = "giveaway_entries"
    __table_args__ = (UniqueConstraint("user_id", "giveaway_id", name="uq_user_giveaway_entry"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    giveaway_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("giveaways.id", ondelete="CASCADE"))
    is_winner: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="entries")
    giveaway: Mapped["Giveaway"] = relationship(back_populates="entries")
