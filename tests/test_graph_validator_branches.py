"""Branch coverage for ``scripts.validators.graph`` (prints, rules, marks, load errors)."""

import json
from pathlib import Path

import pytest

from scripts.validators.graph import (
    PROVIDER_RULE_METRIC_THICKNESS,
    RULE_KIND_BAND,
    GraphValidator,
    _envelope_validation_views,
    _print_analyze_mode,
    _print_validate_mode,
    validate_graph,
)
from tests.minimal_fixtures import minimal_restrictions_document


def _base_graph(**overrides):
    graph = {
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
        "edges": {"products": {}, "marks": {}},
        "services": ["einschreiben"],
        "strategy": "service",
    }
    graph.update(overrides)
    return graph


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
        "products.json": {"file_type": "products", "unit": {"weight": "g"}, "products": []},
        "zones.json": {"file_type": "zones", "zones": []},
        "weights.json": {"file_type": "weights", "unit": {"weight": "g"}, "weights": {}},
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
        _write_bundle(data_dir, _base_graph(services=[]), docs)
        (data_dir / "products.json").write_text("{not json", encoding="utf-8")
        v = GraphValidator(data_dir)
        v.load_data()
        assert any("Invalid JSON" in e for e in v.results["errors"])


class TestGraphExecutionSemantics:
    def test_label_with_tracking_none_is_error(self, tmp_path):
        data_dir = tmp_path / "d"
        products = {
            "file_type": "products",
            "unit": {"weight": "g"},
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
                "weights.json": {
                    "file_type": "weights",
                    "unit": {"weight": "g"},
                    "weights": {"W001": {"min": 0, "max": 1}},
                },
                "marks.json": {
                    "file_type": "marks",
                    "provider": "deutschepost",
                    "default_profile": "p",
                    "profiles": [{"id": "p", "mark_type": "label", "label": "P"}],
                },
            }
        )
        _write_bundle(
            data_dir,
            _base_graph(
                services=[],
                edges={"products": {}, "marks": {"domestic": {"profile": "p"}}},
            ),
            docs,
        )
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("label" in e and "none" in e for e in v.results["errors"])

    def test_optional_tracking_without_covering_service_is_error(self, tmp_path):
        data_dir = tmp_path / "d"
        products = {
            "file_type": "products",
            "unit": {"weight": "g"},
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
                "weights.json": {
                    "file_type": "weights",
                    "unit": {"weight": "g"},
                    "weights": {"W001": {"min": 0, "max": 1}},
                },
                "services.json": services,
            }
        )
        _write_bundle(data_dir, _base_graph(services=[]), docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("tracking_mode optional" in e for e in v.results["errors"])


class TestGraphMarksAndRules:
    def test_marks_wrong_file_type(self, tmp_path):
        data_dir = tmp_path / "d"
        docs = _minimal_extras(
            {"marks.json": {"file_type": "wrong", "provider": "deutschepost", "profiles": []}},
        )
        _write_bundle(data_dir, _base_graph(services=[]), docs)
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
        _write_bundle(data_dir, _base_graph(services=[]), docs)
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
        _write_bundle(data_dir, _graph_with_rules_dep(_base_graph(services=[])), docs)
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
                    "kind": RULE_KIND_BAND,
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
            _graph_with_rules_dep(_base_graph(services=["svc_thick"])),
            docs,
        )
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("min_exclusive" in e for e in v.results["errors"])


class TestGraphCircularDeps:
    def test_circular_products_product_prices_emits_warning(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(services=[]))
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


class TestGraphPriceDependencyRefs:
    def test_wrong_product_prices_file_in_dependencies_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = _base_graph()
        deps = dict(graph["dependencies"])
        deps["product_prices"] = {
            "file": "prices/wrong.json",
            "depends_on": ["products.json"],
        }
        graph["dependencies"] = deps
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
    return {"file_type": "products", "unit": {"weight": "g"}, "products": [row]}


class TestGraphEdgesRefs:
    """Edges → products / zones / weight_tiers resolution errors."""

    def test_edges_unknown_product_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(services=[]))
        graph["edges"] = {
            "products": {"ghost": {"zones": ["domestic"], "weight_tiers": ["W1"]}},
            "marks": {},
        }
        docs = _minimal_extras(
            {
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {
                    "file_type": "weights",
                    "unit": {"weight": "g"},
                    "weights": {"W1": {"min": 0, "max": 50}},
                },
            }
        )
        _write_bundle(data_dir, graph, docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("edges" in e and "ghost" in e for e in v.results["errors"])

    def test_edges_unknown_zone_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(services=[]))
        graph["edges"] = {
            "products": {"p1": {"zones": ["nowhere"], "weight_tiers": ["W1"]}},
            "marks": {},
        }
        docs = _minimal_extras(
            {
                "products.json": _product_letter_fixture(),
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {
                    "file_type": "weights",
                    "unit": {"weight": "g"},
                    "weights": {"W1": {"min": 0, "max": 50}},
                },
            }
        )
        _write_bundle(data_dir, graph, docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("nowhere" in e and "zones" in e.lower() for e in v.results["errors"])

    def test_edges_unknown_weight_tier_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(services=[]))
        graph["edges"] = {
            "products": {"p1": {"zones": ["domestic"], "weight_tiers": ["W999"]}},
            "marks": {},
        }
        docs = _minimal_extras(
            {
                "products.json": _product_letter_fixture(),
                "zones.json": {"file_type": "zones", "zones": [{"id": "domestic", "label": "D"}]},
                "weights.json": {
                    "file_type": "weights",
                    "unit": {"weight": "g"},
                    "weights": {"W1": {"min": 0, "max": 50}},
                },
            }
        )
        _write_bundle(data_dir, graph, docs)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("W999" in e and "weight" in e.lower() for e in v.results["errors"])


class TestGraphValidateGraphEntrypoint:
    """``validate_graph()`` CLI wrapper (prints + exit code)."""

    def test_validate_graph_validate_mode_zero_on_warnings_only(self, tmp_path, capsys):
        data_dir = tmp_path / "d"
        _write_bundle(data_dir, _base_graph(services=[]), _minimal_extras())
        assert validate_graph(data_dir=data_dir, analyze=False) == 0
        out = capsys.readouterr().out
        assert "Validating graph.json" in out and "passed" in out.lower()

    def test_validate_graph_analyze_mode_prints_sections(self, tmp_path, capsys):
        data_dir = tmp_path / "d"
        _write_bundle(data_dir, _base_graph(services=[]), _minimal_extras())
        assert validate_graph(data_dir=data_dir, analyze=True) in (0, 1)
        out = capsys.readouterr().out
        assert "COMPREHENSIVE" in out or "ANALYSIS" in out


class TestGraphLoadAndInit:
    def test_load_data_short_circuits_when_already_loaded(self, tmp_path):
        data_dir = tmp_path / "d"
        _write_bundle(data_dir, _base_graph(services=[]), _minimal_extras())
        v = GraphValidator(data_dir)
        v.load_data()
        first = v.graph
        v.load_data()
        assert v.graph is first

    def test_graph_validator_raises_when_provider_dir_missing(self, tmp_path):
        root = tmp_path / "porto_data"
        (root / "policy").mkdir(parents=True)
        (root / "formats").mkdir(parents=True)
        (root / "providers").mkdir(parents=True)
        with pytest.raises(FileNotFoundError, match="Provider directory"):
            GraphValidator(project_root=root, provider="deutschepost")


class TestGraphPriceDependenciesAndUnits:
    def test_price_dependencies_missing_array_on_doc_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        extras = _minimal_extras(
            {
                "prices/products.json": {
                    "file_type": "product_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": "not-a-list",
                },
            }
        )
        _write_bundle(data_dir, _base_graph(services=["einschreiben"]), extras)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("Price file for product_prices missing" in e for e in v.results["errors"])

    def test_price_dependencies_missing_row_keys_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        extras = _minimal_extras(
            {
                "prices/products.json": {
                    "file_type": "product_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "EUR"},
                    "product_prices": [
                        {
                            "product_id": "p1",
                            "zone": "domestic",
                            "price": [{"amount": 1}],
                        }
                    ],
                },
            }
        )
        _write_bundle(data_dir, _base_graph(services=["einschreiben"]), extras)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("weight_tier" in e for e in v.results["errors"])

    def test_currency_mismatch_between_graph_and_prices_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        extras = _minimal_extras(
            {
                "prices/products.json": {
                    "file_type": "product_prices",
                    "provider": "deutschepost",
                    "unit": {"price": "cents", "currency": "USD"},
                    "product_prices": [],
                },
            }
        )
        _write_bundle(data_dir, _base_graph(services=[]), extras)
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("currency" in e.lower() for e in v.results["errors"])


class TestGraphLayoutsAndProducts:
    def test_layout_unknown_envelope_id_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        layouts = {
            "file_type": "layouts",
            "unit": {"dimension": "mm"},
            "jurisdictions": {
                "DE": {
                    "envelopes": {
                        "NOT_IN_ENVELOPES": {
                            "orientation": "landscape",
                            "layout": {
                                "window": {"supported": False},
                                "post_mark": {"x": 0, "y": 0},
                            },
                        }
                    }
                }
            },
        }
        _write_bundle(
            data_dir,
            _base_graph(services=[]),
            _minimal_extras({"layouts.json": layouts}),
        )
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any(
            "NOT_IN_ENVELOPES" in e or "unknown envelope" in e.lower() for e in v.results["errors"]
        )

    def test_layout_row_missing_orientation_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        layouts = {
            "file_type": "layouts",
            "unit": {"dimension": "mm"},
            "jurisdictions": {
                "DE": {
                    "envelopes": {
                        "C6": {
                            "layout": {
                                "window": {"supported": False},
                                "post_mark": {"x": 90, "y": 5},
                            },
                        }
                    }
                }
            },
        }
        _write_bundle(
            data_dir,
            _base_graph(services=[]),
            _minimal_extras({"layouts.json": layouts}),
        )
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("orientation" in e.lower() or "layout" in e.lower() for e in v.results["errors"])

    def test_layout_window_area_non_integer_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        layouts = {
            "file_type": "layouts",
            "unit": {"dimension": "mm"},
            "jurisdictions": {
                "DE": {
                    "envelopes": {
                        "C6": {
                            "orientation": "landscape",
                            "layout": {
                                "window": {
                                    "supported": True,
                                    "area": {"x": 0.5, "y": 0, "width": 100, "height": 80},
                                },
                                "post_mark": {"x": 90, "y": 5},
                            },
                        }
                    }
                }
            },
        }
        _write_bundle(
            data_dir,
            _base_graph(services=[]),
            _minimal_extras({"layouts.json": layouts}),
        )
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any(
            "window.area" in e.lower() and "integer" in e.lower() for e in v.results["errors"]
        )

    def test_product_envelope_id_missing_in_envelopes_errors(self, tmp_path):
        data_dir = tmp_path / "d"
        _write_bundle(
            data_dir,
            dict(_base_graph(services=[]), edges={"p1": {"zones": [], "weight_tiers": []}}),
            _minimal_extras(
                {
                    "products.json": _product_letter_fixture(envelope_ids=["NO_SUCH_FORMAT"]),
                }
            ),
        )
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("NO_SUCH_FORMAT" in e for e in v.results["errors"])


class TestGraphDependenciesAndCircular:
    def test_dependency_points_at_missing_file_warns(self, tmp_path):
        data_dir = tmp_path / "d"
        graph = dict(_base_graph(services=[]))
        deps = dict(graph["dependencies"])
        deps["ghost"] = {"file": "ghost.json", "depends_on": []}
        graph["dependencies"] = deps
        _write_bundle(data_dir, graph, _minimal_extras())
        v = GraphValidator(data_dir)
        v.validate_all()
        assert any("ghost.json" in w.lower() for w in v.results["warnings"])


class TestGraphEnvelopeHelpers:
    def test_envelope_validation_views_legacy_top_level_window(self):
        env = {
            "window_area": {"x": 0, "y": 0, "width": 10, "height": 10},
            "window_supported": True,
        }
        v = _envelope_validation_views(env)
        assert v["has_w"] and v["force_window"]
