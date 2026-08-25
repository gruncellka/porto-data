"""Deutsche Post stamps and services do not declare ADDRESS_*; calibrations stay geometry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "porto_data" / "providers" / "deutschepost"


def _load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_stamp_products_do_not_require_address() -> None:
    products = _load("products.json")
    for row in products["products"]:
        assert row.get("mark_type") == "stamp", row["id"]
        assert "requires" not in row, row["id"]


def test_mark_profiles_do_not_require_address() -> None:
    marks = _load("marks.json")
    for row in marks["profiles"]:
        assert row.get("type") == "stamp", row["id"]
        assert "requires" not in row, row["id"]


def test_calibrations_keep_provider_layout_tokens() -> None:
    marks = _load("marks.json")
    tokens = {row["mark_profile"] for row in marks["calibrations"]}
    assert tokens == {"FRANKING_ZONE", "ADDRESS_ZONE"}


def test_einschreiben_services_do_not_require_address() -> None:
    services = _load("services.json")
    for row in services["services"]:
        assert "requires" not in row, row["id"]


def test_features_do_not_require_address() -> None:
    features = _load("features.json")
    for row in features["features"]:
        assert "requires" not in row, row["id"]
