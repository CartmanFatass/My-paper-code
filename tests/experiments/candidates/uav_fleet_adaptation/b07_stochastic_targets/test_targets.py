"""Synthetic target laws and declared FP64 CE; no asset or native queries."""
import math
import random

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.targets import (
    MASS_ATOL, SCORE_ATOL, build_targets, soft_cross_entropy,
)


def parent():
    values = np.arange(1, 28, dtype=np.float64)
    return values / values.sum()


def scalar_targets(p, scores, c):
    weights = [float(p[i]) * math.exp((float(scores[i]) - max(scores)) / .014) for i in range(27)]
    total = math.fsum(weights)
    t = np.array([.9 * float(p[i]) + .1 * weights[i] / total for i in range(27)])
    h = np.array([.9 * float(p[i]) + (.1 if i == c else 0.) for i in range(27)])
    return t, h


@pytest.mark.parametrize("scores", [
    np.linspace(0., 1., 27), np.zeros(27), np.ones(27),
    np.array([0.] * 13 + [1.] * 14), np.array([.4, .4, .7] * 9),
])
def test_independent_scalar_formula(scores):
    p = parent()
    p_before, scores_before = p.copy(), scores.copy()
    t, h = build_targets(p, scores, np.int64(12))
    reference_t, reference_h = scalar_targets(p, scores, 12)
    np.testing.assert_allclose(t, reference_t, rtol=0, atol=2e-16)
    np.testing.assert_array_equal(h, reference_h)
    assert t.dtype == h.dtype == np.float64
    assert abs(t.sum() - 1) < 5e-15 and abs(h.sum() - 1) < 5e-15
    np.testing.assert_array_equal(p, p_before)
    np.testing.assert_array_equal(scores, scores_before)


@pytest.mark.parametrize("score", [0., .014, .7, 1.])
def test_flat_t_is_bitwise_independent_copy(score):
    p = parent()
    p[0] = -0.0
    p[1:] /= p[1:].sum()
    p.flags.writeable = False
    t, h = build_targets(p, np.full(27, score), 0)
    assert t.tobytes() == p.tobytes()
    assert not np.shares_memory(t, p) and not np.shares_memory(h, p)
    t[1] = 0.
    assert p[1] != 0.
    assert h[0] == .1


def test_zero_support_and_parent_zero_c_mass():
    p = np.zeros(27, dtype=np.float64)
    p[2], p[15] = .25, .75
    scores = np.zeros(27, dtype=np.float64)
    scores[26], scores[2] = 1., .7
    t, h = build_targets(p, scores, 26)
    assert np.all(t[p == 0] == 0)
    assert t[2] > p[2]
    assert h[26] == .1 and np.count_nonzero(h) == 3
    np.testing.assert_allclose(t, scalar_targets(p, scores, 26)[0], rtol=0, atol=2e-16)


def test_subnormal_parent_mass_does_not_add_support():
    p = np.zeros(27, dtype=np.float64)
    p[0], p[1] = 1., np.nextafter(0., 1.)
    t, h = build_targets(p, np.linspace(1., 0., 27), 1)
    assert np.isfinite(t).all() and np.isfinite(h).all()
    assert np.all(t[2:] == 0) and h[1] >= .1


def test_tv_and_proxy_ordering_in_real_arithmetic_tolerance():
    rng = np.random.default_rng(7001)
    for _ in range(30):
        p = rng.random(27)
        p[rng.random(27) < .2] = 0
        p /= p.sum()
        scores = rng.random(27)
        c = int(np.argmax(scores))
        t, h = build_targets(p, scores, c)
        assert .5 * np.abs(t - p).sum() <= .1 + 2e-15
        assert .5 * np.abs(h - p).sum() <= .1 + 2e-15
        p_proxy, t_proxy, h_proxy = (float(v @ scores) for v in (p, t, h))
        assert t_proxy >= p_proxy - 2e-15
        assert h_proxy >= t_proxy - 2e-15


@pytest.mark.parametrize("change", ["p_dtype", "p_shape", "p_list", "p_nan", "p_inf", "p_negative", "p_mass",
                                   "score_dtype", "score_shape", "score_nan", "score_inf", "score_low", "score_high"])
def test_invalid_array_inputs(change):
    p, scores = parent(), np.linspace(0., 1., 27)
    if change == "p_dtype": p = p.astype(np.float32)
    elif change == "p_shape": p = p.reshape(1, 27)
    elif change == "p_list": p = p.tolist()
    elif change == "p_nan": p[0] = np.nan
    elif change == "p_inf": p[0] = np.inf
    elif change == "p_negative": p[0] = -1e-20
    elif change == "p_mass": p *= .99
    elif change == "score_dtype": scores = scores.astype(np.float32)
    elif change == "score_shape": scores = scores[:26]
    elif change == "score_nan": scores[0] = np.nan
    elif change == "score_inf": scores[0] = np.inf
    elif change == "score_low": scores[0] = -2 * SCORE_ATOL
    else: scores[-1] = 1. + 2 * SCORE_ATOL
    with pytest.raises(ValueError):
        build_targets(p, scores, 0)


@pytest.mark.parametrize("index", [True, np.bool_(False), 0., "1", None, -1, 27])
def test_invalid_c_index(index):
    with pytest.raises(ValueError):
        build_targets(parent(), np.zeros(27), index)


def test_small_endpoint_rounding_is_used_unchanged():
    scores = np.linspace(0., 1., 27)
    scores[0], scores[-1] = -SCORE_ATOL / 2, 1. + SCORE_ATOL / 2
    t, h = build_targets(parent(), scores, 26)
    np.testing.assert_allclose(t, scalar_targets(parent(), scores, 26)[0], rtol=0, atol=2e-16)
    assert scores[0] < 0 and scores[-1] > 1
    assert np.isfinite(h).all()


def test_normalization_validation_is_stricter_than_generic_decoder():
    p = parent()
    p[0] += 2e-13
    assert abs(p.sum() - 1) < 1e-12
    with pytest.raises(ValueError, match="mass"):
        build_targets(p, np.zeros(27), 0)
    assert MASS_ATOL < 1e-12


def test_no_python_numpy_or_torch_rng_consumption():
    numpy_before = np.random.get_state()
    python_before = random.getstate()
    torch_before = torch.random.get_rng_state().clone()
    for scores in (np.zeros(27), np.linspace(0, 1, 27)):
        t, _ = build_targets(parent(), scores, 1)
        logits = torch.arange(54, dtype=torch.float32).reshape(2, 27).requires_grad_()
        targets = torch.from_numpy(np.tile(t, (2, 1)))
        soft_cross_entropy(logits, targets).backward()
    numpy_after = np.random.get_state()
    assert numpy_before[0] == numpy_after[0] and numpy_before[2:] == numpy_after[2:]
    np.testing.assert_array_equal(numpy_before[1], numpy_after[1])
    assert python_before == random.getstate()
    assert torch.equal(torch_before, torch.random.get_rng_state())


def test_soft_ce_matches_independent_scalar_loss_and_gradient():
    values = np.linspace(-9., 8., 81, dtype=np.float32).reshape(3, 27)
    logits = torch.tensor(values, dtype=torch.float32, requires_grad=True)
    targets = np.stack([build_targets(parent(), np.linspace(0., 1., 27), c)[0] for c in (0, 12, 26)])
    tensor_targets = torch.from_numpy(targets.copy())
    loss = soft_cross_entropy(logits, tensor_targets)
    expected_loss, expected_grad = [], []
    for z, t in zip(values.astype(np.float64), targets):
        exps = [math.exp(float(v) - max(z)) for v in z]
        partition = math.fsum(exps)
        logsumexp = float(max(z)) + math.log(partition)
        expected_loss.append(-math.fsum(float(w) * (float(v) - logsumexp) for v, w in zip(z, t)))
        expected_grad.append([(e / partition * math.fsum(t) - float(w)) / 3 for e, w in zip(exps, t)])
    assert loss.dtype == torch.float64
    assert math.isclose(float(loss.detach()), math.fsum(expected_loss) / 3, rel_tol=0, abs_tol=3e-15)
    loss.backward()
    np.testing.assert_allclose(logits.grad.numpy(), np.array(expected_grad, dtype=np.float32), rtol=0, atol=4e-9)
    assert logits.grad.dtype == torch.float32 and torch.isfinite(logits.grad).all()
    np.testing.assert_array_equal(logits.detach().numpy(), values)
    np.testing.assert_array_equal(tensor_targets.numpy(), targets)


def test_identical_targets_have_identical_loss_and_parameter_gradients():
    # Point mass at C makes nonflat T and H exactly identical.
    p = np.zeros(27); p[4] = 1.
    t, h = build_targets(p, np.linspace(0., 1., 27), 4)
    np.testing.assert_array_equal(t, h)
    values = torch.arange(54, dtype=torch.float32).reshape(2, 27) / 13
    left, right = values.clone().requires_grad_(), values.clone().requires_grad_()
    tl = soft_cross_entropy(left, torch.from_numpy(np.tile(t, (2, 1))))
    hl = soft_cross_entropy(right, torch.from_numpy(np.tile(h, (2, 1))))
    assert torch.equal(tl, hl)
    tl.backward(); hl.backward()
    assert torch.equal(left.grad, right.grad)


def test_one_hot_loss_and_gradient_match_declared_fp64_hard_ce():
    values = torch.linspace(-11, 12, 108, dtype=torch.float32).reshape(4, 27)
    labels = torch.tensor([0, 8, 17, 26], dtype=torch.int64)
    left, right = values.clone().requires_grad_(), values.clone().requires_grad_()
    targets = torch.nn.functional.one_hot(labels, num_classes=27).to(torch.float64)
    soft = soft_cross_entropy(left, targets)
    hard_fp64 = torch.nn.functional.cross_entropy(right.to(torch.float64), labels)
    assert torch.equal(soft, hard_fp64)
    soft.backward(); hard_fp64.backward()
    assert torch.equal(left.grad, right.grad)


def test_zero_entries_and_extreme_finite_logits_backward():
    limit = torch.finfo(torch.float32).max
    logits = torch.full((2, 27), -limit, dtype=torch.float32)
    logits[:, 0] = limit
    logits.requires_grad_()
    targets = torch.zeros((2, 27), dtype=torch.float64)
    targets[0, 0], targets[1, 26] = 1., 1.
    loss = soft_cross_entropy(logits, targets)
    assert torch.isfinite(loss) and float(loss.detach()) > 1e38
    loss.backward()
    assert torch.isfinite(logits.grad).all()
    assert logits.grad[0].count_nonzero() == 0
    assert logits.grad[1, 0] == .5 and logits.grad[1, 26] == -.5


def test_tiny_fp64_target_mass_survives_below_fp32_range():
    limit = torch.finfo(torch.float32).max
    logits = torch.full((1, 27), -limit, dtype=torch.float32, requires_grad=True)
    with torch.no_grad():
        logits[0, 0] = limit
    targets = torch.zeros((1, 27), dtype=torch.float64)
    targets[0, 0], targets[0, 1] = 1., 1e-60
    assert targets.to(torch.float32)[0, 1] == 0
    loss = soft_cross_entropy(logits, targets)
    assert float(loss.detach()) == 2 * float(limit) * 1e-60
    assert loss > 0  # Converting the target through FP32 would erase this loss.
    loss.backward()
    assert logits.grad.dtype == torch.float32 and torch.isfinite(logits.grad).all()


@pytest.mark.parametrize("change", ["logit_dtype", "logit_shape", "empty", "logit_nan", "logit_inf", "logit_numpy",
                                   "target_dtype", "target_shape", "target_numpy", "target_nan", "target_inf",
                                   "negative", "zero_mass", "mass_error"])
def test_loss_rejects_invalid_contract(change):
    logits = torch.zeros((2, 27), dtype=torch.float32)
    targets = torch.full((2, 27), 1 / 27, dtype=torch.float64)
    if change == "logit_dtype": logits = logits.to(torch.float64)
    elif change == "logit_shape": logits = logits[0]
    elif change == "empty": logits, targets = logits[:0], targets[:0]
    elif change == "logit_nan": logits[0, 0] = torch.nan
    elif change == "logit_inf": logits[0, 0] = torch.inf
    elif change == "logit_numpy": logits = logits.numpy()
    elif change == "target_dtype": targets = targets.to(torch.float32)
    elif change == "target_shape": targets = targets[:1]
    elif change == "target_numpy": targets = targets.numpy()
    elif change == "target_nan": targets[0, 0] = torch.nan
    elif change == "target_inf": targets[0, 0] = torch.inf
    elif change == "negative": targets[0, 0] = -1e-30
    elif change == "zero_mass": targets[0] = 0
    else: targets[0, 0] += 2e-13
    with pytest.raises(ValueError):
        soft_cross_entropy(logits, targets)


def test_synthetic_count_student_n5_gradients_leave_count_branch_zero():
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import CountStudent
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(7011)
        model = CountStudent()
    inputs = torch.linspace(-1., 1., 342, dtype=torch.float32).reshape(3, 114)
    before = {key: value.detach().clone() for key, value in model.state_dict().items()}
    targets = torch.from_numpy(np.tile(parent(), (3, 1)))
    loss = soft_cross_entropy(model(inputs, torch.full((3,), 5, dtype=torch.int64)), targets)
    loss.backward()
    assert torch.equal(model.count_weight.grad, torch.zeros(128, dtype=torch.float32))
    assert all(parameter.grad.dtype == torch.float32 and torch.isfinite(parameter.grad).all()
               for parameter in model.parameters())
    assert sum(float(parameter.grad.abs().sum()) for parameter in model.parameters()) > 0
    assert all(torch.equal(value, before[key]) for key, value in model.state_dict().items())
