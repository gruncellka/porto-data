"""Validate zone-scoped delivery SLAs and product resolution facts on providers/*/products.json."""

from __future__ import annotations

from typing import Any

from scripts.data_files import (
    get_data_file_path,
    get_project_root,
    list_provider_ids,
    load_providers_registry,
)
from scripts.utils import load_json

_VALID_SPANS = frozenset({"next", "within", "between"})
_VALID_WEEKDAYS = frozenset({"mon_fri", "mon_sat"})

_LAPOSTE_INDEMNITY_TIER_BY_ID: dict[str, str] = {
    "lettre_recommandee_r_un": "R1",
    "lettre_recommandee_r_deux": "R2",
    "lettre_recommandee_r_trois": "R3",
    "lettre_recommandee_internationale_r_un": "R1",
}


def _provider_countries() -> dict[str, str]:
    reg = load_providers_registry()
    providers = reg.get("providers")
    if not isinstance(providers, dict):
        return {}
    out: dict[str, str] = {}
    for pid, row in providers.items():
        if isinstance(row, dict) and isinstance(row.get("country"), str):
            out[str(pid)] = str(row["country"]).upper()
    return out


def _load_feature_ids(provider: str, root: Any) -> set[str]:
    try:
        path = get_data_file_path("features", provider, project_root=root)
        doc = load_json(path)
    except (FileNotFoundError, OSError, ValueError):
        return set()
    features = doc.get("features")
    if not isinstance(features, list):
        return set()
    return {str(f["id"]) for f in features if isinstance(f, dict) and isinstance(f.get("id"), str)}


def _load_graph_product_edges(provider: str, root: Any) -> dict[str, dict[str, Any]]:
    try:
        path = get_data_file_path("graph", provider, project_root=root)
        doc = load_json(path)
    except (FileNotFoundError, OSError, ValueError):
        return {}
    edges = doc.get("edges")
    if not isinstance(edges, dict):
        return {}
    products = edges.get("products")
    if not isinstance(products, dict):
        return {}
    return {str(k): v for k, v in products.items() if isinstance(v, dict)}


def _delivery_zone_signature(product: dict[str, Any], zone: str) -> tuple[Any, ...] | None:
    delivery = product.get("delivery")
    if not isinstance(delivery, list):
        return None
    for entry in delivery:
        if not isinstance(entry, dict):
            continue
        zones_raw = entry.get("zones")
        if isinstance(zones_raw, list) and zone in zones_raw:
            return (
                entry.get("span"),
                entry.get("days_min"),
                entry.get("days_max"),
                entry.get("weekdays"),
            )
    return None


def _resolution_fingerprint(product: dict[str, Any], zone: str) -> tuple[Any, ...]:
    indemnity = product.get("indemnity")
    tier: str | None = None
    if isinstance(indemnity, dict) and isinstance(indemnity.get("tier"), str):
        tier = indemnity["tier"]
    included = product.get("included_features")
    if isinstance(included, list):
        features_key = frozenset(str(x) for x in included if isinstance(x, str))
    else:
        features_key = frozenset()
    return (
        _delivery_zone_signature(product, zone),
        tier,
        features_key,
        product.get("tracking_mode"),
    )


def _validate_included_features(
    *,
    provider: str,
    product_id: str,
    product: dict[str, Any],
    feature_ids: set[str],
    errors: list[str],
) -> None:
    prefix = f"providers/{provider}/products.json product {product_id!r}"
    included = product.get("included_features")
    if included is None:
        return
    if not isinstance(included, list):
        errors.append(f"{prefix}: included_features must be an array when set")
        return
    seen: set[str] = set()
    for feat in included:
        if not isinstance(feat, str):
            errors.append(f"{prefix}: included_features entries must be strings")
            continue
        if feat in seen:
            errors.append(f"{prefix}: duplicate included_features entry {feat!r}")
        seen.add(feat)
        if feature_ids and feat not in feature_ids:
            errors.append(
                f"{prefix}: included_features {feat!r} not found in providers/{provider}/features.json"
            )


def _validate_indemnity(
    *,
    provider: str,
    product_id: str,
    product: dict[str, Any],
    errors: list[str],
) -> None:
    prefix = f"providers/{provider}/products.json product {product_id!r}"
    indemnity = product.get("indemnity")
    is_recommandee = product_id.startswith("lettre_recommandee_")

    if provider == "laposte":
        if is_recommandee:
            if not isinstance(indemnity, dict):
                errors.append(f"{prefix}: lettre_recommandee_* must include indemnity")
                return
        elif indemnity is not None:
            errors.append(f"{prefix}: only lettre_recommandee_* products may set indemnity")
            return

    if indemnity is None:
        return
    if not isinstance(indemnity, dict):
        errors.append(f"{prefix}: indemnity must be an object")
        return

    tier = indemnity.get("tier")
    if not isinstance(tier, str) or not tier:
        errors.append(f"{prefix}: indemnity.tier must be a non-empty string")
    elif provider == "laposte":
        expected = _LAPOSTE_INDEMNITY_TIER_BY_ID.get(product_id)
        if expected is not None and tier != expected:
            errors.append(
                f"{prefix}: indemnity.tier must be {expected!r} for product id {product_id!r}"
            )

    max_raw = indemnity.get("max")
    if not isinstance(max_raw, dict):
        errors.append(f"{prefix}: indemnity.max must be an object")
        return
    amount = max_raw.get("amount")
    if not isinstance(amount, int) or amount < 1:
        errors.append(f"{prefix}: indemnity.max.amount must be an integer >= 1")


def _validate_delivery_entry(
    *,
    provider: str,
    product_id: str,
    product_zones: set[str],
    entry: Any,
    entry_index: int,
    errors: list[str],
) -> set[str]:
    prefix = f"providers/{provider}/products.json product {product_id!r} delivery[{entry_index}]"
    if not isinstance(entry, dict):
        errors.append(f"{prefix}: must be an object")
        return set()

    zones_raw = entry.get("zones")
    if not isinstance(zones_raw, list) or not zones_raw:
        errors.append(f"{prefix}: zones must be a non-empty array")
        return set()

    entry_zones: set[str] = set()
    for zone in zones_raw:
        if not isinstance(zone, str):
            errors.append(f"{prefix}: zone ids must be strings")
            continue
        if zone not in product_zones:
            errors.append(
                f"{prefix}: zone {zone!r} is not in product.zones {sorted(product_zones)}"
            )
        if zone in entry_zones:
            errors.append(f"{prefix}: duplicate zone {zone!r}")
        entry_zones.add(zone)

    span = entry.get("span")
    if span not in _VALID_SPANS:
        errors.append(f"{prefix}: span must be one of {sorted(_VALID_SPANS)}")

    days_max = entry.get("days_max")
    if not isinstance(days_max, int) or days_max < 1:
        errors.append(f"{prefix}: days_max must be an integer >= 1")

    days_min = entry.get("days_min")
    has_days_min = days_min is not None

    if span == "next":
        if days_max != 1:
            errors.append(f"{prefix}: span next requires days_max === 1")
        if has_days_min:
            errors.append(f"{prefix}: span next must not include days_min")
    elif span == "within":
        if has_days_min:
            errors.append(f"{prefix}: span within must not include days_min")
    elif span == "between":
        if not isinstance(days_min, int) or days_min < 1:
            errors.append(f"{prefix}: span between requires days_min >= 1")
        elif isinstance(days_max, int) and days_min > days_max:
            errors.append(f"{prefix}: days_min must be <= days_max")

    weekdays = entry.get("weekdays")
    if weekdays is not None and weekdays not in _VALID_WEEKDAYS:
        errors.append(f"{prefix}: weekdays must be one of {sorted(_VALID_WEEKDAYS)}")

    return entry_zones


def _validate_product_delivery(
    *,
    provider: str,
    product: dict[str, Any],
    errors: list[str],
) -> None:
    product_id = str(product.get("id", "<unknown>"))
    zones_raw = product.get("zones")
    if not isinstance(zones_raw, list):
        errors.append(
            f"providers/{provider}/products.json product {product_id!r}: zones must be an array"
        )
        return
    product_zones = {str(z) for z in zones_raw if isinstance(z, str)}

    delivery = product.get("delivery")
    if not isinstance(delivery, list) or not delivery:
        errors.append(
            f"providers/{provider}/products.json product {product_id!r}: delivery must be a non-empty array"
        )
        return

    covered: set[str] = set()
    for idx, entry in enumerate(delivery):
        entry_zones = _validate_delivery_entry(
            provider=provider,
            product_id=product_id,
            product_zones=product_zones,
            entry=entry,
            entry_index=idx,
            errors=errors,
        )
        overlap = covered & entry_zones
        if overlap:
            errors.append(
                f"providers/{provider}/products.json product {product_id!r}: "
                f"zones {sorted(overlap)} appear in more than one delivery entry"
            )
        covered |= entry_zones

    if covered != product_zones:
        missing = product_zones - covered
        extra = covered - product_zones
        if missing:
            errors.append(
                f"providers/{provider}/products.json product {product_id!r}: "
                f"delivery missing zones {sorted(missing)}"
            )
        if extra:
            errors.append(
                f"providers/{provider}/products.json product {product_id!r}: "
                f"delivery has unknown zones {sorted(extra)}"
            )

    _validate_swisspost_delivery_rules(provider, product_id, delivery, errors)


def _validate_swisspost_delivery_rules(
    provider: str,
    product_id: str,
    delivery: list[Any],
    errors: list[str],
) -> None:
    if provider != "swisspost":
        return
    if not product_id.startswith("b_post_"):
        if product_id.startswith("a_post_"):
            for entry in delivery:
                if isinstance(entry, dict) and entry.get("weekdays") is not None:
                    errors.append(
                        f"providers/swisspost/products.json product {product_id!r}: "
                        "a_post_* must not override weekdays (uses CH market mon_sat)"
                    )
        return

    for entry in delivery:
        if not isinstance(entry, dict):
            continue
        zones = entry.get("zones")
        if zones == ["domestic"] and entry.get("weekdays") != "mon_fri":
            errors.append(
                f"providers/swisspost/products.json product {product_id!r}: "
                "b_post_* domestic delivery must set weekdays mon_fri"
            )


def _validate_twin_disambiguation(
    *,
    provider: str,
    products_by_id: dict[str, dict[str, Any]],
    graph_edges: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    twin_groups: dict[tuple[str, str, str], list[str]] = {}
    for product_id, edge in graph_edges.items():
        product = products_by_id.get(product_id)
        if product is None:
            continue
        porto_id = product.get("porto_id")
        if not isinstance(porto_id, str):
            continue
        zones_raw = edge.get("zones")
        tiers_raw = edge.get("weight_tiers")
        if not isinstance(zones_raw, list) or not isinstance(tiers_raw, list):
            continue
        for zone in zones_raw:
            if not isinstance(zone, str):
                continue
            for tier in tiers_raw:
                if not isinstance(tier, str):
                    continue
                key = (porto_id, zone, tier)
                twin_groups.setdefault(key, []).append(product_id)

    for (porto_id, zone, tier), product_ids in twin_groups.items():
        unique_ids = sorted(set(product_ids))
        if len(unique_ids) < 2:
            continue
        fingerprints: dict[tuple[Any, ...], list[str]] = {}
        for pid in unique_ids:
            product = products_by_id[pid]
            fp = _resolution_fingerprint(product, zone)
            fingerprints.setdefault(fp, []).append(pid)
        for fp, pids in fingerprints.items():
            if len(pids) < 2:
                continue
            errors.append(
                f"providers/{provider}: products {pids} share porto_id={porto_id!r}, "
                f"zone={zone!r}, weight_tier={tier!r} and identical resolution fingerprint "
                f"{fp!r}; distinguish via delivery[], indemnity.tier, included_features, or tracking_mode"
            )


def validate_delivery() -> int:
    """Validate delivery[], included_features, indemnity, and twin disambiguation on products.json."""
    print("Validating delivery (zone SLAs)...\n")

    errors: list[str] = []
    root = get_project_root()
    countries = _provider_countries()

    for provider in list_provider_ids():
        if provider not in countries:
            errors.append(f"providers/{provider}: no country in providers.json")
            continue
        feature_ids = _load_feature_ids(provider, root)
        graph_edges = _load_graph_product_edges(provider, root)

        try:
            path = get_data_file_path("products", provider, project_root=root)
            doc = load_json(path)
        except (FileNotFoundError, OSError, ValueError) as e:
            errors.append(f"providers/{provider}/products.json: {e}")
            continue

        products = doc.get("products")
        if not isinstance(products, list):
            errors.append(f"providers/{provider}/products.json: missing products array")
            continue

        products_by_id: dict[str, dict[str, Any]] = {}
        for product in products:
            if not isinstance(product, dict):
                continue
            product_id = str(product.get("id", "<unknown>"))
            products_by_id[product_id] = product
            _validate_product_delivery(provider=provider, product=product, errors=errors)
            _validate_included_features(
                provider=provider,
                product_id=product_id,
                product=product,
                feature_ids=feature_ids,
                errors=errors,
            )
            _validate_indemnity(
                provider=provider,
                product_id=product_id,
                product=product,
                errors=errors,
            )

        _validate_twin_disambiguation(
            provider=provider,
            products_by_id=products_by_id,
            graph_edges=graph_edges,
            errors=errors,
        )

    for err in errors:
        print(f"❌ ERROR: {err}")
    if errors:
        print()
        print("❌ Delivery validation failed.")
        return 1

    print(f"✅ Delivery OK ({len(list_provider_ids())} providers).\n")
    return 0
