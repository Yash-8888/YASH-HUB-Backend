"""
Quick-start script: creates all tables directly from the SQLAlchemy models.
Good enough for local development. Once the schema stabilizes, switch to
Alembic migrations (`alembic upgrade head`) instead of this script.

Run with:  python -m scripts.create_tables
"""

from app.database import Base, engine
import app.models  # noqa: F401 - import so all models register on Base.metadata


def main():
    Base.metadata.create_all(bind=engine)
    print("All tables created (or already existed).")


if __name__ == "__main__":
    main()
