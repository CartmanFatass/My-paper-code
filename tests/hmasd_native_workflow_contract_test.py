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


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_only_current_session_skills_are_discoverable() -> None:
    expected = {
        "hmasd-root-task",
        "hmasd-portfolio-task",
        "hmasd-em-task",
        "hmasd-cm-task",
        "hmasd-browser-conversation",
    }
    actual = {
        path.parent.name
        for path in (ROOT / ".agents" / "skills").glob("hmasd-*/SKILL.md")
    }
    assert actual == expected
    transport_policy = _read(
        ".agents/skills/hmasd-browser-conversation/agents/openai.yaml"
    )
    assert "allow_implicit_invocation: false" in transport_policy
    assert not list((ROOT / ".codex" / "prompts").glob("hmasd-*.md"))


def test_authority_is_split_between_global_semantics_and_cross_task_protocol() -> None:
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    protocol_flat = _flat(protocol)
    agents = _read("AGENTS.md")
    principles = _read("docs/project/ALGORITHM_PRINCIPLES.md")
    assert protocol.startswith("# HMASD native Codex workflow\n\nWorkflow revision: ")
    for marker in (
        "[WORK]", "[RESULT]", "[CONTROL]",
        "[BROWSER WORK]", "[BROWSER RESULT]", "[BROWSER CONTROL]",
    ):
        assert marker in protocol
    assert "Return task: <native task id of requester>" in protocol_flat
    assert "用户直接进入 Root、Portfolio、EM 或 CM 时，不制造 `Return task`" in protocol
    assert "Portfolio → EM → CM → EM → Portfolio" in protocol
    assert "Action: PAUSE | RESUME | CANCEL" in protocol
    assert "Action: PAUSE | RESUME | CANCEL | REPLACE | RELOAD" not in protocol
    for marker in (
        "同时最多持有一个 unfinished inbound WORK",
        "所有已投递 EM 自然 terminal",
        "initial prompt 本身就是完整 `[WORK]`",
        "同一 direction 同时只有一个 Git-visible writer phase",
        "Codex 原生 `environment: worktree`",
        "方向目录不需要另存为 Desktop",
        "branch 必须 fast-forward 到该 commit",
        "不得 cherry-pick、rebase 或重写历史",
        "native-worktree 交接只使用本地 exact commit",
        "`CM/shared → Root` 使用同样的单 writer、fast-forward 交接",
        "terminal Reviewer observation",
        "intended target 仍可 fast-forward",
        "创建替代 CM",
        "不需要 push",
        "向当前 `Return task` 返回",
        "不得越过 requester 直接联系 Root",
        "一个 successor 必须等当前 WORK terminal",
        "先读取同一 recipient history",
        "不得因 API 超时、UI 未刷新",
        "本地未知状态盲目重复 WORK/CONTROL",
        "idle、stopped、completed 或 not-loaded",
        "只补同一 assignment 的 RESULT",
        "requester 直接消费，不要求第二份",
        "explicit non-goals",
        "intended remote ref",
    ):
        assert marker in protocol_flat
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
    assert "universal semantic kernel" in agents
    assert "sole cross-task transport authority" in agents
    assert "公共字段含义、caller" in protocol_flat
    assert "这里不复制这些内容" in protocol_flat
    assert "top-level session skill" in protocol_flat
    for local_recipe in (
        "agentify_review_query", "Experiment Operator", "current snapshot",
        "## 8. External and result Effects", "## 9. Milestone memory and recovery",
        "## 10. Cutover",
    ):
        assert local_recipe not in protocol
    active_role_surfaces = "\n".join(
        [agents, protocol]
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
    assert not (ROOT / "CONTEXT.md").exists()
    for stale in (
        "docs/project/CURRENT_WORK.md",
        ".agents/roles/*.md",
        "External Pro owns",
        "Project Manager owns",
    ):
        assert stale not in principles
    assert "hmasd-*-task" in principles
    assert not (ROOT / "docs/project/WORKFLOW_GOALS_AND_ACCEPTANCE.md").exists()
    assert not (
        ROOT / "docs/project/EM_CM_MILESTONE_AND_LEAF_SIMPLIFICATION_WORKING_DRAFT.md"
    ).exists()


def test_agent_roster_is_small_and_has_generic_luna_xhigh_leaf() -> None:
    config = tomllib.loads(_read(".codex/config.toml"))
    assert config["agents"]["max_concurrent_threads_per_session"] == 8
    assert "max_depth" not in config["agents"]
    assert "max_threads" not in config["agents"]
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
        "HMASDResearchScout",
        "HMASDResearchCritic",
        "HMASDGeneralLeaf",
        "HMASDResearchInnovator",
        "HMASDResearchPrinciplesAnalyst",
        "HMASDImplementer",
        "HMASDRoutineImplementer",
        "HMASDWorkflowDesigner",
        "HMASDDesignReviewer",
    }
    general_path = ROOT / ".codex" / entries["HMASDGeneralLeaf"]["config_file"]
    general = tomllib.loads(general_path.read_text(encoding="utf-8"))
    assert general["model"] == "gpt-5.6-luna"
    assert general["model_reasoning_effort"] == "xhigh"
    assert "Never spawn" not in general["developer_instructions"]
    agents = _read("AGENTS.md")
    assert "sole depth-2 exception" in agents
    assert "fact-check child cannot delegate" in agents
    assert "`ri` | `hmasd-research-innovator`" in agents
    assert "`rp` | `hmasd-research-principles-analyst`" in agents
    assert "`im` | `hmasd-implementer`" in agents
    assert "`rt` | `hmasd-routine-implementer`" in agents
    assert "scientific scope, evidence synthesis" in agents
    assert "engineering contract, implementer selection" in agents
    assert "`wd` | `hmasd-workflow-designer`" in agents
    assert "`dr` | `hmasd-design-reviewer`" in agents


def test_workflow_design_leaves_do_not_expand_the_native_protocol() -> None:
    agents = _flat(_read("AGENTS.md"))
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    root = _flat(_read(".agents/skills/hmasd-root-task/SKILL.md"))
    design_reviewer = _flat(_read(".agents/roles/DESIGN_REVIEWER.md"))

    for leaf in ("HMASDWorkflowDesigner", "HMASDDesignReviewer"):
        assert leaf not in protocol
    assert "| Root | `gl`, `wd`, `dr` |" in _read("AGENTS.md")
    assert "same Root WORK and the same design-review assignment" in root
    assert "another design reviewer" in root
    assert "rereview loop" in root
    assert "before_send_click" in design_reviewer
    assert "review_model_mismatch" in design_reviewer
    assert "zero-send" in design_reviewer
    assert "does not claim that the Browser runtime is fixed" in design_reviewer
    for forbidden in ("registry", "receipt", "retry ledger", "scheduler", "authentication gate"):
        assert f"new {forbidden}" not in agents


def test_global_field_semantics_and_local_role_slices_are_distinct() -> None:
    agents = _read("AGENTS.md")
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    skills = {
        "Root": _read(".agents/skills/hmasd-root-task/SKILL.md"),
        "Portfolio": _read(".agents/skills/hmasd-portfolio-task/SKILL.md"),
        "EM": _read(".agents/skills/hmasd-em-task/SKILL.md"),
        "CM": _read(".agents/skills/hmasd-cm-task/SKILL.md"),
    }
    owned = {
        "Root": ("Root status:", "Integration status:"),
        "Portfolio": ("Direction actions:", "Capacity action:"),
        "EM": ("Scientific status:", "Decision impact:", "Recommendation:", "Pro Innovator:", "Pro Convergence:"),
        "CM": ("Engineering status:", "Observation status:", "Verification status:", "Commit:"),
    }
    for field in ("Outcome:",) + tuple(field for fields in owned.values() for field in fields):
        assert field in agents
    assert "`Outcome:` describes" in agents
    assert "Transport failure cannot imply `PARK`" in agents
    agents_flat = _flat(agents)
    for meaning in (
        "`NO_MATERIAL_INSIGHT` means the scientific acceptance was completed",
        "`NOT_REACHED` means no valid scientific synthesis was reached",
        "`BLOCKED` means the engineering acceptance was not satisfied",
        "`NOT_OBSERVED` means the current bounded acquisition ended without one",
        "`UNSATISFIED` means the current bounded verification concluded against the candidate",
        "`PARK` retains the direction without active investment",
        "`ACTIVE` requires a current executable scientific question",
        "`PARKED` has no live direction WORK",
        "`CLOSED` has a terminal investment reason",
        "`INCOMPLETE` lacks a premise required for judgment",
        "current assignment stage, not merely the last failed attempt",
    ):
        assert meaning in agents_flat
    assert "Root status:" not in protocol
    assert "Direction actions:" not in protocol
    assert "Portfolio action:" not in agents
    assert "Scientific status:" not in protocol
    assert "Engineering status:" not in protocol
    for role, skill in skills.items():
        assert all(field not in skill for fields in owned.values() for field in fields)
        assert "Outcome:" not in skill

    mechanical = (
        "CAPTCHA",
        "responsePath",
        "agentify_review_query",
    )
    em = _read(".agents/skills/hmasd-em-task/SKILL.md")
    cm = _read(".agents/skills/hmasd-cm-task/SKILL.md")
    for detail in mechanical:
        assert detail not in protocol
        assert detail not in em
        assert detail not in cm
    assert "`hmasd-browser-conversation` skill" in protocol
    assert "理解页面与对话阶段" in protocol
    assert "one complete `[BROWSER WORK]` directly" in _flat(em)
    assert "one complete `[BROWSER WORK]` directly" in _flat(cm)


def test_top_level_models_and_leaf_task_names_are_explicit() -> None:
    agents = _read("AGENTS.md")
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    for text in (
        "Portfolio | `gpt-5.6-sol` | `max`",
        "EM | `gpt-5.6-sol` | `max`",
        "CM | `gpt-5.6-sol` | `high`",
        "Browser Transport | `gpt-5.6-luna` | `xhigh`",
    ):
        assert text in agents
        assert text not in protocol
    assert "显式传入 `AGENTS.md` 的 model/thinking" in protocol
    assert "`<code>_<model>_<effort>_<task>`" in agents
    for example in ("`rv_s_xh_plan`", "`gl_l_xh_pdf`"):
        assert example in agents
    assert "Direct-leaf `spawn_agent.task_name` uses" in agents
    assert "`[a-z0-9_]+`" in agents
    assert "actual selected profile" in _flat(agents)
    for skill_name in (
        "hmasd-root-task", "hmasd-portfolio-task", "hmasd-em-task", "hmasd-cm-task",
        "hmasd-browser-conversation",
    ):
        skill = _read(f".agents/skills/{skill_name}/SKILL.md")
        assert "gpt-5.6-" not in skill
        assert "<code>_<model>_<effort>_<task>" not in skill


def test_external_pro_prompt_is_natural_language_not_control_serialization() -> None:
    em = _read(".agents/skills/hmasd-em-task/SKILL.md")
    transport = _read(".agents/skills/hmasd-browser-conversation/SKILL.md")
    normalized = _flat(f"{em}\n{transport}")
    assert "cohesive natural-language `INNOVATOR` prompt" in normalized
    assert "Do not emit top-level `Outcome`" in normalized
    assert "EM owns the complete Pro prompt" in normalized
    assert "Never compose, shorten, summarize, append, translate, wrap" in normalized

    for profile in (ROOT / ".codex/agents").glob("*.toml"):
        assert "<code>_<model>_<effort>_<task>" not in profile.read_text(encoding="utf-8")


def test_transport_facts_cannot_cancel_or_park_a_direction() -> None:
    agents = _read("AGENTS.md")
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    for text in (
        "only a received `[CONTROL] Action: CANCEL`",
        "Transport failure cannot imply `PARK`",
        "不得为了释放 join 自行取消子 WORK",
    ):
        assert text in agents or text in protocol
    assert "Portfolio 逐一 CANCEL" not in protocol
    assert "由 Portfolio 逐一 CANCEL" not in protocol


def test_nonterminal_work_cannot_leave_the_owner_loop() -> None:
    agents = _flat(_read("AGENTS.md"))
    portfolio = _flat(_read(".agents/skills/hmasd-portfolio-task/SKILL.md"))
    em = _flat(_read(".agents/skills/hmasd-em-task/SKILL.md"))
    cm = _flat(_read(".agents/skills/hmasd-cm-task/SKILL.md"))
    operator = _flat(_read(".agents/roles/EXPERIMENT_OPERATOR.md"))

    for marker in (
        "`WORKING`: the same inbound WORK is actively advancing",
        "`WAITING_REENTRY`: the same WORK remains live",
        "`TERMINAL_GAP`: the current WORK ended before the role's final milestone",
        "`COMPLETE`: the current WORK reached the role's final milestone",
        "A wait timeout, stale status, clipped/unreadable response, or lost process observation is not completion",
        "cannot produce `DONE`, `FAILED`, or `CANCELLED` or release the target",
    ):
        assert marker in agents
    assert "still-running EM keeps the existing join live" in portfolio
    assert "running research leaf or CM" in em
    assert "Do not return a terminal Outcome" in em
    assert "running engineering leaf" in cm
    assert "Do not return a terminal Outcome" in cm
    assert "A wait timeout is not a terminal witness" in operator


def test_work_and_leaf_returns_are_meaning_first() -> None:
    agents = _read("AGENTS.md")
    protocol = _read("docs/project/WORKFLOW_PROTOCOL.md")
    normalized = _flat(f"{agents}\n{protocol}")
    for text in (
        "self-contained natural-language task model",
        "factual anchors after meaning",
        "cannot substitute for the parent's judgment",
        "conclusion-first",
        "fork_turns=1",
    ):
        assert text in normalized
    assert protocol.index("Summary: <conclusion and direct consequence>") < protocol.index(
        "<only this role's fixed fields from AGENTS.md>"
    )


def test_portfolio_authority_uses_native_worktrees_not_saved_direction_projects() -> None:
    portfolio = _read("docs/research/portfolio/PORTFOLIO.md")
    assert "saved permanent direction project" not in portfolio
    assert "sibling permanent worktree saved as a Codex local project" not in portfolio
    assert "native `environment: worktree`" in _flat(portfolio)


def test_legacy_control_is_absent_and_current_milestone_snapshots_validate() -> None:
    for relative in (
        "scripts/hmasd_session_envelope.py",
        "scripts/hmasd_control_release.py",
        "scripts/hmasd_dashboard.py",
        "scripts/hmasd_protocol_contracts.py",
        "scripts/hmasd_external_review.py",
        "scripts/hmasd_path_policy.py",
        "scripts/hmasd_host_compat.py",
        "tests/hmasd_host_compat_test.py",
        "docs/project/git-path-policy-v1.json",
        "docs/research/portfolio/workflow/registry.json",
    ):
        assert not (ROOT / relative).exists()
    assert not list((ROOT / "scripts/dashboard").glob("**/*"))
    candidates = ROOT / "docs/research/candidates"
    for kind in ("research", "engineering"):
        for state_path in candidates.glob(f"*/workflow/{kind}/state.json"):
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/hmasd_state.py",
                    "validate",
                    "--kind",
                    kind,
                    "--path",
                    str(state_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stderr
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
    assert lifecycle["expressibility_gated_renewal_credit_relay"] == "PARKED"
    assert owner["expressibility_gated_renewal_credit_relay"] == "NONE"
    assert lifecycle["commitment_residual_triggered_options"] == "PARKED"
    assert owner["commitment_residual_triggered_options"] == "NONE"
    assert lifecycle["dual_epoch_receipt_survival"] == "ACTIVE"
    assert owner["dual_epoch_receipt_survival"] == "EM"
    assert lifecycle["opportunity_normalized_lease_gated_rebinding"] == "ACTIVE"
    assert owner["opportunity_normalized_lease_gated_rebinding"] == "PORTFOLIO"
    assert lifecycle["ucope"] == "PARKED"
    assert owner["ucope"] == "NONE"
    assert lifecycle["semigroup_consistent_duration_model_policy"] == "ACTIVE"
    assert owner["semigroup_consistent_duration_model_policy"] == "EM"
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
    cycle = _flat(_read(".agents/skills/hmasd-em-task/SKILL.md"))
    transport = _flat(_read(".agents/skills/hmasd-browser-conversation/SKILL.md"))
    assert cycle.index("`INNOVATOR`") < cycle.index("send a meaning-complete WORK to CM")
    assert cycle.index("send a meaning-complete WORK to CM") < cycle.index("`SYNTHESIS_READY`")
    assert cycle.index("`SYNTHESIS_READY`") < cycle.index("`CONVERGENCE`")
    assert cycle.index("`CONVERGENCE`") < cycle.index("`REVIEW_RESOLVED`")
    assert "may omit CM" in cycle
    assert "writes one cohesive natural-language `INNOVATOR` prompt" in cycle
    assert cycle.count("user explicitly waived that exact unsent operation") == 2
    assert "Browser Transport, which sends it once" in cycle
    assert "does not create shared repair work" in transport
    assert "Invoke it once for one operation" in transport
    fanout = _flat(protocol.split("## 5. Portfolio fan-out and join", 1)[1].split(
        "## 6. Adjacent scientific content", 1
    )[0])
    assert "所有已投递 EM 自然 terminal" in fanout
    assert "逐一转达" in fanout
    assert "不得为了释放 join 自行取消" in fanout
    assert "不写本地 batch、queue 或 task registry" in fanout
    assert "terminal EM RESULT 已结束该 join leg" in fanout
    assert "下游建议不得自动继承" in fanout

    portfolio_role = _flat(_read(".agents/skills/hmasd-portfolio-task/SKILL.md"))
    for required in (
        "technical or measurement gap",
        "A downstream repair proposal is a candidate, not an inherited reentry",
        "current executable decision question",
        "exact user-controlled reentry",
        "never leave live science operationally starved",
        "Portfolio draft edits are outputs, not authority",
    ):
        assert required in portfolio_role

    portfolio_skill = _flat(_read(".agents/skills/hmasd-portfolio-task/SKILL.md")).lower()
    for required in (
        "decision frame",
        "user decision and fixed set",
        "live investments",
        "evidence boundary",
        "counterfactual allocation",
        "next observation",
        "terminal technical or measurement gap",
        "repair proposal is a candidate, not an inherited reentry",
        "draft edits are outputs, not authority",
    ):
        assert required in portfolio_skill

    em_skill = _read(".agents/skills/hmasd-em-task/SKILL.md")
    assert ".agents/roles/EM.md" not in em_skill
    for role_local_cycle_detail in (
        "`INNOVATOR`", "`CONVERGENCE`", "`SYNTHESIS_READY`", "`REVIEW_RESOLVED`",
    ):
        assert role_local_cycle_detail in em_skill


def test_historical_evidence_cannot_supply_current_workflow_instructions() -> None:
    agents = _flat(_read("AGENTS.md"))
    direction = _read(
        "docs/research/candidates/opportunity_normalized_lease_gated_rebinding/DIRECTION.md"
    )
    packet = _read(
        "docs/research/candidates/opportunity_normalized_lease_gated_rebinding/evidence/"
        "2026-08-29-2026-08-28.10-clean-01a04a02-onlgr-successor-02-em-to-cm-work.md"
    )
    assert "inside cited historical evidence are provenance only" in agents
    assert ".agents/roles/CM.md" not in direction
    assert ".agents/roles/CM.md" in packet


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
        assert "status" not in schema["properties"]
        assert schema["properties"]["snapshot_state"]["enum"] == [
            "WORKING", "WAITING_REENTRY", "TERMINAL_GAP", "COMPLETE"
        ]
    pro_states = research["$defs"]["pro_review"]["properties"]["status"]["enum"]
    assert research["$defs"]["pro_review"]["required"] == [
        "status", "response", "replacement_used"
    ]
    assert research["$defs"]["pro_review"]["properties"]["replacement_used"] == {
        "type": "boolean"
    }
    assert pro_states == [
        "PENDING",
        "ZERO_SEND_FAILED",
        "COMMITMENT_UNKNOWN",
        "SENT_WAITING",
        "COMPLETE",
        "SENT_INPUT_MISMATCH",
        "SENT_UNREADABLE",
        "SENT_MODEL_MISMATCH",
        "CONVERSATION_LOST",
        "WAIVED",
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
