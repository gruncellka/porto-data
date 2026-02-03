"""Consistency tests between canonical definitions and data files."""

import json
from pathlib import Path


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_registered_mail_enum_matches_services(project_root: Path):
    """Ensure registered mail enum stays in sync with services.json."""
    services = _load_json(project_root / "data/services.json")["services"]
    enum_values = set(_load_json(project_root / "definitions/enums/registered-mail-type.schema.json")["enum"])

    service_registered = {s["id"] for s in services if s["id"].startswith("registered_mail")}

    assert service_registered == enum_values, (
        "registered_mail services and enum diverged. "
        f"services_only={service_registered - enum_values}, "
        f"enum_only={enum_values - service_registered}"
    )


def test_zone_enum_matches_zones_data(project_root: Path):
    """Ensure zone enum matches zones.json ids."""
    zones = _load_json(project_root / "data/zones.json")["zones"]
    enum_values = set(_load_json(project_root / "definitions/enums/zone-id.schema.json")["enum"])

    zone_ids = {z["id"] for z in zones}

    assert zone_ids == enum_values, (
        "zone ids and enum diverged. "
        f"zones_only={zone_ids - enum_values}, enum_only={enum_values - zone_ids}"
    )


def test_letter_type_enum_matches_products(project_root: Path):
    """Ensure letter type enum matches product ids (semantic product ids)."""
    products = _load_json(project_root / "data/products.json")["products"]
    enum_values = set(_load_json(project_root / "definitions/enums/letter-type.schema.json")["enum"])

    product_ids = {p["id"] for p in products}

    assert product_ids == enum_values, (
        "product ids and letter-type enum diverged. "
        f"products_only={product_ids - enum_values}, enum_only={enum_values - product_ids}"
    )
