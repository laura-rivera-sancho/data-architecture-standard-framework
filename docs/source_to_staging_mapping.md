# Source-to-Staging Mapping

## Standard transformation contract

Every staging model is source-aligned and applies only the controls required to make operational records safe and consistent for downstream modeling.

| Control | Staging behavior | Evidence |
|---|---|---|
| Schema | Reject missing or unexpected source columns | Contract-driven schema-drift check |
| Names | Preserve contract field names | Version-controlled source contract |
| Strings | Trim surrounding whitespace | Normalized staged value |
| Integers | Parse and serialize as base-10 integers | Type-validation failure on invalid input |
| Decimals | Parse with decimal arithmetic and serialize to two places | Stable financial representation |
| Booleans | Normalize accepted true/false representations | Canonical `true` or `false` |
| Dates/timestamps | Parse ISO values and normalize timestamps to UTC | Canonical ISO-8601 output |
| Nullability | Reject empty required fields; preserve allowed nulls | Row-level actionable failure |
| Duplicates | Retain the latest record by contracted load timestamp | Manifest duplicate count |
| Traceability | Add source, file, row number, row hash, and staging timestamp | Five audit columns on every staged row |

## Source mappings

| Raw source | Staged output | Declared grain | Primary downstream models |
|---|---|---|---|
| `customers.csv` | `stg_customers.csv` | One current record per customer | `dim_customer`, `customer_360` |
| `orders.csv` | `stg_orders.csv` | One record per order | `fact_orders`, RFM |
| `order_items.csv` | `stg_order_items.csv` | One product line per order | `fact_order_items` |
| `campaign_touchpoints.csv` | `stg_campaign_touchpoints.csv` | One observed campaign interaction | Campaign performance and attribution |
| `experiment_exposures.csv` | `stg_experiment_exposures.csv` | One customer assignment per experiment | Experiment integrity and results |
| `customer_events.csv` | `stg_customer_events.csv` | One behavioral event | Engagement and ML features |

## Explicit staging boundaries

Staging does not calculate RFM scores, attribute conversions, define experiment outcomes, resolve slowly changing dimensions, or publish executive metrics. Those rules belong in intermediate, warehouse, mart, or semantic layers where their business meaning can be governed and reused.
