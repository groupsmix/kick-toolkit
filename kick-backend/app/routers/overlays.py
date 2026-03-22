"""OBS Overlay Widgets router."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import require_auth
from app.models.schemas import OverlaySettingsUpdate
from app.repositories import overlays as overlays_repo
from app.services.db import get_conn, _generate_id, _now_iso
from app.services.wordcloud import extract_word_frequencies

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/overlays", tags=["overlays"])


@router.get("/{channel}")
async def list_overlays(channel: str, _session: dict = Depends(require_auth)) -> list[dict]:
    overlays = await overlays_repo.list_overlays(channel)
    if not overlays:
        overlays = await overlays_repo.init_default_overlays(channel)
    return overlays


@router.get("/{channel}/{overlay_type}")
async def get_overlay(
    channel: str, overlay_type: str, _session: dict = Depends(require_auth)
) -> dict:
    overlay = await overlays_repo.get_overlay(channel, overlay_type)
    if not overlay:
        result = await overlays_repo.upsert_overlay(channel, overlay_type, True, {})
        return result
    return overlay


@router.put("/{channel}/{overlay_type}")
async def update_overlay(
    channel: str, overlay_type: str, body: OverlaySettingsUpdate,
    _session: dict = Depends(require_auth),
) -> dict:
    existing = await overlays_repo.get_overlay(channel, overlay_type)
    config = body.config if body.config is not None else (existing["config"] if existing else {})
    enabled = body.enabled if body.enabled is not None else (existing["enabled"] if existing else True)
    result = await overlays_repo.upsert_overlay(channel, overlay_type, enabled, config)
    logger.info("Overlay %s updated for channel=%s", overlay_type, channel)
    return result


@router.post("/{channel}/{overlay_type}/regenerate-token")
async def regenerate_token(
    channel: str, overlay_type: str, _session: dict = Depends(require_auth)
) -> dict:
    result = await overlays_repo.regenerate_token(channel, overlay_type)
    if not result:
        raise HTTPException(status_code=404, detail="Overlay not found")
    logger.info("Overlay token regenerated for %s in channel=%s", overlay_type, channel)
    return result


# Public endpoint for OBS browser source (token-based auth, no session needed)
@router.get("/render/{token}")
async def render_overlay(token: str) -> dict:
    overlay = await overlays_repo.get_overlay_by_token(token)
    if not overlay:
        raise HTTPException(status_code=404, detail="Invalid or disabled overlay token")
    return {
        "channel": overlay["channel"],
        "overlay_type": overlay["overlay_type"],
        "config": overlay["config"],
    }


# ========== Word Cloud Overlay ==========
@router.get("/wordcloud/{channel}")
async def get_wordcloud(
    channel: str,
    minutes: int = Query(default=30, le=1440),
    max_words: int = Query(default=80, le=200),
    _session: dict = Depends(require_auth),
) -> dict:
    """Get word frequencies from recent chat messages for word cloud overlay."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT message FROM chat_logs
               WHERE channel = %s
                 AND timestamp >= (NOW() - make_interval(mins => %s))::text
               ORDER BY timestamp DESC LIMIT 5000""",
            (channel, minutes),
        )
        rows = await row.fetchall()

    messages = [r["message"] for r in rows]
    words = extract_word_frequencies(messages, max_words=max_words)
    return {"channel": channel, "minutes": minutes, "total_messages": len(messages), "words": words}


# ========== Alert Queue ==========
@router.post("/alerts/{channel}/trigger")
async def trigger_alert(
    channel: str, body: dict, _session: dict = Depends(require_auth)
) -> dict:
    """Manually trigger a test alert."""
    alert_type = body.get("alert_type", "follow")
    data = body.get("data", {})
    alert_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO alert_queue (id, channel, alert_type, data, status, created_at)
               VALUES (%s, %s, %s, %s, 'pending', %s)""",
            (alert_id, channel, alert_type, json.dumps(data), now),
        )
        await conn.commit()
    logger.info("Alert triggered: type=%s channel=%s", alert_type, channel)
    return {"id": alert_id, "channel": channel, "alert_type": alert_type, "data": data, "status": "pending", "created_at": now}


@router.get("/alerts/{channel}/queue")
async def get_alert_queue(
    channel: str,
    status: str = Query(default="pending"),
    limit: int = Query(default=10, le=50),
    _session: dict = Depends(require_auth),
) -> list[dict]:
    """Get pending alerts from the queue."""
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT * FROM alert_queue WHERE channel = %s AND status = %s
               ORDER BY created_at ASC LIMIT %s""",
            (channel, status, limit),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


@router.post("/alerts/{channel}/mark-displayed")
async def mark_alert_displayed(
    channel: str, body: dict, _session: dict = Depends(require_auth)
) -> dict:
    """Mark an alert as displayed."""
    alert_id = body.get("alert_id", "")
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """UPDATE alert_queue SET status = 'displayed', displayed_at = %s
               WHERE id = %s AND channel = %s""",
            (now, alert_id, channel),
        )
        await conn.commit()
    return {"id": alert_id, "status": "displayed"}
