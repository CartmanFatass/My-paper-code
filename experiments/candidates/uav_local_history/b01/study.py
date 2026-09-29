"""Complete native episodes, evaluator-only audits, and compact paired reading."""

import hashlib
import json
import os
from pathlib import Path
import resource
import time

import numpy as np
from scipy.stats import t as student_t

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from .controller import LocalController

HORIZON = 256
SEEDS = tuple(range(29091000, 29091032))
ARMS = ("C", "H")


def write_json(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def file_identity(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def own_positions(obs):
    positions = np.array(obs[:, :3], dtype=np.float64, copy=True)
    positions[:, :2] *= 1000.0
    positions[:, 2] = 50.0 + 100.0 * positions[:, 2]
    return positions


def audit_points(points, true_users):
    """Privileged evaluator diagnostics; returned values never enter the actor."""
    if not len(points):
        return {"max_error_m": 0.0, "unmatched": 0, "duplicate_matches": 0,
                "ambiguous_matches": 0, "unique_true_users": 0}
    distances = np.linalg.norm(points[:, None, :] - true_users[None, :, :], axis=-1)
    nearest = distances.argmin(axis=1)
    errors = distances[np.arange(len(points)), nearest]
    return {
        "max_error_m": float(errors.max()), "unmatched": int((errors > .01).sum()),
        "duplicate_matches": int(len(points) - len(np.unique(nearest))),
        "ambiguous_matches": int(((distances <= .01).sum(axis=1) > 1).sum()),
        "unique_true_users": int(len(np.unique(nearest))),
    }


def native_reading(info):
    global_info = info["infos_dict"]["uav_0"]["global"]
    connections = np.asarray(global_info["connections"], dtype=bool)
    sinr = np.asarray(global_info["sinr_matrix"], dtype=np.float64)
    service = int(global_info["served_users"])
    if service != int(connections.sum()):
        raise RuntimeError("inconsistent native service fields")
    quality = float(np.clip((sinr[connections] - 3.0) / 30.0, 0, 1).sum()
                    / max(service, 1))
    reward = sum(float(value) for value in info["rewards_dict"].values())
    if not np.isfinite(reward) or not np.isclose(reward, .7 * service / 50 + .3 * quality,
                                               rtol=0, atol=1e-12):
        raise RuntimeError("native reward reconstruction failed")
    return reward, service, quality


def collect_episode(env, arm, seed, out, counts, *, horizon=HORIZON):
    started = time.perf_counter()
    obs, info = env.reset(seed=seed)
    counts["explicit_resets"] += 1
    if np.asarray(obs).shape != (5, 104):
        raise ValueError("B01 requires five 104-feature actor rows")
    # This evaluator copy has no connection to controller construction or act().
    true_users = np.array(info["state_info"]["user_positions"], dtype=np.float64, copy=True)
    actual_positions = np.array(info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
    controllers = [LocalController(history=arm == "H") for _ in range(5)]
    raw = {name: [] for name in (
        "observations", "commands", "displacements", "reward", "served", "sinr_quality",
        "decision", "fallback", "selected_index", "shadow_current_index",
        "shadow_current_fallback", "shadow_command_disagreement", "shadow_executed_disagreement",
        "n_current", "n_cached", "n_absent",
        "mean_absent_age", "max_absent_age", "predicted_J", "predicted_service",
        "n_visible_peers", "audit_error_m", "audit_unmatched", "audit_duplicates",
        "audit_ambiguous", "audit_unique_true_users", "post_positions",
    )}
    decision_raw = {name: [] for name in ("decision_time", "cache_points", "cache_last_seen",
                                        "cache_current_mask", "candidate_scores", "candidate_service")}
    initial_positions = actual_positions.copy()
    first_seen = np.full(5, -1, dtype=np.int64)
    for clock in range(horizon):
        commands, diagnostics, audits = [], [], []
        for agent, controller in enumerate(controllers):
            command, diagnostic = controller.act(obs[agent].copy(), clock)
            commands.append(command)
            diagnostics.append(diagnostic)
            audits.append(audit_points(controller.points, true_users))
            if first_seen[agent] < 0 and diagnostic["n_current"]:
                first_seen[agent] = clock
        commands = np.asarray(commands, dtype=np.float32)
        if commands.shape != (5, 3) or not np.isfinite(commands).all() or np.abs(commands).max() > 1:
            raise RuntimeError("invalid controller command")
        before = actual_positions
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        for key in ("decision", "fallback", "selected_index", "shadow_current_index",
                    "shadow_current_fallback", "shadow_command_disagreement", "shadow_executed_disagreement",
                    "n_current", "n_cached", "n_absent",
                    "mean_absent_age", "max_absent_age", "predicted_J", "predicted_service",
                    "n_visible_peers"):
            raw[key].append([diagnostic[key] for diagnostic in diagnostics])
        for destination, key in (("audit_error_m", "max_error_m"), ("audit_unmatched", "unmatched"),
                                 ("audit_duplicates", "duplicate_matches"),
                                 ("audit_ambiguous", "ambiguous_matches"),
                                 ("audit_unique_true_users", "unique_true_users")):
            raw[destination].append([audit[key] for audit in audits])
        if clock % 4 == 0:
            points = np.zeros((5, 64, 2), dtype=np.float64)
            seen = np.full((5, 64), -1, dtype=np.int64)
            current = np.zeros((5, 64), dtype=bool)
            for agent, controller in enumerate(controllers):
                size = len(controller.points)
                points[agent, :size] = controller.points
                seen[agent, :size] = controller.last_seen
                current[agent, :size] = controller.current_mask
            decision_raw["decision_time"].append(clock)
            decision_raw["cache_points"].append(points)
            decision_raw["cache_last_seen"].append(seen)
            decision_raw["cache_current_mask"].append(current)
            decision_raw["candidate_scores"].append([d["scores"] for d in diagnostics])
            decision_raw["candidate_service"].append([d["served_candidates"] for d in diagnostics])
        counts["native_step_calls"] += 1
        next_obs, _average_agent_reward, terminated, truncated, next_info = env.step(commands)
        counts["team_steps"] += 1
        reward, served, quality = native_reading(next_info)
        after = np.array(next_info["state_info"]["uav_positions"], dtype=np.float64, copy=True)
        raw["reward"].append(reward)
        raw["served"].append(served)
        raw["sinr_quality"].append(quality)
        raw["displacements"].append(after - before)
        raw["post_positions"].append(after)
        if (terminated or truncated) != (clock + 1 == horizon):
            raise RuntimeError(f"unexpected native boundary at {clock + 1}/{horizon}")
        obs, actual_positions = next_obs, after
    arrays = {name: np.asarray(values) for name, values in raw.items()}
    arrays.update({name: np.asarray(values) for name, values in decision_raw.items()})
    arrays.update(true_users=true_users, initial_positions=initial_positions, first_seen=first_seen,
                  terminal_observation=obs.copy())
    path = Path(out) / "raw" / f"{arm}_{seed}.npz"
    np.savez_compressed(path, **arrays)
    reward, served = arrays["reward"], arrays["served"]
    decision = arrays["decision"].astype(bool)
    fallback = arrays["fallback"].astype(bool)
    shadow_disagreement = decision & (arrays["selected_index"] != arrays["shadow_current_index"])
    post = arrays["post_positions"]
    boundary = ((post[..., 0] <= 1e-3) | (post[..., 0] >= 1000 - 1e-3)
                | (post[..., 1] <= 1e-3) | (post[..., 1] >= 1000 - 1e-3))
    counter_keys = set().union(*(controller.counters for controller in controllers))
    controller_counts = {key: sum(int(c.counters.get(key, 0)) for c in controllers)
                         for key in sorted(counter_keys)}
    row = {
        "arm": arm, "seed": seed, "steps": horizon, "J": float(reward.mean()),
        "return_sum": float(reward.sum()), "mean_served": float(served.mean()),
        "min_served": int(served.min()), "service_p10": float(np.quantile(served, .1)),
        "zero_service_steps": int((served == 0).sum()),
        "mean_sinr_quality": float(arrays["sinr_quality"].mean()),
        "coverage_reward": float(.7 * served.mean() / 50),
        "quality_reward": float(.3 * arrays["sinr_quality"].mean()),
        "mean_path_length_m": float(np.linalg.norm(arrays["displacements"], axis=-1).sum(axis=0).mean()),
        "xy_boundary_uav_steps": int(boundary.sum()),
        "lower_altitude_uav_steps": int((post[..., 2] <= 50.001).sum()),
        "fallback_decisions": int((decision & fallback).sum()),
        "fallback_uav_steps": int(fallback.sum()),
        "first_user_observation_time": first_seen.tolist(),
        "never_observed_uavs": int((first_seen < 0).sum()),
        "absent_point_decisions": int((decision & (arrays["n_absent"] > 0)).sum()),
        "same_input_shadow_action_disagreements": int(shadow_disagreement.sum()) if arm == "H" else None,
        "same_input_shadow_executed_disagreements": int((decision & arrays["shadow_executed_disagreement"]).sum()) if arm == "H" else None,
        "shadow_fallback_decisions": int((decision & arrays["shadow_current_fallback"]).sum()) if arm == "H" else None,
        "mean_cached_points": float(arrays["n_cached"].mean()),
        "max_cached_points": int(arrays["n_cached"].max()),
        "mean_absent_points": float(arrays["n_absent"].mean()),
        "max_absent_age": int(arrays["max_absent_age"].max()),
        "max_cache_position_error_m": float(arrays["audit_error_m"].max()),
        "unmatched_cache_point_observations": int(arrays["audit_unmatched"].sum()),
        "duplicate_cache_match_observations": int(arrays["audit_duplicates"].sum()),
        "ambiguous_cache_match_observations": int(arrays["audit_ambiguous"].sum()),
        "controller_counts": controller_counts,
        "wall_seconds": time.perf_counter() - started, "raw": file_identity(path),
    }
    counts["complete_episodes"] += 1
    return row


def paired_reading(rows):
    by_key = {(row["arm"], row["seed"]): row for row in rows}
    if len(by_key) != len(rows):
        raise ValueError("duplicate arm/world endpoint")
    seeds = sorted({row["seed"] for row in rows})
    if any((arm, seed) not in by_key for seed in seeds for arm in ARMS):
        raise ValueError("paired reading requires every C/H episode")
    result = {}
    for metric in ("J", "mean_served", "return_sum", "mean_sinr_quality", "min_served",
                   "zero_service_steps", "mean_path_length_m", "xy_boundary_uav_steps"):
        differences = np.array([by_key[("H", seed)][metric] - by_key[("C", seed)][metric]
                                for seed in seeds], dtype=np.float64)
        mean = float(differences.mean())
        half = (float(student_t.ppf(.975, len(seeds) - 1) * differences.std(ddof=1)
                      / np.sqrt(len(seeds))) if len(seeds) > 1 else None)
        result[metric] = {"mean_H_minus_C": mean, "differences": differences.tolist(),
                          "descriptive_t95": [mean - half, mean + half] if half is not None else None,
                          "positive": int((differences > 0).sum()),
                          "negative": int((differences < 0).sum()),
                          "zero": int((differences == 0).sum())}
    return {"seeds": seeds, "unit": "world for these fixed deterministic programs; no training inference",
            "metrics": result}


def run_batch(out, launch_sha, *, factory=make_real, seeds=SEEDS, horizon=HORIZON, entry_start=None):
    started = time.perf_counter() if entry_start is None else entry_start
    usage = resource.getrusage(resource.RUSAGE_SELF)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists() or (out / "raw").exists():
        raise FileExistsError("refusing to replace an existing scientific output")
    (out / "raw").mkdir()
    counts = {"constructors": 0, "explicit_resets": 0, "native_step_calls": 0,
              "team_steps": 0, "complete_episodes": 0, "fit_started": 0, "optimizer_steps": 0}
    config = {
        "arms": list(ARMS), "seeds": list(seeds), "horizon": horizon, "n_agents": 5,
        "cache_capacity": 64, "association_tolerance_m": .01, "censor_margin_db": .0001,
        "decision_period": 4, "candidates": 27, "unknown_peer_grid": [8, 8, 100],
        "seed_order": "ascending; C/H on even world index, H/C on odd",
        "training": None, "planned_fits": 0, "planned_team_steps": 2 * len(seeds) * horizon,
        "numpy_threads": 1, "source_constructor": "ucope.uav_motion_prefix_b01.environment.make_real",
        "actor_information": "one own 104-feature observation row; private bounded geometry/navigation only",
        "evaluator_truth": "state_info coordinates only for after-action association/motion audit",
        "launch_sha": launch_sha,
    }
    summary = {"object": "UAV-LOCAL-HISTORY-B01", "status": "INCOMPLETE", "launch_sha": launch_sha,
               "scientific_invocation": factory is make_real, "counts": counts, "rows": [],
               "limits": [], "config": config}
    write_json(out / "config.json", config)
    write_json(out / "summary.json", summary)
    env = None
    try:
        env = factory(seeds[0])
        counts["constructors"] += 1
        for index, seed in enumerate(seeds):
            for arm in (ARMS if index % 2 == 0 else ARMS[::-1]):
                row = collect_episode(env, arm, seed, out, counts, horizon=horizon)
                summary["rows"].append(row)
                write_json(out / "summary.json", summary)
                print(json.dumps({"arm": arm, "seed": seed, "complete_episodes": counts["complete_episodes"],
                                  "team_steps": counts["team_steps"], "wall_seconds": row["wall_seconds"]}), flush=True)
        if counts["team_steps"] != config["planned_team_steps"]:
            raise RuntimeError("scientific step count mismatch")
        summary["paired"] = paired_reading(summary["rows"])
        summary["status"] = "COMPLETE"
    except Exception as error:
        summary["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        if env is not None:
            try:
                env.close()
            except Exception as error:
                summary["status"] = "INCOMPLETE"
                summary["limits"].append(f"environment close: {type(error).__name__}: {error}")
        final = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "wall_seconds_from_runner_entry": time.perf_counter() - started,
            "user_seconds_batch": final.ru_utime - usage.ru_utime,
            "system_seconds_batch": final.ru_stime - usage.ru_stime,
            "process_lifetime_peak_rss_kib_linux": final.ru_maxrss,
            "scope": "one worker; user/system delta starts after scientific imports, wall starts at runner entry",
            "thread_environment": {name: os.environ.get(name) for name in
                                   ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
        }
        summary["artifacts"] = {"raw_files": len(summary["rows"]),
                                "raw_bytes": sum(row["raw"]["bytes"] for row in summary["rows"])}
        write_json(out / "summary.json", summary)
    return summary
