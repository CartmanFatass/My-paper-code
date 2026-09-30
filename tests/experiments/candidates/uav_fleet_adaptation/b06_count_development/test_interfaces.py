"""Synthetic geometry, injected hosts and artificial weights only."""
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers as old
from experiments.candidates.uav_fleet_adaptation.b02.model import make_student, state_copy
from experiments.candidates.uav_fleet_adaptation.b06_count_development import controllers as new
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN, new_counts
from experiments.candidates.uav_fleet_adaptation.b06_count_development.environment import initial_layout, make_real, reset_layout
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import make_inherited
from experiments.candidates.uav_fleet_adaptation.b06_count_development.policies import OrdinaryPolicy, StudentPolicy, indexed_uniform


def local_row(users, peers):
    rng = np.random.default_rng(81 + users + peers)
    row = np.zeros(104, dtype=np.float32)
    row[:3] = [.4, .5, .3]
    block = row[3:63].reshape(20, 3)
    block[:users, :2] = rng.uniform(-.35, .35, size=(users, 2))
    block[:users, 2] = rng.uniform(.27, .6, size=users)
    block = row[63:103].reshape(10, 4)
    block[:peers, :3] = rng.uniform(-.3, .3, size=(peers, 3))
    block[:peers, 3] = .6
    return row


@pytest.mark.parametrize("users,peers", [(0, 0), (1, 0), (20, 0), (1, 4), (20, 4), (12, 3)])
def test_n5_full_C_and_analytic_helper_exact_original_law(users, peers):
    row = local_row(users, peers)
    for nav in (0, 4, 9):
        before = old.MemoC().query(row, 0, nav)
        after = new.MemoC(5).query(row, 0, nav)
        for name in ("action_index", "next_nav", "fallback", "n_current", "n_peers"):
            assert before[name] == after[name]
        for name in ("command", "features", "scores", "served"):
            np.testing.assert_array_equal(before[name], after[name])
        before, after = old.analyze(row, nav), new.analyze(row, nav, 5)
        for name in ("features", "unknown_power", "extreme_power", "extreme_sinr"):
            np.testing.assert_array_equal(before[name], after[name])
        assert before["fallback"] == after["fallback"]
        assert before["next_nav"] == after["next_nav"]


def test_count_completeness_and_packed_peer_support():
    own, users = np.array([500., 500., 50.]), np.array([[500., 500.]])
    peers = np.tile([0., 0., 150.], (4, 1))
    observed = np.array([3.])
    present, incomplete = new.setup(own, users, observed, peers, 7)
    _, complete = new.setup(own, users, observed, peers, 5)
    expected = np.maximum(present[0] / (10. ** .3) - present[1:].sum(axis=0) - old.original.NOISE, 0.)
    # Independent scalar power and the vector NumPy power can differ by an
    # FP64 ulp; this check concerns the residual/completeness law, not libm identity.
    np.testing.assert_allclose(incomplete, expected, rtol=4 * np.finfo(np.float64).eps, atol=0)
    assert incomplete[0] > 0 and complete[0] == 0
    assert new.local_row(local_row(4, 6), 7).shape == (104,)
    with pytest.raises(ValueError, match="visible peers"):
        new.local_row(local_row(4, 3), 3)
    for n in (True, 2, 8, 5.):
        with pytest.raises(ValueError):
            new.fleet_count(n)
    # Count is part of cache identity; time is not an input to this static law.
    row = local_row(3, 2)
    assert new.memo_key(row, 4, 3) != new.memo_key(row, 4, 7)
    cache = new.MemoC(7)
    first = cache.query(row, 0, 4)
    row[-1] = .5
    second = cache.query(row, 4, 4)
    assert not first["memo_hit"] and second["memo_hit"]
    assert cache.counters["requests"] == 2 and cache.counters["trajectories"] == 27
    second["scores"].fill(100)
    assert not np.all(cache.query(row, 8, 4)["scores"] == 100)


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7])
def test_helper_fallback_agrees_with_full_support_ranking_at_each_count(n):
    for users in (0, 1, 9, 20):
        for peers in (0, n - 1):
            row = local_row(users, peers)
            c = new.MemoC(n).query(row, 0, 2)
            h = new.analyze(row, 2, n)
            assert c["fallback"] == h["fallback"]
            assert c["next_nav"] == h["next_nav"]
            np.testing.assert_array_equal(c["features"], h["features"])


def test_private_innovations_and_cache_hits_do_not_reuse_categories():
    parent = make_student(42)
    model = make_inherited(state_copy(parent), 43).eval()
    for p in model.parameters():
        torch.nn.init.zeros_(p)
    calls = []
    hook = model.register_forward_pre_hook(lambda m, args: calls.append(args))
    policy = StudentPolicy(model, n=7, world=81, agent=6, sampling_root=91)
    row = local_row(0, 0)
    first, second = policy.query(row, 0, 4), policy.query(row, 4, 4)
    hook.remove()
    assert len(calls) == 1 and calls[0][0].shape == (1, 114)
    assert calls[0][1].tolist() == [7]
    assert second["memo_hit"] and policy.counters["sampled_draws"] == 2
    for tick, result in ((0, first), (4, second)):
        independent = float(np.random.default_rng(np.random.SeedSequence([91, 81, tick, 6])).random())
        assert independent == result["innovation"]
        np.testing.assert_array_equal(result["probabilities"], np.ones(27) / 27.)
    assert first["innovation"] != second["innovation"]
    assert indexed_uniform(91, 81, 0, 2, 3) == indexed_uniform(91, 81, 0, 2, 7)
    with pytest.raises(ValueError):
        indexed_uniform(91, 81, 1, 2, 7)
    with pytest.raises(ValueError):
        indexed_uniform(91, 81, 0, 3, 3)
    greedy = StudentPolicy(model, n=7, world=81, agent=6).query(row, 0, 4)
    assert greedy["action_index"] == 0 and greedy["innovation"] == -1.


def test_ordinary_Q_uses_same_paid_C_mode_and_fixed_perturbation():
    row = local_row(7, 4)
    c = OrdinaryPolicy(n=6, world=71, agent=2).query(row, 0, 3)
    q = OrdinaryPolicy(n=6, world=71, agent=2, sampling_root=99).query(row, 0, 3)
    assert q["mode_index"] == c["action_index"]
    p = np.full(27, .1 / 26.)
    p[c["action_index"]] = .9
    np.testing.assert_array_equal(q["probabilities"], p)
    np.testing.assert_array_equal(q["scores"], c["scores"])


class ArtificialBase:
    """Zero-service array host. No native environment or radio kernel is imported."""
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.n_uavs, self.max_steps = kwargs["n_uavs"], kwargs["max_steps"]
        self.agents = [f"uav_{i}" for i in range(self.n_uavs)]
        self.transmitter_mask = np.ones(self.n_uavs, dtype=bool)
        self.reset()

    def reset(self):
        self.current_step = 0
        self.uav_positions = np.tile([12., 34., 60.], (self.n_uavs, 1))
        self.user_positions = np.full((50, 2), 8.)
        self._begin_path_loss_step()
        self._update_channel_state()

    def _begin_path_loss_step(self):
        self.current = False

    def _update_channel_state(self):
        self.sinr_matrix = np.full((self.n_uavs, 50), -20., dtype=np.float64)
        self.uav_sinr_matrix = np.full((self.n_uavs, self.n_uavs), -20., dtype=np.float64)
        np.fill_diagonal(self.uav_sinr_matrix, -np.inf)
        self.connections = np.zeros((self.n_uavs, 50), dtype=bool)
        self.channel_positions = self.uav_positions.copy()
        self.current = True

    def _vector_channel_state_is_current(self):
        return self.current and np.array_equal(self.channel_positions, self.uav_positions)

    def _get_observation(self, agent):
        i = int(agent.split("_")[1])
        row = np.zeros(104, dtype=np.float32)
        row[:2] = self.channel_positions[i, :2] / 1000.
        row[2] = (self.channel_positions[i, 2] - 50.) / 100.
        row[-1] = self.current_step / self.max_steps
        return {"obs": row}


class ArtificialAdapter:
    def __init__(self, base, seed):
        self.env, self.n_uavs = base, base.n_uavs

    def _dict_to_array(self, values):
        return np.stack([values[a]["obs"] for a in self.env.agents])

    def _state_array(self):
        return np.r_[self.env.uav_positions.ravel(), self.env.user_positions.ravel(), self.env.current_step / self.env.max_steps].astype(np.float32)

    def get_current_state(self):
        return dict(uav_positions=self.env.uav_positions.copy(), user_positions=self.env.user_positions.copy())

    def _obs(self):
        return self._dict_to_array({a: self.env._get_observation(a) for a in self.env.agents})

    def reset(self, seed):
        self.env.reset()
        return self._obs(), dict(state_info=self.get_current_state())

    def step(self, actions):
        self.env.uav_positions = np.clip(self.env.uav_positions + actions.astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        self.env.current_step += 1
        self.env._begin_path_loss_step()
        self.env._update_channel_state()
        global_info = dict(sinr_matrix=self.env.sinr_matrix, connections=self.env.connections, served_users=0)
        info = dict(state_info=self.get_current_state(), rewards_dict={a: 0. for a in self.env.agents},
                    infos_dict={a: {"global": global_info} for a in self.env.agents})
        return self._obs(), 0., self.env.current_step == self.env.max_steps, False, info


def test_count_factory_and_independently_addressed_refresh_pairing():
    found = []
    for n in (3, 5, 7):
        env = make_real(n, 81, base_class=ArtificialBase, adapter_class=ArtificialAdapter)
        assert env.env.kwargs["n_uavs"] == n and env.env.kwargs["max_observed_uavs"] == 10
        assert env.env.kwargs["max_steps"] == 256 and env.env.kwargs["use_shadowing"] is False
        counts = new_counts()
        obs, info, seven = reset_layout(env, 75, FROZEN, counts)
        users = np.random.default_rng(np.random.SeedSequence([FROZEN.layout_root, 75, 1])).uniform(0, 1000, (50, 2))
        full = np.random.default_rng(np.random.SeedSequence([FROZEN.layout_root, 75, 2])).uniform([0, 0, 50], [1000, 1000, 150], (7, 3))
        np.testing.assert_array_equal(users, info["state_info"]["user_positions"])
        np.testing.assert_array_equal(seven, full)
        np.testing.assert_array_equal(info["state_info"]["uav_positions"], full[:n])
        np.testing.assert_array_equal(obs[:, :2], (full[:n, :2] / 1000.).astype(np.float32))
        assert counts["explicit_resets"] == counts["layout_refreshes"] == 1
        assert counts["native_dense_slots"] == 2 * n * (50 + n)
        found.append(info["state_info"])
    for other in found[1:]:
        np.testing.assert_array_equal(found[0]["user_positions"], other["user_positions"])
        np.testing.assert_array_equal(found[0]["uav_positions"], other["uav_positions"][:3])


def test_complete_synthetic_collection_keeps_all_labels_and_greedy_law(tmp_path):
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.collect import collect_episode
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import check_episode
    protocol = SimpleNamespace(horizon=8, period=4, fixture_horizon=8, fixture_world=99,
                               layout_root=41, evaluation_roots=(52, 53))
    protocol.phase_worlds = lambda lineage, phase: (91 + phase,)
    protocol.acquisition_count = lambda arm, index: 7
    env = make_real(7, 81, base_class=ArtificialBase, adapter_class=ArtificialAdapter)
    env.env.max_steps = 8
    (tmp_path / "raw").mkdir()
    counts = new_counts()
    row, cases = collect_episode(env, arm="M", lineage=0, world=91, n=7, out=tmp_path,
                                 protocol=protocol, counts=counts, kind="acquisition", phase=0)
    assert cases[0].shape == (14, 114) and cases[1].shape == cases[2].shape == (14,)
    assert np.all(cases[2] == 7) and counts["expert_labels"] == 14
    assert row["expert_counts"]["requests"] == row["policy_counts"]["requests"] == 14
    with np.load(tmp_path / row["raw"]["path"]) as raw:
        assert check_episode(dict(raw), row, protocol)["decision_rows"] == 14
    model = make_inherited(state_copy(make_student(42)), 43).eval()
    row2, cases2 = collect_episode(env, arm="M", lineage=0, world=92, n=7, out=tmp_path,
                                   protocol=protocol, counts=counts, kind="acquisition", phase=1,
                                   actor=model, policy_sha="synthetic")
    with np.load(tmp_path / row2["raw"]["path"]) as raw:
        assert check_episode(dict(raw), row2, protocol)["decision_rows"] == 14
        np.testing.assert_array_equal(raw["action_index"], np.argmax(raw["logits"], axis=-1))
        assert np.all(raw["innovation"] == -1.) and np.all(raw["terminated"][:-1] == 0)
        assert raw["terminated"][-1] and not np.any(raw["truncated"])
    assert row2["expert_counts"]["requests"] == 14 and cases2[0].shape == (14, 114)
    assert counts["acquisition_episodes"] == 2 and counts["native_steps"] == 16
    assert counts["native_uav_ticks"] == 112


@pytest.mark.parametrize("n,arm,tape", [(4, "C", None), (6, "Q", 1), (5, "P", 0), (4, "Bstar", 1)])
def test_synthetic_final_collector_to_independent_raw_audit(tmp_path, n, arm, tape):
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.collect import collect_episode
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import check_episode
    protocol = SimpleNamespace(horizon=8, period=4, fixture_horizon=8, fixture_world=99,
                               layout_root=41, evaluation_roots=(52, 53), evaluation_worlds=(91,))
    env = make_real(n, 81, base_class=ArtificialBase, adapter_class=ArtificialAdapter)
    env.env.max_steps = 8
    (tmp_path / "raw").mkdir()
    neural = arm in ("P", "Bstar")
    model = make_inherited(state_copy(make_student(42)), 43).eval() if neural else None
    row, cases = collect_episode(env, arm=arm, lineage=0 if neural else None, world=91,
                                 n=n, out=tmp_path, protocol=protocol, counts=new_counts(),
                                 kind="evaluation", tape=tape, actor=model,
                                 policy_sha="synthetic" if neural else None)
    assert cases is None
    with np.load(tmp_path / row["raw"]["path"]) as raw:
        checked = check_episode(dict(raw), row, protocol)
    assert checked["saved_native_steps"] == 8
    assert checked["saved_agent_ticks"] == 8 * n


@pytest.mark.parametrize("phase", [0, 1])
def test_interrupted_collection_retains_paid_prefix_without_double_counting(tmp_path, monkeypatch, phase):
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.collect import collect_episode
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.reading import cost_totals
    protocol = SimpleNamespace(horizon=8, period=4, fixture_horizon=8, fixture_world=99,
                               layout_root=41, evaluation_roots=(52, 53))
    env = make_real(7, 81, base_class=ArtificialBase, adapter_class=ArtificialAdapter)
    env.env.max_steps = 8
    (tmp_path / "raw").mkdir()
    counts, inflight = new_counts(), {}
    actor = make_inherited(state_copy(make_student(42)), 43).eval() if phase else None
    options = dict(env=env, arm="M", lineage=0, n=7, out=tmp_path, protocol=protocol,
                   counts=counts, kind="acquisition", phase=phase, actor=actor, inflight=inflight)
    completed, _ = collect_episode(world=91, **options)
    assert not inflight
    step = env.step

    def fail_after_one_native_tick(actions):
        if env.env.current_step == 1:
            raise ArithmeticError("synthetic interrupted native call")
        return step(actions)

    monkeypatch.setattr(env, "step", fail_after_one_native_tick)
    with pytest.raises(ArithmeticError, match="synthetic interrupted native call"):
        collect_episode(world=92, **options)
    assert counts["native_steps"] == 9 and counts["native_step_calls"] == 10
    assert counts["acquisition_episodes"] == 1 and len(list((tmp_path / "raw").glob("*.npz"))) == 1
    costs = cost_totals([completed], inflight=inflight)
    assert costs["full_C"]["requests"] == 21  # 14 complete +7 partial labels, never phase0 twice.
    assert costs["helper"]["helper_calls"] == completed["policy_counts"].get("helper_calls", 0) + completed["feature_counts"].get("helper_calls", 0) + sum(
        c.get("helper_calls", 0) for name in ("policy_agents", "feature_agents") for c in inflight[name])
    assert costs["student_requests"] == (21 if phase else 0)
    assert costs["neural"].get("neural_rows", 0) == completed["policy_counts"].get("neural_rows", 0) + sum(
        c.get("neural_rows", 0) for c in inflight["policy_agents"])
    assert "interrupted-call internals may be unmeasured" in costs["scope"]
    assert cost_totals([completed])["full_C"]["requests"] == 14
