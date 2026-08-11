from fastapi import APIRouter, HTTPException, status

from app.services.youtube import get_subscriber_count

router = APIRouter(prefix="/api/channel", tags=["channel"])


@router.get("/stats")
def channel_stats():
    try:
        count = get_subscriber_count()
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Couldn't fetch subscriber count")
    return {"subscriber_count": count}