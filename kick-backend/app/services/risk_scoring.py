"""ML-powered adaptive risk scoring engine."""

import json
import logging
import math
from typing import Optional

from app.services.db import get_conn, _now_iso

logger = logging.getLogger(__name__)

# Default feature weights (used before any training)
DEFAULT_WEIGHTS: dict[str, float] = {
    "account_age_score": 3.0,
    "follower_score": 2.0,
    "follow_status_score": 1.0,
    "name_similarity_score": 2.5,
    "fingerprint_score": 3.0,
    "behavior_similarity_score": 2.0,
    "chat_history_score": 1.5,
    "pattern_score": 1.5,
}


def _sigmoid(x: float) -> float:
    """Sigmoid function for logistic regression."""
    return 1.0 / (1.0 + math.exp(-max(min(x, 500), -500)))


def calculate_account_age_score(account_age_days: int) -> float:
    """Score based on account age (0-1, higher = more suspicious)."""
    if account_age_days < 1:
        return 1.0
    if account_age_days < 7:
        return 0.7
    if account_age_days < 30:
        return 0.4
    if account_age_days < 90:
        return 0.2
    return 0.0


def calculate_follower_score(follower_count: int) -> float:
    """Score based on follower count (0-1, higher = more suspicious)."""
    if follower_count == 0:
        return 1.0
    if follower_count < 5:
        return 0.6
    if follower_count < 20:
        return 0.3
    return 0.0


class RiskScoringEngine:
    """Adaptive risk scoring engine that learns from moderator actions."""

    async def get_weights(self, channel: str) -> dict[str, float]:
        """Get feature weights for a channel (personalized or default)."""
        async with get_conn() as conn:
            row = await conn.execute(
                "SELECT feature_weights FROM risk_model_weights WHERE channel = %s",
                (channel,),
            )
            result = await row.fetchone()

        if result and result["feature_weights"]:
            weights = result["feature_weights"]
            if isinstance(weights, str):
                weights = json.loads(weights)
            return weights
        return DEFAULT_WEIGHTS.copy()

    async def calculate_risk(
        self,
        channel: str,
        features: dict[str, float],
    ) -> float:
        """Calculate risk score (0-100) using weighted features.

        Features dict should contain scores from 0-1 for each feature.
        """
        weights = await self.get_weights(channel)

        # Weighted sum
        weighted_sum = 0.0
        total_weight = 0.0
        for feature_name, feature_value in features.items():
            weight = weights.get(feature_name, 1.0)
            weighted_sum += feature_value * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        # Normalize to 0-100
        raw_score = (weighted_sum / total_weight) * 100
        return min(max(raw_score, 0.0), 100.0)

    async def record_action(
        self,
        username: str,
        channel: str,
        action: str,
        risk_score: float,
        features: dict[str, float],
        performed_by: str = "system",
    ) -> None:
        """Record a moderation action for future model training."""
        async with get_conn() as conn:
            await conn.execute(
                """INSERT INTO moderation_actions
                   (username, channel, action, risk_score_at_action, features, performed_by, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (username, channel, action, risk_score,
                 json.dumps(features), performed_by, _now_iso()),
            )
            await conn.commit()

    async def retrain(self, channel: str) -> dict:
        """Retrain the risk model for a channel using recorded actions.

        Uses a simple gradient descent approach on logistic regression.
        """
        async with get_conn() as conn:
            row = await conn.execute(
                "SELECT action, features FROM moderation_actions WHERE channel = %s",
                (channel,),
            )
            actions = await row.fetchall()

        if not actions or len(actions) < 5:
            return {
                "status": "insufficient_data",
                "samples": len(actions) if actions else 0,
                "required": 5,
            }

        # Prepare training data
        # Label: ban/timeout = 1 (suspicious), whitelist/unban/ignore = 0 (safe)
        positive_actions = {"ban", "timeout"}
        feature_names = list(DEFAULT_WEIGHTS.keys())

        weights = {name: DEFAULT_WEIGHTS.get(name, 1.0) for name in feature_names}
        learning_rate = 0.1
        epochs = 50

        samples: list[tuple[dict[str, float], float]] = []
        for action_row in actions:
            action_row = dict(action_row)
            features = action_row["features"]
            if isinstance(features, str):
                features = json.loads(features)
            label = 1.0 if action_row["action"] in positive_actions else 0.0
            samples.append((features, label))

        # Simple gradient descent
        for _ in range(epochs):
            for features, label in samples:
                # Forward pass
                z = sum(
                    features.get(name, 0.0) * weights.get(name, 1.0)
                    for name in feature_names
                )
                prediction = _sigmoid(z)
                error = prediction - label

                # Update weights
                for name in feature_names:
                    gradient = error * features.get(name, 0.0)
                    weights[name] -= learning_rate * gradient
                    # Clamp weights to reasonable range
                    weights[name] = max(0.1, min(weights[name], 10.0))

        # Save updated weights
        now = _now_iso()
        async with get_conn() as conn:
            row = await conn.execute(
                "SELECT model_version FROM risk_model_weights WHERE channel = %s",
                (channel,),
            )
            existing = await row.fetchone()
            version = (existing["model_version"] + 1) if existing else 1

            await conn.execute(
                """INSERT INTO risk_model_weights (channel, feature_weights, training_samples, last_trained_at, model_version)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (channel) DO UPDATE SET
                       feature_weights = EXCLUDED.feature_weights,
                       training_samples = EXCLUDED.training_samples,
                       last_trained_at = EXCLUDED.last_trained_at,
                       model_version = EXCLUDED.model_version""",
                (channel, json.dumps(weights), len(samples), now, version),
            )
            await conn.commit()

        logger.info(
            "Risk model retrained for channel=%s samples=%d version=%d",
            channel, len(samples), version,
        )

        return {
            "status": "trained",
            "samples": len(samples),
            "version": version,
            "weights": weights,
        }

    async def get_model_stats(self, channel: str) -> Optional[dict]:
        """Get model statistics for a channel."""
        async with get_conn() as conn:
            row = await conn.execute(
                "SELECT * FROM risk_model_weights WHERE channel = %s",
                (channel,),
            )
            result = await row.fetchone()

        if not result:
            return {
                "channel": channel,
                "feature_weights": DEFAULT_WEIGHTS,
                "training_samples": 0,
                "last_trained_at": None,
                "model_version": 0,
                "status": "using_defaults",
            }

        stats = dict(result)
        if isinstance(stats["feature_weights"], str):
            stats["feature_weights"] = json.loads(stats["feature_weights"])
        stats["status"] = "trained"
        return stats


# Module-level singleton
risk_engine = RiskScoringEngine()
