"""Tests for porto_id validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validators.porto_ids import (
    MAPPING_DOC,
    REQUIRED_PROVIDER_SCHEMAS,
    _porto_ids_by_entity,
    _product_ids,
    _render_mapping_doc,
    _service_ids,
    validate_porto_ids,
)

_SCHEMA_SRC = Path(__file__).parent.parent / "porto_data/schemas/porto_ids.schema.json"


def _write_porto_ids_schema(schemas_dir: Path) -> None:
    schemas_dir.mkdir(parents=True, exist_ok=True)
    (schemas_dir / "porto_ids.schema.json").write_text(
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
                    provider_id: {"name": "T", "country": "DE", "mark_types": ["stamp"]},
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
    _write_porto_ids_schema(root / "schemas")
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
            "provider": "testco",
            "unit": {"weight": "g"},
            "products": [
                {
                    "id": "p1",
                    "porto_id": "small",
                    "name": "P",
                    "envelope_ids": ["DL"],
                    "zones": ["domestic"],
                    "effective_from": "2026-01-01",
                    "effective_to": None,
                    "mark_type": "stamp",
                    "tracking_mode": "optional",
                }
            ],
        },
        "services": {
            "file_type": "services",
            "provider": "testco",
            "services": [
                {
                    "id": "svc_native",
                    "porto_id": "tracking",
                    "name": "S",
                    "label": "S",
                    "description": "d",
                    "features": ["f1"],
                }
            ],
        },
        "features": {
            "file_type": "features",
            "provider": "testco",
            "features": [
                {
                    "id": "f1",
                    "porto_id": "tracking_number",
                    "name": "F",
                    "label": "F",
                    "description": "d",
                }
            ],
        },
        "graph": {
            "file_type": "graph",
            "provider": "testco",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {},
            "edges": {"p1": {"zones": ["domestic"], "weight_tiers": ["W0020"]}},
            "services": ["svc_native"],
        },
        "product_prices": {
            "file_type": "product_prices",
            "provider": "testco",
            "unit": {"price": "cents", "currency": "EUR"},
            "product_prices": [],
        },
        "service_prices": {
            "file_type": "service_prices",
            "provider": "testco",
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
def porto_ids_sandbox(tmp_path: Path, monkeypatch):
    """Minimal provider tree with monkeypatched project root."""
    root = _write_registry(tmp_path)
    prov = root / "providers" / "testco"
    prov.mkdir(parents=True)
    _write_provider_files(prov)
    monkeypatch.setattr(
        "scripts.validators.porto_ids.list_provider_ids",
        lambda: ["testco"],
    )
    monkeypatch.setattr(
        "scripts.validators.porto_ids.get_project_root",
        lambda: root,
    )
    return tmp_path, root, prov


class TestPortoIdsHelpers:
    def test_service_ids_empty_inputs(self) -> None:
        assert _service_ids(None) == set()
        assert _service_ids({}) == set()

    def test_product_ids_empty_inputs(self) -> None:
        assert _product_ids(None) == set()
        assert _product_ids({}) == set()

    def test_porto_ids_by_entity_skips_non_dict_rows(self) -> None:
        assert _porto_ids_by_entity(["not-a-dict", {"id": "a", "porto_id": "small"}]) == {
            "small": ["a"]
        }


class TestPortoIdsValidator:
    def test_required_provider_schemas_count(self) -> None:
        assert len(REQUIRED_PROVIDER_SCHEMAS) == 10
        assert "schemas/graph.schema.json" in REQUIRED_PROVIDER_SCHEMAS

    def test_render_mapping_doc(self) -> None:
        doc = _render_mapping_doc(
            {
                "deutschepost": {
                    "products": [("standardbrief", "small")],
                    "services": [],
                    "features": [],
                }
            }
        )
        assert "deutschepost" in doc
        assert "`standardbrief`" in doc
        assert "`small`" in doc

    def test_validate_porto_ids_live_bundle(self, project_root: Path) -> None:
        rc = validate_porto_ids(write_mapping_doc=True)
        assert rc == 0
        mapping = project_root / "docs" / "porto_id.md"
        assert mapping.is_file()

    def test_validate_success_without_rewriting_current_mapping(
        self, porto_ids_sandbox, capsys
    ) -> None:
        _tmp, root, _prov = porto_ids_sandbox
        mapping_path = root / MAPPING_DOC
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        rc_first = validate_porto_ids(write_mapping_doc=True)
        assert rc_first == 0
        content = mapping_path.read_text(encoding="utf-8")
        rc_second = validate_porto_ids(write_mapping_doc=True)
        assert rc_second == 0
        assert "is current" in capsys.readouterr().out
        assert mapping_path.read_text(encoding="utf-8") == content

    def test_validate_updates_mapping_when_content_differs(self, porto_ids_sandbox) -> None:
        _tmp, root, _prov = porto_ids_sandbox
        mapping_path = root / MAPPING_DOC
        mapping_path.parent.mkdir(parents=True, exist_ok=True)
        mapping_path.write_text("# stale\n", encoding="utf-8")
        rc = validate_porto_ids(write_mapping_doc=True)
        assert rc == 0
        text = mapping_path.read_text(encoding="utf-8")
        assert "p1" in text
        assert text.startswith("# Porto ID mapping tables")

    def test_rejects_porto_id_in_services(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        graph = json.loads((prov / "graph.json").read_text(encoding="utf-8"))
        graph["services"] = ["tracking"]
        (prov / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_rejects_unknown_available_service(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        graph = json.loads((prov / "graph.json").read_text(encoding="utf-8"))
        graph["services"] = ["missing_svc"]
        (prov / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_rejects_porto_id_in_product_prices(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        (prov / "prices" / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "testco",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [
                        {
                            "product_id": "small",
                            "zone": "domestic",
                            "weight_tier": "W0020",
                            "price": 100,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_rejects_unknown_product_price_ref(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        (prov / "prices" / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "testco",
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
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_rejects_porto_id_in_service_prices(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        (prov / "prices" / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "provider": "testco",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [{"service_id": "tracking", "price": 50}],
                }
            ),
            encoding="utf-8",
        )
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_rejects_unknown_service_price_ref(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        (prov / "prices" / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "provider": "testco",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [{"service_id": "ghost_service", "price": 50}],
                }
            ),
            encoding="utf-8",
        )
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_skips_non_dict_and_empty_price_rows(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        (prov / "prices" / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "testco",
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
                    "provider": "testco",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": ["skip", {"price": 50}],
                }
            ),
            encoding="utf-8",
        )
        assert validate_porto_ids(write_mapping_doc=False) == 0

    def test_rejects_invalid_porto_id_on_catalog_rows(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        products = json.loads((prov / "products.json").read_text(encoding="utf-8"))
        products["products"] = [
            products["products"][0],
            "bad-row",
            {
                **products["products"][0],
                "id": "p2",
                "porto_id": "not_a_real_porto_id",
            },
        ]
        services = json.loads((prov / "services.json").read_text(encoding="utf-8"))
        services["services"] = [
            services["services"][0],
            "bad-row",
            {
                **services["services"][0],
                "id": "svc2",
                "porto_id": "not_a_real_porto_id",
            },
        ]
        features = json.loads((prov / "features.json").read_text(encoding="utf-8"))
        features["features"] = [
            features["features"][0],
            "bad-row",
            {
                **features["features"][0],
                "id": "f2",
                "porto_id": "not_a_real_porto_id",
            },
        ]
        (prov / "products.json").write_text(json.dumps(products), encoding="utf-8")
        (prov / "services.json").write_text(json.dumps(services), encoding="utf-8")
        (prov / "features.json").write_text(json.dumps(features), encoding="utf-8")
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_warns_on_duplicate_product_and_service_porto_ids(
        self, porto_ids_sandbox, capsys
    ) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        products = json.loads((prov / "products.json").read_text(encoding="utf-8"))
        products["products"].append({**products["products"][0], "id": "p2"})
        services = json.loads((prov / "services.json").read_text(encoding="utf-8"))
        services["services"].append(
            {
                **services["services"][0],
                "id": "svc_dup",
                "porto_id": "tracking",
            }
        )
        (prov / "products.json").write_text(json.dumps(products), encoding="utf-8")
        (prov / "services.json").write_text(json.dumps(services), encoding="utf-8")
        assert validate_porto_ids(write_mapping_doc=False) == 0
        out = capsys.readouterr().out
        assert "WARNING" in out
        assert "product porto_id 'small'" in out
        assert "service porto_id 'tracking'" in out

    def test_load_failure_reports_error(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        (prov / "products.json").write_text("{not json", encoding="utf-8")
        assert validate_porto_ids(write_mapping_doc=False) == 1

    def test_missing_catalog_file_reports_error(self, porto_ids_sandbox) -> None:
        _tmp, _root, prov = porto_ids_sandbox
        (prov / "products.json").unlink()
        assert validate_porto_ids(write_mapping_doc=False) == 1
