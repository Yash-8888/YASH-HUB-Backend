import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User, Fruit, FruitListing, FruitOffer
from app.models.enums import ListingStatus, OfferStatus
from app.schemas.marketplace import (
    FruitPublic,
    FruitCreate,
    ListingCreate,
    ListingPublic,
    ListingWithOffers,
    OfferCreate,
    OfferPublic,
    SubmitProofRequest,
    ReportCheatRequest,
)
from app.services.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


# ---------- Fruit catalog ----------

@router.get("/fruits", response_model=list[FruitPublic])
def list_fruits(db: Session = Depends(get_db)):
    return db.query(Fruit).filter(Fruit.active == True).order_by(Fruit.category.asc(), Fruit.name.asc()).all()


@router.post("/fruits", response_model=FruitPublic)
def create_fruit(
    payload: FruitCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    fruit = Fruit(name=payload.name, category=payload.category, image=payload.image)
    db.add(fruit)
    db.commit()
    db.refresh(fruit)
    return fruit


# ---------- Listings (public trade feed) ----------

@router.get("/listings", response_model=list[ListingPublic])
def list_listings(
    status_filter: ListingStatus | None = None,
    fruit_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(FruitListing).options(
        joinedload(FruitListing.fruit), joinedload(FruitListing.seller)
    )
    if status_filter:
        query = query.filter(FruitListing.status == status_filter)
    if fruit_id:
        query = query.filter(FruitListing.fruit_id == fruit_id)
    return query.order_by(FruitListing.created_at.desc()).all()


@router.get("/listings/mine", response_model=list[ListingWithOffers])
def my_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(FruitListing)
        .options(
            joinedload(FruitListing.fruit),
            joinedload(FruitListing.seller),
            joinedload(FruitListing.offers).joinedload(FruitOffer.buyer),
        )
        .filter(FruitListing.seller_id == current_user.id)
        .order_by(FruitListing.created_at.desc())
        .all()
    )


@router.get("/listings/{listing_id}", response_model=ListingWithOffers)
def get_listing(listing_id: uuid.UUID, db: Session = Depends(get_db)):
    listing = (
        db.query(FruitListing)
        .options(
            joinedload(FruitListing.fruit),
            joinedload(FruitListing.seller),
            joinedload(FruitListing.offers).joinedload(FruitOffer.buyer),
        )
        .filter(FruitListing.id == listing_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


@router.post("/listings", response_model=ListingPublic)
def create_listing(
    payload: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fruit = db.query(Fruit).filter(Fruit.id == payload.fruit_id, Fruit.active == True).first()
    if not fruit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fruit not found")

    listing = FruitListing(
        fruit_id=fruit.id,
        seller_id=current_user.id,
        listing_type=payload.listing_type,
        requirement=payload.requirement,
        status=ListingStatus.open,
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.post("/listings/{listing_id}/cancel", response_model=ListingPublic)
def cancel_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.query(FruitListing).filter(FruitListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    if listing.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing")
    listing.status = ListingStatus.cancelled
    db.commit()
    db.refresh(listing)
    return listing


# ---------- Offers ----------

@router.post("/listings/{listing_id}/offers", response_model=OfferPublic)
def make_offer(
    listing_id: uuid.UUID,
    payload: OfferCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.query(FruitListing).filter(FruitListing.id == listing_id).first()
    if not listing or listing.status != ListingStatus.open:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not open for offers")
    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot offer on your own listing")

    offer = FruitOffer(
        listing_id=listing.id,
        buyer_id=current_user.id,
        offer_details=payload.offer_details,
        status=OfferStatus.pending,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def _get_offer_and_listing(offer_id: uuid.UUID, db: Session) -> tuple[FruitOffer, FruitListing]:
    offer = db.query(FruitOffer).filter(FruitOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    listing = db.query(FruitListing).filter(FruitListing.id == offer.listing_id).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return offer, listing


@router.post("/offers/{offer_id}/accept", response_model=OfferPublic)
def accept_offer(
    offer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offer, listing = _get_offer_and_listing(offer_id, db)
    if listing.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing")
    if listing.status != ListingStatus.open:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Listing is not open")

    offer.status = OfferStatus.accepted
    listing.status = ListingStatus.pending
    listing.accepted_offer_id = offer.id

    # reject every other pending offer on this listing
    others = (
        db.query(FruitOffer)
        .filter(FruitOffer.listing_id == listing.id, FruitOffer.id != offer.id)
        .all()
    )
    for other in others:
        if other.status == OfferStatus.pending:
            other.status = OfferStatus.rejected

    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/submit-proof", response_model=OfferPublic)
def submit_proof(
    offer_id: uuid.UUID,
    payload: SubmitProofRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offer, listing = _get_offer_and_listing(offer_id, db)
    if offer.buyer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your offer")
    if offer.status != OfferStatus.accepted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offer must be accepted first")

    offer.inventory_screenshot_url = payload.inventory_screenshot_url
    offer.status = OfferStatus.proof_submitted
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/confirm", response_model=OfferPublic)
def confirm_trade(
    offer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offer, listing = _get_offer_and_listing(offer_id, db)
    if listing.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing")
    if offer.status != OfferStatus.proof_submitted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Buyer hasn't submitted proof yet")

    offer.status = OfferStatus.confirmed
    listing.status = ListingStatus.completed
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/offers/{offer_id}/report-cheat", response_model=OfferPublic)
def report_cheat(
    offer_id: uuid.UUID,
    payload: ReportCheatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Seller flags a buyer as a cheater. This does NOT auto-ban — it flags the
    offer for an admin to review via /api/admin/users/ban, so bans are never
    applied on a single unverified accusation."""
    offer, listing = _get_offer_and_listing(offer_id, db)
    if listing.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your listing")

    offer.status = OfferStatus.flagged_cheat
    offer.cheat_report_reason = payload.reason
    listing.status = ListingStatus.open
    listing.accepted_offer_id = None
    db.commit()
    db.refresh(offer)
    return offer
