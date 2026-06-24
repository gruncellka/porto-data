"""Validate provider ``graph.json`` against catalog files.

Implementation is split under this package: ``validator`` (orchestrator),
``runner`` (CLI entry + printing), ``edges``, ``layouts``, ``services``,
``execution_semantics``, ``marks_profiles``, ``provider_rules``, ``dependencies``,
``units``, ``envelope_geometry``, ``constants``.
"""

from .constants import (
    EXPECTED_CURRENCY,
    EXPECTED_DIMENSION_UNIT,
    EXPECTED_PRICE_UNIT,
    EXPECTED_WEIGHT_UNIT,
    PRICE_KEY_PRODUCTS,
    PRICE_KEY_SERVICES,
    PROVIDER_RULE_METRIC_THICKNESS,
    RULE_KIND_BAND,
)
from .envelope_geometry import envelope_validation_views
from .runner import (
    _print_analyze_mode,
    _print_validate_mode,
    validate_graph,
)
from .validator import GraphValidator

# Tests import ``_envelope_validation_views`` from this module
_envelope_validation_views = envelope_validation_views

__all__ = [
    "EXPECTED_CURRENCY",
    "EXPECTED_DIMENSION_UNIT",
    "EXPECTED_PRICE_UNIT",
    "PRICE_KEY_PRODUCTS",
    "PRICE_KEY_SERVICES",
    "EXPECTED_WEIGHT_UNIT",
    "RULE_KIND_BAND",
    "PROVIDER_RULE_METRIC_THICKNESS",
    "GraphValidator",
    "_envelope_validation_views",
    "_print_analyze_mode",
    "_print_validate_mode",
    "validate_graph",
]
