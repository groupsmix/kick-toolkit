"""IP/fingerprint tracking and similarity detection service."""

import hashlib
from typing import Optional

from app.services.db import get_conn, _now_iso


def _hash_value(value: Optional[str]) -> Optional[str]:
    """SHA-256 hash a value for privacy-preserving storage."""
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def record_fingerprint(
    username: str,
    channel: str,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """Record or update a user's fingerprint data."""
    now = _now_iso()
    ip_hash = _hash_value(client_ip)
    ua_hash = _hash_value(user_agent)

    # Composite fingerprint from available data
    composite = f"{ip_hash or ''}{ua_hash or ''}"
    fp_hash = _hash_value(composite) if composite else None

    import json
    meta_json = json.dumps(metadata or {})

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO user_fingerprints
               (username, channel, fingerprint_hash, client_ip_hash, user_agent_hash,
                session_metadata, first_seen, last_seen)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (username, channel) DO UPDATE SET
                   fingerprint_hash = COALESCE(EXCLUDED.fingerprint_hash, user_fingerprints.fingerprint_hash),
                   client_ip_hash = COALESCE(EXCLUDED.client_ip_hash, user_fingerprints.client_ip_hash),
                   user_agent_hash = COALESCE(EXCLUDED.user_agent_hash, user_fingerprints.user_agent_hash),
                   session_metadata = EXCLUDED.session_metadata,
                   last_seen = EXCLUDED.last_seen""",
            (username, channel, fp_hash, ip_hash, ua_hash, meta_json, now, now),
        )
        await conn.commit()


async def find_matching_fingerprints(
    username: str,
    channel: str,
) -> list[dict]:
    """Find other users sharing the same fingerprint or IP hash."""
    async with get_conn() as conn:
        # Get this user's fingerprint data
        row = await conn.execute(
            "SELECT fingerprint_hash, client_ip_hash FROM user_fingerprints WHERE username = %s AND channel = %s",
            (username, channel),
        )
        user_fp = await row.fetchone()

    if not user_fp:
        return []

    matches: list[dict] = []
    conditions: list[str] = []
    params: list[str] = [username, channel]

    if user_fp["fingerprint_hash"]:
        conditions.append("fingerprint_hash = %s")
        params.append(user_fp["fingerprint_hash"])

    if user_fp["client_ip_hash"]:
        conditions.append("client_ip_hash = %s")
        params.append(user_fp["client_ip_hash"])

    if not conditions:
        return []

    where_clause = " OR ".join(conditions)
    query = f"""
        SELECT username, channel, fingerprint_hash, client_ip_hash, first_seen, last_seen
        FROM user_fingerprints
        WHERE username != %s AND channel = %s AND ({where_clause})
    """

    async with get_conn() as conn:
        row = await conn.execute(query, tuple(params))
        rows = await row.fetchall()
        matches = [dict(r) for r in rows]

    return matches


async def find_banned_fingerprint_matches(
    username: str,
    channel: str,
    banned_usernames: list[str],
) -> list[str]:
    """Find banned users sharing fingerprint data with the given user."""
    all_matches = await find_matching_fingerprints(username, channel)
    banned_set = {b.lower() for b in banned_usernames}
    return [m["username"] for m in all_matches if m["username"].lower() in banned_set]


async def get_fingerprint_risk_score(
    username: str,
    channel: str,
    banned_usernames: list[str],
) -> tuple[float, list[str]]:
    """Calculate fingerprint-based risk score (0-25).

    Returns (score, list_of_matched_banned_users).
    """
    matched = await find_banned_fingerprint_matches(username, channel, banned_usernames)
    if not matched:
        return 0.0, []

    # Score scales with number of matches, capped at 25
    score = min(len(matched) * 12.5, 25.0)
    return score, matched
