import json
import hashlib
import os
import re
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
    # The shared feature worktree may be ACTIVE; test stages always start from
    # an isolated OFF baseline without changing the live workspace.
    config = stage / ".codex" / "config.toml"
    text = config.read_text()
    text = re.sub(
        r"\n?# BEGIN HMASD CODEX SEMANTIC HOOKS.*?# END HMASD CODEX SEMANTIC HOOKS\n?",
        "\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"(?s)(# BEGIN HMASD CODEX SEMANTIC MVP.*?# END HMASD CODEX SEMANTIC MVP)",
        lambda match: match.group(1).replace("enabled = true", "enabled = false", 1),
        text,
        count=1,
    )
    config.write_text(text)
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
        errors="replace",
        check=False,
    )


def test_operator_capture_preserves_failure_output_with_invalid_stderr_bytes(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    fake_repo = tmp_path / "fake-repo"
    scripts = fake_repo / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "codex-semantic-mvp-enable.ps1").write_text(
        "[Console]::Out.WriteLine('EXPECTED_STDOUT')\n"
        "[Console]::OpenStandardError().Write([byte[]](0xFF), 0, 1)\n"
        "[Console]::Error.WriteLine('EXPECTED_FAILURE_MARKER')\n"
        "exit 7\n"
    )

    result = _run_operator(fake_repo, stage, "codex-semantic-mvp-enable.ps1")

    assert result.returncode == 7
    assert result.stdout == "EXPECTED_STDOUT\n"
    assert isinstance(result.stderr, str)
    assert "EXPECTED_FAILURE_MARKER" in result.stderr
    assert "\ufffd" in result.stderr


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
    assert ("enabled = true" if "# BEGIN HMASD CODEX SEMANTIC HOOKS" in config else "enabled = false") in config


def test_doctor_reports_machine_readable_activation_state(repo_root: Path):
    result = collect_baseline(repo_root)
    assert result["live_hooks_hash"] == result["hooks_json"]["sha256"]
    assert result["config_hash"] == result["config_toml"]["sha256"]
    assert result["mcp_version"] == "2.0.0"
    assert result["server_config_present"] is True
    expected_enabled = 'enabled = true' in (repo_root / ".codex" / "config.toml").read_text()
    assert result["server_enabled"] is expected_enabled
    assert result["runtime_writable"] is True
    assert result["mode"] in ({"active", "off"} if expected_enabled else {"off"})
    assert result["user_trust"] == {
        "status": "unknown",
        "scope": "repository_only",
        "message": "Repository-only doctor cannot establish user-level Codex trust.",
    }


def test_doctor_mode_uses_effective_inline_toml_not_legacy_hooks_json(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    legacy = stage / ".codex" / "hooks.json"
    legacy.write_bytes((repo_root / ".codex" / "hooks.semantic-mvp.shadow.json").read_bytes())
    result = collect_baseline(stage)
    assert result["mode"] == "active"


def test_doctor_reports_shadow_from_inline_toml(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert enabled.returncode == 0, enabled.stderr
    result = collect_baseline(stage)
    assert result["mode"] == "shadow"


def test_doctor_never_reports_active_for_malformed_inline_toml(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text() + "\n# BEGIN HMASD CODEX SEMANTIC HOOKS\n")
    assert collect_baseline(stage)["mode"] != "active"


def test_doctor_reports_unknown_for_invalid_full_toml_even_when_semantics_match(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("enabled = true", "enabled = true\nbroken = [", 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_requires_features_hooks_true_for_active_mode(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("hooks = true", "hooks = false", 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_indented_duplicate_features_hooks_assignment(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("hooks = true", "hooks = true\n  hooks = false", 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_requires_exact_semantic_mcp_args_for_active_mode(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace('"tools.codex_semantic_mvp.mcp_server"', '"wrong.server"', 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_indented_duplicate_inline_hook_type(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace('type = "command"', 'type = "command"\n  type = "wrong"', 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_indented_duplicate_inline_hook_command(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace(
        'command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"',
        'command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n  command = "wrong"',
        1,
    ))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_missing_or_mismatched_windows_hook_command(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    expected = (
        'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe '
        '-m tools.codex_semantic_mvp.hook_entry --mode active"'
    )
    config.write_text(config.read_text().replace(expected, 'commandWindows = "wrong"', 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_duplicate_mcp_enabled_assignment_for_active_mode(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("enabled = true", "enabled = true\nenabled = false", 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_duplicate_mcp_args_assignment_for_active_mode(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("# END HMASD CODEX SEMANTIC MVP", "  args = []\n# END HMASD CODEX SEMANTIC MVP", 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_duplicate_mcp_timeout_assignment_for_active_mode(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("tool_timeout_sec = 1800", "tool_timeout_sec = 1800\n  tool_timeout_sec = 1800", 1))
    assert collect_baseline(stage)["mode"] == "unknown"


def test_doctor_rejects_indented_duplicate_mcp_command_for_active_mode(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace(
        "# END HMASD CODEX SEMANTIC MVP",
        '  command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe"\n# END HMASD CODEX SEMANTIC MVP',
        1,
    ))
    assert collect_baseline(stage)["mode"] == "unknown"


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


def test_active_activation_installs_inline_toml_handlers_and_enables_mcp(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert result.returncode == 0, result.stderr

    config = (stage / ".codex" / "config.toml").read_text()
    assert "hooks = true" in config
    hook_block = config.split("# BEGIN HMASD CODEX SEMANTIC HOOKS", 1)[1].split(
        "# END HMASD CODEX SEMANTIC HOOKS", 1
    )[0]
    for event in ("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse"):
        assert f"[[hooks.{event}]]" in hook_block
        assert f"[[hooks.{event}.hooks]]" in hook_block
    assert 'command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"' in hook_block
    assert hook_block.count('commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"') == 5
    assert '"runtime/codex-semantic-mvp"' in config
    assert config.count("enabled = true") == 1
    assert config.count("enabled = false") == 0


def test_activation_leaves_legacy_hooks_json_byte_exact(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    hooks_before = (stage / ".codex" / "hooks.json").read_bytes()
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert result.returncode == 0, result.stderr
    assert (stage / ".codex" / "hooks.json").read_bytes() == hooks_before


def test_disable_restores_uniform_lf_config_byte_exact(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_bytes(config.read_bytes().replace(b"\r\n", b"\n"))
    config_before = config.read_bytes()
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    disabled = _run_operator(repo_root, stage, "codex-semantic-mvp-disable.ps1")
    assert disabled.returncode == 0, disabled.stderr
    assert config.read_bytes() == config_before


def test_enable_rejects_existing_dotted_inline_hook_definition(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text() + "\n[[hooks.SessionStart]]\n")
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert result.returncode != 0
    assert "HOOKS_TABLE_CONFLICT" in (result.stdout + result.stderr)


@pytest.mark.parametrize(
    "assignment",
    [
        "hooks.SessionStart = []",
        "hooks = { SessionStart = [] }",
    ],
)
def test_enable_rejects_existing_inline_hook_assignments(
    repo_root: Path, tmp_path: Path, assignment: str
):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text() + f"\n{assignment}\n")
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert result.returncode != 0
    assert "HOOKS_TABLE_CONFLICT" in (result.stdout + result.stderr)


def test_active_replaces_managed_shadow_block_without_changing_unrelated_config(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text() + "\n# unrelated activation sentinel\n")
    shadow = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Shadow")
    assert shadow.returncode == 0, shadow.stderr
    shadow_text = config.read_text()
    active = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert active.returncode == 0, active.stderr
    active_text = config.read_text()

    begin = "# BEGIN HMASD CODEX SEMANTIC HOOKS"
    end = "# END HMASD CODEX SEMANTIC HOOKS"
    shadow_begin = shadow_text.index(begin)
    shadow_end = shadow_text.index(end) + len(end)
    active_begin = active_text.index(begin)
    active_end = active_text.index(end) + len(end)
    assert shadow_text[:shadow_begin].replace("enabled = false", "enabled = <mcp>") == active_text[:active_begin].replace("enabled = true", "enabled = <mcp>")
    assert shadow_text[shadow_end:] == active_text[active_end:]
    assert "--mode shadow" in shadow_text[shadow_begin:shadow_end]
    assert "--mode active" in active_text[active_begin:active_end]
    assert "--mode shadow" not in active_text[active_begin:active_end]
    state = json.loads((stage / "runtime/codex-semantic-mvp/activation-state.json").read_text())
    assert state["mode"] == "active"


def test_disable_removes_inline_toml_handlers_and_disables_mcp(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    enabled = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert enabled.returncode == 0, enabled.stderr
    disabled = _run_operator(repo_root, stage, "codex-semantic-mvp-disable.ps1")
    assert disabled.returncode == 0, disabled.stderr

    config = (stage / ".codex" / "config.toml").read_text()
    assert "# BEGIN HMASD CODEX SEMANTIC HOOKS" not in config
    assert "# END HMASD CODEX SEMANTIC HOOKS" not in config
    assert config.count("enabled = false") == 1
    assert config.count("enabled = true") == 0


@pytest.mark.parametrize(
    "suffix",
    [
        "\n# BEGIN HMASD CODEX SEMANTIC HOOKS\n# END HMASD CODEX SEMANTIC HOOKS\n",
        "\n# BEGIN HMASD CODEX SEMANTIC HOOKS\n",
    ],
)
def test_enable_rejects_duplicate_or_malformed_inline_hook_block(
    repo_root: Path, tmp_path: Path, suffix: str
):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text() + suffix)
    result = _run_operator(repo_root, stage, "codex-semantic-mvp-enable.ps1", "-Mode", "Active")
    assert result.returncode != 0
    assert "HOOK_MARKER_BLOCK_INVALID" in (result.stdout + result.stderr)


def test_native_smoke_contract_requires_inline_active_toml_and_audit_evidence(repo_root: Path):
    script = (repo_root / "scripts/codex-semantic-mvp-test.ps1").read_text()
    assert "NativeSmoke" in script
    assert "dangerously-bypass-hook-trust" in script
    assert "audit.jsonl" in script
    assert "NATIVE_HOOK_EVENT_REQUIRED" in script
    assert "# BEGIN HMASD CODEX SEMANTIC HOOKS" in script
    assert "hooks\\.' + $event" in script
    assert "commandWindows" in script
    assert "ArgumentList.Add" in script


def _native_active_stage(repo_root: Path, tmp_path: Path) -> Path:
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(
        config.read_text().replace("enabled = false", "enabled = true", 1)
        + '\n# BEGIN HMASD CODEX SEMANTIC HOOKS\n'
        + ''.join(
            f'[[hooks.{event}]]\n[[hooks.{event}.hooks]]\ntype = "command"\n'
            'command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            for event in ("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse")
        )
        + '# END HMASD CODEX SEMANTIC HOOKS\n'
    )
    return stage


def _run_native_config_failure(repo_root: Path, stage: Path) -> subprocess.CompletedProcess[str]:
    fake = stage / "fake-codex.cmd"
    fake.write_text('@echo off\r\necho {"type":"thread.started","thread_id":"unused"}\r\nexit /b 0\r\n')
    return subprocess.run(
        [
            "pwsh", "-NoProfile", "-NonInteractive", "-File",
            str(repo_root / "scripts/codex-semantic-mvp-test.ps1"),
            "-RepoRoot", str(stage), "-NativeSmoke", "-CodexCommand", str(fake),
        ],
        text=True, capture_output=True, encoding="utf-8", check=False,
        errors="replace",
    )


def test_native_smoke_rejects_notcommand_handler(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace('type = "command"', 'notcommand = "command"', 1))
    result = _run_native_config_failure(repo_root, stage)
    assert result.returncode != 0
    assert "NATIVE_SMOKE_REQUIRES_INLINE_TOML" in (result.stdout + result.stderr)


def test_native_smoke_rejects_missing_windows_hook_command(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    expected = (
        'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe '
        '-m tools.codex_semantic_mvp.hook_entry --mode active"\n'
    )
    config.write_text(config.read_text().replace(expected, "", 1))
    result = _run_native_config_failure(repo_root, stage)
    assert result.returncode != 0
    assert "NATIVE_SMOKE_REQUIRES_INLINE_TOML" in (result.stdout + result.stderr)


def test_native_smoke_rejects_duplicate_windows_hook_command(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    expected = (
        'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe '
        '-m tools.codex_semantic_mvp.hook_entry --mode active"\n'
    )
    config.write_text(config.read_text().replace(expected, expected + expected, 1))
    result = _run_native_config_failure(repo_root, stage)
    assert result.returncode != 0
    assert "NATIVE_SMOKE_REQUIRES_INLINE_TOML" in (result.stdout + result.stderr)


def test_native_smoke_rejects_mismatched_windows_hook_command(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    expected = (
        'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe '
        '-m tools.codex_semantic_mvp.hook_entry --mode active"\n'
    )
    config.write_text(config.read_text().replace(expected, 'commandWindows = "wrong"\n', 1))
    result = _run_native_config_failure(repo_root, stage)
    assert result.returncode != 0
    assert "NATIVE_SMOKE_REQUIRES_INLINE_TOML" in (result.stdout + result.stderr)


def test_native_smoke_rejects_duplicate_mismatched_event_handler(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace(
        '[[hooks.SessionStart.hooks]]',
        '[[hooks.SessionStart.extra]]\ntype = "command"\ncommand = "wrong"\n[[hooks.SessionStart.hooks]]',
        1,
    ))
    result = _run_native_config_failure(repo_root, stage)
    assert result.returncode != 0
    assert "NATIVE_SMOKE_REQUIRES_INLINE_TOML" in (result.stdout + result.stderr)


def test_native_smoke_rejects_relative_path_hidden_in_other_section(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    text = config.read_text().replace('"runtime/codex-semantic-mvp"', '"C:/absolute/semantic-state"', 1)
    config.write_text(text + '\n[mcp_servers.other]\nargs = ["runtime/codex-semantic-mvp"]\n')
    result = _run_native_config_failure(repo_root, stage)
    assert result.returncode != 0
    assert "NATIVE_SMOKE_REQUIRES_INLINE_TOML" in (result.stdout + result.stderr)


def test_native_smoke_rejects_wrong_orchestrator_server_args(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace(
        '"tools.codex_semantic_mvp.mcp_server"', '"wrong.server"', 1
    ))
    result = _run_native_config_failure(repo_root, stage)
    assert result.returncode != 0
    assert "NATIVE_SMOKE_REQUIRES_INLINE_TOML" in (result.stdout + result.stderr)


def test_native_smoke_resolves_powershell_codex_shim_to_cmd_sibling(repo_root: Path, tmp_path: Path):
    stage = _native_active_stage(repo_root, tmp_path)
    shim_dir = tmp_path / "codex shim"
    shim_dir.mkdir()
    audit = stage / "runtime" / "codex-semantic-mvp" / "audit.jsonl"
    audit.parent.mkdir(parents=True)
    (shim_dir / "codex.ps1").write_text("# PowerShell shim")
    (shim_dir / "codex.cmd").write_text(
        f'@echo off\r\necho {{"type":"thread.started","thread_id":"shim-session"}}\r\n'
        f'echo {{"event":"SESSION_STARTED","session_id":"shim-session","mode":"active"}}>>"{audit}"\r\n'
        f'exit /b 0\r\n'
    )
    env = os.environ.copy()
    env["PATH"] = str(shim_dir) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-File",
         str(repo_root / "scripts/codex-semantic-mvp-test.ps1"),
         "-RepoRoot", str(stage), "-NativeSmoke"],
        text=True, capture_output=True, encoding="utf-8", errors="replace", check=False, env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_native_smoke_rejects_unlaunchable_codex_shim(repo_root: Path, tmp_path: Path):
    shim_dir = tmp_path / "only shim"
    shim_dir.mkdir()
    (shim_dir / "codex.ps1").write_text("# PowerShell shim")
    env = os.environ.copy()
    env["PATH"] = str(shim_dir)
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-File",
         str(repo_root / "scripts/codex-semantic-mvp-test.ps1"),
         "-RepoRoot", str(repo_root), "-NativeSmoke"],
        text=True, capture_output=True, encoding="utf-8", errors="replace", check=False, env=env,
    )
    assert result.returncode != 0
    assert "NATIVE_SMOKE_CODEX_COMMAND_INVALID" in (result.stdout + result.stderr)


def test_native_smoke_accepts_fake_native_audit_event_without_mutating_config_or_state(
    repo_root: Path, tmp_path: Path
):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("enabled = false", "enabled = true", 1))
    config.write_text(
        config.read_text()
        + '\n# BEGIN HMASD CODEX SEMANTIC HOOKS\n'
        + ''.join(
            f'[[hooks.{event}]]\n[[hooks.{event}.hooks]]\ntype = "command"\n'
            'command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            for event in ("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse")
        )
        + '# END HMASD CODEX SEMANTIC HOOKS\n'
    )
    config_before = config.read_bytes()
    audit = stage / "runtime" / "codex-semantic-mvp" / "audit.jsonl"
    audit.parent.mkdir(parents=True)
    activation = stage / "runtime" / "codex-semantic-mvp" / "activation-state.json"
    activation.write_bytes(b'{"mode":"active","protected":true}\n')
    activation_before = activation.read_bytes()
    fake = tmp_path / "fake-codex.cmd"
    fake.write_text(
        f'@echo off\r\n'
        f'if not "%1"=="exec" exit /b 11\r\n'
        f'if not "%2"=="--json" exit /b 12\r\n'
        f'if not "%3"=="--dangerously-bypass-hook-trust" exit /b 13\r\n'
        f'if not "%4"=="--skip-git-repo-check" exit /b 14\r\n'
        f'if not "%5"=="--cd" exit /b 15\r\n'
        f'if not "%7"=="--model" exit /b 16\r\n'
        f'if not "%8"=="gpt-5.6-luna" exit /b 17\r\n'
        f'echo {{"type":"thread.started","thread_id":"native-smoke-session"}}\r\n'
        f'echo {{"event":"SESSION_STARTED","session_id":"native-smoke-session","mode":"active"}}>>"{audit}"\r\n'
        f'exit /b 0\r\n'
    )
    result = subprocess.run(
        [
            "pwsh", "-NoProfile", "-NonInteractive", "-File",
            str(repo_root / "scripts/codex-semantic-mvp-test.ps1"),
            "-RepoRoot", str(stage), "-NativeSmoke", "-CodexCommand", str(fake),
        ],
        text=True, capture_output=True, encoding="utf-8", errors="replace", check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert config.read_bytes() == config_before
    assert activation.read_bytes() == activation_before


def test_native_smoke_rejects_stdout_without_new_audit_event(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("enabled = false", "enabled = true", 1))
    config.write_text(
        config.read_text()
        + '\n# BEGIN HMASD CODEX SEMANTIC HOOKS\n'
        + ''.join(
            f'[[hooks.{event}]]\n[[hooks.{event}.hooks]]\ntype = "command"\n'
            'command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            for event in ("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse")
        )
        + '# END HMASD CODEX SEMANTIC HOOKS\n'
    )
    fake = tmp_path / "fake-codex-no-audit.cmd"
    fake.write_text('@echo off\r\necho {"type":"thread.started","thread_id":"native-smoke-session"}\r\necho NATIVE_SEMANTIC_SMOKE_OK\r\nexit /b 0\r\n')
    result = subprocess.run(
        [
            "pwsh", "-NoProfile", "-NonInteractive", "-File",
            str(repo_root / "scripts/codex-semantic-mvp-test.ps1"),
            "-RepoRoot", str(stage), "-NativeSmoke", "-CodexCommand", str(fake),
        ],
        text=True, capture_output=True, encoding="utf-8", errors="replace", check=False,
    )
    assert result.returncode != 0
    assert "NATIVE_HOOK_EVENT_REQUIRED" in (result.stdout + result.stderr)


def test_native_smoke_rejects_audit_event_for_wrong_cli_session(repo_root: Path, tmp_path: Path):
    stage = _stage(repo_root, tmp_path)
    config = stage / ".codex" / "config.toml"
    config.write_text(config.read_text().replace("enabled = false", "enabled = true", 1))
    config.write_text(
        config.read_text()
        + '\n# BEGIN HMASD CODEX SEMANTIC HOOKS\n'
        + ''.join(
            f'[[hooks.{event}]]\n[[hooks.{event}.hooks]]\ntype = "command"\n'
            'command = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            'commandWindows = "C:\\\\Users\\\\wu\\\\.conda\\\\envs\\\\SB3\\\\python.exe -m tools.codex_semantic_mvp.hook_entry --mode active"\n'
            for event in ("SessionStart", "SubagentStart", "SubagentStop", "Stop", "PreToolUse")
        )
        + '# END HMASD CODEX SEMANTIC HOOKS\n'
    )
    audit = stage / "runtime" / "codex-semantic-mvp" / "audit.jsonl"
    audit.parent.mkdir(parents=True)
    fake = tmp_path / "fake-codex-wrong-session.cmd"
    fake.write_text(
        f'@echo off\r\n'
        f'echo {{"type":"thread.started","thread_id":"native-smoke-session"}}\r\n'
        f'echo {{"event":"SESSION_STARTED","session_id":"different-session","mode":"active"}}>>"{audit}"\r\n'
        f'exit /b 0\r\n'
    )
    result = subprocess.run(
        [
            "pwsh", "-NoProfile", "-NonInteractive", "-File",
            str(repo_root / "scripts/codex-semantic-mvp-test.ps1"),
            "-RepoRoot", str(stage), "-NativeSmoke", "-CodexCommand", str(fake),
        ],
        text=True, capture_output=True, encoding="utf-8", errors="replace", check=False,
    )
    assert result.returncode != 0
    assert "NATIVE_HOOK_EVENT_REQUIRED" in (result.stdout + result.stderr)
