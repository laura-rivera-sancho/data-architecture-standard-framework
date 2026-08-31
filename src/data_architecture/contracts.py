"""Load and validate version-controlled source contracts."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

REQUIRED_KEYS = {
    "version",
    "source",
    "owner",
    "description",
    "grain",
    "primary_key",
    "freshness",
    "fields",
}
ALLOWED_TYPES = {"string", "integer", "decimal", "boolean", "date", "timestamp"}
ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "restricted"}
REQUIRED_FIELD_KEYS = {
    "name",
    "type",
    "nullable",
    "description",
    "pii",
    "classification",
}


class ContractValidationError(ValueError):
    """Raised when a source contract violates the portfolio contract standard."""


def _require_nonempty_string(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")


def validate_contract(contract: dict[str, Any]) -> None:
    """Validate a parsed contract and raise one actionable aggregated error."""

    errors: list[str] = []
    missing = sorted(REQUIRED_KEYS - contract.keys())
    if missing:
        errors.append(f"missing required keys: {', '.join(missing)}")

    for key in ("source", "owner", "description", "grain"):
        _require_nonempty_string(contract.get(key), key, errors)

    fields = contract.get("fields")
    if not isinstance(fields, list) or not fields:
        errors.append("fields must be a non-empty list")
        fields = []

    field_names: list[str] = []
    fields_by_name: dict[str, dict[str, Any]] = {}
    for index, field in enumerate(fields):
        label = f"fields[{index}]"
        if not isinstance(field, dict):
            errors.append(f"{label} must be a mapping")
            continue

        missing_field_keys = sorted(REQUIRED_FIELD_KEYS - field.keys())
        if missing_field_keys:
            errors.append(f"{label} missing keys: {', '.join(missing_field_keys)}")

        name = field.get("name")
        _require_nonempty_string(name, f"{label}.name", errors)
        if isinstance(name, str) and name:
            field_names.append(name)
            fields_by_name[name] = field

        if field.get("type") not in ALLOWED_TYPES:
            errors.append(f"{label}.type must be one of {sorted(ALLOWED_TYPES)}")
        if not isinstance(field.get("nullable"), bool):
            errors.append(f"{label}.nullable must be boolean")
        _require_nonempty_string(field.get("description"), f"{label}.description", errors)
        if not isinstance(field.get("pii"), bool):
            errors.append(f"{label}.pii must be boolean")
        classification = field.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(
                f"{label}.classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}"
            )
        if field.get("pii") is True and classification == "public":
            errors.append(f"{label} is pii and cannot be classified as public")

    duplicates = sorted({name for name in field_names if field_names.count(name) > 1})
    if duplicates:
        errors.append(f"duplicate field names: {', '.join(duplicates)}")

    primary_key = contract.get("primary_key")
    if not isinstance(primary_key, list) or not primary_key:
        errors.append("primary_key must be a non-empty list")
    else:
        for key in primary_key:
            if key not in fields_by_name:
                errors.append(f"primary-key field '{key}' is not declared")
            elif fields_by_name[key].get("nullable") is not False:
                errors.append(f"primary-key field '{key}' must be non-nullable")

    freshness = contract.get("freshness")
    if not isinstance(freshness, dict):
        errors.append("freshness must be a mapping")
    else:
        loaded_at = freshness.get("loaded_at_field")
        if loaded_at not in fields_by_name:
            errors.append("freshness.loaded_at_field must reference a declared field")
        warn = freshness.get("warn_after_hours")
        error = freshness.get("error_after_hours")
        if not isinstance(warn, int) or warn <= 0:
            errors.append("freshness.warn_after_hours must be a positive integer")
        if not isinstance(error, int) or error <= 0:
            errors.append("freshness.error_after_hours must be a positive integer")
        if isinstance(warn, int) and isinstance(error, int) and warn >= error:
            errors.append("freshness warning threshold must precede the error threshold")

    if errors:
        source = contract.get("source", "<unknown>")
        details = "\n- ".join(errors)
        raise ContractValidationError(f"Invalid contract '{source}':\n- {details}")


def load_and_validate_contract(path: str | Path) -> dict[str, Any]:
    """Load one YAML contract, validate it, and return the parsed mapping."""

    contract_path = Path(path)
    with contract_path.open(encoding="utf-8") as handle:
        contract = yaml.safe_load(handle)
    if not isinstance(contract, dict):
        raise ContractValidationError(f"Contract '{contract_path}' must contain a YAML mapping")
    validate_contract(contract)
    return contract


def validate_directory(directory: str | Path) -> list[Path]:
    """Validate every YAML contract in a directory and return validated paths."""

    contract_paths = sorted(Path(directory).glob("*.yml"))
    if not contract_paths:
        raise ContractValidationError(f"No .yml contracts found in '{directory}'")
    for path in contract_paths:
        load_and_validate_contract(path)
    return contract_paths


def main() -> None:  # pragma: no cover - exercised by the CI command-line smoke check
    parser = argparse.ArgumentParser(description="Validate source-contract YAML files.")
    parser.add_argument("directory", type=Path, help="Directory containing .yml contracts")
    args = parser.parse_args()
    paths = validate_directory(args.directory)
    print(f"Validated {len(paths)} source contract(s).")


if __name__ == "__main__":  # pragma: no cover
    main()
