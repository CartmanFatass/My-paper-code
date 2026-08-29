"""Scalar TEST-only oracle for native UCOPE r03 S0/S1 fixture conformance.

This module is forbidden as an environment or rollout backend.  It exists only
to compare nonregistered fixture bytes against the retained C++ lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .contract import (
    K_TRAIN,
    TEST_NAMESPACE,
    require_s1_test_request,
    require_test_namespace,
)


_MASK = (1 << 32) - 1
S1_SCALAR_ORACLE_BRIDGE_ID = (
    "UCOPE_R01_R03_S1_TEST_TO_RETAINED_S0_SCALAR_MECHANISM_V1"
)


def _philox_words(
    seed: int, tag: int, panel: int, arm: int, network: int, a: int, b: int
) -> tuple[int, int, int, int]:
    key0 = (seed & _MASK) ^ 0x55434F50
    key1 = ((seed >> 32) & _MASK) ^ 0x52303133
    counter = [a & _MASK, b & _MASK, tag | (panel << 8) | (arm << 16) | (network << 24), 0x20260823]
    for _ in range(10):
        product0 = 0xD2511F53 * counter[0]
        product1 = 0xCD9E8D57 * counter[2]
        counter = [
            ((product1 >> 32) ^ counter[1] ^ key0) & _MASK,
            product1 & _MASK,
            ((product0 >> 32) ^ counter[3] ^ key1) & _MASK,
            product0 & _MASK,
        ]
        key0 = (key0 + 0x9E3779B9) & _MASK
        key1 = (key1 + 0xBB67AE85) & _MASK
    return tuple(counter)  # type: ignore[return-value]


def philox_word0(seed: int, tag: int, panel: int, arm: int, network: int, a: int, b: int) -> int:
    return _philox_words(seed, tag, panel, arm, network, a, b)[0]


def uniform01(seed: int, tag: int, panel: int, arm: int, network: int, a: int, b: int) -> np.float32:
    return np.float32(philox_word0(seed, tag, panel, arm, network, a, b) >> 8) * np.float32(2.0**-24)


def regime_roster(seed: int, panel: int, batch_index: int) -> tuple[tuple[int, int, int], ...]:
    entries: list[tuple[int, int, tuple[int, int, int]]] = []
    for slot in range(256):
        if panel == 0:
            probe = 0 if slot < 128 else 1
            value = (probe, probe, probe)
        else:
            pair = slot // 64
            first, second = pair // 2, pair % 2
            value = (first, second, first) if panel == 1 else (first, first, second)
        entries.append((philox_word0(seed, 1, panel, 255, 0, batch_index, slot), slot, value))
    entries.sort(key=lambda item: (item[0], item[1]))
    return tuple(item[2] for item in entries)


def _candidate(channel: np.ndarray, *, root: bool, probe: bool, k: int) -> np.ndarray:
    result = np.zeros(13, dtype=np.float32)
    result[:6] = channel
    result[6:8] = (np.float32(1.0), np.float32(0.0)) if root else (np.float32(0.0), np.float32(1.0))
    result[8:10] = (np.float32(1.0), np.float32(0.0)) if probe else (np.float32(0.0), np.float32(1.0))
    if not probe:
        scaled = np.float32(k) / np.float32(9.0)
        result[10:12] = (scaled, np.float32(scaled * scaled))
    result[12] = np.float32(1.0) if root else np.float32(10.0) / np.float32(12.0)
    return result


def _baseline(channel: np.ndarray, *, root: bool) -> np.ndarray:
    result = np.zeros(9, dtype=np.float32)
    result[:6] = channel
    result[6:8] = (np.float32(1.0), np.float32(0.0)) if root else (np.float32(0.0), np.float32(1.0))
    result[8] = np.float32(1.0) if root else np.float32(10.0) / np.float32(12.0)
    return result


def root_features() -> tuple[np.ndarray, np.ndarray]:
    channel = np.zeros(6, dtype=np.float32)
    candidates = [_candidate(channel, root=True, probe=True, k=0)]
    candidates.extend(_candidate(channel, root=True, probe=False, k=k) for k in K_TRAIN)
    return np.stack(candidates), _baseline(channel, root=True)


def _marks(seed: int, tag: int, panel: int, episode: int, regime: int) -> np.ndarray:
    probability = np.float32(0.85) if regime == 0 else np.float32(0.15)
    return np.asarray(
        [uniform01(seed, tag, panel, 255, 0, episode, micro) < probability for micro in range(6)],
        dtype=np.int32,
    )


def _tail_channel(panel: int, arm: int, displayed: np.ndarray) -> np.ndarray:
    count = int(displayed.sum())
    channel = np.zeros(6, dtype=np.float32)
    if arm == 0:
        channel[:4] = (
            np.float32(count) / np.float32(6.0),
            np.float32(1.0),
            (np.float32(count) - np.float32(3.0)) / np.float32(6.0),
            np.float32(1.0),
        )
    elif arm == 1:
        channel[:] = displayed.astype(np.float32)
    else:
        rho = np.float32(0.5)
        if panel == 0:
            short_weight = np.float32(1.0)
            long_weight = np.float32(1.0)
            for _ in range(count):
                short_weight = np.float32(short_weight * np.float32(0.85))
                long_weight = np.float32(long_weight * np.float32(0.15))
            for _ in range(count, 6):
                short_weight = np.float32(short_weight * np.float32(0.15))
                long_weight = np.float32(long_weight * np.float32(0.85))
            rho = np.float32(short_weight / np.float32(short_weight + long_weight))
        channel[:3] = (rho, np.float32(1.0) - rho, np.float32(1.0))
    return channel


def _tail_components(seed: int, panel: int, episode: int, regime: int, k: int) -> np.ndarray:
    anchor = 2 if regime == 0 else 8
    probability = np.float32(0.95) - np.float32((k - anchor) ** 2) / np.float32(100.0)
    service = np.float32(uniform01(seed, 4, panel, 255, 0, episode, k) < probability)
    return np.asarray(
        [service, np.float32(-0.01) * np.float32(k), np.float32(-0.001) * np.float32(k * k)],
        dtype=np.float32,
    )


@dataclass(frozen=True)
class OracleEpisode:
    regimes: np.ndarray
    root_features: np.ndarray
    root_baseline: np.ndarray
    actual_marks: np.ndarray
    displayed_marks: np.ndarray
    probe_components: np.ndarray
    tail_features: np.ndarray
    tail_baseline: np.ndarray
    components: np.ndarray
    total: np.float32


def _run_episode(
    *, seed: int, panel: int, batch_index: int, slot: int, arm: int,
    root_action: int, tail_action: int,
) -> OracleEpisode:
    if panel not in (0, 1, 2) or arm not in (0, 1, 2) or not 0 <= slot < 256:
        raise ValueError("invalid TEST oracle coordinate")
    if not 0 <= root_action <= 5 or not 0 <= tail_action < 5:
        raise ValueError("invalid TEST oracle action")
    regimes = np.asarray(regime_roster(seed, panel, batch_index)[slot], dtype=np.int32)
    root, root_baseline = root_features()
    episode = batch_index * 256 + slot
    actual = np.zeros(6, dtype=np.int32)
    displayed = np.zeros(6, dtype=np.int32)
    probe = np.zeros(3, dtype=np.float32)
    tail_candidates = np.zeros((5, 13), dtype=np.float32)
    tail_baseline = np.zeros(9, dtype=np.float32)
    components = np.zeros(6, dtype=np.float32)
    if root_action == 0:
        actual = _marks(seed, 2, panel, episode, int(regimes[0]))
        displayed = (
            _marks(seed, 3, panel, episode, int(regimes[2]))
            if panel == 2
            else actual.copy()
        )
        count = int(actual.sum())
        probe = np.asarray(
            [
                np.float32(0.08) * (np.float32(count) / np.float32(6.0)),
                np.float32(-0.03),
                np.float32(-0.03),
            ],
            dtype=np.float32,
        )
        channel = _tail_channel(panel, arm, displayed)
        tail_candidates = np.stack(
            [_candidate(channel, root=False, probe=False, k=k) for k in K_TRAIN]
        )
        tail_baseline = _baseline(channel, root=False)
        components[:3] = _tail_components(
            seed, panel, episode, int(regimes[1]), K_TRAIN[tail_action],
        )
        components[3:] = probe
    else:
        components[:3] = _tail_components(
            seed, panel, episode, int(regimes[1]), K_TRAIN[root_action - 1],
        )
    total = np.float32(0.0)
    for value in components:
        total = np.float32(total + value)
    return OracleEpisode(
        regimes, root, root_baseline, actual, displayed, probe,
        tail_candidates, tail_baseline, components, total,
    )


def run_episode(
    *, namespace: str = TEST_NAMESPACE, seed: int, panel: int, batch_index: int,
    slot: int, arm: int, root_action: int, tail_action: int = 0,
) -> OracleEpisode:
    """Run the preserved S0 TEST entrypoint."""

    require_test_namespace(namespace, seed)
    return _run_episode(
        seed=seed,
        panel=panel,
        batch_index=batch_index,
        slot=slot,
        arm=arm,
        root_action=root_action,
        tail_action=tail_action,
    )


def run_s1_test_episode(
    *, namespace: str, request: str, seed: int, panel: int, batch_index: int,
    slot: int, arm: int, root_action: int, tail_action: int = 0,
) -> OracleEpisode:
    """Bridge an admitted S1 TEST fixture to the retained scalar mechanism."""

    require_s1_test_request(namespace, seed, request)
    return _run_episode(
        seed=seed,
        panel=panel,
        batch_index=batch_index,
        slot=slot,
        arm=arm,
        root_action=root_action,
        tail_action=tail_action,
    )

def sample_action(
    probabilities: np.ndarray, *, seed: int, panel: int, batch_index: int,
    slot: int, arm: int, decision_code: int,
) -> int:
    if probabilities.dtype != np.float32 or probabilities.ndim != 1:
        raise TypeError("oracle probabilities must be an FP32 vector")
    draw = uniform01(seed, 5, panel, arm, 0, batch_index * 256 + slot, decision_code)
    cumulative = np.float32(0.0)
    for index, probability in enumerate(probabilities):
        cumulative = np.float32(cumulative + probability)
        if draw < cumulative:
            return index
    return probabilities.size - 1


def potential_tail_marks(
    *, seed: int, panel: int, batch_index: int, slot: int,
) -> np.ndarray:
    regimes = regime_roster(seed, panel, batch_index)[slot]
    episode = batch_index * 256 + slot
    return np.asarray(
        [
            _tail_components(seed, panel, episode, int(regimes[1]), k)[0]
            for k in K_TRAIN
        ],
        dtype=np.int32,
    )


def _expected_tail(rho: np.float32, k: int) -> np.float32:
    short = np.float32(0.95) - np.float32((k - 2) ** 2) / np.float32(100.0)
    long = np.float32(0.95) - np.float32((k - 8) ** 2) / np.float32(100.0)
    value = np.float32(rho * short)
    value = np.float32(value + np.float32((np.float32(1.0) - rho) * long))
    value = np.float32(value - np.float32(0.01) * np.float32(k))
    return np.float32(value - np.float32(0.001) * np.float32(k * k))


def _first_best(rho: np.float32, periods: tuple[int, ...]) -> tuple[int, np.float32]:
    selected = 0
    best = _expected_tail(rho, periods[0])
    for index, k in enumerate(periods[1:], start=1):
        value = _expected_tail(rho, k)
        if value > np.float32(best + np.float32(1.0e-6)):
            selected, best = index, value
    return selected, best


def _history_probability(theta: int, history: int) -> np.float32:
    hit = np.float32(0.85) if theta == 0 else np.float32(0.15)
    miss = np.float32(0.15) if theta == 0 else np.float32(0.85)
    probability = np.float32(1.0)
    for micro in range(6):
        probability = np.float32(
            probability * (hit if (history >> (5 - micro)) & 1 else miss)
        )
    return probability


def _posterior(count: int) -> np.float32:
    short_weight = np.float32(1.0)
    long_weight = np.float32(1.0)
    for _ in range(count):
        short_weight = np.float32(short_weight * np.float32(0.85))
        long_weight = np.float32(long_weight * np.float32(0.15))
    for _ in range(count, 6):
        short_weight = np.float32(short_weight * np.float32(0.15))
        long_weight = np.float32(long_weight * np.float32(0.85))
    return np.float32(short_weight / np.float32(short_weight + long_weight))


def nonlearned_actions(
    *, panel: int, displayed_count: int, periods: tuple[int, ...] = K_TRAIN,
) -> dict[str, int]:
    """Independent TEST-only scalar action oracle for the three DP arms."""

    immediate_period, immediate_value = _first_best(np.float32(0.5), periods)
    rho = _posterior(displayed_count) if panel == 0 else np.float32(0.5)
    belief_tail, _ = _first_best(rho, periods)
    probe_value = np.float32(immediate_value - np.float32(0.02))
    if panel == 0:
        probe_value = np.float32(0.0)
        for theta in range(2):
            for history in range(64):
                count = sum((history >> micro) & 1 for micro in range(6))
                _, history_tail = _first_best(_posterior(count), periods)
                direct = np.float32(
                    np.float32(0.08) * (np.float32(count) / np.float32(6.0))
                    - np.float32(0.06)
                )
                term = np.float32(
                    np.float32(0.5) * _history_probability(theta, history)
                )
                probe_value = np.float32(
                    probe_value + np.float32(term * np.float32(history_tail + direct))
                )
    belief_root = 0 if np.float32(probe_value + np.float32(1.0e-6)) >= immediate_value else immediate_period + 1
    return {
        "belief_dp_root": belief_root,
        "belief_dp_tail": belief_tail,
        "immediate_dp_root": immediate_period + 1,
        "forced_probe_blind_dp_root": 0,
        "forced_probe_blind_dp_tail": immediate_period,
    }
