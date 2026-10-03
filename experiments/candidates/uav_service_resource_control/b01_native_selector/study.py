"""Finite native missions and persistent serial fits within one admitted purchase."""
from __future__ import annotations

import faulthandler
import json
from pathlib import Path
import time
import traceback

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    TRACE_FIELDS, evaluate_world, make_eval_config,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.uav_information_value.batch import effective_config
from experiments.candidates.uav_service_auxiliary.b01.native import make_env
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.capture import (
    CaptureEnv, Recorder, TimedController,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.metrics import episode_metrics
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import CANDIDATE_DTYPE

from .budget import check_stop, request_stop
from .contract import (HORIZON, FIT_SEEDS, clean, diagnostic_bytes, expected_counts,
                       identity, telemetry, training_jobs, write_json)
from .controller import make_controller
from .learner import Learner, _digest


def initialize_worker():
    import torch
    from experiments.candidates.energy_relay_benchmark.b01.heuristic import _lsa
    faulthandler.enable()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    if _lsa is None or torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B01 requires SciPy assignment and CPU Torch FP32")


def stem(spec):
    return spec["job_key"].replace("/", "_")


def save_checkpoint(out, fit, completed, learner):
    import torch
    path = Path(out)/"raw"/f"L{fit}_checkpoint_{completed:03d}.pt"
    if path.exists():
        raise FileExistsError(path)
    state = learner.state(include_replay=False)
    torch.save(state, path)
    return dict(path=str(path.relative_to(out)), **identity(path),
                state_digest=_digest(state), counts=learner.counts(), digests=learner.digests(),
                completed_missions=completed, inference_only=completed != 0)


def load_checkpoint(out, receipt, fit):
    import torch
    path = Path(out)/receipt["path"]
    actual = identity(path)
    if any(actual[key] != receipt[key] for key in ("bytes", "sha256")):
        raise AssertionError("checkpoint file identity changed")
    # This is our own source-bound trusted checkpoint; numpy RNG state is needed.
    state = torch.load(path, map_location="cpu", weights_only=False)
    if _digest(state) != receipt["state_digest"]:
        raise AssertionError("checkpoint state digest changed")
    learner = Learner(**FIT_SEEDS[fit])
    learner.load_state(state)
    if learner.digests() != receipt["digests"] or learner.counts() != receipt["counts"]:
        raise AssertionError("checkpoint restoration differs")
    return learner


class RewardCaptureEnv(CaptureEnv):
    def __init__(self, adapter, recorder, learner):
        super().__init__(adapter, recorder)
        self.learner = learner
        self.reward_hook_cpu_seconds = 0.

    def step(self, submitted):
        result = super().step(submitted)
        if self.learner is not None:
            origin = time.process_time()
            try:
                _, reward, terminated, truncated, _ = result
                self.learner.observe_reward(float(reward), bool(terminated or truncated))
            finally:
                self.reward_hook_cpu_seconds += time.process_time()-origin
        return result


def compact_row(row, row_path, out):
    # Detailed individual spells/arrays remain in one durable raw evidence tree.
    compact = {k: v for k, v in row.items() if isinstance(v, (str, int, float, bool)) or v is None}
    for key in ("policy_counts", "learner_counts", "learner_digests", "raw", "partial",
                "assignment_exposure", "learner_episode_counts"):
        if key in row:
            compact[key] = row[key]
    compact["row"] = dict(path=str(row_path.relative_to(out)), **identity(row_path))
    return compact


def episode(spec, out, learner=None, *, final_checkpoint=None):
    out = Path(out)
    wall, cpu = time.perf_counter(), time.process_time()
    raw_path, row_path = (out/"raw"/(stem(spec)+suffix) for suffix in (".npz", ".json"))
    progress_path = out/"raw"/(stem(spec)+".progress.json")
    adapter = env = recorder = controller = None
    completed_steps = constructions = construction_attempts = resets = 0
    setup_cpu = setup_wall = 0.
    learner_setup_cpu = learner_setup_wall = 0.
    learner_before = None

    def progress(count):
        nonlocal completed_steps
        completed_steps += count
        if completed_steps % 100 == 0:
            write_json(progress_path, dict(**spec, observed_steps=recorder.native_steps,
                                           policy_counts=controller.counters))
            check_stop(out)

    try:
        check_stop(out)
        if raw_path.exists() or row_path.exists():
            raise FileExistsError("episode already has evidence: " + spec["job_key"])
        if final_checkpoint is not None:
            if learner is not None or spec["program"] != "SELECTOR" or spec["phase"] != "final":
                raise ValueError("only fixed learned deployment may load a final checkpoint")
            setup_w, setup_c = time.perf_counter(), time.process_time()
            learner = load_checkpoint(out, final_checkpoint, spec["fit"])
            learner_setup_cpu = time.process_time()-setup_c
            learner_setup_wall = time.perf_counter()-setup_w
        setup_w, setup_c = time.perf_counter(), time.process_time()
        construction_attempts += 1
        config = make_eval_config(HORIZON, 0)
        constructions += 1
        construction_attempts += 1
        adapter = make_env(config, spec["seed"])
        constructions += 1
        effective = effective_config(adapter, HORIZON)
        setup_cpu, setup_wall = time.process_time()-setup_c, time.perf_counter()-setup_w
        tracked = spec["program"] != "C"
        recorder = Recorder(HORIZON, "H_A" if tracked else "C")
        env = RewardCaptureEnv(adapter, recorder, learner)
        if spec["program"] == "SELECTOR":
            if learner is None:
                raise ValueError("learned mission lacks its fixed fit")
            learner_before = learner.counts()
            learner.start_episode(spec["episode_index"], spec["phase"] == "train")
        elif learner is not None:
            raise ValueError("ordinary program received a learner")
        base = make_controller(spec["program"], chooser=None if learner is None else learner.decide,
                               theta=spec.get("theta"), initial_parity=spec.get("initial_parity", 0))
        controller = TimedController(base)
        resets = 1
        row, steps = evaluate_world(controller, env, config, spec["seed"], PRODUCTION_PARAMS,
                                    observer=recorder, progress=progress)
        length = row["actual_length"]
        if not (length == recorder.native_steps == recorder.decision_steps == completed_steps):
            raise AssertionError("native/evaluator/observer chronology differs")
        if not recorder.native_ends[length-1].any():
            raise AssertionError("complete mission lacks a native ending")
        counts = controller.counters
        if any(counts.get(k, 0) != v for k, v in expected_counts(spec["program"], length).items()):
            raise AssertionError("actual controller clock/ingestion exposure differs")
        audit = controller.audit_arrays() if hasattr(controller, "audit_arrays") else {
            "candidate_records": np.empty(0, CANDIDATE_DTYPE)}
        arrays = steps | recorder.arrays() | audit | {"metric_fields": np.asarray(TRACE_FIELDS)}
        arrays["choice_diagnostics_json"] = diagnostic_bytes(getattr(controller, "choice_diagnostics", []))
        if learner is not None:
            arrays.update({"learn_"+key: value for key, value in learner.episode_arrays().items()})
            if not learner.episode_ended or learner.pending is not None:
                raise AssertionError("mission left learner block pending")
            row["learner_counts"], row["learner_digests"] = learner.counts(), learner.digests()
            row["learner_episode_counts"] = {k: learner.counts()[k]-learner_before[k]
                                             for k in learner_before if k != "replay_size"}
            if spec["phase"] != "train" and row["learner_episode_counts"]["updates"] != 0:
                raise AssertionError("fixed deployment updated the learner")
        candidates = arrays["candidate_records"]
        if (not candidates["completed"].all() or not np.all(candidates["ticks"] == 30)
                or counts.get("candidate_forecasts", 0) != len(candidates)
                or counts.get("model_rf_calls", 0) != len(candidates)*3
                or counts.get("model_constructions", 0) != int(len(candidates) > 0)):
            raise AssertionError("complete private-query exposure differs")
        np.savez_compressed(raw_path, **arrays)
        row.update(episode_metrics(arrays))
        row.update(**spec, status="completed", policy_counts=counts, effective_config=effective,
                   native_parameters=recorder.parameters, environment_constructions=constructions,
                   explicit_resets=resets, native_terminal_type=("terminated" if
                   recorder.native_ends[length-1, 0] else "truncated"), engineering_harness_stop=False,
                   raw=dict(path=str(raw_path.relative_to(out)), **identity(raw_path)),
                   raw_array_bytes=sum(v.nbytes for v in arrays.values()),
                   configuration_cpu_seconds=setup_cpu, configuration_wall_seconds=setup_wall,
                   learner_setup_cpu_seconds=learner_setup_cpu, learner_setup_wall_seconds=learner_setup_wall,
                   reset_cpu_seconds=env.reset_cpu_seconds, reset_wall_seconds=env.reset_wall_seconds,
                   native_cpu_seconds=env.native_cpu_seconds, native_wall_seconds=env.native_wall_seconds,
                   proposal_cpu_seconds=controller.proposal_cpu_seconds,
                   proposal_wall_seconds=controller.proposal_wall_seconds,
                   reward_hook_cpu_seconds=env.reward_hook_cpu_seconds)
    except BaseException as error:
        request_stop(out, "native mission failed", job=spec, error=repr(error))
        row = dict(**spec, status="failed", error=repr(error), traceback=traceback.format_exc(),
                   observed_native_steps=0 if recorder is None else recorder.native_steps,
                   completed_decisions=completed_steps, environment_constructions=constructions,
                   construction_attempts=construction_attempts, explicit_resets=resets,
                   policy_counts=None if controller is None else controller.counters)
        if learner is not None:
            row.update(learner_counts=learner.counts(), learner_digests=learner.digests())
        try:
            if raw_path.exists():
                row["incomplete_raw"] = dict(path=str(raw_path.relative_to(out)), **identity(raw_path))
            elif recorder is not None and recorder.boundaries:
                arrays = recorder.arrays()
                if controller is not None and hasattr(controller, "audit_arrays"):
                    arrays.update(controller.audit_arrays())
                if controller is not None and hasattr(controller, "choice_diagnostics"):
                    arrays["choice_diagnostics_json"] = diagnostic_bytes(controller.choice_diagnostics)
                if learner is not None:
                    arrays.update({"learn_"+k: v for k, v in learner.episode_arrays().items()})
                partial_path = raw_path.with_suffix(".partial.npz")
                np.savez_compressed(partial_path, **arrays)
                row["partial"] = dict(path=str(partial_path.relative_to(out)), **identity(partial_path))
        except BaseException as preservation_error:
            row["preservation_error"] = repr(preservation_error)
    finally:
        try:
            if controller is not None:
                controller.close()
            if env is not None:
                env.close()
            elif adapter is not None:
                adapter.close()
        except BaseException as close_error:
            request_stop(out, "native/controller close failed", job=spec, error=repr(close_error))
            row.update(status="failed", close_error=repr(close_error))
    row.update({"worker_"+key: value for key, value in telemetry(wall, cpu).items()})
    write_json(row_path, clean(row))
    write_json(progress_path, dict(job_key=spec["job_key"], status=row["status"]))
    return compact_row(row, row_path, out)


def mission_worker(payload):
    spec, out, final_checkpoint = payload
    return episode(spec, out, final_checkpoint=final_checkpoint)


def fit_worker(payload):
    spec, out = payload
    wall, cpu = time.perf_counter(), time.process_time()
    fit = spec["fit"]
    ledger = dict(**spec, status="running", episodes=[], checkpoints=[])
    learner = None
    path = Path(out)/f"fit_{fit}.json"
    try:
        check_stop(out)
        learner = Learner(**FIT_SEEDS[fit])
        ledger["checkpoints"].append(save_checkpoint(out, fit, 0, learner))
        write_json(path, ledger)
        for mission in training_jobs(fit):
            check_stop(out)
            row = episode(mission, out, learner)
            ledger["episodes"].append(row)
            if row["status"] != "completed":
                raise RuntimeError("training mission failed; purchase closes")
            completed = mission["episode_index"] + 1
            if completed % 16 == 0:
                ledger["checkpoints"].append(save_checkpoint(out, fit, completed, learner))
            write_json(path, clean(ledger))
        ledger.update(status="completed", learner_counts=learner.counts(), learner_digests=learner.digests())
    except BaseException as error:
        request_stop(out, "fit failed", fit=fit, error=repr(error))
        ledger.update(status="failed", error=repr(error), traceback=traceback.format_exc())
        if learner is not None:
            ledger.update(learner_counts=learner.counts(), learner_digests=learner.digests())
            try:
                import torch
                failed = Path(out)/"raw"/f"L{fit}_failed_prefix.pt"
                torch.save(learner.state(), failed)
                ledger["failed_checkpoint"] = dict(path=str(failed.relative_to(out)), **identity(failed))
            except BaseException as preservation_error:
                ledger["preservation_error"] = repr(preservation_error)
    ledger.update({"worker_"+key: value for key, value in telemetry(wall, cpu).items()})
    write_json(path, clean(ledger))
    return ledger
