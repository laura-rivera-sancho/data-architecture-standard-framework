# Data Architecture Fundamentals

This guide summarizes the concepts, tradeoffs, and interview language behind the Data Architecture Standard Framework. It is designed as a review aid: understand the decision each pattern supports rather than memorizing definitions in isolation.

## What data architecture does

Data architecture defines how data is collected, stored, transformed, governed, secured, and served to consumers. A strong architecture connects technical choices to business outcomes: reliable decisions, reusable definitions, controlled access, recoverable operations, and an acceptable cost of change.

Related roles overlap but emphasize different concerns:

- **Data architect:** target state, domain boundaries, standards, integration patterns, governance, and major tradeoffs.
- **Data engineer:** ingestion, transformation, storage, orchestration, reliability, and performance.
- **Analytics engineer:** tested transformation models, dimensional design, metrics, documentation, and analyst-facing data products.
- **Data modeler:** conceptual, logical, and physical representations of entities, relationships, constraints, and history.
- **Data steward or governance lead:** ownership, definitions, quality expectations, classification, access, and policy compliance.

## Operational and analytical systems

### Online transaction processing

Operational systems support current business processes such as placing an order, updating a customer profile, or recording a payment. They favor fast point lookups and writes, strong transaction guarantees, and normalized models that reduce update anomalies.

### Online analytical processing

Analytical systems support scans, joins, aggregations, history, and comparison across business processes. They favor read efficiency, stable historical meaning, denormalized dimensional models, and column-oriented storage.

Moving operational data into an analytical platform protects production workloads and creates a governed historical view. A warehouse is not simply a copy of application databases; it applies shared identity, business rules, quality controls, and consumer-oriented structures.

## Common analytical platform patterns

| Pattern | Best fit | Main tradeoff |
|---|---|---|
| Data warehouse | Structured, governed reporting and analytics | Strong modeling discipline; less natural for raw unstructured data |
| Data lake | Low-cost storage of raw structured and unstructured data | Flexibility can become poor discoverability and inconsistent quality |
| Lakehouse | Lake storage with warehouse-style transactions, governance, and performance | More platform complexity and product-specific behavior |
| Data mart | A focused product for a defined function or decision | Fast consumer value, but independent marts can duplicate logic |
| Operational data store | Integrated, current operational reporting | Usually limited history and not a replacement for an analytical warehouse |

Architecture is not a maturity contest. Choose the simplest pattern that satisfies volume, latency, governance, interoperability, skills, and cost requirements.

## Layered analytical architecture

A common flow is:

`sources → ingestion/raw → staging → intermediate → warehouse → marts → semantic layer → consumers`

### Sources and contracts

Source contracts declare the interface between a producer and the data platform: grain, keys, schema, semantics, freshness, ownership, classification, and change expectations. Contracts make assumptions visible and testable.

### Raw or landing layer

The landing layer preserves source fidelity and ingestion metadata. It supports replay, audit, and investigation. Access should be limited because raw data may contain sensitive fields and unresolved quality problems.

### Staging layer

Staging models are source-aligned. They rename fields, cast types, standardize formats, deduplicate under an explicit rule, and retain traceability. They should not silently embed consumer-specific business logic.

### Intermediate layer

Intermediate models express reusable cross-source logic such as identity resolution, status normalization, or reusable aggregations. They reduce repeated transformations without becoming undocumented reporting endpoints.

### Dimensional warehouse

The warehouse publishes facts and conformed dimensions at declared grains. It creates a stable analytical core that multiple marts can reuse.

### Data marts

Marts package data for a specific audience and decision, such as customer lifecycle management or campaign performance. A governed mart declares its grain, owner, refresh cadence, measures, dependencies, limitations, and access policy.

### Semantic layer

The semantic layer gives reusable business metrics and dimensions a governed definition. It helps dashboards and analytical tools calculate the same concept consistently, but it does not repair incorrect upstream modeling.

## Grain: the most important modeling decision

Grain states exactly what one row represents. Declare it before choosing columns or measures.

Examples:

- one row per order
- one row per order line
- one row per customer at a daily snapshot
- one row per experiment and assigned variant

Mixing grains creates fanout, duplicated measures, ambiguous keys, and incorrect totals. When two one-to-many sources must feed a customer-level product, aggregate each source to customer grain before joining.

An interview-safe design sequence is:

1. define the business process and decision
2. declare the grain
3. identify dimensions
4. identify facts and measures
5. define keys and history behavior
6. document late-arriving and correction rules
7. add reconciliation and relationship tests

## Facts and dimensions

### Fact tables

Facts record measurable business processes. They usually contain foreign keys to dimensions and numeric measures.

Common fact patterns:

- **Transaction fact:** one row per event, such as an order or payment.
- **Periodic snapshot:** one row per entity per regular interval, such as daily account balance.
- **Accumulating snapshot:** one row updated as a process reaches milestones, such as an order lifecycle.
- **Factless fact:** records that an event or relationship occurred when no numeric measure is needed, such as eligibility or attendance.

Measures may be:

- **Additive:** safe to sum across all dimensions, such as recognized revenue.
- **Semi-additive:** additive across some dimensions but not time, such as account balance.
- **Non-additive:** ratios and percentages that must be recomputed from their components.

### Dimension tables

Dimensions provide descriptive context such as customer, product, campaign, channel, and date.

Useful dimension patterns include:

- **Conformed dimension:** reused consistently across facts and business processes.
- **Role-playing dimension:** one dimension used in different roles, such as order date and delivery date.
- **Degenerate dimension:** a business identifier stored in the fact without a separate dimension, such as an order number.
- **Junk dimension:** combines several low-cardinality flags to avoid many tiny dimensions.
- **Unknown member:** a reserved record used when descriptive context is missing or arrives late.

### Star and snowflake schemas

A star schema keeps dimensions relatively denormalized around a fact table. It is usually easier for users and business-intelligence tools. A snowflake normalizes dimension hierarchies, reducing some redundancy but increasing joins and cognitive load. Use snowflaking when hierarchy reuse, governance, or scale provides a clear benefit.

## Business keys and surrogate keys

A business or natural key comes from the source domain, such as `customer_id`. A surrogate key is generated by the analytical platform.

Surrogate keys help:

- represent multiple historical versions of the same business entity
- isolate warehouse relationships from source-key changes
- integrate multiple source systems
- provide an unknown member for late-arriving references

They do not replace the business key. Both are needed: the business key supports source traceability, while the surrogate key identifies the warehouse version.

## Slowly changing dimensions

Slowly changing dimension patterns define how descriptive attribute changes are stored.

- **Type 0:** retain the original value permanently.
- **Type 1:** overwrite the old value; no attribute history remains.
- **Type 2:** create a new row with a new surrogate key and effective dates; full history is preserved.
- **Type 3:** retain limited previous-state columns; useful only for narrow comparison needs.

Use Type 1 for corrections or attributes whose historical state is not analytically meaningful. Use Type 2 when facts must be interpreted using the attribute value that was valid when the event occurred.

A Type 2 record commonly includes `valid_from`, `valid_to`, `is_current`, and a hash or comparison of tracked attributes. New facts resolve the dimension version whose effective interval contains the event timestamp.

## Late-arriving data and corrections

A late-arriving fact appears after its expected processing window. A late-arriving dimension means a fact references descriptive context that is not yet available.

Professional handling may include:

- load the fact against an unknown dimension member and backfill the key later
- hold the record in quarantine when publication would be unsafe
- use event time for business logic and ingestion time for operational monitoring
- define a correction window and replay strategy
- make reruns idempotent so the same input does not create duplicates

The correct choice depends on the business tolerance for delay, incomplete context, and correction complexity.

## Ingestion and change-data patterns

### Full refresh

Rebuild the complete target from source data. It is simple and reliable for small datasets but can become slow or expensive.

### Incremental load

Process only new or changed records using a timestamp, sequence, partition, or source log. It improves efficiency but requires careful handling of updates, deletes, late data, and replay.

### Change data capture

Change data capture reads inserts, updates, and deletes from a source log or change stream. It can reduce latency and source load, but ordering, schema evolution, duplicate delivery, and recovery must be designed explicitly.

### Batch versus streaming

Batch processing handles bounded groups on a schedule. Streaming processes continuously arriving events. Streaming is justified by a real latency requirement, not simply because it is newer. Many decision processes work well with hourly or daily batches at lower operational complexity.

## Idempotency, backfills, and reproducibility

An idempotent pipeline can process the same input again without changing the correct final result. This is essential for retries and recovery.

Common techniques include deterministic keys, merge/upsert rules, partition replacement, deduplication by event identity, and versioned transformation code. A backfill should declare its data interval, code version, downstream impact, validation plan, and rollback approach.

Reproducibility also requires a fixed analysis or as-of date, pinned dependencies, deterministic synthetic data or inspectable inputs, and manifests that record what ran.

## Data contracts and schema evolution

A useful contract documents:

- owner and escalation path
- row grain and business meaning
- required and optional fields
- data types and formats
- primary and foreign-key expectations
- accepted values and nullability
- freshness and volume expectations
- sensitivity classification
- compatibility and deprecation policy

Changes can be additive, compatible, or breaking. Adding an optional field is often compatible; renaming a field, changing its meaning, narrowing accepted values, or changing grain may be breaking. Breaking changes require versioning, impact analysis, communication, migration time, and validation of downstream consumers.

## Data quality

Data quality is fitness for a declared use, not an abstract score. Important dimensions include:

- **Completeness:** required data are present.
- **Uniqueness:** identifiers match the declared grain.
- **Validity:** types, formats, and accepted values are correct.
- **Consistency:** related representations agree.
- **Accuracy:** data reflect the real-world event or entity.
- **Timeliness:** data arrive within the decision window.
- **Integrity:** relationships and business invariants hold.

Test at multiple boundaries:

1. contract and ingestion checks
2. staging identifiers, casts, freshness, and deduplication
3. warehouse grain, relationships, history, and reconciliation
4. mart coverage, metric invariants, and privacy controls
5. operational freshness, volume, latency, and publication status

A failed critical test should block publication rather than merely produce a dashboard warning.

## Reconciliation and auditability

Reconciliation proves that transformations preserve expected population and value.

Examples include:

- source row counts versus staged accepted plus quarantined rows
- staged orders versus warehouse order facts
- order-header revenue versus allocated order-line revenue
- mart totals versus governed warehouse totals
- known plus unknown dimension references versus total facts

Audit metadata commonly includes source file or system, ingestion timestamp, batch or run identifier, transformation version, and publication status.

## Metric governance and the semantic layer

A governed metric should define:

- business meaning and decision supported
- numerator and denominator
- qualifying population and exclusions
- time grain, time zone, and attribution window
- aggregation behavior
- owner, certification status, and effective date
- upstream lineage and known limitations

Store additive components where possible and calculate ratios at the query grain. Averaging precomputed percentages often produces the wrong answer. Preserve `NULL` for an undefined rate when the denominator is zero rather than silently reporting zero performance.

## Lineage, metadata, and ownership

Lineage connects sources, transformations, data products, metrics, and consumers. It supports impact analysis, incident investigation, trust, and change management.

Technical lineage shows table and column dependencies. Business lineage explains how a source concept becomes a decision metric. Both need ownership: every critical source, product, and metric should name an accountable role and an escalation path.

A data catalog helps consumers discover products, definitions, owners, classifications, freshness, and usage guidance. A catalog is valuable only when metadata remain current and connected to the delivery process.

## Orchestration and dependency management

An orchestrator schedules work, resolves dependencies, tracks state, retries safe failures, and records execution history. Pipelines are commonly represented as directed acyclic graphs.

Good orchestration design includes:

- explicit dependencies rather than timing assumptions
- bounded retries with backoff
- timeouts and failure routing
- idempotent tasks
- parameterized backfills
- separate build, test, and publish states
- notification and ownership rules
- a way to stop or roll back unsafe publication

The orchestrator coordinates reliability; it does not replace validation inside the data models.

## Service levels and observability

Observability should answer whether the data product is available, fresh, complete, correct enough for its use, and performing within expectations.

- **Service-level indicator:** measured signal, such as freshness lag or successful-run rate.
- **Service-level objective:** target for that signal, such as 99% of daily loads published before 08:00.
- **Service-level agreement:** a formal commitment, often with business consequences.

Monitor freshness, volume, schema changes, quality checks, duration, query latency, cost, and downstream publication. Alerts need severity, owner, runbook, and escalation rules; otherwise they become noise.

## Security, privacy, and access

Apply least privilege and expose only the data needed for a declared use.

Common controls include:

- role-based or attribute-based access control
- separate raw, transformation, and consumer roles
- row- and column-level security
- tokenization, hashing, or masking of direct identifiers
- encryption in transit and at rest
- secrets management and credential rotation
- retention and deletion policies
- access logging and periodic reviews
- separation of development, test, and production environments

Hashing is not the same as anonymization. Stable hashes can still allow linkage and may remain personal data. Privacy design also considers purpose limitation, minimization, consent, residency, and the ability to honor deletion or access requests.

## Performance and cost

Optimize only after measuring the workload and preserving correctness.

Typical techniques include:

- partition pruning on common time or domain filters
- clustering, sorting, or indexing on selective access paths
- columnar storage and compression
- incremental materialization
- pre-aggregations or materialized views for repeated queries
- avoiding unnecessary wide scans and many-to-many joins
- workload isolation and concurrency controls
- query-plan inspection and cost monitoring

Partitioning is not free: too many small partitions increase metadata and file-management overhead. Pre-aggregation improves speed but adds freshness and consistency responsibilities.

## Data products and data mesh

A data product is a maintained dataset or service with a defined audience, owner, interface, quality expectations, documentation, and lifecycle. Treating a table as a product changes the question from “Did the pipeline run?” to “Can consumers safely use this for the declared decision?”

Data mesh applies domain-oriented ownership, data-as-a-product, self-service platform capabilities, and federated governance. It can improve scaling across large organizations, but it does not remove the need for shared standards, conformed meaning, or central platform capabilities. It is usually unnecessary for a small team with a manageable central platform.

## Machine Learning and experimentation boundaries

Machine Learning features require point-in-time correctness: every feature must reflect only information available at the prediction cutoff. Joining the latest customer record to historical training examples can leak future information.

Experiment products must preserve assignment, exposure, eligibility, variant, timestamp, and outcome windows. A mart can summarize observed results, but causal interpretation still requires randomization checks, sample-ratio validation, power, uncertainty, and guardrails.

## Architecture tradeoffs interviewers often probe

### Build versus buy

Evaluate strategic differentiation, total cost, integration, portability, operational burden, security, and team skill. Managed services can reduce undifferentiated operations; custom components may be justified for unique requirements.

### Centralization versus domain ownership

Centralization improves consistency and platform leverage but can create bottlenecks. Domain ownership improves context and responsiveness but can fragment definitions. A common balance is domain-owned products on a shared platform with federated standards.

### Normalization versus denormalization

Normalization reduces update anomalies in operational systems. Denormalization reduces joins and improves usability in analytics. Choose according to workload and ownership, not ideology.

### Flexibility versus governance

Raw access speeds exploration but increases privacy and consistency risk. Curated products improve trust but require stewardship. Mature platforms provide both under different access and publication controls.

### Latency versus complexity and cost

Real-time delivery increases operational complexity. Start from the business decision's maximum tolerable delay, then choose the least complex architecture that meets it.

## How to explain this portfolio project in an interview

Use a concise problem–decision–design–control–tradeoff structure:

1. **Problem:** fragmented customer, order, campaign, experiment, and event sources produced inconsistent metrics and duplicated feature logic.
2. **Decision:** create a governed analytical foundation for lifecycle, campaign, experimentation, Machine Learning, and executive use cases.
3. **Design:** versioned source contracts feed source-aligned staging, a dimensional warehouse, six decision-specific marts, and a semantic governance layer.
4. **Controls:** automated tests protect grain, keys, freshness, relationships, financial reconciliation, metric definitions, lineage, and service expectations.
5. **Tradeoff:** DuckDB and synthetic data make the design portable and inspectable; a production deployment would add durable cloud storage, orchestration, enforced access control, alert delivery, and incremental processing.

### Milestone talking points

- **DA1:** contracts turn producer assumptions into governed interfaces; staging standardizes data while preserving source traceability.
- **DA2:** declared grains, conformed dimensions, surrogate keys, Type 2-ready customer history, unknown members, and reconciliation create a defensible warehouse core.
- **DA3:** six marts serve specific audiences and prevent every team from rebuilding joins and metric logic independently.
- **DA4:** metric definitions, lineage, ownership, service levels, runbooks, and change management make the platform operable rather than merely modeled.

## Practice interview questions

### Why use a star schema?

It gives analytical consumers a clear fact-centered model, reduces join complexity, works well with columnar engines and business-intelligence tools, and makes grain and measure behavior easier to govern. I would normalize selectively only when hierarchy reuse or scale justified the extra joins.

### When would you choose Type 1 versus Type 2?

I use Type 1 for corrections or attributes whose historical value is not relevant. I use Type 2 when facts must retain the context that was valid at event time. The choice is per attribute and driven by the analytical question.

### How do you prevent duplicate metrics after joins?

I declare the target grain, validate relationship cardinality, aggregate each one-to-many source before joining to a higher grain, and reconcile component and final totals. I also store additive numerators and denominators rather than averaging rates.

### How would you handle a breaking source-schema change?

The contract check should block unsafe publication. I would identify impacted consumers through lineage, agree on a versioned interface and migration window, update transformations and tests, validate a parallel run, communicate the effective date, and retain a rollback path.

### How do you decide between batch and streaming?

I start with the decision's latency requirement. If hourly or daily data supports the action, batch is simpler and cheaper. I choose streaming only when continuous processing creates measurable value and the team can operate ordering, replay, schema, and monitoring concerns.

### What makes a pipeline production-ready?

Clear ownership, versioned inputs, idempotent processing, automated tests, observable service levels, secure access, bounded retries, backfill and rollback procedures, documented dependencies, cost controls, and a tested incident runbook.

### What would you change for production scale?

I would preserve the demonstrated contracts and model boundaries while selecting managed storage and compute based on workload, adding orchestration, incremental or change-data processing, enforced identity and access management, centralized secrets, alert delivery, environment promotion, durable run history, and cost/performance monitoring.

## Compact glossary

| Term | Practical meaning |
|---|---|
| Grain | What exactly one row represents |
| Fact | A measurable business event or snapshot |
| Dimension | Descriptive context used to analyze facts |
| Conformed dimension | A shared dimension used consistently across facts |
| Surrogate key | Warehouse-generated identifier for a dimension version |
| Slowly changing dimension | Pattern for managing changes to descriptive attributes |
| Data mart | Curated product for a defined audience and decision |
| Semantic layer | Governed interface for reusable metrics and dimensions |
| Data contract | Versioned expectations between producer and consumer |
| Lineage | Trace from sources through transformations to consumers |
| Idempotency | Safe reprocessing without changing the correct final result |
| Change data capture | Capture of source inserts, updates, and deletes |
| SLI / SLO | Measured reliability signal and its target |
| Point-in-time correctness | Features contain only data available at the historical cutoff |
| Fanout | Row multiplication caused by joining mismatched grains |
| Reconciliation | Proof that counts or values balance across transformations |

## Final review checklist

- Can I explain the business problem before the technology?
- Can I state the grain of every important fact and mart?
- Can I explain why surrogate keys and Type 2 history are useful?
- Can I distinguish warehouse, lake, lakehouse, and mart patterns?
- Can I describe how contracts, tests, reconciliation, and lineage work together?
- Can I explain batch, incremental, and change-data choices?
- Can I discuss security, privacy, service levels, recovery, performance, and cost?
- Can I name the limits of the portfolio implementation and a credible production evolution?

Use the linked implementation documents in the repository README to connect each concept to concrete SQL, configuration, tests, evidence, and design decisions.
