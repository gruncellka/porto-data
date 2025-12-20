"""Base validator and types for porto-data validation."""

from typing import TypedDict


class ValidationResults(TypedDict):
    """Type definition for validation results."""

    errors: list[str]
    warnings: list[str]
    fixes_needed: list[str]
    correct: list[str]
