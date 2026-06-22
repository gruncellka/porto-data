#!/usr/bin/env python3
"""Graph validator: marks, provider rules, and lookup build edge cases."""

from __future__ import annotations

from pathlib import Path

from scripts.validators.base import ValidationResults
from scripts.validators.graph import GraphValidator
from scripts.validators.graph.constants import (
    PROVIDER_RULE_METRIC_THICKNESS,
    RULE_KIND_BAND,
)
from scripts.validators.graph.marks_profiles import run_validate_marks_profiles
from scripts.validators.graph.provider_rules import run_validate_provider_rules


def _empty_results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


def _marks_doc(*, profiles: list[dict], marks_zones: dict[str, str] | None = None) -> dict:
    zmap = marks_zones or {"domestic": "domestic"}
    return {
        "file_type": "marks",
        "provider": "p",
        "default_profile": profiles[0]["id"],
        "zones": zmap,
        "profiles": profiles,
    }


class TestMarksProfilesCoverage:
    def test_missing_marks_errors(self) -> None:
        r = _empty_results()
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=None)
        assert r["errors"]

    def test_wrong_file_type(self) -> None:
        r = _empty_results()
        marks = {"file_type": "wrong", "profiles": [{"id": "a"}]}
        run_validate_marks_profiles(
            r, graph={"provider": "p"}, products={"products": []}, marks=marks
        )
        assert any("file_type" in e for e in r["errors"])

    def test_provider_mismatch(self) -> None:
        r = _empty_results()
        marks = _marks_doc(profiles=[{"id": "a", "mark_type": "stamp"}])
        marks["provider"] = "other"
        run_validate_marks_profiles(
            r, graph={"provider": "mine"}, products={"products": []}, marks=marks
        )
        assert any("provider" in e for e in r["errors"])

    def test_profiles_not_nonempty_list(self) -> None:
        r = _empty_results()
        marks = {"file_type": "marks", "profiles": [], "zones": {"domestic": "a"}}
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=marks)
        assert any("profiles" in e for e in r["errors"])

    def test_bad_profile_rows_and_duplicate_id(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "profiles": [
                "bad",
                {"id": "dup", "mark_type": "stamp"},
                {"id": "dup", "mark_type": "stamp"},
            ],
            "default_profile": 123,
            "zones": {"domestic": "dup"},
        }
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=marks)
        assert any("object with id" in e for e in r["errors"])
        assert any("duplicate" in e for e in r["errors"])
        assert any("default_profile" in e for e in r["errors"])

    def test_default_profile_not_in_profiles(self) -> None:
        r = _empty_results()
        marks = _marks_doc(
            profiles=[{"id": "a", "mark_type": "stamp"}],
            marks_zones={"domestic": "a"},
        )
        marks["default_profile"] = "missing"
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=marks)
        assert any("not found in profiles" in e for e in r["errors"])

    def test_marks_zones_missing(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "profiles": [{"id": "a", "mark_type": "stamp"}],
            "default_profile": "a",
        }
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=marks)
        assert any("zones must be a non-empty object" in e for e in r["errors"])

    def test_marks_zones_unknown_zone_key(self) -> None:
        r = _empty_results()
        marks = _marks_doc(
            profiles=[{"id": "a", "mark_type": "stamp"}],
            marks_zones={"domestic": "a", "world": "a"},
        )
        zones = {"zones": [{"id": "domestic"}]}
        run_validate_marks_profiles(
            r, graph={}, products={"products": []}, marks=marks, zones=zones
        )
        assert any("not in zones.json" in e for e in r["errors"])

    def test_marks_zones_missing_zone_from_zones_json(self) -> None:
        r = _empty_results()
        marks = _marks_doc(
            profiles=[{"id": "a", "mark_type": "stamp"}],
            marks_zones={"domestic": "a"},
        )
        zones = {"zones": [{"id": "domestic"}, {"id": "world"}]}
        run_validate_marks_profiles(
            r, graph={}, products={"products": []}, marks=marks, zones=zones
        )
        assert any("missing entries for zones.json" in e for e in r["errors"])

    def test_marks_zones_unknown_profile_id(self) -> None:
        r = _empty_results()
        marks = _marks_doc(
            profiles=[{"id": "a", "mark_type": "stamp"}],
            marks_zones={"domestic": "missing"},
        )
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=marks)
        assert any("missing" in e for e in r["errors"])

    def test_marks_zones_empty_profile_value(self) -> None:
        r = _empty_results()
        marks = _marks_doc(
            profiles=[{"id": "a", "mark_type": "stamp"}],
            marks_zones={"domestic": ""},
        )
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=marks)
        assert any("non-empty profile id" in e for e in r["errors"])


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
            graph={"provider": "y"},
            doc=doc,
            product_dict={},
            service_prices=[],
            services={"services": []},
        )
        assert any("provider" in e.lower() for e in r["errors"])

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
            "provider": "p",
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
