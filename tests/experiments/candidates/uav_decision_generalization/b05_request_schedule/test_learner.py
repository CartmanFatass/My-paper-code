"""Synthetic learner checks only; exactly two actual network gradient updates.

All other update paths use a one-scalar mock scorer, no-op backward/optimizer,
and fixed caches. No world generation, host model, fitted asset or score screen.
"""
import copy
import json
import resource
import time
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.uav_decision_generalization.b05_request_schedule import learner as m


def caches():
    features = np.zeros((4, 303), dtype=np.float32)
    features[:, 0] = (4, 0, -4, 2)
    return features, np.array([1200, 2400, 3600, 4800], dtype=np.float64)


class TinyScorer(torch.nn.Module):
    def __init__(self, coefficient=1):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.tensor(float(coefficient)))

    def forward(self, features):
        return features[:, 0] * self.weight


class MockOptimizer:
    state = {}

    def __init__(self, model, fail=False):
        self.model, self.fail = model, fail

    def zero_grad(self, set_to_none=True):
        self.model.weight.grad = torch.zeros_like(self.model.weight)

    def step(self):
        if self.fail:
            raise RuntimeError("mock optimizer failure")


def mock_learner(monkeypatch):
    result = m.ResidualLearner.__new__(m.ResidualLearner)
    result.online, result.target = TinyScorer(), TinyScorer(2)
    result.target.requires_grad_(False)
    result.optimizer = MockOptimizer(result.online)
    result.fit_index = 0
    result.event_callback = None
    result._event_callback_failed = False
    result.initial = copy.deepcopy(result.online.state_dict())
    result.replay = m.Replay()
    result.sampler = np.random.Generator(np.random.PCG64(np.random.SeedSequence(
        [109259999, 11, 0])))
    result.counters = dict(transition_attempts=0, transitions=0, update_attempts=0, updates=0,
                           backward_attempts=0, backwards=0, optimizer_attempts=0,
                           optimizer_steps=0, initial_target_copy_attempts=1, initial_target_copies=1,
                           target_copy_attempts=0, target_copies=0, update_failures=0)
    result.forward_counts = {}
    result.failed = False
    result.last_update = None
    result.timing = dict(update_wall_s=0., update_cpu_s=0.)
    # Count calls in the learner while avoiding any real backward work.
    monkeypatch.setattr(torch.Tensor, "backward", lambda *_a, **_k: None)
    return result


def test_float64_lexicographic_cost_and_raw_g_ties():
    total = np.array([1 + 1e-10, 1., 1., 2.], dtype=np.float64)
    raw = np.array([0., 8., 7., 0.], dtype=np.float64)
    assert total.astype(np.float32)[0] == total.astype(np.float32)[1]
    assert m.lexicographic_actions(total, raw) == 2
    assert m.lexicographic_actions(np.ones(4), np.ones(4)) == 0
    assert np.array_equal(m.compose_q(raw, np.zeros(4, dtype=np.float32)), raw / 1200)
    with pytest.raises(ValueError):
        m.lexicographic_actions(total.astype(np.float32), raw)


def test_replay_validates_copies_and_refuses_overwrite():
    features, raw = caches()
    replay = m.Replay()
    replay.append(features, raw, 1, 20, None, None, True)
    features[:] = 42
    raw[:] = 9
    assert replay.rows[0][0][0, 0] == 4
    assert replay.rows[0][1][0] == 1200
    assert not replay.rows[0][0].flags.writeable
    assert replay.rows[0][4] is None
    for replacements in ({"features": features.astype(np.float64)},
                         {"raw_g": raw.astype(np.float32)}, {"action": 4},
                         {"cost": 1.5}, {"cost": -1}, {"terminated": 1},
                         {"next_features": features}):
        args = dict(features=features, raw_g=raw, action=0, cost=20,
                    next_features=None, next_raw_g=None, terminated=True)
        args.update(replacements)
        with pytest.raises(ValueError):
            replay.append(**args)
    features[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        replay.append(features, raw, 0, 20, None, None, True)
    replay.rows = [replay.rows[0]] * m.CAPACITY
    with pytest.raises(RuntimeError, match="overwriting"):
        replay.append(*replay.rows[0])


def test_warmup_fit_limit_and_sampler_stream(monkeypatch):
    learner = mock_learner(monkeypatch)
    features, raw = caches()
    update_calls = []
    monkeypatch.setattr(learner, "_update", lambda: update_calls.append(1) or {"mock": True})
    for _ in range(256):
        assert learner.observe(features, raw, 0, 20, terminated=True) is None
    sampler_before = copy.deepcopy(learner.sampler.bit_generator.state)
    assert learner.observe(features, raw, 0, 20, terminated=True) == {"mock": True}
    assert update_calls == [1]
    assert learner.sampler.bit_generator.state == sampler_before
    reference = np.random.Generator(np.random.PCG64(np.random.SeedSequence([109259999, 11, 0])))
    exploration = np.random.Generator(np.random.PCG64(np.random.SeedSequence([109259999, 10, 0])))
    exploration.random(100)
    indices, _ = learner.replay.sample(learner.sampler)
    assert np.array_equal(indices, reference.choice(257, size=128, replace=False))
    assert len(set(indices)) == 128
    learner.counters["transitions"] = m.FIT_TRANSITIONS
    with pytest.raises(RuntimeError, match="allowance"):
        learner.observe(features, raw, 0, 20, terminated=True)
    assert m.FIT_TRANSITIONS - m.WARMUP == 30464
    assert (m.FIT_TRANSITIONS - m.WARMUP) // m.TARGET_PERIOD == 119


def test_duplicate_sampling_refused_before_forward(monkeypatch):
    learner = mock_learner(monkeypatch)
    features, raw = caches()
    for _ in range(128):
        learner.replay.append(features, raw, 0, 20, None, None, True)
    learner.sampler = SimpleNamespace(choice=lambda *_a, **_k: np.zeros(128, dtype=int))
    with pytest.raises(ValueError, match="distinct"):
        learner._update()
    assert learner.counters["update_failures"] == 1
    assert learner.counters["backward_attempts"] == 0
    assert learner.forward_counts == {}


def test_cost_double_q_sign_masks_and_target_selection_mocked(monkeypatch):
    learner = mock_learner(monkeypatch)
    next_features, raw = caches()
    current = np.zeros_like(next_features)
    for index in range(128):
        terminal = index >= 64
        learner.replay.append(current, raw, 0, 2400 if terminal else 1200,
                              None if terminal else next_features,
                              None if terminal else raw, terminal)
    output = learner._update()
    # Online next values [5,2,-1,6] choose action2. Target next=3-8=-5;
    # nonterminal y=1-5=-4, terminal y=2, current prediction=1.
    assert output["target_mean"] == -1.
    assert output["prediction_mean"] == 1.
    assert output["loss"] == 2.5
    assert output["nonterminal_rows"] == 64
    assert learner.forward_counts["update_current"]["rows"] == 128
    assert learner.forward_counts["update_next_online"]["rows"] == 256
    assert learner.forward_counts["update_next_target"]["rows"] == 64
    assert learner.target.weight.grad is None


def test_failed_forward_and_optimizer_attempts_retained(monkeypatch):
    features, raw = caches()
    learner = mock_learner(monkeypatch)
    for _ in range(128):
        learner.replay.append(features, raw, 0, 20, None, None, True)
    def failed_forward(_features):
        raise RuntimeError("mock scorer failure")
    monkeypatch.setattr(learner.online, "forward", failed_forward)
    with pytest.raises(RuntimeError, match="scorer"):
        learner._update()
    assert learner.forward_counts["update_current"] == {
        "attempts": 1, "calls": 0, "attempted_rows": 128, "rows": 0}
    assert learner.counters["backward_attempts"] == 0
    with pytest.raises(RuntimeError, match="failed update"):
        learner.observe(features, raw, 0, 20, terminated=True)
    second = mock_learner(monkeypatch)
    for _ in range(128):
        second.replay.append(features, raw, 0, 20, None, None, True)
    second.optimizer = MockOptimizer(second.online, fail=True)
    with pytest.raises(RuntimeError, match="optimizer"):
        second._update()
    assert second.counters["backward_attempts"] == second.counters["backwards"] == 1
    assert second.counters["optimizer_attempts"] == 1
    assert second.counters["optimizer_steps"] == second.counters["updates"] == 0


def test_numeric_event_order_and_failed_sink_quarantine_mocked(monkeypatch):
    learner = mock_learner(monkeypatch)
    features, raw = caches()
    sequence, snapshots = [], {}
    def numeric_only(value):
        if isinstance(value, dict):
            for child in value.values():
                numeric_only(child)
        else:
            assert isinstance(value, (int, float))
    def callback(event, counts):
        numeric_only(counts)
        sequence.append(event)
        snapshots[event] = copy.deepcopy(counts)
        # A consumer cannot mutate the learner's counters or nested row counts.
        counts["transitions"] = -99
        if counts["forward"]:
            next(iter(counts["forward"].values()))["rows"] = -99
    learner.event_callback = callback
    forward = learner.online.forward
    monkeypatch.setattr(learner.online, "forward", lambda rows:
                        sequence.append("actual.forward") or forward(rows))
    append = learner.replay.append
    monkeypatch.setattr(learner.replay, "append", lambda *args:
                        sequence.append("actual.insert") or append(*args))
    sample = learner.replay.sample
    monkeypatch.setattr(learner.replay, "sample", lambda sampler:
                        sequence.append("actual.sample") or sample(sampler))
    monkeypatch.setattr(torch.Tensor, "backward", lambda *_a, **_k:
                        sequence.append("actual.backward"))
    step = learner.optimizer.step
    monkeypatch.setattr(learner.optimizer, "step", lambda:
                        sequence.append("actual.optimizer") or step())
    target_copy = learner.target.load_state_dict
    monkeypatch.setattr(learner.target, "load_state_dict", lambda state:
                        sequence.append("actual.target_copy") or target_copy(state))
    learner.choose(features, raw)
    learner.observe(features, raw, 0, 20, terminated=True)
    for _ in range(127):
        append(features, raw, 0, 20, None, None, True)
    learner.counters["transitions"] = 128
    learner.counters["updates"] = learner.counters["optimizer_steps"] = 255
    learner._update()
    assert sequence == [
        "forward.collection.attempt", "actual.forward", "forward.collection.complete",
        "transition.attempt", "actual.insert", "transition.complete",
        "update.attempt", "actual.sample", "forward.update_current.attempt",
        "actual.forward", "forward.update_current.complete",
        "backward.attempt", "actual.backward", "backward.complete",
        "optimizer.attempt", "actual.optimizer", "optimizer.complete", "update.complete",
        "target_copy.attempt", "actual.target_copy", "target_copy.complete"]
    assert snapshots["forward.collection.attempt"]["forward"]["collection"] == {
        "attempts": 1, "calls": 0, "attempted_rows": 4, "rows": 0}
    assert snapshots["forward.collection.complete"]["forward"]["collection"]["rows"] == 4
    assert snapshots["transition.attempt"]["transitions"] == 0
    assert snapshots["transition.complete"]["transitions"] == 1
    assert snapshots["backward.attempt"]["backwards"] == 0
    assert snapshots["backward.complete"]["backwards"] == 1
    assert snapshots["optimizer.attempt"]["optimizer_steps"] == 255
    assert snapshots["optimizer.complete"]["optimizer_steps"] == 256
    assert snapshots["target_copy.attempt"]["target_copies"] == 0
    assert snapshots["target_copy.complete"]["target_copies"] == 1
    assert learner.forward_counts["collection"]["rows"] == 4
    assert learner.counters["transitions"] == 128

    failed = mock_learner(monkeypatch)
    for _ in range(128):
        failed.replay.append(features, raw, 0, 20, None, None, True)
    sink_events = []
    def bad_sink(event, counts):
        sink_events.append(event)
        if event == "forward.update_current.attempt":
            raise RuntimeError("mock sink failure")
    failed.event_callback = bad_sink
    monkeypatch.setattr(failed.online, "forward", lambda _rows: pytest.fail("call after failed sink"))
    with pytest.raises(RuntimeError, match="sink failure"):
        failed._update()
    assert sink_events == ["update.attempt", "forward.update_current.attempt"]
    assert failed.failed and failed.counters["update_failures"] == 1
    assert failed.counters["backward_attempts"] == 0
    assert failed.forward_counts["update_current"]["calls"] == 0
    with pytest.raises(RuntimeError, match="previously failed"):
        failed._emit("update.failure")
    assert sink_events == ["update.attempt", "forward.update_current.attempt"]

    scientific_failure = mock_learner(monkeypatch)
    for _ in range(128):
        scientific_failure.replay.append(features, raw, 0, 20, None, None, True)
    failure_events = []
    scientific_failure.event_callback = lambda event, counts: failure_events.append((event, counts))
    scientific_failure.optimizer = MockOptimizer(scientific_failure.online, fail=True)
    with pytest.raises(RuntimeError, match="optimizer failure"):
        scientific_failure._update()
    assert [event for event, _ in failure_events].count("update.failure") == 1
    assert failure_events[-1][0] == "update.failure"
    assert failure_events[-1][1]["update_failures"] == 1
    assert failure_events[-1][1]["optimizer_attempts"] == 1
    assert failure_events[-1][1]["optimizer_steps"] == 0


def test_actual_zero_head_two_updates_copy_and_checkpoint(tmp_path):
    """The only real network backward/optimizer calls in this file, no rerun budget."""
    wall, cpu = time.perf_counter(), time.process_time()
    construction_count = 0
    learner = None
    try:
        global_rng = torch.random.get_rng_state().clone()
        learner = m.ResidualLearner(0)
        construction_count += 1
        assert torch.equal(global_rng, torch.random.get_rng_state())
        certificate = learner.zero_head_certificate()
        assert certificate["exact_zero_head"]
        assert certificate["parameter_count"] == 55553
        assert certificate["parameter_sha256"] == certificate["initial_parameter_sha256"]
        assert learner.metrics()["parameter_motion_l2"] == 0
        features = np.full((4, 303), .25, dtype=np.float32)
        raw = np.array([1200 + 1e-8, 1200, 1200, 2400], dtype=np.float64)
        action, total, residual = learner.choose(features, raw)
        assert action == 1
        assert total.dtype == np.float64
        assert residual.dtype == np.float32
        assert np.array_equal(residual, np.zeros(4, dtype=np.float32))
        assert np.array_equal(total, raw / 1200)
        for _ in range(257):
            learner.replay.append(features, raw, 1, 2400, None, None, True)
        learner.counters["transitions"] = 257
        target_initial = copy.deepcopy(learner.target.state_dict())
        first = learner._update()
        assert first["grad_norm_before_clip"] > 0
        assert first["grad_norm_after_clip"] <= 10
        assert first["loss"] == pytest.approx(.5)
        assert learner.metrics()["parameter_motion_l2"] > 0
        assert all(torch.equal(value, target_initial[key])
                   for key, value in learner.target.state_dict().items())
        # Exact target-copy branch, without 254 extra gradient updates.
        learner.counters["updates"] = learner.counters["optimizer_steps"] = 255
        second = learner._update()
        assert second["update"] == 256
        assert learner.counters["target_copies"] == 1
        assert all(torch.equal(value, learner.online.state_dict()[key])
                   for key, value in learner.target.state_dict().items())
        assert all(not p.requires_grad for p in learner.target.parameters())
        assert all(p.grad is None for p in learner.target.parameters())
        checkpoint = learner.state_dict()
        deployment = learner.deployment_state_dict()
        assert "replay" not in deployment and "optimizer" not in deployment
        assert deployment["certificate"]["exact_zero_head"] is False
        identity = learner.checkpoint_identity()
        checkpoint_path = tmp_path / "synthetic-state.pt"
        torch.save(checkpoint, checkpoint_path)
        restored = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        expected_indices = learner.replay.sample(learner.sampler)[0]
        learner.load_state_dict(restored)
        assert learner.checkpoint_identity() == identity
        assert np.array_equal(learner.replay.sample(learner.sampler)[0], expected_indices)
        corrupt = copy.deepcopy(checkpoint)
        corrupt["fit_index"] = 1
        with pytest.raises(ValueError, match="identity"):
            learner.load_state_dict(corrupt)
        counts = learner.metrics()
        assert counts["backwards"] == counts["optimizer_attempts"] == 2
        assert counts["forward"]["collection"]["rows"] == 4
        assert counts["forward"]["update_current"]["rows"] == 256
        assert "update_next_online" not in counts["forward"]
    finally:
        readings = {"synthetic_only": True, "real_scorer_constructions": construction_count,
                    "schedule_update_counter_override": 255,
                    "wall_s": time.perf_counter() - wall,
                    "cpu_s": time.process_time() - cpu,
                    "child_cpu_s": resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
                    + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime}
        if learner is not None:
            readings["actual_optimizer_steps"] = learner.counters["optimizer_attempts"]
            readings["actual_network_counts"] = learner.metrics()
        print("B05_REAL_SYNTHETIC_DIAGNOSTICS=" + json.dumps(readings, sort_keys=True))
