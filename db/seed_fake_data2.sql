BEGIN;

SET search_path = public;

-- ============================================================
-- Seed extension: countries (excludes countries already in seed_fake_data.sql)
-- Existing in seed_fake_data.sql: US, GB, AE, SG
-- ============================================================
INSERT INTO countries (code, name, flag_emoji, channels_count)
VALUES
  ('AF', 'Afghanistan', '🇦🇫', 10),
  ('DZ', 'Algeria', '🇩🇿', 8),
  ('AR', 'Argentina', '🇦🇷', 2000),
  ('AM', 'Armenia', '🇦🇲', 3600),
  ('AU', 'Australia', '🇦🇺', 7),
  ('AT', 'Austria', '🇦🇹', 89),
  ('AZ', 'Azerbaijan', '🇦🇿', 3600),
  ('BD', 'Bangladesh', '🇧🇩', 25700),
  ('BY', 'Belarus', '🇧🇾', 4400),
  ('BO', 'Bolivia', '🇧🇴', 61),
  ('BR', 'Brazil', '🇧🇷', 35600),
  ('BG', 'Bulgaria', '🇧🇬', 26),
  ('KH', 'Cambodia', '🇰🇭', 8700),
  ('CM', 'Cameroon', '🇨🇲', 437),
  ('CA', 'Canada', '🇨🇦', 9),
  ('CL', 'Chile', '🇨🇱', 372),
  ('CN', 'China', '🇨🇳', 179100),
  ('CO', 'Colombia', '🇨🇴', 2100),
  ('CR', 'Costa Rica', '🇨🇷', 58),
  ('CZ', 'Czech Republic', '🇨🇿', 657),
  ('EC', 'Ecuador', '🇪🇨', 706),
  ('EG', 'Egypt', '🇪🇬', 18700),
  ('EE', 'Estonia', '🇪🇪', 5),
  ('ET', 'Ethiopia', '🇪🇹', 20700),
  ('FI', 'Finland', '🇫🇮', 1900),
  ('FR', 'France', '🇫🇷', 19600),
  ('GE', 'Georgia', '🇬🇪', 1200),
  ('DE', 'Germany', '🇩🇪', 9400),
  ('GR', 'Greece', '🇬🇷', 385),
  ('GT', 'Guatemala', '🇬🇹', 61),
  ('HT', 'Haiti', '🇭🇹', 9),
  ('IN', 'India', '🇮🇳', 235500),
  ('ID', 'Indonesia', '🇮🇩', 50000),
  ('IR', 'Iran', '🇮🇷', 271000),
  ('IQ', 'Iraq', '🇮🇶', 127100),
  ('IL', 'Israel', '🇮🇱', 3600),
  ('IT', 'Italy', '🇮🇹', 16400),
  ('JP', 'Japan', '🇯🇵', 4900),
  ('JO', 'Jordan', '🇯🇴', 4),
  ('KZ', 'Kazakhstan', '🇰🇿', 7200),
  ('KE', 'Kenya', '🇰🇪', 13),
  ('KR', 'Korea', '🇰🇷', 5600),
  ('KG', 'Kyrgyzstan', '🇰🇬', 2700),
  ('LV', 'Latvia', '🇱🇻', 221),
  ('LB', 'Lebanon', '🇱🇧', 4),
  ('LY', 'Libya', '🇱🇾', 6),
  ('LT', 'Lithuania', '🇱🇹', 199),
  ('MY', 'Malaysia', '🇲🇾', 26500),
  ('MX', 'Mexico', '🇲🇽', 3700),
  ('MD', 'Moldova', '🇲🇩', 889),
  ('MN', 'Mongolia', '🇲🇳', 3),
  ('MA', 'Morocco', '🇲🇦', 5),
  ('MM', 'Myanmar', '🇲🇲', 49100),
  ('NL', 'Netherlands', '🇳🇱', 828),
  ('NG', 'Nigeria', '🇳🇬', 6500),
  ('OM', 'Oman', '🇴🇲', 2),
  ('PK', 'Pakistan', '🇵🇰', 14),
  ('PS', 'Palestine', '🇵🇸', 4),
  ('PA', 'Panama', '🇵🇦', 20),
  ('PY', 'Paraguay', '🇵🇾', 54),
  ('PE', 'Peru', '🇵🇪', 1600),
  ('PH', 'Philippines', '🇵🇭', 4600),
  ('PL', 'Poland', '🇵🇱', 2900),
  ('PT', 'Portugal', '🇵🇹', 1500),
  ('PR', 'Puerto Rico', '🇵🇷', 28),
  ('RO', 'Romania', '🇷🇴', 817),
  ('RU', 'Russia', '🇷🇺', 856200),
  ('SA', 'Saudi Arabia', '🇸🇦', 66400)
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name,
  flag_emoji = EXCLUDED.flag_emoji,
  channels_count = EXCLUDED.channels_count,
  updated_at = NOW();

-- ============================================================
-- Seed extension: categories (adds new slugs only)
-- Existing in seed_fake_data.sql: technology, cryptocurrency, marketing,
-- news, gaming, finance, education, e-commerce
-- ============================================================
INSERT INTO categories (slug, name, description, icon, channels_count)
VALUES
  ('art-design', 'Art & Design', 'Art, illustration, and design focused channels', 'palette', 62800),
  ('beauty', 'Beauty', 'Beauty tips, makeup, and skincare channels', 'sparkles', 65200),
  ('betting-casino', 'Betting and Casino', 'Sports betting and casino related channels', 'dice-5', 145500),
  ('blogs', 'Blogs', 'Personal and niche blogging channels', 'file-text', 127500),
  ('books', 'Books', 'Book clubs, reading, and literature channels', 'book-open', 35300),
  ('business', 'Business', 'Business strategy and entrepreneurship channels', 'briefcase-business', 80800),
  ('career', 'Career', 'Jobs, hiring, and career development channels', 'users', 18400),
  ('economy-and-finance', 'Economy & Finance', 'Macroeconomics and financial market channels', 'landmark', 76800),
  ('facts', 'Facts', 'Fact-based educational and trivia channels', 'clipboard-list', 8900),
  ('family-and-children', 'Family & Children', 'Parenting and children focused channels', 'baby', 20000),
  ('food-and-drinks', 'Food & Drinks', 'Cooking, recipes, and food channels', 'utensils-crossed', 27500),
  ('healthy-lifestyle', 'Healthy Lifestyle', 'Wellness and healthy living channels', 'heart', 28400),
  ('home-and-architecture', 'Home & Architecture', 'Interior design and architecture channels', 'house', 13900),
  ('humor-and-entertainment', 'Humor & Entertainment', 'Comedy and entertainment channels', 'smile', 47600),
  ('law', 'Law', 'Legal news and law education channels', 'scale', 8100),
  ('linguistics', 'Linguistics', 'Language, grammar, and linguistics channels', 'languages', 7400),
  ('medicine', 'Medicine', 'Medical education and healthcare channels', 'stethoscope', 29400),
  ('motivation-and-quotes', 'Motivation & Quotes', 'Motivational and inspirational channels', 'quote', 29300),
  ('movies', 'Movies', 'Cinema and film related channels', 'film', 124600),
  ('music', 'Music', 'Music discovery and artist channels', 'music', 85600),
  ('nature-and-animals', 'Nature & Animals', 'Wildlife and nature themed channels', 'leaf', 21000),
  ('news-and-media', 'News & Media', 'Media publishers and news digest channels', 'newspaper', 72500),
  ('other', 'Other', 'Miscellaneous channels outside main groups', 'box', 31),
  ('pictures', 'Pictures', 'Photography and image sharing channels', 'image', 10800),
  ('politics', 'Politics', 'Political analysis and civic channels', 'vote', 36100),
  ('psychology', 'Psychology', 'Psychology and mental health channels', 'brain', 35200),
  ('real-estate', 'Real Estate', 'Property and real estate channels', 'building-2', 20200),
  ('religion-and-spirituality', 'Religion & Spirituality', 'Faith and spirituality channels', 'landmark', 138000),
  ('sales', 'Sales', 'Sales tactics and commercial channels', 'shopping-cart', 53600),
  ('social-networks', 'Social Networks', 'Social platform growth and trends channels', 'share-2', 16100),
  ('sports', 'Sports', 'Sports updates and fan communities', 'trophy', 42900),
  ('telegram', 'Telegram', 'Telegram tips, updates, and ecosystem channels', 'send', 2800),
  ('transport', 'Transport', 'Mobility and transport channels', 'bus', 28700),
  ('travel', 'Travel', 'Travel guides and trip planning channels', 'plane', 24100)
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  icon = EXCLUDED.icon,
  channels_count = EXCLUDED.channels_count,
  updated_at = NOW();

-- ============================================================
-- Seed extension: advertisers (adds new slugs only)
-- Existing in seed_fake_data.sql: binance, telegram-premium, 1xbet, bybit, temu
-- ============================================================
INSERT INTO advertisers (
  name, slug, industry_id, logo_url, website_url, description,
  active_creatives_count, estimated_spend_current, avg_engagement_rate_current,
  total_ads_current, channels_used_current, trend_30d
)
VALUES
  ('OKX', 'okx', (SELECT id FROM industries WHERE slug = 'crypto'), 'https://cdn.example.com/adv/okx.png', 'https://www.okx.com', 'Crypto exchange campaigns and ecosystem promotions.', 78, 850000, 4.10, 2200, 620, 12.40),
  ('AliExpress', 'aliexpress', (SELECT id FROM industries WHERE slug = 'ecommerce'), 'https://cdn.example.com/adv/aliexpress.png', 'https://www.aliexpress.com', 'E-commerce marketplace deals and seasonal campaigns.', 198, 720000, 2.50, 1900, 1100, -2.80),
  ('Stake', 'stake', (SELECT id FROM industries WHERE slug = 'gaming'), 'https://cdn.example.com/adv/stake.png', 'https://stake.example', 'Gaming and betting promotions focused on global audiences.', 167, 680000, 3.40, 1800, 445, 18.90)
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

COMMIT;
