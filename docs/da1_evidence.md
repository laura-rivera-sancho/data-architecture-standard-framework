# DA1 Evidence: Source Contracts & Staging

## Decision supported

Can six fictional operational sources be accepted into a governed analytical platform with explicit interfaces, consistent staging behavior, actionable failures, and reproducible evidence?

## Reference run

The deterministic reference run uses seed `20260831`, a fictional source load at `2026-08-30T12:00:00Z`, and a staging run one hour later.

| Source | Input rows | Staged rows | Duplicates removed | Freshness |
|---|---:|---:|---:|---|
| Campaign touchpoints | 2,000 | 2,000 | 0 | Current |
| Customer events | 3,000 | 3,000 | 0 | Current |
| Customers | 250 | 250 | 0 | Current |
| Experiment exposures | 375 | 375 | 0 | Current |
| Order items | 1,995 | 1,995 | 0 | Current |
| Orders | 800 | 800 | 0 | Current |

All staged outputs contain the contracted business fields plus source name, source file, source row number, a deterministic row hash, and the staging timestamp.

## Controls demonstrated

- six version-controlled contracts with declared grain, ownership, keys, freshness, field meaning, nullability, and classification
- deterministic generation of related customer, commerce, marketing, experimentation, and behavioral sources
- referentially valid identifiers across generated sources
- rejection of missing or unexpected columns
- type and nullability enforcement with source file and row context
- primary-key deduplication using the latest source-load timestamp
- runtime freshness classification as current, warning, or error
- an inspectable staging manifest with row counts, duplicate counts, load age, status, and output location
- a documented source-to-staging mapping and failure-response runbook

## Deliberate failure evidence

Automated tests verify that the framework rejects undeclared keys, nullable primary keys, public classification of sensitive fields, invalid freshness thresholds, duplicate field definitions, schema drift, missing raw sources, and invalid contract structures. Separate tests demonstrate warning and error freshness states without depending on the wall-clock date.

## Result and limitation

DA1 meets its defined source-contract and staging acceptance criteria and is ready for review. The implementation is deliberately local and file-based so any reviewer can reproduce it without cloud credentials. It does not yet demonstrate warehouse relationships, slowly changing dimensions, mart-level business rules, or large-scale performance; those belong to DA2–DA4.

## Reproduce

```bash
python -m data_architecture.contracts contracts/sources
python -m data_architecture.synthetic_data data/generated/raw
python -m data_architecture.staging data/generated/raw contracts/sources data/generated/staged --staged-at 2026-08-30T13:00:00Z
pytest --cov
```
