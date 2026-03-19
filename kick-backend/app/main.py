from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.bot import router as bot_router, mod_router
from app.routers.chatlogs import router as chatlogs_router
from app.routers.giveaway import router as giveaway_router
from app.routers.antialt import router as antialt_router
from app.routers.tournament import router as tournament_router
from app.routers.ideas import router as ideas_router

app = FastAPI(title="Kick Toolkit API", version="1.0.0")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
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
    from app.services.database import chat_logs, giveaways, tournaments, flagged_accounts, bot_commands

    active_giveaways = sum(1 for g in giveaways.values() if g["status"] == "active")
    active_tournaments = sum(1 for t in tournaments.values() if t["status"] in ["registration", "in_progress"])
    total_commands = sum(len(cmds) for cmds in bot_commands.values())

    return {
        "total_messages": len(chat_logs),
        "flagged_messages": sum(1 for l in chat_logs if l["flagged"]),
        "unique_users": len(set(l["username"] for l in chat_logs)),
        "active_giveaways": active_giveaways,
        "active_tournaments": active_tournaments,
        "flagged_accounts": len(flagged_accounts),
        "total_commands": total_commands,
        "moderation_rate": round(sum(1 for l in chat_logs if l["flagged"]) / max(len(chat_logs), 1) * 100, 1),
    }
