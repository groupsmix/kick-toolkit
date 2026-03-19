"""Multi-Language Chat Translation schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS translation_settings (
    channel TEXT PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    target_language TEXT NOT NULL DEFAULT 'en',
    auto_translate BOOLEAN NOT NULL DEFAULT FALSE,
    show_original BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TEXT NOT NULL
);
"""
