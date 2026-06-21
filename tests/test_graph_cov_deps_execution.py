#!/usr/bin/env python3
"""Graph validator: dependencies and execution-semantics branch coverage."""

from __future__ import annotations

from scripts.data_files import GRAPH_FILE
from scripts.validators.base import ValidationResults
from scripts.validators.graph.dependencies import (
    run_validate_cycles,
    run_validate_dependencies,
)
from scripts.validators.graph.execution_semantics import run_validate_execution_semantics


def _empty_results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


class TestDependenciesCoverage:
    def test_fixes_needed_when_files_missing_from_dependencies(self) -> None:
        r = _empty_results()
        all_files = {GRAPH_FILE, "products.json", "zones.json"}
        graph = {"dependencies": {"p": {"file": "products.json", "depends_on": []}}}
        run_validate_dependencies(r, graph=graph, all_data_files=all_files)
        assert r["fixes_needed"]

    def test_dependency_file_not_in_all_files_warns(self) -> None:
        r = _empty_results()
        graph = {"dependencies": {"x": {"file": "ghost.json", "depends_on": []}}}
        run_validate_dependencies(r, graph=graph, all_data_files=set())
        assert any("ghost.json" in w for w in r["warnings"])

    def test_unknown_depends_on_file_warns(self) -> None:
        r = _empty_results()
        graph = {
            "dependencies": {
                "p": {"file": "products.json", "depends_on": ["ghost.json"]},
            }
        }
        all_files = {"products.json"}
        run_validate_dependencies(r, graph=graph, all_data_files=all_files)
        assert any("ghost.json" in w for w in r["warnings"])

    def test_non_dict_dep_skipped_in_graph(self) -> None:
        r = _empty_results()
        graph = {"dependencies": {"bad": "x", "ok": {"file": "a.json", "depends_on": []}}}
        run_validate_cycles(r, graph=graph)

    def test_non_str_depends_on_skipped(self) -> None:
        r = _empty_results()
        graph = {
            "dependencies": {
                "a": {"file": "a.json", "depends_on": [1, "b.json"]},
                "b": {"file": "b.json", "depends_on": []},
            }
        }
        run_validate_cycles(r, graph=graph)

    def test_circular_deps_skips_non_dict_dependencies(self) -> None:
        r = _empty_results()
        run_validate_cycles(r, graph={"dependencies": []})

    def test_products_product_prices_circular_warns(self) -> None:
        r = _empty_results()
        graph = {
            "dependencies": {
                "products": {
                    "file": "products.json",
                    "depends_on": ["prices/product_prices.json"],
                },
                "product_prices": {
                    "file": "prices/product_prices.json",
                    "depends_on": ["products.json"],
                },
            }
        }
        run_validate_cycles(r, graph=graph)
        assert any("Circular dependency" in w for w in r["warnings"])


class TestExecutionSemanticsCoverage:
    def test_early_return_when_products_none(self) -> None:
        r = _empty_results()
        run_validate_execution_semantics(
            r,
            graph={},
            products=None,
            services={"services": []},
            services_by_id={},
            product_dict={},
        )
        assert not r["errors"]

    def test_services_not_list_resets(self) -> None:
        r = _empty_results()
        graph = {"services": (1,)}
        products = {"products": [{"id": "p1", "mark_type": "stamp", "tracking_mode": "none"}]}
        services = {"services": []}
        run_validate_execution_semantics(
            r,
            graph=graph,
            products=products,
            services=services,
            services_by_id={},
            product_dict={p["id"]: p for p in products["products"]},
        )
        assert not r["errors"]

    def test_missing_mark_type_errors(self) -> None:
        r = _empty_results()
        graph = {"services": []}
        products = {"products": [{"id": "p1", "tracking_mode": "none"}]}
        services = {"services": []}
        run_validate_execution_semantics(
            r,
            graph=graph,
            products=products,
            services=services,
            services_by_id={},
            product_dict={p["id"]: p for p in products["products"]},
        )
        assert any("mark_type" in e for e in r["errors"])

    def test_label_none_errors(self) -> None:
        r = _empty_results()
        graph = {"services": []}
        products = {
            "products": [
                {"id": "p1", "mark_type": "label", "tracking_mode": "none", "zones": ["z"]}
            ]
        }
        services = {"services": []}
        run_validate_execution_semantics(
            r,
            graph=graph,
            products=products,
            services=services,
            services_by_id={},
            product_dict={p["id"]: p for p in products["products"]},
        )
        assert any("label" in e and "none" in e for e in r["errors"])

    def test_optional_tracking_via_available_service(self) -> None:
        r = _empty_results()
        graph = {"services": ["no_trk", "trk"]}
        products = {
            "products": [
                {
                    "id": "p1",
                    "mark_type": "label",
                    "tracking_mode": "optional",
                    "zones": ["domestic"],
                }
            ]
        }
        services = {
            "services": [
                {"id": "no_trk", "porto_id": "n1"},
                {
                    "id": "trk",
                    "porto_id": "t1",
                    "enables_tracking": True,
                    "supported_zones": ["domestic"],
                },
            ]
        }
        by_id = {s["id"]: s for s in services["services"]}
        run_validate_execution_semantics(
            r,
            graph=graph,
            products=products,
            services=services,
            services_by_id=by_id,
            product_dict={p["id"]: p for p in products["products"]},
        )
        assert not r["errors"]

    def test_optional_tracking_service_without_zones_covers(self) -> None:
        r = _empty_results()
        graph = {"services": ["trk"]}
        products = {
            "products": [
                {
                    "id": "p1",
                    "mark_type": "label",
                    "tracking_mode": "optional",
                    "zones": ["domestic"],
                }
            ]
        }
        services = {
            "services": [
                {"id": "trk", "enables_tracking": True},
            ]
        }
        by_id = {s["id"]: s for s in services["services"]}
        run_validate_execution_semantics(
            r,
            graph=graph,
            products=products,
            services=services,
            services_by_id=by_id,
            product_dict={p["id"]: p for p in products["products"]},
        )
        assert not r["errors"]

    def test_optional_tracking_no_service_errors(self) -> None:
        r = _empty_results()
        graph = {"services": []}
        products = {
            "products": [
                {
                    "id": "p1",
                    "mark_type": "label",
                    "tracking_mode": "optional",
                    "zones": ["domestic"],
                }
            ]
        }
        services = {"services": [{"id": "x", "enables_tracking": False}]}
        by_id = {s["id"]: s for s in services["services"]}
        run_validate_execution_semantics(
            r,
            graph=graph,
            products=products,
            services=services,
            services_by_id=by_id,
            product_dict={p["id"]: p for p in products["products"]},
        )
        assert any("optional" in e for e in r["errors"])

    def test_optional_tracking_fallback_services_by_id(self) -> None:
        r = _empty_results()
        graph = {"services": ["only_plain"]}
        products = {
            "products": [
                {
                    "id": "p1",
                    "mark_type": "label",
                    "tracking_mode": "optional",
                    "zones": ["domestic"],
                }
            ]
        }
        services = {
            "services": [
                {"id": "only_plain", "enables_tracking": False},
                {
                    "id": "hidden_trk",
                    "enables_tracking": True,
                    "supported_zones": ["domestic"],
                },
            ]
        }
        by_id = {s["id"]: s for s in services["services"]}
        run_validate_execution_semantics(
            r,
            graph=graph,
            products=products,
            services=services,
            services_by_id=by_id,
            product_dict={p["id"]: p for p in products["products"]},
        )
        assert not r["errors"]
