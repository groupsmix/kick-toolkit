"""Hype detection service — analyzes chat activity to find highlight moments."""

import statistics
from collections import defaultdict

from app.services.db import get_conn


async def detect_hype_moments(
    channel: str,
    session_id: str | None = None,
    window_seconds: int = 60,
    spike_threshold: float = 2.0,
    min_messages: int = 5,
) -> list[dict]:
    """Analyze chat_logs to detect message rate spikes indicating hype moments.

    Algorithm:
    1. Fetch chat messages for the channel (optionally filtered by session).
    2. Bucket messages into time windows (default 60s).
    3. Calculate mean and std deviation of message rates.
    4. Flag windows where rate > mean + (spike_threshold * std_dev).
    5. Extract sample messages and classify category.
    """
    async with get_conn() as conn:
        if session_id:
            cur = await conn.execute(
                """SELECT username, message, timestamp FROM chat_logs
                   WHERE channel = %s AND session_id = %s
                   ORDER BY timestamp ASC""",
                (channel, session_id),
            )
        else:
            cur = await conn.execute(
                """SELECT username, message, timestamp FROM chat_logs
                   WHERE channel = %s
                   ORDER BY timestamp DESC LIMIT 10000""",
                (channel,),
            )
        rows = await cur.fetchall()

    if len(rows) < min_messages:
        return []

    # Parse timestamps and bucket into windows
    buckets: dict[int, list[dict]] = defaultdict(list)
    timestamps = []
    for row in rows:
        ts_str = row["timestamp"]
        # Parse ISO timestamp to epoch seconds
        try:
            from datetime import datetime, timezone
            if "T" in ts_str:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(ts_str)
            epoch = int(dt.timestamp())
        except (ValueError, TypeError):
            continue
        timestamps.append(epoch)
        bucket_key = epoch // window_seconds
        buckets[bucket_key].append({
            "username": row["username"],
            "message": row["message"],
            "timestamp": ts_str,
        })

    if not buckets:
        return []

    # Calculate message rates per bucket
    bucket_keys = sorted(buckets.keys())
    rates = [len(buckets[k]) for k in bucket_keys]

    if len(rates) < 3:
        return []

    mean_rate = statistics.mean(rates)
    std_rate = statistics.stdev(rates) if len(rates) > 1 else 0.0

    if std_rate == 0:
        return []

    threshold = mean_rate + (spike_threshold * std_rate)

    # Detect spikes
    moments = []
    first_ts = min(timestamps) if timestamps else 0

    for key in bucket_keys:
        rate = len(buckets[key])
        if rate >= threshold and rate >= min_messages:
            offset_seconds = (key * window_seconds) - first_ts
            if offset_seconds < 0:
                offset_seconds = 0

            # Calculate intensity (0-100 scale)
            intensity = min(100.0, ((rate - mean_rate) / std_rate) * 25 + 50)

            # Get sample messages (top 5)
            msgs = buckets[key]
            sample = [m["message"] for m in msgs[:5]]

            # Classify category based on message content
            category = _classify_category(sample)

            # Description
            description = f"Chat spike: {rate} messages in {window_seconds}s ({rate / mean_rate:.1f}x normal rate)"

            moments.append({
                "timestamp_offset_seconds": max(0, offset_seconds),
                "intensity": round(intensity, 1),
                "message_rate": round(rate / (window_seconds / 60), 1),
                "duration_seconds": window_seconds,
                "description": description,
                "sample_messages": sample,
                "category": category,
            })

    # Sort by intensity descending
    moments.sort(key=lambda m: m["intensity"], reverse=True)
    return moments


def _classify_category(messages: list[str]) -> str:
    """Classify hype moment category based on message content."""
    text = " ".join(messages).lower()

    hype_words = {"hype", "lets go", "letsgo", "pog", "poggers", "gg", "insane", "clutch", "ace", "goat"}
    funny_words = {"lol", "lmao", "lmfao", "haha", "rofl", "bruh", "kekw", "lul", "comedy"}
    rage_words = {"rage", "mald", "tilted", "trash", "wtf", "rigged", "scam"}
    sad_words = {"sadge", "sad", "rip", "unlucky", "pain", "feelsbad"}

    scores = {
        "hype": sum(1 for w in hype_words if w in text),
        "funny": sum(1 for w in funny_words if w in text),
        "rage": sum(1 for w in rage_words if w in text),
        "sad": sum(1 for w in sad_words if w in text),
    }

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "hype"
