from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    roblox_username: str | None = None
    referred_by: str | None = None  # referral code of the inviter, optional


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleAuthRequest(BaseModel):
    credential: str  # the ID token JWT returned by Google's Sign-In button