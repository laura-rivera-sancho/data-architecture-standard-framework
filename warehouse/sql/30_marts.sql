DROP SCHEMA IF EXISTS marts CASCADE;
CREATE SCHEMA marts;

CREATE TABLE marts.customer_360 AS
WITH order_metrics AS (
    SELECT
        customer_key,
        MIN(order_timestamp) FILTER (WHERE order_status = 'completed') AS first_completed_order_at,
        MAX(order_timestamp) FILTER (WHERE order_status = 'completed') AS last_completed_order_at,
        COUNT(*) AS order_count,
        COUNT(*) FILTER (WHERE order_status = 'completed') AS completed_order_count,
        SUM(gross_amount) AS gross_amount,
        SUM(recognized_revenue) AS recognized_revenue
    FROM warehouse.fact_orders
    GROUP BY customer_key
),
event_metrics AS (
    SELECT
        customer_key,
        MAX(event_timestamp) AS last_event_at,
        SUM(event_count) AS event_count
    FROM warehouse.fact_customer_events
    GROUP BY customer_key
),
campaign_metrics AS (
    SELECT
        customer_key,
        COUNT(DISTINCT campaign_key) AS campaigns_touched,
        SUM(clicked_count) AS clicked_touchpoints,
        SUM(converted_count) AS converted_touchpoints
    FROM warehouse.fact_campaign_touchpoints
    GROUP BY customer_key
),
experiment_metrics AS (
    SELECT
        customer_key,
        COUNT(*) AS experiment_assignments,
        SUM(CAST(was_exposed AS INTEGER)) AS experiment_exposures
    FROM warehouse.fact_experiment_exposures
    GROUP BY customer_key
)
SELECT
    customers.customer_key,
    customers.customer_id,
    customers.acquisition_channel,
    customers.country_code,
    customers.marketing_consent,
    orders.first_completed_order_at,
    orders.last_completed_order_at,
    COALESCE(orders.order_count, 0) AS order_count,
    COALESCE(orders.completed_order_count, 0) AS completed_order_count,
    COALESCE(orders.gross_amount, 0) AS gross_amount,
    COALESCE(orders.recognized_revenue, 0) AS recognized_revenue,
    CASE
        WHEN COALESCE(orders.completed_order_count, 0) = 0 THEN 0
        ELSE orders.recognized_revenue / orders.completed_order_count
    END AS average_order_value,
    events.last_event_at,
    COALESCE(events.event_count, 0) AS event_count,
    COALESCE(campaigns.campaigns_touched, 0) AS campaigns_touched,
    COALESCE(campaigns.clicked_touchpoints, 0) AS clicked_touchpoints,
    COALESCE(campaigns.converted_touchpoints, 0) AS converted_touchpoints,
    COALESCE(experiments.experiment_assignments, 0) AS experiment_assignments,
    COALESCE(experiments.experiment_exposures, 0) AS experiment_exposures
FROM warehouse.dim_customer AS customers
LEFT JOIN order_metrics AS orders USING (customer_key)
LEFT JOIN event_metrics AS events USING (customer_key)
LEFT JOIN campaign_metrics AS campaigns USING (customer_key)
LEFT JOIN experiment_metrics AS experiments USING (customer_key)
WHERE customers.customer_key <> 0 AND customers.is_current;

CREATE TABLE marts.rfm_segments AS
WITH analysis_date AS (
    SELECT MAX(CAST(order_timestamp AS DATE)) + INTERVAL 1 DAY AS as_of_date
    FROM warehouse.fact_orders
    WHERE order_status = 'completed'
),
customer_metrics AS (
    SELECT
        orders.customer_key,
        CAST(analysis_date.as_of_date AS DATE) AS as_of_date,
        date_diff('day', MAX(CAST(orders.order_timestamp AS DATE)), analysis_date.as_of_date) AS recency_days,
        COUNT(*) AS frequency,
        SUM(orders.recognized_revenue) AS monetary_value
    FROM warehouse.fact_orders AS orders
    CROSS JOIN analysis_date
    WHERE orders.order_status = 'completed' AND orders.customer_key <> 0
    GROUP BY orders.customer_key, analysis_date.as_of_date
),
scored AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC, customer_key) AS recency_score,
        NTILE(5) OVER (ORDER BY frequency, customer_key) AS frequency_score,
        NTILE(5) OVER (ORDER BY monetary_value, customer_key) AS monetary_score
    FROM customer_metrics
)
SELECT
    scored.customer_key,
    customers.customer_id,
    scored.as_of_date,
    scored.recency_days,
    scored.frequency,
    scored.monetary_value,
    scored.recency_score,
    scored.frequency_score,
    scored.monetary_score,
    CASE
        WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
        WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal Customers'
        WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New or Potential'
        WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
        WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Hibernating'
        ELSE 'Needs Attention'
    END AS rfm_segment
FROM scored
JOIN warehouse.dim_customer AS customers USING (customer_key);

CREATE TABLE marts.campaign_performance AS
SELECT
    facts.campaign_key,
    campaigns.campaign_id,
    campaigns.campaign_name,
    facts.channel_key,
    channels.channel_code,
    COUNT(*) AS touchpoint_count,
    SUM(facts.delivered_count) AS delivered_count,
    SUM(facts.opened_count) AS opened_count,
    SUM(facts.clicked_count) AS clicked_count,
    SUM(facts.converted_count) AS converted_count,
    SUM(facts.attributed_cost) AS attributed_cost,
    SUM(facts.opened_count) / NULLIF(SUM(facts.delivered_count), 0) AS open_rate,
    SUM(facts.clicked_count) / NULLIF(SUM(facts.delivered_count), 0) AS click_rate,
    SUM(facts.converted_count) / NULLIF(SUM(facts.delivered_count), 0) AS conversion_rate,
    SUM(facts.attributed_cost) / NULLIF(SUM(facts.converted_count), 0) AS cost_per_conversion
FROM warehouse.fact_campaign_touchpoints AS facts
JOIN warehouse.dim_campaign AS campaigns USING (campaign_key)
JOIN warehouse.dim_channel AS channels USING (channel_key)
GROUP BY
    facts.campaign_key,
    campaigns.campaign_id,
    campaigns.campaign_name,
    facts.channel_key,
    channels.channel_code;

CREATE TABLE marts.experiment_results AS
WITH exposure_outcomes AS (
    SELECT
        exposures.exposure_key,
        exposures.experiment_id,
        exposures.variant,
        exposures.eligible_at_assignment,
        exposures.was_exposed,
        MAX(CAST(orders.order_key IS NOT NULL AS INTEGER)) AS converted_within_14_days,
        COALESCE(SUM(orders.recognized_revenue), 0) AS recognized_revenue_within_14_days
    FROM warehouse.fact_experiment_exposures AS exposures
    LEFT JOIN warehouse.fact_orders AS orders
        ON exposures.customer_key = orders.customer_key
        AND orders.order_status = 'completed'
        AND orders.order_timestamp >= exposures.assigned_at
        AND orders.order_timestamp < exposures.assigned_at + INTERVAL 14 DAY
    GROUP BY
        exposures.exposure_key,
        exposures.experiment_id,
        exposures.variant,
        exposures.eligible_at_assignment,
        exposures.was_exposed
)
SELECT
    experiment_id,
    variant,
    COUNT(*) AS assignments,
    SUM(CAST(eligible_at_assignment AS INTEGER)) AS eligible_assignments,
    SUM(CAST(was_exposed AS INTEGER)) AS exposed_assignments,
    SUM(converted_within_14_days) AS converted_assignments,
    SUM(CAST(was_exposed AS INTEGER)) / NULLIF(COUNT(*), 0) AS exposure_rate,
    SUM(converted_within_14_days) / NULLIF(COUNT(*), 0) AS conversion_rate,
    SUM(recognized_revenue_within_14_days) AS recognized_revenue,
    SUM(recognized_revenue_within_14_days) / NULLIF(COUNT(*), 0) AS revenue_per_assignment
FROM exposure_outcomes
GROUP BY experiment_id, variant;

CREATE TABLE marts.ml_features AS
WITH as_of AS (
    SELECT MAX(calendar_date) AS as_of_date
    FROM warehouse.dim_date
    WHERE date_key <> 0
),
event_features AS (
    SELECT
        events.customer_key,
        SUM(events.event_count) FILTER (
            WHERE CAST(events.event_timestamp AS DATE) > as_of.as_of_date - INTERVAL 30 DAY
        ) AS event_count_30d,
        SUM(events.event_count) FILTER (
            WHERE CAST(events.event_timestamp AS DATE) > as_of.as_of_date - INTERVAL 90 DAY
        ) AS event_count_90d
    FROM warehouse.fact_customer_events AS events
    CROSS JOIN as_of
    GROUP BY events.customer_key
),
campaign_features AS (
    SELECT
        touchpoints.customer_key,
        COUNT(*) FILTER (
            WHERE CAST(touchpoints.touchpoint_timestamp AS DATE) > as_of.as_of_date - INTERVAL 90 DAY
        ) AS campaign_touchpoints_90d,
        SUM(touchpoints.clicked_count) FILTER (
            WHERE CAST(touchpoints.touchpoint_timestamp AS DATE) > as_of.as_of_date - INTERVAL 90 DAY
        ) AS campaign_clicks_90d,
        SUM(touchpoints.converted_count) FILTER (
            WHERE CAST(touchpoints.touchpoint_timestamp AS DATE) > as_of.as_of_date - INTERVAL 90 DAY
        ) AS campaign_conversions_90d
    FROM warehouse.fact_campaign_touchpoints AS touchpoints
    CROSS JOIN as_of
    GROUP BY touchpoints.customer_key
)
SELECT
    customer.customer_key,
    customer.customer_id,
    as_of.as_of_date,
    customer.country_code,
    customer.acquisition_channel,
    customer.marketing_consent,
    COALESCE(rfm.recency_days, 9999) AS recency_days,
    COALESCE(rfm.frequency, 0) AS order_frequency,
    COALESCE(rfm.monetary_value, 0) AS monetary_value,
    COALESCE(rfm.recency_score, 0) AS recency_score,
    COALESCE(rfm.frequency_score, 0) AS frequency_score,
    COALESCE(rfm.monetary_score, 0) AS monetary_score,
    COALESCE(rfm.rfm_segment, 'No Purchases') AS rfm_segment,
    COALESCE(events.event_count_30d, 0) AS event_count_30d,
    COALESCE(events.event_count_90d, 0) AS event_count_90d,
    COALESCE(campaigns.campaign_touchpoints_90d, 0) AS campaign_touchpoints_90d,
    COALESCE(campaigns.campaign_clicks_90d, 0) AS campaign_clicks_90d,
    COALESCE(campaigns.campaign_conversions_90d, 0) AS campaign_conversions_90d,
    customer.experiment_assignments,
    customer.experiment_exposures
FROM marts.customer_360 AS customer
CROSS JOIN as_of
LEFT JOIN marts.rfm_segments AS rfm USING (customer_key)
LEFT JOIN event_features AS events USING (customer_key)
LEFT JOIN campaign_features AS campaigns USING (customer_key);

CREATE TABLE marts.executive_growth AS
WITH month_spine AS (
    SELECT DISTINCT date_trunc('month', calendar_date)::DATE AS month_start
    FROM warehouse.dim_date
    WHERE date_key <> 0
),
order_metrics AS (
    SELECT
        date_trunc('month', order_timestamp)::DATE AS month_start,
        COUNT(*) AS order_count,
        COUNT(*) FILTER (WHERE order_status = 'completed') AS completed_order_count,
        COUNT(DISTINCT customer_key) FILTER (WHERE customer_key <> 0) AS active_customers,
        SUM(gross_amount) AS gross_amount,
        SUM(recognized_revenue) AS recognized_revenue
    FROM warehouse.fact_orders
    GROUP BY month_start
),
customer_metrics AS (
    SELECT
        date_trunc('month', valid_from)::DATE AS month_start,
        COUNT(*) AS new_customers
    FROM warehouse.dim_customer
    WHERE customer_key <> 0
    GROUP BY month_start
),
campaign_metrics AS (
    SELECT
        date_trunc('month', touchpoint_timestamp)::DATE AS month_start,
        SUM(attributed_cost) AS campaign_cost,
        SUM(delivered_count) AS delivered_count,
        SUM(clicked_count) AS clicked_count,
        SUM(converted_count) AS converted_count
    FROM warehouse.fact_campaign_touchpoints
    GROUP BY month_start
)
SELECT
    months.month_start,
    CAST(strftime(months.month_start, '%Y%m') AS INTEGER) AS month_key,
    COALESCE(customers.new_customers, 0) AS new_customers,
    COALESCE(orders.active_customers, 0) AS active_customers,
    COALESCE(orders.order_count, 0) AS order_count,
    COALESCE(orders.completed_order_count, 0) AS completed_order_count,
    COALESCE(orders.gross_amount, 0) AS gross_amount,
    COALESCE(orders.recognized_revenue, 0) AS recognized_revenue,
    COALESCE(campaigns.campaign_cost, 0) AS campaign_cost,
    COALESCE(campaigns.delivered_count, 0) AS delivered_count,
    COALESCE(campaigns.clicked_count, 0) AS clicked_count,
    COALESCE(campaigns.converted_count, 0) AS converted_count
FROM month_spine AS months
LEFT JOIN order_metrics AS orders USING (month_start)
LEFT JOIN customer_metrics AS customers USING (month_start)
LEFT JOIN campaign_metrics AS campaigns USING (month_start)
ORDER BY months.month_start;
