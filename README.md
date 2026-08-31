# Data Architecture Standard Framework

[![Repository quality](https://github.com/laura-rivera-sancho/data-architecture-standard-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/laura-rivera-sancho/data-architecture-standard-framework/actions/workflows/ci.yml)

**A portfolio-ready framework for turning fragmented operational data into governed, tested, and decision-ready analytical data products.**

This repository demonstrates how I design an omnichannel marketing data platform from source contracts through dimensional models, business data marts, semantic definitions, and operational monitoring. The work is intentionally tied to concrete Analytics and Machine Learning use cases: RFM segmentation, marketing experimentation, campaign performance, campaign-response propensity, and executive growth reporting.

All companies, identifiers, and future sample datasets are fictional or synthetic. No employer, client, customer, or confidential data are used.

## Recommended review path

| What to assess | Start here | What it demonstrates |
|---|---|---|
| Portfolio scope | [Roadmap](ROADMAP.md) | Four milestone sequence and completion gates |
| Architecture judgment | [Architecture overview](docs/architecture_overview.md) | Layering, ownership, governance, and downstream consumers |
| Data-contract design | [Customer source contract](contracts/sources/customers.yml) | Grain, keys, freshness, field semantics, and data classification |
| Reusable implementation | [Contract validator](src/data_architecture/contracts.py) | Automated validation of contract structure and governance rules |
| Engineering quality | [Automated tests](tests) | Contract, repository-integrity, and critical-rule checks |
| Design decisions | [ADR-001](docs/decisions/ADR-001-portfolio-platform.md) | Explicit tradeoffs and implementation boundaries |

## Portfolio business case

A fictional omnichannel retailer has customer, transaction, campaign, experiment, and behavioral-event data distributed across operational systems. Teams currently calculate customer value and marketing performance differently, model features are rebuilt for each project, and freshness or ownership failures are discovered manually.

The target platform will provide:

- consistent customer and campaign identities
- auditable facts and conformed dimensions
- trusted marts for RFM, campaigns, experiments, ML features, and executive reporting
- governed metric definitions with owners, lineage, and freshness expectations
- automated quality controls from source contracts through published marts

## Planned architecture

```text
Operational sources
    │
    ▼
Source contracts and ingestion checks
    │
    ▼
Staging models ──► Intermediate identity and business-rule models
    │
    ▼
Dimensional warehouse
    │
    ├──► customer_360 / rfm_segments
    ├──► campaign_performance / experiment_results
    ├──► ml_features
    └──► executive_growth
             │
             ▼
      Governed semantic metrics
```

See the [architecture overview](docs/architecture_overview.md) for layer responsibilities and quality controls.

## Milestones

| Milestone | Status | Outcome |
|---|---|---|
| **DA1 — Source Contracts & Staging** | In progress | Governed inputs, freshness expectations, identifiers, staging conventions, and automated checks |
| **DA2 — Dimensional Warehouse** | Planned | Defensible facts, conformed dimensions, declared grain, history strategy, and business rules |
| **DA3 — Business Data Marts** | Planned | Reusable data products for customer, marketing, experimentation, ML, and executive decisions |
| **DA4 — Semantic Governance & Operations** | Planned | Trusted metrics, lineage, ownership, observability, performance, and change management |

## Repository map

```text
data-architecture-standard-framework/
├── .github/workflows/       # Automated repository-quality checks
├── contracts/
│   ├── schema.yml           # Contract format and governance rules
│   └── sources/             # Version-controlled operational source contracts
├── docs/
│   ├── decisions/           # Architecture decision records
│   └── architecture_overview.md
├── src/data_architecture/   # Reusable validation and modeling utilities
├── tests/                   # Contract and repository-integrity tests
├── ROADMAP.md               # Pillar milestones and acceptance criteria
└── README.md                # Recruiter-facing repository landing page
```

## Quick start

Requirements: Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --requirement requirements-dev.txt
python -m data_architecture.contracts contracts/sources
ruff check .
pytest
```

## Design principles

- Declare grain before defining columns or measures.
- Treat source expectations and business semantics as version-controlled interfaces.
- Separate source-aligned staging from reusable business logic and consumer-facing marts.
- Test identifiers, relationships, accepted values, freshness, and business invariants.
- Make ownership, sensitivity, lineage, and limitations visible to consumers.
- Define metrics once and reuse them consistently.
- Prefer simple, inspectable architecture until scale or service requirements justify complexity.

## Portfolio relationship

This is the Data Warehousing, Data Marts & Data Modeling pillar of the broader [Data & AI Portfolio Roadmap](https://github.com/users/laura-rivera-sancho/projects/2). Its governed marketing data products are designed to support the RFM, experimentation, and campaign-response case studies planned across the Analytics and Machine Learning repositories.

## License and citation

This project is available under the [MIT License](LICENSE). Citation metadata are provided in [CITATION.cff](CITATION.cff).
