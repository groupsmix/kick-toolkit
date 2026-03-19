"""Kick OAuth 2.1 (PKCE) authentication service."""

import base64
import hashlib
import json
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from app.services.db import get_conn

SESSION_LIFETIME_HOURS = int(os.environ.get("SESSION_LIFETIME_HOURS", "168"))  # 7 days

logger = logging.getLogger(__name__)

KICK_AUTH_URL = "https://id.kick.com/oauth/authorize"
KICK_TOKEN_URL = "https://id.kick.com/oauth/token"
KICK_REVOKE_URL = "https://id.kick.com/oauth/revoke"
KICK_USER_URL = "https://api.kick.com/public/v1/users"

KICK_CLIENT_ID = os.environ.get("KICK_CLIENT_ID", "")
KICK_CLIENT_SECRET = os.environ.get("KICK_CLIENT_SECRET", "")
KICK_REDIRECT_URI = os.environ.get("KICK_REDIRECT_URI", "http://localhost:5173/auth/callback")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

KICK_SCOPES = "user:read channel:read chat:write events:subscribe moderation:manage chat:moderate"


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


async def create_auth_url() -> tuple[str, str]:
    """Create the Kick OAuth authorization URL and return (url, session_id)."""
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    session_id = str(uuid.uuid4())

    async with get_conn() as conn:
        await conn.execute(
            "INSERT INTO pending_auth (state, code_verifier, session_id) VALUES (%s, %s, %s)",
            (state, code_verifier, session_id),
        )
        await conn.commit()

    params = {
        "client_id": KICK_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": KICK_REDIRECT_URI,
        "scope": KICK_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = f"{KICK_AUTH_URL}?{httpx.QueryParams(params)}"
    return url, session_id


async def exchange_code(code: str, state: str) -> Optional[dict]:
    """Exchange authorization code for tokens and fetch user info."""
    async with get_conn() as conn:
        row = await conn.execute(
            "DELETE FROM pending_auth WHERE state = %s RETURNING code_verifier, session_id",
            (state,),
        )
        auth_data = await row.fetchone()
        await conn.commit()

    if not auth_data:
        return None

    session_id = auth_data["session_id"]
    code_verifier = auth_data["code_verifier"]

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            KICK_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": KICK_CLIENT_ID,
                "client_secret": KICK_CLIENT_SECRET,
                "redirect_uri": KICK_REDIRECT_URI,
                "code_verifier": code_verifier,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_response.status_code != 200:
            logger.error("Token exchange failed: status=%s body=%s", token_response.status_code, token_response.text[:200])
            return None

        token_data = token_response.json()
        logger.info("Token exchange succeeded, fetching user info")

        user_response = await client.get(
            KICK_USER_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

        user_data = {}
        if user_response.status_code == 200:
            user_json = user_response.json()
            if "data" in user_json and isinstance(user_json["data"], list) and len(user_json["data"]) > 0:
                user_data = user_json["data"][0]
            elif "data" in user_json and isinstance(user_json["data"], dict):
                user_data = user_json["data"]
            else:
                user_data = user_json
        else:
            logger.warning("User info fetch failed: status=%s", user_response.status_code)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=SESSION_LIFETIME_HOURS)

    async with get_conn() as conn:
        await conn.execute(
            """INSERT INTO sessions (session_id, access_token, refresh_token, expires_in, token_type, scope, user_data, created_at, expires_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (session_id) DO UPDATE SET
                   access_token = EXCLUDED.access_token,
                   refresh_token = EXCLUDED.refresh_token,
                   expires_in = EXCLUDED.expires_in,
                   token_type = EXCLUDED.token_type,
                   scope = EXCLUDED.scope,
                   user_data = EXCLUDED.user_data,
                   expires_at = EXCLUDED.expires_at""",
            (session_id, token_data.get("access_token"), token_data.get("refresh_token"),
             token_data.get("expires_in"), token_data.get("token_type"),
             token_data.get("scope"), json.dumps(user_data),
             now.isoformat(), expires_at.isoformat()),
        )
        await conn.commit()

    return {"session_id": session_id, "user": user_data}


async def refresh_session(session_id: str) -> Optional[dict]:
    """Refresh the access token for a session."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT refresh_token FROM sessions WHERE session_id = %s",
            (session_id,),
        )
        session = await row.fetchone()

    if not session or not session.get("refresh_token"):
        return None

    async with httpx.AsyncClient() as client:
        response = await client.post(
            KICK_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": KICK_CLIENT_ID,
                "client_secret": KICK_CLIENT_SECRET,
                "refresh_token": session["refresh_token"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            return None

        token_data = response.json()

    async with get_conn() as conn:
        await conn.execute(
            """UPDATE sessions SET access_token = %s, refresh_token = %s, expires_in = %s
               WHERE session_id = %s""",
            (token_data.get("access_token"), token_data.get("refresh_token"),
             token_data.get("expires_in"), session_id),
        )
        await conn.commit()

    return {"status": "refreshed", "expires_in": token_data.get("expires_in")}


async def revoke_session(session_id: str) -> bool:
    """Revoke tokens and delete session."""
    async with get_conn() as conn:
        row = await conn.execute(
            "DELETE FROM sessions WHERE session_id = %s RETURNING access_token",
            (session_id,),
        )
        session = await row.fetchone()
        await conn.commit()

    if not session:
        return False

    access_token = session.get("access_token")
    if access_token:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{KICK_REVOKE_URL}?token={access_token}&token_hint_type=access_token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

    return True


async def get_session(session_id: str) -> Optional[dict]:
    """Get session data by session ID."""
    async with get_conn() as conn:
        row = await conn.execute(
            "SELECT session_id, access_token, refresh_token, expires_in, token_type, scope, user_data FROM sessions WHERE session_id = %s",
            (session_id,),
        )
        session = await row.fetchone()

    if not session:
        return None
    return dict(session)
