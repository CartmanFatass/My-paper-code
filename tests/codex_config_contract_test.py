"""Focused contracts for the project-scoped native Codex configuration."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 project env
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT / ".codex"

EXPECTED_ROLE_RUNTIME = {
    "hmasd-code-scout": ("gpt-5.6-luna", "medium", "read-only", "never"),
    "hmasd-cpm-agentify-transport": ("gpt-5.6-luna", "medium", "workspace-write", "never"),
    "hmasd-experiment-operator": ("gpt-5.6-luna", "low", "workspace-write", "never"),
    "hmasd-explorer-agentify-transport": ("gpt-5.6-luna", "medium", "workspace-write", "never"),
    "hmasd-external-gemini-transport": ("gpt-5.6-luna", "high", "workspace-write", "never"),
    "hmasd-implementer-terra": ("gpt-5.6-terra", "high", "workspace-write", "never"),
    "hmasd-implementer": ("gpt-5.6-sol", "high", "workspace-write", "never"),
    "hmasd-project-scout": ("gpt-5.6-luna", "medium", "read-only", "never"),
    "hmasd-research-artifact-writer": ("gpt-5.6-luna", "medium", "workspace-write", "never"),
    "hmasd-research-critic": ("gpt-5.6-sol", "max", "read-only", "never"),
    "hmasd-research-innovator": ("gpt-5.6-sol", "max", "read-only", "never"),
    "hmasd-research-principles-analyst": ("gpt-5.6-sol", "max", "read-only", "never"),
    "hmasd-research-scout": ("gpt-5.6-sol", "high", "read-only", "never"),
    "hmasd-reviewer": ("gpt-5.6-sol", "xhigh", "read-only", "never"),
    "hmasd-verifier": ("gpt-5.6-luna", "high", "read-only", "never"),
}

INSTRUMENT_LEAF_ROLES = {
    "hmasd-research-scout",
    "hmasd-research-critic",
    "hmasd-research-principles-analyst",
    "hmasd-research-innovator",
    "hmasd-implementer",
    "hmasd-implementer-terra",
    "hmasd-verifier",
}


def _config() -> dict:
    return tomllib.loads((CODEX / "config.toml").read_text(encoding="utf-8"))


def test_project_config_retains_depth_value_and_references_existing_roles() -> None:
    config = _config()
    agents = config["agents"]
    # Runtime enforcement must be checked after restarting Codex because the
    # project configuration is loaded when the host starts.
    assert config["features"]["multi_agent_v2"] is True
    assert agents["max_depth"] == 1

    referenced = {
        key: (CODEX / entry["config_file"][2:]).resolve()
        for key, entry in agents.items()
        if isinstance(entry, dict) and "config_file" in entry
    }
    files = {path.resolve() for path in (CODEX / "agents").glob("*.toml")}
    assert referenced
    assert set(referenced.values()) == files
    assert all(path.is_file() for path in referenced.values())

    for path in files:
        role = tomllib.loads(path.read_text(encoding="utf-8"))
        name = role["name"]
        assert name in EXPECTED_ROLE_RUNTIME
        assert (
            role["model"],
            role["model_reasoning_effort"],
            role["sandbox_mode"],
            role["approval_policy"],
        ) == EXPECTED_ROLE_RUNTIME[name]
    assert {path.stem for path in files} == set(EXPECTED_ROLE_RUNTIME)
    assert "HMASDWorkflowRecoveryManager" not in agents
    assert not (CODEX / "agents" / "hmasd-workflow-recovery-manager.toml").exists()


def test_native_mcp_commands_do_not_use_wsl_executable_paths() -> None:
    config = _config()
    assert config["mcp_servers"]["agentify-desktop"]["command"] == "node"

    active_text = "\n".join(
        path.read_text(encoding="utf-8")
        for base in (CODEX, ROOT / ".agents")
        for path in base.rglob("*")
        if path.is_file() and path.suffix in {".toml", ".md"}
    ).lower()
    for forbidden in ("/mnt/", "/home/", "/usr/", "/opt/", "python3", "hub start", "hub logs", "hub wait"):
        assert forbidden not in active_text


def test_experiment_operator_uses_the_mechanical_result_file_contract() -> None:
    role = tomllib.loads(
        (CODEX / "agents" / "hmasd-experiment-operator.toml").read_text(
            encoding="utf-8"
        )
    )
    instructions = " ".join(role["developer_instructions"].lower().split())
    for required in (
        "execute exactly assignment.execute_argv",
        "operator-result.json is the authoritative result witness",
        "do not construct, rewrite, or replace that result file",
        "final response is not result evidence",
        "never silently retry",
    ):
        assert required in instructions


def test_instrument_capable_leaves_require_one_frozen_explicit_operation() -> None:
    for role_name in INSTRUMENT_LEAF_ROLES:
        role = tomllib.loads(
            (CODEX / "agents" / f"{role_name}.toml").read_text(encoding="utf-8")
        )
        instructions = " ".join(role["developer_instructions"].lower().split())
        for required in (
            "capability_id",
            "hash-bound inputs",
            "judgment criteria",
            "requested output",
            "typed observation",
            "report unavailable",
            "do not install",
            "do not write the durable evidence sidecar",
        ):
            assert required in instructions, (role_name, required)


def test_experiment_operator_does_not_receive_the_instrument_contract() -> None:
    role = tomllib.loads(
        (CODEX / "agents" / "hmasd-experiment-operator.toml").read_text(
            encoding="utf-8"
        )
    )
    instructions = role["developer_instructions"].lower()

    for forbidden in ("capability_id", "instrument evidence", "validate-evidence"):
        assert forbidden not in instructions
