# Data Product Operations Runbook

## Service expectations

The executable service-level declarations are in [`operations/service_levels.yml`](../operations/service_levels.yml). All six marts require at least one published row and daily freshness. Freshness warns at 24 hours and errors at 36 hours. Critical products (`customer_360` and `ml_features`) have a two-hour response objective; high-priority products have a four-hour response objective.

Semantic query performance warns at 250 ms and errors at 1,000 ms in the portable reference environment. These are evidence thresholds, not production capacity promises.

## Monitored signals

| Signal | Evidence | Failure meaning |
|---|---|---|
| Source freshness | Staging run manifest and contract thresholds | A required source did not arrive on time |
| Build success | Workflow status | Models or tests could not complete |
| Data volume | Warehouse manifest compared with minimum rows | A published product is empty or unexpectedly absent |
| Data integrity | 22 warehouse and mart checks | Grain, relationships, or reconciliation are broken |
| Semantic validity | Governance validation | A metric, owner, service level, or lineage reference is invalid |
| Query latency | Timed execution of each governed metric | Reference queries exceed declared performance thresholds |

## Incident procedure

1. **Detect and contain:** stop publication when an error-level contract, build, quality, volume, or governance check fails. Do not silently publish the previous result as current.
2. **Classify:** identify the affected products, consumers, severity, first failing layer, and whether confidentiality or financial measures are involved.
3. **Assign:** route source failures to the contract owner and transformation failures to Analytics Engineering; notify each affected product owner.
4. **Diagnose:** reproduce with the retained manifests, failed check, model order, and deterministic sample data. Confirm the last known-good commit.
5. **Recover:** correct the narrowest responsible layer, rebuild from contracts forward, and require all publication checks to pass.
6. **Communicate:** record impact, affected decision windows, workaround, resolution time, and whether downstream refreshes or model scores must be replaced.
7. **Learn:** add a regression test, update the runbook or contract, and document prevention actions.

## Severity guide

- **Critical:** confidentiality risk, materially incorrect executive/ML output, or both critical products unavailable. Respond within two hours.
- **High:** a governed product is unavailable, stale beyond 36 hours, or materially unreconciled. Respond within four hours.
- **Medium:** warning-level freshness or performance degradation without incorrect output. Address in the next working cycle.

## Recovery evidence

Recovery is complete only when the source and warehouse manifests are regenerated, all checks pass, governed metrics execute, affected row counts reconcile, and consumers receive a clear resolution notice.
