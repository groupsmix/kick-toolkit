"""Unit tests for schema module organization."""

from app.services.schema import all_schemas, _ALL_SCHEMAS


def test_all_schemas_returns_string():
    result = all_schemas()
    assert isinstance(result, str)


def test_all_schemas_not_empty():
    result = all_schemas()
    assert len(result) > 0


def test_all_schemas_contains_all_tables():
    """Verify key tables from each domain are present."""
    schema = all_schemas()
    expected_tables = [
        "bot_configs", "bot_commands", "timed_messages", "moderation_rules",
        "chat_logs",
        "giveaways", "giveaway_fraud_flags",
        "sessions", "pending_auth",
        "anti_alt_settings", "flagged_accounts", "banned_users",
        "tournaments", "saved_ideas",
        "subscriptions",
        "streamer_snapshots", "growth_predictions",
        "coach_settings", "stream_sessions",
        "hype_moments", "generated_clips",
        "viewer_sessions", "heatmap_snapshots",
        "organizations", "org_members",
        "seller_profiles", "marketplace_items",
        "loyalty_settings", "loyalty_points",
        "song_queue_settings", "song_requests",
        "stream_schedules",
        "streamer_profiles",
        "overlay_settings", "alert_queue",
        "stream_intel_sessions", "stream_scores",
        "viewer_profiles",
        "debrief_results",
        "discord_bot_configs",
        "revenue_entries",
        "highlight_markers",
        "polls", "poll_votes", "predictions", "prediction_bets",
        "translation_settings",
    ]
    for table in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema, f"Missing table: {table}"


def test_schema_module_count():
    """We should have 26 domain modules."""
    assert len(_ALL_SCHEMAS) == 26


def test_each_schema_is_valid_sql():
    """Each schema module should contain at least one CREATE TABLE."""
    for i, schema in enumerate(_ALL_SCHEMAS):
        assert "CREATE TABLE" in schema, f"Schema module {i} has no CREATE TABLE"
