"""
Creates (or promotes) the first admin user, using FIRST_ADMIN_EMAIL /
FIRST_ADMIN_PASSWORD from your .env file.

Run with:  python -m scripts.create_admin
"""

from app.config import settings
from app.database import SessionLocal
from app.models import User, UserRole
from app.utils.security import hash_password, generate_referral_code


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.first_admin_email).first()

        if user:
            user.role = UserRole.admin
            print(f"Promoted existing user {user.email} to admin.")
        else:
            code = generate_referral_code()
            while db.query(User).filter(User.referral_code == code).first():
                code = generate_referral_code()

            user = User(
                email=settings.first_admin_email,
                hashed_password=hash_password(settings.first_admin_password),
                role=UserRole.admin,
                referral_code=code,
            )
            db.add(user)
            print(f"Created admin user {user.email}.")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
