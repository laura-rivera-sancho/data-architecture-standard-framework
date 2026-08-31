# Data Architecture Pillar Roadmap

This repository delivers the Data Warehousing, Data Marts & Data Modeling pillar of the broader Data & AI portfolio. The business case is an omnichannel marketing platform that provides trusted data for customer analytics, experimentation, campaign optimization, Machine Learning, and executive reporting.

## Completion standard

A milestone is complete only when it includes documented business purpose and grain, reproducible implementation, automated tests, ownership and classification, source-to-target lineage, operational considerations, and a recruiter-friendly result preview.

## DA1 — Source Contracts & Staging

**Status:** Complete

**Outcome:** Operational inputs become explicit, version-controlled interfaces before downstream modeling begins.

Deliverables:

- [x] source contracts for customers, orders, order items, campaign touchpoints, experiment exposures, and customer events
- [x] declared owner, grain, primary keys, freshness thresholds, field semantics, nullability, and sensitivity classifications
- [x] automated structural and governance validation
- [x] staging naming, typing, deduplication, and audit-column conventions
- [x] deterministic synthetic source fixtures for development and testing
- [x] a source-to-staging mapping and failure-handling runbook

Acceptance criteria:

- every primary-key field exists and is non-nullable
- field names are unique and supported types are explicit
- freshness warning thresholds precede error thresholds
- sensitive fields have a non-public classification
- validation failures are actionable and block publication
- staging models preserve source traceability without embedding consumer-specific business logic

## DA2 — Dimensional Warehouse

**Status:** Complete

**Outcome:** Reusable facts and conformed dimensions provide stable analytical grain and business meaning.

Planned facts:

- `fact_orders`
- `fact_order_items`
- `fact_campaign_touchpoints`
- `fact_experiment_exposures`
- `fact_customer_events`

Planned conformed dimensions:

- `dim_customer`
- `dim_product`
- `dim_campaign`
- `dim_channel`
- `dim_date`

Completed evidence:

- [x] declared fact grain and deterministic integer surrogate keys
- [x] conformed customer, product, campaign, channel, and date dimensions
- [x] customer Type 2 history columns and effective-date fact lookup
- [x] reserved unknown members and a tested late-arriving-dimension path
- [x] primary, unique, not-null, and foreign-key constraints
- [x] relationship, grain, financial-rule, and source-to-fact reconciliation checks
- [x] reproducible DuckDB build with inspectable SQL and an evidence manifest
- [x] documented business rules, architecture tradeoffs, and limitations

## DA3 — Business Data Marts

**Status:** Complete

**Outcome:** Role-oriented analytical products answer defined business questions without repeated metric reconstruction.

Published marts:

- `customer_360`
- `rfm_segments`
- `campaign_performance`
- `experiment_results`
- `ml_features`
- `executive_growth`

Each mart must declare its audience, decision, grain, dimensions, measures, update cadence, owner, upstream dependencies, and limitations.

Completed evidence:

- [x] fanout-safe `customer_360` with reconciled customer coverage
- [x] deterministic RFM measures, quintile scores, and action-oriented segments
- [x] campaign-channel counts, rates, cost, and cost-per-conversion
- [x] descriptive experiment outcomes within a declared 14-day window
- [x] target-free, point-in-time ML feature snapshot with leakage guidance
- [x] monthly executive growth product with a complete calendar spine
- [x] mart catalog covering audience, decision, grain, cadence, owner, dependencies, measures, and limitations
- [x] automated mart grain, score-bound, coverage, and financial reconciliation checks

## DA4 — Semantic Governance & Operations

**Status:** In review

**Outcome:** Consumers can discover, trust, operate, and safely change published analytical data products.

Completed evidence:

- [x] eight executable metric definitions with grain, source, aggregation behavior, owner, and caveat
- [x] machine-readable lineage for all six published data products
- [x] aligned ownership, classification, priority, freshness, volume, and incident-response expectations
- [x] automated rejection of incomplete metrics, broken lineage, owner drift, and invalid thresholds
- [x] operational report covering source freshness, product volume, and semantic-query latency
- [x] incident response and recovery runbook
- [x] backward-compatible, breaking-change, deprecation, and rollback procedures
- [x] final stakeholder architecture readout and documented production-evolution boundary

## Delivery order

1. Define and validate source contracts.
2. Generate deterministic synthetic operational data.
3. Implement source-aligned staging models.
4. Build dimensions and facts in dependency order.
5. Publish customer and marketing marts.
6. Add ML and executive products.
7. Establish semantic metrics, observability, and change controls.
8. Complete the technical, analytical, communication, and portfolio review gates.

Dates remain intentionally unassigned until delivery cadence is agreed.
