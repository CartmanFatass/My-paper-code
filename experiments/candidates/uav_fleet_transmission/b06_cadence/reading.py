"""Complete native metrics and the fixed paired-world descriptive comparisons."""
import numpy as np

from experiments.candidates.uav_fleet_transmission.b05_score_sampling.reading import sample_summary
from .contract import CELLS, MODES, ORDINARY_ARMS, cell_name

METRICS = (
    "J", "return_sum", "mean_served", "service_p10", "min_served", "zero_service_steps",
    "longest_zero_run", "mean_sinr_quality", "coverage_reward", "quality_reward",
    "mean_path_length_m", "xy_boundary_uav_steps", "lower_altitude_uav_steps",
    "zero_displacement_uav_ticks", "queries", "fallback_decisions", "policy_cache_hits",
    "mean_entropy", "offgrid_count_losses", "eligible_extra_queries", "event_queries",
    "event_category_changes", "event_remaining_motion_changes", "decision_query_cpu_seconds",
    "decision_query_wall_seconds", "gate_cpu_seconds", "gate_wall_seconds", "cpu_seconds", "wall_seconds",
)


def episode_metrics(raw):
    served = raw["served"]
    longest, current = 0, 0
    for value in served:
        current = current + 1 if value == 0 else 0
        longest = max(longest, current)
    displacements = raw["positions"][1:] - raw["positions"][:-1]
    positions = raw["positions"][1:]
    extra = raw["query_kind"] == 1
    offgrid = np.arange(len(served)) % 4 != 0
    losses = raw["count_loss"][offgrid]
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
                offgrid_count_losses=int(losses.sum()),
                eligible_extra_queries=int((raw["count_loss"] & raw["extra_available"]).sum()),
                event_queries=int(extra.sum()),
                event_category_changes=int(np.count_nonzero(extra & (raw["action_index"] != raw["held_before"]))),
                event_remaining_motion_changes=int(np.count_nonzero(extra & raw["remaining_motion_changed"])))


def contrast_pairs():
    pairs = []
    for arm in ("C", "Q10", "Q05", "G", "S_L0", "S_L1"):
        pairs.extend(((cell_name(arm, "E"), cell_name(arm, "H4")),
                      (cell_name(arm, "E"), cell_name(arm, "H1")),
                      (cell_name(arm, "H1"), cell_name(arm, "H4"))))
    for arm in ("S_L0", "S_L1"):
        for mode in MODES:
            pairs.extend((cell_name(arm, mode), cell_name(ordinary, mode)) for ordinary in ORDINARY_ARMS)
    pairs.extend((cell_name("S_L0", mode), "Bstar_L0/H4") for mode in MODES)
    return pairs


def comparisons(rows, protocol):
    expected = {(arm, mode, world, tape) for world in protocol.worlds
                for arm, mode, tape in protocol.episode_order(0)}
    by_key = {(r["arm"], r["mode"], r["world"], r["tape"]): r for r in rows}
    if set(by_key) != expected or len(rows) != len(expected):
        raise ValueError("missing, duplicated or undeclared B06 cells")
    indices = np.random.default_rng(protocol.bootstrap_seed).integers(
        0, len(protocol.worlds), (protocol.bootstrap_resamples, len(protocol.worlds)))
    by_world = {cell_name(arm, mode): {metric: np.asarray([
        np.mean([by_key[arm, mode, world, tape][metric] for tape in ((-1,) if arm == "C" else (0, 1))])
        for world in protocol.worlds]) for metric in METRICS} for arm, mode in CELLS}
    levels = {cell: {metric: sample_summary(values, indices) for metric, values in table.items()}
              for cell, table in by_world.items()}
    pairs = {later + "-" + earlier: {
        metric: sample_summary(by_world[later][metric] - by_world[earlier][metric], indices)
        for metric in METRICS} for later, earlier in contrast_pairs()}
    return dict(levels=levels, comparisons=pairs, worlds=list(protocol.worlds),
                aliases={"Bstar_L1/H4": "S_L1/H4"},
                primary=[f"S_L{x}/E-S_L{x}/{mode}" for x in (0, 1) for mode in ("H4", "H1")],
                scope="Two tapes averaged within each paired world; C once. Conditional descriptive "
                      "world-percentile intervals; fixed assets, no training replication, equivalence, "
                      "individual-user continuity or reliability inference.")
