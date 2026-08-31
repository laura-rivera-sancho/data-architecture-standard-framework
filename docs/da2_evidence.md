# DA2 Evidence: Dimensional Warehouse

## Decision supported

Can the six governed operational sources be transformed into a reproducible dimensional warehouse with explicit grain, conformed dimensions, customer-history readiness, late-arriving-data controls, and reconciled financial measures?

## Reference implementation

- **Engine:** DuckDB 1.5.5
- **Model pattern:** ordered, version-controlled SQL executed into a persistent local database
- **Schemas:** `staging` and `warehouse`
- **Dimensions:** 5
- **Facts:** 5
- **Automated warehouse checks:** 12

## Reference build output

| Table | Rows | Interpretation |
|---|---:|---|
| `dim_date` | 242 | Complete analytical date range plus unknown member |
| `dim_customer` | 251 | 250 fictional customers plus unknown member |
| `dim_product` | 81 | 80 observed products plus unknown member |
| `dim_campaign` | 13 | 12 campaigns plus unknown member |
| `dim_channel` | 12 | 11 conformed channels plus unknown member |
| `fact_orders` | 800 | One row per staged order |
| `fact_order_items` | 1,995 | One row per staged order line |
| `fact_campaign_touchpoints` | 2,000 | One row per staged interaction |
| `fact_experiment_exposures` | 375 | One row per staged experiment assignment |
| `fact_customer_events` | 3,000 | One row per staged behavioral event |

## Quality evidence

All 12 warehouse checks pass:

- customer business-version grain and one-current-version rules
- order and order-line fact grain
- customer, date, product, campaign, and channel relationships
- order-header to order-line gross reconciliation
- zero recognized revenue for cancelled and refunded orders
- positive order-item quantities
- staged-source to fact row-count reconciliation

A dedicated automated scenario replaces an order's customer with an unavailable business key. The order remains in the fact table and resolves to customer key `0`, demonstrating the late-arriving-dimension control without silently losing the event.

## Result and limitation

DA2 meets the defined dimensional-model acceptance criteria and is ready for review. The build demonstrates a reliable local analytical warehouse, not distributed-scale performance or cloud-specific workload isolation. Product and campaign attributes are intentionally limited because the current operational scope has no product-master or campaign-master source; that limitation is explicit rather than filled with unsupported detail.

## Reproduce

```bash
python -m data_architecture.synthetic_data data/generated/raw
python -m data_architecture.staging data/generated/raw contracts/sources data/generated/staged --staged-at 2026-08-30T13:00:00Z
python -m data_architecture.warehouse data/generated/portfolio.duckdb data/generated/staged --manifest data/generated/warehouse_manifest.json
pytest --cov
```
