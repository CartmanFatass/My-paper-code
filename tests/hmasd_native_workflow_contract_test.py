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
        "hmasd-workflow-clerk-task",
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
    assert protocol.startswith("# HMASD native Codex workflow\n\nWorkflow revision: ")
    for marker in ("[WORK]", "[RESULT]", "[CONTROL]"):
        assert marker in protocol
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
        "HMASDExternalProTransport",
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
    assert "| Direction | Lifecycle | Priority | Next role | Updated at | Reason/condition |" in portfolio
    for lifecycle in ("REGISTERED", "ACTIVE", "PARKED", "CLOSED"):
        assert lifecycle in portfolio
    assert "sha256" not in portfolio.lower()
    assert "registry revision" not in portfolio.lower()
    rows = [line for line in portfolio.splitlines() if line.startswith("| ")][2:]
    assert len(rows) == 33
    lifecycle = {row.split("|")[1].strip(): row.split("|")[2].strip() for row in rows}
    assert lifecycle["active_post_churn_population_flow_identification"] == "ACTIVE"
    assert lifecycle["finite_semantic_boundary_support"] == "ACTIVE"
    assert lifecycle["ucope"] == "ACTIVE"
    assert lifecycle["semigroup_consistent_duration_model_policy"] == "PARKED"
    assert lifecycle["metric_ground_transport_allocation"] == "CLOSED"


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
