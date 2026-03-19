"""OBS Overlay Widgets router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_auth
from app.models.schemas import OverlaySettingsUpdate
from app.repositories import overlays as overlays_repo

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
