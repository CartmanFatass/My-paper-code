"""Behavioral proof-sized checks for the CPM mechanical dispatcher."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / ".agents" / "skills" / "hmasd-agile-research-development" / "scripts" / "hmasd_cpm_mechanical.py"
TICKET_SCRIPT = REPOSITORY_ROOT / "scripts" / "hmasd_workspace_ticket.py"
REGISTERED_PYTHON = Path(r"C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe")


def _load_dispatcher():
    spec = importlib.util.spec_from_file_location("hmasd_cpm_mechanical_test_module", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(tmp_path: Path, task_class: str, task: dict, *, reads: list[str], writes: list[str]) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = tmp_path / "result.json"
    spec = {
        "schema_version": 1,
        "assignment_id": "CPM-MECHANICAL-TEST",
        "task_class": task_class,
        "attempt_id": "attempt-1",
        "working_directory": str(tmp_path),
        "allowed_read_paths": reads,
        "allowed_write_paths": writes,
        "result_path": str(result),
        "task": task,
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    completed = subprocess.run(
        [str(REGISTERED_PYTHON), str(SCRIPT), "run", "--spec", str(spec_path), "--result", str(result)],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.read_text(encoding="utf-8"))
    return completed, payload


def test_inspect_identity_has_single_terminal_result(tmp_path: Path) -> None:
    completed, payload = _run(tmp_path, "inspect_identity", {}, reads=[], writes=["result.json"])
    assert completed.returncode == 0
    assert completed.stdout.count("CPM_MECHANICAL_TASK_RESULT") == 1
    assert payload["status"] == "COMPLETE"
    assert payload["first_failure"] is None
    assert payload["assignment_id"] == "CPM-MECHANICAL-TEST"


def test_focused_checks_stop_at_first_failure_and_log(tmp_path: Path) -> None:
    checks = [
        {
            "argv": [str(REGISTERED_PYTHON), "-c", "print('ok')"],
            "timeout_sec": 5,
            "log_path": "logs/one.log",
        },
        {
            "argv": [str(REGISTERED_PYTHON), "-c", "raise SystemExit(7)"],
            "timeout_sec": 5,
            "log_path": "logs/two.log",
        },
        {
            "argv": [str(REGISTERED_PYTHON), "-c", "raise SystemExit(8)"],
            "timeout_sec": 5,
            "log_path": "logs/three.log",
        },
    ]
    completed, payload = _run(tmp_path, "run_focused_checks", {"checks": checks}, reads=[], writes=["result.json", "logs"])
    assert completed.returncode == 1
    assert payload["status"] == "ERROR"
    assert payload["first_failure"]["code"] == "CHECK_FAILED"
    assert (tmp_path / "logs/one.log").is_file()
    assert (tmp_path / "logs/two.log").is_file()
    assert not (tmp_path / "logs/three.log").exists()
    assert payload["retry_class"] == "CHECK"


def test_focused_check_timeout_preserves_byte_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output=b"stdout-\xff", stderr=b"stderr")

    monkeypatch.setattr(dispatcher.subprocess, "run", timeout)
    spec = {
        "task": {
            "checks": [
                {
                    "argv": [str(REGISTERED_PYTHON), "-c", "print('unused')"],
                    "timeout_sec": 0.01,
                    "log_path": "logs/timeout.log",
                }
            ]
        }
    }
    with pytest.raises(dispatcher.MechanicalError) as caught:
        dispatcher._task_run_focused_checks(spec, tmp_path, [], ["logs"])

    assert caught.value.code == "CHECK_TIMEOUT"
    assert caught.value.retry_class == "TIMEOUT"
    assert (tmp_path / "logs/timeout.log").read_text(encoding="utf-8") == "stdout-�stderr"


def test_verify_result_exact_identity_and_numeric_extraction(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps({"assignment_id": "CPM-MECHANICAL-TEST", "score": 3.5}), encoding="utf-8")
    completed, payload = _run(
        tmp_path,
        "verify_result",
        {
            "required_artifacts": ["artifact.json"],
            "required_json_fields": {"artifact.json": ["assignment_id", "score"]},
            "exact_equals": [{"artifact": "artifact.json", "field": "assignment_id", "expected": "CPM-MECHANICAL-TEST"}],
            "numeric_constraints": [{"artifact": "artifact.json", "field": "score", "minimum": 3, "maximum": 4, "name": "score"}],
            "extractions": [{"artifact": "artifact.json", "field": "score", "name": "score_copy"}],
        },
        reads=["artifact.json"],
        writes=["result.json"],
    )
    assert completed.returncode == 0
    assert payload["status"] == "COMPLETE"
    assert payload["observations"]["extractions"]["score"] == 3.5
    assert payload["observations"]["extractions"]["score_copy"] == 3.5


def test_render_state_rejects_canonical_owner_file(tmp_path: Path) -> None:
    completed, payload = _run(
        tmp_path,
        "render_state",
        {"proposed_files": [{"path": "docs/state.md", "content": "x"}]},
        reads=[],
        writes=["result.json", "docs"],
    )
    assert completed.returncode == 1
    assert payload["first_failure"]["code"] == "OWNER_FILE_NOT_TEMPORARY"


def test_ticket_prepare_rejects_finalize_command(tmp_path: Path) -> None:
    completed, payload = _run(
        tmp_path,
        "ticket_prepare",
        {
            "argv": [str(REGISTERED_PYTHON), str(TICKET_SCRIPT), "retire", "--ticket", "ticket.json"],
            "timeout_sec": 5,
        },
        reads=["ticket.json"],
        writes=["result.json"],
    )
    assert completed.returncode == 1
    assert payload["first_failure"]["code"] == "INVOCATION_NOT_ALLOWED"
    assert payload["retry_class"] == "INVOCATION"


def test_ticket_prepare_requires_complete_file_bound_argv(tmp_path: Path) -> None:
    completed, payload = _run(
        tmp_path,
        "ticket_prepare",
        {"timeout_sec": 5},
        reads=[],
        writes=["result.json"],
    )
    assert completed.returncode == 1
    assert payload["first_failure"]["code"] == "INVALID_SPEC"


def test_ticket_prepare_timeout_preserves_byte_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dispatcher = _load_dispatcher()
    ticket = tmp_path / "ticket.json"
    ticket.write_text("{}", encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    log = tmp_path / "logs" / "ticket-timeout.log"
    argv = [
        str(REGISTERED_PYTHON),
        str(dispatcher.TICKET_SCRIPT),
        "prepare-integrate",
        "--ticket",
        str(ticket),
        "--assignment-id",
        "CPM-MECHANICAL-TEST",
        "--target-repo",
        str(tmp_path),
        "--receipt",
        str(receipt),
    ]

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"], output=b"prepare-\xff", stderr=b"stderr")

    monkeypatch.setattr(dispatcher.subprocess, "run", timeout)
    spec = {
        "assignment_id": "CPM-MECHANICAL-TEST",
        "task": {"argv": argv, "timeout_sec": 0.01, "log_path": str(log)},
    }
    with pytest.raises(dispatcher.MechanicalError) as caught:
        dispatcher._task_ticket_prepare(spec, tmp_path, ["ticket.json"], ["receipt.json", "logs"])

    assert caught.value.code == "CHECK_TIMEOUT"
    assert caught.value.retry_class == "TIMEOUT"
    assert log.read_text(encoding="utf-8") == "prepare-�stderr"
