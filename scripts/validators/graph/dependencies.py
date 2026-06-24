"""``graph.dependencies`` completeness, price file refs, and circular dependency hints."""

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

from .constants import PRICE_KEY_PRODUCTS, PRICE_KEY_SERVICES


def run_validate_dependencies(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
    all_data_files: set[str],
) -> None:
    dependencies = graph.get("dependencies", {})

    expected_data_files = all_data_files - {GRAPH_FILE}
    files_in_dependencies = {dep_data.get("file") for dep_data in dependencies.values()}
    missing_in_dependencies = expected_data_files - files_in_dependencies

    if missing_in_dependencies:
        results["fixes_needed"].append(
            f"Data files not in dependencies section: {sorted(missing_in_dependencies)}"
        )
    else:
        results["correct"].append("All data files are covered in dependencies section")

    for dep_name, dep_data in dependencies.items():
        dep_file = dep_data.get("file")
        if dep_file not in all_data_files:
            results["warnings"].append(f"Dependency file '{dep_file}' is not a known data file")

        depends_on = dep_data.get("depends_on", [])
        for dep_file_name in depends_on:
            if dep_file_name not in all_data_files:
                results["warnings"].append(
                    f"Dependency '{dep_file_name}' in '{dep_name}' is not a known data file"
                )


def run_validate_cycles(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
) -> None:
    dependencies = graph.get("dependencies", {})
    if not isinstance(dependencies, dict):
        return

    file_ref_to_dep: dict[str, str] = {}
    for dep_name, dep_data in dependencies.items():
        df = dep_data.get("file") if isinstance(dep_data, dict) else None
        if isinstance(df, str) and df:
            file_ref_to_dep[df] = dep_name

    dep_graph: dict[str, set[str]] = {}
    for dep_name, dep_data in dependencies.items():
        if not isinstance(dep_data, dict):
            continue
        resolved: set[str] = set()
        for d in dep_data.get("depends_on", []) or []:
            if not isinstance(d, str):
                continue
            target = file_ref_to_dep.get(d)
            if target:
                resolved.add(target)
        dep_graph[dep_name] = resolved

    if "products" in dep_graph.get("product_prices", set()) and "product_prices" in dep_graph.get(
        "products", set()
    ):
        results["warnings"].append(
            "Circular dependency: products ↔ product_prices — review intentional or not."
        )


def run_validate_price_dependencies(
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
    """Validate price file paths via ``dependencies`` and row keys from price schemas."""
    dependencies = graph.get("dependencies", {})
    if not isinstance(dependencies, dict):
        return

    if shared_bundle_subdir == bundle_root:
        expected_pp = f"prices/{PRODUCT_PRICES_FILE}"
        expected_sp = f"prices/{SERVICE_PRICES_FILE}"
    else:
        prov = provider_dir.name
        pbase = bundle_root / PROVIDERS_DIR / prov
        expected_pp = (
            get_data_file_path("product_prices", prov, project_root=bundle_root)
            .relative_to(pbase)
            .as_posix()
        )
        expected_sp = (
            get_data_file_path("service_prices", prov, project_root=bundle_root)
            .relative_to(pbase)
            .as_posix()
        )

    specs: tuple[tuple[str, str, str, list[dict[str, Any]], set[str]], ...] = (
        (
            "product_prices",
            expected_pp,
            PRICE_KEY_PRODUCTS,
            product_prices,
            {"product_id", "zone", "weight_tier"},
        ),
        (
            "service_prices",
            expected_sp,
            PRICE_KEY_SERVICES,
            service_prices,
            {"service_id"},
        ),
    )

    for dep_name, expected_path, array_key, rows, required_keys in specs:
        dep = dependencies.get(dep_name, {})
        actual_path = dep.get("file", "") if isinstance(dep, dict) else ""
        path_hint = f"{GRAPH_FILE} -> dependencies -> {dep_name} -> file"
        if actual_path == expected_path:
            if expected_path in all_data_files:
                results["correct"].append(
                    f"dependencies.{dep_name}.file '{expected_path}' matches bundle layout"
                )
            else:
                results["errors"].append(
                    f"dependencies.{dep_name}.file references '{expected_path}' but file "
                    f"does not exist. Found in: {path_hint}"
                )
        else:
            results["errors"].append(
                f"dependencies.{dep_name}.file '{actual_path}' should be '{expected_path}'. "
                f"Found in: {path_hint}"
            )

        doc = product_prices_doc if dep_name == "product_prices" else service_prices_doc
        if doc and array_key in doc and isinstance(doc.get(array_key), list):
            results["correct"].append(
                f"dependencies.{dep_name} target has '{array_key}' array in price file"
            )
        else:
            results["errors"].append(
                f"Price file for {dep_name} missing '{array_key}' array. "
                f"Expected path: {expected_path}"
            )

        if not rows:
            results["warnings"].append(
                f"No {dep_name} rows found to validate required keys {sorted(required_keys)}"
            )
            continue
        sample_keys = set(rows[0].keys())
        missing = required_keys - sample_keys
        if missing:
            results["errors"].append(
                f"{dep_name} rows missing keys {sorted(missing)}; "
                f"available keys: {sorted(sample_keys)}"
            )
        else:
            results["correct"].append(
                f"{dep_name} rows include required keys {sorted(required_keys)}"
            )
