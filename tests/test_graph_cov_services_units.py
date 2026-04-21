#!/usr/bin/env python3
"""Graph validator: services helpers and unit-validation early exits."""

from __future__ import annotations

from scripts.validators.base import ValidationResults
from scripts.validators.graph.services import (
    get_service_by_ref,
    run_validate_available_services,
    run_validate_service_price_consistency,
    service_refs_set,
)
from scripts.validators.graph.units import (
    run_validate_currency_units,
    run_validate_dimension_units,
    run_validate_price_units,
    run_validate_weight_units,
)


def _empty_results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


class TestServicesHelpersCoverage:
    def test_get_service_by_ref_skips_non_dict_rows(self) -> None:
        services = {"services": ["bad", {"id": "ok"}]}
        assert get_service_by_ref(services, "ok") == {"id": "ok"}
        assert get_service_by_ref(services, "missing") is None

    def test_service_refs_set_empty_services(self) -> None:
        assert service_refs_set(None) == set()
        assert service_refs_set({}) == set()

    def test_get_service_by_ref_empty(self) -> None:
        assert get_service_by_ref({"services": [{"id": "x"}]}, "") is None

    def test_available_services_invalid_and_missing_price_warn(self) -> None:
        r = _empty_results()
        graph = {"global_settings": {"available_services": ["ghost", "real"]}}
        services = {"services": [{"id": "real", "porto_id": "r1"}]}
        prices = [{"service_id": "other"}]
        run_validate_available_services(r, graph=graph, services=services, service_prices=prices)
        assert any("ghost" in e for e in r["errors"])
        assert any("real" in w and "no row" in w for w in r["warnings"])

    def test_service_price_consistency_branches(self) -> None:
        r = _empty_results()
        run_validate_service_price_consistency(
            r,
            services={
                "services": [
                    {"id": "s1", "effective_to": "2020-01-01"},
                    {"id": "s2"},
                ]
            },
            service_prices=[
                {},
                {
                    "service_id": "gone",
                    "price": [{"effective_to": "2021-01-01"}],
                },
                {
                    "service_id": "s2",
                    "price": [{"effective_to": "2021-01-01"}],
                },
                {
                    "service_id": "s1",
                    "price": [{"effective_to": "2022-01-01"}],
                },
                {
                    "service_id": "s1",
                    "price": [{"effective_to": "2020-01-01"}],
                },
            ],
        )
        assert any("not found" in e for e in r["errors"])
        assert any("does not have effective_to" in e for e in r["errors"])
        assert any("Dates must match" in e for e in r["errors"])


class TestUnitsEarlyReturns:
    def test_weight_units_skips_without_all_inputs(self) -> None:
        r = _empty_results()
        run_validate_weight_units(r, graph=None, products={}, weight_tiers={})

    def test_dimension_units_skips_without_envelopes(self) -> None:
        r = _empty_results()
        run_validate_dimension_units(
            r, graph={"unit": {"dimension": "mm"}}, envelopes=None, envelope_layouts=None
        )

    def test_price_units_skips_without_product_prices_doc(self) -> None:
        r = _empty_results()
        run_validate_price_units(
            r, graph={"unit": {"price": "cents"}}, product_prices_doc=None, service_prices_doc=None
        )

    def test_currency_units_skips_without_product_prices_doc(self) -> None:
        r = _empty_results()
        run_validate_currency_units(
            r, graph={"unit": {"currency": "EUR"}}, product_prices_doc=None, service_prices_doc=None
        )
