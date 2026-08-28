from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "hmasd-cm-scout": ("gpt-5.6-luna", "medium", "read-only"),
    "hmasd-reviewer": ("gpt-5.6-sol", "xhigh", "read-only"),
    "hmasd-verifier": ("gpt-5.6-luna", "high", "read-only"),
    "hmasd-experiment-operator": ("gpt-5.6-luna", "low", "workspace-write"),
    "hmasd-cpm-agentify-transport": ("gpt-5.6-luna", "medium", "workspace-write"),
    "hmasd-explorer-agentify-transport": ("gpt-5.6-luna", "medium", "workspace-write"),
    "hmasd-research-scout": ("gpt-5.6-sol", "high", "read-only"),
    "hmasd-research-critic": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-general-leaf": ("gpt-5.6-luna", "xhigh", "workspace-write"),
}


def test_registered_agent_profiles_are_exact_and_nonspawning() -> None:
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert config["agents"]["max_threads"] == 8
    assert config["agents"]["max_depth"] == 1
    profiles = {
        value["config_file"]
        for value in config["agents"].values()
        if isinstance(value, dict)
    }
    assert profiles == {f"./agents/{name}.toml" for name in EXPECTED}
    for name, expected in EXPECTED.items():
        profile = tomllib.loads((ROOT / ".codex/agents" / f"{name}.toml").read_text(encoding="utf-8"))
        assert (profile["model"], profile["model_reasoning_effort"], profile["sandbox_mode"]) == expected
        assert profile["approval_policy"] == "never"
        assert "Never spawn" in profile["developer_instructions"]
        assert "spawning parent" in profile["developer_instructions"]
    general = tomllib.loads(
        (ROOT / ".codex/agents/hmasd-general-leaf.toml").read_text(encoding="utf-8")
    )
    assert "Never commit or push" in general["developer_instructions"]
    assert "NO_MATERIAL_INSIGHT" in general["developer_instructions"]
    pro = tomllib.loads(
        (ROOT / ".codex/agents/hmasd-explorer-agentify-transport.toml").read_text(encoding="utf-8")
    )
    assert "neutral frozen scope" in pro["developer_instructions"]
    assert "not the Innovator transcript" in pro["developer_instructions"]
    assert "Send the frozen prompt at most once" in pro["developer_instructions"]
    assert "If send commitment" in pro["developer_instructions"]
    assert "is unknown, observe and never resend" in pro["developer_instructions"]


def test_legacy_agent_profiles_are_absent() -> None:
    forbidden = {
        "hmasd-project-scout", "hmasd-code-scout", "hmasd-implementer",
        "hmasd-implementer-terra", "hmasd-research-innovator",
        "hmasd-research-principles-analyst", "hmasd-research-artifact-writer",
        "hmasd-external-pro-transport", "hmasd-external-gemini-transport",
    }
    assert not any((ROOT / ".codex/agents" / f"{name}.toml").exists() for name in forbidden)
