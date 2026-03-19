"""Unit tests for the risk scoring engine."""

import math

from app.services.risk_scoring import (
    RiskScoringEngine,
    _sigmoid,
    calculate_account_age_score,
    calculate_follower_score,
    DEFAULT_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Sigmoid function tests
# ---------------------------------------------------------------------------

def test_sigmoid_zero():
    assert _sigmoid(0) == 0.5


def test_sigmoid_positive():
    result = _sigmoid(5)
    assert 0.99 < result < 1.0


def test_sigmoid_negative():
    result = _sigmoid(-5)
    assert 0.0 < result < 0.01


def test_sigmoid_clamps_large_positive():
    """Should not overflow for very large inputs."""
    result = _sigmoid(1000)
    assert result == 1.0 / (1.0 + math.exp(-500))  # clamped to 500


def test_sigmoid_clamps_large_negative():
    result = _sigmoid(-1000)
    assert result == 1.0 / (1.0 + math.exp(500))


# ---------------------------------------------------------------------------
# Account age scoring tests
# ---------------------------------------------------------------------------

def test_account_age_new_account():
    """Brand-new accounts (< 1 day) should be max suspicious."""
    assert calculate_account_age_score(0) == 1.0


def test_account_age_one_week():
    assert calculate_account_age_score(3) == 0.7


def test_account_age_one_month():
    assert calculate_account_age_score(15) == 0.4


def test_account_age_three_months():
    assert calculate_account_age_score(60) == 0.2


def test_account_age_old_account():
    """Accounts older than 90 days are fully trusted."""
    assert calculate_account_age_score(365) == 0.0


# ---------------------------------------------------------------------------
# Follower count scoring tests
# ---------------------------------------------------------------------------

def test_follower_score_zero():
    assert calculate_follower_score(0) == 1.0


def test_follower_score_few():
    assert calculate_follower_score(3) == 0.6


def test_follower_score_some():
    assert calculate_follower_score(10) == 0.3


def test_follower_score_many():
    assert calculate_follower_score(100) == 0.0


# ---------------------------------------------------------------------------
# RiskScoringEngine.calculate_risk (offline — no DB)
# ---------------------------------------------------------------------------

class FakeRiskEngine(RiskScoringEngine):
    """RiskScoringEngine subclass that uses default weights without DB."""

    async def get_weights(self, channel: str) -> dict[str, float]:
        return DEFAULT_WEIGHTS.copy()


import asyncio


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_calculate_risk_all_zeros():
    engine = FakeRiskEngine()
    features = {k: 0.0 for k in DEFAULT_WEIGHTS}
    score = _run(engine.calculate_risk("test_channel", features))
    assert score == 0.0


def test_calculate_risk_all_ones():
    engine = FakeRiskEngine()
    features = {k: 1.0 for k in DEFAULT_WEIGHTS}
    score = _run(engine.calculate_risk("test_channel", features))
    assert score == 100.0


def test_calculate_risk_mixed():
    engine = FakeRiskEngine()
    features = {
        "account_age_score": 0.7,
        "follower_score": 0.6,
        "follow_status_score": 0.0,
        "name_similarity_score": 0.0,
        "fingerprint_score": 0.0,
        "behavior_similarity_score": 0.0,
        "chat_history_score": 0.0,
        "pattern_score": 0.0,
    }
    score = _run(engine.calculate_risk("test_channel", features))
    # Weighted sum: (0.7*3 + 0.6*2) / (3+2+1+2.5+3+2+1.5+1.5) = 3.3 / 16.5 = 0.2 -> 20.0
    assert 0 < score < 100
    assert round(score, 1) == 20.0


def test_calculate_risk_clamped_high():
    """Scores above 100 should be clamped."""
    engine = FakeRiskEngine()
    # All features at max
    features = {k: 1.0 for k in DEFAULT_WEIGHTS}
    score = _run(engine.calculate_risk("test_channel", features))
    assert score <= 100.0


def test_calculate_risk_empty_features():
    engine = FakeRiskEngine()
    score = _run(engine.calculate_risk("test_channel", {}))
    assert score == 0.0


def test_calculate_risk_unknown_feature():
    """Unknown feature names should use weight=1.0."""
    engine = FakeRiskEngine()
    features = {"unknown_feature": 0.5}
    score = _run(engine.calculate_risk("test_channel", features))
    # (0.5 * 1.0) / 1.0 * 100 = 50.0
    assert score == 50.0
