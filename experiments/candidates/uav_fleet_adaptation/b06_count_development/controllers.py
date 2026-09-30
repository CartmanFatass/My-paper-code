"""Count-aware local C and analytic helper; frozen geometry and ranking arithmetic."""
from copy import deepcopy
from numbers import Integral

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02 import controllers as inherited

original = inherited.original
COMMANDS, WAYPOINTS = inherited.COMMANDS, inherited.WAYPOINTS
COUNTER_NAMES = inherited.COUNTER_NAMES


def fleet_count(n):
    if isinstance(n, (bool, np.bool_)) or not isinstance(n, Integral) or not 3 <= n <= 7:
        raise ValueError("B06 fleet count must be an integer in3..7")
    return int(n)


def local_row(row, n):
    n = fleet_count(n)
    row = np.asarray(row, dtype=np.float32)
    if row.shape != (104,) or not np.isfinite(row).all():
        raise ValueError("finite ordered104-field FP32 observation required")
    if np.count_nonzero(row[63:103].reshape(10, 4)[:, 3] > 0) > n - 1:
        raise ValueError("more visible peers than the public fleet permits")
    return row


def memo_key(row, nav, n):
    return bytes([fleet_count(n), inherited._nav(nav)]) + local_row(row, n)[:103].tobytes(order="C")


def initial_nav(row, n):
    own, _, _, _ = original._parse(local_row(row, n))
    return int(np.argmin(np.sum((WAYPOINTS - own[:2]) ** 2, axis=1)))


def setup(own, users, observed_sinr, peers, n):
    """Only the completeness threshold changes from4 to the actual N−1."""
    n = fleet_count(n)
    if len(peers) > n - 1:
        raise ValueError("invalid count-aware calibration support")
    present = original._power(np.concatenate((own[None], peers), axis=0), users)
    peer_power = np.sum(present[1:], axis=0)
    unknown = np.zeros(len(users))
    if len(peers) < n - 1:
        gamma = 10.0 ** (observed_sinr / 10.0)
        unknown[:] = np.maximum(present[0] / gamma - peer_power - original.NOISE, 0.0)
    return present, unknown


def analyze(row, nav, n):
    """Cheaper full-support fallback, preserving the original extrema arithmetic."""
    row, nav = local_row(row, n), inherited._nav(nav)
    own, users, observed_sinr, peers = original._parse(row)
    u, p = len(users), len(peers)
    counters = dict(helper_calls=1, helper_setup_links=0, helper_extreme_links=0)
    if u:
        present, unknown = setup(own, users, observed_sinr, peers, n)
        extrema = inherited._extreme_positions(own, users)
        extreme_power = original._power(extrema, users[:, None, :]).squeeze(-1)
        sinr = inherited._sinr(extreme_power, present, unknown)
        eligible = bool(np.any(sinr[0, 0] >= original.THRESHOLD)
                        or np.any(sinr[1, 1:] >= original.THRESHOLD))
        counters.update(helper_setup_links=(1 + p) * u, helper_extreme_links=2 * u)
    else:
        present, unknown = np.empty((1 + p, 0)), np.empty(0)
        extrema, extreme_power, sinr = np.empty((2, 0, 3)), np.empty((2, 0)), np.empty((2, 1 + p, 0))
        eligible = False
    fallback = not eligible
    return dict(features=inherited._features(row, nav, fallback),
                next_nav=inherited._next_nav(own, nav, fallback), fallback=fallback,
                n_current=u, n_peers=p, counters=counters, own=own, users=users,
                peers=peers, present_power=present, unknown_power=unknown,
                extreme_positions=extrema, extreme_power=extreme_power, extreme_sinr=sinr)


def cached_analysis(result):
    return {name: deepcopy(result[name]) for name in
            ("features", "next_nav", "fallback", "n_current", "n_peers")}


class MemoC:
    """One agent/episode's C_N ranking with an explicit public-count key."""
    def __init__(self, n):
        inherited.verify_source()
        self.n = fleet_count(n)
        self._score_program = original.LocalController(history=False)
        self.cache = {}
        self.counters = {name: 0 for name in COUNTER_NAMES}

    def _miss(self, row, nav):
        own, users, observed_sinr, peers = original._parse(row)
        u, p = len(users), len(peers)
        trajectory = original.LocalController._trajectories(own)
        if u:
            present, unknown = setup(own, users, observed_sinr, peers, self.n)
            moving = original._power(trajectory, users)
            sinr = inherited._sinr(moving, present, unknown)
        else:
            sinr = np.empty((27, 4, 1 + p, 0))
        scores, served = self._score_program._score(sinr, np.ones(u, dtype=bool))
        fallback = bool(np.all(served == 0.))
        next_nav = inherited._next_nav(own, nav, fallback)
        if fallback:
            target = np.r_[WAYPOINTS[next_nav], 50.]
            choice = int(np.argmin(np.sum((trajectory[:, -1] - target) ** 2, axis=1)))
        else:
            choice = int(np.argmax(scores))
        for key, value in dict(trajectories=27, model_ticks=108, candidate_links=108 * u,
                               setup_links=(1 + p) * u, objective_reductions=108).items():
            self.counters[key] += value
        return dict(action_index=choice, command=COMMANDS[choice].copy(), next_nav=next_nav,
                    fallback=fallback, scores=scores, served=served, n_current=u, n_peers=p,
                    features=inherited._features(row, nav, fallback))

    def query(self, row, tick, nav):
        row, tick, nav = local_row(row, self.n), inherited._tick(tick), inherited._nav(nav)
        key = memo_key(row, nav, self.n)
        self.counters["requests"] += 1
        hit = key in self.cache
        if hit:
            self.counters["hits"] += 1
        else:
            self.counters["misses"] += 1
            result = self._miss(row, nav)
            self.cache[key] = deepcopy(result)
            self.counters["cache_entries"] += 1
            self.counters["cache_key_bytes"] += len(key)
            self.counters["cache_array_bytes"] += sum(v.nbytes for v in result.values() if isinstance(v, np.ndarray))
        result = deepcopy(self.cache[key])
        result["memo_hit"] = hit
        return result


class FeatureMemo:
    def __init__(self, n):
        self.n, self.cache = fleet_count(n), {}
        self.counters = dict(requests=0, hits=0, misses=0, helper_calls=0,
                             helper_setup_links=0, helper_extreme_links=0,
                             cache_entries=0, cache_key_bytes=0, cache_array_bytes=0)

    def query(self, row, tick, nav):
        inherited._tick(tick)
        key = memo_key(row, nav, self.n)
        self.counters["requests"] += 1
        hit = key in self.cache
        if hit:
            self.counters["hits"] += 1
        else:
            result = analyze(row, nav, self.n)
            self.cache[key] = cached_analysis(result)
            self.counters["misses"] += 1
            for name, value in result["counters"].items():
                self.counters[name] += int(value)
            self.counters["cache_entries"] += 1
            self.counters["cache_key_bytes"] += len(key)
            self.counters["cache_array_bytes"] += result["features"].nbytes
        result = deepcopy(self.cache[key])
        result["memo_hit"] = hit
        return result
