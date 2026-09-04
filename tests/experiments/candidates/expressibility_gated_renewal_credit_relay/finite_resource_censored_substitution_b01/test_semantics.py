from __future__ import annotations

import math

import torch

from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01 import config as C
from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01.environment import exact_q, generate_evaluation, generate_training, make_episode
from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01.experiment import greedy_action, initial_vector
from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01.models import AssociationFactor, GenericPair
from experiments.candidates.expressibility_gated_renewal_credit_relay.finite_resource_censored_substitution_b01.rng import cyclic_minibatches


def test_three_transition_host_preserves_provenance_and_changes_replacement_carrier() -> None:
    episode = make_episode(source=0, content=1, action=1, mode="REPLACE")
    assert episode.clockwise_waiter == 1
    assert episode.counterclockwise_waiter == 3
    assert episode.selected_waiter == 1
    assert episode.replacement_carrier == 2
    assert episode.final_carrier == 2
    eligible_waiters = {episode.clockwise_waiter, episode.counterclockwise_waiter}
    unselected_waiter = (eligible_waiters - {episode.selected_waiter}).pop()
    assert episode.replacement_carrier not in eligible_waiters
    assert episode.replacement_carrier != unselected_waiter
    assert episode.replacement_carrier not in {episode.source, episode.selected_waiter}
    assert len(episode.transitions) == 3
    assert [transition.step for transition in episode.transitions] == [1, 2, 3]
    assert {transition.provenance_relation for transition in episode.transitions} == {1}
    assert episode.utility == 1
    expired = make_episode(source=0, content=1, action=1, mode="EXPIRE")
    assert expired.final_carrier is None
    assert expired.utility == 0


def test_exact_q_is_two_thirds_only_for_matching_relation() -> None:
    for source in C.SOURCES:
        for content in C.CONTENTS:
            for action in C.ACTIONS:
                observed = sum(
                    make_episode(source, content, action, mode).utility for mode in C.MODES
                ) / len(C.MODES)
                expected = 2.0 / 3.0 if action == content else 0.0
                assert exact_q(source, content, action) == expected
                assert observed == expected


def test_counter_coordinates_and_cyclic_minibatches_are_shared_and_stable() -> None:
    first = generate_training(17, 32)
    second = generate_training(17, 32)
    assert first == second
    assert generate_evaluation(17, 32) == generate_evaluation(17, 32)
    batches = cyclic_minibatches(17, C.RNG_NAMESPACES["minibatch_permutation"], 7, 4, 5)
    assert batches == cyclic_minibatches(17, C.RNG_NAMESPACES["minibatch_permutation"], 7, 4, 5)
    assert len(batches) == 4
    assert all(len(batch) == 5 for batch in batches)
    flattened = [index for batch in batches for index in batch]
    assert flattened[:7] == flattened[7:14]


def test_models_share_flat_initial_bytes_but_use_distinct_frozen_mapping() -> None:
    initial = initial_vector(23)
    generic = GenericPair(initial)
    factor = AssociationFactor(initial)
    assert generic.theta.numel() == factor.theta.numel() == 32
    assert generic.theta.detach().numpy().tobytes() == factor.theta.detach().numpy().tobytes()
    assert generic.layout != factor.layout
    assert [entry["shape"] for entry in generic.layout] == [[4, 2, 2], [4, 2, 2]]
    assert [entry["shape"] for entry in factor.layout] == [
        [4, 2], [2, 2], [4, 2], [2, 2], [4], [2], [2]
    ]


def test_model_equations_use_the_documented_flat_order() -> None:
    initial = torch.arange(32, dtype=torch.float32) / 10.0
    source = torch.tensor([2])
    content = torch.tensor([-1])
    action = torch.tensor([1])
    generic = GenericPair(initial)
    factor = AssociationFactor(initial)
    assert generic(source, content, action).item() == torch.tensor((9.0 + 25.0) / 20.0).item()
    u1, v1, u2, v2 = 5.0 / 10.0, 9.0 / 10.0, 17.0 / 10.0, 21.0 / 10.0
    expected = 0.5 * (u1 * v1 + u2 * v2) + 26.0 / 10.0 + 28.0 / 10.0 + 31.0 / 10.0
    assert math.isclose(factor(source, content, action).item(), expected, rel_tol=0.0, abs_tol=1e-6)


def test_temperature_one_tie_rule_is_shared_and_stable() -> None:
    assert greedy_action(0.0, 0.0) == -1
    assert greedy_action(0.0, 1.0) == 1
    assert greedy_action(1.0, 0.0) == -1
