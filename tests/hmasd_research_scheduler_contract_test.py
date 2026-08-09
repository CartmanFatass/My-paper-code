from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_scheduler_is_user_owned_and_not_registered() -> None:
    router = _text("AGENTS.md")
    role = _text(".agents/roles/RESEARCH_SCHEDULER.md")
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    for text in (router, role, contract):
        assert "user_owned_persistent_desktop_task" in text
        assert "registered_child=false" in text
        assert "profile_path=none" in text
        assert "task_lifecycle_and_resource_conflict_routing_only" in text
    assert ".codex" in role and "no `.codex` profile" in role
    assert "max_depth=1" in role


def test_scheduler_has_same_level_owner_modes_and_boundary() -> None:
    role = _text(".agents/roles/RESEARCH_SCHEDULER.md")
    assert "same-level ephemeral owner tasks" in role
    for mode in ("explorer_direction", "explorer_portfolio", "cpm_treatment", "cpm_integration"):
        assert mode in role
    for forbidden in (
        "science_authority=none",
        "code_authority=none",
        "technical_acceptance_authority=none",
        "git_authority=none",
        "runtime_execution_authority=none",
        "semantic_relay_authority=none",
        "sibling_preload_authority=none",
    ):
        assert forbidden in role


def test_frozen_desktop_path_is_exact_and_bounded() -> None:
    text = " ".join(_text(".agents/skills/hmasd-research-scheduler/SKILL.md").split())
    for cue in (
        "create_thread",
        "environment=local",
        "threadId",
        "hostId",
        "binding-ready follow-up",
        "wait_threads",
        "at most eight",
        "read_thread",
        "canonical locator",
        "Request archive/close for the exact thread",
        "archive",
        "one unresolved observation",
        "direct exact-ID resolution",
    ):
        assert cue in text
    assert "Do not retry blindly" in text


def test_binding_session_id_requires_exact_hook_identity_mapping() -> None:
    text = " ".join(_text(".agents/skills/hmasd-research-scheduler/SKILL.md").split()).lower()
    for cue in (
        "roster retains the returned exact `threadid`+`hostid` pair as task-observation locators",
        "binding's `session_id` is the exact owner hook session identity",
        "owner pretooluse/stop hook payloads",
        "desktop-exposed locator-to-hook-session mapping only when it is observable",
        "never substitute `hostid` or `threadid` for `session_id`",
        "never infer the mapping from titles or history",
        "before sending the binding-ready follow-up, mechanically match the returned task locator",
        "mapping is unavailable or ambiguous",
        "do not activate the binding or authorize mutation",
        "record one unresolved observation in the roster",
        "require exact desktop/user resolution",
        "do not create a second owner, retry, or scan threads",
    ):
        assert cue in text
    assert "assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active" in text
    assert "hook_session_id" not in text


def test_binding_schema_is_minimal_and_live_state_is_ignored() -> None:
    role = _text(".agents/roles/RESEARCH_SCHEDULER.md")
    readme = _text("docs/session-workspaces/research_scheduler/README.md")
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    for text in (role, readme, contract):
        assert "temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md" in text
        assert "temp/sessions/research_scheduler/bindings/<assignment_id>.json" in text
        assert "assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active" in text
        assert "mutation-boundary identity" in text
    assert "tracked_live_state=false" in readme
    assert "not task context" in role


def test_scheduler_rejects_stale_control_mechanisms_and_defers_context() -> None:
    role = _text(".agents/roles/RESEARCH_SCHEDULER.md")
    skill = _text(".agents/skills/hmasd-research-scheduler/SKILL.md")
    text = " ".join((role + "\n" + skill).split()).lower()
    for stale in (
        "polling loop",
        "daemon",
        "lease",
        "cas",
        "epoch",
        "revision",
        "idempotency",
        "thread scan",
        "blind retry",
        "cli assumption",
    ):
        assert stale in text
    assert "load the session workspace contract" in text
    assert "only when" in text


def test_resource_policy_has_no_fixed_pool_and_explicit_cloud_grant() -> None:
    text = _text(".agents/skills/hmasd-research-scheduler/SKILL.md")
    assert "no fixed capacity pool" in text
    assert "local formal" in text and "result-bearing runtime" in text
    assert "non-runtime work continues" in text
    for grant in ("provider", "budget", "credential", "egress"):
        assert grant in text


def test_no_scheduler_profile_or_config_is_registered() -> None:
    assert not (ROOT / ".codex/agents/hmasd-research-scheduler.toml").exists()
    assert not (ROOT / ".codex/agents/research_scheduler.toml").exists()
    router = _text("AGENTS.md")
    assert "research_scheduler_registered_child=false" in router
    assert "research_scheduler_profile_path=none" in router


def test_scheduler_procedure_and_resource_policy_have_one_skill_source() -> None:
    skill = _text(".agents/skills/hmasd-research-scheduler/SKILL.md")
    for path in (
        "AGENTS.md",
        "docs/project/SESSION_WORKSPACE_CONTRACT.md",
        "docs/project/WORKFLOW_MAP.md",
    ):
        text = _text(path)
        assert ".agents/skills/hmasd-research-scheduler/SKILL.md" in text
        for command_level in ("create_thread", "wait_threads", "read_thread"):
            assert command_level not in text
    assert "create_thread" in skill
    assert "wait_threads" in skill
    assert "read_thread" in skill


def test_result_read_revokes_binding_before_archive_and_cleans_roster() -> None:
    skill = " ".join(_text(".agents/skills/hmasd-research-scheduler/SKILL.md").split())
    role = " ".join(_text(".agents/roles/RESEARCH_SCHEDULER.md").split())
    readme = " ".join(_text("docs/session-workspaces/research_scheduler/README.md").split())

    assert "direct exact task" in skill
    assert "mechanically confirm" in skill
    assert "existing six-key binding's `active` value to `false` (`active=false`)" in skill
    assert skill.index("mechanically confirm") < skill.index("active=false")
    assert skill.index("active=false") < skill.index("Request archive/close")
    assert "revokes owner mutation authority before archival" in skill
    assert "If archive succeeds, remove the task's entry from the human-readable active roster" in skill
    assert "Canonical assignment/result locators remain restart/archive evidence" in skill
    assert "not a Scheduler result ledger" in skill
    assert "active=false_before_archive" in role
    assert "successful archive removes that task's entry from the active roster" in readme


def test_ambiguous_archive_keeps_binding_inactive_and_unresolved() -> None:
    text = " ".join(
        "\n".join(
            (
                _text(".agents/roles/RESEARCH_SCHEDULER.md"),
                _text(".agents/skills/hmasd-research-scheduler/SKILL.md"),
                _text("docs/session-workspaces/research_scheduler/README.md"),
            )
        ).split()
    ).lower()
    for cue in (
        "archive/close is ambiguous",
        "binding stays inactive",
        "binding remains inactive",
        "one unresolved observation",
        "direct exact-id or user resolution",
        "never reactivate",
        "blindly retry",
        "replacement owner",
        "active=true",
        "stale identity remains fail-closed",
    ):
        assert cue in text


def test_binding_schema_adds_no_lifecycle_fields_queue_or_state_machine() -> None:
    texts = (
        _text(".agents/roles/RESEARCH_SCHEDULER.md"),
        _text(".agents/skills/hmasd-research-scheduler/SKILL.md"),
        _text("docs/session-workspaces/research_scheduler/README.md"),
    )
    schema = "assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active"
    for text in texts:
        assert schema in text
    joined = " ".join(texts).lower()
    assert "no new lifecycle fields" in joined
    assert "no new" in joined and "queue state" in joined
    assert "no new" in joined and "state machine" in joined
    assert "not a scheduler result ledger" in joined
