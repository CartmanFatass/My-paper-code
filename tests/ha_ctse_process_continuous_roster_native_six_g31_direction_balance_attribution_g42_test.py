from __future__ import annotations

import copy
import hashlib
import io
import json
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest
import torch
from torch import nn

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_direction_balance_attribution_g42 as g42,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)


ACCEPTED_ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)
ACCEPTED_ANCHOR_FIXTURE_BYTES = 81_017
ACCEPTED_ANCHOR_FIXTURE_SHA256 = (
    "d6920e8ab958b776ee0b25a5d2a1b120528b69abc87d4eacc2a6deee2351b521"
)


def _optimizer_state(
    optimizer: torch.optim.Optimizer,
    parameters: Sequence[nn.Parameter] | None = None,
) -> tuple[tuple[tuple[str, Any], ...], ...]:
    selected = (
        tuple(parameters)
        if parameters is not None
        else tuple(
            parameter
            for group in optimizer.param_groups
            for parameter in group["params"]
        )
    )
    rows: list[tuple[tuple[str, Any], ...]] = []
    for parameter in selected:
        state = optimizer.state.get(parameter, {})
        rows.append(
            tuple(
                (
                    name,
                    value.detach().clone()
                    if isinstance(value, torch.Tensor)
                    else value,
                )
                for name, value in sorted(state.items())
            )
        )
    return tuple(rows)


def _assert_optimizer_state_equal(
    left: torch.optim.Optimizer,
    right: torch.optim.Optimizer,
    left_parameters: Sequence[nn.Parameter] | None = None,
    right_parameters: Sequence[nn.Parameter] | None = None,
) -> None:
    left_rows = _optimizer_state(left, left_parameters)
    right_rows = _optimizer_state(right, right_parameters)
    assert len(left_rows) == len(right_rows)
    for left_state, right_state in zip(left_rows, right_rows):
        assert tuple(name for name, _ in left_state) == tuple(
            name for name, _ in right_state
        )
        for (_, left_value), (_, right_value) in zip(left_state, right_state):
            if isinstance(left_value, torch.Tensor):
                assert isinstance(right_value, torch.Tensor)
                assert torch.equal(left_value, right_value)
            else:
                assert left_value == right_value


@pytest.fixture(scope="module")
def accepted_anchor_batch() -> Iterator[
    tuple[g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory]
]:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        fixture_bytes = ACCEPTED_ANCHOR_FIXTURE.read_bytes()
        assert len(fixture_bytes) == ACCEPTED_ANCHOR_FIXTURE_BYTES
        assert hashlib.sha256(fixture_bytes).hexdigest() == (
            ACCEPTED_ANCHOR_FIXTURE_SHA256
        )
        payload = torch.load(
            io.BytesIO(fixture_bytes), map_location="cpu", weights_only=False
        )
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            payload, accepted_anchor_replicate=0
        )
        trajectory = g40.collect_g40_trajectory(
            anchor,
            episode_ids=range(8),
            ledger_seed=10_404_000,
            action_seed=10_405_000,
            device=torch.device("cpu"),
        )
        assert trajectory.rewards.numel() == 384
        yield anchor, trajectory
    finally:
        torch.set_num_threads(prior_threads)


@pytest.fixture(scope="module")
def accepted_g42_update(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> dict[str, object]:
    anchor, trajectory = accepted_anchor_batch
    models = g42.project_g42_arms(anchor, accepted_anchor_replicate=0)
    _, reference = g41.project_post_anchor_paths(
        anchor, accepted_anchor_replicate=0
    )
    for model in (*models.values(), reference):
        model.begin_credit_branch_phase()
    initial_baseline_state = g40.state_bytes(models[g42.DB_ARM].credit_baselines)
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    reference_optimizer = g41.make_actor_head_optimizer(reference)
    boundary = g42.branch_boundary_audit(models, optimizers)
    assert boundary["passed"] is True, boundary
    rng_before = torch.random.get_rng_state().clone()
    update_record = g42.optimize_matched_direction_attribution_update(
        models, optimizers, trajectory, ppo_passes=2
    )
    reference_record = g41.optimize_retained_actor_head_update(
        reference, reference_optimizer, trajectory, ppo_passes=2
    )
    assert torch.equal(rng_before, torch.random.get_rng_state())
    return {
        "models": models,
        "optimizers": optimizers,
        "reference": reference,
        "reference_optimizer": reference_optimizer,
        "reference_record": reference_record,
        "initial_baseline_state": initial_baseline_state,
        "update_record": update_record,
    }


def test_projection_is_exact_accepted_g41_no_slow_with_manifest_anchor(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = accepted_anchor_batch
    models = g42.project_g42_arms(anchor, accepted_anchor_replicate=0)
    _, accepted_g41_no_slow = g41.project_post_anchor_paths(
        anchor, accepted_anchor_replicate=0
    )
    assert g42.ACCEPTED_G41_SOURCE_COMMIT == (
        "a5f63c349228fc2bba7843647e0ae4c34361c1c9"
    )
    assert g42.ACCEPTED_G40_ANCHOR_REPLICATES == (0, 1, 2)
    for model in models.values():
        assert g40.state_bytes(model) == g40.state_bytes(accepted_g41_no_slow)
        assert not hasattr(model, "slow_critic")
        assert model.phase == "fast"
        assert model.accepted_g40_anchor_authority == (
            g41.accepted_g40_anchor_authority(0)
        )
    assert g40.shared_tensor_storage_count(tuple(models.values())) == 0
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    boundary = g42.branch_boundary_audit(models, optimizers)
    assert boundary["accepted_g41_source_commit"] == (
        g42.ACCEPTED_G41_SOURCE_COMMIT
    )
    assert boundary["authority_valid"] is True
    assert boundary["model_state_bytes_equal"] is True
    assert boundary["parameter_name_shape_trainable_contract_equal"] is True
    assert boundary["standalone_slow_absent"] is True
    assert boundary["shared_tensor_storage_count"] == 0
    assert boundary["optimizer_parameter_order_equal"] is True
    assert boundary["optimizer_states_empty_and_separate"] is True
    assert boundary["passed"] is True, boundary


def test_db_arm_is_bitwise_accepted_g41_and_null_is_scale_matched_raw_sum(
    accepted_g42_update: dict[str, object],
) -> None:
    models = accepted_g42_update["models"]
    optimizers = accepted_g42_update["optimizers"]
    assert isinstance(models, dict)
    assert isinstance(optimizers, dict)
    db_model = models[g42.DB_ARM]
    no_db_model = models[g42.NO_DB_ARM]
    db_optimizer = optimizers[g42.DB_ARM]
    reference = accepted_g42_update["reference"]
    reference_optimizer = accepted_g42_update["reference_optimizer"]
    assert g40.state_bytes(db_model) == g40.state_bytes(reference)
    _assert_optimizer_state_equal(db_optimizer, reference_optimizer)
    assert accepted_g42_update["reference_record"][
        "actor_head_optimizer_steps"
    ] == 2

    parameter = nn.Parameter(torch.zeros(2, dtype=torch.float64))
    composition = g42.compose_scale_matched_raw_sum_gradients(
        (torch.tensor([3.0, 0.0], dtype=torch.float64),),
        (torch.tensor([0.0, 4.0], dtype=torch.float64),),
        (parameter,),
        registered_gradient_norm=2.0,
    )
    assert composition.immediate_norm == 3.0
    assert composition.successor_norm == 4.0
    assert composition.raw_sum_norm == 5.0
    assert composition.scale_factor == 0.4
    assert torch.allclose(
        composition.gradients[0],
        torch.tensor([1.2, 1.6], dtype=torch.float64),
        rtol=0.0,
        atol=1e-15,
    )
    assert composition.applied_gradient_norm == pytest.approx(2.0)
    dependency = g42.raw_sum_null_dependency_audit()
    assert dependency["input_signature"] == (
        "immediate",
        "successor",
        "parameters",
        "registered_gradient_norm",
    )
    assert dependency["forbidden_db_direction_reads"] == ()
    assert dependency["registered_scalar_norm_only"] is True
    assert dependency["passed"] is True, dependency
    assert g40.state_bytes(db_model.credit_baselines) == g40.state_bytes(
        no_db_model.credit_baselines
    )


def test_zero_cancellation_and_non_scale_match_fail_before_adam_step() -> None:
    parameter = nn.Parameter(torch.zeros(1, dtype=torch.float64))
    optimizer = torch.optim.Adam((parameter,), lr=1e-3)
    failures = (
        ((torch.zeros(1),), (torch.ones(1),), 1.0, "immediate_gradient"),
        ((torch.ones(1),), (torch.zeros(1),), 1.0, "successor_gradient"),
        ((torch.ones(1),), (-torch.ones(1),), 1.0, "raw_sum_cancellation"),
        ((torch.ones(1),), (torch.ones(1),), 0.0, "registered_gradient"),
    )
    for immediate, successor, registered_norm, reason in failures:
        with pytest.raises(g42.G42GradientGateError) as caught:
            g42.compose_scale_matched_raw_sum_gradients(
                immediate,
                successor,
                (parameter,),
                registered_gradient_norm=registered_norm,
            )
        record = caught.value.to_record()
        assert reason in record["reason"]
        assert record["stage"] == "before_optimizer_step"
        assert record["channel_fallback_used"] is False
        assert record["sum_perturbed"] is False
        assert optimizer.state == {}
    with pytest.raises(
        g42.G42GradientGateError, match="non_scale_match"
    ) as caught:
        g42.validate_scale_match(
            registered_gradient_norm=1.0, applied_gradient_norm=0.5
        )
    assert caught.value.to_record()["stage"] == "before_optimizer_step"
    assert optimizer.state == {}


def test_paired_source_rng_optimizer_baselines_diagnostics_and_checkpoints(
    accepted_g42_update: dict[str, object],
) -> None:
    models = accepted_g42_update["models"]
    optimizers = accepted_g42_update["optimizers"]
    record = accepted_g42_update["update_record"]
    assert isinstance(models, dict)
    assert isinstance(optimizers, dict)
    assert isinstance(record, dict)
    assert record["passed"] is True, record
    assert record["first_paired_replay_equal"] is True
    assert record["advantage_normalization_count"] == 2
    assert record["advantage_recomputed_between_passes"] is False
    assert record["actor_head_optimizer_steps"] == {
        g42.DB_ARM: 2.0,
        g42.NO_DB_ARM: 2.0,
    }
    assert record["baseline_state_bytes_equal"] is True
    assert record["baseline_optimizer_state_equal"] is True
    assert record["paired_source_trace_passed"] is True
    assert record["torch_rng_unchanged"] is True
    assert record["real_transitions"] == 384
    assert record["K_search"] == 0
    assert record["hypothetical_transitions"] == 0
    assert tuple(
        row["replicate"] for row in record["accepted_g40_anchor_registry"]
    ) == (0, 1, 2)
    for pass_index, pass_record in enumerate(record["pass_records"]):
        assert pass_record["pass_index"] == pass_index
        null_record = pass_record["no_db_composition"]
        assert null_record["mode"] == "scale_matched_raw_sum"
        assert null_record["db_direction_input_present"] is False
        assert null_record["channel_fallback_used"] is False
        assert null_record["sum_perturbed"] is False
        assert null_record["scale_match_error"] <= null_record[
            "scale_match_tolerance"
        ]
        assert null_record["registered_gradient_norm"] == (
            pass_record["db_registered_gradient_norm"]
        )
    assert json.loads(g42.serialize_diagnostics(record))["passed"] is True

    db_model = models[g42.DB_ARM]
    no_db_model = models[g42.NO_DB_ARM]
    assert g40.state_bytes(db_model.credit_baselines) != (
        accepted_g42_update["initial_baseline_state"]
    )
    assert g40.state_bytes(db_model.credit_baselines) == g40.state_bytes(
        no_db_model.credit_baselines
    )
    _assert_optimizer_state_equal(
        optimizers[g42.DB_ARM],
        optimizers[g42.NO_DB_ARM],
        tuple(db_model.credit_baselines.parameters()),
        tuple(no_db_model.credit_baselines.parameters()),
    )
    checkpoints = {
        arm: g42.build_final_checkpoint(arm, models[arm], record)
        for arm in g42.ARMS
    }
    for arm, checkpoint in checkpoints.items():
        assert checkpoint["arm"] == arm
        assert checkpoint["checkpoint_kind"] == (
            "FINAL_ONLY_NO_SLOW_DIRECTION_ATTRIBUTION"
        )
        assert checkpoint["standalone_slow_present"] is False
        assert checkpoint["accepted_g40_anchor_authority"] == (
            g41.accepted_g40_anchor_identity(0)
        )
        assert checkpoint["model_state_digest"] == g41._state_digest(
            checkpoint["model_state"]
        )
        assert not any(
            "slow_critic" in name for name in checkpoint["model_state"]
        )
        assert checkpoint["diagnostics"] == {
            "passed": True,
            "real_transitions": 384,
            "K_search": 0,
            "hypothetical_transitions": 0,
        }
    assert checkpoints[g42.DB_ARM]["direction_mode"] == (
        "registered_g31_direction_balanced"
    )
    assert checkpoints[g42.NO_DB_ARM]["direction_mode"] == (
        "scale_matched_raw_sum_no_db"
    )
