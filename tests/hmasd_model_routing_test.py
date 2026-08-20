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
REVIEWER_PROFILE = REPOSITORY_ROOT / ".codex" / "agents" / "hmasd-reviewer.toml"
REVIEWER_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "REVIEWER.md"
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
ROOT_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "ROOT.md"
CODE_MANAGER_ROLE = REPOSITORY_ROOT / ".agents" / "roles" / "CODE_PROJECT_MANAGER.md"
MODEL_COST_RUNBOOK = (
    REPOSITORY_ROOT / "docs" / "project" / "HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md"
)

L1_PROFILES = {
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


def test_reviewer_is_scope_local_and_advisory() -> None:
    with REVIEWER_PROFILE.open("rb") as stream:
        profile = tomllib.load(stream)

    assert profile["name"] == "hmasd-reviewer"
    assert profile["model"] == "gpt-5.6-sol"
    assert profile["model_reasoning_effort"] == "xhigh"
    assert profile["sandbox_mode"] == "read-only"
    assert profile["approval_policy"] == "never"
    instructions = " ".join(str(profile["developer_instructions"]).split())
    assert ".agents/roles/REVIEWER.md" in instructions

    role_text = " ".join(REVIEWER_ROLE.read_text(encoding="utf-8").split())
    for required in (
        "authority=one_exact_read_only_scope_local_candidate_review",
        "review_scope=one_scope_local_coherent_candidate_after_same_cpm_combines_l2_outputs",
        "review_scope_boundary=no_cross_direction_union_review",
        "review_acceptance=advisory_only",
        "never performs a cross-direction or union review",
        "owning CPM alone makes technical acceptance",
    ):
        assert required in role_text
    for retired in (
        "authority=one_exact_read_only_integrated_package_review",
        "review_scope=coherent_integrated_batch_not_each_implementer",
        "whole_integrated_diff_visibility=allowed",
    ):
        assert retired not in role_text


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
    assert "fork_turns=1" in instructions
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
        "fork_turns=1",
        "self-contained natural-language task model",
        "one conclusion-first native result",
    ):
        assert required in instructions

    assert EXPLORER_MECHANICAL_ROLE.is_file()
    role_text = EXPLORER_MECHANICAL_ROLE.read_text(encoding="utf-8")
    for required in (
        "role=explorer_mechanical_operator",
        "callable_agent_type=hmasd-explorer-mechanical",
        "parent=root|independent_research_explorer",
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
        assert "registered child invokable" in instructions
        assert "Root" in instructions and "Code Project Manager" in instructions
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

    for manager in ("HMASDIndependentResearchExplorer",):
        with L1_REGISTRY[manager]["profile"].open("rb") as stream:
            profile = tomllib.load(stream)
        instructions = " ".join(str(profile["developer_instructions"]).split()).lower()
        assert "root" in instructions and "fork_turns=1" in instructions, manager

def test_leaf_roles_and_profiles_explicitly_forbid_spawn_and_cross_owner_contact() -> None:
    role_paths = [
        REPOSITORY_ROOT / ".agents/roles/CODE_SCOUT.md",
        REPOSITORY_ROOT / ".agents/roles/RESEARCH_SCOUT.md",
        REPOSITORY_ROOT / ".agents/roles/EXPLORER_MECHANICAL_OPERATOR.md",
    ]
    for role_path in role_paths:
        role = " ".join(role_path.read_text(encoding="utf-8").split()).lower()
        assert "agent_tree_level=1_or_2" in role
        assert "spawn_authority=none" in role
        assert "return" in role and "invoker" in role


def test_steady_surge_model_routing_policy_is_explicit() -> None:
    router = " ".join(ROUTER.read_text(encoding="utf-8").split())
    root = " ".join(ROOT_ROLE.read_text(encoding="utf-8").split())
    manager = " ".join(CODE_MANAGER_ROLE.read_text(encoding="utf-8").split())

    for required in (
        "Steady Operational Root guidance is Luna-high",
        "Root integration or recovery is Terra-high",
        "novel governance is Sol-high",
        "EM remains Sol-max and CM remains Sol-high",
        "There is no automatic model fallback",
        "Project Scout capacity fallback below is the only named exception",
        "Never migrate an active agent mid-turn",
        "Model selection allocates capability only",
    ):
        assert required in router

    for required in (
        "use Luna-high for steady orchestration",
        "promote to Terra-high only when",
        "promote to Sol-high only when",
        "simple_mechanical",
        "ordinary_task",
        "high_difficulty",
        "Difficulty, urgency, or a large context alone is not a promotion trigger",
        "do not silently substitute another model",
    ):
        assert required in root

    for required in (
        "hmasd-implementer-terra`/Terra-high",
        "hmasd-implementer`/Sol-high",
        "probability, gradient, replay, recurrent-state, RNG, checkpoint, result",
        "cost, urgency, context size, or a prior worker failure is not",
        "Use Reviewer only for one named material",
        "Use Verifier only for one different, proof-sized executable question",
        "never as a routine Implementer+Reviewer+Verifier chain",
        "A completed review is not automatically repeated",
    ):
        assert required in manager


def test_model_cost_runbook_has_canaries_records_and_rollback_boundaries() -> None:
    assert MODEL_COST_RUNBOOK.is_file()
    runbook_raw = MODEL_COST_RUNBOOK.read_text(encoding="utf-8")
    runbook = " ".join(runbook_raw.split())
    for required in (
        "cp0_root_model=populate_from_cost_script_before_cp1",
        "cp0_root_effort=populate_from_cost_script_before_cp1",
        "runtime/codex-semantic-mvp/agent-model-cost-routing/",
        "quality.jsonl",
        "join-manifest.json",
        "first_pass_accepted",
        "material_defect_count",
        "unauthorized_scope_or_semantic_escape",
        "accepting_owner",
        "Never infer quality from prose",
        "019fec57-cea2-7f31-8595-8e9ca929b0dd",
        "019ff336-ddf4-7751-b1da-99757fddbf64",
        "01a009fa-30eb-7de2-8c8d-4e93e4419070",
        "stdlib `sqlite3` to make a runtime snapshot",
        "DELETE FROM threads WHERE id = ?",
        "--state-db $HistoricalStateDb",
        "--role unlabeled_root --role hmasd-implementer --role hmasd-implementer-terra",
        "--unit both",
        "--cost-scope self",
        "zero eligible quality/task-class baseline",
        "<role>/<task_class>",
        "Every row deleted from a runtime filtered SQLite snapshot",
        "<join-manifest.cp0_root_model>/<join-manifest.cp0_root_effort>",
        "A/simple_mechanical",
        "A/ordinary_task",
        "B/ordinary_task",
        "$Experiment = 'A' # Set to 'A' or 'B'.",
        "$RuntimeDir/canary-$Experiment-$TaskClass-compare.json",
        "Prospective quality records begin only after",
        "Each populated experiment/task-class stratum has its own sample boundary",
        "at least 10 eligible tasks with balanced arms and at least 5 eligible tasks in each arm",
        "20-assigned-task per-stratum cap",
        "fewer than 5 eligible in either arm is non-passing",
        "No undersized or failing stratum may support activation or be hidden by pooling",
        "For experiment A, control is the exact CP0 current-Root comparator",
        "experimental is steady Operational Root `gpt-5.6-luna/high`",
        "For experiment B, control is `hmasd-implementer`/`gpt-5.6-sol/high`",
        "experimental is `hmasd-implementer-terra`/`gpt-5.6-terra/high`",
        "validate arm identity for every otherwise eligible quality row",
        "cost script to report exactly one model/effort group per arm",
        "A mismatch cannot count toward the per-stratum sample minimum or activation",
        "Full activation requires every populated stratum for that route to pass separately",
        "Do not duplicate a task",
        "hard-roll back",
        "CP0 baseline",
        "CP1 Root-only",
        "CP2 CM/leaf routing",
        "CP3 review policy",
        "CP4 full activation",
        "not runtime states, approval gates, or a workflow lifecycle",
        "Root alone performs each Git integration or reversal",
    ):
        assert required in runbook

    assert "cp0_root_comparator=gpt-5.6-sol/high" not in runbook
    assert "exact CP0 current-Root comparator `gpt-5.6-sol/high`" not in runbook
    assert "10--20 future tasks total" not in runbook
    assert "The first comparison report is valid only at 10 eligible total" not in runbook
    assert "$EligibleThreadIds" not in runbook
    cp0_command = next(
        line for line in runbook_raw.splitlines()
        if "$CostScript summary" in line and "--label cp0_current_root" in line
    )
    assert "--project 'C:/Projects/HMASD'" in cp0_command
    assert "--role" not in cp0_command
    assert "$Cp0StartLocal" in cp0_command and "$Cp0EndLocal" in cp0_command
    assert runbook_raw.count("Remove-Item -LiteralPath") == 3
    assert "Remove-Item -LiteralPath $RawStateDb" not in runbook_raw
    assert runbook_raw.count("& $Python -c $SnapshotCode") == 3
    assert runbook.count("tests/hmasd_two_level_agent_topology_test.py") >= 5
    for prior in ("exact CP0 version", "exact CP1 versions", "exact CP2 versions", "exact CP3"):
        assert prior in runbook
    assert "manual cost" not in runbook.lower()


def test_direct_run_requires_pytest_instead_of_printing_partial_success() -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    legacy_success_marker = "HMASD_MODEL_" + "ROUTING_OK"
    assert legacy_success_marker not in source
    assert 'raise SystemExit("Run with pytest' in source


if __name__ == "__main__":
    raise SystemExit("Run with pytest so every model-routing policy test executes.")
