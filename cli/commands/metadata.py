"""Metadata command for porto CLI."""

import subprocess
import sys
from pathlib import Path

# Add scripts to path for imports
_scripts_path = Path(__file__).parent.parent.parent / "scripts"
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

from generate_metadata import main as generate_metadata_main
from utils import has_file_changes


def check_metadata_status() -> tuple[bool, bool]:
    """Check if metadata.json is modified and/or staged.

    Returns:
        tuple: (is_modified, is_staged)
    """
    check_modified = subprocess.run(
        ["git", "diff", "--name-only", "metadata.json"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        check=False,
    )
    metadata_modified = bool(check_modified.stdout.strip())

    check_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "metadata.json"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        check=False,
    )
    metadata_staged = bool(check_staged.stdout.strip())

    return metadata_modified, metadata_staged


def check_data_files_staged() -> bool:
    """Check if any data/schema files are staged."""
    check_staged_data = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", "data/", "schemas/"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
        check=False,
    )
    return bool(check_staged_data.stdout.strip())


def handle_metadata_generation() -> int:
    """Handle metadata generation after schema validation.

    This checks if metadata.json needs to be generated and handles
    git staging requirements for CI/CD.

    Returns:
        Exit code: 0 if successful, 1 if there are staging issues.
    """
    # Check if any data/schema files are staged
    data_files_staged = check_data_files_staged()

    # Check if metadata needs updating
    if has_file_changes():
        print("")
        print("Changes detected, generating metadata.json...")
        try:
            # Call metadata generator directly
            generate_metadata_main()
            metadata_modified, metadata_staged = check_metadata_status()

            # If data/schema files are staged and metadata needs updating but isn't staged, reject
            if data_files_staged and metadata_modified and not metadata_staged:
                print("")
                print("❌ ERROR: metadata.json was generated but is not staged!")
                print("")
                print("Data/schema files are staged, but metadata.json is not.")
                print("Please stage metadata.json in the same commit:")
                print("  git add metadata.json")
                print("  git commit")
                print("")
                return 1
            elif metadata_modified and metadata_staged:
                print("✓ metadata.json generated and staged")
            elif metadata_modified:
                print("✓ metadata.json generated (not needed for this commit)")
            else:
                print("✓ metadata.json up to date")
        except Exception as e:
            print(f"⚠ Warning: Could not generate metadata.json: {e}")
    else:
        # Even if no changes detected, check if metadata.json should be staged
        # (in case it was generated previously but not committed)
        if data_files_staged:
            metadata_modified, metadata_staged = check_metadata_status()

            if metadata_modified and not metadata_staged:
                print("")
                print("❌ ERROR: metadata.json is modified but not staged!")
                print("")
                print("Data/schema files are staged, but metadata.json is modified and not staged.")
                print("Please stage metadata.json in the same commit:")
                print("  git add metadata.json")
                print("  git commit")
                print("")
                return 1

        print("")
        print("✓ No changes detected, skipping metadata generation")

    return 0


def generate_metadata() -> int:
    """Generate metadata.json (standalone command).

    Returns:
        Exit code: 0 if successful, 1 otherwise.
    """
    try:
        generate_metadata_main()
        return 0
    except Exception as e:
        print(f"❌ ERROR: Failed to generate metadata.json: {e}")
        return 1
