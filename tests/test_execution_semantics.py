#!/usr/bin/env python3
"""Tests for execution semantics (mark_type, tracking)."""

import json
from pathlib import Path

from scripts.data_files import get_project_root
from scripts.validators.graph import validate_graph
from scripts.validators.graph.execution_semantics import service_enables_tracking
from scripts.validators.schema import validate_file


def _products_schema_path() -> Path:
    root = get_project_root()
    return root / "schemas" / "products.schema.json"


def _minimal_delivery() -> list[dict]:
    return [{"zones": ["domestic"], "span": "within", "days_max": 2}]


class TestProductsSchemaExecutionSemantics:
    """JSON Schema: required execution fields and label/none rejection."""

    def test_product_without_mark_type_fails_schema(self, tmp_path):
        schema_path = _products_schema_path()
        data_path = tmp_path / "products.json"
        data = {
            "file_type": "products",
            "unit": {"weight": "g"},
            "products": [
                {
                    "id": "prod_one",
                    "name": "P",
                    "envelope_ids": ["C6"],
                    "zones": ["domestic"],
                    "effective_from": None,
                    "effective_to": None,
                    "tracking": "none",
                    "delivery": _minimal_delivery(),
                }
            ],
        }
        data_path.write_text(json.dumps(data), encoding="utf-8")
        assert validate_file(str(schema_path), str(data_path)) is False

    def test_label_with_tracking_none_fails_schema(self, tmp_path):
        schema_path = _products_schema_path()
        data_path = tmp_path / "products.json"
        data = {
            "file_type": "products",
            "unit": {"weight": "g"},
            "products": [
                {
                    "id": "prod_one",
                    "name": "P",
                    "envelope_ids": ["C6"],
                    "zones": ["domestic"],
                    "effective_from": None,
                    "effective_to": None,
                    "mark_type": "label",
                    "tracking": "none",
                    "delivery": _minimal_delivery(),
                }
            ],
        }
        data_path.write_text(json.dumps(data), encoding="utf-8")
        assert validate_file(str(schema_path), str(data_path)) is False

    def test_stamp_with_none_passes_schema(self, tmp_path):
        schema_path = _products_schema_path()
        data_path = tmp_path / "products.json"
        data = {
            "file_type": "products",
            "unit": {"weight": "g"},
            "products": [
                {
                    "id": "prod_one",
                    "name": "P",
                    "label": "Product",
                    "envelope_ids": ["C6"],
                    "zones": ["domestic"],
                    "effective_from": None,
                    "effective_to": None,
                    "mark_type": "stamp",
                    "tracking": "none",
                    "delivery": _minimal_delivery(),
                }
            ],
        }
        data_path.write_text(json.dumps(data), encoding="utf-8")
        assert validate_file(str(schema_path), str(data_path)) is True


class TestLaposteProviderData:
    """La Poste illustrative dataset follows label + tracking rules."""

    def test_laposte_products_are_labels(self):
        root = get_project_root()
        path = root / "providers" / "laposte" / "products.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for p in data["products"]:
            assert p["mark_type"] == "label"
            assert p["tracking"] in ("optional", "included")

    def test_laposte_graph_validation_exits_zero(self):
        assert validate_graph(provider="laposte") == 0


class TestDeutschepostInsuranceIsNotTracking:
    """Zusatzversicherung is priced insurance, not Sendungsnummer."""

    def test_zusatzversicherung_features_omit_tracking(self):
        root = get_project_root()
        services = json.loads(
            (root / "providers" / "deutschepost" / "services.json").read_text(encoding="utf-8")
        )
        features = json.loads(
            (root / "providers" / "deutschepost" / "features.json").read_text(encoding="utf-8")
        )
        zv = next(s for s in services["services"] if s["id"] == "zusatzversicherung")
        by_id = {
            str(row["id"]): row
            for row in features.get("features", [])
            if isinstance(row, dict) and row.get("id")
        }
        assert "tracking" not in zv["features"]
        assert not service_enables_tracking(zv, by_id)

    def test_empty_service_features_pass_schema(self, tmp_path):
        root = get_project_root()
        schema_path = root / "schemas" / "services.schema.json"
        data_path = tmp_path / "services.json"
        data = {
            "file_type": "services",
            "services": [
                {
                    "id": "zusatzversicherung",
                    "kind": "insurance",
                    "name": "Z",
                    "label": "I",
                    "description": "d",
                    "features": [],
                }
            ],
        }
        data_path.write_text(json.dumps(data), encoding="utf-8")
        assert validate_file(str(schema_path), str(data_path)) is True
