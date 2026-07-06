
"""Round-12 situation substrate utilities.

This module is pure Python/NumPy. It converts validated OPT substrate outputs
into slow situation labels and diagnostics. It must not depend on environment-
specific communication metrics.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SituationDebounceConfig:
    min_stable_count: int = 2
    missing_kappa: int = -1


@dataclass(frozen=True)
class SituationState:
    env_id: int
    raw_kappa: int
    kappa: int
    previous_kappa: int
    stable_count: int
    changed: bool


def assign_kappa_from_omega(omega: np.ndarray, *, missing_kappa: int = -1) -> int:
    values = np.asarray(omega, dtype=np.float64).reshape(-1)
    if values.size == 0 or not np.all(np.isfinite(values)):
        return int(missing_kappa)
    return int(np.argmax(values))


def compact_cluster_predict(
    compact: np.ndarray,
    centroids: np.ndarray,
    *,
    missing_kappa: int = -1,
) -> int:
    vector = np.asarray(compact, dtype=np.float64).reshape(-1)
    centers = np.asarray(centroids, dtype=np.float64)
    if vector.size == 0 or centers.ndim != 2 or centers.shape[0] == 0:
        return int(missing_kappa)
    if centers.shape[1] != vector.size:
        return int(missing_kappa)
    if not np.all(np.isfinite(vector)) or not np.all(np.isfinite(centers)):
        return int(missing_kappa)
    distances = np.sum((centers - vector[None, :]) ** 2, axis=1)
    return int(np.argmin(distances))


class SituationDebouncer:
    def __init__(self, config: SituationDebounceConfig | None = None):
        self.config = config or SituationDebounceConfig()
        self._current: dict[int, int] = {}
        self._candidate: dict[int, int] = {}
        self._count: dict[int, int] = {}

    def reset_env(self, env_id: int) -> None:
        env = int(env_id)
        self._current.pop(env, None)
        self._candidate.pop(env, None)
        self._count.pop(env, None)

    def update(self, *, env_id: int, raw_kappa: int) -> SituationState:
        env = int(env_id)
        raw = int(raw_kappa)
        previous = int(self._current.get(env, raw))
        if env not in self._current:
            self._current[env] = raw
            self._candidate[env] = raw
            self._count[env] = 1
            return SituationState(env, raw, raw, raw, 1, False)

        if raw == self._candidate.get(env):
            self._count[env] = int(self._count.get(env, 0)) + 1
        else:
            self._candidate[env] = raw
            self._count[env] = 1

        changed = False
        if (
            raw != self._current[env]
            and self._count[env] >= max(int(self.config.min_stable_count), 1)
        ):
            self._current[env] = raw
            changed = True

        return SituationState(
            env_id=env,
            raw_kappa=raw,
            kappa=int(self._current[env]),
            previous_kappa=previous,
            stable_count=int(self._count[env]),
            changed=bool(changed),
        )


@dataclass(frozen=True)
class AgentSituationState(SituationState):
    agent_id: int = 0


class PerAgentSituationDebouncer:
    """Debounce situation labels independently for each (env, agent) pair."""

    def __init__(self, config: SituationDebounceConfig | None = None):
        self.config = config or SituationDebounceConfig()
        self._current: dict[tuple[int, int], int] = {}
        self._candidate: dict[tuple[int, int], int] = {}
        self._count: dict[tuple[int, int], int] = {}

    def reset_env(self, env_id: int) -> None:
        env = int(env_id)
        for store in (self._current, self._candidate, self._count):
            for key in list(store.keys()):
                if int(key[0]) == env:
                    store.pop(key, None)

    def reset_all(self) -> None:
        self._current.clear()
        self._candidate.clear()
        self._count.clear()

    def update(self, *, env_id: int, agent_id: int, raw_kappa: int) -> AgentSituationState:
        env = int(env_id)
        agent = int(agent_id)
        key = (env, agent)
        raw = int(raw_kappa)
        previous = int(self._current.get(key, raw))
        if key not in self._current:
            self._current[key] = raw
            self._candidate[key] = raw
            self._count[key] = 1
            return AgentSituationState(env, raw, raw, raw, 1, False, agent)

        if raw == self._candidate.get(key):
            self._count[key] = int(self._count.get(key, 0)) + 1
        else:
            self._candidate[key] = raw
            self._count[key] = 1

        changed = False
        if (
            raw != self._current[key]
            and self._count[key] >= max(int(self.config.min_stable_count), 1)
        ):
            self._current[key] = raw
            changed = True

        return AgentSituationState(
            env_id=env,
            raw_kappa=raw,
            kappa=int(self._current[key]),
            previous_kappa=previous,
            stable_count=int(self._count[key]),
            changed=bool(changed),
            agent_id=agent,
        )


def kappa_transition_metrics(kappas: np.ndarray) -> dict[str, float]:
    raw_values = np.asarray(kappas, dtype=np.float64).reshape(-1)
    if raw_values.size == 0 or not np.all(np.isfinite(raw_values)):
        return {
            "situation_change_rate": 0.0,
            "situation_median_dwell": 0.0,
            "situation_unique_kappa": 0.0,
        }
    values = raw_values.astype(np.int64)
    if values.size == 1:
        return {
            "situation_change_rate": 0.0,
            "situation_median_dwell": 1.0,
            "situation_unique_kappa": 1.0,
        }
    changes = values[1:] != values[:-1]
    boundaries = np.concatenate(([0], np.nonzero(changes)[0] + 1, [values.size]))
    dwell = np.diff(boundaries).astype(np.float64)
    return {
        "situation_change_rate": float(np.mean(changes)),
        "situation_median_dwell": float(np.median(dwell)) if dwell.size else 0.0,
        "situation_unique_kappa": float(np.unique(values).size),
    }
