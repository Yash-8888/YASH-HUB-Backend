import enum


class UserRole(str, enum.Enum):
    member = "member"
    admin = "admin"


class GiveawayStatus(str, enum.Enum):
    active = "active"
    ended = "ended"
    cancelled = "cancelled"
