import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Giveaway, GiveawayEntry, GiveawayStatus
from app.schemas.giveaway import GiveawayCreate, GiveawayUpdate, GiveawayPublic, GiveawayEntryResult
from app.services.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/giveaways", tags=["giveaways"])


def _to_public(g: Giveaway) -> GiveawayPublic:
    return GiveawayPublic(
        id=g.id,
        title=g.title,
        description=g.description,
        image=g.image,
        prize=g.prize,
        requirements=g.requirements,
        max_winners=g.max_winners,
        winner_date=g.winner_date,
        status=g.status,
        entry_count=g.entry_count,
        created_at=g.created_at,
    )


@router.get("", response_model=list[GiveawayPublic])
def list_giveaways(status_filter: GiveawayStatus | None = None, db: Session = Depends(get_db)):
    query = db.query(Giveaway)
    if status_filter:
        query = query.filter(Giveaway.status == status_filter)
    giveaways = query.order_by(Giveaway.winner_date.asc()).all()
    return [_to_public(g) for g in giveaways]


@router.get("/{giveaway_id}", response_model=GiveawayPublic)
def get_giveaway(giveaway_id: uuid.UUID, db: Session = Depends(get_db)):
    g = db.query(Giveaway).filter(Giveaway.id == giveaway_id).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Giveaway not found")
    return _to_public(g)


@router.post("/{giveaway_id}/enter", response_model=GiveawayEntryResult)
def enter_giveaway(
    giveaway_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    g = db.query(Giveaway).filter(Giveaway.id == giveaway_id).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Giveaway not found")

    if g.status != GiveawayStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This giveaway is not active")

    # Roblox username is required to enter — this is how winners get contacted in-game
    if not current_user.roblox_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add your Roblox username to your profile before entering",
        )

    existing = (
        db.query(GiveawayEntry)
        .filter(GiveawayEntry.giveaway_id == giveaway_id, GiveawayEntry.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already entered this giveaway")

    entry = GiveawayEntry(user_id=current_user.id, giveaway_id=giveaway_id)
    db.add(entry)
    db.commit()

    db.refresh(g)
    return GiveawayEntryResult(message="Entry submitted", entry_count=g.entry_count)


# --- Admin-only endpoints ---


@router.post("", response_model=GiveawayPublic, status_code=status.HTTP_201_CREATED)
def create_giveaway(
    payload: GiveawayCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    g = Giveaway(**payload.model_dump())
    db.add(g)
    db.commit()
    db.refresh(g)
    return _to_public(g)


@router.patch("/{giveaway_id}", response_model=GiveawayPublic)
def update_giveaway(
    giveaway_id: uuid.UUID,
    payload: GiveawayUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    g = db.query(Giveaway).filter(Giveaway.id == giveaway_id).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Giveaway not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(g, field, value)

    db.commit()
    db.refresh(g)
    return _to_public(g)


@router.delete("/{giveaway_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_giveaway(
    giveaway_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    g = db.query(Giveaway).filter(Giveaway.id == giveaway_id).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Giveaway not found")
    db.delete(g)
    db.commit()


@router.post("/{giveaway_id}/pick-winners", response_model=list[GiveawayPublic])
def pick_winners(
    giveaway_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Randomly selects up to max_winners entrants, marks them as winners,
    increments their `wins` count, and closes the giveaway.
    Kept simple for MVP — Phase 4 spec calls for full automatic selection with
    audit logging, which can build on top of this.
    """
    import random

    g = db.query(Giveaway).filter(Giveaway.id == giveaway_id).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Giveaway not found")
    if g.status != GiveawayStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Giveaway is not active")
    if not g.entries:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No entries to pick from")

    winners = random.sample(g.entries, k=min(g.max_winners, len(g.entries)))
    for entry in winners:
        entry.is_winner = True
        entry.user.wins += 1

    g.status = GiveawayStatus.ended
    db.commit()
    db.refresh(g)
    return [_to_public(g)]
