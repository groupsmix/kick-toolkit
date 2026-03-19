"""Unit tests for authentication logic."""

import hashlib
import base64

from app.services.kick_auth import generate_pkce


def test_generate_pkce_returns_tuple():
    verifier, challenge = generate_pkce()
    assert isinstance(verifier, str)
    assert isinstance(challenge, str)


def test_generate_pkce_verifier_length():
    """PKCE verifier should be reasonably long (>= 43 chars per spec)."""
    verifier, _ = generate_pkce()
    assert len(verifier) >= 43


def test_generate_pkce_challenge_is_s256():
    """Code challenge should be base64url(sha256(verifier)) without padding."""
    verifier, challenge = generate_pkce()
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    assert challenge == expected


def test_generate_pkce_unique():
    """Each call should produce unique values."""
    v1, c1 = generate_pkce()
    v2, c2 = generate_pkce()
    assert v1 != v2
    assert c1 != c2


def test_generate_pkce_challenge_no_padding():
    """Base64 padding ('=') must be stripped for PKCE S256."""
    _, challenge = generate_pkce()
    assert "=" not in challenge
