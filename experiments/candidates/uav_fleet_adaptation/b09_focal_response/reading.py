"""Complete native components and fixed conditional paired-world comparisons."""
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b08_local_gate.reading import _longest, _summary
from .contract import CONTRASTS, EGOS, PANELS


def episode_metrics(raw):
    reward, served, quality = (np.asarray(raw[key]) for key in ("reward", "served", "sinr_quality"))
    positions = np.asarray(raw["positions"], dtype=np.float64)
    displacement, post = np.diff(positions, axis=0), positions[1:]
    travel = np.linalg.norm(displacement, axis=-1).sum(axis=0)
    lower, upper = post[..., 2] <= 50.001, post[..., 2] >= 149.999
    boundary = ((post[..., :2] <= .001) | (post[..., :2] >= 999.999)).any(axis=-1)
    matches = np.asarray(raw["history_matches"]) >= 0
    moving = np.any(np.asarray(raw["history_delta"]) != 0, axis=-1)
    descriptor = np.asarray(raw["history_descriptor"])
    result = dict(steps=len(reward), J=float(reward.mean()), return_sum=float(reward.sum()),
                  mean_served=float(served.mean()), service_p10=float(np.quantile(served, .1, method="linear")),
                  min_served=int(served.min()), zero_service_steps=int(np.count_nonzero(served == 0)),
                  zero_service_episode=int(np.any(served == 0)), longest_zero_service_streak=_longest(served == 0),
                  mean_sinr_quality=float(quality.mean()), coverage_reward=float(.7 * served.mean() / 50),
                  quality_reward=float(.3 * quality.mean()), mean_path_length_m=float(travel.mean()),
                  mean_height_m=float(post[..., 2].mean()), end_height_m=float(post[-1, :, 2].mean()),
                  lower_altitude_uav_steps=int(lower.sum()), upper_altitude_uav_steps=int(upper.sum()),
                  xy_boundary_uav_steps=int(boundary.sum()), zero_displacement_uav_ticks=int(np.all(displacement == 0, axis=-1).sum()),
                  active_transmitter_ticks=int(np.asarray(raw["transmitter_mask"]).sum()),
                  mean_visible_users=float(np.mean(raw["n_current"])), mean_visible_peers=float(np.mean(raw["n_peers"])),
                  ego_mean_visible_users=float(np.mean(raw["n_current"][:, 0])),
                  ego_mean_visible_peers=float(np.mean(raw["n_peers"][:, 0])),
                  fallback_decisions=int(np.count_nonzero(raw["fallback"])),
                  ego_fallback_decisions=int(np.count_nonzero(raw["fallback"][:, 0])),
                  mean_motion_entropy=float(np.mean(raw["entropy"])), ego_mean_entropy=float(np.mean(raw["entropy"][:, 0])),
                  policy_cache_hits=int(np.count_nonzero(raw["memo_hit"])), policy_decisions=int(raw["action_index"].size),
                  tracked_peer_rows=int(np.asarray(raw["history_n_peers"]).sum()),
                  tracked_matched_rows=int(matches.sum()), tracked_moving_rows=int(moving.sum()),
                  tracked_nonzero_ticks=int(np.any(descriptor != 0, axis=-1).sum()),
                  tracked_nonzero_decisions=int(np.any(descriptor[::4] != 0, axis=-1).sum()),
                  tracked_moving_decisions=int(moving[::4].any(axis=-1).sum()),
                  tracked_ambiguous_rows=int(((~matches) & (raw["history_gate_counts"] > 0)).sum()))
    for i in range(5):
        result.update({f"uav{i}_{key}": value for key, value in (
            ("travel_m", float(travel[i])), ("mean_height_m", float(post[:, i, 2].mean())),
            ("end_height_m", float(post[-1, i, 2])), ("lower_height_ticks", int(lower[:, i].sum())),
            ("upper_height_ticks", int(upper[:, i].sum())), ("xy_boundary_ticks", int(boundary[:, i].sum())),
            ("mean_served", float(np.asarray(raw["connections"])[:, i].sum(axis=-1).mean())),
            ("zero_displacement_ticks", int(np.all(displacement[:, i] == 0, axis=-1).sum())))})
    for choice in range(27):
        result[f"ego_category_{choice}_decisions"] = int(np.count_nonzero(raw["action_index"][:, 0] == choice))
    return result


def metric_values(row):
    exclude = {"world", "tape", "block", "group", "motion_root", "assignment_root", "assignment_index"}
    values = {key: float(value) for key, value in row.items() if key not in exclude and type(value) in (int, float)}
    values.update({"policy_" + key: float(value) for key, value in row["policy_counts"].items()})
    if not all(np.isfinite(value) for value in values.values()):
        raise ValueError("nonfinite episode measurement")
    return values


def comparisons(rows, protocol):
    final = [row for row in rows if row["kind"] == "evaluation"]
    by_key = {(row["ego"], row["panel"], row["world"], row["tape"]): row for row in final}
    expected = {(ego, panel, world, tape) for world in protocol.worlds for ego, panel, tape in protocol.episode_order(0)}
    if len(by_key) != len(final) or set(by_key) != expected:
        raise ValueError("incomplete/duplicate fixed final panel")
    values = {key: metric_values(row) for key, row in by_key.items()}
    metrics = tuple(sorted(next(iter(values.values()))))
    if any(tuple(sorted(row)) != metrics for row in values.values()):
        raise ValueError("different episode measurement columns")
    tapes = range(len(protocol.evaluation_roots))
    world_values = {(ego, panel): {metric: np.array([
        np.mean([values[ego, panel, world, tape][metric] for tape in tapes]) for world in protocol.worlds])
        for metric in metrics} for ego in EGOS for panel in PANELS}
    indices = np.random.default_rng(protocol.bootstrap_seed).integers(
        0, len(protocol.worlds), size=(protocol.bootstrap_resamples, len(protocol.worlds)))
    levels = {f"{ego}/{panel}": {metric: _summary(vector, indices) for metric, vector in measurements.items()}
              for (ego, panel), measurements in world_values.items()}
    contrasts, adverses = {}, {}
    for left, right, panel in CONTRASTS:
        key = f"{left}-{right}/{panel}"
        contrasts[key] = {metric: _summary(world_values[left, panel][metric] - world_values[right, panel][metric], indices)
                          for metric in metrics}
        adverses[key] = {}
        for metric, sign in (("J", -1), ("mean_served", -1), ("service_p10", -1), ("min_served", -1),
                             ("zero_service_steps", 1), ("longest_zero_service_streak", 1), ("mean_path_length_m", 1)):
            vector = np.asarray(contrasts[key][metric]["world_values"])
            adverses[key][metric] = dict(worlds=[w for w, value in zip(protocol.worlds, vector) if sign * value > 0],
                world_tapes=[dict(world=world, tape=tape,
                                  difference=values[left, panel, world, tape][metric] - values[right, panel, world, tape][metric])
                             for world in protocol.worlds for tape in tapes
                             if sign * (values[left, panel, world, tape][metric] - values[right, panel, world, tape][metric]) > 0])
    return dict(worlds=list(protocol.worlds), levels=levels, contrasts=contrasts, adverses=adverses,
                primary=[f"H{block}-F{block}/{panel}" for block in range(2) for panel in PANELS],
                uncertainty="Pointwise paired-world percentile bootstrap after averaging both tapes within each world; "
                            "training blocks and rosters separate. Conditional on these four fitted endpoints and retained "
                            "P0/P1 assets; no training-population or simultaneous-coverage claim.",
                bootstrap=dict(seed=protocol.bootstrap_seed, resamples=protocol.bootstrap_resamples, quantile="linear"))
