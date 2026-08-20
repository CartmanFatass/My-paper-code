"""Focused checks for the direct Root, research, and code agent topology."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]

RETIRED_PATHS = (
    ".codex/agents/hmasd-workflow-design-manager.toml",
    ".codex/agents/hmasd-workflow-auditor.toml",
    ".codex/agents/hmasd-workflow-implementer.toml",
    ".codex/agents/hmasd-workflow-reviewer.toml",
    ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
    ".agents/roles/WORKFLOW_AUDITOR.md",
    ".agents/roles/WORKFLOW_IMPLEMENTER.md",
    ".agents/roles/WORKFLOW_REVIEWER.md",
    ".agents/skills/hmasd-collaborative-workflow-design/SKILL.md",
    ".agents/skills/hmasd-workflow-change-audit/SKILL.md",
    ".agents/skills/hmasd-writing-agent-assignments/SKILL.md",
    "docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md",
    "docs/project/L1_STARTUP_CONTEXT.md",
    "docs/project/SESSION_WORKSPACE_CONTRACT.md",
    "docs/project/WORKFLOW_MAP.md",
)

ROOT_CALLABLE_LEAF_ROLES = (
    "CODE_SCOUT.md",
    "CPM_AGENTIFY_TRANSPORT_OPERATOR.md",
    "CPM_MECHANICAL_OPERATOR.md",
    "EXPERIMENT_OPERATOR.md",
    "EXPLORER_AGENTIFY_TRANSPORT_OPERATOR.md",
    "EXPLORER_MECHANICAL_OPERATOR.md",
    "IMPLEMENTER.md",
    "PROJECT_SCOUT.md",
    "RESEARCH_ARTIFACT_WRITER.md",
    "RESEARCH_CRITIC.md",
    "RESEARCH_INNOVATOR.md",
    "RESEARCH_PRINCIPLES_ANALYST.md",
    "RESEARCH_SCOUT.md",
    "REVIEWER.md",
    "ROUTINE_IMPLEMENTER.md",
    "VERIFIER.md",
)


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _config() -> dict:
    return tomllib.loads(_text(".codex/config.toml"))


def test_workflow_manager_surfaces_are_not_active() -> None:
    for path in RETIRED_PATHS:
        assert not (ROOT / path).exists(), path

    config = _config()
    registered = "\n".join(config["agents"].keys()).lower()
    for retired in (
        "workflowdesignmanager",
        "workflowauditor",
        "workflowimplementer",
        "workflowreviewer",
    ):
        assert retired not in registered
    assert "hmasdworkflowrecoverymanager" in registered

    router = _text("AGENTS.md").lower()
    assert "workflow_design_manager" not in router
    assert "hmasd-workflow-design" not in router
    assert "wdm" not in router


def test_root_is_the_direct_default_executor() -> None:
    router = _text("AGENTS.md")
    root_role = _text(".agents/roles/ROOT.md")
    assert "The operational Root alone contacts the user" in router
    assert "performs final Git actions" in router
    assert "Handle truly trivial one-step work directly" in root_role
    assert "A simple task never requires" in root_role
    assert "ordinary_task=agent_type:default|model:gpt-5.6-terra" in root_role


def test_only_research_and_code_are_registered_domain_managers() -> None:
    config = _config()["agents"]
    assert config["HMASDCodeProjectManager"]["config_file"] == "./agents/hmasd-code-project-manager.toml"
    assert config["HMASDIndependentResearchExplorer"]["config_file"] == "./agents/hmasd-independent-research-explorer.toml"

    assert (ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md").is_file()
    assert (ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md").is_file()


def test_project_scout_is_optional_and_questions_are_split() -> None:
    router = " ".join(_text("AGENTS.md").split())
    role = " ".join(_text(".agents/roles/PROJECT_SCOUT.md").split())
    assert "common read-only Spark lookup utility" in router
    assert "Split independent owners, routes, files, or evidence families" in router
    assert "allowed_callers=root|code_project_manager|independent_research_explorer" in role
    assert "exactly one narrow factual question" in role
    assert "model=gpt-5.3-codex-spark" in role
    assert "default_fork_turns=1" in role


def test_every_registered_specialist_leaf_is_root_callable() -> None:
    for name in ROOT_CALLABLE_LEAF_ROLES:
        role = _text(f".agents/roles/{name}")
        assert "agent_tree_level=1_or_2" in role, name
        assert "parent=root" in role, name
        assert "default_fork_turns=1" in role or "fork_turns=1" in role, name


def test_root_native_child_prompt_and_model_routing_are_explicit() -> None:
    router = _text("AGENTS.md")
    root_role = _text(".agents/roles/ROOT.md")
    assert "Root may directly invoke every registered subagent" in router
    assert "simple_mechanical=agent_type:default|model:gpt-5.6-luna|reasoning_effort:high|fork_turns:1" in root_role
    assert "ordinary_task=agent_type:default|model:gpt-5.6-terra|reasoning_effort:high|fork_turns:1" in root_role
    assert "high_difficulty=agent_type:default|model:gpt-5.6-sol|reasoning_effort:high|fork_turns:1" in root_role
    assert "Complete exactly one bounded task and return the result to Root" in root_role
