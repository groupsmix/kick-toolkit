"""Anti-cheat system router for raid detection, giveaway fraud, and queue integrity."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth, require_channel_owner
from app.models.schemas import (
    RaidEvent,
    RaidSettings,
    GiveawayFraudFlag,
    FraudReviewRequest,
)
from app.services import raid_detection as raid_svc
from app.services import giveaway_fraud as fraud_svc
from app.repositories import anticheat as anticheat_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/anticheat", tags=["anticheat"])


# ========== Raid Detection ==========


@router.get("/raids")
async def list_raids(
    channel: str,
    session: dict = Depends(require_auth),
) -> list[RaidEvent]:
    require_channel_owner(session, channel)
    rows = await anticheat_repo.list_raids(channel)
    return [RaidEvent(**r) for r in rows]


@router.post("/raids/{raid_id}/resolve")
async def resolve_raid(raid_id: int, session: dict = Depends(require_auth)) -> dict:
    result = await anticheat_repo.resolve_raid(raid_id)
    if not result:
        raise HTTPException(status_code=404, detail="Raid event not found")
    require_channel_owner(session, result["channel"])
    logger.info("Raid %d resolved", raid_id)
    return {"status": "resolved", "raid": result}


@router.get("/raid-settings")
async def get_raid_settings(session: dict = Depends(require_auth)) -> RaidSettings:
    settings = await anticheat_repo.get_raid_settings()
    return RaidSettings(**settings)


@router.put("/raid-settings")
async def update_raid_settings(
    settings: RaidSettings,
    channel: str,
    session: dict = Depends(require_auth),
) -> RaidSettings:
    require_channel_owner(session, channel)
    result = await anticheat_repo.upsert_raid_settings(
        settings.enabled,
        settings.new_chatter_threshold,
        settings.window_seconds,
        settings.auto_action,
        settings.min_account_age_days,
    )
    logger.info("Raid settings updated by channel=%s", channel)
    return RaidSettings(**result)


@router.post("/raids/check")
async def check_raid(channel: str, session: dict = Depends(require_auth)) -> dict:
    """Manually trigger a raid check for a channel."""
    require_channel_owner(session, channel)
    result = await raid_svc.check_for_raid(channel)
    if result:
        return {"detected": True, "raid": result}
    return {"detected": False}


# ========== Giveaway Fraud ==========


@router.get("/giveaway-fraud/{giveaway_id}")
async def get_giveaway_fraud_flags(
    giveaway_id: str,
    session: dict = Depends(require_auth),
) -> list[GiveawayFraudFlag]:
    rows = await fraud_svc.get_fraud_flags(giveaway_id)
    return [GiveawayFraudFlag(**r) for r in rows]


@router.post("/giveaway-fraud/{giveaway_id}/analyze")
async def analyze_giveaway(
    giveaway_id: str,
    session: dict = Depends(require_auth),
) -> dict:
    """Run fraud analysis on all entries in a giveaway."""
    # Get channel from giveaway
    from app.services.db import get_conn
    async with get_conn() as conn:
        row = await conn.execute("SELECT channel FROM giveaways WHERE id = %s", (giveaway_id,))
        gw = await row.fetchone()
    if not gw:
        raise HTTPException(status_code=404, detail="Giveaway not found")
    require_channel_owner(session, gw["channel"])

    flags = await fraud_svc.analyze_giveaway_entries(giveaway_id, gw["channel"])
    return {"giveaway_id": giveaway_id, "fraud_flags": len(flags), "flags": flags}


@router.post("/giveaway-fraud/review")
async def review_fraud_flag(
    req: FraudReviewRequest,
    session: dict = Depends(require_auth),
) -> dict:
    result = await fraud_svc.review_fraud_flag(req.flag_id, req.action)
    if not result:
        raise HTTPException(status_code=404, detail="Fraud flag not found")
    logger.info("Fraud flag %d reviewed: %s", req.flag_id, req.action)
    return {"status": "reviewed", "flag": result}
