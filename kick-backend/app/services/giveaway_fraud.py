"""Giveaway fraud prevention service."""

import json
import logging
from typing import Optional

from app.services.db import get_conn, _now_iso
from app.services import fingerprint as fp_svc
from app.services import behavior_analysis as behavior_svc

logger = logging.getLogger(__name__)


async def pre_check_entry(
    username: str,
    giveaway_id: str,
    channel: str,
) -> dict:
    """Pre-check a giveaway entry for fraud indicators.

    Returns dict with 'allowed' bool and optional 'reason'.
    """
    # Check if user is flagged as alt
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT risk_score, risk_level FROM flagged_accounts WHERE lower(username) = lower(%s)",
            (username,),
        )
        flagged = await row.fetchone()

    if flagged and flagged["risk_score"] >= 70:
        return {
            "allowed": False,
            "reason": f"Account flagged as {flagged['risk_level']} risk alt (score: {flagged['risk_score']:.0f})",
        }

    # Check fingerprint against other entrants
    existing_entries = await _get_giveaway_entrants(giveaway_id)
    fp_matches = await _check_fingerprint_overlap(username, channel, existing_entries)

    if fp_matches:
        # Record fraud flag
        for matched in fp_matches:
            await _record_fraud_flag(
                giveaway_id, username, "fingerprint_match", matched, 0.9,
            )
        return {
            "allowed": False,
            "reason": f"Fingerprint matches existing entrant(s): {', '.join(fp_matches[:3])}",
        }

    # Check behavior similarity against other entrants
    behavior_matches = await _check_behavior_overlap(username, channel, existing_entries)
    if behavior_matches:
        for matched_name, sim_score in behavior_matches:
            await _record_fraud_flag(
                giveaway_id, username, "behavior_match", matched_name, sim_score,
            )
        # Behavior match is softer — flag but allow
        return {
            "allowed": True,
            "reason": f"Behavior similar to entrant(s): {', '.join(n for n, _ in behavior_matches[:3])} (flagged for review)",
        }

    return {"allowed": True, "reason": None}


async def analyze_giveaway_entries(giveaway_id: str, channel: str) -> list[dict]:
    """Analyze all entries in a giveaway for fraud clusters.

    Returns list of fraud flag dicts.
    """
    entries = await _get_giveaway_entrants(giveaway_id)
    flags: list[dict] = []

    # Pairwise fingerprint comparison
    for i, entry_a in enumerate(entries):
        for entry_b in entries[i + 1:]:
            matches = await fp_svc.find_matching_fingerprints(entry_a, channel)
            matched_names = [m["username"] for m in matches]
            if entry_b.lower() in [n.lower() for n in matched_names]:
                flag = await _record_fraud_flag(
                    giveaway_id, entry_a, "fingerprint_match", entry_b, 0.95,
                )
                if flag:
                    flags.append(flag)

    return flags


async def get_fraud_flags(giveaway_id: str) -> list[dict]:
    """Get all fraud flags for a giveaway."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT * FROM giveaway_fraud_flags WHERE giveaway_id = %s ORDER BY confidence DESC",
            (giveaway_id,),
        )
        return [dict(r) for r in await row.fetchall()]


async def review_fraud_flag(flag_id: int, action: str) -> Optional[dict]:
    """Review a fraud flag (allow or remove)."""
    async with get_conn() as conn:
        row = await conn.execute(
            """UPDATE giveaway_fraud_flags SET reviewed = TRUE, review_action = %s
               WHERE id = %s RETURNING *""",
            (action, flag_id),
        )
        result = await row.fetchone()
        await conn.commit()
    return dict(result) if result else None


async def _get_giveaway_entrants(giveaway_id: str) -> list[str]:
    """Get list of usernames entered in a giveaway."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT entries FROM giveaways WHERE id = %s",
            (giveaway_id,),
        )
        result = await row.fetchone()

    if not result:
        return []

    entries = result["entries"]
    if isinstance(entries, str):
        entries = json.loads(entries)

    return [e["username"] for e in entries if isinstance(e, dict) and "username" in e]


async def _check_fingerprint_overlap(
    username: str,
    channel: str,
    existing_entries: list[str],
) -> list[str]:
    """Check if user's fingerprint matches any existing entrants."""
    matches = await fp_svc.find_matching_fingerprints(username, channel)
    entry_set = {e.lower() for e in existing_entries}
    return [m["username"] for m in matches if m["username"].lower() in entry_set]


async def _check_behavior_overlap(
    username: str,
    channel: str,
    existing_entries: list[str],
    threshold: float = 0.75,
) -> list[tuple[str, float]]:
    """Check behavior similarity against existing entrants."""
    return await behavior_svc.find_similar_banned_profiles(
        username, channel, existing_entries, threshold,
    )


async def _record_fraud_flag(
    giveaway_id: str,
    username: str,
    flag_type: str,
    matched_username: str,
    confidence: float,
) -> Optional[dict]:
    """Record a fraud flag."""
    now = _now_iso()
    async with get_conn() as conn:
        row = await conn.execute(
            """INSERT INTO giveaway_fraud_flags
               (giveaway_id, username, flag_type, matched_username, confidence, created_at)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
            (giveaway_id, username, flag_type, matched_username, confidence, now),
        )
        result = await row.fetchone()
        await conn.commit()

    logger.info(
        "Fraud flag: giveaway=%s user=%s type=%s matched=%s confidence=%.2f",
        giveaway_id, username, flag_type, matched_username, confidence,
    )
    return dict(result) if result else None
