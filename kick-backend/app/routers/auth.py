"""Kick OAuth 2.1 authentication routes."""

import json
import logging

from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import RedirectResponse

from app.services.kick_auth import (
    create_auth_url,
    exchange_code,
    get_session,
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
    """Handle OAuth callback from Kick — exchange code for tokens."""
    result = await exchange_code(code, state)
    if not result:
        logger.error("OAuth exchange failed for state=%s", state)
        raise HTTPException(status_code=400, detail="OAuth callback failed")

    session_id = result["session_id"]
    logger.info("OAuth exchange succeeded, session=%s", session_id[:8])

    redirect_url = f"{FRONTEND_URL}/auth/callback?session_id={session_id}"
    resp = RedirectResponse(url=redirect_url)
    return resp


@router.get("/me")
async def me(session_id: str):
    """Get current user info from session."""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_data = session.get("user_data", {})
    # Guard against double-serialised JSON (stored as string instead of dict)
    if isinstance(user_data, str):
        try:
            user_data = json.loads(user_data)
        except (json.JSONDecodeError, TypeError):
            user_data = {}

    return {
        "user": user_data,
        "scope": session.get("scope", ""),
    }


@router.post("/refresh")
async def refresh(session_id: str):
    """Refresh the access token."""
    result = await refresh_session(session_id)
    if not result:
        raise HTTPException(status_code=401, detail="Could not refresh token")
    return result


@router.post("/logout")
async def logout(session_id: str):
    """Revoke tokens and clear session."""
    success = await revoke_session(session_id)
    if not success:
        raise HTTPException(status_code=400, detail="Logout failed")
    return {"status": "logged_out"}
