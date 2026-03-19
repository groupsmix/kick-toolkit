"""Repository for translation settings."""

from typing import Optional

from app.services.db import get_conn, _now_iso


async def get_settings(channel: str) -> Optional[dict]:
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM translation_settings WHERE channel = %s", (channel,)
        )
        result = await row.fetchone()
    return dict(result) if result else None


async def upsert_settings(
    channel: str,
    enabled: bool,
    target_language: str,
    auto_translate: bool,
    show_original: bool,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO translation_settings
               (channel, enabled, target_language, auto_translate, show_original, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (channel) DO UPDATE SET
                   enabled = EXCLUDED.enabled,
                   target_language = EXCLUDED.target_language,
                   auto_translate = EXCLUDED.auto_translate,
                   show_original = EXCLUDED.show_original,
                   updated_at = EXCLUDED.updated_at""",
            (channel, enabled, target_language, auto_translate, show_original, now),
        )
        await conn.commit()
    return {
        "channel": channel, "enabled": enabled,
        "target_language": target_language,
        "auto_translate": auto_translate,
        "show_original": show_original,
        "updated_at": now,
    }
