"""One-episode saved-array proof, without radio, controller or neural queries.

Teacher scores are checked as supplied rankings, not recomputed radio scores.
Learned fallback bits are checked for encoding, cache and navigation consistency;
their numerical helper provenance is checked separately by the bounded reader.
"""
from numbers import Integral

import numpy as np

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, WAYPOINTS
from .contract import array_digest


def _require(condition, name):
    if not condition:
        raise ValueError("B06 saved episode: " + name)


def _equal(actual, expected, name, *, tolerance=None):
    a, b = np.asarray(actual), np.asarray(expected)
    ok = a.shape == b.shape
    if ok:
        ok = (np.array_equal(a, b) if tolerance is None else
              np.allclose(a, b, rtol=0, atol=tolerance))
    _require(ok, name)


def _array(raw, name, shape, dtype, *, peer=False):
    _require(name in raw, "missing " + name)
    value = raw[name]
    _require(isinstance(value, np.ndarray) and value.shape == shape
             and value.dtype == np.dtype(dtype), "shape/dtype " + name)
    if peer:
        allowed = np.broadcast_to(np.eye(shape[-1], dtype=bool), shape)
        _require(np.all(np.isfinite(value) | (allowed & np.isneginf(value))),
                 "nonfinite " + name)
    else:
        _require(np.isfinite(value).all(), "nonfinite " + name)
    return value


def _assignment(sinr):
    # Python tuple sort independently implements descending values/row-major ties.
    n, users = sinr.shape
    result = np.zeros((n, users), dtype=bool)
    loads, taken = [0] * n, set()
    links = sorted(((-float(sinr[i, j]), i, j) for i in range(n)
                    for j in range(users) if sinr[i, j] >= 3.))
    for _, i, j in links:
        if loads[i] < 10 and j not in taken:
            result[i, j], loads[i] = True, loads[i] + 1
            taken.add(j)
    return result


def _observation(positions, users, sinr, peer_sinr, agent, tick, horizon):
    own = positions[agent]
    result = np.zeros(104, dtype=np.float64)
    result[:3] = [own[0] / 1000., own[1] / 1000., (own[2] - 50.) / 100.]
    ordered = sorted((j for j in range(50) if sinr[agent, j] >= 3.),
                     key=lambda j: (-float(sinr[agent, j]), j))[:20]
    for slot, j in enumerate(ordered):
        result[3 + 3 * slot:6 + 3 * slot] = [
            (users[j, 0] - own[0]) / 1000., (users[j, 1] - own[1]) / 1000.,
            np.clip((sinr[agent, j] + 10.) / 50., 0., 1.)]
    peers = sorted((j for j in range(len(positions))
                    if j != agent and peer_sinr[agent, j] >= 3.),
                   key=lambda j: (-float(peer_sinr[agent, j]), j))
    for slot, j in enumerate(peers):
        result[63 + 4 * slot:67 + 4 * slot] = [
            (positions[j, 0] - own[0]) / 1000.,
            (positions[j, 1] - own[1]) / 1000.,
            (positions[j, 2] - own[2]) / 100.,
            np.clip((peer_sinr[agent, j] + 10.) / 50., 0., 1.)]
    result[-1] = tick / horizon
    return result.astype(np.float32)


def _own(observation):
    return np.array([float(observation[0]) * 1000., float(observation[1]) * 1000.,
                     50. + float(observation[2]) * 100.])


def _next_nav(own, nav, fallback):
    return ((nav + 1) % 10 if fallback
            and np.linalg.norm(WAYPOINTS[nav] - own[:2]) <= 60. else nav)


def _ranking(scores, served, own, nav, fallback, users, peers):
    _require(np.all(served >= 0) and np.all(served <= (1 + peers) * min(users, 10))
             and np.array_equal(served * 4., np.floor(served * 4.)), "teacher served range")
    lower = .7 * served / 50.
    _require(np.all(scores >= lower - 1e-12) and np.all(scores <= lower + .3 + 1e-12)
             and np.all(scores[served == 0.] == 0.), "teacher score range")
    _require(fallback == bool(np.all(served == 0.)), "teacher fallback support")
    if not fallback:
        return int(np.argmax(scores))
    # No radio evaluation: only the declared 27 four-tick clipped endpoints.
    endpoints = np.broadcast_to(own, (27, 3)).copy()
    for _ in range(4):
        endpoints = np.clip(endpoints + COMMANDS * 30., [0., 0., 50.], [1000., 1000., 150.])
    target = np.r_[WAYPOINTS[_next_nav(own, nav, True)], 50.]
    return int(np.argmin(np.sum((endpoints - target) ** 2, axis=1)))


_C_NAMES = ("requests", "hits", "misses", "trajectories", "model_ticks", "candidate_links",
            "setup_links", "objective_reductions", "helper_calls", "helper_setup_links",
            "helper_extreme_links", "cache_entries", "cache_key_bytes", "cache_array_bytes")
_HELPER_NAMES = ("requests", "hits", "misses", "helper_calls", "helper_setup_links",
                 "helper_extreme_links", "cache_entries", "cache_key_bytes", "cache_array_bytes")


def _counts(kind, *, draws=False):
    names = _C_NAMES if kind == "C" else _HELPER_NAMES
    result = dict.fromkeys(names, 0)
    if kind == "student":
        result["neural_rows"] = 0
    if draws or kind == "student":
        result["sampled_draws"] = 0
    return result


def _charge(counts, kind, hit, users, peers, stochastic=False):
    counts["requests"] += 1
    counts["hits" if hit else "misses"] += 1
    if "sampled_draws" in counts:
        counts["sampled_draws"] += int(stochastic)
    if hit:
        return
    counts["cache_entries"] += 1
    counts["cache_key_bytes"] += 414
    counts["cache_array_bytes"] += {"C": 900, "student": 564, "feature": 456}[kind]
    if kind == "C":
        for key, value in dict(trajectories=27, model_ticks=108, candidate_links=108 * users,
                               setup_links=(1 + peers) * users, objective_reductions=108).items():
            counts[key] += value
    else:
        counts["helper_calls"] += 1
        counts["helper_setup_links"] += (1 + peers) * users
        counts["helper_extreme_links"] += 2 * users
        if kind == "student":
            counts["neural_rows"] += 1


def _memo(cache, key, payload, hit, name):
    _require(hit == (key in cache), name + " memo_hit")
    if hit:
        for field, value in payload.items():
            _equal(value, cache[key][field], name + " cached " + field)
    else:
        cache[key] = {field: np.asarray(value).copy() for field, value in payload.items()}


def _metrics(raw):
    rewards, served, quality, positions = (raw[k] for k in ("reward", "served", "sinr_quality", "positions"))
    moves = np.diff(positions, axis=0)
    post = positions[1:]
    peers = raw["n_peers"]
    longest = current = 0
    for count in served:
        current = current + 1 if count == 0 else 0
        longest = max(longest, current)
    result = dict(steps=len(rewards), J=float(rewards.mean()), return_sum=float(rewards.sum()),
                  mean_served=float(served.mean()), service_p10=float(np.quantile(served, .1)),
                  min_served=int(served.min()), zero_service_steps=int(np.count_nonzero(served == 0)),
                  mean_sinr_quality=float(quality.mean()), coverage_reward=float(.7 * served.mean() / 50),
                  quality_reward=float(.3 * quality.mean()),
                  mean_path_length_m=float(np.linalg.norm(moves, axis=-1).sum(axis=0).mean()),
                  xy_boundary_uav_steps=int(np.count_nonzero(
                      (post[..., 0] <= .001) | (post[..., 0] >= 999.999)
                      | (post[..., 1] <= .001) | (post[..., 1] >= 999.999))),
                  lower_altitude_uav_steps=int(np.count_nonzero(post[..., 2] <= 50.001)),
                  fallback_decisions=int(np.count_nonzero(raw["fallback"])),
                  command_counts=np.bincount(raw["action_index"].reshape(-1), minlength=27).tolist(),
                  zero_displacement_uav_ticks=int(np.count_nonzero(np.all(moves == 0, axis=-1))),
                  policy_cache_hits=int(np.count_nonzero(raw["memo_hit"])),
                  policy_decisions=int(raw["action_index"].size), longest_zero_service_streak=longest,
                  visible_peer_counts=np.bincount(peers.reshape(-1), minlength=7).tolist(),
                  more_than_four_peer_decisions=int(np.count_nonzero(peers > 4)),
                  no_visible_peer_decisions=int(np.count_nonzero(peers == 0)),
                  mean_visible_peers=float(peers.mean()), zero_service_ticks=np.flatnonzero(served == 0).tolist())
    if "entropy" in raw:
        result["mean_entropy"] = float(raw["entropy"].mean())
    return result


def check_episode(raw, row, protocol):
    """Validate one saved trajectory and return independently reconstructed metrics.

    Array digests bind layouts and acquisition rows; file/source/checkpoint bindings
    and panel ordering remain the reader's responsibility. Production protocol
    validation is runner-owned; a reduced artificial protocol is supported in tests.
    """
    n = row["n"]
    _require(isinstance(n, Integral) and not isinstance(n, (bool, np.bool_)) and 3 <= n <= 7, "fleet count")
    n = int(n)
    kind, arm, phase, lineage, world = (row[k] for k in ("kind", "arm", "phase", "lineage", "world"))
    training, fixture = kind == "acquisition", kind == "fixture"
    _require(kind in ("acquisition", "evaluation", "fixture") and type(world) is int and world >= 0,
             "episode identity")
    neural = row["neural"]
    _require(type(neural) is bool, "neural flag")
    if training:
        _require(arm in ("F", "M") and type(lineage) is int and lineage in (0, 1)
                 and type(phase) is int and phase in (0, 1, 2) and neural == (phase != 0), "acquisition identity")
        worlds = protocol.phase_worlds(lineage, phase)
        _require(world in worlds and n == protocol.acquisition_count(arm, worlds.index(world)), "acquisition world/count")
    elif fixture:
        _require(arm == "C" and world == protocol.fixture_world and not neural
                 and phase is None and lineage is None, "fixture identity")
    else:
        _require(arm in ("C", "Q", "P", "F", "M", "Bstar") and phase is None
                 and neural == (arm in ("P", "F", "M", "Bstar"))
                 and ((lineage in (0, 1) and type(lineage) is int) if neural else lineage is None)
                 and (arm != "Bstar" or lineage == 0) and n in (4, 5, 6)
                 and world in protocol.evaluation_worlds, "evaluation identity")
    _require(protocol.period == 4, "decision period")
    h = protocol.fixture_horizon if fixture else protocol.horizon
    _require(type(h) is int and h > 0 and h % 4 == 0 and h <= protocol.horizon, "horizon")
    d, stochastic = h // 4, kind == "evaluation" and arm != "C"
    tape = row["tape"]
    _require((type(tape) is int and tape in (0, 1)) if stochastic else tape is None, "private tape")
    root = protocol.evaluation_roots[tape] if stochastic else None
    _require(row["sampling_root"] == root and row["temperature"] == ((2. if arm == "Bstar" else 1.) if neural else None),
             "sampling law")
    expected_id = f"{kind}_L{lineage}_{arm}_N{n}_w{world}_p{phase}_t{tape}"
    _require(row["id"] == expected_id, "row id")
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
        "n_peers": ((d, n), "int64"),
    }
    if neural:
        shapes.update(logits=((d, n, 27), "float32"), probabilities=((d, n, 27), "float64"),
                      innovation=((d, n), "float64"), entropy=((d, n), "float64"))
    if training:
        shapes.update(expert_action_index=((d, n), "int64"), expert_fallback=((d, n), "bool"),
                      expert_nav_next=((d, n), "int64"), expert_memo_hit=((d, n), "bool"),
                      expert_scores=((d, n, 27), "float64"), expert_served=((d, n, 27), "float64"))
    elif not neural:
        shapes.update(policy_scores=((d, n, 27), "float64"), policy_served=((d, n, 27), "float64"),
                      mode_index=((d, n), "int64"), probabilities=((d, n, 27), "float64"),
                      innovation=((d, n), "float64"))
    _require(set(raw) == set(shapes), "raw array schema")
    for name, (shape, dtype) in shapes.items():
        _array(raw, name, shape, dtype, peer=name in ("peer_sinr", "initial_peer_sinr"))
    if "probabilities" in raw:
        _require(np.all((raw["probabilities"] >= 0.) & (raw["probabilities"] <= 1.)),
                 "probability range")
    users = np.random.default_rng(np.random.SeedSequence([protocol.layout_root, world, 1])).uniform(0, 1000, (50, 2))
    seven = np.random.default_rng(np.random.SeedSequence([protocol.layout_root, world, 2])).uniform(
        [0., 0., 50.], [1000., 1000., 150.], (7, 3))
    _equal(raw["initial_users"], users, "addressed users")
    _equal(raw["initial_seven_uavs"], seven, "addressed seven UAVs")
    _equal(raw["positions"][0], seven[:n], "nested initial positions")
    _require(row["initial_state_sha256"] == array_digest(seven[:n], users)
             and row["shared_layout_sha256"] == array_digest(users, seven), "layout digests")
    _equal(raw["decision_ticks"], np.arange(0, h, 4, dtype=np.int64), "decision clock")
    _require(raw["transmitter_mask"].all() and not raw["truncated"].any(), "all-on/truncation")
    _equal(raw["terminated"], np.arange(1, h + 1) == protocol.horizon, "terminal boundary")
    _equal(raw["initial_connections"], _assignment(raw["initial_sinr"]), "initial assignment")
    for tick in range(h):
        _equal(raw["positions"][tick + 1], np.clip(
            raw["positions"][tick] + raw["commands"][tick].astype(np.float64) * 30.,
            [0., 0., 50.], [1000., 1000., 150.]), "clipped motion")
        assigned = _assignment(raw["sinr"][tick])
        _equal(raw["connections"][tick], assigned, "native assignment")
        service = int(assigned.sum())
        quality = float(np.clip((raw["sinr"][tick][assigned] - 3.) / 30., 0, 1).sum() / max(service, 1))
        _equal(raw["served"][tick], service, "native served")
        _equal(raw["sinr_quality"][tick], quality, "native quality", tolerance=1e-12)
        _equal(raw["reward"][tick], .7 * service / 50 + .3 * quality, "native reward", tolerance=1e-12)
    for tick in range(h + 1):
        sinr = raw["initial_sinr"] if tick == 0 else raw["sinr"][tick - 1]
        peer = raw["initial_peer_sinr"] if tick == 0 else raw["peer_sinr"][tick - 1]
        saved = raw["observations"][tick] if tick < h else raw["terminal_observation"]
        for agent in range(n):
            _equal(saved[agent], _observation(raw["positions"][tick], users, sinr, peer, agent, tick, protocol.horizon),
                   "local observation packing")
    policy_kind = "student" if neural else "C"
    policy_counts = _counts(policy_kind, draws=not training)
    expert_counts = _counts("C") if training else {}
    feature_counts = _counts("feature") if fixture or training and phase == 0 else {}
    caches = [{} for _ in range(n)]
    expert_caches = [{} for _ in range(n)]
    fallback_rankings = 0
    navs = [int(np.argmin(np.sum((WAYPOINTS - _own(raw["observations"][0, i])[:2]) ** 2, axis=1))) for i in range(n)]
    for di, tick in enumerate(range(0, h, 4)):
        _equal(raw["nav_pre"][di], navs, "navigation continuity")
        for agent in range(n):
            observation = raw["observations"][tick, agent]
            own, nav = _own(observation), navs[agent]
            fallback = bool(raw["fallback"][di, agent])
            u = int(np.count_nonzero(observation[3:63].reshape(20, 3)[:, 2] > 0))
            p = int(np.count_nonzero(observation[63:103].reshape(10, 4)[:, 3] > 0))
            _equal(raw["n_current"][di, agent], u, "visible users")
            _equal(raw["n_peers"][di, agent], p, "visible peers")
            _require(u != 0 or fallback, "empty-support fallback")
            feature = np.r_[observation[:103], np.eye(10, dtype=np.float32)[nav], np.float32(fallback)]
            _equal(raw["features"][di, agent], feature, "lawful features")
            next_nav = _next_nav(own, nav, fallback)
            _equal(raw["nav_next"][di, agent], next_nav, "fallback navigation")
            action = int(raw["action_index"][di, agent])
            _require(0 <= action < 27, "action index")
            _equal(raw["commands"][tick:tick + 4, agent], np.tile(COMMANDS[action], (4, 1)), "held categorical command")
            key = bytes([n, nav]) + observation[:103].tobytes(order="C")
            payload = dict(features=feature, fallback=fallback, next_nav=next_nav, n_current=u, n_peers=p)
            mode = None
            if training or not neural:
                prefix = "expert_" if training else "policy_"
                scores, served = (raw[prefix + k][di, agent] for k in ("scores", "served"))
                mode = _ranking(scores, served, own, nav, fallback, u, p)
                fallback_rankings += int(fallback)
                teacher_payload = dict(payload, scores=scores, served=served, action_index=mode)
                if training:
                    _equal(raw["expert_fallback"][di, agent], fallback, "expert/helper fallback")
                    _equal(raw["expert_nav_next"][di, agent], next_nav, "expert/helper navigation")
                    _equal(raw["expert_action_index"][di, agent], mode, "expert ranking/label")
                    hit = bool(raw["expert_memo_hit"][di, agent])
                    _memo(expert_caches[agent], key, teacher_payload, hit, "expert")
                    _charge(expert_counts, "C", hit, u, p)
                else:
                    _equal(raw["mode_index"][di, agent], mode, "ordinary ranking/mode")
                if not neural:
                    payload = teacher_payload
            if neural:
                logits = raw["logits"][di, agent]
                payload["logits"] = logits
                z = logits.astype(np.float64) / row["temperature"]
                exps = np.exp(z - np.max(z))
                probabilities = exps / np.sum(exps)
                positive = probabilities > 0
                entropy = float(-np.sum(probabilities[positive] * np.log(probabilities[positive])))
                _equal(raw["entropy"][di, agent], entropy, "nominal entropy", tolerance=1e-12)
            elif not training:
                probabilities = np.full(27, .1 / 26., dtype=np.float64) if stochastic else np.zeros(27, dtype=np.float64)
                probabilities[mode] = .9 if stochastic else 1.
            if neural or not training:
                _equal(raw["probabilities"][di, agent], probabilities, "nominal probabilities", tolerance=5e-14)
                uniform = (float(np.random.default_rng(np.random.SeedSequence([root, world, tick, agent])).random())
                           if stochastic else -1.)
                _equal(raw["innovation"][di, agent], uniform, "private innovation")
                if stochastic:
                    cumulative = np.cumsum(probabilities, dtype=np.float64)
                    cumulative[-1] = 1.
                    expected_action = int(np.searchsorted(cumulative, uniform, side="right"))
                else:
                    expected_action = int(np.argmax(logits)) if neural else mode
            else:
                expected_action = mode
            _equal(action, expected_action, "policy action law")
            hit = bool(raw["memo_hit"][di, agent])
            _memo(caches[agent], key, payload, hit, "policy")
            _charge(policy_counts, policy_kind, hit, u, p, stochastic)
            if feature_counts:
                _charge(feature_counts, "feature", hit, u, p)
            navs[agent] = next_nav
    for name, expected in (("policy_counts", policy_counts), ("expert_counts", expert_counts), ("feature_counts", feature_counts)):
        actual = row[name]
        _require(set(actual) == set(expected) and all(type(v) is int and v >= 0 for v in actual.values())
                 and actual == expected, name)
    digest = (array_digest(raw["features"].reshape(-1, 114).copy(), raw["expert_action_index"].reshape(-1).copy(),
                           np.full(d * n, n, dtype=np.int64)) if training else None)
    _require(row["label_data_sha256"] == digest, "label/count data digest")
    metrics = _metrics(raw)
    for name, expected in metrics.items():
        _equal(row[name], expected, "metric " + name, tolerance=1e-12 if isinstance(expected, float) else None)
    return dict(metrics=metrics, saved_native_steps=h, saved_agent_ticks=h * n, decision_rows=d * n,
                observation_rows=(h + 1) * n, saved_assignment_matrices=h + 1,
                fallback_geometric_rankings=fallback_rankings, policy_counts=policy_counts,
                expert_counts=expert_counts, feature_counts=feature_counts,
                scope="saved-array algebra/packing/motion/ranking/encoding only; no radio, helper, C or neural replay")
