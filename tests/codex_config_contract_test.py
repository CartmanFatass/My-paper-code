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
    "hmasd-verifier": ("gpt-5.6-luna", "high", "workspace-write"),
    "hmasd-experiment-operator": ("gpt-5.6-luna", "low", "danger-full-access"),
    "hmasd-research-scout": ("gpt-5.6-sol", "high", "read-only"),
    "hmasd-research-critic": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-general-leaf": ("gpt-5.6-luna", "xhigh", "danger-full-access"),
    "hmasd-research-innovator": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-research-principles-analyst": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-implementer": ("gpt-5.6-sol", "high", "workspace-write"),
    "hmasd-routine-implementer": ("gpt-5.6-terra", "high", "workspace-write"),
    "hmasd-workflow-designer": ("gpt-5.6-luna", "xhigh", "read-only"),
    "hmasd-design-reviewer": ("gpt-5.6-luna", "max", "read-only"),
}
TASK_NAME_CODES = {
    "cs": "hmasd-cm-scout",
    "rv": "hmasd-reviewer",
    "vf": "hmasd-verifier",
    "op": "hmasd-experiment-operator",
    "rs": "hmasd-research-scout",
    "rc": "hmasd-research-critic",
    "gl": "hmasd-general-leaf",
    "ri": "hmasd-research-innovator",
    "rp": "hmasd-research-principles-analyst",
    "im": "hmasd-implementer",
    "rt": "hmasd-routine-implementer",
    "wd": "hmasd-workflow-designer",
    "dr": "hmasd-design-reviewer",
}


def test_registered_agent_profiles_are_exact_and_semantically_thin() -> None:
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert config["sandbox_mode"] == "danger-full-access"
    assert config["approval_policy"] == "never"
    assert config["agents"]["max_concurrent_threads_per_session"] == 40
    assert "max_depth" not in config["agents"]
    assert "max_threads" not in config["agents"]
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
        normalized = " ".join(profile["developer_instructions"].split())
        assert "Read the exact assignment" in normalized
        assert "Apply only that role method" in normalized
        assert "universal boundaries come from `AGENTS.md`" in normalized
        for duplicated in (
            "fork_turns=1", "Never spawn", "spawning parent", "Never commit",
            "Role owns", "observation:", "status:", "transport state:",
        ):
            assert duplicated not in profile["developer_instructions"]
    general_role = (ROOT / ".agents/roles/GENERAL_LEAF.md").read_text(encoding="utf-8")
    assert "owner judgment" in general_role
    assert "assigned output" in general_role


def test_short_task_name_codes_cover_the_exact_registered_roster() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert set(TASK_NAME_CODES.values()) == set(EXPECTED)
    for code, profile in TASK_NAME_CODES.items():
        assert f"| `{code}` | `{profile}` |" in agents
    assert "Codex has no native alias field for these codes" in agents
    assert "<code>_<model>_<effort>_<task>" in agents
    for example in ("rv_s_xh_plan", "gl_l_xh_pdf", "wd_l_xh_design", "dr_l_mx_review"):
        assert example in agents


def test_each_leaf_profile_points_to_only_its_own_observation_role() -> None:
    markers = {
        "hmasd-cm-scout": "Surface status:",
        "hmasd-reviewer": "Review status:",
        "hmasd-verifier": "Verification observation:",
        "hmasd-experiment-operator": "Run observation:",
        "hmasd-research-scout": "Evidence status:",
        "hmasd-research-critic": "Critique status:",
        "hmasd-general-leaf": "Chore status:",
        "hmasd-research-innovator": "Innovation status:",
        "hmasd-research-principles-analyst": "Principles status:",
        "hmasd-implementer": "Implementation observation:",
        "hmasd-routine-implementer": "Routine implementation observation:",
        "hmasd-workflow-designer": "Workflow design status:",
        "hmasd-design-reviewer": "Design review disposition:",
    }
    for name, own_marker in markers.items():
        instructions = tomllib.loads(
            (ROOT / ".codex/agents" / f"{name}.toml").read_text(encoding="utf-8")
        )["developer_instructions"]
        assert own_marker not in instructions
        role_path = instructions.split(".agents/roles/", 1)[1].split(".md", 1)[0] + ".md"
        role = (ROOT / ".agents/roles" / role_path).read_text(encoding="utf-8")
        assert own_marker.removesuffix(":") in " ".join(role.split())


def test_reviewer_fact_checks_premises_instead_of_inventing_requirements() -> None:
    role = (ROOT / ".agents/roles/REVIEWER.md").read_text(encoding="utf-8")
    normalized = " ".join(role.split())
    for required in (
        "fact-check every premise",
        "verified fact",
        "applicable authority",
        "violated behavior",
        "owner-supplied constraint",
        "Review status: INCOMPLETE",
    ):
        assert required in normalized
    assert "must not become a finding" in normalized
    assert "hmasd-cm-scout" in role
    assert "hmasd-research-scout" in role
    assert "hmasd-verifier" in role
    agents = " ".join((ROOT / "AGENTS.md").read_text(encoding="utf-8").split())
    assert "native `conflict packet` to its spawning parent" in agents


def test_depth_two_is_only_for_role_local_fact_check_and_parent_convergence() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    normalized = " ".join(agents.split())
    assert "sole depth-2 exception" in normalized
    assert "fact-check child cannot delegate" in normalized
    assert "conflict packet" in normalized
    assert "spawning parent" in normalized
    allowed = {
        "REVIEWER.md": ("hmasd-cm-scout", "hmasd-research-scout", "hmasd-verifier"),
        "RESEARCH_INNOVATOR.md": ("hmasd-research-scout", "hmasd-cm-scout"),
        "RESEARCH_PRINCIPLES_ANALYST.md": ("hmasd-research-scout", "hmasd-cm-scout"),
        "RESEARCH_CRITIC.md": ("hmasd-research-scout", "hmasd-cm-scout"),
        "IMPLEMENTER.md": ("hmasd-cm-scout", "hmasd-verifier"),
        "ROUTINE_IMPLEMENTER.md": ("hmasd-cm-scout", "hmasd-verifier"),
    }
    for filename, fact_checkers in allowed.items():
        role = (ROOT / ".agents/roles" / filename).read_text(encoding="utf-8")
        flat = " ".join(role.split())
        assert "## Fact check and parent convergence" in role
        assert "Under the AGENTS fact-check boundary" in flat
        assert "unresolved conflict returns" in flat
        for fact_checker in fact_checkers:
            assert fact_checker in role
    for filename in (
        "CM_SCOUT.md", "RESEARCH_SCOUT.md", "VERIFIER.md", "GENERAL_LEAF.md",
        "EXPERIMENT_OPERATOR.md",
    ):
        role = (ROOT / ".agents/roles" / filename).read_text(encoding="utf-8")
        assert "## Fact check and parent convergence" not in role


def test_browser_conversation_uses_semantic_page_reasoning_and_one_strict_send() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    skill = (ROOT / ".agents/skills/hmasd-browser-conversation/SKILL.md").read_text(
        encoding="utf-8"
    )
    em = (ROOT / ".agents/skills/hmasd-em-task/SKILL.md").read_text(encoding="utf-8")
    instructions = " ".join(skill.split())
    for required in (
        "Agentify strict review", "GPT-5.6 Pro", "frozen prompt path",
        "observe → interpret → act → verify", "Computer Use",
        "full response is written to the exact response path",
    ):
        assert required in instructions
    for owner_prompt_requirement in (
        "GitHub connector", "origin-reachable", "exact commit",
        "scientific reference", "never as a general code-review assignment",
    ):
        assert owner_prompt_requirement in em
    for state in (
        "PENDING", "ZERO_SEND_FAILED", "COMMITMENT_UNKNOWN", "SENT_WAITING",
        "COMPLETE", "SENT_INPUT_MISMATCH", "SENT_UNREADABLE",
        "SENT_MODEL_MISMATCH", "CONVERSATION_LOST", "WAIVED",
    ):
        assert state in agents
    assert "Never compose, shorten" in instructions
    assert "Invoke it once for one operation" in instructions
    assert "exclusive send-capable actuator" in instructions
    assert "Computer Use must not click Send" in instructions
    assert "Do not loop an unchanged failure" in instructions
    assert "ordinary query" in instructions
    assert "stop or reentry condition" in instructions
    for conversation_fact in (
        "browser tab is a replaceable local view",
        "45-minute window",
        "New conversation",
        "causal assistant turn",
        "close the replaceable tab",
        "scientific or engineering judgment",
    ):
        assert conversation_fact in instructions
    assert "same material cycle" not in instructions
    assert "one long-lived Luna/xhigh Browser Transport task" in instructions
    assert not (ROOT / ".agents/roles/BROWSER_CONVERSATION.md").exists()
    assert not (ROOT / ".codex/agents/hmasd-browser-conversation.toml").exists()


def test_profiles_are_thin_role_pointers_with_bounded_context() -> None:
    role_files = {
        "hmasd-cm-scout": "CM_SCOUT.md",
        "hmasd-reviewer": "REVIEWER.md",
        "hmasd-verifier": "VERIFIER.md",
        "hmasd-experiment-operator": "EXPERIMENT_OPERATOR.md",
        "hmasd-research-scout": "RESEARCH_SCOUT.md",
        "hmasd-research-critic": "RESEARCH_CRITIC.md",
        "hmasd-general-leaf": "GENERAL_LEAF.md",
        "hmasd-research-innovator": "RESEARCH_INNOVATOR.md",
        "hmasd-research-principles-analyst": "RESEARCH_PRINCIPLES_ANALYST.md",
        "hmasd-implementer": "IMPLEMENTER.md",
        "hmasd-routine-implementer": "ROUTINE_IMPLEMENTER.md",
        "hmasd-workflow-designer": "WORKFLOW_DESIGNER.md",
        "hmasd-design-reviewer": "DESIGN_REVIEWER.md",
    }
    for name, role_file in role_files.items():
        instructions = tomllib.loads(
            (ROOT / ".codex/agents" / f"{name}.toml").read_text(encoding="utf-8")
        )["developer_instructions"]
        assert f".agents/roles/{role_file}" in instructions
        normalized = " ".join(instructions.split())
        assert "Apply only that role method" in normalized
        assert "universal boundaries come from `AGENTS.md`" in normalized
        assert "docs/project/WORKFLOW_PROTOCOL.md" not in instructions
        assert len(instructions) < 250


def test_workflow_design_profiles_are_read_only_and_root_cannot_self_approve() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    root_skill = (ROOT / ".agents/skills/hmasd-root-task/SKILL.md").read_text(encoding="utf-8")
    reviewer = (ROOT / ".agents/roles/REVIEWER.md").read_text(encoding="utf-8")
    root_flat = " ".join(root_skill.split())

    assert "| Root | `gl`, `wd`, `dr` |" in agents
    assert "Root has no authority to design workflow, control-plane, protocol, role, or skill topology" in agents
    assert "`rv` cannot satisfy this design-review role" in agents
    assert "APPROVED_WITH_AMENDMENTS" not in agents
    assert "hmasd-workflow-designer" in root_skill
    assert "hmasd-design-reviewer" in root_skill
    assert "There is no second reviewer, amendment disposition, quorum, or rereview loop" in root_flat
    assert "shared workflow repair" not in root_skill
    assert "review the same object twice" not in root_skill
    assert "after repair, review only the affected delta" not in root_skill
    assert "workflow, control-plane, protocol, role, or skill topology design" in reviewer.lower()
    assert "Review status: INCOMPLETE" in reviewer


def test_agents_is_the_only_human_readable_shared_field_glossary() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Shared field semantics" in agents
    assert "only human-readable glossary for shared top-level, transport, and leaf result" in agents
    assert "Schemas and tests may mirror values mechanically but do not define" in agents
    assert "Top-level outcome meanings are exhaustive" in agents
    assert "Transport states are shared facts" in agents
    exhaustive_fragments = (
        "Outcome: DONE | WAITING | FAILED | CANCELLED",
        "PENDING`: no send-capable call occurred",
        "ZERO_SEND_FAILED`: the provider definitely received no request",
        "SENT_INPUT_MISMATCH`: a send is confirmed",
        "Innovation status: CANDIDATE | NO_SURVIVING_CANDIDATE | INCOMPLETE",
        "Implementation observation: IMPLEMENTED | PARTIAL | BLOCKED",
        "`COMPLETE` requires",
    )
    for relative in (
        "docs/project/WORKFLOW_PROTOCOL.md",
        ".agents/skills/hmasd-browser-conversation/SKILL.md",
        ".agents/roles/RESEARCH_INNOVATOR.md",
        ".agents/roles/IMPLEMENTER.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert all(fragment not in text for fragment in exhaustive_fragments)
def test_legacy_agent_profiles_are_absent() -> None:
    forbidden = {
        "hmasd-project-scout", "hmasd-code-scout", "hmasd-implementer-terra",
        "hmasd-research-artifact-writer",
        "hmasd-external-pro-transport", "hmasd-external-gemini-transport",
        "hmasd-cpm-agentify-transport", "hmasd-explorer-agentify-transport",
        "hmasd-browser-conversation",
    }
    assert not any((ROOT / ".codex/agents" / f"{name}.toml").exists() for name in forbidden)
