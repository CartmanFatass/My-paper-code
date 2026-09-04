from __future__ import annotations

import pytest

from experiments.candidates.variable_n_fleet_churn_r02.autodiff import (
    AutodiffError,
    ScalarTape,
)
from experiments.candidates.variable_n_fleet_churn_r02.optimizer import ParameterTensor
from experiments.candidates.variable_n_fleet_churn_r02.probability import (
    clamp_centered_max_adjoint,
    construct_probability,
)
from experiments.candidates.variable_n_fleet_churn_r02.scalar import binary64_bits, rn64


class FrozenTestKernel:
    def __init__(self) -> None:
        self.log_calls = 0

    def sigmoid_R02(self, value: float) -> float:
        return {-2.0: 0.25, 0.0: 0.5}[value]

    def exp_R02(self, value: float) -> float:
        return {0.0: 1.0, -1.0: 0.5, -16.0: 2.0**-16}[value]

    def log_R02(self, value: float) -> float:
        self.log_calls += 1
        return rn64(value - 1.0)

    def sqrt_R02(self, value: float) -> float:
        return {0.25: 0.5, 1.0: 1.0}[value]


def test_repeated_leaf_and_silu_keep_distinct_ordered_contributions() -> None:
    kernel = FrozenTestKernel()
    tape = ScalarTape(kernel)
    x = tape.leaf("tensor/x/0", -2.0)
    squared = tape.mul(x, x, "loss/square")
    silu = tape.silu(x, "loss/silu")
    total = tape.add(squared, silu, "loss/total")
    result = tape.backward(total)

    direct = rn64(1.0 * 0.25)
    to_s = rn64(1.0 * -2.0)
    sigmoid_local = rn64(0.25 * rn64(1.0 - 0.25))
    sigmoid_path = rn64(to_s * sigmoid_local)
    silu_gradient = rn64(rn64(0.0 + direct) + sigmoid_path)
    square_slot_zero = rn64(1.0 * -2.0)
    square_slot_one = rn64(1.0 * -2.0)
    square_gradient = rn64(rn64(0.0 + square_slot_zero) + square_slot_one)
    expected = rn64(rn64(0.0 + silu_gradient) + square_gradient)
    assert binary64_bits(result.gradient(x)) == binary64_bits(expected)
    assert result.node_table[1].parent_node_ids_in_operand_slot_order == (0, 0)
    assert tuple(record.node_id for record in result.node_table) == tuple(range(len(result.node_table)))


def test_division_uses_declared_yy_gx_qy_association() -> None:
    tape = ScalarTape(FrozenTestKernel())
    x = tape.leaf("tensor/a/0", 3.0)
    y = tape.leaf("tensor/b/0", 2.0)
    total = tape.div(x, y, "loss/div")
    result = tape.backward(total)
    expected_x = rn64(1.0 / 2.0)
    yy = rn64(2.0 * 2.0)
    gx = rn64(1.0 * 3.0)
    expected_y = rn64(-rn64(gx / yy))
    assert binary64_bits(result.gradient(x)) == binary64_bits(expected_x)
    assert binary64_bits(result.gradient(y)) == binary64_bits(expected_y)


def test_affine_reverse_decreasing_j_k_and_ascii_c_order_extraction() -> None:
    parameters = (
        ParameterTensor("a.bias", (2,), (0.0, 0.0)),
        ParameterTensor("b.weight", (2, 2), (1.0, 2.0, 3.0, 4.0)),
    )
    tape = ScalarTape(FrozenTestKernel())
    leaves = tape.register_parameters(parameters)
    two = tape.constant("constant/2", 2.0)
    x0 = tape.leaf("tensor/input/0", 5.0)
    x1 = tape.leaf("tensor/input/1", 7.0)
    weights = (leaves["b.weight"][:2], leaves["b.weight"][2:])
    outputs = tape.affine((x0, x1), weights, leaves["a.bias"], "model/affine")
    twice_second = tape.mul(two, outputs[1], "loss/twice_second")
    total = tape.add(outputs[0], twice_second, "loss/total")
    result = tape.backward(total)

    assert tuple(gradient.name for gradient in result.parameter_gradients) == ("a.bias", "b.weight")
    assert result.parameter_gradients[0].values == (1.0, 2.0)
    assert result.parameter_gradients[1].values == (5.0, 7.0, 10.0, 14.0)
    # Shared input contributions arrive from j=1 before j=0.
    expected_x0 = rn64(rn64(0.0 + rn64(2.0 * 3.0)) + rn64(1.0 * 1.0))
    expected_x1 = rn64(rn64(0.0 + rn64(2.0 * 4.0)) + rn64(1.0 * 2.0))
    assert result.gradient(x0) == expected_x0
    assert result.gradient(x1) == expected_x1


def test_two_output_affine_silu_sum_uses_interleaved_layer_builder() -> None:
    tape = ScalarTape(FrozenTestKernel())
    bias0 = tape.constant("constant/bias/0", 0.0)
    bias1 = tape.constant("constant/bias/1", 0.0)
    weight0 = tape.constant("constant/weight/0", 2.0)
    weight1 = tape.constant("constant/weight/1", 3.0)
    x = tape.leaf("tensor/input/0", 0.0)
    outputs = tape.affine_with_output_callback(
        (x,),
        ((weight0,), (weight1,)),
        (bias0, bias1),
        "model/layer",
        lambda output, j: tape.silu(output, f"model/layer/j{j}/silu"),
    )
    total = tape.add(outputs[0], outputs[1], "loss/total")
    result = tape.backward(total)
    assert result.gradient(x) == rn64(rn64(0.5 * 3.0) + rn64(0.5 * 2.0))
    primitives = tuple(record.primitive for record in result.node_table)
    first_sigmoid = primitives.index("sigmoid")
    second_output_first_product = next(
        record.node_id
        for record in result.node_table
        if record.semantic_path == "model/layer/j1/k0/product"
    )
    assert first_sigmoid < second_output_first_product


def test_stacked_dense_silu_graph_compiles_provisional_handles_to_dfs_ids() -> None:
    tape = ScalarTape(FrozenTestKernel())
    constants = {
        name: tape.constant(f"constant/{name}", value)
        for name, value in (
            ("b0", 0.0),
            ("b1", 0.0),
            ("four", 4.0),
            ("one", 1.0),
            ("three", 3.0),
            ("two", 2.0),
        )
    }
    x0 = tape.leaf("tensor/input/0", 0.0)
    x1 = tape.leaf("tensor/input/1", 0.0)
    weights = (
        (constants["one"], constants["two"]),
        (constants["three"], constants["four"]),
    )
    first_affine = tape.affine(
        (x0, x1), weights, (constants["b0"], constants["b1"]), "model/layer0"
    )
    first_hidden = tuple(
        tape.silu(value, f"model/layer0/silu/{j}")
        for j, value in enumerate(first_affine)
    )
    second_affine = tape.affine(
        first_hidden, weights, (constants["b0"], constants["b1"]), "model/layer1"
    )
    second_hidden = tuple(
        tape.silu(value, f"model/layer1/silu/{j}")
        for j, value in enumerate(second_affine)
    )
    total = tape.affine(
        second_hidden,
        ((constants["one"], constants["one"]),),
        (constants["b0"],),
        "model/out",
    )[0]
    result = tape.backward(total)

    assert result.gradient(x0) == 5.5
    assert result.gradient(x1) == 8.0
    assert all(
        parent < record.node_id
        for record in result.node_table
        for parent in record.parent_node_ids_in_operand_slot_order
    )
    assert result.construction_to_node_id != tuple(range(len(result.node_table)))
    primitive_ids = tuple(
        record.node_id
        for record in result.node_table
        if record.primitive not in {"leaf", "constant"}
    )
    assert primitive_ids == tuple(range(primitive_ids[0], len(result.node_table)))


def test_shared_fanout_uses_decreasing_compiled_consumer_ids() -> None:
    tape = ScalarTape(FrozenTestKernel())
    two = tape.constant("constant/2", 2.0)
    three = tape.constant("constant/3", 3.0)
    four = tape.constant("constant/4", 4.0)
    x = tape.leaf("tensor/x/0", 1.0)
    shared = tape.mul(x, two, "graph/shared")
    lower_consumer = tape.mul(shared, three, "graph/lower_consumer")
    higher_consumer = tape.mul(shared, four, "graph/higher_consumer")
    total = tape.add(lower_consumer, higher_consumer, "loss/total")
    result = tape.backward(total)
    assert result.gradient(shared) == rn64(rn64(0.0 + 4.0) + 3.0)
    assert result.gradient(x) == 14.0


def test_exact_mean_strict_tie_max_clamp_and_identity_join_routes() -> None:
    tape = ScalarTape(FrozenTestKernel())
    base = tape.leaf("tensor/a_base/0", -3.0)
    residual = tape.leaf("tensor/b_residual/0", 0.0)
    row0 = tape.leaf("tensor/c_rows/0", 1.0)
    row1 = tape.leaf("tensor/c_rows/1", 1.0)
    row2 = tape.leaf("tensor/c_rows/2", -2.0)
    below = tape.leaf("tensor/d_clamp/0", -1.0)
    boundary = tape.leaf("tensor/d_clamp/1", 0.0)
    joined = tape.identity_join(base, residual, "model/join")
    mean = tape.roster_mean(((row0,), (row1,), (row2,)), "model/mean")[0]
    branch0 = tape.add(joined, mean, "loss/branch0")
    maximum = tape.roster_max(((row0,), (row1,), (row2,)), "model/max")[0]
    clamped_below = tape.clamp(below, 0.0, 2.0, "model/clamp_below")
    branch1 = tape.add(maximum, clamped_below, "loss/branch1")
    branch2 = tape.add(branch0, branch1, "loss/branch2")
    clamped_boundary = tape.clamp(boundary, 0.0, 2.0, "model/clamp_boundary")
    total = tape.add(branch2, clamped_boundary, "loss/total")
    result = tape.backward(total)

    assert result.gradient(base) == 1.0
    assert result.gradient(residual) == 1.0
    one_third = rn64(1.0 / 3.0)
    assert result.gradient(row0) == rn64(rn64(0.0 + 1.0) + one_third)
    assert result.gradient(row1) == rn64(rn64(0.0 + 0.0) + one_third)
    assert result.gradient(row2) == one_third
    assert result.gradient(below) == 0.0
    assert result.gradient(boundary) == 0.0


def test_stored_categorical_custom_edges_then_clamp_centered_max_injection() -> None:
    kernel = FrozenTestKernel()
    probability = construct_probability((0.0, -1.0, -16.0), (1, 2, None), kernel)
    tape = ScalarTape(kernel)
    logits = (
        tape.leaf("tensor/logits/0", 0.0),
        tape.leaf("tensor/logits/1", -1.0),
        tape.leaf("tensor/logits/2", -16.0),
    )
    q = tape.centered_clamp(logits, probability, "policy/q")
    stored = tape.stored_categorical(probability)
    assert kernel.log_calls == 3
    logp = tape.categorical_log_probability(q, stored, 1, "policy/logp")
    entropy = tape.categorical_entropy(q, stored, "policy/entropy")
    total = tape.add(logp, entropy, "loss/total")
    result = tape.backward(total)
    assert kernel.log_calls == 3  # reverse reuses stored p/log_p/H bits

    g_q: list[float] = []
    for index, (p, log_p) in enumerate(zip(probability.probabilities, stored.stored_log_p)):
        lp_plus_h = rn64(log_p + stored.stored_H)
        entropy_edge = rn64(1.0 * rn64(-rn64(p * lp_plus_h)))
        indicator = 1.0 if index == 0 else 0.0
        log_edge = rn64(1.0 * rn64(indicator - p))
        g_q.append(rn64(rn64(0.0 + entropy_edge) + log_edge))
    expected = clamp_centered_max_adjoint(probability, tuple(g_q))
    assert tuple(result.gradient(logit) for logit in logits) == expected
    assert result.gradient(logits[2]) == 0.0  # exact -16 boundary gate is closed


def test_leaf_order_graph_postorder_compilation_and_identity_preconditions() -> None:
    tape = ScalarTape(FrozenTestKernel())
    tape.leaf("tensor/z/0", 1.0)
    with pytest.raises(AutodiffError):
        tape.leaf("tensor/a/0", 1.0)

    tape2 = ScalarTape(FrozenTestKernel())
    x = tape2.leaf("tensor/x/0", 1.0)
    bad_residual = tape2.leaf("tensor/y/0", 1.0)
    with pytest.raises(AutodiffError):
        tape2.identity_join(x, bad_residual, "model/join")

    tape3 = ScalarTape(FrozenTestKernel())
    x3 = tape3.leaf("tensor/x/0", 1.0)
    first = tape3.copy(x3, "branch/first")
    second = tape3.copy(x3, "branch/second")
    # Operand order makes DFS primitive postorder second,first although construction
    # handles were created first,second. Compilation remaps the semantic node ids.
    total = tape3.add(second, first, "loss/total")
    result = tape3.backward(total)
    primitive_paths = tuple(
        record.semantic_path
        for record in result.node_table
        if record.primitive not in {"leaf", "constant"}
    )
    assert primitive_paths == ("branch/second", "branch/first", "loss/total")
