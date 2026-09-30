"""Source-bound C memoization and the cheaper full-support navigation helper."""
from copy import deepcopy
import hashlib
from numbers import Integral
from pathlib import Path

import numpy as np

from experiments.candidates.uav_local_history.b01 import controller as original

SOURCE_SHA256 = "b5fdfbfe2718ee693c9ed1d7aeb8bbb6c5c59964ec6c56c5bb35be8b685f23d2"
COMMANDS = original.COMMANDS
WAYPOINTS = original.WAYPOINTS
C7_INDICES = np.flatnonzero(np.count_nonzero(COMMANDS, axis=1) <= 1)
C7_COMMANDS = COMMANDS[C7_INDICES]
COUNTER_NAMES = ("requests", "hits", "misses", "trajectories", "model_ticks",
                 "candidate_links", "setup_links", "objective_reductions", "helper_calls",
                 "helper_setup_links", "helper_extreme_links", "cache_entries", "cache_key_bytes",
                 "cache_array_bytes")


def verify_source():
    digest = hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError("original local C source differs from the selected binding")
    return digest


verify_source()


def _row(row):
    row = np.asarray(row, dtype=np.float32)
    if row.shape != (104,) or not np.isfinite(row[:103]).all():
        raise ValueError("requires a finite ordered FP32 local observation of width104")
    if np.count_nonzero(row[63:103].reshape(10, 4)[:, 3] > 0.) > 4:
        raise ValueError("the N5 contract permits at most four visible peers")
    return row


def _nav(nav):
    if isinstance(nav, (bool, np.bool_)) or not isinstance(nav, Integral) or not 0 <= nav < len(WAYPOINTS):
        raise ValueError("predecision navigation must be an integer in0..9")
    return int(nav)


def _tick(t):
    if isinstance(t, (bool, np.bool_)) or not isinstance(t, Integral) or t < 0 or t % 4:
        raise ValueError("only nonnegative four-tick decision boundaries may query controllers")
    return int(t)


def initial_nav(row):
    own, _, _, _ = original._parse(_row(row))
    return int(np.argmin(np.sum((WAYPOINTS - own[:2]) ** 2, axis=1)))


def memo_key(row, nav):
    """Exact ordered103 FP32 values plus one navigation byte; no time/command."""
    return _row(row)[:103].tobytes(order="C") + bytes([_nav(nav)])


def _features(row, nav, fallback):
    onehot = np.zeros(10, dtype=np.float32)
    onehot[nav] = 1.
    return np.concatenate((row[:103], onehot, np.asarray([fallback], dtype=np.float32)))


def _next_nav(own, nav, fallback):
    return ((nav + 1) % len(WAYPOINTS)
            if fallback and np.linalg.norm(WAYPOINTS[nav] - own[:2]) <= 60.0 else nav)


def _setup(own, users, observed_sinr, peers):
    """Keep the original C calibration and its subtraction/addition order."""
    present = original._power(np.concatenate((own[None], peers), axis=0), users)
    peer_power = np.sum(present[1:], axis=0)
    unknown = np.zeros(len(users))
    if len(peers) < 4:
        gamma = 10.0 ** (observed_sinr / 10.0)
        unknown[:] = np.maximum(present[0] / gamma - peer_power - original.NOISE, 0.0)
    return present, unknown


def _sinr(moving_power, present, unknown):
    """Source station order and total-minus-own denominator, including rounding."""
    p, n = present.shape[0] - 1, present.shape[1]
    all_power = np.concatenate((moving_power[..., None, :],
                               np.broadcast_to(present[1:], (*moving_power.shape[:-1], p, n))), axis=-2)
    denominator = np.sum(all_power, axis=-2, keepdims=True) - all_power + unknown + original.NOISE
    return 10.0 * np.log10(all_power / denominator)


def _extreme_positions(own, users):
    """Factor three independent coordinate choices; never rank27 trajectories.

    Iterate clipping like C, rather than replacing it with a differently rounded
    p+30*k expression. For every user, each distance extremum chooses realizable
    coordinates from the same tick. Retain the station that attains each global
    extremum so the original _power expression can evaluate it unchanged.
    """
    choices = np.broadcast_to(own, (3, 3)).copy()
    targets = np.column_stack((users, np.zeros(len(users))))
    nearest, farthest, minimum, maximum = [], [], [], []
    for _ in range(4):
        choices = np.clip(choices + np.asarray((-30., 0., 30.))[:, None],
                          original.BOUNDS_LOW, original.BOUNDS_HIGH)
        squared = (choices[None] - targets[:, None]) ** 2
        low_indices, high_indices = np.argmin(squared, axis=1), np.argmax(squared, axis=1)
        low = choices[low_indices, np.arange(3)]
        high = choices[high_indices, np.arange(3)]
        nearest.append(low)
        farthest.append(high)
        # Match _power: sum horizontal squares first, then add height squared.
        minimum.append(np.sum((low[:, :2] - users) ** 2, axis=1) + low[:, 2] ** 2)
        maximum.append(np.sum((high[:, :2] - users) ** 2, axis=1) + high[:, 2] ** 2)
    nearest, farthest = np.asarray(nearest), np.asarray(farthest)
    user_indices = np.arange(len(users))
    near_tick, far_tick = np.argmin(minimum, axis=0), np.argmax(maximum, axis=0)
    return np.stack((nearest[near_tick, user_indices], farthest[far_tick, user_indices]))


def analyze(row, nav):
    """Lawful114 features and full-support C fallback using at most2*n extreme links."""
    row, nav = _row(row), _nav(nav)
    own, users, observed_sinr, peers = original._parse(row)
    n, p = len(users), len(peers)
    counters = {"helper_calls": 1, "helper_setup_links": 0, "helper_extreme_links": 0}
    if n:
        present, unknown = _setup(own, users, observed_sinr, peers)
        extrema = _extreme_positions(own, users)
        # Paired users broadcast as[n,1,2], avoiding an n-by-n power matrix.
        extreme_power = original._power(extrema, users[:, None, :]).squeeze(-1)
        sinr = _sinr(extreme_power, present, unknown)
        # Own link is maximal at nearest/highest power; peer links at farthest.
        eligible = bool(np.any(sinr[0, 0] >= original.THRESHOLD)
                        or np.any(sinr[1, 1:] >= original.THRESHOLD))
        counters["helper_setup_links"] = (1 + p) * n
        counters["helper_extreme_links"] = 2 * n
    else:
        present, unknown = np.empty((1 + p, 0)), np.empty(0)
        extrema, extreme_power, sinr = np.empty((2, 0, 3)), np.empty((2, 0)), np.empty((2, 1 + p, 0))
        eligible = False
    fallback = not eligible
    return {"features": _features(row, nav, fallback), "next_nav": _next_nav(own, nav, fallback),
            "fallback": fallback, "n_current": n, "n_peers": p, "counters": counters,
            "own": own, "users": users, "peers": peers, "present_power": present,
            "unknown_power": unknown, "extreme_positions": extrema, "extreme_power": extreme_power,
            "extreme_sinr": sinr}


class MemoC:
    """One agent's episode-local cache of unchanged original-C decisions."""

    def __init__(self):
        verify_source()
        self.reset()

    def reset(self):
        self._cache = {}
        self._original = original.LocalController(history=False)
        self.counters = {name: 0 for name in COUNTER_NAMES}

    def _miss(self, row, t, nav):
        self._original._nav_index = nav
        before = self._original.counters.copy()
        command, diag = self._original.act(row, t)
        for target, field in (("trajectories", "trajectories"), ("model_ticks", "model_ticks"),
                              ("candidate_links", "candidate_link_evaluations"),
                              ("setup_links", "setup_link_evaluations"),
                              ("objective_reductions", "objective_reductions")):
            self.counters[target] += self._original.counters[field] - before[field]
        return {"action_index": int(diag["selected_index"]), "command": command,
                "next_nav": int(self._original._nav_index), "fallback": bool(diag["fallback"]),
                "scores": diag["scores"], "served": diag["served_candidates"],
                "n_current": int(diag["n_current"]), "n_peers": int(diag["n_visible_peers"]),
                "features": _features(row, nav, diag["fallback"])}

    def query(self, row, t, nav):
        row, t, nav = _row(row), _tick(t), _nav(nav)
        key = memo_key(row, nav)
        self.counters["requests"] += 1
        if key in self._cache:
            self.counters["hits"] += 1
            hit = True
        else:
            self.counters["misses"] += 1
            self._cache[key] = deepcopy(self._miss(row, t, nav))
            self.counters["cache_entries"] += 1
            self.counters["cache_key_bytes"] += len(key)
            # Actual retained ndarray payload; excludes Python container overhead.
            self.counters["cache_array_bytes"] += sum(
                value.nbytes for value in self._cache[key].values() if isinstance(value, np.ndarray))
            hit = False
        result = deepcopy(self._cache[key])
        result["memo_hit"] = hit
        return result


class MemoC7(MemoC):
    """Seven-command ranking; full-support helper controls fallback/navigation."""

    def _miss(self, row, t, nav):
        analysis = analyze(row, nav)
        for name, value in analysis["counters"].items():
            self.counters[name] += value
        own, n, p = analysis["own"], analysis["n_current"], analysis["n_peers"]
        positions = np.broadcast_to(own, (len(C7_COMMANDS), 3)).copy()
        trajectory = np.empty((len(C7_COMMANDS), 4, 3))
        for step in range(4):
            positions = np.clip(positions + C7_COMMANDS * 30.0, original.BOUNDS_LOW, original.BOUNDS_HIGH)
            trajectory[:, step] = positions
        if n:
            moving = original._power(trajectory, analysis["users"])
            sinr = _sinr(moving, analysis["present_power"], analysis["unknown_power"])
        else:
            sinr = np.empty((len(C7_COMMANDS), 4, 1 + p, 0))
        scores, served = self._original._score(sinr, np.ones(n, dtype=bool))
        if analysis["fallback"]:
            target = np.r_[WAYPOINTS[analysis["next_nav"]], 50.]
            choice = int(np.argmin(np.sum((trajectory[:, -1] - target) ** 2, axis=1)))
        else:
            choice = int(np.argmax(scores))
        self.counters["trajectories"] += len(C7_COMMANDS)
        self.counters["model_ticks"] += 4 * len(C7_COMMANDS)
        self.counters["candidate_links"] += 4 * len(C7_COMMANDS) * n
        self.counters["objective_reductions"] += 4 * len(C7_COMMANDS)
        return {"action_index": int(C7_INDICES[choice]), "command": C7_COMMANDS[choice].copy(),
                "next_nav": analysis["next_nav"], "fallback": analysis["fallback"],
                "scores": scores, "served": served, "n_current": n, "n_peers": p,
                "features": analysis["features"]}
