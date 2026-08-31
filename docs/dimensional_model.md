# Dimensional Warehouse Model

## Purpose

The DA2 warehouse creates a governed dimensional core for customer, commerce, campaign, experimentation, and behavioral analysis. Each fact declares one stable grain and resolves reusable descriptive context through conformed dimensions.

## Conformed dimensions

| Dimension | Business key | Surrogate key | History strategy | Primary consumers |
|---|---|---|---|---|
| `dim_customer` | `customer_id` + `valid_from` | `customer_key` | Type 2-ready effective dating for channel, country, and consent | All customer-linked facts, RFM, ML features |
| `dim_product` | `product_id` | `product_key` | Type 1 in the reference build | Order-item analysis |
| `dim_campaign` | `campaign_id` | `campaign_key` | Type 1 until a campaign master source exists | Campaign performance |
| `dim_channel` | `channel_code` | `channel_key` | Governed conformed mapping | Campaign, event, and acquisition analysis |
| `dim_date` | `calendar_date` | `date_key` (`YYYYMMDD`) | Static calendar | Every dated fact |

Every dimension reserves surrogate key `0` for an unknown member. Facts use that member when descriptive context arrives late, preserving fact grain and row-count reconciliation until the relevant dimension is available.

## Fact tables

| Fact | Declared grain | Primary key | Main additive measures |
|---|---|---|---|
| `fact_orders` | One row per order | `order_key`; unique `order_id` | Gross, discount, recognized revenue, order count |
| `fact_order_items` | One row per order and line number | `order_item_key`; unique order/line | Quantity, line gross, discount, recognized revenue |
| `fact_campaign_touchpoints` | One row per observed campaign interaction | `touchpoint_key`; unique `touchpoint_id` | Cost and interaction-type counts |
| `fact_experiment_exposures` | One row per experiment and customer assignment | `exposure_key`; unique experiment/customer | Eligibility and exposure indicators |
| `fact_customer_events` | One row per behavioral event | `event_key`; unique `event_id` | Event count |

## Customer history strategy

The initial full snapshot creates one current customer version with `valid_from`, `valid_to`, `is_current`, and a hash of tracked attributes. Facts resolve the customer surrogate key through the event timestamp and the effective interval. A future incremental load can therefore expire the previous version and insert a new version without changing fact-table logic.

Tracked Type 2 attributes:

- acquisition channel
- country code
- marketing consent

The synthetic email hash is retained for controlled identity demonstrations but excluded from the Type 2 attribute hash because it is not intended as a behavioral segmentation attribute.

## Late-arriving data

Unmatched customer, product, campaign, channel, or date references resolve to the corresponding unknown member rather than dropping the fact. Automated reconciliation requires fact row counts to match their staged sources. A later backfill can update the surrogate key after the missing dimension member is available.

## Financial rules

- Order gross is the sum of quantity multiplied by unit price across its lines.
- Discounts are allocated to lines and reconcile with the order-header discount.
- Recognized revenue is gross minus discount for completed orders.
- Cancelled and refunded orders retain operational amounts but report zero recognized revenue.

## Build order

1. Create typed source-aligned staging views.
2. Build the calendar and conformed dimensions.
3. Build order facts, followed by marketing, experiment, and event facts.
4. Execute declared grain, relationship, reconciliation, and business-rule checks.
5. Write a manifest containing engine version, model files, table counts, and check results.
