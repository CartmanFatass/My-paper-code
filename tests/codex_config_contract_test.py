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
    "hmasd-cpm-agentify-transport": ("gpt-5.6-luna", "medium", "danger-full-access"),
    "hmasd-explorer-agentify-transport": ("gpt-5.6-luna", "medium", "danger-full-access"),
    "hmasd-research-scout": ("gpt-5.6-sol", "high", "read-only"),
    "hmasd-research-critic": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-general-leaf": ("gpt-5.6-luna", "xhigh", "danger-full-access"),
    "hmasd-research-innovator": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-research-principles-analyst": ("gpt-5.6-sol", "max", "read-only"),
    "hmasd-implementer": ("gpt-5.6-sol", "high", "workspace-write"),
    "hmasd-routine-implementer": ("gpt-5.6-terra", "high", "workspace-write"),
}
TASK_NAME_CODES = {
    "cs": "hmasd-cm-scout",
    "rv": "hmasd-reviewer",
    "vf": "hmasd-verifier",
    "op": "hmasd-experiment-operator",
    "et": "hmasd-cpm-agentify-transport",
    "pt": "hmasd-explorer-agentify-transport",
    "rs": "hmasd-research-scout",
    "rc": "hmasd-research-critic",
    "gl": "hmasd-general-leaf",
    "ri": "hmasd-research-innovator",
    "rp": "hmasd-research-principles-analyst",
    "im": "hmasd-implementer",
    "rt": "hmasd-routine-implementer",
}


def test_registered_agent_profiles_are_exact_and_semantically_thin() -> None:
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    assert config["sandbox_mode"] == "danger-full-access"
    assert config["approval_policy"] == "never"
    assert config["agents"]["max_concurrent_threads_per_session"] == 8
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
    for example in ("rv_s_xh_plan", "gl_l_xh_pdf", "pt_l_m_pro"):
        assert example in agents


def test_each_leaf_profile_points_to_only_its_own_observation_role() -> None:
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
        "hmasd-research-innovator": "Innovation status:",
        "hmasd-research-principles-analyst": "Principles status:",
        "hmasd-implementer": "Implementation observation:",
        "hmasd-routine-implementer": "Routine implementation observation:",
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
        "PRO_TRANSPORT.md", "ENGINEERING_TRANSPORT.md", "EXPERIMENT_OPERATOR.md",
    ):
        role = (ROOT / ".agents/roles" / filename).read_text(encoding="utf-8")
        assert "## Fact check and parent convergence" not in role


def test_pro_transport_uses_exact_file_backed_strict_review() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    profile = tomllib.loads(
        (ROOT / ".codex/agents/hmasd-explorer-agentify-transport.toml").read_text(
            encoding="utf-8"
        )
    )["developer_instructions"]
    role = (ROOT / ".agents/roles/PRO_TRANSPORT.md").read_text(encoding="utf-8")
    skill = (ROOT / ".agents/skills/hmasd-agentify-transport/SKILL.md").read_text(
        encoding="utf-8"
    )
    manual = (ROOT / "docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md").read_text(
        encoding="utf-8"
    )
    instructions = " ".join("\n".join((role, skill, manual)).split())
    for required in (
        "agentify_review_query", "GPT-5.6 Pro", "GitHub connector",
        "origin-reachable commit", "scientific reference", "not a request for general code review",
        "promptPath", "verifyExisting", "natural completion",
    ):
        assert required in instructions
    for state in (
        "PENDING", "ZERO_SEND_FAILED", "COMMITMENT_UNKNOWN", "SENT_WAITING",
        "COMPLETE", "SENT_INPUT_MISMATCH", "SENT_UNREADABLE",
        "SENT_MODEL_MISMATCH", "CONVERSATION_LOST", "WAIVED",
    ):
        assert state in agents
    assert "exact frozen prompt file" in instructions
    assert "must not compose" in instructions
    assert "call `agentify_review_query` exactly once" in instructions
    assert "valid unwaived assignment is not silently left unsent" in instructions
    assert "Never make a second send-capable call" in instructions
    assert "Do not block on the first stale view" in instructions
    assert "do not loop or follow a fixed UI checklist" in instructions
    assert "ordinary `agentify_query`" in instructions
    assert "observation bound" in instructions
    assert "stop condition" in instructions
    for conversation_fact in (
        "tab is not a conversation",
        "exact visible label `Pro`",
        "up to 45 minutes",
        "responsePath",
        "new provider conversation",
        "same material cycle",
        "late content",
    ):
        assert conversation_fact in instructions
    assert ".agents/skills/hmasd-agentify-transport/SKILL.md" in role
    assert ".agents/roles/PRO_TRANSPORT.md" in profile


def test_profiles_are_thin_role_pointers_with_bounded_context() -> None:
    role_files = {
        "hmasd-cm-scout": "CM_SCOUT.md",
        "hmasd-reviewer": "REVIEWER.md",
        "hmasd-verifier": "VERIFIER.md",
        "hmasd-experiment-operator": "EXPERIMENT_OPERATOR.md",
        "hmasd-cpm-agentify-transport": "ENGINEERING_TRANSPORT.md",
        "hmasd-explorer-agentify-transport": "PRO_TRANSPORT.md",
        "hmasd-research-scout": "RESEARCH_SCOUT.md",
        "hmasd-research-critic": "RESEARCH_CRITIC.md",
        "hmasd-general-leaf": "GENERAL_LEAF.md",
        "hmasd-research-innovator": "RESEARCH_INNOVATOR.md",
        "hmasd-research-principles-analyst": "RESEARCH_PRINCIPLES_ANALYST.md",
        "hmasd-implementer": "IMPLEMENTER.md",
        "hmasd-routine-implementer": "ROUTINE_IMPLEMENTER.md",
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
        "docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md",
        ".agents/roles/PRO_TRANSPORT.md",
        ".agents/roles/ENGINEERING_TRANSPORT.md",
        ".agents/roles/RESEARCH_INNOVATOR.md",
        ".agents/roles/IMPLEMENTER.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert all(fragment not in text for fragment in exhaustive_fragments)
    manual = (ROOT / "docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md").read_text(
        encoding="utf-8"
    )
    assert "`AGENTS.md` is the only human-readable glossary" in manual


def test_legacy_agent_profiles_are_absent() -> None:
    forbidden = {
        "hmasd-project-scout", "hmasd-code-scout", "hmasd-implementer-terra",
        "hmasd-research-artifact-writer",
        "hmasd-external-pro-transport", "hmasd-external-gemini-transport",
    }
    assert not any((ROOT / ".codex/agents" / f"{name}.toml").exists() for name in forbidden)
