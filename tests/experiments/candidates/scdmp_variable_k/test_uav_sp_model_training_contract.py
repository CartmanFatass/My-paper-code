from __future__ import annotations

import math

import pytest
import torch

from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.model import (
    ACTION_UNIFORM_DENOMINATOR,
    ACTION_UNIFORM_MAX,
    FREE_PARAMETER_COUNT,
    LEXICOGRAPHIC_ACTIONS,
    SET_PARAMETER_COUNT,
    TREAT_PARAMETER_COUNT,
    LearnedArm,
    categorical_entropy,
    chronology_q_scalar,
    initialization_requests,
    inverse_cdf_action,
    lexicographic_argmax,
    model_schema,
    parameter_schema,
    risk_vector,
    row_major_xavier_from_uniforms,
    validate_static_model_contract,
)
from experiments.candidates.scdmp_variable_k.uav_suspended_payload_order_value.training import (
    ADVANTAGE_EPSILON,
    ENTROPY_COEFFICIENT,
    GAE_LAMBDA,
    GAMMA,
    POLICY_CLIP_HIGH,
    POLICY_CLIP_LOW,
    VALUE_COEFFICIENT,
    FrozenParameterSnapshot,
    duration_correct_gae,
    joint_ppo_loss_from_terms,
    registered_minibatch_plan,
    training_contract,
)


class _TinyNamedTensorFixture:
    def __init__(self, name: str = "fixture.weight") -> None:
        self.name = name
        self.parameter = torch.nn.Parameter(torch.tensor([0.25, -0.5], dtype=torch.float32))

    def named_parameters(self):
        return ((self.name, self.parameter),)


def test_static_model_schemas_are_exact_without_parameter_materialization():
    assert validate_static_model_contract() == {
        "TREAT": 12_637,
        "FREE": 19_576,
        "SET": 19_576,
    }
    assert model_schema(LearnedArm.TREAT).parameter_count == TREAT_PARAMETER_COUNT
    assert model_schema(LearnedArm.FREE).parameter_count == FREE_PARAMETER_COUNT
    assert model_schema(LearnedArm.SET).parameter_count == SET_PARAMETER_COUNT

    treat = parameter_schema(LearnedArm.TREAT)
    free = parameter_schema(LearnedArm.FREE)
    set_free = parameter_schema(LearnedArm.SET)
    assert treat == free[: len(treat)] == set_free[: len(treat)]
    assert sum(spec.count for spec in treat if spec.name.startswith("base.")) == 6_875
    assert sum(spec.count for spec in treat if spec.name.startswith("risk.")) == 513
    assert sum(spec.count for spec in treat if spec.name.startswith("critic.")) == 5_249
    assert sum(spec.count for spec in free if spec.name.startswith("residual.")) == 6_939
    assert all(spec.initialization == "zeros" for spec in treat if spec.name.endswith("bias"))
    assert {spec.identity_stream for spec in treat} == {"paired_shared"}
    assert {
        spec.identity_stream for spec in free if spec.name.startswith("residual.")
    } == {"arm_disjoint_residual"}
    residual_outputs = {
        spec.name: spec.initialization
        for spec in free
        if spec.name.startswith("residual.layers.2")
    }
    assert residual_outputs == {
        "residual.layers.2.weight": "zeros",
        "residual.layers.2.bias": "zeros",
    }
    assert model_schema(LearnedArm.SET).chronology_law == "q_SET=0.5"


def test_initialization_addresses_freeze_shared_and_arm_disjoint_row_major_streams():
    treat = initialization_requests("TREAT")
    free = initialization_requests("FREE")
    set_free = initialization_requests("SET")
    free_shared = tuple(request for request in free if request.shared_across_arms)
    set_shared = tuple(request for request in set_free if request.shared_across_arms)
    assert treat == free_shared == set_shared
    assert all(request.arm == "SHARED" for request in treat)

    free_residual = tuple(request for request in free if not request.shared_across_arms)
    set_residual = tuple(request for request in set_free if not request.shared_across_arms)
    assert [request.tensor_group for request in free_residual] == [
        "residual.layers.0.weight",
        "residual.layers.1.weight",
    ]
    assert [request.arm for request in free_residual] == ["FREE", "FREE"]
    assert [request.arm for request in set_residual] == ["SET", "SET"]
    assert not any(request.tensor_group == "residual.layers.2.weight" for request in free)

    matrix = row_major_xavier_from_uniforms(
        (0.0, 0.25, 0.5, 0.75), fan_in=2, fan_out=2
    )
    bound = torch.tensor(math.sqrt(6.0 / 4.0), dtype=torch.float32)
    expected = ((torch.tensor([0.0, 0.25, 0.5, 0.75]) * 2.0 - 1.0) * bound).reshape(2, 2)
    assert matrix.is_contiguous()
    assert torch.equal(matrix, expected)


def test_frozen_chronology_risk_and_categorical_action_laws_are_exact():
    assert LEXICOGRAPHIC_ACTIONS == tuple(
        (u1, u2, u3) for u1 in range(3) for u2 in range(3) for u3 in range(3)
    )
    assert chronology_q_scalar("TREAT", 1.0) == 1.0
    assert chronology_q_scalar("FREE", 0.0) == 0.0
    assert chronology_q_scalar("SET", 0.0) == chronology_q_scalar("SET", 1.0) == 0.5
    with pytest.raises(ValueError, match="exactly 0 or 1"):
        chronology_q_scalar("TREAT", 0.5)

    rho = risk_vector()
    assert rho.dtype == torch.float32 and rho.shape == (27,)
    assert float(rho[0]) == 0.0
    assert float(rho[26]) == 0.75
    expected_012 = 0.75 * (1.0 / 2.0) + 0.25 * (1.0 / (4.0 / 3.0))
    assert float(rho[5]) == pytest.approx(expected_012)

    tied = torch.zeros((2, 27), dtype=torch.float32)
    assert lexicographic_argmax(tied).tolist() == [0, 0]
    upper_raw_uint24 = ACTION_UNIFORM_DENOMINATOR - 1
    upper = torch.tensor(
        upper_raw_uint24 / ACTION_UNIFORM_DENOMINATOR, dtype=torch.float32
    )
    assert upper.item() == ACTION_UNIFORM_MAX
    assert upper.item() < 1.0
    assert int((upper * ACTION_UNIFORM_DENOMINATOR).item()) == upper_raw_uint24
    sampled = inverse_cdf_action(tied, torch.stack((torch.zeros_like(upper), upper)))
    assert sampled.tolist() == [0, 26]
    with pytest.raises(ValueError, match=r"registered \[0,1\)"):
        inverse_cdf_action(tied[:1], torch.ones(1, dtype=torch.float32))
    with pytest.raises(ValueError, match="exact uint24"):
        inverse_cdf_action(
            tied[:1], torch.tensor([1.0 / (1 << 25)], dtype=torch.float32)
        )
    assert categorical_entropy(tied) == pytest.approx(
        torch.full((2,), math.log(27.0), dtype=torch.float32)
    )


def test_duration_correct_gae_uses_primitive_discount_and_one_population_normalization():
    gamma = GAMMA
    trace = GAMMA * GAE_LAMBDA
    old = torch.tensor([0.5, 0.25, 0.1], dtype=torch.float32)
    targets = duration_correct_gae(
        primitive_rewards=((1.0, 2.0), (3.0,), (-1.0, 0.5)),
        old_values=old,
        nonterminal=torch.tensor([True, False, False], dtype=torch.bool),
        slot_offsets=(0, 2, 3),
    )

    rbar0 = 1.0 + gamma * 2.0
    rbar1 = 3.0
    rbar2 = -1.0 + gamma * 0.5
    delta0 = rbar0 + gamma**2 * 0.25 - 0.5
    delta1 = rbar1 - 0.25
    delta2 = rbar2 - 0.1
    raw1 = delta1
    raw0 = delta0 + trace**2 * raw1
    raw2 = delta2
    expected_raw = torch.tensor([raw0, raw1, raw2], dtype=torch.float32)

    assert targets.discounted_rewards == pytest.approx(
        torch.tensor([rbar0, rbar1, rbar2], dtype=torch.float32)
    )
    assert targets.deltas == pytest.approx(
        torch.tensor([delta0, delta1, delta2], dtype=torch.float32)
    )
    assert targets.raw_advantages == pytest.approx(expected_raw)
    assert targets.value_targets == pytest.approx(expected_raw + old)
    expected_normalized = (expected_raw - expected_raw.mean()) / torch.sqrt(
        ((expected_raw - expected_raw.mean()) ** 2).mean() + ADVANTAGE_EPSILON
    )
    assert targets.normalized_advantages == pytest.approx(expected_normalized)
    assert all(not tensor.requires_grad for tensor in targets.__dict__.values())


def test_old_parameter_snapshot_rejects_stale_and_cross_wired_live_parameters():
    fixture = _TinyNamedTensorFixture()
    snapshot = FrozenParameterSnapshot.from_model(fixture)  # synthetic two-scalar fixture
    snapshot.require_exact_current_model(fixture)

    with torch.no_grad():
        fixture.parameter[0].add_(1.0)
    with pytest.raises(RuntimeError, match="stale or cross-wired"):
        snapshot.require_exact_current_model(fixture)

    cross_wired = _TinyNamedTensorFixture(name="other.weight")
    with pytest.raises(RuntimeError, match="names do not match"):
        snapshot.require_exact_current_model(cross_wired)


class _InjectedPermutationSource:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str, int, int, int]] = []

    def permutation_indices(self, *, replicate, arm, update, epoch, count):
        self.calls.append((replicate, arm, update, epoch, count))
        values = tuple(range(count))
        shift = epoch % count
        return values[shift:] + values[:shift]


def test_injected_seed_update_epoch_plan_is_exact_and_near_equal():
    source = _InjectedPermutationSource()
    plans = registered_minibatch_plan(
        source,
        replicate=7,
        arm="FREE",
        update=19,
        count=7,
    )
    assert source.calls == [(7, "FREE", 19, epoch, 7) for epoch in range(1, 5)]
    assert len(plans) == 4
    assert sum(len(plan.minibatches) for plan in plans) == 16
    for plan in plans:
        assert sorted(plan.permutation) == list(range(7))
        assert tuple(map(len, plan.minibatches)) == (2, 2, 2, 1)
        assert tuple(index for batch in plan.minibatches for index in batch) == plan.permutation


def test_joint_ppo_loss_is_the_only_frozen_clipped_value_entropy_expression():
    current_logp = torch.log(torch.tensor([1.30, 0.70], dtype=torch.float32))
    old_logp = torch.zeros(2, dtype=torch.float32)
    advantage = torch.tensor([2.0, -3.0], dtype=torch.float32)
    current_value = torch.tensor([1.5, -0.5], dtype=torch.float32)
    target = torch.tensor([1.0, 0.25], dtype=torch.float32)
    entropy = torch.tensor([0.4, 0.6], dtype=torch.float32)

    loss = joint_ppo_loss_from_terms(
        current_logp=current_logp,
        current_value=current_value,
        current_entropy=entropy,
        old_logp=old_logp,
        value_target=target,
        normalized_advantage=advantage,
    )
    ratio = torch.exp(current_logp)
    policy = -torch.minimum(
        ratio * advantage,
        torch.clamp(ratio, POLICY_CLIP_LOW, POLICY_CLIP_HIGH) * advantage,
    ).mean()
    value = 0.5 * ((current_value - target) ** 2).mean()
    entropy_mean = entropy.mean()
    expected_total = policy + VALUE_COEFFICIENT * value - ENTROPY_COEFFICIENT * entropy_mean
    assert loss.policy == pytest.approx(policy)
    assert loss.value == pytest.approx(value)
    assert loss.entropy == pytest.approx(entropy_mean)
    assert loss.total == pytest.approx(expected_total)


def test_static_trainer_contract_freezes_optimizer_steps_and_excludes_menus():
    contract = training_contract()
    assert contract["gamma"] == 0.996
    assert contract["gae_lambda"] == 0.94
    assert contract["policy_clip"] == (0.82, 1.18)
    assert contract["epochs_per_update"] == contract["minibatches_per_epoch"] == 4
    assert contract["optimizer_steps_per_update"] == 16
    assert contract["optimizer_steps_per_arm"] == 2_304
    assert contract["optimizer"] == {
        "name": "single_persistent_all_parameter_AdamW",
        "lr": 2.5e-4,
        "betas": (0.9, 0.999),
        "epsilon": 1e-8,
        "weight_decay": 2e-5,
        "decay_applies_to": "all_matrices_and_biases",
        "amsgrad": False,
        "maximize": False,
        "globally_one_based_steps": (1, 2_304),
    }
    assert {"trainer_menu", "early_stop", "running_normalization", "per_k_head"}.issubset(
        set(contract["forbidden"])
    )
