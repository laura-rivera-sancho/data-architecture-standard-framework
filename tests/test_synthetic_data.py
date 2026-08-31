import csv
import hashlib

import pytest

from data_architecture.synthetic_data import GenerationConfig, generate_operational_data


def _rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generation_is_deterministic_and_complete(tmp_path):
    config = GenerationConfig(seed=42, customers=20, orders=30, touchpoints=40, events=50)
    first = generate_operational_data(tmp_path / "first", config)
    second = generate_operational_data(tmp_path / "second", config)

    assert set(first) == {
        "customers",
        "orders",
        "order_items",
        "campaign_touchpoints",
        "experiment_exposures",
        "customer_events",
    }
    assert {name: _digest(path) for name, path in first.items()} == {
        name: _digest(second[name]) for name in second
    }
    assert len(_rows(first["customers"])) == 20
    assert len(_rows(first["orders"])) == 30
    assert len(_rows(first["campaign_touchpoints"])) == 40
    assert len(_rows(first["customer_events"])) == 50


def test_generated_relationships_are_valid(tmp_path):
    paths = generate_operational_data(
        tmp_path,
        GenerationConfig(seed=7, customers=15, orders=25, touchpoints=30, events=35),
    )
    customer_ids = {row["customer_id"] for row in _rows(paths["customers"])}
    order_ids = {row["order_id"] for row in _rows(paths["orders"])}

    assert {row["customer_id"] for row in _rows(paths["orders"])} <= customer_ids
    assert {row["order_id"] for row in _rows(paths["order_items"])} <= order_ids
    assert {row["customer_id"] for row in _rows(paths["campaign_touchpoints"])} <= customer_ids
    assert {row["customer_id"] for row in _rows(paths["experiment_exposures"])} <= customer_ids
    assert {row["customer_id"] for row in _rows(paths["customer_events"])} <= customer_ids


def test_generation_requires_positive_row_counts(tmp_path):
    with pytest.raises(ValueError, match="must all be positive"):
        generate_operational_data(tmp_path, GenerationConfig(customers=0))
