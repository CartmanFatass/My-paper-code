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
    "hmasd-experiment-operator": ("gpt-5.6-luna", "low", "danger-full-access"),
    "hmasd-cpm-agentify-transport": ("gpt-5.6-luna", "medium", "danger-full-access"),
    "hmasd-explorer-agentify-transport": ("gpt-5.6-luna", "medium", "danger-full-access"),
    "hmasd-research-scout": ("gpt-5.6-sol", "high", "read-only"),
    "hmasd-research-critic": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-general-leaf": ("gpt-5.6-luna", "xhigh", "danger-full-access"),
}
ALIASES = {
    "cs": "hmasd-cm-scout",
    "rv": "hmasd-reviewer",
    "vf": "hmasd-verifier",
    "op": "hmasd-experiment-operator",
    "et": "hmasd-cpm-agentify-transport",
    "pt": "hmasd-explorer-agentify-transport",
    "rs": "hmasd-research-scout",
    "rc": "hmasd-research-critic",
    "gl": "hmasd-general-leaf",
}


def test_registered_agent_profiles_are_exact_and_nonspawning() -> None:
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert config["sandbox_mode"] == "danger-full-access"
    assert config["approval_policy"] == "never"
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
    assert "NO_MATERIAL_INSIGHT" not in general["developer_instructions"]
    assert "no new decision-relevant observation" in general["developer_instructions"]
    pro = tomllib.loads(
        (ROOT / ".codex/agents/hmasd-explorer-agentify-transport.toml").read_text(encoding="utf-8")
    )
    assert "neutral frozen scope" in pro["developer_instructions"]
    assert "must not receive the Innovator transcript" in pro["developer_instructions"]
    assert "Call agentify_query at most once" in pro["developer_instructions"]
    assert "COMMITMENT_UNKNOWN" in pro["developer_instructions"]
    assert "observe and never resend" in pro["developer_instructions"]


def test_short_subagent_aliases_cover_the_exact_registered_roster() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert set(ALIASES.values()) == set(EXPECTED)
    for alias, profile in ALIASES.items():
        assert f"| `{alias}` | `{profile}` |" in agents
    assert "<alias>_<model>_<effort>_<task>" in agents
    for example in ("rv_s_xh_plan", "gl_l_xh_pdf", "pt_l_m_pro"):
        assert example in agents


def test_each_leaf_returns_only_its_own_observation_namespace() -> None:
    markers = {
        "hmasd-cm-scout": "Surface status:",
        "hmasd-reviewer": "Review status:",
        "hmasd-verifier": "Verification observation:",
        "hmasd-experiment-operator": "Run observation:",
        "hmasd-cpm-agentify-transport": "Engineering transport state:",
        "hmasd-explorer-agentify-transport": "Pro transport state:",
        "hmasd-research-scout": "Evidence status:",
        "hmasd-research-critic": "Critique status:",
        "hmasd-general-leaf": "Chore status:",
    }
    forbidden = (
        "Outcome:", "Root status:", "Integration status:", "Portfolio action:",
        "Capacity action:", "Scientific status:", "Decision impact:",
        "Recommendation:", "Pro Innovator:", "Pro Convergence:",
        "Engineering status:", "Observation status:", "Verification status:", "Commit:",
    )
    for name, own_marker in markers.items():
        instructions = tomllib.loads(
            (ROOT / ".codex/agents" / f"{name}.toml").read_text(encoding="utf-8")
        )["developer_instructions"]
        assert own_marker in instructions
        assert all(field not in instructions for field in forbidden)
        assert "top-level task" not in instructions


def test_pro_transport_uses_remote_github_research_query_and_bounded_preflight() -> None:
    instructions = tomllib.loads(
        (ROOT / ".codex/agents/hmasd-explorer-agentify-transport.toml").read_text(
            encoding="utf-8"
        )
    )["developer_instructions"]
    for required in (
        "agentify_query", "expectedModel=GPT-5.6 Pro", "GitHub connector",
        "origin-reachable commit", "scientific reference", "not a general code",
        "agentify_wait_response", "ZERO_SEND_FAILED", "COMMITMENT_UNKNOWN",
        "SENT_WAITING", "COMPLETE", "SENT_UNREADABLE",
    ):
        assert required in instructions
    assert "at most two fresh-tab preflight recoveries" in instructions
    assert "Call agentify_query at most once" in instructions
    assert "attachments" in instructions and "omit" in instructions
    assert "contextPaths" in instructions and "omit" in instructions
    assert "agentify_review_query" in instructions and "Do not use" in instructions
    assert "observation bound and stop condition" in instructions
    assert "provider received no request and created no operation" in instructions
    assert "one active send tab/key" in instructions


def test_legacy_agent_profiles_are_absent() -> None:
    forbidden = {
        "hmasd-project-scout", "hmasd-code-scout", "hmasd-implementer",
        "hmasd-implementer-terra", "hmasd-research-innovator",
        "hmasd-research-principles-analyst", "hmasd-research-artifact-writer",
        "hmasd-external-pro-transport", "hmasd-external-gemini-transport",
    }
    assert not any((ROOT / ".codex/agents" / f"{name}.toml").exists() for name in forbidden)
