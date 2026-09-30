"""Small cached-context fixtures only; no original asset or native episode."""
import copy
import hashlib

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b05_native_consequence.learning import (
    BATCH_SIZE, MU_ATOL, Head, fit_head, paired_loss,
)


@pytest.fixture(autouse=True)
def one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def probabilities(logits):
    z = logits.astype(np.float64)
    weights = np.exp(z - z.max(axis=-1, keepdims=True))
    return weights / weights.sum(axis=-1, keepdims=True, dtype=np.float64)


def contexts(n=7):
    rng = np.random.default_rng(71)
    z = rng.normal(0, .5, (n, 27)).astype(np.float32)
    return dict(hidden=rng.normal(size=(n, 128)).astype(np.float32), logits=z,
                mu=.5 * probabilities(z) + .5 / 27.,
                action_a=rng.integers(0, 27, size=n), action_b=rng.integers(0, 27, size=n),
                delta_j=rng.uniform(-.08, .08, size=n), weight=rng.uniform(.5, 2., size=n))


def batch(n):
    return (np.arange(BATCH_SIZE) % n).astype(np.int64)


@pytest.mark.parametrize("kind,parameters", [("CAL", 28), ("CONT", 3483)])
def test_zero_head_exact_identity_parameter_counts_and_no_rng_draws(kind, parameters):
    before = torch.random.get_rng_state().clone()
    head = Head(kind)
    assert torch.equal(before, torch.random.get_rng_state())
    assert sum(p.numel() for p in head.parameters()) == parameters
    assert all(torch.count_nonzero(p) == 0 for p in head.parameters())
    data = contexts()
    for h, z in zip(data["hidden"], data["logits"]):
        output = head(torch.from_numpy(h), torch.from_numpy(z))
        assert output.shape == (27,) and output.dtype == torch.float32
        torch.testing.assert_close(output, torch.from_numpy(z), rtol=0, atol=0)
        np.testing.assert_array_equal(probabilities(output.detach().numpy()), probabilities(z))
    loss, diagnostics = paired_loss(head, data, batch(len(data["hidden"])))
    assert loss.dtype == torch.float64 and diagnostics["KL"] == 0
    assert diagnostics["loss"] == pytest.approx(-diagnostics["F"], abs=1e-15)


@pytest.mark.parametrize("kind", ["CAL", "CONT"])
def test_manual_two_action_gradient_and_score_sign(kind):
    data = contexts(1)
    data["logits"][:] = 0
    data["hidden"][:] = .7
    data["mu"][:] = 1 / 27.
    data["action_a"][:] = 2
    data["action_b"][:] = 9
    data["delta_j"][:] = .4
    data["weight"][:] = 1.3
    head = Head(kind)
    loss, diagnostics = paired_loss(head, data, batch(1))
    assert abs(float(loss.detach())) < 1e-15
    loss.backward()
    expected = np.zeros(27, dtype=np.float32)
    # At uniform S, p/mu=1 and d(.5*tanh(b))/db=.5.
    expected[2], expected[9] = -.25 * .4 * 1.3, .25 * .4 * 1.3
    torch.testing.assert_close(head.b.grad, torch.from_numpy(expected), rtol=1e-6, atol=1e-8)
    assert head.b.grad.dtype == torch.float32
    if kind == "CAL":
        assert head.alpha.grad == 0
    else:
        torch.testing.assert_close(head.W.grad, torch.from_numpy(np.outer(expected, data["hidden"][0])), rtol=1e-6, atol=1e-8)
    with torch.no_grad():
        for p in head.parameters():
            p -= .01 * p.grad
    output = head(torch.tensor(data["hidden"][0]), torch.tensor(data["logits"][0])).detach().numpy()
    assert output[2] > output[9]
    new_loss, _ = paired_loss(head, data, batch(1))
    assert new_loss < loss.detach()


@pytest.mark.parametrize("case", ["zero_delta", "same_action"])
def test_zero_contrast_retains_kl_and_zero_score(case):
    data = contexts(3)
    if case == "zero_delta":
        data["delta_j"][:] = 0
    else:
        data["action_b"][:] = data["action_a"]
    head = Head("CAL")
    zero, diagnostic = paired_loss(head, data, batch(3))
    zero.backward()
    assert diagnostic["F"] == diagnostic["KL"] == 0
    assert all(float(p.grad.abs().max()) < 1e-7 for p in head.parameters())
    with torch.no_grad():
        head.b.copy_(torch.linspace(-.8, .8, 27))
    loss, diagnostic = paired_loss(head, data, batch(3))
    assert diagnostic["F"] == 0 and diagnostic["KL"] > 0
    assert float(loss.detach()) == pytest.approx(.01 * diagnostic["KL"], abs=1e-15)


def test_fixed_denominator_and_address_weight_on_both_score_and_kl():
    data = contexts(2)
    data["weight"][:] = [.2, 2.8]
    indices = batch(2)
    head = Head("CAL")
    with torch.no_grad():
        head.alpha.fill_(.2)
        head.b.copy_(torch.linspace(-.5, .9, 27))
    loss, diagnostics = paired_loss(head, data, indices)
    logits = np.stack([head(torch.tensor(data["hidden"][i]), torch.tensor(data["logits"][i])).detach().numpy() for i in indices])
    p, s = probabilities(logits), probabilities(data["logits"][indices])
    a, b = data["action_a"][indices], data["action_b"][indices]
    mu, weight = data["mu"][indices], data["weight"][indices]
    arange = np.arange(BATCH_SIZE)
    score = .5 * data["delta_j"][indices] * (p[arange, a] / mu[arange, a] - p[arange, b] / mu[arange, b])
    kl = (p * np.log(p / s)).sum(-1)
    expected = np.sum(weight * (-score + .01 * kl)) / 128
    assert float(loss.detach()) == pytest.approx(expected, abs=1e-14)
    assert diagnostics["F"] == pytest.approx(np.sum(weight * score) / 128, abs=1e-14)
    assert diagnostics["KL"] == pytest.approx(np.sum(weight * kl) / 128, abs=1e-14)
    assert abs(expected - np.sum(weight * (-score + .01 * kl)) / weight.sum()) > 1e-5
    assert abs(expected - np.sum(-weight * score + .01 * kl) / 128) > 1e-7
    scaled = copy.deepcopy(data)
    scaled["weight"] *= 2
    loss2, diagnostics2 = paired_loss(head, scaled, indices)
    assert float(loss2.detach()) == pytest.approx(2 * expected, abs=1e-14)
    assert diagnostics2["KL"] == pytest.approx(2 * diagnostics["KL"], abs=1e-14)


@pytest.mark.parametrize("kind", ["CAL", "CONT"])
def test_fp64_density_extremes_underflow_and_numpy_agreement(kind):
    data = contexts(3)
    data["logits"][0] = np.linspace(-1000, 0, 27, dtype=np.float32)
    data["logits"][1] = np.float32(1e20)  # Huge common shift, still uniform.
    data["logits"][2] = np.linspace(-100, 100, 27, dtype=np.float32)
    data["mu"] = .5 * probabilities(data["logits"]) + .5 / 27.
    assert data["mu"].min() >= 1 / 54.
    head = Head(kind)
    with torch.no_grad():
        head.b.copy_(torch.linspace(-.8, .8, 27))
    output_rows = []
    hook = head.register_forward_hook(lambda module, inputs, output: output_rows.append(output.detach().numpy().copy()))
    loss, diagnostic = paired_loss(head, data, batch(3))
    hook.remove()
    loss.backward()
    assert torch.isfinite(loss) and all(torch.isfinite(p.grad).all() for p in head.parameters())
    assert all(np.isfinite(value) for value in diagnostic.values())
    assert diagnostic["KL"] >= -1e-14
    # Torch and NumPy stable nominal densities agree within 5e-15 absolute:
    # FP64 27-term normalization error at unit scale, not bitwise decoder masses.
    z = torch.tensor(np.stack(output_rows), dtype=torch.float64)
    shifted = z - z.max(-1, keepdim=True).values
    torch_p = (shifted - torch.logsumexp(shifted, -1, keepdim=True)).exp().numpy()
    np.testing.assert_allclose(torch_p, probabilities(np.stack(output_rows)), rtol=0, atol=5e-15)
    assert np.any(probabilities(data["logits"])[0] == 0)  # log(S_p) would be -inf.


@pytest.mark.parametrize("kind", ["CAL", "CONT"])
def test_same_row_fit_deployment_and_deterministic_steps(kind):
    data = contexts()
    before_data = copy.deepcopy(data)
    before_rng = torch.random.get_rng_state().clone()
    rows = []
    original_forward = Head.forward
    # A temporary subclass-free hook records all fit calls, with no extra fit.
    observed = []
    def progress(record):
        observed.append((record["status"], record["optimizer_steps"], record["training_rows"]))
    counts = dict(head_fits_started=5, head_fits_completed=4, head_optimizer_steps=13, head_training_rows=17, unrelated=91)
    head, optimizer, record = fit_head(kind, data, seed=42, counts=counts, updates=3, progress=progress)
    assert torch.equal(before_rng, torch.random.get_rng_state())
    assert counts == dict(head_fits_started=6, head_fits_completed=5, head_optimizer_steps=16, head_training_rows=401, unrelated=91)
    assert record["status"] == "COMPLETE" and record["optimizer_steps"] == 3 and record["training_rows"] == 384
    assert record["initial_optimizer_entries"] == 0 and record["movement"]["changed_parameters"] > 0
    assert record["initial_state_sha256"] != record["final_state_sha256"] == state_digest(head.state_dict())
    assert record["adam_step_values"] == [3] * len(list(head.parameters()))
    assert record["counts"] == dict(head_fits_started=1, head_fits_completed=1, head_optimizer_steps=3, head_training_rows=384)
    assert observed[0] == ("INCOMPLETE", 0, 0) and observed[-1] == ("COMPLETE", 3, 384)
    rng, order = np.random.default_rng(42), hashlib.sha256()
    for index, update in enumerate(record["updates"]):
        indices = rng.integers(0, len(data["hidden"]), size=128)
        payload = indices.astype("<i8").tobytes()
        order.update(payload)
        assert update["update"] == index and update["batch_sha256"] == hashlib.sha256(payload).hexdigest()
        assert update["status"] == "COMPLETE" and update["optimizer_step_completed"]
        assert update["adam_step_values"] == [index + 1] * len(list(head.parameters()))
        assert update["loss"] == pytest.approx(-update["F"] + .01 * update["KL"], abs=1e-14)
        assert update["gradient_l2"] > 0 and update["gradient_max_abs"] > 0
    assert record["batch_order_sha256"] == order.hexdigest()
    for key, value in dict(lr=.001, betas=(.9, .999), eps=1e-8, weight_decay=0, amsgrad=False, foreach=False, fused=False).items():
        assert optimizer.defaults[key] == value
    second, other_optimizer, repeated = fit_head(kind, data, seed=42, counts={}, updates=3)
    assert repeated["final_state_sha256"] == record["final_state_sha256"]
    assert repeated["batch_order_sha256"] == record["batch_order_sha256"]
    assert all(torch.equal(p, q) for p, q in zip(head.parameters(), second.parameters()))
    hook = head.register_forward_hook(lambda module, inputs, output: rows.append((inputs, output.detach().clone())))
    paired_loss(head, data, batch(len(data["hidden"])))
    hook.remove()
    assert len(rows) == 128
    for (hidden, logits), output in rows:
        assert hidden.shape == (128,) and logits.shape == (27,)
        torch.testing.assert_close(output, original_forward(head, hidden, logits), rtol=0, atol=0)
    for key in data:
        np.testing.assert_array_equal(data[key], before_data[key])


def test_cal_cont_same_minibatch_stream():
    data = contexts()
    cal, _, first = fit_head("CAL", data, seed=42, counts={}, updates=2)
    cont, _, second = fit_head("CONT", data, seed=42, counts={}, updates=2)
    assert first["batch_order_sha256"] == second["batch_order_sha256"]
    assert first["updates"][0]["loss"] == second["updates"][0]["loss"]
    assert first["data_sha256"] == second["data_sha256"]


@pytest.mark.parametrize("case", ["dtype", "shape", "action", "weight", "mu", "nan", "indices", "batch_size"])
def test_malformed_data_and_batch_rejected_without_fit_effects(case):
    data = contexts()
    indices = batch(len(data["hidden"]))
    counts = {}
    if case == "dtype":
        data["delta_j"] = data["delta_j"].astype(np.float32)
    elif case == "shape":
        data["hidden"] = data["hidden"][:, :127]
    elif case == "action":
        data["action_a"][0] = 27
    elif case == "weight":
        data["weight"][0] = 0
    elif case == "mu":
        data["mu"][0, 0] += 1e-12
    elif case == "nan":
        data["delta_j"][0] = np.nan
    elif case == "indices":
        indices = indices[:127]
    if case == "indices":
        with pytest.raises(ValueError):
            paired_loss(Head("CAL"), data, indices)
    else:
        with pytest.raises((ValueError, FloatingPointError)):
            fit_head("CAL", data, seed=42, counts=counts, updates=2, batch_size=64 if case == "batch_size" else 128)
    assert not counts


def test_partial_fit_failure_keeps_rows_steps_record_and_actual_objects(monkeypatch):
    data = contexts()
    original = Head.forward
    calls = []
    def fail_after_one_update(self, hidden, logits):
        calls.append((hidden.shape, logits.shape))
        if len(calls) == 129:
            raise FloatingPointError("synthetic second-update failure")
        return original(self, hidden, logits)
    monkeypatch.setattr(Head, "forward", fail_after_one_update)
    reports, counts = [], {}
    with pytest.raises(FloatingPointError) as caught:
        fit_head("CAL", data, seed=42, counts=counts, updates=3, progress=lambda record: reports.append(copy.deepcopy(record)))
    error = caught.value
    assert counts == dict(head_fits_started=1, head_optimizer_steps=1, head_training_rows=129)
    assert error.fit_record["status"] == reports[-1]["status"] == "FAILED"
    assert error.fit_record["training_rows"] == 129 and error.fit_record["optimizer_steps"] == 1
    assert len(error.fit_record["updates"]) == 2
    assert error.fit_record["updates"][0]["optimizer_step_completed"] is True
    assert error.fit_record["updates"][1]["optimizer_step_completed"] is False
    assert error.fit_record["final_state_sha256"] == state_digest(error.fit_head.state_dict())
    assert all(float(entry["step"]) == 1 for entry in error.fit_optimizer.state.values())
    assert set(calls) == {((128,), (27,))}


def test_nonfinite_gradient_preserves_paid_rows_and_zero_actual_steps():
    data = contexts(1)
    data["delta_j"][:] = 1e300
    data["action_a"][:] = 0
    data["action_b"][:] = 1
    counts = {}
    with pytest.raises(FloatingPointError, match="gradient") as caught:
        fit_head("CONT", data, seed=42, counts=counts, updates=2)
    assert counts == dict(head_fits_started=1, head_training_rows=128)
    assert caught.value.fit_record["optimizer_steps"] == 0
    assert not caught.value.fit_optimizer.state
    assert caught.value.fit_record["updates"][0]["optimizer_step_completed"] is False


def test_large_finite_gradient_reaches_adam_without_clipping():
    data = contexts(1)
    data["logits"][:] = 0
    data["mu"][:] = 1 / 27.
    data["action_a"][:] = 2
    data["action_b"][:] = 9
    data["delta_j"][:] = 1
    data["weight"][:] = 100
    head, optimizer, record = fit_head("CAL", data, seed=42, counts={}, updates=1)
    expected = torch.zeros(27)
    expected[2], expected[9] = -25, 25
    torch.testing.assert_close(optimizer.state[head.b]["exp_avg"], .1 * expected, rtol=1e-6, atol=1e-6)
    torch.testing.assert_close(optimizer.state[head.b]["exp_avg_sq"], .001 * expected.square(), rtol=1e-6, atol=1e-6)
    assert record["updates"][0]["gradient_l2"] == pytest.approx(np.sqrt(2) * 25, rel=1e-6)
    assert record["updates"][0]["gradient_max_abs"] == pytest.approx(25, rel=1e-6)


def test_head_rejects_batched_or_nonfinite_context():
    head = Head("CONT")
    with pytest.raises(ValueError):
        head(torch.zeros(1, 128), torch.zeros(1, 27))
    with pytest.raises(ValueError):
        head(torch.zeros(128, dtype=torch.float64), torch.zeros(27))
    with pytest.raises(FloatingPointError):
        head(torch.full((128,), float("nan")), torch.zeros(27))
    assert MU_ATOL == 5e-15
