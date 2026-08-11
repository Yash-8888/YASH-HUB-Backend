import time
import requests

from app.config import settings

_cache: dict = {"count": None, "fetched_at": 0}
_CACHE_SECONDS = 300  # refetch at most every 5 minutes


def get_subscriber_count() -> int:
    now = time.time()
    if _cache["count"] is not None and (now - _cache["fetched_at"]) < _CACHE_SECONDS:
        return _cache["count"]

    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/channels",
        params={
            "part": "statistics",
            "id": settings.youtube_channel_id,
            "key": settings.youtube_api_key,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    count = int(data["items"][0]["statistics"]["subscriberCount"])

    _cache["count"] = count
    _cache["fetched_at"] = now
    return count    