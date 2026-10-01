"""Complete native metrics and descriptive paired-world comparisons."""
import itertools

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b06_count_development.audit import _metrics
from experiments.candidates.uav_fleet_adaptation.b06_count_development.controllers import COMMANDS
from experiments.candidates.uav_fleet_transmission.b05_score_sampling.reading import grid_probabilities, sample_summary
from .contract import ARMS


METRICS = ("J", "mean_served", "mean_sinr_quality", "coverage_reward", "quality_reward",
           "service_p10", "min_served", "zero_service_steps", "longest_zero_service_streak",
           "mean_path_length_m", "xy_boundary_uav_steps", "lower_altitude_uav_steps",
           "zero_displacement_uav_ticks", "fallback_decisions", "mean_entropy", "policy_cache_hits",
           "categorical_departures", "first_tick_physical_departures", "end_hold_physical_departures",
           "nominal_departure_probability", "effective_departure_probability",
           "decision_query_cpu_seconds", "decision_query_wall_seconds", "cpu_seconds", "wall_seconds")


def episode_metrics(raw):
    result = _metrics(raw)
    p, choices = raw["probabilities"], raw["action_index"]
    modal = np.argmax(p, axis=-1)
    effective = grid_probabilities(p)
    pmodal = np.take_along_axis(p, modal[..., None], axis=-1)[..., 0]
    emodal = np.take_along_axis(effective, modal[..., None], axis=-1)[..., 0]
    starts = raw["positions"][raw["decision_ticks"]]
    chosen, mode = COMMANDS[choices].astype(np.float64), COMMANDS[modal].astype(np.float64)
    low, high = [0., 0., 50.], [1000., 1000., 150.]
    first = np.any(np.clip(starts + 30 * chosen, low, high) != np.clip(starts + 30 * mode, low, high), axis=-1)
    final = np.any(np.clip(starts + 120 * chosen, low, high) != np.clip(starts + 120 * mode, low, high), axis=-1)
    result.update(categorical_departures=int(np.count_nonzero(choices != modal)),
                  first_tick_physical_departures=int(first.sum()), end_hold_physical_departures=int(final.sum()),
                  nominal_departure_probability=float((1 - pmodal).mean()),
                  effective_departure_probability=float((1 - emodal).mean()),
                  zero_grid_categories=int(np.count_nonzero(effective == 0)),
                  zero_float_categories=int(np.count_nonzero(p == 0)),
                  positive_float_zero_grid_categories=int(np.count_nonzero((p > 0) & (effective == 0))),
                  departure_reference="argmax of the deployed distribution on its own actual history")
    return result


def comparisons(rows, protocol):
    expected = [(arm, world, tape) for wi, world in enumerate(protocol.worlds)
                for arm, tape in protocol.episode_order(wi)]
    if [(r["arm"], r["world"], r["tape"]) for r in rows] != expected:
        raise ValueError("final execution order/coverage changed")
    by_key = {(r["arm"], r["world"], r["tape"]): r for r in rows}
    indices = np.random.default_rng(protocol.bootstrap_seed).integers(
        0, len(protocol.worlds), (protocol.bootstrap_resamples, len(protocol.worlds)))
    values = {arm: {metric: np.asarray([
        np.mean([by_key[arm, world, tape][metric] for tape in ((None,) if arm == "C" else (0, 1))])
        for world in protocol.worlds], dtype=np.float64) for metric in METRICS} for arm in ARMS}
    pairs = {}
    for earlier, later in itertools.combinations(ARMS, 2):
        left, right = ("T", "H") if (earlier, later) == ("T", "H") else (later, earlier)
        pairs[left + "-" + right] = {m: sample_summary(values[left][m] - values[right][m], indices) for m in METRICS}
    return dict(primary="T-H", worlds=list(protocol.worlds),
                levels={a: {m: sample_summary(v, indices) for m, v in table.items()} for a, table in values.items()},
                comparisons=pairs,
                zero_service_episodes=[{k: r[k] for k in ("id", "arm", "world", "tape", "zero_service_steps",
                                                         "zero_service_ticks", "longest_zero_service_streak")}
                                       for r in rows if r["zero_service_steps"]],
                scope="One parent/data instance. Two stochastic tapes averaged within each of 32 worlds; C once. "
                      "Same fixed bootstrap indices for all 55 contrasts/metrics. Exploratory descriptive intervals, "
                      "no training-population, equivalence or isolated full-score/entropy attribution.")
