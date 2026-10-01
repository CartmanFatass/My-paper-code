"""Small artificial phases/actors only; no production archive or endpoint."""
from dataclasses import dataclass
import hashlib

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_copy, state_digest
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import array_digest
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import make_inherited, make_optimizer, checkpoint
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets import training


@dataclass(frozen=True)
class Small:
    epochs: tuple = (2, 1, 1)
    batch_size: int = 4
    learning_rate: float = 3e-4
    grad_norm: float = 1.
    def validate(self):
        return self
    def expected(self):
        return dict(datasets=[8, 12, 16])


@pytest.fixture(autouse=True)
def one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def model():
    return make_inherited(state_copy(make_student(7031)), 7032)


def data():
    rng = np.random.default_rng(7033)
    x = rng.normal(size=(16, 114)).astype(np.float32)
    y = rng.random((16, 27))
    y[:, 2] = 0.
    y /= y.sum(axis=1, keepdims=True)
    return x, y


def test_reference_updates_order_shared_kernel_streams_and_no_extra_forward(monkeypatch):
    actor, reference, p = model(), model(), Small()
    optimizer, reference_optimizer = make_optimizer(actor, p), make_optimizer(reference, p)
    x, y = data(); x, y = x[:8], y[:8]
    expected, orders = [], []
    for epoch in range(2):
        order = np.random.default_rng(np.random.SeedSequence([17, 0, epoch])).permutation(8)
        orders.append(order)
        confusion, losses = np.zeros((27, 27), dtype=np.int64), []
        for start in range(0, 8, 4):
            ids = order[start:start + 4]
            reference_optimizer.zero_grad(set_to_none=True)
            # N5 has a zero multiplier; compose original layers independently.
            hidden = reference.network[0](torch.from_numpy(x[ids])) + reference.count_weight * 0.
            logits = reference.network[4](reference.network[3](reference.network[2](reference.network[1](hidden))))
            target = torch.from_numpy(y[ids])
            loss = -(target * torch.log_softmax(logits.double(), dim=1)).sum(dim=1).mean()
            losses.append(float(loss.detach()) * 4)
            np.add.at(confusion, (y[ids].argmax(1), logits.detach().argmax(1).numpy()), 1)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(reference.parameters(), 1., error_if_nonfinite=True)
            reference_optimizer.step()
        expected.append((sum(losses) / 8, float(np.trace(confusion) / 8), confusion))
    calls, kernel_calls, progress = [], [], []
    hook = actor.register_forward_pre_hook(lambda module, args: calls.append((args[0].clone(), args[1].clone())))
    shared = training.soft_cross_entropy
    def kernel(logits, targets):
        kernel_calls.append((logits.dtype, targets.dtype))
        return shared(logits, targets)
    monkeypatch.setattr(training, "soft_cross_entropy", kernel)
    counts = dict(optimizer_steps=100, sample_presentations=200, unrelated=19)
    result = training.train_phase(actor, optimizer, x, y, 0, counts, protocol=p, shuffle_root=17,
                                  progress=lambda phase, row: progress.append((phase, row)))
    hook.remove()
    assert counts == dict(optimizer_steps=104, sample_presentations=216, unrelated=19)
    assert len(calls) == len(kernel_calls) == 4
    assert kernel_calls == [(torch.float32, torch.float64)] * 4
    assert state_digest(actor.state_dict()) == state_digest(reference.state_dict())
    all_order = hashlib.sha256()
    for e, row in enumerate(result["epochs"]):
        payload = orders[e].astype("<i8").tobytes()
        all_order.update(payload)
        assert row["shuffle_sha256"] == hashlib.sha256(payload).hexdigest()
        assert row["stream_cross_entropy"] == expected[e][0]
        assert row["stream_target_mode_accuracy"] == expected[e][1]
        assert row["updates"] == row["count_zero_gradient_updates"] == 2
        assert row["count_nonzero_gradient_updates"] == 0
        assert row["nonzero_gradient_updates"] == 2
        assert row["stream_rows"] == row["sample_presentations"] == 8
        assert row["max_count_gradient_norm_before_clip"] == 0
        assert "stream_accuracy" not in row and "stream_confusion" not in row
        for b in range(2):
            np.testing.assert_array_equal(calls[2 * e + b][0].numpy(), x[orders[e][4 * b:4 * b + 4]])
            assert torch.equal(calls[2 * e + b][1], torch.full((4,), 5, dtype=torch.int64))
    np.testing.assert_array_equal(result["epochs"][-1]["stream_target_mode_confusion"], expected[-1][2])
    assert result["all_shuffle_sha256"] == all_order.hexdigest()
    assert result["data_sha256"] == array_digest(x, y, np.full(8, 5, dtype=np.int64))
    assert result["targets_sha256"] == array_digest(y)
    assert result["features_sha256"] == array_digest(x)
    assert result["count_counts"] == {"3": 0, "4": 0, "5": 8, "6": 0, "7": 0}
    assert result["adam_step_values"] == [4] * 7
    assert result["movement"]["changed_parameters"] > 0
    assert result["count_branch_movement"]["l2"] == 0
    assert result["wall_seconds"] >= 0 and result["cpu_seconds"] >= 0
    assert len(progress) == 2 and all(phase == 0 for phase, _ in progress)
    assert not actor.training


def test_three_phases_continue_adam_checkpoint_and_same_target_arms(tmp_path):
    actor, restored, p = model(), model(), Small()
    optimizer = make_optimizer(actor, p)
    x, y = data(); counts = {}
    first = training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p, shuffle_root=17)
    path = tmp_path / "synthetic.pt"
    torch.save(checkpoint(actor, optimizer), path)
    payload = torch.load(path, weights_only=True)
    restored.load_state_dict(payload["state_dict"])
    other_optimizer = make_optimizer(restored, p)
    other_optimizer.load_state_dict(payload["optimizer"])
    other_counts, trace = dict(counts), list(first["epochs"])
    for phase, size in ((1, 12), (2, 16)):
        left = training.train_phase(actor, optimizer, x[:size], y[:size], phase, counts, protocol=p, shuffle_root=17)
        right = training.train_phase(restored, other_optimizer, x[:size], y[:size].copy(), phase, other_counts,
                                     protocol=p, shuffle_root=17)
        assert left["before_sha256"] == right["before_sha256"]
        assert left["after_sha256"] == right["after_sha256"]
        assert left["all_shuffle_sha256"] == right["all_shuffle_sha256"]
        assert left["adam_step_values"] == right["adam_step_values"]
        assert left["count_branch_movement"]["changed_parameters"] == 0
        trace.extend(left["epochs"])
    assert len(trace) == 4  # Artificial equivalent of production 30+20+20.
    assert counts == other_counts == dict(optimizer_steps=11, sample_presentations=44)
    assert checkpoint(actor, optimizer)["optimizer_steps"] == 11
    for key in ("exp_avg", "exp_avg_sq"):
        assert optimizer.state[actor.count_weight][key].count_nonzero() == 0
    assert actor.count_weight.count_nonzero() == 0


@pytest.mark.parametrize("case", ["feature_dtype", "feature_shape", "features_nan", "target_dtype", "target_shape",
                                  "target_nan", "target_negative", "target_zero_mass", "target_mass", "phase", "root", "counter"])
def test_reject_bad_data_before_effects(case):
    actor, p = model(), Small(); optimizer = make_optimizer(actor, p)
    x, y = data(); x, y = x[:8], y[:8]
    counts, phase, root = {}, 0, 17
    if case == "feature_dtype": x = x.astype(np.float64)
    elif case == "feature_shape": x = x[:, :113]
    elif case == "features_nan": x[0, 0] = np.nan
    elif case == "target_dtype": y = y.astype(np.float32)
    elif case == "target_shape": y = y[:, :26]
    elif case == "target_nan": y[0, 0] = np.nan
    elif case == "target_negative": y[0, 2] = -1e-30
    elif case == "target_zero_mass": y[0] = 0
    elif case == "target_mass": y[0, 0] += 2e-13
    elif case == "phase": phase = True
    elif case == "root": root = -1
    else: counts["optimizer_steps"] = True
    before = state_digest(actor.state_dict())
    with pytest.raises(ValueError):
        training.train_phase(actor, optimizer, x, y, phase, counts, protocol=p, shuffle_root=root)
    assert not optimizer.state and state_digest(actor.state_dict()) == before
    assert counts == ({"optimizer_steps": True} if case == "counter" else {})


@pytest.mark.parametrize("option,value", [("lr", .001), ("betas", (.8, .999)), ("eps", 1e-7),
                                         ("weight_decay", .01), ("amsgrad", True), ("foreach", True),
                                         ("fused", True), ("maximize", True), ("capturable", True), ("differentiable", True),
                                         ("decoupled_weight_decay", True)])
def test_exact_adam_options(option, value):
    actor, p = model(), Small(); optimizer = make_optimizer(actor, p)
    optimizer.param_groups[0][option] = value
    x, y = data(); counts = {}
    with pytest.raises(ValueError, match="Adam configuration"):
        training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p)
    assert not counts and not optimizer.state


@pytest.mark.parametrize("case", ["extra_param", "frozen_param", "double_param", "nonzero_count", "wrong_owner"])
def test_actor_contract(case):
    actor, p = model(), Small()
    if case == "extra_param": actor.extra = torch.nn.Parameter(torch.zeros(1))
    elif case == "frozen_param": actor.network[0].weight.requires_grad_(False)
    elif case == "double_param": actor.network[0].weight.data = actor.network[0].weight.data.double()
    elif case == "nonzero_count": actor.count_weight.data[0] = 1
    optimizer = make_optimizer(model() if case == "wrong_owner" else actor, p)
    x, y = data(); counts = {}
    with pytest.raises(ValueError):
        training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p)
    assert not counts


def test_reset_skipped_phase_and_fractional_adam_step_rejected():
    actor, p = model(), Small(); optimizer = make_optimizer(actor, p)
    x, y = data(); counts = {}
    with pytest.raises(AssertionError):
        training.train_phase(actor, optimizer, x[:12], y[:12], 1, counts, protocol=p)
    training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p)
    before = dict(counts)
    with pytest.raises(AssertionError):
        training.train_phase(actor, make_optimizer(actor, p), x[:12], y[:12], 1, counts, protocol=p)
    optimizer.state[next(actor.parameters())]["step"] += .5
    with pytest.raises(AssertionError):
        training.train_phase(actor, optimizer, x[:12], y[:12], 1, counts, protocol=p)
    assert counts == before


def test_nonzero_count_moments_rejected_before_next_phase():
    actor, p = model(), Small(); optimizer = make_optimizer(actor, p)
    x, y = data(); counts = {}
    training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p)
    optimizer.state[actor.count_weight]["exp_avg"][0] = .01
    before = dict(counts)
    with pytest.raises(ValueError, match="count branch Adam"):
        training.train_phase(actor, optimizer, x[:12], y[:12], 1, counts, protocol=p)
    assert counts == before


def test_partial_forward_failure_counts_and_stream_record(monkeypatch):
    actor, p = model(), Small(); optimizer = make_optimizer(actor, p)
    x, y = data(); counts = dict(optimizer_steps=100, sample_presentations=200)
    forward, calls = actor.forward, []
    def fail_second(features, fleet_counts):
        calls.append(1)
        if len(calls) == 2:
            raise FloatingPointError("synthetic second forward")
        return forward(features, fleet_counts)
    monkeypatch.setattr(actor, "forward", fail_second)
    with pytest.raises(FloatingPointError) as caught:
        training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p, shuffle_root=17)
    r = caught.value.phase_record
    assert counts == dict(optimizer_steps=101, sample_presentations=208)
    assert r["optimizer_steps"] == 1 and r["sample_presentations"] == 8
    assert r["status"] == "FAILED" and r["interrupted_call_work_may_be_unmeasured"]
    assert r["epochs"][0]["stream_rows"] == 4
    assert np.sum(r["epochs"][0]["stream_target_mode_confusion"]) == 4
    assert r["adam_step_values"] == [1] * 7
    assert r["parameters_finite"] and r["movement"]["l2"] > 0


def test_post_step_nonfinite_failure_keeps_completed_update_counts(monkeypatch):
    actor, p = model(), Small(); optimizer = make_optimizer(actor, p)
    x, y = data(); counts = {}
    step = optimizer.step
    def poisoned_step(*args, **kwargs):
        value = step(*args, **kwargs)
        with torch.no_grad():
            actor.network[0].weight[0, 0] = torch.nan
        return value
    monkeypatch.setattr(optimizer, "step", poisoned_step)
    with pytest.raises(FloatingPointError) as caught:
        training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p)
    r = caught.value.phase_record
    assert counts == dict(optimizer_steps=1, sample_presentations=4)
    assert r["optimizer_steps"] == 1 and not r["parameters_finite"]
    assert r["movement"] is None and r["count_branch_movement"] is None


def test_completed_epoch_progress_failure_preserves_epoch(monkeypatch):
    actor, p = model(), Small(); optimizer = make_optimizer(actor, p)
    x, y = data(); counts = {}
    def progress(phase, row):
        assert phase == 0 and row["status"] == "COMPLETE"
        raise RuntimeError("synthetic serialization failure")
    with pytest.raises(RuntimeError) as caught:
        training.train_phase(actor, optimizer, x[:8], y[:8], 0, counts, protocol=p, progress=progress)
    assert counts == dict(optimizer_steps=2, sample_presentations=8)
    assert caught.value.phase_record["epochs"][0]["status"] == "COMPLETE"
    assert caught.value.phase_record["adam_step_values"] == [2] * 7
