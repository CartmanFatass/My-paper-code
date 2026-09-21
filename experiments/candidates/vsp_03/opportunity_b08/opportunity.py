"""Fitted public opportunity model and finite-horizon VSP-03 planner.

The fitter consumes only the public packed observations and their episode/time
coordinates.  Target identities are relative to the episode's phase: feature 12
is zero for the phase-first target and one for the other target.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from scipy.optimize import minimize


N_STATES = 42
MAX_DECISION_TIME = 32
HORIZON = 40


def _binary_feature(values: np.ndarray, name: str) -> np.ndarray:
    rounded = np.rint(values)
    if not np.all(np.isfinite(values)) or not np.all(np.abs(values - rounded) <= 1e-6):
        raise ValueError(f"{name} must contain binary values")
    result = rounded.astype(np.int64)
    if np.any((result < 0) | (result > 1)):
        raise ValueError(f"{name} must contain binary values")
    return result


def _observation_states(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return own state, partner state and the current actor's relative slot."""
    own_present = _binary_feature(x[:, 1], "own presence")
    partner_present = _binary_feature(x[:, 6], "partner presence")
    actor_slot = _binary_feature(x[:, 12], "actor identity")

    def encode(present: np.ndarray, scaled_age: np.ndarray, name: str) -> np.ndarray:
        raw_age = scaled_age.astype(np.float64) * HORIZON
        ages = np.rint(raw_age).astype(np.int64)
        if not np.all(np.isfinite(raw_age)) or not np.all(np.abs(raw_age - ages) <= 1e-4):
            raise ValueError(f"{name} age must encode an integer tick")
        if np.any((ages < 0) | (ages > HORIZON)):
            raise ValueError(f"{name} age is outside 0..40")
        return np.where(present == 1, ages + 1, 0)

    own = encode(own_present, x[:, 2], "own")
    partner = encode(partner_present, x[:, 7], "partner")
    return own, partner, actor_slot


class EndpointCounts:
    """Multi-step endpoint counts indexed by ``[gap, source, endpoint]``."""

    def __init__(self) -> None:
        self.counts = np.zeros((HORIZON + 1, N_STATES, N_STATES), dtype=np.int64)
        self.batches = 0
        self.rows = 0

    def add_batch(self, batch: Mapping[str, object]) -> "EndpointCounts":
        """Add one B02 packed rollout batch using only public observation fields."""
        if not isinstance(batch, Mapping) or set(batch) != {"x", "episode_ids", "times"}:
            raise ValueError("batch must contain exactly x, episode_ids, and times")

        x = np.asarray(batch["x"])
        episode_ids = np.asarray(batch["episode_ids"])
        times = np.asarray(batch["times"])
        if x.ndim != 2 or x.shape[1] != 14:
            raise ValueError("x must have shape (rows, 14)")
        n = len(x)
        if episode_ids.shape != (n,) or times.shape != (n,):
            raise ValueError("episode_ids and times must be one-dimensional and match x")
        if not np.all(np.isfinite(x)):
            raise ValueError("x must contain only finite values")

        ids_float = episode_ids.astype(np.float64)
        times_float = times.astype(np.float64)
        ids = np.rint(ids_float).astype(np.int64)
        clock = np.rint(times_float).astype(np.int64)
        if (not np.all(np.isfinite(ids_float)) or
                not np.all(np.abs(ids_float - ids) <= 1e-9) or np.any(ids < 0)):
            raise ValueError("episode_ids must be non-negative integers")
        if (not np.all(np.isfinite(times_float)) or
                not np.all(np.abs(times_float - clock) <= 1e-9) or
                np.any((clock < 0) | (clock > MAX_DECISION_TIME) | (clock % 2 != 0))):
            raise ValueError("times must be even integer decision clocks in 0..32")

        own, partner, actor_slot = _observation_states(x)
        physical = np.empty((n, 2), dtype=np.int64)
        row = np.arange(n)
        physical[row, actor_slot] = own
        physical[row, 1 - actor_slot] = partner

        for episode in np.unique(ids):
            selected = np.flatnonzero(ids == episode)
            order = selected[np.argsort(clock[selected], kind="stable")]
            ordered_times = clock[order]
            if len(order) > 1 and np.any(np.diff(ordered_times) <= 0):
                raise ValueError("each episode must have unique, increasing packed times")
            for left, right in zip(order[:-1], order[1:]):
                gap = int(clock[right] - clock[left])
                for slot in (0, 1):
                    self.counts[gap, physical[left, slot], physical[right, slot]] += 1

        self.batches += 1
        self.rows += n
        return self

    @property
    def transitions(self) -> int:
        return int(self.counts.sum())

    def as_dict(self) -> dict[str, object]:
        nonzero = np.argwhere(self.counts > 0)
        records = [
            {"gap": int(gap), "source": int(source), "end": int(end),
             "count": int(self.counts[gap, source, end])}
            for gap, source, end in nonzero
        ]
        return {
            "shape": [HORIZON + 1, N_STATES, N_STATES],
            "state_encoding": "0=absent; age+1=present",
            "batches": int(self.batches),
            "rows": int(self.rows),
            "transitions": int(self.transitions),
            "records": records,
        }


def transition_matrix(c: float, p: float) -> np.ndarray:
    """One-tick transition matrix for absent plus present ages 0..40."""
    c = float(c)
    p = float(p)
    if not (c > 1 and 0 < p < 1):
        raise ValueError("c must exceed 1 and p must lie strictly between 0 and 1")
    matrix = np.zeros((N_STATES, N_STATES), dtype=np.float64)
    matrix[0, 0] = 1 - p
    matrix[0, 1] = p
    for age in range(HORIZON):
        state = age + 1
        leave = 1 / (age + c)
        matrix[state, 0] = leave
        matrix[state, state + 1] = 1 - leave
    # Age 40 cannot transition again in a valid forty-tick host trajectory.  A
    # self-loop keeps the matrix stochastic for generic table calculations.
    leave = 1 / (HORIZON + c)
    matrix[HORIZON + 1, 0] = leave
    matrix[HORIZON + 1, HORIZON + 1] = 1 - leave
    return matrix


def _negative_log_likelihood(parameters: np.ndarray, counts: np.ndarray) -> float:
    matrix = transition_matrix(parameters[0], parameters[1])
    total = 0.0
    for gap in np.flatnonzero(counts.sum(axis=(1, 2))):
        endpoint = np.linalg.matrix_power(matrix, int(gap))
        source, end = np.nonzero(counts[gap])
        probabilities = endpoint[source, end]
        if np.any(probabilities <= 0):
            return float("inf")
        total -= float(np.dot(counts[gap, source, end], np.log(probabilities)))
    return total


def fit_model(counts: EndpointCounts) -> dict[str, object]:
    """Fit ``c,p`` by the declared multi-step endpoint likelihood."""
    if not isinstance(counts, EndpointCounts):
        raise TypeError("counts must be an EndpointCounts instance")
    if counts.transitions == 0:
        raise ValueError("at least one endpoint transition is required")
    start = np.array([6.0, 0.4], dtype=np.float64)
    initial = _negative_log_likelihood(start, counts.counts)
    if not np.isfinite(initial):
        raise ValueError("counts include a transition impossible under the fitted family")
    result = minimize(
        _negative_log_likelihood,
        start,
        args=(counts.counts,),
        method="L-BFGS-B",
        bounds=((1.01, 30.0), (0.01, 0.99)),
        options={"maxiter": 200, "ftol": 1e-12, "gtol": 1e-7},
    )
    c, p = map(float, result.x)
    serialized = counts.as_dict()
    return {
        "c": c,
        "p": p,
        "success": bool(result.success),
        "message": str(result.message),
        "metadata": {
            "method": "L-BFGS-B",
            "start": {"c": 6.0, "p": 0.4},
            "bounds": {"c": [1.01, 30.0], "p": [0.01, 0.99]},
            "options": {"maxiter": 200, "ftol": 1e-12, "gtol": 1e-7},
            "success": bool(result.success),
            "status": int(result.status),
            "message": str(result.message),
            "iterations": int(result.nit),
            "function_evaluations": int(result.nfev),
            "negative_log_likelihood": float(result.fun),
            "log_likelihood": -float(result.fun),
            "initial_negative_log_likelihood": float(initial),
            "transition_observations": counts.transitions,
        },
        "counts": serialized,
    }


class Planner:
    """Finite-horizon solo and two-job opportunity recursion in native units."""

    def __init__(self, c: float, p: float) -> None:
        self.c = float(c)
        self.p = float(p)
        self.transition = transition_matrix(self.c, self.p)
        self._powers = {
            gap: np.linalg.matrix_power(self.transition, gap)
            for gap in (2, 4, 10)
        }
        self.survival8 = np.empty(N_STATES, dtype=np.float64)
        self.survival8[0] = self.p * (self.c - 1) / (self.c + 6)
        ages = np.arange(HORIZON + 1, dtype=np.float64)
        self.survival8[1:] = (ages + self.c - 1) / (ages + self.c + 7)

        shape_solo = (MAX_DECISION_TIME + 1, N_STATES)
        shape_joint = (MAX_DECISION_TIME + 1, N_STATES, N_STATES)
        self.solo = np.full(shape_solo, np.nan, dtype=np.float64)
        self.solo_submit = np.full(shape_solo, np.nan, dtype=np.float64)
        self.solo_wait = np.full(shape_solo, np.nan, dtype=np.float64)
        self.joint = np.full(shape_joint, np.nan, dtype=np.float64)
        self.joint_submit = np.full(shape_joint, np.nan, dtype=np.float64)
        self.joint_wait = np.full(shape_joint, np.nan, dtype=np.float64)
        self._solve()

    def _solve(self) -> None:
        submit_reward = -10 + 200 * self.survival8
        transition4 = self._powers[4]
        for t in range(MAX_DECISION_TIME, -1, -2):
            self.solo_submit[t] = submit_reward
            if t + 4 <= MAX_DECISION_TIME:
                self.solo_wait[t] = -4 + transition4 @ self.solo[t + 4]
            else:
                self.solo_wait[t] = -(HORIZON - t)
            self.solo[t] = np.maximum(self.solo_submit[t], self.solo_wait[t])

        transition2 = self._powers[2]
        transition10 = self._powers[10]
        for t in range(MAX_DECISION_TIME, -1, -2):
            if t + 10 <= MAX_DECISION_TIME:
                partner_after_block = -10 + transition10 @ self.solo[t + 10]
            else:
                partner_after_block = np.full(N_STATES, -(HORIZON - t), dtype=np.float64)
            self.joint_submit[t] = submit_reward[:, None] + partner_after_block[None, :]
            if t + 2 <= MAX_DECISION_TIME:
                # At the next clock the partner is the actor, hence transpose the
                # continuation axes after independently advancing both targets.
                next_value = self.joint[t + 2].T
                self.joint_wait[t] = -4 + transition2 @ next_value @ transition2.T
            else:
                self.joint_wait[t] = -2 * (HORIZON - t)
            self.joint[t] = np.maximum(self.joint_submit[t], self.joint_wait[t])

    @staticmethod
    def _decision_inputs(x: object) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        observations = np.asarray(x)
        if observations.ndim == 1:
            observations = observations[None, :]
        if observations.ndim != 2 or observations.shape[1] != 14:
            raise ValueError("x must have shape (rows, 14)")
        if not np.all(np.isfinite(observations)):
            raise ValueError("x must contain only finite values")
        own, partner, _ = _observation_states(observations)
        raw_time = observations[:, 0].astype(np.float64) * HORIZON
        times = np.rint(raw_time).astype(np.int64)
        if (not np.all(np.abs(raw_time - times) <= 1e-4) or
                np.any((times < 0) | (times > MAX_DECISION_TIME) | (times % 2 != 0))):
            raise ValueError("x time must encode an even decision clock in 0..32")
        partner_pending = _binary_feature(observations[:, 11], "partner pending").astype(bool)
        return times, own, partner, partner_pending

    def action_advantage(self, x: object, mode: str = "joint") -> np.ndarray:
        """Return SUBMIT minus WAIT value for each public observation row."""
        if mode not in {"joint", "self"}:
            raise ValueError("mode must be 'joint' or 'self'")
        times, own, partner, partner_pending = self._decision_inputs(x)
        margins = self.solo_submit[times, own] - self.solo_wait[times, own]
        if mode == "joint":
            selected = np.flatnonzero(partner_pending)
            margins[selected] = (
                self.joint_submit[times[selected], own[selected], partner[selected]]
                - self.joint_wait[times[selected], own[selected], partner[selected]]
            )
        return margins

    def actions(self, x: object, mode: str = "joint") -> np.ndarray:
        """Choose SUBMIT, with exact value ties resolved in favor of SUBMIT."""
        return self.action_advantage(x, mode=mode) >= 0
