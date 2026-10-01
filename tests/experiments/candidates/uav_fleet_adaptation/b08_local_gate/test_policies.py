"""Synthetic original/zero-count N5 identity; no production assets or worlds."""
import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers as original
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student
from experiments.candidates.uav_fleet_adaptation.b02.policies import StudentPolicy, categorical_probabilities
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import make_inherited
from experiments.candidates.uav_fleet_adaptation.b06_count_development.policies import StudentPolicy as CountPolicy
from experiments.candidates.uav_fleet_adaptation.b06_count_development.controllers import MemoC as CountC
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.targets import build_targets
from experiments.candidates.uav_fleet_adaptation.b08_local_gate import policies


def row(kind="visible"):
    obs = np.zeros(104, dtype=np.float32)
    obs[:3] = [.1, .1, .0]
    if kind != "censored":
        obs[3:9] = [.02, .03, .8, -.04, .01, .7]
        obs[63:67] = [.3, .4, .5, .8]  # Three peers remain hidden.
        if kind == "weak":
            obs[[5, 8]] = .001
    return obs


@pytest.mark.parametrize("kind", ["visible", "weak", "censored"])
@pytest.mark.parametrize("parent", ["P0", "Bstar0"])
def test_original_forward_hidden_and_zero_count_identity(kind, parent):
    actor = make_student(61).eval()
    count_actor = make_inherited(actor.state_dict(), 62).eval()
    observed = row(kind)
    reference = StudentPolicy(actor, world=103, agent=2, sampled=True, sampling_root=105)
    counted = CountPolicy(count_actor, n=5, world=103, agent=2, sampling_root=105,
                          temperature=2. if parent == "Bstar0" else 1.)
    policy = policies.Policy(parent, actor, world=103, agent=2, sampling_root=105)
    calls = []
    handle = actor.register_forward_pre_hook(lambda module, args: calls.append(args[0].shape))
    before_rng = torch.random.get_rng_state().clone()
    before_state = {k: v.clone() for k, v in actor.state_dict().items()}
    first = policy.query(observed, 0, 0)
    observed[-1] = 4 / 256
    second = policy.query(observed, 4, 0)
    handle.remove()
    assert calls == [torch.Size([1, 114])]
    assert not actor.network[3]._forward_hooks
    ref = reference.query(observed, 0, 0)
    count = counted.query(observed, 0, 0)
    with torch.inference_mode():
        hidden = actor.network[:4](torch.from_numpy(first["features"]).reshape(1, 114))[0].numpy()
    for key in ("features", "logits"):
        np.testing.assert_array_equal(first[key], ref[key])
        np.testing.assert_array_equal(first[key], count[key])
    np.testing.assert_array_equal(first["hidden"], hidden)
    np.testing.assert_array_equal(first["probabilities"], count["probabilities"])
    assert first["features"].dtype == first["hidden"].dtype == np.float32
    assert first["fallback"] == (kind != "visible")
    assert first["next_nav"] == (1 if first["fallback"] else 0)
    np.testing.assert_array_equal(first["features"][103:113], np.eye(10, dtype=np.float32)[0])
    for answer, tick in ((first, 0), (second, 4)):
        expected = np.random.default_rng(np.random.SeedSequence([105, 103, tick, 2])).random()
        cdf = np.cumsum(answer["probabilities"], dtype=np.float64); cdf[-1] = 1.
        assert answer["innovation"] == expected
        assert answer["action_index"] == np.searchsorted(cdf, expected, side="right")
    assert first["innovation"] != second["innovation"] and second["memo_hit"]
    second["hidden"][:] = -99
    third = policy.query(observed, 8, 0)
    np.testing.assert_array_equal(third["hidden"], hidden)
    assert policy.counters["neural_rows"] == policy.counters["helper_calls"] == 1
    assert policy.counters["cache_array_bytes"] == 4 * (114 + 27 + 128)
    assert policy.counters["sampled_draws"] == policy.counters["law_evaluations"] == 3
    policy.query(observed, 12, 1)
    assert policy.counters["misses"] == 2
    assert torch.equal(before_rng, torch.random.get_rng_state())
    for k, v in actor.state_dict().items():
        assert torch.equal(before_state[k], v)


@pytest.mark.parametrize("kind", ["visible", "weak", "censored"])
def test_hdirect_c_only_helper_and_both_targets_every_call(kind, monkeypatch):
    actor = make_student(63).eval()
    observed = row(kind)
    ref = original.MemoC().query(observed, 0, 0)
    count = CountC(5).query(observed, 0, 0)
    for key in ("features", "scores", "command", "served"):
        np.testing.assert_array_equal(ref[key], count[key])
    calls, forwards = [], []
    def targets(*args):
        calls.append(args)
        return build_targets(*args)
    def forbidden(*args, **kwargs):
        raise AssertionError("Hdirect must never instantiate a StudentPolicy/helper")
    monkeypatch.setattr(policies, "_HiddenStudentPolicy", forbidden)
    monkeypatch.setattr(policies, "build_targets", targets)
    handle = actor.register_forward_pre_hook(lambda module, args: forwards.append(1))
    policy = policies.Policy("Hdirect", actor, world=103, agent=0, sampling_root=7)
    first = policy.query(observed, 0, 0)
    second = policy.query(observed, 4, 0)
    handle.remove()
    assert len(calls) == 2 and len(forwards) == 1
    for key in ("features", "scores", "served"):
        np.testing.assert_array_equal(first[key], ref[key])
    with torch.inference_mode():
        x = torch.from_numpy(ref["features"]).reshape(1, 114)
        logits, hidden = actor(x)[0].numpy(), actor.network[:4](x)[0].numpy()
    np.testing.assert_array_equal(first["logits"], logits)
    np.testing.assert_array_equal(first["hidden"], hidden)
    expected = .9 * categorical_probabilities(logits)
    expected[ref["action_index"]] += .1
    np.testing.assert_array_equal(first["probabilities"], expected)
    assert second["memo_hit"] and second["innovation"] != first["innovation"]
    assert policy.counters["helper_calls"] == 0
    assert policy.counters["trajectories"] == 27 and policy.counters["model_ticks"] == 108
    assert policy.counters["target_vectors"] == 4 and policy.counters["neural_rows"] == 1
    assert policy.counters["cache_array_bytes"] == sum(v.nbytes for v in ref.values() if isinstance(v, np.ndarray)) + 4 * (27 + 128)
    assert not actor.network[3]._forward_hooks


@pytest.mark.parametrize("parent", ["C", "Q10", "G"])
@pytest.mark.parametrize("kind", ["visible", "censored"])
def test_original_ordinary_laws(parent, kind):
    policy = policies.Policy(parent, None, world=103, agent=1, sampling_root=None if parent == "C" else 9)
    reference = original.MemoC().query(row(kind), 0, 0)
    for tick in (0, 4):
        answer = policy.query(row(kind), tick, 0)
        expected = (policies.score_tail_probabilities(reference["scores"], reference["action_index"])
                    if parent == "G" else policies.q_probabilities(reference["action_index"], 0 if parent == "C" else .1))
        np.testing.assert_array_equal(answer["probabilities"], expected)
        assert answer["c_index"] == reference["action_index"]
        assert "hidden" not in answer
    assert policy.counters["neural_rows"] == policy.counters["helper_calls"] == 0
    assert policy.counters["sampled_draws"] == (0 if parent == "C" else 2)
    assert policy.counters["score_tail_evaluations"] == (2 if parent == "G" else 0)


def test_all27_aliases_remain_categories_and_right_search(monkeypatch):
    actor = make_student(64).eval()
    with torch.no_grad():
        for parameter in actor.parameters():
            parameter.zero_()
    policy = policies.Policy("P0", actor, world=1, agent=0, sampling_root=2)
    observed = row("censored")
    observed[:3] = [0, 0, 0]  # Clipping aliases many physical endpoints.
    p = np.full(27, 1 / 27, dtype=np.float64)
    cdf = np.cumsum(p); cdf[-1] = 1.
    for index in range(27):
        uniform = 0. if index == 0 else cdf[index - 1]
        monkeypatch.setattr(policies, "indexed_uniform", lambda *args, u=uniform: u)
        answer = policy.query(observed, index * 4, 0)
        assert answer["action_index"] == index
        np.testing.assert_array_equal(answer["command"], policies.COMMANDS[index])
        np.testing.assert_array_equal(answer["probabilities"], p)
    assert len(np.unique(np.clip(policies.COMMANDS * 30 + [0, 0, 50], [0, 0, 50], [1000, 1000, 150]), axis=0)) < 27
    assert policy.counters["sampled_draws"] == 27 and policy.counters["neural_rows"] == 1


def test_rights_and_hook_cleanup_on_exception(monkeypatch):
    actor = make_student(65)
    for parent, supplied, root in (("C", actor, None), ("P0", None, 1), ("C", None, 1), ("P0", actor, None)):
        with pytest.raises(ValueError):
            policies.Policy(parent, supplied, world=1, agent=0, sampling_root=root)
    with pytest.raises(ValueError):
        policies.Policy("P0", make_inherited(actor.state_dict(), 66), world=1, agent=0, sampling_root=2)
    policy = policies.Policy("P0", actor, world=1, agent=0, sampling_root=2)
    def fail(*args):
        raise RuntimeError("synthetic failure")
    monkeypatch.setattr(actor, "forward", fail)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        policy.query(row(), 0, 0)
    assert not actor.network[3]._forward_hooks


@pytest.mark.parametrize("parent", ["P0", "Hdirect"])
def test_episode_caches_and_agent_innovations_are_private(parent):
    actor = make_student(67).eval()
    policies_by_agent = [policies.Policy(parent, actor, world=103, agent=agent, sampling_root=105)
                         for agent in (0, 1)]
    calls = []
    handle = actor.register_forward_pre_hook(lambda module, args: calls.append(1))
    answers = [policy.query(row(), 0, 0) for policy in policies_by_agent]
    assert len(calls) == 2
    assert answers[0]["innovation"] != answers[1]["innovation"]
    answers[0]["features"][:] = 0
    answers[0]["logits"][:] = 0
    answers[0]["hidden"][:] = -1
    for policy in policies_by_agent:
        cached = policy.query(row(), 4, 0)
        assert cached["memo_hit"]
        assert np.any(cached["features"] != 0) and np.any(cached["logits"] != 0)
        assert np.all(cached["hidden"] >= 0)
        assert policy.counters["requests"] == 2 and policy.counters["neural_rows"] == 1
    handle.remove()
    assert len(calls) == 2 and not actor.network[3]._forward_hooks
