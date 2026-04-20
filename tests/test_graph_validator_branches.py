"""Branch coverage for scripts.validators.graph (prints, rules, marks, load errors)."""

import json
from pathlib import Path

from scripts.validators.graph import (
    PROVIDER_RULE_KIND_METRIC_BAND_ATTACH,
    PROVIDER_RULE_METRIC_THICKNESS,
    GraphValidator,
    _print_analyze_mode,
    _print_validate_mode,
)
from tests.minimal_fixtures import minimal_restrictions_document


def _base_graph(**gs_overrides):
    return {
        "file_type": "graph",
        "provider": "deutschepost",
        "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
        "dependencies": {
            "products": {"file": "products.json", "depends_on": []},
            "zones": {"file": "zones.json", "depends_on": []},
            "weights": {"file": "weights.json", "depends_on": []},
            "services": {"file": "services.json", "depends_on": ["features.json"]},
            "features": {"file": "features.json", "depends_on": []},
            "marks": {"file": "marks.json", "depends_on": []},
            "product_prices": {
                "file": "prices/products.json",
                "depends_on": ["products.json"],
            },
            "service_prices": {
                "file": "prices/services.json",
                "depends_on": ["services.json"],
            },
            "envelopes": {"file": "envelopes.json", "depends_on": []},
            "layouts": {"file": "layouts.json", "depends_on": ["envelopes.json"]},
            "restrictions": {"file": "restrictions.json", "depends_on": []},
        },
        "edges": {},
        "lookup_rules": {},
        "global_settings": {
            "price_lookup": {
                "product_prices": {
                    "file": "prices/products.json",
                    "array": "product_prices",
                    "match": {"product_id": "x", "zone": "y", "weight_tier": "z"},
                    "description": "t",
                },
                "service_prices": {
                    "file": "prices/services.json",
                    "array": "service_prices",
                    "match": {"service_id": "x"},
                    "description": "t",
                },
            },
            **gs_overrides,
        },
    }


def _envelopes_fixture():
    return {
        "file_type": "envelopes",
        "unit": {"dimension": "mm"},
        "envelopes": [
            {
                "id": "C6",
                "label": "C6",
                "width": 162,
                "height": 114,
                "standard": "ISO269",
                "sheets": [{"sheet": "A4", "fold": "quarter", "description": "Test"}],
            }
        ],
    }


def _layouts_fixture():
    return {
        "file_type": "layouts",
        "unit": {"dimension": "mm"},
        "jurisdictions": {
            "DE": {
                "envelopes": {
                    "C6": {
                        "orientation": "landscape",
                        "layout": {
                            "print_area": {"x": 0, "y": 0, "width": 100, "height": 80},
                            "address_area": {"x": 0, "y": 0, "width": 100, "height": 80},
                            "window": {"supported": False},
                            "post_mark": {"x": 90, "y": 5},
                        },
                    }
                }
            }
        },
    }


def _default_marks():
    return {
        "file_type": "marks",
        "provider": "deutschepost",
        "default_profile": "p",
        "profiles": [{"id": "p", "mark_type": "stamp", "label": "P"}],
    }


def _default_features():
    return {
        "file_type": "features",
        "provider": "deutschepost",
        "features": [
            {
                "id": "tracking_number",
                "porto_id": "tracking_number",
                "name": "T",
                "label": "T",
                "description": "D",
            }
        ],
    }


def _write_bundle(data_dir: Path, graph: dict, docs: dict[str, dict]) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    for rel, doc in docs.items():
        path = data_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc), encoding="utf-8")


def _minimal_extras(overrides: dict[str, dict] | None = None) -> dict[str, dict]:
    base: dict[str, dict] = {
        "products.json": {"file_type": "products", "products": []},
        "zones.json": {"file_type": "zones", "zones": []},
        "weights.json": {"file_type": "weights", "weights": {}},
        "services.json": {"file_type": "services", "services": []},
        "prices/products.json": {
            "file_type": "product_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "product_prices": [],
        },
        "prices/services.json": {
            "file_type": "service_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "service_prices": [],
        },
        "envelopes.json": _envelopes_fixture(),
        "layouts.json": _layouts_fixture(),
        "marks.json": _default_marks(),
        "restrictions.json": minimal_restrictions_document(),
        "features.json": _default_features(),
    }
    if overrides:
        base.update(overrides)
    return base


def _graph_with_rules_dep(graph: dict) -> dict:
    out = dict(graph)
    deps = dict(out["dependencies"])
    deps["rules"] = {"file": "rules.json", "depends_on": []}
    out["dependencies"] = deps
    return out


class TestGraphPrintModes:
    def test_print_validate_mode_errors(self, capsys):
        r = {"errors": ["bad"], "warnings": ["w"], "fixes_needed": ["f"], "correct": []}
        assert _print_validate_mode(r, "acme") == 1
        out = capsys.readouterr().out
        assert "acme" in out and "ERROR" in out and "WARNING" in out

    def test_print_validate_mode_success_with_warnings(self, capsys):
        r = {"errors": [], "warnings": ["only"], "fixes_needed": [], "correct": []}
        assert _print_validate_mode(r) == 0
        assert "passed" in capsys.readouterr().out.lower()

    def test_print_analyze_mode_with_issues(self, capsys):
        r = {
            "errors": ["e"],
            "warnings": ["w"],
            "fixes_needed": ["f"],
            "correct": ["c"],
        }
        assert _print_analyze_mode(r, "de") == 1
        out = capsys.readouterr().out
        for label in ("ERRORS", "WARNINGS", "FIXES NEEDED", "CORRECT"):
            assert label in out

    def test_print_analyze_mode_clean(self, capsys):
        r = {"errors": [], "warnings": [], "fixes_needed": [], "correct": ["ok"]}
        assert _print_analyze_mode(r) == 0
        assert "passed" in capsys.readouterr().out.lower()


class TestGraphLoadErrors:
    def test_load_data_records_invalid_json(self, tmp_path):
        data_dir = tmp_path / "d"
        docs = _minimal_extras()
        _write_bundle(data_dir, _base_graph(available_services=[]), docs)
        (data_dir / "products.json").write_text("{not json", encoding="utf-8")
        v = GraphValidator(data_dir)
        v.load_data()
        assert any("Invalid JSON" in e for e in v.results["errors"])


class TestGraphExecutionSemantics:
    def test_label_with_tracking_none_is_error(self, tmp_path):
        data_dir = tmp_path / "d"
        products = {
            "file_type": "products",
            "products": [
                {
                    "id": "p1",
                    "name": "P",
                    "envelope_ids": ["C6"],
                    "zones": ["domestic"],
                    "effective_from": None,
                    "effective_to": None,
                    "mark_type": "label",
                    "tracking_mode": "none",
                }
            ],
        }
        docs = _minimal_extras(
            {
                "products.json": products,
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {"file_type": "weights", "weights": {"W001": {"min": 0, "max": 1}}},
                "marks.json": {
                    "file_type": "marks",
                    "provider": "deutschepost",
                    "default_profile": "p",
                    "profiles": [{"id": "p", "mark_type": "label", "label": "P"}],
                },
            }
        )
        _write_bundle(data_dir, _base_graph(available_services=[]), docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("label" in e and "none" in e for e in v.results["errors"])

    def test_optional_tracking_without_covering_service_is_error(self, tmp_path):
        data_dir = tmp_path / "d"
        products = {
            "file_type": "products",
            "products": [
                {
                    "id": "p1",
                    "name": "P",
                    "envelope_ids": ["C6"],
                    "zones": ["domestic"],
                    "effective_from": None,
                    "effective_to": None,
                    "mark_type": "stamp",
                    "tracking_mode": "optional",
                }
            ],
        }
        services = {
            "file_type": "services",
            "services": [
                {
                    "id": "no_track",
                    "porto_id": "x",
                    "name": "N",
                    "label": "L",
                    "description": "D",
                    "features": ["tracking_number"],
                    "enables_tracking": False,
                }
            ],
        }
        docs = _minimal_extras(
            {
                "products.json": products,
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {"file_type": "weights", "weights": {"W001": {"min": 0, "max": 1}}},
                "services.json": services,
            }
        )
        _write_bundle(data_dir, _base_graph(available_services=[]), docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("tracking_mode optional" in e for e in v.results["errors"])


class TestGraphMarksAndRules:
    def test_marks_wrong_file_type(self, tmp_path):
        data_dir = tmp_path / "d"
        docs = _minimal_extras(
            {"marks.json": {"file_type": "wrong", "provider": "deutschepost", "profiles": []}},
        )
        _write_bundle(data_dir, _base_graph(available_services=[]), docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("marks" in e.lower() and "file_type" in e.lower() for e in v.results["errors"])

    def test_marks_duplicate_profile_id(self, tmp_path):
        data_dir = tmp_path / "d"
        docs = _minimal_extras(
            {
                "marks.json": {
                    "file_type": "marks",
                    "provider": "deutschepost",
                    "default_profile": "a",
                    "profiles": [
                        {"id": "a", "mark_type": "stamp", "label": "A"},
                        {"id": "a", "mark_type": "stamp", "label": "Dup"},
                    ],
                },
            },
        )
        _write_bundle(data_dir, _base_graph(available_services=[]), docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("duplicate profile" in e.lower() for e in v.results["errors"])

    def test_rules_unsupported_kind(self, tmp_path):
        data_dir = tmp_path / "d"
        rules = {
            "file_type": "provider_rules",
            "provider": "deutschepost",
            "unit": {"thickness": "mm"},
            "rules": [{"id": "r1", "kind": "other", "metric": "thickness"}],
        }
        docs = _minimal_extras({"rules.json": rules})
        _write_bundle(data_dir, _graph_with_rules_dep(_base_graph(available_services=[])), docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("unsupported kind" in e for e in v.results["errors"])

    def test_rules_thickness_band_min_ge_max(self, tmp_path):
        data_dir = tmp_path / "d"
        services = {
            "file_type": "services",
            "services": [
                {
                    "id": "svc_thick",
                    "porto_id": "thickness",
                    "name": "T",
                    "label": "T",
                    "description": "D",
                    "features": ["tracking_number"],
                    "enables_tracking": False,
                }
            ],
        }
        rules = {
            "file_type": "provider_rules",
            "provider": "deutschepost",
            "unit": {"thickness": "mm"},
            "rules": [
                {
                    "id": "thick",
                    "kind": PROVIDER_RULE_KIND_METRIC_BAND_ATTACH,
                    "metric": PROVIDER_RULE_METRIC_THICKNESS,
                    "product_ids": [],
                    "service_id": "svc_thick",
                    "min_exclusive": 50,
                    "max_inclusive": 20,
                }
            ],
        }
        docs = _minimal_extras(
            {
                "services.json": services,
                "prices/services.json": {
                    "file_type": "service_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "service_prices": [
                        {"service_id": "svc_thick", "price": [{"amount": 1}]},
                    ],
                },
                "rules.json": rules,
            },
        )
        _write_bundle(
            data_dir,
            _graph_with_rules_dep(_base_graph(available_services=["svc_thick"])),
            docs,
        )
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("min_exclusive" in e for e in v.results["errors"])


class TestGraphCircularDeps:
    def test_circular_products_product_prices_emits_warning(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(available_services=[]))
        deps = dict(graph["dependencies"])
        deps["products"] = {"file": "products.json", "depends_on": ["prices/products.json"]}
        deps["product_prices"] = {
            "file": "prices/products.json",
            "depends_on": ["products.json"],
        }
        graph["dependencies"] = deps
        _write_bundle(data_dir, graph, _minimal_extras())
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("Circular dependency" in w for w in v.results["warnings"])


class TestGraphLookupFileRef:
    def test_wrong_product_prices_file_in_graph_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        gs = dict(_base_graph()["global_settings"])
        gs["price_lookup"] = dict(gs["price_lookup"])
        gs["price_lookup"]["product_prices"] = dict(gs["price_lookup"]["product_prices"])
        gs["price_lookup"]["product_prices"]["file"] = "prices/wrong.json"
        graph = _base_graph()
        graph["global_settings"] = gs
        _write_bundle(data_dir, graph, _minimal_extras())
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("wrong.json" in e or "should be" in e for e in v.results["errors"])


def _product_letter_fixture(**overrides):
    row = {
        "id": "p1",
        "name": "P",
        "envelope_ids": ["C6"],
        "zones": ["domestic"],
        "effective_from": None,
        "effective_to": None,
        "mark_type": "stamp",
        "tracking_mode": "none",
    }
    row.update(overrides)
    return {"file_type": "products", "products": [row]}


class TestGraphEdgesRefs:
    """Edges → products / zones / weight_tiers resolution errors."""

    def test_edges_unknown_product_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(available_services=[]))
        graph["edges"] = {"ghost": {"zones": ["domestic"], "weight_tiers": ["W1"]}}
        docs = _minimal_extras(
            {
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {"file_type": "weights", "weights": {"W1": {"min": 0, "max": 50}}},
            }
        )
        _write_bundle(data_dir, graph, docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("edges" in e and "ghost" in e for e in v.results["errors"])

    def test_edges_unknown_zone_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(available_services=[]))
        graph["edges"] = {"p1": {"zones": ["nowhere"], "weight_tiers": ["W1"]}}
        docs = _minimal_extras(
            {
                "products.json": _product_letter_fixture(),
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {"file_type": "weights", "weights": {"W1": {"min": 0, "max": 50}}},
            }
        )
        _write_bundle(data_dir, graph, docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("nowhere" in e and "zones" in e.lower() for e in v.results["errors"])

    def test_edges_unknown_weight_tier_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(available_services=[]))
        graph["edges"] = {"p1": {"zones": ["domestic"], "weight_tiers": ["W999"]}}
        docs = _minimal_extras(
            {
                "products.json": _product_letter_fixture(),
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {"file_type": "weights", "weights": {"W1": {"min": 0, "max": 50}}},
            }
        )
        _write_bundle(data_dir, graph, docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("W999" in e and "weight" in e.lower() for e in v.results["errors"])
