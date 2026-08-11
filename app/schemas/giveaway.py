import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GiveawayStatus


class GiveawayCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str
    image: str | None = None
    prize: str | None = None
    requirements: str | None = None
    max_winners: int = Field(default=1, ge=1)
    winner_date: datetime
    sub_goal: int | None = None


class GiveawayUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    image: str | None = None
    prize: str | None = None
    requirements: str | None = None
    max_winners: int | None = None
    winner_date: datetime | None = None
    status: GiveawayStatus | None = None


class GiveawayPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    image: str | None
    prize: str | None
    requirements: str | None
    max_winners: int
    winner_date: datetime
    status: GiveawayStatus
    entry_count: int
    created_at: datetime
    sub_goal: int | None


class GiveawayEntryResult(BaseModel):
    message: str
    entry_count: int
