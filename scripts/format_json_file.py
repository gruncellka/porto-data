#!/usr/bin/env python3
"""Format a single JSON file (same output as make format-json).

Usage:
  python format_json_file.py <file_path>       # format in place
  python format_json_file.py --check <file>    # return 0 if already formatted, 1 otherwise

This ensures Cmd+S and make format-json produce identical output.
"""

import json
import sys
from pathlib import Path


def format_json(content: str) -> str:
    """Format JSON with indent=2 (project standard; ``python -m json.tool`` uses 4)."""
    data = json.loads(content)
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    args = sys.argv[1:]
    check_only = False
    if args and args[0] == "--check":
        check_only = True
        args = args[1:]
    if len(args) != 1:
        print("Usage: format_json_file.py [--check] <file_path>", file=sys.stderr)
        return 1
    path = Path(args[0])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1
    try:
        content = path.read_text(encoding="utf-8")
        formatted = format_json(content)
        if check_only:
            return 0 if content == formatted else 1
        path.write_text(formatted, encoding="utf-8")
        return 0
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
