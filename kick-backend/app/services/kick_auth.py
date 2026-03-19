"""Kick OAuth 2.1 (PKCE) authentication service."""

import hashlib
import os
import secrets
import uuid
from typing import Optional

import httpx

KICK_AUTH_URL = "https://id.kick.com/oauth/authorize"
KICK_TOKEN_URL = "https://id.kick.com/oauth/token"
KICK_REVOKE_URL = "https://id.kick.com/oauth/revoke"
KICK_USER_URL = "https://api.kick.com/public/v1/users"

KICK_CLIENT_ID = os.environ.get("KICK_CLIENT_ID", "")
KICK_CLIENT_SECRET = os.environ.get("KICK_CLIENT_SECRET", "")
KICK_REDIRECT_URI = os.environ.get("KICK_REDIRECT_URI", "https://kick-toolkit.pages.dev/auth/callback")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://kick-toolkit.pages.dev")

KICK_SCOPES = "user:read channel:read chat:write events:subscribe moderation:manage chat:moderate"

# In-memory session storage: session_id -> session data
sessions: dict[str, dict] = {}

# Pending OAuth states: state -> {code_verifier, ...}
pending_auth: dict[str, dict] = {}


def generate_pkce() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge (S256)."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = (
        digest.hex()
        .encode("ascii")
    )
    # Base64url encode the SHA256 hash
    import base64
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def create_auth_url() -> tuple[str, str]:
    """Create the Kick OAuth authorization URL and return (url, session_id)."""
    code_verifier, code_challenge = generate_pkce()
    state = secrets.token_urlsafe(32)
    session_id = str(uuid.uuid4())

    pending_auth[state] = {
        "code_verifier": code_verifier,
        "session_id": session_id,
    }

    params = {
        "client_id": KICK_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": KICK_REDIRECT_URI,
        "scope": KICK_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    query = "&".join(f"{k}={httpx.QueryParams({k: v})}" for k, v in params.items())
    # Build URL properly
    url = f"{KICK_AUTH_URL}?{httpx.QueryParams(params)}"
    return url, session_id


async def exchange_code(code: str, state: str) -> Optional[dict]:
    """Exchange authorization code for tokens and fetch user info."""
    auth_data = pending_auth.pop(state, None)
    if not auth_data:
        return None

    session_id = auth_data["session_id"]
    code_verifier = auth_data["code_verifier"]

    # Exchange code for tokens
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
            return None

        token_data = token_response.json()

        # Fetch user info
        user_response = await client.get(
            KICK_USER_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )

        user_data = {}
        if user_response.status_code == 200:
            user_json = user_response.json()
            # The Kick API returns user data in a "data" array
            if "data" in user_json and len(user_json["data"]) > 0:
                user_data = user_json["data"][0]
            elif "data" in user_json and isinstance(user_json["data"], dict):
                user_data = user_json["data"]
            else:
                user_data = user_json

    # Store session
    sessions[session_id] = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "expires_in": token_data.get("expires_in"),
        "token_type": token_data.get("token_type"),
        "scope": token_data.get("scope"),
        "user": user_data,
    }

    return {"session_id": session_id, "user": user_data}


async def refresh_session(session_id: str) -> Optional[dict]:
    """Refresh the access token for a session."""
    session = sessions.get(session_id)
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
        session["access_token"] = token_data.get("access_token")
        session["refresh_token"] = token_data.get("refresh_token")
        session["expires_in"] = token_data.get("expires_in")

        return {"status": "refreshed", "expires_in": token_data.get("expires_in")}


async def revoke_session(session_id: str) -> bool:
    """Revoke tokens and delete session."""
    session = sessions.pop(session_id, None)
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


def get_session(session_id: str) -> Optional[dict]:
    """Get session data by session ID."""
    return sessions.get(session_id)
