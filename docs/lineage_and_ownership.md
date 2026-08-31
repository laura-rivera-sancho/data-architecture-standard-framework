# Lineage and Ownership

## End-to-end flow

```text
Contracted sources
  ├─ customers ───────────────► dim_customer ──────────┬─► customer_360 ──► CRM
  ├─ orders / order_items ────► order facts ───────────┼─► rfm_segments ──► Retention
  ├─ campaign touchpoints ────► campaign fact ─────────┼─► campaign_performance
  ├─ experiment exposures ────► experiment fact ───────┼─► experiment_results
  └─ customer events ─────────► customer event fact ───┴─► ml_features
       conformed date/customer dimensions ───────────────► executive_growth
```

The machine-readable lineage source is [`semantic/lineage.yml`](../semantic/lineage.yml). Validation permits only known warehouse or mart products and rejects broken upstream references.

## Product accountability

| Product | Accountable owner | Classification | Principal consumers |
|---|---|---|---|
| `customer_360` | Analytics Engineering | Confidential | CRM activation, lifecycle analytics |
| `rfm_segments` | Customer Analytics | Confidential | RFM analysis, retention strategy |
| `campaign_performance` | Marketing Analytics | Internal | Campaign optimization, growth reporting |
| `experiment_results` | Experimentation Analytics | Internal | Split and multivariate testing |
| `ml_features` | Data Science Platform | Confidential | Campaign-response propensity |
| `executive_growth` | Growth Analytics | Confidential | Executive growth dashboard |

## Responsibility model

- The product owner approves meaning, acceptable use, and breaking changes.
- Analytics Engineering owns successful builds, lineage integrity, and publication controls.
- Source owners resolve contract freshness or schema failures.
- Consumers validate that the product grain and caveats fit their decision.
- Data Science owns label construction and point-in-time correctness downstream of `ml_features`.

The portfolio uses fictional role mailboxes to demonstrate assignment without exposing personal or employer information.
