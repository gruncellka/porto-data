#!/usr/bin/env python3
"""Tests for execution semantics (mark_type, tracking_mode, enables_tracking)."""

import json
from pathlib import Path

from scripts.data_files import get_project_root
from scripts.validators.graph import validate_graph
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
            "provider": "testprov",
            "unit": {"weight": "g"},
            "products": [
                {
                    "id": "prod_one",
                    "name": "P",
                    "envelope_ids": ["C6"],
                    "zones": ["domestic"],
                    "effective_from": None,
                    "effective_to": None,
                    "tracking_mode": "none",
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
            "provider": "testprov",
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
                    "tracking_mode": "none",
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
            "provider": "testprov",
            "unit": {"weight": "g"},
            "products": [
                {
                    "id": "prod_one",
                    "porto_id": "small",
                    "name": "P",
                    "envelope_ids": ["C6"],
                    "zones": ["domestic"],
                    "effective_from": None,
                    "effective_to": None,
                    "mark_type": "stamp",
                    "tracking_mode": "none",
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
            assert p["tracking_mode"] in ("optional", "included")

    def test_laposte_graph_validation_exits_zero(self):
        assert validate_graph(provider="laposte") == 0
