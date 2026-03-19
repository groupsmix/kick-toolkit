import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.bot import router as bot_router, mod_router
from app.routers.chatlogs import router as chatlogs_router
from app.routers.giveaway import router as giveaway_router
from app.routers.antialt import router as antialt_router
from app.routers.tournament import router as tournament_router
from app.routers.ideas import router as ideas_router
from app.services.db import init_pool, close_pool, create_tables, seed_demo_data, get_conn


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


app = FastAPI(title="Kick Toolkit API", version="1.0.0", lifespan=lifespan)

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
app.include_router(tournament_router)
app.include_router(ideas_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/dashboard/stats")
async def dashboard_stats():
    async with get_conn() as conn:
        row = await conn.execute("SELECT count(*) AS cnt FROM chat_logs")
        total_messages = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM chat_logs WHERE flagged = TRUE")
        flagged_messages = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(DISTINCT username) AS cnt FROM chat_logs")
        unique_users = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM giveaways WHERE status = 'active'")
        active_giveaways = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM tournaments WHERE status IN ('registration', 'in_progress')")
        active_tournaments = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM flagged_accounts")
        flagged_accounts_count = (await row.fetchone())["cnt"]

        row = await conn.execute("SELECT count(*) AS cnt FROM bot_commands")
        total_commands = (await row.fetchone())["cnt"]

    moderation_rate = round(flagged_messages / max(total_messages, 1) * 100, 1)

    return {
        "total_messages": total_messages,
        "flagged_messages": flagged_messages,
        "unique_users": unique_users,
        "active_giveaways": active_giveaways,
        "active_tournaments": active_tournaments,
        "flagged_accounts": flagged_accounts_count,
        "total_commands": total_commands,
        "moderation_rate": moderation_rate,
    }
