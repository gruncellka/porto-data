"""Unit and integration coverage for ``scripts.validators.graph`` package modules."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.validators.base import ValidationResults
from scripts.validators.graph import GraphValidator
from scripts.validators.graph.dependencies import run_validate_price_dependencies
from scripts.validators.graph.edges import run_validate_edges
from scripts.validators.graph.envelope_geometry import (
    envelope_rect_complete,
    resolve_envelope_layout_row,
)
from scripts.validators.graph.layouts import (
    envelope_layout_geometry_errors,
    run_validate_envelope_address_window,
    run_validate_envelope_ids,
    run_validate_layout_refs,
)


def _results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


class TestGraphEdgesBranches:
    def test_weight_tier_on_product_missing_from_edges_fixes_needed(self) -> None:
        r = _results()
        graph = {
            "edges": {"products": {"p1": {"zones": ["z1"], "weight_tiers": ["W1"]}}, "marks": {}}
        }
        product_dict = {
            "p1": {"id": "p1", "zones": ["z1"], "weight_tier": "W2"},
        }
        run_validate_edges(
            r,
            graph=graph,
            product_dict=product_dict,
            zone_ids={"z1": {}},
            weight_tier_ids={"W1", "W2"},
            product_prices=[],
        )
        assert any("not in edges" in f and "W2" in f for f in r["fixes_needed"])

    def test_price_weight_tier_not_in_edges_fixes_needed(self) -> None:
        r = _results()
        graph = {
            "edges": {"products": {"p1": {"zones": ["z1"], "weight_tiers": ["W1"]}}, "marks": {}}
        }
        product_dict = {"p1": {"id": "p1", "zones": ["z1"], "weight_tier": "W1"}}
        product_prices = [{"product_id": "p1", "zone": "z1", "weight_tier": "W9"}]
        run_validate_edges(
            r,
            graph=graph,
            product_dict=product_dict,
            zone_ids={"z1": {}},
            weight_tier_ids={"W1", "W9"},
            product_prices=product_prices,
        )
        assert any("W9" in f and "not in edges" in f for f in r["fixes_needed"])

    def test_all_price_weight_tiers_match_edges_correct(self) -> None:
        r = _results()
        graph = {
            "edges": {
                "products": {"p1": {"zones": ["z1"], "weight_tiers": ["W1", "W2"]}},
                "marks": {},
            }
        }
        product_dict = {"p1": {"id": "p1", "zones": ["z1"], "weight_tier": "W1"}}
        product_prices = [
            {"product_id": "p1", "weight_tier": "W1"},
            {"product_id": "p1", "weight_tier": "W2"},
        ]
        run_validate_edges(
            r,
            graph=graph,
            product_dict=product_dict,
            zone_ids={"z1": {}},
            weight_tier_ids={"W1", "W2"},
            product_prices=product_prices,
        )
        assert any("all price weight_tiers match edges" in c for c in r["correct"])


class TestEnvelopeGeometryResolve:
    def test_resolve_row_none_paths(self) -> None:
        assert resolve_envelope_layout_row({}, "DE", "C6") is None
        assert resolve_envelope_layout_row({"DE": "x"}, "DE", "C6") is None
        assert resolve_envelope_layout_row({"DE": {}}, "DE", "C6") is None
        assert resolve_envelope_layout_row({"DE": {"envelopes": []}}, "DE", "C6") is None
        assert resolve_envelope_layout_row({"DE": {"envelopes": {}}}, "DE", "C6") is None
        assert resolve_envelope_layout_row({"DE": {"envelopes": {"C6": "bad"}}}, "DE", "C6") is None
        row = resolve_envelope_layout_row(
            {"DE": {"envelopes": {"C6": {"orientation": None, "layout": {}}}}},
            "DE",
            "C6",
        )
        assert row is None

    def test_envelope_rect_complete_rejects_non_dict(self) -> None:
        assert envelope_rect_complete(None) is False
        assert envelope_rect_complete({"x": 0, "y": 0, "width": 1}) is False


class TestLayoutsPureAndRunners:
    def test_geometry_bad_window_area(self) -> None:
        err = envelope_layout_geometry_errors(
            layout_fingerprint_id="F",
            path="layouts.json (DE, F)",
            env={
                "layout": {
                    "window": {
                        "supported": True,
                        "area": {"x": 0.5, "y": 0, "width": 1, "height": 1},
                    },
                }
            },
        )
        assert len(err) == 1 and "window.area" in err[0]

    def test_geometry_no_window_and_force_window_legacy(self) -> None:
        err = envelope_layout_geometry_errors(
            layout_fingerprint_id="F",
            path="p",
            env={
                "supports_window": False,
                "window_supported": True,
            },
        )
        assert any("supports_window" in m and "window_supported" in m for m in err)

    def test_geometry_no_window_with_window_area_legacy(self) -> None:
        err = envelope_layout_geometry_errors(
            layout_fingerprint_id="F",
            path="p",
            env={
                "supports_window": False,
                "window_area": {"x": 0, "y": 0, "width": 5, "height": 5},
            },
        )
        assert any("omit window" in m for m in err)

    def test_geometry_force_window_requires_area_nested(self) -> None:
        err = envelope_layout_geometry_errors(
            layout_fingerprint_id="F",
            path="p",
            env={
                "layout": {
                    "window": {"supported": True},
                }
            },
        )
        assert any("requires window.area" in m for m in err)

    def test_geometry_valid_no_window_nested(self) -> None:
        err = envelope_layout_geometry_errors(
            layout_fingerprint_id="F",
            path="p",
            env={
                "layout": {
                    "window": {"supported": False},
                }
            },
        )
        assert err == []

    def test_run_address_window_skips_non_dict_jurisdiction_blocks(self) -> None:
        r = _results()
        run_validate_envelope_address_window(
            r,
            envelope_layouts={
                "jurisdictions": {
                    "DE": "not-a-dict",
                    "CH": {"envelopes": "not-a-dict"},
                }
            },
        )
        assert not r["errors"]

    def test_run_layout_references_skips_malformed_blocks(self) -> None:
        r = _results()
        run_validate_layout_refs(r, envelope_layouts=None, envelopes={})
        assert not r["errors"]
        run_validate_layout_refs(
            r,
            envelope_layouts={"jurisdictions": []},
            envelopes={"envelopes": [{"id": "C6"}]},
        )
        run_validate_layout_refs(
            r,
            envelope_layouts={
                "jurisdictions": {
                    "DE": "bad",
                    "FR": {"envelopes": []},
                    "IT": {"envelopes": {"C6": []}},
                }
            },
            envelopes={"envelopes": [{"id": "C6"}]},
        )
        assert not r["errors"]

    def test_run_address_window_early_exits(self) -> None:
        r = _results()
        run_validate_envelope_address_window(r, envelope_layouts=None)
        run_validate_envelope_address_window(r, envelope_layouts={})
        run_validate_envelope_address_window(r, envelope_layouts={"jurisdictions": "bad"})
        assert not r["errors"]

    def test_run_address_window_appends_geometry_errors(self) -> None:
        r = _results()
        run_validate_envelope_address_window(
            r,
            envelope_layouts={
                "jurisdictions": {
                    "DE": {
                        "envelopes": {
                            "C6": {
                                "orientation": "landscape",
                                "layout": {
                                    "window": {"supported": True},
                                    "post_mark": {"x": 0, "y": 0},
                                },
                            }
                        }
                    }
                }
            },
        )
        assert r["errors"]

    def test_run_product_envelope_ids_skips_and_errors(self) -> None:
        r = _results()
        run_validate_envelope_ids(r, envelopes=None, products={})
        assert not r["errors"]
        run_validate_envelope_ids(
            r,
            envelopes={"envelopes": [{"id": "C6"}]},
            products={"products": ["not-a-dict", {"id": "p1", "envelope_ids": ["Nope"]}]},
        )
        assert any("Nope" in e for e in r["errors"])


class TestPriceDependenciesRunner:
    _deps_graph = {
        "dependencies": {
            "product_prices": {"file": "prices/products.json", "depends_on": []},
            "service_prices": {"file": "prices/services.json", "depends_on": []},
        }
    }

    def test_price_dependencies_skips_when_dependencies_not_dict(self) -> None:
        r = _results()
        run_validate_price_dependencies(
            r,
            graph={"dependencies": []},
            shared_bundle_subdir=Path("/a"),
            bundle_root=Path("/a"),
            provider_dir=Path("/a/p"),
            all_data_files=set(),
            product_prices_doc=None,
            service_prices_doc=None,
            product_prices=[],
            service_prices=[],
        )
        assert not r["errors"] and not r["warnings"] and not r["fixes_needed"] and not r["correct"]

    def test_file_reference_missing_on_disk_error(self) -> None:
        r = _results()
        run_validate_price_dependencies(
            r,
            graph=self._deps_graph,
            shared_bundle_subdir=Path("/tmp"),
            bundle_root=Path("/tmp"),
            provider_dir=Path("/tmp/deutschepost"),
            all_data_files=set(),
            product_prices_doc={"product_prices": []},
            service_prices_doc={"service_prices": []},
            product_prices=[],
            service_prices=[],
        )
        assert any("does not exist" in e for e in r["errors"])

    def test_price_array_structure_mismatch_errors(self) -> None:
        r = _results()
        run_validate_price_dependencies(
            r,
            graph=self._deps_graph,
            shared_bundle_subdir=Path("/x"),
            bundle_root=Path("/x"),
            provider_dir=Path("/x"),
            all_data_files={"prices/products.json", "prices/services.json"},
            product_prices_doc={"product_prices": "not-a-list"},
            service_prices_doc={"service_prices": []},
            product_prices=[],
            service_prices=[],
        )
        assert any("Price file for product_prices missing" in e for e in r["errors"])

    def test_empty_product_prices_rows_warns(self) -> None:
        r = _results()
        run_validate_price_dependencies(
            r,
            graph=self._deps_graph,
            shared_bundle_subdir=Path("/x"),
            bundle_root=Path("/x"),
            provider_dir=Path("/x"),
            all_data_files={"prices/products.json", "prices/services.json"},
            product_prices_doc={"product_prices": []},
            service_prices_doc={"service_prices": [{"service_id": "s", "price": []}]},
            product_prices=[],
            service_prices=[{"service_id": "s", "price": []}],
        )
        assert any("No product_prices rows" in w for w in r["warnings"])

    def test_empty_service_prices_rows_warns(self) -> None:
        r = _results()
        run_validate_price_dependencies(
            r,
            graph=self._deps_graph,
            shared_bundle_subdir=Path("/x"),
            bundle_root=Path("/x"),
            provider_dir=Path("/x"),
            all_data_files={"prices/products.json", "prices/services.json"},
            product_prices_doc={
                "product_prices": [
                    {"product_id": "p", "zone": "z", "weight_tier": "w", "price": []}
                ]
            },
            service_prices_doc={"service_prices": []},
            product_prices=[{"product_id": "p", "zone": "z", "weight_tier": "w", "price": []}],
            service_prices=[],
        )
        assert any("No service_prices rows" in w for w in r["warnings"])

    def test_wrong_dependency_path_errors(self) -> None:
        r = _results()
        run_validate_price_dependencies(
            r,
            graph={
                "dependencies": {
                    "product_prices": {"file": "prices/wrong.json", "depends_on": []},
                    "service_prices": {"file": "prices/services.json", "depends_on": []},
                }
            },
            shared_bundle_subdir=Path("/x"),
            bundle_root=Path("/x"),
            provider_dir=Path("/x"),
            all_data_files={"prices/products.json", "prices/services.json"},
            product_prices_doc={"product_prices": []},
            service_prices_doc={"service_prices": []},
            product_prices=[],
            service_prices=[],
        )
        assert any("should be" in e for e in r["errors"])

    def test_missing_row_keys_errors(self) -> None:
        r = _results()
        run_validate_price_dependencies(
            r,
            graph=self._deps_graph,
            shared_bundle_subdir=Path("/x"),
            bundle_root=Path("/x"),
            provider_dir=Path("/x"),
            all_data_files={"prices/products.json", "prices/services.json"},
            product_prices_doc={"product_prices": [{"product_id": "p", "zone": "z"}]},
            service_prices_doc={"service_prices": []},
            product_prices=[{"product_id": "p", "zone": "z"}],
            service_prices=[],
        )
        assert any("weight_tier" in e for e in r["errors"])


class TestGraphValidatorEarlyReturnsAndBranches:
    def test_validate_methods_noop_when_graph_unloaded(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "d"
        data_dir.mkdir()
        v = GraphValidator(data_dir=data_dir)
        v.graph = None
        v.validate_price_dependencies()
        v.validate_edges()
        v.validate_products_in_edges()
        v.validate_zones_and_weight_tiers()
        v.validate_services()
        v.validate_dependencies()
        v.validate_circular_dependencies()
        assert not v.results["errors"] and not v.results["warnings"]

    def test_circular_deps_skips_when_dependencies_not_dict(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "d"
        data_dir.mkdir()
        graph = {
            "file_type": "graph",
            "provider": "x",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {"products": {"file": "products.json", "depends_on": []}},
            "edges": {"products": {}, "marks": {}},
            "services": ["svc"],
        }
        (data_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        (data_dir / "products.json").write_text(
            json.dumps({"file_type": "products", "unit": {"weight": "g"}, "products": []}),
            encoding="utf-8",
        )
        (data_dir / "zones.json").write_text(
            json.dumps({"file_type": "zones", "zones": []}), encoding="utf-8"
        )
        (data_dir / "weights.json").write_text(
            json.dumps({"file_type": "weights", "unit": {"weight": "g"}, "weights": {}}),
            encoding="utf-8",
        )
        (data_dir / "services.json").write_text(
            json.dumps({"file_type": "services", "services": []}), encoding="utf-8"
        )
        (data_dir / "marks.json").write_text(
            json.dumps(
                {
                    "file_type": "marks",
                    "provider": "x",
                    "default_profile": "p",
                    "profiles": [{"id": "p", "mark_type": "stamp"}],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "envelopes.json").write_text(
            json.dumps({"file_type": "envelopes", "unit": {"dimension": "mm"}, "envelopes": []}),
            encoding="utf-8",
        )
        (data_dir / "layouts.json").write_text(
            json.dumps({"file_type": "layouts", "unit": {"dimension": "mm"}, "jurisdictions": {}}),
            encoding="utf-8",
        )
        (data_dir / "restrictions.json").write_text(
            json.dumps({"file_type": "restrictions", "version": 1, "destinations": []}),
            encoding="utf-8",
        )
        (data_dir / "features.json").write_text(
            json.dumps({"file_type": "features", "provider": "x", "features": []}), encoding="utf-8"
        )
        prices = data_dir / "prices"
        prices.mkdir()
        (prices / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "x",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [],
                }
            ),
            encoding="utf-8",
        )
        (prices / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "provider": "x",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [],
                }
            ),
            encoding="utf-8",
        )
        v = GraphValidator(data_dir=data_dir)
        v.load_data()
        assert v.graph is not None
        v.graph["dependencies"] = "bad"  # type: ignore[assignment]
        v.validate_circular_dependencies()
        assert not v.results["warnings"]

    def test_service_price_unknown_service_errors(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "d"
        data_dir.mkdir()
        graph = {
            "file_type": "graph",
            "provider": "deutschepost",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {
                "products": {"file": "products.json", "depends_on": []},
                "zones": {"file": "zones.json", "depends_on": []},
                "weights": {"file": "weights.json", "depends_on": []},
                "services": {"file": "services.json", "depends_on": []},
                "marks": {"file": "marks.json", "depends_on": []},
                "product_prices": {"file": "prices/products.json", "depends_on": ["products.json"]},
                "service_prices": {"file": "prices/services.json", "depends_on": ["services.json"]},
                "envelopes": {"file": "envelopes.json", "depends_on": []},
                "layouts": {"file": "layouts.json", "depends_on": ["envelopes.json"]},
                "restrictions": {"file": "restrictions.json", "depends_on": []},
                "features": {"file": "features.json", "depends_on": []},
            },
            "edges": {"products": {}, "marks": {}},
            "services": ["einschreiben"],
        }
        (data_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        (data_dir / "products.json").write_text(
            json.dumps({"file_type": "products", "unit": {"weight": "g"}, "products": []}),
            encoding="utf-8",
        )
        (data_dir / "zones.json").write_text(
            json.dumps({"file_type": "zones", "zones": []}), encoding="utf-8"
        )
        (data_dir / "weights.json").write_text(
            json.dumps({"file_type": "weights", "unit": {"weight": "g"}, "weights": {}}),
            encoding="utf-8",
        )
        (data_dir / "services.json").write_text(
            json.dumps({"file_type": "services", "services": []}),
            encoding="utf-8",
        )
        (data_dir / "marks.json").write_text(
            json.dumps(
                {
                    "file_type": "marks",
                    "provider": "deutschepost",
                    "default_profile": "p",
                    "profiles": [{"id": "p", "mark_type": "stamp"}],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "envelopes.json").write_text(
            json.dumps({"file_type": "envelopes", "unit": {"dimension": "mm"}, "envelopes": []}),
            encoding="utf-8",
        )
        (data_dir / "layouts.json").write_text(
            json.dumps({"file_type": "layouts", "unit": {"dimension": "mm"}, "jurisdictions": {}}),
            encoding="utf-8",
        )
        (data_dir / "restrictions.json").write_text(
            json.dumps({"file_type": "restrictions", "version": 1, "destinations": []}),
            encoding="utf-8",
        )
        (data_dir / "features.json").write_text(
            json.dumps({"file_type": "features", "provider": "deutschepost", "features": []}),
            encoding="utf-8",
        )
        prices = data_dir / "prices"
        prices.mkdir()
        (prices / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [],
                }
            ),
            encoding="utf-8",
        )
        (prices / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [{"service_id": "ghost", "price": []}],
                }
            ),
            encoding="utf-8",
        )
        v = GraphValidator(data_dir=data_dir)
        v.validate_all()
        assert any("ghost" in e and "service_prices" in e for e in v.results["errors"])


def test_subpackage_import_graph_constants() -> None:
    from scripts.validators.graph.constants import EXPECTED_WEIGHT_UNIT

    assert EXPECTED_WEIGHT_UNIT == "g"


class TestGraphValidatorMoreBranches:
    def test_execution_semantics_returns_when_products_or_services_none(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "d"
        data_dir.mkdir()
        graph = {
            "file_type": "graph",
            "provider": "deutschepost",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {
                "products": {"file": "products.json", "depends_on": []},
                "zones": {"file": "zones.json", "depends_on": []},
                "weights": {"file": "weights.json", "depends_on": []},
                "services": {"file": "services.json", "depends_on": []},
                "marks": {"file": "marks.json", "depends_on": []},
                "product_prices": {"file": "prices/products.json", "depends_on": ["products.json"]},
                "service_prices": {"file": "prices/services.json", "depends_on": ["services.json"]},
                "envelopes": {"file": "envelopes.json", "depends_on": []},
                "layouts": {"file": "layouts.json", "depends_on": ["envelopes.json"]},
                "restrictions": {"file": "restrictions.json", "depends_on": []},
                "features": {"file": "features.json", "depends_on": []},
            },
            "edges": {"products": {}, "marks": {}},
            "services": ["einschreiben"],
        }
        (data_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        (data_dir / "products.json").write_text(
            json.dumps({"file_type": "products", "unit": {"weight": "g"}, "products": []}),
            encoding="utf-8",
        )
        (data_dir / "zones.json").write_text(
            json.dumps({"file_type": "zones", "zones": []}), encoding="utf-8"
        )
        (data_dir / "weights.json").write_text(
            json.dumps({"file_type": "weights", "unit": {"weight": "g"}, "weights": {}}),
            encoding="utf-8",
        )
        (data_dir / "services.json").write_text(
            json.dumps({"file_type": "services", "services": []}),
            encoding="utf-8",
        )
        (data_dir / "marks.json").write_text(
            json.dumps(
                {
                    "file_type": "marks",
                    "provider": "deutschepost",
                    "default_profile": "p",
                    "profiles": [{"id": "p", "mark_type": "stamp"}],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "envelopes.json").write_text(
            json.dumps({"file_type": "envelopes", "unit": {"dimension": "mm"}, "envelopes": []}),
            encoding="utf-8",
        )
        (data_dir / "layouts.json").write_text(
            json.dumps({"file_type": "layouts", "unit": {"dimension": "mm"}, "jurisdictions": {}}),
            encoding="utf-8",
        )
        (data_dir / "restrictions.json").write_text(
            json.dumps({"file_type": "restrictions", "version": 1, "destinations": []}),
            encoding="utf-8",
        )
        (data_dir / "features.json").write_text(
            json.dumps({"file_type": "features", "provider": "deutschepost", "features": []}),
            encoding="utf-8",
        )
        prices = data_dir / "prices"
        prices.mkdir()
        (prices / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [],
                }
            ),
            encoding="utf-8",
        )
        (prices / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [],
                }
            ),
            encoding="utf-8",
        )
        v = GraphValidator(data_dir=data_dir)
        v.load_data()
        products_backup = v.products
        services_backup = v.services
        v.products = None
        v.validate_execution_semantics()
        v.products = products_backup
        v.services = None
        v.validate_execution_semantics()
        v.services = services_backup

    def test_marks_invalid_file_type_errors(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "d"
        data_dir.mkdir()
        graph = {
            "file_type": "graph",
            "provider": "deutschepost",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {
                "products": {"file": "products.json", "depends_on": []},
                "zones": {"file": "zones.json", "depends_on": []},
                "weights": {"file": "weights.json", "depends_on": []},
                "services": {"file": "services.json", "depends_on": []},
                "marks": {"file": "marks.json", "depends_on": []},
                "product_prices": {"file": "prices/products.json", "depends_on": ["products.json"]},
                "service_prices": {"file": "prices/services.json", "depends_on": ["services.json"]},
                "envelopes": {"file": "envelopes.json", "depends_on": []},
                "layouts": {"file": "layouts.json", "depends_on": ["envelopes.json"]},
                "restrictions": {"file": "restrictions.json", "depends_on": []},
                "features": {"file": "features.json", "depends_on": []},
            },
            "edges": {"products": {}, "marks": {}},
            "services": ["einschreiben"],
        }
        (data_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        (data_dir / "products.json").write_text(
            json.dumps({"file_type": "products", "unit": {"weight": "g"}, "products": []}),
            encoding="utf-8",
        )
        (data_dir / "zones.json").write_text(
            json.dumps({"file_type": "zones", "zones": []}), encoding="utf-8"
        )
        (data_dir / "weights.json").write_text(
            json.dumps({"file_type": "weights", "unit": {"weight": "g"}, "weights": {}}),
            encoding="utf-8",
        )
        (data_dir / "services.json").write_text(
            json.dumps({"file_type": "services", "services": []}),
            encoding="utf-8",
        )
        (data_dir / "marks.json").write_text(
            json.dumps({"file_type": "not_marks", "provider": "deutschepost"}),
            encoding="utf-8",
        )
        (data_dir / "envelopes.json").write_text(
            json.dumps({"file_type": "envelopes", "unit": {"dimension": "mm"}, "envelopes": []}),
            encoding="utf-8",
        )
        (data_dir / "layouts.json").write_text(
            json.dumps({"file_type": "layouts", "unit": {"dimension": "mm"}, "jurisdictions": {}}),
            encoding="utf-8",
        )
        (data_dir / "restrictions.json").write_text(
            json.dumps({"file_type": "restrictions", "version": 1, "destinations": []}),
            encoding="utf-8",
        )
        (data_dir / "features.json").write_text(
            json.dumps({"file_type": "features", "provider": "deutschepost", "features": []}),
            encoding="utf-8",
        )
        prices = data_dir / "prices"
        prices.mkdir()
        (prices / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [],
                }
            ),
            encoding="utf-8",
        )
        (prices / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [],
                }
            ),
            encoding="utf-8",
        )
        v = GraphValidator(data_dir=data_dir)
        v.validate_all()
        assert any("file_type must be 'marks'" in e for e in v.results["errors"])

    def test_service_price_row_without_service_id_skipped(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "d"
        data_dir.mkdir()
        graph = {
            "file_type": "graph",
            "provider": "deutschepost",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {
                "products": {"file": "products.json", "depends_on": []},
                "zones": {"file": "zones.json", "depends_on": []},
                "weights": {"file": "weights.json", "depends_on": []},
                "services": {"file": "services.json", "depends_on": []},
                "marks": {"file": "marks.json", "depends_on": []},
                "product_prices": {"file": "prices/products.json", "depends_on": ["products.json"]},
                "service_prices": {"file": "prices/services.json", "depends_on": ["services.json"]},
                "envelopes": {"file": "envelopes.json", "depends_on": []},
                "layouts": {"file": "layouts.json", "depends_on": ["envelopes.json"]},
                "restrictions": {"file": "restrictions.json", "depends_on": []},
                "features": {"file": "features.json", "depends_on": []},
            },
            "edges": {"products": {}, "marks": {}},
            "services": ["einschreiben"],
        }
        (data_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
        (data_dir / "products.json").write_text(
            json.dumps({"file_type": "products", "unit": {"weight": "g"}, "products": []}),
            encoding="utf-8",
        )
        (data_dir / "zones.json").write_text(
            json.dumps({"file_type": "zones", "zones": []}), encoding="utf-8"
        )
        (data_dir / "weights.json").write_text(
            json.dumps({"file_type": "weights", "unit": {"weight": "g"}, "weights": {}}),
            encoding="utf-8",
        )
        (data_dir / "services.json").write_text(
            json.dumps({"file_type": "services", "services": []}),
            encoding="utf-8",
        )
        (data_dir / "marks.json").write_text(
            json.dumps(
                {
                    "file_type": "marks",
                    "provider": "deutschepost",
                    "default_profile": "p",
                    "profiles": [{"id": "p", "mark_type": "stamp"}],
                }
            ),
            encoding="utf-8",
        )
        (data_dir / "envelopes.json").write_text(
            json.dumps({"file_type": "envelopes", "unit": {"dimension": "mm"}, "envelopes": []}),
            encoding="utf-8",
        )
        (data_dir / "layouts.json").write_text(
            json.dumps({"file_type": "layouts", "unit": {"dimension": "mm"}, "jurisdictions": {}}),
            encoding="utf-8",
        )
        (data_dir / "restrictions.json").write_text(
            json.dumps({"file_type": "restrictions", "version": 1, "destinations": []}),
            encoding="utf-8",
        )
        (data_dir / "features.json").write_text(
            json.dumps({"file_type": "features", "provider": "deutschepost", "features": []}),
            encoding="utf-8",
        )
        prices = data_dir / "prices"
        prices.mkdir()
        (prices / "products.json").write_text(
            json.dumps(
                {
                    "file_type": "product_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [],
                }
            ),
            encoding="utf-8",
        )
        (prices / "services.json").write_text(
            json.dumps(
                {
                    "file_type": "service_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [{"price": []}],
                }
            ),
            encoding="utf-8",
        )
        v = GraphValidator(data_dir=data_dir)
        v.validate_all()
        assert not any("ghost" in e for e in v.results["errors"])
