"""Validate command for porto CLI - thin wrapper around validators."""

from scripts.data_files import list_provider_ids
from scripts.validators.graph import validate_graph as _validate_provider_graph
from scripts.validators.limits_scope import validate_limits_scope
from scripts.validators.mappings_layout import validate_mappings_layout
from scripts.validators.schema import validate_all_schemas


def validate_limits() -> int:
    """Validate providers/*/limits.json (letter-send scope, frameworks, provider id)."""
    return validate_limits_scope()


def validate_schema() -> int:
    """Validate JSON schemas."""
    result: int = validate_all_schemas()
    return result


def validate_mappings() -> int:
    """Validate mappings.json vs provider files, registry, metadata, no stray JSON."""
    return validate_mappings_layout()


def validate_graph(analyze: bool = False, provider: str | None = None) -> int:
    """Validate provider graph for one provider or all providers in mappings."""
    if provider is not None:
        return _validate_provider_graph(analyze=analyze, provider=provider)
    exit_code = 0
    for pid in list_provider_ids():
        rc = _validate_provider_graph(analyze=analyze, provider=pid)
        if rc != 0:
            exit_code = rc
    return exit_code


def validate_all() -> int:
    """Validate data bundle: schema → mappings → limits → graph per provider."""
    schema_result = validate_schema()
    if schema_result != 0:
        return schema_result
    mappings_result = validate_mappings()
    if mappings_result != 0:
        return mappings_result
    limits_result = validate_limits()
    if limits_result != 0:
        return limits_result
    return validate_graph(analyze=False)
