"""Focused contracts for the Root-owned Codex runtime task cache."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from scripts import hmasd_state


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "hmasd_state.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _document(project_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "revision": 1,
        "updated_at": "2026-08-25T00:00:00.1234567Z",
        "writer": "Root",
        "tasks": [
            {
                "logical_identity": "Root",
                "kind": "root",
                "generation": 1,
                "task_title": "HMASD Root",
                "thread_id": "thread-root",
                "host_id": "local",
                "last_cursor": "cursor-1",
                "project_root": str(project_root),
                "worktree_ref": None,
                "checkpoint_sha": None,
                "lifecycle": "ACTIVE",
                "last_seen_at": "2026-08-25T00:00:00.1234567Z",
            }
        ],
    }


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def test_runtime_tasks_initialize_and_replace_allow_rebuildable_rows(tmp_path: Path) -> None:
    target = tmp_path / ".codex" / "runtime" / "tasks.json"
    source = tmp_path / "initial.json"
    state = _document(tmp_path)
    _write(source, state)

    initialized = _run(
        "initialize",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--input",
        str(source),
    )
    assert initialized.returncode == 0, initialized.stderr

    replacement = copy.deepcopy(state)
    replacement["revision"] = 2
    replacement["updated_at"] = "2026-08-25T00:01:00Z"
    replacement["tasks"][0].update(
        {
            "thread_id": "thread-root-restarted",
            "lifecycle": "IDLE",
            "last_seen_at": "2026-08-25T00:01:00Z",
        }
    )
    replacement["tasks"].append(
        {
            "logical_identity": "Implementer-example",
            "kind": "implementer",
            "generation": 1,
            "task_title": "Candidate implementation",
            "lifecycle": "RUNNING",
        }
    )
    replacement_path = tmp_path / "replacement.json"
    _write(replacement_path, replacement)
    replaced = _run(
        "replace",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--expected-revision",
        "1",
        "--input",
        str(replacement_path),
    )
    assert replaced.returncode == 0, replaced.stderr
    assert json.loads(target.read_text(encoding="utf-8"))["revision"] == 2


def test_runtime_tasks_accept_json_like_cursor_and_opaque_refs_on_initialize_replace(
    tmp_path: Path,
) -> None:
    target = tmp_path / ".codex" / "runtime" / "tasks.json"
    source = tmp_path / "opaque-initial.json"
    state = _document(tmp_path)
    state["tasks"][0].update(
        {
            "thread_id": '{"thread":"01abc","labels":["root","cursor"]}',
            "host_id": '{"host":"local","slot":1}',
            "last_cursor": '{"after":"abc","items":["x,y",{"quoted":"yes"}]}',
            "worktree_ref": "worktree/{root-task},slot=1",
        }
    )
    _write(source, state)

    initialized = _run(
        "initialize",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--input",
        str(source),
    )
    assert initialized.returncode == 0, initialized.stderr

    replacement = copy.deepcopy(state)
    replacement["revision"] = 2
    replacement["updated_at"] = "2026-08-25T00:02:00Z"
    replacement["tasks"][0]["last_cursor"] = (
        '{"after":"def","nested":{"quote":"a,b"},"page":2}'
    )
    replacement_path = tmp_path / "opaque-replacement.json"
    _write(replacement_path, replacement)
    replaced = _run(
        "replace",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--expected-revision",
        "1",
        "--input",
        str(replacement_path),
    )
    assert replaced.returncode == 0, replaced.stderr
    observed = json.loads(target.read_text(encoding="utf-8"))
    assert observed["tasks"][0]["last_cursor"] == replacement["tasks"][0]["last_cursor"]


def test_runtime_tasks_reject_identity_takeover_duplicate_writer_and_path(tmp_path: Path) -> None:
    target = tmp_path / ".codex" / "runtime" / "tasks.json"
    source = tmp_path / "initial.json"
    state = _document(tmp_path)
    _write(source, state)
    assert _run(
        "initialize",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--input",
        str(source),
    ).returncode == 0

    takeover = copy.deepcopy(state)
    takeover["revision"] = 2
    takeover["tasks"][0]["kind"] = "portfolio"
    takeover_path = tmp_path / "takeover.json"
    _write(takeover_path, takeover)
    result = _run(
        "replace",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--expected-revision",
        "1",
        "--input",
        str(takeover_path),
    )
    assert result.returncode == 6

    duplicate = copy.deepcopy(state)
    duplicate["tasks"].append(copy.deepcopy(duplicate["tasks"][0]))
    with pytest.raises(hmasd_state.ValidationError):
        hmasd_state.validate_document("runtime_tasks", duplicate)

    wrong_writer = copy.deepcopy(state)
    wrong_writer["writer"] = "Portfolio"
    wrong_writer_path = tmp_path / "wrong-checkout" / ".codex" / "runtime" / "tasks.json"
    _write(wrong_writer_path, wrong_writer)
    result = _run("validate", "--kind", "runtime_tasks", "--path", str(wrong_writer_path))
    assert result.returncode == 5

    result = _run("validate", "--kind", "runtime_tasks", "--path", str(tmp_path / "tasks.json"))
    assert result.returncode == 5


def test_runtime_tasks_stale_revision_preserves_canonical_bytes(tmp_path: Path) -> None:
    target = tmp_path / ".codex" / "runtime" / "tasks.json"
    source = tmp_path / "initial.json"
    state = _document(tmp_path)
    _write(source, state)
    assert _run(
        "initialize",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--input",
        str(source),
    ).returncode == 0
    before = target.read_bytes()
    replacement = copy.deepcopy(state)
    replacement["revision"] = 2
    replacement["updated_at"] = "2026-08-25T00:01:00Z"
    replacement_path = tmp_path / "replacement.json"
    _write(replacement_path, replacement)
    result = _run(
        "replace",
        "--kind",
        "runtime_tasks",
        "--path",
        str(target),
        "--writer",
        "Root",
        "--expected-revision",
        "9",
        "--input",
        str(replacement_path),
    )
    assert result.returncode == 4
    assert target.read_bytes() == before
