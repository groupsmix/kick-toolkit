"""Repository for public streamer profiles."""

import json
from typing import Optional

from app.services.db import get_conn, _now_iso


async def get_profile(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM streamer_profiles WHERE channel = %s", (channel,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def upsert_profile(
    channel: str,
    display_name: str,
    bio: str,
    avatar_url: Optional[str],
    banner_url: Optional[str],
    social_links: dict,
    is_public: bool,
    theme_color: str,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO streamer_profiles
               (channel, display_name, bio, avatar_url, banner_url, social_links,
                is_public, theme_color, total_followers, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   display_name = EXCLUDED.display_name, bio = EXCLUDED.bio,
                   avatar_url = EXCLUDED.avatar_url, banner_url = EXCLUDED.banner_url,
                   social_links = EXCLUDED.social_links, is_public = EXCLUDED.is_public,
                   theme_color = EXCLUDED.theme_color, updated_at = EXCLUDED.updated_at""",
            (channel, display_name, bio, avatar_url, banner_url,
             json.dumps(social_links), is_public, theme_color, now),
        )
        await conn.commit()
    return {
        "channel": channel, "display_name": display_name, "bio": bio,
        "avatar_url": avatar_url, "banner_url": banner_url,
        "social_links": social_links, "is_public": is_public,
        "theme_color": theme_color, "updated_at": now,
    }


async def update_profile(channel: str, **kwargs: object) -> Optional[dict]:
    set_parts = []
    values = []
    for key, value in kwargs.items():
        if value is not None:
            if key == "social_links":
                set_parts.append(f"{key} = %s")
                values.append(json.dumps(value))
            else:
                set_parts.append(f"{key} = %s")
                values.append(value)

    if not set_parts:
        return await get_profile(channel)

    now = _now_iso()
    set_parts.append("updated_at = %s")
    values.append(now)
    values.append(channel)

    async with get_conn() as conn:
        row = await conn.execute(
            f"UPDATE streamer_profiles SET {', '.join(set_parts)} WHERE channel = %s RETURNING *",
            tuple(values),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def get_public_profile(channel: str) -> Optional[dict]:
    """Get a public profile for display on profile pages."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM streamer_profiles WHERE channel = %s AND is_public = TRUE",
            (channel,),
        )
        result = await row.fetchone()
    return dict(result) if result else None
