# ADR-001: Build a Portable Marketing Analytics Reference Platform

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

The portfolio must demonstrate professional data-architecture judgment while remaining inexpensive, reproducible, and reviewable by someone without access to a specific cloud warehouse.

## Decision

Build the reference implementation around an omnichannel marketing domain and use portable local execution for the primary evidence. Separate contracts, staging, warehouse, marts, and semantic definitions so the design can later be mapped to managed warehouse services without changing its business grain or governance rules.

## Consequences

Benefits:

- reviewers can run the project locally
- architecture decisions remain visible rather than hidden behind managed services
- the same governed data supports multiple Analytics and ML portfolio cases
- testing can run in continuous integration without cloud credentials

Tradeoffs:

- local execution will not prove very-large-scale performance
- cloud-specific security, orchestration, and cost controls will initially be design evidence rather than deployed infrastructure
- a later decision record must select the concrete transformation engine and local analytical database

## Rejected alternatives

- **Cloud-only implementation:** stronger vendor-specific evidence, but creates credentials, cost, and reviewer-access barriers.
- **Independent datasets for every case study:** faster for isolated demos, but fails to demonstrate governed reuse and cross-domain consistency.
