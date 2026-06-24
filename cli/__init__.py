"""Porto Data CLI - Single source of truth for all validation logic."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

_DIST_NAME = "gruncellka-porto-data"


def _dev_version() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject.is_file():
        import tomllib

        with open(pyproject, "rb") as f:
            return str(tomllib.load(f).get("project", {}).get("version", "0.0.0-dev"))
    return "0.0.0-dev"


try:
    __version__ = version(_DIST_NAME)
except PackageNotFoundError:
    __version__ = _dev_version()
