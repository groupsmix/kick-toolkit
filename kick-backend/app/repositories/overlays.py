"""Repository for OBS overlay widget settings."""

import json
import secrets
from typing import Optional

from app.services.db import get_conn, _generate_id, _now_iso


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


async def list_overlays(channel: str) -> list[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM overlay_settings WHERE channel = %s ORDER BY overlay_type",
            (channel,),
        )
        results = await row.fetchall()
    return [dict(r) for r in results]


async def get_overlay(channel: str, overlay_type: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM overlay_settings WHERE channel = %s AND overlay_type = %s",
            (channel, overlay_type),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def upsert_overlay(
    channel: str, overlay_type: str, enabled: bool, config: dict,
) -> dict:
    now = _now_iso()
    overlay_id = _generate_id()
    token = _generate_token()
    async with get_conn() as conn:
        # Check if exists to preserve existing token
        row = await conn.execute(
            "SELECT token FROM overlay_settings WHERE channel = %s AND overlay_type = %s",
            (channel, overlay_type),
        )
        existing = await row.fetchone()
        if existing:
            token = existing["token"]

        await conn.execute(
            """INSERT INTO overlay_settings
               (id, channel, overlay_type, enabled, token, config, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel, overlay_type) DO UPDATE SET
                   enabled = EXCLUDED.enabled, config = EXCLUDED.config,
                   updated_at = EXCLUDED.updated_at""",
            (overlay_id, channel, overlay_type, enabled, token, json.dumps(config), now, now),
        )
        await conn.commit()
    return {
        "id": overlay_id, "channel": channel, "overlay_type": overlay_type,
        "enabled": enabled, "token": token, "config": config,
        "created_at": now, "updated_at": now,
    }


async def regenerate_token(channel: str, overlay_type: str) -> Optional[dict]:
    new_token = _generate_token()
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE overlay_settings SET token = %s, updated_at = %s
               WHERE channel = %s AND overlay_type = %s RETURNING *""",
            (new_token, now, channel, overlay_type),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def get_overlay_by_token(token: str) -> Optional[dict]:
    """Look up overlay config by token (for public overlay rendering)."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM overlay_settings WHERE token = %s AND enabled = TRUE",
            (token,),
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def init_default_overlays(channel: str) -> list[dict]:
    """Create default overlay settings for all types if they don't exist."""
    overlay_types = ["chat", "alerts", "giveaway", "nowplaying"]
    results = []
    for otype in overlay_types:
        existing = await get_overlay(channel, otype)
        if not existing:
            result = await upsert_overlay(channel, otype, True, _default_config(otype))
            results.append(result)
        else:
            results.append(existing)
    return results


def _default_config(overlay_type: str) -> dict:
    configs = {
        "chat": {
            "font_size": 14,
            "show_badges": True,
            "show_timestamps": False,
            "max_messages": 25,
            "fade_delay": 30,
            "background_opacity": 0.5,
            "text_color": "#ffffff",
        },
        "alerts": {
            "duration": 5,
            "animation": "slideIn",
            "sound_enabled": True,
            "show_follower": True,
            "show_subscriber": True,
            "show_raid": True,
            "font_size": 24,
        },
        "giveaway": {
            "show_entries": True,
            "show_timer": True,
            "show_keyword": True,
            "animation": "bounce",
            "background_opacity": 0.8,
        },
        "nowplaying": {
            "show_artist": True,
            "show_title": True,
            "show_game": True,
            "show_viewers": False,
            "position": "bottom-left",
            "background_opacity": 0.7,
        },
    }
    return configs.get(overlay_type, {})
