import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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
from app.routers.polls import router as polls_router
from app.routers.predictions import router as predictions_router
from app.routers.translation import router as translation_router
from app.routers.activity import router as activity_router
from app.dependencies import get_channel_from_session, require_auth, require_channel_owner
from app.repositories import dashboard as dashboard_repo
from app.services.db import get_conn, init_pool, close_pool, create_tables, seed_demo_data
from app.services.http_client import close_all as close_all_http_clients
from app.services.redis_cache import init_redis, close_redis, check_rate_limit

# Structured logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate limiter — uses Redis when available, falls back to in-memory
# ---------------------------------------------------------------------------

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 60     # requests per window


# Trusted reverse-proxy IPs (comma-separated).  Only when a request arrives
# from one of these addresses will the X-Forwarded-For header be trusted.
TRUSTED_PROXIES: set[str] = {
    ip.strip()
    for ip in os.environ.get("TRUSTED_PROXY_IPS", "").split(",")
    if ip.strip()
}


def _get_client_ip(request: Request) -> str:
    """Extract real client IP.  Only trusts X-Forwarded-For from configured proxies.

    Uses the rightmost untrusted IP to prevent spoofing via a forged
    X-Forwarded-For header.
    """
    client_ip = request.client.host if request.client else "unknown"

    if TRUSTED_PROXIES and client_ip in TRUSTED_PROXIES:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            ips = [ip.strip() for ip in forwarded.split(",")]
            # Walk from the right; the first IP not in TRUSTED_PROXIES is
            # the real client IP (rightmost untrusted).
            for ip in reversed(ips):
                if ip not in TRUSTED_PROXIES:
                    return ip
            return ips[0]

    return client_ip


async def _rate_limit(request: Request) -> None:
    """Check rate limit per client IP. Raises 429 if exceeded."""
    client_ip = _get_client_ip(request)
    allowed = await check_rate_limit(client_ip, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many requests")


ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173",
).split(",")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response to mitigate XSS and other attacks."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' https://kick.com https://*.kick.com; "
            "connect-src 'self' https://api.kick.com https://id.kick.com; "
            "frame-ancestors 'none'"
        )
        return response


async def _cleanup_expired_sessions() -> None:
    """Delete expired sessions and stale pending_auth entries periodically."""
    while True:
        try:
            await asyncio.sleep(3600)  # every hour
            async with get_conn() as conn:
                await conn.execute(
                    "DELETE FROM sessions WHERE expires_at < %s",
                    (datetime.now(timezone.utc).isoformat(),),
                )
                await conn.commit()
            logger.info("Expired session cleanup completed")
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Session cleanup failed")


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_pool()
    await init_redis()
    await create_tables()
    await seed_demo_data()
    cleanup_task = asyncio.create_task(_cleanup_expired_sessions())
    yield
    cleanup_task.cancel()
    # Close all shared HTTP client singletons
    await close_all_http_clients()
    await close_redis()
    await close_pool()


app = FastAPI(
    title="Kick Toolkit API",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(_rate_limit)],
)

app.add_middleware(SecurityHeadersMiddleware)
# CSRF note: Cookie-based session auth is now used. The SameSite=Lax attribute on
# the session cookie prevents CSRF for state-changing requests from cross-origin
# contexts. The Authorization header fallback is kept for backwards compatibility
# and API clients. The CORS policy restricts origins to the frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
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
app.include_router(polls_router)
app.include_router(predictions_router)
app.include_router(translation_router)
app.include_router(activity_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/dashboard/stats")
async def dashboard_stats(session: dict = Depends(require_auth)):
    channel = get_channel_from_session(session)
    if not channel:
        raise HTTPException(status_code=400, detail="No channel associated with session")
    require_channel_owner(session, channel)
    return await dashboard_repo.get_stats(channel)
