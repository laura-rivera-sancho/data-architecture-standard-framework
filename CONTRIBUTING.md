# Contributing

Contributions should strengthen this repository as a reproducible, governed, and decision-focused data architecture reference.

## Ways to contribute

- improve contract, modeling, testing, lineage, or operational guidance
- correct unclear documentation, broken links, or reproducibility problems
- propose a source, dimensional model, mart, or semantic definition
- improve accessibility and reviewer experience

For substantial changes, open a proposal before implementation so the business decision, grain, ownership, and acceptance criteria can be reviewed first.

## Local setup

Use Python 3.11 or 3.12:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --requirement requirements-dev.txt
```

## Quality checks

```bash
python -m data_architecture.contracts contracts/sources
ruff check .
ruff format --check src tests
pytest --cov
```

## Data and privacy

Only fictional or synthetically generated data belongs in this repository. Never submit personal data, confidential business information, credentials, API keys, or employer/client artifacts.

## Change standard

Every model or contract change should document its business purpose, grain, owner, upstream inputs, downstream consumers, tests, classification, operational impact, and migration or rollback considerations.

By contributing, you agree that your contribution will be licensed under the repository's [MIT License](LICENSE).
