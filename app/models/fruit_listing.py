import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ListingType, ListingStatus


class FruitListing(Base):
    __tablename__ = "fruit_listings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fruit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fruits.id", ondelete="CASCADE"))
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))

    listing_type: Mapped[ListingType] = mapped_column(Enum(ListingType), default=ListingType.sell, nullable=False)
    requirement: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.open, nullable=False)

    accepted_offer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fruit_offers.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    fruit: Mapped["Fruit"] = relationship(foreign_keys=[fruit_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])
    offers: Mapped[list["FruitOffer"]] = relationship(
        back_populates="listing", foreign_keys="FruitOffer.listing_id", cascade="all, delete-orphan"
    )
