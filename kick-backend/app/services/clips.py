"""AI Clip Pipeline service.

Detects hype moments from chat data and generates AI captions for clips.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

from app.repositories import clips as clips_repo
from app.services.db import get_conn

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


async def detect_hype_moments(channel: str, window_minutes: int = 60) -> list[dict]:
    """Analyze chat logs for hype moments based on message frequency spikes."""
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT
                 date_trunc('minute', timestamp::timestamptz) AS minute_bucket,
                 count(*) AS msg_count,
                 count(DISTINCT username) AS unique_chatters,
                 array_agg(message ORDER BY timestamp DESC) AS messages
               FROM chat_logs
               WHERE channel = %s
               AND timestamp >= (NOW() - INTERVAL '%s minutes')::text
               GROUP BY minute_bucket
               ORDER BY minute_bucket ASC""",
            (channel, window_minutes),
        )
        buckets = [dict(r) for r in await cur.fetchall()]

    if len(buckets) < 3:
        return []

    # Calculate average message rate
    avg_rate = sum(b["msg_count"] for b in buckets) / len(buckets)
    if avg_rate == 0:
        return []

    # Detect spikes (2x+ the average)
    moments = []
    for i, bucket in enumerate(buckets):
        intensity = bucket["msg_count"] / avg_rate if avg_rate > 0 else 0
        if intensity >= 2.0:
            ts = bucket["minute_bucket"]
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            end_ts = (ts + timedelta(minutes=1)).isoformat() if hasattr(ts, "isoformat") else str(ts)

            messages_list = bucket.get("messages", [])
            sample = messages_list[:5] if isinstance(messages_list, list) else []

            moment = await clips_repo.create_hype_moment(
                channel=channel,
                session_id=None,
                timestamp_start=ts_str,
                timestamp_end=end_ts,
                intensity=round(intensity, 2),
                trigger_type="chat_spike",
                message_count=bucket["msg_count"],
                peak_rate=float(bucket["msg_count"]),
                sample_messages=sample,
            )
            moments.append(moment)

    return moments


async def generate_caption(clip_id: str, style: str = "engaging") -> str:
    """Generate an AI caption for a clip using OpenAI."""
    clip = await clips_repo.get_clip(clip_id)
    if not clip:
        return ""

    # Get context from the hype moment if available
    context = ""
    if clip.get("hype_moment_id"):
        moment = await clips_repo.get_hype_moment(clip["hype_moment_id"])
        if moment:
            samples = moment.get("sample_messages", [])
            context = f"\nChat context during the moment: {', '.join(samples[:5])}"

    if not OPENAI_API_KEY:
        # Fallback caption without AI
        style_templates = {
            "engaging": f"Check out this insane moment! {clip.get('title', 'Epic clip')} - Follow for more!",
            "funny": f"When the stream gets wild... {clip.get('title', '')} - You had to be there!",
            "informative": f"{clip.get('title', 'Stream highlight')} - {clip.get('description', 'An amazing moment from the stream')}",
            "trending": f"POV: {clip.get('title', 'This moment')} #streaming #gaming #kick",
        }
        caption = style_templates.get(style, style_templates["engaging"])
        await clips_repo.update_clip(clip_id, caption=caption)
        return caption

    prompt = f"""Generate a short, catchy social media caption for a streaming clip.

Title: {clip.get('title', 'Untitled')}
Description: {clip.get('description', 'A highlight clip from a live stream')}
Style: {style} (make it {style})
{context}

Requirements:
- Keep it under 200 characters
- Include 2-3 relevant hashtags
- Make it attention-grabbing for TikTok/YouTube Shorts/Reels
- Don't use quotes around the caption"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.8,
                },
            )
        if response.status_code == 200:
            data = response.json()
            caption = data["choices"][0]["message"]["content"].strip().strip('"')
            await clips_repo.update_clip(clip_id, caption=caption)
            return caption
    except Exception:
        logger.exception("Failed to generate AI caption")

    fallback = f"{clip.get('title', 'Epic moment')} - Follow for more! #streaming #kick"
    await clips_repo.update_clip(clip_id, caption=fallback)
    return fallback


async def post_to_platform(clip_id: str, platform: str, caption: str) -> dict:
    """Create a post record for a clip. Actual API posting is placeholder."""
    post = await clips_repo.create_clip_post(
        clip_id=clip_id,
        platform=platform,
        caption=caption,
    )

    # In a real implementation, this would call TikTok/YouTube/Instagram APIs
    # For now, mark as "ready" since we need API keys to actually post
    await clips_repo.update_clip_post(
        post_id=post["id"],
        status="ready",
        error_message="Platform API integration pending — clip is ready for manual upload",
    )
    post["status"] = "ready"
    post["error_message"] = "Platform API integration pending — clip is ready for manual upload"
    return post
