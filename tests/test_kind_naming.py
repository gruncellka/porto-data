"""Tests for service/feature kind naming policy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validators.kind_naming import (
    _THREE_WORD_KINDS,
    _TWO_WORD_KINDS,
    kind_word_count,
    validate_kind_enum,
    validate_kind_token,
)

_SCHEMA = Path(__file__).parent.parent / "porto_data/schemas/kinds.schema.json"


def _load_enum(key: str) -> list[str]:
    doc = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    return list(doc["definitions"][key]["enum"])


class TestKindNamingPolicy:
    def test_shipped_service_and_feature_enums_pass_policy(self) -> None:
        service = _load_enum("service_kind")
        feature = _load_enum("feature_kind")
        errors = validate_kind_enum(service_kinds=service, feature_kinds=feature)
        assert errors == []

    def test_one_word_kinds_are_single_token(self) -> None:
        one_word = {"registered", "tracking", "insurance", "thickness"}
        for kind in one_word:
            assert kind_word_count(kind) == 1
            assert validate_kind_token(kind) == []

    def test_two_word_kinds_are_documented(self) -> None:
        for kind in _TWO_WORD_KINDS:
            assert kind_word_count(kind) == 2
            assert validate_kind_token(kind) == []

    def test_three_word_kinds_are_documented(self) -> None:
        for kind in _THREE_WORD_KINDS:
            assert kind_word_count(kind) == 3
            assert validate_kind_token(kind) == []

    @pytest.mark.parametrize(
        "bad",
        [
            "registered_rr",
            "reg_return_receipt",
            "proof_of_mailing_of",
            "acceptance_proof_of",
            "four_word_kind_name",
            "trk",
            "return_receipt_extra_word",
        ],
    )
    def test_rejects_abbreviations_and_overlong_kinds(self, bad: str) -> None:
        assert validate_kind_token(bad)

    def test_registered_rr_is_ambiguous_abbreviation(self) -> None:
        errors = validate_kind_token("registered_rr")
        assert any("rr" in e for e in errors)

    def test_acceptance_proof_is_documented_two_word(self) -> None:
        assert validate_kind_token("acceptance_proof") == []
        assert validate_kind_token("delivery_proof") == []

    def test_rejects_empty_or_non_string_kind(self) -> None:
        assert validate_kind_token("") == ["kind: kind must be a non-empty string"]
        assert validate_kind_token("Bad-Kind")  # not empty; fails snake_case / shape

    def test_rejects_invalid_snake_case(self) -> None:
        errors = validate_kind_token("BadKind")
        assert any("snake_case" in e for e in errors)

    def test_three_word_connector_shape_without_registry(self) -> None:
        assert validate_kind_token("registered_return_receipt") == []
        assert validate_kind_token("foo_of_bar") == []  # connector middle word
        errors = validate_kind_token("foo_bar_baz")
        assert any("_THREE_WORD_KINDS" in e for e in errors)

    def test_validate_kind_enum_registry_drift(self) -> None:
        errors = validate_kind_enum(service_kinds=["registered"], feature_kinds=[])
        assert any("_TWO_WORD_KINDS" in e for e in errors)
        assert any("_THREE_WORD_KINDS" in e for e in errors)

    def test_two_word_kind_requires_full_word_segments(self) -> None:
        errors = validate_kind_enum(service_kinds=["ab_cd"], feature_kinds=[])
        assert any("full-word segments" in e for e in errors)
