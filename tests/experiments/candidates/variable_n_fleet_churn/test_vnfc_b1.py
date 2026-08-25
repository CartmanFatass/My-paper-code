from __future__ import annotations

import math

import numpy as np
import torch

from experiments.candidates.variable_n_fleet_churn.experiment import (
    _decoder_base, _joint_group_statistics, _replica_deviations,
    _world_descriptors, Transition,
)
from experiments.candidates.variable_n_fleet_churn.analyze import analyze
from experiments.candidates.variable_n_fleet_churn.host import (
    CAPACITY_NORMALIZED, REGIMES, TRUE_EXPANSION, allocation_metrics,
    churn_world, row_order, static_pair, training_world,
)
from experiments.candidates.variable_n_fleet_churn.models import (
    A_JOINT, A_MASS, B_REBIND, G_MEAN, LEARNED_ARMS, SetActorCritic,
    assignment_tensor, exact_best_response, greedy_action, make_observation,
)


def test_training_worlds_are_odd_arm_independent_and_capacity_normalized() -> None:
    first = [training_world(1103, index) for index in range(24)]
    second = [training_world(1103, index) for index in range(24)]
    assert [world.sequence for world in first] == [world.sequence for world in second]
    assert all(set(world.sequence) <= {3, 5, 7} for world in first)
    assert {world.regime for world in first} == set(REGIMES)
    for world in first:
        assert all({world.specialties[h] for h in roster} == {0, 1, 2} for roster in world.rosters)
        if world.regime == CAPACITY_NORMALIZED:
            for segment in range(3):
                capacities = world.capacities(segment)
                for task in range(3):
                    ratio = sum(float(row[task]) for row in capacities.values()) / world.demands[task]
                    assert math.isclose(ratio, 1.35, rel_tol=1e-5, abs_tol=1e-6)


def test_static_panel_is_nested_and_full_panel_has_480_base_episodes() -> None:
    for regime in REGIMES:
        for pair_index in range(3):
            world4, world6 = static_pair(1103, regime, pair_index)
            assert world6.rosters[0][:4] == world4.rosters[0]
            assert world4.demands == world6.demands
            assert world4.raw_capabilities == world6.raw_capabilities
    descriptors = list(_world_descriptors(1103))
    assert len(descriptors) == 480
    assert sum(panel == "static" for panel, *_ in descriptors) == 192
    assert sum(panel == "churn" for panel, *_ in descriptors) == 288


def test_all_learned_arms_have_identical_parameter_count_and_widths() -> None:
    models = {arm: SetActorCritic(arm) for arm in LEARNED_ARMS}
    assert len({model.parameter_count for model in models.values()}) == 1
    assert SetActorCritic.COMMON_WIDTH == 237
    assert SetActorCritic.BID_INPUT_WIDTH == 333


def test_greedy_physical_assignment_is_row_permutation_equivariant() -> None:
    world = churn_world(1103, TRUE_EXPANSION, 3, 2)
    previous = None
    for arm in LEARNED_ARMS:
        model = SetActorCritic(arm).eval()
        outputs = []
        for replica in range(4):
            order = row_order(
                world.rosters[0], world.base_seed, world.split,
                world.world_index, world.regime, 0, replica,
            )
            observation = make_observation(world, 0, order, previous)
            with torch.no_grad():
                logits, _ = model(observation)
                allocation, probability, _ = greedy_action(arm, observation, logits)
            outputs.append((allocation, probability))
        assert all(allocation == outputs[0][0] for allocation, _ in outputs)
        assert all(math.isclose(probability, outputs[0][1], rel_tol=1e-5, abs_tol=1e-6)
                   for _, probability in outputs)


def test_exact_best_response_matches_reward_enumeration_on_small_roster() -> None:
    world = churn_world(1103, CAPACITY_NORMALIZED, 0, 0)
    allocation, metrics = exact_best_response(world, 0, None)
    capacities = world.capacities(0)
    observed = allocation_metrics(world.rosters[0], capacities, world.demands, allocation, None)
    assert math.isclose(float(metrics["reward"]), float(observed["reward"]), abs_tol=1e-7)
    # Exhaustive independent check is cheap at N=4.
    maximum = -1.0
    roster = tuple(sorted(world.rosters[0]))
    for code in range(4 ** len(roster)):
        roles = []
        value = code
        for _ in roster:
            roles.append(value % 4)
            value //= 4
        candidate = dict(zip(roster, reversed(roles)))
        maximum = max(maximum, float(allocation_metrics(
            roster, capacities, world.demands, candidate, None,
        )["reward"]))
    assert math.isclose(float(metrics["reward"]), maximum, rel_tol=1e-6, abs_tol=1e-6)


def test_joint_softmax_batch_has_finite_gradient() -> None:
    world = training_world(1103, 0)
    model = SetActorCritic(B_REBIND)
    order = tuple(world.rosters[0])
    observation = make_observation(world, 0, order, None)
    logits, value = model(observation)
    allocation, _, _ = greedy_action(B_REBIND, observation, logits.detach())
    action = assignment_tensor(observation, allocation)
    row = Transition(
        observation=observation, action=action, old_logprob=0.0,
        old_value=float(value.detach()), reward=0.0, episode=0, segment=0,
        decoder_base=_decoder_base(B_REBIND, observation),
    )
    logprobs, entropies = _joint_group_statistics(B_REBIND, [row], [logits])
    loss = -(logprobs[0] + 0.01 * entropies[0])
    loss.backward()
    gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
    assert gradients
    assert all(torch.isfinite(gradient).all() for gradient in gradients)


def test_analysis_keeps_joint_arm_diagnostic_and_checks_both_real_candidates() -> None:
    rows = [{
        "arms": {
            arm: {"P": 0.5, "H": 0.5, "Ogap": 0.1, "X": 0.1,
                  "capacity_normalized_N6_minus_N4": 0.0}
            for arm in LEARNED_ARMS
        }
    } for _ in range(8)]
    criteria = analyze(rows)["prespecified_support_conditions"]
    assert A_JOINT not in criteria
    assert set(criteria["additional_named_conditions"]["true_expansion_capture_by_candidate"]) == {
        A_MASS, B_REBIND,
    }


def test_replica_tolerance_uses_registered_relative_and_absolute_rule() -> None:
    base_segment = {
        "selected_probability": 0.5,
        "role_probabilities": [[0.5, 0.5]],
        "reward": 0.5,
        "assignment": [0],
    }
    within = {"segments": [dict(base_segment)]}
    close_segment = dict(base_segment)
    close_segment["selected_probability"] = 0.500005
    close_segment["reward"] = 0.500005
    close = {"segments": [close_segment]}
    deviations = _replica_deviations([within, close])
    assert deviations["probability_tolerance_violations"] == 0
    assert deviations["reward_tolerance_violations"] == 0
