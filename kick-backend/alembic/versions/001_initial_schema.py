"""Initial schema — all 69 tables.

Revision ID: 001
Revises: None
Create Date: 2026-03-19

This migration captures the full existing schema so that future changes
can be expressed as incremental Alembic migrations instead of relying on
CREATE TABLE IF NOT EXISTS at startup.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import the full schema from the modular schema package
    from app.services.schema import all_schemas
    op.execute(all_schemas())


def downgrade() -> None:
    # List every table in reverse dependency order for a clean teardown.
    tables = [
        "translation_settings",
        "prediction_bets", "predictions",
        "poll_votes", "polls",
        "highlight_markers",
        "revenue_entries",
        "discord_bot_configs",
        "debrief_results",
        "viewer_profiles",
        "best_time_slots", "stream_scores", "stream_intel_sessions",
        "alert_queue", "overlay_settings",
        "streamer_profiles",
        "stream_schedules",
        "song_requests", "song_queue_settings",
        "loyalty_redemptions", "loyalty_rewards", "loyalty_points", "loyalty_settings",
        "seller_payouts", "marketplace_reviews", "marketplace_purchases",
        "marketplace_items", "seller_profiles",
        "org_settings", "org_branding", "org_members", "organizations",
        "heatmap_snapshots", "content_segments", "viewer_sessions",
        "clip_posts", "generated_clips", "hype_moments",
        "stream_snapshots", "coach_suggestions", "stream_sessions", "coach_settings",
        "streamer_stock_scores", "growth_comparisons", "growth_predictions", "streamer_snapshots",
        "subscriptions",
        "saved_ideas", "tournaments",
        "giveaway_fraud_flags", "giveaways",
        "raid_settings", "raid_events",
        "risk_model_weights", "moderation_actions",
        "whitelisted_users", "user_challenges",
        "behavior_profiles", "user_fingerprints",
        "banned_users", "flagged_accounts", "anti_alt_settings",
        "moderation_rules", "timed_messages", "bot_commands", "bot_configs",
        "chat_logs",
        "pending_auth", "sessions",
    ]
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
