"""``graph.dependencies`` completeness and circular dependency hints."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE
from scripts.validators.base import ValidationResults


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


def run_validate_circular_dependencies(
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
