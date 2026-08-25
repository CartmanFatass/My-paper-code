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
    continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as g43,
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
            ledger_seed=10_431_000,
            action_seed=10_432_000,
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
    models = g43.project_g43_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    record = g43.optimize_norm_schedule_update(
        models,
        optimizers,
        {arm: trajectory for arm in g43.ARMS},
        update_index=0,
    )
    return models, optimizers, record


def test_projection_preserves_g40_g41_g42_provenance_and_empty_branches(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = accepted_anchor_batch
    models = g43.project_g43_arms(anchor, accepted_anchor_replicate=0)
    assert g43.ACCEPTED_G40_SOURCE_COMMIT == (
        "97a8b237e0cec6c2713dd2a710d324040fa3dfc2"
    )
    assert g43.ACCEPTED_G41_SOURCE_COMMIT == (
        "a5f63c349228fc2bba7843647e0ae4c34361c1c9"
    )
    assert g43.ACCEPTED_G42_REFERENCE_SOURCE_COMMIT == (
        "a6c3c2971ee74e76a453995c3a7c12627bb8f02c"
    )
    assert g43.ACCEPTED_G42_ALIGNED_SOURCE_COMMIT == (
        "6b8ea82d8fdbc76c14a414ff2b042a126f945dfb"
    )
    assert g43.ACCEPTED_G42_ALIGNMENT_STAGE_COMMIT == (
        "309858dca06af66f13857f94773bcef37527d821"
    )
    assert tuple(models) == g43.ARMS
    assert g40.state_bytes(models[g43.DBNORM_ARM]) == g40.state_bytes(
        models[g43.MEAN_ARM]
    )
    assert g40.shared_tensor_storage_count(tuple(models.values())) == 0
    assert all(not hasattr(model, "slow_critic") for model in models.values())
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    boundary = g43.branch_boundary_audit(models, optimizers)
    assert boundary["model_state_bytes_equal"] is True
    assert boundary["optimizer_states_empty_and_separate"] is True
    assert boundary["provenance_valid"] is True
    assert boundary["passed"] is True, boundary


def test_deterministic_mean_and_dbnorm_zero_cancellation_contract() -> None:
    parameter = nn.Parameter(torch.zeros(2, dtype=torch.float64))
    immediate = (torch.tensor([3.0, 0.0], dtype=torch.float64),)
    successor = (torch.tensor([0.0, 4.0], dtype=torch.float64),)
    mean = g43.compose_equal_mean_gradients(
        immediate, successor, (parameter,)
    )
    assert mean.literal_coefficient == 0.5
    assert mean.raw_sum_norm == 5.0
    assert mean.applied_gradient_norm == 2.5
    assert torch.equal(
        mean.gradients[0], torch.tensor([1.5, 2.0], dtype=torch.float64)
    )
    dependency = g43.mean_dependency_audit()
    assert dependency["input_signature"] == (
        "immediate",
        "successor",
        "parameters",
    )
    for name in (
        "DB_vector_read_count",
        "DB_norm_read_count",
        "DB_composer_call_count",
        "shadow_DB_state_count",
        "fallback_channel_count",
        "per_group_scale_count",
        "search_count",
    ):
        assert dependency[name] == 0
    assert dependency["passed"] is True, dependency

    zero = g43._dbnorm_composition(
        (torch.ones(2, dtype=torch.float64),),
        (-torch.ones(2, dtype=torch.float64),),
        (parameter,),
        db_norm=0.0,
    )
    zero_mean = g43.compose_equal_mean_gradients(
        (torch.ones(2, dtype=torch.float64),),
        (-torch.ones(2, dtype=torch.float64),),
        (parameter,),
    )
    schedule = g43.treatment_schedule_record(
        dbnorm=zero, reference_equal_mean=zero_mean
    )
    assert schedule["q"] == 0.0
    assert schedule["q_counting"] is False
    assert schedule["zero_db_norm"] is True
    assert schedule["zero_raw_sum"] is True
    assert torch.equal(zero.gradients[0], torch.zeros_like(parameter))
    with pytest.raises(
        g43.G43GradientGateError,
        match="positive_norm_raw_sum_zero_or_nonfinite",
    ):
        g43._dbnorm_composition(
            (torch.ones(2, dtype=torch.float64),),
            (-torch.ones(2, dtype=torch.float64),),
            (parameter,),
            db_norm=1.0,
        )


def test_first_paired_update_enforces_liveness_activation_order_and_artifacts(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, optimizers, record = _project_update(anchor, trajectory)
    assert record["passed"] is True, record
    assert record["first_paired_direct_treatment_audit"]["passed"] is True
    assert record["first_paired_direct_treatment_audit"][
        "non_collinearity_detected"
    ] is False
    assert record["order_swap_guard"]["passed"] is True
    assert record["order_swap_guard"]["diagnostic_optimizer_steps"] == 0
    assert record["branch_update_order"] == list(g43.ARMS)
    assert record["actor_head_optimizer_steps"] == {
        g43.DBNORM_ARM: 2.0,
        g43.MEAN_ARM: 2.0,
    }
    assert record["K_search"] == 0
    assert record["hypothetical_trajectory_count"] == 0
    assert record["hypothetical_transitions"] == 0
    assert record["torch_rng_unchanged"] is True
    for pass_record in record["pass_records"]:
        assert pass_record["plans_materialized_before_either_optimizer"] is True
        assert pass_record["branch_update_order"] == list(g43.ARMS)
        assert all(
            g43.validate_registered_gradient_evidence(
                pass_record["gradient_evidence"][arm]
            )
            for arm in g43.ARMS
        )
        assert pass_record["composition"][g43.MEAN_ARM][
            "literal_coefficient"
        ] == 0.5
        assert pass_record["composition"][g43.MEAN_ARM][
            "DB_norm_read_count"
        ] == 0
        assert g43.validate_treatment_schedule_record(
            pass_record["treatment_schedule"]
        )
        assert pass_record["treatment_schedule"]["evidence_source_arm"] == (
            g43.DBNORM_ARM
        )
        assert pass_record["treatment_schedule"][
            "null_arm_evidence_read_count"
        ] == 0
    conclusion = g43.build_conclusion_evidence([record], formal=False)
    assert conclusion["passed"] is True, conclusion
    assert g43.validate_conclusion_evidence(conclusion) is True
    checkpoints = {
        arm: g43.build_final_checkpoint(
            arm, models[arm], record, conclusion, formal=False
        )
        for arm in g43.ARMS
    }
    assert checkpoints[g43.DBNORM_ARM]["gradient_schedule"] == (
        "db_derived_global_norm_raw_sum_direction"
    )
    assert checkpoints[g43.MEAN_ARM]["gradient_schedule"] == (
        "fixed_literal_half_raw_sum"
    )
    for checkpoint in checkpoints.values():
        assert checkpoint["checkpoint_kind"] == (
            "FINAL_ONLY_NO_SLOW_DB_NORM_ATTRIBUTION"
        )
        assert checkpoint["standalone_slow_present"] is False
        assert not any("slow_critic" in name for name in checkpoint["model_state"])
    assert all(
        all(
            float(optimizer.state[parameter]["step"]) == 2.0
            for parameter in models[arm].actor_credit_parameters()
        )
        for arm, optimizer in optimizers.items()
    )


def test_reference_schedule_ignores_post_divergence_mean_arm_gradients(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models = g43.project_g43_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    trajectories = {arm: trajectory for arm in g43.ARMS}
    credits = {
        arm: g41.compute_g31_credit_without_slow(
            rewards=trajectory.rewards,
            immediate_baselines=trajectory.old_immediate_baselines,
            successor_baselines=trajectory.old_successor_baselines,
            terminals=g40.terminal_mask(trajectory),
        )
        for arm in g43.ARMS
    }
    normalized = {
        arm: g41._normalized_g31_advantages(credits[arm])
        for arm in g43.ARMS
    }
    initial_plans, _, initial_schedule = g43._prepare_passes(
        models, trajectories, credits, normalized
    )
    with torch.no_grad():
        next(models[g43.MEAN_ARM].policy.parameters()).add_(0.125)
    divergent_plans, _, divergent_schedule = g43._prepare_passes(
        models, trajectories, credits, normalized
    )
    assert divergent_plans[g43.MEAN_ARM].composition_record != (
        initial_plans[g43.MEAN_ARM].composition_record
    )
    assert divergent_schedule == initial_schedule
    assert divergent_schedule["evidence_source_arm"] == g43.DBNORM_ARM
    assert divergent_schedule["reference_equal_mean_counterfactual"] is True
    assert divergent_schedule["null_arm_evidence_read_count"] == 0

    parameter = nn.Parameter(torch.zeros(1, dtype=torch.float64))
    reference_dbnorm = g43._dbnorm_composition(
        (torch.tensor([2.0], dtype=torch.float64),),
        (torch.tensor([0.0], dtype=torch.float64),),
        (parameter,),
        db_norm=1.0,
    )
    reference_equal_mean = g43.compose_equal_mean_gradients(
        (torch.tensor([2.0], dtype=torch.float64),),
        (torch.tensor([0.0], dtype=torch.float64),),
        (parameter,),
    )
    divergent_null_mean = g43.compose_equal_mean_gradients(
        (torch.tensor([20.0], dtype=torch.float64),),
        (torch.tensor([0.0], dtype=torch.float64),),
        (parameter,),
    )
    assert divergent_null_mean.applied_gradient_norm != (
        reference_equal_mean.applied_gradient_norm
    )
    inactive = g43.treatment_schedule_record(
        dbnorm=reference_dbnorm,
        reference_equal_mean=reference_equal_mean,
    )
    assert inactive["q"] == 0.0
    assert inactive["strict_activation_observed"] is False


def test_zero_db_norm_still_steps_actor_head_and_updates_baselines(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models = g43.project_g43_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    actor_before = tuple(
        parameter.detach().clone()
        for parameter in models[g43.DBNORM_ARM].full_actor_parameters()
    )
    baseline_before = g40.state_bytes(models[g43.DBNORM_ARM].credit_baselines)

    original = g40._actor_objective_gradients

    def exact_zero_preview(*args: object, **kwargs: object):
        policy, _ = original(*args, **kwargs)
        model = args[1]
        return policy, tuple(
            torch.zeros_like(parameter)
            for parameter in model.full_actor_parameters()
        )

    monkeypatch.setattr(g40, "_actor_objective_gradients", exact_zero_preview)
    record = g43.optimize_norm_schedule_update(
        models,
        optimizers,
        {arm: trajectory for arm in g43.ARMS},
        update_index=0,
    )
    assert all(
        pass_record["treatment_schedule"]["zero_db_norm"] is True
        for pass_record in record["pass_records"]
    )
    assert all(
        torch.equal(before, after)
        for before, after in zip(
            actor_before, models[g43.DBNORM_ARM].full_actor_parameters()
        )
    )
    assert baseline_before != g40.state_bytes(
        models[g43.DBNORM_ARM].credit_baselines
    )
    assert all(
        float(optimizers[arm].state[parameter]["step"]) == 2.0
        for arm in g43.ARMS
        for parameter in models[arm].actor_credit_parameters()
    )


def test_dead_groups_q_tamper_and_missing_formal_replicate_fail_closed(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, _, record = _project_update(anchor, trajectory)
    model = models[g43.DBNORM_ARM]
    actor = model.full_actor_parameters()
    baseline = tuple(model.credit_baselines.parameters())
    live_actor = tuple(torch.ones_like(parameter) for parameter in actor)
    live_baseline = tuple(torch.ones_like(parameter) for parameter in baseline)
    actor_index = {id(parameter): index for index, parameter in enumerate(actor)}
    dead_actor = list(live_actor)
    for parameter in g40._actor_groups(model)["current_readout"]:
        dead_actor[actor_index[id(parameter)]] = torch.zeros_like(parameter)
    evidence = g43.registered_gradient_evidence(
        model,
        tuple(dead_actor),
        tuple(dead_actor),
        live_baseline,
        live_baseline,
    )
    assert g43.validate_registered_gradient_evidence(evidence) is False
    dead_baseline = g43.registered_gradient_evidence(
        model,
        live_actor,
        live_actor,
        tuple(torch.zeros_like(parameter) for parameter in baseline),
        live_baseline,
    )
    assert g43.validate_registered_gradient_evidence(dead_baseline) is False

    tampered = copy.deepcopy(record)
    tampered["pass_records"][0]["treatment_schedule"]["q"] = 0.0
    assert g43._update_evidence_valid(tampered) is False

    formal_records: list[dict[str, object]] = []
    for replicate in g43.ACCEPTED_G40_ANCHOR_REPLICATES:
        item = copy.deepcopy(record)
        item["accepted_g40_anchor_replicate"] = replicate
        item["branch_boundary"]["accepted_g40_anchor_authority"] = (
            g41.accepted_g40_anchor_identity(replicate)
        )
        formal_records.append(item)
    formal = g43.build_conclusion_evidence(formal_records, formal=True)
    assert formal["passed"] is True, formal
    assert g43.validate_conclusion_evidence(formal) is True
    missing = g43.build_conclusion_evidence(formal_records[:2], formal=True)
    assert missing["passed"] is False
    assert g43.validate_conclusion_evidence(missing) is False
    inactive = copy.deepcopy(formal_records)
    for pass_record in inactive[1]["pass_records"]:
        schedule = pass_record["treatment_schedule"]
        schedule["equal_mean_norm"] = schedule["db_norm"]
        schedule["q"] = 0.0
        schedule["q_counting"] = schedule["db_norm"] > 0.0
        schedule["q_state"] = (
            "defined_positive_denominator"
            if schedule["q_counting"]
            else "both_zero_noncounting_zero_step"
        )
        schedule["strict_activation_observed"] = False
    inactive_formal = g43.build_conclusion_evidence(inactive, formal=True)
    assert inactive_formal["passed"] is False
    assert g43.validate_conclusion_evidence(inactive_formal) is False
