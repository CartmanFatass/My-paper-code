from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 project runtime
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_only_current_session_skills_are_discoverable() -> None:
    expected = {
        "hmasd-root-task",
        "hmasd-portfolio-task",
        "hmasd-em-task",
        "hmasd-cm-task",
    }
    actual = {
        path.parent.name
        for path in (ROOT / ".agents" / "skills").glob("hmasd-*/SKILL.md")
    }
    assert actual == expected
    assert not list((ROOT / ".codex" / "prompts").glob("hmasd-*.md"))


def test_protocol_is_the_single_readable_workflow_authority() -> None:
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    agents = _read("AGENTS.md")
    context = _read("CONTEXT.md")
    assert protocol.startswith("# HMASD native Codex workflow\n\nWorkflow revision: ")
    for marker in ("[WORK]", "[RESULT]", "[CONTROL]"):
        assert marker in protocol
    assert "Return task: <native task id of the requester>" in protocol
    assert "用户直接进入某 participant 时不制造 Return task" in protocol
    assert "Portfolio → EM → CM → EM → Portfolio" in protocol
    assert "Action: PAUSE | RESUME | CANCEL" in protocol
    assert "Action: PAUSE | RESUME | CANCEL | REPLACE | RELOAD" not in protocol
    assert "同时最多持有一个 unfinished inbound WORK" in protocol
    assert "所有已发送 EM 必须 terminal" in protocol
    assert "initial prompt 本身就是完整 `[WORK]`" in protocol
    assert "同一 direction 同时只有一个 Git-visible writer phase" in protocol
    assert "Codex 原生 `environment: worktree`" in protocol
    assert "方向目录不需要另存为 Desktop" in protocol
    assert "branch fast-forward 到该 commit" in protocol
    assert "不得 cherry-pick、rebase 或重写历史" in protocol
    assert "native-worktree 交接只使用本地 exact" in protocol
    assert "不需要 push" in protocol
    assert "向当前 `Return task` 返回" in protocol
    assert "不得越过 requester 直接联系 Root" in protocol
    assert "hmasd-explorer-agentify-transport" in protocol
    assert "不设固定配额" in protocol
    assert "0–2 个 leaves" not in protocol
    assert "不得生成数值 VOI" in protocol
    assert "仍由\ncallee 持有" in protocol
    assert "successor 都先返回 terminal RESULT" in protocol
    assert "CANCELLED RESULT 并释放 target" in protocol
    assert "Clerk" not in protocol
    assert "Next: EM | CM | PORTFOLIO | ROOT | SAME | NONE" not in protocol
    for legacy in (
        "protocol_epoch",
        "control_release",
        "message_id",
        "reply_to",
        "hmasd_session_envelope",
        "hmasd_control_release",
        "Dashboard",
        "SHA256",
    ):
        assert legacy not in protocol
    assert "唯一控制 authority" in agents
    active_role_surfaces = "\n".join(
        [agents, protocol, context]
        + [
            _read(f".agents/skills/{name}/SKILL.md")
            for name in (
                "hmasd-root-task",
                "hmasd-portfolio-task",
                "hmasd-em-task",
                "hmasd-cm-task",
            )
        ]
    )
    assert "Clerk" not in active_role_surfaces
    assert "Session Envelope" not in active_role_surfaces
    assert "assignment-from-brief" not in active_role_surfaces
    assert "context SHA" not in active_role_surfaces
    assert "Return task" in active_role_surfaces
    assert not (ROOT / "docs/project/WORKFLOW_GOALS_AND_ACCEPTANCE.md").exists()
    assert not (
        ROOT / "docs/project/EM_CM_MILESTONE_AND_LEAF_SIMPLIFICATION_WORKING_DRAFT.md"
    ).exists()


def test_agent_roster_is_small_and_has_generic_luna_xhigh_leaf() -> None:
    config = tomllib.loads(_read(".codex/config.toml"))
    assert config["agents"]["max_depth"] == 1
    assert config["agents"]["max_threads"] == 8
    entries = {
        key: value
        for key, value in config["agents"].items()
        if isinstance(value, dict)
    }
    assert set(entries) == {
        "HMASDCMScout",
        "HMASDReviewer",
        "HMASDVerifier",
        "HMASDExperimentOperator",
        "HMASDCPMAgentifyTransport",
        "HMASDExplorerAgentifyTransport",
        "HMASDResearchScout",
        "HMASDResearchCritic",
        "HMASDGeneralLeaf",
    }
    general_path = ROOT / ".codex" / entries["HMASDGeneralLeaf"]["config_file"]
    general = tomllib.loads(general_path.read_text(encoding="utf-8"))
    assert general["model"] == "gpt-5.6-luna"
    assert general["model_reasoning_effort"] == "xhigh"
    assert "Never spawn" in general["developer_instructions"]


def test_legacy_control_programs_and_portfolio_registry_are_absent() -> None:
    for relative in (
        "scripts/hmasd_session_envelope.py",
        "scripts/hmasd_control_release.py",
        "scripts/hmasd_dashboard.py",
        "scripts/hmasd_protocol_contracts.py",
        "scripts/hmasd_external_review.py",
        "scripts/hmasd_path_policy.py",
        "docs/project/git-path-policy-v1.json",
        "docs/research/portfolio/workflow/registry.json",
    ):
        assert not (ROOT / relative).exists()
    assert not list((ROOT / "scripts/dashboard").glob("**/*"))
    candidates = ROOT / "docs/research/candidates"
    assert not list(candidates.glob("*/workflow/research/state.json"))
    assert not list(candidates.glob("*/workflow/engineering/state.json"))
    assert not list(candidates.glob("*/workflow/external-review/index.json"))


def test_portfolio_is_one_current_table() -> None:
    portfolio = _read("docs/research/portfolio/PORTFOLIO.md")
    assert "| Direction | Lifecycle | Priority | Direction owner | Updated at | Reason/condition |" in portfolio
    for lifecycle in ("REGISTERED", "ACTIVE", "PARKED", "CLOSED"):
        assert lifecycle in portfolio
    assert "sha256" not in portfolio.lower()
    assert "registry revision" not in portfolio.lower()
    rows = [line for line in portfolio.splitlines() if line.startswith("| ")][2:]
    assert len(rows) == 33
    lifecycle = {row.split("|")[1].strip(): row.split("|")[2].strip() for row in rows}
    owner = {row.split("|")[1].strip(): row.split("|")[4].strip() for row in rows}
    assert set(owner.values()) <= {"NONE", "PORTFOLIO", "EM"}
    for direction, current_lifecycle in lifecycle.items():
        if current_lifecycle == "ACTIVE":
            assert owner[direction] in {"PORTFOLIO", "EM"}
        else:
            assert owner[direction] == "NONE"
    assert lifecycle["active_post_churn_population_flow_identification"] == "PARKED"
    assert owner["active_post_churn_population_flow_identification"] == "NONE"
    assert lifecycle["expressibility_gated_renewal_credit_relay"] == "ACTIVE"
    assert owner["expressibility_gated_renewal_credit_relay"] == "PORTFOLIO"
    assert lifecycle["opportunity_normalized_lease_gated_rebinding"] == "ACTIVE"
    assert owner["opportunity_normalized_lease_gated_rebinding"] == "PORTFOLIO"
    assert lifecycle["finite_semantic_boundary_support"] == "PARKED"
    assert lifecycle["ucope"] == "PARKED"
    assert owner["ucope"] == "NONE"
    assert lifecycle["semigroup_consistent_duration_model_policy"] == "PARKED"
    assert lifecycle["metric_ground_transport_allocation"] == "CLOSED"


def test_research_navigation_does_not_duplicate_portfolio_state() -> None:
    research_map = _read("docs/research/RESEARCH_MAP.md")
    assert "Current lifecycle, priority, capacity, and direction owner exist only" in research_map
    assert "Status snapshot:" not in research_map
    assert "| Direction | State |" not in research_map
    assert "ACTIVE_ENGINEERING" not in research_map
    assert "SCIENTIFIC_NO_CURRENT" not in research_map

    directions = sorted((ROOT / "docs/research/candidates").glob("*/DIRECTION.md"))
    assert len(directions) == 33
    for path in directions:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert "docs/research/portfolio/portfolio.md" in lowered
        for stale in (
            "workflow json points here",
            "initial registry lifecycle",
            "and its registry",
            "current registry observation",
            "no engineering request is active",
            "no external-review round is active",
            "external-review workflow",
        ):
            assert stale not in lowered, path


def test_research_cycle_and_fanout_relations_are_ordered() -> None:
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    cycle = protocol.split("## 6. Material research cycle and External Pro", 1)[1].split(
        "## 7. Portfolio", 1
    )[0]
    assert cycle.index("Mode: INNOVATOR") < cycle.index("EM → CM → EM")
    assert cycle.index("EM → CM → EM") < cycle.index("`SYNTHESIS_READY`")
    assert cycle.index("`SYNTHESIS_READY`") < cycle.index("Mode: CONVERGENCE")
    assert cycle.index("Mode: CONVERGENCE") < cycle.index("`REVIEW_RESOLVED`")
    assert "纯理论/静态证据对象可以不调用 CM" in cycle
    assert "两个独立的 fresh transport" in cycle
    assert "Unknown commitment 只观察不重发" in cycle

    fanout = protocol.split("Portfolio 可以在一个当前比较性 WORK", 1)[1].split(
        "Participant 可以为完成当前 acceptance", 1
    )[0]
    assert "所有已发送 EM 必须 terminal" in fanout
    assert "逐一 CANCEL 并收到" in fanout
    assert "不写本地 batch、queue 或 task registry" in fanout

    em_skill = _read(".agents/skills/hmasd-em-task/SKILL.md")
    assert em_skill.index("Mode: INNOVATOR") < em_skill.index("direction CM")
    assert em_skill.index("direction CM") < em_skill.index("`SYNTHESIS_READY`")
    assert em_skill.index("`SYNTHESIS_READY`") < em_skill.index("Mode: CONVERGENCE")
    assert em_skill.index("Mode: CONVERGENCE") < em_skill.index("`REVIEW_RESOLVED`")


def test_sensitive_direction_science_boundaries_survive_metadata_cleanup() -> None:
    fsbs = _read("docs/research/candidates/finite_semantic_boundary_support/DIRECTION.md")
    assert "Equivalent implementation paths may not change its" in fsbs
    for boundary in ("host, arms, matched resources, learner", "workload, thresholds", "claim map"):
        assert boundary in fsbs

    mgtap = _read("docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md")
    assert "The accepted revision-04 result is `BOUNDED_NONIDENTIFICATION_STRUCTURAL`" in mgtap
    assert "FIRST_TRUE_BRANCH=BOUNDED_NONIDENTIFICATION_STRUCTURAL" in mgtap

    ucope = _read("docs/research/candidates/ucope/DIRECTION.md")
    assert "The complete result is immutable: no technical repair can convert its frozen" in ucope
    assert "support failure into an identifying result" in ucope


def test_retired_control_notebooks_are_not_active_docs() -> None:
    for relative in (
        "docs/research/workflow/WORKFLOW_IMPROVEMENTS.md",
        "docs/DISTRIBUTED_RESEARCH_COGNITION_WORKING_NOTES.md",
        "docs/plans/2026-07-22-controller-direct-external-review-design.md",
        "docs/plans/2026-07-22-controller-direct-external-review-implementation.md",
    ):
        assert not (ROOT / relative).exists()
    requirements = _read("docs/SCIENTIFIC_CAPABILITY_LAYER_REQUIREMENTS.md")
    assert "Workflow-Clerk" not in requirements
    temp_readme = _read("temp/README.md")
    assert "Codex native" in temp_readme
    assert "does not need to be saved as a separate" in temp_readme


def test_state_cli_only_exposes_validate_and_update() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/hmasd_state.py"), "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "{validate,update}" in completed.stdout
    for legacy in ("initialize", "replace", "portfolio-apply", "migration"):
        assert legacy not in completed.stdout


def test_minimal_state_schemas_define_milestones_without_hashes() -> None:
    research = json.loads(_read("scripts/schemas/hmasd_research_state.schema.json"))
    engineering = json.loads(_read("scripts/schemas/hmasd_engineering_state.schema.json"))
    assert research["properties"]["milestone"]["enum"] == [
        "SCOPE_FROZEN",
        "SYNTHESIS_READY",
        "REVIEW_RESOLVED",
        "HANDOFF_READY",
    ]
    assert engineering["properties"]["milestone"]["enum"] == [
        "SCOPE_FROZEN",
        "CANDIDATE_READY",
        "REVIEW_RESOLVED",
        "RUN_OR_HANDOFF_READY",
    ]
    for schema in (research, engineering):
        rendered = json.dumps(schema)
        assert "sha256" not in rendered.lower()
        assert schema["additionalProperties"] is False
        assert schema["properties"]["status"]["enum"] == [
            "ACTIVE", "WAITING", "FAILED", "CANCELLED", "COMPLETE"
        ]


def test_science_cli_is_observation_only() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/hmasd_science_capabilities.py"), "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "{list,show,doctor}" in completed.stdout
    for forbidden in ("run", "install", "route", "validate-evidence"):
        assert forbidden not in completed.stdout
    catalog = tomllib.loads(_read("configs/scientific-capabilities-v1.toml"))
    assert catalog["catalog"]["version"] == 1
    for item in catalog["capability"]:
        assert set(item) == {
            "capability",
            "status",
            "purpose",
            "entrypoint",
            "environment",
            "allowed_effects",
        }
        assert item["status"] in {"active", "unavailable"}
