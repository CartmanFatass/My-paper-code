"""Proof-sized contracts for the Root -> L1 manager -> L2 leaf topology."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".codex" / "config.toml"

MANAGERS = {
    "hmasd-workflow-design-manager": {
        "profile": ROOT / ".codex/agents/hmasd-workflow-design-manager.toml",
        "role": ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
        "parent": "workflow_design_manager",
        "model": "gpt-5.6-sol",
        "effort": "high",
        "allow": ("hmasd-workflow-auditor", "hmasd-workflow-implementer", "hmasd-workflow-reviewer"),
    },
    "hmasd-code-project-manager": {
        "profile": ROOT / ".codex/agents/hmasd-code-project-manager.toml",
        "role": ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md",
        "parent": "code_project_manager",
        "model": "gpt-5.6-sol",
        "effort": "high",
        "allow": (
            "hmasd-code-scout", "hmasd-implementer", "hmasd-implementer-terra",
            "hmasd-reviewer", "hmasd-verifier", "hmasd-experiment-operator",
            "hmasd-cpm-mechanical", "hmasd-cpm-agentify-transport",
        ),
    },
    "hmasd-independent-research-explorer": {
        "profile": ROOT / ".codex/agents/hmasd-independent-research-explorer.toml",
        "role": ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
        "parent": "independent_research_explorer",
        "model": "gpt-5.6-sol",
        "effort": "max",
        "allow": (
            "hmasd-research-scout", "hmasd-research-innovator", "hmasd-research-critic",
            "hmasd-research-principles-analyst", "hmasd-explorer-mechanical",
            "hmasd-research-artifact-writer", "hmasd-explorer-agentify-transport",
        ),
    },
}

LEAF_ROLES = {
    "hmasd-code-scout": "CODE_SCOUT.md",
    "hmasd-cpm-agentify-transport": "CPM_AGENTIFY_TRANSPORT_OPERATOR.md",
    "hmasd-cpm-mechanical": "CPM_MECHANICAL_OPERATOR.md",
    "hmasd-experiment-operator": "EXPERIMENT_OPERATOR.md",
    "hmasd-explorer-agentify-transport": "EXPLORER_AGENTIFY_TRANSPORT_OPERATOR.md",
    "hmasd-explorer-mechanical": "EXPLORER_MECHANICAL_OPERATOR.md",
    "hmasd-implementer": "IMPLEMENTER.md",
    "hmasd-implementer-terra": "ROUTINE_IMPLEMENTER.md",
    "hmasd-reviewer": "REVIEWER.md",
    "hmasd-verifier": "VERIFIER.md",
    "hmasd-research-scout": "RESEARCH_SCOUT.md",
    "hmasd-research-innovator": "RESEARCH_INNOVATOR.md",
    "hmasd-research-critic": "RESEARCH_CRITIC.md",
    "hmasd-research-principles-analyst": "RESEARCH_PRINCIPLES_ANALYST.md",
    "hmasd-research-artifact-writer": "RESEARCH_ARTIFACT_WRITER.md",
    "hmasd-workflow-auditor": "WORKFLOW_AUDITOR.md",
    "hmasd-workflow-implementer": "WORKFLOW_IMPLEMENTER.md",
    "hmasd-workflow-reviewer": "WORKFLOW_REVIEWER.md",
}

PROFILE_COUNT = 21
ROLE_COUNT = 22
NON_LEAF_ROLE_FILES = {"EXTERNAL_PRO.md"}
ACTIVE_AGENTIFY_TRANSPORTS = {
    "hmasd-cpm-agentify-transport",
    "hmasd-explorer-agentify-transport",
}


def _load(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def _flat(text: str) -> str:
    return " ".join(text.split()).lower()


def test_config_declares_depth_two_and_twenty_thread_capacity() -> None:
    config = _load(CONFIG)
    agents = config["agents"]
    assert agents["max_threads"] == 20
    assert agents["max_depth"] == 2
    assert "max_concurrent_threads_per_session" not in agents
    hooks = json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
    assert hooks["hooks"] == {}


def test_three_root_registered_l1_managers_have_frozen_routing() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    for name, spec in MANAGERS.items():
        assert spec["profile"].is_file(), name
        assert spec["role"].is_file(), name
        profile = _load(spec["profile"])
        assert profile["name"] == name
        assert profile["model"] == spec["model"]
        assert profile["model_reasoning_effort"] == spec["effort"]
        assert profile["sandbox_mode"] == "read-only"
        assert profile["approval_policy"] == "never"
        assert f'config_file = "./agents/{name}.toml"' in config
        instructions = _flat(str(profile.get("developer_instructions", "")))
        role = _flat(spec["role"].read_text(encoding="utf-8"))
        for required in ("agent_tree_level=1", "parent=root", "return", "root"):
            assert required in instructions or required in role, (name, required)
        assert "return_route=return_to_root" in role
        for child in spec["allow"]:
            assert child in instructions, (name, child)
        assert "spawn_authority=none" not in instructions

        for required in (
            'agent_type="default"',
            'model="gpt-5.6-luna"',
            'reasoning_effort="high"',
            'fork_turns="1"',
        ):
            assert required in role, (name, required)
        assert "native default" in role, (name, "native default")
        assert "exact bounded" in role, (name, "exact bounded")
        assert (
            "adds no generic profile or role" in role
            or "never gains durable, git, routing, science, runtime or acceptance authority" in role
        ), (name, "native default scope")

    callable_leaves = [child for spec in MANAGERS.values() for child in spec["allow"]]
    assert len(callable_leaves) == len(set(callable_leaves)) == len(LEAF_ROLES)
    assert set(callable_leaves) == set(LEAF_ROLES)
    assert ACTIVE_AGENTIFY_TRANSPORTS <= set(callable_leaves)
    assert "hmasd-agentify-transport" not in callable_leaves


def test_l1_scope_keys_allow_disjoint_manager_instances_without_a_global_singleton() -> None:
    router = _flat((ROOT / "AGENTS.md").read_text(encoding="utf-8"))
    wdm_role = _flat(
        (ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md").read_text(encoding="utf-8")
    )

    # Scope-key vocabulary is shared by the Root router, while the WDM Role
    # supplies the workflow-specific key.  Do not require CPM or Explorer to
    # expose detailed scope fields here: their scopes remain owner-defined.
    for required in (
        "scope-key",
        "(role, scope_key)",
        "unique per root tree",
        "multiple active wdms",
        "disjoint frozen scopes",
    ):
        assert required in router, required
    assert "workflow_scope_key" in wdm_role


def test_root_wdm_background_context_is_distinct_from_implementer_fork_context() -> None:
    router = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    wdm_profile = _load(ROOT / ".codex/agents/hmasd-workflow-design-manager.toml")
    wdm_role = _flat(
        (ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md").read_text(encoding="utf-8")
    )
    implementer_role = _flat(
        (ROOT / ".agents/roles/WORKFLOW_IMPLEMENTER.md").read_text(encoding="utf-8")
    )

    assert re.search(r"fork_turns\s*=\s*[\"']?1[\"']?", router, re.IGNORECASE)
    assert "fork_turns" not in wdm_profile
    assert "fork_turns=none" in wdm_role
    assert "fork_turns=none" in implementer_role
    assert "disjoint" in wdm_role
    assert "same writable path" in wdm_role


@pytest.mark.parametrize("leaf", sorted(LEAF_ROLES))
def test_registered_l2_profiles_and_roles_are_non_spawning_leaves(leaf: str) -> None:
    profile_path = ROOT / ".codex" / "agents" / f"{leaf}.toml"
    role_path = ROOT / ".agents" / "roles" / LEAF_ROLES[leaf]
    assert profile_path.is_file(), leaf
    assert role_path.is_file(), leaf
    profile = _load(profile_path)
    role = _flat(role_path.read_text(encoding="utf-8"))
    profile_text = _flat(profile_path.read_text(encoding="utf-8"))
    assert profile["name"] == leaf
    assert "agent_tree_level=2" in role or "agent_tree_level=2" in profile_text
    parent_matches = re.findall(
        r"parent=(workflow_design_manager|code_project_manager|independent_research_explorer)",
        role,
    )
    assert len(parent_matches) == 1
    callable_managers = [name for name, spec in MANAGERS.items() if leaf in spec["allow"]]
    assert len(callable_managers) == 1
    assert parent_matches == [MANAGERS[callable_managers[0]]["parent"]]
    for required in (
        "spawn_authority=none",
        "user_contact_authority=none",
        "cross_branch_transport=none",
        "canonical_state_write_authority=none",
        "git_authority=none",
    ):
        assert required in role or required in profile_text, (leaf, required)
    assert (
        "output_contract=conclusion_first_return_to_parent" in role
        or "output_contract=conclusion_first_return_to_parent" in profile_text
    )
    assert leaf != "default"


def test_l2_profiles_are_registered_once_and_artifact_writer_covers_durable_research() -> None:
    config = CONFIG.read_text(encoding="utf-8")
    profile_paths = {path.stem for path in (ROOT / ".codex/agents").glob("*.toml")}
    assert len(profile_paths) == PROFILE_COUNT
    assert profile_paths == set(MANAGERS) | set(LEAF_ROLES)
    role_paths = {path.name for path in (ROOT / ".agents/roles").glob("*.md")}
    expected_role_paths = {spec["role"].name for spec in MANAGERS.values()} | set(LEAF_ROLES.values())
    assert len(role_paths) == ROLE_COUNT
    assert role_paths == expected_role_paths | NON_LEAF_ROLE_FILES
    assert "hmasd-agentify-transport" not in LEAF_ROLES
    assert "hmasd-agentify-transport.toml" not in profile_paths
    assert "default" not in profile_paths
    for leaf in LEAF_ROLES:
        profile = ROOT / ".codex/agents" / f"{leaf}.toml"
        assert profile.is_file(), leaf
        assert config.count(profile.name) == 1, leaf
    continuity = ROOT / "local_research" / "RESEARCH_CONTINUITY.md"
    if continuity.is_file():
        writer = ROOT / ".codex/agents/hmasd-research-artifact-writer.toml"
        assert writer.is_file()
        assert "research-artifact-writer" in config
