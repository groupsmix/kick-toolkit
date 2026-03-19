"""FastAPI dependencies for authentication."""

from datetime import datetime, timezone

from fastapi import Header, HTTPException

from app.services.db import get_conn


async def require_auth(authorization: str = Header(..., description="Bearer <session_id>")) -> dict:
    """Validate session and return session data. Use as a FastAPI dependency."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    session_id = authorization.removeprefix("Bearer ").strip()
    if not session_id:
        raise HTTPException(status_code=401, detail="Missing session ID")

    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT session_id, user_data, scope, access_token, expires_at FROM sessions WHERE session_id = %s",
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
            pass  # Malformed date — allow through for backwards compat

    return dict(session)
