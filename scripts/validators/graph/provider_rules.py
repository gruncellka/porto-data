"""Optional ``rules.json`` (provider metric band attach rules)."""

from __future__ import annotations

from typing import Any

from scripts.validators.base import ValidationResults

from .constants import (
    PROVIDER_RULE_METRIC_THICKNESS,
    RULE_KIND_BAND,
)
from .services import service_refs_set


def run_validate_provider_rules(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    doc: dict[str, Any] | None,
    product_dict: dict[str, dict[str, Any]],
    service_prices: list[dict[str, Any]],
    services: dict[str, Any] | None,
) -> None:
    if not doc:
        return
    if doc.get("file_type") != "provider_rules":
        results["errors"].append(
            f"rules.json: file_type must be 'provider_rules' (got {doc.get('file_type')!r})"
        )
        return
    if doc.get("provider") is not None:
        results["errors"].append(
            "rules.json: top-level 'provider' is path-implied — remove redundant field"
        )
    rules_raw = doc.get("rules")
    if not isinstance(rules_raw, list):
        results["errors"].append("rules.json: rules must be an array")
        return

    valid_refs = service_refs_set(services)
    service_price_ids = {str(sp.get("service_id")) for sp in service_prices if sp.get("service_id")}
    product_ids = set(product_dict.keys())
    unit_raw = doc.get("unit")
    unit_block: dict[str, Any] = unit_raw if isinstance(unit_raw, dict) else {}
    uses_thickness_metric = any(
        isinstance(r, dict)
        and r.get("kind") == RULE_KIND_BAND
        and str(r.get("metric") or "") == PROVIDER_RULE_METRIC_THICKNESS
        for r in rules_raw
    )
    if uses_thickness_metric and unit_block.get("thickness") != "mm":
        results["errors"].append(
            "rules.json: metric 'thickness' requires document unit.thickness 'mm' "
            f"(got {unit_block.get('thickness')!r})"
        )

    for rule in rules_raw:
        if not isinstance(rule, dict):
            results["errors"].append("rules.json: each rule must be an object")
            continue
        rid = rule.get("id", "?")
        kind = rule.get("kind")
        if kind != RULE_KIND_BAND:
            results["errors"].append(f"rules.json rule {rid!r}: unsupported kind {kind!r}")
            continue
        metric = rule.get("metric")
        if str(metric) != PROVIDER_RULE_METRIC_THICKNESS:
            results["errors"].append(
                f"rules.json rule {rid!r}: unsupported metric {metric!r} "
                f"(validator currently checks {PROVIDER_RULE_METRIC_THICKNESS!r} only)"
            )
            continue
        for pid in rule.get("product_ids") or []:
            if str(pid) not in product_ids:
                results["errors"].append(f"rules.json rule {rid!r}: unknown product_id {pid!r}")
        sid = rule.get("service_id")
        if not sid or str(sid) not in valid_refs:
            results["errors"].append(f"rules.json rule {rid!r}: unknown service_id {sid!r}")
        elif str(sid) not in service_price_ids:
            results["warnings"].append(
                f"rules.json rule {rid!r}: service {sid!r} has no row in service_prices"
            )
        lo = rule.get("min_exclusive")
        hi = rule.get("max_inclusive")
        if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
            results["errors"].append(
                f"rules.json rule {rid!r}: min_exclusive and max_inclusive must be numbers"
            )
        elif lo >= hi:
            results["errors"].append(
                f"rules.json rule {rid!r}: min_exclusive must be < max_inclusive"
            )

    if not results["errors"]:
        results["correct"].append("rules.json references are consistent with catalog and prices")
