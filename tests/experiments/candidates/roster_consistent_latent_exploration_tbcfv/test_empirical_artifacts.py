from __future__ import annotations

from dataclasses import dataclass, replace
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable, Mapping

import pytest

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (
    empirical_artifacts as empirical_artifact_module,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_artifacts import (
    ArtifactRef,
    ANALYZER_OUTPUT_SCHEMA,
    AtomicEmpiricalFrontier,
    BLOCK_COUNT,
    BLOCK_COUNTS,
    EMPIRICAL_OBJECT,
    EmpiricalArtifactError,
    EmpiricalBindings,
    HELDOUT_EPISODES_PER_CELL,
    LEARNED_ARMS,
    LOCK_SCHEMA,
    PANEL_COUNTS,
    REGISTERED_TAIL_COUNT,
    REGISTERED_TAIL_NAMES,
    RESULT_OUTPUT_SCHEMA,
    ResumeState,
    SCRIPTED_PANELS,
    StagedGeneration,
    UPDATE_COUNT,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_contract import (
    PANEL_COUNTS as CONTRACT_PANEL_COUNTS,
    SOURCE_REPAIR_REASON,
    SOURCE_REPAIR_TRANSITION_SCHEMA,
    document_sha256,
    validate_source_repair_replacement_lease,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.inference import (
    HELDOUT_CELLS,
)


OWNER = "synthetic-parent-owner"
NOW = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class _SyntheticPermit:
    lease_id: str
    origin_lease_id: str = "synthetic-origin-lease"
    predecessor_lease_id: str | None = None
    replacement_index: int = 0
    lease_lineage: tuple[str, ...] = ("synthetic-origin-lease",)
    stage_binding_sha256: str = "f" * 64
    accepted_binding_sha256: str = "7" * 64
    preactivity_certificate_sha256: str = "8" * 64
    coordinate_proposal_sha256: str = "9" * 64
    paths: Mapping[str, str] | None = None
    repair_transition_sha256: str | None = None

    def require_active(self, *, now: datetime) -> None:
        if now != NOW:
            raise PermissionError("synthetic permit inactive")

    def immutable_frontier_lease_binding(self) -> dict[str, str]:
        return {
            "origin_lease_id": self.origin_lease_id,
            "lease_id": self.origin_lease_id,
            "lease_binding_sha256": self.stage_binding_sha256,
        }


def _permit(
    lease_id: str = "synthetic-origin-lease",
    *,
    replacement_of: str | None = None,
    stage_binding_sha256: str = "f" * 64,
    accepted_binding_sha256: str = "7" * 64,
    preactivity_certificate_sha256: str = "8" * 64,
    paths: Mapping[str, str] | None = None,
    repair_transition_sha256: str | None = None,
) -> _SyntheticPermit:
    if replacement_of is None:
        return _SyntheticPermit(
            lease_id=lease_id,
            stage_binding_sha256=stage_binding_sha256,
            accepted_binding_sha256=accepted_binding_sha256,
            preactivity_certificate_sha256=preactivity_certificate_sha256,
            paths=paths,
            repair_transition_sha256=repair_transition_sha256,
        )
    return _SyntheticPermit(
        lease_id=lease_id,
        predecessor_lease_id=replacement_of,
        replacement_index=1,
        lease_lineage=("synthetic-origin-lease", lease_id),
        stage_binding_sha256=stage_binding_sha256,
        accepted_binding_sha256=accepted_binding_sha256,
        preactivity_certificate_sha256=preactivity_certificate_sha256,
        paths=paths,
        repair_transition_sha256=repair_transition_sha256,
    )


def _bindings() -> EmpiricalBindings:
    permit = _permit()
    immutable = permit.immutable_frontier_lease_binding()
    return EmpiricalBindings(
        source_manifest_sha256="1" * 64,
        config_sha256="2" * 64,
        native_binding_sha256="3" * 64,
        coordinate_digest="4" * 64,
        master_digest="5" * 64,
        origin_lease_id=immutable["origin_lease_id"],
        lease_id=immutable["lease_id"],
        lease_binding_sha256=immutable["lease_binding_sha256"],
    )


def _create(root: Path) -> AtomicEmpiricalFrontier:
    return AtomicEmpiricalFrontier.create(
        root,
        _bindings(),
        owner_token=OWNER,
        permit=_permit(),
        now=NOW,
        lease_document_sha256="a" * 64,
    )


def _resume(
    root: Path,
    *,
    bindings: EmpiricalBindings | None = None,
    permit: _SyntheticPermit | None = None,
    lease_document_sha256: str = "a" * 64,
    owner_token: str = OWNER,
    process_alive_probe: Callable[[int], bool] | None = None,
) -> AtomicEmpiricalFrontier:
    selected = permit or _permit()
    return AtomicEmpiricalFrontier.resume(
        root,
        bindings or _bindings(),
        owner_token=owner_token,
        permit=selected,
        now=NOW,
        lease_document_sha256=lease_document_sha256,
        process_alive_probe=process_alive_probe,
    )


def test_parent_commit_lock_serializes_threads_in_one_worker_process(tmp_path: Path) -> None:
    frontier = _create(tmp_path / "frontier")
    order: list[str] = []

    def commit(label: str) -> None:
        with frontier._exclusive_commit(OWNER):
            order.append(f"{label}:enter")
            time.sleep(0.02)
            order.append(f"{label}:exit")

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(commit, label) for label in ("a", "b")]
        for future in futures:
            future.result()

    assert order in (
        ["a:enter", "a:exit", "b:enter", "b:exit"],
        ["b:enter", "b:exit", "a:enter", "a:exit"],
    )
    assert not (frontier.root / "PARENT_COMMIT.lock").exists()


def _write_ref(root: Path, block_index: int, name: str, generation: int = 0) -> ArtifactRef:
    path = root / "blocks" / f"block_{block_index:02d}" / "data" / f"g{generation}_{name}.bin"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = f"fixed-synthetic-fixture:{block_index}:{generation}:{name}".encode("ascii")
    path.write_bytes(payload)
    return ArtifactRef.capture(root, path)


def _refs(root: Path, block_index: int, generation: int = 0) -> dict[str, object]:
    return {
        "models": {
            arm: _write_ref(root, block_index, f"model_{slot}", generation)
            for slot, arm in enumerate(LEARNED_ARMS)
        },
        "optimizers": {
            arm: _write_ref(root, block_index, f"optimizer_{slot}", generation)
            for slot, arm in enumerate(LEARNED_ARMS)
        },
        "baselines": {
            arm: _write_ref(root, block_index, f"baseline_{slot}", generation)
            for slot, arm in enumerate(LEARNED_ARMS)
        },
        "semantic": _write_ref(root, block_index, "semantic", generation),
        "aggregates": _write_ref(root, block_index, "aggregates", generation),
    }


def _staging_payloads() -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for slot in range(len(LEARNED_ARMS)):
        result[f"model_{slot}.pt"] = f"fixed-staged-model-{slot}".encode("ascii")
        result[f"optimizer_{slot}.json"] = f"fixed-staged-optimizer-{slot}".encode("ascii")
        result[f"baseline_{slot}.json"] = f"fixed-staged-baseline-{slot}".encode("ascii")
    result["semantic.json"] = b"fixed-staged-semantic"
    result["aggregates.json"] = b"fixed-staged-aggregates"
    return result


def _refs_from_staged(staged: StagedGeneration) -> dict[str, object]:
    refs = staged.refs
    return {
        "models": {arm: refs[f"model_{slot}.pt"] for slot, arm in enumerate(LEARNED_ARMS)},
        "optimizers": {
            arm: refs[f"optimizer_{slot}.json"] for slot, arm in enumerate(LEARNED_ARMS)
        },
        "baselines": {
            arm: refs[f"baseline_{slot}.json"] for slot, arm in enumerate(LEARNED_ARMS)
        },
        "semantic": refs["semantic.json"],
        "aggregates": refs["aggregates.json"],
    }


def _state(
    refs: dict[str, object],
    *,
    phase: str,
    updates: int,
    learned: int,
    scripted: int,
    complete_counts: bool = False,
) -> ResumeState:
    training_episodes = len(LEARNED_ARMS) * updates * 64
    learned_episodes = len(LEARNED_ARMS) * len(HELDOUT_CELLS) * learned
    scripted_episodes = len(SCRIPTED_PANELS) * len(HELDOUT_CELLS) * scripted
    total = training_episodes + learned_episodes + scripted_episodes
    counts = (
        dict(BLOCK_COUNTS)
        if complete_counts
        else {
            "training_episodes": training_episodes,
            "learned_heldout_episodes": learned_episodes,
            "scripted_heldout_episodes": scripted_episodes,
            "total_episodes": total,
            "environment_ticks": total * 64,
            "agent_ticks": 0,
            "agent_claim_decisions": 0,
            "candidate_pointer_scores": 0,
        }
    )
    return ResumeState(
        phase=phase,
        updates_completed={arm: updates for arm in LEARNED_ARMS},
        model_state=refs["models"],  # type: ignore[arg-type]
        optimizer_state=refs["optimizers"],  # type: ignore[arg-type]
        baselines=refs["baselines"],  # type: ignore[arg-type]
        semantic_coordinate=refs["semantic"],  # type: ignore[arg-type]
        aggregates=refs["aggregates"],  # type: ignore[arg-type]
        learned_heldout_completed={
            arm: {cell: learned for cell in HELDOUT_CELLS} for arm in LEARNED_ARMS
        },
        scripted_heldout_completed={
            package: {cell: scripted for cell in HELDOUT_CELLS}
            for package in SCRIPTED_PANELS
        },
        counts=counts,
    )


def _complete_state(root: Path, block_index: int) -> ResumeState:
    return _state(
        _refs(root, block_index),
        phase="BLOCK_COMPLETE",
        updates=UPDATE_COUNT,
        learned=HELDOUT_EPISODES_PER_CELL,
        scripted=HELDOUT_EPISODES_PER_CELL,
        complete_counts=True,
    )


def _complete_block(frontier: AtomicEmpiricalFrontier, index: int) -> None:
    frontier.commit_resume(index, _complete_state(frontier.root, index), owner_token=OWNER)
    frontier.seal_block(index, owner_token=OWNER)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode("ascii")


def _repaired_bindings() -> EmpiricalBindings:
    return replace(
        _bindings(),
        source_manifest_sha256="6" * 64,
        lease_binding_sha256="e" * 64,
    )


def _repair_transition(root: Path) -> dict[str, object]:
    body: dict[str, object] = {
        "schema": SOURCE_REPAIR_TRANSITION_SCHEMA,
        "fixture_only": True,
        "non_scientific": True,
        "reason": SOURCE_REPAIR_REASON,
        "direction_id": "roster_consistent_latent_exploration",
        "science_revision": "RCLE-TBCFV-SCIENCE-20260821-04",
        "empirical_object": EMPIRICAL_OBJECT,
        "origin_lease_id": "synthetic-origin-lease",
        "original": {
            "certificate_sha256": "8" * 64,
            "binding_sha256": "7" * 64,
            "request_sha256": "a" * 64,
            "source_set_sha256": "1" * 64,
            "stage_binding_sha256": "f" * 64,
            "lease_id": "synthetic-origin-lease",
        },
        "repaired": {
            "certificate_sha256": "c" * 64,
            "binding_sha256": "d" * 64,
            "request_sha256": "b" * 64,
            "source_set_sha256": "6" * 64,
            "stage_binding_sha256": "e" * 64,
        },
        "run_identity": {"fixture_only": True},
        "failed_terminal": {"fixture_only": True},
        "source_deltas": [
            {
                "logical_path": "experiments/candidates/roster_consistent_latent_exploration_tbcfv/empirical_artifacts.py",
                "old_sha256": "1" * 64,
                "new_sha256": "6" * 64,
                "reason": SOURCE_REPAIR_REASON,
            }
        ],
        "preserved": {
            "coordinate_binding_sha256": "4" * 64,
            "master_digest": "5" * 64,
            "run_block_roots": [
                {"block_index": index, "root_digest": f"{index + 16:064x}"}
                for index in range(BLOCK_COUNT)
            ],
            "result_root": str(root.parent / "synthetic-results"),
            "resource_ceiling": {"fixture_only": True},
            "config_sha256": "2" * 64,
            "native_identity_sha256": "3" * 64,
            "analyzer_sha256": "9" * 64,
            "counts": dict(CONTRACT_PANEL_COUNTS),
        },
        "science_change": False,
        "coordinate_materialization_authorized": False,
        "partial_interpretation_permitted": False,
    }
    return {
        **body,
        "repair_transition_sha256": hashlib.sha256(_canonical(body)).hexdigest(),
    }


def _repair_permit(root: Path, transition: Mapping[str, object]) -> _SyntheticPermit:
    return _permit(
        "synthetic-source-repair-lease",
        replacement_of="synthetic-origin-lease",
        stage_binding_sha256="e" * 64,
        accepted_binding_sha256="d" * 64,
        preactivity_certificate_sha256="c" * 64,
        paths={
            "frontier_root": str(root),
            "result_root": str(root.parent / "synthetic-results"),
        },
        repair_transition_sha256=str(transition["repair_transition_sha256"]),
    )


def _stage_failed_generation_zero(root: Path) -> AtomicEmpiricalFrontier:
    frontier = _create(root)
    frontier.stage_generation_payloads(0, _staging_payloads(), owner_token=OWNER)
    return frontier


def _publication_payloads(branch: str = "TARGET_UNRESOLVED") -> tuple[bytes, bytes]:
    analyzer = _canonical(
        {
            "schema": ANALYZER_OUTPUT_SCHEMA,
            "science_revision": "RCLE-TBCFV-SCIENCE-20260821-04",
            "empirical_object": EMPIRICAL_OBJECT,
            "block_count": BLOCK_COUNT,
            "registered_tail_count": REGISTERED_TAIL_COUNT,
            "registered_tail_names": list(REGISTERED_TAIL_NAMES),
            "branch": branch,
            "payload": {"test_fixture_only": True},
        }
    )
    result = _canonical(
        {
            "schema": RESULT_OUTPUT_SCHEMA,
            "science_revision": "RCLE-TBCFV-SCIENCE-20260821-04",
            "empirical_object": EMPIRICAL_OBJECT,
            "block_count": BLOCK_COUNT,
            "counts": dict(PANEL_COUNTS),
            "branch": branch,
            "analyzer_sha256": hashlib.sha256(analyzer).hexdigest(),
            "payload": {"test_fixture_only": True},
        }
    )
    return analyzer, result


def test_frozen_panel_inventory_and_counts_are_exact() -> None:
    assert EMPIRICAL_OBJECT == "RCLE-TBCFV-R04-FULL-EMPIRICAL-PANEL"
    assert BLOCK_COUNT == 20
    assert len(LEARNED_ARMS) == 5
    assert UPDATE_COUNT == 800
    assert len(HELDOUT_CELLS) == 8
    assert len(SCRIPTED_PANELS) == 3
    assert REGISTERED_TAIL_COUNT == 72
    assert len(REGISTERED_TAIL_NAMES) == len(set(REGISTERED_TAIL_NAMES)) == 72
    assert PANEL_COUNTS == {
        "training_episodes": 5_120_000,
        "learned_heldout_episodes": 1_638_400,
        "scripted_heldout_episodes": 983_040,
        "total_episodes": 7_741_440,
        "environment_ticks": 495_452_160,
        "agent_ticks": 4_299_161_600,
        "agent_claim_decisions": 1_074_790_400,
        "candidate_pointer_scores": 6_448_742_400,
    }


def test_atomic_write_uses_bounded_temp_name_at_production_length(tmp_path: Path) -> None:
    basename = "p" * 96 + ".bin"
    parent_component_length = 233 - len(str(tmp_path)) - 2 - len(basename)
    assert 1 <= parent_component_length <= 200
    parent = tmp_path / ("r" * parent_component_length)
    target = parent / basename
    assert len(str(target)) == 233
    payload = b"fixed-production-length-atomic-payload"

    empirical_artifact_module._write_exclusive(target, payload)

    assert target.read_bytes() == payload
    assert hashlib.sha256(target.read_bytes()).hexdigest() == hashlib.sha256(payload).hexdigest()
    assert not tuple(parent.glob(".aw-*.tmp"))
    with pytest.raises(EmpiricalArtifactError, match="create-only artifact already exists"):
        empirical_artifact_module._write_exclusive(target, b"must-not-overwrite")
    assert target.read_bytes() == payload


def test_ambiguous_bounded_temp_is_preserved_and_refused_on_resume(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    _create(root)
    resume_root = root / "blocks" / "block_00" / "resume"
    data_root = root / "blocks" / "block_00" / "data"
    resume_root.mkdir(parents=True)
    data_root.mkdir()
    ambiguous = resume_root / (".aw-" + "e" * 32 + ".tmp")
    ambiguous.write_bytes(b"injected-unproven-atomic-temp")

    with pytest.raises(EmpiricalArtifactError, match="generation inventory"):
        _resume(root)
    assert ambiguous.read_bytes() == b"injected-unproven-atomic-temp"


def test_create_and_resume_require_every_immutable_binding_and_parent_owner(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    bindings = _bindings()
    _create(root)
    resumed = _resume(root, bindings=bindings)
    assert resumed.bindings == bindings

    for field in (
        "source_manifest_sha256",
        "config_sha256",
        "native_binding_sha256",
        "coordinate_digest",
        "master_digest",
        "lease_binding_sha256",
    ):
        with pytest.raises(EmpiricalArtifactError, match="same-coordinate|stage binding"):
            _resume(root, bindings=replace(bindings, **{field: "b" * 64}))
    with pytest.raises(
        EmpiricalArtifactError,
        match="same-coordinate|origin lease lineage|must equal origin_lease_id",
    ):
        _resume(root, bindings=replace(bindings, origin_lease_id="synthetic-other-origin"))
    with pytest.raises(EmpiricalArtifactError, match="same-coordinate"):
        _resume(root, bindings=bindings, owner_token="synthetic-other-parent")


def test_replacement_lease_is_runtime_audit_not_coordinate_identity(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    refs = _refs(root, 0)
    frontier.commit_resume(
        0,
        _state(refs, phase="TRAINING", updates=1, learned=0, scripted=0),
        owner_token=OWNER,
    )
    replacement = _permit("synthetic-replacement-lease", replacement_of="synthetic-origin-lease")
    resumed = _resume(
        root,
        permit=replacement,
        lease_document_sha256="b" * 64,
    )
    assert resumed.bindings == _bindings()
    resumed.commit_resume(
        0,
        _state(
            refs,
            phase="TRAINING",
            updates=2,
            learned=0,
            scripted=0,
        ),
        owner_token=OWNER,
    )
    audits = sorted((root / "lease_audits").glob("lease_*.json"))
    assert [path.name for path in audits] == ["lease_000000.json", "lease_000001.json"]
    assert resumed.bindings.coordinate_digest == "4" * 64
    assert resumed.bindings.master_digest == "5" * 64

    bad_root = tmp_path / "bad-lineage-frontier"
    _create(bad_root)
    with pytest.raises(EmpiricalArtifactError, match="lineage"):
        _resume(
            bad_root,
            permit=_permit("synthetic-unrelated-lease", replacement_of="synthetic-not-current"),
            lease_document_sha256="c" * 64,
        )
    with pytest.raises(EmpiricalArtifactError, match="stage binding"):
        _resume(
            bad_root,
            permit=replace(
                _permit("synthetic-stage-drift", replacement_of="synthetic-origin-lease"),
                stage_binding_sha256="d" * 64,
            ),
            lease_document_sha256="d" * 64,
        )
    with pytest.raises(EmpiricalArtifactError, match="origin lease lineage"):
        _resume(
            bad_root,
            permit=replace(
                _permit("synthetic-origin-drift", replacement_of="synthetic-origin-lease"),
                origin_lease_id="synthetic-other-origin",
            ),
            lease_document_sha256="e" * 64,
        )


def test_source_repair_appends_bridge_without_rewriting_original_frontier(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-source-repair-frontier"
    _stage_failed_generation_zero(root)
    transition = _repair_transition(root)
    permit = _repair_permit(root, transition)
    original_manifest = (root / "bindings.json").read_bytes()
    original_audit = (root / "lease_audits" / "lease_000000.json").read_bytes()

    repaired = AtomicEmpiricalFrontier.apply_source_repair(
        root,
        _bindings(),
        _repaired_bindings(),
        repair_transition=transition,
        permit=permit,
        now=NOW,
        lease_document_sha256="b" * 64,
        owner_token=OWNER,
    )

    assert repaired.bindings == _repaired_bindings()
    assert (root / "bindings.json").read_bytes() == original_manifest
    assert (root / "lease_audits" / "lease_000000.json").read_bytes() == original_audit
    assert not (root / "blocks" / "block_00").exists()
    repair_packet = json.loads(
        (root / "stage_repairs" / "repair_000001.json").read_text("ascii")
    )
    assert repair_packet["repair_transition_sha256"] == transition["repair_transition_sha256"]
    assert repair_packet["old_lease_id"] == "synthetic-origin-lease"
    assert repair_packet["new_lease_id"] == "synthetic-source-repair-lease"
    assert repair_packet["recovered_staging_count"] == 1
    replacement_audit = json.loads(
        (root / "lease_audits" / "lease_000001.json").read_text("ascii")
    )
    assert replacement_audit["source_manifest_sha256"] == "6" * 64
    assert replacement_audit["stage_binding_sha256"] == "e" * 64
    assert replacement_audit["repair_transition_sha256"] == transition["repair_transition_sha256"]

    staged = repaired.stage_generation_payloads(0, _staging_payloads(), owner_token=OWNER)
    staging_manifest = json.loads(
        (
            root
            / "blocks"
            / "block_00"
            / ".staging"
            / f"generation_000000-{staged.token}"
            / "manifest.json"
        ).read_text("ascii")
    )
    assert staging_manifest["bindings_sha256"] == repaired.effective_bindings_sha256
    resumed = _resume(
        root,
        bindings=_repaired_bindings(),
        permit=permit,
        lease_document_sha256="b" * 64,
    )
    assert resumed.bindings == _repaired_bindings()
    assert not (root / "blocks" / "block_00").exists()
    continuation = _SyntheticPermit(
        lease_id="synthetic-post-repair-continuation",
        predecessor_lease_id="synthetic-source-repair-lease",
        replacement_index=2,
        lease_lineage=(
            "synthetic-origin-lease",
            "synthetic-source-repair-lease",
            "synthetic-post-repair-continuation",
        ),
        stage_binding_sha256="e" * 64,
        accepted_binding_sha256="d" * 64,
        preactivity_certificate_sha256="c" * 64,
    )
    continued = _resume(
        root,
        bindings=_repaired_bindings(),
        permit=continuation,
        lease_document_sha256="c" * 64,
    )
    assert continued.bindings == _repaired_bindings()
    continuation_audit = json.loads(
        (root / "lease_audits" / "lease_000002.json").read_text("ascii")
    )
    assert continuation_audit["source_manifest_sha256"] == "6" * 64
    assert continuation_audit["stage_binding_sha256"] == "e" * 64
    assert continuation_audit["repair_transition_sha256"] is None


def test_source_repair_accepts_public_contract_transition_root_shape(tmp_path: Path) -> None:
    from tests.experiments.candidates.roster_consistent_latent_exploration_tbcfv.test_empirical_contract import (
        _repair_fixture,
    )

    fixture_key = tmp_path / hashlib.sha256(str(tmp_path).encode("utf-8")).hexdigest()[:16]
    fixture_key.mkdir(parents=True, exist_ok=False)
    fixture = _repair_fixture(fixture_key)
    transition = fixture["transition"]
    original_permit = fixture["original_permit"]
    replacement = validate_source_repair_replacement_lease(
        fixture["replacement_lease"],
        repair_transition=transition,
        original_permit=original_permit,
        repaired_certificate=fixture["repaired_certificate"],
        repaired_binding=fixture["repaired_binding"],
        repaired_request=fixture["repaired_request"],
        now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
        synthetic_fixture=True,
    )
    preserved = transition["preserved"]
    assert isinstance(preserved, Mapping)
    roots = preserved["run_block_roots"]
    assert isinstance(roots, list)
    assert [row["block_index"] for row in roots] == list(range(BLOCK_COUNT))
    assert len({row["root_digest"] for row in roots}) == BLOCK_COUNT

    original_certificate = fixture["original_certificate"]
    repaired_certificate = fixture["repaired_certificate"]
    root = Path(original_permit.paths["frontier_root"])
    original_bindings = EmpiricalBindings(
        source_manifest_sha256=str(original_certificate["source"]["source_set_sha256"]),
        config_sha256=str(original_certificate["config"]["config_sha256"]),
        native_binding_sha256=str(original_certificate["native"]["native_identity_sha256"]),
        coordinate_digest=str(preserved["coordinate_binding_sha256"]),
        master_digest=str(preserved["master_digest"]),
        origin_lease_id=original_permit.origin_lease_id,
        lease_id=original_permit.origin_lease_id,
        lease_binding_sha256=original_permit.stage_binding_sha256,
    )
    repaired_bindings = replace(
        original_bindings,
        source_manifest_sha256=str(repaired_certificate["source"]["source_set_sha256"]),
        lease_binding_sha256=replacement.stage_binding_sha256,
    )
    frontier = AtomicEmpiricalFrontier.create(
        root,
        original_bindings,
        owner_token=OWNER,
        permit=original_permit,
        now=datetime(2026, 8, 21, 11, tzinfo=timezone.utc),
        lease_document_sha256="a" * 64,
    )
    frontier.stage_generation_payloads(0, _staging_payloads(), owner_token=OWNER)

    repaired = AtomicEmpiricalFrontier.apply_source_repair(
        root,
        original_bindings,
        repaired_bindings,
        repair_transition=transition,
        permit=replacement,
        now=datetime(2026, 8, 21, 13, tzinfo=timezone.utc),
        lease_document_sha256=document_sha256(fixture["replacement_lease"]),
        owner_token=OWNER,
    )
    assert repaired.bindings == repaired_bindings
    assert not (root / "blocks" / "block_00").exists()


def test_source_repair_rejects_committed_generation_and_duplicate_repair(tmp_path: Path) -> None:
    committed_root = tmp_path / "committed-frontier"
    committed = _create(committed_root)
    committed.commit_resume(
        0,
        _state(_refs(committed_root, 0), phase="TRAINING", updates=1, learned=0, scripted=0),
        owner_token=OWNER,
    )
    transition = _repair_transition(committed_root)
    with pytest.raises(EmpiricalArtifactError, match="committed|inventory"):
        AtomicEmpiricalFrontier.apply_source_repair(
            committed_root,
            _bindings(),
            _repaired_bindings(),
            repair_transition=transition,
            permit=_repair_permit(committed_root, transition),
            now=NOW,
            lease_document_sha256="b" * 64,
            owner_token=OWNER,
        )

    repaired_root = tmp_path / "already-repaired-frontier"
    _stage_failed_generation_zero(repaired_root)
    transition = _repair_transition(repaired_root)
    permit = _repair_permit(repaired_root, transition)
    AtomicEmpiricalFrontier.apply_source_repair(
        repaired_root,
        _bindings(),
        _repaired_bindings(),
        repair_transition=transition,
        permit=permit,
        now=NOW,
        lease_document_sha256="b" * 64,
        owner_token=OWNER,
    )
    with pytest.raises(EmpiricalArtifactError, match="duplicate"):
        AtomicEmpiricalFrontier.apply_source_repair(
            repaired_root,
            _bindings(),
            _repaired_bindings(),
            repair_transition=transition,
            permit=permit,
            now=NOW,
            lease_document_sha256="b" * 64,
            owner_token=OWNER,
        )


def test_source_repair_rejects_ambiguous_staging_and_binding_drift(tmp_path: Path) -> None:
    ambiguous_root = tmp_path / "ambiguous-source-repair-frontier"
    _stage_failed_generation_zero(ambiguous_root)
    staging_parent = ambiguous_root / "blocks" / "block_00" / ".staging"
    (staging_parent / ("generation_000000-" + "a" * 32)).mkdir()
    transition = _repair_transition(ambiguous_root)
    with pytest.raises(EmpiricalArtifactError, match="multiplicity"):
        AtomicEmpiricalFrontier.apply_source_repair(
            ambiguous_root,
            _bindings(),
            _repaired_bindings(),
            repair_transition=transition,
            permit=_repair_permit(ambiguous_root, transition),
            now=NOW,
            lease_document_sha256="b" * 64,
            owner_token=OWNER,
        )

    drift_root = tmp_path / "binding-drift-source-repair-frontier"
    _stage_failed_generation_zero(drift_root)
    transition = _repair_transition(drift_root)
    with pytest.raises(EmpiricalArtifactError, match="protected binding"):
        AtomicEmpiricalFrontier.apply_source_repair(
            drift_root,
            _bindings(),
            replace(_repaired_bindings(), coordinate_digest="a" * 64),
            repair_transition=transition,
            permit=_repair_permit(drift_root, transition),
            now=NOW,
            lease_document_sha256="b" * 64,
            owner_token=OWNER,
        )


@pytest.mark.parametrize("drift", ["config", "native", "counts", "path"])
def test_source_repair_rejects_transition_preservation_drift(
    tmp_path: Path, drift: str
) -> None:
    root = tmp_path / f"transition-{drift}-drift"
    _stage_failed_generation_zero(root)
    transition = _repair_transition(root)
    preserved = transition["preserved"]
    assert isinstance(preserved, dict)
    if drift == "config":
        preserved["config_sha256"] = "a" * 64
    elif drift == "native":
        preserved["native_identity_sha256"] = "a" * 64
    elif drift == "counts":
        counts = dict(CONTRACT_PANEL_COUNTS)
        counts["run_blocks"] = 19
        preserved["counts"] = counts
    else:
        preserved["result_root"] = str(root.parent / "drifted-results")
    body = {key: value for key, value in transition.items() if key != "repair_transition_sha256"}
    transition["repair_transition_sha256"] = hashlib.sha256(_canonical(body)).hexdigest()

    with pytest.raises(EmpiricalArtifactError, match="protected evidence|path binding"):
        AtomicEmpiricalFrontier.apply_source_repair(
            root,
            _bindings(),
            _repaired_bindings(),
            repair_transition=transition,
            permit=_repair_permit(root, transition),
            now=NOW,
            lease_document_sha256="b" * 64,
            owner_token=OWNER,
        )


def test_source_repair_audit_tampering_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "tampered-source-repair-frontier"
    _stage_failed_generation_zero(root)
    transition = _repair_transition(root)
    permit = _repair_permit(root, transition)
    AtomicEmpiricalFrontier.apply_source_repair(
        root,
        _bindings(),
        _repaired_bindings(),
        repair_transition=transition,
        permit=permit,
        now=NOW,
        lease_document_sha256="b" * 64,
        owner_token=OWNER,
    )
    audit_path = root / "stage_repairs" / "repair_000001.json"
    audit = json.loads(audit_path.read_text("ascii"))
    audit["analyzer_sha256"] = "a" * 64
    audit_path.write_bytes(_canonical(audit))

    with pytest.raises(EmpiricalArtifactError, match="stage repair audit binding"):
        _resume(
            root,
            bindings=_repaired_bindings(),
            permit=permit,
            lease_document_sha256="b" * 64,
        )


def test_resume_chain_is_monotonic_digest_bound_and_parent_owned(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    refs = _refs(root, 0)
    first = _state(refs, phase="TRAINING", updates=1, learned=0, scripted=0)
    first_digest = frontier.commit_resume(0, first, owner_token=OWNER)
    assert len(first_digest) == 64

    second = _state(refs, phase="TRAINING", updates=2, learned=0, scripted=0)
    second_digest = frontier.commit_resume(0, second, owner_token=OWNER)
    assert second_digest != first_digest
    _resume(root)

    with pytest.raises(EmpiricalArtifactError, match="parent owner"):
        frontier.commit_resume(1, _complete_state(root, 1), owner_token="synthetic-other-parent")
    with pytest.raises(EmpiricalArtifactError, match="regressed"):
        frontier.commit_resume(0, first, owner_token=OWNER)

    generation = root / "blocks" / "block_00" / "resume" / "generation_000000.json"
    generation.write_bytes(generation.read_bytes() + b" ")
    with pytest.raises(EmpiricalArtifactError, match="canonical"):
        _resume(root)


def test_incomplete_or_schema_mismatched_block_cannot_be_sealed(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    refs = _refs(root, 0)
    partial = _state(refs, phase="TRAINING", updates=1, learned=0, scripted=0)
    frontier.commit_resume(0, partial, owner_token=OWNER)
    with pytest.raises(EmpiricalArtifactError, match="not the exact complete"):
        frontier.seal_block(0, owner_token=OWNER)

    wrong_counts = replace(
        _complete_state(root, 1),
        counts={**BLOCK_COUNTS, "agent_ticks": BLOCK_COUNTS["agent_ticks"] - 1},
    )
    with pytest.raises(EmpiricalArtifactError, match="exact complete"):
        frontier.commit_resume(1, wrong_counts, owner_token=OWNER)


def test_extra_unbound_or_corrupt_component_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    state = _complete_state(root, 0)
    frontier.commit_resume(0, state, owner_token=OWNER)
    extra = root / "blocks" / "block_00" / "data" / "unbound.bin"
    extra.write_bytes(b"fixed-synthetic-extra")
    with pytest.raises(
        EmpiricalArtifactError,
        match="unbound, or extra|lacks exact owner-bound staging provenance",
    ):
        _resume(root)
    extra.unlink()

    target = root / next(iter(state.model_state.values())).path
    target.write_bytes(b"fixed-synthetic-corruption")
    with pytest.raises(EmpiricalArtifactError, match="size or digest"):
        _resume(root)


def test_staged_payload_crash_is_recovered_without_replacing_coordinate(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)

    def crash_after_stage(phase: str) -> None:
        assert phase == "after_payload_staging"
        raise RuntimeError("injected process loss after durable staging")

    with pytest.raises(RuntimeError, match="injected process loss"):
        frontier.stage_generation_payloads(
            0,
            _staging_payloads(),
            owner_token=OWNER,
            failure_hook=crash_after_stage,
        )
    assert (root / "blocks" / "block_00" / ".staging").exists()
    recovered = _resume(root)
    assert not (root / "blocks" / "block_00").exists()
    assert recovered.bindings.coordinate_digest == "4" * 64
    assert recovered.bindings.master_digest == "5" * 64

    staged = recovered.stage_generation_payloads(0, _staging_payloads(), owner_token=OWNER)
    state = _state(
        _refs_from_staged(staged), phase="TRAINING", updates=1, learned=0, scripted=0
    )
    recovered.commit_staged_resume(staged, state, owner_token=OWNER)
    _resume(root)


def test_partial_payload_publication_is_cleaned_but_committed_generation_is_preserved(
    tmp_path: Path,
) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    staged = frontier.stage_generation_payloads(0, _staging_payloads(), owner_token=OWNER)
    state = _state(
        _refs_from_staged(staged), phase="TRAINING", updates=1, learned=0, scripted=0
    )

    def crash_after_publication(phase: str) -> None:
        if phase == "after_payload_publication":
            raise RuntimeError("injected process loss after payload publication")

    with pytest.raises(RuntimeError, match="after payload publication"):
        frontier.commit_staged_resume(
            staged,
            state,
            owner_token=OWNER,
            failure_hook=crash_after_publication,
        )
    assert any((root / "blocks" / "block_00" / "data").iterdir())
    recovered = _resume(root)
    assert not (root / "blocks" / "block_00").exists()

    staged = recovered.stage_generation_payloads(0, _staging_payloads(), owner_token=OWNER)
    state = _state(
        _refs_from_staged(staged), phase="TRAINING", updates=1, learned=0, scripted=0
    )

    def crash_after_generation(phase: str) -> None:
        if phase == "after_generation_commit":
            raise RuntimeError("injected process loss after generation commit")

    with pytest.raises(RuntimeError, match="after generation commit"):
        recovered.commit_staged_resume(
            staged,
            state,
            owner_token=OWNER,
            failure_hook=crash_after_generation,
        )
    committed = root / "blocks" / "block_00" / "resume" / "generation_000000.json"
    assert committed.is_file()
    restored = _resume(root)
    assert committed.is_file()
    assert not (root / "blocks" / "block_00" / ".staging").exists()
    restored.validate()


def test_stale_owner_lock_recovery_rejects_live_foreign_or_ambiguous_locks(
    tmp_path: Path,
) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    lock = root / "PARENT_COMMIT.lock"

    def lock_payload(*, owner_sha: str, binding_sha: str, process_id: int) -> bytes:
        return _canonical(
            {
                "schema": LOCK_SCHEMA,
                "parent_owner_sha256": owner_sha,
                "frontier_bindings_sha256": binding_sha,
                "process_id": process_id,
                "process_nonce": "c" * 64,
            }
        )

    owner_sha = hashlib.sha256(OWNER.encode("ascii")).hexdigest()
    lock.write_bytes(
        lock_payload(owner_sha=owner_sha, binding_sha=frontier.bindings_sha256, process_id=424242)
    )
    resumed = _resume(root, process_alive_probe=lambda process_id: False)
    assert resumed.bindings == frontier.bindings
    assert not lock.exists()

    lock.write_bytes(
        lock_payload(owner_sha=owner_sha, binding_sha=frontier.bindings_sha256, process_id=os.getpid())
    )
    with pytest.raises(EmpiricalArtifactError, match="live or ambiguous"):
        _resume(root, process_alive_probe=lambda process_id: True)
    assert lock.exists()
    lock.unlink()

    lock.write_bytes(
        lock_payload(owner_sha="d" * 64, binding_sha=frontier.bindings_sha256, process_id=424242)
    )
    with pytest.raises(EmpiricalArtifactError, match="foreign or ambiguous"):
        _resume(root, process_alive_probe=lambda process_id: False)
    assert lock.exists()
    lock.unlink()

    lock.write_bytes(b"not-canonical-lock")
    with pytest.raises(EmpiricalArtifactError, match="malformed JSON"):
        _resume(root, process_alive_probe=lambda process_id: False)
    assert lock.exists()


def test_foreign_staging_provenance_is_rejected_and_preserved(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    staged = frontier.stage_generation_payloads(0, _staging_payloads(), owner_token=OWNER)
    staging_root = (
        root
        / "blocks"
        / "block_00"
        / ".staging"
        / f"generation_{staged.generation:06d}-{staged.token}"
    )
    manifest_path = staging_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="ascii"))
    manifest["parent_owner_sha256"] = "d" * 64
    manifest_path.write_bytes(_canonical(manifest))
    with pytest.raises(EmpiricalArtifactError, match="staging provenance differs"):
        _resume(root)
    assert manifest_path.exists()
    assert any((staging_root / "payloads").iterdir())


def test_analyzer_and_result_are_withheld_until_all_twenty_blocks(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    _complete_block(frontier, 0)
    analyzer, result = _publication_payloads()
    with pytest.raises(EmpiricalArtifactError, match="twenty"):
        frontier.publish_complete_panel(
            branch="TARGET_UNRESOLVED",
            analyzer_payload=analyzer,
            result_payload=result,
            owner_token=OWNER,
        )
    assert not (root / "published").exists()

    for index in range(1, BLOCK_COUNT):
        _complete_block(frontier, index)
    published = frontier.publish_complete_panel(
        branch="TARGET_UNRESOLVED",
        analyzer_payload=analyzer,
        result_payload=result,
        owner_token=OWNER,
    )
    assert published == root / "published"
    restored = _resume(root)
    panel = restored.restore_complete_panel()
    assert panel.branch == "TARGET_UNRESOLVED"
    assert panel.analyzer_payload == analyzer
    assert panel.result_payload == result
    assert panel.manifest["registered_tail_names"] == list(REGISTERED_TAIL_NAMES)


def test_published_digest_and_any_top_level_extra_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "synthetic-frontier"
    frontier = _create(root)
    for index in range(BLOCK_COUNT):
        _complete_block(frontier, index)
    analyzer, result = _publication_payloads()
    frontier.publish_complete_panel(
        branch="TARGET_UNRESOLVED",
        analyzer_payload=analyzer,
        result_payload=result,
        owner_token=OWNER,
    )
    (root / "published" / "analyzer.json").write_bytes(b"changed-synthetic-fixture")
    with pytest.raises(EmpiricalArtifactError, match="published panel binding"):
        _resume(root)

    (root / "published" / "analyzer.json").write_bytes(analyzer)
    (root / "unexpected.bin").write_bytes(hashlib.sha256(b"fixed").digest())
    with pytest.raises(EmpiricalArtifactError, match="unexpected"):
        _resume(root)
