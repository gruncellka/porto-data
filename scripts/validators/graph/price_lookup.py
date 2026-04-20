"""Price lookup block under graph.global_settings (file refs, arrays, match keys)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.data_files import (
    GRAPH_FILE,
    PRODUCT_PRICES_FILE,
    PROVIDERS_DIR,
    SERVICE_PRICES_FILE,
    get_data_file_path,
)
from scripts.validators.base import ValidationResults

from .constants import EXPECTED_PRODUCT_PRICES_ARRAY, EXPECTED_SERVICE_PRICES_ARRAY


def _validate_file_reference(
    results: ValidationResults,
    all_data_files: set[str],
    actual: str,
    expected: str,
    field_name: str,
    path_parts: list[str],
) -> None:
    if actual == expected:
        if expected in all_data_files:
            results["correct"].append(f"{field_name} '{expected}' matches actual file")
        else:
            results["errors"].append(
                f"{field_name} references '{expected}' but file doesn't exist. "
                f"Found in: {GRAPH_FILE} -> {' -> '.join(path_parts)}"
            )
    else:
        results["errors"].append(
            f"{field_name} '{actual}' should be '{expected}'. "
            f"Found in: {GRAPH_FILE} -> {' -> '.join(path_parts)}"
        )


def _validate_lookup_array(
    results: ValidationResults,
    lookup_array: str,
    expected: str,
    label: str,
    doc: dict[str, Any] | None,
    top_key: str,
) -> None:
    path_hint = f"{GRAPH_FILE} -> global_settings -> price_lookup -> {label} -> array"
    if lookup_array == expected:
        if doc and top_key in doc and isinstance(doc.get(top_key), list):
            results["correct"].append(
                f"price_lookup.{label}.array '{expected}' matches actual structure"
            )
        else:
            results["errors"].append(
                f"Lookup references '{expected}' but structure doesn't match. Found in: {path_hint}"
            )
    else:
        results["warnings"].append(
            f"price_lookup.{label}.array path {lookup_array!r} — expected {expected!r}. {path_hint}"
        )


def _validate_lookup_match_keys(
    results: ValidationResults,
    lookup_match: dict[str, Any],
    *,
    for_product_prices: bool,
    product_prices: list[dict[str, Any]],
    service_prices: list[dict[str, Any]],
) -> None:
    path = (
        f"{GRAPH_FILE} -> global_settings -> price_lookup -> "
        f"{'product_prices' if for_product_prices else 'service_prices'} -> match"
    )
    if for_product_prices:
        if not product_prices:
            results["warnings"].append(
                "No product prices found to validate price_lookup.product_prices.match keys"
            )
            return
        sample_keys = set(product_prices[0].keys())
    else:
        if not service_prices:
            results["warnings"].append(
                "No service prices found to validate price_lookup.service_prices.match keys"
            )
            return
        sample_keys = set(service_prices[0].keys())

    expected_match_keys = set(lookup_match.keys())
    match_keys_to_check = {k for k in expected_match_keys if k != "description"}
    missing_keys = match_keys_to_check - sample_keys
    if missing_keys:
        results["errors"].append(
            f"price_lookup match keys {sorted(missing_keys)} do not exist in entries. "
            f"Available keys: {sorted(sample_keys)}. Found in: {path}"
        )
    else:
        results["correct"].append(
            f"price_lookup match keys {sorted(match_keys_to_check)} exist in entries ({path})"
        )


def run_price_lookup_validation(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
    shared_bundle_subdir: Path,
    bundle_root: Path,
    provider_dir: Path,
    all_data_files: set[str],
    product_prices_doc: dict[str, Any] | None,
    service_prices_doc: dict[str, Any] | None,
    product_prices: list[dict[str, Any]],
    service_prices: list[dict[str, Any]],
) -> None:
    """Validate ``global_settings.price_lookup`` (paths, arrays, match keys)."""
    global_settings = graph.get("global_settings", {})
    price_lookup = global_settings.get("price_lookup", {})
    if not isinstance(price_lookup, dict):
        return

    pp = price_lookup.get("product_prices", {})
    sp = price_lookup.get("service_prices", {})

    if shared_bundle_subdir == bundle_root:
        expected_pp = f"prices/{PRODUCT_PRICES_FILE}"
        expected_sp = f"prices/{SERVICE_PRICES_FILE}"
    else:
        prov = provider_dir.name
        root = bundle_root
        pbase = root / PROVIDERS_DIR / prov
        expected_pp = (
            get_data_file_path("product_prices", prov, project_root=root)
            .relative_to(pbase)
            .as_posix()
        )
        expected_sp = (
            get_data_file_path("service_prices", prov, project_root=root)
            .relative_to(pbase)
            .as_posix()
        )

    _validate_file_reference(
        results,
        all_data_files,
        pp.get("file", "") if isinstance(pp, dict) else "",
        expected_pp,
        "price_lookup.product_prices.file",
        ["global_settings", "price_lookup", "product_prices", "file"],
    )
    _validate_file_reference(
        results,
        all_data_files,
        sp.get("file", "") if isinstance(sp, dict) else "",
        expected_sp,
        "price_lookup.service_prices.file",
        ["global_settings", "price_lookup", "service_prices", "file"],
    )

    if isinstance(pp, dict):
        _validate_lookup_array(
            results,
            pp.get("array", ""),
            EXPECTED_PRODUCT_PRICES_ARRAY,
            "product_prices",
            product_prices_doc,
            "product_prices",
        )
        _validate_lookup_match_keys(
            results,
            pp.get("match", {}),
            for_product_prices=True,
            product_prices=product_prices,
            service_prices=service_prices,
        )

    if isinstance(sp, dict):
        _validate_lookup_array(
            results,
            sp.get("array", ""),
            EXPECTED_SERVICE_PRICES_ARRAY,
            "service_prices",
            service_prices_doc,
            "service_prices",
        )
        _validate_lookup_match_keys(
            results,
            sp.get("match", {}),
            for_product_prices=False,
            product_prices=product_prices,
            service_prices=service_prices,
        )
