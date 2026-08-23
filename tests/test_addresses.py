"""Branch coverage for scripts.validators.addresses."""

from __future__ import annotations

import json
from unittest.mock import patch

import scripts.validators.addresses as addresses
from scripts.validators.addresses import validate_addresses


def _write_bundle(
    tmp_path,
    *,
    addresses_doc: object | None = None,
    layouts_doc: object | None = None,
    jurisdictions_doc: object | None = None,
) -> None:
    (tmp_path / "formats").mkdir(exist_ok=True)
    (tmp_path / "policy").mkdir(exist_ok=True)
    if addresses_doc is None:
        addresses_doc = {
            "jurisdictions": {
                "DE": {
                    "standard": "DIN678",
                    "forms": [{"kind": "street", "required": ["name"]}],
                }
            }
        }
    if layouts_doc is None:
        layouts_doc = {
            "jurisdictions": {
                "DE": {
                    "envelopes": {"DL": {"standard": "DIN678"}},
                }
            }
        }
    if jurisdictions_doc is None:
        jurisdictions_doc = {
            "jurisdictions": {
                "DE": {"timezone": "Europe/Berlin"},
                "EU": {"members": ["DE", "FR", 1]},
            }
        }
    (tmp_path / "formats" / "addresses.json").write_text(
        json.dumps(addresses_doc), encoding="utf-8"
    )
    (tmp_path / "formats" / "layouts.json").write_text(json.dumps(layouts_doc), encoding="utf-8")
    (tmp_path / "policy" / "jurisdictions.json").write_text(
        json.dumps(jurisdictions_doc), encoding="utf-8"
    )


def _run(tmp_path) -> int:
    with patch.object(addresses, "_get_project_root", return_value=tmp_path):
        return validate_addresses()


def test_live_bundle_ok() -> None:
    assert validate_addresses() == 0


def test_load_non_object_root(tmp_path, capsys) -> None:
    (tmp_path / "formats").mkdir()
    (tmp_path / "formats" / "addresses.json").write_text("[]", encoding="utf-8")
    (tmp_path / "formats" / "layouts.json").write_text("{}", encoding="utf-8")
    (tmp_path / "policy").mkdir()
    (tmp_path / "policy" / "jurisdictions.json").write_text("{}", encoding="utf-8")
    assert _run(tmp_path) == 1
    assert "expected object root" in capsys.readouterr().out


def test_load_missing_file(tmp_path, capsys) -> None:
    assert _run(tmp_path) == 1
    assert "failed to load inputs" in capsys.readouterr().out


def test_jurisdictions_must_be_non_empty(tmp_path, capsys) -> None:
    _write_bundle(tmp_path, addresses_doc={"jurisdictions": {}})
    assert _run(tmp_path) == 1
    assert "must be a non-empty object" in capsys.readouterr().out


def test_known_codes_skip_non_dict_jurisdictions_root(tmp_path, capsys) -> None:
    _write_bundle(
        tmp_path,
        jurisdictions_doc={"jurisdictions": []},
        addresses_doc={
            "jurisdictions": {
                "XX": {
                    "standard": "DIN678",
                    "forms": [{"kind": "street", "required": ["name"]}],
                }
            }
        },
        layouts_doc={"jurisdictions": {}},
    )
    assert _run(tmp_path) == 0
    assert "OK" in capsys.readouterr().out


def test_layout_standard_none_when_no_jurisdictions(tmp_path) -> None:
    _write_bundle(tmp_path, layouts_doc={"file_type": "layouts"})
    assert _run(tmp_path) == 0


def test_layout_standard_none_when_row_or_envelopes_invalid(tmp_path) -> None:
    _write_bundle(
        tmp_path,
        layouts_doc={"jurisdictions": {"DE": {"envelopes": {}}}},
    )
    assert _run(tmp_path) == 0
    _write_bundle(tmp_path, layouts_doc={"jurisdictions": {"DE": "nope"}})
    assert _run(tmp_path) == 0
    _write_bundle(
        tmp_path,
        layouts_doc={"jurisdictions": {"DE": {"envelopes": {"DL": {}}}}},
    )
    assert _run(tmp_path) == 0


def test_ambiguous_layout_standards(tmp_path, capsys) -> None:
    _write_bundle(
        tmp_path,
        layouts_doc={
            "jurisdictions": {
                "DE": {
                    "envelopes": {
                        "DL": {"standard": "DIN678"},
                        "C5": {"standard": "OTHER"},
                    }
                }
            }
        },
    )
    assert _run(tmp_path) == 1
    assert "conflicting standards" in capsys.readouterr().out


def test_standard_mismatch(tmp_path, capsys) -> None:
    _write_bundle(
        tmp_path,
        addresses_doc={
            "jurisdictions": {
                "DE": {
                    "standard": "WRONG",
                    "forms": [{"kind": "street", "required": ["name"]}],
                }
            }
        },
    )
    assert _run(tmp_path) == 1
    assert "must match layouts standard" in capsys.readouterr().out


def test_forms_errors(tmp_path, capsys) -> None:
    _write_bundle(
        tmp_path,
        addresses_doc={"jurisdictions": {"DE": {"standard": "DIN678"}}},
    )
    assert _run(tmp_path) == 1
    assert "forms must be a non-empty array" in capsys.readouterr().out

    _write_bundle(
        tmp_path,
        addresses_doc={
            "jurisdictions": {
                "DE": {"standard": "DIN678", "forms": ["nope"]},
            }
        },
    )
    assert _run(tmp_path) == 1
    assert "must be an object" in capsys.readouterr().out

    _write_bundle(
        tmp_path,
        addresses_doc={
            "jurisdictions": {
                "DE": {
                    "standard": "DIN678",
                    "forms": [{"kind": "parcel", "required": ["name"]}],
                }
            }
        },
    )
    assert _run(tmp_path) == 1
    assert "kind must be one of" in capsys.readouterr().out

    _write_bundle(
        tmp_path,
        addresses_doc={
            "jurisdictions": {
                "DE": {
                    "standard": "DIN678",
                    "forms": [
                        {"kind": "street", "required": ["name"]},
                        {"kind": "street", "required": ["city"]},
                    ],
                }
            }
        },
    )
    assert _run(tmp_path) == 1
    assert "duplicate form kind" in capsys.readouterr().out

    _write_bundle(
        tmp_path,
        addresses_doc={
            "jurisdictions": {
                "DE": {
                    "standard": "DIN678",
                    "forms": [{"kind": "street", "required": []}],
                }
            }
        },
    )
    assert _run(tmp_path) == 1
    assert "required must be a non-empty array" in capsys.readouterr().out


def test_invalid_key_unknown_jurisdiction_and_form_shape(tmp_path, capsys) -> None:
    _write_bundle(
        tmp_path,
        addresses_doc={
            "jurisdictions": {
                "deu": {"standard": "DIN678", "forms": [{"kind": "street", "required": ["n"]}]},
                "XX": "not-an-object",
                "ZZ": {"forms": [{"kind": "street", "required": ["n"]}]},
                "YY": {
                    "standard": "DIN678",
                    "forms": [{"kind": "street", "required": ["n"]}],
                },
            }
        },
        layouts_doc={"jurisdictions": {}},
    )
    assert _run(tmp_path) == 1
    out = capsys.readouterr().out
    assert "alpha-2 uppercase" in out
    assert "unknown jurisdiction" in out
    assert "form must be an object" in out
    assert "standard is required" in out
    assert "error(s)" in out
