"""
Resets the FIRST_ADMIN_EMAIL user's password to FIRST_ADMIN_PASSWORD,
regardless of whether the user already existed.

Run with:  python -m scripts.reset_admin_password
"""

from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.utils.security import hash_password


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.first_admin_email).first()
        if not user:
            print(f"No user found with email {settings.first_admin_email}")
            return
        user.hashed_password = hash_password(settings.first_admin_password)
        db.commit()
        print(f"Password reset for {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()