from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import hmasd_operator_result


def operator_result() -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": "run-1",
        "manifest_path": "temp/directions/example/exp/run-1/manifest.json",
        "stdout_path": "temp/directions/example/exp/run-1/stdout.log",
        "stderr_path": "temp/directions/example/exp/run-1/stderr.log",
        "terminal_status": "SUCCEEDED",
        "exit_code": 0,
        "observed_at": "2026-08-28T00:00:00Z",
    }


def test_validator_accepts_path_only_terminal_observation() -> None:
    document = operator_result()
    assert hmasd_operator_result.validate_document(document) == document
    rendered = json.dumps(document).lower()
    assert "sha256" not in rendered
    assert "assignment" not in rendered
    assert "operator_identity" not in rendered

    invalid = copy.deepcopy(document)
    invalid["message_id"] = "legacy"
    with pytest.raises(hmasd_operator_result.ValidationError):
        hmasd_operator_result.validate_document(invalid)


def test_public_cli_validates_the_same_document(tmp_path: Path) -> None:
    path = tmp_path / "operator-result.json"
    path.write_text(json.dumps(operator_result()), encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "scripts/hmasd_operator_result.py", "validate", "--path", str(path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == operator_result()
