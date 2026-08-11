"""Structural checks for the registered execution-readiness verifier route."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPOSITORY_ROOT / ".codex" / "config.toml"
ROUTER = REPOSITORY_ROOT / "AGENTS.md"
VERIFIER_PROFILE = REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-verifier.toml"
VERIFIER_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "VERIFIER.md"
MECHANICAL_PROFILE = REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-cpm-mechanical.toml"
MECHANICAL_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "CPM_MECHANICAL_OPERATOR.md"
EXPLORER_MECHANICAL_PROFILE = (
    REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-explorer-mechanical.toml"
)
EXPLORER_MECHANICAL_ROLE = (
    REPOSITORY_ROOT / ".agents" / "roles" / "EXPLORER_MECHANICAL_OPERATOR.md"
)
IMPLEMENTER_PROFILES = {
    "hmasd-implementer": (
        REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-implementer.toml",
        "gpt-5.6-sol",
        "high",
        ".agents/roles/IMPLEMENTER.md",
    ),
    "hmasd-implementer-terra": (
        REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-implementer-terra.toml",
        "gpt-5.6-terra",
        "high",
        ".agents/roles/ROUTINE_IMPLEMENTER.md",
    ),
}
IMPLEMENTER_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "IMPLEMENTER.md"

L1_PROFILES = {
    "hmasd-workflow-design-manager": (
        REPOSITORY_ROOT / ".codex/agents/hmasd-workflow-design-manager.toml",
        REPOSITORY_ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
        "gpt-5.6-sol",
        "high",
    ),
    "hmasd-code-project-manager": (
        REPOSITORY_ROOT / ".codex/agents/hmasd-code-project-manager.toml",
        REPOSITORY_ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md",
        "gpt-5.6-sol",
        "high",
    ),
    "hmasd-independent-research-explorer": (
        REPOSITORY_ROOT / ".codex/agents/hmasd-independent-research-explorer.toml",
        REPOSITORY_ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
        "gpt-5.6-sol",
        "max",
    ),
}

# Codex profile files use this small standard top-level surface. In
# particular, role metadata and child-pointer conveniences are not TOML
# profile fields; routing remains in the config table, developer instructions
# and the named Role charter.
STANDARD_L1_PROFILE_KEYS = {
    "name",
    "description",
    "model",
    "model_reasoning_effort",
    "sandbox_mode",
    "approval_policy",
    "nickname_candidates",
    "developer_instructions",
}
REJECTED_L1_PROFILE_KEYS = {
    "role",
    "role_pointer",
    "registered_child_pointers",
}
L1_REGISTRY = {
    "HMASDCodeProjectManager": {
        "name": "hmasd-code-project-manager",
        "profile": REPOSITORY_ROOT / ".codex/agents/hmasd-code-project-manager.toml",
        "role": REPOSITORY_ROOT / ".agents/roles/CODE_PROJECT_MANAGER.md",
        "model": "gpt-5.6-sol",
        "effort": "high",
        "children": (
            "hmasd-code-scout",
            "hmasd-implementer",
            "hmasd-implementer-terra",
            "hmasd-reviewer",
            "hmasd-verifier",
            "hmasd-experiment-operator",
            "hmasd-cpm-mechanical",
            "hmasd-cpm-agentify-transport",
        ),
    },
    "HMASDWorkflowDesignManager": {
        "name": "hmasd-workflow-design-manager",
        "profile": REPOSITORY_ROOT / ".codex/agents/hmasd-workflow-design-manager.toml",
        "role": REPOSITORY_ROOT / ".agents/roles/WORKFLOW_DESIGN_MANAGER.md",
        "model": "gpt-5.6-sol",
        "effort": "high",
        "children": (
            "hmasd-workflow-auditor",
            "hmasd-workflow-implementer",
            "hmasd-workflow-reviewer",
        ),
    },
    "HMASDIndependentResearchExplorer": {
        "name": "hmasd-independent-research-explorer",
        "profile": REPOSITORY_ROOT / ".codex/agents/hmasd-independent-research-explorer.toml",
        "role": REPOSITORY_ROOT / ".agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md",
        "model": "gpt-5.6-sol",
        "effort": "max",
        "children": (
            "hmasd-research-scout",
            "hmasd-research-innovator",
            "hmasd-research-critic",
            "hmasd-research-principles-analyst",
            "hmasd-explorer-mechanical",
            "hmasd-research-artifact-writer",
            "hmasd-explorer-agentify-transport",
        ),
    },
}


def test_verifier_registration_and_model_routing() -> None:
    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    registered = [
        (profile_path, profile)
        for profile_path, profile in profiles
        if profile.get("name") == "hmasd-verifier"
    ]
    assert len(registered) == 1, "verifier must have exactly one registered profile"

    profile_path, profile = registered[0]
    assert profile_path == VERIFIER_PROFILE
    assert profile["model"] == "gpt-5.6-luna"
    assert profile["model_reasoning_effort"] == "high"
    assert profile["sandbox_mode"] == "workspace-write"
    assert profile["approval_policy"] == "never"
    instructions = profile.get("developer_instructions", "")
    assert ".agents/roles/VERIFIER.md" in instructions

    assert VERIFIER_ROLE.is_file()
    role_text = VERIFIER_ROLE.read_text(encoding="utf-8")
    assert "role=verifier" in role_text


def test_cpm_mechanical_registration_and_model_routing() -> None:
    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    registered = [
        (profile_path, profile)
        for profile_path, profile in profiles
        if profile.get("name") == "hmasd-cpm-mechanical"
    ]
    assert len(registered) == 1, "CPM mechanical child must have exactly one registered profile"

    profile_path, profile = registered[0]
    assert profile_path == MECHANICAL_PROFILE
    assert profile["model"] == "gpt-5.6-luna"
    assert profile["model_reasoning_effort"] == "low"
    assert profile["sandbox_mode"] == "workspace-write"
    assert profile["approval_policy"] == "never"
    instructions = profile.get("developer_instructions", "")
    assert "CPM_MECHANICAL_TASK_ASSIGNMENT" in instructions
    assert "fork_turns=none" in instructions
    assert MECHANICAL_ROLE.is_file()
    role_text = MECHANICAL_ROLE.read_text(encoding="utf-8")
    assert "role=cpm_mechanical_operator" in role_text


def test_explorer_mechanical_registration_and_model_routing() -> None:
    assert EXPLORER_MECHANICAL_PROFILE.is_file()

    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    registered = [
        (profile_path, profile)
        for profile_path, profile in profiles
        if profile.get("name") == "hmasd-explorer-mechanical"
    ]
    assert len(registered) == 1, "Explorer mechanical child must have exactly one registered profile"
    profile_path, profile = registered[0]
    assert profile_path == EXPLORER_MECHANICAL_PROFILE
    assert profile["model"] == "gpt-5.6-luna"
    assert profile["model_reasoning_effort"] == "low"
    assert profile["sandbox_mode"] == "read-only"
    assert profile["approval_policy"] == "never"
    instructions = " ".join(str(profile.get("developer_instructions", "")).split())
    for required in (
        ".agents/roles/EXPLORER_MECHANICAL_OPERATOR.md",
        ".agents/skills/hmasd-explorer-mechanical/SKILL.md",
        "fork_turns=none",
        "self-contained natural-language task model",
        "one conclusion-first native result",
    ):
        assert required in instructions

    assert EXPLORER_MECHANICAL_ROLE.is_file()
    role_text = EXPLORER_MECHANICAL_ROLE.read_text(encoding="utf-8")
    for required in (
        "role=explorer_mechanical_operator",
        "callable_agent_type=hmasd-explorer-mechanical",
        "parent=independent_research_explorer",
        "write_authority=none",
        "scientific_authority=none",
        "technical_acceptance_authority=none",
        "runtime_authority=none",
    ):
        assert required in role_text


def test_implementer_registration_and_model_routing() -> None:
    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))

    for name, (
        expected_path,
        expected_model,
        expected_effort,
        expected_role_pointer,
    ) in IMPLEMENTER_PROFILES.items():
        registered = [
            (profile_path, profile)
            for profile_path, profile in profiles
            if profile.get("name") == name
        ]
        assert len(registered) == 1, f"{name} must have exactly one registered profile"
        profile_path, profile = registered[0]
        assert profile_path == expected_path
        assert profile["model"] == expected_model
        assert profile["model_reasoning_effort"] == expected_effort
        assert profile["sandbox_mode"] == "workspace-write"
        assert profile["approval_policy"] == "never"
        instructions = profile.get("developer_instructions", "")
        assert expected_role_pointer in instructions
        if name == "hmasd-implementer-terra":
            assert ".agents/roles/IMPLEMENTER.md" not in instructions
        assert "exact assignment" in instructions
        assert "registered child of Code Project Manager" in instructions
        assert "Do not mutate Git" in instructions
        for duplicated in (
            "purpose, observed behavior or failure",
            "necessary consequential scope",
            "Every result must begin with a concise natural-language conclusion",
            "scripts/hmasd_workspace_ticket.py",
            "absolute `apply_patch` targets",
            "core.longpaths=true",
            "Return status, changed files, checks",
        ):
            assert duplicated not in instructions

    role_text = IMPLEMENTER_ROLE.read_text(encoding="utf-8")
    role_text_normalized = " ".join(role_text.split())
    for required in (
        "Every result must begin with a concise natural-language conclusion",
        "what outcome was achieved or remains unresolved",
        "direct consumer or cross-module consequence checked",
        "residual uncertainty",
        "A mechanical status or changed-path list alone is not a complete result",
        "necessary consequential scope",
        "model strength adds no authority and never substitutes for a complete assignment",
        "rigid schema or admission gate",
    ):
        assert required in role_text_normalized

    terra_text = IMPLEMENTER_PROFILES["hmasd-implementer-terra"][0].read_text(encoding="utf-8")
    terra_text_normalized = " ".join(terra_text.split())
    assert "material or outcome-changing" in terra_text_normalized
    assert "reversible internal organization" in terra_text_normalized
    assert "You do not choose scientific semantics, architecture direction" not in terra_text
    sol_text = IMPLEMENTER_PROFILES["hmasd-implementer"][0].read_text(encoding="utf-8")
    assert "protected Sol route" in sol_text
    assert "assignment-specified semantics" in sol_text


def test_root_managers_are_read_only_l1_profiles_with_allow_lists() -> None:
    profiles = []
    for profile_path in sorted((REPOSITORY_ROOT / ".codex" / "agents").glob("*.toml")):
        with profile_path.open("rb") as stream:
            profiles.append((profile_path, tomllib.load(stream)))
    for name, (expected_path, role_path, model, effort) in L1_PROFILES.items():
        registered = [(path, data) for path, data in profiles if data.get("name") == name]
        assert len(registered) == 1
        path, profile = registered[0]
        assert path == expected_path
        assert profile["model"] == model
        assert profile["model_reasoning_effort"] == effort
        assert profile["sandbox_mode"] == "read-only"
        assert profile["approval_policy"] == "never"
        instructions = " ".join(str(profile.get("developer_instructions", "")).split()).lower()
        assert "agent_tree_level=1" in instructions
        assert "parent=root" in instructions
        assert "return" in instructions and "root" in instructions
        assert role_path.is_file()


def test_l1_registry_uses_standard_schema_and_static_routing_contracts() -> None:
    """Static checks only; they do not prove runtime registration/live spawn or repair completion."""
    with CONFIG.open("rb") as stream:
        config = tomllib.load(stream)
    agents = config["agents"]
    router = ROUTER.read_text(encoding="utf-8")

    for table_name, spec in L1_REGISTRY.items():
        table = agents.get(table_name)
        assert isinstance(table, dict), table_name
        profile_path = spec["profile"]
        role_path = spec["role"]
        assert profile_path.is_file(), profile_path
        assert role_path.is_file(), role_path
        assert table["config_file"] == f'./agents/{spec["name"]}.toml'

        with profile_path.open("rb") as stream:
            profile = tomllib.load(stream)
        assert profile["name"] == spec["name"]
        assert set(profile).issubset(STANDARD_L1_PROFILE_KEYS), (table_name, set(profile))
        required = {
            "name",
            "description",
            "model",
            "model_reasoning_effort",
            "sandbox_mode",
            "approval_policy",
            "developer_instructions",
        }
        assert required <= set(profile)
        assert profile["model"] == spec["model"]
        assert profile["model_reasoning_effort"] == spec["effort"]
        assert profile["sandbox_mode"] == "read-only"
        assert profile["approval_policy"] == "never"

        instructions = " ".join(str(profile["developer_instructions"]).split()).lower()
        role = " ".join(role_path.read_text(encoding="utf-8").split()).lower()
        assert "agent_tree_level=1" in instructions or "agent_tree_level=1" in role
        assert "parent=root" in instructions or "parent=root" in role
        assert ".agents/roles/" in instructions
        for child in spec["children"]:
            assert child in instructions or child in role, (table_name, child)

        # Local strict-doctor evidence rejects these metadata conveniences;
        # they must not return under another top-level profile key.
        assert not (set(profile) & REJECTED_L1_PROFILE_KEYS), (table_name, set(profile))

    for manager in ("HMASDWorkflowDesignManager", "HMASDIndependentResearchExplorer"):
        with L1_REGISTRY[manager]["profile"].open("rb") as stream:
            profile = tomllib.load(stream)
        instructions = " ".join(str(profile["developer_instructions"]).split()).lower()
        assert "root" in instructions and "fork_turns=1" in instructions, manager

    assert "workflow_design_manager_root_fork_turns=1_caller_action_only" in router
    assert "Root invokes every WDM L1 with caller action `fork_turns=1`" in router


def test_leaf_roles_and_profiles_explicitly_forbid_spawn_and_cross_owner_contact() -> None:
    role_paths = [
        REPOSITORY_ROOT / ".agents/roles/WORKFLOW_AUDITOR.md",
        REPOSITORY_ROOT / ".agents/roles/CODE_SCOUT.md",
        REPOSITORY_ROOT / ".agents/roles/RESEARCH_SCOUT.md",
        REPOSITORY_ROOT / ".agents/roles/EXPLORER_MECHANICAL_OPERATOR.md",
    ]
    for role_path in role_paths:
        role = " ".join(role_path.read_text(encoding="utf-8").split()).lower()
        assert "agent_tree_level=2" in role
        assert "spawn_authority=none" in role
        assert "return" in role and "parent" in role


if __name__ == "__main__":
    test_verifier_registration_and_model_routing()
    test_cpm_mechanical_registration_and_model_routing()
    test_explorer_mechanical_registration_and_model_routing()
    test_implementer_registration_and_model_routing()
    print("HMASD_MODEL_ROUTING_OK")
