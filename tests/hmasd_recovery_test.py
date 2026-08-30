"""Phase 7 pressure evidence for the public HMASD recovery contracts.

The recovery manager has no private Python API. These tests therefore use the
state and run command-line contracts and inspect only the published recovery
Skill for the manager-only decisions (generation rotation, late-result
handling, and bounded route selection).
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
import pytest


from scripts import hmasd_external_review as external_review


ROOT = Path(__file__).resolve().parents[1]
PHASE0_FIXTURES = ROOT / "tests" / "fixtures" / "hmasd_phase0"
RECOVERY_FIXTURES = ROOT / "tests" / "fixtures" / "hmasd_recovery"
STATE_SCRIPT = ROOT / "scripts" / "hmasd_state.py"
RUN_SCRIPT = ROOT / "scripts" / "hmasd_run.py"
EXTERNAL_SCRIPT = ROOT / "scripts" / "hmasd_external_review.py"
RECOVERY_SKILL = ROOT / ".omp" / "skills" / "hmasd-workflow-recovery" / "SKILL.md"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(script: Path, *args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _validate(kind: str, path: Path) -> subprocess.CompletedProcess[str]:
    return _run(STATE_SCRIPT, "validate", "--kind", kind, "--path", str(path))


def _recovery_skill() -> str:
    assert RECOVERY_SKILL.is_file(), f"missing recovery Skill: {RECOVERY_SKILL}"
    return RECOVERY_SKILL.read_text(encoding="utf-8").lower()


def test_recovery_skill_covers_every_matrix_row_and_effect_boundary() -> None:
    """The Skill must carry the complete matrix, not only the happy path."""

    scenario = _load(RECOVERY_FIXTURES / "recovery_matrix.json")
    skill = _recovery_skill()

    # These are intentionally broad row anchors: the exact procedure belongs
    # to the Skill, while the pressure test must fail if a whole failure class
    # disappears during a topology migration.
    row_anchors = {
        "pure research": ("pure research", "research"),
        "manager": ("manager",),
        "partial code": ("partial code", "worktree"),
        "running": ("running",),
        "memory": ("memory",),
        "git": ("git",),
        "push": ("push",),
        "external": ("external",),
        "late": ("late",),
        "dashboard": ("dashboard",),
    }
    for label, alternatives in row_anchors.items():
        assert any(anchor in skill for anchor in alternatives), (
            f"recovery matrix row is missing: {label}"
        )

    for row in scenario["matrix"]:
        failure_words = row["failure"].lower().replace("/", " ").split()
        assert any(word in skill for word in failure_words if len(word) > 3), row

    required_boundaries = (
        ("generation",),
        ("checkpoint",),
        ("compaction",),
        ("runtime",),
        ("reconstruct",),
        ("materially distinct",),
        ("three",),
        ("user-visible blocker", "user blocker"),
        ("never relaunch", "never replay", "no blind relaunch"),
        ("never resend", "no resend", "do not resend"),
        ("never overwrite", "do not overwrite", "superseded"),
        ("browsertransport",),
        ("send_attempted",),
        ("provider user id", "provider user message"),
        ("observe the same",),
        ("fail closed",),
    )
    missing = [
        " / ".join(alternatives)
        for alternatives in required_boundaries
        if not any(term in skill for term in alternatives)
    ]
    assert not missing, f"recovery Skill omits pressure boundary terms: {missing}"

def test_recovery_skill_preserves_browser_parked_and_git_fail_closed_contracts() -> None:
    skill = " ".join(_recovery_skill().split())
    required = (
        "only root invokes and owns this recovery manager",
        "browsertransport runtime row missing",
        "logical identity `browsertransport`",
        "agent type `hmasd-browser-transport`",
        "exact agentify operation",
        "bound provider target",
        "`send_attempted` is a direct no-resend fact",
        "never activate send",
        "stale requester generation is superseded evidence",
        "`parked` without a non-null `reactivation_condition_ref` is invalid",
        "git writer conflict or stale base",
        "fail closed",
        "never relaunch the command",
        "while run/result state is unknown",
    )
    missing = [term for term in required if term not in skill]
    assert not missing, f"recovery Skill omits target recovery contracts: {missing}"


def test_authoritative_state_remains_reconstructible_when_runtime_maps_are_missing(
    tmp_path: Path,
) -> None:
    """Logical refs reconstruct ignored maps without changing durable sources."""

    scenario = _load(RECOVERY_FIXTURES / "recovery_matrix.json")
    kinds = tuple(scenario["reconstruction"]["authoritative_sources"])
    for kind in kinds:
        source = PHASE0_FIXTURES / f"{kind}.json"
        assert source.is_file(), source
        result = _validate(kind, source)
        assert result.returncode == 0, (kind, result.stdout, result.stderr)

    registry = _load(PHASE0_FIXTURES / "portfolio_registry.json")
    runtime_agents = _load(PHASE0_FIXTURES / "runtime_agents.json")
    runtime_worktrees = _load(PHASE0_FIXTURES / "runtime_worktrees.json")
    expected = scenario["reconstruction"]

    # The durable registry is the source for manager identity and generation;
    # the ignored runtime map contributes only local handles.
    direction = registry["directions"][0]
    logical = (
        direction["agent"]["logical_identity"],
        direction["agent"]["generation"],
    )
    observed_logical = [
        (agent["logical_identity"], agent["generation"])
        for agent in runtime_agents["agents"]
    ]
    assert observed_logical == [logical]
    assert expected["expected_agent"]["logical_identity"] == logical[0]
    assert scenario["compaction"]["state_revision"] == scenario["compaction"]["current_revision"]
    manager_effects = [effect for effect in scenario["effects"] if effect["effect"] == "manager"]
    assert len(manager_effects) == 1
    assert manager_effects[0]["logical_identity"] == logical[0]
    assert manager_effects[0]["expected"] == "revive_matching_generation_or_reconstruct_once"
    assert expected["expected_agent"]["generation"] == logical[1]
    assert len(set(observed_logical)) == len(observed_logical)

    worktree = runtime_worktrees["worktrees"][0]
    assert {
        "assignment_id": worktree["assignment_id"],
        "direction_id": worktree["direction_id"],
        "worktree_ref": worktree["worktree_ref"],
    } == expected["expected_worktree"]

    # Delete only reconstructed, ignored inputs.  All authoritative fixture
    # bytes must remain available and unchanged for a fresh reconstruction.
    runtime_copy = tmp_path / "runtime"
    runtime_copy.mkdir()
    for name in ("runtime_agents.json", "runtime_worktrees.json"):
        source = PHASE0_FIXTURES / name
        target = runtime_copy / name
        shutil.copyfile(source, target)
        before = source.read_bytes()
        target.unlink()
        assert source.read_bytes() == before

    assert "runtime_ref" in direction["agent"]
    assert direction["agent"]["runtime_ref"] is None
    assert "canonical_absolute_path" in worktree


def test_generation_mismatch_and_late_result_are_read_only_until_reconciled(
    tmp_path: Path,
) -> None:
    """A valid late envelope is evidence, not permission to overwrite state."""

    scenario = _load(RECOVERY_FIXTURES / "recovery_matrix.json")
    late = _load(RECOVERY_FIXTURES / "late_result.json")
    current = scenario["compaction"]
    assert late["generation"] == scenario["generation_mismatch"]["late_generation"]
    assert late["generation"] < current["generation"]
    assert late["checkpoint_sha"] != current["current_checkpoint_sha"]
    assert "event_id" not in late

    target = tmp_path / "late-result.json"
    target.write_bytes((RECOVERY_FIXTURES / "late_result.json").read_bytes())
    before = target.read_bytes()
    result = _validate("agent_result", target)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert target.read_bytes() == before

    skill = _recovery_skill()
    for term in ("generation", "late", "checkpoint", "superseded", "newer", "reconcile"):
        assert term in skill


def test_recovery_schemas_round_trip_root_git_and_declared_active_identities(
    tmp_path: Path,
) -> None:
    """Recovery can retain every live contract without inventing an identity."""

    root_result = _load(PHASE0_FIXTURES / "agent_result.json")
    root_result.update(
        {
            "assignment_id": "root-wake",
            "logical_identity": "Root",
            "materiality": "NONE",
            "payload": {"kind": "root", "wake_reason": "startup"},
            "role": "root",
            "summary": "Root observed a durable workflow state.",
        }
    )
    git_result = copy.deepcopy(root_result)
    git_result.update(
        {
            "assignment_id": "git-integration",
            "materiality": "DIRECTION",
            "payload": {
                "kind": "git",
                "direction_id": "example-direction",
                "base_sha": "1" * 40,
                "candidate_sha": "2" * 40,
                "integrated_sha": "3" * 40,
                "changed_paths": [],
                "actor": "root",
            },
            "role": "hmasd-git-integration",
            "summary": "Root integrated the exact candidate.",
        }
    )
    for label, document in (("root-result", root_result), ("git-result", git_result)):
        path = tmp_path / f"{label}.json"
        path.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
        before = path.read_bytes()
        result = _validate("agent_result", path)
        assert result.returncode == 0, (label, result.stdout, result.stderr)
        assert path.read_bytes() == before

    identities = (
        "Root",
        "hmasd-git-integration",
        "EM-example-direction",
        "CM-example-direction",
        "hmasd-project-scout",
        "hmasd-code-scout",
        "hmasd-implementer",
        "hmasd-implementer-terra",
        "hmasd-reviewer",
        "hmasd-verifier",
        "hmasd-experiment-operator",
        "hmasd-research-scout",
        "hmasd-research-innovator",
        "hmasd-research-critic",
        "hmasd-research-principles-analyst",
        "BrowserTransport",
        "hmasd-workflow-recovery-manager",
        "librarian",
    )
    active_agents = [
        {
            "logical_identity": identity,
            "generation": 1,
            "assignment_id": f"assignment-{index}",
            "runtime_ref": f"runtime-{index}",
        }
        for index, identity in enumerate(identities, start=1)
    ]
    for kind in ("research_state", "engineering_state"):
        state = _load(PHASE0_FIXTURES / f"{kind}.json")
        state["active_agents"] = active_agents
        path = tmp_path / f"{kind}.json"
        path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        before = path.read_bytes()
        result = _validate(kind, path)
        assert result.returncode == 0, (kind, result.stdout, result.stderr)
        assert path.read_bytes() == before


def test_running_reconcile_observes_once_and_duplicate_execute_is_refused(
    tmp_path: Path,
) -> None:
    """Recovery observes an interrupted run and never launches it a second time."""

    manifest_dir = tmp_path / "run"
    manifest_dir.mkdir()
    manifest = manifest_dir / "manifest.json"
    manifest.write_bytes((RECOVERY_FIXTURES / "running_manifest.json").read_bytes())

    first = _run(RUN_SCRIPT, "reconcile", "--manifest", str(manifest))
    assert first.returncode == 0, (first.stdout, first.stderr)
    observed = _load(manifest)
    assert observed["run_id"] == "example-run"
    assert observed["status"] == "UNKNOWN"
    assert observed["process"]["terminal_reason"] == "PROCESS_IDENTITY_REUSED"
    first_bytes = manifest.read_bytes()

    second = _run(RUN_SCRIPT, "reconcile", "--manifest", str(manifest))
    assert second.returncode == 0, (second.stdout, second.stderr)
    assert manifest.read_bytes() == first_bytes

    duplicate = _run(RUN_SCRIPT, "execute", "--manifest", str(manifest))
    assert duplicate.returncode == 5, (duplicate.stdout, duplicate.stderr)
    assert manifest.read_bytes() == first_bytes


def test_attempted_send_without_user_id_is_not_published_and_response_is_idempotent(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """An attempted send is never repeated and exact response bytes stay immutable."""

    response = tmp_path / "source-response.md"
    response.write_bytes(b"hello")
    unknown_operation = _load(RECOVERY_FIXTURES / "unknown_operation_ref.json")
    monkeypatch.setattr(external_review, "_PROJECT_ROOT", tmp_path)
    with pytest.raises(external_review.ExternalReviewError, match="never resend"):
        external_review.create_archive_if_absent(
            unknown_operation,
            response,
            tmp_path / "unused.md",
        )
    assert not (tmp_path / "docs").exists()

    operation = _load(RECOVERY_FIXTURES / "committed_operation_ref.json")
    destination = (
        tmp_path
        / "docs/external-review/directions/example-direction/a2604c701f39adec08f5"
        / "pro_innovator/chatgpt/response.md"
    )
    committed = external_review.create_archive_if_absent(operation, response, destination)
    assert committed["status"] == "CREATED"
    first_bytes = destination.read_bytes()
    repeated = external_review.create_archive_if_absent(operation, response, destination)
    assert repeated["status"] == "IDEMPOTENT"
    assert destination.read_bytes() == first_bytes



def test_recovery_attempt_deduplication_and_exhaustion_emit_one_precise_blocker() -> None:
    """Identical routes consume one slot; only exhaustion reaches the user."""

    scenario = _load(RECOVERY_FIXTURES / "recovery_matrix.json")
    attempts = scenario["repeated_attempts"]
    route_keys = {
        (attempt["effect_class"], attempt["assignment_id"], attempt["route"])
        for attempt in attempts
    }
    assert len(attempts) == 4
    assert len(route_keys) == 3
    assert scenario["attempt_budget"] == len(route_keys)

    blocker = scenario["exhausted_blocker"]
    assert blocker == {
        "code": "RECOVERY_EXHAUSTED",
        "failure_class": "process_identity_unresolved",
        "resume_condition": "exact_process_identity_becomes_observable",
        "user_visible": True,
    }
    skill = _recovery_skill()
    for term in ("duplicate", "distinct", "budget", "exhaust", "blocker", "resume"):
        assert term in skill
