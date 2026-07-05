"""Validate command for porto CLI - thin wrapper around validators."""

from scripts.data_files import list_provider_ids
from scripts.validators.delivery import validate_delivery
from scripts.validators.graph import validate_graph as _validate_provider_graph
from scripts.validators.limits_scope import validate_limits_scope
from scripts.validators.mappings_layout import validate_mappings_layout
from scripts.validators.markets import validate_markets
from scripts.validators.porto_ids import validate_porto_ids as _validate_porto_ids_impl
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


def validate_porto_ids() -> int:
    """Validate porto_id enums and native-id cross-file references."""
    return _validate_porto_ids_impl()


def validate_markets_cmd() -> int:
    """Validate policy/markets.json against provider countries and fiscal shape."""
    return validate_markets()


def validate_delivery_cmd() -> int:
    """Validate zone-scoped delivery SLAs on providers/*/products.json."""
    return validate_delivery()


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
    """Validate data bundle: schema → mappings → markets → limits → porto_ids → delivery → graph."""
    schema_result = validate_schema()
    if schema_result != 0:
        return schema_result
    mappings_result = validate_mappings()
    if mappings_result != 0:
        return mappings_result
    markets_result = validate_markets_cmd()
    if markets_result != 0:
        return markets_result
    limits_result = validate_limits()
    if limits_result != 0:
        return limits_result
    porto_ids_result = validate_porto_ids()
    if porto_ids_result != 0:
        return porto_ids_result
    delivery_result = validate_delivery_cmd()
    if delivery_result != 0:
        return delivery_result
    return validate_graph(analyze=False)
