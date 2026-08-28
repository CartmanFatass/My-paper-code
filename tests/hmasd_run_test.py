from __future__ import annotations

import copy
import hashlib
import json
import multiprocessing
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts import hmasd_operator_result, hmasd_run


SAFE_SNAPSHOT = {
    "schema_version": 1,
    "cpu": {"physical_cores": 4, "logical_processors": 8, "load_percent": 0.0},
    "memory": {
        "total_bytes": 32 * 1024**3,
        "available_bytes": 24 * 1024**3,
        "cgroup_memory_max_bytes": None,
        "cgroup_memory_current_bytes": None,
        "cgroup_memory_max_raw": "max",
    },
}


def _json_digest(value: object) -> str:
    rendered = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _review_subject(
    *,
    direction_id: str,
    run_id: str,
    assignment_id: str,
    command: list[str],
    code_sha: str,
    parameters: dict[str, object],
    estimate: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "direction_id": direction_id,
        "run_id": run_id,
        "assignment_id": assignment_id,
        "argv": command,
        "code_sha": code_sha,
        "parameters": parameters,
        "estimate": estimate,
    }


def _observed_review(
    *,
    direction_id: str,
    run_id: str,
    assignment_id: str,
    command: list[str],
    code_sha: str,
    parameters: dict[str, object],
    estimate: dict[str, object],
) -> dict[str, object]:
    subject = _review_subject(
        direction_id=direction_id,
        run_id=run_id,
        assignment_id=assignment_id,
        command=command,
        code_sha=code_sha,
        parameters=parameters,
        estimate=estimate,
    )
    return {
        "schema_version": 1,
        "reviewer": "hmasd-reviewer",
        "assignment_id": assignment_id,
        "attempt_id": f"performance-{run_id}",
        "observed_at": "2026-08-24T00:00:00Z",
        "status": "COMPLETED",
        "subject_sha256": _json_digest(subject),
        "summary": "Observed performance review attempt.",
    }


def _prepare(
    monkeypatch,
    tmp_path: Path,
    *command: str,
    wall_seconds: int = 1,
    peak_memory_gib: float = 0.01,
    direction_id: str = "direction",
    run_id: str = "run",
    code_sha: str = "a" * 40,
    observed_head: str | None = None,
    output_root: Path | None = None,
    review_evidence: dict[str, object] | bool = True,
    expected_code: int | None = None,
    snapshot: dict[str, object] | None = None,
) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        hmasd_run, "capture_snapshot", lambda: snapshot or SAFE_SNAPSHOT
    )
    monkeypatch.setattr(hmasd_run, "_require_omp_branch", lambda _cwd: "omp/test")
    monkeypatch.setattr(hmasd_run, "_git_head", lambda _cwd: observed_head or code_sha)
    assignment_id = "assignment"
    parameters: dict[str, object] = {"seed": 7}
    estimate: dict[str, object] = {
        "wall_seconds": wall_seconds,
        "peak_memory_gib": peak_memory_gib,
        "basis": "fixture",
        "workers": 1,
        "threads_per_worker": 1,
    }
    command_parts = list(command)
    output_root = output_root or (
        tmp_path / "temp" / "directions" / direction_id / "exp" / run_id
    )
    arguments = [
        "prepare",
        "--direction",
        direction_id,
        "--run-id",
        run_id,
        "--assignment",
        assignment_id,
        "--code-sha",
        code_sha,
        "--parameters",
        json.dumps(parameters),
        "--estimate",
        json.dumps(estimate),
        "--output-root",
        str(output_root),
    ]
    if wall_seconds > 7200 and review_evidence is not False:
        evidence = (
            _observed_review(
                direction_id=direction_id,
                run_id=run_id,
                assignment_id=assignment_id,
                command=command_parts,
                code_sha=code_sha,
                parameters=parameters,
                estimate=estimate,
            )
            if review_evidence is True
            else review_evidence
        )
        review_path = tmp_path / f"{run_id}-review-attempt.json"
        review_path.write_text(json.dumps(evidence), encoding="utf-8")
        arguments.extend(["--review-evidence", str(review_path)])
    arguments.extend(["--", *command_parts])
    expected = expected_code if expected_code is not None else (8 if wall_seconds > 7200 else 0)
    assert hmasd_run.main(arguments) == expected
    return output_root / "manifest.json"


def test_prepare_unsafe_memory_leaves_reserved_root_absent(
    monkeypatch, tmp_path: Path
) -> None:
    unsafe_snapshot = {
        **SAFE_SNAPSHOT,
        "memory": {
            **SAFE_SNAPSHOT["memory"],
            "available_bytes": 6 * 1024**3,
        },
    }

    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "raise AssertionError('must not launch')",
        peak_memory_gib=1.0,
        snapshot=unsafe_snapshot,
        expected_code=6,
    )

    assert not manifest_path.parent.exists()


def test_prepare_reclaims_only_exact_legacy_unsafe_partial_root(
    monkeypatch, tmp_path: Path
) -> None:
    root = tmp_path / "temp" / "directions" / "direction" / "exp" / "run"
    root.mkdir(parents=True)
    for name in ("artifacts", "checkpoints", "metrics"):
        (root / name).mkdir()
    (root / "preflight.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "direction_id": "direction",
                "run_id": "run",
                "memory_safe": False,
            }
        ),
        encoding="utf-8",
    )

    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "print('prepared only')",
        output_root=root,
    )

    assert manifest_path.is_file()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "PREPARED"


def test_prepare_does_not_reclaim_partial_root_with_any_extra_file(
    monkeypatch, tmp_path: Path
) -> None:
    root = tmp_path / "temp" / "directions" / "direction" / "exp" / "run"
    root.mkdir(parents=True)
    for name in ("artifacts", "checkpoints", "metrics"):
        (root / name).mkdir()
    (root / "preflight.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "direction_id": "direction",
                "run_id": "run",
                "memory_safe": False,
            }
        ),
        encoding="utf-8",
    )
    sentinel = root / "stdout.log"
    sentinel.write_text("must remain", encoding="utf-8")

    _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "raise AssertionError('must not launch')",
        output_root=root,
        expected_code=6,
    )

    assert sentinel.read_text(encoding="utf-8") == "must remain"
def _execute_process(manifest_path: str, results) -> None:
    results.put(hmasd_run.main(["execute", "--manifest", manifest_path]))


@pytest.mark.skipif(os.name != "nt", reason="native Windows compatibility contract")
@pytest.mark.parametrize(
    "command",
    [
        ("python3", "-c", "pass"),
        ("python3.11", "-c", "pass"),
        ("/home/fires/HMASD/scripts/train.py",),
        (sys.executable, "/mnt/c/Projects/HMASD/config.json"),
    ],
)
def test_prepare_refuses_omp_linux_command_paths_on_native_windows(
    monkeypatch, tmp_path: Path, command: tuple[str, ...]
) -> None:
    _prepare(monkeypatch, tmp_path, *command, expected_code=2)


@pytest.mark.skipif(os.name != "nt", reason="native Windows compatibility contract")
def test_manifest_with_wsl_cwd_is_refused_before_file_open(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "direction_id": "direction",
                "run_id": "run",
                "cwd": "/home/fires/HMASD",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(hmasd_run.RunRefusal, match="WSL/POSIX"):
        hmasd_run._manifest_direction_root(
            manifest_path, json.loads(manifest_path.read_text(encoding="utf-8"))
        )




def test_short_real_subprocess_records_complete_manifest_and_output(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "import sys; print('stdout sentinel'); print('stderr sentinel', file=sys.stderr)",
    )

    assert hmasd_run.main(["execute", "--manifest", str(manifest_path)]) == 0

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "SUCCEEDED"
    assert manifest["process"]["exit_code"] == 0
    assert manifest["process"]["pid"] is not None
    assert manifest["process"]["process_group_id"] is not None
    assert manifest["process"]["linux_boot_id"]
    assert manifest["process"]["proc_start_ticks"] is not None
    assert manifest["process"]["identity_persisted_at"] is not None
    assert manifest["process"]["group_quiescent"] is True
    assert hmasd_run._group_pids(manifest["process"]["process_group_id"]) == []
    assert "stdout sentinel" in (manifest_path.parent / "stdout.log").read_text(encoding="utf-8")
    assert "stderr sentinel" in (manifest_path.parent / "stderr.log").read_text(encoding="utf-8")
    assert not (manifest_path.parent / "operator-result.json").exists()


def test_execute_can_emit_one_schema_valid_operator_result(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "import sys; print('stdout sentinel'); print('stderr sentinel', file=sys.stderr)",
    )

    assert hmasd_run.main(
        ["execute", "--manifest", str(manifest_path), "--emit-operator-result"]
    ) == 0

    result_path = manifest_path.parent / "operator-result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    hmasd_operator_result.validate_document(result)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result == {
        "schema_version": 1,
        "run_id": "run",
        "manifest_path": "temp/directions/direction/exp/run/manifest.json",
        "stdout_path": "temp/directions/direction/exp/run/stdout.log",
        "stderr_path": "temp/directions/direction/exp/run/stderr.log",
        "terminal_status": "SUCCEEDED",
        "exit_code": 0,
        "observed_at": manifest["updated_at"],
    }
    assert "work_id" not in result


def test_manifest_replacement_preserves_immutable_run_identity(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "--version")
    current = json.loads(manifest_path.read_text(encoding="utf-8"))
    replacement = copy.deepcopy(current)
    replacement["revision"] += 1
    replacement["updated_at"] = hmasd_run._utc_now()
    replacement["cwd"] = str(tmp_path / "different-cwd")
    with pytest.raises(hmasd_run.RunRefusal, match="immutable"):
        hmasd_run._replace_manifest(manifest_path, replacement, current["revision"])


def test_terminal_manifest_status_cannot_return_to_running(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "--version")
    assert hmasd_run.main(["execute", "--manifest", str(manifest_path)]) == 0
    current = json.loads(manifest_path.read_text(encoding="utf-8"))
    replacement = copy.deepcopy(current)
    replacement["revision"] += 1
    replacement["updated_at"] = hmasd_run._utc_now()
    replacement["status"] = "RUNNING"
    with pytest.raises(hmasd_run.RunRefusal, match="illegal run status transition"):
        hmasd_run._replace_manifest(manifest_path, replacement, current["revision"])


def test_emit_operator_result_refuses_preexisting_path_before_launch(
    monkeypatch, tmp_path: Path
) -> None:
    executed = tmp_path / "executed.txt"
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        f"from pathlib import Path; Path({str(executed)!r}).write_text('ran')",
    )
    result_path = manifest_path.parent / "operator-result.json"
    result_path.write_text("preserve", encoding="utf-8")

    assert hmasd_run.main(
        ["execute", "--manifest", str(manifest_path), "--emit-operator-result"]
    ) == 6
    assert result_path.read_text(encoding="utf-8") == "preserve"
    assert not executed.exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "PREPARED"


def test_emit_operator_result_rejects_alias_risk_before_launch(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "-c", "pass")
    result_path = manifest_path.parent / "operator-result.json"
    original = hmasd_run.hmasd_platform.is_reparse_or_symlink
    monkeypatch.setattr(
        hmasd_run.hmasd_platform,
        "is_reparse_or_symlink",
        lambda path, info=None: Path(path) == result_path or original(Path(path), info),
    )

    assert hmasd_run.main(
        ["execute", "--manifest", str(manifest_path), "--emit-operator-result"]
    ) == 6
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "PREPARED"


def test_emit_operator_result_refuses_preexisting_symlink_before_launch(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "-c", "pass")
    target = tmp_path / "alias-target.json"
    target.write_text("preserve", encoding="utf-8")
    result_path = manifest_path.parent / "operator-result.json"
    try:
        result_path.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"host cannot create test symlink: {exc}")

    assert hmasd_run.main(
        ["execute", "--manifest", str(manifest_path), "--emit-operator-result"]
    ) == 6
    assert target.read_text(encoding="utf-8") == "preserve"
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "PREPARED"


def test_failed_run_does_not_emit_or_retry_operator_result(
    monkeypatch, tmp_path: Path
) -> None:
    count_path = tmp_path / "count.txt"
    command = (
        "from pathlib import Path; "
        f"p=Path({str(count_path)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x'); "
        "raise SystemExit(7)"
    )
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "-c", command)
    execute_argv = [
        "execute",
        "--manifest",
        str(manifest_path),
        "--emit-operator-result",
    ]

    assert hmasd_run.main(execute_argv) == 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"
    assert manifest["process"]["exit_code"] == 7
    assert count_path.read_text(encoding="utf-8") == "x"
    assert not (manifest_path.parent / "operator-result.json").exists()
    assert hmasd_run.main(execute_argv) == 6
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
    assert count_path.read_text(encoding="utf-8") == "x"
    assert not (manifest_path.parent / "operator-result.json").exists()


@pytest.mark.skipif(os.name != "nt", reason="native Windows gate observation contract")
def test_unknown_run_does_not_emit_or_retry_operator_result(
    monkeypatch, tmp_path: Path
) -> None:
    count_path = tmp_path / "unknown-count.txt"
    command = (
        "import subprocess, sys, time; from pathlib import Path; "
        f"p=Path({str(count_path)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x'); "
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
        "time.sleep(0.25)"
    )
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "-c", command)
    execute_argv = [
        "execute",
        "--manifest",
        str(manifest_path),
        "--emit-operator-result",
    ]
    terminate_owned_group = hmasd_run._terminate_owned_group

    def cleanup_then_observation_fault(manifest, descendant_identities):
        terminate_owned_group(manifest, descendant_identities)
        raise hmasd_run.RunRefusal(1, "injected terminal observation fault")

    monkeypatch.setattr(
        hmasd_run, "_terminate_owned_group", cleanup_then_observation_fault
    )
    assert hmasd_run.main(execute_argv) == 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "UNKNOWN"
    assert count_path.read_text(encoding="utf-8") == "x"
    assert hmasd_run._group_pids(manifest["process"]["process_group_id"]) == []
    assert not (manifest_path.parent / "operator-result.json").exists()
    assert hmasd_run.main(execute_argv) == 6
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
    assert count_path.read_text(encoding="utf-8") == "x"
    assert not (manifest_path.parent / "operator-result.json").exists()


def test_operator_result_publish_fault_preserves_success_without_retry(
    monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    count_path = tmp_path / "count.txt"
    command = (
        "from pathlib import Path; "
        f"p=Path({str(count_path)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x')"
    )
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "-c", command)
    execute_argv = [
        "execute",
        "--manifest",
        str(manifest_path),
        "--emit-operator-result",
    ]

    def fail_publish(*_args, **_kwargs):
        stdout_path = manifest_path.parent / "stdout.log"
        moved = manifest_path.parent / "stdout.closed"
        stdout_path.rename(moved)
        moved.rename(stdout_path)
        raise hmasd_operator_result.PublicationError("injected publish fault")

    monkeypatch.setattr(hmasd_run.hmasd_operator_result, "publish_document", fail_publish)
    assert hmasd_run.main(execute_argv) == 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "SUCCEEDED"
    assert manifest["process"]["exit_code"] == 0
    assert manifest["process"]["group_quiescent"] is True
    assert count_path.read_text(encoding="utf-8") == "x"
    assert not (manifest_path.parent / "operator-result.json").exists()
    assert hmasd_run.main(execute_argv) == 6
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
    assert count_path.read_text(encoding="utf-8") == "x"
    assert not (manifest_path.parent / "operator-result.json").exists()
    assert "OPERATOR_RESULT_PUBLISH_FAILED" in capsys.readouterr().err


def test_success_waits_for_and_proves_process_group_quiescence(
    monkeypatch, tmp_path: Path
) -> None:
    command = (
        "import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
        "time.sleep(0.25)"
    )
    manifest_path = _prepare(monkeypatch, tmp_path, sys.executable, "-c", command)

    assert hmasd_run.main(["execute", "--manifest", str(manifest_path)]) == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "SUCCEEDED"
    assert manifest["process"]["group_quiescent"] is True
    assert hmasd_run._group_pids(manifest["process"]["process_group_id"]) == []


def test_child_exit_code_is_stored_separately_from_wrapper_refusal_codes(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "import sys; print('child output'); raise SystemExit(6)",
    )

    assert hmasd_run.main(["execute", "--manifest", str(manifest_path)]) == 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"
    assert manifest["process"]["exit_code"] == 6
    assert "worker_wrapper_error" not in (manifest_path.parent / "stderr.log").read_text(
        encoding="utf-8"
    )


def test_long_request_freezes_review_evidence_and_approved_resume_is_once(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "print('approved once')",
        wall_seconds=7201,
    )
    request_path = manifest_path.parent / "decision-request.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    assert request["review_attempt"]["attempted"] is True
    assert hmasd_run.main(["execute", "--manifest", str(manifest_path)]) == 8

    approval = {
        "schema_version": 1,
        "request_sha256": request["request_sha256"],
        "direction_id": request["direction_id"],
        "run_id": request["run_id"],
        "argv": request["argv"],
        "code_sha": request["code_sha"],
        "parameters": request["parameters"],
        "estimates": request["estimates"],
        "evidence_sha256": request["evidence_sha256"],
        "approved": True,
    }
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(json.dumps(approval), encoding="utf-8")

    assert hmasd_run.main(
        ["execute", "--manifest", str(manifest_path), "--approval", str(approval_path)]
    ) == 0
    assert hmasd_run.main(
        ["execute", "--manifest", str(manifest_path), "--approval", str(approval_path)]
    ) == 6
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "SUCCEEDED"


def test_changed_frozen_request_requires_new_decision(monkeypatch, tmp_path: Path) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "print('must not launch')",
        wall_seconds=7201,
    )
    request_path = manifest_path.parent / "decision-request.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    approval = {
        "schema_version": 1,
        "request_sha256": request["request_sha256"],
        "direction_id": request["direction_id"],
        "run_id": request["run_id"],
        "argv": ["changed"],
        "code_sha": request["code_sha"],
        "parameters": request["parameters"],
        "estimates": request["estimates"],
        "evidence_sha256": request["evidence_sha256"],
        "approved": True,
    }
    approval_path = tmp_path / "changed-approval.json"
    approval_path.write_text(json.dumps(approval), encoding="utf-8")

    assert hmasd_run.main(
        ["execute", "--manifest", str(manifest_path), "--approval", str(approval_path)]
    ) == 4
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "PREPARED"


def test_long_request_requires_observed_sha_bound_reviewer_evidence(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "raise AssertionError('must not launch')",
        wall_seconds=7201,
        review_evidence=False,
        expected_code=4,
    )

    assert not (manifest_path.parent / "decision-request.json").exists()


def test_fake_or_wrongly_bound_reviewer_evidence_is_refused(
    monkeypatch, tmp_path: Path
) -> None:
    fake = {
        "schema_version": 1,
        "reviewer": "hmasd-reviewer",
        "assignment_id": "assignment",
        "attempt_id": "fabricated",
        "observed_at": "2026-08-24T00:00:00Z",
        "status": "UNAVAILABLE",
        "subject_sha256": "0" * 64,
        "summary": "Not bound to the requested run.",
    }
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "raise AssertionError('must not launch')",
        wall_seconds=7201,
        review_evidence=fake,
        expected_code=4,
    )

    assert not (manifest_path.parent / "decision-request.json").exists()


def test_prepare_refuses_code_sha_that_is_not_cwd_head(monkeypatch, tmp_path: Path) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "pass",
        observed_head="b" * 40,
        expected_code=5,
    )

    assert not manifest_path.exists()


def test_prepare_refuses_output_root_not_owned_by_direction_and_run(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = _prepare(
        monkeypatch,
        tmp_path,
        sys.executable,
        "-c",
        "pass",
        output_root=tmp_path / "unowned-run",
        expected_code=5,
    )

    assert not manifest_path.exists()


def test_direction_digest_claim_blocks_duplicate_launch_across_run_roots(
    monkeypatch, tmp_path: Path
) -> None:
    command = [sys.executable, "-c", "import time; time.sleep(1.0)"]
    first = _prepare(monkeypatch, tmp_path, *command, run_id="run-one")
    second = _prepare(monkeypatch, tmp_path, *command, run_id="run-two")
    context = multiprocessing.get_context("spawn" if os.name == "nt" else "fork")
    results = context.Queue()
    process = context.Process(target=_execute_process, args=(str(first), results))
    process.start()
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        observed = json.loads(first.read_text(encoding="utf-8"))
        if observed["status"] == "RUNNING" and observed["process"]["pid"] is not None:
            break
        time.sleep(0.01)
    else:
        process.terminate()
        process.join(timeout=5)
        raise AssertionError("first run never persisted its process identity")

    assert hmasd_run.main(["execute", "--manifest", str(second)]) == 6
    assert json.loads(second.read_text(encoding="utf-8"))["status"] == "PREPARED"
    process.join(timeout=10)
    assert not process.is_alive()
    assert results.get(timeout=1) == 0


def test_unknown_direction_claim_is_never_relaunched(monkeypatch, tmp_path: Path) -> None:
    command = [sys.executable, "-c", "print('first')"]
    first = _prepare(monkeypatch, tmp_path, *command, run_id="run-one")
    second = _prepare(monkeypatch, tmp_path, *command, run_id="run-two")
    assert hmasd_run.main(["execute", "--manifest", str(first)]) == 0
    first_manifest = json.loads(first.read_text(encoding="utf-8"))
    claim_path = (
        tmp_path
        / "temp"
        / "directions"
        / "direction"
        / ".run-claims"
        / f"{first_manifest['claim_sha256']}.json"
    )
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    claim["status"] = "UNKNOWN"
    claim_path.write_text(json.dumps(claim), encoding="utf-8")

    assert hmasd_run.main(["execute", "--manifest", str(second)]) == 6
    assert json.loads(second.read_text(encoding="utf-8"))["status"] == "PREPARED"


def test_target_command_starts_only_after_process_identity_is_persisted(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = (
        tmp_path / "temp" / "directions" / "direction" / "exp" / "run" / "manifest.json"
    )
    check = (
        "import json, os, pathlib; "
        f"m=json.loads(pathlib.Path({str(manifest_path)!r}).read_text()); "
        "assert m['status']=='RUNNING'; "
        "assert m['process']['pid']==os.getpid(); "
        "assert m['process']['identity_persisted_at']"
    )
    prepared = _prepare(monkeypatch, tmp_path, sys.executable, "-c", check)

    assert hmasd_run.main(["execute", "--manifest", str(prepared)]) == 0


def test_exec_gate_eof_prevents_popen_to_persistence_orphan(tmp_path: Path) -> None:
    marker = tmp_path / "target-started"
    if os.name == "nt":
        gate = tmp_path / "unreleased.gate"
        gate.touch()
        child = subprocess.Popen(
            [
                sys.executable,
                str(Path(hmasd_run.__file__).resolve()),
                "_exec-gate",
                "--gate-path",
                str(gate),
                "--",
                sys.executable,
                "-c",
                f"from pathlib import Path; Path({str(marker)!r}).touch()",
            ]
        )
        gate.unlink()
        assert child.wait(timeout=5) != 0
        assert not marker.exists()
        return
    read_fd, write_fd = os.pipe()
    child = subprocess.Popen(
        [
            sys.executable,
            str(Path(hmasd_run.__file__).resolve()),
            "_exec-gate",
            "--gate-fd",
            str(read_fd),
            "--",
            sys.executable,
            "-c",
            f"from pathlib import Path; Path({str(marker)!r}).touch()",
        ],
        pass_fds=(read_fd,),
    )
    os.close(read_fd)
    os.close(write_fd)

    assert child.wait(timeout=5) != 0
    assert not marker.exists()


def test_reused_pid_identity_is_not_treated_as_an_owned_group(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "status": "RUNNING",
        "command_sha256": "a" * 64,
        "process": {
            "pid": 4242,
            "process_group_id": 4242,
            "linux_boot_id": "boot-a",
            "proc_start_ticks": 100,
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    killed: list[tuple[int, int]] = []
    monkeypatch.setattr(hmasd_run, "_read_boot_id", lambda: "boot-a")
    monkeypatch.setattr(hmasd_run, "_proc_start_ticks", lambda _pid: 200)
    monkeypatch.setattr(hmasd_run, "_group_pids", lambda _pgid: [4242])
    if os.name == "nt":
        monkeypatch.setattr(
            hmasd_run,
            "_terminate_windows_pid",
            lambda pid: killed.append((pid, 0)),
        )
    else:
        monkeypatch.setattr(os, "killpg", lambda pgid, signum: killed.append((pgid, signum)))

    assert hmasd_run.main(["cancel", "--manifest", str(manifest_path)]) == 6
    assert killed == []
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "RUNNING"


def test_absent_leader_with_untied_reused_pgid_is_never_signalled(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "status": "RUNNING",
        "command_sha256": "a" * 64,
        "process": {
            "pid": 4242,
            "process_group_id": 4242,
            "linux_boot_id": "boot-a",
            "proc_start_ticks": 100,
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    killed: list[tuple[int, int]] = []
    monkeypatch.setattr(hmasd_run, "_read_boot_id", lambda: "boot-a")
    monkeypatch.setattr(
        hmasd_run,
        "_proc_start_ticks",
        lambda pid: None if pid == 4242 else 900,
    )
    monkeypatch.setattr(hmasd_run, "_group_pids", lambda _pgid: [5000])
    if os.name == "nt":
        monkeypatch.setattr(
            hmasd_run,
            "_terminate_windows_pid",
            lambda pid: killed.append((pid, 0)),
        )
    else:
        monkeypatch.setattr(os, "killpg", lambda pgid, signum: killed.append((pgid, signum)))

    assert hmasd_run.main(["cancel", "--manifest", str(manifest_path)]) == 6
    assert killed == []
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["status"] == "RUNNING"


def _write_promotable_pair(monkeypatch, tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    monkeypatch.setattr(hmasd_run, "ROOT", tmp_path)
    direction_id = "direction"
    run_id = "run"
    command = [sys.executable, "-c", "print('complete')"]
    command_sha = hashlib.sha256(
        b"\0".join(os.fsencode(part) for part in command)
    ).hexdigest()
    parameters = {"seed": 7}
    outputs = {
        "stdout": "stdout.log",
        "stderr": "stderr.log",
        "checkpoints": "checkpoints",
        "metrics": "metrics",
        "artifacts": "artifacts",
    }
    run_root = tmp_path / "temp" / "directions" / direction_id / "exp" / run_id
    run_root.mkdir(parents=True)
    preflight_path = run_root / "preflight.json"
    preflight_path.write_text('{"memory_safe":true}\n', encoding="utf-8")
    preflight_sha = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
    runner_spec = {
        "schema_version": 1,
        "command": command,
        "command_sha256": command_sha,
        "cwd": str(tmp_path),
        "git_branch": "omp/test",
        "output_root": str(run_root),
        "outputs": outputs,
        "preflight_sha256": preflight_sha,
    }
    runner_spec_path = run_root / "runner-spec.json"
    runner_spec_path.write_text(
        json.dumps(runner_spec, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    code_sha = "a" * 40
    manifest = {
        "schema_version": 1,
        "revision": 3,
        "writer": "Operator-run",
        "run_id": run_id,
        "direction_id": direction_id,
        "assignment_id": "assignment",
        "operator_identity": "Operator-run",
        "status": "SUCCEEDED",
        "command": command,
        "command_sha256": command_sha,
        "claim_sha256": _json_digest(
            {
                "direction_id": direction_id,
                "code_sha": code_sha,
                "command_sha256": command_sha,
            }
        ),
        "cwd": str(tmp_path),
        "parameters": parameters,
        "parameters_sha256": _json_digest(parameters),
        "code_sha": code_sha,
        "environment": {
            "python": "3.12",
            "platform": "linux",
            "hostname": "test",
            "captured_variables": {},
        },
        "estimate": {
            "wall_seconds": 1,
            "basis": "fixture",
            "peak_memory_gib": 0.01,
        },
        "resources": {
            "preflight_ref": "preflight.json",
            "preflight_sha256": preflight_sha,
            "runner_spec_sha256": hashlib.sha256(runner_spec_path.read_bytes()).hexdigest(),
            "workers": 1,
            "threads_per_worker": 1,
            "memory_safe": True,
        },
        "process": {
            "execution_token": "token",
            "pid": 123,
            "process_group_id": 123,
            "linux_boot_id": "boot",
            "proc_start_ticks": 1,
            "identity_persisted_at": "2026-08-24T00:00:01Z",
            "group_quiescent": True,
            "started_at": "2026-08-24T00:00:00Z",
            "ended_at": "2026-08-24T00:00:02Z",
            "exit_code": 0,
            "terminal_reason": "CHILD_EXIT_0",
        },
        "outputs": outputs,
        "observed_metrics": {},
        "created_at": "2026-08-24T00:00:00Z",
        "updated_at": "2026-08-24T00:00:02Z",
    }
    manifest_path = run_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    results_root = (
        tmp_path / "docs" / "research" / "candidates" / direction_id / "results"
    )
    results_root.mkdir(parents=True)
    markdown_path = results_root / "result.md"
    markdown_path.write_text("# Conclusion\n\nObserved result.\n", encoding="utf-8")
    result_path = results_root / "result.json"
    result = {
        "schema_version": 1,
        "revision": 1,
        "updated_at": "2026-08-24T00:00:03Z",
        "writer": "EM-direction",
        "result_id": "result",
        "direction_id": direction_id,
        "conclusion_path": "docs/research/candidates/direction/results/result.md",
        "source_run": {
            "run_id": run_id,
            "manifest_path": "temp/directions/direction/exp/run/manifest.json",
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "code_sha": code_sha,
            "parameters": parameters,
            "parameters_sha256": _json_digest(parameters),
        },
        "metrics": {
            "score": {
                "value": 1.0,
                "unit": "score",
                "split": "evaluation",
                "aggregation": "mean",
                "sample_count": 1,
            }
        },
        "promoted_at": "2026-08-24T00:00:03Z",
        "promoted_by": "EM-direction",
    }
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest_path, result_path, markdown_path, preflight_path


def test_promote_accepts_only_matching_manifest_code_parameter_and_evidence_hashes(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path, result_path, markdown_path, preflight_path = _write_promotable_pair(
        monkeypatch, tmp_path
    )
    arguments = [
        "promote",
        "--manifest",
        str(manifest_path),
        "--result-json",
        str(result_path),
        "--result-markdown",
        str(markdown_path),
    ]
    original_result = result_path.read_bytes()
    original_preflight = preflight_path.read_bytes()

    assert hmasd_run.main(arguments) == 0
    for field, changed in (
        ("manifest_sha256", "0" * 64),
        ("code_sha", "b" * 40),
        ("parameters_sha256", "1" * 64),
    ):
        result = json.loads(original_result)
        result["source_run"][field] = changed
        result_path.write_text(json.dumps(result), encoding="utf-8")
        assert hmasd_run.main(arguments) == 4
        result_path.write_bytes(original_result)

    result = json.loads(original_result)
    changed_parameters = {"seed": 8}
    result["source_run"]["parameters"] = changed_parameters
    result["source_run"]["parameters_sha256"] = _json_digest(changed_parameters)
    result_path.write_text(json.dumps(result), encoding="utf-8")
    assert hmasd_run.main(arguments) == 4
    result_path.write_bytes(original_result)

    preflight_path.write_text('{"memory_safe":false}\n', encoding="utf-8")
    assert hmasd_run.main(arguments) == 4
    preflight_path.write_bytes(original_preflight)

    runner_spec_path = manifest_path.parent / "runner-spec.json"
    original_runner_spec = runner_spec_path.read_bytes()
    runner_spec_path.write_text('{"changed":true}\n', encoding="utf-8")
    assert hmasd_run.main(arguments) == 4
    runner_spec_path.write_bytes(original_runner_spec)


def test_promote_requires_the_exact_result_json_markdown_pair(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path, result_path, markdown_path, _preflight_path = _write_promotable_pair(
        monkeypatch, tmp_path
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["conclusion_path"] = "docs/research/candidates/direction/results/other.md"
    result_path.write_text(json.dumps(result), encoding="utf-8")
    other_markdown = markdown_path.with_name("other.md")
    other_markdown.write_text("Different conclusion.", encoding="utf-8")

    assert (
        hmasd_run.main(
            [
                "promote",
                "--manifest",
                str(manifest_path),
                "--result-json",
                str(result_path),
                "--result-markdown",
                str(markdown_path),
            ]
        )
        == 4
    )
