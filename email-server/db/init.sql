-- =====================================================
-- Mail Server Database Schema
-- =====================================================

-- Virtual domains managed by this mail server
CREATE TABLE IF NOT EXISTS domains (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Virtual mailbox users
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    domain_id   INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,  -- stored as {SCHEME}hash via Dovecot
    quota       BIGINT NOT NULL DEFAULT 1073741824,  -- 1 GB default
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    is_admin    BOOLEAN NOT NULL DEFAULT FALSE,
    display_name VARCHAR(255) DEFAULT '',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Virtual aliases (forwarding addresses)
CREATE TABLE IF NOT EXISTS aliases (
    id          SERIAL PRIMARY KEY,
    domain_id   INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    source      VARCHAR(255) NOT NULL,  -- e.g. info@example.com
    destination VARCHAR(255) NOT NULL,  -- e.g. user@example.com
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source, destination)
);

-- DKIM keys per domain
CREATE TABLE IF NOT EXISTS dkim_keys (
    id          SERIAL PRIMARY KEY,
    domain_id   INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    selector    VARCHAR(63) NOT NULL DEFAULT 'mail',
    private_key TEXT NOT NULL,
    public_key  TEXT NOT NULL,
    key_size    INTEGER NOT NULL DEFAULT 2048,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(domain_id, selector)
);

-- Server settings (key-value store for web UI configuration)
CREATE TABLE IF NOT EXISTS settings (
    key         VARCHAR(255) PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Postfix/Dovecot SQL lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_aliases_source ON aliases(source);
CREATE INDEX IF NOT EXISTS idx_domains_name ON domains(name);

-- Insert default settings
INSERT INTO settings (key, value) VALUES
    ('max_message_size', '52428800'),
    ('quota_default', '1073741824'),
    ('spam_threshold', '6.0'),
    ('greylist_enabled', 'true'),
    ('antivirus_enabled', 'true'),
    ('welcome_email_enabled', 'true'),
    ('autoconfig_enabled', 'true')
ON CONFLICT (key) DO NOTHING;
