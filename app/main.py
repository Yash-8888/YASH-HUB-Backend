from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, users, giveaways, rewards, announcements, leaderboard, admin, channel, ads, trades

app = FastAPI(title="Candy Hub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(giveaways.router)
app.include_router(rewards.router)
app.include_router(announcements.router)
app.include_router(leaderboard.router)
app.include_router(admin.router)
app.include_router(channel.router)
app.include_router(ads.router)
app.include_router(trades.router)


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok"}
