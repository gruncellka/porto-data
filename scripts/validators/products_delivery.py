"""Validate zone-scoped delivery SLAs on providers/*/products.json."""

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
        if zones == ["domestic"]:
            if entry.get("weekdays") != "mon_fri":
                errors.append(
                    f"providers/swisspost/products.json product {product_id!r}: "
                    "b_post_* domestic delivery must set weekdays mon_fri"
                )


def validate_products_delivery() -> int:
    """Validate delivery[] on all provider products.json files. Returns 0 if ok, 1 if errors."""
    print("Validating products delivery (zone SLAs)...\n")

    errors: list[str] = []
    root = get_project_root()
    countries = _provider_countries()

    for provider in list_provider_ids():
        if provider not in countries:
            errors.append(f"providers/{provider}: no country in providers.json")
            continue
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

        for product in products:
            if isinstance(product, dict):
                _validate_product_delivery(provider=provider, product=product, errors=errors)

    for err in errors:
        print(f"❌ ERROR: {err}")
    if errors:
        print()
        print("❌ Products delivery validation failed.")
        return 1

    print(f"✅ Products delivery OK ({len(list_provider_ids())} providers).\n")
    return 0
