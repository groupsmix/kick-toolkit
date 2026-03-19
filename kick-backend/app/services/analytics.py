"""Predictive Analytics service.

Analyzes streamer growth patterns, generates predictions, compares growth curves,
and computes "stock market" scores for streamers.
"""

import logging
import os
from datetime import datetime, timedelta, timezone

import httpx

from app.repositories import analytics as analytics_repo

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


# ---------------------------------------------------------------------------
# Growth Analysis
# ---------------------------------------------------------------------------

async def compute_overview(channel: str) -> dict:
    """Compute a full analytics overview for a channel."""
    snapshots = await analytics_repo.get_snapshots(channel, limit=30)
    predictions = await analytics_repo.get_predictions(channel)
    comparisons = await analytics_repo.get_comparisons(channel)
    stock = await analytics_repo.get_stock_score(channel)

    growth_score = _compute_growth_score(snapshots)
    sponsorship = _compute_sponsorship_readiness(snapshots)
    consistency = _compute_consistency_score(snapshots)
    engagement = _compute_engagement_rate(snapshots)
    trend = _determine_trend(snapshots)

    return {
        "channel": channel,
        "growth_score": round(growth_score, 1),
        "sponsorship_readiness": round(sponsorship, 1),
        "consistency_score": round(consistency, 1),
        "engagement_rate": round(engagement, 2),
        "trend": trend,
        "predictions": predictions,
        "comparisons": comparisons,
        "recent_snapshots": snapshots[:14],
        "stock": stock,
    }


def _compute_growth_score(snapshots: list[dict]) -> float:
    """Score 0-100 based on viewer and follower growth trends."""
    if len(snapshots) < 2:
        return 50.0

    recent = snapshots[:7]
    older = snapshots[7:14] if len(snapshots) > 7 else snapshots[-len(snapshots):]

    if not older:
        return 50.0

    avg_recent_viewers = sum(s["avg_viewers"] for s in recent) / len(recent)
    avg_older_viewers = sum(s["avg_viewers"] for s in older) / len(older)

    avg_recent_followers = sum(s["follower_count"] for s in recent) / len(recent)
    avg_older_followers = sum(s["follower_count"] for s in older) / len(older)

    viewer_growth = 0.0
    if avg_older_viewers > 0:
        viewer_growth = ((avg_recent_viewers - avg_older_viewers) / avg_older_viewers) * 100

    follower_growth = 0.0
    if avg_older_followers > 0:
        follower_growth = ((avg_recent_followers - avg_older_followers) / avg_older_followers) * 100

    # Weighted: 60% viewer growth, 40% follower growth, normalized to 0-100
    raw = (viewer_growth * 0.6 + follower_growth * 0.4) + 50
    return max(0.0, min(100.0, raw))


def _compute_sponsorship_readiness(snapshots: list[dict]) -> float:
    """Score 0-100 indicating how ready a streamer is for sponsorships."""
    if not snapshots:
        return 0.0

    latest = snapshots[0]
    score = 0.0

    # Viewer count (0-30 pts)
    viewers = latest.get("avg_viewers", 0)
    if viewers >= 500:
        score += 30
    elif viewers >= 100:
        score += 20
    elif viewers >= 50:
        score += 10

    # Follower count (0-25 pts)
    followers = latest.get("follower_count", 0)
    if followers >= 10000:
        score += 25
    elif followers >= 5000:
        score += 18
    elif followers >= 1000:
        score += 10

    # Consistency - how many snapshots in last 14 days (0-25 pts)
    score += min(25.0, len(snapshots) * (25 / 14))

    # Engagement rate (0-20 pts)
    engagement = _compute_engagement_rate(snapshots[:7])
    score += min(20.0, engagement * 200)

    return min(100.0, score)


def _compute_consistency_score(snapshots: list[dict]) -> float:
    """Score 0-100 based on streaming consistency."""
    if len(snapshots) < 2:
        return 50.0

    hours = [s.get("hours_streamed", 0) for s in snapshots[:14]]
    if not hours or max(hours) == 0:
        return 50.0

    avg_hours = sum(hours) / len(hours)
    if avg_hours == 0:
        return 30.0

    variance = sum((h - avg_hours) ** 2 for h in hours) / len(hours)
    std_dev = variance ** 0.5
    cv = std_dev / avg_hours if avg_hours > 0 else 1.0

    # Lower CV = more consistent = higher score
    score = max(0.0, 100.0 - (cv * 50))
    return min(100.0, score)


def _compute_engagement_rate(snapshots: list[dict]) -> float:
    """Chat messages per viewer per hour."""
    if not snapshots:
        return 0.0

    total_messages = sum(s.get("chat_messages", 0) for s in snapshots)
    total_viewers = sum(s.get("avg_viewers", 0) for s in snapshots)
    total_hours = sum(s.get("hours_streamed", 0) for s in snapshots)

    if total_viewers == 0 or total_hours == 0:
        return 0.0

    return total_messages / (total_viewers * total_hours)


def _determine_trend(snapshots: list[dict]) -> str:
    """Determine overall growth trend from snapshots."""
    if len(snapshots) < 2:
        return "stable"

    recent = snapshots[:3]
    older = snapshots[3:6] if len(snapshots) > 3 else snapshots[1:]

    if not older:
        return "stable"

    avg_recent = sum(s["avg_viewers"] for s in recent) / len(recent)
    avg_older = sum(s["avg_viewers"] for s in older) / len(older)

    if avg_older == 0:
        return "rising" if avg_recent > 0 else "stable"

    pct_change = ((avg_recent - avg_older) / avg_older) * 100

    if pct_change > 10:
        return "rising"
    elif pct_change < -10:
        return "declining"
    return "stable"


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------

async def generate_predictions(channel: str) -> list[dict]:
    """Generate growth predictions for a channel based on snapshot history."""
    snapshots = await analytics_repo.get_snapshots(channel, limit=30)

    if len(snapshots) < 2:
        return []

    predictions = []

    # Predict followers
    follower_pred = _predict_metric(snapshots, "follower_count", "followers")
    if follower_pred:
        saved = await analytics_repo.upsert_prediction(**follower_pred)
        predictions.append(saved)

    # Predict avg viewers
    viewer_pred = _predict_metric(snapshots, "avg_viewers", "avg_viewers")
    if viewer_pred:
        saved = await analytics_repo.upsert_prediction(**viewer_pred)
        predictions.append(saved)

    # Predict subscribers
    sub_pred = _predict_metric(snapshots, "subscriber_count", "subscribers")
    if sub_pred:
        saved = await analytics_repo.upsert_prediction(**sub_pred)
        predictions.append(saved)

    return predictions


def _predict_metric(snapshots: list[dict], field: str, metric_name: str) -> dict | None:
    """Simple linear regression prediction for a given metric."""
    values = [s.get(field, 0) for s in reversed(snapshots)]
    if len(values) < 2:
        return None

    n = len(values)
    x_vals = list(range(n))
    x_mean = sum(x_vals) / n
    y_mean = sum(values) / n

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, values))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)

    if denominator == 0:
        return None

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    # Predict 30 days out
    future_x = n + 30
    predicted = slope * future_x + intercept
    predicted = max(0, predicted)

    current = values[-1] if values else 0

    # Confidence based on R² (coefficient of determination)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_vals, values))
    ss_tot = sum((y - y_mean) ** 2 for y in values)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    confidence = max(0.0, min(1.0, r_squared))

    if slope > 0.01:
        trend = "rising"
    elif slope < -0.01:
        trend = "declining"
    else:
        trend = "stable"

    predicted_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    return {
        "channel": snapshots[0]["channel"],
        "metric": metric_name,
        "current_value": float(current),
        "predicted_value": round(float(predicted), 1),
        "predicted_date": predicted_date,
        "confidence": round(confidence, 3),
        "trend": trend,
    }


# ---------------------------------------------------------------------------
# Growth Comparisons
# ---------------------------------------------------------------------------

async def generate_comparisons(channel: str) -> list[dict]:
    """Compare a channel's growth curve to other tracked channels."""
    target_snapshots = await analytics_repo.get_snapshots(channel, limit=30)
    if len(target_snapshots) < 2:
        return []

    all_channels = await analytics_repo.get_all_channels_latest()
    other_channels = [c for c in all_channels if c["channel"] != channel]

    if not other_channels:
        # Generate AI-based comparisons if no other channels exist
        return await _generate_ai_comparisons(channel, target_snapshots)

    comparisons = []
    target_viewers = [s["avg_viewers"] for s in reversed(target_snapshots)]

    for other in other_channels:
        other_snaps = await analytics_repo.get_snapshots(other["channel"], limit=30)
        if len(other_snaps) < 2:
            continue

        other_viewers = [s["avg_viewers"] for s in reversed(other_snaps)]
        similarity = _compute_curve_similarity(target_viewers, other_viewers)
        phase = _determine_growth_phase(other_snaps)

        insight = (
            f"Your growth pattern has {similarity:.0%} similarity to "
            f"{other['channel']}'s trajectory. They are in the '{phase}' phase."
        )

        saved = await analytics_repo.upsert_comparison(
            channel=channel,
            compared_channel=other["channel"],
            similarity_score=round(similarity * 100, 1),
            growth_phase=phase,
            insight=insight,
        )
        comparisons.append(saved)

    return sorted(comparisons, key=lambda c: c["similarity_score"], reverse=True)[:5]


def _compute_curve_similarity(curve_a: list[float], curve_b: list[float]) -> float:
    """Compute normalized similarity between two growth curves (0-1)."""
    min_len = min(len(curve_a), len(curve_b))
    if min_len < 2:
        return 0.0

    a = curve_a[:min_len]
    b = curve_b[:min_len]

    # Normalize both curves to 0-1 range
    a_min, a_max = min(a), max(a)
    b_min, b_max = min(b), max(b)

    a_range = a_max - a_min if a_max != a_min else 1
    b_range = b_max - b_min if b_max != b_min else 1

    a_norm = [(v - a_min) / a_range for v in a]
    b_norm = [(v - b_min) / b_range for v in b]

    # Compute mean absolute error
    mae = sum(abs(an - bn) for an, bn in zip(a_norm, b_norm)) / min_len
    similarity = max(0.0, 1.0 - mae)
    return similarity


def _determine_growth_phase(snapshots: list[dict]) -> str:
    """Determine which growth phase a channel is in."""
    if not snapshots:
        return "early"

    latest = snapshots[0]
    avg_viewers = latest.get("avg_viewers", 0)
    followers = latest.get("follower_count", 0)

    if avg_viewers >= 1000 or followers >= 50000:
        return "established"
    elif avg_viewers >= 100 or followers >= 5000:
        return "growth"
    elif avg_viewers >= 10 or followers >= 500:
        return "emerging"
    return "early"


async def _generate_ai_comparisons(channel: str, snapshots: list[dict]) -> list[dict]:
    """Generate AI-based growth comparisons when no peer data is available."""
    if not OPENAI_API_KEY:
        phase = _determine_growth_phase(snapshots)
        insight = (
            f"Your channel is in the '{phase}' growth phase. "
            "As more streamers are tracked, you'll see detailed growth comparisons here."
        )
        saved = await analytics_repo.upsert_comparison(
            channel=channel,
            compared_channel="(industry benchmark)",
            similarity_score=0.0,
            growth_phase=phase,
            insight=insight,
        )
        return [saved]

    latest = snapshots[0]
    prompt = (
        f"A Kick.com streamer '{channel}' has {latest.get('avg_viewers', 0)} average viewers, "
        f"{latest.get('follower_count', 0)} followers, and streams ~{latest.get('hours_streamed', 0)} hours/day. "
        f"Compare their growth trajectory to well-known streamers who were at a similar stage. "
        f"Provide 2-3 short comparisons. Each should name a real or realistic streamer, "
        f"the similarity, and an actionable insight. Keep each comparison under 50 words."
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a streaming growth analyst. Respond in plain text, one comparison per line. Format: 'StreamerName: <insight>'"},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7,
                },
            )
            data = resp.json()
            text = data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("OpenAI comparison generation failed: %s", exc)
        text = ""

    if not text:
        phase = _determine_growth_phase(snapshots)
        saved = await analytics_repo.upsert_comparison(
            channel=channel,
            compared_channel="(industry benchmark)",
            similarity_score=0.0,
            growth_phase=phase,
            insight=f"Your channel is in the '{phase}' growth phase.",
        )
        return [saved]

    comparisons = []
    phase = _determine_growth_phase(snapshots)
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        parts = line.split(":", 1)
        compared = parts[0].strip().strip("-•*0123456789.")
        insight_text = parts[1].strip() if len(parts) > 1 else line
        if not compared:
            continue

        saved = await analytics_repo.upsert_comparison(
            channel=channel,
            compared_channel=compared,
            similarity_score=50.0,
            growth_phase=phase,
            insight=insight_text,
        )
        comparisons.append(saved)

    return comparisons[:3]


# ---------------------------------------------------------------------------
# Stock Market Scores
# ---------------------------------------------------------------------------

async def update_stock_scores() -> list[dict]:
    """Recalculate stock scores for all tracked channels."""
    all_latest = await analytics_repo.get_all_channels_latest()
    if not all_latest:
        return []

    scores = []
    for snap in all_latest:
        channel = snap["channel"]
        snapshots = await analytics_repo.get_snapshots(channel, limit=14)
        score = _compute_stock_score(snapshots)
        trend = _determine_trend(snapshots)
        change = _compute_change_pct(snapshots)

        scores.append({
            "channel": channel,
            "stock_score": score,
            "trend": trend,
            "change_pct": change,
            "avg_viewers": snap.get("avg_viewers", 0),
            "follower_count": snap.get("follower_count", 0),
        })

    # Sort by score and assign ranks
    scores.sort(key=lambda s: s["stock_score"], reverse=True)
    results = []
    for rank, entry in enumerate(scores, 1):
        saved = await analytics_repo.upsert_stock_score(
            channel=entry["channel"],
            stock_score=round(entry["stock_score"], 1),
            trend=entry["trend"],
            change_pct=round(entry["change_pct"], 2),
            rank=rank,
            avg_viewers=entry["avg_viewers"],
            follower_count=entry["follower_count"],
        )
        results.append(saved)

    return results


def _compute_stock_score(snapshots: list[dict]) -> float:
    """Compute a 0-1000 'stock price' based on metrics."""
    if not snapshots:
        return 0.0

    latest = snapshots[0]
    viewers = latest.get("avg_viewers", 0)
    followers = latest.get("follower_count", 0)
    engagement = _compute_engagement_rate(snapshots[:7])
    growth = _compute_growth_score(snapshots)

    # Weighted composite
    viewer_component = min(300, viewers * 0.5)
    follower_component = min(200, followers * 0.01)
    engagement_component = min(200, engagement * 2000)
    growth_component = min(300, growth * 3)

    return viewer_component + follower_component + engagement_component + growth_component


def _compute_change_pct(snapshots: list[dict]) -> float:
    """Compute % change in avg viewers over recent snapshots."""
    if len(snapshots) < 2:
        return 0.0

    recent = snapshots[0].get("avg_viewers", 0)
    older = snapshots[-1].get("avg_viewers", 0)

    if older == 0:
        return 100.0 if recent > 0 else 0.0

    return ((recent - older) / older) * 100


# ---------------------------------------------------------------------------
# AI Growth Narrative
# ---------------------------------------------------------------------------

async def get_growth_narrative(channel: str) -> str:
    """Generate an AI-powered growth narrative for the streamer."""
    snapshots = await analytics_repo.get_snapshots(channel, limit=14)
    predictions = await analytics_repo.get_predictions(channel)

    if not snapshots:
        return "No data available yet. Record some snapshots to get AI-powered growth insights."

    latest = snapshots[0]

    if not OPENAI_API_KEY:
        trend = _determine_trend(snapshots)
        return (
            f"Channel '{channel}' currently has {latest.get('avg_viewers', 0)} average viewers "
            f"and {latest.get('follower_count', 0)} followers. Growth trend: {trend}. "
            f"Set up your OpenAI API key for detailed AI-powered growth analysis."
        )

    pred_summary = ""
    for p in predictions:
        pred_summary += (
            f"- {p['metric']}: current {p['current_value']}, "
            f"predicted {p['predicted_value']} in 30 days ({p['trend']})\n"
        )

    prompt = (
        f"Analyze this Kick.com streamer's growth data and provide actionable insights:\n\n"
        f"Channel: {channel}\n"
        f"Current stats: {latest.get('avg_viewers', 0)} avg viewers, "
        f"{latest.get('follower_count', 0)} followers, "
        f"{latest.get('subscriber_count', 0)} subscribers\n"
        f"Hours streamed recently: {latest.get('hours_streamed', 0)}\n"
        f"Data points: {len(snapshots)} snapshots\n\n"
        f"Predictions:\n{pred_summary}\n"
        f"Provide a concise growth analysis (3-5 paragraphs) covering:\n"
        f"1. Current trajectory assessment\n"
        f"2. Key strengths and areas for improvement\n"
        f"3. Specific actionable recommendations\n"
        f"4. Sponsorship/monetization readiness\n"
        f"Keep it encouraging but honest."
    )

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are an expert streaming growth consultant. Provide data-driven insights in a professional but encouraging tone."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 600,
                    "temperature": 0.7,
                },
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        logger.warning("OpenAI growth narrative failed: %s", exc)
        trend = _determine_trend(snapshots)
        return (
            f"Channel '{channel}' has {latest.get('avg_viewers', 0)} average viewers "
            f"and {latest.get('follower_count', 0)} followers. Trend: {trend}. "
            f"AI analysis temporarily unavailable."
        )
