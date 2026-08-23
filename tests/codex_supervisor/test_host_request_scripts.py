from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.host_control import HostControlChannel
from tools.codex_supervisor.runtime_profiles import RuntimeProfile
from tools.codex_supervisor.store import ObserverStore


POWER_SHELL = shutil.which("powershell.exe") or shutil.which("powershell")


def _script(repo_root: Path, name: str) -> Path:
    return repo_root / "scripts" / name


def _parse_powershell(path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    command = (
        "& { param($Path) $tokens = $null; $errors = $null; "
        "[System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -ne 0) { $errors | ForEach-Object { $_.Message }; exit 1 } }"
    )
    result = subprocess.run(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", command, str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def _identity(process_id: int) -> dict[str, str | int]:
    assert POWER_SHELL is not None
    command = (
        f"$p = Get-Process -Id {process_id} -ErrorAction Stop; "
        "[pscustomobject]@{ pid = $p.Id; process_start_time_utc = $p.StartTime.ToUniversalTime().ToString('o'); "
        "executable = [System.IO.Path]::GetFullPath([string]$p.Path) } | ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _write_ready_fixture(
    runtime_home: Path,
    identity: dict[str, str | int],
    *,
    control_home: Path | None = None,
    active_run: bool = True,
) -> None:
    runtime_home.mkdir(parents=True)
    ready = runtime_home / "ready.json"
    process = runtime_home / "supervisor-process.json"
    control = control_home or runtime_home / "control"
    now = "2026-08-23T00:00:00+00:00"
    store = ObserverStore(runtime_home)
    try:
        run_id = store.start_run(
            codex_binary="fixture",
            codex_version="fixture",
            client_name="request-script-test",
            process_id=int(identity["pid"]),
        )
        if active_run:
            store.mark_initialized(run_id)
    finally:
        store.close()
    process.write_text(
        json.dumps(
            {
                "schema": "HMASD_SUPERVISOR_PROCESS_V1",
                "pid": identity["pid"],
                "process_start_time_utc": identity["process_start_time_utc"],
                "executable": identity["executable"],
                "repo_root": "C:/external-test-repo",
                "runtime_home": str(runtime_home),
                "profile": "MANAGED_MANUAL",
                "started_at": now,
                "ready_file": str(ready),
            }
        ),
        encoding="utf-8",
    )
    ready.write_text(
        json.dumps(
            {
                "schema": "HMASD_SUPERVISOR_READY_V2",
                "run_id": run_id,
                "process_id": identity["pid"],
                "initialized_at": now,
                "watcher_active": True,
                "first_reconciliation_completed": True,
                "thread_count": 0,
                "runtime_home": str(runtime_home),
                "profile": "MANAGED_MANUAL",
            }
        ),
        encoding="utf-8",
    )
    (runtime_home / "supervisor-launch-evidence.json").write_text(
        json.dumps(
            {
                "schema": "HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2",
                "observed_at": now,
                "argument_vector": ["-m", "tools.codex_supervisor", "serve"],
                "control_home": str(control),
                "ready_file": str(ready),
            }
        ),
        encoding="utf-8",
    )


def test_request_wrapper_and_all_routed_scripts_parse(repo_root: Path) -> None:
    names = (
        "hmasd-supervisor-request.ps1",
        "codex-managed-actor-create.ps1",
        "codex-managed-actor-adopt.ps1",
        "codex-managed-actor-turn.ps1",
        "codex-managed-actor-suspend.ps1",
        "codex-mailbox-list.ps1",
        "codex-mailbox-once.ps1",
        "codex-mailbox-send-canary.ps1",
    )
    for name in names:
        _parse_powershell(_script(repo_root, name))


def test_routed_scripts_use_typed_host_requests_and_preserve_safety_contract(repo_root: Path) -> None:
    wrapper = _script(repo_root, "hmasd-supervisor-request.ps1").read_text(encoding="utf-8")
    for required in (
        "HMASD_SUPERVISOR_HOST_REQUIRED_V1",
        "HMASD_SUPERVISOR_CONTROL_REQUEST_V1",
        "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1",
        "Test-ExactReadyHost",
        "Test-ActiveObserverRun",
        "Get-ValidatedControlHome",
        "Get-Process -Id",
        "SUBMISSION_UNCERTAIN",
        "[System.IO.File]::Move",
    ):
        assert required in wrapper
    assert "$requestId = [guid]::NewGuid().ToString()" in wrapper
    scripts = {
        "codex-managed-actor-create.ps1": "MANAGED_CREATE",
        "codex-managed-actor-adopt.ps1": "MANAGED_ADOPT",
        "codex-managed-actor-turn.ps1": "MANAGED_TURN",
        "codex-managed-actor-suspend.ps1": "MANAGED_SUSPEND",
        "codex-mailbox-list.ps1": "MAILBOX_LIST",
        "codex-mailbox-once.ps1": "MAILBOX_DELIVER_ONCE",
        "codex-mailbox-send-canary.ps1": "MAILBOX_ENQUEUE",
    }
    for name, command in scripts.items():
        text = _script(repo_root, name).read_text(encoding="utf-8")
        assert "hmasd-supervisor-request.ps1" in text
        assert command in text
        assert "-PythonExecutable $PythonExecutable" in text
        assert "-m\", \"tools.codex_supervisor\"" not in text
    assert "confirm_global_memory_disabled = $true" in _script(repo_root, "codex-managed-actor-create.ps1").read_text(encoding="utf-8")
    adopt = _script(repo_root, "codex-managed-actor-adopt.ps1").read_text(encoding="utf-8")
    assert "confirm_history_nonauthoritative = $true" in adopt
    assert "confirm_global_memory_disabled = $true" in adopt
    once = _script(repo_root, "codex-mailbox-once.ps1").read_text(encoding="utf-8")
    assert "scheduler" not in once.lower()
    canary = _script(repo_root, "codex-mailbox-send-canary.ps1").read_text(encoding="utf-8")
    assert "source_actor_context_id" in canary and "target_actor_context_id" in canary
    assert "source_snapshot" not in canary and "target_snapshot" not in canary
    assert "message_kind = 'ROOT_TO_PORTFOLIO_REVIEW'" in canary
    assert "OPERATOR_ATTENTION_REQUEST" not in canary


def test_no_ready_host_returns_exact_marker_without_writing_mutation(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    runtime_home = tmp_path / "external-runtime"
    result = subprocess.run(
        [
            POWER_SHELL,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(_script(repo_root, "hmasd-supervisor-request.ps1")),
            "-Command",
            "MANAGED_TURN",
            "-ArgumentsJson",
            "{}",
            "-Operator",
            "test-operator",
            "-RuntimeHome",
            str(runtime_home),
            "-TimeoutSeconds",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert result.stdout.strip() == "HMASD_SUPERVISOR_HOST_REQUIRED_V1"
    assert not (runtime_home / "control" / "inbox").exists()
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_inactive_observer_run_returns_host_required_without_writing(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    sleeper = subprocess.Popen([POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 20"])
    try:
        runtime_home = tmp_path / "external-runtime"
        control = tmp_path / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), control_home=control, active_run=False)
        result = subprocess.run(
            [
                POWER_SHELL,
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command",
                "MANAGED_TURN",
                "-ArgumentsJson",
                "{}",
                "-Operator",
                "test-operator",
                "-RuntimeHome",
                str(runtime_home),
                "-TimeoutSeconds",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert result.stdout.strip() == "HMASD_SUPERVISOR_HOST_REQUIRED_V1", result.stderr
        assert not (control / "inbox").exists()
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_custom_control_home_returns_submission_uncertain_once_without_a_new_request(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    # This is an inert process-identity fixture, not a supervisor host.  The test itself writes the response.
    sleeper = subprocess.Popen([POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 20"])
    try:
        runtime_home = tmp_path / "external-runtime"
        control = tmp_path / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), control_home=control)
        inbox = control / "inbox"
        outbox = control / "outbox"
        process = subprocess.Popen(
            [
                POWER_SHELL,
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command",
                "MANAGED_TURN",
                "-ArgumentsJson",
                "{}",
                "-Operator",
                "test-operator",
                "-RuntimeHome",
                str(runtime_home),
                "-TimeoutSeconds",
                "3",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 2.0
        requests: list[Path] = []
        while time.monotonic() < deadline:
            requests = list(inbox.glob("*.json")) if inbox.exists() else []
            if requests:
                break
            time.sleep(0.03)
        assert len(requests) == 1, process.stdout.read() + process.stderr.read()
        request = json.loads(requests[0].read_text(encoding="utf-8"))
        outbox.mkdir(parents=True, exist_ok=True)
        response = {
            "schema": "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1",
            "request_id": request["request_id"],
            "status": "SUBMISSION_UNCERTAIN",
            "payload": {"test": True},
            "error": "submission status cannot be determined",
            "completed_at": "2026-08-23T00:00:00+00:00",
        }
        (outbox / requests[0].name).write_text(json.dumps(response), encoding="utf-8")
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        assert json.loads(stdout)["status"] == "SUBMISSION_UNCERTAIN"
        assert len(list(inbox.glob("*.json"))) == 1
        assert len(list(outbox.glob("*.json"))) == 1
        assert not (runtime_home / "control").exists()
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_canary_script_dispatches_exact_root_to_portfolio_acl_message(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    actors_home = tmp_path / "actors"
    actors_home.mkdir()
    seeded = seed_active_root_portfolio(actors_home)
    sleeper = subprocess.Popen(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 20"]
    )
    try:
        runtime_home = tmp_path / "external-runtime"
        control = tmp_path / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), control_home=control)
        process = subprocess.Popen(
            [
                POWER_SHELL,
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(_script(repo_root, "codex-mailbox-send-canary.ps1")),
                "-RepoRoot",
                str(tmp_path / "repo"),
                "-PythonExecutable",
                "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
                "-Operator",
                "test-operator",
                "-SourceActorContextId",
                seeded["root"].actor_context_id,
                "-TargetActorContextId",
                seeded["portfolio"].actor_context_id,
                "-SubjectRef",
                "canary-subject",
                "-PayloadRef",
                "canary-payload",
                "-SemanticState",
                str(actors_home / "semantic.sqlite3"),
                "-RuntimeHome",
                str(runtime_home),
                "-TimeoutSeconds",
                "5",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 3.0
        inbox_requests: list[Path] = []
        while time.monotonic() < deadline:
            inbox_requests = list((control / "inbox").glob("*.json"))
            if inbox_requests:
                break
            time.sleep(0.03)
        assert len(inbox_requests) == 1

        channel = HostControlChannel(control)
        request = channel.claim_next()
        assert request is not None, [
            path.read_text(encoding="utf-8") for path in channel.rejected.glob("*.reason.json")
        ]
        assert request.arguments["message_kind"] == "ROOT_TO_PORTFOLIO_REVIEW"
        response = asyncio.run(
            channel.dispatch(
                request,
                profile=RuntimeProfile.MAILBOX_MANUAL,
                service=SimpleNamespace(
                    store=seeded["supervisor"],
                    run_id="fixture-run",
                    client=object(),
                    transport=None,
                    _stopped=False,
                ),
                stop_event=asyncio.Event(),
            )
        )
        channel.write_response(response)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        emitted = json.loads(stdout)
        assert emitted["request_id"] == request.request_id
        assert emitted["status"] == "OK"

        bindings = seeded["bindings"]
        root_binding = bindings.binding_for_actor(seeded["root"].actor_context_id)
        portfolio_binding = bindings.binding_for_actor(
            seeded["portfolio"].actor_context_id
        )
        assert root_binding is not None
        assert portfolio_binding is not None
        eligible = seeded["mailbox"].select_eligible(
            target_actor_context_id=seeded["portfolio"].actor_context_id,
            target_kind=portfolio_binding.actor_kind.value,
            target_binding_state=portfolio_binding.binding_state.value,
            sender_kind_for={
                seeded["root"].actor_context_id: root_binding.actor_kind.value
            },
        )
        assert len(eligible) == 1
        assert eligible[0].source_system == "MANAGED_ACTOR"
        assert eligible[0].message_kind.value == "ROOT_TO_PORTFOLIO_REVIEW"
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_response_timeout_returns_correlated_uncertain_response_without_retry(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    # This inert process fixture satisfies only the guarded host identity; no
    # process reads the durable request or writes an outbox response.
    sleeper = subprocess.Popen(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 20"]
    )
    try:
        runtime_home = tmp_path / "external-runtime"
        control = tmp_path / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), control_home=control)
        result = subprocess.run(
            [
                POWER_SHELL,
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command",
                "MANAGED_TURN",
                "-ArgumentsJson",
                "{}",
                "-Operator",
                "test-operator",
                "-RuntimeHome",
                str(runtime_home),
                "-TimeoutSeconds",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        response = json.loads(result.stdout)
        assert response["schema"] == "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1"
        assert response["status"] == "SUBMISSION_UNCERTAIN"
        assert response["payload"] == {
            "local_response_timeout": True,
            "durable_request_written": True,
            "timeout_seconds": 1,
        }
        assert "inspect the durable request" in response["error"]
        assert "do not retry" in response["error"]
        assert response["completed_at"]
        requests = list((control / "inbox").glob("*.json"))
        assert len(requests) == 1
        request = json.loads(requests[0].read_text(encoding="utf-8"))
        assert response["request_id"] == request["request_id"] == requests[0].stem
        assert not (control / "outbox").exists()
        assert not (runtime_home / "control").exists()
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)
        shutil.rmtree(tmp_path, ignore_errors=True)
