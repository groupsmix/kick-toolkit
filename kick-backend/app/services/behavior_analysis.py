"""Behavioral fingerprinting service for chat pattern analysis."""

import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from app.services.db import get_conn, _now_iso

# Emoji detection pattern
_EMOJI_PATTERN = re.compile(
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251"
    r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]",
)


def _extract_emojis(text: str) -> list[str]:
    """Extract all emoji characters from text."""
    return _EMOJI_PATTERN.findall(text)


def _extract_vocab(text: str) -> list[str]:
    """Extract lowercase words from text."""
    return re.findall(r"[a-zA-Z]{2,}", text.lower())


async def update_profile(
    username: str,
    channel: str,
    message: str,
    timestamp: Optional[str] = None,
) -> None:
    """Incrementally update a user's behavior profile with a new message."""
    now = timestamp or _now_iso()
    msg_len = len(message)
    emojis = _extract_emojis(message)
    words = _extract_vocab(message)
    upper_chars = sum(1 for c in message if c.isupper())
    alpha_chars = sum(1 for c in message if c.isalpha())
    caps_ratio = upper_chars / alpha_chars if alpha_chars > 0 else 0.0

    # Parse hour for timing histogram
    try:
        dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
        hour = str(dt.hour)
    except (ValueError, TypeError):
        hour = str(datetime.now(timezone.utc).hour)

    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM behavior_profiles WHERE username = %s AND channel = %s",
            (username, channel),
        )
        existing = await row.fetchone()

    if existing:
        existing = dict(existing)
        count = existing["message_count"] + 1
        # Running average for message length
        new_avg_len = (existing["avg_msg_length"] * existing["message_count"] + msg_len) / count
        # Running average for caps ratio
        new_caps = (existing["caps_ratio"] * existing["message_count"] + caps_ratio) / count

        # Update emoji profile
        emoji_prof = existing["emoji_profile"] if isinstance(existing["emoji_profile"], dict) else json.loads(existing["emoji_profile"] or "{}")
        for e in emojis:
            emoji_prof[e] = emoji_prof.get(e, 0) + 1
        total_emoji_count = sum(emoji_prof.values())
        new_emoji_freq = total_emoji_count / count

        # Update vocab fingerprint (top 50 words)
        vocab_fp = existing["vocab_fingerprint"] if isinstance(existing["vocab_fingerprint"], dict) else json.loads(existing["vocab_fingerprint"] or "{}")
        for w in words:
            vocab_fp[w] = vocab_fp.get(w, 0) + 1
        # Keep only top 50
        if len(vocab_fp) > 50:
            sorted_vocab = sorted(vocab_fp.items(), key=lambda x: x[1], reverse=True)[:50]
            vocab_fp = dict(sorted_vocab)

        # Update timing histogram
        timing = existing["timing_histogram"] if isinstance(existing["timing_histogram"], dict) else json.loads(existing["timing_histogram"] or "{}")
        timing[hour] = timing.get(hour, 0) + 1

        # Update message length stats
        msg_stats = existing["msg_length_stats"] if isinstance(existing["msg_length_stats"], dict) else json.loads(existing["msg_length_stats"] or "{}")
        prev_mean = msg_stats.get("mean", 0.0)
        prev_var = msg_stats.get("variance", 0.0)
        prev_n = existing["message_count"]
        # Welford's online algorithm for variance
        delta = msg_len - prev_mean
        new_mean = prev_mean + delta / count
        delta2 = msg_len - new_mean
        new_var = (prev_var * prev_n + delta * delta2) / count if count > 1 else 0.0
        msg_stats = {"mean": new_mean, "variance": new_var, "stddev": math.sqrt(max(new_var, 0))}

        async with get_conn() as conn:
            await conn.execute(
                """UPDATE behavior_profiles SET
                    message_count = %s, avg_msg_length = %s, caps_ratio = %s,
                    emoji_frequency = %s, emoji_profile = %s, vocab_fingerprint = %s,
                    timing_histogram = %s, msg_length_stats = %s, updated_at = %s
                   WHERE username = %s AND channel = %s""",
                (count, new_avg_len, new_caps, new_emoji_freq,
                 json.dumps(emoji_prof), json.dumps(vocab_fp),
                 json.dumps(timing), json.dumps(msg_stats), _now_iso(),
                 username, channel),
            )
            await conn.commit()
    else:
        # Create new profile
        emoji_prof = dict(Counter(emojis))
        vocab_fp = dict(Counter(words))
        timing = {hour: 1}
        msg_stats = {"mean": float(msg_len), "variance": 0.0, "stddev": 0.0}

        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO behavior_profiles
                   (username, channel, message_count, avg_msg_length, avg_typing_speed,
                    caps_ratio, emoji_frequency, emoji_profile, vocab_fingerprint,
                    timing_histogram, msg_length_stats, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (username, channel, 1, float(msg_len), 0.0, caps_ratio,
                 float(len(emojis)), json.dumps(emoji_prof), json.dumps(vocab_fp),
                 json.dumps(timing), json.dumps(msg_stats), _now_iso()),
            )
            await conn.commit()


async def get_profile(username: str, channel: str) -> Optional[dict]:
    """Get a user's behavior profile."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM behavior_profiles WHERE username = %s AND channel = %s",
            (username, channel),
        )
        result = await row.fetchone()
    return dict(result) if result else None


def compare_profiles(profile_a: dict, profile_b: dict) -> float:
    """Compare two behavior profiles using cosine similarity.

    Returns similarity score 0.0 - 1.0.
    """
    if not profile_a or not profile_b:
        return 0.0

    # Build feature vectors from comparable attributes
    features_a: list[float] = []
    features_b: list[float] = []

    # Numeric features
    for key in ["avg_msg_length", "caps_ratio", "emoji_frequency"]:
        features_a.append(float(profile_a.get(key, 0)))
        features_b.append(float(profile_b.get(key, 0)))

    # Vocab overlap (Jaccard-like)
    vocab_a = set((profile_a.get("vocab_fingerprint") or {}).keys())
    vocab_b = set((profile_b.get("vocab_fingerprint") or {}).keys())
    if vocab_a or vocab_b:
        vocab_sim = len(vocab_a & vocab_b) / len(vocab_a | vocab_b) if (vocab_a | vocab_b) else 0.0
        features_a.append(vocab_sim)
        features_b.append(1.0)  # Reference is self

    # Timing similarity
    timing_a = profile_a.get("timing_histogram") or {}
    timing_b = profile_b.get("timing_histogram") or {}
    if isinstance(timing_a, str):
        timing_a = json.loads(timing_a)
    if isinstance(timing_b, str):
        timing_b = json.loads(timing_b)
    all_hours = set(timing_a.keys()) | set(timing_b.keys())
    if all_hours:
        total_a = sum(timing_a.values()) or 1
        total_b = sum(timing_b.values()) or 1
        timing_vec_a = [timing_a.get(h, 0) / total_a for h in sorted(all_hours)]
        timing_vec_b = [timing_b.get(h, 0) / total_b for h in sorted(all_hours)]
        # Cosine similarity of timing vectors
        dot = sum(a * b for a, b in zip(timing_vec_a, timing_vec_b))
        mag_a = math.sqrt(sum(a * a for a in timing_vec_a))
        mag_b = math.sqrt(sum(b * b for b in timing_vec_b))
        timing_sim = dot / (mag_a * mag_b) if mag_a > 0 and mag_b > 0 else 0.0
        features_a.append(timing_sim)
        features_b.append(1.0)

    # Emoji overlap
    emoji_a = set((profile_a.get("emoji_profile") or {}).keys())
    emoji_b = set((profile_b.get("emoji_profile") or {}).keys())
    if emoji_a or emoji_b:
        emoji_sim = len(emoji_a & emoji_b) / len(emoji_a | emoji_b) if (emoji_a | emoji_b) else 0.0
        features_a.append(emoji_sim)
        features_b.append(1.0)

    if not features_a:
        return 0.0

    # Cosine similarity of feature vectors
    dot = sum(a * b for a, b in zip(features_a, features_b))
    mag_a = math.sqrt(sum(a * a for a in features_a))
    mag_b = math.sqrt(sum(b * b for b in features_b))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


async def find_similar_banned_profiles(
    username: str,
    channel: str,
    banned_usernames: list[str],
    threshold: float = 0.6,
) -> list[tuple[str, float]]:
    """Find banned users with similar behavior profiles.

    Returns list of (banned_username, similarity_score).
    """
    user_profile = await get_profile(username, channel)
    if not user_profile:
        return []

    results: list[tuple[str, float]] = []
    for banned in banned_usernames:
        banned_profile = await get_profile(banned, channel)
        if banned_profile:
            sim = compare_profiles(user_profile, banned_profile)
            if sim >= threshold:
                results.append((banned, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
