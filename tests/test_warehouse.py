import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest

from data_architecture.staging import run_staging_pipeline
from data_architecture.synthetic_data import GenerationConfig, generate_operational_data
from data_architecture.warehouse import (
    WarehouseBuildError,
    build_warehouse,
    execute_models,
    run_quality_checks,
)

ROOT = Path(__file__).parents[1]
SQL = ROOT / "warehouse" / "sql"
QUALITY = ROOT / "warehouse" / "quality_checks.yml"
CONTRACTS = ROOT / "contracts" / "sources"


@pytest.fixture(scope="module")
def warehouse_build(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("warehouse")
    raw = workspace / "raw"
    staged = workspace / "staged"
    database = workspace / "portfolio.duckdb"
    manifest_path = workspace / "warehouse_manifest.json"
    generate_operational_data(
        raw,
        GenerationConfig(seed=19, customers=30, orders=60, touchpoints=80, events=100),
    )
    run_staging_pipeline(
        raw,
        CONTRACTS,
        staged,
        datetime(2026, 8, 30, 13, 0, tzinfo=UTC),
    )
    manifest = build_warehouse(database, staged, SQL, QUALITY, manifest_path)
    return database, manifest, json.loads(manifest_path.read_text(encoding="utf-8"))


def test_build_creates_expected_dimensions_facts_and_manifest(warehouse_build):
    _, manifest, persisted_manifest = warehouse_build

    assert manifest["engine"] == "duckdb"
    assert manifest["engine_version"] == "1.5.5"
    assert len(manifest["table_counts"]) == 16
    assert manifest["table_counts"]["fact_orders"] == 60
    assert manifest["table_counts"]["fact_campaign_touchpoints"] == 80
    assert manifest["table_counts"]["fact_customer_events"] == 100
    assert manifest["table_counts"]["marts.customer_360"] == 30
    assert manifest["table_counts"]["marts.ml_features"] == 30
    assert len(manifest["quality_checks"]) == 22
    assert all(check["passed"] for check in persisted_manifest["quality_checks"])


def test_dimensions_reserve_unknown_members_and_customer_history_columns(warehouse_build):
    database, _, _ = warehouse_build
    with duckdb.connect(str(database), read_only=True) as connection:
        unknown_customers = connection.execute(
            "SELECT COUNT(*) FROM warehouse.dim_customer WHERE customer_key = 0"
        ).fetchone()[0]
        invalid_versions = connection.execute(
            """
            SELECT COUNT(*)
            FROM warehouse.dim_customer
            WHERE customer_key <> 0
              AND (valid_from >= valid_to OR NOT is_current OR attribute_hash IS NULL)
            """
        ).fetchone()[0]
        unknown_products = connection.execute(
            "SELECT COUNT(*) FROM warehouse.dim_product WHERE product_key = 0"
        ).fetchone()[0]

    assert unknown_customers == 1
    assert unknown_products == 1
    assert invalid_versions == 0


def test_fact_grain_and_header_line_reconciliation(warehouse_build):
    database, _, _ = warehouse_build
    with duckdb.connect(str(database), read_only=True) as connection:
        duplicate_orders = connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT order_id FROM warehouse.fact_orders
                GROUP BY order_id HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        duplicate_items = connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT order_id, line_number FROM warehouse.fact_order_items
                GROUP BY order_id, line_number HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        reconciliation_failures = connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT orders.order_id
                FROM warehouse.fact_orders AS orders
                JOIN warehouse.fact_order_items AS items USING (order_key)
                GROUP BY orders.order_id, orders.gross_amount
                HAVING ABS(orders.gross_amount - SUM(items.line_gross_amount)) > 0.01
            )
            """
        ).fetchone()[0]

    assert duplicate_orders == 0
    assert duplicate_items == 0
    assert reconciliation_failures == 0


def test_business_marts_have_declared_grain_and_reconcile(warehouse_build):
    database, _, _ = warehouse_build
    with duckdb.connect(str(database), read_only=True) as connection:
        duplicate_customer_rows = connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT customer_key FROM marts.customer_360
                GROUP BY customer_key HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
        invalid_rfm_scores = connection.execute(
            """
            SELECT COUNT(*) FROM marts.rfm_segments
            WHERE recency_score NOT BETWEEN 1 AND 5
               OR frequency_score NOT BETWEEN 1 AND 5
               OR monetary_score NOT BETWEEN 1 AND 5
            """
        ).fetchone()[0]
        campaign_reconciliation = connection.execute(
            """
            SELECT
                (SELECT SUM(touchpoint_count) FROM marts.campaign_performance),
                (SELECT COUNT(*) FROM warehouse.fact_campaign_touchpoints)
            """
        ).fetchone()
        experiment_reconciliation = connection.execute(
            """
            SELECT
                (SELECT SUM(assignments) FROM marts.experiment_results),
                (SELECT COUNT(*) FROM warehouse.fact_experiment_exposures)
            """
        ).fetchone()

    assert duplicate_customer_rows == 0
    assert invalid_rfm_scores == 0
    assert campaign_reconciliation[0] == campaign_reconciliation[1]
    assert experiment_reconciliation[0] == experiment_reconciliation[1]


def test_ml_features_are_point_in_time_and_target_free(warehouse_build):
    database, _, _ = warehouse_build
    with duckdb.connect(str(database), read_only=True) as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info('marts.ml_features')").fetchall()
        }
        row_count, distinct_customers, distinct_dates = connection.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT customer_key), COUNT(DISTINCT as_of_date)
            FROM marts.ml_features
            """
        ).fetchone()

    assert row_count == distinct_customers == 30
    assert distinct_dates == 1
    assert not any(column.startswith("target_") for column in columns)


def test_late_arriving_customer_uses_unknown_member(tmp_path):
    raw = tmp_path / "raw"
    staged = tmp_path / "staged"
    database = tmp_path / "late_arriving.duckdb"
    generate_operational_data(
        raw,
        GenerationConfig(seed=23, customers=12, orders=15, touchpoints=15, events=15),
    )
    run_staging_pipeline(
        raw,
        CONTRACTS,
        staged,
        datetime(2026, 8, 30, 13, 0, tzinfo=UTC),
    )
    orders_path = staged / "stg_orders.csv"
    with orders_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    late_order_id = rows[0]["order_id"]
    rows[0]["customer_id"] = "C99999"
    with orders_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    manifest = build_warehouse(database, staged, SQL, QUALITY)
    with duckdb.connect(str(database), read_only=True) as connection:
        customer_key = connection.execute(
            "SELECT customer_key FROM warehouse.fact_orders WHERE order_id = ?",
            [late_order_id],
        ).fetchone()[0]

    assert manifest["table_counts"]["fact_orders"] == 15
    assert customer_key == 0


def test_model_execution_requires_sql_files(tmp_path):
    with duckdb.connect() as connection:
        with pytest.raises(WarehouseBuildError, match="No warehouse SQL models"):
            execute_models(connection, tmp_path, tmp_path)


def test_quality_configuration_must_not_be_empty(tmp_path):
    config = tmp_path / "empty.yml"
    config.write_text("checks: []\n", encoding="utf-8")
    with duckdb.connect() as connection:
        with pytest.raises(WarehouseBuildError, match="configuration is empty"):
            run_quality_checks(connection, config)


def test_failed_quality_check_blocks_build(tmp_path):
    config = tmp_path / "failing.yml"
    config.write_text(
        """
checks:
  - name: intentional_failure
    description: Proves failed checks block publication.
    expected_value: 0
    sql: SELECT 1
""".strip()
        + "\n",
        encoding="utf-8",
    )
    with duckdb.connect() as connection:
        with pytest.raises(WarehouseBuildError, match="intentional_failure"):
            run_quality_checks(connection, config)
