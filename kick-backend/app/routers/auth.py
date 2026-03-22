"""Kick OAuth 2.1 authentication routes."""

import logging

from fastapi import APIRouter, Depends, Response, HTTPException
from fastapi.responses import RedirectResponse

from app.dependencies import require_auth, safe_json_parse
from app.services.kick_auth import (
    create_auth_url,
    exchange_code,
    refresh_session,
    revoke_session,
    FRONTEND_URL,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/login")
async def login():
    """Generate Kick OAuth URL and return it to the frontend."""
    url, session_id = await create_auth_url()
    return {"auth_url": url, "session_id": session_id}


@router.get("/callback")
async def callback(code: str, state: str, response: Response):
    """Handle OAuth callback from Kick — exchange code for tokens.

    The session_id is passed via a URL fragment (#) instead of a query param
    so that it is never sent to the server in Referer headers or logged in
    server access logs.
    """
    result = await exchange_code(code, state)
    if not result:
        logger.error("OAuth exchange failed for state=%s", state)
        raise HTTPException(status_code=400, detail="OAuth callback failed")

    session_id = result["session_id"]
    logger.info("OAuth exchange succeeded, session=%s", session_id[:8])

    # Use fragment (#) instead of query param (?) to prevent session_id from
    # leaking via Referer headers, server logs, and browser history.
    redirect_url = f"{FRONTEND_URL}/auth/callback#session_id={session_id}"
    resp = RedirectResponse(url=redirect_url)
    # Prevent the redirect URL from being cached or stored in browser history
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp


@router.get("/me")
async def me(session: dict = Depends(require_auth)):
    """Get current user info from session (uses Authorization header)."""
    user_data = safe_json_parse(session.get("user_data", {}))

    # Return expires_in so the frontend can schedule token refresh
    expires_in = None
    expires_at = session.get("expires_at")
    if expires_at:
        from datetime import datetime, timezone
        try:
            exp_dt = datetime.fromisoformat(expires_at)
            remaining = (exp_dt - datetime.now(timezone.utc)).total_seconds()
            expires_in = max(int(remaining), 0)
        except (ValueError, TypeError):
            pass

    return {
        "user": user_data,
        "scope": session.get("scope", ""),
        "expires_in": expires_in,
    }


@router.post("/refresh")
async def refresh(session: dict = Depends(require_auth)):
    """Refresh the access token (uses Authorization header)."""
    session_id = session["session_id"]
    result = await refresh_session(session_id)
    if not result:
        raise HTTPException(status_code=401, detail="Could not refresh token")
    return result


@router.post("/logout")
async def logout(session: dict = Depends(require_auth)):
    """Revoke tokens and clear session (uses Authorization header)."""
    session_id = session["session_id"]
    success = await revoke_session(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Logout failed")
    return {"status": "logged_out"}
