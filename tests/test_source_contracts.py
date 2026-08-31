from copy import deepcopy
from pathlib import Path

import pytest

from data_architecture.contracts import (
    ContractValidationError,
    load_and_validate_contract,
    validate_contract,
    validate_directory,
)

CONTRACTS = Path(__file__).parents[1] / "contracts" / "sources"


@pytest.fixture
def customer_contract():
    return load_and_validate_contract(CONTRACTS / "customers.yml")


def test_all_source_contracts_validate():
    validated = validate_directory(CONTRACTS)
    assert {path.name for path in validated} == {"customers.yml", "orders.yml"}


def test_primary_key_must_be_declared(customer_contract):
    invalid = deepcopy(customer_contract)
    invalid["primary_key"] = ["missing_customer_key"]

    with pytest.raises(ContractValidationError, match="not declared"):
        validate_contract(invalid)


def test_primary_key_must_be_non_nullable(customer_contract):
    invalid = deepcopy(customer_contract)
    invalid["fields"][0]["nullable"] = True

    with pytest.raises(ContractValidationError, match="must be non-nullable"):
        validate_contract(invalid)


def test_pii_cannot_be_public(customer_contract):
    invalid = deepcopy(customer_contract)
    invalid["fields"][1]["classification"] = "public"

    with pytest.raises(ContractValidationError, match="cannot be classified as public"):
        validate_contract(invalid)


def test_freshness_warning_precedes_error(customer_contract):
    invalid = deepcopy(customer_contract)
    invalid["freshness"]["warn_after_hours"] = 72

    with pytest.raises(ContractValidationError, match="warning threshold"):
        validate_contract(invalid)


def test_field_names_are_unique(customer_contract):
    invalid = deepcopy(customer_contract)
    invalid["fields"].append(deepcopy(invalid["fields"][0]))

    with pytest.raises(ContractValidationError, match="duplicate field names"):
        validate_contract(invalid)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda contract: contract.pop("owner"), "missing required keys"),
        (lambda contract: contract["fields"][0].update(type="unsupported"), "type must be"),
        (lambda contract: contract["fields"][0].update(nullable="no"), "nullable must be"),
        (lambda contract: contract["fields"][0].update(pii="no"), "pii must be"),
        (
            lambda contract: contract["fields"][0].update(classification="secret"),
            "classification must be",
        ),
        (
            lambda contract: contract["freshness"].update(loaded_at_field="missing_loaded_at"),
            "must reference a declared field",
        ),
        (
            lambda contract: contract["freshness"].update(warn_after_hours=0),
            "must be a positive integer",
        ),
    ],
)
def test_contract_rejects_invalid_governance_values(customer_contract, mutation, message):
    invalid = deepcopy(customer_contract)
    mutation(invalid)

    with pytest.raises(ContractValidationError, match=message):
        validate_contract(invalid)


def test_contract_file_must_contain_a_mapping(tmp_path):
    invalid_path = tmp_path / "invalid.yml"
    invalid_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ContractValidationError, match="must contain a YAML mapping"):
        load_and_validate_contract(invalid_path)


def test_contract_directory_must_not_be_empty(tmp_path):
    with pytest.raises(ContractValidationError, match="No .yml contracts found"):
        validate_directory(tmp_path)
