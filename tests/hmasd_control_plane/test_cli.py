from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

import pytest

from tools.hmasd_control_plane import cli


def test_incident_text_render_includes_bare_index_records(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    incident = {
        "incident_id": "incident-1",
        "component": "semantic",
        "exact_object": "workflow/task",
        "observed_fact": "mechanical fact only",
    }
    monkeypatch.setattr(
        "tools.hmasd_control_plane.diagnostics.collect_incidents",
        lambda *args, **kwargs: ([incident], 1),
    )

    assert (
        cli.main(
            [
                "incidents",
                "--repo-root",
                str(tmp_path),
                "--format",
                "text",
                "--component",
                "semantic",
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "incident-1" in output
    assert "mechanical fact only" in output
    assert not output.lstrip().startswith("[")


def test_output_snapshot_is_restricted_to_repo_runtime(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "tools.hmasd_control_plane.diagnostics.collect_doctor",
        lambda *args, **kwargs: (
            {
                "schema": "HMASD_CONTROL_PLANE_DOCTOR_V1",
                "generated_at": "2026-08-20T00:00:00Z",
                "status": "OK",
                "sources": {},
                "counters": {},
                "findings": [],
            },
            0,
        ),
    )
    output = tmp_path / "runtime/snapshots/doctor.json"
    assert (
        cli.main(
            [
                "doctor",
                "--repo-root",
                str(tmp_path),
                "--component",
                "semantic",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "OK"
    assert (
        cli.main(
            [
                "doctor",
                "--repo-root",
                str(tmp_path),
                "--component",
                "semantic",
                "--output",
                str(tmp_path / "outside.json"),
            ]
        )
        == 2
    )


def test_long_effect_run_and_observe_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    spec = {
        "schema": "HMASD_LONG_EFFECT_V1",
        "experiment_id": str(uuid.uuid4()),
        "component": "harmless-cli-test",
        "working_directory": str(tmp_path.resolve()),
        "argv": [sys.executable, "-c", "print('ok')"],
        "input_refs": [],
        "output_refs": [],
        "metadata": {"direction_id": None, "stage": None, "effect_id": None},
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    run_root = tmp_path / "run"

    assert cli.main(["long-effect", "run", "--spec", str(spec_path), "--run-root", str(run_root)]) == 0
    terminal = json.loads(capsys.readouterr().out)
    assert terminal["phase"] == "CHILD_EXITED"
    assert terminal["exit_code"] == 0

    assert cli.main(["long-effect", "observe", "--run-root", str(run_root)]) == 0
    observed = json.loads(capsys.readouterr().out)
    assert observed["owner_without_terminal"] is False
    assert observed["experiment"]["component"] == "harmless-cli-test"
    assert "ok" not in json.dumps(observed)
