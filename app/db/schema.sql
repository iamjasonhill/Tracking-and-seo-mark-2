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
