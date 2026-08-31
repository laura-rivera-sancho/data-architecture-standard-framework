# Business Data Mart Catalog

## Purpose

DA3 publishes six governed, role-oriented data products from the dimensional warehouse. Each mart answers a defined decision question at a declared grain, so consumers do not need to reconstruct joins or business logic independently.

## Published marts

| Mart | Primary audience | Decision supported | Declared grain | Refresh | Owner |
|---|---|---|---|---|---|
| `customer_360` | CRM and lifecycle marketing | Which customers should receive a given engagement strategy? | One row per current, known customer | Daily after warehouse completion | Analytics Engineering |
| `rfm_segments` | Retention and growth teams | Which value and engagement segment should each purchasing customer enter? | One row per customer with a completed order, at one analysis date | Daily | Customer Analytics |
| `campaign_performance` | Marketing and channel owners | Which campaign-channel combinations are generating engagement and conversions efficiently? | One row per campaign and channel | Daily | Marketing Analytics |
| `experiment_results` | Experiment owners and analysts | How did assigned variants differ on observed 14-day outcomes? | One row per experiment and assigned variant | Daily while an experiment is active | Experimentation Analytics |
| `ml_features` | Data Science and ML Engineering | Which governed, point-in-time customer features are ready for model development? | One row per customer at one as-of date | Per model-training snapshot | Data Science Platform |
| `executive_growth` | Growth leadership | How are customer acquisition, revenue, activity, and campaign outcomes changing by month? | One row per calendar month | Daily; reviewed monthly | Growth Analytics |

## Measure definitions and dependencies

### `customer_360`

Combines current customer attributes with separately aggregated order, event, campaign, and experiment measures. This avoids fanout when multiple one-to-many activities exist for the same customer. Average order value uses recognized revenue divided by completed orders.

Upstream dependencies: `dim_customer`, `fact_orders`, `fact_customer_events`, `fact_campaign_touchpoints`, and `fact_experiment_exposures`.

### `rfm_segments`

Recency is the number of days since the most recent completed order. Frequency is completed-order count, and monetary value is recognized revenue. Quintile scores run from 1 (lowest) to 5 (highest); a deterministic customer-key tie breaker makes repeat runs stable. The as-of date is one day after the latest completed order in the loaded dataset.

Upstream dependencies: `fact_orders` and `dim_customer`.

### `campaign_performance`

Interaction counts and attributed cost are additive. Open, click, and conversion rates divide the respective interaction count by delivered count; cost per conversion divides attributed cost by conversions. A zero denominator produces `NULL`, preserving the distinction between zero performance and an undefined rate.

Upstream dependencies: `fact_campaign_touchpoints`, `dim_campaign`, and `dim_channel`.

### `experiment_results`

An assignment is considered converted when the assigned customer completes at least one order within 14 days after assignment. Revenue includes completed-order recognized revenue within that same window. Results are observational summaries by assigned variant and must not be treated as causal estimates without validating randomization, sample ratio, power, and statistical uncertainty.

Upstream dependencies: `fact_experiment_exposures` and `fact_orders`.

### `ml_features`

Publishes customer attributes, RFM measures and scores, recent 30/90-day behavior, recent 90-day campaign engagement, and experiment activity at one declared as-of date. It intentionally contains no target label. Model-specific pipelines must create labels after the feature cutoff and preserve point-in-time joins to avoid leakage.

Upstream dependencies: `customer_360`, `rfm_segments`, `fact_customer_events`, `fact_campaign_touchpoints`, and `dim_date`.

### `executive_growth`

Publishes monthly new customers, active customers, order volume, gross amount, recognized revenue, marketing cost, and interaction outcomes. The calendar spine preserves months with no activity, and separately aggregated inputs prevent cross-domain fanout.

Upstream dependencies: `dim_date`, `dim_customer`, `fact_orders`, and `fact_campaign_touchpoints`.

## Publication controls

- Grain, coverage, and reconciliation checks execute after every build.
- A failed check stops publication and prevents the evidence manifest from being written.
- Customer email hashes and source-level identifiers are excluded unless the declared use requires them.
- Rates retain `NULL` when denominators are zero rather than silently reporting zero.
- Current marts are full-refresh reference models; incremental materialization is deferred until operational scale requires it.

## Known limitations

- Synthetic data demonstrate engineering behavior, not real commercial performance.
- Campaign conversion events are source-reported and are not a multi-touch attribution model.
- Experiment results omit confidence intervals and causal diagnostics by design; those belong in the Analytics experimentation project.
- The ML feature table demonstrates feature governance but is not yet a model-training dataset.
- Time windows use the maximum loaded date, not wall-clock time, so reference runs remain reproducible.
