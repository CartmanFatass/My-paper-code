from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _flat(relative: str) -> str:
    return " ".join(_read(relative).split())


def test_browser_conversation_is_one_luna_xhigh_session_role() -> None:
    config = tomllib.loads(_read(".codex/config.toml"))
    entry = config["agents"]["HMASDBrowserConversation"]
    assert entry["config_file"] == "./agents/hmasd-browser-conversation.toml"

    profile = tomllib.loads(_read(".codex/agents/hmasd-browser-conversation.toml"))
    assert profile["model"] == "gpt-5.6-luna"
    assert profile["model_reasoning_effort"] == "xhigh"
    assert profile["sandbox_mode"] == "danger-full-access"
    assert profile["approval_policy"] == "never"
    instructions = " ".join(profile["developer_instructions"].split())
    assert ".agents/roles/BROWSER_CONVERSATION.md" in instructions
    assert "universal boundaries come from `AGENTS.md`" in instructions


def test_browser_conversation_skill_has_a_semantic_closed_loop() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    role = _flat(".agents/roles/BROWSER_CONVERSATION.md")

    for marker in (
        "local browser task model",
        "agent session, browser tab, and provider conversation",
        "observe → interpret → act → verify",
        "DOM, accessibility, URL, and provider conversation facts first",
        "screenshots and Computer Use",
        "only when semantic page evidence is insufficient",
        "one external conversation assignment until",
        "ordinary page-local recovery",
        "conditional observation",
        "elapsed time alone",
        "close the replaceable tab",
    ):
        assert marker in skill

    assert "understands the page, conversation stage, and browser-task progress" in role
    assert "scientific or engineering interpretation remains with the parent" in role
    assert "Portfolio" not in role


def test_computer_use_cannot_cross_the_send_boundary() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    assert "Agentify strict operation is the exclusive send-capable actuator" in skill
    assert "Computer Use must not click Send, press Enter in the composer" in skill
    for forbidden in ("Retry", "Continue", "Regenerate", "Answer now"):
        assert forbidden in skill
    assert "After any ambiguous send-capable event, observe only" in skill


def test_complete_is_bound_to_one_prompt_and_its_causal_response() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "exclusive writer ownership",
        "exact baseline turn identity",
        "exactly one provider-visible user turn equal to the frozen prompt",
        "causally associated assistant turn",
        "Unexpected turn drift",
        "observe-only ambiguity",
        "full naturally completed response",
        "written to the exact response path and reread",
    ):
        assert marker in skill


def test_unbound_provider_root_is_not_treated_as_an_isolated_new_conversation() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "root URL or a New conversation action is intent, not proof",
        "unbound root composer can be shared across tabs",
        "serialize first-binding preparation and its strict send",
        "concrete provider conversation ID",
        "tool-local ephemeral root-writer mutex",
        "must not type, paste, clear, select, or delete composer content",
    ):
        assert marker in skill


def test_old_blind_transport_roles_are_absent_from_the_active_surface() -> None:
    for relative in (
        ".codex/agents/hmasd-cpm-agentify-transport.toml",
        ".codex/agents/hmasd-explorer-agentify-transport.toml",
        ".agents/roles/PRO_TRANSPORT.md",
        ".agents/roles/ENGINEERING_TRANSPORT.md",
        ".agents/skills/hmasd-agentify-transport/SKILL.md",
        "docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md",
    ):
        assert not (ROOT / relative).exists(), relative

    active = "\n".join(
        _read(relative)
        for relative in (
            "AGENTS.md",
            ".codex/config.toml",
            ".agents/skills/hmasd-em-task/SKILL.md",
            ".agents/skills/hmasd-cm-task/SKILL.md",
            "docs/project/WORKFLOW_PROTOCOL.md",
        )
    )
    for stale in (
        "hmasd-cpm-agentify-transport",
        "hmasd-explorer-agentify-transport",
        "hmasd-agentify-transport",
        "PRO_TRANSPORT",
        "ENGINEERING_TRANSPORT",
        "existing `pt`",
        "existing `et`",
    ):
        assert stale not in active
    assert "`bc`" in active
    assert "hmasd-browser-conversation" in active


def test_browser_conversation_returns_only_its_local_fact_namespace() -> None:
    agents = _flat("AGENTS.md")
    role = _flat(".agents/roles/BROWSER_CONVERSATION.md")
    assert "| `bc` | `hmasd-browser-conversation` | `Browser conversation state: <transport state>` |" in agents
    assert "EM | `gl`, `rs`, `ri`, `rp`, `rc`, `bc`" in agents
    assert "CM | `gl`, `cs`, `im`, `rt`, `rv`, `vf`, `op`, `bc`" in agents
    assert "Browser conversation state" in role
    for leaked in (
        "Scientific status:",
        "Engineering status:",
        "Portfolio action:",
        "Recommendation:",
    ):
        assert leaked not in role
