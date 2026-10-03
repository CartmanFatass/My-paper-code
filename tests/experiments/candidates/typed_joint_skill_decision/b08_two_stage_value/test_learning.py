import numpy as np
import pytest
import torch

from experiments.candidates.typed_joint_skill_decision.b08_two_stage_value import features, learning


def test_loss_uniform_world_weight_offset_invariance_singleton_and_padding():
    scores = torch.tensor([[1, 4, 999, 999, 999, 999, 999, 999],
                           [2, 3, 5, 7, 999, 999, 999, 999],
                           [8, 999, 999, 999, 999, 999, 999, 999]], dtype=torch.float32, requires_grad=True)
    valid = torch.tensor([[True]*m+[False]*(8-m) for m in (2, 4, 1)])
    labels = torch.tensor([[10, 12]+[float("nan")]*6, [20, 22, 24, 26]+[float("nan")]*4,
                           [30]+[float("nan")]*7], dtype=torch.float64)
    expected = []
    for row, m in enumerate((2, 4, 1)):
        terms = [(float(scores[row, i].detach()) - float(scores[row, j].detach())
                  - 100*(float(labels[row, i]) - float(labels[row, j]))/460)**2
                 for i in range(m) for j in range(i+1, m)]
        expected.append(sum(terms)/len(terms) if terms else 0.)
    loss = learning.pairwise_loss(scores, labels, valid)
    assert loss.dtype == torch.float64
    assert float(loss.detach()) == pytest.approx(sum(expected)/3, rel=1e-15)
    offsets = torch.tensor([[32.], [-64.], [128.]], dtype=torch.float32)
    assert torch.equal(loss, learning.pairwise_loss(scores + offsets, labels, valid))
    assert torch.equal(loss, learning.pairwise_loss(scores, labels + 512., valid))
    loss.backward()
    assert torch.isfinite(scores.grad).all()
    assert torch.count_nonzero(scores.grad[~valid]) == 0
    assert torch.count_nonzero(scores.grad[2]) == 0
    torch.testing.assert_close(scores.grad.sum(dim=1), torch.zeros(3), atol=1e-7, rtol=0.)


def test_original_double_differences_not_full_value_cast_and_centered_identity():
    scores = torch.zeros((1, 8), dtype=torch.float32, requires_grad=True)
    valid = torch.tensor([[True, True] + [False]*6])
    labels = torch.zeros((1, 8), dtype=torch.float64)
    labels[0, :2] = torch.tensor([1.e8, 1.e8 + 1.e-3], dtype=torch.float64)
    assert labels[0, 0].float() == labels[0, 1].float()
    loss = learning.pairwise_loss(scores, labels, valid)
    assert float(loss.detach()) > 0
    loss.backward(); assert float(scores.grad[0, 0]) > 0 and float(scores.grad[0, 1]) < 0
    scores2 = torch.tensor([[1, 3, -2, 9, 0, 0, 0, 0]], dtype=torch.float32)
    labels2 = torch.tensor([[4, 7, 2, -3, 0, 0, 0, 0]], dtype=torch.float64)
    valid2 = torch.tensor([[True]*4+[False]*4])
    errors = scores2[0, :4].double() - 100*labels2[0, :4]/460
    centered = 2*4/3*((errors-errors.mean()).square().mean())
    torch.testing.assert_close(learning.pairwise_loss(scores2, labels2, valid2), centered, atol=1e-14, rtol=1e-14)


def test_complete_schedule_separate_permutation_rng_and_exposure():
    before = np.random.get_state()
    batches = list(learning.epoch_batches(51))
    after = np.random.get_state()
    assert before[0] == after[0] and np.array_equal(before[1], after[1]) and before[2:] == after[2:]
    assert len(batches) == 2048
    rng = np.random.RandomState(51)
    counts = np.zeros(128, dtype=int)
    for epoch in range(1, 257):
        actual = np.concatenate([indices for e, indices in batches[(epoch-1)*8:epoch*8] if e == epoch])
        np.testing.assert_array_equal(actual, rng.permutation(128))
        np.testing.assert_array_equal(np.sort(actual), np.arange(128))
        counts[actual] += 1
    np.testing.assert_array_equal(counts, np.full(128, 256))


def test_full_fit_control_mock_no_network_fit_or_optimizer_update(monkeypatch):
    """Exercise all control iterations using a zero-cost fake network/Adam/loss.

    This is a schedule fixture, not a 2048-update scientific fit: backward,
    clipping and optimizer are mocks, and no B08 network is constructed.
    """
    old_threads = torch.get_num_threads(); torch.set_num_threads(1)
    try:
        bank = {k: np.zeros((128, *s), dtype=np.float32) for k, s in features.SHAPES.items()}
        counts = 1 + np.arange(128) % 8
        bank["valid"] = np.arange(8)[None] < counts[:, None]
        labels = np.zeros((128, 8), dtype=np.float64)
        ids = list(range(1000, 1128))
        calls, checkpoints, updates = [], [], []
        parameters = [torch.nn.Parameter(torch.zeros(1)) for _ in learning.model.STATE_SHAPES]
        param = parameters[0]
        cpu = [0.]
        real_deepcopy = learning.deepcopy

        def clone_state(module):
            cpu[0] += 2.
            return {"mock": param.detach().clone()}

        def movement(initial, final):
            cpu[0] += 5.
            return {"l2": 0.}

        def identity_copy(value):
            cpu[0] += 7.
            return real_deepcopy(value)

        class FakeModule:
            def parameters(self): return parameters
            def __call__(self, x):
                calls.append(x["U"].shape[0])
                if x["U"].shape[0] == 1: cpu[0] += 3.
                return torch.zeros((x["U"].shape[0], 8), dtype=torch.float32)

        class FakeAdam:
            def __init__(self, supplied_parameters, **kwargs):
                assert all(a is b for a, b in zip(supplied_parameters, parameters))
                assert kwargs == dict(lr=.001, betas=(.9, .999), eps=1e-8, weight_decay=0.)
                self.state = {p: {"step": torch.tensor(0.)} for p in parameters}
            def zero_grad(self, *, set_to_none): assert set_to_none is True
            def step(self):
                for value in self.state.values(): value["step"] += 1

        backwards, clips = [], []
        def clipped(supplied_parameters, maximum, *, error_if_nonfinite):
            assert all(a is b for a, b in zip(supplied_parameters, parameters))
            assert maximum == 1. and error_if_nonfinite
            clips.append(True); return torch.tensor(0.)
        monkeypatch.setattr(learning.model, "build", lambda seed: FakeModule())
        monkeypatch.setattr(learning.model, "clone_state", clone_state)
        monkeypatch.setattr(learning.model, "parameter_movement", movement)
        monkeypatch.setattr(learning, "deepcopy", identity_copy)
        monkeypatch.setattr(learning, "process_time", lambda: cpu[0])
        monkeypatch.setattr(torch.optim, "Adam", FakeAdam)
        monkeypatch.setattr(learning, "pairwise_loss", lambda *a: torch.tensor(0., dtype=torch.float64))
        monkeypatch.setattr(torch.Tensor, "backward", lambda self: backwards.append(True))
        monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", clipped)
        def checkpoint(record):
            cpu[0] += 11.
            checkpoints.append(record)
            assert float(record["state"]["mock"]) == 0
            record["state"]["mock"].fill_(999.)
            record["predictions"].fill(999.)
            record["world_ids"][0] = -1
        def update(record):
            cpu[0] += 13.
            updates.append(record)
        result = learning.fit(bank, labels, ids, init_seed=9, permutation_seed=51,
                              on_checkpoint=checkpoint, on_update=update)
        assert len(backwards) == len(clips) == len(updates) == 2048
        assert calls.count(16) == 2048 and calls.count(1) == 9*128
        assert [r["update"] for r in checkpoints] == list(range(0, 2049, 256))
        for i, record in enumerate(updates, 1):
            assert record["update"] == record["optimizer_counter"] == i
            assert record["actual_optimizer_steps"] == [i] * len(learning.model.STATE_SHAPES)
            assert record["world_ids"] == ids
            assert record["fit_id"] == dict(init_seed=9, permutation_seed=51)
            assert len(record["batch_world_ids"]) == 16
            assert record["batch_world_ids"] == [ids[j] for j in record["batch_indices"]]
            np.testing.assert_array_equal(record["valid_candidates"], counts[record["batch_indices"]])
        metadata = result["metadata"]
        assert metadata["menu_presentations"] == 32768
        assert metadata["candidate_presentations"] == int(counts.sum()) * 256
        assert metadata["pair_presentations"] == int((counts*(counts-1)//2).sum()) * 256
        assert metadata["world_exposure"] == [256]*128 and metadata["world_ids"] == ids
        assert float(result["state"]["mock"]) == float(param) == 0.
        assert metadata["checkpoint_work_cpu_seconds"] == 9*(2 + 128*3 + 5 + 7 + 11)
        assert metadata["update_callback_cpu_seconds"] == 2048*13
        assert "checkpoint_work_cpu_seconds" not in updates[0] and "update_callback_cpu_seconds" not in checkpoints[0]
        # Initial/final clones, update-record construction and final movement
        # remain outside those two nonoverlapping support scopes.
        remaining = cpu[0] - metadata["checkpoint_work_cpu_seconds"] - metadata["update_callback_cpu_seconds"]
        assert remaining == 2 + 2048*7 + 2 + 7 + 5
        class IncompleteAdam(FakeAdam):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.state.pop(parameters[-1])
        monkeypatch.setattr(torch.optim, "Adam", IncompleteAdam)
        with pytest.raises(RuntimeError, match="optimizer counter"):
            learning.fit(bank, labels, ids, init_seed=9, permutation_seed=51,
                         on_checkpoint=checkpoint, on_update=update)
        # No partial-bank fit can reach model/optimizer construction.
        broken = dict(bank); broken["U"] = broken["U"][:127]
        with pytest.raises(ValueError, match="128"): learning.fit(broken, labels, ids, init_seed=9,
                 permutation_seed=51, on_checkpoint=checkpoint, on_update=updates.append)
    finally: torch.set_num_threads(old_threads)
