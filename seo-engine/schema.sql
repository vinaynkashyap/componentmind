-- Neon Serverless Postgres Free Tier Schema for Autonomous SEO Engine
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    keyword TEXT UNIQUE NOT NULL,
    intent TEXT DEFAULT 'bofu',
    search_volume INTEGER DEFAULT 0,
    weak_spot_score REAL DEFAULT 0,
    target_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rank_snapshots (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    domain TEXT NOT NULL,
    position INTEGER,
    ranking_url TEXT,
    has_ai_overview BOOLEAN DEFAULT FALSE,
    top_competitors JSONB DEFAULT '[]'::jsonb,
    captured_at DATE DEFAULT CURRENT_DATE,
    UNIQUE (keyword, domain, captured_at)
);

CREATE TABLE IF NOT EXISTS gsc_metrics (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    page TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0,
    avg_position REAL DEFAULT 0,
    captured_at DATE DEFAULT CURRENT_DATE,
    UNIQUE (query, page, captured_at)
);
