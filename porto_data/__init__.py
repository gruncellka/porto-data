"""Porto data package: Deutsche Post shipping data, schemas, and metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["__version__", "metadata", "get_package_root"]

# Package root (directory containing metadata.json, data/, schemas/)
_PACKAGE_DIR = Path(__file__).resolve().parent

# Load metadata once at import (same as npm default export)
with open(_PACKAGE_DIR / "metadata.json", encoding="utf-8") as f:
    metadata: dict[str, Any] = json.load(f)

# Version: from metadata when installed, else from loaded metadata.json (dev)
try:
    from importlib.metadata import version as _pkg_version

    __version__: str = _pkg_version("gruncellka-porto-data")
except Exception:  # PackageNotFoundError when run from repo without install
    __version__ = str(metadata["project"]["version"])


def get_package_root() -> Path:
    """Return the package root (directory containing data/, schemas/, metadata.json)."""
    return _PACKAGE_DIR
