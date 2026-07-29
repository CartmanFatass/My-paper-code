from __future__ import annotations

import copy
import hashlib
import io
import math
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_realized_successor_channel_attribution_g48
    as g48,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)


ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)
ANCHOR_SHA256 = "d6920e8ab958b776ee0b25a5d2a1b120528b69abc87d4eacc2a6deee2351b521"


class _SuccessorReadTrap:
    def __init__(self, trajectory: g40.AnchoredRosterTrajectory) -> None:
        self._trajectory = trajectory

    def __getattr__(self, name: str) -> object:
        if "successor" in name.lower() or name == "returns":
            raise AssertionError("null G48 path read a realized-successor accessor")
        return getattr(self._trajectory, name)


@pytest.fixture(scope="module")
def accepted_anchor_batch() -> Iterator[
    tuple[g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory]
]:
    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        payload = ANCHOR_FIXTURE.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == ANCHOR_SHA256
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            torch.load(io.BytesIO(payload), map_location="cpu", weights_only=False),
            accepted_anchor_replicate=0,
        )
        trajectory = g40.collect_g40_trajectory(
            anchor,
            episode_ids=range(8),
            ledger_seed=11_483_000,
            action_seed=11_483_000,
            device=torch.device("cpu"),
        )
        assert trajectory.rewards.shape == (48, 8)
        yield anchor, trajectory
    finally:
        torch.set_num_threads(previous_threads)


@pytest.fixture(scope="module")
def completed_update(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> tuple[dict[str, g48.G48Model], dict[str, object]]:
    anchor, trajectory = accepted_anchor_batch
    models = g48.project_g48_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = g48.make_g48_optimizers(models)
    record = g48.optimize_realized_successor_channel_update(
        models,
        optimizers,
        {arm: trajectory for arm in g48.ARMS},
        update_index=0,
    )
    return models, record


def test_projection_and_null_route_are_actor_only_and_successor_read_free(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    rng_before = torch.random.get_rng_state().clone()
    models = g48.project_g48_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = g48.make_g48_optimizers(models)

    assert torch.equal(rng_before, torch.random.get_rng_state())
    assert tuple(models) == g48.ARMS
    assert all(not hasattr(model, "credit_baselines") for model in models.values())
    assert all(
        not name.startswith("credit_baselines.")
        for model in models.values()
        for name in model.state_dict()
    )
    boundary = g48.branch_boundary_audit(models, optimizers)
    assert boundary["passed"] is True, boundary
    assert boundary["shared_parameter_buffer_storage_count"] == 0
    certificate = g48.reconstruct_static_certificate(models, optimizers)
    assert g48.validate_static_certificate(certificate), certificate
    assert all(
        certificate["null_zero_reads"][name] == 0
        for name in (
            "realized_successor_read_into_null_target",
            "realized_successor_read_into_null_normalization",
            "realized_successor_read_into_null_actor_loss",
            "realized_successor_read_into_null_gradient_scale",
            "realized_successor_read_into_null_checkpoint_selection",
            "realized_successor_read_into_null_evaluation",
            "realized_successor_read_into_null_result_selection",
            "successor_counterfactual_calls",
        )
    )
    assert certificate["null_zero_reads"][
        "null_builder_forbidden_bytecode_reads"
    ] == []

    null = g48.duplicated_immediate_channel_package(trajectory.rewards)
    assert null.target_route == "duplicated_immediate_reward_only"
    assert null.realized_successor_read_count == 0
    assert null.channel_1.data_ptr() != null.channel_2.data_ptr()
    assert torch.equal(null.channel_1, null.channel_2)
    assert g48.reference_channel_package(trajectory).realized_successor_read_count == 1
    packages, _, _ = g48._prepared_packages(
        {
            g48.REFERENCE_ARM: trajectory,
            g48.NULL_ARM: _SuccessorReadTrap(trajectory),  # type: ignore[dict-item]
        }
    )
    assert packages[g48.NULL_ARM].realized_successor_read_count == 0


def test_strict_activation_and_zero_nonfinite_cases() -> None:
    rows = g48.NORMALIZATION_ROWS
    immediate = torch.zeros(rows, dtype=torch.float64)
    at_threshold = torch.full(
        (rows,), g48.ACTIVATION_TOLERANCE, dtype=torch.float64
    )
    reference = (torch.ones(1, dtype=torch.float64),)
    null_zero = (torch.zeros(1, dtype=torch.float64),)
    exact = g48._activation_scalars(
        immediate, at_threshold, reference, null_zero
    )
    assert exact["q_target"] == g48.ACTIVATION_TOLERANCE
    assert exact["q_credit"] == 1.0
    assert exact["treatment_active"] is False

    above = g48._activation_scalars(
        immediate,
        torch.full(
            (rows,),
            math.nextafter(g48.ACTIVATION_TOLERANCE, math.inf),
            dtype=torch.float64,
        ),
        reference,
        null_zero,
    )
    assert above["q_target"] > g48.ACTIVATION_TOLERANCE
    assert above["treatment_active"] is True

    intermediate = g48._activation_scalars(
        immediate,
        torch.full((rows,), 1.0e-3, dtype=torch.float64),
        (torch.tensor([1.0005], dtype=torch.float64),),
        (torch.tensor([1.0], dtype=torch.float64),),
    )
    assert intermediate["q_target"] == 1.0e-3
    assert intermediate["q_credit"] == abs(1.0005 - 1.0) / 1.0005
    assert 1.0e-6 < intermediate["q_credit"] < 1.0e-3
    assert intermediate["treatment_active"] is True
    intermediate_record = {
        **intermediate,
        "evidence_source_arm": g48.REFERENCE_ARM,
        "reference_evidence_source": True,
        "reference_null_counterfactual": "0.5*(g_I+g_I)",
        "actual_null_evidence_read_count": 0,
        "activation_tolerance": g48.ACTIVATION_TOLERANCE,
        "direction_distance_conclusion_gate": False,
    }
    assert g48.validate_activation_record(intermediate_record)
    squared = copy.deepcopy(intermediate_record)
    squared["q_credit"] = squared["full_credit_vector_difference_sum_square"] / max(
        squared["reference_credit_norm_square"],
        squared["null_counterfactual_credit_norm_square"],
    )
    squared["treatment_active"] = False
    assert not g48.validate_activation_record(squared)

    both_zero = g48._activation_scalars(
        immediate,
        immediate,
        (torch.zeros(1, dtype=torch.float64),),
        (torch.zeros(1, dtype=torch.float64),),
    )
    assert both_zero["q_credit"] == 0.0
    assert both_zero["treatment_active"] is False
    with pytest.raises(g48.G48InvariantError, match="activation_credit_nonfinite"):
        g48._activation_scalars(
            immediate,
            immediate,
            (torch.tensor([float("nan")], dtype=torch.float64),),
            null_zero,
        )


def test_update_serializes_reference_activation_and_rejects_route_tampering(
    completed_update: tuple[dict[str, g48.G48Model], dict[str, object]],
) -> None:
    models, record = completed_update
    assert g48._update_evidence_valid(record), record
    assert record["real_transitions"] == 768
    assert record["order_swap_guard"]["passed"] is True
    assert len(record["pass_records"]) == 2
    for pass_record in record["pass_records"]:
        assert pass_record["null_duplicate_channel_gradient_bytes_equal"] is True
        assert pass_record["actual_null_activation_evidence_read_count"] == 0
        assert pass_record["activation"]["evidence_source_arm"] == g48.REFERENCE_ARM
        assert pass_record["activation"]["direction_distance_conclusion_gate"] is False
        assert pass_record["reference_gradient_evidence"][
            "every_group_live_in_at_least_one_channel"
        ] is True

    conclusion = g48.build_conclusion_evidence([record], formal=False)
    assert conclusion["passed"] is True
    assert g48.validate_conclusion_evidence(conclusion)
    checkpoints = {
        arm: g48.build_final_checkpoint(
            arm, models[arm], record, conclusion, formal=False
        )
        for arm in g48.ARMS
    }
    assert checkpoints[g48.NULL_ARM]["target_route_certificate"] == {
        "target_law": "x_I1=r_t|x_I2=r_t",
        "channel_ids": ["immediate_1", "immediate_2"],
        "realized_successor_actor_credit_reads": 0,
        "successor_counterfactual_calls": 0,
        "duplicate_channel_evidence_required": True,
    }

    swapped = copy.deepcopy(record)
    swapped["pass_records"][0]["normalization_by_arm"][g48.NULL_ARM][
        "target_route"
    ] = "immediate_reward|realized_successor_G_next"
    assert not g48._update_evidence_valid(swapped)

    forged_null = copy.deepcopy(record)
    forged_null["pass_records"][0]["actual_null_activation_evidence_read_count"] = 1
    assert not g48._update_evidence_valid(forged_null)

    no_active = copy.deepcopy(conclusion)
    no_active["activation_records"][0]["activation"]["treatment_active"] = False
    assert not g48.validate_conclusion_evidence(no_active)
