"""Validate policy/markets.json against providers.json and fiscal shape rules."""

from __future__ import annotations

from typing import Any

from scripts.data_files import (
    load_markets,
    load_providers_registry,
)

_VALID_CURRENCIES = frozenset({"EUR", "CHF", "UAH", "USD"})

_DEPRECATED_MARKET_KEYS: dict[str, str] = {
    "intl_ccy": "international_currency",
}

_DEPRECATED_VAT_KEYS: dict[str, str] = {
    "intl_excl": "vat.international.inclusive",
    "inclusive": "vat.domestic.inclusive / vat.international.inclusive",
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


_VALID_WEEKDAYS = frozenset({"mon_fri", "mon_sat"})


def _validate_working_days(country: str, row: dict[str, Any], errors: list[str]) -> None:
    wd = row.get("working_days")
    if wd is None:
        errors.append(f"markets.{country}: working_days is required")
        return
    if not isinstance(wd, dict):
        errors.append(f"markets.{country}: working_days must be an object")
        return
    weekdays = wd.get("weekdays")
    if weekdays not in _VALID_WEEKDAYS:
        errors.append(
            f"markets.{country}: working_days.weekdays must be one of {sorted(_VALID_WEEKDAYS)}"
        )
    if not isinstance(wd.get("exclude_public_holidays"), bool):
        errors.append(f"markets.{country}: working_days.exclude_public_holidays must be a boolean")


def _validate_market_row(country: str, row: dict[str, Any], errors: list[str]) -> None:
    currency = row.get("currency")
    if not isinstance(currency, str) or currency not in _VALID_CURRENCIES:
        errors.append(f"markets.{country}: currency must be one of {sorted(_VALID_CURRENCIES)}")

    for deprecated, replacement in _DEPRECATED_MARKET_KEYS.items():
        if deprecated in row:
            errors.append(f"markets.{country}: deprecated key {deprecated!r}; use {replacement!r}")

    intl_currencies = row.get("international_currency")
    if intl_currencies is not None:
        if not isinstance(intl_currencies, list) or not intl_currencies:
            errors.append(
                f"markets.{country}: international_currency must be a non-empty array when set"
            )
        else:
            for code in intl_currencies:
                if not isinstance(code, str) or code not in _VALID_CURRENCIES:
                    errors.append(
                        f"markets.{country}: international_currency entry {code!r} is not a valid currency"
                    )
                elif isinstance(currency, str) and code == currency:
                    errors.append(
                        f"markets.{country}: international_currency must not include domestic currency {currency!r}"
                    )

    vat = row.get("vat")
    if vat is not None:
        if not isinstance(vat, dict):
            errors.append(f"markets.{country}: vat must be an object when set")
        else:
            for deprecated, replacement in _DEPRECATED_VAT_KEYS.items():
                if deprecated in vat:
                    errors.append(
                        f"markets.{country}: deprecated vat.{deprecated}; use {replacement}"
                    )
            if vat.get("exempt") is True and vat.get("rate") is not None:
                errors.append(
                    f"markets.{country}: vat.rate must be omitted when vat.exempt is true"
                )
            if vat.get("exempt") is True and (
                vat.get("domestic") is not None or vat.get("international") is not None
            ):
                errors.append(
                    f"markets.{country}: vat.domestic/international must be omitted when vat.exempt is true"
                )

    settlement = row.get("settlement")
    if settlement is not None and not isinstance(settlement, dict):
        errors.append(f"markets.{country}: settlement must be an object when set")

    _validate_working_days(country, row, errors)


def validate_markets() -> int:
    """Validate markets policy. Returns 0 if ok, 1 if errors."""
    print("Validating policy/markets.json...\n")

    errors: list[str] = []

    try:
        doc = load_markets()
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ ERROR: {e}")
        return 1

    markets = doc.get("markets")
    if not isinstance(markets, dict):
        print("❌ ERROR: policy/markets.json missing 'markets' object")
        return 1

    countries = _provider_countries()
    for pid, cc in countries.items():
        if cc not in markets:
            errors.append(
                f"providers.{pid}.country {cc!r} has no markets.{cc} entry in policy/markets.json"
            )
            continue
        row = markets.get(cc)
        if isinstance(row, dict):
            _validate_market_row(cc, row, errors)
        else:
            errors.append(f"markets.{cc}: entry must be an object")

    for err in errors:
        print(f"❌ ERROR: {err}")
    if errors:
        print()
        print("❌ Markets validation failed.")
        return 1

    print(f"✅ Markets OK ({len(countries)} provider countries covered).\n")
    return 0
