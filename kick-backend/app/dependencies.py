"""FastAPI dependencies for authentication and shared utilities."""

import json
import logging
from datetime import datetime, timezone

from fastapi import Header, HTTPException

from app.services.db import get_conn

logger = logging.getLogger(__name__)


def extract_user_id(session: dict) -> str:
    """Safely extract user_id from session data. Raises 401 on failure."""
    user_data = session.get("user_data")
    if isinstance(user_data, str):
        try:
            user_data = json.loads(user_data)
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=401, detail="Corrupt session data")
    if not user_data or not user_data.get("user_id"):
        raise HTTPException(status_code=401, detail="User ID not found in session")
    return str(user_data["user_id"])


def safe_json_parse(value, default=None):
    """Parse JSON string, returning default on failure."""
    if isinstance(value, (dict, list)):
        return value
    if not value:
        return default if default is not None else {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse JSON: %r", value[:100] if isinstance(value, str) else value)
        return default if default is not None else {}


def get_channel_from_session(session: dict) -> str:
    """Extract the user's channel slug from their session data."""
    user_data = session.get("user_data")
    if isinstance(user_data, str):
        try:
            user_data = json.loads(user_data)
        except (json.JSONDecodeError, TypeError):
            return ""
    if not user_data:
        return ""
    return str(user_data.get("streamer_channel") or user_data.get("name") or "")


def require_channel_owner(session: dict, channel: str) -> None:
    """Verify the authenticated user owns the given channel. Raises 403 on mismatch."""
    user_channel = get_channel_from_session(session)
    if not user_channel or user_channel != channel:
        raise HTTPException(status_code=403, detail="Access denied: not your channel")


async def require_auth(authorization: str = Header(..., description="Bearer <session_id>")) -> dict:
    """Validate session and return session data. Use as a FastAPI dependency."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    session_id = authorization.removeprefix("Bearer ").strip()
    if not session_id:
        raise HTTPException(status_code=401, detail="Missing session ID")

    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT session_id, user_data, scope, expires_at FROM sessions WHERE session_id = %s",
            (session_id,),
        )
        session = await row.fetchone()

    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Enforce session expiry
    expires_at = session.get("expires_at", "")
    if expires_at:
        try:
            exp_dt = datetime.fromisoformat(expires_at)
            if datetime.now(timezone.utc) > exp_dt:
                # Clean up expired session
                async with get_conn() as conn:
                    await conn.execute(
                        "DELETE FROM sessions WHERE session_id = %s",
                        (session_id,),
                    )
                    await conn.commit()
                raise HTTPException(status_code=401, detail="Session expired")
        except (ValueError, TypeError):
            logger.warning("Malformed expires_at for session %s: %r", session_id, expires_at)
            raise HTTPException(status_code=401, detail="Invalid session — please log in again")

    return dict(session)
