# DA3 Evidence — Business Data Marts

## Review summary

DA3 turns the governed warehouse into six reusable decision products for customer strategy, marketing performance, experimentation, Machine Learning, and executive growth. The implementation declares audience, decision, grain, cadence, ownership, upstream dependencies, measure rules, and limitations in the [mart catalog](mart_catalog.md).

## Implemented products

| Mart | Result demonstrated |
|---|---|
| `customer_360` | Fanout-safe customer activity and value profile |
| `rfm_segments` | Deterministic recency, frequency, monetary scores and action-oriented segments |
| `campaign_performance` | Campaign-channel volume, rates, cost, and cost-per-conversion |
| `experiment_results` | Variant-level assignment, exposure, 14-day conversion, and revenue summaries |
| `ml_features` | Target-free point-in-time feature snapshot with explicit leakage boundary |
| `executive_growth` | Reconciled monthly customer, commerce, and campaign measures |

## Reference run

The published reference run uses seed `42` with 250 customers, 800 orders, 2,000 campaign touchpoints, and 3,000 behavioral events. The same build command used by automated validation produced the following inspectable outputs.

| Data product | Reference rows |
|---|---:|
| `customer_360` | 250 |
| `rfm_segments` | 236 |
| `campaign_performance` | 48 |
| `experiment_results` | 9 |
| `ml_features` | 250 |
| `executive_growth` | 8 |

## Automated evidence

- Sixteen warehouse and mart data products are materialized by one reproducible command.
- Twenty-two publication checks cover warehouse integrity plus mart grain, coverage, score bounds, and source reconciliation.
- Campaign counts and cost reconcile to campaign touchpoint facts.
- Experiment assignments reconcile to exposure facts.
- Executive recognized revenue reconciles to order facts.
- The feature mart contains one customer per as-of date and intentionally excludes target labels.

## Review cautions

- Experiment summaries are descriptive, not causal claims.
- RFM quintiles are relative to the loaded customer population and may require business calibration in production.
- Undefined rates remain `NULL` when their denominators are zero.
- Full-refresh tables favor inspectability for this portfolio implementation; production materialization strategy depends on volume and service-level objectives.
