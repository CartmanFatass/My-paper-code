"""Collection, one fixed fit, then the complete P/H/L native panel."""

from __future__ import annotations

import hashlib
import multiprocessing
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from experiments.candidates.energy_relay_availability.b04.runner import (
    PairingObserver, _config, _effective_s2, _rng_state_bytes,
)
from experiments.candidates.energy_relay_availability.b04.transit_hold import (
    H1_CENTRAL_10, TransitHoldController, battery_tail_readings,
)
from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    HeuristicController, evaluate_world,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS

from .controller import MAX_CANDIDATES, WIDTH, ValueTransitController
from .learner import FIT_SEED, FrozenValue, fit
from .readout import ARMS, summarize

DIRECTION = "uav_cooperative_planning"
TAG = "b02_transit_value_a01"
HORIZON = 3000
COLLECTION_SEEDS = tuple(range(29092701, 29092765))
EVALUATION_SEEDS = tuple(range(29102701, 29102733))


class PrefixObserver(PairingObserver):
    """Keep per-step exogenous witnesses so different native lengths can pair."""

    def __init__(self, raw):
        super().__init__(raw)
        self.rng_state_sha256 = []

    @contextmanager
    def attach(self, controller):
        with super().attach(controller):
            self.rng_state_sha256.append(hashlib.sha256(_rng_state_bytes(self.raw)).hexdigest())
            yield

    def on_step(self, *, t, **kwargs):
        super().on_step(t=t, **kwargs)
        self.rng_state_sha256.append(hashlib.sha256(_rng_state_bytes(self.raw)).hexdigest())

    def as_arrays(self):
        return {**super().as_arrays(),
                "rng_state_sha256": np.asarray(self.rng_state_sha256, dtype="S64")}


def jobs_for(stage):
    if stage == "collection":
        return [{"stage": stage, "arm": "collect", "seed": seed,
                 "job_key": f"collect/{seed}"} for seed in COLLECTION_SEEDS]
    if stage == "evaluation":
        return [{"stage": stage, "arm": arm, "seed": seed,
                 "job_key": f"{arm}/{seed}"} for arm in ARMS for seed in EVALUATION_SEEDS]
    raise ValueError(stage)


def _decision_arrays(controller, length, rewards):
    heuristic = controller.heuristic
    records = heuristic.decision_records
    starts = np.asarray([record["step"] for record in records], dtype=np.int32)
    expected = np.arange(0, length, H1_CENTRAL_10.replan_period, dtype=np.int32)
    if not np.array_equal(starts, expected) or len(heuristic.contexts) != len(records):
        raise ValueError("actual replan clock/context alignment changed")
    if any(record["candidate_count"] > MAX_CANDIDATES for record in records):
        raise ValueError("candidate library exceeded nine proposals")
    features = np.stack([item[0] for item in heuristic.contexts])
    mask = np.stack([item[1] for item in heuristic.contexts])
    chosen = np.asarray([item[2] for item in heuristic.contexts], dtype=np.int16)
    suggested = np.asarray([item[3] for item in heuristic.contexts], dtype=np.int16)
    probability = np.asarray([item[4] for item in heuristic.contexts], dtype=np.float32)
    if (features.shape != (len(records), MAX_CANDIDATES, WIDTH)
            or not np.isfinite(features[mask]).all() or
            not np.all(mask[np.arange(len(chosen)), chosen]) or
            np.any(probability <= 0) or np.any(probability > 1)):
        raise ValueError("invalid recorded candidate context")
    lengths = np.diff(np.r_[starts, length]).astype(np.int16)
    if np.any(lengths < 1) or np.any(lengths > 10):
        raise ValueError("invalid actual macro segment length")
    macro = np.asarray([np.sum(rewards[start:start + size], dtype=np.float64)
                        for start, size in zip(starts, lengths)], dtype=np.float64)
    if not np.isclose(np.sum(macro), np.sum(rewards, dtype=np.float64), rtol=1e-12, atol=1e-9):
        raise ValueError("native reward was not partitioned exactly once")
    next_index = np.arange(1, len(records) + 1, dtype=np.int32)
    next_index[-1] = -1
    terminal = np.zeros(len(records), dtype=bool)
    terminal[-1] = True
    return {"planner_step": starts, "features": features, "mask": mask,
            "chosen_index": chosen, "p_suggested_index": suggested,
            "behavior_probability": probability, "macro_reward": macro,
            "macro_length": lengths, "terminal": terminal,
            "next_index": next_index,
            "selected_hold_uav": np.asarray([r["selected_hold_uav"] for r in records], dtype=np.int16),
            "p_suggested_hold_uav": np.asarray([r["p_suggested_hold_uav"] for r in records], dtype=np.int16),
            "candidate_count": np.asarray([r["candidate_count"] for r in records], dtype=np.int8),
            "fallback": np.asarray([r["fallback"] or "" for r in records], dtype="U40"),
            "h1_targets_xy": np.asarray([r["h1_targets_xy"] for r in records], dtype=np.float64)}


def _simulate(job, out: Path, checkpoint: Path | None):
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    env = observer = controller = None
    raw_path = out / "raw" / f'{job["arm"]}_{job["seed"]}.npz'
    try:
        import torch

        torch.set_num_threads(1)
        if torch.get_default_dtype() != torch.float32:
            raise RuntimeError("B02 requires CPU float32 Torch")
        config = _config()
        env = make_env(config, int(job["seed"]))
        raw = env.env
        if (raw.energy_stage != "S2" or raw.routing_protocol != "widest_path"
                or bool(raw.failure_enabled) or env.observation_space.shape != (8, 365)
                or raw.n_ground_bs != 1 or raw.n_charging_stations != 2):
            raise ValueError("effective native S7-S2 environment changed")
        if job["arm"] == "collect":
            rng = np.random.default_rng(np.random.SeedSequence([int(job["seed"]), 290927]))
            controller = ValueTransitController(env, policy="collect", rng=rng)
        elif job["arm"] == "P":
            controller = ValueTransitController(env, policy="P")
        elif job["arm"] == "L":
            if checkpoint is None:
                raise ValueError("L requires the fixed final fit")
            controller = ValueTransitController(env, policy="L", model=FrozenValue(checkpoint))
        elif job["arm"] == "H":
            controller = HeuristicController(H1_CENTRAL_10, env=env)
        else:
            raise ValueError("unknown B02 arm")
        observer = PrefixObserver(raw)
        row, steps = evaluate_world(controller, env, config, int(job["seed"]),
                                    PRODUCTION_PARAMS, observer=observer)
        length = int(row["actual_length"])
        if (length < 1 or length > HORIZON or len(steps["reward"]) != length
                or len(observer.user_xy) != length + 1
                or len(observer.rng_state_sha256) != length + 1):
            raise ValueError("native reward, trace and length mismatch")
        decision_arrays = {}
        if job["arm"] != "H":
            decision_arrays = _decision_arrays(controller, length, steps["reward"])
            records = controller.heuristic.decision_records
            row.update(selected_hold_windows=sum(r["selected_hold_uav"] >= 0 for r in records),
                       planner_windows=len(records),
                       planner_active_windows=sum(r["fallback"] is None for r in records),
                       service_snapshot_calls=controller.heuristic.service_snapshot_calls,
                       candidate_plan_evaluations=sum(r["candidate_count"] for r in records
                                                      if r["fallback"] is None),
                       inference_candidate_count=controller.heuristic.inference_candidate_count)
        else:
            row.update(selected_hold_windows=0, planner_windows=0,
                       planner_active_windows=0, service_snapshot_calls=0,
                       candidate_plan_evaluations=0, inference_candidate_count=0)
        row.update(battery_tail_readings(steps["battery"],
                                         reserve_ratio=float(raw.return_reserve_ratio),
                                         service_cutoff_ratio=float(raw.service_cutoff_threshold)))
        row["qos_sum_over_3000"] = float(row["cumulative_qos"] / HORIZON)
        row.update(observer.digests())
        row.update(job)
        if raw_path.exists():
            raise FileExistsError(raw_path)
        np.savez_compressed(raw_path, **steps, **observer.as_arrays(), **decision_arrays,
                            metric_fields=np.asarray(TRACE_FIELDS))
        row.update(status="completed", raw_path=str(raw_path.relative_to(out)),
                   raw_sha256=_sha256(raw_path), raw_bytes=raw_path.stat().st_size,
                   worker_wall_seconds=time.monotonic() - started,
                   worker_cpu_seconds=_cpu_seconds() - cpu_started,
                   worker_peak_rss_kib=_rss_kib())
        return row
    except BaseException as error:
        partial = {}
        if raw_path.exists():
            partial = {"incomplete_raw_path": str(raw_path.relative_to(out)),
                       "incomplete_raw_sha256": _sha256(raw_path),
                       "incomplete_raw_bytes": raw_path.stat().st_size}
        elif observer is not None and observer.user_xy:
            partial_path = raw_path.with_name(raw_path.stem + "_partial.npz")
            try:
                np.savez_compressed(partial_path, **observer.as_arrays())
                partial = {"partial_path": str(partial_path.relative_to(out)),
                           "partial_sha256": _sha256(partial_path),
                           "partial_bytes": partial_path.stat().st_size,
                           "partial_observed_steps": len(observer.user_xy) - 1}
            except BaseException as preserve_error:
                partial = {"partial_preservation_error": repr(preserve_error)}
        return {**job, **partial, "status": "failed", "error_type": type(error).__name__,
                "error": str(error), "traceback": traceback.format_exc(),
                "worker_wall_seconds": time.monotonic() - started,
                "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                "worker_peak_rss_kib": _rss_kib()}
    finally:
        if env is not None:
            try:
                env.close()
            except BaseException:
                pass


def _worker(payload):
    job, out_string, checkpoint_string = payload
    if job not in jobs_for(job["stage"]):
        return {**job, "status": "failed", "error_type": "ValueError",
                "error": "world outside fixed B02 plan"}
    return _simulate(job, Path(out_string), Path(checkpoint_string) if checkpoint_string else None)


def _pairing(rows, out):
    by_key = {row["job_key"]: row for row in rows}
    result = []
    for seed in EVALUATION_SEEDS:
        paths = []
        for arm in ARMS:
            row = by_key[f"{arm}/{seed}"]
            if row["status"] != "completed":
                return {"valid": False, "error": "incomplete evaluation world"}
            paths.append(out / row["raw_path"])
        with np.load(paths[0], allow_pickle=False) as p, np.load(paths[1], allow_pickle=False) as h, np.load(paths[2], allow_pickle=False) as l:
            initial = len({by_key[f"{arm}/{seed}"]["initial_state_sha256"] for arm in ARMS}) == 1
            comparisons = {}
            for reference, archive in (("P", p), ("H", h)):
                common = min(len(l["rng_state_sha256"]), len(archive["rng_state_sha256"]))
                comparisons[f"L_vs_{reference}"] = {
                    "common_observed_steps": common - 1,
                    "user_prefix_equal": bool(np.array_equal(
                        l["user_xy_m"][:common], archive["user_xy_m"][:common])),
                    "rng_prefix_equal": bool(np.array_equal(
                        l["rng_state_sha256"][:common], archive["rng_state_sha256"][:common])),
                }
            result.append({"seed": seed, "initial_equal": initial,
                           "comparisons": comparisons,
                           "actual_lengths": {arm: by_key[f"{arm}/{seed}"]["actual_length"]
                                              for arm in ARMS}})
    return {"valid": all(item["initial_equal"] and all(
                pair["user_prefix_equal"] and pair["rng_prefix_equal"]
                for pair in item["comparisons"].values()) for item in result),
            "worlds": result}


def run(out: Path, launch_sha: str, *, workers: int = 2, threads: int = 1):
    if workers != 2 or threads != 1:
        raise ValueError("B02 fixes two serial-world workers and one numeric thread each")
    out = Path(out)
    if out.parts[-3:] != ("runs", DIRECTION, TAG):
        raise ValueError("B02 output must use the canonical direction/tag run path")
    if any((out / name).exists() for name in
           ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError("B02 scientific artifacts already exist")
    started = time.monotonic()
    cpu_started = _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    rows = []
    fit_reading = None
    fit_progress_reading = {}
    fits_started = 0
    fit_resources = None
    pairing = None
    stage = "collection"
    runner_error = None
    pool_errors = []
    submitted = []
    checkpoint = out / "raw" / "final_value.pt"
    _write_json(out / "perworld.json", rows)
    _write_json(out / "summary.json", summarize(rows, COLLECTION_SEEDS, EVALUATION_SEEDS))

    def publish():
        _write_json(out / "perworld.json", rows)
        summary = summarize(rows, COLLECTION_SEEDS, EVALUATION_SEEDS, fit_reading, pairing)
        returned = {row["job_key"]: row for row in rows}
        resource_fields = ("worker_cpu_seconds", "worker_wall_seconds", "worker_peak_rss_kib")
        resource_gaps = {
            key: [field for field in resource_fields
                  if returned.get(key, {}).get(field) is None]
            for key in submitted
            if any(returned.get(key, {}).get(field) is None for field in resource_fields)
        }
        work_count_gaps = [key for key in submitted
                           if returned.get(key, {}).get("status") != "completed"]
        measured_cpu = sum(row["worker_cpu_seconds"] for row in rows
                           if row.get("worker_cpu_seconds") is not None)
        measured_wall = sum(row["worker_wall_seconds"] for row in rows
                            if row.get("worker_wall_seconds") is not None)
        summary.update(launch_sha=launch_sha, stage=stage, submitted_jobs=submitted,
                       planned_fits=1, fits_started=fits_started,
                       fits_completed=int(fit_reading is not None),
                       fit_resources=fit_resources,
                       fit_progress_recorded_lower_bound=(fit_progress_reading if fit_reading is None
                                                          else None),
                       optimizer_updates=(fit_reading["updates"] if fit_reading else
                                          (0 if fits_started == 0 else None)),
                       optimizer_updates_recorded_lower_bound=(
                           fit_reading["updates"] if fit_reading else
                           fit_progress_reading.get("updates", 0)),
                       fixed_policy_evaluation_optimizer_updates=0,
                       completed_evaluation_worlds=sum(
                           row.get("arm") in ARMS and row.get("status") == "completed"
                           for row in rows),
                       raw_recorded_bytes=sum(row.get("raw_bytes", 0) +
                                              row.get("partial_bytes", 0) +
                                              row.get("incomplete_raw_bytes", 0) for row in rows)
                           + (checkpoint.stat().st_size if checkpoint.exists() else 0),
                       parent_wall_seconds=time.monotonic() - started,
                       parent_cpu_seconds=_cpu_seconds() - cpu_started,
                       parent_peak_rss_kib=_rss_kib(),
                       worker_cpu_seconds_measured_subtotal=measured_cpu,
                       worker_wall_seconds_measured_subtotal=measured_wall,
                       worker_cpu_seconds_sum=(None if any("worker_cpu_seconds" in fields
                           for fields in resource_gaps.values()) else measured_cpu),
                       worker_wall_seconds_sum=(None if any("worker_wall_seconds" in fields
                           for fields in resource_gaps.values()) else measured_wall),
                       worker_peak_rss_kib_max_recorded=max((row["worker_peak_rss_kib"]
                           for row in rows if row.get("worker_peak_rss_kib") is not None), default=None),
                       resources_unmeasured=bool(resource_gaps),
                       missing_or_pending_worker_resource_fields=resource_gaps,
                       native_work_count_scope="returned completed worlds; lower bound if jobs are missing",
                       missing_or_failed_work_count_jobs=work_count_gaps,
                       completed_native_steps=sum(row.get("actual_length", 0) for row in rows
                                                  if row.get("status") == "completed"),
                       partial_observed_steps=sum(row.get("partial_observed_steps", 0)
                                                  for row in rows),
                       completed_macro_transitions=sum(row.get("planner_windows", 0)
                                                       for row in rows if row.get("arm") == "collect"
                                                       and row.get("status") == "completed"),
                       scorer_snapshots=sum(row.get("service_snapshot_calls", 0) for row in rows),
                       candidate_plan_evaluations=sum(row.get("candidate_plan_evaluations", 0)
                                                      for row in rows),
                       inference_candidate_evaluations=sum(row.get("inference_candidate_count", 0)
                                                           for row in rows))
        for name in ("scorer_snapshots", "candidate_plan_evaluations", "inference_candidate_evaluations"):
            summary[name + "_recorded_lower_bound"] = summary[name]
            if work_count_gaps:
                summary[name] = None
        if runner_error or pool_errors:
            summary["status"] = "incomplete"
            summary["runner_error"] = runner_error
            summary["pool_errors"] = pool_errors
        _write_json(out / "summary.json", summary)
        return summary

    def on_result(row):
        rows.append(row)
        _write_json(out / "progress.json", {"stage": stage, "last_job": row["job_key"],
                                            "last_status": row["status"],
                                            "completed_jobs": sum(r["status"] == "completed" for r in rows)})
        publish()

    try:
        config = _config()
        effective = _effective_s2(config, COLLECTION_SEEDS[0])
        if (effective["energy_stage"] != "S2" or effective["n_uavs"] != 8
                or effective["n_users"] != 30 or effective["n_ground_bs"] != 1
                or effective["n_charging_stations"] != 2
                or effective["routing_protocol"] != "widest_path"
                or effective["max_steps"] != HORIZON or effective["failure_enabled"]):
            raise ValueError("effective B02 S7-S2 configuration differs")
        _write_json(out / "config.json", {
            "direction": DIRECTION, "tag": TAG, "launch_sha": launch_sha,
            "horizon_maximum": HORIZON, "collection_seeds": COLLECTION_SEEDS,
            "evaluation_seeds": EVALUATION_SEEDS, "fit_seed": FIT_SEED,
            "workers": workers, "numeric_threads_per_worker": threads,
            "device": "cpu", "dtype": "float32", "effective_raw": effective,
            "feature_width": WIDTH, "candidate_capacity": MAX_CANDIDATES,
            "feature_order": ("time; own xyz; six own battery/availability/charging/returning/"
                              "dock/margin fields; station xy; user xy; BS xy; H1 target xy/valid; "
                              "shield modes; hold one-hot; candidate target xy; nominal xyz at 5/10; "
                              "q0/q5/q10/integrated; missing-score bit"),
            "feature_normalization": "population mean/std of all valid collection candidate rows; "
                                     "constant dimensions use scale one; fixed coordinate scaling first",
            "learner": {"architecture": [248, 128, 64, 1], "hidden_activation": "ReLU",
                        "final_layer_initialization": "zero", "optimizer": "Adam",
                        "learning_rate": 0.001, "weight_decay": 0,
                        "batch_size": 256, "updates": 5000, "gradient_norm_cap": 1,
                        "target_copy_interval": 100, "discount_per_macro": 0.97,
                        "sampling": "with replacement, default_rng(29092791)",
                        "initialization_seed": FIT_SEED},
            "behavior": "0.5 P plus 0.5 uniform legal; independent SeedSequence([world_seed,290927])",
            "target": "actual native segment reward / 10 + 0.97 nonterminal max legal next Q",
            "evaluation_arms": ARMS,
        })
        for stage_name in ("collection", "evaluation"):
            stage = stage_name
            jobs = jobs_for(stage_name)
            with ProcessPoolExecutor(max_workers=workers,
                                     mp_context=multiprocessing.get_context("spawn")) as pool:
                _, errors = execute_bounded(
                    pool, jobs, workers,
                    lambda job: (job, str(out), str(checkpoint) if stage_name == "evaluation" else None),
                    on_result, submitted, worker_fn=_worker)
                pool_errors.extend(errors)
            if errors or any(row.get("status") != "completed" for row in rows):
                break
            if stage_name == "collection":
                stage = "fit"
                collection_rows = {row["seed"]: row for row in rows}
                paths = [out / collection_rows[seed]["raw_path"] for seed in COLLECTION_SEEDS]
                fit_started = time.monotonic()
                fit_cpu_started = _cpu_seconds()
                fits_started += 1
                fit_resources = {"status": "running", "wall_seconds": None,
                                 "cpu_seconds": None}
                fit_progress_reading.update(updates=0, target_copies=0)
                _write_json(out / "progress.json", {"stage": "fit", "fits_started": fits_started,
                                                    "updates_recorded_lower_bound": 0})
                publish()

                def fit_progress(reading):
                    fit_progress_reading.update(reading)
                    fit_resources.update(
                        elapsed_wall_seconds_recorded_lower_bound=time.monotonic() - fit_started,
                        cpu_seconds_recorded_lower_bound=_cpu_seconds() - fit_cpu_started)
                    _write_json(out / "progress.json", {"stage": "fit", **reading})
                    publish()
                try:
                    fit_reading = fit(paths, checkpoint, fit_progress)
                finally:
                    fit_resources.update(
                        status="completed" if fit_reading is not None else "did_not_complete",
                        wall_seconds=time.monotonic() - fit_started,
                        cpu_seconds=_cpu_seconds() - fit_cpu_started,
                        parent_peak_rss_kib_cumulative=_rss_kib())
                publish()
        if stage == "evaluation" and len([r for r in rows if r.get("arm") in ARMS]) == 96 and all(
                row.get("status") == "completed" for row in rows):
            pairing = _pairing(rows, out)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    stage = "finished" if pairing and pairing.get("valid") else stage
    summary = publish()
    orphan = orphan_raw_files(out, rows)
    if orphan:
        summary["orphan_raw"] = orphan
        summary["status"] = "incomplete"
        _write_json(out / "summary.json", summary)
    artifacts = {}
    for name in ("config.json", "perworld.json", "summary.json", "progress.json"):
        path = out / name
        if path.exists():
            artifacts[name] = {"sha256": _sha256(path), "bytes": path.stat().st_size}
    for row in rows:
        for name in ("raw", "partial", "incomplete_raw"):
            rel = row.get(f"{name}_path")
            if rel:
                artifacts[rel] = {"sha256": row[f"{name}_sha256"],
                                  "bytes": row[f"{name}_bytes"]}
    if checkpoint.exists():
        artifacts[str(checkpoint.relative_to(out))] = {"sha256": _sha256(checkpoint),
                                                        "bytes": checkpoint.stat().st_size}
    for path in sorted((out / "raw").iterdir()):
        if path.is_file() and str(path.relative_to(out)) not in artifacts:
            artifacts[str(path.relative_to(out))] = {"sha256": _sha256(path),
                                                      "bytes": path.stat().st_size,
                                                      "status": "unreconciled"}
            summary["status"] = "incomplete"
    if summary["status"] == "incomplete":
        _write_json(out / "summary.json", summary)
        artifacts["summary.json"] = {"sha256": _sha256(out / "summary.json"),
                                     "bytes": (out / "summary.json").stat().st_size}
    _write_json(out / "manifest.json", {"launch_sha": launch_sha, "artifacts": artifacts,
                                         "recorded_artifact_bytes_excluding_manifest": sum(
                                             item["bytes"] for item in artifacts.values()),
                                         "orphan_raw": orphan})
    return summary
