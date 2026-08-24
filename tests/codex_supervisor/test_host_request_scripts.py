from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.host_control import HostControlChannel
from tools.codex_supervisor.runtime_profiles import RuntimeProfile
from tools.codex_supervisor.store import ObserverStore
from tools.codex_semantic_mvp.store import SemanticStore


POWER_SHELL = shutil.which("powershell.exe") or shutil.which("powershell")
PROJECT_PYTHON = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
CODEX_BINARY = PROJECT_PYTHON


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


def _prepare_fixture_repo(source_repo: Path, fixture_repo: Path) -> Path:
    """Copy only inert test code below pytest's worktree-local basetemp."""
    fixture_repo.mkdir(parents=True)
    shutil.copytree(source_repo / "tools", fixture_repo / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(source_repo / ".codex", fixture_repo / ".codex", ignore=shutil.ignore_patterns("__pycache__"))
    return fixture_repo.resolve()


def _terminate_inert_tree(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return
    subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _fixture_supervisor_process(fixture_repo: Path, launch_vector: list[str]) -> tuple[subprocess.Popen[object], int]:
    """A harmless host/child pair whose OS argv is the strict serve vector."""
    package = fixture_repo / "tools" / "codex_supervisor"
    (fixture_repo / "app-server").write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    pid_file = fixture_repo / "child-pid.json"
    module = (
        "import json,os,subprocess,sys,time\nfrom pathlib import Path\n"
        "if 'serve' not in sys.argv:\n from tools.codex_supervisor.cli import main\n raise SystemExit(main())\n"
        "child=subprocess.Popen([os.environ['HMASD_INERT_CODEX'],'app-server'],cwd=os.getcwd())\n"
        "Path(os.environ['HMASD_INERT_PID_FILE']).write_text(json.dumps({'pid':child.pid}))\ntime.sleep(60)\n"
    )
    (package / "__main__.py").write_text(module, encoding="utf-8")
    environment = os.environ.copy()
    environment.update({"HMASD_INERT_CODEX": str(PROJECT_PYTHON), "HMASD_INERT_PID_FILE": str(pid_file)})
    host = subprocess.Popen([PROJECT_PYTHON, *launch_vector], cwd=fixture_repo, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        if pid_file.is_file():
            child_id = int(json.loads(pid_file.read_text(encoding="utf-8"))["pid"])
            if subprocess.run(["tasklist.exe", "/FI", f"PID eq {child_id}", "/NH"], capture_output=True, text=True, check=False).returncode == 0:
                return host, child_id
        if host.poll() is not None:
            break
        time.sleep(0.05)
    _terminate_inert_tree(host)
    raise AssertionError("inert supervisor-shaped fixture failed to publish child")


def _await_published_request(
    process: subprocess.Popen[str], inbox: Path, *, timeout_seconds: float = 15.0
) -> list[Path]:
    """Wait for the single durable request without racing truthful host preflight."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        requests = list(inbox.glob("*.json")) if inbox.exists() else []
        if requests:
            return requests
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=1)
            raise AssertionError(
                "request wrapper exited before publishing a durable request: "
                f"stdout={stdout!r} stderr={stderr!r}"
            )
        if time.monotonic() >= deadline:
            return requests
        time.sleep(0.03)


def _write_ready_fixture(
    runtime_home: Path,
    identity: dict[str, str | int],
    *,
    repo_root: Path,
    control_home: Path | None = None,
    semantic_state_path: Path | None = None,
    profile: RuntimeProfile = RuntimeProfile.MANAGED_MANUAL,
    active_run: bool = True,
    app_server_process_id: int | None = None,
) -> None:
    runtime_home.mkdir(parents=True)
    ready = runtime_home / "ready.json"
    process = runtime_home / "supervisor-process.json"
    control = control_home or runtime_home / "control"
    semantic_state = semantic_state_path or runtime_home.parent / "semantic.sqlite3"
    semantic_state.parent.mkdir(parents=True, exist_ok=True)
    if not semantic_state.exists():
        semantic = SemanticStore(semantic_state).initialize()
        semantic.close()
    schema_manifest = runtime_home / "schema" / "fixture" / "capture-manifest.json"
    schema_manifest.parent.mkdir(parents=True, exist_ok=True)
    schema_manifest.write_text("{}", encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat()
    store = ObserverStore(runtime_home)
    try:
        run_id = store.start_run(
            codex_binary=str(Path(CODEX_BINARY).resolve()),
            codex_version="fixture",
            client_name="request-script-test",
            process_id=app_server_process_id or int(identity["pid"]),
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
                "repo_root": str(repo_root.resolve()),
                "runtime_home": str(runtime_home),
                "profile": profile.value,
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
                "profile": profile.value,
            }
        ),
        encoding="utf-8",
    )
    (runtime_home / "supervisor-launch-evidence.json").write_text(
        json.dumps(
            {
                "schema": "HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2",
                "observed_at": now,
                "argument_vector": [
                    "-m", "tools.codex_supervisor", "--repo-root", str(repo_root.resolve()),
                    "--runtime-home", str(runtime_home), "--codex-bin", str(Path(CODEX_BINARY).resolve()),
                    "serve", "--profile", profile.value,
                    *([] if profile is RuntimeProfile.OBSERVER else ["--semantic-state", str(semantic_state)]),
                    "--ready-file", str(ready), "--control-home", str(control),
                ],
                "control_home": str(control),
                "ready_file": str(ready),
                "startup_ready_timeout_seconds": 150.0,
            }
        ),
        encoding="utf-8",
    )


def _start_ready_fixture(
    tmp_path: Path,
    source_repo: Path,
    *,
    profile: RuntimeProfile = RuntimeProfile.MANAGED_MANUAL,
    active_run: bool = True,
    semantic_state_path: Path | None = None,
) -> tuple[Path, Path, Path, Path, subprocess.Popen[object]]:
    """Build all disposable state under pytest's worktree-local basetemp."""
    container = tmp_path / "inert-host-fixture"
    fixture_repo = _prepare_fixture_repo(source_repo, container / "repo")
    runtime_home = container / "external-runtime"
    control = container / "custom-control"
    semantic_state = semantic_state_path or (container / "semantic.sqlite3")
    ready = runtime_home / "ready.json"
    vector = [
        "-m", "tools.codex_supervisor", "--repo-root", str(fixture_repo),
        "--runtime-home", str(runtime_home), "--codex-bin", str(Path(CODEX_BINARY).resolve()),
        "serve", "--profile", profile.value,
        *([] if profile is RuntimeProfile.OBSERVER else ["--semantic-state", str(semantic_state)]),
        "--ready-file", str(ready), "--control-home", str(control),
    ]
    host, child_id = _fixture_supervisor_process(fixture_repo, vector)
    _write_ready_fixture(
        runtime_home, _identity(host.pid), repo_root=fixture_repo,
        control_home=control, semantic_state_path=semantic_state, profile=profile,
        active_run=active_run, app_server_process_id=child_id,
    )
    return fixture_repo, runtime_home, control, semantic_state, host


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
        "Get-ReadyStatus",
        "Parse-StrictLaunchArgumentVector",
        "Test-CommandAllowed",
        "Test-ValidatedResponseCapture",
        "Get-ValidatedHostBinding",
        "Test-ExpectedHostTuple",
        "ExpectedSemanticState",
        "hmasd-root-supervisor-status.ps1",
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
        assert "-ExpectedRepoRoot $RepoRoot" in text
        assert "-ExpectedCodexBinary $CodexBinary" in text
        assert "-m\", \"tools.codex_supervisor\"" not in text
    for name in (
        "codex-managed-actor-create.ps1", "codex-managed-actor-adopt.ps1",
        "codex-managed-actor-turn.ps1", "codex-managed-actor-suspend.ps1",
        "codex-mailbox-once.ps1", "codex-mailbox-send-canary.ps1",
    ):
        assert "-ExpectedSemanticState $SemanticState" in _script(repo_root, name).read_text(encoding="utf-8")
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


def test_mailbox_list_rejects_whitespace_repo_root_before_host_request(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        fixture_repo, runtime_home, control, _, host = _start_ready_fixture(
            tmp_path, repo_root, profile=RuntimeProfile.MAILBOX_MANUAL
        )
        rejected = subprocess.run(
            [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(_script(repo_root, "codex-mailbox-list.ps1")),
                "-RepoRoot", "   ", "-PythonExecutable", PROJECT_PYTHON,
                "-RuntimeHome", str(runtime_home), "-TimeoutSeconds", "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert rejected.returncode != 0
        assert "RepoRoot must be non-empty and non-whitespace" in rejected.stderr
        assert not list((control / "inbox").glob("*.json"))

        process = subprocess.Popen(
            [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(_script(repo_root, "codex-mailbox-list.ps1")),
                "-RepoRoot", str(fixture_repo), "-PythonExecutable", PROJECT_PYTHON,
                "-CodexBinary", CODEX_BINARY,
                "-RuntimeHome", str(runtime_home), "-TimeoutSeconds", "5",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        requests = _await_published_request(process, control / "inbox")
        assert len(requests) == 1
        request = json.loads(requests[0].read_text(encoding="utf-8"))
        assert request["command"] == "MAILBOX_LIST"
        outbox = control / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        (outbox / requests[0].name).write_text(
            json.dumps(
                {
                    "schema": "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1",
                    "request_id": request["request_id"],
                    "status": "OK",
                    "payload": {"items": []},
                    "error": None,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            encoding="utf-8",
        )
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        assert json.loads(stdout)["status"] == "OK"
    finally:
        if host is not None:
            _terminate_inert_tree(host)


def test_no_ready_host_returns_exact_marker_without_writing_mutation(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    runtime_home = tmp_path / "no-host-runtime"
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


def test_inactive_observer_run_returns_host_required_without_writing(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        _, runtime_home, control, _, host = _start_ready_fixture(tmp_path, repo_root, active_run=False)
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
        if host is not None: _terminate_inert_tree(host)


def test_profile_disallowed_command_returns_host_required_without_inbox_write(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        _, runtime_home, control, _, host = _start_ready_fixture(tmp_path, repo_root, profile=RuntimeProfile.MAILBOX_MANUAL)
        result = subprocess.run(
            [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command", "MANAGED_TURN", "-ArgumentsJson", "{}", "-Operator", "test-operator",
                "-RuntimeHome", str(runtime_home), "-TimeoutSeconds", "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert result.stdout.strip() == "HMASD_SUPERVISOR_HOST_REQUIRED_V1"
        assert not (control / "inbox").exists()
    finally:
        if host is not None: _terminate_inert_tree(host)


@pytest.mark.parametrize("command", ("STATUS", "INSPECT"))
def test_observer_read_command_uses_validated_generic_host_binding(
    repo_root: Path, tmp_path: Path, command: str
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        fixture_repo, runtime_home, control, _, host = _start_ready_fixture(
            tmp_path, repo_root, profile=RuntimeProfile.OBSERVER
        )
        process = subprocess.Popen(
            [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command", command, "-ArgumentsJson", "{}", "-Operator", "test-operator",
                "-RuntimeHome", str(runtime_home), "-ExpectedRepoRoot", str(fixture_repo),
                "-TimeoutSeconds", "5",
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        requests = _await_published_request(process, control / "inbox")
        assert len(requests) == 1
        request = json.loads(requests[0].read_text(encoding="utf-8"))
        outbox = control / "outbox"; outbox.mkdir(parents=True, exist_ok=True)
        (outbox / requests[0].name).write_text(json.dumps({
            "schema": "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1", "request_id": request["request_id"],
            "status": "OK", "payload": {"read_only": True}, "error": None,
            "completed_at": "2026-08-23T00:00:00+00:00",
        }), encoding="utf-8")
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        assert json.loads(stdout)["payload"] == {"read_only": True}
    finally:
        if host is not None: _terminate_inert_tree(host)


@pytest.mark.parametrize("mismatch", ("repo", "semantic", "missing-semantic", "binary"))
def test_expected_launch_tuple_mismatch_fails_closed_before_inbox_write(
    repo_root: Path, tmp_path: Path, mismatch: str
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        fixture_repo, runtime_home, control, semantic_state, host = _start_ready_fixture(tmp_path, repo_root)
        expected_repo = fixture_repo
        expected_semantic = semantic_state
        expected_binary: Path | None = None
        if mismatch == "repo":
            expected_repo = tmp_path / "wrong-repo"
            expected_repo.mkdir()
        elif mismatch == "semantic":
            expected_semantic = tmp_path / "wrong-semantic.sqlite3"
            semantic = SemanticStore(expected_semantic).initialize()
            semantic.close()
        else:
            if mismatch == "missing-semantic":
                expected_semantic = tmp_path / "missing-semantic.sqlite3"
            else:
                expected_binary = tmp_path / "wrong-codex.exe"
                expected_binary.write_bytes(b"inert")
        result = subprocess.run(
            [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command", "MANAGED_TURN", "-ArgumentsJson", "{}", "-Operator", "test-operator",
                "-RuntimeHome", str(runtime_home), "-ExpectedRepoRoot", str(expected_repo),
                "-ExpectedSemanticState", str(expected_semantic),
                *( ["-ExpectedCodexBinary", str(expected_binary)] if expected_binary else [] ),
                "-TimeoutSeconds", "1",
            ], capture_output=True, text=True, check=False,
        )
        assert result.returncode != 0
        assert result.stdout.strip() == "HMASD_SUPERVISOR_HOST_REQUIRED_V1", result.stderr
        assert not (control / "inbox").exists()
    finally:
        if host is not None: _terminate_inert_tree(host)


def test_custom_control_home_returns_submission_uncertain_once_without_a_new_request(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        fixture_repo, runtime_home, control, semantic_state, host = _start_ready_fixture(tmp_path, repo_root)
        readiness = subprocess.run([POWER_SHELL, "-NoProfile", "-NonInteractive", "-File", str(_script(repo_root, "hmasd-root-supervisor-status.ps1")), "-RepoRoot", str(fixture_repo), "-RuntimeHome", str(runtime_home), "-PythonPath", PROJECT_PYTHON], capture_output=True, text=True, check=False)
        assert json.loads(readiness.stdout)["state"] == "READY", readiness.stderr + readiness.stdout
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
                "-ExpectedRepoRoot",
                str(fixture_repo),
                "-ExpectedSemanticState",
                str(semantic_state),
                "-ExpectedCodexBinary",
                PROJECT_PYTHON,
                "-TimeoutSeconds",
                "5",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        requests = _await_published_request(process, inbox)
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
        if host is not None: _terminate_inert_tree(host)


def test_response_emits_the_single_validated_capture_when_outbox_is_replaced(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        _, runtime_home, control, _, host = _start_ready_fixture(tmp_path, repo_root)
        process = subprocess.Popen(
            [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command", "MANAGED_TURN", "-ArgumentsJson", "{}", "-Operator", "test-operator",
                "-RuntimeHome", str(runtime_home), "-TimeoutSeconds", "5",
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        inbox = control / "inbox"
        requests = _await_published_request(process, inbox)
        assert len(requests) == 1
        request_id = json.loads(requests[0].read_text(encoding="utf-8"))["request_id"]
        outbox = control / "outbox"; outbox.mkdir(parents=True, exist_ok=True)
        response_path = outbox / requests[0].name
        stable = {
            "schema": "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1", "request_id": request_id,
            "status": "OK", "payload": {"capture": "stable", "padding": "x" * 8_000_000},
            "error": None, "completed_at": "2026-08-23T00:00:00+00:00",
        }
        replacement = {
            "schema": "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1", "request_id": request_id,
            "status": "OK", "payload": {"capture": "replacement"},
            "error": None, "completed_at": "2026-08-23T00:00:00+00:00",
        }
        response_path.write_text(json.dumps(stable), encoding="utf-8")
        observed_snapshot = threading.Event()

        def replace_after_capture_seam() -> None:
            capture = control / "validation" / f"{request_id}.capture.json"
            while process.poll() is None:
                if capture.exists():
                    observed_snapshot.set()
                    response_path.write_text(json.dumps(replacement), encoding="utf-8")
                    return
                time.sleep(0.001)

        mutator = threading.Thread(target=replace_after_capture_seam, daemon=True)
        mutator.start()
        stdout, stderr = process.communicate(timeout=10)
        mutator.join(timeout=1)
        assert observed_snapshot.is_set(), "response capture seam was not observed"
        assert process.returncode == 0, stderr
        emitted = json.loads(stdout)
        assert emitted["payload"]["capture"] == "stable"
        assert "padding" in emitted["payload"]
    finally:
        if host is not None: _terminate_inert_tree(host)


@pytest.mark.parametrize(
    ("status", "payload", "error", "completed_at"),
    (
        ("OK", {"test": True}, "unexpected error", "2026-08-23T00:00:00+00:00"),
        ("ERROR", ["not-an-object"], "rejected", "2026-08-23T00:00:00+00:00"),
        ("ERROR", {"test": True}, None, "2026-08-23T00:00:00+00:00"),
        ("ERROR", {"test": True}, "rejected", "2026-08-23T00:00:00"),
    ),
)
def test_malformed_control_response_is_rejected_without_request_replacement(
    repo_root: Path,
    tmp_path: Path,
    status: str,
    payload: object,
    error: object,
    completed_at: str,
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        _, runtime_home, control, _, host = _start_ready_fixture(tmp_path, repo_root)
        process = subprocess.Popen(
            [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(_script(repo_root, "hmasd-supervisor-request.ps1")),
                "-Command", "MANAGED_TURN", "-ArgumentsJson", "{}", "-Operator", "test-operator",
                "-RuntimeHome", str(runtime_home), "-TimeoutSeconds", "5",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        inbox = control / "inbox"
        requests = _await_published_request(process, inbox)
        assert len(requests) == 1, process.stdout.read() + process.stderr.read()
        request = json.loads(requests[0].read_text(encoding="utf-8"))
        outbox = control / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        (outbox / requests[0].name).write_text(
            json.dumps(
                {
                    "schema": "HMASD_SUPERVISOR_CONTROL_RESPONSE_V1",
                    "request_id": request["request_id"],
                    "status": status,
                    "payload": payload,
                    "error": error,
                    "completed_at": completed_at,
                }
            ),
            encoding="utf-8",
        )
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode != 0
        assert not stdout.strip()
        assert "HostControlResponse contract" in stderr
        assert len(list(inbox.glob("*.json"))) == 1
        assert json.loads(requests[0].read_text(encoding="utf-8"))["request_id"] == request["request_id"]
    finally:
        if host is not None: _terminate_inert_tree(host)


def test_canary_script_dispatches_exact_root_to_portfolio_acl_message(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    fixture_root = tmp_path / "inert-host-fixture"
    fixture_root.mkdir()
    actors_home = fixture_root / "actors"
    actors_home.mkdir()
    seeded = seed_active_root_portfolio(actors_home)
    host = None
    try:
        fixture_repo, runtime_home, control, _, host = _start_ready_fixture(
            tmp_path, repo_root, profile=RuntimeProfile.MAILBOX_MANUAL,
            semantic_state_path=actors_home / "semantic.sqlite3",
        )
        process = subprocess.Popen(
            [
                POWER_SHELL,
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(_script(repo_root, "codex-mailbox-send-canary.ps1")),
                "-RepoRoot",
                str(fixture_repo),
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
        deadline = time.monotonic() + 7.0
        inbox_requests: list[Path] = []
        while time.monotonic() < deadline:
            inbox_requests = list((control / "inbox").glob("*.json"))
            if inbox_requests:
                break
            time.sleep(0.03)
        assert len(inbox_requests) == 1, process.stdout.read() + process.stderr.read()

        channel = HostControlChannel(
            control,
            profile=RuntimeProfile.MAILBOX_MANUAL,
            repo_root=fixture_repo,
            semantic_state_path=actors_home / "semantic.sqlite3",
        )
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
        if host is not None: _terminate_inert_tree(host)
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()


def test_response_timeout_returns_correlated_uncertain_response_without_retry(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    host = None
    try:
        _, runtime_home, control, _, host = _start_ready_fixture(tmp_path, repo_root)
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
        if host is not None: _terminate_inert_tree(host)
