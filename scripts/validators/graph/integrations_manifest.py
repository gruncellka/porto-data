"""Cross-file checks for ``providers/<id>/integrations.json`` (SDK execution manifest)."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, INTEGRATIONS_FILE
from scripts.validators.base import ValidationResults

from .edge_access import wire_integration_ids


def _integrations_dependency(graph: dict[str, Any]) -> dict[str, Any] | None:
    dependencies = graph.get("dependencies")
    if not isinstance(dependencies, dict):
        return None
    entry = dependencies.get("integrations")
    return entry if isinstance(entry, dict) else None


def run_validate_integrations_manifest(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    integrations: dict[str, Any] | None,
    provider_id: str,
) -> None:
    """Align integrations.json with graph.dependencies and graph.edges.wire."""
    if graph is None or not isinstance(graph, dict):
        return

    wire_ids = wire_integration_ids(graph)
    dependency = _integrations_dependency(graph)
    has_manifest = integrations is not None

    if dependency is not None:
        dep_file = dependency.get("file")
        if dep_file != INTEGRATIONS_FILE:
            results["errors"].append(
                f"{GRAPH_FILE}: dependencies.integrations.file must be "
                f"{INTEGRATIONS_FILE!r}, got {dep_file!r}"
            )
        elif not has_manifest:
            results["errors"].append(
                f"{GRAPH_FILE}: dependencies.integrations references "
                f"{INTEGRATIONS_FILE} but the file is missing"
            )
        else:
            results["correct"].append(
                f"dependencies.integrations.file points at {INTEGRATIONS_FILE}"
            )

    if not has_manifest:
        if dependency is not None:
            return
        if wire_ids:
            results["warnings"].append(
                f"{GRAPH_FILE}: edges.wire defines {sorted(wire_ids)} but "
                f"{INTEGRATIONS_FILE} is absent (optional until an SDK adapter ships)"
            )
        return

    manifest = integrations
    if not isinstance(manifest, dict):
        return

    if dependency is None:
        results["warnings"].append(
            f"{INTEGRATIONS_FILE} exists but {GRAPH_FILE} dependencies.integrations is missing"
        )

    if manifest.get("provider") != provider_id:
        results["errors"].append(
            f"{INTEGRATIONS_FILE}: provider must be {provider_id!r}, "
            f"got {manifest.get('provider')!r}"
        )

    adapter = manifest.get("adapter")
    if not isinstance(adapter, str) or not adapter.strip():
        results["errors"].append(f"{INTEGRATIONS_FILE}: adapter must be a non-empty string")
        return

    adapter_id = adapter.strip().lower()
    if adapter_id not in wire_ids:
        results["errors"].append(
            f"{INTEGRATIONS_FILE}: adapter {adapter_id!r} must match a key in "
            f"{GRAPH_FILE} edges.wire (have {sorted(wire_ids) or 'none'})"
        )
    else:
        results["correct"].append(f"integrations.adapter {adapter_id!r} matches edges.wire")
