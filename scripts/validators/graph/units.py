"""Cross-file unit consistency (weight, dimension, price, currency)."""

from __future__ import annotations

from typing import Any

from scripts.data_files import (
    ENVELOPES_FILE,
    GRAPH_FILE,
    LAYOUTS_FILE,
    PRODUCT_PRICES_FILE,
    PRODUCTS_FILE,
    SERVICE_PRICES_FILE,
    WEIGHTS_FILE,
)
from scripts.validators.base import ValidationResults
from scripts.validators.helpers import validate_unit_consistency

from .constants import (
    EXPECTED_CURRENCY,
    EXPECTED_DIMENSION_UNIT,
    EXPECTED_PRICE_UNIT,
    EXPECTED_WEIGHT_UNIT,
)


def run_validate_weight_units(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    products: dict[str, Any] | None,
    weight_tiers: dict[str, Any] | None,
) -> None:
    if not all([graph, products, weight_tiers]):
        return

    assert graph is not None
    assert products is not None
    assert weight_tiers is not None

    graph_weight = graph.get("unit", {}).get("weight")
    products_weight = products.get("unit", {}).get("weight")
    weight_tiers_weight = weight_tiers.get("unit", {}).get("weight")

    validate_unit_consistency(
        unit_name="weight",
        graph_unit_value=graph_weight,
        expected_value=EXPECTED_WEIGHT_UNIT,
        file_names=[GRAPH_FILE, PRODUCTS_FILE, WEIGHTS_FILE],
        results=results,
        other_values=[products_weight, weight_tiers_weight],
    )


def run_validate_dimension_units(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    envelopes: dict[str, Any] | None,
    envelope_layouts: dict[str, Any] | None,
) -> None:
    if not all([graph, envelopes]):
        return

    assert graph is not None
    assert envelopes is not None

    graph_dimension = graph.get("unit", {}).get("dimension")
    formats_dimension = envelopes.get("unit", {}).get("dimension")

    layouts_dimension = None
    if envelope_layouts:
        layouts_dimension = envelope_layouts.get("unit", {}).get("dimension")

    validate_unit_consistency(
        unit_name="dimension",
        graph_unit_value=graph_dimension,
        expected_value=EXPECTED_DIMENSION_UNIT,
        file_names=[GRAPH_FILE, ENVELOPES_FILE, LAYOUTS_FILE],
        results=results,
        other_values=[formats_dimension, layouts_dimension],
    )


def run_validate_price_units(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    product_prices_doc: dict[str, Any] | None,
    service_prices_doc: dict[str, Any] | None,
) -> None:
    if not all([graph, product_prices_doc]):
        return

    assert graph is not None
    assert product_prices_doc is not None

    graph_price = graph.get("unit", {}).get("price")
    pp_price = product_prices_doc.get("unit", {}).get("price")
    sp_price = service_prices_doc.get("unit", {}).get("price") if service_prices_doc else None

    validate_unit_consistency(
        unit_name="price",
        graph_unit_value=graph_price,
        expected_value=EXPECTED_PRICE_UNIT,
        file_names=[GRAPH_FILE, PRODUCT_PRICES_FILE, SERVICE_PRICES_FILE],
        results=results,
        other_values=[pp_price, sp_price],
    )


def run_validate_currency_units(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    product_prices_doc: dict[str, Any] | None,
    service_prices_doc: dict[str, Any] | None,
    market: dict[str, Any] | None = None,
) -> None:
    if not all([graph, product_prices_doc]):
        return

    assert graph is not None
    assert product_prices_doc is not None

    graph_currency = graph.get("unit", {}).get("currency")
    pp_currency = product_prices_doc.get("unit", {}).get("currency")
    sp_currency = service_prices_doc.get("unit", {}).get("currency") if service_prices_doc else None

    market_currency = market.get("currency") if market else None
    expected_ccy = (
        str(market_currency)
        if market_currency
        else (str(graph_currency) if graph_currency else EXPECTED_CURRENCY)
    )

    if market_currency and graph_currency and graph_currency != market_currency:
        results["errors"].append(
            f"{GRAPH_FILE} unit.currency {graph_currency!r} != "
            f"policy/markets.json currency {market_currency!r}"
        )

    validate_unit_consistency(
        unit_name="currency",
        graph_unit_value=graph_currency,
        expected_value=expected_ccy,
        file_names=[GRAPH_FILE, PRODUCT_PRICES_FILE, SERVICE_PRICES_FILE],
        results=results,
        other_values=[pp_currency, sp_currency],
    )


def run_validate_row_ccy(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    product_prices_doc: dict[str, Any] | None,
    service_prices_doc: dict[str, Any] | None,
    market: dict[str, Any] | None = None,
) -> None:
    """Validate per-row currency overrides: only when row differs from file default."""
    if not graph:
        return

    graph_currency = graph.get("unit", {}).get("currency")
    intl_ccy: list[str] = []
    market_currency: str | None = None
    if market:
        market_currency = (
            market.get("currency") if isinstance(market.get("currency"), str) else None
        )
        raw_intl = market.get("intl_ccy")
        if isinstance(raw_intl, list):
            intl_ccy = [str(c) for c in raw_intl if isinstance(c, str)]

    def _check_rows(
        rows: list[Any] | None,
        file_label: str,
        file_currency: str | None,
        row_id_key: str,
        zone_key: str | None = None,
    ) -> None:
        if not rows or not file_currency:
            return
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            row_ccy = row.get("currency")
            if row_ccy is None:
                if (
                    zone_key
                    and row.get(zone_key) == "world"
                    and intl_ccy
                    and file_currency == market_currency
                ):
                    row_ref = row.get(row_id_key, idx)
                    results["errors"].append(
                        f"{file_label}[{idx}] ({row_id_key}={row_ref!r}, zone=world): "
                        f"must set currency in {intl_ccy!r} (international rows)"
                    )
                continue
            if row_ccy == file_currency:
                row_ref = row.get(row_id_key, idx)
                results["errors"].append(
                    f"{file_label}[{idx}] ({row_id_key}={row_ref!r}): "
                    f"row currency {row_ccy!r} matches file unit.currency; omit the override"
                )
            elif intl_ccy and row_ccy not in intl_ccy:
                row_ref = row.get(row_id_key, idx)
                results["errors"].append(
                    f"{file_label}[{idx}] ({row_id_key}={row_ref!r}): "
                    f"row currency {row_ccy!r} must be in market intl_ccy {intl_ccy!r}"
                )
            if graph_currency and row_ccy == graph_currency and row_ccy != file_currency:
                row_ref = row.get(row_id_key, idx)
                results["warnings"].append(
                    f"{file_label}[{idx}] ({row_id_key}={row_ref!r}): "
                    f"row currency {row_ccy!r} equals graph.unit.currency but file default is "
                    f"{file_currency!r} — intentional mixed-currency file"
                )

    if product_prices_doc:
        pp_ccy = product_prices_doc.get("unit", {}).get("currency")
        rows = product_prices_doc.get("product_prices")
        if isinstance(rows, list):
            _check_rows(
                rows,
                PRODUCT_PRICES_FILE,
                str(pp_ccy) if pp_ccy else None,
                "product_id",
                zone_key="zone",
            )

    if service_prices_doc:
        sp_ccy = service_prices_doc.get("unit", {}).get("currency")
        rows = service_prices_doc.get("service_prices")
        if isinstance(rows, list):
            _check_rows(
                rows,
                SERVICE_PRICES_FILE,
                str(sp_ccy) if sp_ccy else None,
                "service_id",
            )


def run_validate_units(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    products: dict[str, Any] | None,
    weight_tiers: dict[str, Any] | None,
    envelopes: dict[str, Any] | None,
    envelope_layouts: dict[str, Any] | None,
    product_prices_doc: dict[str, Any] | None,
    service_prices_doc: dict[str, Any] | None,
    market: dict[str, Any] | None = None,
) -> None:
    run_validate_weight_units(results, graph=graph, products=products, weight_tiers=weight_tiers)
    run_validate_dimension_units(
        results,
        graph=graph,
        envelopes=envelopes,
        envelope_layouts=envelope_layouts,
    )
    run_validate_price_units(
        results,
        graph=graph,
        product_prices_doc=product_prices_doc,
        service_prices_doc=service_prices_doc,
    )
    run_validate_currency_units(
        results,
        graph=graph,
        product_prices_doc=product_prices_doc,
        service_prices_doc=service_prices_doc,
        market=market,
    )
    run_validate_row_ccy(
        results,
        graph=graph,
        product_prices_doc=product_prices_doc,
        service_prices_doc=service_prices_doc,
        market=market,
    )
