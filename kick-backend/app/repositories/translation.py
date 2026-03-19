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


async def upsert_settings(channel: str, enabled: Optional[bool] = None,
                          target_language: Optional[str] = None,
                          auto_translate: Optional[bool] = None) -> dict:
    now = _now_iso()
    existing = await get_settings(channel)
    if existing:
        e = enabled if enabled is not None else existing["enabled"]
        t = target_language if target_language is not None else existing["target_language"]
        a = auto_translate if auto_translate is not None else existing["auto_translate"]
        async with get_conn() as conn:
            await conn.execute(
                """UPDATE translation_settings SET enabled = %s, target_language = %s,
                   auto_translate = %s, updated_at = %s WHERE channel = %s""",
                (e, t, a, now, channel),
            )
            await conn.commit()
    else:
        e = enabled if enabled is not None else False
        t = target_language if target_language is not None else "en"
        a = auto_translate if auto_translate is not None else False
        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO translation_settings (channel, enabled, target_language, auto_translate, updated_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (channel, e, t, a, now),
            )
            await conn.commit()
    return {"channel": channel, "enabled": e, "target_language": t, "auto_translate": a, "updated_at": now}
