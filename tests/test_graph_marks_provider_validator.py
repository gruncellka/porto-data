#!/usr/bin/env python3
"""Graph validator: marks catalog, edges.marks, provider rules, lookup edge cases."""

from __future__ import annotations

from pathlib import Path

from scripts.validators.base import ValidationResults
from scripts.validators.graph import GraphValidator
from scripts.validators.graph.constants import (
    PROVIDER_RULE_METRIC_THICKNESS,
    RULE_KIND_BAND,
)
from scripts.validators.graph.edge_access import (
    mark_edges,
    product_edges,
    validate_edges_container,
)
from scripts.validators.graph.mark_edges import run_validate_mark_edges
from scripts.validators.graph.marks_profiles import run_validate_marks_profiles
from scripts.validators.graph.provider_rules import run_validate_provider_rules


def _empty_results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


def _marks_doc(*, profiles: list[dict]) -> dict:
    return {
        "file_type": "marks",
        "provider": "p",
        "default_profile": profiles[0]["id"],
        "profiles": profiles,
    }


def _graph_doc(*, marks_map: dict | None = None, services: list[str] | None = None) -> dict:
    return {
        "file_type": "graph",
        "provider": "p",
        "edges": {"products": {}, "marks": marks_map if marks_map is not None else {}},
        "services": services or [],
    }


class TestMarksProfilesCoverage:
    def test_missing_marks_errors(self) -> None:
        r = _empty_results()
        run_validate_marks_profiles(r, graph={}, marks=None)
        assert r["errors"]

    def test_wrong_file_type(self) -> None:
        r = _empty_results()
        marks = {"file_type": "wrong", "profiles": [{"id": "a"}]}
        run_validate_marks_profiles(r, graph={"provider": "p"}, marks=marks)
        assert any("file_type" in e for e in r["errors"])

    def test_provider_mismatch(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["provider"] = "other"
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("path-implied" in e for e in r["errors"])

    def test_profiles_not_nonempty_list(self) -> None:
        r = _empty_results()
        marks = {"file_type": "marks", "profiles": []}
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("profiles" in e for e in r["errors"])

    def test_bad_profile_rows_and_duplicate_id(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "profiles": [
                "bad",
                {"id": "dup", "mark_type": "stamp", "label": "A"},
                {"id": "dup", "mark_type": "stamp", "label": "B"},
            ],
            "default_profile": 123,
        }
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("object with id" in e for e in r["errors"])
        assert any("duplicate" in e for e in r["errors"])
        assert any("default_profile" in e for e in r["errors"])

    def test_default_profile_not_in_profiles(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["default_profile"] = "missing"
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("not found in profiles" in e for e in r["errors"])

    def test_legacy_marks_zones_rejected(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["zones"] = {"domestic": "a"}
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("edges.marks" in e for e in r["errors"])

    def test_calibration_integration_must_match_wire(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "domestic", "mark_type": "stamp", "label": "D"}])
        marks["calibrations"] = [
            {
                "integration": "unknown_api",
                "voucher_layout": "stamp_only",
                "mime_type": "image/png",
                "dpi": 300,
                "label_canvas": {
                    "width_px": 1,
                    "height_px": 1,
                    "width_mm": 1,
                    "height_mm": 1,
                },
            }
        ]
        graph = {
            "provider": "p",
            "edges": {
                "products": {},
                "marks": {},
                "wire": {"checkout_api": {"letter": {"domestic": {"base": 1}}}},
            },
        }
        run_validate_marks_profiles(r, graph=graph, marks=marks)
        assert any("integration 'unknown_api'" in e for e in r["errors"])

    def test_calibration_by_mark_profile_requires_known_profiles(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "domestic", "mark_type": "stamp", "label": "D"}])
        marks["calibrations"] = [
            {
                "integration": "webstamp",
                "voucher_layout": "stamp_only",
                "mime_type": "image/png",
                "dpi": 300,
                "by_mark_profile": {
                    "unknown": {"width_px": 1, "height_px": 1, "width_mm": 1, "height_mm": 1}
                },
            }
        ]
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("by_mark_profile key 'unknown'" in e for e in r["errors"])

    def test_calibration_rejects_source_run(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "domestic", "mark_type": "stamp", "label": "D"}])
        marks["calibrations"] = [
            {
                "integration": "mtel",
                "voucher_layout": "full_label",
                "mime_type": "image/png",
                "dpi": 300,
                "source_run": "lab-run",
                "label_canvas": {
                    "width_px": 1,
                    "height_px": 1,
                    "width_mm": 1,
                    "height_mm": 1,
                },
            }
        ]
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("source_run must not be set" in e for e in r["errors"])

    def test_calibrations_must_be_array_when_present(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["calibrations"] = "bad"
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("calibrations must be an array" in e for e in r["errors"])

    def test_calibration_row_must_be_object(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["calibrations"] = ["bad"]
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("calibrations[0] must be an object" in e for e in r["errors"])

    def test_calibration_requires_integration_and_layout(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["calibrations"] = [{"integration": "", "voucher_layout": ""}]
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("integration must be a non-empty string" in e for e in r["errors"])
        assert any("voucher_layout must be a non-empty string" in e for e in r["errors"])

    def test_calibration_requires_dimension_data(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["calibrations"] = [
            {"integration": "api", "voucher_layout": "stamp_only", "by_mark_profile": {}}
        ]
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("requires by_mark_profile or label_canvas" in e for e in r["errors"])

    def test_calibration_dimension_box_validation(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        marks["calibrations"] = [
            {
                "integration": "api",
                "voucher_layout": "stamp_only",
                "label_canvas": "bad",
                "by_mark_profile": {"a": "bad"},
            }
        ]
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("label_canvas must be an object" in e for e in r["errors"])
        assert any("by_mark_profile['a'] must be an object" in e for e in r["errors"])
        marks["calibrations"] = [
            {
                "integration": "api",
                "voucher_layout": "stamp_only",
                "label_canvas": {"width_px": 1},
            }
        ]
        run_validate_marks_profiles(r, graph={}, marks=marks)
        assert any("label_canvas missing" in e for e in r["errors"])


class TestEdgeAccessCoverage:
    def test_product_edges_empty_when_no_edges_root(self) -> None:
        assert product_edges(None) == {}
        assert product_edges({}) == {}
        assert product_edges({"edges": "bad"}) == {}

    def test_mark_edges_empty_when_no_edges_root(self) -> None:
        assert mark_edges(None) == {}
        assert mark_edges({}) == {}

    def test_validate_edges_container_none_or_non_object_graph(self) -> None:
        r = _empty_results()
        assert validate_edges_container(r, graph=None) is False
        assert validate_edges_container(r, graph="bad") is False
        assert r["errors"] == []

    def test_validate_edges_container_missing_edges_object(self) -> None:
        r = _empty_results()
        ok = validate_edges_container(r, graph={})
        assert not ok
        assert any("edges must be an object" in e for e in r["errors"])

    def test_validate_edges_container_legacy_mark_edges(self) -> None:
        r = _empty_results()
        ok = validate_edges_container(
            r, graph={"edges": {"products": {}, "marks": {}}, "mark_edges": {}}
        )
        assert not ok
        assert any("mark_edges is removed" in e for e in r["errors"])

    def test_validate_edges_container_missing_products(self) -> None:
        r = _empty_results()
        ok = validate_edges_container(r, graph={"edges": {"marks": {}}})
        assert not ok
        assert any("edges.products must be an object" in e for e in r["errors"])


class TestMarkEdgesCoverage:
    def test_edges_marks_missing_object(self) -> None:
        r = _empty_results()
        run_validate_mark_edges(
            r,
            graph={"file_type": "graph", "edges": {"products": {}, "marks": "bad"}},
            marks=_marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}]),
        )
        assert any("edges.marks must be an object" in e for e in r["errors"])

    def test_legacy_top_level_mark_edges_rejected(self) -> None:
        r = _empty_results()
        run_validate_mark_edges(
            r,
            graph={"file_type": "graph", "edges": {"products": {}, "marks": {}}, "mark_edges": {}},
            marks=_marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}]),
        )
        assert any("mark_edges is removed" in e for e in r["errors"])

    def test_edges_marks_requires_marks(self) -> None:
        r = _empty_results()
        run_validate_mark_edges(r, graph=_graph_doc(), marks=None)
        assert any("requires marks.json" in e for e in r["errors"])

    def test_marks_map_empty_when_zones_defined(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        zones = {"zones": [{"id": "domestic"}]}
        run_validate_mark_edges(r, graph=_graph_doc(marks_map={}), marks=marks, zones=zones)
        assert any("must be non-empty when zones.json" in e for e in r["errors"])

    def test_marks_map_unknown_zone_key(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        graph = _graph_doc(marks_map={"world": {"profile": "a"}})
        zones = {"zones": [{"id": "domestic"}]}
        run_validate_mark_edges(r, graph=graph, marks=marks, zones=zones)
        assert any("not in zones.json" in e for e in r["errors"])

    def test_marks_map_missing_zone_from_zones_json(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        graph = _graph_doc(marks_map={"domestic": {"profile": "a"}})
        zones = {"zones": [{"id": "domestic"}, {"id": "world"}]}
        run_validate_mark_edges(r, graph=graph, marks=marks, zones=zones)
        assert any("missing entries for zones.json" in e for e in r["errors"])

    def test_marks_map_unknown_profile_and_service(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        graph = _graph_doc(
            marks_map={
                "domestic": {
                    "profile": "missing",
                    "services": {"ghost": "also_missing"},
                }
            },
            services=["einschreiben"],
        )
        run_validate_mark_edges(r, graph=graph, marks=marks)
        assert any(".profile" in e and "missing" in e for e in r["errors"])
        assert any("not in graph.services" in e for e in r["errors"])
        assert any("also_missing" in e for e in r["errors"])

    def test_marks_map_bad_shape(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        graph = _graph_doc(
            marks_map={
                "domestic": "bad",
                "world": {"profile": "", "services": {}},
            }
        )
        run_validate_mark_edges(r, graph=graph, marks=marks)
        assert any("must be an object" in e for e in r["errors"])
        assert any(".profile must be" in e for e in r["errors"])
        assert any(".services must be omitted or non-empty" in e for e in r["errors"])

    def test_marks_map_graph_none_returns(self) -> None:
        r = _empty_results()
        run_validate_mark_edges(
            r,
            graph=None,
            marks=_marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}]),
        )
        assert not r["errors"]

    def test_marks_map_services_not_object(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        graph = _graph_doc(marks_map={"domestic": {"profile": "a", "services": "bad"}})
        run_validate_mark_edges(r, graph=graph, marks=marks)
        assert any(".services must be an object" in e for e in r["errors"])

    def test_marks_map_empty_service_profile_value(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp", "label": "A"}])
        graph = _graph_doc(
            marks_map={"domestic": {"profile": "a", "services": {"einschreiben": ""}}},
            services=["einschreiben"],
        )
        run_validate_mark_edges(r, graph=graph, marks=marks)
        assert any("must be a non-empty profile id string" in e for e in r["errors"])

    def test_marks_map_success(self) -> None:
        r = _empty_results()
        marks = _marks_doc(
            profiles=[
                {"id": "domestic", "mark_type": "stamp", "label": "D"},
                {"id": "registered", "mark_type": "stamp", "label": "R"},
            ]
        )
        graph = _graph_doc(
            marks_map={
                "domestic": {
                    "profile": "domestic",
                    "services": {"einschreiben": "registered"},
                }
            },
            services=["einschreiben"],
        )
        zones = {"zones": [{"id": "domestic"}]}
        run_validate_mark_edges(r, graph=graph, marks=marks, zones=zones)
        assert any("edges.marks covers all" in c for c in r["correct"])


class TestProviderRulesCoverage:
    def test_doc_none_returns(self) -> None:
        r = _empty_results()
        run_validate_provider_rules(
            r,
            graph={"provider": "p"},
            doc=None,
            product_dict={},
            service_prices=[],
            services=None,
        )
        assert not r["errors"]

    def test_wrong_file_type(self) -> None:
        r = _empty_results()
        doc = {"file_type": "nope", "rules": []}
        run_validate_provider_rules(
            r, graph={"provider": "p"}, doc=doc, product_dict={}, service_prices=[], services={}
        )
        assert any("provider_rules" in e for e in r["errors"])

    def test_provider_mismatch(self) -> None:
        r = _empty_results()
        doc = {"file_type": "provider_rules", "provider": "x", "rules": []}
        run_validate_provider_rules(
            r,
            graph={},
            doc=doc,
            product_dict={},
            service_prices=[],
            services={"services": []},
        )
        assert any("path-implied" in e for e in r["errors"])

    def test_rules_not_list(self) -> None:
        r = _empty_results()
        doc = {"file_type": "provider_rules", "provider": "p", "rules": {}}
        run_validate_provider_rules(
            r,
            graph={"provider": "p"},
            doc=doc,
            product_dict={},
            service_prices=[],
            services={"services": []},
        )
        assert any("array" in e for e in r["errors"])

    def test_thickness_requires_mm(self) -> None:
        r = _empty_results()
        doc = {
            "file_type": "provider_rules",
            "provider": "p",
            "unit": {"thickness": "in"},
            "rules": [
                {
                    "id": "r1",
                    "kind": RULE_KIND_BAND,
                    "metric": PROVIDER_RULE_METRIC_THICKNESS,
                    "product_ids": [],
                    "service_id": "s1",
                    "min_exclusive": 0,
                    "max_inclusive": 1,
                }
            ],
        }
        run_validate_provider_rules(
            r,
            graph={"provider": "p"},
            doc=doc,
            product_dict={"p1": {"id": "p1"}},
            service_prices=[{"service_id": "s1"}],
            services={"services": [{"id": "s1"}]},
        )
        assert any("mm" in e for e in r["errors"])

    def test_rule_shape_and_refs(self) -> None:
        r = _empty_results()
        base_rule = {
            "kind": RULE_KIND_BAND,
            "metric": PROVIDER_RULE_METRIC_THICKNESS,
            "min_exclusive": 0,
            "max_inclusive": 2,
        }
        doc = {
            "file_type": "provider_rules",
            "provider": "p",
            "unit": {"thickness": "mm"},
            "rules": [
                "bad",
                {"id": "k1", "kind": "other"},
                {
                    "id": "m1",
                    **base_rule,
                    "metric": "width",
                },
                {
                    "id": "pid",
                    **base_rule,
                    "product_ids": ["missing"],
                    "service_id": "ghost",
                },
                {
                    "id": "warn",
                    **base_rule,
                    "product_ids": ["p1"],
                    "service_id": "s1",
                },
                {
                    "id": "badnum",
                    **base_rule,
                    "product_ids": [],
                    "service_id": "s1",
                    "min_exclusive": "x",
                    "max_inclusive": 1,
                },
                {
                    "id": "range",
                    **base_rule,
                    "product_ids": [],
                    "service_id": "s1",
                    "min_exclusive": 2,
                    "max_inclusive": 1,
                },
            ],
        }
        run_validate_provider_rules(
            r,
            graph={"provider": "p"},
            doc=doc,
            product_dict={"p1": {"id": "p1"}},
            service_prices=[],
            services={"services": [{"id": "s1"}]},
        )
        assert any("object" in e for e in r["errors"])
        assert any("unsupported kind" in e for e in r["errors"])
        assert any("unsupported metric" in e for e in r["errors"])
        assert any("unknown product_id" in e for e in r["errors"])
        assert any("unknown service_id" in e for e in r["errors"])
        assert any("service_prices" in w for w in r["warnings"])
        assert any("numbers" in e for e in r["errors"])
        assert any("min_exclusive" in e for e in r["errors"])

    def test_success_correct_message(self) -> None:
        r = _empty_results()
        doc = {
            "file_type": "provider_rules",
            "unit": {"thickness": "mm"},
            "rules": [
                {
                    "id": "ok",
                    "kind": RULE_KIND_BAND,
                    "metric": PROVIDER_RULE_METRIC_THICKNESS,
                    "product_ids": ["p1"],
                    "service_id": "s1",
                    "min_exclusive": 0,
                    "max_inclusive": 1,
                }
            ],
        }
        run_validate_provider_rules(
            r,
            graph={"provider": "p"},
            doc=doc,
            product_dict={"p1": {"id": "p1"}},
            service_prices=[{"service_id": "s1"}],
            services={"services": [{"id": "s1"}]},
        )
        assert any("rules.json references" in c for c in r["correct"])


class TestGraphValidatorBuildLookupEarlyReturn:
    def test_build_lookup_returns_when_products_none(self, tmp_path: Path) -> None:
        (tmp_path / "graph.json").write_text("{}", encoding="utf-8")
        v = GraphValidator(data_dir=tmp_path)
        v.graph = {}
        v.products = None
        v.zones = {"zones": []}
        v.weight_tiers = {"weights": {}}
        v.services = {"services": []}
        v.product_prices_doc = {"product_prices": []}
        v.service_prices_doc = {"service_prices": []}
        v.envelopes = {}
        v.envelope_layouts = {}
        v.marks = {}
        v.shared_bundle_subdir = tmp_path
        v._bundle_root = tmp_path
        v._build_lookup_structures()

    def test_validate_integration_manifest_graph_none_returns(self, tmp_path: Path) -> None:
        (tmp_path / "graph.json").write_text("{}", encoding="utf-8")
        v = GraphValidator(data_dir=tmp_path)
        v.graph = None
        v.integration = {"file_type": "integration", "adapter": "x", "execution": ["create_mark"]}
        v.validate_integration_manifest()
        assert v.results["errors"] == []
