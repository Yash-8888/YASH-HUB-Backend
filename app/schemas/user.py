import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UserPublic(BaseModel):
    """Safe-to-expose user shape (no password hash, no email for other users)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    roblox_username: str | None
    points: int
    wins: int
    role: UserRole


class UserProfile(BaseModel):
    """Full profile shape returned for the logged-in user themselves."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    roblox_username: str | None
    discord_id: str | None
    points: int
    wins: int
    role: UserRole
    referral_code: str
    created_at: datetime


class UserProfileUpdate(BaseModel):
    roblox_username: str | None = None
    discord_id: str | None = None


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rank: int
    roblox_username: str | None
    points: int
    wins: int
