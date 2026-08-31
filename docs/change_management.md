# Data Product Change Management

## Change classes

| Class | Examples | Required treatment |
|---|---|---|
| Patch | Documentation clarification, test strengthening, non-semantic performance improvement | Peer review and passing publication controls |
| Backward-compatible | Additive nullable field, new metric, new mart that does not change existing behavior | Owner approval, lineage/service update, consumer notice |
| Breaking | Grain change, field removal or rename, metric formula change, classification reduction, new required field | Versioned contract, migration plan, parallel validation, explicit consumer approval |

## Review workflow

1. State the business reason, affected products, consumers, and decision impact.
2. Update source contracts, metric definitions, lineage, ownership, and service expectations together.
3. Add or update automated tests before changing publication logic.
4. Demonstrate backward compatibility or declare the change breaking.
5. For breaking changes, publish old and new versions in parallel, provide a comparison and migration deadline, and preserve rollback instructions.
6. Require the accountable product owner to approve meaning and Analytics Engineering to approve operability.
7. Merge only when repository validation succeeds; record the change in commit history and evidence documentation.

## Deprecation and rollback

A deprecated field or metric remains available through the communicated migration window. Consumers receive the replacement definition, grain, effective date, and validation query. Rollback returns to the last known-good commit and rebuilds all downstream layers; it never edits published figures manually.

## Metric-specific controls

A metric formula, eligible population, time window, or attribution rule is a semantic change even when its column name stays the same. Such changes require an example showing old versus new results and a decision-impact statement. Experiment metrics must never be upgraded from descriptive to causal language without the required design and statistical evidence.
