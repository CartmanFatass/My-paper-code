from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.codex_supervisor.mailbox_fixtures import seed_active_root_portfolio
from tools.codex_supervisor.host_control import HostControlChannel
from tools.codex_supervisor.runtime_profiles import RuntimeProfile
from tools.codex_supervisor.store import ObserverStore


POWER_SHELL = shutil.which("powershell.exe") or shutil.which("powershell")
PROJECT_PYTHON = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
CODEX_BINARY = shutil.which("codex")


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


def _fixture_supervisor_process() -> subprocess.Popen[str]:
    return subprocess.Popen([PROJECT_PYTHON, "-c", "import time; time.sleep(20)"])


def _external_fixture_root(repo_root: Path) -> Path:
    return Path(tempfile.mkdtemp(prefix="hmasd-request-fixture-", dir=repo_root.parent))


def _write_ready_fixture(
    runtime_home: Path,
    identity: dict[str, str | int],
    *,
    repo_root: Path,
    control_home: Path | None = None,
    semantic_state_path: Path | None = None,
    profile: RuntimeProfile = RuntimeProfile.MANAGED_MANUAL,
    active_run: bool = True,
) -> None:
    assert CODEX_BINARY is not None
    runtime_home.mkdir(parents=True)
    ready = runtime_home / "ready.json"
    process = runtime_home / "supervisor-process.json"
    control = control_home or runtime_home / "control"
    semantic_state = semantic_state_path or runtime_home.parent / "semantic.sqlite3"
    semantic_state.parent.mkdir(parents=True, exist_ok=True)
    semantic_state.touch(exist_ok=True)
    schema_manifest = runtime_home / "schema" / "fixture" / "capture-manifest.json"
    schema_manifest.parent.mkdir(parents=True, exist_ok=True)
    schema_manifest.write_text("{}", encoding="utf-8")
    now = "2026-08-23T00:00:00+00:00"
    store = ObserverStore(runtime_home)
    try:
        run_id = store.start_run(
            codex_binary=str(Path(CODEX_BINARY).resolve()),
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
                    "serve", "--profile", profile.value, "--semantic-state", str(semantic_state),
                    "--ready-file", str(ready), "--control-home", str(control),
                ],
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
        "Get-ReadyStatus",
        "Parse-StrictLaunchArgumentVector",
        "Test-CommandAllowed",
        "Test-ValidatedResponse",
        "Get-ValidatedControlHome",
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
    fixture_root = _external_fixture_root(repo_root)
    runtime_home = fixture_root / "external-runtime"
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
    shutil.rmtree(fixture_root, ignore_errors=True)
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_inactive_observer_run_returns_host_required_without_writing(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    sleeper = _fixture_supervisor_process()
    try:
        fixture_root = _external_fixture_root(repo_root)
        runtime_home = fixture_root / "external-runtime"
        control = fixture_root / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), repo_root=repo_root, control_home=control, active_run=False)
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
        shutil.rmtree(fixture_root, ignore_errors=True)
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_profile_disallowed_command_returns_host_required_without_inbox_write(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    sleeper = _fixture_supervisor_process()
    fixture_root = _external_fixture_root(repo_root)
    try:
        runtime_home = fixture_root / "external-runtime"
        control = fixture_root / "custom-control"
        _write_ready_fixture(
            runtime_home,
            _identity(sleeper.pid),
            repo_root=repo_root,
            control_home=control,
            profile=RuntimeProfile.MAILBOX_MANUAL,
        )
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
        sleeper.terminate()
        sleeper.wait(timeout=5)
        shutil.rmtree(fixture_root, ignore_errors=True)
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_custom_control_home_returns_submission_uncertain_once_without_a_new_request(repo_root: Path, tmp_path: Path) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    # This is an inert process-identity fixture, not a supervisor host.  The test itself writes the response.
    sleeper = _fixture_supervisor_process()
    try:
        fixture_root = _external_fixture_root(repo_root)
        runtime_home = fixture_root / "external-runtime"
        control = fixture_root / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), repo_root=repo_root, control_home=control)
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
                "5",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 4.0
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
        shutil.rmtree(fixture_root, ignore_errors=True)
        shutil.rmtree(tmp_path, ignore_errors=True)


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
    sleeper = _fixture_supervisor_process()
    fixture_root = _external_fixture_root(repo_root)
    try:
        runtime_home = fixture_root / "external-runtime"
        control = fixture_root / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), repo_root=repo_root, control_home=control)
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
        deadline = time.monotonic() + 4.0
        requests: list[Path] = []
        while time.monotonic() < deadline:
            requests = list(inbox.glob("*.json")) if inbox.exists() else []
            if requests:
                break
            time.sleep(0.03)
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
        sleeper.terminate()
        sleeper.wait(timeout=5)
        shutil.rmtree(fixture_root, ignore_errors=True)
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_canary_script_dispatches_exact_root_to_portfolio_acl_message(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    fixture_root = _external_fixture_root(repo_root)
    actors_home = fixture_root / "actors"
    actors_home.mkdir()
    seeded = seed_active_root_portfolio(actors_home)
    sleeper = _fixture_supervisor_process()
    try:
        runtime_home = fixture_root / "external-runtime"
        control = fixture_root / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), repo_root=repo_root, control_home=control, semantic_state_path=actors_home / "semantic.sqlite3", profile=RuntimeProfile.MAILBOX_MANUAL)
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

        channel = HostControlChannel(
            control,
            profile=RuntimeProfile.MAILBOX_MANUAL,
            repo_root=repo_root,
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
        sleeper.terminate()
        sleeper.wait(timeout=5)
        seeded["bridge"].close()
        seeded["supervisor"].close()
        seeded["semantic"].close()
        shutil.rmtree(fixture_root, ignore_errors=True)
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_response_timeout_returns_correlated_uncertain_response_without_retry(
    repo_root: Path, tmp_path: Path
) -> None:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    # This inert process fixture satisfies only the guarded host identity; no
    # process reads the durable request or writes an outbox response.
    sleeper = _fixture_supervisor_process()
    try:
        fixture_root = _external_fixture_root(repo_root)
        runtime_home = fixture_root / "external-runtime"
        control = fixture_root / "custom-control"
        _write_ready_fixture(runtime_home, _identity(sleeper.pid), repo_root=repo_root, control_home=control)
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
        shutil.rmtree(fixture_root, ignore_errors=True)
        shutil.rmtree(tmp_path, ignore_errors=True)
