import uuid

from pydantic import BaseModel, Field


class AdjustPointsRequest(BaseModel):
    user_id: uuid.UUID
    amount: int = Field(description="Positive to add points, negative to remove")
    reason: str | None = None


class BanUserRequest(BaseModel):
    user_id: uuid.UUID
    banned: bool = True


class ResetEntriesRequest(BaseModel):
    user_id: uuid.UUID
    giveaway_id: uuid.UUID | None = None  # None = reset all entries for that user
