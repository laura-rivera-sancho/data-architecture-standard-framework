# Semantic Metric Catalog

## Purpose

The semantic layer gives business terms one governed definition before they are reused in dashboards, experiments, or Machine Learning analysis. The executable source of truth is [`semantic/metrics.yml`](../semantic/metrics.yml); this page provides a reviewer-friendly summary.

## Governed metrics

| Metric | Definition | Type | Primary dimensions | Owner |
|---|---|---|---|---|
| Recognized revenue | Completed-order gross less discounts; cancelled and refunded orders contribute zero | Sum | Order date, status | Growth Analytics |
| Completed orders | Orders whose operational status is `completed` | Count | Order date | Growth Analytics |
| Average order value | Recognized revenue divided by completed orders | Ratio | Order date | Growth Analytics |
| Known customers | Current, non-unknown customer dimension members | Snapshot count | Country, acquisition channel, consent | Customer Analytics |
| Campaign conversion rate | Converted interactions divided by delivered interactions | Ratio | Campaign, channel | Marketing Analytics |
| Campaign cost per conversion | Attributed campaign cost divided by converted interactions | Ratio | Campaign, channel | Marketing Analytics |
| Experiment conversion rate | Assignments with a completed order within 14 days divided by assignments | Ratio | Experiment, variant | Experimentation Analytics |
| Purchasing customers | Customers with at least one completed order in loaded history | Snapshot count | RFM segment | Customer Analytics |

## Semantic contract

Every metric must declare a stable identifier, business name, description, accountable owner, domain, source, grain behavior, aggregation type, display format, supported dimensions, executable SQL, and a decision-use caveat. Automated validation rejects incomplete or duplicate definitions and unknown source products.

Ratios are always recomputed from their numerator and denominator for the selected population. They are never summed or averaged across pre-aggregated rows. Zero denominators resolve to zero only in the portfolio-wide scalar checks; consumer-facing marts preserve `NULL` where an undefined rate is analytically meaningful.

## Interpretation boundaries

- Recognized revenue is demonstrated in USD and does not yet include taxes, shipping, chargebacks, or currency conversion.
- Campaign metrics describe source-attributed interactions, not incremental causal lift.
- Experiment conversion is descriptive until randomization, sample ratio, power, and uncertainty are validated.
- RFM membership is relative to the loaded customer population and analysis date.
- Metric changes follow the review and versioning process in the [change-management standard](change_management.md).
