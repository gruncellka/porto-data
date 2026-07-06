"""Coverage for ``scripts.validators.graph.wire_edges`` and ``validate_wire_edges`` hook."""

from __future__ import annotations

from unittest.mock import patch

from scripts.validators.base import ValidationResults
from scripts.validators.graph import GraphValidator
from scripts.validators.graph.edge_access import wire_edges
from scripts.validators.graph.wire_edges import (
    run_validate_no_entity_wire_codes,
    run_validate_strategy,
    run_validate_wire_edges,
)


def _results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


def _wire_graph(**overrides: object) -> dict:
    graph = {
        "strategy": "service",
        "edges": {
            "products": {"p1": {"zones": ["domestic"], "weight_tiers": ["W1"]}},
            "marks": {"domestic": {"profile": "p"}},
            "wire": {
                "internetmarke": {
                    "p1": {
                        "domestic": {
                            "base": 10001,
                            "services": {"einschreiben": 11006},
                        }
                    }
                }
            },
        },
        "services": ["einschreiben"],
    }
    graph.update(overrides)
    return graph


class TestWireEdgesAccess:
    def test_wire_edges_empty_when_graph_has_no_edges(self) -> None:
        assert wire_edges(None) == {}
        assert wire_edges({}) == {}
        assert wire_edges({"edges": {"products": {}, "marks": {}, "wire": "bad"}}) == {}


class TestRunValidateStrategy:
    def test_skips_when_graph_missing_or_not_dict(self) -> None:
        r = _results()
        run_validate_strategy(r, graph=None)
        run_validate_strategy(r, graph="not-a-dict")  # type: ignore[arg-type]
        assert r["errors"] == []
        assert r["correct"] == []

    def test_invalid_strategy_errors(self) -> None:
        r = _results()
        run_validate_strategy(r, graph={"strategy": "composite"})
        assert any("strategy must be one of" in e for e in r["errors"])

    def test_valid_strategy_records_correct(self) -> None:
        r = _results()
        run_validate_strategy(r, graph={"strategy": "id"})
        assert r["errors"] == []
        assert r["correct"] == ["strategy: id"]


class TestRunValidateNoEntityWireCodes:
    def test_forbids_native_id_fields_on_entities(self) -> None:
        r = _results()
        run_validate_no_entity_wire_codes(
            r,
            products=[
                {"id": "p1", "native_id": 1, "zone_native_ids": {"z": 2}},
            ],
            services=[
                {"id": "s1", "native_id": 3, "product_native_ids": {"p": 4}},
            ],
        )
        assert len(r["errors"]) == 4
        assert any("native_id" in e and "products.json" in e for e in r["errors"])
        assert any("zone_native_ids" in e for e in r["errors"])
        assert any("native_id" in e and "services.json" in e for e in r["errors"])
        assert any("product_native_ids" in e for e in r["errors"])


class TestRunValidateWireEdges:
    def test_invalid_edges_container_returns_early(self) -> None:
        r = _results()
        run_validate_wire_edges(
            r,
            graph={"edges": "bad"},
            product_dict={},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("edges must be an object" in e for e in r["errors"])

    def test_graph_none_after_container_ok_is_noop(self) -> None:
        r = _results()
        with patch(
            "scripts.validators.graph.wire_edges.validate_edges_container",
            return_value=True,
        ):
            run_validate_wire_edges(
                r,
                graph=None,
                product_dict={},
                services_by_id={},
                graph_service_ids=set(),
            )
        assert r["errors"] == []

    def test_empty_wire_emits_warning(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"] = {}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("edges.wire is empty" in w for w in r["warnings"])

    def test_integration_must_be_object(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"] = {"internetmarke": "not-a-dict"}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("edges.wire.internetmarke must be an object" in e for e in r["errors"])

    def test_unknown_wire_product_errors(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"]["internetmarke"]["ghost"] = {"domestic": {"base": 1}}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("wire product 'ghost' unknown" in e for e in r["errors"])

    def test_wire_product_missing_from_edges_products_errors(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["products"] = {}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("missing from edges.products" in e for e in r["errors"])

    def test_zones_wire_not_dict_skips_zone_checks(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"]["internetmarke"]["p1"] = "bad-zones"
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert not any("not in edges.products zones" in e for e in r["errors"])

    def test_zone_not_in_product_edges_errors(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"]["internetmarke"]["p1"]["nowhere"] = {"base": 1}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("nowhere" in e and "not in edges.products zones" in e for e in r["errors"])

    def test_zone_entry_not_dict_skips_base_and_services(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"]["internetmarke"]["p1"]["domestic"] = "not-a-dict"
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert not any("base" in e for e in r["errors"])

    def test_null_base_service_internetmarke_errors(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"]["internetmarke"]["p1"]["domestic"] = {"base": None}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("must not be null for service strategy" in e for e in r["errors"])

    def test_null_base_other_strategy_warns(self) -> None:
        r = _results()
        graph = _wire_graph(strategy="id")
        graph["edges"]["wire"] = {"mon_timbre_en_ligne": {"p1": {"domestic": {"base": None}}}}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("base is null (TBD catalog code)" in w for w in r["warnings"])

    def test_strategy_id_base_must_equal_product_id(self) -> None:
        r = _results()
        graph = _wire_graph(strategy="id")
        graph["edges"]["wire"] = {"mon_timbre_en_ligne": {"p1": {"domestic": {"base": "wrong"}}}}
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("must equal products.id" in e for e in r["errors"])

    def test_services_map_not_dict_skips_service_checks(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"]["internetmarke"]["p1"]["domestic"] = {
            "base": 10001,
            "services": "not-a-dict",
        }
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={"einschreiben": {"supported_zones": ["domestic"]}},
            graph_service_ids={"einschreiben"},
        )
        assert not any("wire service" in e for e in r["errors"])

    def test_wire_service_not_in_graph_services_errors(self) -> None:
        r = _results()
        graph = _wire_graph(services=[])
        graph["edges"]["wire"]["internetmarke"]["p1"]["domestic"] = {
            "base": 10001,
            "services": {"orphan": 999},
        }
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids=set(),
        )
        assert any("wire service 'orphan' not in graph.services[]" in e for e in r["errors"])

    def test_wire_service_unknown_in_services_json_errors(self) -> None:
        r = _results()
        graph = _wire_graph()
        graph["edges"]["wire"]["internetmarke"]["p1"]["domestic"] = {
            "base": 10001,
            "services": {"missing_row": 999},
        }
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={},
            graph_service_ids={"missing_row"},
        )
        assert any("unknown in services.json" in e for e in r["errors"])

    def test_wire_service_zone_not_supported_errors(self) -> None:
        r = _results()
        graph = _wire_graph()
        run_validate_wire_edges(
            r,
            graph=graph,
            product_dict={"p1": {"id": "p1"}},
            services_by_id={
                "einschreiben": {"supported_zones": ["zone_1_eu"]},
            },
            graph_service_ids={"einschreiben"},
        )
        assert any("not in supported_zones" in e for e in r["errors"])

    def test_valid_wire_passes(self) -> None:
        r = _results()
        run_validate_wire_edges(
            r,
            graph=_wire_graph(),
            product_dict={"p1": {"id": "p1"}},
            services_by_id={
                "einschreiben": {"supported_zones": ["domestic"]},
            },
            graph_service_ids={"einschreiben"},
        )
        assert r["errors"] == []


class TestGraphValidatorValidateWireEdges:
    def test_validate_wire_edges_noop_when_graph_unloaded(self) -> None:
        v = GraphValidator.__new__(GraphValidator)
        v.graph = None
        v.results = _results()
        v.products = {}
        v.services = {}
        v.product_dict = {}
        v.services_by_id = {}
        v.validate_wire_edges()
        assert v.results["errors"] == []
