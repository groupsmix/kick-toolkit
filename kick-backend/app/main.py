import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.bot import router as bot_router, mod_router
from app.routers.chatlogs import router as chatlogs_router
from app.routers.giveaway import router as giveaway_router
from app.routers.antialt import router as antialt_router
from app.routers.anticheat import router as anticheat_router
from app.routers.tournament import router as tournament_router
from app.routers.ideas import router as ideas_router
from app.routers.subscription import router as subscription_router, webhook_router
from app.routers.analytics import router as analytics_router
from app.routers.stream_coach import router as stream_coach_router
from app.routers.clips import router as clips_router
from app.routers.heatmap import router as heatmap_router
from app.routers.whitelabel import router as whitelabel_router
from app.routers.loyalty import router as loyalty_router
from app.routers.songs import router as songs_router
from app.routers.schedule import router as schedule_router
from app.routers.profiles import router as profiles_router
from app.routers.overlays import router as overlays_router
from app.routers.marketplace import router as marketplace_router
from app.routers.stream_intel import router as stream_intel_router
from app.routers.viewer_crm import router as viewer_crm_router
from app.routers.debrief import router as debrief_router
from app.routers.discord_bot import router as discord_bot_router
from app.routers.revenue import router as revenue_router
from app.routers.highlights import router as highlights_router
from app.routers.timed_messages import router as timed_messages_router
from app.routers.polls import router as polls_router
from app.routers.predictions import router as predictions_router
from app.routers.translation import router as translation_router
from app.routers.viewer_count import router as viewer_count_router
from app.routers.game_queue import router as game_queue_router
from app.routers.match_history import router as match_history_router
from app.routers.kd_counter import router as kd_counter_router
from app.routers.achievements import router as achievements_router
from app.routers.game_challenges import router as game_challenges_router
from app.routers.rank_tracker import router as rank_tracker_router
from app.routers.gambling import router as gambling_router
from app.routers.irl import router as irl_router
from app.routers.creative import router as creative_router
from app.dependencies import require_auth
from app.repositories import dashboard as dashboard_repo
from app.services.db import init_pool, close_pool, create_tables, seed_demo_data

# Structured logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Simple in-memory rate limiter
# ---------------------------------------------------------------------------

_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 60     # requests per window


async def _rate_limit(request: Request) -> None:
    """Check rate limit per client IP. Raises 429 if exceeded."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    timestamps = _rate_store[client_ip]
    # Remove expired entries
    _rate_store[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_store[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many requests")
    _rate_store[client_ip].append(now)


ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://kick-toolkit.pages.dev,https://api.zidni.store",
).split(",")


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_pool()
    await create_tables()
    await seed_demo_data()
    yield
    await close_pool()


app = FastAPI(
    title="Kick Toolkit API",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(_rate_limit)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(bot_router)
app.include_router(mod_router)
app.include_router(chatlogs_router)
app.include_router(giveaway_router)
app.include_router(antialt_router)
app.include_router(anticheat_router)
app.include_router(tournament_router)
app.include_router(ideas_router)
app.include_router(subscription_router)
app.include_router(webhook_router)
app.include_router(analytics_router)
app.include_router(stream_coach_router)
app.include_router(clips_router)
app.include_router(heatmap_router)
app.include_router(whitelabel_router)
app.include_router(loyalty_router)
app.include_router(songs_router)
app.include_router(schedule_router)
app.include_router(profiles_router)
app.include_router(overlays_router)
app.include_router(marketplace_router)
app.include_router(stream_intel_router)
app.include_router(viewer_crm_router)
app.include_router(debrief_router)
app.include_router(discord_bot_router)
app.include_router(revenue_router)
app.include_router(highlights_router)
app.include_router(timed_messages_router)
app.include_router(polls_router)
app.include_router(predictions_router)
app.include_router(translation_router)
app.include_router(viewer_count_router)
app.include_router(game_queue_router)
app.include_router(match_history_router)
app.include_router(kd_counter_router)
app.include_router(achievements_router)
app.include_router(game_challenges_router)
app.include_router(rank_tracker_router)
app.include_router(gambling_router)
app.include_router(irl_router)
app.include_router(creative_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/dashboard/stats")
async def dashboard_stats(_session: dict = Depends(require_auth)):
    return await dashboard_repo.get_stats()
