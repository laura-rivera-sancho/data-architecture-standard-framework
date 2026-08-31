# DA4 Evidence — Semantic Governance & Operations

## Review summary

DA4 completes the data-architecture pillar by making business meaning, lineage, accountability, service expectations, and operating procedures explicit and testable. Governance validation runs in the same workflow as contracts, warehouse builds, and the test suite.

## Reference-run evidence

| Control | Result |
|---|---:|
| Governed executable metrics | 8 |
| Published products with lineage | 6 |
| Products with owners and service levels | 6 |
| Warehouse and mart publication checks | 22 passed |
| Fastest semantic query | 1.101 ms |
| Slowest semantic query | 44.227 ms |
| Performance warning threshold | 250 ms |
| Overall operational status | Current |

The reference run used seed `42`, the same 250-customer dataset documented in DA3. All products met minimum volume and freshness signals. Exact timing is environment-dependent; the executable report records every run rather than treating these sample timings as a production guarantee.

## Failure controls demonstrated

- Missing metric fields and duplicate identifiers are rejected.
- Unknown lineage sources are rejected.
- Lineage and service-level product lists must match.
- Ownership must agree across lineage and service declarations.
- Freshness warning thresholds must precede error thresholds.
- Empty published products fail their volume expectation.
- Metric query latency is classified against warning and error thresholds.
- Governance validation is part of GitHub Actions and blocks publication on failure.

## Supporting review path

1. [Metric catalog](semantic_metric_catalog.md)
2. [Lineage and ownership](lineage_and_ownership.md)
3. [Operations runbook](operations_runbook.md)
4. [Change-management standard](change_management.md)
5. [Stakeholder architecture readout](stakeholder_readout.md)

## Completion boundary

DA4 demonstrates an executable local control plane, not a production monitoring service. Alert delivery, access enforcement, orchestration history, and long-running SLO measurement require a deployed environment and are documented as production evolution rather than simulated here.
