"""Exercise the source inspector, not agent obedience or native permission enforcement."""
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("codex_inspector", ROOT / "tools/inspect_codex_control.py")
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def put(root, path, text):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


def repo(tmp_path, config="", role=None):
    root = tmp_path / "checkout"
    put(root, ".codex/config.toml", config)
    if role is not None:
        put(root, ".codex/agents/worker.toml", role)
    return root


def test_relative_role_paths_and_no_invented_inheritance(tmp_path, monkeypatch):
    root = repo(tmp_path, '''
# Root preference: an imaginary model / low. This comment is not a setting.
sandbox_mode = "danger-full-access"
[agents]
max_concurrent_threads_per_session = 40
default_subagent_model = "default-choice"
[agents.Worker]
config_file = "./agents/worker.toml"
''', 'model_reasoning_effort = "high"\n')
    monkeypatch.chdir(tmp_path)
    result = inspector.inspect_repository(root)
    assert result["errors"] == []
    assert result["root"]["declared"]["model"] is None
    assert result["root"]["declared"]["sandbox_mode"] == "danger-full-access"
    role = result["registered_roles"][0]["source"]
    assert role["path"] == ".codex/agents/worker.toml"
    assert role["declared"]["model_reasoning_effort"] == "high"
    assert role["declared"]["model"] is None  # Not resolved from [agents] or the parent.
    assert role["declared"]["sandbox_mode"] is None
    assert result["agent_settings"]["max_concurrent_threads_per_session"] == 40
    assert result["runtime_verified"] is False


def test_native_readonly_is_a_declaration_not_verification(tmp_path):
    root = repo(tmp_path, '[agents.Reviewer]\nconfig_file="agents/worker.toml"\n',
                'sandbox_mode="read-only"\napproval_policy="never"\n')
    result = inspector.inspect_repository(root)
    assert result["registered_roles"][0]["source"]["declared"]["sandbox_mode"] == "read-only"
    assert result["runtime_verified"] is False
    assert "runtime NOT verified" in inspector.render_text(result)


def test_aliases_and_description_only_roles_are_not_errors(tmp_path):
    root = repo(tmp_path, '''
[agents.A]
config_file="agents/worker.toml"
[agents.B]
config_file="agents/worker.toml"
[agents.NoLayer]
description="Inherit configuration without a separate file."
''', 'model="sample"\n')
    result = inspector.inspect_repository(root)
    assert result["errors"] == []
    assert len(result["registered_roles"]) == 3
    assert result["registered_roles"][0]["source"] == result["registered_roles"][1]["source"]
    assert result["registered_roles"][2]["source"] is None
    assert result["unregistered_agent_files"] == []


def test_unregistered_standalone_file_is_not_called_retired(tmp_path):
    root = repo(tmp_path, '[agents]\nenabled=true\n', 'name="standalone"\nmodel="sample"\n')
    result = inspector.inspect_repository(root)
    assert result["errors"] == []
    assert result["registered_roles"] == []
    assert result["unregistered_agent_files"][0]["name"] == "standalone"
    assert "NOT proof of inactivity" in inspector.render_text(result)


@pytest.mark.parametrize("bad", ["", 'model = [', 'model="bad"\nmodel="duplicate"\n'])
def test_bad_or_missing_role_does_not_hide_good_role(tmp_path, bad):
    root = repo(tmp_path, '''
[agents.Bad]
config_file="roles/bad.toml"
[agents.Good]
config_file="agents/worker.toml"
''', 'model="good"\n')
    if bad:
        put(root, ".codex/roles/bad.toml", bad)
    result = inspector.inspect_repository(root)
    assert len(result["errors"]) == 1
    assert result["registered_roles"][0]["source"] is None
    assert result["registered_roles"][1]["source"]["declared"]["model"] == "good"


@pytest.mark.parametrize("reference", ['""', '"   "', "false", "17", "[]", "{}"])
def test_invalid_config_file_type_or_empty_value_is_reported(tmp_path, reference):
    root = repo(tmp_path, f"[agents.Bad]\nconfig_file={reference}\n")
    result = inspector.inspect_repository(root)
    assert len(result["errors"]) == 1
    assert "nonempty path string" in result["errors"][0]["message"]


@pytest.mark.parametrize("config", ['agents="wrong"', 'model=[', 'model="a"\nmodel="b"'])
def test_bad_root_config_reports_failure(tmp_path, capsys, config):
    root = repo(tmp_path, config)
    assert inspector.main(["--root", str(root), "--json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["errors"]
    assert result["runtime_verified"] is False


def test_missing_config_is_not_an_empty_success(tmp_path, capsys):
    assert inspector.main(["--root", str(tmp_path), "--json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["root"] is None
    assert result["errors"][0]["path"] == ".codex/config.toml"


def test_external_reference_is_not_read(tmp_path, monkeypatch):
    root = repo(tmp_path, '[agents.External]\nconfig_file="../../outside.toml"\n')
    outside = put(tmp_path, "outside.toml", 'model="private-value"\n')
    original = Path.read_bytes

    def guarded(path):
        assert path != outside, "Inspector read outside the selected checkout"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    result = inspector.inspect_repository(root)
    assert len(result["errors"]) == 1
    assert "outside selected checkout" in result["errors"][0]["message"]
    assert "private-value" not in json.dumps(result)


def link_or_skip(link, target, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("Native symlink creation is not available")


def test_redirected_agent_directory_is_not_enumerated(tmp_path, monkeypatch):
    root = repo(tmp_path)
    outside = tmp_path / "private"
    outside.mkdir()
    link_or_skip(root / ".codex/agents", outside, directory=True)
    original = Path.iterdir

    def guarded(path):
        assert not path.resolve().is_relative_to(outside)
        return original(path)

    monkeypatch.setattr(Path, "iterdir", guarded)
    result = inspector.inspect_repository(root)
    assert len(result["errors"]) == 1
    assert result["unregistered_agent_files"] == []


def test_external_standalone_symlink_does_not_hide_remaining_files(tmp_path):
    root = repo(tmp_path, role='name="good"\nmodel="good"\n')
    outside = put(tmp_path, "outside.toml", 'model="private-value"\n')
    link_or_skip(root / ".codex/agents/a-bad.toml", outside)
    result = inspector.inspect_repository(root)
    assert len(result["errors"]) == 1
    assert result["unregistered_agent_files"][0]["name"] == "good"
    assert "private-value" not in json.dumps(result)


def test_raw_byte_identity_and_structured_approval_policy(tmp_path):
    root = repo(tmp_path)
    path = root / ".codex/config.toml"
    data = b'approval_policy = { granular = { mcp_elicitations = false } }\r\n'
    path.write_bytes(data)
    result = inspector.inspect_repository(root)
    assert result["root"]["sha256"] == hashlib.sha256(data).hexdigest()
    assert result["root"]["declared"]["approval_policy"] == {"granular": {"mcp_elicitations": False}}


def test_cli_is_readonly_offline_deterministic_and_omits_unselected_secrets(tmp_path, monkeypatch, capsys):
    root = repo(tmp_path, '''
model="sample"
[mcp_servers.private]
command="DO NOT EXECUTE"
[mcp_servers.private.env]
TOKEN="DO NOT PRINT"
[agents.Worker]
config_file="agents/worker.toml"
''', 'developer_instructions="DO NOT PRINT BODY"\n')
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def forbidden(*args, **kwargs):
        pytest.fail("Source inspection attempted a write, network connection or external command")

    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "mkdir", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    outputs = []
    for _ in range(2):
        assert inspector.main(["--root", str(root), "--json"]) == 0
        outputs.append(capsys.readouterr().out)
    assert outputs[0] == outputs[1]
    assert "DO NOT" not in outputs[0]
    assert json.loads(outputs[0])["runtime_verified"] is False
    assert before == {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("relative", [
    ".claude/skills/hmasd-loop-dispatch/SKILL.md",
    ".claude/skills/hmasd-research-hub/SKILL.md",
])
def test_changed_workflow_outputs_match_existing_publisher(monkeypatch, relative):
    # Isolate these skill outputs from unrelated native-agent header generation.
    # This checks publication bytes, not a running agent's adoption or behavior.
    spec = importlib.util.spec_from_file_location("codex_workflow_publisher", ROOT / "tools/publish_claude_control.py")
    publisher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publisher)
    monkeypatch.setattr(publisher, "ROLE_MAP", {})
    expected = publisher.generated(ROOT)
    target = ROOT / relative
    assert target.read_bytes() == expected[target]
