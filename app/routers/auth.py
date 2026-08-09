from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token, generate_referral_code

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Ensure referral code uniqueness (astronomically unlikely to collide, but check anyway)
    code = generate_referral_code()
    while db.query(User).filter(User.referral_code == code).first():
        code = generate_referral_code()

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        roblox_username=payload.roblox_username,
        referral_code=code,
    )
    db.add(user)

    # Award the referrer points if a valid referral code was supplied (future: move to referrals table)
    if payload.referred_by:
        referrer = db.query(User).filter(User.referral_code == payload.referred_by).first()
        if referrer:
            referrer.points += 100

    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been banned")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
