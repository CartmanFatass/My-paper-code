from __future__ import annotations

import copy
import pickle
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49
    as g49,
)
from scripts import (
    run_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48
    as g48_runner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANCHOR_ROOT = PROJECT_ROOT / (
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)


@pytest.fixture(scope="module")
def accepted_shared_batch() -> Iterator[
    tuple[
        g49.g40.G40NativeSixPolicy,
        g49.AnchoredRosterTrajectory,
    ]
]:
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        anchor = g48_runner._load_accepted_anchor(ANCHOR_ROOT, 0)
        predecessor = g49.project_g49_arms(
            anchor, accepted_anchor_replicate=0
        )[g49.REFERENCE_ARM]
        predecessor.begin_credit_branch_phase()
        seeds = g48_runner.seed_block(0, formal=False)
        trajectory = g48_runner._collect_trajectory(
            predecessor,
            episode_ids=tuple(range(8)),
            ledger_seed=seeds["branch_ledger"],
            action_seed=seeds["branch_action"],
        )
        assert trajectory.rewards.numel() == 384
        yield anchor, trajectory
    finally:
        torch.set_num_threads(previous_threads)


def _project(
    anchor: g49.g40.G40NativeSixPolicy,
) -> tuple[
    dict[str, g49.G49Model],
    dict[str, torch.optim.Adam],
]:
    models = g49.project_g49_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    return models, g49.make_g49_optimizers(models)


def test_static_factorization_and_single_schema_have_zero_removed_residue(
    accepted_shared_batch: tuple[
        g49.g40.G40NativeSixPolicy, g49.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_shared_batch
    rng_before = torch.random.get_rng_state().clone()
    models, optimizers = _project(anchor)
    assert torch.equal(rng_before, torch.random.get_rng_state())

    certificate = g49.reconstruct_static_certificate(models, optimizers)
    assert g49.validate_static_certificate(certificate), certificate
    assert certificate["accepted_g48_formal_source_commit"] == (
        "4abbee66d43ffd592d65624121121bc0109882ab"
    )
    assert certificate["accepted_g48_formal_branch"] == (
        "DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48"
    )
    dependency = certificate["reduced_dependency_certificate"]
    assert dependency["forbidden_reduced_dependency_reads"] == []
    assert all(
        dependency[name] == 0
        for name in (
            "second_target_tensor_count",
            "second_normalization_instance_count",
            "second_channel_loss_count",
            "second_backward_gradient_construction_count",
            "equal_mean_duplicate_composition_count",
            "second_channel_diagnostic_field_count",
        )
    )

    target = g49._single_immediate_target(trajectory.rewards)
    normalization = g49._normalize_single(target)
    record = g49._single_normalization_record(normalization)
    assert g49.validate_single_normalization_record(record)
    assert g49.validate_reduced_schema({"target": record})
    contaminated = {"target": record, "channel_2_gradient": "placeholder"}
    assert not g49.validate_reduced_schema(contaminated)
    hidden_value_residue = {
        "legacy": {
            "route": "accepted_G48_duplicated_immediate",
            "channels": ["immediate_1", "immediate_2"],
        }
    }
    assert not g49.validate_reduced_schema(hidden_value_residue)


def test_actual_two_loss_to_one_loss_bytes_match_through_both_adam_passes(
    accepted_shared_batch: tuple[
        g49.g40.G40NativeSixPolicy, g49.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_shared_batch
    models, optimizers = _project(anchor)
    record = g49.optimize_duplicated_immediate_single_channel_update(
        models, optimizers, trajectory, update_index=0
    )
    assert g49.validate_update_evidence(record), record
    assert record["shared_real_trajectory_batches"] == 1
    assert record["real_transitions"] == 384
    assert record["PPO_passes"] == 2
    assert record["actor_optimizer_steps_per_arm"] == 2
    assert record["D_SC"] == 0.0
    assert record["order_swap_guard"]["diagnostic_optimizer_steps"] == 0
    for row in record["pass_records"]:
        assert row["plan_materialized_before_either_optimizer_step_for_pass"]
        assert all(row["floating_point_equivalence"].values())
        assert all(row["plan_effect_audit"].values())
        assert row["post_optimizer_equivalence"]["passed"] is True
        reduced = row["reduced_route"]
        assert g49.validate_reduced_schema(reduced)
        assert reduced["route"] == "single_immediate"
        assert set(reduced["target"]) == g49._SINGLE_NORMALIZATION_KEYS

    checkpoints = g49.build_final_checkpoints(models, optimizers, record)
    assert g49.validate_checkpoint_pair(checkpoints)
    assert g49._canonical_values_equal(
        g49.canonical_actor_projection(checkpoints[g49.REFERENCE_ARM]),
        g49.canonical_actor_projection(checkpoints[g49.REDUCED_ARM]),
    )
    assert g49.validate_reduced_schema(checkpoints[g49.REDUCED_ARM])

    serialized = pickle.dumps(checkpoints)
    reloaded = pickle.loads(serialized)
    assert g49.validate_checkpoint_pair(reloaded)


def test_tamper_guards_reject_removed_fields_and_projection_drift(
    accepted_shared_batch: tuple[
        g49.g40.G40NativeSixPolicy, g49.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_shared_batch
    models, optimizers = _project(anchor)
    record = g49.optimize_duplicated_immediate_single_channel_update(
        models, optimizers, trajectory, update_index=0
    )
    checkpoints = g49.build_final_checkpoints(models, optimizers, record)

    residue = copy.deepcopy(checkpoints)
    residue[g49.REDUCED_ARM]["route_schema"]["second_target"] = torch.zeros(1)
    assert not g49.validate_checkpoint_pair(residue)

    dummy = copy.deepcopy(checkpoints)
    dummy[g49.REDUCED_ARM]["dummy_compatibility_channel"] = 0
    assert not g49.validate_checkpoint_pair(dummy)

    hidden_checkpoint_residue = copy.deepcopy(checkpoints)
    hidden_checkpoint_residue[g49.REDUCED_ARM]["legacy"] = {
        "route": "accepted_G48_duplicated_immediate",
        "channels": ["immediate_1", "immediate_2"],
    }
    assert not g49.validate_checkpoint_pair(hidden_checkpoint_residue)

    drift = copy.deepcopy(checkpoints)
    projection = drift[g49.REDUCED_ARM]["canonical_projection"]
    first = next(iter(projection["actor_log_std_state"]))
    projection["actor_log_std_state"][first].view(-1)[0] += 1
    assert not g49.validate_checkpoint_pair(drift)

    forged = copy.deepcopy(record)
    forged["pass_records"][0]["floating_point_equivalence"][
        "actual_reference_average_equals_single_gradient_bytes"
    ] = False
    assert not g49.validate_update_evidence(forged)

    hidden_pass_residue = copy.deepcopy(record)
    hidden_pass_residue["pass_records"][0]["reduced_route"]["legacy"] = {
        "route": "accepted_G48_duplicated_immediate",
        "channels": ["immediate_1", "immediate_2"],
    }
    assert not g49.validate_update_evidence(hidden_pass_residue)

    nested_gradient_residue = copy.deepcopy(record)
    nested_gradient_residue["pass_records"][0]["reduced_route"][
        "gradient_evidence"
    ]["legacy"] = "single_immediate"
    assert not g49.validate_update_evidence(nested_gradient_residue)


def test_gate_exception_pickle_roundtrip_preserves_fail_closed_diagnostics() -> None:
    error = g49.G49InvariantError("single_gradient_mismatch", {"pass": 1})
    restored = pickle.loads(pickle.dumps(error))
    assert isinstance(restored, g49.G49InvariantError)
    assert restored.reason == error.reason
    assert restored.diagnostics == error.diagnostics
    assert str(restored) == str(error)
    assert restored.to_record() == error.to_record()
