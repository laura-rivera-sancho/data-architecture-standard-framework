# ADR-002: Use DuckDB for the Portable Reference Warehouse

- **Status:** Accepted
- **Date:** 2026-08-31

## Context

DA2 must demonstrate dimensional modeling, SQL transformations, constraints, reconciliation, and reproducible analytical queries. Reviewers should be able to build the warehouse locally without cloud credentials or a long-running database service.

## Decision

Use DuckDB 1.5.5 as the reference analytical warehouse and execute ordered, version-controlled SQL models through a small Python runner.

DuckDB provides a persistent local database, direct CSV ingestion, analytical SQL, constraints, and a supported Python client while remaining simple to install. The [official Python documentation](https://duckdb.org/docs/stable/clients/python/overview) documents persistent connections and file ingestion; the [official package record](https://pypi.org/project/duckdb/) identifies 1.5.5 as the current stable release selected for this reproducible build.

## Implementation rules

- Keep business transformations in ordered SQL files rather than Python data-frame operations.
- Build into explicit `staging` and `warehouse` schemas.
- Recreate the reference warehouse deterministically from staged inputs.
- Use integer surrogate keys with reserved unknown members.
- Declare fact grain in table names, documentation, and automated uniqueness tests.
- Resolve customer keys using effective-date joins so the fact pattern remains compatible with Type 2 history.
- Keep the generated `.duckdb` database untracked; source contracts, SQL, tests, and evidence are the durable artifacts.

## Consequences

Benefits:

- a reviewer can reproduce the full warehouse locally
- SQL remains inspectable and portable in concept
- continuous integration can validate the whole dimensional model
- persistent output can be queried with standard DuckDB clients

Tradeoffs:

- the reference build does not prove distributed or very-large-scale performance
- surrogate-key assignment is deterministic for a full rebuild, not an incremental sequence service
- cloud-specific identity, orchestration, workload isolation, and cost controls remain deployment-design concerns

## Rejected alternatives

- **SQLite:** highly portable, but less representative of modern analytical workloads and file-native analytics.
- **Cloud-only warehouse:** stronger vendor-specific deployment evidence, but introduces cost, credentials, and reviewer-access barriers.
- **Data-frame-only implementation:** easy to prototype, but weaker evidence for dimensional SQL, declarative transformations, and warehouse review.
