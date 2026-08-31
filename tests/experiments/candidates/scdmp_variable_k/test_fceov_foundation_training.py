from __future__ import annotations

import inspect
import math

import pytest
import torch

from experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value import (
    foundation,
    rng as fceov_rng,
    training,
)


class MidpointUniforms:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str, str, int]] = []

    def initialization_uniforms(
        self, *, replicate: int, arm: str, tensor_name: str, count: int
    ) -> tuple[float, ...]:
        self.calls.append((replicate, arm, tensor_name, count))
        return (0.5,) * count


def test_foundation_is_one_fresh_order_erased_actor_critic_with_registered_structure():
    source = MidpointUniforms()
    model = foundation.FoundationActorCritic(source)

    assert [(layer.in_features, layer.out_features) for layer in model.actor.layers] == [
        (18, 96),
        (96, 96),
        (96, 18),
    ]
    assert [(layer.in_features, layer.out_features) for layer in model.critic.layers] == [
        (18, 96),
        (96, 96),
        (96, 1),
    ]
    assert sum(parameter.numel() for parameter in model.actor.parameters()) == 12_882
    assert sum(parameter.numel() for parameter in model.critic.parameters()) == 11_233
    assert all(parameter.dtype == torch.float32 for parameter in model.parameters())
    assert {call[0] for call in source.calls} == {0}
    assert {call[1] for call in source.calls} == {"FOUNDATION"}

    constructor = inspect.signature(foundation.FoundationActorCritic).parameters
    assert tuple(constructor) == ("initialization_source",)
    assert not {"q", "graph", "order", "token", "assignment", "permit", "approval"} & set(
        constructor
    )


def test_injected_row_major_xavier_is_exact_and_materialization_does_not_touch_torch_rng():
    class RowMajorUniforms:
        def initialization_uniforms(self, *, replicate, arm, tensor_name, count):
            return tuple(index / count for index in range(count))

    rng_before = torch.random.get_rng_state().clone()
    model = foundation.FoundationActorCritic(RowMajorUniforms())
    assert torch.equal(torch.random.get_rng_state(), rng_before)

    layer = model.actor.layers[0]
    count = 18 * 96
    bound = math.sqrt(6.0 / (18 + 96))
    assert float(layer.weight[0, 0]) == pytest.approx(-bound, abs=2e-8)
    assert float(layer.weight[0, 1]) == pytest.approx((2.0 / count - 1.0) * bound, abs=2e-8)
    assert float(layer.weight[1, 0]) == pytest.approx((2.0 * 18 / count - 1.0) * bound, abs=2e-8)
    assert torch.count_nonzero(layer.bias).item() == 0


def test_foundation_lexicographic_argmax_and_direct_freeze_are_immutable():
    model = foundation.FoundationActorCritic(MidpointUniforms())
    logits = torch.full((2, 18), -1.0, dtype=torch.float32)
    logits[0, (4, 9)] = 3.0
    logits[1, (0, 17)] = 2.0
    assert foundation.lexicographic_argmax(logits).tolist() == [4, 0]

    frozen = foundation.freeze_foundation(model)
    before = foundation.direct_tensor_state(frozen.actor)
    assert all(parameter.requires_grad is False for parameter in frozen.actor.parameters())
    frozen.validate_immutable()

    with torch.no_grad():
        next(frozen.actor.parameters()).view(-1)[0] += 1.0
    with pytest.raises(foundation.FoundationContractError, match="changed"):
        frozen.validate_immutable()
    assert foundation.direct_tensor_state(frozen.actor) != before


def test_product_initial_state_transform_is_exact_and_has_no_graph_or_disturbance_input():
    assert tuple(inspect.signature(training.initial_public_draws).parameters) == ("uniforms",)
    assert training.initial_public_draws((0.0, 0.0, 0.0)) == (0.0, -0.01, -0.01)
    assert training.initial_public_draws((0.5, 0.5, 0.5)) == (0.015, 0.0, 0.0)
    assert training.initial_public_draws((0.25, 0.75, 0.125)) == pytest.approx(
        (0.0075, 0.005, -0.0075)
    )
    with pytest.raises(training.TrainingContractError):
        training.initial_public_draws((0.5, 0.5))


def test_training_plan_is_160_by_12_fixed_13_and_balanced_without_running_training():
    plan = training.build_training_plan()

    assert len(plan) == 160 * 12 == 1_920
    assert {row.update for row in plan} == set(range(1, 161))
    assert {row.k for row in plan} == {13}
    for update in range(1, 161):
        rows = [row for row in plan if row.update == update]
        assert [row.episode for row in rows] == list(range(12))
        assert sum(row.graph == "HR" and row.q == 1 for row in rows) == 6
        assert sum(row.graph == "RH" and row.q == 0 for row in rows) == 6


def test_training_rng_addresses_pair_only_state_and_disturbance_and_use_uniform24_actions():
    plan = training.build_training_plan()
    report = training.validate_training_rng_contract()
    assert report == {
        "paired_initial_state_prefixes": 160 * 6,
        "paired_disturbance_prefixes": 160 * 6,
        "episode_action_prefixes": 160 * 12,
        "domains": 8,
    }
    source = fceov_rng.TestAddressRNG(bytes(range(32)))
    hr, rh = plan[0], plan[1]
    assert hr.initialization_address == rh.initialization_address
    assert hr.disturbance_address_prefix == rh.disturbance_address_prefix
    assert hr.action_address(0) != rh.action_address(0)
    assert training.training_initial_draws(source, hr) == training.training_initial_draws(source, rh)
    assert training.training_disturbance(
        source, hr, tick=0, component="eta_v"
    ) == training.training_disturbance(source, rh, tick=0, component="eta_v")
    assert fceov_rng.MAX_UNIFORM24 == 1.0 - 2.0**-24
    assert float(torch.tensor(fceov_rng.MAX_UNIFORM24, dtype=torch.float32)) < 1.0
    uniforms = tuple(training.training_action_uniform(source, row, renewal=0) for row in (hr, rh))
    assert all(0.0 <= value <= fceov_rng.MAX_UNIFORM24 for value in uniforms)
    actions = training.sample_training_actions(
        torch.zeros((2, 18), dtype=torch.float32), source, (hr, rh), (0, 0)
    )
    assert actions.dtype == torch.int64 and actions.shape == (2,)


def test_registered_resource_maxima_include_only_one_checkpoint_and_query_decomposition():
    assert training.summarize_resource_usage() == {
        "episodes_rollouts": 2_184,
        "primitive_slots": 794_976,
        "adamw_steps": 1_920,
        "checkpoints": 1,
        "forced_actions": 144,
        "foundation_queries": 61_008,
    }
    assert 794_976 == (1_920 + 120 + 144) * 364
    assert 61_008 == 1_920 * 28 + 120 * 28 + 144 * 27


def test_duration_correct_gae_keeps_complete_episodes_separate_and_validates_offsets():
    rewards = tuple((float(index + 1),) for index in range(24))
    old_values = torch.zeros(24, dtype=torch.float32)
    nonterminal = torch.tensor((True, False) * 12, dtype=torch.bool)
    delimiters = tuple(range(0, 25, 2))
    separated = training.duration_correct_gae(
        rewards,
        old_values,
        nonterminal,
        episode_offsets=delimiters,
    )
    changed_rewards = list(rewards)
    changed_rewards[4:6] = ((-7.0,), (-9.0,))
    changed_second = training.duration_correct_gae(
        changed_rewards,
        old_values,
        nonterminal,
        episode_offsets=delimiters,
    )
    assert torch.equal(separated.raw_advantages[:4], changed_second.raw_advantages[:4])

    with pytest.raises(TypeError):
        training.duration_correct_gae(rewards, old_values, nonterminal)  # type: ignore[call-arg]

    for offsets in (delimiters[:-1], (0,) + delimiters[2:], (0, 1, *delimiters[2:-1], 23)):
        with pytest.raises(training.TrainingContractError, match="episode offsets"):
            training.duration_correct_gae(
                rewards,
                old_values,
                nonterminal,
                episode_offsets=offsets,
            )
    with pytest.raises(training.TrainingContractError, match="end"):
        training.duration_correct_gae(rewards, old_values, torch.ones(24, dtype=torch.bool), episode_offsets=delimiters)
    early_terminal = nonterminal.clone()
    early_terminal[0] = False
    with pytest.raises(training.TrainingContractError, match="final record"):
        training.duration_correct_gae(rewards, old_values, early_terminal, episode_offsets=delimiters)
    with pytest.raises(training.TrainingContractError, match="finite"):
        training.duration_correct_gae(
            rewards,
            torch.tensor((0.0, float("nan"), *(0.0,) * 22), dtype=torch.float32),
            nonterminal,
            episode_offsets=delimiters,
        )


def test_duration_13_bootstrap_uses_legacy_python_power_then_float32_rounding():
    rewards = tuple((0.0,) * 13 for _ in range(24))
    old_values = torch.linspace(0.1, 2.4, 24, dtype=torch.float32)
    nonterminal = torch.tensor([value for _ in range(12) for value in (True, False)])
    delimiters = tuple(range(0, 25, 2))
    observed = training.duration_correct_gae(
        rewards, old_values, nonterminal, episode_offsets=delimiters
    )
    expected = (
        torch.tensor(0.0, dtype=torch.float32)
        + torch.tensor(1.0, dtype=torch.float32) * (training.GAMMA**13) * old_values[1]
        - old_values[0]
    )
    assert torch.equal(observed.deltas[0], expected)
    with pytest.raises(training.TrainingContractError, match="detached"):
        training.duration_correct_gae(
            rewards,
            torch.zeros(24, dtype=torch.float32, requires_grad=True),
            nonterminal,
            episode_offsets=delimiters,
        )


def test_training_action_sampling_uses_strict_inverse_cdf_boundary_semantics():
    probabilities = torch.zeros((3, 18), dtype=torch.float32)
    probabilities[:, :3] = torch.tensor((0.25, 0.25, 0.5), dtype=torch.float32)
    uniforms = torch.tensor((0.0, 0.25, 0.5), dtype=torch.float32)
    assert training.strict_inverse_cdf(probabilities, uniforms).tolist() == [0, 1, 2]
    logits = torch.zeros((2, 18), dtype=torch.float32)
    assert training.sample_actions_from_logits(
        logits, torch.zeros(2, dtype=torch.float32)
    ).tolist() == [0, 0]


def test_epoch_keyed_minibatches_use_three_distinct_addressed_permutations():
    class PermutationSource:
        def __init__(self):
            self.calls = []

        def permutation(self, count, *, domain, address):
            self.calls.append((count, domain, address))
            shift = address[1]
            return tuple((*range(shift, count), *range(shift)))

    source = PermutationSource()
    batches = training.epoch_keyed_minibatches(source, update=17, record_count=8)
    assert source.calls == [
        (8, "foundation-minibatch", (17, 0)),
        (8, "foundation-minibatch", (17, 1)),
        (8, "foundation-minibatch", (17, 2)),
    ]
    assert len(batches) == 3 and all(len(epoch) == 4 for epoch in batches)


def test_empty_ppo_nonfinite_gradient_and_nonfinite_or_nonscalar_resume_state_reject():
    empty = torch.empty(0, dtype=torch.float32)
    with pytest.raises(training.TrainingContractError, match="PPO"):
        training.joint_ppo_loss(
            current_log_probability=empty,
            current_value=empty,
            current_entropy=empty,
            old_log_probability=empty,
            value_target=empty,
            normalized_advantage=empty,
        )

    parameter = torch.tensor((1.0,), dtype=torch.float32, requires_grad=True)
    parameter.grad = torch.tensor((float("nan"),), dtype=torch.float32)
    with pytest.raises(training.TrainingContractError, match="nonfinite"):
        training.clip_global_gradient((parameter,))

    optimizer = training.ExactAdamW((("parameter", parameter.detach().clone()),))
    snapshot = optimizer.snapshot()
    bad_moment = training.OptimizerSnapshot(
        snapshot.step,
        snapshot.names,
        (torch.tensor((float("inf"),), dtype=torch.float32),),
        snapshot.second,
    )
    with pytest.raises(training.TrainingContractError, match="moment"):
        optimizer.restore(bad_moment)
    for invalid_step in (True, 0.0):
        with pytest.raises(training.TrainingContractError, match="resume structure"):
            optimizer.restore(
                training.OptimizerSnapshot(
                    invalid_step,  # type: ignore[arg-type]
                    snapshot.names,
                    snapshot.first,
                    snapshot.second,
                )
            )


def test_late_bad_gradient_or_restore_moment_causes_no_partial_optimizer_mutation():
    first = torch.tensor((1.0,), dtype=torch.float32, requires_grad=True)
    second = torch.tensor((2.0,), dtype=torch.float32, requires_grad=True)
    optimizer = training.ExactAdamW((("first", first), ("second", second)))
    first.grad = torch.tensor((1.0,), dtype=torch.float32)
    second.grad = torch.tensor((float("nan"),), dtype=torch.float32)
    before_parameters = (first.detach().clone(), second.detach().clone())
    before_state = optimizer.snapshot()
    with pytest.raises(training.TrainingContractError, match="nonfinite"):
        optimizer.step()
    assert torch.equal(first, before_parameters[0]) and torch.equal(second, before_parameters[1])
    after_failed_step = optimizer.snapshot()
    assert all(torch.equal(left, right) for left, right in zip(before_state.first, after_failed_step.first))
    assert all(torch.equal(left, right) for left, right in zip(before_state.second, after_failed_step.second))

    bad_restore = training.OptimizerSnapshot(
        0,
        before_state.names,
        (torch.ones_like(first), torch.tensor((float("inf"),), dtype=torch.float32)),
        before_state.second,
    )
    with pytest.raises(training.TrainingContractError, match="moment"):
        optimizer.restore(bad_restore)
    after_failed_restore = optimizer.snapshot()
    assert all(torch.equal(left, right) for left, right in zip(before_state.first, after_failed_restore.first))
    assert all(torch.equal(left, right) for left, right in zip(before_state.second, after_failed_restore.second))


def test_adamw_atomic_candidates_preserve_legacy_in_place_float32_operation_order():
    parameter = torch.tensor((1.0000001, -0.33333334), dtype=torch.float32, requires_grad=True)
    gradient = torch.tensor((0.12345679, -0.7654321), dtype=torch.float32)
    parameter.grad = gradient.clone()
    optimizer = training.ExactAdamW((("parameter", parameter),))

    expected_first = torch.zeros_like(parameter)
    expected_first.mul_(training.ADAMW_BETA1).add_(
        gradient, alpha=1.0 - training.ADAMW_BETA1
    )
    expected_second = torch.zeros_like(parameter)
    expected_second.mul_(training.ADAMW_BETA2).addcmul_(
        gradient, gradient, value=1.0 - training.ADAMW_BETA2
    )
    old = parameter.detach().clone()
    expected_parameter = old - training.ADAMW_LR * (
        expected_first / (1.0 - training.ADAMW_BETA1)
        / (torch.sqrt(expected_second / (1.0 - training.ADAMW_BETA2)) + training.ADAMW_EPSILON)
        + training.ADAMW_WEIGHT_DECAY * old
    )

    optimizer.step()
    snapshot = optimizer.snapshot()
    assert torch.equal(snapshot.first[0], expected_first)
    assert torch.equal(snapshot.second[0], expected_second)
    assert torch.equal(parameter, expected_parameter)
