# SEO Data Sync Platform -- Requirements

## 🎯 Objectives

-   Integrate with **Google Search Console (GSC)** and **Bing Webmaster
    Tools (BWT)**.
-   Support **multiple accounts / sites per user** (multi-tenant).
-   Perform **initial historical backfill** (maximum available history).
-   Run **daily sync jobs** to fetch incremental data ("top up").
-   Store all data in a **PostgreSQL database**.
-   Provide APIs for querying/exporting data.
-   Enforce clear **constraints** so development assistants
    (Cursor/Windsurf) can build consistently.

------------------------------------------------------------------------

## 🏗️ Architecture

### Core Components

1.  **API Layer**
    -   REST or GraphQL endpoints for managing accounts, sites, sync
        jobs, and serving data.
    -   Options:
        -   **Python**: FastAPI + Celery for async jobs.
        -   **Node.js/TypeScript**: Express or NestJS + BullMQ for jobs.
2.  **Job Scheduler / Worker**
    -   Handles API calls and retries (backfill + daily syncs).
    -   Cron-based or queue-driven.
3.  **Database**
    -   PostgreSQL schema for users, accounts, sites, search data, sync
        jobs.
4.  **Storage Layer**
    -   Data inserted via **UPSERT** (avoid duplicates).
    -   Daily sync adds only new rows since last run.
5.  **OAuth Integration**
    -   Google: OAuth 2.0 with refresh tokens.
    -   Bing: API key or OAuth 2.0.

------------------------------------------------------------------------

## 📡 Data Flow

1.  **User connects account**
    -   Google: OAuth flow.
    -   Bing: API key or OAuth.
    -   Save credentials encrypted in DB.
2.  **Backfill**
    -   Google: up to 16 months.
    -   Bing: up to 6--12 months.
    -   Paginate until complete.
3.  **Daily sync**
    -   Fetch only yesterday's data.
    -   Upsert into DB.
4.  **Error handling**
    -   Retry with exponential backoff.
    -   Log HTTP status + response body.

------------------------------------------------------------------------

## ⚙️ Constraints

-   **Language**: Either Python (FastAPI + Celery) OR Node.js
    (TypeScript + NestJS/Express).
-   **Database**: PostgreSQL only.
-   **Deployment**: Must run on Docker.
-   **Scheduler**: Cron-style jobs.
-   **Auth**: Multiple Google/Bing accounts supported.
-   **Data freshness**: Only incremental pulls after backfill.
-   **Error logging**: Always log `site`, `status`, `body` on failure.
-   **Scalability**: Handle 100+ sites daily.

------------------------------------------------------------------------

## 🔄 Sync Logic

### Google Search Console

-   Endpoint: `searchanalytics.query`
-   Params: `siteUrl`, `startDate`, `endDate`,
    `dimensions=[query/page]`, `rowLimit=25000`, `startRow`.
-   Historical limit: \~16 months.

### Bing Webmaster Tools

-   Base URL: `https://api.bing.microsoft.com/v7.0/Webmaster`
-   Endpoints:
    -   `/QueryStats`
    -   `/PageStats`
    -   `/SiteStats`
-   Auth: `apikey=KEY` or OAuth token.
-   Historical limit: 6--12 months.

------------------------------------------------------------------------

## 📊 Database Schema

``` sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE,
  password_hash TEXT
);

CREATE TABLE accounts (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  provider TEXT CHECK (provider IN ('google', 'bing')),
  credentials JSONB -- encrypted
);

CREATE TABLE sites (
  id SERIAL PRIMARY KEY,
  account_id INT REFERENCES accounts(id),
  site_url TEXT,
  enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE search_data (
  id BIGSERIAL PRIMARY KEY,
  site_id INT REFERENCES sites(id),
  provider TEXT,
  date DATE,
  dimension TEXT, -- 'query' or 'page'
  key TEXT,       -- query string or page URL
  clicks INT,
  impressions INT,
  ctr FLOAT,
  position FLOAT,
  UNIQUE(site_id, provider, date, dimension, key)
);

CREATE TABLE sync_jobs (
  id SERIAL PRIMARY KEY,
  site_id INT REFERENCES sites(id),
  started_at TIMESTAMP,
  finished_at TIMESTAMP,
  status TEXT,
  error TEXT
);
```

------------------------------------------------------------------------

## 🛠️ Next Steps

-   [ ] Decide **Python vs Node.js** stack.
-   [ ] Scaffold project with Docker + Postgres.
-   [ ] Implement **OAuth + credential storage**.
-   [ ] Build **backfill worker** for Google & Bing.
-   [ ] Build **daily incremental sync worker**.
-   [ ] Add logging + retries.
-   [ ] (Optional) Expose API/GraphQL for querying data.

------------------------------------------------------------------------
