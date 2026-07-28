from __future__ import annotations

import copy
import hashlib
import io
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch
from torch import nn

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44
    as g44,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as g43,
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
ANCHOR_BYTES = 81_017
ANCHOR_SHA256 = "d6920e8ab958b776ee0b25a5d2a1b120528b69abc87d4eacc2a6deee2351b521"


@pytest.fixture(scope="module")
def accepted_anchor_batch() -> Iterator[
    tuple[g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory]
]:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        fixture = ANCHOR_FIXTURE.read_bytes()
        assert len(fixture) == ANCHOR_BYTES
        assert hashlib.sha256(fixture).hexdigest() == ANCHOR_SHA256
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            torch.load(io.BytesIO(fixture), map_location="cpu", weights_only=False),
            accepted_anchor_replicate=0,
        )
        trajectory = g40.collect_g40_trajectory(
            anchor,
            episode_ids=range(8),
            ledger_seed=11_343_000,
            action_seed=11_343_000,
            device=torch.device("cpu"),
        )
        assert trajectory.rewards.numel() == 384
        yield anchor, trajectory
    finally:
        torch.set_num_threads(prior_threads)


def _project_update(
    anchor: g40.G40NativeSixPolicy,
    trajectory: g40.AnchoredRosterTrajectory,
) -> tuple[
    dict[str, g41.G41NoSlowProjection],
    dict[str, torch.optim.Optimizer],
    dict[str, object],
]:
    models = g44.project_g44_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    record = g44.optimize_channel_scale_update(
        models,
        optimizers,
        {arm: trajectory for arm in g44.ARMS},
        update_index=0,
    )
    return models, optimizers, record


def test_exact_centering_rms_and_zero_rules() -> None:
    rewards = torch.tensor([[1.0, 3.0, 5.0, 7.0] * 2]).repeat(48, 1)
    credit = g41.G41Credit(
        returns=torch.zeros_like(rewards),
        successor_targets=torch.zeros_like(rewards),
        immediate_advantage=rewards,
        successor_advantage=2.0 * rewards,
    )
    normalized = g44.normalize_credit_channels(credit)
    assert normalized.centered_immediate.numel() == 384
    assert normalized.immediate_mean == 4.0
    assert normalized.successor_mean == 8.0
    assert normalized.immediate_centered_sum_square == 1_920.0
    assert normalized.successor_centered_sum_square == 7_680.0
    assert normalized.immediate_scale == pytest.approx(2.23606797749979)
    assert normalized.successor_scale == pytest.approx(4.47213595499958)
    expected_pool = ((normalized.immediate_scale**2 + normalized.successor_scale**2) / 2) ** 0.5
    assert normalized.pooled_scale == pytest.approx(expected_pool)
    assert normalized.normalization_row_count == 384
    assert normalized.normalization_mask_digest == g44.NORMALIZATION_MASK_DIGEST
    assert len(normalized.normalization_mask_digest) == 64
    assert float(normalized.independent_immediate.mean()) == pytest.approx(0.0)
    assert float(normalized.independent_successor.mean()) == pytest.approx(0.0)

    constant = torch.ones((48, 8))
    zeros = g44.normalize_credit_channels(
        g41.G41Credit(
            returns=constant,
            successor_targets=constant,
            immediate_advantage=constant,
            successor_advantage=constant,
        )
    )
    assert zeros.immediate_scale == 0.0
    assert zeros.successor_scale == 0.0
    assert zeros.pooled_scale == 0.0
    assert zeros.immediate_centered_sum_square == 0.0
    assert zeros.successor_centered_sum_square == 0.0
    assert zeros.normalization_mask_digest == normalized.normalization_mask_digest
    assert torch.count_nonzero(zeros.independent_immediate) == 0
    assert torch.count_nonzero(zeros.pooled_successor) == 0


def test_projection_preserves_accepted_chain_and_has_no_db_state(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = accepted_anchor_batch
    models = g44.project_g44_arms(anchor, accepted_anchor_replicate=0)
    assert tuple(models) == g44.ARMS
    assert g44.ACCEPTED_G43_SOURCE_COMMIT == (
        "bb42840ab1479abde7f3485006bfbbee981a73cf"
    )
    assert g44.ACCEPTED_G43_ALIGNED_SOURCE_COMMIT == (
        "45e16f71d171228135b6444bee1678b157d79abe"
    )
    assert g40.state_bytes(models[g44.INDEPENDENT_ARM]) == g40.state_bytes(
        models[g44.POOLED_ARM]
    )
    assert g40.shared_tensor_storage_count(tuple(models.values())) == 0
    assert all(not hasattr(model, "slow_critic") for model in models.values())
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    boundary = g44.branch_boundary_audit(models, optimizers)
    assert boundary["provenance_valid"] is True
    assert boundary["no_db_state"] is True
    assert boundary["db_vector_present"] is False
    assert boundary["db_norm_present"] is False
    assert boundary["db_shadow_present"] is False
    assert boundary["passed"] is True, boundary


def test_pooled_counterfactual_scalar_gate_and_cancellation() -> None:
    parameter = nn.Parameter(torch.zeros(2, dtype=torch.float64))
    raw = (torch.tensor([3.0, 4.0], dtype=torch.float64),)
    assigned, record = g44._scale_to_counterfactual_norm(
        raw, (parameter,), counterfactual_norm=2.5
    )
    assert torch.equal(
        assigned[0], torch.tensor([1.5, 2.0], dtype=torch.float64)
    )
    assert record["assigned_credit_norm"] == 2.5
    assert record["raw_credit_norm"] == 5.0
    assert record["raw_credit_norm"] != record[
        "counterfactual_independent_credit_norm"
    ]
    assert record["unscaled_raw_norm_compared_to_counterfactual"] is False
    assert record["assigned_norm_match_error"] <= record[
        "assigned_norm_match_tolerance"
    ]
    assert record["shadow_output_type"] == "one_detached_scalar_norm"
    for name in (
        "shadow_vector_coordinate_use_outside_norm",
        "shadow_gradient_assignment_count",
        "shadow_optimizer_state_count",
        "shadow_RNG_consumption",
        "shadow_model_mutation_count",
        "shadow_checkpoint_selection_reads",
        "shadow_evaluation_reads",
        "pooled_arm_evidence_read_count",
    ):
        assert record[name] == 0
    zero, zero_record = g44._scale_to_counterfactual_norm(
        raw, (parameter,), counterfactual_norm=0.0
    )
    assert torch.equal(zero[0], torch.zeros_like(parameter))
    assert zero_record["actor_credit_gradients_exact_zero"] is True
    with pytest.raises(
        g44.G44GradientGateError,
        match="positive_counterfactual_norm_with_zero_pooled_direction",
    ):
        g44._scale_to_counterfactual_norm(
            (torch.zeros(2, dtype=torch.float64),),
            (parameter,),
            counterfactual_norm=1.0,
        )


def test_first_update_is_exact_treatment_and_activation_reconstructs(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, optimizers, record = _project_update(anchor, trajectory)
    assert record["passed"] is True
    assert record["normalization_rows"] == 384
    assert record["normalization_count"] == 1
    assert record["normalization_recomputed_between_passes"] is False
    assert record["branch_update_order"] == list(g44.ARMS)
    assert record["actor_head_optimizer_steps"] == {
        arm: 2.0 for arm in g44.ARMS
    }
    assert record["first_paired_direct_treatment_audit"]["passed"] is True
    assert record["order_swap_guard"]["passed"] is True
    for pass_record in record["pass_records"]:
        schedule = pass_record["channel_scale_schedule"]
        normalization_by_arm = pass_record["normalization_by_arm"]
        assert tuple(normalization_by_arm) == g44.ARMS
        assert g44.validate_normalization_by_arm(normalization_by_arm)
        for arm in g44.ARMS:
            assert normalization_by_arm[arm]["arm"] == arm
            assert g44.validate_normalization_statistics(
                normalization_by_arm[arm]
            )
        assert all(
            schedule[name] == normalization_by_arm[g44.INDEPENDENT_ARM][name]
            for name in g44.NORMALIZATION_STATISTIC_FIELDS
        )
        assert g44.validate_schedule_record(schedule)
        assert schedule["evidence_source_arm"] == g44.INDEPENDENT_ARM
        assert schedule["reference_pooled_counterfactual"] is True
        assert schedule["pooled_arm_evidence_read_count"] == 0
        assert schedule["normalization_row_count"] == 384
        assert schedule["normalization_mask_digest"] == (
            g44.NORMALIZATION_MASK_DIGEST
        )
        assert schedule["immediate_scale"] == schedule["s_I"]
        assert schedule["successor_scale"] == schedule["s_S"]
        assert schedule["pooled_scale"] == schedule["s_P"]
        assert schedule["strict_activation_observed"] is True
        independent = pass_record["composition"][g44.INDEPENDENT_ARM]
        pooled = pass_record["composition"][g44.POOLED_ARM]
        assert independent["entropy_added_after_credit_gate"] is True
        assert pooled["entropy_added_after_credit_gate"] is True
        assert independent[
            "entropy_and_baseline_terms_bitwise_independent_of_scale_path"
        ] is True
        assert pooled[
            "entropy_and_baseline_terms_bitwise_independent_of_scale_path"
        ] is True
        assert independent["entropy_gradient_source_arm"] == g44.INDEPENDENT_ARM
        assert pooled["entropy_gradient_source_arm"] == g44.INDEPENDENT_ARM
        assert independent["entropy_gradient_bitwise_identical_across_arms"] is True
        assert pooled["entropy_gradient_bitwise_identical_across_arms"] is True
        assert pooled["assigned_norm_match_error"] <= pooled[
            "assigned_norm_match_tolerance"
        ]
        assert pooled["unscaled_raw_norm_compared_to_counterfactual"] is False
        assert pooled["shadow_vector_serialized"] is False
        for arm in g44.ARMS:
            assert g43.validate_registered_gradient_evidence(
                pass_record["gradient_evidence"][arm]
            )
    conclusion = g44.build_conclusion_evidence([record], formal=False)
    assert g44.validate_conclusion_evidence(conclusion)
    assert conclusion["reference_pooled_counterfactual"] is True
    assert conclusion["pooled_arm_evidence_read_count"] == 0
    assert conclusion["normalization_evidence_arms"] == list(g44.ARMS)
    assert g44.validate_normalization_by_arm(
        conclusion["replicate_rows"][0]["reconstructed_passes"][0][
            "normalization_by_arm"
        ]
    )
    forged = copy.deepcopy(conclusion)
    forged["replicate_rows"][0]["reconstructed_passes"][0]["q_scale"] = 0.0
    forged["replicate_rows"][0]["strict_activation_observed"] = True
    assert not g44.validate_conclusion_evidence(forged)
    forged_direction = copy.deepcopy(conclusion)
    forged_direction["replicate_rows"][0]["reconstructed_passes"][0][
        "q_direction"
    ] = 0.0
    assert not g44.validate_conclusion_evidence(forged_direction)
    forged_mask = copy.deepcopy(conclusion)
    forged_mask["replicate_rows"][0]["reconstructed_passes"][0][
        "normalization_mask_digest"
    ] = "0" * 64
    assert not g44.validate_conclusion_evidence(forged_mask)
    forged_pooled = copy.deepcopy(conclusion)
    forged_pooled["replicate_rows"][0]["reconstructed_passes"][0][
        "normalization_by_arm"
    ][g44.POOLED_ARM]["normalization_mask_digest"] = "0" * 64
    assert not g44.validate_conclusion_evidence(forged_pooled)
    pooled_tamper = copy.deepcopy(record)
    reference_schedule = copy.deepcopy(
        pooled_tamper["pass_records"][0]["channel_scale_schedule"]
    )
    pooled_tamper["pass_records"][0]["normalization_by_arm"][
        g44.POOLED_ARM
    ]["normalization_mask_digest"] = "0" * 64
    assert pooled_tamper["pass_records"][0]["channel_scale_schedule"] == (
        reference_schedule
    )
    assert not g44._update_evidence_valid(pooled_tamper)
    assert not g44.validate_conclusion_evidence(
        g44.build_conclusion_evidence([pooled_tamper], formal=False)
    )
    with pytest.raises(ValueError, match="final checkpoint update evidence invalid"):
        g44.build_final_checkpoint(
            g44.POOLED_ARM,
            models[g44.POOLED_ARM],
            pooled_tamper,
            conclusion,
            formal=False,
        )
    route_tamper = copy.deepcopy(record)
    route_tamper["pass_records"][0]["normalization_by_arm"][
        g44.POOLED_ARM
    ]["arm"] = g44.INDEPENDENT_ARM
    assert not g44._update_evidence_valid(route_tamper)
    assert all(
        min(
            g44._optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].actor_credit_parameters()
        )
        == 2.0
        for arm in g44.ARMS
    )


def test_dead_actor_and_baseline_groups_fail_registered_liveness(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = accepted_anchor_batch
    model = g44.project_g44_arms(anchor, accepted_anchor_replicate=0)[
        g44.INDEPENDENT_ARM
    ]
    actor = model.full_actor_parameters()
    baseline = tuple(model.credit_baselines.parameters())
    live_actor = tuple(torch.ones_like(parameter) for parameter in actor)
    dead_actor = tuple(torch.zeros_like(parameter) for parameter in actor)
    live_baseline = tuple(torch.ones_like(parameter) for parameter in baseline)
    dead_baseline = tuple(torch.zeros_like(parameter) for parameter in baseline)
    dead_actor_evidence = g43.registered_gradient_evidence(
        model, dead_actor, live_actor, live_baseline, live_baseline
    )
    dead_baseline_evidence = g43.registered_gradient_evidence(
        model, live_actor, live_actor, dead_baseline, live_baseline
    )
    assert not g43.validate_registered_gradient_evidence(dead_actor_evidence)
    assert not g43.validate_registered_gradient_evidence(dead_baseline_evidence)
