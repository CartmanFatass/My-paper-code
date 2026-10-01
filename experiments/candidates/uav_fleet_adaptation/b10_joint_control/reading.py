"""Native component readings; fixed paired descriptive world comparisons."""
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reading import (
    _summary, episode_metrics as original_episode_metrics,
)
from .contract import CONTRASTS, DETERMINISTIC, PROGRAMS


def episode_metrics(raw):
    result = original_episode_metrics(raw)
    eligible = np.asarray(raw["eligible"], dtype=bool)
    off = np.asarray(raw["requested_off"], dtype=bool)
    displacement = np.diff(raw["positions"], axis=0)
    silent = ~raw["transmitter_mask"]
    midpoint = len(raw["reward"]) // 2
    selected_fidelity = raw["initial_fidelity"]
    result.update(mean_motion_entropy=float(raw["motion_entropy"].mean()),
                  mean_category_entropy=float(raw["entropy"].mean()),
                  eligible_mean_gate_entropy=float(raw["gate_entropy"][eligible].mean()),
                  eligible_mean_off_probability=float(raw["off_probability"][eligible].mean()),
                  eligible_preferred_off=int(np.count_nonzero(raw["hidden_preferred_off"] & eligible)),
                  eligible_matches_hidden_preference=int(np.count_nonzero((off == raw["hidden_preferred_off"]) & eligible)),
                  noneligible_off_requests=int(np.count_nonzero(off & ~eligible)),
                  requested_zero_motion=int(np.count_nonzero(raw["motion_index"] == int(np.flatnonzero(np.all(COMMANDS == 0, axis=1))[0]))),
                  silent_moving_uav_ticks=int(np.count_nonzero(silent & np.any(displacement != 0., axis=-1))),
                  silent_travel_m=float(np.linalg.norm(displacement, axis=-1)[silent].sum()),
                  clipped_command_uav_ticks=int(np.count_nonzero(np.any(
                      displacement != raw["commands"].astype(np.float64) * 30., axis=-1))),
                  CJ_off_score_evaluations=int(np.count_nonzero(raw["off_evaluated"])),
                  initial_fidelity_rows=int(np.count_nonzero(selected_fidelity)),
                  init_logit_max_abs=float(raw["init_logit_max_abs"].max()),
                  init_probability_max_abs=float(raw["init_probability_max_abs"].max()),
                  init_tv_max=float(raw["init_tv"].max()),
                  init_tv_mean=float(raw["init_tv"][selected_fidelity].mean()) if selected_fidelity.any() else 0.)
    for name, part in (("first", slice(0, midpoint)), ("later", slice(midpoint, None))):
        result[name + "_J"] = float(raw["reward"][part].mean())
        result[name + "_mean_served"] = float(raw["served"][part].mean())
        result[name + "_zero_service_steps"] = int(np.count_nonzero(raw["served"][part] == 0))
    for agent in range(5):
        result[f"uav{agent}_eligible_decisions"] = int(np.count_nonzero(eligible[:, agent]))
        result[f"uav{agent}_off_decisions"] = int(np.count_nonzero(off[:, agent]))
    # These complete histograms describe requested categories; raw masks and
    # native positions retain their executed physical consequences separately.
    result["requested_category_counts"] = np.bincount(raw["action_index"].ravel(), minlength=54).tolist()
    result["requested_motion_counts"] = np.bincount(raw["motion_index"].ravel(), minlength=27).tolist()
    return result


def metric_values(row):
    exclude = {"world", "tape", "motion_root", "block", "group"}
    values = {key: float(value) for key, value in row.items() if key not in exclude and type(value) in (int, float)}
    values.update({"policy_" + key: float(value) for key, value in row["policy_counts"].items()})
    if not all(np.isfinite(value) for value in values.values()):
        raise ValueError("nonfinite episode measurement")
    return values


def comparisons(rows, protocol):
    final = [row for row in rows if row["kind"] == "evaluation"]
    by_key = {(row["program"], row["world"], row["tape"]): row for row in final}
    expected = {(program, world, tape) for world in protocol.worlds for program, tape in protocol.episode_order(0)}
    if len(by_key) != len(final) or set(by_key) != expected:
        raise ValueError("incomplete or duplicate final panel")
    all_values = {key: metric_values(row) for key, row in by_key.items()}
    metrics = tuple(sorted(next(iter(all_values.values()))))
    if any(tuple(sorted(value)) != metrics for value in all_values.values()):
        raise ValueError("inconsistent program measurement roster")
    world_values = {program: {} for program in PROGRAMS}
    for program in PROGRAMS:
        tapes = (None,) if program in DETERMINISTIC else (0, 1)
        for metric in metrics:
            world_values[program][metric] = np.array([
                np.mean([all_values[program, world, tape][metric] for tape in tapes]) for world in protocol.worlds])
    indices = np.random.default_rng(protocol.bootstrap_seed).integers(
        0, len(protocol.worlds), size=(protocol.bootstrap_resamples, len(protocol.worlds)))
    levels = {program: {metric: _summary(values, indices) for metric, values in measurements.items()}
              for program, measurements in world_values.items()}
    contrasts = {f"{left}-{right}": {metric: _summary(world_values[left][metric] - world_values[right][metric], indices)
                                    for metric in metrics} for left, right in CONTRASTS}
    adverse_metrics = dict(lower_J=("J", -1), lower_mean_service=("mean_served", -1),
                           lower_quality=("mean_sinr_quality", -1), lower_service_p10=("service_p10", -1),
                           lower_min_service=("min_served", -1), more_zero_service_steps=("zero_service_steps", 1),
                           longer_zero_service_streak=("longest_zero_service_streak", 1))
    adverses = {key: {name: [world for world, value in zip(protocol.worlds, measures[metric]["world_values"])
                           if value * sign > 0] for name, (metric, sign) in adverse_metrics.items()}
                for key, measures in contrasts.items()}
    return dict(worlds=list(protocol.worlds), levels=levels, contrasts=contrasts, adverses=adverses,
                uncertainty="Pointwise percentile world bootstrap, two stochastic tapes averaged within world, deterministic controls once. "
                            "Conditional on the retained original P0/HIDDEN assets and two separately reported training blocks; "
                            "no independent-parent, training-population, simultaneous-comparison or equivalence coverage.",
                bootstrap=dict(seed=protocol.bootstrap_seed, resamples=protocol.bootstrap_resamples, quantile="linear"))
