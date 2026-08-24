"""Phase 7 pressure evidence for the public HMASD recovery contracts.

The recovery manager has no private Python API.  These tests therefore use the
state, run, and worktree command-line contracts and inspect only the published
recovery Skill for the manager-only decisions (generation rotation, late-result
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

from scripts import hmasd_external_review as external_review


ROOT = Path(__file__).resolve().parents[1]
PHASE0_FIXTURES = ROOT / "tests" / "fixtures" / "hmasd_phase0"
RECOVERY_FIXTURES = ROOT / "tests" / "fixtures" / "hmasd_recovery"
STATE_SCRIPT = ROOT / "scripts" / "hmasd_state.py"
RUN_SCRIPT = ROOT / "scripts" / "hmasd_run.py"
WORKTREE_SCRIPT = ROOT / "scripts" / "hmasd_worktree.py"
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
    )
    missing = [
        " / ".join(alternatives)
        for alternatives in required_boundaries
        if not any(term in skill for term in alternatives)
    ]
    assert not missing, f"recovery Skill omits pressure boundary terms: {missing}"


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
        "Portfolio",
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
        "hmasd-research-artifact-writer",
        "hmasd-external-pro-transport",
        "hmasd-external-gemini-transport",
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


def test_worktree_inspect_and_provision_refuse_an_orphan_duplicate(
    tmp_path: Path,
) -> None:
    """A journaled Git mutation is inspected, never blindly provisioned twice."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch", "omp/workflow")
    (repo / ".omp").mkdir()
    (repo / ".omp" / "AGENTS.md").write_text("# test root\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "-c", "user.name=HMASD Test", "-c", "user.email=hmasd@example.invalid", "commit", "-m", "initial")
    base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    container = tmp_path / "worktrees"
    container.mkdir()
    entry = _load(PHASE0_FIXTURES / "runtime_worktrees.json")["worktrees"][0]
    entry.update(
        {
            "base_sha": base_sha,
            "branch": "omp/example-direction/engineering/run-example",
            "canonical_absolute_path": str(container / "example-direction-engineering-run-example"),
            "lifecycle": "PROVISIONING",
            "operation_token": "0123456789abcdef0123456789abcdef",
        }
    )
    runtime = _load(PHASE0_FIXTURES / "runtime_worktrees.json")
    runtime["worktrees"] = [entry]
    runtime_dir = repo / ".omp" / "runtime"
    runtime_dir.mkdir()
    runtime_path = runtime_dir / "worktrees.json"
    runtime_path.write_text(json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    inspected = _run(WORKTREE_SCRIPT, "inspect", "--worktree-ref", "wt-example", cwd=repo)
    assert inspected.returncode == 6, (inspected.stdout, inspected.stderr)
    observation = _load_json_text(inspected.stdout)
    assert observation.get("orphaned") is True, observation
    assert observation.get("orphan_reason"), observation

    before = runtime_path.read_bytes()
    provisioned = _run(
        WORKTREE_SCRIPT,
        "provision",
        "--repo",
        str(repo),
        "--container",
        str(container),
        "--direction",
        "example-direction",
        "--kind",
        "engineering",
        "--assignment",
        "run-example",
        "--base",
        base_sha,
        cwd=repo,
    )
    assert provisioned.returncode == 6, (provisioned.stdout, provisioned.stderr)
    assert runtime_path.read_bytes() == before
    assert not (container / "example-direction-engineering-run-example").exists()

def test_external_unknown_commitment_is_not_resent_and_archive_import_is_idempotent(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """Agentify remains authoritative for commitment and exact archive bytes."""

    archive = tmp_path / "archive.json"
    archive.write_bytes((PHASE0_FIXTURES / "external_archive.json").read_bytes())

    unknown = _run(
        EXTERNAL_SCRIPT,
        "validate-archive",
        "--operation-ref",
        str(RECOVERY_FIXTURES / "unknown_operation_ref.json"),
        "--archive",
        str(archive),
    )
    assert unknown.returncode == 7, (unknown.stdout, unknown.stderr)

    destination = (
        tmp_path
        / "docs/external-review/directions/example-direction/a2604c701f39adec08f5/chatgpt"
        / "NATURAL_COMPLETION_ARCHIVE.json"
    )
    monkeypatch.setattr(external_review, "_PROJECT_ROOT", tmp_path)
    operation = _load(RECOVERY_FIXTURES / "committed_operation_ref.json")
    committed = external_review.create_archive_if_absent(operation, archive, destination)
    assert committed["status"] == "CREATED"
    first_bytes = destination.read_bytes()

    repeated = external_review.create_archive_if_absent(operation, archive, destination)
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
        "failure_class": "external_commitment_unknown",
        "resume_condition": "user_decides_how_to_verify_the_existing_operation_before_any_resend",
        "user_visible": True,
    }
    skill = _recovery_skill()
    for term in ("duplicate", "distinct", "budget", "exhaust", "blocker", "resume"):
        assert term in skill


def _load_json_text(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    assert isinstance(payload, dict)
    return payload


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
