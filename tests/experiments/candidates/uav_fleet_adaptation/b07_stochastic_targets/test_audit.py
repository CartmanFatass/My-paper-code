"""Artificial saved channels/motion exercise the complete policy/native reader.

The fixture never instantiates the native environment or opens a production input.
"""
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import _assignment, _observation
from experiments.candidates.uav_fleet_adaptation.b06_count_development.controllers import initial_nav
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.audit import check_native, check_final_policy
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.contract import ARMS, DIRECT, NEURAL, ORDINARY, array_digest
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.policies import Policy
from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets.reading import episode_metrics


class Actor(torch.nn.Module):
    def forward(self, x, n):
        return torch.arange(27, dtype=torch.float32).reshape(1, 27) / 9


def synthetic_episode(arm, *, visible=False):
    h, world, layout_root = 8, 8101, 8102
    protocol = SimpleNamespace(horizon=h, worlds=(world,), layout_root=layout_root, evaluation_roots=(8103, 8104))
    tape = None if arm == "C" else 1
    root = None if arm == "C" else 8104
    users = np.random.default_rng(np.random.SeedSequence([layout_root, world, 1])).uniform(0, 1000, (50, 2))
    seven = np.random.default_rng(np.random.SeedSequence([layout_root, world, 2])).uniform([0., 0., 50.], [1000., 1000., 150.], (7, 3))
    positions = seven[:5].copy()
    sinr = np.full((5, 50), -20., dtype=np.float64)
    if visible:
        sinr[:, 0] = 4.
    assigned = _assignment(sinr)
    service = int(assigned.sum())
    quality = float(np.clip((sinr[assigned] - 3.) / 30., 0., 1.).sum() / max(service, 1))
    peers = np.full((5, 5), -20., dtype=np.float64); np.fill_diagonal(peers, -np.inf)
    def observe(tick):
        return np.stack([_observation(positions, users, sinr, peers, i, tick, h) for i in range(5)])
    obs = observe(0)
    actor = None if arm in ORDINARY else Actor()
    policies = [Policy(arm, actor, world=world, agent=i, sampling_root=root) for i in range(5)]
    navs = [initial_nav(obs[i], 5) for i in range(5)]
    raw = {k: [] for k in ("observations", "commands", "sinr", "peer_sinr", "connections", "positions",
                            "nav_pre", "nav_next", "fallback", "action_index", "memo_hit", "features", "n_current", "n_peers",
                            "probabilities", "innovation", "entropy")}
    raw["positions"].append(positions.copy())
    if arm not in NEURAL:
        raw.update({k: [] for k in ("policy_scores", "policy_served", "c_index")})
    if arm not in ORDINARY: raw["logits"] = []
    if arm in DIRECT: raw["parent_probabilities"] = []
    decision_names = set(raw) - {"observations", "commands", "sinr", "peer_sinr", "connections", "positions", "nav_pre", "nav_next"}
    for tick in range(h):
        obs = observe(tick)
        if tick % 4 == 0:
            answers = [p.query(obs[i], tick, navs[i]) for i, p in enumerate(policies)]
            raw["nav_pre"].append(np.asarray(navs, dtype=np.int64))
            navs = [int(a["next_nav"]) for a in answers]
            raw["nav_next"].append(np.asarray(navs, dtype=np.int64))
            for key in decision_names:
                source = {"policy_scores": "scores", "policy_served": "served"}.get(key, key)
                raw[key].append([a[source] for a in answers])
            commands = np.stack([a["command"] for a in answers])
        raw["observations"].append(obs)
        raw["commands"].append(commands.copy())
        positions = np.clip(positions + commands.astype(np.float64) * 30., [0, 0, 50], [1000, 1000, 150])
        raw["positions"].append(positions.copy())
        raw["sinr"].append(sinr.copy()); raw["peer_sinr"].append(peers.copy())
        raw["connections"].append(assigned.copy())
    raw = {k: np.asarray(v) for k, v in raw.items()}
    raw.update(initial_users=users, initial_seven_uavs=seven, initial_sinr=sinr.copy(), initial_peer_sinr=peers.copy(),
               initial_connections=assigned.copy(), terminal_observation=observe(h),
               reward=np.full(h, .7 * service / 50. + .3 * quality),
               served=np.full(h, service, dtype=np.int64), sinr_quality=np.full(h, quality),
               transmitter_mask=np.ones((h, 5), dtype=bool), terminated=np.arange(h) == h - 1,
               truncated=np.zeros(h, dtype=bool), decision_ticks=np.arange(0, h, 4, dtype=np.int64))
    row = dict(arm=arm, kind="evaluation", world=world, tape=tape, n=5,
               id=f"evaluation_{arm}_w{world}_t{tape}", sampling_root=root,
               temperature=2. if arm == "Bstar0" else (1. if actor is not None else None),
               initial_state_sha256=array_digest(seven[:5], users), shared_layout_sha256=array_digest(users, seven),
               policy_counts=sum_counts(p.counters for p in policies), **episode_metrics(raw))
    return raw, row, protocol, actor


@pytest.mark.parametrize("arm", ARMS)
@pytest.mark.parametrize("visible", [False, True])
def test_full_synthetic_native_and_policy_reconstruction(arm, visible):
    raw, row, protocol, actor = synthetic_episode(arm, visible=visible)
    native = check_native(raw, row, protocol)
    counts = dict(C_requests=0, helper_requests=0, actor_forward_calls=0, actor_rows=0)
    result = check_final_policy(raw, row, actor, counts)
    assert native == dict(saved_ticks=8, observation_rows=45, decision_rows=10)
    assert counts["C_requests"] == (0 if arm in NEURAL else 10)
    assert counts["helper_requests"] == (10 if arm in NEURAL else 0)
    assert counts["actor_rows"] == (0 if arm in ORDINARY else 10)
    assert result["max_logit_abs_error"] == result["max_score_abs_error"] == 0


@pytest.mark.parametrize("field", ["reward", "observations", "positions", "transmitter_mask", "connections", "terminated"])
def test_native_corruption_is_rejected(field):
    raw, row, protocol, _ = synthetic_episode("C")
    changed = deepcopy(raw)
    if changed[field].dtype == bool:
        changed[field].flat[0] = not changed[field].flat[0]
    else:
        changed[field].flat[0] += .25
    with pytest.raises(ValueError):
        check_native(changed, row, protocol)


@pytest.mark.parametrize("field", ["probabilities", "innovation", "nav_next", "logits", "memo_hit", "parent_probabilities", "c_index"])
def test_actual_direct_law_corruption_is_rejected(field):
    raw, row, _, actor = synthetic_episode("Tdirect")
    changed = deepcopy(raw)
    if changed[field].dtype == bool:
        changed[field].flat[0] = not changed[field].flat[0]
    else:
        changed[field].flat[0] += 1 if np.issubdtype(changed[field].dtype, np.integer) else .01
    counts = dict(C_requests=0, helper_requests=0, actor_forward_calls=0, actor_rows=0)
    with pytest.raises(ValueError):
        check_final_policy(changed, row, actor, counts)


def test_changed_cached_work_count_is_rejected():
    raw, row, _, actor = synthetic_episode("Hdirect")
    row["policy_counts"]["neural_rows"] += 1
    with pytest.raises(ValueError):
        check_final_policy(raw, row, actor, dict(C_requests=0, helper_requests=0, actor_forward_calls=0, actor_rows=0))


def test_failed_final_reconstruction_keeps_actual_partial_work(monkeypatch):
    from experiments.candidates.uav_fleet_adaptation.b07_stochastic_targets import audit
    raw, row, _, actor = synthetic_episode("Tdirect", visible=True)
    original = audit.forward_one
    calls = 0
    def fail_second(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("synthetic post-C actor failure")
        return original(*args)
    monkeypatch.setattr(audit, "forward_one", fail_second)
    work = {}
    counts = dict(C_requests=0, helper_requests=0, actor_forward_calls=0, actor_rows=0)
    with pytest.raises(RuntimeError, match="post-C"):
        audit.check_final_policy(raw, row, actor, counts, work)
    assert counts["C_requests"] == 2 and counts["actor_rows"] == 1
    assert work["C_costs"]["requests"] == work["C_costs"]["misses"] == 2
    assert work["C_costs"]["trajectories"] == 54 and work["C_costs"]["model_ticks"] == 216
    assert work["C_costs"]["candidate_links"] == 216 and work["C_costs"]["setup_links"] == 2
    assert work["scopes_completed"] == 0 and work["scopes_failed"] == 1 and work["inflight"] is None
    assert work["last_scope"]["status"] == "FAILED"
