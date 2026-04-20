"""Jurisdiction reference data (EU/UN/CH blocs + per-country timezones) in policy/jurisdictions.json."""

import json
from typing import Any, cast

import pytest
from jsonschema import Draft7Validator

from scripts.data_files import get_data_file_path, get_project_root


def _load_jurisdictions_doc() -> dict[str, Any]:
    path = get_data_file_path("jurisdictions")
    if not path.is_file():
        pytest.skip("jurisdictions.json missing")
    with open(path, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def _load_providers_doc() -> dict[str, Any]:
    path = get_data_file_path("providers")
    if not path.is_file():
        pytest.skip("providers.json missing")
    with open(path, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def test_jurisdictions_json_invariants() -> None:
    doc = _load_jurisdictions_doc()
    assert doc["file_type"] == "jurisdictions"
    unit = doc["unit"]
    assert unit["country_code"] == "ISO 3166-1 alpha-2"
    assert unit.get("region_code") == "ISO 3166-2"
    assert unit.get("date") == "ISO 8601"
    g = doc["jurisdictions"]
    assert isinstance(g, dict)
    assert {"eu", "un"}.issubset(g.keys())
    assert "ch" not in g
    assert "CH" in g
    for tag in ("eu", "un"):
        bloc = g[tag]
        assert isinstance(bloc, dict)
        assert "members" in bloc and "timezone" in bloc
        assert isinstance(bloc["members"], list)
        assert isinstance(bloc["timezone"], str) and bloc["timezone"].strip()
    eu = set(g["eu"]["members"])
    un = set(g["un"]["members"])
    assert len(un) == 193
    assert len(eu) == 27
    assert eu <= un
    assert g["eu"]["timezone"] == "Europe/Brussels"
    assert g["un"]["timezone"] == "Europe/Zurich"
    assert g["CH"]["timezone"] == "Europe/Zurich"
    assert "registry_timezones" not in doc
    assert "jurisdiction_timezones" not in doc
    country_keys = {k for k in g if len(k) == 2 and k.isalpha() and k.isupper()}
    un_upper = {str(c).upper() for c in un}
    assert country_keys == un_upper
    assert g["US"]["timezone"] == "America/New_York"
    assert g["AU"]["timezone"] == "Australia/Sydney"


def test_provider_countries_have_jurisdiction_timezone() -> None:
    jdoc = _load_jurisdictions_doc()
    pdoc = _load_providers_doc()
    g = jdoc["jurisdictions"]
    prov = pdoc.get("providers") or {}
    assert isinstance(prov, dict)
    for pid, row in prov.items():
        assert isinstance(row, dict), pid
        cc = row.get("country")
        assert isinstance(cc, str) and len(cc.strip()) >= 2, pid
        iso = cc.strip().upper()[:2]
        assert iso in g, f"providers.{pid}.country {iso!r} missing in jurisdictions"
        bloc = g[iso]
        assert isinstance(bloc, dict), iso
        tz = bloc.get("timezone")
        assert isinstance(tz, str) and tz.strip(), iso
        assert "timezone" not in row, f"providers.{pid} must not duplicate timezone"


def test_global_jurisdictions_json_matches_schema() -> None:
    root = get_project_root()
    data_path = get_data_file_path("jurisdictions")
    schema_path = root / "schemas" / "jurisdictions.schema.json"
    if not data_path.exists():
        pytest.skip("jurisdictions.json not in test root")
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    Draft7Validator(schema).validate(data)


def test_get_data_file_path_jurisdictions() -> None:
    root = get_project_root()
    p = get_data_file_path("jurisdictions")
    assert p == root / "policy" / "jurisdictions.json"
