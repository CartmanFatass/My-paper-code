"""One admitted fixed three-fit availability-recovery study."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time
import traceback

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

for _variable in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_variable] = "1"

import numpy as np
import torch

from ha_ctse_process.uav_episode_schema import Cell, SERVICE_TARGET
from ha_ctse_process.uav_g0_environment import UAVSourceIdentifiabilityEnv
from ha_ctse_process.uav_g0_geometry import make_episode_source
from ha_ctse_process.uav_g0_statistics import weakest_hotspot_service_row
from experiments.candidates.uav_availability_recovery.control import FEATURE_DIM, HORIZON, RecoveryControl
from experiments.candidates.uav_availability_recovery.learning import (
    EVAL_IDS, FIT_SEEDS, MacroTransition, Policy, parameter_vector, ppo_update, training_world_ids,
)


DIRECTION = "uav_availability_recovery"
METRICS = (
    "scenario7_reward", "qos_satisfaction_ratio", "graph_potential_delta",
    "graph_potential_before", "graph_potential", "safety_reward_before_pbrs",
    "return_risk_penalty", "cutoff_event_count", "depletion_event_count",
)


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def append_json(path, value):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def maximum_streak(values, threshold=0.6):
    longest = current = 0
    for value in values:
        current = current + 1 if value < threshold else 0
        longest = max(current, longest)
    return longest


def episode_metrics(arrays, *, world, arm, onset, duration, event):
    native = arrays["native_metrics"]
    j = native[:, 0]
    qos = native[:, 1]
    weakest = arrays["weakest_service"]
    rejoin = onset + duration
    window_stop = min(rejoin + 60, HORIZON)
    event_values = weakest[onset:window_stop]
    deficit = np.maximum(0, SERVICE_TARGET-event_values) / SERVICE_TARGET
    path = np.linalg.norm(np.diff(arrays["positions"], axis=0), axis=-1)
    action_counts = np.bincount(arrays["joint_action"], minlength=16)
    result = {
        "world": int(world), "arm": arm, "cell": "event" if event else "no_event",
        "steps": HORIZON, "onset": int(onset), "duration": int(duration),
        "J": float(j.sum()), "QoS": float(qos.mean()),
        "graph_potential_delta_sum": float(native[:, 2].sum()),
        "weakest_service_mean": float(weakest.mean()), "weakest_service_min": float(weakest.min()),
        "J_event": float(1-deficit.mean()) if event else 1.0,
        "event_deficit_sum": float(deficit.sum()) if event else 0.0,
        "event_min_service": float(event_values.min()) if event else float(weakest.min()),
        "event_catastrophe": int(maximum_streak(event_values) >= 10) if event else 0,
        "event_max_below_06_streak": maximum_streak(event_values) if event else 0,
        "complete_max_below_06_streak": maximum_streak(weakest),
        "zero_QoS_steps": int(np.count_nonzero(qos == 0)),
        "guard_blocked_actions": int(arrays["native_guard_count"].sum()),
        "motion_modified_rows": int(arrays["motion_modified"].sum()),
        "reserve_motion_modified_rows": int(arrays["motion_modified"][:, 6:].sum()),
        "path_length_m": float(path.sum()), "reserve_path_length_m": float(path[:, 6:].sum()),
        "joint_decisions": int(len(arrays["joint_action"])), "joint_action_counts": action_counts.tolist(),
        "shadow_S_disagreements": int(np.count_nonzero(arrays["joint_action"] != arrays["incumbent_action"])),
        "native_return_penalty_sum": float(native[:, 6].sum()),
        "cutoff_events": int(native[:, 7].sum()), "depletion_events": int(native[:, 8].sum()),
    }
    windows = {"pre": (0, onset), "absence": (onset, rejoin),
               "rejoin60": (rejoin, window_stop), "post": (window_stop, HORIZON)}
    result["windows"] = {
        name: {"start": start, "stop": stop, "J": float(j[start:stop].sum()),
               "QoS": float(qos[start:stop].mean()),
               "weakest_service": float(weakest[start:stop].mean())}
        for name, (start, stop) in windows.items()
    }
    return result


def run_episode(source, *, arm, policy=None, generator=None, training=False, event=True):
    wall_start = time.monotonic()
    cpu_start = time.process_time()
    env = UAVSourceIdentifiabilityEnv(source, Cell.EVENT if event else Cell.NO_EVENT)
    try:
        env.reset()
        if env.reward_discount_gamma != 0.99 or env.max_steps != HORIZON:
            raise ValueError("native reward/horizon drift")
        if env.battery_enabled or env.charging_enabled or env.failure_enabled:
            raise ValueError("native S7-S1 inventory drift")
        controller = RecoveryControl(source, env)
        predictor = None
        if arm == "P":
            from experiments.candidates.uav_availability_recovery.predictor import PublicPredictor
            predictor = PublicPredictor()
        if arm == "L" and policy is None:
            raise ValueError("L requires a policy")
        arrays = {
            "native_metrics": np.empty((HORIZON, len(METRICS)), dtype=np.float64),
            "user_rates_mbps": np.empty((HORIZON, 30), dtype=np.float64),
            "weakest_service": np.empty(HORIZON, dtype=np.float64),
            "positions": np.empty((HORIZON+1, 8, 3), dtype=np.float64),
            "targets": np.empty((HORIZON, 8, 3), dtype=np.float64),
            "requested_actions": np.empty((HORIZON, 8, 4), dtype=np.float32),
            "executed_velocities": np.empty((HORIZON, 8, 3), dtype=np.float64),
            "active_mask": np.empty((HORIZON, 8), dtype=bool),
            "association": np.empty((HORIZON, 8, 30), dtype=bool),
            "motion_modified": np.empty((HORIZON, 8), dtype=bool),
            "native_guard_count": np.empty(HORIZON, dtype=np.int64),
        }
        transitions = []
        current_macro = None
        decisions = []
        features = []
        predictions = []
        events = env.consume_boundary_events()
        event_output = []
        planner_wall = 0.0
        planner_calls = 0
        for t in range(HORIZON):
            view = controller.view(env, events)
            event_output.extend(item.to_primitive() for item in events)
            events = ()
            choice = None
            if arm in {"P", "L"} and view["decision"]:
                if current_macro is not None:
                    current_macro.stop = t
                    transitions.append(current_macro)
                if arm == "L":
                    choice, log_prob, value, entropy = policy.choose(
                        view["feature"], generator=generator, deterministic=not training)
                    current_macro = MacroTransition(view["feature"].copy(), choice, log_prob, value, t, t, 0.0)
                else:
                    planner_start = time.monotonic()
                    previous_calls = predictor.snapshot_calls
                    decision = predictor.score(controller.snapshot(env, view))
                    planner_wall += time.monotonic() - planner_start
                    choice = decision.action
                    prediction = decision.to_dict()
                    prediction["step"] = t
                    prediction["snapshot_calls_this_decision"] = decision.snapshot_calls-previous_calls
                    predictions.append(prediction)
                    planner_calls += int(decision.snapshot_calls-previous_calls)
                    log_prob = value = entropy = 0.0
                decisions.append({"step": t, "action": int(choice), "incumbent": view["incumbent"],
                                  "log_prob": log_prob, "value": value, "entropy": entropy})
                features.append(view["feature"])
            dense, targets = controller.commands(env, view, arm=arm, joint_action=choice)
            role_order = np.argsort([controller.role_by_handle[row.handle] for row in view["storage_rows"]])
            role_actions = dense[role_order]
            expected_velocity = np.stack([env._movement_velocity_from_action(action[:3]) for action in role_actions])
            expected_velocity[~view["active"]] = 0.0
            arrays["positions"][t] = view["positions"]
            arrays["targets"][t] = targets
            arrays["requested_actions"][t] = role_actions
            arrays["active_mask"][t] = view["active"]
            arrays["association"][t] = view["association"]
            transition = env.step_dense(dense)
            if transition.physical_step != t:
                raise ValueError("completed-step identity drift")
            if transition.terminated or transition.truncated:
                if t != HORIZON-1 or transition.terminated or not transition.truncated:
                    raise ValueError("unexpected native early ending")
            elif t == HORIZON-1:
                raise ValueError("native endpoint did not truncate")
            native = env.last_constrained_reward_metrics
            arrays["native_metrics"][t] = [native[key] for key in METRICS]
            arrays["user_rates_mbps"][t] = transition.delivered_user_rates_mbps
            arrays["weakest_service"][t] = weakest_hotspot_service_row(
                transition.delivered_user_rates_mbps, np.repeat(np.arange(3), 10))
            arrays["positions"][t+1] = transition.positions_after[role_order]
            arrays["executed_velocities"][t] = transition.actual_velocities[role_order]
            arrays["motion_modified"][t] = np.any(
                np.abs(expected_velocity-transition.actual_velocities[role_order]) > 1e-7, axis=1)
            arrays["native_guard_count"][t] = transition.backhaul_guard_blocked_actions
            if current_macro is not None:
                current_macro.reward += float(native["scenario7_reward"])
            events = transition.boundary_events
        if events:
            raise ValueError("unexpected lifecycle event at final boundary")
        if current_macro is not None:
            current_macro.stop = HORIZON
            transitions.append(current_macro)
        if len(event_output) != (2 if event else 0):
            raise ValueError("lifecycle event inventory mismatch")
        for prediction in predictions:
            step = prediction["step"]
            selected = prediction["action"]
            prediction["realized_QoS_at_horizons"] = [
                float(arrays["native_metrics"][step+horizon-1, 1])
                for horizon in prediction["horizons"]]
            prediction["selected_prediction_errors"] = [
                float(predicted-realized) for predicted, realized in zip(
                    prediction["predictions"][selected], prediction["realized_QoS_at_horizons"])]
            stop = step + prediction["horizons"][-1]
            prediction["realized_mean_QoS_in_forecast_window"] = float(arrays["native_metrics"][step:stop, 1].mean())
            prediction["later_replanning_included_in_realized"] = True
            prediction["forecast_availability_time"] = "boundary t+h after lifecycle events"
            prediction["realized_service_time"] = "completed step t+h-1 before events at boundary t+h"
            prediction["lifecycle_at_forecast_boundary"] = [
                any(item["physical_step"] == step+horizon for item in event_output)
                for horizon in prediction["horizons"]]
        for key, value in arrays.items():
            if not np.isfinite(value).all():
                raise FloatingPointError(f"nonfinite {key}")
        arrays.update({
            "decision_step": np.asarray([row["step"] for row in decisions], dtype=np.int64),
            "joint_action": np.asarray([row["action"] for row in decisions], dtype=np.int64),
            "incumbent_action": np.asarray([row["incumbent"] for row in decisions], dtype=np.int64),
            "decision_entropy": np.asarray([row["entropy"] for row in decisions], dtype=np.float64),
            "decision_features": np.stack(features) if features else np.empty((0, FEATURE_DIM), dtype=np.float32),
            "macro_start": np.asarray([row.start for row in transitions], dtype=np.int64),
            "macro_stop": np.asarray([row.stop for row in transitions], dtype=np.int64),
            "macro_reward": np.asarray([row.reward for row in transitions], dtype=np.float64),
            "macro_value": np.asarray([row.value for row in transitions], dtype=np.float64),
            "macro_log_prob": np.asarray([row.log_prob for row in transitions], dtype=np.float64),
            "events_json": np.asarray(json.dumps(event_output, sort_keys=True)),
            "predictions_json": np.asarray(json.dumps(predictions, sort_keys=True, allow_nan=False)),
            "public_user_xy": controller.user_xy,
            "world_id": np.asarray(source.geometry.episode_id, dtype=np.int64),
            "source_sha256": np.asarray(source.to_primitive()["sha256"]),
        })
        metrics = episode_metrics(arrays, world=source.geometry.episode_id, arm=arm,
                                  onset=source.event.onset, duration=source.event.duration, event=event)
        metrics.update({"episode_wall_s": time.monotonic()-wall_start,
                        "episode_cpu_s": time.process_time()-cpu_start,
                        "service_snapshot_calls": planner_calls, "planner_wall_s": planner_wall,
                        "mean_policy_entropy": float(np.mean(arrays["decision_entropy"])) if decisions and arm == "L" else None,
                        "macro_rows": len(transitions), "actor_updates_in_episode": 0,
                        "source_sha256": str(arrays["source_sha256"]),
                        "physics": {"time_step": float(env.time_step), "max_speed": float(env.max_speed),
                                    "max_vertical_speed_mps": float(env.max_vertical_speed_mps)},
                        "shadow_S": controller.shadow.evidence()})
        if predictions:
            errors = np.asarray([error for row in predictions for error in row["selected_prediction_errors"]])
            metrics["forecast_error_mean"] = float(errors.mean())
            metrics["forecast_error_RMSE"] = float(np.sqrt(np.mean(errors**2)))
        return metrics, arrays, transitions
    finally:
        env.close()


def write_episode(out, name, metrics, arrays):
    raw = out / "raw" / f"{name}.npz"
    np.savez_compressed(raw, **arrays)
    metrics["raw"] = str(raw.relative_to(out))
    metrics["raw_sha256"] = sha256_file(raw)
    metrics["raw_bytes"] = raw.stat().st_size
    return metrics


def train_fit(seed, out, progress, curves):
    start = time.monotonic()
    cpu_start = time.process_time()
    torch.manual_seed(seed)
    policy = Policy()
    initial = parameter_vector(policy)
    torch.save({"seed": seed, "weights": policy.state_dict()}, out / "raw" / f"L_{seed}_init.pt")
    optimizer = torch.optim.Adam(policy.parameters(), lr=3e-4)
    sampler = torch.Generator(device="cpu").manual_seed(seed + 101)
    minibatches = np.random.default_rng(np.random.SeedSequence([seed, 0x504F]))
    worlds = training_world_ids(seed)
    optimizer_updates = macro_rows = row_exposures = 0
    source_wall = 0.0
    for collection in range(32):
        episodes, rows = [], []
        for lane, world in enumerate(worlds[collection*16:(collection+1)*16]):
            source_start = time.monotonic()
            source = make_episode_source(world)
            source_wall += time.monotonic()-source_start
            row, arrays, transitions = run_episode(source, arm="L", policy=policy, generator=sampler, training=True)
            row.update({"seed": seed, "collection": collection, "episode_index": collection*16+lane})
            name = f"train_L_{seed}_{world}"
            write_episode(out, name, row, arrays)
            append_json(out / "raw" / "training_episodes.jsonl", row)
            append_json(out / "progress.jsonl", {"phase": "training", "seed": seed,
                        "complete_episodes": collection*16+lane+1, "complete_steps": (collection*16+lane+1)*HORIZON})
            episodes.append(transitions)
            rows.append(row)
        update = ppo_update(policy, optimizer, episodes, minibatches)
        optimizer_updates += update["optimizer_updates"]
        macro_rows += update["macro_rows"]
        row_exposures += update["optimizer_row_exposures"]
        curve = {"seed": seed, "collection": collection+1, "complete_episodes": (collection+1)*16,
                 "J": float(np.mean([row["J"] for row in rows])),
                 "QoS": float(np.mean([row["QoS"] for row in rows])),
                 "guard_blocked_actions": int(sum(row["guard_blocked_actions"] for row in rows)),
                 "joint_action_counts": np.sum([row["joint_action_counts"] for row in rows], axis=0).tolist(),
                 "elapsed_wall_s": time.monotonic()-start, **update}
        curves.append(curve)
        write_json(out / "curves.json", curves)
        append_json(out / "progress.jsonl", {"phase": "optimizer", "seed": seed, "collection": collection+1,
                    "optimizer_updates": optimizer_updates})
    final = parameter_vector(policy)
    torch.save({"seed": seed, "weights": policy.state_dict(), "optimizer": optimizer.state_dict(),
                "training_worlds": worlds, "optimizer_updates": optimizer_updates}, out / "raw" / f"L_{seed}_final.pt")
    if optimizer_updates != 512:
        raise ValueError("optimizer exposure drift")
    progress["fits_completed"] += 1
    progress["training_steps"] += 512 * HORIZON
    progress["optimizer_updates"] += optimizer_updates
    norm = float(torch.linalg.vector_norm(final-initial))
    result = {"seed": seed, "episodes": 512, "steps": 512*HORIZON,
              "optimizer_updates": optimizer_updates, "macro_rows": macro_rows,
              "optimizer_row_exposures": row_exposures, "initial_parameter_norm": float(initial.norm()),
              "parameter_change_norm": norm, "relative_parameter_change": norm / max(float(initial.norm()), 1e-30),
              "wall_s": time.monotonic()-start, "cpu_s": time.process_time()-cpu_start,
              "source_construction_wall_s": source_wall, "training_world_ids": list(worlds)}
    return policy, result


def paired_description(values):
    from scipy.stats import t

    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    sd = float(values.std(ddof=1)) if len(values) > 1 else 0.0
    half = float(t.ppf(.975, len(values)-1)) * sd / np.sqrt(len(values)) if len(values) > 1 else 0.0
    return {"n": len(values), "mean": mean, "sd": sd,
            "t95": [mean-half, mean+half], "positive": int(np.count_nonzero(values > 0)),
            "negative": int(np.count_nonzero(values < 0)), "zero": int(np.count_nonzero(values == 0))}


def summarize_evaluation(rows):
    arms = ["S", "P", *(f"L_{seed}" for seed in FIT_SEEDS), "S_no_event"]
    keyed = {(row["arm"], row["world"]): row for row in rows}
    if len(keyed) != 384 or any((arm, world) not in keyed for arm in arms for world in EVAL_IDS):
        raise ValueError("evaluation inventory mismatch")
    metrics = ("J", "QoS", "weakest_service_mean", "J_event", "event_deficit_sum",
               "event_catastrophe", "guard_blocked_actions", "reserve_path_length_m", "graph_potential_delta_sum")
    absolute = {arm: {key: paired_description([keyed[arm, world][key] for world in EVAL_IDS])
                      for key in metrics} for arm in arms}
    pairs = [("P", "S"), *((f"L_{seed}", baseline) for seed in FIT_SEEDS for baseline in ("P", "S")),
             *((arm, "S_no_event") for arm in arms if arm != "S_no_event")]
    contrasts = {}
    for left, right in pairs:
        contrasts[f"{left}-{right}"] = {
            key: paired_description([keyed[left, world][key]-keyed[right, world][key] for world in EVAL_IDS])
            for key in metrics}
        contrasts[f"{left}-{right}"]["adverse_worlds"] = [
            {"world": world, "J": keyed[left, world]["J"]-keyed[right, world]["J"],
             "QoS": keyed[left, world]["QoS"]-keyed[right, world]["QoS"]}
            for world in EVAL_IDS if keyed[left, world]["J"] < keyed[right, world]["J"]
            or keyed[left, world]["QoS"] < keyed[right, world]["QoS"]]
    training_units = {
        baseline: {key: paired_description([contrasts[f"L_{seed}-{baseline}"][key]["mean"] for seed in FIT_SEEDS])
                   for key in ("J", "QoS")} for baseline in ("P", "S")}
    return {"absolute": absolute, "contrasts": contrasts,
            "three_training_unit_description": training_units,
            "uncertainty_scope": "world t63 intervals condition on fitted policies; training t2 is small-n descriptive"}


def run_study(out, launch_sha):
    start = time.monotonic()
    cpu_start = time.process_time()
    out = Path(out)
    (out / "raw").mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    worlds = [training_world_ids(seed) for seed in FIT_SEEDS]
    if len(set(world for sequence in worlds for world in sequence)) != 1536:
        raise ValueError("training streams collided")
    config = {"direction": DIRECTION, "launch_sha": launch_sha, "seeds": list(FIT_SEEDS),
              "training_episodes_per_fit": 512, "horizon": HORIZON, "eval_worlds": list(EVAL_IDS),
              "learner_gamma": 1.0, "gae_lambda": .95, "native_pbrs_gamma": .99,
              "optimizer": "Adam", "learning_rate": .0003, "epochs": 4, "minibatches": 4,
              "collections": 32, "episodes_per_collection": 16, "clip": .2, "entropy": .01,
              "value_coefficient": .5, "value_loss": "half_mean_squared_error", "grad_norm_cap": .5,
              "network": "496-128tanh-128tanh;16logits,value", "numeric_threads": 1, "device": "cpu",
              "source_assignment_candidates": 129024000, "P_snapshot_upper": 270336,
              "planned_native_steps": 960000, "planned_complete_episodes": 1920,
              "public_user_xy_payload_bytes_per_episode": 240,
              "runtime": {"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__},
              "primary": "final-only deterministic complete native J/QoS L-P; L-S secondary",
              "metric_columns": list(METRICS)}
    write_json(out / "config.json", config)
    progress = {"state": "running", "launch_sha": launch_sha, "fits_started": 0, "fits_completed": 0,
                "training_steps": 0, "evaluation_steps": 0, "optimizer_updates": 0,
                "service_snapshot_calls": 0, "fit_results": []}
    curves = []
    policies = {}
    rows = []
    try:
        for seed in FIT_SEEDS:
            progress["fits_started"] += 1
            write_json(out / "summary.json", progress)
            policy, result = train_fit(seed, out, progress, curves)
            policies[seed] = policy.eval()
            progress["fit_results"].append(result)
            write_json(out / "summary.json", progress)
        evaluation_source_wall = 0.0
        for world in EVAL_IDS:
            source_start = time.monotonic()
            source = make_episode_source(world)
            evaluation_source_wall += time.monotonic()-source_start
            append_json(out / "raw" / "evaluation_sources.jsonl", source.to_primitive())
            programs = [("S_no_event", "S", None, False), ("S", "S", None, True), ("P", "P", None, True)]
            programs.extend((f"L_{seed}", "L", policies[seed], True) for seed in FIT_SEEDS)
            for name, arm, policy, event in programs:
                row, arrays, _ = run_episode(source, arm=arm, policy=policy, event=event)
                row["arm"] = name
                write_episode(out, f"eval_{name}_{world}", row, arrays)
                rows.append(row)
                progress["evaluation_steps"] += HORIZON
                progress["service_snapshot_calls"] += row["service_snapshot_calls"]
                write_json(out / "perworld.json", rows)
                append_json(out / "progress.jsonl", {"phase": "evaluation", "world": world,
                            "arm": name, "evaluation_steps": progress["evaluation_steps"]})
            write_json(out / "summary.json", progress)
        if progress["training_steps"] != 768000 or progress["evaluation_steps"] != 192000:
            raise ValueError("native exposure mismatch")
        if progress["service_snapshot_calls"] > 270336:
            raise ValueError("ordinary snapshot work exceeded the fixed upper count")
        progress["evaluation"] = summarize_evaluation(rows)
        progress["evaluation_source_construction_wall_s"] = evaluation_source_wall
        progress["state"] = "complete"
    except BaseException as error:
        progress["state"] = "technical_failure"
        progress["error"] = f"{type(error).__name__}: {error}"
        progress["traceback"] = traceback.format_exc()
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        progress["runner_wall_s"] = time.monotonic()-start
        progress["runner_cpu_s"] = time.process_time()-cpu_start
        progress["peak_RSS_KiB"] = int(usage.ru_maxrss)
        progress["resource_scope"] = "one scientific Python worker, one numeric thread; includes children only if separately reported"
        write_json(out / "summary.json", progress)
        artifacts = []
        for path in sorted(out.rglob("*")):
            if path.is_file() and ("raw" in path.relative_to(out).parts or path.name in {"summary.json", "config.json", "curves.json", "perworld.json"}):
                artifacts.append({"path": str(path.relative_to(out)), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
        write_json(out / "artifacts.json", {"launch_sha": launch_sha, "files": artifacts,
                                            "total_bytes": sum(row["bytes"] for row in artifacts)})
    return progress


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--seed", type=int, default=FIT_SEEDS[0])
    args = parser.parse_args()
    if args.seed != FIT_SEEDS[0]:
        parser.error("B01 is the fixed three-fit seed sequence 2026092911..13")
    from scripts.hmasd_admission import require_admission

    admission = require_admission(__file__, direction=DIRECTION)
    if args.launch_sha != admission["sha"]:
        raise ValueError("launch SHA does not match admission")
    run_study(Path(args.out), args.launch_sha)


if __name__ == "__main__":
    main()
