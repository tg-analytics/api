BEGIN;

SET search_path = public;

-- ============================================================
-- Seed: core auth/account
-- ============================================================
INSERT INTO users (id, email, first_name, last_name, role, status)
VALUES
  ('11111111-1111-1111-1111-111111111111', 'owner@tgpulse.local', 'Alex', 'Owner', 'owner', 'active'),
  ('22222222-2222-2222-2222-222222222222', 'editor@tgpulse.local', 'Nina', 'Editor', 'editor', 'active')
ON CONFLICT (id) DO UPDATE SET
  email = EXCLUDED.email,
  first_name = EXCLUDED.first_name,
  last_name = EXCLUDED.last_name,
  role = EXCLUDED.role,
  status = EXCLUDED.status,
  updated_at = NOW();

INSERT INTO accounts (id, name, slug, owner_user_id, is_default, created_by, updated_by)
VALUES
  ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Telegram Pulse Demo', 'telegram-pulse-demo', '11111111-1111-1111-1111-111111111111', true, '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  slug = EXCLUDED.slug,
  owner_user_id = EXCLUDED.owner_user_id,
  updated_by = EXCLUDED.updated_by,
  updated_at = NOW();

INSERT INTO team_members (id, account_id, user_id, role, status, created_by, joined_at)
VALUES
  ('aaaaaaaa-0000-0000-0000-000000000001', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'owner', 'accepted', '11111111-1111-1111-1111-111111111111', NOW() - interval '120 days'),
  ('aaaaaaaa-0000-0000-0000-000000000002', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '22222222-2222-2222-2222-222222222222', 'editor', 'accepted', '11111111-1111-1111-1111-111111111111', NOW() - interval '90 days')
ON CONFLICT (account_id, user_id) DO UPDATE SET
  role = EXCLUDED.role,
  status = EXCLUDED.status,
  joined_at = EXCLUDED.joined_at;

-- ============================================================
-- Seed: taxonomy
-- ============================================================
INSERT INTO countries (code, name, flag_emoji, channels_count)
VALUES
  ('US', 'United States', '🇺🇸', 6),
  ('GB', 'United Kingdom', '🇬🇧', 2),
  ('AE', 'United Arab Emirates', '🇦🇪', 1),
  ('SG', 'Singapore', '🇸🇬', 1)
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name,
  flag_emoji = EXCLUDED.flag_emoji,
  channels_count = EXCLUDED.channels_count,
  updated_at = NOW();

INSERT INTO categories (slug, name, description, icon, channels_count)
VALUES
  ('technology', 'Technology', 'Tech channels and innovation news', 'cpu', 12000),
  ('cryptocurrency', 'Cryptocurrency', 'Crypto trading and blockchain channels', 'coins', 9800),
  ('marketing', 'Marketing', 'Digital marketing and growth channels', 'megaphone', 5400),
  ('news', 'News', 'Global and local news channels', 'newspaper', 6400),
  ('gaming', 'Gaming', 'Gaming and esports channels', 'gamepad-2', 7000),
  ('finance', 'Finance', 'Personal finance and investing channels', 'landmark', 4100),
  ('education', 'Education', 'Learning and educational channels', 'graduation-cap', 2800),
  ('e-commerce', 'E-commerce', 'Ecommerce and marketplace channels', 'shopping-bag', 1800)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  icon = EXCLUDED.icon,
  channels_count = EXCLUDED.channels_count,
  updated_at = NOW();

INSERT INTO industries (slug, name, description)
VALUES
  ('crypto', 'Crypto', 'Cryptocurrency and blockchain companies'),
  ('tech', 'Tech', 'Technology companies and products'),
  ('gaming', 'Gaming', 'Gaming and betting advertisers'),
  ('ecommerce', 'E-commerce', 'Online retail and marketplace advertisers'),
  ('finance', 'Finance', 'Financial products and services')
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  updated_at = NOW();

INSERT INTO tags (slug, name, usage_count)
VALUES
  ('ai', 'AI', 38),
  ('technology', 'Technology', 42),
  ('crypto', 'Crypto', 24),
  ('news', 'News', 19),
  ('startup', 'Startup', 15),
  ('mobile', 'Mobile', 12)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  usage_count = EXCLUDED.usage_count,
  updated_at = NOW();

INSERT INTO mini_app_categories (slug, name, description, apps_count)
VALUES
  ('games', 'Games', 'Play-to-earn and casual games', 1820),
  ('finance', 'Finance', 'Wallets and payment apps', 640),
  ('shopping', 'Shopping', 'Marketplaces and commerce bots', 520),
  ('productivity', 'Productivity', 'Task and workflow apps', 410),
  ('entertainment', 'Entertainment', 'Media and streaming apps', 560),
  ('social', 'Social', 'Community and chat mini apps', 462)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  apps_count = EXCLUDED.apps_count,
  updated_at = NOW();

-- ============================================================
-- Seed: channels + related analytics
-- ============================================================
INSERT INTO channels (
  telegram_channel_id, name, username, avatar_url, description, country_code, primary_category_id,
  status, subscribers_current, avg_views_current, engagement_rate_current, posts_per_day_current,
  last_post_at, last_crawled_at
)
VALUES
  (100001, 'Tech News Daily', 'technewsdaily', 'https://cdn.example.com/ch/tn.png', 'Your daily source for the latest technology news, AI breakthroughs, and digital innovation.', 'US', (SELECT id FROM categories WHERE slug = 'technology'), 'verified', 5430000, 1780000, 3.20, 4.20, NOW() - interval '2 hours', NOW() - interval '15 minutes'),
  (100002, 'Crypto Insights', 'cryptoinsights', 'https://cdn.example.com/ch/ci.png', 'Market insights, charts, and blockchain ecosystem analysis.', 'US', (SELECT id FROM categories WHERE slug = 'cryptocurrency'), 'verified', 1800000, 910000, 6.20, 3.10, NOW() - interval '4 hours', NOW() - interval '15 minutes'),
  (100003, 'News Breaking', 'newsbreaking', 'https://cdn.example.com/ch/nb.png', 'Breaking stories from tech, global politics, and economy.', 'US', (SELECT id FROM categories WHERE slug = 'news'), 'verified', 1500000, 640000, 7.10, 5.00, NOW() - interval '1 hour', NOW() - interval '15 minutes'),
  (100004, 'Gaming Universe', 'gaminguniverse', 'https://cdn.example.com/ch/gu.png', 'Gaming updates, esports highlights, and release schedules.', 'US', (SELECT id FROM categories WHERE slug = 'gaming'), 'verified', 1200000, 520000, 5.50, 3.80, NOW() - interval '3 hours', NOW() - interval '20 minutes'),
  (100005, 'Marketing Pro', 'marketingpro', 'https://cdn.example.com/ch/mp.png', 'Performance marketing tactics and growth experiments.', 'US', (SELECT id FROM categories WHERE slug = 'marketing'), 'normal', 980000, 320000, 3.90, 2.90, NOW() - interval '6 hours', NOW() - interval '30 minutes'),
  (100006, 'Easy Money Tips', 'easymoneytips', 'https://cdn.example.com/ch/em.png', 'Unverified promises and high-risk schemes.', 'US', (SELECT id FROM categories WHERE slug = 'finance'), 'scam', 120000, 100000, 1.20, 8.10, NOW() - interval '5 hours', NOW() - interval '30 minutes')
ON CONFLICT (telegram_channel_id) DO UPDATE SET
  name = EXCLUDED.name,
  username = EXCLUDED.username,
  avatar_url = EXCLUDED.avatar_url,
  description = EXCLUDED.description,
  country_code = EXCLUDED.country_code,
  primary_category_id = EXCLUDED.primary_category_id,
  status = EXCLUDED.status,
  subscribers_current = EXCLUDED.subscribers_current,
  avg_views_current = EXCLUDED.avg_views_current,
  engagement_rate_current = EXCLUDED.engagement_rate_current,
  posts_per_day_current = EXCLUDED.posts_per_day_current,
  last_post_at = EXCLUDED.last_post_at,
  last_crawled_at = EXCLUDED.last_crawled_at,
  updated_at = NOW();

INSERT INTO channel_categories (channel_id, category_id, is_primary)
SELECT c.id, c.primary_category_id, true
FROM channels c
WHERE c.telegram_channel_id BETWEEN 100001 AND 100006
ON CONFLICT (channel_id, category_id) DO UPDATE SET is_primary = EXCLUDED.is_primary;

INSERT INTO channel_tags (channel_id, tag_id, relevance_score)
VALUES
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), (SELECT id FROM tags WHERE slug = 'technology'), 92.5),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), (SELECT id FROM tags WHERE slug = 'ai'), 86.0),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), (SELECT id FROM tags WHERE slug = 'news'), 77.0),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100002), (SELECT id FROM tags WHERE slug = 'crypto'), 94.0),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100003), (SELECT id FROM tags WHERE slug = 'news'), 95.0),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100004), (SELECT id FROM tags WHERE slug = 'startup'), 43.0)
ON CONFLICT (channel_id, tag_id) DO UPDATE SET relevance_score = EXCLUDED.relevance_score;

INSERT INTO channel_about (channel_id, about_text, website_url, contact_links, language_code)
VALUES
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), 'Trusted by 1M+ readers. Daily summaries and explainers.', 'https://technewsdaily.example', '{"x":"https://x.com/technewsdaily","youtube":"https://youtube.com/@technewsdaily"}', 'en'),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100002), 'Crypto market updates with daily chart reviews.', 'https://cryptoinsights.example', '{"x":"https://x.com/cryptoinsights"}', 'en')
ON CONFLICT (channel_id) DO UPDATE SET
  about_text = EXCLUDED.about_text,
  website_url = EXCLUDED.website_url,
  contact_links = EXCLUDED.contact_links,
  language_code = EXCLUDED.language_code,
  updated_at = NOW();

INSERT INTO channel_metrics_daily (
  channel_id, metric_date, subscribers, avg_views, engagement_rate, growth_24h, growth_7d, growth_30d, posts_per_day
)
SELECT
  c.id,
  d::date,
  GREATEST(c.subscribers_current - (30 - gs.i) * (1200 + (c.telegram_channel_id % 10) * 120), 50000),
  GREATEST(c.avg_views_current - (30 - gs.i) * (350 + (c.telegram_channel_id % 7) * 40), 15000),
  GREATEST(0.8, c.engagement_rate_current + ((gs.i % 5) - 2) * 0.08),
  ((gs.i % 7) - 3) * 0.4,
  CASE c.telegram_channel_id
    WHEN 100001 THEN 8.5
    WHEN 100002 THEN 12.4
    WHEN 100003 THEN 5.1
    WHEN 100004 THEN 9.8
    WHEN 100005 THEN 7.3
    ELSE -2.6
  END,
  CASE c.telegram_channel_id
    WHEN 100001 THEN 24.2
    WHEN 100002 THEN 12.1
    WHEN 100003 THEN 8.3
    WHEN 100004 THEN 15.3
    WHEN 100005 THEN 18.9
    ELSE 120.5
  END,
  c.posts_per_day_current
FROM channels c
CROSS JOIN LATERAL generate_series(CURRENT_DATE - interval '29 days', CURRENT_DATE, interval '1 day') WITH ORDINALITY AS gs(d, i)
WHERE c.telegram_channel_id BETWEEN 100001 AND 100006
ON CONFLICT (channel_id, metric_date) DO UPDATE SET
  subscribers = EXCLUDED.subscribers,
  avg_views = EXCLUDED.avg_views,
  engagement_rate = EXCLUDED.engagement_rate,
  growth_24h = EXCLUDED.growth_24h,
  growth_7d = EXCLUDED.growth_7d,
  growth_30d = EXCLUDED.growth_30d,
  posts_per_day = EXCLUDED.posts_per_day;

INSERT INTO channel_inout_daily (channel_id, metric_date, incoming_subscribers, outgoing_subscribers)
SELECT
  c.id,
  d::date,
  300 + (gs.i * 11) + (c.telegram_channel_id % 100),
  120 + (gs.i * 5) + (c.telegram_channel_id % 50)
FROM channels c
CROSS JOIN LATERAL generate_series(CURRENT_DATE - interval '29 days', CURRENT_DATE, interval '1 day') WITH ORDINALITY AS gs(d, i)
WHERE c.telegram_channel_id = 100001
ON CONFLICT (channel_id, metric_date) DO UPDATE SET
  incoming_subscribers = EXCLUDED.incoming_subscribers,
  outgoing_subscribers = EXCLUDED.outgoing_subscribers;

INSERT INTO channel_similarities (channel_id, similar_channel_id, similarity_score, reason)
VALUES
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), (SELECT id FROM channels WHERE telegram_channel_id = 100002), 0.8200, 'Overlapping AI and crypto coverage'),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), (SELECT id FROM channels WHERE telegram_channel_id = 100004), 0.6100, 'Shared startup and product launch audience'),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), (SELECT id FROM channels WHERE telegram_channel_id = 100005), 0.7000, 'Marketing + technology content overlap')
ON CONFLICT (channel_id, similar_channel_id) DO UPDATE SET
  similarity_score = EXCLUDED.similarity_score,
  reason = EXCLUDED.reason,
  updated_at = NOW();

INSERT INTO account_channels (account_id, channel_id, monitoring_enabled, is_favorite, created_by, updated_by)
SELECT
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  c.id,
  true,
  (c.telegram_channel_id IN (100001, 100002)),
  '11111111-1111-1111-1111-111111111111',
  '11111111-1111-1111-1111-111111111111'
FROM channels c
WHERE c.telegram_channel_id BETWEEN 100001 AND 100006
ON CONFLICT (account_id, channel_id) DO UPDATE SET
  monitoring_enabled = EXCLUDED.monitoring_enabled,
  is_favorite = EXCLUDED.is_favorite,
  updated_by = EXCLUDED.updated_by,
  updated_at = NOW();

INSERT INTO member_channel_access (account_id, team_member_id, channel_id, access_level, created_by)
SELECT
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  tm.id,
  c.id,
  CASE WHEN tm.user_id = '11111111-1111-1111-1111-111111111111' THEN 'admin'::user_role ELSE 'viewer'::user_role END,
  '11111111-1111-1111-1111-111111111111'
FROM team_members tm
JOIN channels c ON c.telegram_channel_id BETWEEN 100001 AND 100006
WHERE tm.account_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
ON CONFLICT (account_id, team_member_id, channel_id) DO UPDATE SET
  access_level = EXCLUDED.access_level;

-- ============================================================
-- Seed: posts
-- ============================================================
INSERT INTO posts (
  channel_id, telegram_message_id, external_post_url, title, content_text, media_type, published_at,
  views_count, reactions_count, comments_count, forwards_count, is_deleted
)
VALUES
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), 9001, 'https://t.me/technewsdaily/9001', 'Breaking: New AI model released', 'New AI model released with unprecedented capabilities.', 'text', NOW() - interval '2 hours', 125000, 4200, 640, 1800, false),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), 9002, 'https://t.me/technewsdaily/9002', 'Tip of the day', 'How to optimize your workflow with five simple tools.', 'text', NOW() - interval '5 hours', 89000, 2100, 220, 920, false),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100001), 9003, 'https://t.me/technewsdaily/9003', 'Weekly market analysis', 'What to expect in the tech sector this week.', 'document', NOW() - interval '1 day', 67000, 1500, 180, 450, true),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100002), 9101, 'https://t.me/cryptoinsights/9101', 'BTC funding rates', 'Funding rates cooled as open interest rises.', 'image', NOW() - interval '3 hours', 74000, 2600, 300, 760, false),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100003), 9201, 'https://t.me/newsbreaking/9201', 'Global markets update', 'Markets react to inflation data release.', 'text', NOW() - interval '1 hour', 98000, 1700, 520, 870, false),
  ((SELECT id FROM channels WHERE telegram_channel_id = 100004), 9301, 'https://t.me/gaminguniverse/9301', 'New tournament announced', 'International tournament prize pool reaches $2M.', 'video', NOW() - interval '6 hours', 56000, 1900, 410, 600, false)
ON CONFLICT (channel_id, telegram_message_id) DO UPDATE SET
  title = EXCLUDED.title,
  content_text = EXCLUDED.content_text,
  media_type = EXCLUDED.media_type,
  published_at = EXCLUDED.published_at,
  views_count = EXCLUDED.views_count,
  reactions_count = EXCLUDED.reactions_count,
  comments_count = EXCLUDED.comments_count,
  forwards_count = EXCLUDED.forwards_count,
  is_deleted = EXCLUDED.is_deleted,
  updated_at = NOW();

INSERT INTO post_metrics_daily (post_id, metric_date, views_count, reactions_count, comments_count, forwards_count, engagement_rate)
SELECT
  p.id,
  d::date,
  GREATEST(p.views_count - (7 - gs.i) * 1200, 1000),
  GREATEST(p.reactions_count - (7 - gs.i) * 50, 10),
  GREATEST(p.comments_count - (7 - gs.i) * 10, 2),
  GREATEST(p.forwards_count - (7 - gs.i) * 20, 3),
  LEAST(100, ROUND(((p.reactions_count + p.comments_count + p.forwards_count)::numeric / NULLIF(p.views_count, 0)) * 100, 2))
FROM posts p
CROSS JOIN LATERAL generate_series(CURRENT_DATE - interval '6 days', CURRENT_DATE, interval '1 day') WITH ORDINALITY AS gs(d, i)
WHERE p.telegram_message_id IN (9001, 9002, 9101, 9201, 9301)
ON CONFLICT (post_id, metric_date) DO UPDATE SET
  views_count = EXCLUDED.views_count,
  reactions_count = EXCLUDED.reactions_count,
  comments_count = EXCLUDED.comments_count,
  forwards_count = EXCLUDED.forwards_count,
  engagement_rate = EXCLUDED.engagement_rate;

INSERT INTO post_reaction_breakdown (post_id, reaction_code, reaction_count)
VALUES
  ((SELECT id FROM posts WHERE telegram_message_id = 9001 AND channel_id = (SELECT id FROM channels WHERE telegram_channel_id = 100001)), '👍', 2800),
  ((SELECT id FROM posts WHERE telegram_message_id = 9001 AND channel_id = (SELECT id FROM channels WHERE telegram_channel_id = 100001)), '🔥', 900),
  ((SELECT id FROM posts WHERE telegram_message_id = 9001 AND channel_id = (SELECT id FROM channels WHERE telegram_channel_id = 100001)), '🚀', 500),
  ((SELECT id FROM posts WHERE telegram_message_id = 9101 AND channel_id = (SELECT id FROM channels WHERE telegram_channel_id = 100002)), '📈', 1200),
  ((SELECT id FROM posts WHERE telegram_message_id = 9101 AND channel_id = (SELECT id FROM channels WHERE telegram_channel_id = 100002)), '💎', 880)
ON CONFLICT (post_id, reaction_code) DO UPDATE SET
  reaction_count = EXCLUDED.reaction_count;

-- ============================================================
-- Seed: advertisers + ads
-- ============================================================
INSERT INTO advertisers (
  name, slug, industry_id, logo_url, website_url, description,
  active_creatives_count, estimated_spend_current, avg_engagement_rate_current,
  total_ads_current, channels_used_current, trend_30d
)
VALUES
  ('Binance', 'binance', (SELECT id FROM industries WHERE slug = 'crypto'), 'https://cdn.example.com/adv/binance.png', 'https://www.binance.com', 'Global crypto exchange and ecosystem products.', 156, 2500000, 4.20, 4500, 1200, 15.30),
  ('Telegram Premium', 'telegram-premium', (SELECT id FROM industries WHERE slug = 'tech'), 'https://cdn.example.com/adv/tgpremium.png', 'https://telegram.org', 'Premium subscription and Telegram features.', 89, 1800000, 5.80, 3900, 2100, 22.10),
  ('1xBet', '1xbet', (SELECT id FROM industries WHERE slug = 'gaming'), 'https://cdn.example.com/adv/1xbet.png', 'https://1xbet.example', 'Gaming and betting promotions.', 234, 1500000, 3.10, 3200, 890, -5.20),
  ('Bybit', 'bybit', (SELECT id FROM industries WHERE slug = 'crypto'), 'https://cdn.example.com/adv/bybit.png', 'https://www.bybit.com', 'Crypto trading platform and campaigns.', 112, 1200000, 3.90, 3000, 756, 8.70),
  ('Temu', 'temu', (SELECT id FROM industries WHERE slug = 'ecommerce'), 'https://cdn.example.com/adv/temu.png', 'https://www.temu.com', 'Marketplace campaigns and seasonal offers.', 345, 980000, 2.80, 2600, 1600, 45.60)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  industry_id = EXCLUDED.industry_id,
  logo_url = EXCLUDED.logo_url,
  website_url = EXCLUDED.website_url,
  description = EXCLUDED.description,
  active_creatives_count = EXCLUDED.active_creatives_count,
  estimated_spend_current = EXCLUDED.estimated_spend_current,
  avg_engagement_rate_current = EXCLUDED.avg_engagement_rate_current,
  total_ads_current = EXCLUDED.total_ads_current,
  channels_used_current = EXCLUDED.channels_used_current,
  trend_30d = EXCLUDED.trend_30d,
  updated_at = NOW();

INSERT INTO ad_campaigns (advertiser_id, name, objective, status, budget, currency, start_date, end_date)
VALUES
  ((SELECT id FROM advertisers WHERE slug = 'binance'), 'Binance Q1 Growth Push', 'Acquisition', 'active', 650000, 'USD', CURRENT_DATE - 45, CURRENT_DATE + 25),
  ((SELECT id FROM advertisers WHERE slug = 'telegram-premium'), 'Premium Feature Awareness', 'Awareness', 'active', 520000, 'USD', CURRENT_DATE - 35, CURRENT_DATE + 40),
  ((SELECT id FROM advertisers WHERE slug = '1xbet'), 'Sports Event Blitz', 'Conversion', 'active', 480000, 'USD', CURRENT_DATE - 20, CURRENT_DATE + 15),
  ((SELECT id FROM advertisers WHERE slug = 'bybit'), 'Bybit Trading Challenge', 'Acquisition', 'active', 410000, 'USD', CURRENT_DATE - 30, CURRENT_DATE + 20),
  ((SELECT id FROM advertisers WHERE slug = 'temu'), 'Temu Seasonal Sale', 'Conversion', 'active', 350000, 'USD', CURRENT_DATE - 15, CURRENT_DATE + 30)
ON CONFLICT DO NOTHING;

INSERT INTO ad_creatives (
  campaign_id, advertiser_id, source_channel_id, preview_text, headline, body_text, ad_type,
  media_type, media_url, destination_url, cta_text, category_id, language_code, posted_at, last_seen_at, is_active
)
SELECT
  ac.id,
  ac.advertiser_id,
  (SELECT id FROM channels WHERE telegram_channel_id = 100002),
  'Trade smarter with advanced insights.',
  'Join Binance Today',
  'Lower fees, deeper liquidity, and pro tools for active traders.',
  'sponsored',
  'image',
  'https://cdn.example.com/ads/binance-01.png',
  'https://binance.example/campaign-a',
  'Start Trading',
  (SELECT id FROM categories WHERE slug = 'cryptocurrency'),
  'en',
  NOW() - interval '7 days',
  NOW() - interval '30 minutes',
  true
FROM ad_campaigns ac
WHERE ac.name = 'Binance Q1 Growth Push'
AND NOT EXISTS (
  SELECT 1
  FROM ad_creatives x
  WHERE x.advertiser_id = ac.advertiser_id
    AND x.headline = 'Join Binance Today'
);

INSERT INTO ad_creatives (
  campaign_id, advertiser_id, source_channel_id, preview_text, headline, body_text, ad_type,
  media_type, media_url, destination_url, cta_text, category_id, language_code, posted_at, last_seen_at, is_active
)
SELECT
  ac.id,
  ac.advertiser_id,
  (SELECT id FROM channels WHERE telegram_channel_id = 100001),
  'Unlock more power on Telegram.',
  'Go Premium',
  'Faster downloads, larger uploads, and exclusive features.',
  'native',
  'image',
  'https://cdn.example.com/ads/premium-01.png',
  'https://telegram.org/premium',
  'Upgrade',
  (SELECT id FROM categories WHERE slug = 'technology'),
  'en',
  NOW() - interval '5 days',
  NOW() - interval '20 minutes',
  true
FROM ad_campaigns ac
WHERE ac.name = 'Premium Feature Awareness'
AND NOT EXISTS (
  SELECT 1
  FROM ad_creatives x
  WHERE x.advertiser_id = ac.advertiser_id
    AND x.headline = 'Go Premium'
);

INSERT INTO ad_placements (creative_id, channel_id, placed_at, removed_at, placement_cost, currency, notes)
SELECT * FROM (
  VALUES
    ((SELECT ac.id FROM ad_creatives ac JOIN advertisers a ON a.id = ac.advertiser_id WHERE a.slug = 'binance' ORDER BY ac.created_at ASC LIMIT 1), (SELECT id FROM channels WHERE telegram_channel_id = 100002), NOW() - interval '6 days', NULL::timestamptz, 12500::numeric, 'USD'::char(3), 'Pinned for 24h on premium slot'::text),
    ((SELECT ac.id FROM ad_creatives ac JOIN advertisers a ON a.id = ac.advertiser_id WHERE a.slug = 'telegram-premium' ORDER BY ac.created_at ASC LIMIT 1), (SELECT id FROM channels WHERE telegram_channel_id = 100001), NOW() - interval '4 days', NULL::timestamptz, 14800::numeric, 'USD'::char(3), 'Organic placement and repost'::text)
) AS v(creative_id, channel_id, placed_at, removed_at, placement_cost, currency, notes)
WHERE NOT EXISTS (
  SELECT 1
  FROM ad_placements ap
  WHERE ap.creative_id = v.creative_id
    AND ap.channel_id = v.channel_id
    AND ap.notes = v.notes
);

INSERT INTO ad_metrics_daily (creative_id, metric_date, impressions, clicks, ctr, engagement_rate, spend, conversions)
SELECT
  ac.id,
  d::date,
  40000 + (gs.i * 1200),
  1100 + (gs.i * 42),
  ROUND(((1100 + (gs.i * 42))::numeric / NULLIF((40000 + (gs.i * 1200)), 0)) * 100, 4),
  3.1 + (gs.i % 5) * 0.18,
  2400 + (gs.i * 110),
  65 + (gs.i * 3)
FROM ad_creatives ac
CROSS JOIN LATERAL generate_series(CURRENT_DATE - interval '29 days', CURRENT_DATE, interval '1 day') WITH ORDINALITY AS gs(d, i)
JOIN advertisers a ON a.id = ac.advertiser_id
WHERE a.slug IN ('binance', 'telegram-premium')
ON CONFLICT (creative_id, metric_date) DO UPDATE SET
  impressions = EXCLUDED.impressions,
  clicks = EXCLUDED.clicks,
  ctr = EXCLUDED.ctr,
  engagement_rate = EXCLUDED.engagement_rate,
  spend = EXCLUDED.spend,
  conversions = EXCLUDED.conversions;

INSERT INTO advertiser_metrics_daily (
  advertiser_id, metric_date, estimated_spend, total_ads, active_creatives, channels_used, avg_engagement_rate, trend_percent
)
SELECT
  a.id,
  d::date,
  GREATEST(20000, a.estimated_spend_current - (30 - gs.i) * 2500),
  GREATEST(100, a.total_ads_current - (30 - gs.i) * 8),
  GREATEST(1, a.active_creatives_count - (30 - gs.i) / 2),
  GREATEST(1, a.channels_used_current - (30 - gs.i)),
  GREATEST(0.5, a.avg_engagement_rate_current + ((gs.i % 4) - 1) * 0.07),
  a.trend_30d
FROM advertisers a
CROSS JOIN LATERAL generate_series(CURRENT_DATE - interval '29 days', CURRENT_DATE, interval '1 day') WITH ORDINALITY AS gs(d, i)
WHERE a.slug IN ('binance', 'telegram-premium', '1xbet', 'bybit', 'temu')
ON CONFLICT (advertiser_id, metric_date) DO UPDATE SET
  estimated_spend = EXCLUDED.estimated_spend,
  total_ads = EXCLUDED.total_ads,
  active_creatives = EXCLUDED.active_creatives,
  channels_used = EXCLUDED.channels_used,
  avg_engagement_rate = EXCLUDED.avg_engagement_rate,
  trend_percent = EXCLUDED.trend_percent;

INSERT INTO advertiser_top_channels_daily (advertiser_id, snapshot_date, channel_id, rank, estimated_spend, impressions, engagement_rate)
VALUES
  ((SELECT id FROM advertisers WHERE slug = 'binance'), CURRENT_DATE, (SELECT id FROM channels WHERE telegram_channel_id = 100002), 1, 520000, 8700000, 4.6),
  ((SELECT id FROM advertisers WHERE slug = 'binance'), CURRENT_DATE, (SELECT id FROM channels WHERE telegram_channel_id = 100001), 2, 410000, 6500000, 4.1),
  ((SELECT id FROM advertisers WHERE slug = 'telegram-premium'), CURRENT_DATE, (SELECT id FROM channels WHERE telegram_channel_id = 100001), 1, 480000, 7200000, 5.2),
  ((SELECT id FROM advertisers WHERE slug = 'telegram-premium'), CURRENT_DATE, (SELECT id FROM channels WHERE telegram_channel_id = 100004), 2, 260000, 3900000, 4.8)
ON CONFLICT (advertiser_id, snapshot_date, channel_id) DO UPDATE SET
  rank = EXCLUDED.rank,
  estimated_spend = EXCLUDED.estimated_spend,
  impressions = EXCLUDED.impressions,
  engagement_rate = EXCLUDED.engagement_rate;

-- ============================================================
-- Seed: rankings + collections
-- ============================================================
INSERT INTO ranking_collections (slug, name, description, icon, is_active)
VALUES
  ('top-tech-us', 'Top Tech USA', 'Most relevant US technology channels', 'trophy', true),
  ('crypto-movers', 'Crypto Movers', 'Fastest-growing crypto channels', 'rocket', true)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  icon = EXCLUDED.icon,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

INSERT INTO ranking_collection_channels (collection_id, channel_id, rank, score)
VALUES
  ((SELECT id FROM ranking_collections WHERE slug = 'top-tech-us'), (SELECT id FROM channels WHERE telegram_channel_id = 100001), 1, 98.5),
  ((SELECT id FROM ranking_collections WHERE slug = 'top-tech-us'), (SELECT id FROM channels WHERE telegram_channel_id = 100003), 2, 95.1),
  ((SELECT id FROM ranking_collections WHERE slug = 'top-tech-us'), (SELECT id FROM channels WHERE telegram_channel_id = 100005), 3, 91.0),
  ((SELECT id FROM ranking_collections WHERE slug = 'crypto-movers'), (SELECT id FROM channels WHERE telegram_channel_id = 100002), 1, 97.2)
ON CONFLICT (collection_id, channel_id) DO UPDATE SET
  rank = EXCLUDED.rank,
  score = EXCLUDED.score,
  added_at = NOW();

INSERT INTO channel_rankings_daily (
  snapshot_date, ranking_scope, country_code, category_id, channel_id, rank, score, subscribers, engagement_rate, growth_7d
)
VALUES
  (CURRENT_DATE, 'country', 'US', NULL, (SELECT id FROM channels WHERE telegram_channel_id = 100001), 1, 98.20, 5430000, 3.20, 8.5),
  (CURRENT_DATE, 'country', 'US', NULL, (SELECT id FROM channels WHERE telegram_channel_id = 100002), 2, 96.80, 1800000, 6.20, 12.4),
  (CURRENT_DATE, 'country', 'US', NULL, (SELECT id FROM channels WHERE telegram_channel_id = 100003), 3, 95.40, 1500000, 7.10, 5.1),
  (CURRENT_DATE, 'country', 'US', NULL, (SELECT id FROM channels WHERE telegram_channel_id = 100004), 4, 93.30, 1200000, 5.50, 9.8),
  (CURRENT_DATE, 'country', 'US', NULL, (SELECT id FROM channels WHERE telegram_channel_id = 100005), 5, 91.10, 980000, 3.90, 7.3),

  (CURRENT_DATE, 'category', NULL, (SELECT id FROM categories WHERE slug = 'technology'), (SELECT id FROM channels WHERE telegram_channel_id = 100001), 1, 97.90, 5430000, 3.20, 8.5),
  (CURRENT_DATE, 'category', NULL, (SELECT id FROM categories WHERE slug = 'cryptocurrency'), (SELECT id FROM channels WHERE telegram_channel_id = 100002), 1, 97.10, 1800000, 6.20, 12.4),
  (CURRENT_DATE, 'category', NULL, (SELECT id FROM categories WHERE slug = 'news'), (SELECT id FROM channels WHERE telegram_channel_id = 100003), 1, 96.50, 1500000, 7.10, 5.1),

  (CURRENT_DATE, 'global', NULL, NULL, (SELECT id FROM channels WHERE telegram_channel_id = 100001), 1, 99.00, 5430000, 3.20, 8.5),
  (CURRENT_DATE, 'global', NULL, NULL, (SELECT id FROM channels WHERE telegram_channel_id = 100002), 2, 98.10, 1800000, 6.20, 12.4)
ON CONFLICT DO NOTHING;

INSERT INTO advertiser_rankings_daily (
  snapshot_date, ranking_scope, industry_id, advertiser_id, rank, score, estimated_spend, avg_engagement_rate, trend_30d
)
VALUES
  (CURRENT_DATE, 'global', NULL, (SELECT id FROM advertisers WHERE slug = 'binance'), 1, 97.90, 2500000, 4.20, 15.30),
  (CURRENT_DATE, 'global', NULL, (SELECT id FROM advertisers WHERE slug = 'telegram-premium'), 2, 96.40, 1800000, 5.80, 22.10),
  (CURRENT_DATE, 'global', NULL, (SELECT id FROM advertisers WHERE slug = '1xbet'), 3, 93.80, 1500000, 3.10, -5.20),
  (CURRENT_DATE, 'global', NULL, (SELECT id FROM advertisers WHERE slug = 'bybit'), 4, 92.50, 1200000, 3.90, 8.70),
  (CURRENT_DATE, 'global', NULL, (SELECT id FROM advertisers WHERE slug = 'temu'), 5, 90.90, 980000, 2.80, 45.60),

  (CURRENT_DATE, 'industry', (SELECT id FROM industries WHERE slug = 'crypto'), (SELECT id FROM advertisers WHERE slug = 'binance'), 1, 98.30, 2500000, 4.20, 15.30),
  (CURRENT_DATE, 'industry', (SELECT id FROM industries WHERE slug = 'crypto'), (SELECT id FROM advertisers WHERE slug = 'bybit'), 2, 94.10, 1200000, 3.90, 8.70)
ON CONFLICT DO NOTHING;

-- ============================================================
-- Seed: mini apps
-- ============================================================
INSERT INTO mini_apps (
  telegram_app_id, name, slug, category_id, icon_url, description, rating, launched_at,
  daily_users_current, total_users_current, total_sessions_current, avg_session_seconds,
  growth_weekly, is_verified
)
VALUES
  ('mini_10001', 'Hamster Kombat', 'hamster-kombat', (SELECT id FROM mini_app_categories WHERE slug = 'games'), 'https://cdn.example.com/mini/hamster.png', 'Tap-to-earn crypto game with hamster theme.', 4.8, CURRENT_DATE - 240, 2500000, 45000000, 98000000, 272, 15.2, true),
  ('mini_10002', 'Notcoin', 'notcoin', (SELECT id FROM mini_app_categories WHERE slug = 'games'), 'https://cdn.example.com/mini/notcoin.png', 'Popular tap-to-earn mining game.', 4.6, CURRENT_DATE - 320, 1800000, 35000000, 76000000, 268, 8.5, true),
  ('mini_10003', 'Wallet', 'wallet', (SELECT id FROM mini_app_categories WHERE slug = 'finance'), 'https://cdn.example.com/mini/wallet.png', 'Official Telegram crypto wallet.', 4.9, CURRENT_DATE - 410, 1200000, 28000000, 54000000, 295, 22.3, true),
  ('mini_10004', 'Fragment', 'fragment', (SELECT id FROM mini_app_categories WHERE slug = 'finance'), 'https://cdn.example.com/mini/fragment.png', 'NFT marketplace for usernames and numbers.', 4.7, CURRENT_DATE - 450, 450000, 8500000, 16000000, 260, 12.1, true),
  ('mini_10005', 'Yescoin', 'yescoin', (SELECT id FROM mini_app_categories WHERE slug = 'games'), 'https://cdn.example.com/mini/yescoin.png', 'Swipe-to-earn game with social features.', 4.4, CURRENT_DATE - 140, 950000, 18000000, 32000000, 254, 28.7, false),
  ('mini_10006', 'Major', 'major', (SELECT id FROM mini_app_categories WHERE slug = 'games'), 'https://cdn.example.com/mini/major.png', 'Star collection mini-game.', 4.3, CURRENT_DATE - 100, 680000, 12000000, 21000000, 246, 45.2, false)
ON CONFLICT (telegram_app_id) DO UPDATE SET
  name = EXCLUDED.name,
  slug = EXCLUDED.slug,
  category_id = EXCLUDED.category_id,
  icon_url = EXCLUDED.icon_url,
  description = EXCLUDED.description,
  rating = EXCLUDED.rating,
  launched_at = EXCLUDED.launched_at,
  daily_users_current = EXCLUDED.daily_users_current,
  total_users_current = EXCLUDED.total_users_current,
  total_sessions_current = EXCLUDED.total_sessions_current,
  avg_session_seconds = EXCLUDED.avg_session_seconds,
  growth_weekly = EXCLUDED.growth_weekly,
  is_verified = EXCLUDED.is_verified,
  updated_at = NOW();

INSERT INTO mini_app_metrics_daily (
  mini_app_id, metric_date, daily_users, total_users, sessions, avg_session_seconds, rating, growth_weekly
)
SELECT
  m.id,
  d::date,
  GREATEST(10000, m.daily_users_current - (30 - gs.i) * 1500),
  GREATEST(50000, m.total_users_current - (30 - gs.i) * 2200),
  GREATEST(80000, m.total_sessions_current - (30 - gs.i) * 4000),
  m.avg_session_seconds + ((gs.i % 5) - 2) * 3,
  m.rating,
  m.growth_weekly
FROM mini_apps m
CROSS JOIN LATERAL generate_series(CURRENT_DATE - interval '29 days', CURRENT_DATE, interval '1 day') WITH ORDINALITY AS gs(d, i)
WHERE m.telegram_app_id IN ('mini_10001', 'mini_10002', 'mini_10003', 'mini_10004', 'mini_10005', 'mini_10006')
ON CONFLICT (mini_app_id, metric_date) DO UPDATE SET
  daily_users = EXCLUDED.daily_users,
  total_users = EXCLUDED.total_users,
  sessions = EXCLUDED.sessions,
  avg_session_seconds = EXCLUDED.avg_session_seconds,
  rating = EXCLUDED.rating,
  growth_weekly = EXCLUDED.growth_weekly;

INSERT INTO mini_app_rankings_daily (snapshot_date, category_id, mini_app_id, rank, score, daily_users, growth_7d)
VALUES
  (CURRENT_DATE, (SELECT id FROM mini_app_categories WHERE slug = 'games'), (SELECT id FROM mini_apps WHERE telegram_app_id = 'mini_10001'), 1, 98.2, 2500000, 15.2),
  (CURRENT_DATE, (SELECT id FROM mini_app_categories WHERE slug = 'games'), (SELECT id FROM mini_apps WHERE telegram_app_id = 'mini_10002'), 2, 96.4, 1800000, 8.5),
  (CURRENT_DATE, (SELECT id FROM mini_app_categories WHERE slug = 'finance'), (SELECT id FROM mini_apps WHERE telegram_app_id = 'mini_10003'), 1, 97.5, 1200000, 22.3),
  (CURRENT_DATE, (SELECT id FROM mini_app_categories WHERE slug = 'finance'), (SELECT id FROM mini_apps WHERE telegram_app_id = 'mini_10004'), 2, 93.0, 450000, 12.1),
  (CURRENT_DATE, (SELECT id FROM mini_app_categories WHERE slug = 'games'), (SELECT id FROM mini_apps WHERE telegram_app_id = 'mini_10005'), 3, 92.6, 950000, 28.7),
  (CURRENT_DATE, (SELECT id FROM mini_app_categories WHERE slug = 'games'), (SELECT id FROM mini_apps WHERE telegram_app_id = 'mini_10006'), 4, 90.8, 680000, 45.2)
ON CONFLICT DO NOTHING;

-- ============================================================
-- Seed: tracker + export samples
-- ============================================================
INSERT INTO trackers (
  id, account_id, tracker_type, tracker_value, normalized_value, status,
  mentions_count, last_activity_at, notify_push, notify_telegram, notify_email,
  created_by, updated_by
)
VALUES
  ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'keyword', 'airdrop', 'airdrop', 'active', 3, NOW() - interval '1 hour', true, true, false, '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111'),
  ('cccccccc-cccc-cccc-cccc-cccccccccccc', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'channel', '@technewsdaily', '@technewsdaily', 'active', 2, NOW() - interval '2 hours', true, true, true, '11111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111')
ON CONFLICT (id) DO UPDATE SET
  tracker_value = EXCLUDED.tracker_value,
  normalized_value = EXCLUDED.normalized_value,
  status = EXCLUDED.status,
  mentions_count = EXCLUDED.mentions_count,
  last_activity_at = EXCLUDED.last_activity_at,
  notify_push = EXCLUDED.notify_push,
  notify_telegram = EXCLUDED.notify_telegram,
  notify_email = EXCLUDED.notify_email,
  updated_by = EXCLUDED.updated_by,
  updated_at = NOW();

INSERT INTO tracker_mentions (account_id, tracker_id, channel_id, post_id, mention_text, context_snippet, mentioned_at)
VALUES
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    (SELECT id FROM channels WHERE telegram_channel_id = 100002),
    (SELECT id FROM posts WHERE telegram_message_id = 9101 AND channel_id = (SELECT id FROM channels WHERE telegram_channel_id = 100002)),
    'airdrop',
    'Funding rates cooled as open interest rises before the weekend airdrop announcements.',
    NOW() - interval '3 hours'
  ),
  (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    (SELECT id FROM channels WHERE telegram_channel_id = 100001),
    (SELECT id FROM posts WHERE telegram_message_id = 9001 AND channel_id = (SELECT id FROM channels WHERE telegram_channel_id = 100001)),
    '@technewsdaily',
    'Mention from partner network citing rapid coverage growth this week.',
    NOW() - interval '2 hours'
  )
ON CONFLICT DO NOTHING;

INSERT INTO export_jobs (account_id, export_type, status, filters, file_url, file_size_bytes, created_by, started_at, completed_at, expires_at)
SELECT
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  'channels_csv',
  'completed',
  '{"country":"US","limit":100}'::jsonb,
  'https://cdn.example.com/exports/channels-us-latest.csv',
  182044,
  '11111111-1111-1111-1111-111111111111',
  NOW() - interval '3 days',
  NOW() - interval '3 days' + interval '2 minutes',
  NOW() + interval '27 days'
WHERE NOT EXISTS (
  SELECT 1 FROM export_jobs
  WHERE account_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    AND export_type = 'channels_csv'
    AND created_by = '11111111-1111-1111-1111-111111111111'
);

INSERT INTO export_jobs (account_id, export_type, status, filters, created_by, started_at)
SELECT
  'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  'advertisers_csv',
  'processing',
  '{"industry":"crypto","window":"30d"}'::jsonb,
  '22222222-2222-2222-2222-222222222222',
  NOW() - interval '20 minutes'
WHERE NOT EXISTS (
  SELECT 1 FROM export_jobs
  WHERE account_id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    AND export_type = 'advertisers_csv'
    AND status = 'processing'
    AND created_by = '22222222-2222-2222-2222-222222222222'
);

COMMIT;
