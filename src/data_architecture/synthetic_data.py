"""Generate deterministic fictional operational data for the portfolio platform."""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

ANCHOR = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)


@dataclass(frozen=True)
class GenerationConfig:
    """Row-count and random-seed controls for deterministic fixture generation."""

    seed: int = 20260831
    customers: int = 250
    orders: int = 800
    touchpoints: int = 2_000
    events: int = 3_000


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _money(value: Decimal | float) -> str:
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Cannot write empty synthetic source '{path.name}'")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate_operational_data(
    output_directory: str | Path,
    config: GenerationConfig | None = None,
) -> dict[str, Path]:
    """Generate six related operational sources and return their file paths."""

    config = config or GenerationConfig()
    if min(config.customers, config.orders, config.touchpoints, config.events) <= 0:
        raise ValueError("Synthetic row counts must all be positive")

    rng = random.Random(config.seed)
    output = Path(output_directory)
    loaded_at = _timestamp(ANCHOR)
    customer_ids = [f"C{index:05d}" for index in range(1, config.customers + 1)]

    customers: list[dict[str, Any]] = []
    customer_created: dict[str, datetime] = {}
    for customer_id in customer_ids:
        created_at = ANCHOR - timedelta(days=rng.randint(45, 900), hours=rng.randint(0, 23))
        customer_created[customer_id] = created_at
        customers.append(
            {
                "customer_id": customer_id,
                "email_hash": hashlib.sha256(
                    f"{customer_id}@synthetic.example".encode()
                ).hexdigest(),
                "acquisition_channel": rng.choice(
                    ["organic", "paid_search", "paid_social", "referral", "partner"]
                ),
                "country_code": rng.choice(["CR", "US", "MX", "CO", "ES"]),
                "created_at": _timestamp(created_at),
                "marketing_consent": str(rng.random() < 0.82).lower(),
                "source_updated_at": _timestamp(ANCHOR - timedelta(hours=rng.randint(1, 72))),
                "source_loaded_at": loaded_at,
            }
        )

    orders: list[dict[str, Any]] = []
    order_items: list[dict[str, Any]] = []
    for index in range(1, config.orders + 1):
        order_id = f"O{index:06d}"
        customer_id = rng.choice(customer_ids)
        earliest = max(customer_created[customer_id], ANCHOR - timedelta(days=240))
        available_hours = max(1, int((ANCHOR - earliest).total_seconds() // 3600) - 24)
        order_timestamp = earliest + timedelta(hours=rng.randint(1, available_hours))
        line_count = rng.randint(1, 4)
        raw_lines: list[tuple[int, str, int, Decimal]] = []
        gross = Decimal("0")
        for line_number in range(1, line_count + 1):
            quantity = rng.randint(1, 3)
            unit_price = Decimal(str(rng.randint(8, 180))) + Decimal(
                rng.choice(["0.00", "0.49", "0.99"])
            )
            raw_lines.append((line_number, f"P{rng.randint(1, 80):04d}", quantity, unit_price))
            gross += unit_price * quantity

        discount_rate = Decimal(str(rng.choice([0, 0, 0.05, 0.10, 0.15])))
        total_discount = (gross * discount_rate).quantize(Decimal("0.01"))
        allocated = Decimal("0")
        for position, (line_number, product_id, quantity, unit_price) in enumerate(raw_lines, 1):
            line_gross = unit_price * quantity
            if position == len(raw_lines):
                line_discount = total_discount - allocated
            else:
                line_discount = (total_discount * line_gross / gross).quantize(Decimal("0.01"))
                allocated += line_discount
            order_items.append(
                {
                    "order_id": order_id,
                    "line_number": line_number,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": _money(unit_price),
                    "line_discount_amount": _money(line_discount),
                    "source_loaded_at": loaded_at,
                }
            )

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_timestamp": _timestamp(order_timestamp),
                "order_status": rng.choices(
                    ["completed", "cancelled", "refunded"], weights=[88, 7, 5], k=1
                )[0],
                "currency_code": "USD",
                "gross_amount": _money(gross),
                "discount_amount": _money(total_discount),
                "source_loaded_at": loaded_at,
            }
        )

    touchpoints: list[dict[str, Any]] = []
    channels = ["email", "paid_social", "sms", "push"]
    for index in range(1, config.touchpoints + 1):
        channel = rng.choice(channels)
        touchpoints.append(
            {
                "touchpoint_id": f"T{index:07d}",
                "customer_id": rng.choice(customer_ids),
                "campaign_id": f"CMP{rng.randint(1, 12):03d}",
                "channel": channel,
                "touchpoint_type": rng.choices(
                    ["delivered", "opened", "clicked", "converted"],
                    weights=[52, 28, 15, 5],
                    k=1,
                )[0],
                "touchpoint_timestamp": _timestamp(
                    ANCHOR - timedelta(hours=rng.randint(12, 24 * 180))
                ),
                "attributed_cost": _money(
                    {"email": 0.03, "paid_social": 0.85, "sms": 0.08, "push": 0.01}[channel]
                ),
                "source_loaded_at": loaded_at,
            }
        )

    experiment_exposures: list[dict[str, Any]] = []
    for experiment_number in range(1, 4):
        experiment_id = f"EXP{experiment_number:03d}"
        sample_size = min(config.customers, max(10, config.customers // 2))
        for customer_id in rng.sample(customer_ids, sample_size):
            assigned_at = ANCHOR - timedelta(days=rng.randint(15, 120), hours=rng.randint(0, 23))
            was_exposed = rng.random() < 0.94
            experiment_exposures.append(
                {
                    "experiment_id": experiment_id,
                    "customer_id": customer_id,
                    "variant": rng.choice(["control", "message_a", "message_b"]),
                    "eligible_at_assignment": str(rng.random() < 0.98).lower(),
                    "assigned_at": _timestamp(assigned_at),
                    "first_exposed_at": (
                        _timestamp(assigned_at + timedelta(minutes=rng.randint(1, 240)))
                        if was_exposed
                        else ""
                    ),
                    "source_loaded_at": loaded_at,
                }
            )

    customer_events: list[dict[str, Any]] = []
    for index in range(1, config.events + 1):
        customer_events.append(
            {
                "event_id": f"E{index:08d}",
                "customer_id": rng.choice(customer_ids),
                "session_id": f"S{rng.randint(1, max(1, config.events // 3)):07d}",
                "event_name": rng.choice(
                    ["page_view", "product_view", "add_to_cart", "checkout_start", "login"]
                ),
                "channel": rng.choice(["web", "ios", "android"]),
                "event_timestamp": _timestamp(
                    ANCHOR - timedelta(minutes=rng.randint(60, 60 * 24 * 120))
                ),
                "source_loaded_at": loaded_at,
            }
        )

    sources = {
        "customers": customers,
        "orders": orders,
        "order_items": order_items,
        "campaign_touchpoints": touchpoints,
        "experiment_exposures": experiment_exposures,
        "customer_events": customer_events,
    }
    paths: dict[str, Path] = {}
    for source, rows in sources.items():
        path = output / f"{source}.csv"
        _write_csv(path, rows)
        paths[source] = path
    return paths


def main() -> None:  # pragma: no cover - command-line wrapper
    parser = argparse.ArgumentParser(description="Generate fictional operational source data.")
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--seed", type=int, default=GenerationConfig.seed)
    args = parser.parse_args()
    paths = generate_operational_data(args.output_directory, GenerationConfig(seed=args.seed))
    print(f"Generated {len(paths)} operational source file(s) in '{args.output_directory}'.")


if __name__ == "__main__":  # pragma: no cover
    main()
