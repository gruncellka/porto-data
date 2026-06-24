"""Country fiscal policy in policy/markets.json."""

import json
from typing import Any, cast

import pytest
from jsonschema import Draft7Validator

from scripts.data_files import (
    get_data_file_path,
    get_project_root,
    load_markets,
    market_for_country,
)
from scripts.validators.markets import validate_markets


def _load_providers_doc() -> dict[str, Any]:
    path = get_data_file_path("providers")
    if not path.is_file():
        pytest.skip("providers.json missing")
    with open(path, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def test_markets_json_invariants() -> None:
    doc = load_markets()
    assert doc["file_type"] == "markets"
    markets = doc["markets"]
    assert isinstance(markets, dict)
    for cc in ("DE", "FR", "CH", "UA"):
        assert cc in markets
        assert markets[cc]["currency"] in ("EUR", "CHF", "UAH", "USD")
    ua = markets["UA"]
    assert ua["international_currency"] == ["USD"]
    assert ua["vat"]["rate"] == 0.2
    assert ua["vat"]["domestic"]["inclusive"] is True
    assert ua["vat"]["international"]["inclusive"] is False
    assert ua["settlement"]["fx"] == "NBU"


def test_provider_countries_have_market() -> None:
    pdoc = _load_providers_doc()
    markets = load_markets()["markets"]
    prov = pdoc.get("providers") or {}
    for pid, row in prov.items():
        cc = str(row["country"]).upper()
        assert cc in markets, f"providers.{pid}.country {cc!r} missing in markets"
        assert "vat" not in row, f"providers.{pid} must not carry vat (use markets)"


def test_global_markets_json_matches_schema() -> None:
    root = get_project_root()
    data_path = get_data_file_path("markets")
    schema_path = root / "schemas" / "markets.schema.json"
    if not data_path.exists():
        pytest.skip("markets.json not in test root")
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    Draft7Validator(schema).validate(data)


def test_get_data_file_path_markets() -> None:
    root = get_project_root()
    p = get_data_file_path("markets")
    assert p == root / "policy" / "markets.json"


def test_market_for_country() -> None:
    row = market_for_country("UA")
    assert row["currency"] == "UAH"


def test_validate_markets_real_tree() -> None:
    assert validate_markets() == 0


def test_market_for_country_missing_raises() -> None:
    with pytest.raises(ValueError, match="markets\\['XX'\\]"):
        market_for_country("XX", markets_doc={"markets": {"DE": {"currency": "EUR"}}})
