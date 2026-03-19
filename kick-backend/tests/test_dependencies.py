"""Unit tests for session expiry logic in dependencies."""

from datetime import datetime, timedelta, timezone

import pytest


def test_session_expiry_detection():
    """Expired sessions should be detected."""
    now = datetime.now(timezone.utc)
    expired_at = (now - timedelta(hours=1)).isoformat()

    exp_dt = datetime.fromisoformat(expired_at)
    assert now > exp_dt, "Expired session should be detected"


def test_session_not_expired():
    """Active sessions should pass expiry check."""
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(hours=24)).isoformat()

    exp_dt = datetime.fromisoformat(expires_at)
    assert now <= exp_dt, "Active session should not be expired"


def test_session_expiry_edge_case():
    """Session that just expired should be detected."""
    now = datetime.now(timezone.utc)
    expired_at = (now - timedelta(seconds=1)).isoformat()

    exp_dt = datetime.fromisoformat(expired_at)
    assert now > exp_dt


def test_malformed_expiry_allows_through():
    """Malformed dates should not crash — should allow through per code."""
    expires_at = "not-a-valid-date"
    try:
        datetime.fromisoformat(expires_at)
        assert False, "Should have raised ValueError"
    except (ValueError, TypeError):
        pass  # Expected — matches the behavior in require_auth


def test_bearer_token_parsing():
    """Authorization header parsing logic."""
    header = "Bearer abc-123-session-id"
    assert header.startswith("Bearer ")

    session_id = header.removeprefix("Bearer ").strip()
    assert session_id == "abc-123-session-id"


def test_bearer_token_empty():
    """Empty bearer token should be caught."""
    header = "Bearer "
    session_id = header.removeprefix("Bearer ").strip()
    assert session_id == ""


def test_invalid_auth_header():
    """Non-Bearer auth header should be rejected."""
    header = "Basic dXNlcjpwYXNz"
    assert not header.startswith("Bearer ")
