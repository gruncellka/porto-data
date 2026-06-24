"""Tests for cli package version resolution."""

from __future__ import annotations

from pathlib import Path


class TestCliVersion:
    def test_dev_version_without_pyproject(self, monkeypatch) -> None:
        import cli.__init__ as cli_init

        class FakePath:
            def resolve(self) -> FakePath:
                return self

            @property
            def parents(self) -> list[FakePath]:
                return [self, self]

            def __truediv__(self, other: str) -> FakePath:
                return self

            def is_file(self) -> bool:
                return False

        monkeypatch.setattr(cli_init, "Path", lambda *_args, **_kwargs: FakePath())
        assert cli_init._dev_version() == "0.0.0-dev"

    def test_version_fallback_when_package_not_installed(
        self, monkeypatch, project_root: Path
    ) -> None:
        import importlib.util
        from importlib.metadata import PackageNotFoundError

        init_path = project_root / "cli" / "__init__.py"

        def _missing(_name: str) -> str:
            raise PackageNotFoundError()

        monkeypatch.setattr("importlib.metadata.version", _missing)
        spec = importlib.util.spec_from_file_location("cli_init_isolated", init_path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.__version__ == mod._dev_version()
