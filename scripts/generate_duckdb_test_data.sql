-- DuckDB SQL script to generate users_prod and users_dev test data.
-- Adjust the values in the params table to control row counts.

-- params:start
CREATE OR REPLACE TEMP TABLE params AS
SELECT
  100::INTEGER AS prod_rows,
  5::INTEGER AS dev_remove_rows,
  10::INTEGER AS dev_add_rows,
  8::INTEGER AS dev_null_status_rows;
-- params:end

DROP TABLE IF EXISTS users_prod;
DROP TABLE IF EXISTS users_dev;

CREATE TABLE users_prod (
  id BIGINT,
  name VARCHAR,
  status VARCHAR,
  created_at TIMESTAMP
);

INSERT INTO users_prod (id, name, status, created_at)
SELECT
  ROW_NUMBER() OVER () AS id,
  'user_' || lpad(CAST(i AS VARCHAR), 6, '0') AS name,
  CASE
    WHEN r < 0.70 THEN 'active'
    WHEN r < 0.90 THEN 'inactive'
    ELSE 'banned'
  END AS status,
  NOW() - (random() * INTERVAL '365 days') AS created_at
FROM (
  SELECT
    i,
    random() AS r
  FROM range((SELECT prod_rows FROM params)) AS t(i)
) AS seeded;

CREATE TABLE users_dev (
  id BIGINT,
  name VARCHAR,
  status VARCHAR,
  created_at TIMESTAMP,
  is_deleted BOOLEAN
);

INSERT INTO users_dev (id, name, status, created_at, is_deleted)
SELECT
  id,
  name,
  status,
  created_at,
  FALSE AS is_deleted
FROM users_prod;

DELETE FROM users_dev
WHERE id IN (
  SELECT id
  FROM users_dev
  ORDER BY random()
  LIMIT (SELECT dev_remove_rows FROM params)
);

UPDATE users_dev
SET status = NULL
WHERE id IN (
  SELECT id
  FROM users_dev
  ORDER BY random()
  LIMIT (SELECT dev_null_status_rows FROM params)
);

INSERT INTO users_dev (id, name, status, created_at, is_deleted)
WITH max_id AS (
  SELECT COALESCE(MAX(id), 0) AS id FROM users_dev
)
SELECT
  max_id.id + ROW_NUMBER() OVER () AS id,
  'user_dev_' || lpad(CAST(i AS VARCHAR), 6, '0') AS name,
  CASE
    WHEN r < 0.60 THEN 'active'
    WHEN r < 0.85 THEN 'inactive'
    ELSE 'banned'
  END AS status,
  NOW() - (random() * INTERVAL '365 days') AS created_at,
  FALSE AS is_deleted
FROM (
  SELECT
    i,
    random() AS r
  FROM range((SELECT dev_add_rows FROM params)) AS t(i)
) AS seeded
CROSS JOIN max_id;
