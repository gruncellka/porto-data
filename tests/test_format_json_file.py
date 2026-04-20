"""Tests for scripts/format_json_file.py (CLI used by make format-json)."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.format_json_file import format_json, main

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestFormatJson:
    def test_pretty_prints_and_trailing_newline(self) -> None:
        out = format_json('{"b": 2, "a": 1}')
        assert json.loads(out) == {"a": 1, "b": 2}
        assert out.endswith("\n")
        assert "\n  " in out

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            format_json("not json {")


class TestFormatJsonMain:
    def test_usage_missing_file_arg(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch.object(sys, "argv", ["format_json_file.py"]):
            assert main() == 1
        assert "Usage" in capsys.readouterr().err

    def test_usage_too_many_args(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch.object(sys, "argv", ["format_json_file.py", "a", "b"]):
            assert main() == 1
        assert "Usage" in capsys.readouterr().err

    def test_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch.object(sys, "argv", ["format_json_file.py", "/nonexistent/porto-data.json"]):
            assert main() == 1
        assert "not found" in capsys.readouterr().err.lower()

    def test_formats_in_place(self, tmp_path: Path) -> None:
        path = tmp_path / "doc.json"
        path.write_text('{"x":1,"y":2}', encoding="utf-8")
        with patch.object(sys, "argv", ["format_json_file.py", str(path)]):
            assert main() == 0
        assert json.loads(path.read_text(encoding="utf-8")) == {"x": 1, "y": 2}

    def test_check_passes_when_already_formatted(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.json"
        path.write_text(format_json('{"z": true}'), encoding="utf-8")
        with patch.object(sys, "argv", ["format_json_file.py", "--check", str(path)]):
            assert main() == 0

    def test_check_fails_when_minified(self, tmp_path: Path) -> None:
        path = tmp_path / "raw.json"
        path.write_text('{"z":true}', encoding="utf-8")
        with patch.object(sys, "argv", ["format_json_file.py", "--check", str(path)]):
            assert main() == 1

    def test_invalid_json_in_file(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{", encoding="utf-8")
        with patch.object(sys, "argv", ["format_json_file.py", str(path)]):
            assert main() == 1
        assert "Invalid JSON" in capsys.readouterr().err


def test_script_invoked_as___main__(tmp_path: Path) -> None:
    """Covers ``if __name__ == '__main__'`` path via subprocess."""
    script = REPO_ROOT / "scripts" / "format_json_file.py"
    path = tmp_path / "m.json"
    path.write_text('{"k":0}', encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(script), str(path)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {"k": 0}
