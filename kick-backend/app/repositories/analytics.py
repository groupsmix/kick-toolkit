"""Repository for Predictive Analytics data access."""

import json

from app.services.db import get_conn, _generate_id, _now_iso


# ---------------------------------------------------------------------------
# Streamer Snapshots
# ---------------------------------------------------------------------------

async def create_snapshot(
    channel: str,
    avg_viewers: float = 0.0,
    peak_viewers: int = 0,
    follower_count: int = 0,
    subscriber_count: int = 0,
    hours_streamed: float = 0.0,
    chat_messages: int = 0,
    categories: list[str] | None = None,
) -> dict:
    snap_id = _generate_id()
    now = _now_iso()
    cats = json.dumps(categories or [])
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO streamer_snapshots
               (id, channel, avg_viewers, peak_viewers, follower_count,
                subscriber_count, hours_streamed, chat_messages, categories, recorded_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (snap_id, channel, avg_viewers, peak_viewers, follower_count,
             subscriber_count, hours_streamed, chat_messages, cats, now),
        )
        await conn.commit()
    return {
        "id": snap_id, "channel": channel, "avg_viewers": avg_viewers,
        "peak_viewers": peak_viewers, "follower_count": follower_count,
        "subscriber_count": subscriber_count, "hours_streamed": hours_streamed,
        "chat_messages": chat_messages, "categories": categories or [],
        "recorded_at": now,
    }


async def get_snapshots(channel: str, limit: int = 30) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM streamer_snapshots
               WHERE channel = %s ORDER BY recorded_at DESC LIMIT %s""",
            (channel, limit),
        )
        rows = await cur.fetchall()
    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("categories"), str):
            d["categories"] = json.loads(d["categories"])
        results.append(d)
    return results


async def get_latest_snapshot(channel: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT * FROM streamer_snapshots
               WHERE channel = %s ORDER BY recorded_at DESC LIMIT 1""",
            (channel,),
        )
        row = await cur.fetchone()
    if row:
        d = dict(row)
        if isinstance(d.get("categories"), str):
            d["categories"] = json.loads(d["categories"])
        return d
    return None


async def get_all_channels_latest() -> list[dict]:
    """Get the latest snapshot for every tracked channel."""
    async with get_conn() as conn:
        cur = await conn.execute(
            """SELECT DISTINCT ON (channel) *
               FROM streamer_snapshots
               ORDER BY channel, recorded_at DESC"""
        )
        rows = await cur.fetchall()
    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("categories"), str):
            d["categories"] = json.loads(d["categories"])
        results.append(d)
    return results


# ---------------------------------------------------------------------------
# Growth Predictions
# ---------------------------------------------------------------------------

async def upsert_prediction(
    channel: str,
    metric: str,
    current_value: float,
    predicted_value: float,
    predicted_date: str,
    confidence: float,
    trend: str,
) -> dict:
    pred_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        # Remove old prediction for same channel+metric
        await conn.execute(
            "DELETE FROM growth_predictions WHERE channel = %s AND metric = %s",
            (channel, metric),
        )
        await conn.execute(
            """INSERT INTO growth_predictions
               (id, channel, metric, current_value, predicted_value,
                predicted_date, confidence, trend, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (pred_id, channel, metric, current_value, predicted_value,
             predicted_date, confidence, trend, now),
        )
        await conn.commit()
    return {
        "id": pred_id, "channel": channel, "metric": metric,
        "current_value": current_value, "predicted_value": predicted_value,
        "predicted_date": predicted_date, "confidence": confidence,
        "trend": trend, "created_at": now,
    }


async def get_predictions(channel: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM growth_predictions WHERE channel = %s ORDER BY created_at DESC",
            (channel,),
        )
        return [dict(r) for r in await cur.fetchall()]


# ---------------------------------------------------------------------------
# Growth Comparisons
# ---------------------------------------------------------------------------

async def upsert_comparison(
    channel: str,
    compared_channel: str,
    similarity_score: float,
    growth_phase: str,
    insight: str,
) -> dict:
    comp_id = _generate_id()
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            "DELETE FROM growth_comparisons WHERE channel = %s AND compared_channel = %s",
            (channel, compared_channel),
        )
        await conn.execute(
            """INSERT INTO growth_comparisons
               (id, channel, compared_channel, similarity_score, growth_phase, insight, created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (comp_id, channel, compared_channel, similarity_score, growth_phase, insight, now),
        )
        await conn.commit()
    return {
        "id": comp_id, "channel": channel, "compared_channel": compared_channel,
        "similarity_score": similarity_score, "growth_phase": growth_phase,
        "insight": insight, "created_at": now,
    }


async def get_comparisons(channel: str) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM growth_comparisons WHERE channel = %s ORDER BY similarity_score DESC",
            (channel,),
        )
        return [dict(r) for r in await cur.fetchall()]


# ---------------------------------------------------------------------------
# Streamer Stock Scores
# ---------------------------------------------------------------------------

async def upsert_stock_score(
    channel: str,
    stock_score: float,
    trend: str,
    change_pct: float,
    rank: int,
    avg_viewers: float,
    follower_count: int,
) -> dict:
    now = _now_iso()
    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO streamer_stock_scores
               (channel, stock_score, trend, change_pct, rank, avg_viewers, follower_count, updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (channel) DO UPDATE SET
                 stock_score = EXCLUDED.stock_score,
                 trend = EXCLUDED.trend,
                 change_pct = EXCLUDED.change_pct,
                 rank = EXCLUDED.rank,
                 avg_viewers = EXCLUDED.avg_viewers,
                 follower_count = EXCLUDED.follower_count,
                 updated_at = EXCLUDED.updated_at""",
            (channel, stock_score, trend, change_pct, rank, avg_viewers, follower_count, now),
        )
        await conn.commit()
    return {
        "channel": channel, "stock_score": stock_score, "trend": trend,
        "change_pct": change_pct, "rank": rank, "avg_viewers": avg_viewers,
        "follower_count": follower_count, "updated_at": now,
    }


async def get_stock_scores(limit: int = 20) -> list[dict]:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM streamer_stock_scores ORDER BY stock_score DESC LIMIT %s",
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_stock_score(channel: str) -> dict | None:
    async with get_conn() as conn:
        cur = await conn.execute(
            "SELECT * FROM streamer_stock_scores WHERE channel = %s",
            (channel,),
        )
        row = await cur.fetchone()
    return dict(row) if row else None
