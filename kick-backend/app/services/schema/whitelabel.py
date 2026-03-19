"""White-Label Platform schema."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    owner_user_id TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'starter',
    status TEXT NOT NULL DEFAULT 'active',
    max_members INT NOT NULL DEFAULT 5,
    custom_domain TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS org_members (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',
    channel TEXT,
    joined_at TEXT NOT NULL,
    UNIQUE(org_id, user_id)
);

CREATE TABLE IF NOT EXISTS org_branding (
    org_id TEXT PRIMARY KEY,
    logo_url TEXT,
    primary_color TEXT NOT NULL DEFAULT '#10b981',
    secondary_color TEXT NOT NULL DEFAULT '#6366f1',
    accent_color TEXT NOT NULL DEFAULT '#f59e0b',
    dark_mode BOOLEAN NOT NULL DEFAULT TRUE,
    custom_css TEXT,
    welcome_message TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS org_settings (
    org_id TEXT PRIMARY KEY,
    features_enabled JSONB NOT NULL DEFAULT '["coach","analytics","clips","heatmap"]',
    default_role TEXT NOT NULL DEFAULT 'viewer',
    require_approval BOOLEAN NOT NULL DEFAULT FALSE,
    billing_email TEXT,
    updated_at TEXT NOT NULL
);
"""
