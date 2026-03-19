"""AI Stream Coach analysis service.

Analyzes stream metrics and chat data to generate real-time coaching suggestions.
"""

import logging
import os
from datetime import datetime, timezone

import httpx

from app.repositories import stream_coach as coach_repo

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


async def analyze_stream(
    channel: str,
    session_id: str,
    viewer_count: int,
    game: str,
) -> dict:
    """Run all coaching analyses and return new suggestions + metrics."""

    settings = await coach_repo.get_settings(channel)
    if not settings.get("enabled", True):
        return {"suggestions": [], "metrics": {}}

    session = await coach_repo.get_session(session_id)
    if not session:
        return {"suggestions": [], "metrics": {}}

    # Record a snapshot for trend tracking
    snapshots = await coach_repo.get_snapshots(session_id)
    current_msg_count = await _get_session_message_count(channel, session["started_at"])
    await coach_repo.record_snapshot(session_id, channel, viewer_count, current_msg_count, game)

    # Update session stats
    peak = max(session.get("peak_viewers", 0), viewer_count)
    snapshot_count = len(snapshots) + 1
    prev_avg = session.get("avg_viewers", 0.0)
    new_avg = ((prev_avg * (snapshot_count - 1)) + viewer_count) / snapshot_count
    await coach_repo.update_session_stats(session_id, peak, round(new_avg, 1), current_msg_count, game)

    suggestions: list[dict] = []

    # 1. Engagement drop detection
    if settings.get("engagement_alerts", True):
        engagement_suggestion = await _check_engagement_drop(
            channel, session_id, snapshots,
            settings.get("engagement_drop_threshold", 30.0),
        )
        if engagement_suggestion:
            suggestions.append(engagement_suggestion)

    # 2. Game duration alerts
    if settings.get("game_duration_alerts", True):
        game_suggestion = _check_game_duration(snapshots, game, session["started_at"])
        if game_suggestion:
            suggestions.append(game_suggestion)

    # 3. Viewer count change alerts
    if settings.get("viewer_change_alerts", True):
        viewer_suggestion = _check_viewer_changes(
            snapshots, viewer_count,
            settings.get("viewer_change_threshold", 10),
        )
        if viewer_suggestion:
            suggestions.append(viewer_suggestion)

    # 4. Raid detection (sudden viewer spike)
    if settings.get("raid_welcome_alerts", True):
        raid_suggestion = _check_for_raid(snapshots, viewer_count)
        if raid_suggestion:
            suggestions.append(raid_suggestion)

    # 5. Break reminders
    if settings.get("break_reminders", True):
        break_suggestion = _check_break_reminder(
            session["started_at"],
            settings.get("break_reminder_minutes", 120),
        )
        if break_suggestion:
            suggestions.append(break_suggestion)

    # 6. Peak moment detection
    peak_suggestion = _check_peak_moment(snapshots, current_msg_count)
    if peak_suggestion:
        suggestions.append(peak_suggestion)

    # 7. Chat sentiment analysis
    if settings.get("sentiment_alerts", True):
        sentiment_suggestion = await _check_chat_sentiment(channel, session["started_at"])
        if sentiment_suggestion:
            suggestions.append(sentiment_suggestion)

    # Save new suggestions to DB
    saved_suggestions = []
    existing = await coach_repo.get_suggestions(session_id, include_dismissed=True)
    existing_types = {s["type"] for s in existing}

    for s in suggestions:
        # Avoid duplicate suggestion types within a short window
        if s["type"] not in existing_types or s["type"] in ("engagement", "viewer_change", "peak_moment", "sentiment"):
            saved = await coach_repo.create_suggestion(
                session_id=session_id,
                channel=channel,
                suggestion_type=s["type"],
                priority=s["priority"],
                title=s["title"],
                message=s["message"],
            )
            saved_suggestions.append(saved)

    # Compute sentiment score for metrics
    sentiment = await _compute_sentiment_score(channel, session["started_at"])

    metrics = {
        "viewer_count": viewer_count,
        "peak_viewers": peak,
        "avg_viewers": round(new_avg, 1),
        "total_messages": current_msg_count,
        "stream_duration_minutes": _get_duration_minutes(session["started_at"]),
        "game": game,
        "snapshot_count": snapshot_count,
        "sentiment": sentiment,
    }

    return {"suggestions": saved_suggestions, "metrics": metrics}


async def get_ai_insights(channel: str, session_id: str) -> str:
    """Generate AI-powered coaching insights using OpenAI."""
    if not OPENAI_API_KEY:
        return "AI insights require an OpenAI API key. Set OPENAI_API_KEY to enable."

    session = await coach_repo.get_session(session_id)
    if not session:
        return "No active session found."

    snapshots = await coach_repo.get_snapshots(session_id)
    suggestions = await coach_repo.get_suggestions(session_id, include_dismissed=True)

    # Build context for OpenAI
    duration = _get_duration_minutes(session["started_at"])
    snapshot_summary = []
    for s in snapshots[-10:]:  # Last 10 snapshots
        snapshot_summary.append(
            f"- {s['recorded_at']}: {s['viewer_count']} viewers, {s['message_count']} messages, playing {s['game']}"
        )

    prompt = f"""You are an AI stream coach for a Kick.com streamer. Analyze the following stream data and provide 2-3 actionable coaching tips.

Channel: {channel}
Current game: {session.get('game', 'Unknown')}
Stream duration: {duration} minutes
Peak viewers: {session.get('peak_viewers', 0)}
Average viewers: {session.get('avg_viewers', 0)}
Total chat messages: {session.get('total_messages', 0)}

Recent metrics (last snapshots):
{chr(10).join(snapshot_summary) if snapshot_summary else 'No snapshots yet.'}

Previous suggestions given: {len(suggestions)}

Provide brief, actionable coaching tips. Be encouraging but direct. Focus on engagement, content, and viewer retention. Format as a short bulleted list."""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 300,
                    "temperature": 0.7,
                },
            )

        if response.status_code != 200:
            logger.error("OpenAI API error: %s %s", response.status_code, response.text)
            return "Unable to generate AI insights at this time."

        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        logger.exception("Failed to generate AI insights")
        return "Unable to generate AI insights at this time."


# ---------------------------------------------------------------------------
# Internal analysis helpers
# ---------------------------------------------------------------------------

async def _get_session_message_count(channel: str, started_at: str) -> int:
    """Count messages in channel since session started."""
    from app.services.db import get_conn
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT count(*) AS cnt FROM chat_logs WHERE channel = %s AND timestamp >= %s",
            (channel, started_at),
        )
        result = await row.fetchone()
    return result["cnt"] if result else 0


async def _check_engagement_drop(
    channel: str, session_id: str, snapshots: list[dict], threshold: float
) -> dict | None:
    """Detect if chat engagement has dropped significantly."""
    if len(snapshots) < 3:
        return None

    recent = snapshots[-1]
    previous = snapshots[-3]

    recent_msgs = recent.get("message_count", 0)
    prev_msgs = previous.get("message_count", 0)

    if prev_msgs == 0:
        return None

    # Calculate message rate change between snapshots
    msg_diff = recent_msgs - prev_msgs
    older_diff = prev_msgs - (snapshots[-4]["message_count"] if len(snapshots) >= 4 else 0)

    if older_diff > 0 and msg_diff < older_diff * (1 - threshold / 100):
        return {
            "type": "engagement",
            "priority": "warning",
            "title": "Chat Engagement Dropping",
            "message": "Chat activity has slowed down significantly. Try interacting with your viewers — ask a question, run a poll, or acknowledge recent chatters to boost engagement.",
        }
    return None


def _check_game_duration(snapshots: list[dict], current_game: str, started_at: str) -> dict | None:
    """Alert if playing the same game for too long."""
    if not current_game:
        return None

    # Find when current game started
    game_start = started_at
    for s in snapshots:
        if s.get("game") == current_game:
            game_start = s["recorded_at"]
            break

    duration = _get_duration_minutes(game_start)
    if duration >= 90:
        hours = duration // 60
        mins = duration % 60
        return {
            "type": "game_duration",
            "priority": "info",
            "title": "Long Game Session",
            "message": f"You've been playing {current_game} for {hours}h {mins}m. Historically, viewer engagement tends to drop after 90 minutes on the same game. Consider switching games or taking a break to re-energize your audience.",
        }
    return None


def _check_viewer_changes(
    snapshots: list[dict], current_viewers: int, threshold: int
) -> dict | None:
    """Detect significant viewer count changes."""
    if len(snapshots) < 2:
        return None

    prev_viewers = snapshots[-1].get("viewer_count", 0)
    diff = current_viewers - prev_viewers

    if abs(diff) >= threshold:
        if diff > 0:
            return {
                "type": "viewer_change",
                "priority": "info",
                "title": "Viewer Spike Detected",
                "message": f"You gained {diff} viewers! Something you're doing is working — keep the energy up and engage with newcomers to retain them.",
            }
        else:
            return {
                "type": "viewer_change",
                "priority": "warning",
                "title": "Viewer Drop Detected",
                "message": f"You lost {abs(diff)} viewers recently. Consider switching up your content, interacting more with chat, or checking if there's a technical issue with your stream.",
            }
    return None


def _check_for_raid(snapshots: list[dict], current_viewers: int) -> dict | None:
    """Detect potential raids from sudden large viewer spikes."""
    if len(snapshots) < 2:
        return None

    prev_viewers = snapshots[-1].get("viewer_count", 0)
    spike = current_viewers - prev_viewers

    # A raid typically brings 20+ viewers at once
    if spike >= 20 and prev_viewers > 0 and spike > prev_viewers * 0.3:
        return {
            "type": "raid",
            "priority": "action",
            "title": "Possible Raid Incoming!",
            "message": f"{spike} new viewers just arrived — this looks like a raid! Welcome them warmly, introduce yourself and what you're doing, and make a great first impression.",
        }
    return None


def _check_break_reminder(started_at: str, reminder_minutes: int) -> dict | None:
    """Remind streamer to take breaks."""
    duration = _get_duration_minutes(started_at)

    if duration > 0 and duration % reminder_minutes < 5 and duration >= reminder_minutes:
        hours = duration // 60
        mins = duration % 60
        return {
            "type": "break",
            "priority": "info",
            "title": "Time for a Break",
            "message": f"You've been streaming for {hours}h {mins}m. Taking a short break helps maintain energy levels and can actually increase viewer retention when you return refreshed.",
        }
    return None


def _check_peak_moment(snapshots: list[dict], current_msg_count: int) -> dict | None:
    """Detect hype/peak moments from chat activity spikes."""
    if len(snapshots) < 3:
        return None

    # Check if recent message rate is significantly higher than average
    recent_msgs = current_msg_count - snapshots[-1].get("message_count", 0)
    avg_rate = (snapshots[-1].get("message_count", 0) - snapshots[0].get("message_count", 0)) / max(len(snapshots), 1)

    if avg_rate > 0 and recent_msgs > avg_rate * 2.5:
        return {
            "type": "peak_moment",
            "priority": "action",
            "title": "Hype Moment Detected!",
            "message": "Chat is going wild right now! This could be a great clip-worthy moment. Keep the energy up and consider marking this timestamp for a highlight reel.",
        }
    return None


# ---------------------------------------------------------------------------
# Sentiment analysis
# ---------------------------------------------------------------------------

# Negative keywords commonly seen in toxic/negative chat
_NEGATIVE_KEYWORDS = [
    "trash", "garbage", "boring", "terrible", "awful", "worst",
    "cringe", "dead stream", "dead chat", "leave", "unfollow",
    "sucks", "bad", "hate", "toxic", "annoying", "stupid",
    "dumb", "lame", "waste", "unwatchable", "yawn", "sleeper",
    "ratio", "L stream", "dogwater", "mid",
]

_POSITIVE_KEYWORDS = [
    "gg", "pog", "poggers", "hype", "lets go", "let's go",
    "goat", "amazing", "incredible", "insane", "clutch",
    "love", "great", "awesome", "fire", "W stream",
    "based", "goated", "cracked", "nice", "well played",
    "beautiful", "perfect", "legendary", "epic",
]


async def _get_recent_messages(channel: str, started_at: str, limit: int = 50) -> list[str]:
    """Fetch recent chat messages for sentiment analysis."""
    from app.services.db import get_conn
    async with get_conn() as conn:
        row = await conn.execute(
            """SELECT message FROM chat_logs
               WHERE channel = %s AND timestamp >= %s
               ORDER BY timestamp DESC LIMIT %s""",
            (channel, started_at, limit),
        )
        results = await row.fetchall()
    return [r["message"] for r in results]


def _score_sentiment(messages: list[str]) -> dict:
    """Score sentiment of a batch of messages using keyword matching.

    Returns a dict with score (-1.0 to 1.0), label, and counts.
    """
    if not messages:
        return {"score": 0.0, "label": "neutral", "positive": 0, "negative": 0, "total": 0}

    positive_count = 0
    negative_count = 0

    for msg in messages:
        lower = msg.lower()
        for kw in _NEGATIVE_KEYWORDS:
            if kw in lower:
                negative_count += 1
                break
        for kw in _POSITIVE_KEYWORDS:
            if kw in lower:
                positive_count += 1
                break

    total = len(messages)
    pos_ratio = positive_count / total if total > 0 else 0
    neg_ratio = negative_count / total if total > 0 else 0
    score = round(pos_ratio - neg_ratio, 3)

    if score > 0.1:
        label = "positive"
    elif score < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return {
        "score": score,
        "label": label,
        "positive": positive_count,
        "negative": negative_count,
        "total": total,
    }


async def _compute_sentiment_score(channel: str, started_at: str) -> dict:
    """Compute current chat sentiment for metrics reporting."""
    messages = await _get_recent_messages(channel, started_at, limit=50)
    return _score_sentiment(messages)


async def _check_chat_sentiment(channel: str, started_at: str) -> dict | None:
    """Detect negative chat sentiment trends and generate coaching suggestion."""
    messages = await _get_recent_messages(channel, started_at, limit=30)
    if len(messages) < 5:
        return None

    sentiment = _score_sentiment(messages)

    if sentiment["label"] == "negative" and sentiment["negative"] >= 3:
        neg_pct = round(sentiment["negative"] / sentiment["total"] * 100)
        return {
            "type": "sentiment",
            "priority": "warning",
            "title": "Negative Chat Sentiment Detected",
            "message": f"About {neg_pct}% of recent messages have negative sentiment. "
                       "Consider addressing chat concerns, switching topics, or engaging "
                       "positively to shift the mood. A quick interaction or fun moment can "
                       "turn things around.",
        }

    return None


def _get_duration_minutes(started_at: str) -> int:
    """Calculate minutes since the given ISO timestamp."""
    try:
        start = datetime.fromisoformat(started_at)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return int((now - start).total_seconds() / 60)
    except (ValueError, TypeError):
        return 0
