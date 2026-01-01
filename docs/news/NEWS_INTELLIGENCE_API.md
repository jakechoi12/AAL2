# News Intelligence API Documentation

## Overview

The News Intelligence service provides logistics-focused news collection, AI analysis, and visualization capabilities. It aggregates news from multiple sources and provides intelligent insights for supply chain decision-making.

### Key Features (v2.0)

- **Optimized AI Analysis**: Rule-based first + AI supplementary approach (70% API cost reduction)
- **Async Background Processing**: Non-blocking server startup with background analysis
- **Batch Processing**: Multiple articles analyzed in single API call
- **GDELT Title Scraping**: Automatic title extraction from source URLs
- **Interactive Map**: Country-level crisis visualization with news popup

## Base URL

```
/api/news-intelligence
```

---

## Endpoints

### 1. Get News Articles

```
GET /api/news-intelligence/articles
```

Retrieve paginated news articles with filtering options.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `news_type` | string | `all` | Filter by news type: `KR`, `GLOBAL`, or `all` |
| `category` | string | - | Filter by category: `Crisis`, `Ocean`, `Air`, `Inland`, `Economy`, `ETC` |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max: 100) |
| `is_crisis` | boolean | - | Filter crisis articles only |

#### Response

```json
{
  "articles": [
    {
      "id": 1,
      "title": "Port Strike in Rotterdam...",
      "content_summary": "Labor unions...",
      "source_name": "FreightWaves",
      "url": "https://...",
      "published_at_utc": "2025-01-01T10:00:00",
      "collected_at_utc": "2025-01-01T10:15:00",
      "news_type": "GLOBAL",
      "category": "Crisis",
      "is_crisis": true,
      "country_tags": ["NL", "DE"],
      "goldstein_scale": -7.5,
      "avg_tone": -4.2,
      "num_mentions": 142,
      "num_sources": 18,
      "num_articles": 25,
      "keywords": ["strike", "port", "delay"],
      "status": "ACTIVE"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

---

### 2. Get Status Summary

```
GET /api/news-intelligence/status
```

Get collection status and summary statistics.

#### Response

```json
{
  "total_articles": 1428,
  "kr_count": 512,
  "global_count": 916,
  "crisis_count": 45,
  "categories": {
    "Crisis": 45,
    "Ocean": 320,
    "Air": 280,
    "Inland": 210,
    "Economy": 350,
    "ETC": 223
  },
  "last_updated_utc": "2025-01-01T10:00:00",
  "current_time_utc": "2025-01-01T10:15:00"
}
```

---

### 3. Get Map Data

```
GET /api/news-intelligence/map
```

Get crisis data for map visualization (country-level heatmap).

#### Response

```json
{
  "countries": {
    "US": 5,
    "CN": 3,
    "NL": 2,
    "DE": 1
  },
  "total_crisis": 45
}
```

---

### 4. Get Country Articles (NEW)

```
GET /api/news-intelligence/map/country/{country_code}
```

Get crisis articles for a specific country (used for map popup).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `country_code` | string | ISO 2-letter country code (e.g., US, CN, KR) |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Maximum articles to return (max: 20) |

#### Response

```json
{
  "country_code": "US",
  "articles": [
    {
      "id": 1,
      "title": "Port congestion at Long Beach...",
      "source_name": "FreightWaves",
      "category": "Crisis",
      "url": "https://...",
      "published_at_utc": "2025-01-01T10:00:00",
      "goldstein_scale": -5.2
    }
  ],
  "total": 5
}
```

---

### 5. Get Word Cloud Data

```
GET /api/news-intelligence/wordcloud
```

Get keyword frequency data for word cloud visualization.

#### Response

```json
{
  "keywords": {
    "congestion": 25,
    "strike": 18,
    "delay": 15,
    "freight": 12,
    "port": 10
  },
  "total_articles": 1428
}
```

---

### 6. Get Categories

```
GET /api/news-intelligence/categories
```

Get category distribution for chart visualization.

#### Response

```json
{
  "categories": [
    {"name": "Economy", "count": 350, "percentage": 24.5},
    {"name": "Ocean", "count": 320, "percentage": 22.4},
    {"name": "Air", "count": 280, "percentage": 19.6},
    {"name": "ETC", "count": 223, "percentage": 15.6},
    {"name": "Inland", "count": 210, "percentage": 14.7},
    {"name": "Crisis", "count": 45, "percentage": 3.2}
  ],
  "total": 1428
}
```

---

### 7. Get Critical Alerts

```
GET /api/news-intelligence/critical-alerts
```

Get crisis articles for critical alerts panel.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 10 | Maximum alerts to return |
| `include_summary` | boolean | false | Include AI-generated summary |

#### Response

```json
{
  "alerts": [...],
  "count": 45,
  "summary": "• Rotterdam port strike affecting container handling..."
}
```

---

### 8. Trigger Manual Collection (Admin)

```
POST /api/news-intelligence/collect
```

Manually trigger a news collection job.

#### Response

```json
{
  "success": true,
  "total_collected": 150,
  "new_articles": 45,
  "duplicates": 105,
  "kr_count": 30,
  "global_count": 120,
  "executed_at_utc": "2025-01-01T10:00:00",
  "duration_seconds": 12.5
}
```

---

## Data Sources

### RSS Feeds (International)

| Source | URL |
|--------|-----|
| The Loadstar | https://theloadstar.com/feed/ |
| FreightWaves | https://www.freightwaves.com/feed |
| Supply Chain Dive | https://www.supplychaindive.com/feeds/news/ |
| Splash247 | https://splash247.com/feed/ |
| Air Cargo Week | https://aircargoweek.com/feed/ |
| Supply Chain 247 | https://www.supplychain247.com/rss/all/feeds |

### RSS Feeds (Korean)

| Source | URL |
|--------|-----|
| 물류신문 | https://www.klnews.co.kr/rss/allArticle.xml |
| 해운신문 | https://www.maritimepress.co.kr/rss/allArticle.xml |
| 카고뉴스 | https://www.cargonews.co.kr/rss/allArticle.xml |

### Other Sources

- **GDELT**: Global events with Goldstein scale analysis (title scraping from source URLs)
- **Google News**: Search-based collection (logistics keywords)
- **Naver News**: Korean search-based collection (requires API key)

---

## News Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **Crisis** | Supply chain disruptions | Strikes, accidents, disasters, conflicts |
| **Ocean** | Maritime/shipping | Port news, container shipping, vessel updates |
| **Air** | Aviation/air cargo | Air freight, airlines, airports |
| **Inland** | Land transportation | Trucking, rail, warehousing |
| **Economy** | Economic indicators | Freight rates, demand, trade policy |
| **ETC** | Other/miscellaneous | General logistics news |

---

## AI Analysis Optimization (v2.0)

### Strategy

The analyzer uses a three-tier optimization strategy:

| Tier | Method | Cost | Speed | Accuracy |
|------|--------|------|-------|----------|
| 1 | Rule-based | Free | Fast | 85% |
| 2 | AI Batch | Low | Medium | 95% |
| 3 | AI Single | High | Slow | 95% |

### Processing Flow

```
Articles -> Rule-based Analysis -> Confidence Score
                |
                +-> High confidence (>60%): Use rule-based result ✓
                |
                +-> Low confidence: Queue for AI batch processing
                                    |
                                    +-> Batch 10 articles per API call
                                    +-> Update database
```

### Performance Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| API Calls per 50 articles | 50 | 5-10 | 80-90% ↓ |
| Processing time | 50s | 10s | 80% ↓ |
| Cost per cycle | $0.0075 | $0.001 | 87% ↓ |
| Server startup block | 60s | 0s | 100% ↓ |

### Background Processing

Analysis runs in a separate background thread:

1. **Collection Phase**: Fast, non-blocking (~5s)
2. **Analysis Phase**: Background thread, non-blocking
3. **Server Ready**: Immediate, no wait for analysis

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | No | PostgreSQL connection URL (defaults to SQLite) |
| `OPENAI_API_KEY` | No | OpenAI API key for AI analysis |
| `NAVER_CLIENT_ID` | No | Naver API client ID |
| `NAVER_CLIENT_SECRET` | No | Naver API client secret |

---

## Scheduled Jobs

| Job | Interval | Description |
|-----|----------|-------------|
| News Collection | 1 hour | Collects news from all sources |
| Background Analysis | After collection | Analyzes new articles (async) |
| Archiving | 1 hour | Archives articles older than 24 hours |

---

## File Structure

```
server/news_intelligence/
├── __init__.py           # Module exports
├── models.py             # Database models (NewsArticle, CollectionLog)
├── api.py                # API endpoints (Flask Blueprint)
├── analyzer.py           # Optimized AI analysis (rule-based + batch AI)
└── collectors/
    ├── __init__.py       # Collectors exports
    ├── base.py           # Base collector class
    ├── manager.py        # Collection orchestration
    ├── rss_collector.py  # RSS feed collector
    ├── gdelt_collector.py    # GDELT collector (with URL title scraping)
    ├── google_news_collector.py  # Google News
    └── naver_news_collector.py   # Naver News
```

---

## Frontend Features

### Map Visualization

- **Crisis Heatmap**: Country-level intensity based on crisis count
- **Color Scale**: 
  - Light red (1-2 alerts)
  - Medium red (3-5 alerts)
  - Dark red (6+ alerts)
- **Interactive Popup**: Click country to see news list with scroll

### Word Cloud

- **Keywords**: Top 50 logistics keywords from last 24 hours
- **Size**: Based on frequency
- **Excluded**: GDELT metrics, common stop words

---

## Changelog

### v2.0 (2026-01-01)

- Added rule-based first analysis with confidence scoring
- Implemented async background processing for analysis
- Added batch AI processing (10 articles per call)
- Added GDELT title scraping from source URLs
- Added country articles endpoint for map popup
- Improved word cloud filtering (excludes GDELT metrics)
- Updated API documentation with optimization details

### v1.0 (Initial)

- Basic news collection from multiple sources
- AI-powered categorization and keyword extraction
- Map visualization and word cloud
- Real-time dashboard
