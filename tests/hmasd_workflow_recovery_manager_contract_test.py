"""Static contracts for the autonomous workflow-recovery manager route."""

from __future__ import annotations

import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


REPO = Path(__file__).resolve().parents[1]
PROFILE = REPO / ".codex" / "agents" / "hmasd-workflow-recovery-manager.toml"
ROLE = REPO / ".agents" / "roles" / "WORKFLOW_RECOVERY_MANAGER.md"
ROUTER = REPO / "AGENTS.md"
ROOT_ROLE = REPO / ".agents" / "roles" / "ROOT.md"
CM_ROLE = REPO / ".agents" / "roles" / "CODE_PROJECT_MANAGER.md"
CM_PROFILE = REPO / ".codex" / "agents" / "hmasd-code-project-manager.toml"
CONFIG = REPO / ".codex" / "config.toml"
FIXTURE = REPO / "tests" / "fixtures" / "workflow_recovery" / "stale_skill_loop.json"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_workflow_recovery_manager_is_registered_as_terra_high_l1() -> None:
    assert PROFILE.is_file()
    with PROFILE.open("rb") as stream:
        profile = tomllib.load(stream)

    assert profile["name"] == "hmasd-workflow-recovery-manager"
    assert profile["model"] == "gpt-5.6-terra"
    assert profile["model_reasoning_effort"] == "high"
    assert profile["sandbox_mode"] == "workspace-write"
    assert profile["approval_policy"] == "never"

    instructions = " ".join(str(profile["developer_instructions"]).split())
    for required in (
        ".agents/roles/WORKFLOW_RECOVERY_MANAGER.md",
        "Treat the reported failure, the prior Skill, and prior agent conclusions as evidence",
        "hmasd-code-scout",
        "hmasd-implementer-terra",
        "Children return to you",
        "WORKFLOW_RECOVERY_RESULT",
    ):
        assert required in instructions

    config = CONFIG.read_text(encoding="utf-8")
    assert config.count('config_file = "./agents/hmasd-workflow-recovery-manager.toml"') == 1
    assert "hmasd-workflow-recovery-manager" in CM_PROFILE.read_text(encoding="utf-8")


def test_recovery_role_has_autonomy_and_real_boundaries() -> None:
    role = _normalized(ROLE)
    for required in (
        "role=workflow_recovery_manager",
        "parent=root|code_project_manager",
        "worktree_authority=assignment_scoped_detached_lifecycle",
        "runtime_authority=assignment_scoped_diagnostic_control",
        "external_action_authority=explicit_assignment_allow_list_only",
        "WORKFLOW_RECOVERY_ASSIGNMENT",
        "current facts and unknowns",
        "A relevant Skill is evidence",
        "Every recovery cycle must produce new evidence",
        "Do not repeat the same Skill path, command, or retry",
        "Do not return merely because diagnosis, planning, a local command, or one test has completed",
        "Production sends, publication, paid services, credentials, shared services, destructive actions",
        "WORKFLOW_RECOVERY_RESULT",
        "status=RECOVERED|BLOCKED",
    ):
        assert required in role

    for forbidden in (
        "git_authority=exclusive",
        "user_contact_authority=exclusive",
        "external_action_authority=unbounded",
    ):
        assert forbidden not in role


def test_router_and_parent_roles_transfer_only_real_workflow_failures() -> None:
    router = _normalized(ROUTER)
    root = _normalized(ROOT_ROLE)
    cm = _normalized(CM_ROLE)

    assert "Workflow Recovery Manager" in router
    for text in (root, cm):
        for required in (
            "hmasd-workflow-recovery-manager",
            "repeated failure",
            "no new evidence",
            "observation",
        ):
            assert required in text


def test_stale_skill_loop_fixture_requires_expanded_observation_and_completion() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["name"] == "stale_skill_loop"
    assert "treat skill staleness as a testable hypothesis" in payload["required_recovery_actions"]
    assert "expand the observation surface before repeating an action" in payload["required_recovery_actions"]
    assert "repeat the same skill path without new evidence" in payload["forbidden_actions"]
    assert "perform an external side effect without explicit assignment authority" in payload["forbidden_actions"]


if __name__ == "__main__":
    test_workflow_recovery_manager_is_registered_as_terra_high_l1()
    test_recovery_role_has_autonomy_and_real_boundaries()
    test_router_and_parent_roles_transfer_only_real_workflow_failures()
    test_stale_skill_loop_fixture_requires_expanded_observation_and_completion()
    print("HMASD_WORKFLOW_RECOVERY_MANAGER_CONTRACT_OK")
