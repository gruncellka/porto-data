"""Kind token naming policy — one word default; multi-word only when necessary."""

from __future__ import annotations

import re
from collections.abc import Iterable

# Same rule family as product names (PortoMark): prefer one word; add words only when needed.
MAX_KIND_WORDS = 3
_CONNECTOR_WORDS = frozenset({"of", "with", "and"})

# Abbreviation segments are forbidden (e.g. registered_rr → ambiguous).
_FORBIDDEN_SEGMENTS = frozenset(
    {
        "rr",
        "id",
        "num",
        "no",
        "svc",
        "feat",
        "reg",
        "trk",
        "sig",
        "rec",
        "del",
        "mail",
        "pkg",
    }
)

_KIND_TOKEN_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z][a-z0-9]*)*$")

# Three-word kinds shipped today — each needs a distinct meaning not expressible in one word.
_THREE_WORD_KINDS: dict[str, str] = {
    "registered_return_receipt": (
        "registered service that includes return receipt (not plain registered or return_receipt alone)"
    ),
}

# Two-word kinds — necessary disambiguation (one word alone would collide or mislead).
_TWO_WORD_KINDS: dict[str, str] = {
    "acceptance_proof": (
        "provider-issued document at acceptance into carrier custody (proof alone is ambiguous)"
    ),
    "delivery_proof": (
        "provider-issued document that delivery occurred (proof alone is ambiguous)"
    ),
    "return_receipt": "receipt returned to sender (receipt alone is ambiguous)",
    "recipient_signature": "signature of recipient (signature alone could mean sender)",
}


def kind_word_count(kind: str) -> int:
    return len(kind.split("_"))


def kind_segments(kind: str) -> list[str]:
    return kind.split("_")


def validate_kind_token(kind: str, *, context: str = "kind") -> list[str]:
    """Return policy violations for a single kind token."""
    errors: list[str] = []
    if not kind or not isinstance(kind, str):
        return [f"{context}: kind must be a non-empty string"]

    if not _KIND_TOKEN_RE.match(kind):
        errors.append(
            f"{context}: kind {kind!r} must be lowercase snake_case ASCII "
            "(one word or joined full words; no abbreviations)"
        )
        return errors

    segments = kind_segments(kind)
    count = len(segments)

    if count > MAX_KIND_WORDS:
        errors.append(
            f"{context}: kind {kind!r} has {count} words; max {MAX_KIND_WORDS} "
            "(prefer one word; add words only when necessary)"
        )

    for seg in segments:
        if seg in _FORBIDDEN_SEGMENTS:
            errors.append(
                f"{context}: kind {kind!r} uses forbidden abbreviation segment {seg!r} "
                "(use full words — e.g. not registered_rr)"
            )

    if count == 3:
        if kind in _THREE_WORD_KINDS:
            return errors
        if segments[1] in _CONNECTOR_WORDS:
            return errors
        errors.append(
            f"{context}: kind {kind!r} is three content words; "
            "add to kind_naming._THREE_WORD_KINDS with rationale or shorten to one/two words"
        )

    return errors


def validate_kind_enum(*, service_kinds: Iterable[str], feature_kinds: Iterable[str]) -> list[str]:
    """Validate all canonical enum values and multi-word necessity registry."""
    errors: list[str] = []
    all_kinds = set(service_kinds) | set(feature_kinds)

    for kind in sorted(all_kinds):
        ctx = "service_kind" if kind in service_kinds else "feature_kind"
        if kind in service_kinds and kind in feature_kinds:
            ctx = "service_kind/feature_kind"
        errors.extend(validate_kind_token(kind, context=ctx))

    for kind, _reason in _THREE_WORD_KINDS.items():
        if kind not in all_kinds:
            errors.append(
                f"kind_naming: _THREE_WORD_KINDS lists {kind!r} but it is not in kinds.schema.json"
            )

    for kind, _reason in _TWO_WORD_KINDS.items():
        if kind not in all_kinds:
            errors.append(
                f"kind_naming: _TWO_WORD_KINDS lists {kind!r} but it is not in kinds.schema.json"
            )

    for kind in all_kinds:
        wc = kind_word_count(kind)
        if wc == 2 and kind not in _TWO_WORD_KINDS and kind not in _THREE_WORD_KINDS:
            # New two-word kinds are allowed when segments are full words; document in _TWO_WORD_KINDS.
            segs = kind_segments(kind)
            if any(len(s) < 3 for s in segs):
                errors.append(
                    f"kind {kind!r}: two-word kind must use full-word segments (min 3 letters each)"
                )

    return errors
