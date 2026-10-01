"""Complete episode readings; compulsory q/tape means precede world inference."""
import numpy as np

from experiments.candidates.uav_fleet_transmission.b05_score_sampling.reading import sample_summary
from .contract import CELLS, cell_name

TIMED_PARTS = ("reset", "schedule", "decision_query", "native_step", "raw_write")
METRICS = (
    "J", "return_sum", "mean_served", "service_p10", "min_served", "zero_service_steps",
    "longest_zero_run", "mean_sinr_quality", "coverage_reward", "quality_reward",
    "mean_path_length_m", "xy_boundary_uav_steps", "lower_altitude_uav_steps",
    "zero_displacement_uav_ticks", "queries", "fallback_decisions", "policy_cache_hits",
    "mean_entropy", "renewals_after_initial", "category_changes", "physical_hold_changes",
    "multiagent_query_ticks", "multiagent_category_change_ticks", "multiagent_physical_change_ticks",
    *(f"{part}_{clock}_seconds" for part in TIMED_PARTS for clock in ("cpu", "wall")),
    "cpu_seconds", "wall_seconds",
)


def episode_metrics(raw):
    served = raw["served"]
    longest, current = 0, 0
    for value in served:
        current = current + 1 if value == 0 else 0
        longest = max(longest, current)
    positions = raw["positions"][1:]
    displacements = positions - raw["positions"][:-1]
    category_changes = np.bincount(raw["decision_ticks"], weights=raw["category_changed"], minlength=len(served))
    physical_changes = np.bincount(raw["decision_ticks"], weights=raw["physical_hold_changed"], minlength=len(served))
    return dict(J=float(raw["reward"].mean()), return_sum=float(raw["reward"].sum()),
                mean_served=float(served.mean()), service_p10=float(np.quantile(served, .1)),
                min_served=int(served.min()), zero_service_steps=int(np.count_nonzero(served == 0)),
                longest_zero_run=longest, mean_sinr_quality=float(raw["sinr_quality"].mean()),
                coverage_reward=float((.7 * served / 50.).mean()),
                quality_reward=float((.3 * raw["sinr_quality"]).mean()),
                mean_path_length_m=float(np.linalg.norm(displacements, axis=-1).sum(axis=0).mean()),
                xy_boundary_uav_steps=int(np.any((positions[..., :2] == 0.) | (positions[..., :2] == 1000.), axis=-1).sum()),
                lower_altitude_uav_steps=int((positions[..., 2] == 50.).sum()),
                zero_displacement_uav_ticks=int(np.all(displacements == 0., axis=-1).sum()),
                queries=int(len(raw["decision_ticks"])), fallback_decisions=int(raw["fallback"].sum()),
                policy_cache_hits=int(raw["memo_hit"].sum()), mean_entropy=float(raw["entropy"].mean()),
                renewals_after_initial=int(np.count_nonzero(raw["held_before"] >= 0)),
                category_changes=int(raw["category_changed"].sum()),
                physical_hold_changes=int(raw["physical_hold_changed"].sum()),
                multiagent_query_ticks=int(np.count_nonzero(raw["query_mask"].sum(axis=1) > 1)),
                multiagent_category_change_ticks=int(np.count_nonzero(category_changes > 1)),
                multiagent_physical_change_ticks=int(np.count_nonzero(physical_changes > 1)))


def comparisons(rows, protocol):
    expected = {(arm, schedule, world, q, tape) for world in protocol.worlds
                for arm, schedule, q, tape in protocol.episode_order(0)}
    by_key = {(r["arm"], r["schedule"], r["world"], r["q"], r["tape"]): r for r in rows}
    if set(by_key) != expected or len(rows) != len(expected):
        raise ValueError("missing, duplicated or undeclared B07 cells")
    indices = np.random.default_rng(protocol.bootstrap_seed).integers(
        0, len(protocol.worlds), (protocol.bootstrap_resamples, len(protocol.worlds)))
    by_world = {cell_name(arm, schedule): {metric: np.asarray([
        np.mean([by_key[arm, schedule, world, q, tape][metric]
                 for q in range(4) for tape in ((-1,) if arm == "C" else (0, 1))])
        for world in protocol.worlds]) for metric in METRICS} for arm, schedule in CELLS}
    levels = {cell: {metric: sample_summary(values, indices) for metric, values in table.items()}
              for cell, table in by_world.items()}
    vectors = {}
    for later, earlier in (("C/DISPERSED", "C/SYNC"), ("Q10/DISPERSED", "Q10/SYNC"),
                           ("Q10/SYNC", "C/SYNC"), ("Q10/DISPERSED", "C/DISPERSED")):
        vectors[later + "-" + earlier] = {metric: by_world[later][metric] - by_world[earlier][metric]
                                          for metric in METRICS}
    interaction = "(Q10/DISPERSED-Q10/SYNC)-(C/DISPERSED-C/SYNC)"
    vectors[interaction] = {metric: vectors["Q10/DISPERSED-Q10/SYNC"][metric]
                           - vectors["C/DISPERSED-C/SYNC"][metric] for metric in METRICS}
    return dict(levels=levels, comparisons={name: {metric: sample_summary(values, indices)
                for metric, values in table.items()} for name, table in vectors.items()},
                worlds=list(protocol.worlds), primary="C/DISPERSED-C/SYNC:J",
                consequential=["C/DISPERSED-C/SYNC:mean_served", "Q10/DISPERSED-Q10/SYNC", interaction],
                scope="All four q offsets and Q10's two tapes averaged within each world. Conditional "
                      "descriptive world-percentile intervals, not training replication, confirmation, "
                      "equivalence, individual-user continuity or steady-state-only attribution.")
