from __future__ import annotations

import copy

import pytest

from experiments.candidates.variable_n_fleet_churn_r02.contract import (
    BETA1,
    BETA2,
    ContractViolation,
    LR,
    WEIGHT_DECAY,
)
from experiments.candidates.variable_n_fleet_churn_r02.optimizer import (
    AdamWState,
    GradientTensor,
    ParameterTensor,
    adamw_step,
    clip_raw_gradients,
    initialize_adamw,
)
from experiments.candidates.variable_n_fleet_churn_r02.scalar import binary64_bits, rn64


class ExactTestSqrt:
    def sigmoid_R02(self, value: float) -> float:
        raise AssertionError

    def exp_R02(self, value: float) -> float:
        raise AssertionError

    def log_R02(self, value: float) -> float:
        raise AssertionError

    def sqrt_R02(self, value: float) -> float:
        table = {0.0: 0.0, 25.0: 5.0, 0.0009: 0.03, 0.0016: 0.04}
        if value in table:
            return table[value]
        return value**0.5


KERNEL = ExactTestSqrt()


def _parameters() -> tuple[ParameterTensor, ...]:
    return (
        ParameterTensor("a.bias", (1,), (1.0,)),
        ParameterTensor("b.weight", (1, 1), (1.0,)),
    )


def test_global_raw_gradient_clipping_uses_ascii_name_c_order() -> None:
    gradients = (
        GradientTensor("a.bias", (1,), (3.0,)),
        GradientTensor("b.weight", (1, 1), (4.0,)),
    )
    clipped = clip_raw_gradients(_parameters(), gradients, KERNEL)
    assert clipped.raw_norm == 5.0
    assert clipped.multiplier == 0.1
    assert clipped.gradients[0].values == (rn64(3.0 * 0.1),)
    assert clipped.gradients[1].values == (rn64(4.0 * 0.1),)


def test_zero_gradient_step_has_exact_power_and_rank_based_decay_bits() -> None:
    parameters = _parameters()
    gradients = (
        GradientTensor("a.bias", (1,), (0.0,)),
        GradientTensor("b.weight", (1, 1), (0.0,)),
    )
    result = adamw_step(parameters, gradients, initialize_adamw(parameters), KERNEL)
    assert result.state.step == 1
    assert binary64_bits(result.state.beta1_power) == binary64_bits(BETA1)
    assert binary64_bits(result.state.beta2_power) == binary64_bits(BETA2)
    assert binary64_bits(result.parameters[0].values[0]) == binary64_bits(1.0)
    expected_decay = rn64(1.0 - rn64(LR * WEIGHT_DECAY))
    assert binary64_bits(result.parameters[1].values[0]) == binary64_bits(expected_decay)
    assert result.state.tensors[0].m == result.state.tensors[0].v == (0.0,)


def test_cloned_one_step_results_and_serialized_state_are_bit_equal() -> None:
    parameters = _parameters()
    gradients = (
        GradientTensor("a.bias", (1,), (0.25,)),
        GradientTensor("b.weight", (1, 1), (-0.125,)),
    )
    initial = initialize_adamw(parameters)
    first = adamw_step(parameters, gradients, initial, KERNEL)
    second = adamw_step(parameters, gradients, initial, KERNEL)
    assert first == second
    restored = AdamWState.from_dict(copy.deepcopy(first.state.to_dict()))
    assert restored == first.state
    assert [binary64_bits(value) for value in first.parameters[0].values] == [
        binary64_bits(value) for value in second.parameters[0].values
    ]


def test_state_power_name_shape_order_and_nonfinite_tampering_fail_closed() -> None:
    state_dict = initialize_adamw(_parameters()).to_dict()

    bad_power = copy.deepcopy(state_dict)
    bad_power["beta1_power"] = 0.5
    with pytest.raises(ContractViolation):
        AdamWState.from_dict(bad_power)

    bad_order = copy.deepcopy(state_dict)
    bad_order["tensors"].reverse()
    with pytest.raises(ContractViolation):
        AdamWState.from_dict(bad_order)

    bad_shape = copy.deepcopy(state_dict)
    bad_shape["tensors"][0]["shape"] = [2]
    with pytest.raises(ContractViolation):
        AdamWState.from_dict(bad_shape)

    bad_nan = copy.deepcopy(state_dict)
    bad_nan["tensors"][0]["m"][0] = float("nan")
    with pytest.raises(ContractViolation):
        AdamWState.from_dict(bad_nan)

    bad_name_type = copy.deepcopy(state_dict)
    bad_name_type["tensors"][0]["name"] = 7
    with pytest.raises(ContractViolation):
        AdamWState.from_dict(bad_name_type)


def test_parameter_and_gradient_order_drift_fails_closed() -> None:
    parameters = tuple(reversed(_parameters()))
    gradients = (
        GradientTensor("a.bias", (1,), (0.0,)),
        GradientTensor("b.weight", (1, 1), (0.0,)),
    )
    with pytest.raises(ContractViolation):
        initialize_adamw(parameters)
    with pytest.raises(ContractViolation):
        clip_raw_gradients(_parameters(), tuple(reversed(gradients)), KERNEL)
