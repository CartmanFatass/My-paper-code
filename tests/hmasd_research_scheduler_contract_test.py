from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / ".agents/roles/RESEARCH_SCHEDULER.md"
SKILL = ROOT / ".agents/skills/hmasd-research-scheduler/SKILL.md"
README = ROOT / "docs/session-workspaces/research_scheduler/README.md"
CONTRACT = ROOT / "docs/project/SESSION_WORKSPACE_CONTRACT.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _joined(*paths: Path) -> str:
    return " ".join(" ".join(_text(path).split()) for path in paths).lower()


def test_scheduler_is_user_owned_and_not_registered() -> None:
    router = _text(ROOT / "AGENTS.md")
    role = _text(ROLE)
    contract = _text(CONTRACT)
    for text in (router, role, contract):
        assert "user_owned_persistent_desktop_task" in text
        assert "registered_child=false" in text
        assert "profile_path=none" in text
        assert "task_lifecycle_and_resource_conflict_routing_only" in text
    assert ".codex" in role and "no `.codex` profile" in role
    assert "max_depth=1" in role


def test_native_handle_is_the_only_scheduler_lifecycle_identity() -> None:
    text = _joined(ROLE, SKILL, README, CONTRACT)
    for cue in (
        "desktop_handle=threadid|hostid",
        "exact_desktop_lifecycle_and_routing_identity",
        "single_create_thread_return",
        "exact native `{threadid, hostid}`",
        "lifecycle/routing identity",
        "wait_threads",
        "read_thread",
        "archive",
    ):
        assert cue in text
    for stale in (
        "identity_observation",
        "binding-ready",
        "temporary handshake",
        "session binding",
        "file handshake",
        "outer `functions.exec` probe",
    ):
        assert stale not in text


def test_owner_assignment_is_prose_first_and_names_exact_write_ownership() -> None:
    text = _joined(ROLE, SKILL, README)
    for cue in (
        "self-contained natural-language assignment",
        "exact cooperative write ownership",
        "canonical result destination",
        "why the task exists",
        "protected decisions",
        "bounded recovery",
        "same-file writers serialize",
        "disjoint exact files may overlap",
        "direction owner writes/returns only",
        "portfolio explorer alone writes shared portfolio continuity",
        "treatment cpm owner writes only its ticket worktree",
        "integration cpm owner writes the shared mainline",
    ):
        assert cue in text


def test_roster_and_files_are_artifacts_not_identity_proof() -> None:
    text = _joined(ROLE, README, CONTRACT)
    for cue in (
        "optional",
        "human-readable restart locator",
        "not proof of llm identity",
        "artifact and continuity",
        "not authority",
        "no tracked live state",
    ):
        assert cue in text
    assert "research_scheduler_roster_purpose=human_readable_restart_locator_only" in _text(CONTRACT)


def test_portfolio_cardinality_and_ceiling_remain_explorer_owned() -> None:
    role = _joined(ROLE)
    skill = _joined(SKILL)
    assert "portfolio_cardinality_owner=independent_research_explorer" in role
    assert "derived_by_explorer_from_canonical_scientific_facts" in role
    for cue in (
        "workflow never compresses, pads, fills, merges",
        "initial owner concurrency ceiling of `3`",
        "active same-level `owner_mode=direction` tasks",
        "excludes the portfolio owner",
        "may launch fewer than three",
        "named dependency or an observed write/resource conflict",
        "never fills slots, invents readiness, reprioritizes, merges",
        "return the result to the portfolio explorer for intake",
    ):
        assert cue in skill


def test_scheduler_has_no_queue_monitor_registry_or_task_scan() -> None:
    text = _joined(ROLE, SKILL, README, CONTRACT)
    for cue in (
        "no queue",
        "monitor",
        "registry",
        "no task scan",
        "known exact native handles only",
        "never blindly retry",
    ):
        assert cue in text


def test_resource_policy_has_no_fixed_pool_and_explicit_cloud_grant() -> None:
    text = _joined(SKILL)
    assert "not a runtime capacity pool" in text
    assert "no fixed runtime capacity pool" in text
    assert "local formal" in text and "result-bearing runtime" in text
    assert "non-runtime work continues" in text
    for grant in ("provider", "budget", "credential", "egress"):
        assert grant in text


def test_no_scheduler_profile_or_config_is_registered() -> None:
    assert not (ROOT / ".codex/agents/hmasd-research-scheduler.toml").exists()
    assert not (ROOT / ".codex/agents/research_scheduler.toml").exists()
    router = _text(ROOT / "AGENTS.md")
    assert "research_scheduler_registered_child=false" in router
    assert "research_scheduler_profile_path=none" in router


def test_scheduler_procedure_and_resource_policy_have_one_skill_source() -> None:
    skill = _text(SKILL)
    for path in (
        ROOT / "AGENTS.md",
        CONTRACT,
        ROOT / "docs/project/WORKFLOW_MAP.md",
    ):
        text = _text(path)
        assert ".agents/skills/hmasd-research-scheduler/SKILL.md" in text
        for command_level in ("create_thread", "wait_threads", "read_thread"):
            assert command_level not in text
    assert "create_thread" in skill
    assert "wait_threads" in skill
    assert "read_thread" in skill


def test_direct_handle_result_read_precedes_archive_and_roster_cleanup() -> None:
    skill = " ".join(_text(SKILL).split())
    readme = " ".join(_text(README).split())
    assert "direct exact handle with `read_thread`" in skill
    assert skill.index("direct exact handle with `read_thread`") < skill.index("Archive/close that exact native handle")
    assert "may remove its roster locator" in skill
    assert "optional roster locator after successful archive" in readme


def test_ambiguous_archive_preserves_live_owner_and_uses_exact_resolution() -> None:
    text = _joined(ROLE, SKILL, README)
    for cue in (
        "archive/close is ambiguous",
        "preserve the owner",
        "direct exact-handle",
        "user resolution",
        "never blindly retry",
        "never create a replacement",
    ):
        assert cue in text
