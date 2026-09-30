"""Artificial weights, cached rows and reduced protocols; no result asset/native."""
from dataclasses import dataclass
import hashlib

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_copy, state_digest
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import (
    CountStudent, make_inherited, make_optimizer, train_phase, checkpoint,
)
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import array_digest


@dataclass(frozen=True)
class ArtificialProtocol:
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


def data(n=16, fixed=False):
    rng = np.random.default_rng(52)
    x = rng.normal(size=(n, 114)).astype(np.float32)
    y = rng.integers(0, 27, size=n)
    counts = np.full(n, 5, dtype=np.int64) if fixed else np.resize(np.array([3, 7], dtype=np.int64), n)
    return x, y, counts


def parent_and_model():
    parent = make_student(9)
    return parent, make_inherited(state_copy(parent), 71)


def test_original_keys_zero_branch_identity_all_counts_and_rng_isolation():
    parent = make_student(9)
    parent_state = state_copy(parent)
    before_rng = torch.random.get_rng_state().clone()
    model = make_inherited(parent_state, 71)
    assert torch.equal(before_rng, torch.random.get_rng_state())
    assert sum(p.numel() for p in model.parameters()) == 34843
    assert set(model.state_dict()) == {*parent_state, "count_weight"}
    assert torch.count_nonzero(model.count_weight) == 0
    assert all(p.requires_grad for p in model.parameters())
    for key in parent_state:
        assert torch.equal(parent_state[key], model.state_dict()[key])
        assert parent_state[key].data_ptr() != model.state_dict()[key].data_ptr()
    x, _, _ = data()
    for fleet_count in range(3, 8):
        n = torch.full((len(x),), fleet_count, dtype=torch.int64)
        torch.testing.assert_close(model(torch.from_numpy(x), n), parent(torch.from_numpy(x)), rtol=0, atol=0)
        torch.testing.assert_close(model(torch.from_numpy(x[0]), fleet_count), parent(torch.from_numpy(x[0])), rtol=0, atol=0)
        torch.testing.assert_close(model(torch.from_numpy(x[:1]), n[:1]), parent(torch.from_numpy(x[:1])), rtol=0, atol=0)


def test_count_gradient_at_initialization_matches_first_bias_and_n5_zero():
    parent, model = parent_and_model()
    x, y, _ = data(8)
    features, labels = torch.from_numpy(x), torch.from_numpy(y)
    loss = torch.nn.functional.cross_entropy(model(features, torch.full((8,), 7)), labels)
    loss.backward()
    assert torch.count_nonzero(model.count_weight.grad) > 0
    torch.testing.assert_close(model.count_weight.grad, model.network[0].bias.grad, rtol=0, atol=0)
    model.zero_grad(set_to_none=True)
    torch.nn.functional.cross_entropy(model(features, torch.full((8,), 5)), labels).backward()
    assert torch.count_nonzero(model.count_weight.grad) == 0
    assert torch.count_nonzero(model.network[0].weight.grad) > 0


def test_ce_stream_independent_reference_order_counts_gradients_and_no_extra_forward():
    parent, model = parent_and_model()
    reference = make_inherited(state_copy(parent), 72)
    protocol = ArtificialProtocol()
    optimizer, ref_optimizer = make_optimizer(model, protocol), make_optimizer(reference, protocol)
    x, y, n = data(8)
    orders, expected_epochs = [], []
    for epoch in range(2):
        order = np.random.default_rng(np.random.SeedSequence([17, 0, epoch])).permutation(len(x))
        orders.append(order)
        confusion = np.zeros((27, 27), dtype=np.int64)
        total_loss = 0.
        for first in range(0, len(order), 4):
            indices = order[first:first + 4]
            ref_optimizer.zero_grad(set_to_none=True)
            # Independent layer composition, with the count term before ReLU.
            h = reference.network[0](torch.tensor(x[indices]))
            h = h + reference.count_weight * torch.tensor((n[indices] - 5) * .5, dtype=torch.float32)[:, None]
            z = reference.network[4](reference.network[3](reference.network[2](reference.network[1](h))))
            loss = torch.nn.functional.cross_entropy(z, torch.tensor(y[indices]))
            total_loss += float(loss.detach()) * 4
            np.add.at(confusion, (y[indices], z.detach().argmax(-1).numpy()), 1)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(reference.parameters(), 1., error_if_nonfinite=True)
            ref_optimizer.step()
        expected_epochs.append((total_loss / len(x), float(np.trace(confusion) / len(x)), confusion))
    actual_inputs, progress = [], []
    hook = model.register_forward_pre_hook(lambda module, inputs: actual_inputs.append((inputs[0].clone(), inputs[1].clone())))
    counts = dict(optimizer_steps=20, sample_presentations=100, unrelated=41)
    record = train_phase(model, optimizer, x, y, n, 0, protocol, counts, 17,
                         progress=lambda phase, row: progress.append((phase, row)))
    hook.remove()
    assert counts == dict(optimizer_steps=24, sample_presentations=116, unrelated=41)
    assert len(actual_inputs) == 4 and all(tuple(features.shape) == (4, 114) for features, _ in actual_inputs)
    all_order = hashlib.sha256()
    for epoch, row in enumerate(record["epochs"]):
        payload = orders[epoch].astype("<i8").tobytes()
        all_order.update(payload)
        assert row["shuffle_sha256"] == hashlib.sha256(payload).hexdigest()
        assert row["stream_cross_entropy"] == expected_epochs[epoch][0]
        assert row["stream_accuracy"] == expected_epochs[epoch][1]
        assert row["sample_presentations"] == row["stream_rows"] == 8 and row["updates"] == 2
        assert row["nonzero_gradient_updates"] == row["count_nonzero_gradient_updates"] == 2
        assert row["zero_gradient_updates"] == row["count_zero_gradient_updates"] == 0
        for batch in range(2):
            indices = orders[epoch][batch * 4:batch * 4 + 4]
            torch.testing.assert_close(actual_inputs[2 * epoch + batch][0], torch.from_numpy(x[indices]), rtol=0, atol=0)
            torch.testing.assert_close(actual_inputs[2 * epoch + batch][1], torch.from_numpy(n[indices]), rtol=0, atol=0)
    np.testing.assert_array_equal(record["epochs"][-1]["stream_confusion"], expected_epochs[-1][2])
    assert record["data_sha256"] == array_digest(x, y, n)
    assert record["all_shuffle_sha256"] == all_order.hexdigest()
    assert len(progress) == 2 and all(phase == 0 for phase, _ in progress)
    assert record["count_branch_movement"]["changed_parameters"] > 0
    assert state_digest(model.state_dict()) == state_digest(reference.state_dict())
    assert record["adam_step_values"] == [4] * len(list(model.parameters()))
    assert not model.training


def test_n5_branch_stays_zero_and_checkpoint_continuity_across_three_phases(tmp_path):
    parent, model = parent_and_model()
    protocol = ArtificialProtocol()
    optimizer = make_optimizer(model, protocol)
    assert not optimizer.state
    for key, expected in dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0, amsgrad=False, foreach=False, fused=False).items():
        assert optimizer.defaults[key] == expected
    x, y, n = data(fixed=True)
    counts = {}
    first = train_phase(model, optimizer, x[:8], y[:8], n[:8], 0, protocol, counts, 17)
    assert first["count_branch_movement"]["l2"] == 0
    assert all(row["count_zero_gradient_updates"] == row["updates"] for row in first["epochs"])
    path = tmp_path / "artificial.pt"
    torch.save(checkpoint(model, optimizer), path)
    payload = torch.load(path, weights_only=True)
    assert payload["parameters"] == 34843 and payload["optimizer_steps"] == 4
    restored = make_inherited(state_copy(parent), 75)
    restored.load_state_dict(payload["state_dict"], strict=True)
    restored_optimizer = make_optimizer(restored, protocol)
    restored_optimizer.load_state_dict(payload["optimizer"])
    restored_counts = dict(counts)
    for phase, size in ((1, 12), (2, 16)):
        result = train_phase(model, optimizer, x[:size], y[:size], n[:size], phase, protocol, counts, 17)
        result2 = train_phase(restored, restored_optimizer, x[:size], y[:size], n[:size], phase, protocol, restored_counts, 17)
        assert result["after_sha256"] == result2["after_sha256"]
        assert result["all_shuffle_sha256"] == result2["all_shuffle_sha256"]
    assert counts == restored_counts == dict(optimizer_steps=11, sample_presentations=44)
    assert checkpoint(model, optimizer)["optimizer_steps"] == 11
    assert torch.count_nonzero(model.count_weight) == 0
    assert torch.count_nonzero(optimizer.state[model.count_weight]["exp_avg"]) == 0
    assert torch.count_nonzero(optimizer.state[model.count_weight]["exp_avg_sq"]) == 0


@pytest.mark.parametrize("case", ["features", "labels", "fractional_labels", "count_shape", "count_range", "count_dtype", "nan"])
def test_invalid_training_data_rejected_before_paid_work(case):
    parent, model = parent_and_model()
    protocol = ArtificialProtocol()
    optimizer = make_optimizer(model, protocol)
    x, y, n = data(8)
    if case == "features":
        x = x[:, :113]
    elif case == "labels":
        y[0] = 27
    elif case == "fractional_labels":
        y = y.astype(np.float64) + .5
    elif case == "count_shape":
        n = n[:, None]
    elif case == "count_range":
        n[0] = 8
    elif case == "count_dtype":
        n = n.astype(np.float32)
    else:
        x[0, 0] = np.nan
    counts = {}
    with pytest.raises(ValueError):
        train_phase(model, optimizer, x, y, n, 0, protocol, counts, 17)
    assert not counts and not optimizer.state


def test_parent_state_and_forward_count_shape_rejection():
    parent, model = parent_and_model()
    bad = state_copy(parent)
    bad["count_weight"] = torch.zeros(128)
    with pytest.raises(ValueError, match="original Student keys"):
        make_inherited(bad, 71)
    bad = state_copy(parent)
    bad["network.0.weight"] = bad["network.0.weight"].double()
    with pytest.raises(ValueError, match="parent tensor"):
        make_inherited(bad, 71)
    with pytest.raises(ValueError):
        model(torch.zeros(2, 114), 5)
    with pytest.raises(ValueError):
        model(torch.zeros(114), 2)
    with pytest.raises(ValueError):
        model(torch.zeros(114), 5.)


def test_optimizer_reset_rejected_and_partial_forward_counts_preserved(monkeypatch):
    parent, model = parent_and_model()
    protocol, counts = ArtificialProtocol(), {}
    x, y, n = data(12)
    optimizer = make_optimizer(model, protocol)
    train_phase(model, optimizer, x[:8], y[:8], n[:8], 0, protocol, counts, 17)
    before = dict(counts)
    with pytest.raises(AssertionError, match="Adam was reset"):
        train_phase(model, make_optimizer(model, protocol), x, y, n, 1, protocol, counts, 17)
    assert counts == before
    original = model.forward
    calls = []
    def fail_second(features, fleet_counts):
        calls.append(1)
        if len(calls) == 2:
            raise FloatingPointError("synthetic partial failure")
        return original(features, fleet_counts)
    monkeypatch.setattr(model, "forward", fail_second)
    with pytest.raises(FloatingPointError) as caught:
        train_phase(model, optimizer, x, y, n, 1, protocol, counts, 17)
    assert counts == dict(optimizer_steps=5, sample_presentations=24)
    record = caught.value.phase_record
    assert record["status"] == "FAILED" and record["optimizer_steps"] == 1 and record["sample_presentations"] == 8
    assert record["epochs"][0]["stream_rows"] == 4
    assert np.sum(record["epochs"][0]["stream_confusion"]) == 4


def test_changed_adam_law_rejected_before_training():
    parent, model = parent_and_model()
    protocol = ArtificialProtocol()
    optimizer = make_optimizer(model, protocol)
    optimizer.param_groups[0]["lr"] = .001
    x, y, n = data(8)
    counts = {}
    with pytest.raises(ValueError, match="Adam configuration"):
        train_phase(model, optimizer, x, y, n, 0, protocol, counts, 17)
    assert not counts and not optimizer.state
