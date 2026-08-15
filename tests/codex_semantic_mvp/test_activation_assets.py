import json
import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.codex_semantic_mvp.constants import (
    ACTIVE_MODE,
    OFF_MODE,
    SHADOW_MODE,
    STATE_DIR_ENV,
)
from tools.codex_semantic_mvp.doctor import _runtime_writable, collect_baseline, installed_mcp_version


def _stage(repo_root: Path, tmp_path: Path) -> Path:
    stage = tmp_path / "activation-stage"
    (stage / ".codex").mkdir(parents=True)
    for name in ("hooks.json", "config.toml", "hooks.semantic-mvp.shadow.json", "hooks.semantic-mvp.active.json"):
        shutil.copy2(repo_root / ".codex" / name, stage / ".codex" / name)
    return stage


def _run_operator(
    repo_root: Path,
    stage: Path,
    script: str,
    *args: str,
    supply_initial_baseline: bool = True,
) -> subprocess.CompletedProcess[str]:
    operator_args = list(args)
    if script == "codex-semantic-mvp-enable.ps1" and supply_initial_baseline:
        operator_args.extend(("-ExpectedHooksHash", hashlib.sha256((stage / ".codex" / "hooks.json").read_bytes()).hexdigest()))
    return subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-File", str(repo_root / "scripts" / script), "-RepoRoot", str(stage), *operator_args],
        text=True,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )


def test_mode_constants_are_exact():
    assert (OFF_MODE, SHADOW_MODE, ACTIVE_MODE) == ("off", "shadow", "active")
    assert STATE_DIR_ENV == "HMASD_CODEX_MVP_STATE_DIR"


def test_collect_baseline_hashes_both_codex_files(repo_root: Path):
    result = collect_baseline(repo_root)
    assert result["config_toml"]["sha256"]
    assert result["hooks_json"]["sha256"]
    assert result["hooks_json"]["path"].endswith(".codex/hooks.json")


def test_activation_templates_and_config_contract(repo_root: Path):
    shadow = json.loads((repo_root / ".codex/hooks.semantic-mvp.shadow.json").read_text())
    active = json.loads((repo_root / ".codex/hooks.semantic-mvp.active.json").read_text())
    assert shadow["hooks"] and active["hooks"]
    assert shadow != active

    live = (repo_root / ".codex/hooks.json").read_bytes()
    assert live != (repo_root / ".codex/hooks.semantic-mvp.shadow.json").read_bytes()
    assert live != (repo_root / ".codex/hooks.semantic-mvp.active.json").read_bytes()

    config = (repo_root / ".codex/config.toml").read_text()
    assert config.count("# BEGIN HMASD CODEX SEMANTIC MVP") == 1
    assert config.count("# END HMASD CODEX SEMANTIC MVP") == 1
    assert '"C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe"' in config
    assert "tool_timeout_sec = 1800" in config
    assert "enabled = false" in config


def test_doctor_reports_machine_readable_activation_state(repo_root: Path):
    result = collect_baseline(repo_root)
    assert result["live_hooks_hash"] == result["hooks_json"]["sha256"]
    assert result["config_hash"] == result["config_toml"]["sha256"]
    assert result["mcp_version"] == "2.0.0"
    assert result["server_config_present"] is True
    assert result["server_enabled"] is False
    assert result["runtime_writable"] is True
    assert result["mode"] == "off"


def test_doctor_uses_installed_mcp_distribution_version(repo_root: Path):
    assert installed_mcp_version() == "2.0.0"
    assert installed_mcp_version(lambda _: "9.9.9") == "9.9.9"
    assert installed_mcp_version(lambda _: (_ for _ in ()).throw(Exception("missing"))) is None
    assert collect_baseline(repo_root, mcp_version_reader=lambda _: "9.9.9")["mcp_version"] == "9.9.9"
    assert collect_baseline(
        repo_root, mcp_version_reader=lambda _: (_ for _ in ()).throw(Exception("missing"))
    )["mcp_version"] is None


def test_activation_operator_scripts_exist(repo_root: Path):
    for name in (
        "codex-semantic-mvp-doctor.ps1",
        "codex-semantic-mvp-enable.ps1",
        "codex-semantic-mvp-disable.ps1",
        "codex-semantic-mvp-test.ps1",
    ):
        assert (repo_root / "scripts" / name).is_file()


def test_first_activation_rejects_unknown_live_hooks_without_baseline(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    hooks = stage / ".codex" / "hooks.json"
    hooks.write_bytes(b'{"description":"unknown live hook","hooks":{}}\n')
    config_before = (stage / ".codex" / "config.toml").read_bytes()
    result = _run_operator(
        repo_root,
        stage,
        "codex-semantic-mvp-enable.ps1",
        "-Mode",
        "Shadow",
        supply_initial_baseline=False,
    )
    assert result.returncode != 0
    assert "INITIAL_BASELINE_REQUIRED" in (result.stdout + result.stderr)
    assert hooks.read_bytes() == b'{"description":"unknown live hook","hooks":{}}\n'
    assert (stage / ".codex" / "config.toml").read_bytes() == config_before


def test_first_activation_accepts_only_matching_explicit_baseline(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    hooks = stage / ".codex" / "hooks.json"
    baseline = hashlib.sha256(hooks.read_bytes()).hexdigest()
    result = _run_operator(
        repo_root,
        stage,
        "codex-semantic-mvp-enable.ps1",
        "-Mode",
        "Shadow",
        "-ExpectedHooksHash",
        baseline,
        supply_initial_baseline=False,
    )
    assert result.returncode == 0, result.stderr


def test_doctor_does_not_create_absent_runtime(tmp_path: Path):
    parent = tmp_path / "runtime"
    parent.mkdir()
    runtime = parent / "codex-semantic-mvp"
    before = tuple(parent.iterdir())
    assert _runtime_writable(runtime) is True
    assert not runtime.exists()
    assert tuple(parent.iterdir()) == before


def test_disable_rejects_live_hook_drift_without_overwrite(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert enabled.returncode == 0, enabled.stderr
    hooks = stage / ".codex" / "hooks.json"
    drift = hooks.read_bytes() + b"\nDRIFT"
    hooks.write_bytes(drift)
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-disable.ps1")
    assert result.returncode != 0
    assert "LIVE_HOOK_HASH_MISMATCH" in (result.stdout + result.stderr)
    assert hooks.read_bytes() == drift


def test_disable_rejects_config_drift_without_overwrite(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert enabled.returncode == 0, enabled.stderr
    hooks = stage / ".codex" / "hooks.json"
    hooks_before = hooks.read_bytes()
    config = stage / ".codex" / "config.toml"
    config.write_bytes(config.read_bytes() + b"\n# external drift\n")
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-disable.ps1")
    assert result.returncode != 0
    assert "CONFIG_HASH_MISMATCH" in (result.stdout + result.stderr)
    assert hooks.read_bytes() == hooks_before


def test_enable_rejects_invalid_activation_state_before_mutation(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    hooks_before = (stage / ".codex" / "hooks.json").read_bytes()
    config_before = (stage / ".codex" / "config.toml").read_bytes()
    runtime = stage / "runtime" / "codex-semantic-mvp"
    runtime.mkdir(parents=True)
    (runtime / "activation-state.json").write_text(json.dumps({
        "schema_version": 1,
        "baseline_hooks_sha256": "0" * 64,
        "current_hooks_sha256": "1" * 64,
        "baseline_backup": "backups/../escape.bak",
    }))
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert result.returncode != 0
    assert "ACTIVATION_STATE" in (result.stdout + result.stderr)
    assert (stage / ".codex" / "hooks.json").read_bytes() == hooks_before
    assert (stage / ".codex" / "config.toml").read_bytes() == config_before


def test_enable_transaction_compensates_injected_config_failure(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    hooks_before = (stage / ".codex" / "hooks.json").read_bytes()
    config_before = (stage / ".codex" / "config.toml").read_bytes()
    result = _run_operator(
        repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active", "-InjectFailureAt", "config"
    )
    assert result.returncode != 0
    assert "INJECTED_FAILURE" in (result.stdout + result.stderr)
    assert (stage / ".codex" / "hooks.json").read_bytes() == hooks_before
    assert (stage / ".codex" / "config.toml").read_bytes() == config_before
    assert not (stage / "runtime" / "codex-semantic-mvp" / "activation-state.json").exists()


def test_enable_rejects_duplicate_enabled_assignment(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    text = config.read_text()
    text = text.replace("enabled = false\nrequired = false", "enabled = false\nenabled = true\nrequired = false")
    config.write_text(text)
    hooks_before = (stage / ".codex" / "hooks.json").read_bytes()
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert result.returncode != 0
    assert "MCP_ENABLED_FIELD_INVALID" in (result.stdout + result.stderr)
    assert (stage / ".codex" / "hooks.json").read_bytes() == hooks_before


def test_disable_transaction_compensates_injected_config_failure(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    before = {name: (stage / ".codex" / name).read_bytes() for name in ("hooks.json", "config.toml")}
    state = stage / "runtime" / "codex-semantic-mvp" / "activation-state.json"
    state_before = state.read_bytes()
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-disable.ps1", "-InjectFailureAt", "config")
    assert result.returncode != 0
    assert "INJECTED_FAILURE" in (result.stdout + result.stderr)
    assert (stage / ".codex" / "hooks.json").read_bytes() == before["hooks.json"]
    assert (stage / ".codex" / "config.toml").read_bytes() == before["config.toml"]
    assert state.read_bytes() == state_before


def test_marker_duplicate_is_rejected_by_doctor_and_enable(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    original = config.read_text()
    config.write_text(original + "\n# BEGIN HMASD CODEX SEMANTIC MVP\n")
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert result.returncode != 0
    assert "CONFIG_MARKER_BLOCK_INVALID" in (result.stdout + result.stderr)
    assert collect_baseline(stage)["server_config_present"] is False


def test_agent_profile_bytes_are_not_touched(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    profile = stage / ".codex" / "agents" / "example.toml"
    profile.parent.mkdir()
    profile.write_bytes(b"profile bytes must remain exact\r\n")
    before = profile.read_bytes()
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert enabled.returncode == 0, enabled.stderr
    disabled = _run_operator(repo_root, stage, "codex-semantic-mvp-disable.ps1")
    assert disabled.returncode == 0, disabled.stderr
    assert profile.read_bytes() == before


@pytest.mark.parametrize("failure_point", ["backup", "hooks", "state"])
def test_enable_injected_failures_compensate_every_activation_artifact(
    repo_root: Path, tmp_path: Path, failure_point: str
):
    stage = _stage(repo_root, tmp_path)
    hooks = stage / ".codex" / "hooks.json"
    config = stage / ".codex" / "config.toml"
    runtime = stage / "runtime" / "codex-semantic-mvp"
    hooks_before = hooks.read_bytes()
    config_before = config.read_bytes()
    result = _run_operator(
        repo_root,
        stage,
        "codex-semantic-mvp-enable.ps1",
        "-Mode",
        "Active",
        "-InjectFailureAt",
        failure_point,
    )
    assert result.returncode != 0
    assert "INJECTED_FAILURE" in (result.stdout + result.stderr)
    assert hooks.read_bytes() == hooks_before
    assert config.read_bytes() == config_before
    assert not (runtime / "activation-state.json").exists()
    assert not (runtime / "backups" / f"hooks-{hashlib.sha256(hooks_before).hexdigest()}.bak").exists()


@pytest.mark.parametrize(("mode", "expected"), [("Shadow", "false"), ("Active", "true")])
def test_successful_activation_sets_explicit_mcp_enabled_value(
    repo_root: Path, tmp_path: Path, mode: str, expected: str
):
    stage = _stage(repo_root, tmp_path)
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", mode)
    assert result.returncode == 0, result.stderr
    config = (stage / ".codex" / "config.toml").read_text()
    assert config.count(f"enabled = {expected}") == 1
    assert config.count("enabled = true") + config.count("enabled = false") == 1


def test_successful_disable_restores_hooks_config_and_expected_state(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    hooks = stage / ".codex" / "hooks.json"
    config = stage / ".codex" / "config.toml"
    hooks_before = hooks.read_bytes()
    config_before = config.read_bytes()
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    disabled = _run_operator(repo_root, stage, "codex-semantic-mvp-disable.ps1")
    assert disabled.returncode == 0, disabled.stderr
    assert hooks.read_bytes() == hooks_before
    assert config.read_bytes() == config_before
    state_path = stage / "runtime" / "codex-semantic-mvp" / "activation-state.json"
    state = json.loads(state_path.read_text())
    assert state["mode"] == "off"
    assert state["baseline_hooks_sha256"] == hashlib.sha256(hooks_before).hexdigest()
    assert state["current_hooks_sha256"] == hashlib.sha256(hooks_before).hexdigest()
    assert state["current_config_sha256"] == hashlib.sha256(config_before).hexdigest()
    backup = stage / "runtime" / "codex-semantic-mvp" / state["baseline_backup"]
    assert backup.read_bytes() == hooks_before
