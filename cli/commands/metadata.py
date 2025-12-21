"""Metadata command for porto CLI - thin wrapper around generate_metadata."""

import sys
from pathlib import Path

# Add scripts to path for imports
_scripts_path = Path(__file__).parent.parent.parent / "scripts"
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

from generate_metadata import main as generate_metadata_main


def generate_metadata() -> int:
    """Generate metadata.json.

    Returns:
        Exit code: 0 if successful, 1 otherwise.
    """
    try:
        generate_metadata_main()
        return 0
    except Exception as e:
        print(f"❌ ERROR: Failed to generate metadata.json: {e}")
        return 1
