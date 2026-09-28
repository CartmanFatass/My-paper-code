"""The fixed one-fit, four-reference B01 batch; no retry or endpoint selection."""

from __future__ import annotations

import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import time
import traceback

import numpy as np

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_availability.b04.runner import _effective_s2
from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldController
from experiments.candidates.energy_relay_benchmark.b01.evaluation import evaluate_world, make_eval_config
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_active_sensing.training import fingerprint, optimizer_steps
from experiments.candidates.uav_radio_placement.b01.placement import PlacementController
from experiments.candidates.uav_radio_placement.b01.runner import PlacementObserver, _plain
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

from .constants import (DIRECTION, HORIZON, CLOCK, POLICY_SEED, TRAIN_SEEDS, EVAL_SEEDS,
                        OPTIMIZER_STEPS, MAX_RADIO_QUERIES, MAX_PREDICTION_TEAM_TICKS, evaluation_plan)
from .controllers import TransitionController, FEATURE_DIM
from .records import save_world, controller_records
from .readout import summarize
from .training import PPO_PARAMS, train


def _work(controller, arm):
    if controller is None:
        return {}
    if arm in ("L", "O"):
        return controller.work_counts()
    if arm == "R":
        return {"service_snapshot_calls": controller.snapshot_calls_started,
                "service_snapshot_calls_completed": controller.snapshot_calls_completed}
    return {"service_snapshot_calls": controller.heuristic.service_snapshot_calls}


def simulate_world(job, out, threads=1, config=None):
    import torch
    from stable_baselines3 import PPO

    out = Path(out)
    started, cpu_started = time.monotonic(), _cpu_seconds()
    env = model_env = controller = observer = None
    raw_path = out / "raw" / f"{job['arm']}_{job['seed']}.npz"
    try:
        torch.set_num_threads(threads)
        config = make_eval_config(HORIZON, POLICY_SEED) if config is None else config
        env = make_env(config, job["seed"])
        model_env = make_env(config, 0)
        model_env.reset(seed=0)
        raw = env.env
        if (raw.energy_stage != "S2" or raw.routing_protocol != "widest_path"
                or raw.failure_enabled or env.observation_space.shape != (8, 365)):
            raise ValueError("native host differs from fixed S7-S2")
        policy, audit = None, []
        if job["arm"] == "L":
            policy = PPO.load(out / "endpoint.zip", device="cpu")
            before, updates_before = fingerprint(policy.policy), optimizer_steps(policy.policy)

            def choose(features):
                with torch.no_grad():
                    tensor = torch.as_tensor(features[None], dtype=torch.float32)
                    distribution = policy.policy.get_distribution(tensor)
                    action = distribution.get_actions(deterministic=True)
                    stats = {key: value[0].cpu().numpy() for key, value in distribution.statistics().items()}
                    audit.append({**_plain(stats), "argmax_modes": action[0].cpu().numpy().tolist(),
                                  "argmax_log_probability": float(distribution.log_prob(action)[0])})
                    return action[0].cpu().numpy()

            controller = TransitionController("L", env, model_env, chooser=choose)
        elif job["arm"] == "O":
            controller = TransitionController("O", env, model_env)
        elif job["arm"] == "R":
            controller = PlacementController("R", env, model_env)
        elif job["arm"] == "P":
            controller = TransitHoldController(env)
        else:
            raise ValueError("arm outside fixed panel")
        observer = PlacementObserver(raw)
        row, steps = evaluate_world(controller, env, config, job["seed"], PRODUCTION_PARAMS, observer=observer)
        if len(observer.user_xy) != row["actual_length"] + 1:
            raise RuntimeError("incomplete exogenous trajectory")
        if policy is not None:
            if fingerprint(policy.policy) != before or optimizer_steps(policy.policy) != updates_before:
                raise RuntimeError("evaluation changed policy or optimizer")
            if updates_before != OPTIMIZER_STEPS or len(audit) != len(controller.decision_records):
                raise RuntimeError("wrong endpoint or number of evaluation choices")
            for record, stats in zip(controller.decision_records, audit):
                record["policy"] = stats
            row.update(policy_fingerprint=before, evaluation_optimizer_updates=0)
        row = save_world(raw_path, row, steps, observer, controller, job["arm"])
        if row["actual_length"] != int(config.max_steps):
            raise RuntimeError("native early end retained; fixed horizon incomplete")
        work = _work(controller, job["arm"])
        if "service_snapshot_calls_completed" in work and work["service_snapshot_calls"] != work["service_snapshot_calls_completed"]:
            raise RuntimeError("successful invocation accounting mismatch")
        return {**row, **job, "status": "completed", "raw_path": str(raw_path.relative_to(out)),
                "worker_wall_seconds": time.monotonic()-started,
                "worker_cpu_seconds": _cpu_seconds()-cpu_started, "worker_peak_rss_kib": _rss_kib()}
    except BaseException as error:
        partial = {}
        if observer is not None and observer.physical_xyz and not raw_path.exists():
            try:
                path = raw_path.with_name(raw_path.stem + "_partial.npz")
                if path.exists():
                    raise FileExistsError(path)
                np.savez_compressed(path, **observer.as_arrays(), planner_records_json=np.asarray(json.dumps(
                    _plain(controller_records(controller, job["arm"]) if controller else []))))
                partial = {"partial_path": str(path.relative_to(out)), "partial_sha256": _sha256(path),
                           "partial_bytes": path.stat().st_size,
                           "partial_observed_steps": max(0, len(observer.user_xy)-1)}
            except BaseException as preserve_error:
                partial = {"partial_preservation_error": repr(preserve_error)}
        elif raw_path.exists():
            partial = {"incomplete_raw_path": str(raw_path.relative_to(out)),
                       "incomplete_raw_sha256": _sha256(raw_path), "incomplete_raw_bytes": raw_path.stat().st_size,
                       "partial_observed_steps": max(0, len(observer.user_xy)-1) if observer else 0}
        return {**job, **partial, **_work(controller, job["arm"]), "status": "failed",
                "error_type": type(error).__name__, "error": str(error), "traceback": traceback.format_exc(),
                "worker_wall_seconds": time.monotonic()-started,
                "worker_cpu_seconds": _cpu_seconds()-cpu_started, "worker_peak_rss_kib": _rss_kib()}
    finally:
        for instance in (env, model_env):
            if instance is not None:
                instance.close()


def _worker(payload):
    job, out, threads = payload
    if job not in evaluation_plan():
        return {**job, "status": "failed", "error": "job outside fixed panel"}
    return simulate_world(job, out, threads)


def run(out, launch_sha, workers=2, threads=1):
    if workers != 2 or threads != 1:
        raise ValueError("B01 requires two workers, one numeric thread each")
    out = Path(out)
    if any((out/name).exists() for name in ("config.json", "training.json", "perworld.json", "summary.json", "raw")):
        raise FileExistsError(f"scientific outputs already exist: {out}")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    jobs = evaluation_plan()
    expected = [job["job_key"] for job in jobs]
    config = make_eval_config(HORIZON, POLICY_SEED)
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": "B01", "launch_sha": launch_sha, "horizon": HORIZON,
        "train_seeds": TRAIN_SEEDS, "eval_seeds": EVAL_SEEDS, "jobs": jobs,
        "policy_seed": POLICY_SEED, "workers": workers, "threads_per_worker": threads,
        "fits": 1, "planned_native_steps": 288000, "optimizer_steps": OPTIMIZER_STEPS,
        "ppo": PPO_PARAMS, "clock": CLOCK, "feature_dim": FEATURE_DIM, "modes": ["D", "W", "B+", "B-"],
        "path": {"first_phase_steps": 15, "detour_offset_m": 150, "xy_cap_mps": 30, "z_cap_mps": 5},
        "ordinary": {"coordinate_sweeps": 2, "pair_modes": [0, 1], "candidate_bound": 161,
                     "samples": [10, 20, 30], "score_tolerance": 1e-8, "travel_tolerance_m": 1e-6},
        "max_radio_queries": MAX_RADIO_QUERIES, "max_prediction_team_ticks": MAX_PREDICTION_TEAM_TICKS,
        "information": "same current legal own/station records and central user/BS coordinates at clock30",
        "model": "joint nominal F/limp/dock/energy/queue projection; no intermediate guard/radio/users; independent static radio model",
        "references": {"R": "unchanged full R@30", "P": "exact central TransitHold P@10, not P_BS"},
        "initialization": "zero action weights; eligible probabilities .8,1/15,1/15,1/15; forced D otherwise",
        "shield": {"enter_margin": 0.0, "exit_margin": 0.05}, "effective_native": _effective_s2(config, TRAIN_SEEDS[0]),
        "pairing": "initial state, full users and native RNG digests; no evaluation updates",
    })
    rows, submitted, pool_errors, runner_error = [], [], [], None
    training = train(out)

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        partial_summary = summarize(rows, EVAL_SEEDS, expected)
        partial_summary.update(training_status=training["status"], launch_sha=launch_sha)
        _write_json(out / "summary.json", partial_summary)

    _write_json(out / "perworld.json", [])
    _write_json(out / "summary.json", summarize([], EVAL_SEEDS, expected))
    if training["status"] == "complete":
        try:
            with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as executor:
                _, pool_errors = execute_bounded(executor, jobs, workers,
                    lambda job: (job, str(out), threads), on_result, submitted, worker_fn=_worker)
        except BaseException as error:
            runner_error = {"error": str(error), "traceback": traceback.format_exc()}
    summary = summarize(rows, EVAL_SEEDS, expected)
    train_rows = [row for path in sorted((out/"training").glob("lane*.episodes.json"))
                  for row in json.loads(path.read_text())]
    train_rows.sort(key=lambda row: row["seed"])
    _write_json(out / "training_perworld.json", train_rows)
    orphan = orphan_raw_files(out, rows)
    completed = sum(row.get("actual_length", 0) for row in rows if row["status"] == "completed")
    partial = sum(row.get("partial_observed_steps", 0) for row in rows)
    train_steps = training["recorded_native_step_lower_bound"]
    work = {field: training["recorded_controller_work_lower_bound"][field]
            + sum(row.get(field, 0) for row in rows)
            for field in ("service_snapshot_calls", "prediction_team_ticks")}
    summary.update(launch_sha=launch_sha, fits=training["fits_started"], training_status=training["status"],
                   optimizer_updates=training.get("optimizer_steps", training.get("observed_optimizer_steps", 0)),
                   training_native_steps=train_steps, evaluation_completed_native_steps=completed,
                   evaluation_partial_observed_steps=partial, known_native_step_lower_bound=train_steps+completed+partial,
                   submitted_jobs=submitted, unstarted_jobs=[key for key in expected if key not in submitted],
                   orphan_raw=orphan, runner_error=runner_error, pool_errors=pool_errors, **work,
                   parent_wall_seconds=time.monotonic()-started, parent_cpu_seconds=_cpu_seconds()-cpu_started,
                   parent_peak_rss_kib=_rss_kib(),
                   training_lane_cpu_seconds=training["worker_cpu_seconds_sum"],
                   evaluation_worker_cpu_seconds=sum(row.get("worker_cpu_seconds", 0) for row in rows),
                   worker_wall_seconds_sum=training["worker_wall_seconds_sum"]+sum(row.get("worker_wall_seconds", 0) for row in rows))
    summary["total_recorded_cpu_seconds"] = (summary["parent_cpu_seconds"] + summary["training_lane_cpu_seconds"]
                                               + summary["evaluation_worker_cpu_seconds"])
    if (training["status"] != "complete" or orphan or runner_error or pool_errors
            or work["service_snapshot_calls"] > MAX_RADIO_QUERIES
            or work["prediction_team_ticks"] > MAX_PREDICTION_TEAM_TICKS
            or summary["known_native_step_lower_bound"] != 288000):
        summary["status"] = "incomplete"
    summary["cost_scope"] = ("complete recorded native/model counts" if summary["status"] == "complete"
                              else "known lower bounds; abrupt worker loss can leave unmeasured work")
    _write_json(out / "summary.json", summary)
    files = [path for path in out.rglob("*") if path.is_file() and path.name != "manifest.json"
             and path.suffix in (".json", ".jsonl", ".npz", ".zip")]
    _write_json(out / "manifest.json", {"launch_sha": launch_sha,
        "artifacts": {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
                      for path in sorted(files)}})
    return summary
