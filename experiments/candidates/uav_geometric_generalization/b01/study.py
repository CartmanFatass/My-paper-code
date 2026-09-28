"""One pre-fixed coordinate frame per episode, with native policy/evaluator semantics."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from dataclasses import asdict, replace
import faulthandler
import json
import multiprocessing
from pathlib import Path
import tempfile
import time
import traceback

import numpy as np
import torch
from scipy.stats import t as student_t

from experiments.candidates.energy_relay_availability.runner import (
    _cpu_seconds, _rss_kib, _sha256, _write_json, execute_bounded, orphan_raw_files,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    HeuristicController, L_CONTROLLER_INFORMATION, PolicyController, QOS,
    REFERENCE_INFORMATION, SAMPLE_SEED_RULE, TRACE_FIELDS, TRACE_TIMING, WorldTask, aggregate, evaluate_world,
    learner_eval_config, load_learner_policy, make_eval_config, sample_seed,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import variant
from experiments.candidates.energy_relay_benchmark.b01.observation import own_positions
from experiments.candidates.energy_relay_benchmark.b02.checkpoint_eval import read_record
from experiments.candidates.uav_service_auxiliary.b01.native import (
    initialization_fingerprint, make_env, optimizer_steps,
)
from experiments.candidates.uav_service_auxiliary.b06.native import (
    _normalizer_snapshot, _same_snapshot,
)

from .symmetry import D4, inverse_actions, transform_observations, transform_state

DIRECTION = "uav_geometric_generalization"
HORIZON = 3000
WORLDS = tuple(range(280928401, 280928417))
PROGRAMS = ("P_deterministic", "P_stochastic", "C_deterministic", "C_stochastic", "H_central10")
POLICY_SEED = 925031
CHECKPOINT_SHA256 = "41aa4ff0be5d55f924d8388af055fb087d76c1f517497e69c26d7962ce041bb3"
POLICY_FINGERPRINT = "a7c54b470441b8e742459e47a533a41c58534c36288ece0e9eb026a3b544c39c"
WORKERS = 2
THREADS = 1


def plan():
    return [{"program": program, "seed": seed, "job_key": f"{program}/{seed}"}
            for seed in WORLDS for program in PROGRAMS]


def northeast_frame(observations):
    xy = np.asarray(observations)[:, :2].mean(axis=0)
    if xy[0] < .5 and xy[1] < .5:
        return D4.ROT180
    if xy[0] < .5:
        return D4.MIRROR_X
    if xy[1] < .5:
        return D4.MIRROR_Y
    return D4.IDENTITY


class CanonicalController(PolicyController):
    def __init__(self, evaluator, *, canonical, deterministic=True, sample_seed=None):
        super().__init__(evaluator, deterministic=deterministic, sample_seed=sample_seed)
        self.canonical = bool(canonical)
        self.frame = None

    def reset(self):
        super().reset()
        self.frame = None

    def propose(self, observations, state, step, previous_done, modes):
        if self.frame is None:
            if step != 0:
                raise RuntimeError("a canonical frame must begin at episode reset")
            self.frame = northeast_frame(observations) if self.canonical else D4.IDENTITY
        if self.frame == D4.IDENTITY:
            return super().propose(observations, state, step, previous_done, modes)
        action = super().propose(transform_observations(observations, self.frame),
                                 transform_state(state, self.frame), step, previous_done, modes)
        return inverse_actions(action, self.frame)


class TimedController:
    def __init__(self, controller):
        self.controller = controller
        self.inference_wall_seconds = 0.0
        self.inference_cpu_seconds = 0.0
        self.calls = 0

    def __getattr__(self, name):
        return getattr(self.controller, name)

    def reset(self):
        self.controller.reset()
        self.inference_wall_seconds = self.inference_cpu_seconds = 0.0
        self.calls = 0

    def propose(self, *args):
        wall, cpu = time.perf_counter(), time.process_time()
        try:
            return self.controller.propose(*args)
        finally:
            self.inference_wall_seconds += time.perf_counter() - wall
            self.inference_cpu_seconds += time.process_time() - cpu
            self.calls += 1


class GeometryObserver:
    def __init__(self):
        self.proposals = []
        self.displacements = []

    def attach(self, controller):
        return nullcontext()

    def on_step(self, *, observations_t, observations_t1, proposal_t, **unused):
        self.proposals.append(np.asarray(proposal_t, dtype=np.float32).copy())
        self.displacements.append(own_positions(observations_t1) - own_positions(observations_t))

    def arrays(self):
        return {"proposal": np.asarray(self.proposals, dtype=np.float32),
                "physical_displacement": np.asarray(self.displacements, dtype=np.float64)}


def extra_readings(steps, observed):
    qos = steps["metrics"][:, QOS]
    positive = np.flatnonzero(qos > 0)
    early = min(1000, len(qos))
    delta = observed["physical_displacement"]
    speed = np.linalg.norm(delta[..., :2], axis=-1)
    normal = ~steps["mode"]
    center = 4000.0 - steps["own_xyz"][:100, :, :2]
    inward_dot = np.sum(delta[:100, :, :2] * center, axis=-1)
    distance = np.linalg.norm(center, axis=-1)
    inward_distance = np.divide(inward_dot, distance, out=np.zeros_like(inward_dot),
                                where=distance > 0)
    return {
        "first_service_step": int(positive[0]) if len(positive) else None,
        "first_service_censored_wait": int(positive[0]) if len(positive) else int(len(qos)),
        "served_by_step60": bool(len(positive) and positive[0] <= 60),
        "served_by_step120": bool(len(positive) and positive[0] <= 120),
        "qos_first1000": float(np.mean(qos[:early])),
        "qos_after1000": float(np.mean(qos[1000:])) if len(qos) > 1000 else None,
        "mean_horizontal_speed_mps": float(speed.mean()),
        "normal_horizontal_speed_mps": float(speed[normal].mean()) if normal.any() else None,
        "inward_displacement_first100_m_per_uav": float(inward_distance.sum(axis=0).mean()),
        "reserve10_uav_step_fraction": float(np.mean(steps["battery"] < .10)),
        "reserve10_any_step_fraction": float(np.mean(np.any(steps["battery"] < .10, axis=1))),
    }


def checkpoint_record(checkpoint_dir):
    record = read_record(Path(checkpoint_dir))
    expected = {"checkpoint": "c06", "training_seed": POLICY_SEED,
                "transitions": 1200000, "agent_pt_sha256": CHECKPOINT_SHA256,
                "policy_fingerprint": POLICY_FINGERPRINT}
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("checkpoint is not the prospectively selected c06")
    if _sha256(Path(checkpoint_dir) / record["agent_pt"]) != CHECKPOINT_SHA256:
        raise ValueError("checkpoint bytes differ from the selected c06")
    return record


def learned_controller(config, record, checkpoint_dir, job, log_dir):
    stochastic = job["program"].endswith("_stochastic")
    task = WorldTask(controller="L", seed=job["seed"], params=PRODUCTION_PARAMS,
                     horizon=config.episode_length, policy_seed=POLICY_SEED, threads=THREADS,
                     checkpoint=str(Path(checkpoint_dir) / record["agent_pt"]),
                     checkpoint_record=str(Path(checkpoint_dir) / "record.json"),
                     expected_checkpoint_sha256=CHECKPOINT_SHA256,
                     expected_policy_fingerprint=POLICY_FINGERPRINT,
                     action_mode="stochastic" if stochastic else "deterministic",
                     draw=0 if stochastic else None)
    agent, identity = load_learner_policy(task, record, config, torch.device("cpu"), log_dir)
    controller = CanonicalController(
        agent, canonical=job["program"].startswith("C_"), deterministic=not stochastic,
        sample_seed=sample_seed(POLICY_SEED, job["seed"], 0) if stochastic else None)
    return controller, agent, identity


def worker(payload):
    job, out_string, checkpoint_dir = payload
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    raw_path = out / "raw" / f"{stem}.npz"
    progress_path = out / "raw" / f"{stem}.progress.json"
    env, observer = None, GeometryObserver()
    completed_steps = 0

    def progress(count):
        nonlocal completed_steps
        completed_steps += count
        if completed_steps % 100 == 0:
            _write_json(progress_path, {**job, "steps": completed_steps})

    try:
        if job not in plan():
            raise ValueError("worker received an undeclared job")
        faulthandler.enable()
        torch.set_num_threads(THREADS)
        if torch.get_default_dtype() != torch.float32:
            raise RuntimeError("B01 requires native Torch FP32")
        record = checkpoint_record(checkpoint_dir)
        config = learner_eval_config(make_eval_config(HORIZON, POLICY_SEED), record)
        env = make_env(config, job["seed"])
        with tempfile.TemporaryDirectory(prefix="policy-", dir=out / "logs") as log_dir:
            agent, identity, before = None, {}, None
            if job["program"] == "H_central10":
                controller = HeuristicController(
                    replace(variant("H1", information="central"), replan_period=10), env)
            else:
                controller, agent, identity = learned_controller(
                    config, record, checkpoint_dir, job, log_dir)
                before = (initialization_fingerprint(agent), optimizer_steps(agent),
                          _normalizer_snapshot(agent))
            controller = TimedController(controller)
            row, steps = evaluate_world(controller, env, config, job["seed"], PRODUCTION_PARAMS,
                                        observer=observer, progress=progress)
            if agent is not None and (
                initialization_fingerprint(agent) != before[0]
                or optimizer_steps(agent) != before[1]
                or not _same_snapshot(_normalizer_snapshot(agent), before[2])
            ):
                raise RuntimeError("evaluation mutated frozen policy/optimizer/normalizers")
            observed = observer.arrays()
            if len(observed["proposal"]) != row["actual_length"] or completed_steps != row["actual_length"]:
                raise RuntimeError("native, observer and progress counts differ")
            if raw_path.exists():
                raise FileExistsError(raw_path)
            np.savez_compressed(raw_path, **steps, **observed, metric_fields=np.asarray(TRACE_FIELDS))
            _write_json(progress_path, {**job, "steps": completed_steps, "status": "completed"})
            row.update(job, status="completed", **extra_readings(steps, observed), identity=identity,
                       frame=getattr(controller, "frame", D4.IDENTITY).name,
                       raw_path=str(raw_path.relative_to(out)), raw_sha256=_sha256(raw_path),
                       raw_bytes=raw_path.stat().st_size, inference_calls=controller.calls,
                       inference_wall_seconds=controller.inference_wall_seconds,
                       inference_cpu_seconds=controller.inference_cpu_seconds,
                       sample_seed=(sample_seed(POLICY_SEED, job["seed"], 0)
                                    if job["program"].endswith("_stochastic") else None))
        return row | {"worker_wall_seconds": time.monotonic() - started,
                      "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                      "worker_peak_rss_kib": _rss_kib()}
    except BaseException as error:
        result = {**job, "status": "failed", "error_type": type(error).__name__,
                  "error": str(error), "traceback": traceback.format_exc(),
                  "partial_observed_steps": completed_steps,
                  "worker_wall_seconds": time.monotonic() - started,
                  "worker_cpu_seconds": _cpu_seconds() - cpu_started,
                  "worker_peak_rss_kib": _rss_kib()}
        _write_json(progress_path, {**job, "steps": completed_steps, "status": "failed"})
        if raw_path.exists():
            result.update(incomplete_raw_path=str(raw_path.relative_to(out)),
                          incomplete_raw_sha256=_sha256(raw_path))
        elif observer.proposals:
            partial = raw_path.with_suffix(".partial.npz")
            np.savez_compressed(partial, **observer.arrays())
            result.update(partial_path=str(partial.relative_to(out)), partial_sha256=_sha256(partial),
                          partial_bytes=partial.stat().st_size)
        return result
    finally:
        if env is not None:
            env.close()


CONTRAST_FIELDS = (
    "raw_native_J", "qos_per_step", "return_constraint_cost_sum",
    "cutoff_event_count_sum", "depletion_event_count_sum", "min_decoded_battery",
    "reserve10_uav_step_fraction", "qos_first1000", "qos_after1000",
    "first_service_censored_wait", "mean_horizontal_speed_mps",
    "inward_displacement_first100_m_per_uav", "boundary_share_normal_mode",
    "inference_cpu_seconds", "worker_cpu_seconds",
)


def paired(rows, candidate, baseline):
    by_key = {(row["program"], row["seed"]): row for row in rows}
    result = {}
    for field in CONTRAST_FIELDS:
        paired_seeds = [seed for seed in WORLDS if by_key[candidate, seed][field] is not None
                        and by_key[baseline, seed][field] is not None]
        values = [float(by_key[candidate, seed][field]) - float(by_key[baseline, seed][field])
                  for seed in paired_seeds]
        array = np.asarray(values, dtype=np.float64)
        mean = float(array.mean()) if len(array) else None
        se = float(array.std(ddof=1) / np.sqrt(len(array))) if len(array) > 1 else None
        half = float(student_t.ppf(.975, len(array) - 1) * se) if se is not None else None
        result[field] = {"mean": mean, "se": se,
                         "ci95": [mean-half, mean+half] if half is not None else None,
                         "paired_seeds": paired_seeds, "paired_worlds": len(array),
                         "positive": int((array > 0).sum()), "negative": int((array < 0).sum()),
                         "zero": int((array == 0).sum()), "differences": values}
    return result


def summarize(rows):
    expected = plan()
    completed = [row for row in rows if row["status"] == "completed"]
    keys = [row["job_key"] for row in rows]
    complete = (len(rows) == len(expected) and len(set(keys)) == len(expected)
                and len(completed) == len(expected)
                and set(keys) == {job["job_key"] for job in expected})
    result = {"direction": DIRECTION, "status": "complete" if complete else "incomplete",
              "fits": 0, "optimizer_updates": 0, "planned_episodes": len(expected),
              "episodes_completed": len(completed),
              "completed_transitions": sum(row["actual_length"] for row in completed),
              "programs": {program: aggregate([r for r in completed if r["program"] == program])
                           for program in PROGRAMS}, "contrasts": {}}
    if complete:
        for mode in ("deterministic", "stochastic"):
            result["contrasts"][f"C-P_{mode}"] = paired(rows, f"C_{mode}", f"P_{mode}")
            result["contrasts"][f"C-H_{mode}"] = paired(rows, f"C_{mode}", "H_central10")
    return result


def run(out, launch_sha, checkpoint_dir):
    out, checkpoint_dir = Path(out), Path(checkpoint_dir).resolve()
    record = checkpoint_record(checkpoint_dir)
    if any((out / name).exists() for name in ("config.json", "perworld.json", "summary.json", "manifest.json", "raw")):
        raise FileExistsError(f"scientific artifacts already exist: {out}")
    started, cpu_started = time.monotonic(), _cpu_seconds()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    (out / "logs").mkdir()
    jobs = plan()
    _write_json(out / "config.json", {
        "direction": DIRECTION, "batch": "B01-PC-NE", "launch_sha": launch_sha,
        "jobs": jobs, "horizon": HORIZON, "max_transitions": 240000,
        "fits": 0, "optimizer_updates": 0, "workers": WORKERS, "threads": THREADS,
        "device": "cpu", "dtype": "float32", "checkpoint_dir": str(checkpoint_dir),
        "record_sha256": _sha256(checkpoint_dir / "record.json"), "record": record,
        "shield": asdict(PRODUCTION_PARAMS), "trace_timing": TRACE_TIMING,
        "sample_seed_rule": SAMPLE_SEED_RULE, "stochastic_draw": 0,
        "controller_information": {
            program: (REFERENCE_INFORMATION["H1r10"] if program == "H_central10"
                      else L_CONTROLLER_INFORMATION) for program in PROGRAMS},
        "canonical_rule": "reflect initial mean spawn xy to NE, fixed per episode; no identity permutation",
        "scope": "conditional deployment package; labeled reset law is not D4 invariant",
        "interval": "paired world t interval, descriptive conditional on one retained c06",
    })
    rows, submitted, pool_errors = [], [], []
    expected_keys = [job["job_key"] for job in jobs]

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: expected_keys.index(item["job_key"]))
        _write_json(out / "perworld.json", rows)
        _write_json(out / "summary.json", summarize(rows))

    _write_json(out / "perworld.json", rows)
    _write_json(out / "summary.json", summarize(rows))
    runner_error = None
    try:
        with ProcessPoolExecutor(max_workers=WORKERS, mp_context=multiprocessing.get_context("spawn")) as executor:
            _, pool_errors = execute_bounded(
                executor, jobs, WORKERS, lambda job: (job, str(out), str(checkpoint_dir)),
                on_result, submitted, worker_fn=worker)
    except BaseException as error:
        runner_error = {"error_type": type(error).__name__, "error": str(error),
                        "traceback": traceback.format_exc()}
    summary = summarize(rows)
    orphans = orphan_raw_files(out, rows)
    progress_records = [json.loads(path.read_text()) for path in sorted((out / "raw").glob("*.progress.json"))]
    completed_keys = {row["job_key"] for row in rows if row["status"] == "completed"}
    partial_steps = sum(row["steps"] for row in progress_records if row["job_key"] not in completed_keys)
    if orphans or runner_error or pool_errors:
        summary.update(status="incomplete", contrasts={})
    summary.update(
        launch_sha=launch_sha, submitted_jobs=submitted,
        unstarted_jobs=[key for key in expected_keys if key not in submitted],
        partial_observed_transitions=partial_steps,
        known_transition_lower_bound=summary["completed_transitions"] + partial_steps,
        actual_transitions=summary["completed_transitions"] if summary["status"] == "complete" else None,
        orphan_raw=orphans, runner_error=runner_error, pool_errors=pool_errors,
        parent_wall_seconds=time.monotonic() - started, parent_cpu_seconds=_cpu_seconds()-cpu_started,
        parent_peak_rss_kib=_rss_kib(),
        worker_cpu_seconds_observed_sum=sum(row["worker_cpu_seconds"] for row in rows
                                            if "worker_cpu_seconds" in row),
        worker_wall_seconds_observed_sum=sum(row["worker_wall_seconds"] for row in rows
                                             if "worker_wall_seconds" in row),
        worker_peak_rss_kib_max=max((r["worker_peak_rss_kib"] for r in rows
                                     if "worker_peak_rss_kib" in r), default=None),
        worker_resources_unmeasured=[key for key in submitted
                                     if not any(r["job_key"] == key and "worker_cpu_seconds" in r
                                                for r in rows)],
    )
    _write_json(out / "summary.json", summary)
    files = [out / name for name in ("config.json", "perworld.json", "summary.json")]
    files.extend(path for path in sorted((out / "raw").iterdir()) if path.is_file())
    _write_json(out / "manifest.json", {
        "launch_sha": launch_sha,
        "artifacts": {str(path.relative_to(out)): {"sha256": _sha256(path), "bytes": path.stat().st_size}
                      for path in files},
    })
    return summary
