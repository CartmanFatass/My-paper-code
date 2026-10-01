"""Complete native components and shared paired-world pointwise bootstrap."""
import numpy as np
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reading import _summary, episode_metrics as original_metrics
from .contract import CONTRASTS, DETERMINISTIC, PROGRAMS


def episode_metrics(raw):
    view=dict(raw,gate_count=raw["gate_count_boundary"],gate_prediction=raw["gate_prediction_boundary"])
    result=original_metrics(view)
    displacement=np.diff(raw["positions"],axis=0)
    silent=~raw["transmitter_mask"]
    midpoint=len(raw["reward"])//2
    result.update(noneligible_off_requests=int(np.count_nonzero(raw["requested_off"] & ~raw["eligible"])),
        silent_moving_uav_ticks=int(np.count_nonzero(silent & np.any(displacement != 0.,axis=-1))),
        silent_travel_m=float(np.linalg.norm(displacement,axis=-1)[silent].sum()),
        clipped_command_uav_ticks=int(np.count_nonzero(np.any(displacement != raw["commands"].astype(np.float64)*30.,axis=-1))),
        memory_created=int(raw["memory_created"].sum()), memory_consumed=int(raw["memory_consumed"].sum()),
        terminal_pending=int(raw["terminal_pending"].sum()), bypass_requests=int((~raw["c_available"]).sum()),
        positive_count_off=int(np.count_nonzero(raw["requested_off"] & (raw["n_current"]>0))),
        distinct_return_origins=int(np.count_nonzero(raw["memory_created"] & (raw["origin_c_index"]!=raw["origin_issued_index"]))),
        consumed_nonzero=int(np.count_nonzero(raw["memory_consumed"] & (raw["action_index"]!=0))),
        consumed_old_silent=int(np.count_nonzero(raw["memory_consumed"] & ~raw["old_decision_mask"])),
        C_requests=int(raw["c_available"].sum()), CJ_off_score_evaluations=int(raw["off_evaluated"].sum()))
    for name,part in (("first",slice(0,midpoint)),("later",slice(midpoint,None))):
        result[name+"_J"]=float(raw["reward"][part].mean())
        result[name+"_mean_served"]=float(raw["served"][part].mean())
        result[name+"_zero_service_steps"]=int(np.count_nonzero(raw["served"][part]==0))
    result["requested_category_counts"]=np.bincount(raw["action_index"].ravel(),minlength=27).tolist()
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
                            "Conditional on the retained original P0 and these fixed programs; "
                            "no independent-parent, training-population, simultaneous-comparison or equivalence coverage.",
                bootstrap=dict(seed=protocol.bootstrap_seed, resamples=protocol.bootstrap_resamples, quantile="linear"))


def paired_behavior(left,right):
    """Shared prefixes stop at the first command/mask difference."""
    same=(left["commands"]==right["commands"]).all(axis=(1,2)) & (left["transmitter_mask"]==right["transmitter_mask"]).all(axis=1)
    differences=np.flatnonzero(~same)
    prefix=int(differences[0]) if len(differences) else len(same)
    return dict(shared_prefix_steps=prefix,first_execution_difference_tick=prefix if len(differences) else None,
        category_difference_decisions=int(np.count_nonzero(left["action_index"]!=right["action_index"])),
        mask_difference_uav_ticks=int(np.count_nonzero(left["transmitter_mask"]!=right["transmitter_mask"])),
        displacement_difference_uav_ticks=int(np.count_nonzero(np.any(np.diff(left["positions"],axis=0)!=np.diff(right["positions"],axis=0),axis=-1))),
        position_difference_uav_states=int(np.count_nonzero(np.any(left["positions"]!=right["positions"],axis=-1))),
        reading="Prefix matched only while executed command/mask history is shared; all later differences are descriptive.")
