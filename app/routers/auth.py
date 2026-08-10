from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, GoogleAuthRequest
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
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been banned")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.credential, google_requests.Request(), settings.google_client_id
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    google_sub = idinfo["sub"]
    email = idinfo["email"]

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user:
        # Link to an existing email/password account if one matches, else create fresh
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_sub = google_sub
        else:
            code = generate_referral_code()
            while db.query(User).filter(User.referral_code == code).first():
                code = generate_referral_code()
            user = User(email=email, google_sub=google_sub, referral_code=code)
            db.add(user)
        db.commit()
        db.refresh(user)

    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been banned")

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)
