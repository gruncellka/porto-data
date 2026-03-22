"""Jurisdiction reference data (EU/UN lists) and generator invariants."""

import json

import pytest
from jsonschema import Draft7Validator

from scripts.data_files import get_data_file_path, get_project_root
from scripts.generate_countries_reference import build_countries_document


def test_build_countries_document_invariants() -> None:
    doc = build_countries_document()
    assert doc["file_type"] == "jurisdictions"
    unit = doc["unit"]
    assert unit["country_code"] == "ISO 3166-1 alpha-2"
    assert unit.get("region_code") == "ISO 3166-2"
    assert unit.get("date") == "ISO 8601"
    g = doc["jurisdictions"]
    assert isinstance(g, dict)
    eu = set(g["eu"])
    un = set(g["un"])
    assert len(un) == 193
    assert len(eu) == 27
    assert eu <= un


def test_global_jurisdictions_json_matches_schema() -> None:
    root = get_project_root()
    data_path = root / "global" / "jurisdictions.json"
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
    assert p == root / "global" / "jurisdictions.json"


def test_main_writes_payload(tmp_path, capsys) -> None:
    from scripts.generate_countries_reference import main

    out = tmp_path / "jurisdictions.json"
    main(out)
    assert out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["file_type"] == "jurisdictions"
    assert len(data["jurisdictions"]["un"]) == 193
    assert "Wrote" in capsys.readouterr().out
