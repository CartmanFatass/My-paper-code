"""Off-panel synthetic checks of independent original-policy reconstruction."""
import ast
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student
from experiments.candidates.uav_fleet_adaptation.b08_local_gate import policies, reference


def observation(kind):
    row = np.zeros(104, dtype=np.float32)
    row[:3] = [.1, .1, 0.]
    if kind != "censored":
        row[3:9] = [.02, .03, .8, -.04, .01, .7]
        row[63:67] = [.3, .4, .5, .8]
        if kind == "weak":
            row[[5, 8]] = .001
    return row


@pytest.mark.parametrize("parent", ["P0", "Bstar0", "Hdirect", "G", "Q10", "C"])
@pytest.mark.parametrize("kind", ["visible", "weak", "censored"])
def test_complete_answers_counters_and_same_forward(parent, kind):
    actor = make_student(81).eval() if parent in ("P0", "Bstar0", "Hdirect") else None
    root = None if parent == "C" else 105
    worker = policies.Policy(parent, actor, world=103, agent=2, sampling_root=root)
    reader = reference.ReferencePolicy(parent, actor, world=103, agent=2, sampling_root=root)
    obs = observation(kind)
    for tick, nav in ((0, 0), (4, 0), (8, 1), (12, 1)):
        obs[-1] = tick / 256
        expected = worker.query(obs, tick, nav)
        calls = []
        handle = None if actor is None else actor.register_forward_pre_hook(lambda module, args: calls.append(args[0].shape))
        answer = reader.query(obs, tick, nav)
        if handle is not None:
            handle.remove()
        assert set(answer) == set(expected)
        for key in answer:
            if isinstance(answer[key], np.ndarray):
                assert answer[key].dtype == expected[key].dtype
                np.testing.assert_array_equal(answer[key], expected[key], err_msg=key)
            else:
                assert answer[key] == expected[key], key
        assert reader.counters == worker.counters
        assert answer["memo_hit"] == (tick in (4, 12))
        assert len(calls) == int(actor is not None and tick in (0, 8))
        if actor is not None:
            assert not actor.network[3]._forward_hooks
            with torch.inference_mode():
                x = torch.from_numpy(answer["features"]).reshape(1, 114)
                np.testing.assert_array_equal(answer["logits"], actor(x)[0].numpy())
                np.testing.assert_array_equal(answer["hidden"], actor.network[:4](x)[0].numpy())
        assert answer["fallback"] == (kind != "visible")
    assert reader.counters["neural_rows"] == (2 if actor is not None else 0)
    assert reader.counters["target_vectors"] == (8 if parent == "Hdirect" else 0)


def test_runtime_imports_and_laws_do_not_use_new_worker(monkeypatch):
    tree = ast.parse(Path(reference.__file__).read_text())
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    for node in imports:
        names = ([alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""])
        assert not any("b08_local_gate" in name or "collect" in name for name in names)
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0
    def forbidden(*args, **kwargs):
        raise AssertionError("new worker/target/law must not supply reference answers")
    for name in ("Policy", "build_targets", "categorical_index", "categorical_probabilities", "indexed_uniform", "q_probabilities", "score_tail_probabilities"):
        monkeypatch.setattr(policies, name, forbidden)
    for parent in ("P0", "Bstar0", "Hdirect", "G", "Q10", "C"):
        actor = make_student(82).eval() if parent in ("P0", "Bstar0", "Hdirect") else None
        policy = reference.ReferencePolicy(parent, actor, world=103, agent=0, sampling_root=None if parent == "C" else 105)
        answer = policy.query(observation("visible"), 0, 0)
        assert answer["probabilities"].shape == (27,)
        assert np.isfinite(answer["entropy"])


def test_all27_categories_and_exact_cdf_boundary(monkeypatch):
    actor = make_student(83).eval()
    with torch.no_grad():
        for parameter in actor.parameters():
            parameter.zero_()
    reader = reference.ReferencePolicy("P0", actor, world=1, agent=0, sampling_root=2)
    obs = observation("censored")
    obs[:3] = 0
    probabilities = np.full(27, 1 / 27, dtype=np.float64)
    cumulative = np.cumsum(probabilities); cumulative[-1] = 1.
    calls = []
    handle = actor.register_forward_pre_hook(lambda module, args: calls.append(1))
    for index in range(27):
        uniform = 0. if index == 0 else cumulative[index - 1]
        class Generator:
            def random(self):
                return uniform
        def generator(address):
            assert address.entropy == [2, 1, 4 * index, 0]
            return Generator()
        monkeypatch.setattr(reference.np.random, "default_rng", generator)
        answer = reader.query(obs, 4 * index, 0)
        assert answer["action_index"] == index
        assert answer["innovation"] == uniform
        np.testing.assert_array_equal(answer["command"], reference.COMMANDS[index])
    handle.remove()
    assert len(calls) == 1
    assert reader.counters["sampled_draws"] == 27
    assert reader.counters["cache_array_bytes"] == 4 * (114 + 27 + 128)


@pytest.mark.parametrize("parent", ["P0", "Hdirect"])
def test_private_caches_and_hook_cleanup(parent, monkeypatch):
    actor = make_student(84).eval()
    first = reference.ReferencePolicy(parent, actor, world=103, agent=0, sampling_root=105)
    second = reference.ReferencePolicy(parent, actor, world=103, agent=1, sampling_root=105)
    first_answer = first.query(observation("visible"), 0, 0)
    second_answer = second.query(observation("visible"), 0, 0)
    assert first_answer["innovation"] != second_answer["innovation"]
    first_answer["hidden"][:] = -1
    np.testing.assert_array_equal(first.query(observation("visible"), 4, 0)["hidden"], second_answer["hidden"])
    def fail(*args):
        raise RuntimeError("synthetic actor failure")
    monkeypatch.setattr(actor, "forward", fail)
    with pytest.raises(RuntimeError, match="synthetic actor failure"):
        first.query(observation("weak"), 8, 0)
    assert not actor.network[3]._forward_hooks


def test_c_draws_nothing_and_h_preserves_zero_parent_c_mass(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("C cannot draw")
    with monkeypatch.context() as patch:
        patch.setattr(reference.np.random, "default_rng", forbidden)
        policy = reference.ReferencePolicy("C", None, world=103, agent=0, sampling_root=None)
        deterministic = policy.query(observation("censored"), 0, 0)
        assert deterministic["innovation"] == -1.
        assert deterministic["entropy"] == 0.
        assert deterministic["probabilities"][deterministic["c_index"]] == 1.
        assert policy.counters["sampled_draws"] == 0
    actor = make_student(85).eval()
    with torch.no_grad():
        for parameter in actor.parameters():
            parameter.zero_()
        actor.network[4].bias.fill_(-1000.)
        actor.network[4].bias[(deterministic["c_index"] + 1) % 27] = 0.
    h = reference.ReferencePolicy("Hdirect", actor, world=103, agent=0, sampling_root=105)
    answer = h.query(observation("censored"), 0, 0)
    assert answer["parent_probabilities"][answer["c_index"]] == 0.
    assert answer["probabilities"][answer["c_index"]] == .1
    assert answer["probabilities"].sum(dtype=np.float64) == 1.
    assert h.counters["target_vectors"] == 2


def test_independent_t_and_h_formulas_flat_copy_support_and_normalization():
    parent = np.zeros(27, dtype=np.float64)
    parent[[0, 2]] = [.8, .2]
    before = parent.copy()
    flat_t, flat_h = reference._direct_targets(parent, np.zeros(27, dtype=np.float64), 1)
    assert flat_t is not parent and flat_t.tobytes() == parent.tobytes()
    expected_h = np.zeros(27, dtype=np.float64)
    expected_h[:3] = [.72, .1, .18]
    np.testing.assert_allclose(flat_h, expected_h, rtol=0, atol=2e-16)
    scores = np.zeros(27, dtype=np.float64)
    scores[1:3] = .014 * np.log([2., 4.])
    tilted_t, tilted_h = reference._direct_targets(parent, scores, 1)
    expected_t = np.zeros(27, dtype=np.float64)
    expected_t[[0, 2]] = [.77, .23]
    np.testing.assert_allclose(tilted_t, expected_t, rtol=0, atol=2e-16)
    np.testing.assert_array_equal(tilted_h, flat_h)
    assert np.all(tilted_t[parent == 0.] == 0.)
    for target in (flat_t, flat_h, tilted_t, tilted_h):
        assert target.dtype == np.float64 and np.all(target >= 0.)
        assert abs(float(target.sum(dtype=np.float64)) - 1.) <= 5e-14
    np.testing.assert_array_equal(parent, before)


@pytest.mark.parametrize("kind", ["visible", "censored"])
def test_both_target_vectors_constructed_on_h_cache_hits(kind, monkeypatch):
    actor = make_student(86).eval()
    policy = reference.ReferencePolicy("Hdirect", actor, world=103, agent=0, sampling_root=105)
    constructor = reference._direct_targets
    calls = []
    def targets(*args):
        pair = constructor(*args)
        calls.append(pair)
        return pair
    monkeypatch.setattr(reference, "_direct_targets", targets)
    first = policy.query(observation(kind), 0, 0)
    second = policy.query(observation(kind), 4, 0)
    assert len(calls) == 2 and calls[0][0] is not calls[1][0]
    assert not first["memo_hit"] and second["memo_hit"]
    assert policy.counters["target_vectors"] == 4 and policy.counters["neural_rows"] == 1
    for pair, answer in zip(calls, (first, second)):
        assert np.all(pair[0][answer["parent_probabilities"] == 0.] == 0.)
        assert abs(float(pair[0].sum(dtype=np.float64)) - 1.) <= 5e-14
        np.testing.assert_array_equal(pair[1], answer["probabilities"])
