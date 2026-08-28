"""Tests for kinds validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validators.kinds import (
    MAPPING_DOC,
    REQUIRED_PROVIDER_SCHEMAS,
    _kinds_by_entity,
    _product_ids,
    _render_mapping_doc,
    _service_ids,
    validate_kinds,
)

_SCHEMA_SRC = Path(__file__).parent.parent / "porto_data/schemas/kinds.schema.json"


def _write_kinds_schema(schemas_dir: Path) -> None:
    schemas_dir.mkdir(parents=True, exist_ok=True)
    (schemas_dir / "kinds.schema.json").write_text(
        _SCHEMA_SRC.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def _write_registry(tmp_path: Path, provider_id: str = "testco") -> Path:
    root = tmp_path / "porto_data"
    root.mkdir(parents=True, exist_ok=True)
    (root / "providers.json").write_text(
        json.dumps(
            {
                "providers": {
                    provider_id: {
                        "label": "T",
                        "name": "Test AG",
                        "country": "DE",
                        "mark_types": ["stamp"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (root / "mappings.json").write_text(
        json.dumps(
            {
                "mappings": {
                    "policy": {},
                    "formats": {},
                    "registry": {},
                    "providers": {provider_id: {}},
                }
            }
        ),
        encoding="utf-8",
    )
    _write_kinds_schema(root / "schemas")
    return root


def _write_provider_files(
    prov: Path,
    *,
    products: dict[str, Any] | None = None,
    services: dict[str, Any] | None = None,
    features: dict[str, Any] | None = None,
    graph: dict[str, Any] | None = None,
    product_prices: dict[str, Any] | None = None,
    service_prices: dict[str, Any] | None = None,
    omit: set[str] | None = None,
) -> None:
    omit = omit or set()
    defaults = {
        "products": {
            "file_type": "products",
            "unit": {"weight": "g"},
            "products": [
                {
                    "id": "p1",
                    "name": "P",
                    "envelope_ids": ["DL"],
                    "zones": ["domestic"],
                    "effective_from": "2026-01-01",
                    "effective_to": None,
                    "mark_type": "stamp",
                    "tracking": "optional",
                }
            ],
        },
        "services": {
            "file_type": "services",
            "services": [
                {
                    "id": "svc_native",
                    "kind": "tracking",
                    "name": "S",
                    "label": "S",
                    "description": "d",
                    "features": ["f1"],
                }
            ],
        },
        "features": {
            "file_type": "features",
            "features": [
                {
                    "id": "f1",
                    "kind": "tracking",
                    "name": "F",
                    "label": "F",
                    "description": "d",
                }
            ],
        },
        "graph": {
            "file_type": "graph",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {},
            "edges": {
                "products": {"p1": {"zones": ["domestic"], "weight_tiers": ["W0020"]}},
                "marks": {"domestic": {"profile": "p1"}},
            },
            "services": ["svc_native"],
        },
        "product_prices": {
            "file_type": "product_prices",
            "unit": {"price": "cents", "currency": "EUR"},
            "product_prices": [],
        },
        "service_prices": {
            "file_type": "service_prices",
            "unit": {"price": "cents", "currency": "EUR"},
            "service_prices": [],
        },
    }
    payloads = {
        "products": products if products is not None else defaults["products"],
        "services": services if services is not None else defaults["services"],
        "features": features if features is not None else defaults["features"],
        "graph": graph if graph is not None else defaults["graph"],
    }
    for name, payload in payloads.items():
        if name in omit:
            continue
        (prov / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")

    if "product_prices" not in omit or "service_prices" not in omit:
        (prov / "prices").mkdir(exist_ok=True)
    if "product_prices" not in omit:
        pp = product_prices if product_prices is not None else defaults["product_prices"]
        (prov / "prices" / "products.json").write_text(json.dumps(pp), encoding="utf-8")
    if "service_prices" not in omit:
        sp = service_prices if service_prices is not None else defaults["service_prices"]
        (prov / "prices" / "services.json").write_text(json.dumps(sp), encoding="utf-8")


@pytest.fixture
def kinds_sandbox(tmp_path: Path, monkeypatch):
    root = _write_registry(tmp_path)
    prov = root / "providers" / "testco"
    prov.mkdir(parents=True)
    _write_provider_files(prov)
    monkeypatch.setattr("scripts.validators.kinds.list_provider_ids", lambda: ["testco"])
    monkeypatch.setattr("scripts.validators.kinds.get_project_root", lambda: root)
    return tmp_path, root, prov


class TestKindsHelpers:
    def test_service_ids_empty_inputs(self) -> None:
        assert _service_ids(None) == set()
        assert _service_ids({}) == set()

    def test_product_ids_empty_inputs(self) -> None:
        assert _product_ids(None) == set()
        assert _product_ids({}) == set()

    def test_kinds_by_entity_skips_non_dict_rows(self) -> None:
        assert _kinds_by_entity(["not-a-dict", {"id": "a", "kind": "registered"}]) == {
            "registered": ["a"]
        }


class TestKindsValidator:
    def test_required_provider_schemas_count(self) -> None:
        assert len(REQUIRED_PROVIDER_SCHEMAS) == 9
        assert "schemas/graph.schema.json" in REQUIRED_PROVIDER_SCHEMAS

    def test_render_mapping_doc(self) -> None:
        doc = _render_mapping_doc(
            {
                "deutschepost": {
                    "products": [("standardbrief", "")],
                    "services": [("einschreiben", "registered")],
                    "features": [],
                }
            }
        )
        assert "deutschepost" in doc
        assert "`standardbrief`" in doc
        assert "`einschreiben`" in doc
        assert "`registered`" in doc

    def test_validate_kinds_live_bundle(self, project_root: Path) -> None:
        rc = validate_kinds(write_mapping_doc=True)
        assert rc == 0
        mapping = project_root / "docs" / "kinds.md"
        assert mapping.is_file()

    def test_validate_success_without_rewriting_current_mapping(
        self, kinds_sandbox, capsys
    ) -> None:
        _tmp, root, _prov = kinds_sandbox
        mapping_path = root / MAPPING_DOC
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        while validate_kinds(write_mapping_doc=True) != 0:
            pass
        content = mapping_path.read_text(encoding="utf-8")
        rc_second = validate_kinds(write_mapping_doc=True)
        assert rc_second == 0
        assert "is current" in capsys.readouterr().out
        assert mapping_path.read_text(encoding="utf-8") == content

    def test_validate_updates_mapping_when_content_differs(self, kinds_sandbox) -> None:
        _tmp, root, _prov = kinds_sandbox
        mapping_path = root / MAPPING_DOC
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_path.write_text("# stale\n", encoding="utf-8")
        rc = validate_kinds(write_mapping_doc=True)
        assert rc == 1
        text = mapping_path.read_text(encoding="utf-8")
        assert "p1" in text
        assert text.startswith("# Kind mapping tables")
        rc_again = validate_kinds(write_mapping_doc=True)
        assert rc_again == 0

    def test_rejects_kind_used_as_graph_service_id(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        graph = json.loads((prov / "graph.json").read_text(encoding="utf-8"))
        graph["services"] = ["tracking"]
        (prov / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_unknown_available_service(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        graph = json.loads((prov / "graph.json").read_text(encoding="utf-8"))
        graph["services"] = ["missing_svc"]
        (prov / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_intl_suffix_on_native_product_id(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        products = json.loads((prov / "products.json").read_text(encoding="utf-8"))
        products["products"][0]["id"] = "letter_intl"
        (prov / "products.json").write_text(json.dumps(products), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_intl_suffix_on_native_service_id(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        services = json.loads((prov / "services.json").read_text(encoding="utf-8"))
        services["services"][0]["id"] = "registered_intl"
        (prov / "services.json").write_text(json.dumps(services), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_unknown_product_price_ref(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        (prov / "prices" / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [
                        {
                            "product_id": "ghost_product",
                            "zone": "domestic",
                            "weight_tier": "W0020",
                            "price": 100,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_kind_in_service_prices(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        (prov / "prices" / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [{"service_id": "tracking", "price": 50}],
                }
            ),
            encoding="utf-8",
        )
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_unknown_service_price_ref(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        (prov / "prices" / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [{"service_id": "ghost_service", "price": 50}],
                }
            ),
            encoding="utf-8",
        )
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_skips_non_dict_and_empty_price_rows(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        (prov / "prices" / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [
                        "skip",
                        {"zone": "domestic", "weight_tier": "W0020", "price": 100},
                    ],
                }
            ),
            encoding="utf-8",
        )
        (prov / "prices" / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": ["skip", {"price": 50}],
                }
            ),
            encoding="utf-8",
        )
        assert validate_kinds(write_mapping_doc=False) == 0

    def test_rejects_invalid_kind_on_catalog_rows(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        services = json.loads((prov / "services.json").read_text(encoding="utf-8"))
        services["services"] = [
            services["services"][0],
            "bad-row",
            {**services["services"][0], "id": "svc2", "kind": "not_a_real_kind"},
        ]
        features = json.loads((prov / "features.json").read_text(encoding="utf-8"))
        features["features"] = [
            features["features"][0],
            "bad-row",
            {**features["features"][0], "id": "f2", "kind": "not_a_real_kind"},
        ]
        (prov / "services.json").write_text(json.dumps(services), encoding="utf-8")
        (prov / "features.json").write_text(json.dumps(features), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_skips_non_dict_product_rows(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        products = json.loads((prov / "products.json").read_text(encoding="utf-8"))
        products["products"].insert(0, "bad-row")
        (prov / "products.json").write_text(json.dumps(products), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 0

    def test_rejects_product_kind_field(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        products = json.loads((prov / "products.json").read_text(encoding="utf-8"))
        products["products"][0]["kind"] = "small"
        (prov / "products.json").write_text(json.dumps(products), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_missing_service_and_feature_kind(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        services = json.loads((prov / "services.json").read_text(encoding="utf-8"))
        del services["services"][0]["kind"]
        (prov / "services.json").write_text(json.dumps(services), encoding="utf-8")
        features = json.loads((prov / "features.json").read_text(encoding="utf-8"))
        del features["features"][0]["kind"]
        (prov / "features.json").write_text(json.dumps(features), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_rejects_unknown_service_feature_ref(self, kinds_sandbox, capsys) -> None:
        _tmp, _root, prov = kinds_sandbox
        services = json.loads((prov / "services.json").read_text(encoding="utf-8"))
        services["services"][0]["features"] = ["ghost_feat", 1]
        (prov / "services.json").write_text(json.dumps(services), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1
        assert "ghost_feat" in capsys.readouterr().out

    def test_warns_on_duplicate_service_kind(self, kinds_sandbox, capsys) -> None:
        _tmp, _root, prov = kinds_sandbox
        services = json.loads((prov / "services.json").read_text(encoding="utf-8"))
        services["services"].append({**services["services"][0], "id": "svc_dup"})
        (prov / "services.json").write_text(json.dumps(services), encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 0
        out = capsys.readouterr().out
        assert "WARNING" in out
        assert "service kind 'tracking'" in out

    def test_load_failure_reports_error(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        (prov / "products.json").write_text("{not json", encoding="utf-8")
        assert validate_kinds(write_mapping_doc=False) == 1

    def test_missing_catalog_file_reports_error(self, kinds_sandbox) -> None:
        _tmp, _root, prov = kinds_sandbox
        (prov / "products.json").unlink()
        assert validate_kinds(write_mapping_doc=False) == 1
