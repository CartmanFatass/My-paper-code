from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_activity_contract import (
    prospective_counts,
    prospective_roster,
    update_allocation,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_lifecycle import (
    FoundationLifecycle,
    LifecycleError,
    cold_resume,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_runner import (
    ActivityBlocked,
    FoundationPreactivityRunner,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.foundation_evidence import (
    EXACT_TEST_COMMAND,
    EvidenceError,
    accepted_technical_slot_fixture,
    build_checkpoint_manifest,
    build_evidence_manifest,
    build_s2_acceptance,
    build_source_manifest,
    canonical_json_bytes,
    require_all_technical_acceptance,
)
from experiments.candidates.scdmp_variable_k.native_fusion_r01.barriers import StageBarrier


ROOT = Path(__file__).resolve().parents[4]


def test_prospective_roster_and_update_allocation_are_exact_counts_only() -> None:
    roster = prospective_roster()
    first_update = update_allocation(1)
    last_update = update_allocation(192)
    counts = prospective_counts()

    assert tuple(item.replicate_index for item in roster) == tuple(range(24))
    assert all(item.registered is False for item in roster)
    assert all(item.activity_authorized is False for item in roster)
    assert all(item.identity_materialized is False for item in roster)
    assert len(first_update.slots) == len(last_update.slots) == 16
    assert Counter((slot.k, slot.order) for slot in first_update.slots) == {
        (4, "RG"): 4,
        (4, "GR"): 4,
        (10, "RG"): 4,
        (10, "GR"): 4,
    }
    assert counts.replicates == 24
    assert counts.updates_per_foundation == 192
    assert counts.episodes_per_update == 16
    assert counts.structural_steps_per_update == 16
    assert counts.episodes_per_foundation == 3_072
    assert counts.steps_per_foundation == 3_072
    assert counts.total_foundation_episodes == 73_728
    assert counts.total_foundation_steps == 73_728


def test_atomic_lifecycle_and_cold_resume_never_repeat_persistent_index() -> None:
    lifecycle = FoundationLifecycle.initial(0, technical_state_sha256="0" * 64)
    first = lifecycle.begin_update(observed_old_state_sha256="0" * 64)

    assert (first.update_index, first.step_start, first.step_end) == (1, 1, 16)
    with pytest.raises(LifecycleError, match="immutable old-state"):
        lifecycle.accept_update(
            first,
            observed_old_state_sha256="f" * 64,
            technical_state_sha256="1" * 64,
        )
    lifecycle = lifecycle.accept_update(
        first,
        observed_old_state_sha256="0" * 64,
        technical_state_sha256="1" * 64,
    )
    resumed = cold_resume(lifecycle.snapshot())
    second = resumed.begin_update(observed_old_state_sha256="1" * 64)
    assert (second.update_index, second.step_start, second.step_end) == (2, 17, 32)
    with pytest.raises(LifecycleError, match="next atomic update"):
        resumed.accept_update(
            first,
            observed_old_state_sha256="1" * 64,
            technical_state_sha256="2" * 64,
        )

    lifecycle = resumed
    for update_index in range(2, 193):
        old_sha = lifecycle.technical_state_sha256
        transition = lifecycle.begin_update(observed_old_state_sha256=old_sha)
        lifecycle = lifecycle.accept_update(
            transition,
            observed_old_state_sha256=old_sha,
            technical_state_sha256=f"{update_index:064x}",
        )
    slot = lifecycle.technical_slot()
    assert lifecycle.completed_updates == 192
    assert lifecycle.persistent_step_index == 3_072
    assert slot.materialized is False
    assert slot.eligible is False
    assert slot.technically_accepted is False


def test_runner_exposes_counts_only_and_blocks_every_activity_path() -> None:
    runner = FoundationPreactivityRunner()
    inspection = runner.inspect()

    assert inspection.roster_count == 24
    assert inspection.updates_per_foundation == 192
    assert inspection.total_foundation_episodes == 73_728
    assert inspection.registered_identity_present is False
    assert inspection.activity_authorized is False
    assert inspection.effect_refs == ()
    with pytest.raises(ActivityBlocked, match="registered identity"):
        runner.attempt_activity(
            command=(),
            registered_identity_present=True,
            activity_authorized=False,
            immutable_run_manifest_ref=None,
        )
    with pytest.raises(ActivityBlocked, match="activity flag"):
        runner.attempt_activity(
            command=(),
            registered_identity_present=False,
            activity_authorized=True,
            immutable_run_manifest_ref=None,
        )
    with pytest.raises(ActivityBlocked, match="immutable run manifest"):
        runner.attempt_activity(
            command=("python", "forbidden.py"),
            registered_identity_present=False,
            activity_authorized=False,
            immutable_run_manifest_ref=None,
        )
    with pytest.raises(ActivityBlocked, match="S2 cannot accept"):
        runner.attempt_activity(
            command=("python", "forbidden.py"),
            registered_identity_present=False,
            activity_authorized=False,
            immutable_run_manifest_ref={"path": "fake.json", "sha256": "a" * 64},
        )


def test_complete_manifests_require_all_24_slots_and_hard_downstream_absence() -> None:
    source = build_source_manifest(ROOT)
    slots = tuple(
        accepted_technical_slot_fixture(index, technical_state_sha256=f"{index + 1:064x}")
        for index in range(24)
    )
    checkpoints = build_checkpoint_manifest(slots)
    barrier = require_all_technical_acceptance(checkpoints)
    evidence = build_evidence_manifest(
        source_manifest=source,
        checkpoint_manifest=checkpoints,
        observed_artifact_paths=(),
    )

    assert len(source["files"]) == 5
    assert len(checkpoints["slots"]) == 24
    assert checkpoints["complete"] is True
    assert checkpoints["eligible_artifact_present"] is False
    assert barrier.all_24_technically_accepted is True
    assert barrier.competence_open is False
    assert barrier.opportunity_open is False
    assert barrier.activity_authorized is False
    assert evidence["complete"] is True
    assert evidence["observed_artifact_paths"] == []
    assert evidence["hard_downstream_absence"] is True
    with pytest.raises(EvidenceError, match="all 24"):
        build_checkpoint_manifest(slots[:-1])
    with pytest.raises(EvidenceError, match="downstream artifact"):
        build_evidence_manifest(
            source_manifest=source,
            checkpoint_manifest=checkpoints,
            observed_artifact_paths=("adapter.bin",),
        )


def test_s2_acceptance_binds_manifests_measurements_and_closed_firewall() -> None:
    source = build_source_manifest(ROOT)
    checkpoints = build_checkpoint_manifest(
        tuple(
            accepted_technical_slot_fixture(index, technical_state_sha256=f"{index + 1:064x}")
            for index in range(24)
        )
    )
    evidence = build_evidence_manifest(
        source_manifest=source,
        checkpoint_manifest=checkpoints,
        observed_artifact_paths=(),
    )
    acceptance = build_s2_acceptance(
        repository_root=ROOT,
        source_manifest=source,
        checkpoint_manifest=checkpoints,
        evidence_manifest=evidence,
        measurements={
            "cpu_seconds": 1.0,
            "wall_seconds": 2.0,
            "peak_working_set_bytes": 3,
            "peak_tracemalloc_bytes": 4,
            "read_bytes": 5,
            "write_bytes": 6,
        },
        verification_sha256="b" * 64,
    )

    StageBarrier.s0().validate_payload(acceptance)
    assert acceptance["verification_command"] == EXACT_TEST_COMMAND
    assert len(acceptance["manifest_refs"]) == 3
    assert acceptance["firewall"] == {
        "registered_identity_present": False,
        "eligible_artifact_present": False,
        "question_relevant_value_visible": False,
        "activity_authorized": False,
        "effect_refs": [],
    }
    assert acceptance["effect_refs"] == []
    assert acceptance["activity_authorized"] is False
    assert canonical_json_bytes(acceptance).endswith(b"\n")
