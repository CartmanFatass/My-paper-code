"""Saved-array exposure metrics and the fixed paired-world descriptive reading."""
import itertools
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_fleet_adaptation.b02.reading import episode_metrics as inherited_metrics
from .contract import ARMS, LOW, HIGH

METRICS = (
    "J", "return_sum", "mean_served", "service_p10", "min_served", "zero_service_steps",
    "mean_sinr_quality", "coverage_reward", "quality_reward", "mean_path_length_m",
    "xy_boundary_uav_steps", "lower_altitude_uav_steps", "zero_displacement_uav_ticks",
    "fallback_decisions", "policy_cache_hits", "categorical_departures", "first_tick_physical_departures",
    "end_hold_physical_departures", "nominal_departure_probability", "effective_departure_probability",
    "mean_entropy", "decision_query_cpu_seconds", "decision_query_wall_seconds", "cpu_seconds", "wall_seconds",
)


def grid_probabilities(probabilities):
    """Exact mass of NumPy's k/2**53 innovation grid in each stored CDF bin."""
    edges = np.cumsum(probabilities, axis=-1, dtype=np.float64)
    edges[..., -1] = 1.
    edges = np.clip(edges, 0., 1.)
    # Categorical decoding uses [previous, current), including a boundary in the next bin.
    high = np.ceil(edges * (1 << 53)).astype(np.int64)
    low = np.concatenate((np.zeros_like(high[..., :1]), high[..., :-1]), axis=-1)
    return (high - low).astype(np.float64) / (1 << 53)


def episode_metrics(raw):
    base = inherited_metrics(raw)
    modal = raw["c_index"] if "c_index" in raw else np.argmax(raw["logits"], axis=-1)
    choices = raw["action_index"]
    pmodal = np.take_along_axis(raw["probabilities"], modal[..., None], axis=-1)[..., 0]
    effective = grid_probabilities(raw["probabilities"])
    emodal = np.take_along_axis(effective, modal[..., None], axis=-1)[..., 0]
    starts = raw["positions"][raw["decision_ticks"]]
    commands, ordinary = COMMANDS[choices].astype(np.float64), COMMANDS[modal].astype(np.float64)
    first = np.any(np.clip(starts + 30 * commands, LOW, HIGH) != np.clip(starts + 30 * ordinary, LOW, HIGH), axis=-1)
    final = np.any(np.clip(starts + 120 * commands, LOW, HIGH) != np.clip(starts + 120 * ordinary, LOW, HIGH), axis=-1)
    return dict(base, categorical_departures=int(np.count_nonzero(choices != modal)),
                first_tick_physical_departures=int(first.sum()), end_hold_physical_departures=int(final.sum()),
                nominal_departure_probability=float((1 - pmodal).mean()),
                effective_departure_probability=float((1 - emodal).mean()),
                mean_entropy=float(raw["entropy"].mean()), zero_grid_categories=int(np.count_nonzero(effective == 0)),
                zero_float_categories=int(np.count_nonzero(raw["probabilities"] == 0)))


def sample_summary(values, indices):
    values = np.asarray(values, dtype=np.float64)
    if values.shape != (indices.shape[1],) or not np.isfinite(values).all():
        raise ValueError("invalid complete paired-world values")
    bounds = np.quantile(values[indices].mean(axis=1), [.025, .975])
    return dict(n=len(values), mean=float(values.mean()), min=float(values.min()), max=float(values.max()),
                sd=float(values.std(ddof=1)) if len(values) > 1 else None,
                descriptive_paired_bootstrap95=bounds.tolist(), values=values.tolist(),
                positive=int((values > 0).sum()), negative=int((values < 0).sum()), zero=int((values == 0).sum()))


def comparisons(rows, protocol):
    expected = {(arm, world, tape) for world in protocol.worlds
                for arm, tape in protocol.episode_order(0)}
    by_key = {(r["arm"], r["world"], r["tape"]): r for r in rows}
    if set(by_key) != expected or len(rows) != len(expected):
        raise ValueError("missing, duplicated or undeclared evaluation cells")
    indices = np.random.default_rng(protocol.bootstrap_seed).integers(
        0, len(protocol.worlds), (protocol.bootstrap_resamples, len(protocol.worlds)))
    by_world = {arm: {metric: np.array([
        np.mean([by_key[arm, world, tape][metric] for tape in ((-1,) if arm == "C" else (0, 1))])
        for world in protocol.worlds]) for metric in METRICS} for arm in ARMS}
    levels = {arm: {m: sample_summary(values, indices) for m, values in table.items()}
              for arm, table in by_world.items()}
    pairs = {f"{later}-{earlier}": {m: sample_summary(by_world[later][m] - by_world[earlier][m], indices)
                                   for m in METRICS}
             for earlier, later in itertools.combinations(ARMS, 2)}
    return dict(levels=levels, comparisons=pairs, aliases={"Bstar_L1": "S_L1"},
                primary=["S_L0-G", "S_L1-G"], ordinary_law="G-Q10", worlds=list(protocol.worlds),
                scope="Two stochastic tapes averaged within each world; C once. Fixed assets, exploratory "
                      "descriptive paired-world percentile intervals; no learned-population or equivalence claim.")
