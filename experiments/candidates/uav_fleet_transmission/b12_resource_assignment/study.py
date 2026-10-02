"""Selected E/B missions; fixed C/H/H_T evidence is read, never rerun."""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import faulthandler
import json
import multiprocessing
from pathlib import Path
import resource
import time
import traceback

import numpy as np

from experiments.candidates.uav_fleet_transmission.b10_service_assignment.budget import execute_budgeted, check_worker_stop
from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, TRACE_TIMING, evaluate_world, make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_information_value.batch import effective_config
from experiments.candidates.uav_service_auxiliary.b01.native import make_env

from .capture import CaptureEnv, Recorder, TimedController
from .contract import (
    DIRECTION, HORIZON, OBJECT, expected_counts, identity, jobs, source_binding,
    sum_counts, telemetry, write_json,
)
from .controller import make_controller
from .metrics import comparisons, episode_metrics


def worker(payload):
    job, out_string, phase = payload
    wall, cpu = time.perf_counter(), time.process_time()
    out = Path(out_string)
    stem = job["job_key"].replace("/", "_")
    progress_path = out / "raw" / (stem + ".progress.json")
    raw_path = out / "raw" / (stem + ".npz")
    recorder = env = controller = adapter = None
    completed_steps = constructed = reset_attempts = 0
    configuration_cpu = configuration_wall = 0.0

    def progress(count):
        nonlocal completed_steps
        completed_steps += count
        if completed_steps % 100 == 0:
            write_json(progress_path, dict(**job, status="running", observed_steps=recorder.native_steps,
                                           completed_decisions=recorder.decision_steps,
                                           policy_counts=getattr(controller, "counters", None)))
            check_worker_stop(out)

    try:
        if job not in jobs(phase) or raw_path.exists():
            raise ValueError("undeclared or already-recorded episode")
        import torch
        from experiments.candidates.energy_relay_benchmark.b01.heuristic import _lsa
        faulthandler.enable()
        torch.set_num_threads(1)
        if _lsa is None or torch.get_default_dtype() != torch.float32:
            raise RuntimeError("B12 requires SciPy assignment and Torch FP32")
        setup_wall, setup_cpu = time.perf_counter(), time.process_time()
        config = make_eval_config(HORIZON, 0)  # One shape-probe constructor; no reset.
        constructed = 1
        adapter = make_env(config, job["seed"])
        constructed = 2
        effective = effective_config(adapter, HORIZON)
        configuration_wall = time.perf_counter() - setup_wall
        configuration_cpu = time.process_time() - setup_cpu
        recorder = Recorder(job["limit"], job["arm"])
        env = CaptureEnv(adapter, recorder, engineering=phase == "engineering")
        base = make_controller(job["arm"])
        controller = TimedController(base)
        reset_attempts = 1
        row, steps = evaluate_world(controller, env, config, job["seed"], PRODUCTION_PARAMS,
                                    observer=recorder, progress=progress)
        length = row["actual_length"]
        if not (length == recorder.native_steps == recorder.decision_steps == completed_steps):
            raise AssertionError("native/evaluator/observer exposure mismatch")
        if not recorder.native_ends[length - 1].any():
            raise AssertionError("full mission lacks native ending")
        fixed_counts = expected_counts(job["arm"], length)
        counts = controller.counters
        if any(counts.get(key, 0) != value for key, value in fixed_counts.items()):
            raise AssertionError("actual controller ingestion/clock accounting differs")
        audit = controller.audit_arrays()
        arrays = steps | recorder.arrays() | audit | {"metric_fields": np.asarray(TRACE_FIELDS)}
        candidates = arrays["candidate_records"]
        if not candidates["completed"].all():
            raise AssertionError("incomplete analytical candidate in complete mission")
        if any(counts.get(key, 0) for key in ("associations", "model_constructions", "model_rf_calls", "nominal_ticks")):
            raise AssertionError("forbidden old tracker/private/RF/nominal work")
        np.savez_compressed(raw_path, **arrays)
        row.update(episode_metrics(arrays))
        row.update(**job, status="completed", policy_counts=counts, effective_config=effective,
                   native_parameters=recorder.parameters,
                   environment_constructions=constructed, explicit_resets=reset_attempts,
                   native_terminal_type=("terminated" if recorder.native_ends[length - 1, 0] else
                                         "truncated" if recorder.native_ends[length - 1, 1] else "none"),
                   engineering_harness_stop=phase == "engineering" and not recorder.native_ends[length - 1].any(),
                   raw=dict(path=str(raw_path.relative_to(out)), **identity(raw_path)),
                   raw_array_bytes=sum(value.nbytes for value in arrays.values()),
                   configuration_cpu_seconds=configuration_cpu, configuration_wall_seconds=configuration_wall,
                   reset_cpu_seconds=env.reset_cpu_seconds, reset_wall_seconds=env.reset_wall_seconds,
                   native_cpu_seconds=env.native_cpu_seconds, native_wall_seconds=env.native_wall_seconds,
                   proposal_cpu_seconds=controller.proposal_cpu_seconds,
                   proposal_wall_seconds=controller.proposal_wall_seconds)
        row.update({"worker_" + key: value for key, value in telemetry(wall, cpu).items()})
        write_json(progress_path, dict(**job, status="completed", observed_steps=length,
                                       completed_decisions=length, policy_counts=counts))
        return row
    except BaseException as error:
        row = dict(**job, status="failed", error=repr(error), traceback=traceback.format_exc(),
                   completed_decisions=completed_steps,
                   observed_native_steps=0 if recorder is None else recorder.native_steps,
                   completed_environment_constructions=constructed, explicit_reset_attempts=reset_attempts,
                   construction_count_scope="completed calls; an interrupted constructor may be additional",
                   policy_counts=getattr(controller, "counters", None),
                   failure_count_scope="observed E/B attempted counters; interrupted calls retain their unknown suffix")
        try:
            if raw_path.exists():
                row["incomplete_raw"] = dict(path=str(raw_path.relative_to(out)), **identity(raw_path))
            elif recorder is not None and recorder.boundaries:
                partial = raw_path.with_suffix(".partial.npz")
                partial_arrays = recorder.arrays()
                if controller is not None and hasattr(controller, "audit_arrays"):
                    partial_arrays.update(controller.audit_arrays())
                np.savez_compressed(partial, **partial_arrays)
                row["partial"] = dict(path=str(partial.relative_to(out)), **identity(partial))
        except BaseException as preservation_error:
            row["preservation_error"] = repr(preservation_error)
        row.update({"worker_" + key: value for key, value in telemetry(wall, cpu).items()})
        write_json(progress_path, row)
        return row
    finally:
        if controller is not None and hasattr(controller, "close"):
            controller.close()
        if env is not None:
            env.close()
        elif adapter is not None:
            adapter.close()


def run_batch(out, launch_sha, phase, workers, budget, reference):
    out = Path(out)
    if workers not in range(1, 5) or (phase == "engineering" and workers != 1):
        raise ValueError("scientific workers 1..4; engineering fixed serial order")
    plan = jobs(phase)
    for name in ("config.json", "perworld.json", "summary.json", "manifest.json", "raw"):
        if (out / name).exists():
            raise FileExistsError(out / name)
    binding = source_binding()
    wall, cpu = time.perf_counter(), time.process_time()
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    child_cpu = usage.ru_utime + usage.ru_stime
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    config = dict(object=OBJECT, direction=DIRECTION, phase=phase, launch_sha=launch_sha,
                  source_binding=binding, jobs=plan, horizon=HORIZON, workers=workers, numeric_threads=1,
                  fits=0, labels=0, optimizer_updates=0, shield=asdict(PRODUCTION_PARAMS),
                  trace_timing=TRACE_TIMING,
                  model_contract="all actual analytic edges/leximin criteria counted and replayed once; zero old RF/private model",
                  model_resets=0, model_native_steps=0,
                  truth_rights="read-only capture/reader; every action uses only the original lawful observations",
                  primary="paired B-E native J with QoS; E/B versus frozen C/H_A/H_T complete uses",
                  frozen_reference={k:v for k,v in reference.items() if k!="rows"},
                  prior_cost_evidence=budget.prior_evidence, prior_cpu_seconds=budget.prior,
                  cpu_review_limit_seconds=budget.limit,
                  uncertainty="descriptive two-sided paired-world Student-t 95%, df=31 for science")
    write_json(out / "config.json", config)
    rows, submitted, pool_errors = [], [], []
    order = [job["job_key"] for job in plan]

    def on_result(row):
        rows.append(row)
        rows.sort(key=lambda item: order.index(item["job_key"]))
        write_json(out / "perworld.json", rows)
        write_json(out / "progress.json", dict(phase=phase, completed=sum(r["status"] == "completed" for r in rows),
                   reported=len(rows), submitted=list(submitted), planned=len(plan)))

    write_json(out / "perworld.json", rows)
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        _, pool_errors = execute_budgeted(pool, plan, workers, lambda job: (job, str(out), phase),
                                         on_result, submitted, worker_fn=worker, budget=budget)
    completed = [row for row in rows if row["status"] == "completed"]
    complete = len(completed) == len(plan) and not pool_errors
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    summary = dict(object=OBJECT, phase=phase, launch_sha=launch_sha,
                   status="complete" if complete else "incomplete", fits=0, labels=0, optimizer_updates=0,
                   budget_stopped=budget.stopped,budget_checkpoint=budget.last,
                   jobs=len(plan), completed_episodes=len(completed), submitted_jobs=submitted,
                   unstarted_jobs=[key for key in order if key not in submitted], pool_errors=pool_errors,
                   actual_native_transitions=sum(r["actual_length"] for r in completed) if complete else None,
                   known_native_transition_lower_bound=sum(r["actual_length"] for r in completed)
                       + sum(r.get("observed_native_steps", 0) for r in rows if r["status"] != "completed"),
                   policy_counts=sum_counts(r["policy_counts"] for r in completed),
                   environment_constructions=sum(r["environment_constructions"] for r in completed),
                   explicit_resets=sum(r["explicit_resets"] for r in completed),
                   worker_cpu_seconds_sum=sum(r.get("worker_cpu_seconds", 0) for r in rows),
                   worker_wall_seconds_sum=sum(r.get("worker_wall_seconds", 0) for r in rows),
                   worker_peak_rss_kib_max=max((r.get("worker_peak_rss_kib", 0) for r in rows), default=None),
                   worker_resources_unmeasured=[r["job_key"] for r in rows if "worker_cpu_seconds" not in r],
                   reaped_worker_cpu_seconds=usage.ru_utime + usage.ru_stime - child_cpu,
                   raw_storage_bytes=sum(r["raw"]["bytes"] for r in completed),
                   raw_allocated_bytes=sum(r["raw"]["allocated_bytes"] for r in completed),
                   raw_array_bytes=sum(r["raw_array_bytes"] for r in completed),
                   **{"parent_" + key: value for key, value in telemetry(wall, cpu).items()})
    if complete and phase == "scientific":
        summary["paired"] = comparisons(completed + reference["rows"])
    write_json(out / "summary.json", summary)
    manifest = dict(object=OBJECT, launch_sha=launch_sha,
                    artifacts={name: identity(out / name) for name in ("config.json", "perworld.json", "summary.json")},
                    raw={str(path.relative_to(out)): identity(path) for path in sorted((out / "raw").iterdir())})
    write_json(out / "manifest.json", manifest)
    return summary
