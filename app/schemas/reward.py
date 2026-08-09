import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RewardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    points: int = Field(ge=1)
    image: str | None = None


class RewardPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    points: int
    image: str | None
    created_at: datetime


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str
    pinned: bool = False


class AnnouncementPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    pinned: bool
    created_at: datetime
