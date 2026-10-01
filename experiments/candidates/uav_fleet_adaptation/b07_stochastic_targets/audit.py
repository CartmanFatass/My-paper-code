"""Independent saved-native algebra and actual-history policy reconstruction.

No native environment, optimizer, worker Policy, or worker target constructor is
called. Radio/feature requests are only the prospectively purchased reconstructions.
"""
from contextlib import contextmanager
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import (
    _array, _assignment, _equal, _next_nav, _observation, _own, _require,
)
from experiments.candidates.uav_fleet_adaptation.b06_count_development.controllers import (
    COMMANDS, WAYPOINTS, FeatureMemo, MemoC,
)
from .contract import ARMS, DIRECT, NEURAL, ORDINARY, array_digest
from .reading import episode_metrics


@contextmanager
def replay_scope(work, identifier, controllers, helpers):
    """Attach live counters before a query and fold its prefix exactly once."""
    if work.get("inflight") is not None:
        raise ValueError("a reconstruction scope is already active")
    work.setdefault("C_costs", {})
    work.setdefault("helper_costs", {})
    for key in ("scopes_started", "scopes_completed", "scopes_failed"):
        work.setdefault(key, 0)
    work["scopes_started"] += 1
    wall, cpu = time.perf_counter(), time.process_time()
    current = dict(id=identifier, status="INCOMPLETE", C_agents=[p.counters for p in controllers],
                   helper_agents=[p.counters for p in helpers])
    work["inflight"] = current
    try:
        yield current
    except BaseException:
        current["status"] = "FAILED"
        work["scopes_failed"] += 1
        raise
    else:
        current["status"] = "COMPLETE"
        work["scopes_completed"] += 1
    finally:
        c = sum_counts(current["C_agents"])
        helper = sum_counts(current["helper_agents"])
        work["C_costs"] = sum_counts((work["C_costs"], c))
        work["helper_costs"] = sum_counts((work["helper_costs"], helper))
        work["last_scope"] = dict(id=identifier, status=current["status"], C_costs=c, helper_costs=helper,
                                  cpu_seconds=time.process_time() - cpu, wall_seconds=time.perf_counter() - wall)
        work["inflight"] = None


def probability_reference(logits, temperature=1.):
    z = np.asarray(logits, dtype=np.float64) / temperature
    weights = np.exp(z - np.max(z))
    return weights / np.sum(weights, dtype=np.float64)


def target_reference(parent, scores, c_index):
    # Deliberately independent of targets.build_targets and its validators.
    if np.all(scores == scores[0]):
        t = parent.copy()
    else:
        tilted = parent * np.exp((scores - np.max(scores)) / .014)
        t = .9 * parent + .1 * (tilted / np.sum(tilted, dtype=np.float64))
    h = .9 * parent
    h[int(c_index)] += .1
    return t, h


def ordinary_reference(arm, scores, c_index):
    if arm == "C":
        p = np.zeros(27, dtype=np.float64)
        p[c_index] = 1.
    elif arm == "G" and not np.all(scores == scores[0]):
        mask = np.arange(27) != c_index
        s = scores[mask]
        w = np.exp((s - np.max(s)) / .014)
        p = np.empty(27, dtype=np.float64)
        p[mask], p[c_index] = .1 * (w / w.sum(dtype=np.float64)), .9
    else:
        epsilon = .05 if arm == "Q05" else .1
        p = np.full(27, epsilon / 26., dtype=np.float64)
        p[c_index] = 1. - epsilon
    return p


def forward_one(actor, features, counts):
    counts["actor_forward_calls"] += 1
    with torch.inference_mode():
        logits = actor(torch.from_numpy(np.ascontiguousarray(features)).reshape(1, 114),
                       torch.tensor([5], dtype=torch.int64))[0].numpy().copy()
    counts["actor_rows"] += 1
    if logits.shape != (27,) or logits.dtype != np.float32 or not np.isfinite(logits).all():
        raise ValueError("invalid reconstructed neural row")
    return logits


def check_native(raw, row, protocol):
    """Every saved tick: clipping, all-on assignment, reward and local packing."""
    h, n = protocol.horizon, 5
    d = h // 4
    arm, world, tape = row["arm"], row["world"], row["tape"]
    _require(arm in ARMS and row["kind"] == "evaluation" and row["n"] == 5
             and world in protocol.worlds and type(world) is int, "B07 final identity")
    _require(tape is None if arm == "C" else type(tape) is int and tape in (0, 1), "B07 private tape")
    _require(row["id"] == f"evaluation_{arm}_w{world}_t{tape}", "B07 id")
    root = None if arm == "C" else protocol.evaluation_roots[tape]
    temperature = 2. if arm == "Bstar0" else (1. if arm in (*NEURAL, *DIRECT) else None)
    _require(row["sampling_root"] == root and row["temperature"] == temperature, "B07 density identity")
    shapes = {
        "initial_users": ((50, 2), "float64"), "initial_seven_uavs": ((7, 3), "float64"),
        "initial_sinr": ((n, 50), "float64"), "initial_peer_sinr": ((n, n), "float64"),
        "initial_connections": ((n, 50), "bool"), "observations": ((h, n, 104), "float32"),
        "terminal_observation": ((n, 104), "float32"), "commands": ((h, n, 3), "float32"),
        "positions": ((h + 1, n, 3), "float64"), "reward": ((h,), "float64"),
        "served": ((h,), "int64"), "sinr_quality": ((h,), "float64"),
        "sinr": ((h, n, 50), "float64"), "peer_sinr": ((h, n, n), "float64"),
        "connections": ((h, n, 50), "bool"), "transmitter_mask": ((h, n), "bool"),
        "terminated": ((h,), "bool"), "truncated": ((h,), "bool"),
        "decision_ticks": ((d,), "int64"), "nav_pre": ((d, n), "int64"),
        "nav_next": ((d, n), "int64"), "fallback": ((d, n), "bool"),
        "action_index": ((d, n), "int64"), "memo_hit": ((d, n), "bool"),
        "features": ((d, n, 114), "float32"), "n_current": ((d, n), "int64"),
        "n_peers": ((d, n), "int64"), "probabilities": ((d, n, 27), "float64"),
        "innovation": ((d, n), "float64"), "entropy": ((d, n), "float64"),
    }
    if arm not in NEURAL:
        shapes.update(policy_scores=((d, n, 27), "float64"), policy_served=((d, n, 27), "float64"),
                      c_index=((d, n), "int64"))
    if arm in (*NEURAL, *DIRECT):
        shapes["logits"] = ((d, n, 27), "float32")
    if arm in DIRECT:
        shapes["parent_probabilities"] = ((d, n, 27), "float64")
    _require(set(raw) == set(shapes), "B07 exact raw schema")
    for key, (shape, dtype) in shapes.items():
        _array(raw, key, shape, dtype, peer=key in ("peer_sinr", "initial_peer_sinr"))
    _require(np.all((raw["probabilities"] >= 0) & (raw["probabilities"] <= 1))
             and np.all(np.abs(raw["probabilities"].sum(axis=-1) - 1.) <= 5e-14), "B07 probability mass")
    users = np.random.default_rng(np.random.SeedSequence([protocol.layout_root, world, 1])).uniform(0, 1000, (50, 2))
    seven = np.random.default_rng(np.random.SeedSequence([protocol.layout_root, world, 2])).uniform(
        [0., 0., 50.], [1000., 1000., 150.], (7, 3))
    for key, expected in (("initial_users", users), ("initial_seven_uavs", seven), ("positions", seven[:5])):
        _equal(raw[key][0] if key == "positions" else raw[key], expected, "B07 addressed " + key)
    _require(row["initial_state_sha256"] == array_digest(seven[:5], users)
             and row["shared_layout_sha256"] == array_digest(users, seven), "B07 layout hashes")
    _equal(raw["decision_ticks"], np.arange(0, h, 4, dtype=np.int64), "B07 decision clock")
    _require(raw["transmitter_mask"].all() and not raw["truncated"].any(), "B07 all-on/truncation")
    _equal(raw["terminated"], np.arange(1, h + 1) == h, "B07 terminal")
    _equal(raw["initial_connections"], _assignment(raw["initial_sinr"]), "B07 initial assignment")
    for tick in range(h):
        _equal(raw["positions"][tick + 1], np.clip(raw["positions"][tick] + raw["commands"][tick].astype(np.float64) * 30.,
                                                [0., 0., 50.], [1000., 1000., 150.]), "B07 clipped motion")
        assigned = _assignment(raw["sinr"][tick])
        _equal(raw["connections"][tick], assigned, "B07 native assignment")
        service = int(assigned.sum())
        quality = float(np.clip((raw["sinr"][tick][assigned] - 3.) / 30., 0., 1.).sum() / max(service, 1))
        _equal(raw["served"][tick], service, "B07 native served")
        _equal(raw["sinr_quality"][tick], quality, "B07 native quality", tolerance=1e-12)
        _equal(raw["reward"][tick], .7 * service / 50. + .3 * quality, "B07 native reward", tolerance=1e-12)
    for tick in range(h + 1):
        sinr = raw["initial_sinr"] if tick == 0 else raw["sinr"][tick - 1]
        peer = raw["initial_peer_sinr"] if tick == 0 else raw["peer_sinr"][tick - 1]
        obs = raw["observations"][tick] if tick < h else raw["terminal_observation"]
        for agent in range(n):
            _equal(obs[agent], _observation(raw["positions"][tick], users, sinr, peer, agent, tick, h),
                   "B07 local observation packing")
    return dict(saved_ticks=h, observation_rows=(h + 1) * n, decision_rows=d * n)


def check_final_policy(raw, row, actor, counts, work=None):
    """Full C/feature/actor reconstruction on this program's own saved history."""
    arm = row["arm"]
    pure = arm in NEURAL
    _require((actor is None) == (arm in ORDINARY), "reader actor rights")
    bases = [FeatureMemo(5) if pure else MemoC(5) for _ in range(5)]
    work = {} if work is None else work
    with replay_scope(work, row["id"], [] if pure else bases, bases if pure else []):
        return _final_policy_body(raw, row, actor, counts, bases)


def _final_policy_body(raw, row, actor, counts, bases):
    arm, pure = row["arm"], row["arm"] in NEURAL
    navs = [int(np.argmin(np.sum((WAYPOINTS - _own(raw["observations"][0, i])[:2]) ** 2, axis=1))) for i in range(5)]
    expected_costs = []
    max_logits_error = max_score_error = 0.
    for di, tick in enumerate(raw["decision_ticks"]):
        tick = int(tick)
        _equal(raw["nav_pre"][di], navs, "B07 private navigation continuity")
        for agent in range(5):
            obs, nav = raw["observations"][tick, agent], navs[agent]
            counts["helper_requests" if pure else "C_requests"] += 1
            answer = bases[agent].query(obs.copy(), tick, nav)
            for field in ("features", "fallback", "n_current", "n_peers", "memo_hit"):
                _equal(raw[field][di, agent], answer[field], "B07 reconstructed " + field)
            next_nav = _next_nav(_own(obs), nav, bool(answer["fallback"]))
            _equal(answer["next_nav"], next_nav, "B07 independent fallback navigation")
            _equal(raw["nav_next"][di, agent], next_nav, "B07 saved fallback navigation")
            if not pure:
                for field, source in (("policy_scores", "scores"), ("policy_served", "served"), ("c_index", "action_index")):
                    _equal(raw[field][di, agent], answer[source], "B07 reconstructed C " + source,
                           tolerance=1e-12 if field == "policy_scores" else None)
                max_score_error = max(max_score_error, float(np.max(np.abs(raw["policy_scores"][di, agent] - answer["scores"]))))
            if actor is not None:
                logits = forward_one(actor, answer["features"], counts)
                _equal(raw["logits"][di, agent], logits, "B07 reconstructed one-row logits")
                max_logits_error = max(max_logits_error, float(np.max(np.abs(raw["logits"][di, agent] - logits))))
                parent = probability_reference(logits, 2. if arm == "Bstar0" else 1.)
                if pure:
                    p = parent
                else:
                    _equal(raw["parent_probabilities"][di, agent], parent, "B07 direct P0 density", tolerance=5e-14)
                    t, h = target_reference(parent, answer["scores"], answer["action_index"])
                    p = t if arm == "Tdirect" else h
                    if np.all(answer["scores"] == answer["scores"][0]) and arm == "Tdirect":
                        _require(raw["probabilities"][di, agent].tobytes() == parent.tobytes(), "B07 flat T bitwise P0 identity")
            else:
                p = ordinary_reference(arm, answer["scores"], answer["action_index"])
            _equal(raw["probabilities"][di, agent], p, "B07 independent density law", tolerance=5e-14)
            positive = p > 0
            _equal(raw["entropy"][di, agent], float(-np.sum(p[positive] * np.log(p[positive]))),
                   "B07 entropy", tolerance=1e-12)
            uniform = (-1. if arm == "C" else float(np.random.default_rng(np.random.SeedSequence(
                [row["sampling_root"], row["world"], tick, agent])).random()))
            _equal(raw["innovation"][di, agent], uniform, "B07 private fresh innovation")
            if arm == "C":
                choice = int(answer["action_index"])
            else:
                cdf = np.cumsum(p, dtype=np.float64)
                cdf[-1] = 1.
                choice = int(np.searchsorted(cdf, uniform, side="right"))
            _equal(raw["action_index"][di, agent], choice, "B07 ordered inverse-CDF category")
            _equal(raw["commands"][tick:tick + 4, agent], np.tile(COMMANDS[choice], (4, 1)), "B07 held aliases/command")
            navs[agent] = next_nav
    for base in bases:
        cost = dict(base.counters)
        misses, requests = cost["misses"], cost["requests"]
        cost["sampled_draws"] = requests if arm != "C" else 0
        cost["neural_rows"] = misses if actor is not None else 0
        if actor is not None:
            cost["cache_array_bytes"] += misses * 27 * 4
        cost.update(law_evaluations=requests, target_vectors=2 * requests if arm in DIRECT else 0,
                    score_tail_evaluations=requests if arm == "G" else 0)
        expected_costs.append(cost)
    _require(row["policy_counts"] == sum_counts(expected_costs), "B07 actual cached worker cost")
    metrics = episode_metrics(raw)
    for key, expected in metrics.items():
        if isinstance(expected, str):
            _require(row[key] == expected, "B07 metric " + key)
        else:
            _equal(row[key], expected, "B07 metric " + key, tolerance=1e-12 if isinstance(expected, float) else None)
    return dict(metrics=metrics, max_logit_abs_error=max_logits_error, max_score_abs_error=max_score_error,
                C_costs=sum_counts(base.counters for base in bases) if not pure else {},
                helper_costs=sum_counts(base.counters for base in bases) if pure else {})
