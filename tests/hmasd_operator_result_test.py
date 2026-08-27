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
        "schema_version": 2,
        "assignment_message_id": "msg-assignment-1",
        "run_id": "run-1",
        "operator_identity": "Operator-run-1",
        "manifest_ref": {
            "path": "temp/directions/example/exp/run-1/manifest.json",
            "sha256": "a" * 64,
        },
        "stdout_ref": {
            "path": "temp/directions/example/exp/run-1/stdout.log",
            "sha256": "b" * 64,
        },
        "stderr_ref": {
            "path": "temp/directions/example/exp/run-1/stderr.log",
            "sha256": "c" * 64,
        },
        "terminal_status": "SUCCEEDED",
        "exit_code": 0,
    }


def test_validator_accepts_only_the_narrow_operator_terminal_result() -> None:
    document = operator_result()
    assert hmasd_operator_result.validate_document(document) == document

    for obsolete_field in (
        "role",
        "logical_identity",
        "generation",
        "assignment_id",
        "status",
        "materiality",
        "summary",
        "changed_paths",
        "state_refs",
        "artifact_refs",
        "checkpoint_sha",
        "decision_requests",
        "next_action",
        "payload",
        "recovery",
    ):
        invalid = copy.deepcopy(document)
        invalid[obsolete_field] = None
        with pytest.raises(hmasd_operator_result.ValidationError):
            hmasd_operator_result.validate_document(invalid)


def test_public_cli_validates_the_same_narrow_document(tmp_path: Path) -> None:
    path = tmp_path / "operator-result.json"
    path.write_text(json.dumps(operator_result()), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/hmasd_operator_result.py",
            "validate",
            "--path",
            str(path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == operator_result()

    invalid = operator_result()
    invalid["next_action"] = {"kind": "NONE"}
    path.write_text(json.dumps(invalid), encoding="utf-8")
    refused = subprocess.run(
        [
            sys.executable,
            "scripts/hmasd_operator_result.py",
            "validate",
            "--path",
            str(path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 2
    assert "extra=['next_action']" in refused.stderr
