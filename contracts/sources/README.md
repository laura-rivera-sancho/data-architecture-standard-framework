# Source Contracts

Each YAML file defines one operational input as a version-controlled interface. A valid contract declares source ownership, business grain, primary keys, freshness thresholds, and field-level semantics and classifications.

Run validation from the repository root:

```bash
python -m data_architecture.contracts contracts/sources
```

The initial customer and order contracts establish the standard. DA1 will add order items, campaign touchpoints, experiment exposures, and customer events before staging implementation begins.
