"""Data files configuration and utilities.

This module provides:
- File name constants loaded from mappings.json
- Functions to work with data files and mappings
- Validation of required entities at import time

Schema→data paths come from mappings.json. Provider ids come from global/providers.json;
mappings.providers keys must match that registry. Layout: global/ and providers/{id}/.
"""

import json
from pathlib import Path
from typing import Any

# Directory names for porto-data layout (mappings.json keys match these)
GLOBAL_DIR = "global"
PROVIDERS_DIR = "providers"

# Provider domain registry (same data layer as dimensions/features/restrictions)
PROVIDERS_REGISTRY_FILENAME = "providers.json"
PROVIDERS_REGISTRY_DATA_PATH = f"{GLOBAL_DIR}/{PROVIDERS_REGISTRY_FILENAME}"

# Default provider for backward compatibility (SDK loads this by default)
DEFAULT_PROVIDER = "deutschepost"


def _get_project_root() -> Path:
    """Determine project root by finding mappings.json.

    Tries multiple locations:
    1. porto_data package (installed package; data is inside porto_data)
    2. Relative to script location (development: repo root or porto_data subdir)
    3. Current working directory

    Returns:
        Path to the directory containing mappings.json (and global/, providers/)

    Raises:
        FileNotFoundError: If mappings.json cannot be found
    """
    # Try 1: porto_data package (installed wheel: data is inside the package)
    try:
        import porto_data

        root = Path(porto_data.__file__).parent
        if (root / "mappings.json").exists():
            return root
    except ImportError:
        pass

    # Try 2: Development mode — scripts' parent (repo root) or porto_data under it
    script_dir = Path(__file__).parent
    dev_root = script_dir.parent
    if (dev_root / "mappings.json").exists():
        return dev_root
    if (dev_root / "porto_data" / "mappings.json").exists():
        return dev_root / "porto_data"

    # Try 3: Current working directory (e.g. tests with tmp_path)
    cwd = Path.cwd()
    if (cwd / "mappings.json").exists():
        return cwd
    if (cwd / "porto_data" / "mappings.json").exists():
        return cwd / "porto_data"

    raise FileNotFoundError(
        "mappings.json not found. Tried:\n"
        "  1. porto_data package (installed)\n"
        f"  2. {dev_root} and {dev_root / 'porto_data'}\n"
        f"  3. {cwd} and {cwd / 'porto_data'}\n"
        "Run the CLI from the porto-data project root or install the package."
    )


def get_project_root() -> Path:
    """Return the project root (directory containing mappings.json)."""
    return _get_project_root()


def _load_mappings_raw(mappings_path: str | None = None) -> dict[str, Any]:
    """Load raw mappings from mappings.json (supports global + providers structure)."""
    if mappings_path is None:
        project_root = _get_project_root()
        mappings_file = project_root / "mappings.json"
    else:
        mappings_file = Path(mappings_path)

    try:
        with open(mappings_file, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {mappings_file}: {e}") from e

    mappings = data.get("mappings", {})
    if not mappings:
        raise ValueError(f"No mappings found in {mappings_file}")
    if not isinstance(mappings, dict):
        raise ValueError(
            f"mappings must be a dictionary, got {type(mappings).__name__}"
        )
    return mappings


def _expand_mappings_to_pairs(mappings: dict[str, Any]) -> list[tuple[str, str]]:
    """Expand global + providers structure to flat list of (schema_path, data_path) pairs."""
    pairs: list[tuple[str, str]] = []

    # Global mappings
    global_mappings = mappings.get(GLOBAL_DIR, {})
    if isinstance(global_mappings, dict):
        for schema_path, data_path in global_mappings.items():
            if isinstance(schema_path, str) and isinstance(data_path, str):
                pairs.append((schema_path, data_path))

    # Provider mappings (legacy flat format also supported)
    providers = mappings.get(PROVIDERS_DIR, {})
    if isinstance(providers, dict):
        for _provider_id, provider_mappings in providers.items():
            if isinstance(provider_mappings, dict):
                for schema_path, data_path in provider_mappings.items():
                    if isinstance(schema_path, str) and isinstance(data_path, str):
                        pairs.append((schema_path, data_path))

    # Legacy flat format: mappings is {schema: data} directly
    if not pairs and GLOBAL_DIR not in mappings and PROVIDERS_DIR not in mappings:
        for schema_path, data_path in mappings.items():
            if not isinstance(schema_path, str) or not isinstance(data_path, str):
                raise ValueError(
                    "All mapping keys and values must be strings, "
                    f"got {type(schema_path).__name__} -> {type(data_path).__name__}"
                )
            pairs.append((schema_path, data_path))

    return pairs


def load_mappings(mappings_path: str | None = None) -> dict[str, str]:
    """Load schema to data file mappings from mappings.json.

    For multi-provider structure, returns a flat dict with unique keys.
    Keys are schema paths; for provider entities, uses first provider (deutschepost).
    Use get_all_schema_data_pairs() for full iteration over all files.

    Returns:
        Dictionary mapping schema paths to data file paths.
    """
    mappings = _load_mappings_raw(mappings_path)
    pairs = _expand_mappings_to_pairs(mappings)

    # Build flat dict: for duplicate schema paths (e.g. products), keep first (deutschepost)
    result: dict[str, str] = {}
    for schema_path, data_path in pairs:
        if schema_path not in result:
            result[schema_path] = data_path
    return result


def get_all_schema_data_pairs(mappings_path: str | None = None) -> list[tuple[str, str]]:
    """Get all (schema_path, data_path) pairs for validation and metadata generation."""
    mappings = _load_mappings_raw(mappings_path)
    return _expand_mappings_to_pairs(mappings)


def get_schema_data_mappings(mappings_path: str | None = None) -> dict[str, str]:
    """Get the schema to data file mappings (alias for load_mappings)."""
    return load_mappings(mappings_path)


def get_all_data_file_names() -> dict[str, str]:
    """Get mapping of entity names to file names from mappings.json.

    Uses default provider for provider-scoped entities.
    Returns unique entity names; for provider entities uses base name (e.g. products).
    """
    pairs = get_all_schema_data_pairs()
    entity_to_filename: dict[str, str] = {}

    for schema_path, data_path in pairs:
        entity_name = Path(schema_path).stem.replace(".schema", "")
        filename = Path(data_path).name
        # For duplicates (e.g. products from multiple providers), keep first
        if entity_name not in entity_to_filename:
            entity_to_filename[entity_name] = filename

    return entity_to_filename


def get_data_file_name(
    entity_name: str,
    provider: str | None = None,
    *,
    project_root: Path | None = None,
) -> str:
    """Get data file name from mappings.json by entity name.

    Args:
        entity_name: Entity name (e.g., 'products', 'zones', 'graph', 'prices')
        provider: Optional provider ID for provider-scoped entities (default: deutschepost)
        project_root: Optional bundle root (directory containing mappings.json); default: auto-detect

    Returns:
        Data file name (e.g., "products.json", "graph.json")
    """
    return Path(
        get_data_file_path(entity_name, provider, project_root=project_root)
    ).name


def get_data_file_path(
    entity_name: str,
    provider: str | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    """Resolve a data file path from mappings.json (schema stem → relative data path).

    Args:
        entity_name: Entity name (e.g., 'products', 'zones', 'graph', 'limits')
        provider: Optional provider ID (default: deutschepost for provider-scoped entities)
        project_root: Optional bundle root (directory containing mappings.json); default: auto-detect

    Returns:
        Absolute path to the data file

    Raises:
        FileNotFoundError: If mappings or the requested entity mapping is missing
    """
    root = project_root if project_root is not None else _get_project_root()
    mappings_path = str(root / "mappings.json")
    pairs = get_all_schema_data_pairs(mappings_path)
    schema_key = f"schemas/{entity_name}.schema.json"
    effective_provider = provider if provider is not None else DEFAULT_PROVIDER

    # Global entities: dimensions, restrictions, features, providers (registry)
    global_entities = {
        "dimensions",
        "restrictions",
        "features",
        "providers",
        "jurisdictions",
    }
    if entity_name in global_entities:
        for schema_path, data_path in pairs:
            if schema_path == schema_key and data_path.startswith(f"{GLOBAL_DIR}/"):
                return root / data_path

    # Provider entities: use specified or default provider
    for schema_path, data_path in pairs:
        if schema_path == schema_key and data_path.startswith(f"{PROVIDERS_DIR}/{effective_provider}/"):
            return root / data_path

    raise FileNotFoundError(
        f"No mapping found for '{entity_name}'"
        + (f" (provider={effective_provider})" if effective_provider else "")
        + f". Available: {list({Path(s).stem.replace('.schema', '') for s, _ in pairs})}"
    )


def get_data_files() -> set[str]:
    """Get set of data file names from mappings.json (for dependency validation).

    Returns unique basenames for global/ and providers/* data files.
    ``providers.json`` (global provider registry) is excluded — it is not part of
    per-provider graph dependencies.
    """
    pairs = get_all_schema_data_pairs()
    names = {Path(data_path).name for _schema_path, data_path in pairs}
    names.discard(PROVIDERS_REGISTRY_FILENAME)
    return names


def get_global_data_paths() -> dict[str, str]:
    """Get global entity name -> data path mapping."""
    mappings = _load_mappings_raw()
    global_mappings = mappings.get(GLOBAL_DIR, {})
    if not isinstance(global_mappings, dict):
        return {}
    return {
        Path(schema_path).stem.replace(".schema", ""): data_path
        for schema_path, data_path in global_mappings.items()
    }


def get_provider_data_paths(provider: str) -> dict[str, str]:
    """Get provider entity name -> data path mapping for given provider."""
    mappings = _load_mappings_raw()
    providers = mappings.get(PROVIDERS_DIR, {})
    provider_mappings = providers.get(provider, {}) if isinstance(providers, dict) else {}
    if not isinstance(provider_mappings, dict):
        return {}
    return {
        Path(schema_path).stem.replace(".schema", ""): data_path
        for schema_path, data_path in provider_mappings.items()
    }


def load_providers_registry() -> dict[str, Any]:
    """Load providers.json (domain registry). Provider ids are object keys under 'providers'.

    Raises:
        FileNotFoundError: If providers.json is missing.
        ValueError: If structure is invalid.
    """
    root = _get_project_root()
    path = root / GLOBAL_DIR / PROVIDERS_REGISTRY_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Provider registry not found: {path}. "
            f"Add {PROVIDERS_REGISTRY_DATA_PATH} (see schemas/providers.schema.json)."
        )
    with open(path, encoding="utf-8") as f:
        data: Any = json.load(f)
    prov = data.get("providers")
    if not isinstance(prov, dict) or not prov:
        raise ValueError(
            f"{PROVIDERS_REGISTRY_DATA_PATH} must contain a non-empty object 'providers'"
        )
    return data


def list_provider_ids() -> list[str]:
    """Return sorted provider IDs from providers.json (authoritative registry)."""
    data = load_providers_registry()
    prov = data["providers"]
    assert isinstance(prov, dict)
    return sorted(prov.keys())


def get_mappings_provider_ids(mappings_path: str | None = None) -> set[str]:
    """Provider ids declared under mappings.providers (must match providers.json)."""
    mappings = _load_mappings_raw(mappings_path)
    prov = mappings.get(PROVIDERS_DIR, {})
    if not isinstance(prov, dict):
        return set()
    return set(prov.keys())


# ============================================================================
# File Name Constants - Loaded from mappings.json and validated at import
# ============================================================================

# Load file names from mappings.json (source of truth)
_FILE_NAMES = get_all_data_file_names()

# Minimum schema→data entity keys that must appear in mappings.json at import time.
# Covers graph resolution files, per-provider catalog surface, and shared globals
# (dimensions, restrictions, provider registry, jurisdictions). Basenames for
# provider-scoped rows come from the first matching mapping when names differ.
_REQUIRED_ENTITIES = [
    "dimensions",
    "jurisdictions",
    "providers",
    "restrictions",
    "features",
    "graph",
    "limits",
    "prices",
    "products",
    "services",
    "weight_tiers",
    "zones",
]

# Validate required entities exist - fail fast if mappings.json is incomplete
_missing = [e for e in _REQUIRED_ENTITIES if e not in _FILE_NAMES]
if _missing:
    raise ValueError(
        f"Missing required entities in mappings.json: {_missing}. "
        f"Available entities: {sorted(_FILE_NAMES.keys())}. "
        f"Please update mappings.json to include all required entities."
    )

# Export validated file name constants
GRAPH_FILE = _FILE_NAMES["graph"]
PRODUCTS_FILE = _FILE_NAMES["products"]
ZONES_FILE = _FILE_NAMES["zones"]
WEIGHT_TIERS_FILE = _FILE_NAMES["weight_tiers"]
SERVICES_FILE = _FILE_NAMES["services"]
PRICES_FILE = _FILE_NAMES["prices"]
DIMENSIONS_FILE = _FILE_NAMES["dimensions"]
FEATURES_FILE = _FILE_NAMES["features"]
RESTRICTIONS_FILE = _FILE_NAMES["restrictions"]
LIMITS_FILE = _FILE_NAMES["limits"]
