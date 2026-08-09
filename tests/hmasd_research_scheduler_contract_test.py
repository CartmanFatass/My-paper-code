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


def test_identity_probe_observes_exact_hook_identity() -> None:
    text = " ".join(_text(".agents/skills/hmasd-research-scheduler/SKILL.md").split()).lower()
    for cue in (
        "read-only identity-probe follow-up to that exact `threadid`+`hostid`",
        "c:/users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_workspace_boundary_guard.py observe-owner-session --assignment-id <id> --thread-id <threadid> --host-id local",
        "existing pretooluse guard observes the real payload `session_id`",
        "requires inherited `codex_thread_id==threadid` and host `local`",
        "writes exactly four keys `assignment_id|thread_id|host_id|session_id`",
        "temp/sessions/research_scheduler/identity_observations/<assignment_id>.json",
        "identity observation is read-only",
        "does not authorize mutation or activate a binding",
        "not task context, a queue, registry, ledger, semantic result or acceptance",
        "mechanically match all four observed facts to the exact create result and assignment",
        "only after that match create the unchanged binding",
        "one separate binding-ready follow-up",
        "observation is missing or conflicting",
        "the binding stays inactive",
        "never scan, infer, substitute `hostid` or `threadid`, create a replacement, or retry blindly",
    ):
        assert cue in text
    assert "assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active" in text
    assert "desktop-exposed locator-to-hook-session mapping" not in text
    assert "desktop-exposed" not in text


def test_identity_probe_and_binding_ready_are_separate_actions() -> None:
    text = " ".join(_text(".agents/skills/hmasd-research-scheduler/SKILL.md").split()).lower()
    probe = text.index("identity-probe follow-up")
    ready = text.index("binding-ready follow-up")
    assert probe < ready
    assert "this identity observation is read-only" in text
    assert "separate binding-ready follow-up" in text
    assert "binding-ready follow-up" in text


def test_binding_schema_is_minimal_and_live_state_is_ignored() -> None:
    role = _text(".agents/roles/RESEARCH_SCHEDULER.md")
    readme = _text("docs/session-workspaces/research_scheduler/README.md")
    contract = _text("docs/project/SESSION_WORKSPACE_CONTRACT.md")
    for text in (role, readme, contract):
        assert "temp/sessions/research_scheduler/ACTIVE_ASSIGNMENTS.md" in text
        assert "temp/sessions/research_scheduler/bindings/<assignment_id>.json" in text
        assert "assignment_id|session_id|owner_role|owner_mode|allowed_write_paths|active" in text
        assert "mutation-boundary identity" in text
        assert "identity_observation" in text
    assert "tracked_live_state=false" in readme
    assert "not task context" in role


def test_portfolio_scheduler_boundary_is_explorer_owned_and_bounded() -> None:
    role = " ".join(_text(".agents/roles/RESEARCH_SCHEDULER.md").split()).lower()
    skill = " ".join(_text(".agents/skills/hmasd-research-scheduler/SKILL.md").split()).lower()
    for cue in (
        "the explorer owns portfolio target/state `12`",
        "initial owner concurrency ceiling of `3`",
        "active same-level `owner_mode=direction` tasks",
        "excludes the portfolio owner, registered native children and the result-bearing runtime pool",
        "exact explorer-authored ready assignments in their preserved order",
        "may launch fewer than three",
        "named dependency or an observed write/resource conflict",
        "never fills slots, invents readiness, reprioritizes, merges, retires or scientifically selects",
        "return the result to the portfolio explorer for intake before any successor is marked ready",
        "never binding, roster, queue or scheduler state",
    ):
        assert cue in (role + " " + skill)


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
    text = " ".join(_text(".agents/skills/hmasd-research-scheduler/SKILL.md").split())
    assert "not a runtime capacity pool" in text
    assert "no fixed runtime capacity pool" in text
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
    joined = " ".join(" ".join(text.split()) for text in texts).lower()
    assert "no new lifecycle fields" in joined
    assert "no new" in joined and "queue state" in joined
    assert "no new" in joined and "state machine" in joined
    assert "not a scheduler result ledger" in joined
