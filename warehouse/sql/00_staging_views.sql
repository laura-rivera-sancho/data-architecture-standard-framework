CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE OR REPLACE VIEW staging.customers AS
SELECT
    customer_id,
    email_hash,
    acquisition_channel,
    country_code,
    CAST(created_at AS TIMESTAMPTZ) AS created_at,
    CAST(marketing_consent AS BOOLEAN) AS marketing_consent,
    CAST(source_updated_at AS TIMESTAMPTZ) AS source_updated_at,
    CAST(source_loaded_at AS TIMESTAMPTZ) AS source_loaded_at,
    _row_hash
FROM read_csv('{{STAGED_DIR}}/stg_customers.csv', header = true, all_varchar = true);

CREATE OR REPLACE VIEW staging.orders AS
SELECT
    order_id,
    customer_id,
    CAST(order_timestamp AS TIMESTAMPTZ) AS order_timestamp,
    order_status,
    currency_code,
    CAST(gross_amount AS DECIMAL(18, 2)) AS gross_amount,
    CAST(discount_amount AS DECIMAL(18, 2)) AS discount_amount,
    CAST(source_loaded_at AS TIMESTAMPTZ) AS source_loaded_at,
    _row_hash
FROM read_csv('{{STAGED_DIR}}/stg_orders.csv', header = true, all_varchar = true);

CREATE OR REPLACE VIEW staging.order_items AS
SELECT
    order_id,
    CAST(line_number AS INTEGER) AS line_number,
    product_id,
    CAST(quantity AS INTEGER) AS quantity,
    CAST(unit_price AS DECIMAL(18, 2)) AS unit_price,
    CAST(line_discount_amount AS DECIMAL(18, 2)) AS line_discount_amount,
    CAST(source_loaded_at AS TIMESTAMPTZ) AS source_loaded_at,
    _row_hash
FROM read_csv('{{STAGED_DIR}}/stg_order_items.csv', header = true, all_varchar = true);

CREATE OR REPLACE VIEW staging.campaign_touchpoints AS
SELECT
    touchpoint_id,
    customer_id,
    campaign_id,
    channel,
    touchpoint_type,
    CAST(touchpoint_timestamp AS TIMESTAMPTZ) AS touchpoint_timestamp,
    CAST(attributed_cost AS DECIMAL(18, 2)) AS attributed_cost,
    CAST(source_loaded_at AS TIMESTAMPTZ) AS source_loaded_at,
    _row_hash
FROM read_csv(
    '{{STAGED_DIR}}/stg_campaign_touchpoints.csv',
    header = true,
    all_varchar = true
);

CREATE OR REPLACE VIEW staging.experiment_exposures AS
SELECT
    experiment_id,
    customer_id,
    variant,
    CAST(eligible_at_assignment AS BOOLEAN) AS eligible_at_assignment,
    CAST(assigned_at AS TIMESTAMPTZ) AS assigned_at,
    CAST(NULLIF(first_exposed_at, '') AS TIMESTAMPTZ) AS first_exposed_at,
    CAST(source_loaded_at AS TIMESTAMPTZ) AS source_loaded_at,
    _row_hash
FROM read_csv(
    '{{STAGED_DIR}}/stg_experiment_exposures.csv',
    header = true,
    all_varchar = true
);

CREATE OR REPLACE VIEW staging.customer_events AS
SELECT
    event_id,
    customer_id,
    session_id,
    event_name,
    channel,
    CAST(event_timestamp AS TIMESTAMPTZ) AS event_timestamp,
    CAST(source_loaded_at AS TIMESTAMPTZ) AS source_loaded_at,
    _row_hash
FROM read_csv('{{STAGED_DIR}}/stg_customer_events.csv', header = true, all_varchar = true);
