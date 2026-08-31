"""Contract-driven source-aligned staging for fictional operational data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from data_architecture.contracts import load_and_validate_contract


class StagingValidationError(ValueError):
    """Raised when raw source data violates its declared interface."""


@dataclass(frozen=True)
class StageResult:
    source: str
    input_rows: int
    output_rows: int
    duplicate_rows_removed: int
    newest_source_load: str
    freshness_age_hours: float
    freshness_status: str
    output_path: str


def _normalize_timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _normalize_value(value: str, field: dict[str, Any]) -> str:
    cleaned = value.strip()
    if not cleaned:
        if field["nullable"]:
            return ""
        raise StagingValidationError(f"field '{field['name']}' cannot be null")

    field_type = field["type"]
    try:
        if field_type == "string":
            return cleaned
        if field_type == "integer":
            return str(int(cleaned))
        if field_type == "decimal":
            return str(Decimal(cleaned).quantize(Decimal("0.01")))
        if field_type == "boolean":
            lowered = cleaned.lower()
            if lowered in {"true", "1", "yes"}:
                return "true"
            if lowered in {"false", "0", "no"}:
                return "false"
            raise ValueError("unsupported boolean")
        if field_type == "date":
            return date.fromisoformat(cleaned).isoformat()
        if field_type == "timestamp":
            return _normalize_timestamp(cleaned)
    except (ValueError, InvalidOperation) as exc:
        raise StagingValidationError(
            f"field '{field['name']}' cannot be parsed as {field_type}: {cleaned!r}"
        ) from exc
    raise StagingValidationError(f"unsupported field type '{field_type}'")


def _row_hash(row: dict[str, str], field_names: list[str]) -> str:
    canonical = "|".join(row[name] for name in field_names)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _freshness_result(
    newest_source_load: str,
    staged_at: datetime,
    freshness: dict[str, Any],
) -> tuple[float, str]:
    newest = datetime.fromisoformat(newest_source_load.replace("Z", "+00:00"))
    if newest.tzinfo is None:
        newest = newest.replace(tzinfo=UTC)
    age_hours = (staged_at.astimezone(UTC) - newest.astimezone(UTC)).total_seconds() / 3600
    if age_hours < 0:
        raise StagingValidationError("newest source load cannot be later than the staging run")
    if age_hours >= freshness["error_after_hours"]:
        status = "error"
    elif age_hours >= freshness["warn_after_hours"]:
        status = "warning"
    else:
        status = "current"
    return round(age_hours, 2), status


def stage_source(
    raw_path: str | Path,
    contract_path: str | Path,
    output_path: str | Path,
    staged_at: datetime | None = None,
) -> StageResult:
    """Validate, standardize, deduplicate, and stage one contracted source."""

    contract = load_and_validate_contract(contract_path)
    raw_path = Path(raw_path)
    output_path = Path(output_path)
    staged_at = staged_at or datetime.now(UTC)
    staged_at_text = staged_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    fields = contract["fields"]
    field_names = [field["name"] for field in fields]
    fields_by_name = {field["name"]: field for field in fields}
    primary_key = contract["primary_key"]
    loaded_at_field = contract["freshness"]["loaded_at_field"]

    with raw_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        actual_fields = reader.fieldnames or []
        missing = sorted(set(field_names) - set(actual_fields))
        unexpected = sorted(set(actual_fields) - set(field_names))
        if missing or unexpected:
            raise StagingValidationError(
                f"schema drift in '{raw_path.name}'; missing={missing}, unexpected={unexpected}"
            )
        raw_rows = list(reader)

    staged_by_key: dict[tuple[str, ...], tuple[int, dict[str, str]]] = {}
    for row_number, raw_row in enumerate(raw_rows, start=2):
        try:
            normalized = {
                name: _normalize_value(raw_row.get(name, ""), fields_by_name[name])
                for name in field_names
            }
        except StagingValidationError as exc:
            raise StagingValidationError(f"{raw_path.name} row {row_number}: {exc}") from exc

        key = tuple(normalized[name] for name in primary_key)
        previous = staged_by_key.get(key)
        if previous:
            previous_loaded = previous[1][loaded_at_field]
            if normalized[loaded_at_field] < previous_loaded:
                continue
        staged_by_key[key] = (row_number, normalized)

    if not staged_by_key:
        raise StagingValidationError(f"raw source '{raw_path.name}' contains no data rows")
    newest_source_load = max(row[1][loaded_at_field] for row in staged_by_key.values())
    freshness_age_hours, freshness_status = _freshness_result(
        newest_source_load, staged_at, contract["freshness"]
    )

    audit_fields = ["_source_name", "_source_file", "_source_row_number", "_row_hash", "_staged_at"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names + audit_fields)
        writer.writeheader()
        for key in sorted(staged_by_key):
            row_number, normalized = staged_by_key[key]
            writer.writerow(
                {
                    **normalized,
                    "_source_name": contract["source"],
                    "_source_file": raw_path.name,
                    "_source_row_number": row_number,
                    "_row_hash": _row_hash(normalized, field_names),
                    "_staged_at": staged_at_text,
                }
            )

    return StageResult(
        source=contract["source"],
        input_rows=len(raw_rows),
        output_rows=len(staged_by_key),
        duplicate_rows_removed=len(raw_rows) - len(staged_by_key),
        newest_source_load=newest_source_load,
        freshness_age_hours=freshness_age_hours,
        freshness_status=freshness_status,
        output_path=str(output_path),
    )


def run_staging_pipeline(
    raw_directory: str | Path,
    contract_directory: str | Path,
    output_directory: str | Path,
    staged_at: datetime | None = None,
) -> list[StageResult]:
    """Stage every contracted source and write a run manifest."""

    raw_directory = Path(raw_directory)
    contract_directory = Path(contract_directory)
    output_directory = Path(output_directory)
    contract_paths = sorted(contract_directory.glob("*.yml"))
    if not contract_paths:
        raise StagingValidationError(f"No source contracts found in '{contract_directory}'")

    results: list[StageResult] = []
    for contract_path in contract_paths:
        contract = load_and_validate_contract(contract_path)
        source = contract["source"]
        raw_path = raw_directory / f"{source}.csv"
        if not raw_path.is_file():
            raise StagingValidationError(f"Missing raw source file '{raw_path}'")
        results.append(
            stage_source(
                raw_path,
                contract_path,
                output_directory / f"stg_{source}.csv",
                staged_at,
            )
        )

    output_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = output_directory / "staging_manifest.json"
    manifest_path.write_text(
        json.dumps({"sources": [asdict(result) for result in results]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return results


def main() -> None:  # pragma: no cover - command-line wrapper
    parser = argparse.ArgumentParser(description="Run contract-driven source staging.")
    parser.add_argument("raw_directory", type=Path)
    parser.add_argument("contract_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument(
        "--staged-at",
        help="Optional ISO-8601 run timestamp; useful for deterministic portfolio fixtures.",
    )
    args = parser.parse_args()
    staged_at = (
        datetime.fromisoformat(args.staged_at.replace("Z", "+00:00")) if args.staged_at else None
    )
    results = run_staging_pipeline(
        args.raw_directory, args.contract_directory, args.output_directory, staged_at
    )
    print(f"Staged {len(results)} source(s) in '{args.output_directory}'.")


if __name__ == "__main__":  # pragma: no cover
    main()
