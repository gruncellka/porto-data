"""Porto Data CLI - Single source of truth for all validation logic."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("porto-data")
except PackageNotFoundError:
    __version__ = "0.0.1"  # fallback for development
