import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from data_architecture.staging import (
    StagingValidationError,
    run_staging_pipeline,
    stage_source,
)
from data_architecture.synthetic_data import GenerationConfig, generate_operational_data

ROOT = Path(__file__).parents[1]
CONTRACTS = ROOT / "contracts" / "sources"
STAGED_AT = datetime(2026, 8, 30, 13, 0, tzinfo=UTC)


def _rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_pipeline_stages_every_contracted_source(tmp_path):
    raw = tmp_path / "raw"
    staged = tmp_path / "staged"
    generate_operational_data(
        raw,
        GenerationConfig(seed=11, customers=20, orders=30, touchpoints=40, events=50),
    )

    results = run_staging_pipeline(raw, CONTRACTS, staged, STAGED_AT)

    assert len(results) == 6
    assert all(result.input_rows == result.output_rows for result in results)
    assert all(result.freshness_status == "current" for result in results)
    assert {path.name for path in staged.glob("stg_*.csv")} == {
        f"stg_{result.source}.csv" for result in results
    }
    customer_row = _rows(staged / "stg_customers.csv")[0]
    assert customer_row["marketing_consent"] in {"true", "false"}
    assert customer_row["_source_name"] == "customers"
    assert customer_row["_staged_at"] == "2026-08-30T13:00:00Z"
    assert len(customer_row["_row_hash"]) == 64

    manifest = json.loads((staged / "staging_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["sources"]) == 6


def test_staging_deduplicates_by_latest_load_timestamp(tmp_path):
    raw_dir = tmp_path / "raw"
    paths = generate_operational_data(
        raw_dir,
        GenerationConfig(seed=3, customers=10, orders=10, touchpoints=10, events=10),
    )
    rows = _rows(paths["customers"])
    duplicate = dict(rows[0])
    duplicate["acquisition_channel"] = " partner "
    duplicate["source_loaded_at"] = "2026-08-30T12:30:00Z"
    rows.append(duplicate)
    with paths["customers"].open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = stage_source(
        paths["customers"],
        CONTRACTS / "customers.yml",
        tmp_path / "stg_customers.csv",
        STAGED_AT,
    )

    staged_rows = _rows(tmp_path / "stg_customers.csv")
    retained = next(row for row in staged_rows if row["customer_id"] == duplicate["customer_id"])
    assert result.duplicate_rows_removed == 1
    assert retained["acquisition_channel"] == "partner"
    assert retained["source_loaded_at"] == "2026-08-30T12:30:00Z"


def test_staging_reports_warning_and_error_freshness(tmp_path):
    raw_dir = tmp_path / "raw"
    paths = generate_operational_data(
        raw_dir,
        GenerationConfig(seed=5, customers=10, orders=10, touchpoints=10, events=10),
    )

    customer_result = stage_source(
        paths["customers"],
        CONTRACTS / "customers.yml",
        tmp_path / "stg_customers.csv",
        datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
    )
    order_result = stage_source(
        paths["orders"],
        CONTRACTS / "orders.yml",
        tmp_path / "stg_orders.csv",
        datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
    )

    assert customer_result.freshness_status == "warning"
    assert order_result.freshness_status == "error"
    assert customer_result.freshness_age_hours == 24.0


def test_staging_rejects_schema_drift(tmp_path):
    raw = tmp_path / "customers.csv"
    raw.write_text("customer_id,unexpected\nC00001,value\n", encoding="utf-8")

    with pytest.raises(StagingValidationError, match="schema drift"):
        stage_source(raw, CONTRACTS / "customers.yml", tmp_path / "staged.csv", STAGED_AT)


def test_pipeline_requires_every_raw_source(tmp_path):
    with pytest.raises(StagingValidationError, match="Missing raw source file"):
        run_staging_pipeline(tmp_path, CONTRACTS, tmp_path / "staged", STAGED_AT)
