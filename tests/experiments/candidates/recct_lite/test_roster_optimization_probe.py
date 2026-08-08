"""Proof-sized tests for the RECCT dependency mask on the real learner.

The decisive test here is ``test_unchanged_arm_is_bit_identical_to_g40``: the
probe reimplements G40's fast-anchor update so the mask can be inserted without
touching ``ha_ctse_process/``, and that reimplementation must be exact or every
number the probe emits is measuring the wrong learner.
"""

from __future__ import annotations

import torch

import ha_ctse_process.continuous_roster_native_six_credit_reduction_g40 as g40

from experiments.candidates.recct_lite import roster_learner_mask as mask
from experiments.candidates.recct_lite import roster_optimization_probe as probe

SEED = 20_260_805
CAPACITY = 8


def _model_and_optimizer():
    model = g40.make_model(CAPACITY, initialization_seed=SEED)
    optimizer = torch.optim.Adam(
        model.actor_credit_parameters(), lr=g40.LEARNING_RATE
    )
    return model, optimizer


def _trajectory(model):
    return g40.collect_g40_trajectory(
        model,
        episode_ids=range(2),
        ledger_seed=SEED + 2,
        action_seed=SEED + 3,
        device=torch.device("cpu"),
    )


def test_unchanged_arm_is_bit_identical_to_g40():
    """The reimplementation must be exact, or the probe measures a different learner."""
    reference_model, reference_optimizer = _model_and_optimizer()
    trajectory = _trajectory(reference_model)
    g40.optimize_common_fast_anchor_update(
        reference_model, reference_optimizer, trajectory, ppo_passes=2
    )

    probe_model, probe_optimizer = _model_and_optimizer()
    probe_trajectory = _trajectory(probe_model)
    probe.fast_anchor_update_with_arm(
        probe_model,
        probe_optimizer,
        probe_trajectory,
        arm=mask.UNCHANGED,
        ppo_passes=2,
    )

    assert g40.state_bytes(probe_model) == g40.state_bytes(reference_model)


def test_candidate_arm_actually_diverges_from_unchanged():
    """If the mask never bites, the probe has no treatment at all."""
    unchanged_model, unchanged_optimizer = _model_and_optimizer()
    probe.fast_anchor_update_with_arm(
        unchanged_model,
        unchanged_optimizer,
        _trajectory(unchanged_model),
        arm=mask.UNCHANGED,
        ppo_passes=3,
    )

    candidate_model, candidate_optimizer = _model_and_optimizer()
    probe.fast_anchor_update_with_arm(
        candidate_model,
        candidate_optimizer,
        _trajectory(candidate_model),
        arm=mask.CANDIDATE,
        ppo_passes=3,
    )

    assert g40.state_bytes(candidate_model) != g40.state_bytes(unchanged_model)


def test_mask_is_inactive_on_the_first_step_and_active_later():
    """Step 0 has no Adam moment, so everything is feasible; later it bites."""
    model, optimizer = _model_and_optimizer()
    retained, _, _ = probe.fast_anchor_update_with_arm(
        model, optimizer, _trajectory(model), arm=mask.CANDIDATE, ppo_passes=3
    )
    assert retained[0] == 1.0, "no pre-update moment exists on the first step"
    assert min(retained[1:]) < 1.0, "the mask must remove something after step 0"


def test_sign_destroyed_retains_the_same_support_as_candidate():
    """Objective-matched control: same sparsity, destroyed credit direction."""
    model, optimizer = _model_and_optimizer()
    trajectory = _trajectory(model)
    parameters = model.actor_credit_parameters()

    # Give Adam a real pre-update moment so the mask is non-trivial.
    probe.fast_anchor_update_with_arm(
        model, optimizer, trajectory, arm=mask.UNCHANGED, ppo_passes=1
    )

    replay = g40.replay_trajectory(model, trajectory, device=torch.device("cpu"))
    loss = replay.immediate_baselines.pow(2).mean()
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    saved = [None if p.grad is None else p.grad.clone() for p in parameters]

    candidate = mask.apply_arm(parameters, arm=mask.CANDIDATE, optimizer=optimizer)
    for parameter, original in zip(parameters, saved):
        if original is not None:
            parameter.grad.copy_(original)
    destroyed = mask.apply_arm(
        parameters,
        arm=mask.SIGN_DESTROYED,
        optimizer=optimizer,
        generator=torch.Generator(device="cpu").manual_seed(1),
    )

    assert candidate.retained_parameters == destroyed.retained_parameters
    assert candidate.zeroed_parameters == destroyed.zeroed_parameters
    assert destroyed.sign_flipped_parameters == destroyed.retained_parameters
    assert candidate.sign_flipped_parameters == 0


def test_ancestry_refusal_zeroes_the_whole_tensor():
    model, optimizer = _model_and_optimizer()
    trajectory = _trajectory(model)
    parameters = model.actor_credit_parameters()
    replay = g40.replay_trajectory(model, trajectory, device=torch.device("cpu"))
    optimizer.zero_grad(set_to_none=True)
    replay.immediate_baselines.pow(2).mean().backward()

    refused = {index: False for index in range(len(parameters))}
    decision = mask.apply_arm(
        parameters,
        arm=mask.CANDIDATE,
        optimizer=optimizer,
        ancestry_admits=refused,
    )
    assert decision.retained_parameters == 0
    assert all(
        parameter.grad is None or bool(torch.all(parameter.grad == 0))
        for parameter in parameters
    )


def test_mask_reads_no_post_update_state():
    """Admissibility: the mask must not consult the step it is about to take."""
    model, optimizer = _model_and_optimizer()
    trajectory = _trajectory(model)
    parameters = model.actor_credit_parameters()
    probe.fast_anchor_update_with_arm(
        model, optimizer, trajectory, arm=mask.UNCHANGED, ppo_passes=1
    )

    replay = g40.replay_trajectory(model, trajectory, device=torch.device("cpu"))
    optimizer.zero_grad(set_to_none=True)
    replay.immediate_baselines.pow(2).mean().backward()

    before = {
        id(p): optimizer.state[p]["exp_avg_sq"].clone()
        for p in parameters
        if p in optimizer.state and "exp_avg_sq" in optimizer.state[p]
    }
    target = next(p for p in parameters if p.grad is not None)
    first = mask.recct_feasible_mask(
        target, target.grad, optimizer=optimizer, ancestry_admits=True
    )
    second = mask.recct_feasible_mask(
        target, target.grad, optimizer=optimizer, ancestry_admits=True
    )
    assert torch.equal(first, second), "mask must be a pure function of pre-update state"
    for parameter in parameters:
        if id(parameter) in before:
            assert torch.equal(
                optimizer.state[parameter]["exp_avg_sq"], before[id(parameter)]
            ), "mask must not mutate optimizer state"


def test_unregistered_arm_is_refused():
    model, optimizer = _model_and_optimizer()
    try:
        mask.apply_arm([], arm="SOMETHING_ELSE", optimizer=optimizer)
    except ValueError:
        return
    raise AssertionError("unregistered arm must be refused")


def test_report_carries_the_non_promotion_boundary():
    """The scope limit must travel with the numbers, not beside them."""
    report = probe.ProbeReport(arms={}, capacity=8, iterations=1, ppo_passes=1, seed=0)
    payload = report.payload()
    assert "no promotion and no elimination" in payload["admissible_conclusion"]
