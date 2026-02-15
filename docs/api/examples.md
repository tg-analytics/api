# Telegram Pulse API Examples

This document provides request/response examples for all `/v1.0` endpoints in `/Users/mac/Documents/EP/tganalytics/telegram-pulse/docs/api/openapi.yaml`.

## Conventions

Base URL:

```bash
export API_BASE="https://api.telegrampulse.example.com"
```

Auth + account headers:

```bash
export TOKEN="<custom_jwt>"
export ACCOUNT_ID="11111111-1111-1111-1111-111111111111"
```

Standard response envelope:

```json
{
  "data": {},
  "page": { "next_cursor": null, "has_more": false },
  "meta": {}
}
```

Standard error envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [{ "field": "q", "issue": "q must be <= 100 chars" }]
  }
}
```

---

## Auth

### POST `/v1.0/signin` (request magic link)

```bash
curl -s -X POST "$API_BASE/v1.0/signin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "microsaas.farm@gmail.com"
  }'
```

```json
{
  "token": "b0cfbda7-68a5-4331-a47b-e7de0310a02a",
  "expires_at": "2025-12-25T15:00:00Z"
}
```

### POST `/v1.0/signin/confirm` (confirm magic link)

```bash
curl -s -X POST "$API_BASE/v1.0/signin/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "microsaas.farm@gmail.com",
    "token": "b0cfbda7-68a5-4331-a47b-e7de0310a02a"
  }'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2026-01-15T14:09:53.119669Z",
  "user": {
    "id": "af2a103b-1e52-457a-af33-c5b2f9c4e2e3",
    "email": "microsaas.farm@gmail.com",
    "name": "microsaas.farm",
    "role": "USER",
    "status": "ACTIVE",
    "is_guest": false
  }
}
```

### POST `/v1.0/signin/google` (Google SSO)

```bash
curl -s -X POST "$API_BASE/v1.0/signin/google" \
  -H "Content-Type: application/json" \
  -d "{\"id_token\":\"<google_id_token>\",\"account_id\":\"$ACCOUNT_ID\"}"
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2026-01-15T14:09:53.119669Z",
  "account_id": "11111111-1111-1111-1111-111111111111",
  "user": {
    "id": "af2a103b-1e52-457a-af33-c5b2f9c4e2e3",
    "email": "microsaas.farm@gmail.com",
    "name": "microsaas.farm",
    "role": "USER",
    "status": "ACTIVE",
    "is_guest": false
  }
}
```

### Auth Error Responses

Invalid token:

```json
{ "detail": "Invalid or expired token" }
```

Token mismatch:

```json
{ "detail": "Token does not match the provided email" }
```

Token already used:

```json
{ "detail": "Token has already been used" }
```

Expired token:

```json
{ "detail": "Token has expired" }
```

---

## Home

### GET `/v1.0/home/metrics`

```bash
curl -s "$API_BASE/v1.0/home/metrics" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": {
    "channels_indexed": 11000000,
    "posts_analyzed": 72000000000,
    "ad_creatives": 88000000,
    "mini_apps": 4412
  },
  "meta": { "generated_at": "2026-02-14T10:00:00Z" }
}
```

### GET `/v1.0/home/categories` (base)

```bash
curl -s "$API_BASE/v1.0/home/categories?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/home/categories` (paginated)

```bash
curl -s "$API_BASE/v1.0/home/categories?limit=5&cursor=eyJvZmZzZXQiOjV9" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/home/countries` (base)

```bash
curl -s "$API_BASE/v1.0/home/countries?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/home/countries` (paginated)

```bash
curl -s "$API_BASE/v1.0/home/countries?limit=5&cursor=eyJvZmZzZXQiOjV9" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Channels

### GET `/v1.0/channels` (base list)

```bash
curl -s "$API_BASE/v1.0/channels?limit=20&sort_by=subscribers&sort_order=desc" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": [
    {
      "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
      "name": "Tech News Daily",
      "username": "@technewsdaily",
      "subscribers": 1300000,
      "growth_24h": 2.3,
      "growth_7d": 8.5,
      "growth_30d": 24.2,
      "engagement_rate": 4.8,
      "category_slug": "technology",
      "country_code": "US",
      "status": "verified",
      "verified": true,
      "scam": false
    }
  ],
  "page": { "next_cursor": "eyJsYXN0X2lkIjoiOWYy...", "has_more": true },
  "meta": { "total_estimate": 11000000 }
}
```

### GET `/v1.0/channels` (search + filters)

```bash
curl -s "$API_BASE/v1.0/channels?q=crypto&country_code=US&category_slug=cryptocurrencies&size_bucket=large&er_min=3&er_max=10&verified=true&sort_by=growth_7d&sort_order=desc&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}`

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/overview`

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/overview" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": {
    "channel": {
      "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
      "telegram_channel_id": 100001,
      "name": "Tech News Daily",
      "username": "@technewsdaily",
      "avatar_url": "https://cdn.example.com/ch/tn.png",
      "description": "Your daily source for the latest technology news, AI breakthroughs, and digital innovation.",
      "about_text": "Trusted by 1M+ readers. Daily summaries and explainers.",
      "website_url": "https://technewsdaily.example",
      "status": "verified",
      "country_code": "US",
      "category_slug": "technology",
      "category_name": "Technology"
    },
    "kpis": {
      "subscribers": { "value": 5430000, "delta": 156000, "delta_percent": 2.96 },
      "avg_views": { "value": 1780000, "delta": 42000, "delta_percent": 2.42 },
      "engagement_rate": { "value": 3.2, "delta": 0.3, "delta_percent": 10.34 },
      "posts_per_day": { "value": 4.2, "delta": -0.5, "delta_percent": -10.64 }
    },
    "chart": {
      "range": "30d",
      "points": [
        { "date": "2026-01-16", "subscribers": 5274000, "engagement_rate": 2.9 },
        { "date": "2026-02-14", "subscribers": 5430000, "engagement_rate": 3.2 }
      ]
    },
    "similar_channels": [
      { "channel_id": "e7db20e8-a039-4f6f-bf2e-6f3b8ebf2ea0", "name": "Crypto Insights", "username": "@cryptoinsights", "subscribers": 1800000, "similarity_score": 0.82 },
      { "channel_id": "6f5327be-96a8-426e-8496-b3120b7d7f1c", "name": "Gaming Universe", "username": "@gaminguniverse", "subscribers": 1200000, "similarity_score": 0.61 }
    ],
    "tags": [
      { "tag_id": "b89f2d6b-e4e9-4eb8-a44e-27eb93af5cb4", "slug": "technology", "name": "Technology", "relevance_score": 92.5 },
      { "tag_id": "6f7f57f3-1733-4600-b201-ccbef4a744f3", "slug": "ai", "name": "AI", "relevance_score": 86.0 },
      { "tag_id": "9f6fd3d4-70c0-4e17-8aaf-2247bf4ad4f7", "slug": "news", "name": "News", "relevance_score": 77.0 }
    ],
    "recent_posts": [
      {
        "post_id": "3522a9ea-0c50-4eb1-9053-8a7e0b74f4d3",
        "telegram_message_id": 9001,
        "published_at": "2026-02-14T10:00:00Z",
        "title": "Breaking: New AI model released",
        "content_text": "New AI model released with unprecedented capabilities.",
        "views_count": 125000,
        "reactions_count": 4200,
        "comments_count": 640,
        "forwards_count": 1800,
        "external_post_url": "https://t.me/technewsdaily/9001"
      }
    ],
    "inout_30d": { "incoming": 12500, "outgoing": 3200 },
    "incoming_30d": 12500,
    "outgoing_30d": 3200
  },
  "meta": {}
}
```

### GET `/v1.0/channels/{channelId}/metrics` (chart)

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/metrics?metric=subscribers&range=1y" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/metrics` (custom range)

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/metrics?metric=views&from=2025-10-01&to=2026-02-14" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/posts` (base)

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/posts?include_deleted=true&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/posts` (filtered)

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/posts?include_deleted=false&from=2026-02-01T00:00:00Z&to=2026-02-14T23:59:59Z&limit=20&cursor=eyJwdWJsaXNoZWRfYXQiOiIyMDI2LTAyLTEzIn0=" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/similar`

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/similar?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/tags`

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/tags" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/inout`

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/inout?range=30d" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/channels/{channelId}/alerts` (base list)

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/alerts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### GET `/v1.0/channels/{channelId}/alerts` (filtered in client by active)

```bash
curl -s "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/alerts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### POST `/v1.0/channels/{channelId}/alerts` success

```bash
curl -s -X POST "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/alerts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ER Drop Alert",
    "alert_type": "threshold",
    "threshold_value": 2.5,
    "notify_email": true,
    "notify_telegram": true,
    "notify_push": false
  }'
```

```json
{
  "data": {
    "alert_id": "51e5d3b7-8f90-4fe9-a2ef-40ddfca170e1",
    "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
    "name": "ER Drop Alert",
    "alert_type": "threshold",
    "threshold_value": 2.5,
    "is_active": true,
    "notify_email": true,
    "notify_telegram": true,
    "notify_push": false
  },
  "meta": {}
}
```

### POST `/v1.0/channels/{channelId}/alerts` validation error

```bash
curl -s -X POST "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/alerts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bad Threshold","alert_type":"threshold"}'
```

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [{ "field": "threshold_value", "issue": "required for threshold alerts" }]
  }
}
```

### DELETE `/v1.0/channels/{channelId}/alerts/{alertId}` success

```bash
curl -s -X DELETE "$API_BASE/v1.0/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/alerts/51e5d3b7-8f90-4fe9-a2ef-40ddfca170e1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -i
```

### DELETE `/v1.0/channels/{channelId}/alerts/{alertId}` forbidden error

```json
{
  "error": {
    "code": "forbidden",
    "message": "You do not have access to this account resource.",
    "details": []
  }
}
```

---

## Account Channels + Verification

### GET `/v1.0/accounts/{accountId}/channels` (base)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/channels?limit=20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "account_id": "11111111-1111-1111-1111-111111111111",
      "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
      "alias_name": "Primary Tech Channel",
      "monitoring_enabled": true,
      "is_favorite": true,
      "added_at": "2026-02-14T12:00:00Z"
    }
  ],
  "page": { "next_cursor": null, "has_more": false },
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/channels` (paginated)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/channels?limit=20&cursor=eyJsYXN0X2NoYW5uZWxfaWQiOiI5ZjIifQ==" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### POST `/v1.0/accounts/{accountId}/channels` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/channels" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_channel_id":100001,
    "channel_name":"Tech News Daily",
    "alias_name":"Primary Tech Channel",
    "monitoring_enabled":true,
    "is_favorite":true
  }'
```

```json
{
  "data": {
    "account_id": "11111111-1111-1111-1111-111111111111",
    "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
    "alias_name": "Primary Tech Channel",
    "monitoring_enabled": true,
    "is_favorite": true,
    "added_at": "2026-02-14T12:00:00Z"
  },
  "meta": {}
}
```

### POST `/v1.0/accounts/{accountId}/channels` validation error

```json
{
  "error": {
    "code": "validation_error",
    "message": "telegram_channel_id and channel_name are required",
    "details": []
  }
}
```

### GET `/v1.0/accounts/{accountId}/channels/insights`

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/channels/insights" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": {
    "total_subscribers": 259000,
    "total_views": 1200000,
    "avg_engagement_rate": 4.8,
    "channels_count": 3
  },
  "meta": {}
}
```

### POST `/v1.0/accounts/{accountId}/channels/{channelId}/verification` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/verification" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{"verification_method":"description_code"}'
```

```json
{
  "data": {
    "request_id": "2df0f04b-99cb-4d8f-94a2-cbce3a40ab22",
    "account_id": "11111111-1111-1111-1111-111111111111",
    "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
    "verification_code": "TP-7E2A1F9B",
    "verification_method": "description_code",
    "status": "pending",
    "requested_at": "2026-02-14T13:10:00Z",
    "confirmed_at": null,
    "expires_at": "2026-02-21T13:10:00Z"
  },
  "meta": {}
}
```

### POST `/v1.0/accounts/{accountId}/channels/{channelId}/verification` error (pending exists)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Pending verification already exists for this channel.",
    "details": []
  }
}
```

### POST `/v1.0/accounts/{accountId}/channels/{channelId}/verification/{requestId}/confirm` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/channels/9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2/verification/2df0f04b-99cb-4d8f-94a2-cbce3a40ab22/confirm" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{"evidence":{"description_contains_code":true}}'
```

```json
{
  "data": {
    "request_id": "2df0f04b-99cb-4d8f-94a2-cbce3a40ab22",
    "account_id": "11111111-1111-1111-1111-111111111111",
    "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
    "verification_code": "TP-7E2A1F9B",
    "verification_method": "description_code",
    "status": "confirmed",
    "requested_at": "2026-02-14T13:10:00Z",
    "confirmed_at": "2026-02-14T13:20:00Z",
    "expires_at": "2026-02-21T13:10:00Z"
  },
  "meta": {}
}
```

### POST `/v1.0/accounts/{accountId}/channels/{channelId}/verification/{requestId}/confirm` error (expired)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Verification request expired.",
    "details": []
  }
}
```

---

## Ads

### GET `/v1.0/ads` (base list)

```bash
curl -s "$API_BASE/v1.0/ads?limit=20&sort_by=recent&sort_order=desc" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/ads` (search + filters)

```bash
curl -s "$API_BASE/v1.0/ads?q=bootcamp&ad_type=native&category_slug=technology&time_range=7d&sort_by=impressions&sort_order=desc&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/ads/{adId}`

```bash
curl -s "$API_BASE/v1.0/ads/3f07ea5b-1a18-4445-ab6f-4f5d79db54f8" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/ads/summary`

```bash
curl -s "$API_BASE/v1.0/ads/summary?time_range=30d" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Advertisers

### GET `/v1.0/advertisers` (base list)

```bash
curl -s "$API_BASE/v1.0/advertisers?time_period_days=30&sort_by=estimated_spend&sort_order=desc&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/advertisers` (search + filters)

```bash
curl -s "$API_BASE/v1.0/advertisers?q=binance&industry_slug=crypto&time_period_days=30&min_spend=500000&min_channels=100&min_engagement=3&activity_status=active&sort_by=trend&sort_order=desc&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/advertisers/summary`

```bash
curl -s "$API_BASE/v1.0/advertisers/summary?time_period_days=30" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/advertisers/{advertiserId}`

```bash
curl -s "$API_BASE/v1.0/advertisers/2e63db9e-13f7-4204-b8b6-a394f40ca83a" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/advertisers/{advertiserId}/ads` (base)

```bash
curl -s "$API_BASE/v1.0/advertisers/2e63db9e-13f7-4204-b8b6-a394f40ca83a/ads?limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/advertisers/{advertiserId}/ads` (paginated)

```bash
curl -s "$API_BASE/v1.0/advertisers/2e63db9e-13f7-4204-b8b6-a394f40ca83a/ads?limit=20&cursor=eyJhZF9pZCI6IjNmMDcifQ==" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/advertisers/{advertiserId}/channels` (latest)

```bash
curl -s "$API_BASE/v1.0/advertisers/2e63db9e-13f7-4204-b8b6-a394f40ca83a/channels?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### GET `/v1.0/advertisers/{advertiserId}/channels` (snapshot)

```bash
curl -s "$API_BASE/v1.0/advertisers/2e63db9e-13f7-4204-b8b6-a394f40ca83a/channels?snapshot_date=2026-02-01&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rankings

### GET `/v1.0/rankings/countries` (base list)

```bash
curl -s "$API_BASE/v1.0/rankings/countries?country_code=US&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": [
    {
      "rank": 1,
      "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
      "name": "Tech News Daily",
      "username": "@technewsdaily",
      "subscribers": 2100000,
      "growth_7d": 8.2,
      "engagement_rate": 4.8,
      "context_type": "country",
      "context_label": "United States",
      "trend_label": "growth_7d",
      "trend_value": 8.2
    },
    {
      "rank": 2,
      "channel_id": "f8e98743-1448-4d13-8f8f-b8fbbf272141",
      "name": "Crypto Insights",
      "username": "@cryptoinsights",
      "subscribers": 1800000,
      "growth_7d": 12.4,
      "engagement_rate": 6.2,
      "context_type": "country",
      "context_label": "United States",
      "trend_label": "growth_7d",
      "trend_value": 12.4
    }
  ],
  "meta": {
    "country_code": "US",
    "country_name": "United States",
    "snapshot_date": "2026-02-14",
    "total_ranked_channels": 83,
    "applied_limit": 10
  }
}
```

### GET `/v1.0/rankings/categories` (base list)

```bash
curl -s "$API_BASE/v1.0/rankings/categories?category_slug=technology&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": [
    {
      "rank": 1,
      "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
      "name": "Tech News Daily",
      "username": "@technewsdaily",
      "subscribers": 2100000,
      "growth_7d": 8.2,
      "engagement_rate": 4.8,
      "context_type": "category",
      "context_label": "Technology",
      "trend_label": "engagement_rate",
      "trend_value": 4.8
    },
    {
      "rank": 2,
      "channel_id": "0b4f1ef1-30e3-47f0-89f1-5cf25114ba3b",
      "name": "AI Weekly",
      "username": "@aiweekly",
      "subscribers": 1400000,
      "growth_7d": 6.1,
      "engagement_rate": 5.2,
      "context_type": "category",
      "context_label": "Technology",
      "trend_label": "engagement_rate",
      "trend_value": 5.2
    }
  ],
  "meta": {
    "category_slug": "technology",
    "category_name": "Technology",
    "snapshot_date": "2026-02-14",
    "total_ranked_channels": 41,
    "applied_limit": 10
  }
}
```

### GET `/v1.0/rankings/collections` (base)

```bash
curl -s "$API_BASE/v1.0/rankings/collections?limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": [
    {
      "collection_id": "8fa793e5-c3b9-4140-a498-08d842d2862f",
      "slug": "crypto-blockchain",
      "name": "Crypto & Blockchain",
      "description": "Top channels in crypto markets and blockchain ecosystems.",
      "icon": "💎",
      "channels_count": 2450,
      "cta_label": "Explore",
      "cta_target": "/rankings/collections/8fa793e5-c3b9-4140-a498-08d842d2862f/channels"
    },
    {
      "collection_id": "5ae0cf2c-ef1d-4928-a8d7-a3f5ac04af1f",
      "slug": "tech-startups",
      "name": "Tech & Startups",
      "description": "Fast-growing channels for technology and startup founders.",
      "icon": "🚀",
      "channels_count": 1890,
      "cta_label": "Explore",
      "cta_target": "/rankings/collections/5ae0cf2c-ef1d-4928-a8d7-a3f5ac04af1f/channels"
    }
  ],
  "meta": {
    "total_active_collections": 6,
    "applied_limit": 20
  }
}
```

---

## Mini Apps

### GET `/v1.0/mini-apps/summary`

```bash
curl -s "$API_BASE/v1.0/mini-apps/summary?period=7d" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": {
    "total_mini_apps": 4412,
    "daily_active_users": 28500000,
    "total_sessions": 156000000,
    "avg_session_seconds": 272,
    "total_mini_apps_delta": 127,
    "daily_active_users_delta": 3140000,
    "daily_active_users_delta_percent": 12.38,
    "total_sessions_delta": 12400000,
    "total_sessions_delta_percent": 8.64,
    "avg_session_seconds_delta": 18
  },
  "meta": {}
}
```

### GET `/v1.0/mini-apps` (base list)

```bash
curl -s "$API_BASE/v1.0/mini-apps?sort_by=daily_users&sort_order=desc&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": [
    {
      "mini_app_id": "fbd37667-230f-4c5b-b0f6-243b02608e11",
      "name": "Hamster Kombat",
      "slug": "hamster-kombat",
      "category_slug": "games",
      "daily_users": 2500000,
      "total_users": 45000000,
      "sessions": 98000000,
      "rating": 4.8,
      "growth_weekly": 15.2,
      "launched_at": "2025-06-19"
    }
  ],
  "page": {
    "next_cursor": "eyJsYXN0X2lkIjoiZmJkMzc2NjctMjMwZi00YzViLWIwZjYtMjQzYjAyNjA4ZTExIiwib2Zmc2V0IjoyMH0=",
    "has_more": true
  },
  "meta": {
    "total_estimate": 4412
  }
}
```

### GET `/v1.0/mini-apps` (search + filters)

```bash
curl -s "$API_BASE/v1.0/mini-apps?q=wallet&category_slug=finance&min_daily_users=100000&min_rating=4.5&launch_within_days=180&min_growth=10&sort_by=growth&sort_order=desc&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": [
    {
      "mini_app_id": "8f33af72-4a15-4b6d-ae56-8ea6a0985262",
      "name": "Wallet",
      "slug": "wallet",
      "category_slug": "finance",
      "daily_users": 1200000,
      "total_users": 28000000,
      "sessions": 54000000,
      "rating": 4.9,
      "growth_weekly": 22.3,
      "launched_at": "2025-10-22"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  },
  "meta": {
    "total_estimate": 1
  }
}
```

### GET `/v1.0/mini-apps/{miniAppId}`

```bash
curl -s "$API_BASE/v1.0/mini-apps/fbd37667-230f-4c5b-b0f6-243b02608e11" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Event Tracking (Polling)

### GET `/v1.0/accounts/{accountId}/trackers` (base)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/trackers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "tracker_id": "4bbfc859-7f39-4cb8-bd5b-f79063e67f88",
      "account_id": "11111111-1111-1111-1111-111111111111",
      "tracker_type": "keyword",
      "tracker_value": "bitcoin price",
      "status": "active",
      "mentions_count": 12,
      "last_activity_at": "2026-02-14T20:11:00Z",
      "notify_push": true,
      "notify_telegram": true,
      "notify_email": false
    },
    {
      "tracker_id": "2c4c828f-dad0-4c2e-8deb-154a8b407173",
      "account_id": "11111111-1111-1111-1111-111111111111",
      "tracker_type": "channel",
      "tracker_value": "@technewsdaily",
      "status": "paused",
      "mentions_count": 5,
      "last_activity_at": "2026-02-14T13:20:00Z",
      "notify_push": true,
      "notify_telegram": true,
      "notify_email": true
    }
  ],
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/trackers` (filtered)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/trackers?status=active&type=keyword" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "tracker_id": "4bbfc859-7f39-4cb8-bd5b-f79063e67f88",
      "account_id": "11111111-1111-1111-1111-111111111111",
      "tracker_type": "keyword",
      "tracker_value": "bitcoin price",
      "status": "active",
      "mentions_count": 12,
      "last_activity_at": "2026-02-14T20:11:00Z",
      "notify_push": true,
      "notify_telegram": true,
      "notify_email": false
    }
  ],
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/trackers/{trackerId}` success

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/trackers/4bbfc859-7f39-4cb8-bd5b-f79063e67f88" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": {
    "tracker_id": "4bbfc859-7f39-4cb8-bd5b-f79063e67f88",
    "account_id": "11111111-1111-1111-1111-111111111111",
    "tracker_type": "keyword",
    "tracker_value": "bitcoin price",
    "status": "active",
    "mentions_count": 12,
    "last_activity_at": "2026-02-14T20:11:00Z",
    "notify_push": true,
    "notify_telegram": true,
    "notify_email": false
  },
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/trackers/{trackerId}` error (not found)

```json
{
  "detail": "Tracker not found."
}
```

### POST `/v1.0/accounts/{accountId}/trackers` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/trackers" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "tracker_type":"keyword",
    "tracker_value":"bitcoin price",
    "notify_push":true,
    "notify_telegram":true,
    "notify_email":false
  }'
```

```json
{
  "data": {
    "tracker_id": "9c3fe4c8-2a8f-4f72-8010-7d4649d2cbda",
    "account_id": "11111111-1111-1111-1111-111111111111",
    "tracker_type": "keyword",
    "tracker_value": "bitcoin price",
    "status": "active",
    "mentions_count": 0,
    "last_activity_at": null,
    "notify_push": true,
    "notify_telegram": true,
    "notify_email": false
  },
  "meta": {}
}
```

### POST `/v1.0/accounts/{accountId}/trackers` error (duplicate)

```json
{
  "detail": "Tracker already exists for this account."
}
```

### PATCH `/v1.0/accounts/{accountId}/trackers/{trackerId}` success

```bash
curl -s -X PATCH "$API_BASE/v1.0/accounts/$ACCOUNT_ID/trackers/4bbfc859-7f39-4cb8-bd5b-f79063e67f88" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{"status":"paused","notify_push":false}'
```

```json
{
  "data": {
    "tracker_id": "4bbfc859-7f39-4cb8-bd5b-f79063e67f88",
    "account_id": "11111111-1111-1111-1111-111111111111",
    "tracker_type": "keyword",
    "tracker_value": "bitcoin price",
    "status": "paused",
    "mentions_count": 12,
    "last_activity_at": "2026-02-14T20:11:00Z",
    "notify_push": false,
    "notify_telegram": true,
    "notify_email": false
  },
  "meta": {}
}
```

### PATCH `/v1.0/accounts/{accountId}/trackers/{trackerId}` error (forbidden)

```json
{
  "detail": "Insufficient permissions to update tracker."
}
```

### DELETE `/v1.0/accounts/{accountId}/trackers/{trackerId}` success

```bash
curl -s -X DELETE "$API_BASE/v1.0/accounts/$ACCOUNT_ID/trackers/4bbfc859-7f39-4cb8-bd5b-f79063e67f88" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -i
```

```http
HTTP/1.1 204 No Content
```

### DELETE `/v1.0/accounts/{accountId}/trackers/{trackerId}` error (not found)

```json
{
  "detail": "Tracker not found."
}
```

### GET `/v1.0/accounts/{accountId}/tracker-mentions` (base polling)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/tracker-mentions?limit=50" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "mention_id": "5a5a872f-37d9-475b-939f-e8664b2ec2f5",
      "tracker_id": "4bbfc859-7f39-4cb8-bd5b-f79063e67f88",
      "mention_seq": 100003,
      "channel_id": "9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2",
      "channel_name": "Tech News Daily",
      "post_id": "7066a9dc-bde6-4c73-bf8b-3847ebf72b03",
      "mention_text": "bitcoin price",
      "context_snippet": "Analysts expect more volatility in bitcoin price this week.",
      "mentioned_at": "2026-02-14T20:00:00Z"
    },
    {
      "mention_id": "fbfb27ce-f65b-43a8-83a6-70fc74de0379",
      "tracker_id": "4bbfc859-7f39-4cb8-bd5b-f79063e67f88",
      "mention_seq": 100002,
      "channel_id": "f8e98743-1448-4d13-8f8f-b8fbbf272141",
      "channel_name": "Crypto Growth Radar",
      "post_id": "4a2d7b13-e437-4d15-a5af-c8657e6f6451",
      "mention_text": "bitcoin price",
      "context_snippet": "Daily wrap-up on bitcoin price movement.",
      "mentioned_at": "2026-02-14T19:30:00Z"
    }
  ],
  "page": {
    "next_cursor": "eyJtZW50aW9uX3NlcSI6MTAwMDAyfQ==",
    "has_more": true
  },
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/tracker-mentions` (cursor + filters)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/tracker-mentions?tracker_id=4bbfc859-7f39-4cb8-bd5b-f79063e67f88&since=2026-02-14T00:00:00Z&until=2026-02-14T23:59:59Z&limit=50&cursor=eyJtZW50aW9uX3NlcSI6MTAwMDAwfQ==" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "mention_id": "9f960fd2-c5db-4f08-9fab-94916183f9f9",
      "tracker_id": "4bbfc859-7f39-4cb8-bd5b-f79063e67f88",
      "mention_seq": 99999,
      "channel_id": null,
      "channel_name": null,
      "post_id": null,
      "mention_text": "bitcoin price",
      "context_snippet": null,
      "mentioned_at": "2026-02-14T10:15:00Z"
    }
  ],
  "page": {
    "next_cursor": null,
    "has_more": false
  },
  "meta": {}
}
```

---

## Account

### GET `/v1.0/users/me`

```bash
curl -s "$API_BASE/v1.0/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "default_account_id": "11111111-1111-1111-1111-111111111111"
}
```

### PATCH `/v1.0/users/me` success

```bash
curl -s -X PATCH "$API_BASE/v1.0/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","telegram_username":"@johndoe"}'
```

### PATCH `/v1.0/users/me` validation error

```json
{
  "error": {
    "code": "validation_error",
    "message": "telegram_username must start with @",
    "details": []
  }
}
```

### GET `/v1.0/users/me/preferences`

```bash
curl -s "$API_BASE/v1.0/users/me/preferences" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": {
    "language_code": "en",
    "timezone": "UTC",
    "theme": "system"
  },
  "meta": {}
}
```

### PATCH `/v1.0/users/me/preferences` success

```bash
curl -s -X PATCH "$API_BASE/v1.0/users/me/preferences" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"language_code":"en","timezone":"America/New_York","theme":"dark"}'
```

### PATCH `/v1.0/users/me/preferences` validation error

```json
{
  "error": {
    "code": "validation_error",
    "message": "theme must be one of light,dark,system",
    "details": []
  }
}
```

### GET `/v1.0/users/me/notifications`

```bash
curl -s "$API_BASE/v1.0/users/me/notifications" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "data": {
    "email_notifications": true,
    "telegram_bot_alerts": true,
    "weekly_reports": false,
    "marketing_updates": false,
    "push_notifications": false
  },
  "meta": {}
}
```

### PATCH `/v1.0/users/me/notifications` success

```bash
curl -s -X PATCH "$API_BASE/v1.0/users/me/notifications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email_notifications":true,"telegram_bot_alerts":true,"weekly_reports":false,"marketing_updates":false,"push_notifications":true}'
```

### PATCH `/v1.0/users/me/notifications` validation error

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid notification payload",
    "details": []
  }
}
```

---

## Team

### GET `/v1.0/accounts/{accountId}/members` (base)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### GET `/v1.0/accounts/{accountId}/members` (client-side filtered by role)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### POST `/v1.0/accounts/{accountId}/members/invitations` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/members/invitations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "email":"analyst@example.com",
    "role":"editor",
    "channel_access":["9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2"]
  }'
```

### POST `/v1.0/accounts/{accountId}/members/invitations` error (already member)

```json
{
  "error": {
    "code": "validation_error",
    "message": "User is already a account member.",
    "details": []
  }
}
```

### PATCH `/v1.0/accounts/{accountId}/members/{memberId}` success

```bash
curl -s -X PATCH "$API_BASE/v1.0/accounts/$ACCOUNT_ID/members/8deefe66-b5b8-4b53-8f14-f04ab8f2f146" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin","status":"active"}'
```

### PATCH `/v1.0/accounts/{accountId}/members/{memberId}` error (forbidden)

```json
{
  "error": {
    "code": "forbidden",
    "message": "Only owner/admin can update members.",
    "details": []
  }
}
```

### DELETE `/v1.0/accounts/{accountId}/members/{memberId}` success

```bash
curl -s -X DELETE "$API_BASE/v1.0/accounts/$ACCOUNT_ID/members/8deefe66-b5b8-4b53-8f14-f04ab8f2f146" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -i
```

### DELETE `/v1.0/accounts/{accountId}/members/{memberId}` error (owner removal blocked)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Account owner cannot be removed.",
    "details": []
  }
}
```

### PUT `/v1.0/accounts/{accountId}/members/{memberId}/channel-access` success

```bash
curl -s -X PUT "$API_BASE/v1.0/accounts/$ACCOUNT_ID/members/8deefe66-b5b8-4b53-8f14-f04ab8f2f146/channel-access" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "channels":[
      {"channel_id":"9f28253d-8ffd-4d2f-a67c-ebaf0f6ba2f2","access_level":"editor"},
      {"channel_id":"d5e220e1-74f7-4b20-84a6-67100c53ca76","access_level":"viewer"}
    ]
  }'
```

### PUT `/v1.0/accounts/{accountId}/members/{memberId}/channel-access` error (invalid level)

```json
{
  "error": {
    "code": "validation_error",
    "message": "access_level must be one of viewer,editor,admin",
    "details": []
  }
}
```

---

## API Keys

### GET `/v1.0/accounts/{accountId}/api-keys` (base)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "api_key_id": "b1f55d1e-53d7-4c4f-ba37-81f2c9c3e853",
      "name": "Production API",
      "key_prefix": "tlm_prod_",
      "scopes": ["read:channels", "read:ads", "export"],
      "rate_limit_per_hour": 1000,
      "created_at": "2026-02-14T12:34:00Z",
      "last_used_at": "2026-02-14T13:30:00Z",
      "revoked_at": null
    }
  ],
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/api-keys` (client-side active only)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### POST `/v1.0/accounts/{accountId}/api-keys` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Production API",
    "scopes":["read:channels","read:ads","export"],
    "rate_limit_per_hour":1000
  }'
```

```json
{
  "data": {
    "api_key": {
      "api_key_id": "b1f55d1e-53d7-4c4f-ba37-81f2c9c3e853",
      "name": "Production API",
      "key_prefix": "tlm_prod_",
      "scopes": ["read:channels", "read:ads", "export"],
      "rate_limit_per_hour": 1000,
      "created_at": "2026-02-14T12:34:00Z",
      "last_used_at": null,
      "revoked_at": null
    },
    "secret": "tlm_prod_9f08f3e2..."
  },
  "meta": { "secret_returned_once": true }
}
```

### POST `/v1.0/accounts/{accountId}/api-keys` error (duplicate name)

```json
{
  "error": {
    "code": "validation_error",
    "message": "API key name already exists in account.",
    "details": []
  }
}
```

### POST `/v1.0/accounts/{accountId}/api-keys/{apiKeyId}/rotate` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/api-keys/b1f55d1e-53d7-4c4f-ba37-81f2c9c3e853/rotate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": {
    "api_key": {
      "api_key_id": "b1f55d1e-53d7-4c4f-ba37-81f2c9c3e853",
      "name": "Production API",
      "key_prefix": "tlm_rot_",
      "scopes": ["read:channels", "read:ads", "export"],
      "rate_limit_per_hour": 1000,
      "created_at": "2026-02-14T12:34:00Z",
      "last_used_at": null,
      "revoked_at": null
    },
    "secret": "tlm_rot_e357..."
  },
  "meta": { "secret_returned_once": true }
}
```

### POST `/v1.0/accounts/{accountId}/api-keys/{apiKeyId}/rotate` error (not found)

```json
{
  "error": {
    "code": "not_found",
    "message": "API key not found.",
    "details": []
  }
}
```

### DELETE `/v1.0/accounts/{accountId}/api-keys/{apiKeyId}` success

```bash
curl -s -X DELETE "$API_BASE/v1.0/accounts/$ACCOUNT_ID/api-keys/b1f55d1e-53d7-4c4f-ba37-81f2c9c3e853" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -i
```

### DELETE `/v1.0/accounts/{accountId}/api-keys/{apiKeyId}` error (forbidden)

```json
{
  "error": {
    "code": "forbidden",
    "message": "Only owner/admin can revoke API keys.",
    "details": []
  }
}
```

### GET `/v1.0/accounts/{accountId}/api-usage`

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/api-usage?from=2026-02-01&to=2026-02-14" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": {
    "total_requests": 18670,
    "error_rate": 0.1,
    "avg_latency_ms": 124.0,
    "by_day": [
      { "date": "2026-02-13", "requests": 1120, "errors": 1 },
      { "date": "2026-02-14", "requests": 1430, "errors": 2 }
    ]
  },
  "meta": {}
}
```

---

## Billing

### GET `/v1.0/accounts/{accountId}/subscription`

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/subscription" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": {
    "subscription_id": "4e4c5c95-1504-4684-9112-6ab3d85d3e91",
    "account_id": "11111111-1111-1111-1111-111111111111",
    "plan_code": "pro",
    "status": "active",
    "billing_state": "active",
    "current_period_start": "2026-02-01T00:00:00Z",
    "current_period_end": "2026-03-01T00:00:00Z",
    "cancel_at_period_end": false
  },
  "meta": {}
}
```

### PATCH `/v1.0/accounts/{accountId}/subscription` success

```bash
curl -s -X PATCH "$API_BASE/v1.0/accounts/$ACCOUNT_ID/subscription" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{"plan_code":"pro","cancel_at_period_end":false}'
```

### PATCH `/v1.0/accounts/{accountId}/subscription` error (invalid plan)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Unknown plan_code",
    "details": []
  }
}
```

### GET `/v1.0/accounts/{accountId}/usage`

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/usage?from=2026-02-01&to=2026-02-14" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": {
    "from": "2026-02-01",
    "to": "2026-02-14",
    "channel_searches": 2450,
    "event_trackers_count": 32,
    "api_requests_count": 8230,
    "exports_count": 15
  },
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/payment-methods` (base)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/payment-methods" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "payment_method_id": "2a313503-2c4d-4b91-bf0d-584b5fbd5ea5",
      "brand": "VISA",
      "last4": "4242",
      "exp_month": 12,
      "exp_year": 2027,
      "is_default": true,
      "status": "active"
    }
  ],
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/payment-methods` (client-side default first)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/payment-methods" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### POST `/v1.0/accounts/{accountId}/payment-methods` success

```bash
curl -s -X POST "$API_BASE/v1.0/accounts/$ACCOUNT_ID/payment-methods" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{"provider_payment_method_token":"pm_tok_123","make_default":true}'
```

```json
{
  "data": {
    "payment_method_id": "2a313503-2c4d-4b91-bf0d-584b5fbd5ea5",
    "brand": "VISA",
    "last4": "1234",
    "exp_month": 12,
    "exp_year": 2028,
    "is_default": true,
    "status": "active"
  },
  "meta": {}
}
```

### POST `/v1.0/accounts/{accountId}/payment-methods` error (token rejected)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Payment provider token invalid.",
    "details": []
  }
}
```

### GET `/v1.0/accounts/{accountId}/invoices` (base)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/invoices?limit=20" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": [
    {
      "invoice_id": "9a027168-5e87-42da-80d3-3305ca86d95a",
      "invoice_number": "INV-2026-001",
      "status": "active",
      "currency": "USD",
      "amount_total": 49.0,
      "period_start": "2026-01-01",
      "period_end": "2026-01-31",
      "issued_at": "2026-02-01T00:00:00Z",
      "paid_at": "2026-02-01T00:03:00Z"
    }
  ],
  "page": { "next_cursor": null, "has_more": false },
  "meta": {}
}
```

### GET `/v1.0/accounts/{accountId}/invoices` (paginated)

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/invoices?limit=20&cursor=eyJpbnZvaWNlX2lkIjoiYWJjIn0=" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### GET `/v1.0/accounts/{accountId}/invoices/{invoiceId}/download-url`

```bash
curl -s "$API_BASE/v1.0/accounts/$ACCOUNT_ID/invoices/9a027168-5e87-42da-80d3-3305ca86d95a/download-url" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

```json
{
  "data": {
    "url": "https://cdn.telegrampulse.example.com/invoices/INV-2026-001.pdf?token=abc",
    "expires_at": "2026-02-14T17:00:00Z"
  },
  "meta": {}
}
```

---

## Exports

### POST `/v1.0/exports` success

```bash
curl -s -X POST "$API_BASE/v1.0/exports" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "export_type":"channels_csv",
    "filters":{
      "q":"crypto",
      "country_code":"US",
      "category_slug":"cryptocurrencies"
    }
  }'
```

```json
{
  "data": {
    "export_id": "b0c083e9-a44e-435f-adf4-30bb7dd89d76",
    "account_id": "11111111-1111-1111-1111-111111111111",
    "export_type": "channels_csv",
    "status": "queued",
    "created_at": "2026-02-14T13:00:00Z",
    "started_at": null,
    "completed_at": null,
    "file_size_bytes": null
  },
  "meta": {}
}
```

### POST `/v1.0/exports` error (unsupported export_type)

```json
{
  "error": {
    "code": "validation_error",
    "message": "export_type must be one of supported values",
    "details": []
  }
}
```

### GET `/v1.0/exports/{exportId}`

```bash
curl -s "$API_BASE/v1.0/exports/b0c083e9-a44e-435f-adf4-30bb7dd89d76" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

### GET `/v1.0/exports/{exportId}/download`

```bash
curl -s "$API_BASE/v1.0/exports/b0c083e9-a44e-435f-adf4-30bb7dd89d76/download" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Account-Id: $ACCOUNT_ID"
```

---

## Common Authorization Error Example

Used by all protected endpoints:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Missing or invalid bearer token.",
    "details": []
  }
}
```

## Notes for UU Integration

1. Always send `Authorization: Bearer <custom auth JWT>`.
2. For account-scoped endpoints, always send `X-Account-Id` and keep it equal to path `accountId`.
3. Use cursor pagination for feeds and large lists.
4. Event tracking uses polling (`/tracker-mentions`) and not websocket streaming in v1.
