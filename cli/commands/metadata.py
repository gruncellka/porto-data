"""Metadata command for porto CLI - thin wrapper around generate_metadata."""

from scripts.generate_metadata import main as generate_metadata_main


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
