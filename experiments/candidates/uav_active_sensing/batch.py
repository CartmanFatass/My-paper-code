"""One fit followed by all five programs on the fixed fresh evaluation panel."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict
import faulthandler
import json
import multiprocessing
from pathlib import Path
import time
import traceback

import numpy as np

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, TRACE_TIMING, evaluate_world, make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT
from experiments.candidates.uav_information_value.batch import effective_config
from experiments.candidates.uav_service_auxiliary.b01.native import make_env, seed_everything

from .controllers import FEATURE_DIM, N_ACTIONS, SensingController
from .macro_env import EVAL_SEEDS, HORIZON, N_ENVS, POLICY_SEED, TRAIN_SEEDS
from .readout import ARMS, summarize
from .training import OPTIMIZER_STEPS, PPO_PARAMS, fingerprint, train


DIRECTION = "uav_active_sensing"


def plan():
    return [{"arm": arm, "seed": seed, "job_key": f"{arm}/{seed}"}
            for seed in EVAL_SEEDS for arm in ARMS]


class SensingObserver:
    """Truth is read only after actions for evaluation, with no controller callback."""

    def __init__(self, raw):
        self.raw = raw
        self.visible, self.seen_counts, self.travel, self.scout_travel = [], [], [], []
        self.seen = np.zeros(raw.n_users, dtype=bool)
        self.first_seen = np.full(raw.n_users, -1, dtype=np.int32)

    def _visible(self):
        distance = np.linalg.norm(self.raw.uav_positions[:, None, :] - self.raw.user_positions[None, :, :], axis=2)
        visible = np.zeros(self.raw.n_users, dtype=bool)
        for values in distance:
            order = np.argsort(values, kind="stable")[:self.raw.max_observed_users]
            visible[order[values[order] <= self.raw.observation_radius]] = True
        return visible

    @contextmanager
    def attach(self, controller):
        # evaluate_world has reset the native world before entering this context.
        initial = self._visible()
        self.initial_visible = int(initial.sum())
        self.seen |= initial
        self.first_seen[initial] = 0
        self.previous_positions = self.raw.uav_positions.copy()
        yield

    def on_step(self, *, t, controller, **unused):
        visible = self._visible()
        self.first_seen[visible & ~self.seen] = t + 1
        self.seen |= visible
        self.visible.append(visible)
        self.seen_counts.append(int(self.seen.sum()))
        distance = np.linalg.norm(self.raw.uav_positions - self.previous_positions, axis=1)
        self.travel.append(distance)
        diagnostic = controller.diagnostics[-1]
        scout = diagnostic["scout"] if diagnostic["executed"] else None
        self.scout_travel.append(float(distance[scout]) if scout is not None else 0.0)
        self.previous_positions = self.raw.uav_positions.copy()

    def arrays(self):
        return {"sense_visible_post": np.asarray(self.visible, dtype=bool),
                "sense_seen_count_post": np.asarray(self.seen_counts, dtype=np.int32),
                "sense_actual_travel_m": np.asarray(self.travel, dtype=np.float64),
                "sense_assigned_scout_travel_m": np.asarray(self.scout_travel, dtype=np.float64),
                "sense_first_seen_step": self.first_seen.copy()}

    def reading(self, controller):
        plans = controller.diagnostics
        eligible = sum(row["eligible"] for row in plans)
        return {
            "initial_visible_users": self.initial_visible, "discovered_users": int(self.seen.sum()),
            "newly_discovered_users": int(self.seen.sum()) - self.initial_visible,
            "mean_current_visible_users": float(np.asarray(self.visible).sum(axis=1).mean()),
            "actual_team_travel_m": float(np.asarray(self.travel).sum()),
            "assigned_scout_travel_m": float(np.sum(self.scout_travel)),
            "plan_count": len(plans), "eligible_plans": eligible,
            "requested_scout_plans": sum(row["requested"] > 0 for row in plans),
            "executed_scout_plans": sum(row["executed"] > 0 for row in plans),
            "fallback_plans": sum(row["fallback"] for row in plans),
            "scout_share_of_eligible_plans": sum(row["executed"] > 0 for row in plans) / eligible if eligible else None,
            "mean_canonical_users_at_plan": float(np.mean([row["users"] for row in plans])),
        }


def worker(payload):
    job, out_string, checkpoints = payload
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    raw_path = out / "raw" / f"{stem}.npz"
    progress_path = out / "raw" / f"{stem}.progress.json"
    env, observer = None, None
    completed_steps = 0

    def progress(count):
        nonlocal completed_steps
        completed_steps += count
        if completed_steps % 100 == 0:
            _write_json(progress_path, {**job, "steps": completed_steps, "status": "running"})

    try:
        if job not in plan():
            raise ValueError("worker received an undeclared evaluation world")
        import torch
        from stable_baselines3 import PPO

        faulthandler.enable()
        torch.set_num_threads(1)
        seed_everything(POLICY_SEED, torch.device("cpu"))
        config = make_eval_config(HORIZON, POLICY_SEED)
        env = make_env(config, job["seed"])
        effective = effective_config(env, HORIZON)
        identity = {}
        if job["arm"] in ("L0", "L1"):
            checkpoint = checkpoints[job["arm"]]
            path = out / checkpoint["checkpoint"]
            if _sha256(path) != checkpoint["sha256"]:
                raise ValueError("learned evaluation checkpoint hash differs")
            policy = PPO.load(path, device="cpu")
            identity = {"checkpoint_sha256": checkpoint["sha256"], "policy_fingerprint": fingerprint(policy.policy)}
            if identity["policy_fingerprint"] != checkpoint["fingerprint"]:
                raise ValueError("SB3 restored policy differs from the recorded asset")
            controller = SensingController("L", policy)
        else:
            controller = SensingController(job["arm"])
        observer = SensingObserver(env.env)
        row, steps = evaluate_world(controller, env, config, job["seed"], PRODUCTION_PARAMS,
                                    progress=progress, observer=observer)
        if row["actual_length"] != HORIZON or len(observer.visible) != HORIZON or completed_steps != HORIZON:
            raise RuntimeError("evaluation did not complete the fixed native world")
        if job["arm"] in ("L0", "L1") and fingerprint(policy.policy) != identity["policy_fingerprint"]:
            raise RuntimeError("evaluation changed a saved PPO policy")
        if raw_path.exists():
            raise FileExistsError(raw_path)
        diagnostic_arrays = {
            f"plan_{key}": np.asarray([-1 if row[key] is None else row[key] for row in controller.diagnostics])
            for key in controller.diagnostics[0]
        }
        np.savez_compressed(raw_path, **steps, **observer.arrays(), **diagnostic_arrays,
                            metric_fields=np.asarray(TRACE_FIELDS))
        _write_json(progress_path, {**job, "steps": completed_steps, "status": "completed"})
        row.update(job, status="completed", effective_config=effective, **identity, **observer.reading(controller),
                   reserve10_uav_step_fraction=float(np.mean(steps["battery"] < .10)),
                   raw_path=str(raw_path.relative_to(out)), raw_sha256=_sha256(raw_path),
                   raw_bytes=raw_path.stat().st_size)
    except BaseException as error:
        row = {**job, "status": "failed", "error_type": type(error).__name__, "error": str(error),
               "traceback": traceback.format_exc(), "partial_observed_steps": completed_steps}
        _write_json(progress_path, {**job, "steps": completed_steps, "status": "failed"})
        if raw_path.exists():
            row.update(incomplete_raw_path=str(raw_path.relative_to(out)), incomplete_raw_sha256=_sha256(raw_path))
        elif observer is not None and observer.visible:
            partial = out / "raw" / f"{stem}.partial.npz"
            np.savez_compressed(partial, **observer.arrays())
            row.update(partial_path=str(partial.relative_to(out)), partial_sha256=_sha256(partial))
    finally:
        if env is not None:
            env.close()
    return row | {"worker_wall_seconds": time.monotonic() - started,
                  "worker_cpu_seconds": _cpu_seconds() - cpu_started, "worker_peak_rss_kib": _rss_kib()}


def run(out, launch_sha, workers=4):
    out = Path(out)
    if workers not in range(1, 5):
        raise ValueError("evaluation requires one to four single-thread workers")
    if any((out / name).exists() for name in ("config.json", "training", "raw", "summary.json")):
        raise FileExistsError(f"scientific artifacts already exist: {out}")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    jobs = plan()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": "b01_native_j_a01", "launch_sha": launch_sha,
        "fits": 1, "policy_seed": POLICY_SEED, "training_seeds": TRAIN_SEEDS, "jobs": jobs,
        "horizon": HORIZON, "macro_steps": 30, "max_native_transitions": 720000,
        "ppo": PPO_PARAMS, "network": {"pi": [128, 128], "vf": [128, 128], "activation": "tanh"},
        "feature_dim": FEATURE_DIM, "actions": N_ACTIONS, "train_envs": N_ENVS,
        "evaluation_workers": workers, "numeric_threads": 1, "optimizer_steps": OPTIMIZER_STEPS,
        "finite_horizon": "native H3000 is terminated, never TimeLimit.truncated bootstrap",
        "shield": asdict(PRODUCTION_PARAMS), "h1": variant("H1", information="local").record(),
        "layout": S7S2_LAYOUT.record(), "trace_timing": TRACE_TIMING,
        "evaluation_mode": "deterministic categorical argmax for L0/L1; fixed H/P/A",
        "information": "actor and critic only legal pooled observations, ordinary BS/survey memory and public geometry/time",
        "observer": "ground-truth IDs/positions evaluated post-action only; never passed to controller",
    })
    rows, submitted, pool_errors = [], [], []
    _write_json(out / "perworld.json", rows)
    _write_json(out / "summary.json", summarize(rows, jobs))
    fit = train(out)
    runner_error = None
    if fit["status"] == "complete":
        checkpoints = {arm: fit[arm] | {"fingerprint": fit[f"{name}_fingerprint"]}
                       for arm, name in (("L0", "initial"), ("L1", "endpoint"))}
        expected_keys = [job["job_key"] for job in jobs]

        def on_result(row):
            rows.append(row)
            rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
            _write_json(out / "perworld.json", rows)
            _write_json(out / "summary.json", summarize(rows, jobs))

        try:
            with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as executor:
                _, pool_errors = execute_bounded(executor, jobs, workers,
                                                 lambda job: (job, str(out), checkpoints),
                                                 on_result, submitted, worker_fn=worker)
        except BaseException as error:
            runner_error = {"error_type": type(error).__name__, "error": str(error), "traceback": traceback.format_exc()}
    summary = summarize(rows, jobs)
    orphans = orphan_raw_files(out, rows)
    if fit["status"] != "complete" or runner_error or pool_errors or orphans:
        summary.update(status="incomplete", contrasts={})
    progress = [json.loads(path.read_text()) for path in sorted((out / "raw").glob("*.progress.json"))]
    completed = {row["job_key"]: row["actual_length"] for row in rows if row["status"] == "completed"}
    evaluation_lower_bound = sum(completed.values()) + sum(row["steps"] for row in progress if row["job_key"] not in completed)
    summary.update(
        launch_sha=launch_sha, fits_started=fit["fits_started"], training_status=fit["status"],
        optimizer_steps=fit.get("optimizer_steps"), submitted_jobs=submitted,
        unstarted_jobs=[job["job_key"] for job in jobs if job["job_key"] not in submitted],
        training_native_step_lower_bound=fit["recorded_native_step_lower_bound"],
        evaluation_native_step_lower_bound=evaluation_lower_bound,
        actual_native_steps=720000 if summary["status"] == "complete" else None,
        known_native_step_lower_bound=fit["recorded_native_step_lower_bound"] + evaluation_lower_bound,
        runner_error=runner_error, pool_errors=pool_errors, orphan_raw=orphans,
        parent_wall_seconds=time.monotonic() - started, parent_cpu_seconds=_cpu_seconds() - cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        evaluation_worker_cpu_seconds_sum=sum(row["worker_cpu_seconds"] for row in rows if "worker_cpu_seconds" in row),
        evaluation_worker_wall_seconds_sum=sum(row["worker_wall_seconds"] for row in rows if "worker_wall_seconds" in row),
    )
    _write_json(out / "summary.json", summary)
    paths = [out / name for name in ("config.json", "training.json", "perworld.json", "summary.json", "initial.zip", "endpoint.zip")]
    paths += list((out / "raw").glob("*")) + list((out / "training").glob("*"))
    artifacts = {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
                 for path in sorted(paths) if path.is_file()}
    _write_json(out / "manifest.json", {"launch_sha": launch_sha, "artifacts": artifacts,
                                        "storage_bytes": sum(row["bytes"] for row in artifacts.values())})
    return summary
