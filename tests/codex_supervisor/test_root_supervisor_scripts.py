from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

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


def terminate_inert_tree(process: subprocess.Popen[bytes] | subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    subprocess.run(
        ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
        capture_output=True,
        check=False,
    )
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def spawn_inert_supervisor_shape(
    fixture_root: Path,
    logical_vector: list[str],
    *,
    codex_kind: str = "exe",
    child_mode: str = "valid",
    codex_path: Path | None = None,
) -> tuple[subprocess.Popen[bytes], int, Path]:
    """Start only inert Python fixtures with the production host/child argv shape."""

    package = fixture_root / "tools" / "codex_supervisor"
    package.mkdir(parents=True)
    (fixture_root / "tools" / "__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (fixture_root / "app-server").write_text(
        "import time\ntime.sleep(60)\n", encoding="utf-8"
    )
    pid_file = fixture_root / "child-pid.json"
    if codex_path is not None:
        codex = codex_path.resolve()
    elif codex_kind == "cmd":
        codex = fixture_root / "codex app shim.cmd"
        codex.write_text(
            f'@echo off\r\n"{PROJECT_PYTHON.resolve()}" app-server\r\n',
            encoding="utf-8",
        )
    else:
        codex = PROJECT_PYTHON.resolve()
    module = (
        "import json,os,subprocess,time\n"
        "from pathlib import Path\n"
        "codex=os.environ['HMASD_INERT_CODEX']\n"
        "mode=os.environ['HMASD_INERT_CHILD_MODE']\n"
        "if mode == 'wrong-command':\n"
        "    argv=[os.environ['HMASD_INERT_PYTHON'],'-c','import time;time.sleep(60)']\n"
        "elif Path(codex).suffix.lower() in {'.cmd','.bat'}:\n"
        "    argv=[os.environ.get('COMSPEC') or 'cmd.exe','/d','/s','/c','call',codex,'app-server']\n"
        "else:\n"
        "    argv=[codex,'app-server']\n"
        "child=subprocess.Popen(argv, cwd=os.getcwd())\n"
        "Path(os.environ['HMASD_INERT_PID_FILE']).write_text(json.dumps({'pid':child.pid}))\n"
        "time.sleep(60)\n"
    )
    (package / "__main__.py").write_text(module, encoding="utf-8")
    environment = os.environ.copy()
    environment.update(
        {
            "HMASD_INERT_CODEX": str(codex),
            "HMASD_INERT_CHILD_MODE": child_mode,
            "HMASD_INERT_PYTHON": str(PROJECT_PYTHON.resolve()),
            "HMASD_INERT_PID_FILE": str(pid_file),
        }
    )
    host = subprocess.Popen(
        [str(PROJECT_PYTHON.resolve()), *logical_vector],
        cwd=fixture_root,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        if pid_file.is_file():
            child_id = int(json.loads(pid_file.read_text(encoding="utf-8"))["pid"])
            if process_exists(child_id):
                return host, child_id, codex.resolve()
        if host.poll() is not None:
            break
        time.sleep(0.05)
    terminate_inert_tree(host)
    raise AssertionError("inert supervisor-shape fixture did not publish a live child")


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
    assert "AddSeconds($startupReadyTimeoutSeconds)" in text
    assert "startup_ready_timeout_seconds" in text
    assert "AddSeconds(20)" not in text
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
    for required in ("HMASD_SUPERVISOR_STATUS_V2", "STOPPED", "PROCESS_STARTING", "READY", "STALE_IDENTITY", "INCIDENT", "validate_ready_record", "observer_runs", "ready.run_id", "codex_binary", "process_id", "schema_capture_present", "static_guard_violations", "Test-ProcessRecordIdentity", "Test-SupervisorHostProcessBinding", "Test-AppServerProcessBinding", "Test-ActiveCodexBinding", "Test-FullyQualifiedPath"):
        assert required in text
    assert "Test-RecordAndLaunchBinding $record $RepoRoot $RuntimeHome" in text


def test_status_binds_real_inert_host_and_exe_child_process_truth(repo_root, tmp_path):
    vector = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo_root.resolve()),
        "--runtime-home", str((tmp_path / "runtime").resolve()), "serve",
        "--profile", "OBSERVER", "--ready-file", str((tmp_path / "ready.json").resolve()),
        "--control-home", str((tmp_path / "control").resolve()),
    ]
    host, child_id, active_codex = spawn_inert_supervisor_shape(
        tmp_path / "host-exe", vector
    )
    unrelated = subprocess.Popen(
        [str(PROJECT_PYTHON), "-c", "import time;time.sleep(60)"],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    dead = subprocess.Popen(
        [str(PROJECT_PYTHON), "-c", "import time;time.sleep(60)"],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    dead_id = dead.pid
    dead.terminate()
    dead.wait(timeout=5)
    try:
        record = process_identity(host.pid)
        record["pid"] = record.pop("Pid")
        record["process_start_time_utc"] = record.pop("StartTimeUtc")
        record["executable"] = record.pop("Executable")
        initialized = datetime.now(timezone.utc).isoformat()
        body = (
            "$record=$A1|ConvertFrom-Json;$vector=ConvertFrom-Json -InputObject $A2;"
            "[ordered]@{host=(Test-SupervisorHostProcessBinding $record $A3 $vector);"
            "child=(Test-AppServerProcessBinding ([int]$A4) $record $A3 $A5);"
            "missing=(Test-AppServerProcessBinding 2147483000 $record $A3 $A5);"
            "dead=(Test-AppServerProcessBinding ([int]$A7) $record $A3 $A5);"
            "wrong_parent=(Test-AppServerProcessBinding ([int]$A6) $record $A3 $A5)}|ConvertTo-Json -Compress"
        )
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-status.ps1"),
            (
                "Test-SamePath", "Resolve-CanonicalExecutable",
                "Test-SafeCmdBatchPath", "Test-ExactCmdAppServerVector",
                "ConvertFrom-WindowsCommandLine", "Get-ObservedProcessFacts",
                "Test-ExactObservedProcessVector", "Test-SupervisorHostProcessBinding",
                "Test-AppServerProcessBinding",
            ),
            body,
            json.dumps(record), json.dumps(vector), str(PROJECT_PYTHON.resolve()),
            str(child_id), initialized, str(unrelated.pid), str(dead_id),
        )
        assert result.returncode == 0, result.stderr + result.stdout
        assert json.loads(result.stdout) == {
            "host": True,
            "child": True,
            "missing": False,
            "dead": False,
            "wrong_parent": False,
        }
        wrong_codex = tmp_path / "other-codex.cmd"
        wrong_codex.write_text("@echo off\r\n", encoding="utf-8")
        ready_facts = {
            "valid_ready": True,
            "active_observer_run": True,
            "codex_binary": str(active_codex),
            "app_server_process_id": child_id,
            "initialized_at": initialized,
        }
        start_result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-start.ps1"),
            (
                "Test-SamePath", "Resolve-CanonicalExecutable",
                "Test-SafeCmdBatchPath", "Test-ExactCmdAppServerVector",
                "ConvertFrom-WindowsCommandLine", "Get-ObservedProcessFacts",
                "Test-ExactObservedProcessVector", "Test-AppServerProcessBinding",
                "Test-ReadyProcessTruth",
            ),
            (
                "$ready=$A1|ConvertFrom-Json;$record=$A2|ConvertFrom-Json;"
                "[ordered]@{explicit_match=(Test-ReadyProcessTruth $ready $record $A3 $true);"
                "explicit_drift=(Test-ReadyProcessTruth $ready $record $A4 $true);"
                "default_binding=(Test-ReadyProcessTruth $ready $record '' $false)}|ConvertTo-Json -Compress"
            ),
            json.dumps(ready_facts), json.dumps(record), str(active_codex),
            str(wrong_codex.resolve()),
        )
        assert start_result.returncode == 0, start_result.stderr + start_result.stdout
        assert json.loads(start_result.stdout) == {
            "explicit_match": True,
            "explicit_drift": False,
            "default_binding": True,
        }
    finally:
        terminate_inert_tree(host)
        terminate_inert_tree(unrelated)


def test_status_rejects_fabricated_host_and_wrong_child_command_line(repo_root, tmp_path):
    vector = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo_root.resolve()),
        "--runtime-home", str((tmp_path / "runtime").resolve()), "serve",
        "--profile", "OBSERVER", "--ready-file", str((tmp_path / "ready.json").resolve()),
        "--control-home", str((tmp_path / "control").resolve()),
    ]
    host, child_id, active_codex = spawn_inert_supervisor_shape(
        tmp_path / "wrong-command-host", vector, child_mode="wrong-command"
    )
    wrong_launcher = tmp_path / "wrong-launcher.cmd"
    wrong_launcher.write_text("@echo off\r\n", encoding="utf-8")
    sleeper = subprocess.Popen(
        [str(PROJECT_PYTHON), "-c", "import time;time.sleep(60)"],
        cwd=tmp_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        host_record = process_identity(host.pid)
        host_record = {
            "pid": host_record["Pid"],
            "process_start_time_utc": host_record["StartTimeUtc"],
            "executable": host_record["Executable"],
        }
        sleeper_record = process_identity(sleeper.pid)
        sleeper_record = {
            "pid": sleeper_record["Pid"],
            "process_start_time_utc": sleeper_record["StartTimeUtc"],
            "executable": sleeper_record["Executable"],
        }
        initialized = datetime.now(timezone.utc).isoformat()
        body = (
            "$host=$A1|ConvertFrom-Json;$sleeper=$A2|ConvertFrom-Json;$vector=ConvertFrom-Json -InputObject $A3;"
            "[ordered]@{fabricated_host=(Test-SupervisorHostProcessBinding $sleeper $A4 $vector);"
            "wrong_child_command=(Test-AppServerProcessBinding ([int]$A5) $host $A4 $A6);"
            "wrong_launcher=(Test-AppServerProcessBinding ([int]$A5) $host $A7 $A6)}|ConvertTo-Json -Compress"
        )
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-status.ps1"),
            (
                "Test-SamePath", "Resolve-CanonicalExecutable",
                "Test-SafeCmdBatchPath", "Test-ExactCmdAppServerVector",
                "ConvertFrom-WindowsCommandLine", "Get-ObservedProcessFacts",
                "Test-ExactObservedProcessVector", "Test-SupervisorHostProcessBinding",
                "Test-AppServerProcessBinding",
            ),
            body,
            json.dumps(host_record), json.dumps(sleeper_record), json.dumps(vector),
            str(PROJECT_PYTHON.resolve()), str(child_id), initialized,
            str(wrong_launcher.resolve()),
        )
        assert result.returncode == 0, result.stderr + result.stdout
        assert json.loads(result.stdout) == {
            "fabricated_host": False,
            "wrong_child_command": False,
            "wrong_launcher": False,
        }
    finally:
        terminate_inert_tree(host)
        terminate_inert_tree(sleeper)


def test_status_accepts_exact_cmd_comspec_app_server_child_with_spaced_path(repo_root, tmp_path):
    fixture_root = tmp_path / "host directory (ordinary) with spaces"
    codex = (fixture_root / "codex app shim.cmd").resolve()
    vector = [
        "-m", "tools.codex_supervisor", "--repo-root", str(repo_root.resolve()),
        "--runtime-home", str((tmp_path / "runtime").resolve()),
        "--codex-bin", str(codex), "serve", "--profile", "OBSERVER",
        "--ready-file", str((tmp_path / "ready.json").resolve()),
        "--control-home", str((tmp_path / "control").resolve()),
    ]
    host, child_id, active_codex = spawn_inert_supervisor_shape(
        fixture_root, vector, codex_kind="cmd"
    )
    try:
        raw = process_identity(host.pid)
        record = {
            "pid": raw["Pid"],
            "process_start_time_utc": raw["StartTimeUtc"],
            "executable": raw["Executable"],
        }
        initialized = datetime.now(timezone.utc).isoformat()
        body = (
            "$record=$A1|ConvertFrom-Json;$vector=ConvertFrom-Json -InputObject $A2;"
            "[ordered]@{host=(Test-SupervisorHostProcessBinding $record $A3 $vector);"
            "child=(Test-AppServerProcessBinding ([int]$A4) $record $A5 $A6)}|ConvertTo-Json -Compress"
        )
        result = invoke_start_helpers(
            script_path(repo_root, "hmasd-root-supervisor-status.ps1"),
            (
                "Test-SamePath", "Resolve-CanonicalExecutable",
                "Test-SafeCmdBatchPath", "Test-ExactCmdAppServerVector",
                "ConvertFrom-WindowsCommandLine", "Get-ObservedProcessFacts",
                "Test-ExactObservedProcessVector", "Test-SupervisorHostProcessBinding",
                "Test-AppServerProcessBinding",
            ),
            body,
            json.dumps(record), json.dumps(vector), str(PROJECT_PYTHON.resolve()),
            str(child_id), str(active_codex), initialized,
        )
        assert result.returncode == 0, result.stderr + result.stdout
        assert json.loads(result.stdout) == {"host": True, "child": True}
    finally:
        terminate_inert_tree(host)


def test_status_rejects_combined_quoted_or_extra_cmd_app_server_shapes(repo_root, tmp_path):
    command_processor = Path(os.environ.get("COMSPEC") or "C:/Windows/System32/cmd.exe").resolve()
    batch = (tmp_path / "batch path with spaces" / "codex app shim.cmd").resolve()
    batch.parent.mkdir(parents=True)
    batch.write_text("@echo off\r\n", encoding="utf-8")
    body = (
        "$valid=@($A1,'/d','/s','/c','call',$A2,'app-server');"
        "$combined=@($A1,'/d','/s','/c',('call \"'+$A2+'\" app-server'));"
        "$quotedPath=@($A1,'/d','/s','/c','call',('\"'+$A2+'\"'),'app-server');"
        "$pathCaseDrift=@($A1,'/d','/s','/c','call',$A2.ToUpperInvariant(),'app-server');"
        "$extra=@($A1,'/d','/s','/c','call',$A2,'app-server','&','echo','unexpected');"
        "[ordered]@{valid=(Test-ExactCmdAppServerVector $valid $A1 $A2);"
        "combined=(Test-ExactCmdAppServerVector $combined $A1 $A2);"
        "quoted_path=(Test-ExactCmdAppServerVector $quotedPath $A1 $A2);"
        "path_case_drift=(Test-ExactCmdAppServerVector $pathCaseDrift $A1 $A2);"
        "extra=(Test-ExactCmdAppServerVector $extra $A1 $A2)}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        script_path(repo_root, "hmasd-root-supervisor-status.ps1"),
        ("Test-SamePath", "Test-SafeCmdBatchPath", "Test-ExactCmdAppServerVector"),
        body,
        str(command_processor),
        str(batch),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert json.loads(result.stdout) == {
        "valid": True,
        "combined": False,
        "quoted_path": False,
        "path_case_drift": False,
        "extra": False,
    }


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
        "startup_ready_timeout_seconds": 150.0,
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
        ("Test-SamePath", "Test-FullyQualifiedPath", "Test-ExternalExistingFile", "Test-ExactFields", "Get-StartupReadyTimeout", "Parse-StrictLaunchArgumentVector", "Test-RecordAndLaunchBinding", "Test-ActiveCodexBinding"),
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


def test_start_canonicalizes_explicit_relative_codex_before_launch_vector(repo_root, tmp_path):
    codex = tmp_path / "relative-codex.cmd"
    codex.write_text("@echo off\r\necho codex-inert\r\n", encoding="utf-8")
    relative = os.path.relpath(codex, repo_root)
    other_directory = tmp_path / "other-cwd"
    other_directory.mkdir()
    body = (
        "$resolved=Resolve-CanonicalExecutable $A1 'CodexBin';"
        "$vector=@(Get-SupervisorArgumentVector $A2 $A3 'OBSERVER' '' $A4 $A5 $resolved $false 0);"
        "Push-Location $A6;try{$stable=[System.IO.Path]::IsPathRooted($vector[7]) -and (Test-SamePath $vector[7] $resolved)}finally{Pop-Location};"
        "[ordered]@{resolved=$resolved;vector_codex=$vector[7];stable=$stable}|ConvertTo-Json -Compress"
    )
    result = invoke_start_helpers(
        script_path(repo_root, "hmasd-root-supervisor-start.ps1"),
        ("Test-SamePath", "Resolve-CanonicalExecutable", "Get-SupervisorArgumentVector"),
        body,
        relative,
        str(repo_root.resolve()),
        str((tmp_path / "runtime").resolve()),
        str((tmp_path / "ready.json").resolve()),
        str((tmp_path / "control").resolve()),
        str(other_directory.resolve()),
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert Path(payload["resolved"]).resolve() == codex.resolve()
    assert Path(payload["vector_codex"]).resolve() == codex.resolve()
    assert payload["stable"] is True


def test_status_uses_active_run_binary_when_default_launch_and_environment_change(repo_root, tmp_path):
    assert POWER_SHELL is not None
    assert PROJECT_PYTHON.is_file()
    active_dir = tmp_path / "active-codex"
    active_dir.mkdir()
    active_codex = (active_dir / "codex.cmd").resolve()
    active_codex.write_text(
        "@echo off\r\n"
        "if \"%1\"==\"--version\" (echo codex-inert 0.0-test& exit /b 0)\r\n"
        f'if "%1"=="app-server" ("{PROJECT_PYTHON.resolve()}" app-server& exit /b %ERRORLEVEL%)\r\n'
        "exit /b 2\r\n",
        encoding="utf-8",
    )
    caller_dir = tmp_path / "caller-codex"
    caller_dir.mkdir()
    caller_marker = caller_dir / "caller-invoked.txt"
    caller_codex = caller_dir / "codex.cmd"
    caller_codex.write_text(
        f'@echo off\r\necho invoked>"{caller_marker}"\r\necho codex-caller 0.0-test\r\n',
        encoding="utf-8",
    )
    with tempfile.TemporaryDirectory(prefix="hmasd-status-active-binary-") as external:
        runtime_home = Path(external).resolve()
        ready_path = runtime_home / "ready.json"
        control_home = runtime_home / "control"
        launch_vector = [
            "-m", "tools.codex_supervisor", "--repo-root", str(repo_root.resolve()),
            "--runtime-home", str(runtime_home), "serve", "--profile", "OBSERVER",
            "--ready-file", str(ready_path), "--control-home", str(control_home),
        ]
        host, child_id, fixture_codex = spawn_inert_supervisor_shape(
            tmp_path / "active-host", launch_vector, codex_path=active_codex
        )
        try:
            identity = process_identity(host.pid)
            ready_path = runtime_home / "ready.json"
            control_home = runtime_home / "control"
            run_id = "run-active-binary"
            initialized_at = datetime.now(timezone.utc).isoformat()
            process_record = {
                "schema": "HMASD_SUPERVISOR_PROCESS_V1",
                "pid": host.pid,
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
                        "process_id": host.pid,
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
                        "argument_vector": launch_vector,
                        "control_home": str(control_home),
                        "ready_file": str(ready_path),
                        "startup_ready_timeout_seconds": 150.0,
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
                        child_id,
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
            assert payload["ready"]["app_server_process_id"] == child_id
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
            terminate_inert_tree(host)


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
        "startup_ready_timeout_seconds": 150.0,
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
        "$matched=Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $expected 150.0; "
        "$wrongControl=Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A6 $A7 $expected 150.0; "
        "$wrongRepo=Test-ExistingInvocation $record $A6 $A2 'OBSERVER' $A3 $A4 $A7 $expected 150.0; "
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
                "startup_ready_timeout_seconds": 150.0,
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
        "[ordered]@{matched=(Test-ExistingInvocation $record $A1 $A2 'MANAGED_MANUAL' $A6 $A7 $A8 $expected 150.0);"
        "other=(Test-ExistingInvocation $record $A1 $A2 'MANAGED_MANUAL' $A6 $A7 $A8 $other 150.0)}|ConvertTo-Json -Compress"
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
        "startup_ready_timeout_seconds": 150.0,
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
        "[ordered]@{bounded=(Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $bounded 150.0); "
        "unbounded=(Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $unbounded 150.0); "
        "wrong_codex=(Test-ExistingInvocation $record $A1 $A2 'OBSERVER' $A3 $A4 $A7 $wrongCodex 150.0); "
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
    assert "SELECT initialized_at, ended_at, runtime_home, codex_binary, process_id FROM observer_runs WHERE run_id = ?" in text
    assert "Test-ReadyProcessTruth" in text
    assert "Test-AppServerProcessBinding" in text
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
