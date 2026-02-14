-- Telegram Pulse - bootstrap-compatible schema (custom auth)
-- This schema is adapted for existing users/accounts/team_members bootstrap services.
-- It does NOT depend on Supabase Auth or auth.uid().

BEGIN;

SET search_path = public;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- ============================================================
-- Enums
-- ============================================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
    CREATE TYPE user_role AS ENUM ('owner', 'admin', 'editor', 'viewer', 'user');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'team_member_status') THEN
    CREATE TYPE team_member_status AS ENUM ('invited', 'accepted', 'suspended', 'removed');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_type') THEN
    CREATE TYPE notification_type AS ENUM (
      'welcome',
      'system',
      'security',
      'billing',
      'tracker_alert',
      'channel_alert'
    );
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'channel_status') THEN
    CREATE TYPE channel_status AS ENUM ('normal', 'verified', 'scam', 'restricted', 'deleted');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tracker_type') THEN
    CREATE TYPE tracker_type AS ENUM ('keyword', 'channel');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tracker_status') THEN
    CREATE TYPE tracker_status AS ENUM ('active', 'paused', 'archived');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ad_type') THEN
    CREATE TYPE ad_type AS ENUM ('native', 'banner', 'sponsored', 'bot', 'mini_app', 'other');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ad_media_type') THEN
    CREATE TYPE ad_media_type AS ENUM ('text', 'image', 'video', 'carousel', 'gif', 'audio', 'document', 'unknown');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'billing_status') THEN
    CREATE TYPE billing_status AS ENUM ('active', 'past_due', 'unpaid', 'cancelled', 'trialing', 'paused');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscription_status') THEN
    CREATE TYPE subscription_status AS ENUM ('active', 'trialing', 'past_due', 'canceled', 'paused', 'incomplete');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'export_status') THEN
    CREATE TYPE export_status AS ENUM ('queued', 'processing', 'completed', 'failed', 'expired', 'cancelled');
  END IF;
END
$$;

-- Ensure values exist for bootstrap enums in partially initialized DBs.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'user_role'::regtype AND enumlabel = 'owner') THEN
      ALTER TYPE user_role ADD VALUE 'owner';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'user_role'::regtype AND enumlabel = 'admin') THEN
      ALTER TYPE user_role ADD VALUE 'admin';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'user_role'::regtype AND enumlabel = 'editor') THEN
      ALTER TYPE user_role ADD VALUE 'editor';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'user_role'::regtype AND enumlabel = 'viewer') THEN
      ALTER TYPE user_role ADD VALUE 'viewer';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'user_role'::regtype AND enumlabel = 'user') THEN
      ALTER TYPE user_role ADD VALUE 'user';
    END IF;
  END IF;

  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'team_member_status') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'team_member_status'::regtype AND enumlabel = 'invited') THEN
      ALTER TYPE team_member_status ADD VALUE 'invited';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'team_member_status'::regtype AND enumlabel = 'accepted') THEN
      ALTER TYPE team_member_status ADD VALUE 'accepted';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'team_member_status'::regtype AND enumlabel = 'suspended') THEN
      ALTER TYPE team_member_status ADD VALUE 'suspended';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'team_member_status'::regtype AND enumlabel = 'removed') THEN
      ALTER TYPE team_member_status ADD VALUE 'removed';
    END IF;
  END IF;

  IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_type') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'notification_type'::regtype AND enumlabel = 'welcome') THEN
      ALTER TYPE notification_type ADD VALUE 'welcome';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'notification_type'::regtype AND enumlabel = 'system') THEN
      ALTER TYPE notification_type ADD VALUE 'system';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'notification_type'::regtype AND enumlabel = 'security') THEN
      ALTER TYPE notification_type ADD VALUE 'security';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'notification_type'::regtype AND enumlabel = 'billing') THEN
      ALTER TYPE notification_type ADD VALUE 'billing';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'notification_type'::regtype AND enumlabel = 'tracker_alert') THEN
      ALTER TYPE notification_type ADD VALUE 'tracker_alert';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'notification_type'::regtype AND enumlabel = 'channel_alert') THEN
      ALTER TYPE notification_type ADD VALUE 'channel_alert';
    END IF;
  END IF;
END
$$;

-- ============================================================
-- Utility functions
-- ============================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION channels_search_tsv_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.search_tsv := to_tsvector(
    'simple',
    unaccent(
      COALESCE(NEW.name::text, '') || ' ' ||
      COALESCE(NEW.username::text, '') || ' ' ||
      COALESCE(NEW.description, '')
    )
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION posts_search_tsv_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.search_tsv := to_tsvector(
    'simple',
    unaccent(COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content_text, ''))
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION ad_creatives_search_tsv_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.search_tsv := to_tsvector(
    'simple',
    unaccent(
      COALESCE(NEW.preview_text, '') || ' ' ||
      COALESCE(NEW.headline, '') || ' ' ||
      COALESCE(NEW.body_text, '') || ' ' ||
      COALESCE(NEW.cta_text, '')
    )
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION advertisers_search_tsv_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.search_tsv := to_tsvector(
    'simple',
    unaccent(COALESCE(NEW.name::text, '') || ' ' || COALESCE(NEW.description, ''))
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION mini_apps_search_tsv_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.search_tsv := to_tsvector(
    'simple',
    unaccent(
      COALESCE(NEW.name::text, '') || ' ' ||
      COALESCE(NEW.slug::text, '') || ' ' ||
      COALESCE(NEW.description, '')
    )
  );
  RETURN NEW;
END;
$$;

-- ============================================================
-- Bootstrap auth + account core (existing model)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name TEXT,
  role user_role NOT NULL DEFAULT 'user',
  status TEXT NOT NULL DEFAULT 'active',
  is_guest BOOLEAN NOT NULL DEFAULT FALSE,
  last_login_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
  CHECK (status IN ('active', 'pending', 'blocked', 'deleted'))
);

CREATE TABLE IF NOT EXISTS accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug CITEXT UNIQUE,
  owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  is_default BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
  CHECK (slug IS NULL OR slug ~ '^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$')
);

CREATE TABLE IF NOT EXISTS team_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role user_role NOT NULL DEFAULT 'admin',
  status team_member_status NOT NULL DEFAULT 'accepted',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  joined_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
  UNIQUE (account_id, user_id),
  UNIQUE (id, account_id)
);

CREATE TABLE IF NOT EXISTS notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  type notification_type NOT NULL DEFAULT 'welcome',
  details TEXT,
  cta TEXT,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  read_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS magic_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  token TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS magic_tokens_email_active_uq
  ON magic_tokens(email)
  WHERE used_at IS NULL;

CREATE TABLE IF NOT EXISTS oauth_identities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  provider_user_id TEXT NOT NULL,
  provider_email TEXT,
  raw_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (provider, provider_user_id),
  CHECK (provider IN ('google'))
);

CREATE TABLE IF NOT EXISTS auth_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
  access_token_hash TEXT NOT NULL UNIQUE,
  refresh_token_hash TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS account_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'viewer',
  invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
  token TEXT NOT NULL UNIQUE,
  status team_member_status NOT NULL DEFAULT 'invited',
  expires_at TIMESTAMPTZ NOT NULL,
  accepted_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  accepted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS account_invitations_active_uq
  ON account_invitations(account_id, lower(email))
  WHERE status = 'invited' AND deleted_at IS NULL;

-- ============================================================
-- User/account settings + API keys + audit
-- ============================================================
CREATE TABLE IF NOT EXISTS user_preferences (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  language_code TEXT NOT NULL DEFAULT 'en',
  timezone TEXT NOT NULL DEFAULT 'UTC',
  theme TEXT NOT NULL DEFAULT 'system',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (theme IN ('light', 'dark', 'system'))
);

CREATE TABLE IF NOT EXISTS user_notification_settings (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  email_notifications BOOLEAN NOT NULL DEFAULT true,
  telegram_bot_alerts BOOLEAN NOT NULL DEFAULT true,
  weekly_reports BOOLEAN NOT NULL DEFAULT false,
  marketing_updates BOOLEAN NOT NULL DEFAULT false,
  push_notifications BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  key_prefix TEXT NOT NULL,
  key_hash TEXT NOT NULL,
  scopes TEXT[] NOT NULL DEFAULT ARRAY['read'],
  rate_limit_per_hour INTEGER NOT NULL DEFAULT 1000,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
  revoked_at TIMESTAMPTZ,
  revoked_by UUID REFERENCES users(id) ON DELETE SET NULL,
  last_used_at TIMESTAMPTZ,
  UNIQUE (account_id, name),
  CHECK (rate_limit_per_hour > 0)
);

CREATE TABLE IF NOT EXISTS api_key_usage_daily (
  api_key_id UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  usage_date DATE NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  error_count INTEGER NOT NULL DEFAULT 0,
  average_latency_ms INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (api_key_id, usage_date),
  CHECK (request_count >= 0),
  CHECK (error_count >= 0),
  CHECK (average_latency_ms IS NULL OR average_latency_ms >= 0)
);

CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
  actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT,
  request_id TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Billing
-- ============================================================
CREATE TABLE IF NOT EXISTS billing_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code CITEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  monthly_price NUMERIC(12, 2) NOT NULL DEFAULT 0,
  annual_price NUMERIC(12, 2),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  features JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (monthly_price >= 0),
  CHECK (annual_price IS NULL OR annual_price >= 0)
);

CREATE TABLE IF NOT EXISTS account_subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL UNIQUE REFERENCES accounts(id) ON DELETE CASCADE,
  plan_id UUID NOT NULL REFERENCES billing_plans(id) ON DELETE RESTRICT,
  provider_customer_id TEXT,
  provider_subscription_id TEXT,
  status subscription_status NOT NULL DEFAULT 'trialing',
  billing_state billing_status NOT NULL DEFAULT 'trialing',
  current_period_start TIMESTAMPTZ,
  current_period_end TIMESTAMPTZ,
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
  canceled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (current_period_end IS NULL OR current_period_start IS NULL OR current_period_end >= current_period_start)
);

CREATE TABLE IF NOT EXISTS account_usage_daily (
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  usage_date DATE NOT NULL,
  channel_searches INTEGER NOT NULL DEFAULT 0,
  event_trackers_count INTEGER NOT NULL DEFAULT 0,
  api_requests_count INTEGER NOT NULL DEFAULT 0,
  exports_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (account_id, usage_date),
  CHECK (channel_searches >= 0),
  CHECK (event_trackers_count >= 0),
  CHECK (api_requests_count >= 0),
  CHECK (exports_count >= 0)
);

CREATE TABLE IF NOT EXISTS payment_methods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  provider_payment_method_id TEXT,
  brand TEXT,
  last4 CHAR(4),
  exp_month INTEGER,
  exp_year INTEGER,
  holder_name TEXT,
  is_default BOOLEAN NOT NULL DEFAULT false,
  status billing_status NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (exp_month IS NULL OR (exp_month BETWEEN 1 AND 12))
);

CREATE TABLE IF NOT EXISTS invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  subscription_id UUID REFERENCES account_subscriptions(id) ON DELETE SET NULL,
  provider_invoice_id TEXT,
  invoice_number TEXT,
  status billing_status NOT NULL DEFAULT 'active',
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  amount_subtotal NUMERIC(14, 2) NOT NULL DEFAULT 0,
  amount_tax NUMERIC(14, 2) NOT NULL DEFAULT 0,
  amount_total NUMERIC(14, 2) NOT NULL DEFAULT 0,
  period_start DATE,
  period_end DATE,
  issued_at TIMESTAMPTZ,
  due_at TIMESTAMPTZ,
  paid_at TIMESTAMPTZ,
  pdf_url TEXT,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (amount_subtotal >= 0),
  CHECK (amount_tax >= 0),
  CHECK (amount_total >= 0),
  CHECK (period_end IS NULL OR period_start IS NULL OR period_end >= period_start)
);

CREATE TABLE IF NOT EXISTS invoice_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
  description TEXT NOT NULL,
  quantity NUMERIC(12, 2) NOT NULL DEFAULT 1,
  unit_amount NUMERIC(14, 2) NOT NULL DEFAULT 0,
  total_amount NUMERIC(14, 2) NOT NULL DEFAULT 0,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (quantity > 0),
  CHECK (unit_amount >= 0),
  CHECK (total_amount >= 0)
);

-- ============================================================
-- Taxonomies
-- ============================================================
CREATE TABLE IF NOT EXISTS countries (
  code CHAR(2) PRIMARY KEY,
  name TEXT NOT NULL,
  flag_emoji TEXT,
  channels_count BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (channels_count >= 0)
);

CREATE TABLE IF NOT EXISTS categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug CITEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  icon TEXT,
  channels_count BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (channels_count >= 0)
);

CREATE TABLE IF NOT EXISTS industries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug CITEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug CITEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  usage_count BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (usage_count >= 0)
);

CREATE TABLE IF NOT EXISTS mini_app_categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug CITEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  apps_count BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (apps_count >= 0)
);

-- ============================================================
-- Channel domain
-- ============================================================
CREATE TABLE IF NOT EXISTS channels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_channel_id BIGINT NOT NULL UNIQUE,
  name CITEXT NOT NULL,
  username CITEXT UNIQUE,
  avatar_url TEXT,
  description TEXT,
  country_code CHAR(2) REFERENCES countries(code) ON DELETE SET NULL,
  primary_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
  status channel_status NOT NULL DEFAULT 'normal',
  subscribers_current BIGINT NOT NULL DEFAULT 0,
  avg_views_current BIGINT NOT NULL DEFAULT 0,
  engagement_rate_current NUMERIC(5, 2),
  posts_per_day_current NUMERIC(7, 2),
  last_post_at TIMESTAMPTZ,
  last_crawled_at TIMESTAMPTZ,
  search_tsv tsvector NOT NULL DEFAULT ''::tsvector,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (subscribers_current >= 0),
  CHECK (avg_views_current >= 0),
  CHECK (engagement_rate_current IS NULL OR (engagement_rate_current BETWEEN 0 AND 100)),
  CHECK (posts_per_day_current IS NULL OR posts_per_day_current >= 0)
);

CREATE TABLE IF NOT EXISTS channel_categories (
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  is_primary BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (channel_id, category_id)
);

CREATE TABLE IF NOT EXISTS channel_tags (
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  relevance_score NUMERIC(5, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (channel_id, tag_id),
  CHECK (relevance_score IS NULL OR (relevance_score BETWEEN 0 AND 100))
);

CREATE TABLE IF NOT EXISTS channel_keywords (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  keyword TEXT NOT NULL,
  mentions_count BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (char_length(trim(keyword)) > 0),
  CHECK (mentions_count >= 0)
);

CREATE TABLE IF NOT EXISTS channel_about (
  channel_id UUID PRIMARY KEY REFERENCES channels(id) ON DELETE CASCADE,
  about_text TEXT,
  website_url TEXT,
  contact_links JSONB NOT NULL DEFAULT '{}'::jsonb,
  language_code TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channel_metrics_daily (
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  subscribers BIGINT,
  avg_views BIGINT,
  engagement_rate NUMERIC(5, 2),
  growth_24h NUMERIC(7, 2),
  growth_7d NUMERIC(7, 2),
  growth_30d NUMERIC(7, 2),
  posts_per_day NUMERIC(7, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (channel_id, metric_date),
  CHECK (subscribers IS NULL OR subscribers >= 0),
  CHECK (avg_views IS NULL OR avg_views >= 0),
  CHECK (engagement_rate IS NULL OR (engagement_rate BETWEEN 0 AND 100)),
  CHECK (posts_per_day IS NULL OR posts_per_day >= 0)
);

CREATE TABLE IF NOT EXISTS channel_inout_daily (
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  incoming_subscribers INTEGER NOT NULL DEFAULT 0,
  outgoing_subscribers INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (channel_id, metric_date),
  CHECK (incoming_subscribers >= 0),
  CHECK (outgoing_subscribers >= 0)
);

CREATE TABLE IF NOT EXISTS channel_similarities (
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  similar_channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  similarity_score NUMERIC(5, 4) NOT NULL,
  reason TEXT,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (channel_id, similar_channel_id),
  CHECK (channel_id <> similar_channel_id),
  CHECK (similarity_score BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS account_channels (
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  alias_name TEXT,
  notes TEXT,
  monitoring_enabled BOOLEAN NOT NULL DEFAULT true,
  is_favorite BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
  PRIMARY KEY (account_id, channel_id)
);

CREATE TABLE IF NOT EXISTS member_channel_access (
  account_id UUID NOT NULL,
  team_member_id UUID NOT NULL,
  channel_id UUID NOT NULL,
  access_level user_role NOT NULL DEFAULT 'viewer',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  PRIMARY KEY (account_id, team_member_id, channel_id),
  FOREIGN KEY (account_id, team_member_id)
    REFERENCES team_members(account_id, id)
    ON DELETE CASCADE,
  FOREIGN KEY (account_id, channel_id)
    REFERENCES account_channels(account_id, channel_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS channel_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  alert_type TEXT NOT NULL,
  threshold_value NUMERIC(12, 4),
  keyword TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  notify_email BOOLEAN NOT NULL DEFAULT true,
  notify_telegram BOOLEAN NOT NULL DEFAULT true,
  notify_push BOOLEAN NOT NULL DEFAULT false,
  last_triggered_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
  CHECK (alert_type IN ('keyword', 'threshold', 'status_change', 'new_post', 'engagement_drop', 'growth_spike')),
  CHECK (alert_type <> 'threshold' OR threshold_value IS NOT NULL),
  CHECK (alert_type <> 'keyword' OR keyword IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS channel_verification_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  verification_code TEXT NOT NULL,
  verification_method TEXT NOT NULL DEFAULT 'description_code',
  status TEXT NOT NULL DEFAULT 'pending',
  evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
  requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
  confirmed_at TIMESTAMPTZ,
  confirmed_by UUID REFERENCES users(id) ON DELETE SET NULL,
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + interval '7 days'),
  CHECK (status IN ('pending', 'confirmed', 'failed', 'expired', 'cancelled')),
  CHECK (verification_method IN ('description_code', 'bot_admin', 'manual_review'))
);

-- ============================================================
-- Posts
-- ============================================================
CREATE TABLE IF NOT EXISTS posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  telegram_message_id BIGINT NOT NULL,
  external_post_url TEXT,
  title TEXT,
  content_text TEXT,
  content_html TEXT,
  media_type TEXT NOT NULL DEFAULT 'text',
  published_at TIMESTAMPTZ NOT NULL,
  edited_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ,
  is_deleted BOOLEAN NOT NULL DEFAULT false,
  views_count BIGINT NOT NULL DEFAULT 0,
  reactions_count BIGINT NOT NULL DEFAULT 0,
  comments_count BIGINT NOT NULL DEFAULT 0,
  forwards_count BIGINT NOT NULL DEFAULT 0,
  search_tsv tsvector NOT NULL DEFAULT ''::tsvector,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (channel_id, telegram_message_id),
  CHECK (media_type IN ('text', 'image', 'video', 'audio', 'document', 'poll', 'link', 'other')),
  CHECK (views_count >= 0),
  CHECK (reactions_count >= 0),
  CHECK (comments_count >= 0),
  CHECK (forwards_count >= 0)
);

CREATE TABLE IF NOT EXISTS post_metrics_daily (
  post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  views_count BIGINT,
  reactions_count BIGINT,
  comments_count BIGINT,
  forwards_count BIGINT,
  engagement_rate NUMERIC(5, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (post_id, metric_date),
  CHECK (views_count IS NULL OR views_count >= 0),
  CHECK (reactions_count IS NULL OR reactions_count >= 0),
  CHECK (comments_count IS NULL OR comments_count >= 0),
  CHECK (forwards_count IS NULL OR forwards_count >= 0),
  CHECK (engagement_rate IS NULL OR (engagement_rate BETWEEN 0 AND 100))
);

CREATE TABLE IF NOT EXISTS post_reaction_breakdown (
  post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  reaction_code TEXT NOT NULL,
  reaction_count BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (post_id, reaction_code),
  CHECK (reaction_count >= 0)
);

-- ============================================================
-- Ads + advertisers
-- ============================================================
CREATE TABLE IF NOT EXISTS advertisers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name CITEXT NOT NULL UNIQUE,
  slug CITEXT NOT NULL UNIQUE,
  industry_id UUID REFERENCES industries(id) ON DELETE SET NULL,
  logo_url TEXT,
  website_url TEXT,
  description TEXT,
  active_creatives_count INTEGER NOT NULL DEFAULT 0,
  estimated_spend_current NUMERIC(14, 2) NOT NULL DEFAULT 0,
  avg_engagement_rate_current NUMERIC(5, 2),
  total_ads_current BIGINT NOT NULL DEFAULT 0,
  channels_used_current INTEGER NOT NULL DEFAULT 0,
  trend_30d NUMERIC(7, 2),
  search_tsv tsvector NOT NULL DEFAULT ''::tsvector,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (active_creatives_count >= 0),
  CHECK (estimated_spend_current >= 0),
  CHECK (avg_engagement_rate_current IS NULL OR (avg_engagement_rate_current BETWEEN 0 AND 100)),
  CHECK (total_ads_current >= 0),
  CHECK (channels_used_current >= 0)
);

CREATE TABLE IF NOT EXISTS advertiser_metrics_daily (
  advertiser_id UUID NOT NULL REFERENCES advertisers(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  estimated_spend NUMERIC(14, 2),
  total_ads BIGINT,
  active_creatives INTEGER,
  channels_used INTEGER,
  avg_engagement_rate NUMERIC(5, 2),
  trend_percent NUMERIC(7, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (advertiser_id, metric_date),
  CHECK (estimated_spend IS NULL OR estimated_spend >= 0),
  CHECK (total_ads IS NULL OR total_ads >= 0),
  CHECK (active_creatives IS NULL OR active_creatives >= 0),
  CHECK (channels_used IS NULL OR channels_used >= 0),
  CHECK (avg_engagement_rate IS NULL OR (avg_engagement_rate BETWEEN 0 AND 100))
);

CREATE TABLE IF NOT EXISTS ad_campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  advertiser_id UUID NOT NULL REFERENCES advertisers(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  objective TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  budget NUMERIC(14, 2),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  start_date DATE,
  end_date DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
  CHECK (budget IS NULL OR budget >= 0),
  CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS ad_creatives (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES ad_campaigns(id) ON DELETE CASCADE,
  advertiser_id UUID NOT NULL REFERENCES advertisers(id) ON DELETE CASCADE,
  source_channel_id UUID REFERENCES channels(id) ON DELETE SET NULL,
  preview_text TEXT,
  headline TEXT,
  body_text TEXT,
  ad_type ad_type NOT NULL DEFAULT 'native',
  media_type ad_media_type NOT NULL DEFAULT 'text',
  media_url TEXT,
  thumbnail_url TEXT,
  destination_url TEXT,
  cta_text TEXT,
  category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
  language_code TEXT,
  posted_at TIMESTAMPTZ,
  last_seen_at TIMESTAMPTZ,
  is_active BOOLEAN NOT NULL DEFAULT true,
  search_tsv tsvector NOT NULL DEFAULT ''::tsvector,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ad_placements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  creative_id UUID NOT NULL REFERENCES ad_creatives(id) ON DELETE CASCADE,
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  placed_at TIMESTAMPTZ NOT NULL,
  removed_at TIMESTAMPTZ,
  placement_cost NUMERIC(14, 2),
  currency CHAR(3) NOT NULL DEFAULT 'USD',
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (placement_cost IS NULL OR placement_cost >= 0),
  CHECK (removed_at IS NULL OR removed_at >= placed_at)
);

CREATE TABLE IF NOT EXISTS ad_metrics_daily (
  creative_id UUID NOT NULL REFERENCES ad_creatives(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  impressions BIGINT,
  clicks BIGINT,
  ctr NUMERIC(7, 4),
  engagement_rate NUMERIC(5, 2),
  spend NUMERIC(14, 2),
  conversions BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (creative_id, metric_date),
  CHECK (impressions IS NULL OR impressions >= 0),
  CHECK (clicks IS NULL OR clicks >= 0),
  CHECK (ctr IS NULL OR (ctr BETWEEN 0 AND 100)),
  CHECK (engagement_rate IS NULL OR (engagement_rate BETWEEN 0 AND 100)),
  CHECK (spend IS NULL OR spend >= 0),
  CHECK (conversions IS NULL OR conversions >= 0)
);

CREATE TABLE IF NOT EXISTS advertiser_top_channels_daily (
  advertiser_id UUID NOT NULL REFERENCES advertisers(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  estimated_spend NUMERIC(14, 2),
  impressions BIGINT,
  engagement_rate NUMERIC(5, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (advertiser_id, snapshot_date, channel_id),
  UNIQUE (advertiser_id, snapshot_date, rank),
  CHECK (rank > 0),
  CHECK (estimated_spend IS NULL OR estimated_spend >= 0),
  CHECK (impressions IS NULL OR impressions >= 0),
  CHECK (engagement_rate IS NULL OR (engagement_rate BETWEEN 0 AND 100))
);

-- ============================================================
-- Rankings + collections
-- ============================================================
CREATE TABLE IF NOT EXISTS ranking_collections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug CITEXT NOT NULL UNIQUE,
  description TEXT,
  icon TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ranking_collection_channels (
  collection_id UUID NOT NULL REFERENCES ranking_collections(id) ON DELETE CASCADE,
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  score NUMERIC(10, 4),
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (collection_id, channel_id),
  UNIQUE (collection_id, rank),
  CHECK (rank > 0)
);

CREATE TABLE IF NOT EXISTS channel_rankings_daily (
  id BIGSERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  ranking_scope TEXT NOT NULL,
  country_code CHAR(2) REFERENCES countries(code) ON DELETE CASCADE,
  category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
  channel_id UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  score NUMERIC(10, 4),
  subscribers BIGINT,
  engagement_rate NUMERIC(5, 2),
  growth_7d NUMERIC(7, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (ranking_scope IN ('country', 'category', 'global')),
  CHECK (
    (ranking_scope = 'country' AND country_code IS NOT NULL AND category_id IS NULL) OR
    (ranking_scope = 'category' AND category_id IS NOT NULL AND country_code IS NULL) OR
    (ranking_scope = 'global' AND country_code IS NULL AND category_id IS NULL)
  ),
  CHECK (rank > 0),
  CHECK (subscribers IS NULL OR subscribers >= 0),
  CHECK (engagement_rate IS NULL OR (engagement_rate BETWEEN 0 AND 100))
);

CREATE TABLE IF NOT EXISTS advertiser_rankings_daily (
  id BIGSERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  ranking_scope TEXT NOT NULL,
  industry_id UUID REFERENCES industries(id) ON DELETE CASCADE,
  advertiser_id UUID NOT NULL REFERENCES advertisers(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  score NUMERIC(10, 4),
  estimated_spend NUMERIC(14, 2),
  avg_engagement_rate NUMERIC(5, 2),
  trend_30d NUMERIC(7, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (ranking_scope IN ('industry', 'global')),
  CHECK (
    (ranking_scope = 'industry' AND industry_id IS NOT NULL) OR
    (ranking_scope = 'global' AND industry_id IS NULL)
  ),
  CHECK (rank > 0),
  CHECK (estimated_spend IS NULL OR estimated_spend >= 0),
  CHECK (avg_engagement_rate IS NULL OR (avg_engagement_rate BETWEEN 0 AND 100))
);

-- ============================================================
-- Mini apps
-- ============================================================
CREATE TABLE IF NOT EXISTS mini_apps (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_app_id TEXT NOT NULL UNIQUE,
  name CITEXT NOT NULL UNIQUE,
  slug CITEXT NOT NULL UNIQUE,
  category_id UUID REFERENCES mini_app_categories(id) ON DELETE SET NULL,
  icon_url TEXT,
  description TEXT,
  rating NUMERIC(3, 2),
  launched_at DATE,
  daily_users_current BIGINT,
  total_users_current BIGINT,
  total_sessions_current BIGINT,
  avg_session_seconds INTEGER,
  growth_weekly NUMERIC(7, 2),
  is_verified BOOLEAN NOT NULL DEFAULT false,
  search_tsv tsvector NOT NULL DEFAULT ''::tsvector,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (rating IS NULL OR (rating BETWEEN 0 AND 5)),
  CHECK (daily_users_current IS NULL OR daily_users_current >= 0),
  CHECK (total_users_current IS NULL OR total_users_current >= 0),
  CHECK (total_sessions_current IS NULL OR total_sessions_current >= 0),
  CHECK (avg_session_seconds IS NULL OR avg_session_seconds >= 0)
);

CREATE TABLE IF NOT EXISTS mini_app_metrics_daily (
  mini_app_id UUID NOT NULL REFERENCES mini_apps(id) ON DELETE CASCADE,
  metric_date DATE NOT NULL,
  daily_users BIGINT,
  total_users BIGINT,
  sessions BIGINT,
  avg_session_seconds INTEGER,
  rating NUMERIC(3, 2),
  growth_weekly NUMERIC(7, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (mini_app_id, metric_date),
  CHECK (daily_users IS NULL OR daily_users >= 0),
  CHECK (total_users IS NULL OR total_users >= 0),
  CHECK (sessions IS NULL OR sessions >= 0),
  CHECK (avg_session_seconds IS NULL OR avg_session_seconds >= 0),
  CHECK (rating IS NULL OR (rating BETWEEN 0 AND 5))
);

CREATE TABLE IF NOT EXISTS mini_app_rankings_daily (
  id BIGSERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  category_id UUID REFERENCES mini_app_categories(id) ON DELETE CASCADE,
  mini_app_id UUID NOT NULL REFERENCES mini_apps(id) ON DELETE CASCADE,
  rank INTEGER NOT NULL,
  score NUMERIC(10, 4),
  daily_users BIGINT,
  growth_7d NUMERIC(7, 2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (rank > 0),
  CHECK (daily_users IS NULL OR daily_users >= 0)
);

-- ============================================================
-- Event tracking + exports
-- ============================================================
CREATE TABLE IF NOT EXISTS trackers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  tracker_type tracker_type NOT NULL,
  tracker_value TEXT NOT NULL,
  normalized_value CITEXT NOT NULL,
  status tracker_status NOT NULL DEFAULT 'active',
  mentions_count BIGINT NOT NULL DEFAULT 0,
  last_activity_at TIMESTAMPTZ,
  notify_push BOOLEAN NOT NULL DEFAULT true,
  notify_telegram BOOLEAN NOT NULL DEFAULT true,
  notify_email BOOLEAN NOT NULL DEFAULT false,
  paused_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID REFERENCES users(id) ON DELETE SET NULL,
  UNIQUE (account_id, tracker_type, normalized_value),
  UNIQUE (id, account_id),
  CHECK (char_length(trim(tracker_value)) > 0),
  CHECK (mentions_count >= 0)
);

CREATE TABLE IF NOT EXISTS tracker_mentions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL,
  tracker_id UUID NOT NULL,
  channel_id UUID REFERENCES channels(id) ON DELETE SET NULL,
  post_id UUID REFERENCES posts(id) ON DELETE SET NULL,
  mention_text TEXT NOT NULL,
  context_snippet TEXT,
  mentioned_at TIMESTAMPTZ NOT NULL,
  mention_seq BIGSERIAL NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  FOREIGN KEY (tracker_id, account_id)
    REFERENCES trackers(id, account_id)
    ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS export_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  export_type TEXT NOT NULL,
  filters JSONB NOT NULL DEFAULT '{}'::jsonb,
  status export_status NOT NULL DEFAULT 'queued',
  file_url TEXT,
  file_size_bytes BIGINT,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  CHECK (export_type IN (
    'channels_csv',
    'ads_csv',
    'advertisers_csv',
    'invoices_csv',
    'posts_csv',
    'mini_apps_csv',
    'custom'
  )),
  CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
  CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);

-- ============================================================
-- Constraints + indexes
-- ============================================================
CREATE UNIQUE INDEX IF NOT EXISTS channel_categories_primary_uq
  ON channel_categories(channel_id)
  WHERE is_primary;

CREATE UNIQUE INDEX IF NOT EXISTS channel_keywords_channel_keyword_uq
  ON channel_keywords(channel_id, lower(keyword));

CREATE UNIQUE INDEX IF NOT EXISTS pending_verification_per_account_channel_uq
  ON channel_verification_requests(account_id, channel_id)
  WHERE status = 'pending';

CREATE UNIQUE INDEX IF NOT EXISTS channel_rankings_row_uq
  ON channel_rankings_daily(snapshot_date, ranking_scope, channel_id, country_code, category_id);

CREATE UNIQUE INDEX IF NOT EXISTS advertiser_rankings_row_uq
  ON advertiser_rankings_daily(snapshot_date, ranking_scope, advertiser_id, industry_id);

CREATE UNIQUE INDEX IF NOT EXISTS mini_app_rankings_row_uq
  ON mini_app_rankings_daily(snapshot_date, mini_app_id, category_id);

CREATE UNIQUE INDEX IF NOT EXISTS mini_app_rankings_global_rank_uq
  ON mini_app_rankings_daily(snapshot_date, rank)
  WHERE category_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS mini_app_rankings_category_rank_uq
  ON mini_app_rankings_daily(snapshot_date, category_id, rank)
  WHERE category_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS channel_rankings_country_rank_uq
  ON channel_rankings_daily(snapshot_date, country_code, rank)
  WHERE ranking_scope = 'country';

CREATE UNIQUE INDEX IF NOT EXISTS channel_rankings_category_rank_uq
  ON channel_rankings_daily(snapshot_date, category_id, rank)
  WHERE ranking_scope = 'category';

CREATE UNIQUE INDEX IF NOT EXISTS channel_rankings_global_rank_uq
  ON channel_rankings_daily(snapshot_date, rank)
  WHERE ranking_scope = 'global';

CREATE UNIQUE INDEX IF NOT EXISTS advertiser_rankings_industry_rank_uq
  ON advertiser_rankings_daily(snapshot_date, industry_id, rank)
  WHERE ranking_scope = 'industry';

CREATE UNIQUE INDEX IF NOT EXISTS advertiser_rankings_global_rank_uq
  ON advertiser_rankings_daily(snapshot_date, rank)
  WHERE ranking_scope = 'global';

CREATE INDEX IF NOT EXISTS team_members_user_idx
  ON team_members(user_id, account_id)
  WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS account_channels_channel_idx
  ON account_channels(channel_id, account_id)
  WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS member_channel_access_member_idx
  ON member_channel_access(team_member_id, account_id);

CREATE INDEX IF NOT EXISTS api_keys_account_idx
  ON api_keys(account_id, revoked_at);

CREATE INDEX IF NOT EXISTS api_key_usage_date_idx
  ON api_key_usage_daily(usage_date DESC);

CREATE INDEX IF NOT EXISTS audit_events_account_created_idx
  ON audit_events(account_id, created_at DESC);

CREATE INDEX IF NOT EXISTS invoices_account_created_idx
  ON invoices(account_id, created_at DESC);

CREATE INDEX IF NOT EXISTS account_usage_daily_date_idx
  ON account_usage_daily(account_id, usage_date DESC);

CREATE INDEX IF NOT EXISTS notifications_user_idx
  ON notifications(user_id, created_at DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS magic_tokens_lookup_idx
  ON magic_tokens(email, token, expires_at DESC)
  WHERE used_at IS NULL;

CREATE INDEX IF NOT EXISTS oauth_identities_user_idx
  ON oauth_identities(user_id, provider);

CREATE INDEX IF NOT EXISTS auth_sessions_user_idx
  ON auth_sessions(user_id, expires_at DESC)
  WHERE revoked_at IS NULL;

-- Search indexes
CREATE INDEX IF NOT EXISTS channels_search_tsv_gin_idx
  ON channels USING gin(search_tsv);

CREATE INDEX IF NOT EXISTS channels_name_trgm_idx
  ON channels USING gin(lower(name::text) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS channels_username_trgm_idx
  ON channels USING gin(lower(coalesce(username::text, '')) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS posts_search_tsv_gin_idx
  ON posts USING gin(search_tsv);

CREATE INDEX IF NOT EXISTS posts_content_trgm_idx
  ON posts USING gin(lower(coalesce(content_text, '')) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS ad_creatives_search_tsv_gin_idx
  ON ad_creatives USING gin(search_tsv);

CREATE INDEX IF NOT EXISTS ad_creatives_preview_trgm_idx
  ON ad_creatives USING gin(lower(coalesce(preview_text, '')) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS advertisers_search_tsv_gin_idx
  ON advertisers USING gin(search_tsv);

CREATE INDEX IF NOT EXISTS advertisers_name_trgm_idx
  ON advertisers USING gin(lower(name::text) gin_trgm_ops);

CREATE INDEX IF NOT EXISTS mini_apps_search_tsv_gin_idx
  ON mini_apps USING gin(search_tsv);

CREATE INDEX IF NOT EXISTS mini_apps_name_trgm_idx
  ON mini_apps USING gin(lower(name::text) gin_trgm_ops);

-- Metrics indexes
CREATE INDEX IF NOT EXISTS channel_metrics_daily_entity_date_idx
  ON channel_metrics_daily(channel_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS channel_inout_daily_entity_date_idx
  ON channel_inout_daily(channel_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS post_metrics_daily_entity_date_idx
  ON post_metrics_daily(post_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS advertiser_metrics_daily_entity_date_idx
  ON advertiser_metrics_daily(advertiser_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS ad_metrics_daily_entity_date_idx
  ON ad_metrics_daily(creative_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS mini_app_metrics_daily_entity_date_idx
  ON mini_app_metrics_daily(mini_app_id, metric_date DESC);

CREATE INDEX IF NOT EXISTS channel_rankings_country_filter_idx
  ON channel_rankings_daily(snapshot_date DESC, country_code, rank)
  WHERE ranking_scope = 'country';

CREATE INDEX IF NOT EXISTS channel_rankings_category_filter_idx
  ON channel_rankings_daily(snapshot_date DESC, category_id, rank)
  WHERE ranking_scope = 'category';

CREATE INDEX IF NOT EXISTS advertiser_rankings_filter_idx
  ON advertiser_rankings_daily(snapshot_date DESC, industry_id, rank);

CREATE INDEX IF NOT EXISTS mini_app_rankings_filter_idx
  ON mini_app_rankings_daily(snapshot_date DESC, category_id, rank);

CREATE INDEX IF NOT EXISTS channel_similarities_channel_score_idx
  ON channel_similarities(channel_id, similarity_score DESC);

CREATE INDEX IF NOT EXISTS ad_placements_channel_placed_idx
  ON ad_placements(channel_id, placed_at DESC);

CREATE INDEX IF NOT EXISTS advertiser_top_channels_date_rank_idx
  ON advertiser_top_channels_daily(advertiser_id, snapshot_date DESC, rank);

CREATE INDEX IF NOT EXISTS trackers_account_status_idx
  ON trackers(account_id, status, updated_at DESC)
  WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS tracker_mentions_account_cursor_idx
  ON tracker_mentions(account_id, mention_seq DESC);

CREATE INDEX IF NOT EXISTS tracker_mentions_tracker_time_idx
  ON tracker_mentions(tracker_id, mentioned_at DESC);

CREATE INDEX IF NOT EXISTS export_jobs_account_status_idx
  ON export_jobs(account_id, status, created_at DESC);

-- ============================================================
-- Triggers
-- ============================================================
DROP TRIGGER IF EXISTS users_set_updated_at ON users;
CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS oauth_identities_set_updated_at ON oauth_identities;
CREATE TRIGGER oauth_identities_set_updated_at
BEFORE UPDATE ON oauth_identities
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS accounts_set_updated_at ON accounts;
CREATE TRIGGER accounts_set_updated_at
BEFORE UPDATE ON accounts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS user_preferences_set_updated_at ON user_preferences;
CREATE TRIGGER user_preferences_set_updated_at
BEFORE UPDATE ON user_preferences
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS user_notification_settings_set_updated_at ON user_notification_settings;
CREATE TRIGGER user_notification_settings_set_updated_at
BEFORE UPDATE ON user_notification_settings
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS api_keys_set_updated_at ON api_keys;
CREATE TRIGGER api_keys_set_updated_at
BEFORE UPDATE ON api_keys
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS billing_plans_set_updated_at ON billing_plans;
CREATE TRIGGER billing_plans_set_updated_at
BEFORE UPDATE ON billing_plans
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS account_subscriptions_set_updated_at ON account_subscriptions;
CREATE TRIGGER account_subscriptions_set_updated_at
BEFORE UPDATE ON account_subscriptions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS payment_methods_set_updated_at ON payment_methods;
CREATE TRIGGER payment_methods_set_updated_at
BEFORE UPDATE ON payment_methods
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS countries_set_updated_at ON countries;
CREATE TRIGGER countries_set_updated_at
BEFORE UPDATE ON countries
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS categories_set_updated_at ON categories;
CREATE TRIGGER categories_set_updated_at
BEFORE UPDATE ON categories
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS industries_set_updated_at ON industries;
CREATE TRIGGER industries_set_updated_at
BEFORE UPDATE ON industries
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS tags_set_updated_at ON tags;
CREATE TRIGGER tags_set_updated_at
BEFORE UPDATE ON tags
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS mini_app_categories_set_updated_at ON mini_app_categories;
CREATE TRIGGER mini_app_categories_set_updated_at
BEFORE UPDATE ON mini_app_categories
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS channels_set_updated_at ON channels;
CREATE TRIGGER channels_set_updated_at
BEFORE UPDATE ON channels
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS channel_about_set_updated_at ON channel_about;
CREATE TRIGGER channel_about_set_updated_at
BEFORE UPDATE ON channel_about
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS account_channels_set_updated_at ON account_channels;
CREATE TRIGGER account_channels_set_updated_at
BEFORE UPDATE ON account_channels
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS channel_alerts_set_updated_at ON channel_alerts;
CREATE TRIGGER channel_alerts_set_updated_at
BEFORE UPDATE ON channel_alerts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS posts_set_updated_at ON posts;
CREATE TRIGGER posts_set_updated_at
BEFORE UPDATE ON posts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS advertisers_set_updated_at ON advertisers;
CREATE TRIGGER advertisers_set_updated_at
BEFORE UPDATE ON advertisers
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS ad_campaigns_set_updated_at ON ad_campaigns;
CREATE TRIGGER ad_campaigns_set_updated_at
BEFORE UPDATE ON ad_campaigns
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS ad_creatives_set_updated_at ON ad_creatives;
CREATE TRIGGER ad_creatives_set_updated_at
BEFORE UPDATE ON ad_creatives
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS ranking_collections_set_updated_at ON ranking_collections;
CREATE TRIGGER ranking_collections_set_updated_at
BEFORE UPDATE ON ranking_collections
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS mini_apps_set_updated_at ON mini_apps;
CREATE TRIGGER mini_apps_set_updated_at
BEFORE UPDATE ON mini_apps
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trackers_set_updated_at ON trackers;
CREATE TRIGGER trackers_set_updated_at
BEFORE UPDATE ON trackers
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Search triggers
DROP TRIGGER IF EXISTS channels_search_tsv_biu ON channels;
CREATE TRIGGER channels_search_tsv_biu
BEFORE INSERT OR UPDATE OF name, username, description ON channels
FOR EACH ROW
EXECUTE FUNCTION channels_search_tsv_trigger();

DROP TRIGGER IF EXISTS posts_search_tsv_biu ON posts;
CREATE TRIGGER posts_search_tsv_biu
BEFORE INSERT OR UPDATE OF title, content_text ON posts
FOR EACH ROW
EXECUTE FUNCTION posts_search_tsv_trigger();

DROP TRIGGER IF EXISTS ad_creatives_search_tsv_biu ON ad_creatives;
CREATE TRIGGER ad_creatives_search_tsv_biu
BEFORE INSERT OR UPDATE OF preview_text, headline, body_text, cta_text ON ad_creatives
FOR EACH ROW
EXECUTE FUNCTION ad_creatives_search_tsv_trigger();

DROP TRIGGER IF EXISTS advertisers_search_tsv_biu ON advertisers;
CREATE TRIGGER advertisers_search_tsv_biu
BEFORE INSERT OR UPDATE OF name, description ON advertisers
FOR EACH ROW
EXECUTE FUNCTION advertisers_search_tsv_trigger();

DROP TRIGGER IF EXISTS mini_apps_search_tsv_biu ON mini_apps;
CREATE TRIGGER mini_apps_search_tsv_biu
BEFORE INSERT OR UPDATE OF name, slug, description ON mini_apps
FOR EACH ROW
EXECUTE FUNCTION mini_apps_search_tsv_trigger();

-- ============================================================
-- Helper functions for API service-level authorization checks
-- ============================================================
CREATE OR REPLACE FUNCTION account_user_role(p_account_id UUID, p_user_id UUID)
RETURNS user_role
LANGUAGE sql
STABLE
AS $$
  SELECT tm.role
  FROM team_members tm
  WHERE tm.account_id = p_account_id
    AND tm.user_id = p_user_id
    AND tm.status = 'accepted'
    AND tm.deleted_at IS NULL
  LIMIT 1;
$$;

CREATE OR REPLACE FUNCTION is_account_member(p_account_id UUID, p_user_id UUID)
RETURNS boolean
LANGUAGE sql
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM team_members tm
    WHERE tm.account_id = p_account_id
      AND tm.user_id = p_user_id
      AND tm.status = 'accepted'
      AND tm.deleted_at IS NULL
  );
$$;

-- ============================================================
-- API-facing views
-- ============================================================
CREATE OR REPLACE VIEW vw_catalog_channels AS
SELECT
  c.id AS channel_id,
  c.telegram_channel_id,
  c.name,
  c.username,
  c.country_code,
  cn.name AS country_name,
  c.status,
  (c.status = 'verified') AS verified,
  (c.status = 'scam') AS scam,
  cat.id AS category_id,
  cat.slug AS category_slug,
  cat.name AS category_name,
  COALESCE(m.subscribers, c.subscribers_current) AS subscribers,
  COALESCE(m.avg_views, c.avg_views_current) AS avg_views,
  COALESCE(m.engagement_rate, c.engagement_rate_current) AS engagement_rate,
  m.growth_24h,
  m.growth_7d,
  m.growth_30d,
  COALESCE(m.posts_per_day, c.posts_per_day_current) AS posts_per_day,
  CASE
    WHEN COALESCE(m.subscribers, c.subscribers_current) < 10000 THEN 'small'
    WHEN COALESCE(m.subscribers, c.subscribers_current) < 100000 THEN 'medium'
    WHEN COALESCE(m.subscribers, c.subscribers_current) < 1000000 THEN 'large'
    ELSE 'huge'
  END AS size_bucket,
  c.updated_at
FROM channels c
LEFT JOIN LATERAL (
  SELECT
    cmd.subscribers,
    cmd.avg_views,
    cmd.engagement_rate,
    cmd.growth_24h,
    cmd.growth_7d,
    cmd.growth_30d,
    cmd.posts_per_day
  FROM channel_metrics_daily cmd
  WHERE cmd.channel_id = c.id
  ORDER BY cmd.metric_date DESC
  LIMIT 1
) m ON true
LEFT JOIN categories cat ON cat.id = c.primary_category_id
LEFT JOIN countries cn ON cn.code = c.country_code;

CREATE OR REPLACE VIEW vw_channel_overview AS
SELECT
  c.id AS channel_id,
  c.telegram_channel_id,
  c.name,
  c.username,
  c.avatar_url,
  c.description,
  c.status,
  c.country_code,
  cat.slug AS category_slug,
  cat.name AS category_name,
  ab.about_text,
  ab.website_url,
  COALESCE(m.subscribers, c.subscribers_current) AS subscribers,
  COALESCE(m.avg_views, c.avg_views_current) AS avg_views,
  COALESCE(m.engagement_rate, c.engagement_rate_current) AS engagement_rate,
  COALESCE(m.posts_per_day, c.posts_per_day_current) AS posts_per_day,
  COALESCE(inout.incoming_30d, 0) AS incoming_30d,
  COALESCE(inout.outgoing_30d, 0) AS outgoing_30d
FROM channels c
LEFT JOIN categories cat ON cat.id = c.primary_category_id
LEFT JOIN channel_about ab ON ab.channel_id = c.id
LEFT JOIN LATERAL (
  SELECT
    cmd.subscribers,
    cmd.avg_views,
    cmd.engagement_rate,
    cmd.posts_per_day
  FROM channel_metrics_daily cmd
  WHERE cmd.channel_id = c.id
  ORDER BY cmd.metric_date DESC
  LIMIT 1
) m ON true
LEFT JOIN LATERAL (
  SELECT
    SUM(cid.incoming_subscribers)::bigint AS incoming_30d,
    SUM(cid.outgoing_subscribers)::bigint AS outgoing_30d
  FROM channel_inout_daily cid
  WHERE cid.channel_id = c.id
    AND cid.metric_date >= CURRENT_DATE - 30
) inout ON true;

CREATE OR REPLACE VIEW vw_ads_listing AS
SELECT
  ac.id AS ad_id,
  ac.campaign_id,
  ac.advertiser_id,
  a.name AS advertiser_name,
  a.slug AS advertiser_slug,
  ac.source_channel_id AS channel_id,
  ch.name AS channel_name,
  ch.username AS channel_username,
  ac.preview_text,
  ac.headline,
  ac.body_text,
  ac.ad_type,
  ac.media_type,
  ac.category_id,
  cat.slug AS category_slug,
  cat.name AS category_name,
  ac.posted_at,
  ac.last_seen_at,
  ac.is_active,
  m.impressions,
  m.clicks,
  m.ctr,
  m.engagement_rate,
  m.spend
FROM ad_creatives ac
JOIN advertisers a ON a.id = ac.advertiser_id
LEFT JOIN channels ch ON ch.id = ac.source_channel_id
LEFT JOIN categories cat ON cat.id = ac.category_id
LEFT JOIN LATERAL (
  SELECT
    amd.impressions,
    amd.clicks,
    amd.ctr,
    amd.engagement_rate,
    amd.spend
  FROM ad_metrics_daily amd
  WHERE amd.creative_id = ac.id
  ORDER BY amd.metric_date DESC
  LIMIT 1
) m ON true;

CREATE OR REPLACE VIEW vw_advertiser_rankings AS
SELECT
  ard.snapshot_date,
  ard.ranking_scope,
  ard.rank,
  ard.score,
  ard.industry_id,
  ind.slug AS industry_slug,
  ind.name AS industry_name,
  a.id AS advertiser_id,
  a.name AS advertiser_name,
  a.slug AS advertiser_slug,
  a.logo_url,
  ard.estimated_spend,
  ard.avg_engagement_rate,
  ard.trend_30d
FROM advertiser_rankings_daily ard
JOIN advertisers a ON a.id = ard.advertiser_id
LEFT JOIN industries ind ON ind.id = ard.industry_id;

CREATE OR REPLACE VIEW vw_mini_apps_latest AS
SELECT
  ma.id AS mini_app_id,
  ma.telegram_app_id,
  ma.name,
  ma.slug,
  ma.icon_url,
  ma.description,
  ma.rating,
  ma.launched_at,
  mac.id AS category_id,
  mac.slug AS category_slug,
  mac.name AS category_name,
  COALESCE(mm.daily_users, ma.daily_users_current) AS daily_users,
  COALESCE(mm.total_users, ma.total_users_current) AS total_users,
  COALESCE(mm.sessions, ma.total_sessions_current) AS sessions,
  COALESCE(mm.avg_session_seconds, ma.avg_session_seconds) AS avg_session_seconds,
  COALESCE(mm.growth_weekly, ma.growth_weekly) AS growth_weekly
FROM mini_apps ma
LEFT JOIN mini_app_categories mac ON mac.id = ma.category_id
LEFT JOIN LATERAL (
  SELECT
    mad.daily_users,
    mad.total_users,
    mad.sessions,
    mad.avg_session_seconds,
    mad.growth_weekly
  FROM mini_app_metrics_daily mad
  WHERE mad.mini_app_id = ma.id
  ORDER BY mad.metric_date DESC
  LIMIT 1
) mm ON true;

CREATE OR REPLACE VIEW vw_account_channel_insights AS
SELECT
  ac.account_id,
  ac.channel_id,
  ac.alias_name,
  ac.is_favorite,
  ac.monitoring_enabled,
  ac.created_at,
  c.name,
  c.username,
  c.status,
  COALESCE(m.subscribers, c.subscribers_current) AS subscribers,
  COALESCE(m.avg_views, c.avg_views_current) AS avg_views,
  COALESCE(m.engagement_rate, c.engagement_rate_current) AS engagement_rate,
  m.growth_30d
FROM account_channels ac
JOIN channels c ON c.id = ac.channel_id
LEFT JOIN LATERAL (
  SELECT
    cmd.subscribers,
    cmd.avg_views,
    cmd.engagement_rate,
    cmd.growth_30d
  FROM channel_metrics_daily cmd
  WHERE cmd.channel_id = ac.channel_id
  ORDER BY cmd.metric_date DESC
  LIMIT 1
) m ON true
WHERE ac.deleted_at IS NULL;

-- Backward compatibility alias for old naming
CREATE OR REPLACE VIEW vw_workspace_channel_insights AS
SELECT
  account_id AS workspace_id,
  channel_id,
  alias_name,
  is_favorite,
  monitoring_enabled,
  created_at,
  name,
  username,
  status,
  subscribers,
  avg_views,
  engagement_rate,
  growth_30d
FROM vw_account_channel_insights;

COMMIT;
