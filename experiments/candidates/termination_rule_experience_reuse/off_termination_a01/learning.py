"""Tabular target-termination TD, direct Q(beta), and ordinary Retrace.

All forward targets use a common frozen table inside the current chunk. The
only arm difference is the coefficient multiplying *subsequent TD errors*.
"""

from __future__ import annotations

import numpy as np

from .host import Episode, OPTION_COUNT, STATE_COUNT


ARMS = ("one_step", "qbeta", "retrace")


def greedy_probabilities(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values)
    best = values == np.max(values, axis=-1, keepdims=True)
    return best / best.sum(axis=-1, keepdims=True)


def option_kernel(values: np.ndarray, previous: np.ndarray, beta: float) -> np.ndarray:
    """Marginalize actual continuation and termination with same-label redraw."""
    result = beta * greedy_probabilities(values)
    result[np.arange(len(previous)), previous] += 1 - beta
    return result


def forward_targets(q: np.ndarray, episode: Episode, start: int, stop: int,
                    arm: str, gamma: float, beta: float):
    if arm not in ARMS or not 0 <= start < stop <= len(episode.rewards):
        raise ValueError("invalid arm or chunk bounds")
    if q.shape != (STATE_COUNT, OPTION_COUNT) or not np.isfinite(q).all():
        raise ValueError("invalid Q table")
    if not 0 <= gamma < 1 or not 0 <= beta <= 1:
        raise ValueError("invalid discount or target hazard")
    states = episode.states[start:stop]
    options = episode.options[start:stop]
    next_values = q[episode.states[start + 1:stop + 1]]
    bootstrap = (1 - beta) * next_values[np.arange(stop - start), options]
    bootstrap += beta * next_values.max(axis=1)
    # Episodes are fixed-length collection truncations, not absorbing terminals.
    delta = episode.rewards[start:stop] + gamma * bootstrap - q[states, options]
    coefficients = np.zeros(stop - start, dtype=np.float64)
    ratios = np.empty(max(0, stop - start - 1), dtype=np.float64)
    if stop - start > 1:
        previous, current = options[:-1], options[1:]
        target = option_kernel(q[states[1:]], previous, beta)
        numerators = target[np.arange(len(previous)), current]
        denominators = episode.next_option_probability[start:stop - 1]
        if np.any(denominators <= 0):
            raise ValueError("unsupported observed option transition")
        ratios[:] = numerators / denominators
        if arm == "retrace":
            coefficients[1:] = np.minimum(1., ratios)
        elif arm == "qbeta":
            same_option_probability = target[np.arange(len(previous)), previous]
            coefficients[1:] = np.where(
                episode.renewed[start:stop - 1], 0., same_option_probability
            )

    # coefficients[0] is unused: the starting row is not importance-weighted.
    advantage = delta.copy()
    trace_mass = np.ones(len(delta), dtype=np.float64)
    residual_terms = np.ones(len(delta), dtype=np.int64)
    for t in range(len(delta) - 2, -1, -1):
        weight = gamma * coefficients[t + 1]
        advantage[t] += weight * advantage[t + 1]
        trace_mass[t] += weight * trace_mass[t + 1]
        if weight > 0:
            residual_terms[t] += residual_terms[t + 1]
    return {
        "states": states, "options": options, "delta": delta,
        "advantage": advantage, "target": q[states, options] + advantage,
        "coefficients": coefficients, "raw_ratios": ratios,
        "trace_mass": trace_mass, "residual_terms": residual_terms,
    }


def update_chunk(q: np.ndarray, visits: np.ndarray, episode: Episode, start: int,
                 stop: int, arm: str, gamma: float, beta: float, alpha: float):
    if not 0 < alpha <= 1 or visits.shape != q.shape:
        raise ValueError("invalid step size or visit table")
    values = forward_targets(q, episode, start, stop, arm, gamma, beta)
    flat = values["states"].astype(np.int64) * OPTION_COUNT + values["options"]
    indices, inverse, counts = np.unique(flat, return_inverse=True, return_counts=True)
    chunk_increment = np.bincount(inverse, weights=values["advantage"]) / (stop - start)
    # The denominator is fixed, not a future-dependent realized visit count.
    # This is a batch mean over all start rows, including zeros for other entries.
    q.reshape(-1)[indices] += alpha * chunk_increment
    visits.reshape(-1)[indices] += counts
    ratios = values["raw_ratios"]
    return {
        "target_rows": int(stop - start),
        "table_entries_written": int(len(indices)),
        "discounted_trace_mass_sum": float(values["trace_mass"].sum()),
        "positive_residual_terms": int(values["residual_terms"].sum()),
        "td_square_sum": float(np.square(values["delta"]).sum()),
        "return_increment_square_sum": float(np.square(values["advantage"]).sum()),
        "ratio_count": int(len(ratios)),
        "raw_ratio_sum": float(ratios.sum()),
        "raw_ratio_square_sum": float(np.square(ratios).sum()),
        "raw_ratio_max": float(ratios.max()) if len(ratios) else 0.,
        "ratio_above_one_count": int(np.count_nonzero(ratios > 1.)),
        "coefficient_zero_count": int(np.count_nonzero(values["coefficients"][1:] == 0)),
        "coefficient_sum": float(values["coefficients"][1:].sum()),
        "renewal_edges": int(episode.renewed[start:stop - 1].sum()),
        "renewal_edges_retained": int(np.count_nonzero(
            episode.renewed[start:stop - 1] & (values["coefficients"][1:] > 0)
        )),
    }
