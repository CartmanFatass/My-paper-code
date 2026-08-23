from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from tests.codex_supervisor.helpers import write_fake_codex
from tools.codex_supervisor.db import connect, initialize_database


POWER_SHELL = shutil.which("powershell.exe") or shutil.which("powershell")
PROJECT_PYTHON = Path("C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe")


def read_script(repo_root: Path, name: str) -> str:
    return (repo_root / "scripts" / name).read_text(encoding="utf-8")


def script_path(repo_root: Path, name: str) -> Path:
    return repo_root / "scripts" / name


def parse_powershell(path: Path) -> None:
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


def invoke_start_helpers(path: Path, names: tuple[str, ...], body: str, *args: str) -> subprocess.CompletedProcess[str]:
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    command = (
        "& { "
        "$Path=$env:HMASD_HELPER_PATH; $NamesJson=$env:HMASD_HELPER_NAMES; $Body=$env:HMASD_HELPER_BODY; "
        "$A1=$env:HMASD_HELPER_A1; $A2=$env:HMASD_HELPER_A2; $A3=$env:HMASD_HELPER_A3; "
        "$A4=$env:HMASD_HELPER_A4; $A5=$env:HMASD_HELPER_A5; $A6=$env:HMASD_HELPER_A6; "
        "$A7=$env:HMASD_HELPER_A7; $A8=$env:HMASD_HELPER_A8; $A9=$env:HMASD_HELPER_A9; "
        "$A10=$env:HMASD_HELPER_A10; $A11=$env:HMASD_HELPER_A11; $A12=$env:HMASD_HELPER_A12; "
        "$tokens=$null; $errors=$null; "
        "$ast=[System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors); "
        "if($errors.Count){$errors|ForEach-Object{$_.Message};exit 1}; "
        "$names=ConvertFrom-Json -InputObject $NamesJson; $source=''; foreach($name in @($names)){"
        "$node=$ast.Find({param($candidate) $candidate -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $candidate.Name -eq $name},$true); "
        "if($null -eq $node){throw ('missing function: '+$name)}; $source += $node.Extent.Text + \"`n\"}; "
        "$source += $Body; Invoke-Expression $source }"
    )
    environment = os.environ.copy()
    environment.update(
        {
            "HMASD_HELPER_PATH": str(path),
            "HMASD_HELPER_NAMES": json.dumps(names),
            "HMASD_HELPER_BODY": body,
        }
    )
    for index, value in enumerate(args, start=1):
        environment[f"HMASD_HELPER_A{index}"] = value
    return subprocess.run(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )


def process_identity(process_id: int) -> dict[str, object]:
    assert POWER_SHELL is not None
    command = (
        f"$p=Get-Process -Id {process_id} -ErrorAction Stop; "
        "[ordered]@{Pid=$p.Id;StartTimeUtc=$p.StartTime.ToUniversalTime().ToString('o');"
        "Executable=[System.IO.Path]::GetFullPath([string]$p.Path)}|ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def process_exists(process_id: int) -> bool:
    assert POWER_SHELL is not None
    result = subprocess.run(
        [
            POWER_SHELL,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"if(Get-Process -Id {process_id} -ErrorAction SilentlyContinue){{exit 0}}else{{exit 1}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def test_start_script_uses_external_default_and_rejects_repo_runtime_home(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    assert "LOCALAPPDATA" in text
    assert "HMASD\\codex-supervisor" in text
    assert "runtime/hmasd-root-supervisor" not in text
    assert "runtime home must be external to the repository" in text


def test_start_script_records_identity_and_external_launch_evidence(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    for required in ("HMASD_SUPERVISOR_PROCESS_V1", "process_start_time_utc", "executable", "ready_file", "supervisor-launch-evidence.json", "argument_vector", "HMASD_SUPERVISOR_PROCESS_STARTED_V2", "PROCESS_STARTED"):
        assert required in text
    assert "control_home = $ControlHome; ready_file = $ReadyFile" in text


def test_root_supervisor_scripts_parse_in_windows_powershell_51(repo_root):
    for name in (
        "hmasd-root-supervisor-start.ps1",
        "hmasd-root-supervisor-status.ps1",
        "hmasd-root-supervisor-stop.ps1",
    ):
        parse_powershell(script_path(repo_root, name))


def test_start_identity_helper_does_not_bind_the_read_only_pid_automatic_variable(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    assert "function Get-ExactProcessIdentity([int]$ProcessId)" in text
    assert "Get-Process -Id $ProcessId" in text
    assert "Get-ExactProcessIdentity([int]$Pid)" not in text


def test_start_script_requires_valid_ready_evidence_not_pid_only(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    assert "ready.json" in text
    assert "validate_ready_record" in text
    assert "Test-ProcessRecordIdentity" in text
    assert "Start-Sleep -Milliseconds 200" in text
    assert "Start-Sleep -Milliseconds 300" not in text
    assert "AddSeconds(20)" in text
    assert "HMASD_SUPERVISOR_READY_V2" in text
    assert "HMASD_SUPERVISOR_INCIDENT_V2" in text


def test_start_passes_frozen_runtime_arguments_to_serve(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    assert "$arguments += @('serve', '--profile', $ProfileName)" in text
    assert "$arguments += @('--semantic-state', $SemanticPath)" in text
    assert "$arguments += @('--ready-file', $ReadyPath, '--control-home', $ControlPath)" in text


def test_start_argument_helper_uses_bound_duration_without_nullable_members(repo_root):
    path = script_path(repo_root, "hmasd-root-supervisor-start.ps1")
    text = path.read_text(encoding="utf-8")
    assert "$PSBoundParameters.ContainsKey('DurationSeconds')" in text
    assert "[double]$DurationSeconds" in text
    assert ".HasValue" not in text
    assert ".Value" not in text
    body = (
        "$result=@(Get-SupervisorArgumentVector $A1 $A2 'OBSERVER' '' $A3 $A4 '' $true ([double]0.125)); "
        "$result|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        path,
        ("Get-SupervisorArgumentVector",),
        body,
        "C:/repo with space",
        "C:/runtime with space",
        "C:/runtime with space/ready.json",
        "C:/runtime with space/control",
    )
    assert result.returncode == 0, result.stderr + result.stdout
    arguments = json.loads(result.stdout)
    assert arguments[-2:] == ["--duration-seconds", "0.125"]
    assert arguments[arguments.index("--repo-root") + 1] == "C:/repo with space"


def test_windows_powershell_51_argument_serialization_round_trips_real_child_argv(repo_root, tmp_path):
    assert PROJECT_PYTHON.is_file()
    output = tmp_path / "argv output with spaces.json"
    tail = [
        "plain",
        r"C:\path with spaces\leaf",
        'quote"inside',
        "slashes-before-quote\\\"tail",
        "trailing-backslash\\",
        "",
    ]
    body = (
        "$logical=@('-c',$A2,$A5,$A6,$A7,$A8,$A9,$A10); "
        "$serialized=ConvertTo-WindowsCommandLine $logical; "
        "$child=Start-Process -FilePath $A4 -ArgumentList $serialized -RedirectStandardOutput $A3 -NoNewWindow -Wait -PassThru; "
        "if($child.ExitCode -ne 0){exit $child.ExitCode}"
    )
    result = invoke_start_helpers(
        script_path(repo_root, "hmasd-root-supervisor-start.ps1"),
        ("ConvertTo-WindowsCommandLineArgument", "ConvertTo-WindowsCommandLine"),
        body,
        "unused",
        "import json,sys;print(json.dumps(sys.argv[1:]))",
        str(output),
        str(PROJECT_PYTHON),
        *tail,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(output.read_text(encoding="utf-8")) == tail


def test_start_rejects_custom_ready_and_control_paths_before_writing_or_launching(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    ready_guard = "Resolve-ExternalTarget $ReadyFile $RepoRoot 'ready file'"
    control_guard = "Resolve-ExternalTarget $ControlHome $RepoRoot 'control home'"
    control_creation = "New-Item -ItemType Directory -Force -Path $ControlHome"
    assert "function Resolve-ExternalTarget" in text
    assert ready_guard in text
    assert control_guard in text
    assert text.index(ready_guard) < text.index(control_creation)
    assert text.index(control_guard) < text.index(control_creation)
    assert text.index(control_guard) < text.index("Start-Process -FilePath")


def test_start_binds_semantic_state_to_nonobserver_profiles_before_launch(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    semantic_guard = "Resolve-ExternalExistingFile $SemanticState $RepoRoot 'semantic state'"
    launch = "Start-Process -FilePath"
    assert "$PSBoundParameters.ContainsKey('SemanticState')" in text
    assert "OBSERVER profile forbids SemanticState" in text
    assert 'profile requires SemanticState' in text
    assert "must be an existing regular file" in text
    assert semantic_guard in text
    assert text.index(semantic_guard) < text.index(launch)


def test_status_requires_identity_ready_doctor_and_matching_active_run(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-status.ps1")
    for required in ("HMASD_SUPERVISOR_STATUS_V2", "STOPPED", "PROCESS_STARTING", "READY", "STALE_IDENTITY", "INCIDENT", "validate_ready_record", "observer_runs", "ready.run_id", "codex_binary", "schema_capture_present", "static_guard_violations", "Test-ProcessRecordIdentity", "Test-ActiveCodexBinding", "Test-FullyQualifiedPath"):
        assert required in text
    assert "Test-RecordAndLaunchBinding $record $RepoRoot $RuntimeHome" in text


def test_status_strictly_parses_launch_vector_and_binds_python_and_codex(repo_root, tmp_path):
    path = script_path(repo_root, "hmasd-root-supervisor-status.ps1")
    runtime_home = tmp_path / "runtime"
    runtime_home.mkdir()
    ready = runtime_home / "ready.json"
    control = runtime_home / "control"
    codex = "C:/Program Files/Codex/codex.exe"
    vector = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo_root),
        "--runtime-home", str(runtime_home), "--codex-bin", codex, "serve",
        "--profile", "OBSERVER", "--ready-file", str(ready),
        "--control-home", str(control), "--duration-seconds", "2.5",
    ]
    evidence = {
        "schema": "HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2",
        "observed_at": "2026-08-23T00:00:00Z", "argument_vector": vector,
        "control_home": str(control), "ready_file": str(ready),
    }
    evidence_path = runtime_home / "supervisor-launch-evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    record = {
        "schema": "HMASD_SUPERVISOR_PROCESS_V1", "pid": 1234,
        "process_start_time_utc": "2026-08-23T00:00:00.0000000Z",
        "executable": str(PROJECT_PYTHON.resolve()), "repo_root": str(repo_root),
        "runtime_home": str(runtime_home), "profile": "OBSERVER",
        "started_at": "2026-08-23T00:00:00Z", "ready_file": str(ready),
    }
    body = (
        "$record=$A4|ConvertFrom-Json; "
        "$match=Test-RecordAndLaunchBinding $record $A1 $A2 $A5; "
        "$activeMatch=Test-ActiveCodexBinding $A6 ([string]$match.codex_bin) $true $A6; "
        "$wrongLaunch=Test-ActiveCodexBinding $A7 ([string]$match.codex_bin) $false ''; "
        "$wrongCodex=Test-ActiveCodexBinding $A6 ([string]$match.codex_bin) $true 'wrong'; "
        "$wrongPython=Test-RecordAndLaunchBinding $record $A1 $A2 $A7; "
        "$bad=@($A8|ConvertFrom-Json); "
        "[ordered]@{matched=[bool]$match;derived_codex=[string]$match.codex_bin;active_match=[bool]$activeMatch;wrong_launch=[bool]$wrongLaunch;wrong_codex=[bool]$wrongCodex;wrong_python=[bool]$wrongPython;duplicate_parsed=[bool](Parse-StrictLaunchArgumentVector $bad)}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        path,
        ("Test-SamePath", "Test-FullyQualifiedPath", "Test-ExternalExistingFile", "Test-ExactFields", "Parse-StrictLaunchArgumentVector", "Test-RecordAndLaunchBinding", "Test-ActiveCodexBinding"),
        body,
        str(repo_root), str(runtime_home), str(ready), json.dumps(record),
        str(PROJECT_PYTHON.resolve()), codex, str(tmp_path / "other-python.exe"),
        json.dumps(vector + ["--profile", "OBSERVER"]),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == {
        "matched": True,
        "derived_codex": codex,
        "active_match": True,
        "wrong_launch": False,
        "wrong_codex": False,
        "wrong_python": False,
        "duplicate_parsed": False,
    }


def test_status_strict_parser_enforces_profile_semantic_state_relationship(tmp_path):
    path = Path(__file__).resolve().parents[2] / "scripts" / "hmasd-root-supervisor-status.ps1"
    repo = tmp_path / "repo"
    repo.mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    semantic = tmp_path / "semantic.sqlite3"
    semantic.touch()
    resident = repo / "semantic.sqlite3"
    resident.touch()
    common = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo),
        "--runtime-home", str(runtime), "serve", "--profile",
    ]
    tail = ["--ready-file", str(runtime / "ready.json"), "--control-home", str(runtime / "control")]
    valid = common + ["MANAGED_MANUAL", "--semantic-state", str(semantic)] + tail
    missing = common + ["MAILBOX_MANUAL"] + tail
    observer_with_state = common + ["OBSERVER", "--semantic-state", str(semantic)] + tail
    resident_state = common + ["SINGLE_WAKE", "--semantic-state", str(resident)] + tail
    body = (
        "$valid=ConvertFrom-Json -InputObject $A1;$missing=ConvertFrom-Json -InputObject $A2;"
        "$observer=ConvertFrom-Json -InputObject $A3;$resident=ConvertFrom-Json -InputObject $A4;"
        "$parsed=Parse-StrictLaunchArgumentVector $valid;"
        "[ordered]@{valid=[bool]$parsed;semantic=[string]$parsed.semantic_state;"
        "missing=[bool](Parse-StrictLaunchArgumentVector $missing);"
        "observer=[bool](Parse-StrictLaunchArgumentVector $observer);"
        "resident=[bool](Parse-StrictLaunchArgumentVector $resident)}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        path,
        ("Test-FullyQualifiedPath", "Test-ExternalExistingFile", "Parse-StrictLaunchArgumentVector"),
        body,
        json.dumps(valid),
        json.dumps(missing),
        json.dumps(observer_with_state),
        json.dumps(resident_state),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == {
        "valid": True,
        "semantic": str(semantic.resolve()),
        "missing": False,
        "observer": False,
        "resident": False,
    }


def test_status_rejects_relative_codex_paths_before_binding_comparisons(repo_root):
    path = script_path(repo_root, "hmasd-root-supervisor-status.ps1")
    absolute = "C:/Program Files/Codex/codex.exe"
    unc = r"\\server\share\Codex\codex.exe"
    relative_vector = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo_root),
        "--runtime-home", "C:/runtime", "--codex-bin", "codex.exe", "serve",
        "--profile", "OBSERVER", "--ready-file", "C:/runtime/ready.json",
        "--control-home", "C:/runtime/control",
    ]
    body = (
        "$absolute=$A1; $relative='codex.exe'; "
        "$doctor=[pscustomobject]@{status='OK';binary_error=$null;codex_binary=$relative;"
        "codex_version='codex-test';schema_capture_present=$true;static_guard_violations=@();"
        "direct_state_write_violations=0;direct_mutation_call_violations=0;new_legacy_mutation_writes=0}; "
        "$vector=@($A3|ConvertFrom-Json); "
        "[ordered]@{drive_absolute=(Test-FullyQualifiedPath $absolute);"
        "unc_absolute=(Test-FullyQualifiedPath $A2);relative=(Test-FullyQualifiedPath $relative);"
        "rooted_current_drive=(Test-FullyQualifiedPath '\\Codex\\codex.exe');"
        "drive_relative=(Test-FullyQualifiedPath 'C:codex.exe');"
        "active_relative=(Test-ActiveCodexBinding $relative $absolute $false '');"
        "launch_relative=(Test-ActiveCodexBinding $absolute $relative $false '');"
        "caller_relative=(Test-ActiveCodexBinding $absolute '' $true $relative);"
        "doctor_relative=(Test-DoctorGuards $doctor $absolute);"
        "parsed_relative_launch=[bool](Parse-StrictLaunchArgumentVector $vector)}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        path,
        (
            "Test-SamePath", "Test-FullyQualifiedPath", "Test-ExternalExistingFile", "Parse-StrictLaunchArgumentVector",
            "Test-ActiveCodexBinding", "Test-DoctorGuards",
        ),
        body,
        absolute,
        unc,
        json.dumps(relative_vector),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == {
        "drive_absolute": True,
        "unc_absolute": True,
        "relative": False,
        "rooted_current_drive": False,
        "drive_relative": False,
        "active_relative": False,
        "launch_relative": False,
        "caller_relative": False,
        "doctor_relative": False,
        "parsed_relative_launch": False,
    }


def test_status_uses_active_run_binary_when_default_launch_and_environment_change(repo_root, tmp_path):
    assert POWER_SHELL is not None
    assert PROJECT_PYTHON.is_file()
    active_dir = tmp_path / "active codex"
    active_dir.mkdir()
    active_codex = write_fake_codex(active_dir).resolve()
    caller_dir = tmp_path / "caller codex"
    caller_dir.mkdir()
    caller_marker = caller_dir / "caller-invoked.txt"
    caller_codex = caller_dir / "codex.cmd"
    caller_codex.write_text(
        f'@echo off\r\necho invoked>"{caller_marker}"\r\necho codex-caller 0.0-test\r\n',
        encoding="utf-8",
    )
    sleeper = subprocess.Popen(
        [str(PROJECT_PYTHON), "-c", "import time; time.sleep(30)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        identity = process_identity(sleeper.pid)
        with tempfile.TemporaryDirectory(prefix="hmasd-status-active-binary-") as external:
            runtime_home = Path(external).resolve()
            ready_path = runtime_home / "ready.json"
            control_home = runtime_home / "control"
            run_id = "run-active-binary"
            initialized_at = "2026-08-23T00:00:00Z"
            process_record = {
                "schema": "HMASD_SUPERVISOR_PROCESS_V1",
                "pid": sleeper.pid,
                "process_start_time_utc": identity["StartTimeUtc"],
                "executable": identity["Executable"],
                "repo_root": str(repo_root.resolve()),
                "runtime_home": str(runtime_home),
                "profile": "OBSERVER",
                "started_at": initialized_at,
                "ready_file": str(ready_path),
            }
            (runtime_home / "supervisor-process.json").write_text(
                json.dumps(process_record), encoding="utf-8"
            )
            ready_path.write_text(
                json.dumps(
                    {
                        "schema": "HMASD_SUPERVISOR_READY_V2",
                        "run_id": run_id,
                        "process_id": sleeper.pid,
                        "initialized_at": initialized_at,
                        "watcher_active": True,
                        "first_reconciliation_completed": True,
                        "thread_count": 0,
                        "runtime_home": str(runtime_home),
                        "profile": "OBSERVER",
                    }
                ),
                encoding="utf-8",
            )
            (runtime_home / "supervisor-launch-evidence.json").write_text(
                json.dumps(
                    {
                        "schema": "HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2",
                        "observed_at": initialized_at,
                        "argument_vector": [
                            "-m", "tools.codex_supervisor", "--repo-root", str(repo_root.resolve()),
                            "--runtime-home", str(runtime_home), "serve", "--profile", "OBSERVER",
                            "--ready-file", str(ready_path), "--control-home", str(control_home),
                        ],
                        "control_home": str(control_home),
                        "ready_file": str(ready_path),
                    }
                ),
                encoding="utf-8",
            )
            connection = connect(runtime_home / "state.sqlite3")
            initialize_database(connection)
            with connection:
                connection.execute(
                    """INSERT INTO observer_runs(
                        run_id, codex_binary, codex_version, client_name, process_id,
                        started_at, initialized_at, ended_at, runtime_home
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)""",
                    (
                        run_id,
                        str(active_codex),
                        "codex-fake 0.0-test",
                        "status-test",
                        sleeper.pid,
                        initialized_at,
                        initialized_at,
                        str(runtime_home),
                    ),
                )
            connection.close()
            manifest = runtime_home / "schema" / "fixture" / "capture-manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text("{}", encoding="utf-8")

            active_result = invoke_start_helpers(
                script_path(repo_root, "hmasd-root-supervisor-status.ps1"),
                ("Test-ReadyAndActiveRun",),
                "$PythonPath=$A5; Test-ReadyAndActiveRun $A1 $A2 $A3 $A4 | ConvertTo-Json -Compress",
                str(runtime_home / "supervisor-process.json"),
                str(ready_path),
                str(runtime_home),
                str(repo_root),
                str(PROJECT_PYTHON),
            )
            assert active_result.returncode == 0, active_result.stderr + active_result.stdout
            active_payload = json.loads(active_result.stdout)
            assert active_payload["codex_binary"] == str(active_codex), active_payload

            environment = os.environ.copy()
            environment["CODEX_BIN"] = str(caller_codex)
            command = [
                POWER_SHELL, "-NoProfile", "-NonInteractive", "-File",
                str(script_path(repo_root, "hmasd-root-supervisor-status.ps1")),
                "-RepoRoot", str(repo_root), "-RuntimeHome", str(runtime_home),
                "-PythonPath", str(PROJECT_PYTHON),
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=False, env=environment)
            assert result.returncode == 0, result.stderr + result.stdout
            payload = json.loads(result.stdout)
            assert payload["state"] == "READY", result.stderr + json.dumps(payload, indent=2)
            assert Path(payload["ready"]["codex_binary"]).resolve() == active_codex
            assert Path(payload["doctor"]["codex_binary"]).resolve() == active_codex
            assert not caller_marker.exists()

            mismatch = subprocess.run(
                command + ["-CodexBin", str(caller_codex)],
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
            assert mismatch.returncode == 0, mismatch.stderr + mismatch.stdout
            mismatch_payload = json.loads(mismatch.stdout)
            assert mismatch_payload["state"] == "INCIDENT"
            assert mismatch_payload["doctor"] is None
            assert not caller_marker.exists()
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)


def test_existing_host_binding_rejects_another_repo_or_control_path(repo_root, tmp_path):
    path = script_path(repo_root, "hmasd-root-supervisor-start.ps1")
    runtime_home = tmp_path / "runtime"
    runtime_home.mkdir()
    ready = runtime_home / "ready.json"
    control = runtime_home / "control"
    evidence = {
        "schema": "HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2",
        "observed_at": "2026-08-23T00:00:00Z",
        "argument_vector": [
            "-m",
            "tools.codex_supervisor",
            "--repo-root",
            str(repo_root),
            "--runtime-home",
            str(runtime_home),
            "serve",
            "--profile",
            "OBSERVER",
            "--ready-file",
            str(ready),
            "--control-home",
            str(control),
        ],
        "control_home": str(control),
        "ready_file": str(ready),
    }
    (runtime_home / "supervisor-launch-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    record = {
        "schema": "HMASD_SUPERVISOR_PROCESS_V1",
        "pid": 1234,
        "process_start_time_utc": "2026-08-23T00:00:00.0000000Z",
        "executable": str(PROJECT_PYTHON.resolve()),
        "repo_root": str(repo_root),
        "runtime_home": str(runtime_home),
        "profile": "OBSERVER",
        "started_at": "2026-08-23T00:00:00Z",
        "ready_file": str(ready),
    }
    body = (
        "$record=$A5|ConvertFrom-Json; "
        "$expected=@(Get-SupervisorArgumentVector $A1 $A2 'OBSERVER' '' $A3 $A4 '' $false 0); "
        "$matched=Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $expected; "
        "$wrongControl=Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A6 $A7 $expected; "
        "$wrongRepo=Test-ExistingInvocation $record $A6 $A2 'OBSERVER' $A3 $A4 $A7 $expected; "
        "[ordered]@{matched=$matched;wrong_control=$wrongControl;wrong_repo=$wrongRepo}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        path,
        (
            "Test-SamePath",
            "Test-ExactFields",
            "Test-ExactArgumentVector",
            "Get-SupervisorArgumentVector",
            "Test-LaunchEvidenceBinding",
            "Test-ExistingInvocation",
        ),
        body,
        str(repo_root),
        str(runtime_home),
        str(ready),
        str(control),
        json.dumps(record),
        str(tmp_path / "different"),
        str(PROJECT_PYTHON.resolve()),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == {"matched": True, "wrong_control": False, "wrong_repo": False}


def test_existing_host_binding_requires_exact_semantic_state_vector(repo_root, tmp_path):
    path = script_path(repo_root, "hmasd-root-supervisor-start.ps1")
    runtime_home = tmp_path / "runtime"
    runtime_home.mkdir()
    ready = runtime_home / "ready.json"
    control = runtime_home / "control"
    semantic = tmp_path / "semantic.sqlite3"
    other_semantic = tmp_path / "other-semantic.sqlite3"
    semantic.touch()
    other_semantic.touch()
    expected = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo_root),
        "--runtime-home", str(runtime_home), "serve", "--profile", "MANAGED_MANUAL",
        "--semantic-state", str(semantic), "--ready-file", str(ready),
        "--control-home", str(control),
    ]
    evidence_path = runtime_home / "supervisor-launch-evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
                "schema": "HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2",
                "observed_at": "2026-08-23T00:00:00Z",
                "argument_vector": expected,
                "control_home": str(control),
                "ready_file": str(ready),
            }
        ),
        encoding="utf-8",
    )
    record = {
        "schema": "HMASD_SUPERVISOR_PROCESS_V1", "pid": 1234,
        "process_start_time_utc": "2026-08-23T00:00:00.0000000Z",
        "executable": str(PROJECT_PYTHON.resolve()), "repo_root": str(repo_root),
        "runtime_home": str(runtime_home), "profile": "MANAGED_MANUAL",
        "started_at": "2026-08-23T00:00:00Z", "ready_file": str(ready),
    }
    body = (
        "$record=$A5|ConvertFrom-Json;"
        "$expected=@(Get-SupervisorArgumentVector $A1 $A2 'MANAGED_MANUAL' $A3 $A6 $A7 '' $false 0);"
        "$other=@(Get-SupervisorArgumentVector $A1 $A2 'MANAGED_MANUAL' $A4 $A6 $A7 '' $false 0);"
        "[ordered]@{matched=(Test-ExistingInvocation $record $A1 $A2 'MANAGED_MANUAL' $A6 $A7 $A8 $expected);"
        "other=(Test-ExistingInvocation $record $A1 $A2 'MANAGED_MANUAL' $A6 $A7 $A8 $other)}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        path,
        (
            "Test-SamePath", "Test-ExactFields", "Test-ExactArgumentVector",
            "Get-SupervisorArgumentVector", "Test-LaunchEvidenceBinding",
            "Test-ExistingInvocation",
        ),
        body,
        str(repo_root),
        str(runtime_home),
        str(semantic),
        str(other_semantic),
        json.dumps(record),
        str(ready),
        str(control),
        str(PROJECT_PYTHON.resolve()),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == {"matched": True, "other": False}


def test_existing_host_binding_requires_exact_codex_and_duration_vector(repo_root, tmp_path):
    path = script_path(repo_root, "hmasd-root-supervisor-start.ps1")
    runtime_home = tmp_path / "runtime"
    runtime_home.mkdir()
    ready = runtime_home / "ready.json"
    control = runtime_home / "control"
    codex = "C:/Program Files/Codex/codex.exe"
    bounded = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo_root),
        "--runtime-home", str(runtime_home), "--codex-bin", codex, "serve",
        "--profile", "OBSERVER", "--ready-file", str(ready),
        "--control-home", str(control), "--duration-seconds", "0.125",
    ]
    evidence = {
        "schema": "HMASD_SUPERVISOR_LAUNCH_EVIDENCE_V2",
        "observed_at": "2026-08-23T00:00:00Z",
        "argument_vector": bounded,
        "control_home": str(control),
        "ready_file": str(ready),
    }
    (runtime_home / "supervisor-launch-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    record = {
        "schema": "HMASD_SUPERVISOR_PROCESS_V1", "pid": 1234,
        "process_start_time_utc": "2026-08-23T00:00:00.0000000Z",
        "repo_root": str(repo_root), "runtime_home": str(runtime_home), "profile": "OBSERVER",
        "started_at": "2026-08-23T00:00:00Z", "ready_file": str(ready),
        "executable": str(PROJECT_PYTHON.resolve()),
    }
    body = (
        "$record=$A5|ConvertFrom-Json; "
        "$bounded=@(Get-SupervisorArgumentVector $A1 $A2 'OBSERVER' '' $A3 $A4 $A6 $true 0.125); "
        "$unbounded=@(Get-SupervisorArgumentVector $A1 $A2 'OBSERVER' '' $A3 $A4 $A6 $false 0); "
        "$wrongCodex=@(Get-SupervisorArgumentVector $A1 $A2 'OBSERVER' '' $A3 $A4 'other-codex' $true 0.125); "
        "$duplicate=@($bounded + @('--profile','OBSERVER')); "
        "[ordered]@{bounded=(Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $bounded); "
        "unbounded=(Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $unbounded); "
        "wrong_codex=(Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $wrongCodex); "
        "duplicate=(Test-LaunchEvidenceBinding $A8 $duplicate $A3 $A4)}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        path,
        ("Test-SamePath", "Test-ExactFields", "Test-ExactArgumentVector", "Get-SupervisorArgumentVector", "Test-LaunchEvidenceBinding", "Test-ExistingInvocation"),
        body,
        str(repo_root), str(runtime_home), str(ready), str(control), json.dumps(record), codex,
        str(PROJECT_PYTHON.resolve()), str(runtime_home / "supervisor-launch-evidence.json"),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == {"bounded": True, "unbounded": False, "wrong_codex": False, "duplicate": False}


def test_start_ready_validation_requires_initialized_unended_run_in_same_runtime(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-start.ps1")
    assert "SELECT initialized_at, ended_at, runtime_home FROM observer_runs WHERE run_id = ?" in text
    assert "active and same_home" in text
    assert "Archive-SignalFile $RuntimeHome $ReadyFile 'ready-prelaunch'" in text


def test_stop_refuses_pid_reuse_or_executable_identity_mismatch(repo_root):
    text = read_script(repo_root, "hmasd-root-supervisor-stop.ps1")
    assert "process_start_time_utc" in text
    assert "record.executable" in text
    assert "PID reuse or executable/start-time identity mismatch" in text
    assert "process was left untouched" in text
    assert "HMASD_SUPERVISOR_INCIDENT_V2" in text
    assert "taskkill.exe" in text
    assert "Clear-StoppedSignals" in text
    assert "$taskkillExitCode -eq 0 -and $remaining.Count -eq 0" in text
    assert "known descendant identities remain unverified" in text
    assert text.index("Get-ProcessTreeSnapshot $expectedParent") < text.index("Stop-ProcessTreeFromSnapshot $snapshot $expectedParent")


def test_stop_tree_helper_treats_nonzero_taskkill_as_failure_without_killing(repo_root):
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    sleeper = subprocess.Popen(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 30"]
    )
    try:
        identity = process_identity(sleeper.pid)
        body = (
            "$identity=$A1|ConvertFrom-Json; $snapshot=Get-ProcessTreeSnapshot $identity; "
            "function Invoke-TaskkillTree([int]$ProcessId){return 7}; "
            "Stop-ProcessTreeFromSnapshot $snapshot $identity|ConvertTo-Json -Compress"
        )
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-stop.ps1"),
            (
                "Test-SamePath", "Get-ExactProcessIdentity", "Test-IdentityMatches",
                "Get-ProcessTreeSnapshot", "Test-ProcessIdentitiesSafeToTerminate",
                "Get-MatchingProcessIdentities", "Invoke-TaskkillTree", "Stop-ProcessTreeFromSnapshot",
            ),
            body,
            json.dumps(identity),
        )
        assert result.returncode == 0, result.stderr + result.stdout
        cleanup = json.loads(result.stdout)
        assert cleanup["cleanup_succeeded"] is False
        assert cleanup["taskkill_exit_code"] == 7
        assert cleanup["action"] == "TASKKILL_FAILED_SIGNALS_RETAINED"
        assert sleeper.poll() is None
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)


def test_failed_launch_cleanup_kills_only_matching_inert_process_and_clears_signals(repo_root, tmp_path):
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    sleeper = subprocess.Popen(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 30"]
    )
    try:
        identity = process_identity(sleeper.pid)
        runtime_home = tmp_path / "runtime"
        runtime_home.mkdir()
        ready = runtime_home / "ready.json"
        process_record = runtime_home / "supervisor-process.json"
        started = runtime_home / "supervisor-process-started.json"
        for signal in (ready, process_record, started):
            signal.write_text("{}", encoding="utf-8")
        body = (
            "$identity=$A1|ConvertFrom-Json; "
            "$result=Complete-FailedLaunchCleanup $A2 $identity $A3 $A4 'fixture timeout'; "
            "$result|ConvertTo-Json -Depth 8 -Compress"
        )
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-start.ps1"),
            (
                "Write-AtomicJson",
                "Test-SamePath",
                "Get-ExactProcessIdentity",
                "Test-IdentityMatches",
                "Get-ProcessTreeSnapshot",
                "Test-ProcessIdentitiesSafeToTerminate",
                "Get-MatchingProcessIdentities",
                "Invoke-TaskkillTree",
                "Archive-SignalFile",
                "Stop-LaunchedProcessTreeIdentityChecked",
                "Complete-FailedLaunchCleanup",
            ),
            body,
            json.dumps(identity),
            str(runtime_home),
            str(process_record),
            str(ready),
        )
        assert result.returncode == 0, result.stderr + result.stdout
        cleanup = json.loads(result.stdout)
        assert cleanup["identity_matched"] is True
        assert cleanup["cleanup_succeeded"] is True
        assert cleanup["reason"] == "fixture timeout"
        sleeper.wait(timeout=5)
        assert not ready.exists()
        assert not process_record.exists()
        assert not started.exists()
        assert len(list((runtime_home / "archive").glob("*.json"))) == 3
        persisted = json.loads((runtime_home / "supervisor-start-cleanup.json").read_text(encoding="utf-8"))
        assert persisted["cleanup_succeeded"] is True
    finally:
        if sleeper.poll() is None:
            sleeper.terminate()
            sleeper.wait(timeout=5)


def test_failed_launch_cleanup_leaves_mismatched_inert_process_untouched(repo_root):
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    sleeper = subprocess.Popen(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 30"]
    )
    try:
        identity = process_identity(sleeper.pid)
        identity["StartTimeUtc"] = "2000-01-01T00:00:00.0000000Z"
        body = "$identity=$A1|ConvertFrom-Json; Stop-LaunchedProcessTreeIdentityChecked $identity|ConvertTo-Json -Compress"
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-start.ps1"),
            (
                "Test-SamePath",
                "Get-ExactProcessIdentity",
                "Test-IdentityMatches",
                "Get-ProcessTreeSnapshot",
                "Test-ProcessIdentitiesSafeToTerminate",
                "Get-MatchingProcessIdentities",
                "Invoke-TaskkillTree",
                "Stop-LaunchedProcessTreeIdentityChecked",
            ),
            body,
            json.dumps(identity),
        )
        assert result.returncode == 0, result.stderr + result.stdout
        cleanup = json.loads(result.stdout)
        assert cleanup["identity_matched"] is False
        assert cleanup["cleanup_attempted"] is False
        assert sleeper.poll() is None
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)


def test_failed_launch_cleanup_nonzero_taskkill_retains_process_and_fails(repo_root):
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    sleeper = subprocess.Popen(
        [POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", "Start-Sleep -Seconds 30"]
    )
    try:
        identity = process_identity(sleeper.pid)
        body = (
            "function Invoke-TaskkillTree([int]$ProcessId){return 9}; "
            "$identity=$A1|ConvertFrom-Json; Stop-LaunchedProcessTreeIdentityChecked $identity|ConvertTo-Json -Compress"
        )
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-start.ps1"),
            (
                "Test-SamePath", "Get-ExactProcessIdentity", "Test-IdentityMatches",
                "Get-ProcessTreeSnapshot", "Test-ProcessIdentitiesSafeToTerminate",
                "Get-MatchingProcessIdentities", "Invoke-TaskkillTree",
                "Stop-LaunchedProcessTreeIdentityChecked",
            ),
            body,
            json.dumps(identity),
        )
        assert result.returncode == 0, result.stderr + result.stdout
        cleanup = json.loads(result.stdout)
        assert cleanup["cleanup_succeeded"] is False
        assert cleanup["taskkill_exit_code"] == 9
        assert cleanup["action"] == "TASKKILL_FAILED_SIGNALS_RETAINED"
        assert sleeper.poll() is None
    finally:
        sleeper.terminate()
        sleeper.wait(timeout=5)


def test_failed_launch_cleanup_snapshots_and_confirms_recursive_inert_tree(repo_root, tmp_path):
    if POWER_SHELL is None:
        pytest.skip("Windows PowerShell is unavailable")
    child_pid_file = tmp_path / "child pid.txt"
    escaped_child_pid_file = str(child_pid_file).replace("'", "''")
    command = (
        "$child=Start-Process -FilePath powershell.exe -ArgumentList "
        "'-NoProfile -NonInteractive -Command \"Start-Sleep -Seconds 30\"' -PassThru; "
        f"[System.IO.File]::WriteAllText('{escaped_child_pid_file}',[string]$child.Id); "
        "Wait-Process -Id $child.Id"
    )
    parent = subprocess.Popen([POWER_SHELL, "-NoProfile", "-NonInteractive", "-Command", command])
    child_pid: int | None = None
    try:
        for _ in range(100):
            if child_pid_file.is_file() and child_pid_file.read_text(encoding="utf-8").strip():
                child_pid = int(child_pid_file.read_text(encoding="utf-8").strip())
                break
            time.sleep(0.05)
        assert child_pid is not None
        identity = process_identity(parent.pid)
        body = "$identity=$A1|ConvertFrom-Json; Stop-LaunchedProcessTreeIdentityChecked $identity|ConvertTo-Json -Compress"
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-start.ps1"),
            (
                "Test-SamePath", "Get-ExactProcessIdentity", "Test-IdentityMatches",
                "Get-ProcessTreeSnapshot", "Test-ProcessIdentitiesSafeToTerminate",
                "Get-MatchingProcessIdentities", "Invoke-TaskkillTree",
                "Stop-LaunchedProcessTreeIdentityChecked",
            ),
            body,
            json.dumps(identity),
        )
        assert result.returncode == 0, result.stderr + result.stdout
        cleanup = json.loads(result.stdout)
        assert cleanup["cleanup_succeeded"] is True
        assert cleanup["descendant_count"] >= 1
        parent.wait(timeout=5)
        assert not process_exists(child_pid)
    finally:
        if child_pid is not None and process_exists(child_pid):
            subprocess.run(["taskkill.exe", "/PID", str(child_pid), "/T", "/F"], check=False, capture_output=True)
        if parent.poll() is None:
            parent.terminate()
            parent.wait(timeout=5)


def test_all_wrappers_resolve_and_fail_closed_for_repo_resident_runtime_home(repo_root):
    for name in (
        "hmasd-root-supervisor-start.ps1",
        "hmasd-root-supervisor-status.ps1",
        "hmasd-root-supervisor-stop.ps1",
    ):
        text = read_script(repo_root, name)
        assert "GetFullPath" in text
        assert "runtime home must be external to the repository" in text
