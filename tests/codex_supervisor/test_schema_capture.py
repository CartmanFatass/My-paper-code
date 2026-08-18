from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import write_fake_codex
from tools.codex_supervisor.schema_capture import SchemaCaptureError, capture_app_server_schema


def test_schema_capture_writes_external_manifest(tmp_path: Path, repo_root: Path) -> None:
    binary = write_fake_codex(tmp_path)
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()
    output = tmp_path / "external-schema"
    capture = capture_app_server_schema(binary, output, repo_root=fake_repo)
    assert capture.version.startswith("codex-fake")
    assert capture.manifest_path.is_file()
    assert (capture.output_root / "app-server.json").is_file()
    assert "initialize" in capture.observed_methods
    assert "thread/start" in capture.observed_methods
    try:
        capture.output_root.resolve().relative_to(fake_repo.resolve())
    except ValueError:
        escaped = True
    else:
        escaped = False
    assert escaped
    try:
        capture.output_root.resolve().relative_to(repo_root.resolve())
    except ValueError:
        pass
    del repo_root


def test_schema_capture_rejects_repo_output(tmp_path: Path, repo_root: Path) -> None:
    binary = write_fake_codex(tmp_path)
    with pytest.raises(SchemaCaptureError, match="inside the repository"):
        capture_app_server_schema(binary, repo_root / "docs", repo_root=repo_root)
