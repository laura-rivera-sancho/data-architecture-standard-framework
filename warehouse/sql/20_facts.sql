DROP TABLE IF EXISTS warehouse.fact_order_items;
DROP TABLE IF EXISTS warehouse.fact_orders;
DROP TABLE IF EXISTS warehouse.fact_campaign_touchpoints;
DROP TABLE IF EXISTS warehouse.fact_experiment_exposures;
DROP TABLE IF EXISTS warehouse.fact_customer_events;

CREATE TABLE warehouse.fact_orders (
    order_key BIGINT PRIMARY KEY,
    order_id VARCHAR UNIQUE NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    order_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    order_timestamp TIMESTAMPTZ NOT NULL,
    order_status VARCHAR NOT NULL,
    currency_code VARCHAR NOT NULL,
    gross_amount DECIMAL(18, 2) NOT NULL,
    discount_amount DECIMAL(18, 2) NOT NULL,
    recognized_revenue DECIMAL(18, 2) NOT NULL,
    order_count INTEGER NOT NULL
);

INSERT INTO warehouse.fact_orders
SELECT
    row_number() OVER (ORDER BY orders.order_id) AS order_key,
    orders.order_id,
    COALESCE(customers.customer_key, 0),
    COALESCE(dates.date_key, 0),
    orders.order_timestamp,
    orders.order_status,
    orders.currency_code,
    orders.gross_amount,
    orders.discount_amount,
    CASE
        WHEN orders.order_status = 'completed' THEN orders.gross_amount - orders.discount_amount
        ELSE CAST(0 AS DECIMAL(18, 2))
    END AS recognized_revenue,
    1 AS order_count
FROM staging.orders AS orders
LEFT JOIN warehouse.dim_customer AS customers
    ON orders.customer_id = customers.customer_id
    AND orders.order_timestamp >= customers.valid_from
    AND orders.order_timestamp < customers.valid_to
LEFT JOIN warehouse.dim_date AS dates
    ON CAST(orders.order_timestamp AS DATE) = dates.calendar_date;

CREATE TABLE warehouse.fact_order_items (
    order_item_key BIGINT PRIMARY KEY,
    order_key BIGINT NOT NULL REFERENCES warehouse.fact_orders(order_key),
    order_id VARCHAR NOT NULL,
    line_number INTEGER NOT NULL,
    product_key BIGINT NOT NULL REFERENCES warehouse.dim_product(product_key),
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    order_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(18, 2) NOT NULL,
    line_gross_amount DECIMAL(18, 2) NOT NULL,
    line_discount_amount DECIMAL(18, 2) NOT NULL,
    line_recognized_revenue DECIMAL(18, 2) NOT NULL,
    UNIQUE (order_id, line_number)
);

INSERT INTO warehouse.fact_order_items
SELECT
    row_number() OVER (ORDER BY items.order_id, items.line_number) AS order_item_key,
    orders.order_key,
    items.order_id,
    items.line_number,
    COALESCE(products.product_key, 0),
    orders.customer_key,
    orders.order_date_key,
    items.quantity,
    items.unit_price,
    items.quantity * items.unit_price AS line_gross_amount,
    items.line_discount_amount,
    CASE
        WHEN orders.order_status = 'completed'
            THEN items.quantity * items.unit_price - items.line_discount_amount
        ELSE CAST(0 AS DECIMAL(18, 2))
    END AS line_recognized_revenue
FROM staging.order_items AS items
JOIN warehouse.fact_orders AS orders ON items.order_id = orders.order_id
LEFT JOIN warehouse.dim_product AS products ON items.product_id = products.product_id;

CREATE TABLE warehouse.fact_campaign_touchpoints (
    touchpoint_key BIGINT PRIMARY KEY,
    touchpoint_id VARCHAR UNIQUE NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    campaign_key BIGINT NOT NULL REFERENCES warehouse.dim_campaign(campaign_key),
    channel_key BIGINT NOT NULL REFERENCES warehouse.dim_channel(channel_key),
    touchpoint_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    touchpoint_timestamp TIMESTAMPTZ NOT NULL,
    touchpoint_type VARCHAR NOT NULL,
    attributed_cost DECIMAL(18, 2) NOT NULL,
    delivered_count INTEGER NOT NULL,
    opened_count INTEGER NOT NULL,
    clicked_count INTEGER NOT NULL,
    converted_count INTEGER NOT NULL
);

INSERT INTO warehouse.fact_campaign_touchpoints
SELECT
    row_number() OVER (ORDER BY touchpoints.touchpoint_id),
    touchpoints.touchpoint_id,
    COALESCE(customers.customer_key, 0),
    COALESCE(campaigns.campaign_key, 0),
    COALESCE(channels.channel_key, 0),
    COALESCE(dates.date_key, 0),
    touchpoints.touchpoint_timestamp,
    touchpoints.touchpoint_type,
    touchpoints.attributed_cost,
    CAST(touchpoints.touchpoint_type = 'delivered' AS INTEGER),
    CAST(touchpoints.touchpoint_type = 'opened' AS INTEGER),
    CAST(touchpoints.touchpoint_type = 'clicked' AS INTEGER),
    CAST(touchpoints.touchpoint_type = 'converted' AS INTEGER)
FROM staging.campaign_touchpoints AS touchpoints
LEFT JOIN warehouse.dim_customer AS customers
    ON touchpoints.customer_id = customers.customer_id
    AND touchpoints.touchpoint_timestamp >= customers.valid_from
    AND touchpoints.touchpoint_timestamp < customers.valid_to
LEFT JOIN warehouse.dim_campaign AS campaigns
    ON touchpoints.campaign_id = campaigns.campaign_id
LEFT JOIN warehouse.dim_channel AS channels
    ON touchpoints.channel = channels.channel_code
LEFT JOIN warehouse.dim_date AS dates
    ON CAST(touchpoints.touchpoint_timestamp AS DATE) = dates.calendar_date;

CREATE TABLE warehouse.fact_experiment_exposures (
    exposure_key BIGINT PRIMARY KEY,
    experiment_id VARCHAR NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    assignment_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    variant VARCHAR NOT NULL,
    eligible_at_assignment BOOLEAN NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL,
    first_exposed_at TIMESTAMPTZ,
    was_exposed BOOLEAN NOT NULL,
    UNIQUE (experiment_id, customer_key)
);

INSERT INTO warehouse.fact_experiment_exposures
SELECT
    row_number() OVER (ORDER BY exposures.experiment_id, exposures.customer_id),
    exposures.experiment_id,
    COALESCE(customers.customer_key, 0),
    COALESCE(dates.date_key, 0),
    exposures.variant,
    exposures.eligible_at_assignment,
    exposures.assigned_at,
    exposures.first_exposed_at,
    exposures.first_exposed_at IS NOT NULL
FROM staging.experiment_exposures AS exposures
LEFT JOIN warehouse.dim_customer AS customers
    ON exposures.customer_id = customers.customer_id
    AND exposures.assigned_at >= customers.valid_from
    AND exposures.assigned_at < customers.valid_to
LEFT JOIN warehouse.dim_date AS dates
    ON CAST(exposures.assigned_at AS DATE) = dates.calendar_date;

CREATE TABLE warehouse.fact_customer_events (
    event_key BIGINT PRIMARY KEY,
    event_id VARCHAR UNIQUE NOT NULL,
    customer_key BIGINT NOT NULL REFERENCES warehouse.dim_customer(customer_key),
    channel_key BIGINT NOT NULL REFERENCES warehouse.dim_channel(channel_key),
    event_date_key INTEGER NOT NULL REFERENCES warehouse.dim_date(date_key),
    session_id VARCHAR NOT NULL,
    event_name VARCHAR NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    event_count INTEGER NOT NULL
);

INSERT INTO warehouse.fact_customer_events
SELECT
    row_number() OVER (ORDER BY events.event_id),
    events.event_id,
    COALESCE(customers.customer_key, 0),
    COALESCE(channels.channel_key, 0),
    COALESCE(dates.date_key, 0),
    events.session_id,
    events.event_name,
    events.event_timestamp,
    1
FROM staging.customer_events AS events
LEFT JOIN warehouse.dim_customer AS customers
    ON events.customer_id = customers.customer_id
    AND events.event_timestamp >= customers.valid_from
    AND events.event_timestamp < customers.valid_to
LEFT JOIN warehouse.dim_channel AS channels ON events.channel = channels.channel_code
LEFT JOIN warehouse.dim_date AS dates
    ON CAST(events.event_timestamp AS DATE) = dates.calendar_date;
