#!/usr/bin/env python3
"""Graph validator: marks, provider rules, and lookup build edge cases."""

from __future__ import annotations

from pathlib import Path

from scripts.validators.base import ValidationResults
from scripts.validators.graph import GraphValidator
from scripts.validators.graph.constants import (
    PROVIDER_RULE_KIND_METRIC_BAND_ATTACH,
    PROVIDER_RULE_METRIC_THICKNESS,
)
from scripts.validators.graph.marks_profiles import run_validate_marks_profiles
from scripts.validators.graph.provider_rules import run_validate_provider_rules


def _empty_results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


class TestMarksProfilesCoverage:
    def test_products_none_returns(self) -> None:
        r = _empty_results()
        run_validate_marks_profiles(r, graph={}, products=None, marks={})

    def test_missing_marks_errors(self) -> None:
        r = _empty_results()
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=None)

    def test_wrong_file_type(self) -> None:
        r = _empty_results()
        marks = {"file_type": "wrong", "profiles": [{"id": "a"}]}
        run_validate_marks_profiles(
            r, graph={"provider": "p"}, products={"products": []}, marks=marks
        )
        assert any("file_type" in e for e in r["errors"])

    def test_provider_mismatch(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "provider": "other",
            "profiles": [{"id": "a", "mark_type": "stamp"}],
            "default_profile": "a",
        }
        run_validate_marks_profiles(
            r, graph={"provider": "mine"}, products={"products": []}, marks=marks
        )
        assert any("provider" in e for e in r["errors"])

    def test_profiles_not_nonempty_list(self) -> None:
        r = _empty_results()
        marks = {"file_type": "marks", "profiles": []}
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
        }
        run_validate_marks_profiles(
            r, graph={}, products={"products": [{"id": "x", "mark_type": "stamp"}]}, marks=marks
        )
        assert any("object with id" in e for e in r["errors"])
        assert any("duplicate" in e for e in r["errors"])
        assert any("default_profile" in e for e in r["errors"])

    def test_default_profile_not_in_profiles(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "profiles": [{"id": "a", "mark_type": "stamp"}],
            "default_profile": "missing",
        }
        run_validate_marks_profiles(r, graph={}, products={"products": []}, marks=marks)
        assert any("not found in profiles" in e for e in r["errors"])

    def test_product_mark_profile_and_mark_type_mismatch(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "profiles": [{"id": "prof", "mark_type": "stamp"}],
            "default_profile": "prof",
        }
        products = {
            "products": [
                {"id": "p1", "mark_type": "label", "mark_profile": "prof"},
                "not-a-dict",
            ]
        }
        run_validate_marks_profiles(r, graph={}, products=products, marks=marks)
        assert any("mark_type" in e and "prof" in e for e in r["errors"])

    def test_unknown_mark_profile(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "profiles": [{"id": "a", "mark_type": "stamp"}],
            "default_profile": "a",
        }
        products = {"products": [{"id": "p1", "mark_type": "stamp", "mark_profile": "nope"}]}
        run_validate_marks_profiles(r, graph={}, products=products, marks=marks)
        assert any("nope" in e for e in r["errors"])

    def test_skip_when_no_chosen_profile(self) -> None:
        r = _empty_results()
        marks = {
            "file_type": "marks",
            "profiles": [{"id": "a", "mark_type": "stamp"}],
        }
        products = {"products": [{"id": "p1", "mark_type": "stamp"}]}
        run_validate_marks_profiles(r, graph={}, products=products, marks=marks)
        assert any("default_profile" in e for e in r["errors"])


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
                    "kind": PROVIDER_RULE_KIND_METRIC_BAND_ATTACH,
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
            "kind": PROVIDER_RULE_KIND_METRIC_BAND_ATTACH,
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
                    "kind": PROVIDER_RULE_KIND_METRIC_BAND_ATTACH,
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
