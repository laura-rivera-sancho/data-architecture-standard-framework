DROP TABLE IF EXISTS warehouse.fact_order_items;
DROP TABLE IF EXISTS warehouse.fact_orders;
DROP TABLE IF EXISTS warehouse.fact_campaign_touchpoints;
DROP TABLE IF EXISTS warehouse.fact_experiment_exposures;
DROP TABLE IF EXISTS warehouse.fact_customer_events;

DROP TABLE IF EXISTS warehouse.dim_date;
CREATE TABLE warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    calendar_date DATE UNIQUE,
    day_of_week_number INTEGER,
    day_of_week_name VARCHAR,
    day_of_month INTEGER,
    month_number INTEGER,
    month_name VARCHAR,
    quarter_number INTEGER,
    calendar_year INTEGER,
    is_weekend BOOLEAN
);

WITH date_values AS (
    SELECT CAST(order_timestamp AS DATE) AS calendar_date FROM staging.orders
    UNION ALL
    SELECT CAST(touchpoint_timestamp AS DATE) FROM staging.campaign_touchpoints
    UNION ALL
    SELECT CAST(assigned_at AS DATE) FROM staging.experiment_exposures
    UNION ALL
    SELECT CAST(event_timestamp AS DATE) FROM staging.customer_events
),
bounds AS (
    SELECT MIN(calendar_date) AS min_date, MAX(calendar_date) AS max_date FROM date_values
),
dates AS (
    SELECT CAST(generate_series AS DATE) AS calendar_date
    FROM bounds, generate_series(min_date, max_date, INTERVAL 1 DAY)
)
INSERT INTO warehouse.dim_date
SELECT
    0,
    DATE '1900-01-01',
    1,
    'Unknown',
    1,
    1,
    'Unknown',
    1,
    1900,
    false
UNION ALL
SELECT
    CAST(strftime(calendar_date, '%Y%m%d') AS INTEGER) AS date_key,
    calendar_date,
    CAST(dayofweek(calendar_date) AS INTEGER) AS day_of_week_number,
    dayname(calendar_date) AS day_of_week_name,
    CAST(day(calendar_date) AS INTEGER) AS day_of_month,
    CAST(month(calendar_date) AS INTEGER) AS month_number,
    monthname(calendar_date) AS month_name,
    CAST(quarter(calendar_date) AS INTEGER) AS quarter_number,
    CAST(year(calendar_date) AS INTEGER) AS calendar_year,
    dayofweek(calendar_date) IN (0, 6) AS is_weekend
FROM dates;

DROP TABLE IF EXISTS warehouse.dim_customer;
CREATE TABLE warehouse.dim_customer (
    customer_key BIGINT PRIMARY KEY,
    customer_id VARCHAR NOT NULL,
    email_hash VARCHAR,
    acquisition_channel VARCHAR NOT NULL,
    country_code VARCHAR NOT NULL,
    marketing_consent BOOLEAN NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ NOT NULL,
    is_current BOOLEAN NOT NULL,
    attribute_hash VARCHAR NOT NULL,
    UNIQUE (customer_id, valid_from)
);

INSERT INTO warehouse.dim_customer
SELECT
    0,
    '__UNKNOWN__',
    NULL,
    'unknown',
    'XX',
    false,
    TIMESTAMPTZ '1900-01-01 00:00:00+00',
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    true,
    md5('__UNKNOWN__')
UNION ALL
SELECT
    row_number() OVER (ORDER BY customer_id),
    customer_id,
    email_hash,
    acquisition_channel,
    country_code,
    marketing_consent,
    created_at,
    TIMESTAMPTZ '9999-12-31 23:59:59+00',
    true,
    md5(concat_ws('|', acquisition_channel, country_code, CAST(marketing_consent AS VARCHAR)))
FROM staging.customers;

DROP TABLE IF EXISTS warehouse.dim_product;
CREATE TABLE warehouse.dim_product (
    product_key BIGINT PRIMARY KEY,
    product_id VARCHAR UNIQUE NOT NULL,
    product_name VARCHAR NOT NULL,
    is_active BOOLEAN NOT NULL
);

INSERT INTO warehouse.dim_product
SELECT 0, '__UNKNOWN__', 'Unknown product', false
UNION ALL
SELECT
    row_number() OVER (ORDER BY product_id),
    product_id,
    concat('Product ', product_id),
    true
FROM (SELECT DISTINCT product_id FROM staging.order_items);

DROP TABLE IF EXISTS warehouse.dim_campaign;
CREATE TABLE warehouse.dim_campaign (
    campaign_key BIGINT PRIMARY KEY,
    campaign_id VARCHAR UNIQUE NOT NULL,
    campaign_name VARCHAR NOT NULL,
    is_active BOOLEAN NOT NULL
);

INSERT INTO warehouse.dim_campaign
SELECT 0, '__UNKNOWN__', 'Unknown campaign', false
UNION ALL
SELECT
    row_number() OVER (ORDER BY campaign_id),
    campaign_id,
    concat('Campaign ', campaign_id),
    true
FROM (SELECT DISTINCT campaign_id FROM staging.campaign_touchpoints);

DROP TABLE IF EXISTS warehouse.dim_channel;
CREATE TABLE warehouse.dim_channel (
    channel_key BIGINT PRIMARY KEY,
    channel_code VARCHAR UNIQUE NOT NULL,
    channel_group VARCHAR NOT NULL
);

INSERT INTO warehouse.dim_channel
SELECT 0, '__UNKNOWN__', 'unknown'
UNION ALL
SELECT
    row_number() OVER (ORDER BY channel_code),
    channel_code,
    CASE
        WHEN channel_code IN ('web', 'ios', 'android', 'push') THEN 'owned_digital'
        WHEN channel_code IN ('email', 'sms') THEN 'direct_marketing'
        WHEN channel_code IN ('paid_search', 'paid_social') THEN 'paid_media'
        ELSE 'other'
    END
FROM (
    SELECT channel AS channel_code FROM staging.campaign_touchpoints
    UNION
    SELECT channel AS channel_code FROM staging.customer_events
    UNION
    SELECT acquisition_channel AS channel_code FROM staging.customers
);
