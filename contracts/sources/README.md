# Source Contracts

Each YAML file defines one operational input as a version-controlled interface. A valid contract declares source ownership, business grain, primary keys, freshness thresholds, and field-level semantics and classifications.

Run validation from the repository root:

```bash
python -m data_architecture.contracts contracts/sources
```

DA1 includes six governed operational sources: customers, orders, order items, campaign touchpoints, experiment exposures, and customer events. Together they support customer value, experimentation, campaign-performance, and Machine Learning feature use cases.
