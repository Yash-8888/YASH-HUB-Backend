import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FruitCategory, ListingType, ListingStatus, OfferStatus


# ---------- Fruit catalog ----------

class FruitPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: FruitCategory
    image: str | None
    active: bool


class FruitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: FruitCategory
    image: str | None = None


# ---------- Public seller/buyer identity shown on every trade ----------

class TraderPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    roblox_username: str | None
    discord_id: str | None


# ---------- Offers ----------

class OfferCreate(BaseModel):
    offer_details: str = Field(min_length=1, max_length=1000)


class SubmitProofRequest(BaseModel):
    inventory_screenshot_url: str = Field(min_length=1, max_length=500)


class ReportCheatRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class OfferPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    buyer: TraderPublic
    offer_details: str
    status: OfferStatus
    inventory_screenshot_url: str | None
    created_at: datetime
    updated_at: datetime


# ---------- Listings ----------

class ListingCreate(BaseModel):
    fruit_id: uuid.UUID
    listing_type: ListingType = ListingType.sell
    requirement: str = Field(min_length=1, max_length=1000)


class ListingPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fruit: FruitPublic
    seller: TraderPublic
    listing_type: ListingType
    requirement: str
    status: ListingStatus
    accepted_offer_id: uuid.UUID | None
    created_at: datetime


class ListingWithOffers(ListingPublic):
    offers: list[OfferPublic] = []
