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


def test_browser_transport_is_one_top_level_luna_xhigh_task_not_a_leaf() -> None:
    config = tomllib.loads(_read(".codex/config.toml"))
    assert "HMASDBrowserConversation" not in config["agents"]
    assert not (ROOT / ".codex/agents/hmasd-browser-conversation.toml").exists()
    assert not (ROOT / ".agents/roles/BROWSER_CONVERSATION.md").exists()

    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    openai_yaml = _read(
        ".agents/skills/hmasd-browser-conversation/agents/openai.yaml"
    )
    assert "five session skills" in agents
    assert "Browser Transport | `gpt-5.6-luna` | `xhigh`" in agents
    assert "one long-lived Luna/xhigh Browser Transport task" in skill
    assert 'display_name: "HMASD Browser Transport"' in openai_yaml
    assert "allow_implicit_invocation: false" in openai_yaml


def test_browser_transport_skill_has_a_semantic_closed_loop() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "assignment-local task model",
        "observe → interpret → act → verify",
        "DOM, accessibility, URL",
        "screenshots and the installed `computer-use:computer-use` skill",
        "only when DOM/accessibility evidence is insufficient",
        "ordinary page-local recovery",
        "elapsed time alone",
        "close the replaceable tab",
    ):
        assert marker in skill
    assert "do not behave like a fixed UI macro" in skill


def test_current_chatgpt_product_name_maps_only_to_the_real_pro_control() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "owner terms `GPT-5.6 Pro` and `GPT-5.6 Sol Pro`",
        "composer/model-picker control visibly labelled `Pro`",
        "Preserve the owner term and the visible label as separate facts",
        "account-plan/profile label",
        "never proves model selection",
        "https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt/",
    ):
        assert marker in skill


def test_computer_use_cannot_cross_the_send_boundary() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    assert "Agentify strict review is the exclusive send-capable actuator" in skill
    assert "Computer Use must not click Send, press Enter in the composer" in skill
    for forbidden in ("Retry", "Continue", "Regenerate", "Answer now"):
        assert forbidden in skill
    assert "After an ambiguous send-capable event, observe the same operation only" in skill


def test_complete_is_bound_to_one_prompt_and_its_causal_response() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "exclusive writer ownership",
        "exact baseline turn identity",
        "exactly one provider-visible user turn equals the frozen prompt",
        "causal assistant turn",
        "Unexpected turn drift",
        "observe-only ambiguity",
        "full response is written to the exact response path and reread",
    ):
        assert marker in skill


def test_unbound_provider_root_is_not_treated_as_an_isolated_conversation() -> None:
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "root URL or New conversation action is intent, not proof",
        "unbound root composer may be shared across tabs",
        "strict first-binding operation alone owns composer preparation",
        "root-writer mutex",
        "must not type, paste, clear, select, delete, or send composer content",
    ):
        assert marker in skill


def test_direction_task_assignment_operation_conversation_and_tab_are_distinct() -> None:
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "Browser Transport Codex task",
        "scientific direction is owner context, not transport identity",
        "(Return task, Direction, Owner stage, Transport assignment)",
        "strict operation is one send-capable attempt",
        "provider conversation is the durable remote conversation",
        "browser tab is a replaceable local view",
    ):
        assert marker in skill
    assert "Return task + Direction + Owner stage + Transport assignment" in agents
    assert "operation ID, tab ID, Agentify key, or content hash is never a direction" in agents


def test_multiplex_contract_handles_a_waiting_b_then_a_observe_without_crossing() -> None:
    protocol = _flat("docs/project/WORKFLOW_PROTOCOL.md")
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    for marker in (
        "multiple unfinished browser assignments",
        "native history order",
        "不合并消息",
        "一次只执行一个 send-capable 或 browser mutation action",
        "strict operation 返回 `SENT_WAITING`",
        "立即向 owner 发送当前 RESULT 并 yield",
        "后来 `OBSERVE_ONLY` 必须使用同一 locator",
        "绑定同一 strict operation 和 provider conversation",
    ):
        assert marker in protocol
    for marker in (
        "do not let one long Pro generation block unrelated eligible work",
        "service another assignment only when its native `[BROWSER WORK]` or",
        "observe a long-running conversation again only after an authorized `OBSERVE_ONLY`",
        "There is no self-wakeup, background polling loop, or implicit scheduler",
        "Never reuse a tab, key, current page, or direction name",
    ):
        assert marker in skill
    for text in (protocol, skill):
        assert "local queue" not in text
        assert "local registry" not in text


def test_browser_cancel_stays_in_the_transport_namespace() -> None:
    protocol = _flat("docs/project/WORKFLOW_PROTOCOL.md")
    agents = _flat("AGENTS.md")
    for marker in (
        "Browser Transport 从不输出 top-level `CANCELLED`",
        "若尚无 send-capable call，该 assignment 变为 `WAIVED`",
        "只有 EM/CM owner 在 committed Effect 达到安全事实后",
    ):
        assert marker in protocol
    assert "Browser Transport does not emit `Outcome`" in agents


def test_owner_acceptance_is_the_strict_operation_budget() -> None:
    agents = _flat("AGENTS.md")
    protocol = _flat("docs/project/WORKFLOW_PROTOCOL.md")
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    assert "the shared zero-send rule never expands an owner-frozen operation budget" in agents
    assert "`Acceptance` 是该 assignment 唯一的 operation budget" in protocol
    assert "`ZERO_SEND_FAILED` 本身不授权 operation two" in protocol
    assert "Treat the exact inbound `Acceptance` as the complete operation budget" in skill
    assert "do not create operation two" in skill


def test_em_and_cm_send_direct_browser_work_and_consume_transport_facts() -> None:
    agents = _flat("AGENTS.md")
    em = _flat(".agents/skills/hmasd-em-task/SKILL.md")
    cm = _flat(".agents/skills/hmasd-cm-task/SKILL.md")
    assert "External browser consultation is not a leaf" in agents
    assert "EM or CM sends a complete `[BROWSER WORK]` directly" in agents
    assert "Send one complete `[BROWSER WORK]` directly" in em
    assert "nonterminal `[BROWSER RESULT]`" in em
    assert "sends one complete `[BROWSER WORK]` directly" in cm
    assert "OBSERVE_ONLY" in cm
    assert "`bc`" not in "\n".join((agents, em, cm))


def test_old_blind_transport_roles_are_absent_from_the_active_surface() -> None:
    for relative in (
        ".codex/agents/hmasd-cpm-agentify-transport.toml",
        ".codex/agents/hmasd-explorer-agentify-transport.toml",
        ".codex/agents/hmasd-browser-conversation.toml",
        ".agents/roles/PRO_TRANSPORT.md",
        ".agents/roles/ENGINEERING_TRANSPORT.md",
        ".agents/roles/BROWSER_CONVERSATION.md",
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
    assert "hmasd-browser-conversation" in active


def test_browser_transport_returns_only_its_local_fact_namespace() -> None:
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/hmasd-browser-conversation/SKILL.md")
    assert "Browser Transport | `Browser transport state: <transport state>`" in agents
    assert "Do not emit top-level `Outcome`" in skill
    for leaked in (
        "Scientific status:",
        "Engineering status:",
        "Direction actions:",
        "Recommendation:",
        "Capacity action:",
    ):
        assert leaked not in skill
