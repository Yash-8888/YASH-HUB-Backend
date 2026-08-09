import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Announcement
from app.schemas.reward import AnnouncementCreate, AnnouncementPublic
from app.services.deps import require_admin

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


@router.get("", response_model=list[AnnouncementPublic])
def list_announcements(db: Session = Depends(get_db)):
    return (
        db.query(Announcement)
        .order_by(desc(Announcement.pinned), desc(Announcement.created_at))
        .all()
    )


@router.post("", response_model=AnnouncementPublic, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    announcement = Announcement(**payload.model_dump())
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    a = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    db.delete(a)
    db.commit()


@router.patch("/{announcement_id}/pin", response_model=AnnouncementPublic)
def toggle_pin(
    announcement_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    a = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    a.pinned = not a.pinned
    db.commit()
    db.refresh(a)
    return a
