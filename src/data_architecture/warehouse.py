"""Build and validate the portable DuckDB dimensional warehouse."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import duckdb
import yaml


class WarehouseBuildError(RuntimeError):
    """Raised when a warehouse model or quality check cannot be completed."""


@dataclass(frozen=True)
class QualityCheckResult:
    name: str
    description: str
    actual_value: int | float | str
    expected_value: int | float | str
    passed: bool


WAREHOUSE_TABLES = [
    "dim_date",
    "dim_customer",
    "dim_product",
    "dim_campaign",
    "dim_channel",
    "fact_orders",
    "fact_order_items",
    "fact_campaign_touchpoints",
    "fact_experiment_exposures",
    "fact_customer_events",
]


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def execute_models(
    connection: duckdb.DuckDBPyConnection,
    staged_directory: str | Path,
    sql_directory: str | Path,
) -> list[str]:
    """Execute ordered SQL model files after injecting the staged-data path."""

    staged_directory = Path(staged_directory)
    sql_paths = sorted(Path(sql_directory).glob("*.sql"))
    if not sql_paths:
        raise WarehouseBuildError(f"No warehouse SQL models found in '{sql_directory}'")
    for sql_path in sql_paths:
        sql = sql_path.read_text(encoding="utf-8").replace(
            "{{STAGED_DIR}}", _sql_path(staged_directory)
        )
        try:
            connection.execute(sql)
        except duckdb.Error as exc:
            raise WarehouseBuildError(f"Failed warehouse model '{sql_path.name}': {exc}") from exc
    return [path.name for path in sql_paths]


def run_quality_checks(
    connection: duckdb.DuckDBPyConnection,
    quality_checks_path: str | Path,
) -> list[QualityCheckResult]:
    """Execute declared warehouse checks and return inspectable results."""

    config = yaml.safe_load(Path(quality_checks_path).read_text(encoding="utf-8"))
    checks = config.get("checks", []) if isinstance(config, dict) else []
    if not checks:
        raise WarehouseBuildError("Warehouse quality-check configuration is empty")

    results: list[QualityCheckResult] = []
    for check in checks:
        actual = connection.execute(check["sql"]).fetchone()[0]
        expected = check["expected_value"]
        results.append(
            QualityCheckResult(
                name=check["name"],
                description=check["description"],
                actual_value=actual,
                expected_value=expected,
                passed=actual == expected,
            )
        )
    failed = [result.name for result in results if not result.passed]
    if failed:
        raise WarehouseBuildError(f"Warehouse quality checks failed: {', '.join(failed)}")
    return results


def _table_counts(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM warehouse.{table}").fetchone()[0]
        for table in WAREHOUSE_TABLES
    }


def build_warehouse(
    database_path: str | Path,
    staged_directory: str | Path,
    sql_directory: str | Path,
    quality_checks_path: str | Path,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build the dimensional warehouse, validate it, and optionally write evidence."""

    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database_path)) as connection:
        models = execute_models(connection, staged_directory, sql_directory)
        quality_results = run_quality_checks(connection, quality_checks_path)
        manifest = {
            "engine": "duckdb",
            "engine_version": duckdb.__version__,
            "models_executed": models,
            "table_counts": _table_counts(connection),
            "quality_checks": [asdict(result) for result in quality_results],
        }

    if manifest_path:
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:  # pragma: no cover - command-line wrapper
    parser = argparse.ArgumentParser(description="Build the portable dimensional warehouse.")
    parser.add_argument("database_path", type=Path)
    parser.add_argument("staged_directory", type=Path)
    parser.add_argument("--sql-directory", type=Path, default=Path("warehouse/sql"))
    parser.add_argument(
        "--quality-checks",
        type=Path,
        default=Path("warehouse/quality_checks.yml"),
    )
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    manifest = build_warehouse(
        args.database_path,
        args.staged_directory,
        args.sql_directory,
        args.quality_checks,
        args.manifest,
    )
    print(
        f"Built {len(manifest['table_counts'])} warehouse tables with "
        f"{len(manifest['quality_checks'])} passing quality checks."
    )


if __name__ == "__main__":  # pragma: no cover
    main()
