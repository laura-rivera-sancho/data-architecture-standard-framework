# Architecture Overview

## Purpose

The platform turns fragmented omnichannel operational data into governed analytical products for marketing decisions. The design prioritizes inspectability, reproducibility, and business clarity over infrastructure complexity.

## Layers and responsibilities

| Layer | Responsibility | Must not do |
|---|---|---|
| Source contracts | Declare interfaces, owners, grain, freshness, semantics, and classification | Hide undocumented source assumptions |
| Staging | Rename, cast, standardize, deduplicate, and retain audit metadata | Encode consumer-specific metrics or joins |
| Intermediate | Resolve identities and express reusable multi-source business rules | Become an undocumented reporting endpoint |
| Warehouse | Publish facts and conformed dimensions at declared grain | Mix grains or silently overwrite history |
| Marts | Serve defined audiences and decisions | Reimplement shared business definitions inconsistently |
| Semantic layer | Govern reusable measures and dimensions | Conceal lineage or metric limitations |

## Domain inputs

| Source | Intended grain | Principal downstream use |
|---|---|---|
| Customers | One current source record per customer | Customer dimension and customer 360 |
| Orders | One record per order | Revenue, purchase behavior, and RFM |
| Order items | One record per product line within an order | Product and order-line analysis |
| Campaign touchpoints | One delivered or observed marketing touchpoint | Attribution and campaign performance |
| Experiment exposures | One assignment/exposure per customer and experiment | Experiment integrity and results |
| Customer events | One behavioral event occurrence | Engagement and ML features |

## Cross-pillar consumers

- **Analytics:** RFM, lifecycle migration, split testing, multivariate testing, and executive dashboards
- **Machine Learning:** campaign-response training features, scoring inputs, and monitoring cohorts
- **Portfolio governance:** consistent metric definitions and inspectable lineage across case studies

## Quality control points

1. Contracts block unknown or structurally invalid inputs.
2. Staging tests protect identifiers, types, accepted values, and freshness.
3. Warehouse tests protect grain, relationships, reconciliation, and history rules.
4. Mart tests protect published business invariants and metric consistency.
5. Executable governance monitors freshness, volume, lineage, ownership, metric validity, and query latency.

## Security and privacy posture

The portfolio uses synthetic data only. The architecture still models professional controls: least-privilege access, field classification, minimal exposure of direct identifiers, documented retention assumptions, and separation between raw inputs and consumer-facing marts.

## Implementation boundary

The implementation uses local, portable tooling so reviewers can reproduce it without a cloud account. A production environment would add orchestration, access enforcement, durable storage, alert delivery, incremental processing, and historical SLO measurement while preserving the demonstrated contracts and publication gates.
