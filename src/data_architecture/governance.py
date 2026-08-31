"""Validate semantic governance and produce operational evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from time import perf_counter
from typing import Any

import duckdb
import yaml


class GovernanceValidationError(ValueError):
    """Raised when governance declarations or operational controls are invalid."""


@dataclass(frozen=True)
class MetricResult:
    metric_id: str
    value: int | float | str
    query_latency_ms: float
    performance_status: str


REQUIRED_METRIC_FIELDS = {
    "id",
    "name",
    "description",
    "owner",
    "domain",
    "source",
    "grain",
    "type",
    "format",
    "dimensions",
    "sql",
    "caveat",
}
REQUIRED_LINEAGE_FIELDS = {"name", "owner", "classification", "upstream", "consumers"}
REQUIRED_SERVICE_FIELDS = {
    "name",
    "priority",
    "owner",
    "minimum_rows",
    "freshness_warning_hours",
    "freshness_error_hours",
    "incident_response_hours",
}


def _load_yaml(path: str | Path) -> dict[str, Any]:
    content = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(content, dict) or content.get("version") != 1:
        raise GovernanceValidationError(f"'{path}' must declare governance version 1")
    return content


def _validate_unique(items: list[dict[str, Any]], key: str, label: str) -> None:
    values = [item.get(key) for item in items]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise GovernanceValidationError(f"duplicate {label}: {', '.join(duplicates)}")


def validate_governance(
    metrics_path: str | Path,
    lineage_path: str | Path,
    service_levels_path: str | Path,
) -> dict[str, Any]:
    """Validate catalog completeness, ownership alignment, and lineage references."""

    metric_config = _load_yaml(metrics_path)
    lineage_config = _load_yaml(lineage_path)
    service_config = _load_yaml(service_levels_path)
    metrics = metric_config.get("metrics", [])
    products = lineage_config.get("products", [])
    services = service_config.get("products", [])
    if not metrics or not products or not services:
        raise GovernanceValidationError(
            "metrics, lineage products, and service levels cannot be empty"
        )

    for label, items, required in (
        ("metric", metrics, REQUIRED_METRIC_FIELDS),
        ("lineage product", products, REQUIRED_LINEAGE_FIELDS),
        ("service level", services, REQUIRED_SERVICE_FIELDS),
    ):
        for index, item in enumerate(items, start=1):
            missing = sorted(required - set(item))
            if missing:
                raise GovernanceValidationError(
                    f"{label} {index} is missing required fields: {', '.join(missing)}"
                )

    _validate_unique(metrics, "id", "metric ids")
    _validate_unique(products, "name", "lineage products")
    _validate_unique(services, "name", "service-level products")

    product_names = {product["name"] for product in products}
    service_names = {service["name"] for service in services}
    if product_names != service_names:
        raise GovernanceValidationError("lineage and service-level products must match exactly")

    known_sources = product_names | {
        "warehouse.dim_date",
        "warehouse.dim_customer",
        "warehouse.dim_product",
        "warehouse.dim_campaign",
        "warehouse.dim_channel",
        "warehouse.fact_orders",
        "warehouse.fact_order_items",
        "warehouse.fact_campaign_touchpoints",
        "warehouse.fact_experiment_exposures",
        "warehouse.fact_customer_events",
    }
    invalid_sources = sorted(
        {
            source
            for product in products
            for source in product["upstream"]
            if source not in known_sources
        }
        | {metric["source"] for metric in metrics if metric["source"] not in known_sources}
    )
    if invalid_sources:
        raise GovernanceValidationError(f"unknown lineage sources: {', '.join(invalid_sources)}")

    service_by_name = {service["name"]: service for service in services}
    for product in products:
        if product["owner"] != service_by_name[product["name"]]["owner"]:
            raise GovernanceValidationError(f"owner mismatch for {product['name']}")
    for service in services:
        if service["freshness_warning_hours"] >= service["freshness_error_hours"]:
            raise GovernanceValidationError(
                f"freshness warning must precede error for {service['name']}"
            )

    return {
        "metrics": metrics,
        "lineage": products,
        "services": services,
        "performance_defaults": service_config["defaults"],
    }


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    return value


def build_governance_report(
    database_path: str | Path,
    warehouse_manifest_path: str | Path,
    staging_manifest_path: str | Path,
    metrics_path: str | Path,
    lineage_path: str | Path,
    service_levels_path: str | Path,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Execute semantic metrics and evaluate declared operational service signals."""

    config = validate_governance(metrics_path, lineage_path, service_levels_path)
    warehouse_manifest = json.loads(Path(warehouse_manifest_path).read_text(encoding="utf-8"))
    staging_manifest = json.loads(Path(staging_manifest_path).read_text(encoding="utf-8"))
    warning_ms = config["performance_defaults"]["query_latency_warning_ms"]
    error_ms = config["performance_defaults"]["query_latency_error_ms"]

    metric_results: list[MetricResult] = []
    with duckdb.connect(str(database_path), read_only=True) as connection:
        for metric in config["metrics"]:
            started = perf_counter()
            value = connection.execute(metric["sql"]).fetchone()[0]
            latency_ms = round((perf_counter() - started) * 1000, 3)
            status = (
                "error"
                if latency_ms >= error_ms
                else "warning"
                if latency_ms >= warning_ms
                else "current"
            )
            metric_results.append(
                MetricResult(metric["id"], _json_value(value), latency_ms, status)
            )

    source_statuses = [source["freshness_status"] for source in staging_manifest["sources"]]
    freshness_status = (
        "error"
        if "error" in source_statuses
        else "warning"
        if "warning" in source_statuses
        else "current"
    )
    product_results = []
    for service in config["services"]:
        actual_rows = warehouse_manifest["table_counts"].get(service["name"], 0)
        product_results.append(
            {
                "name": service["name"],
                "owner": service["owner"],
                "priority": service["priority"],
                "row_count": actual_rows,
                "volume_status": "current" if actual_rows >= service["minimum_rows"] else "error",
                "freshness_status": freshness_status,
            }
        )

    report = {
        "governance_version": 1,
        "metric_count": len(config["metrics"]),
        "lineage_product_count": len(config["lineage"]),
        "service_level_count": len(config["services"]),
        "metric_results": [asdict(result) for result in metric_results],
        "product_results": product_results,
        "status": "current"
        if all(
            result["volume_status"] == "current" and result["freshness_status"] == "current"
            for result in product_results
        )
        and all(result.performance_status == "current" for result in metric_results)
        else "attention",
    }
    if report_path:
        destination = Path(report_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Validate governance and build operational evidence."
    )
    parser.add_argument("database_path", type=Path)
    parser.add_argument("warehouse_manifest_path", type=Path)
    parser.add_argument("staging_manifest_path", type=Path)
    parser.add_argument("--metrics", type=Path, default=Path("semantic/metrics.yml"))
    parser.add_argument("--lineage", type=Path, default=Path("semantic/lineage.yml"))
    parser.add_argument(
        "--service-levels", type=Path, default=Path("operations/service_levels.yml")
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = build_governance_report(
        args.database_path,
        args.warehouse_manifest_path,
        args.staging_manifest_path,
        args.metrics,
        args.lineage,
        args.service_levels,
        args.report,
    )
    print(
        f"Validated {report['metric_count']} metrics and {report['lineage_product_count']} "
        f"governed products; operational status: {report['status']}."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
