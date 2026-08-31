import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from data_architecture.governance import (
    GovernanceValidationError,
    build_governance_report,
    validate_governance,
)
from data_architecture.staging import run_staging_pipeline
from data_architecture.synthetic_data import GenerationConfig, generate_operational_data
from data_architecture.warehouse import build_warehouse

ROOT = Path(__file__).parents[1]
METRICS = ROOT / "semantic" / "metrics.yml"
LINEAGE = ROOT / "semantic" / "lineage.yml"
SERVICES = ROOT / "operations" / "service_levels.yml"


@pytest.fixture(scope="module")
def governed_build(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("governance")
    raw = workspace / "raw"
    staged = workspace / "staged"
    database = workspace / "portfolio.duckdb"
    warehouse_manifest = workspace / "warehouse_manifest.json"
    report_path = workspace / "governance_report.json"
    generate_operational_data(
        raw,
        GenerationConfig(seed=29, customers=25, orders=50, touchpoints=75, events=90),
    )
    run_staging_pipeline(
        raw,
        ROOT / "contracts" / "sources",
        staged,
        datetime(2026, 8, 30, 13, 0, tzinfo=UTC),
    )
    build_warehouse(
        database,
        staged,
        ROOT / "warehouse" / "sql",
        ROOT / "warehouse" / "quality_checks.yml",
        warehouse_manifest,
    )
    report = build_governance_report(
        database,
        warehouse_manifest,
        staged / "staging_manifest.json",
        METRICS,
        LINEAGE,
        SERVICES,
        report_path,
    )
    return report, json.loads(report_path.read_text(encoding="utf-8"))


def test_governance_catalog_is_complete_and_aligned():
    config = validate_governance(METRICS, LINEAGE, SERVICES)

    assert len(config["metrics"]) == 8
    assert len(config["lineage"]) == 6
    assert len(config["services"]) == 6
    assert {product["name"] for product in config["lineage"]} == {
        service["name"] for service in config["services"]
    }


def test_governance_report_executes_metrics_and_service_signals(governed_build):
    report, persisted_report = governed_build

    assert report["status"] == "current"
    assert report["metric_count"] == 8
    assert len(report["metric_results"]) == 8
    assert len(report["product_results"]) == 6
    assert all(result["query_latency_ms"] >= 0 for result in report["metric_results"])
    assert all(result["performance_status"] == "current" for result in report["metric_results"])
    assert all(result["volume_status"] == "current" for result in report["product_results"])
    assert persisted_report == report


def test_owner_mismatch_is_rejected(tmp_path):
    config = yaml.safe_load(SERVICES.read_text(encoding="utf-8"))
    config["products"][0]["owner"] = "wrong-owner@fictional.example"
    invalid_services = tmp_path / "service_levels.yml"
    invalid_services.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(GovernanceValidationError, match="owner mismatch"):
        validate_governance(METRICS, LINEAGE, invalid_services)


def test_unknown_lineage_source_is_rejected(tmp_path):
    config = yaml.safe_load(LINEAGE.read_text(encoding="utf-8"))
    config["products"][0]["upstream"].append("warehouse.missing_table")
    invalid_lineage = tmp_path / "lineage.yml"
    invalid_lineage.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(GovernanceValidationError, match="unknown lineage sources"):
        validate_governance(METRICS, invalid_lineage, SERVICES)
