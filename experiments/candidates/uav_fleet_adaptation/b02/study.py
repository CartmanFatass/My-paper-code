"""The selected single-lineage local-C inheritance study; no retry or selection."""
from __future__ import annotations

from datetime import datetime, timezone
import copy
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .collect import collect_episode
from .contract import ARMS, FROZEN, PHASES, SOURCE_PINS, source_identities
from .model import checkpoint, make_optimizer, make_student, movement, state_copy, state_digest, train_phase
from .reading import cost_totals, read_comparisons, sum_counts


ROOT = Path(__file__).resolve().parents[4]


def new_counts():
    return dict(constructors=0, constructor_resets=0, explicit_resets=0, native_step_calls=0,
                native_steps=0, training_native_steps=0, evaluation_native_steps=0,
                complete_episodes=0, training_episodes=0, evaluation_episodes=0,
                fit_started=0, optimizer_steps=0, sample_presentations=0, expert_label_requests=0)


def validate_counts(batch):
    expected, actual = batch["expected"], batch["actual"]
    for key in ("native_steps", "training_native_steps", "evaluation_native_steps", "complete_episodes",
                "training_episodes", "evaluation_episodes", "sample_presentations", "expert_label_requests"):
        if actual[key] != expected[key]:
            raise AssertionError(f"exposure mismatch for {key}: {actual[key]} != {expected[key]}")
    if (actual["fit_started"] != 1 or actual["constructors"] != 1 or actual["constructor_resets"] != 1
            or actual["explicit_resets"] != expected["complete_episodes"]
            or actual["native_step_calls"] != expected["native_steps"]
            or actual["optimizer_steps"] != expected["optimizer_updates"]):
        raise AssertionError("fit/reset/call/update contract mismatch")
    cost = batch["costs"]
    if cost["full_C"]["requests"] != expected["full_C_requests"]:
        raise AssertionError("full-C query count mismatch")
    if cost["C7"]["requests"] != expected["C7_requests"]:
        raise AssertionError("C7 query count mismatch")
    if cost["helper"]["helper_calls"] > expected["helper_request_ceiling"]:
        raise AssertionError("undeclared helper calls")
    if (cost["neural"]["neural_rows"] > expected["neural_rollout_row_ceiling"]
            or cost["neural"]["sampled_draws"] != expected["sampled_draws"]):
        raise AssertionError("neural forward/sampling exposure mismatch")


def run_batch(out, launch_sha, *, admission=None, protocol=FROZEN, factory=None,
              scientific_invocation=False, entry_start=None, entry_cpu=None):
    protocol.validate()
    if factory is None:
        if not scientific_invocation or not admission or admission.get("sha") != launch_sha or protocol != FROZEN:
            raise ValueError("native result work requires the admitted fixed production contract")
        from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
        factory = make_real
    elif scientific_invocation or protocol == FROZEN:
        raise ValueError("dependency-injected fixtures must be nonproduction and nonscientific")
    start_wall = time.perf_counter() if entry_start is None else entry_start
    start_cpu = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError("existing scientific output: reconcile it; this study has no retry/resume interface")
    (out / "raw").mkdir()
    (out / "assets").mkdir()
    batch = dict(object="UAV-LOCAL-C-INHERITANCE-B02", status="INCOMPLETE", launch_sha=launch_sha,
                 scientific_invocation=scientific_invocation, protocol=protocol.to_dict(), expected=protocol.expected(),
                 actual=new_counts(), rows=[], phases=[], assets={}, costs={},
                 start_utc=datetime.now(timezone.utc).isoformat(), admission=dict(admission or {}),
                 environment=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                                  device="cpu", dtype="float32", host=platform.node(),
                                  torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                                  thread_environment={name: os.environ.get(name) for name in
                                                      ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="worker entry through last completed summary preparation, including imports when invoked "
                              "by run.py, environment construction, resets, all collection/training/checks, serialization "
                              "and prior summary writes; final self-report write excluded; no reader cost here")
    env = None
    inflight = {}

    def publish():
        batch["worker_wall_seconds"] = time.perf_counter() - start_wall
        batch["worker_cpu_seconds"] = time.process_time() - start_cpu
        batch["worker_max_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(out / "summary.json", batch)

    def save_asset(name, model, optimizer=None):
        data = checkpoint(model, optimizer)
        data.update(endpoint=name, launch_sha=launch_sha, protocol=protocol.to_dict(),
                    optimizer_steps=batch["actual"]["optimizer_steps"])
        path = out / "assets" / (name + ".pt")
        if path.exists():
            raise FileExistsError("checkpoint already exists")
        torch.save(data, path)
        identity = file_identity(path)
        identity["path"] = str(path.relative_to(out))
        batch["assets"][name] = dict(identity, state_sha256=data["state_sha256"],
                                    optimizer_steps=data["optimizer_steps"])
        return copy.deepcopy(model).eval()

    try:
        batch["source_sha256"] = source_identities(ROOT)
        write_json(out / "config.json", {key: batch[key] for key in
                                        ("object", "launch_sha", "scientific_invocation", "protocol", "expected",
                                         "source_sha256", "environment")})
        publish()
        model = make_student(protocol.init_seed).eval()
        initial = state_copy(model)
        optimizer = make_optimizer(model, protocol)
        endpoints = {"S0": save_asset("S0", model)}
        env = factory(protocol.training_worlds[0][0])
        batch["actual"]["constructors"] += 1
        batch["actual"]["constructor_resets"] += 1  # Bound native constructor performs one unscored reset.
        features, labels = [], []
        for phase, worlds in enumerate(protocol.training_worlds):
            behavior_sha = (SOURCE_PINS["experiments/candidates/uav_local_history/b01/controller.py"]
                            if phase == 0 else state_digest(model.state_dict()))
            for world in worlds:
                row, cases = collect_episode(
                    env, arm=PHASES[phase], world=world, out=out, protocol=protocol, counts=batch["actual"],
                    kind="training", actor=None if phase == 0 else model, phase=phase, policy_sha=behavior_sha,
                    inflight=inflight)
                batch["rows"].append(row)
                features.append(cases[0])
                labels.append(cases[1])
                batch["progress"] = dict(stage="collect", phase=phase, world=world,
                                         complete_episodes=batch["actual"]["complete_episodes"])
                publish()
            x, y = np.concatenate(features), np.concatenate(labels)
            if phase == 0:
                batch["actual"]["fit_started"] += 1

            def progress(p, epoch):
                batch["progress"] = dict(stage="optimization", phase=p, epoch=epoch,
                                         optimizer_steps=batch["actual"]["optimizer_steps"])
                publish()

            phase_row = train_phase(model, optimizer, x, y, phase, protocol, batch["actual"], progress)
            batch["phases"].append(phase_row)
            name = ("BC", "D1", "S")[phase]
            frozen = save_asset(name, model, optimizer)
            if name in ("BC", "S"):
                endpoints[name] = frozen
            publish()
        batch["learner_movement"] = movement(initial, state_copy(model))
        batch["initial_state_sha256"] = state_digest(initial)
        batch["final_state_sha256"] = state_digest(model.state_dict())
        batch["actual_learning"] = bool(batch["actual"]["optimizer_steps"] > 0
                                        and batch["learner_movement"]["changed_parameters"] > 0)
        del features, labels, x, y
        for wi, world in enumerate(protocol.evaluation_worlds):
            order = ARMS[wi % len(ARMS):] + ARMS[:wi % len(ARMS)]
            for arm in order:
                asset = "S" if arm in ("S_greedy", "S_sampled") else arm
                actor = endpoints.get(asset)
                policy_sha = (batch["assets"][asset]["state_sha256"] if actor is not None else
                              batch["source_sha256"]["experiments/candidates/uav_fleet_adaptation/b02/controllers.py"])
                row, cases = collect_episode(env, arm=arm, world=world, out=out, protocol=protocol,
                                             counts=batch["actual"], kind="evaluation", actor=actor,
                                             policy_sha=policy_sha, inflight=inflight)
                if cases is not None:
                    raise AssertionError("evaluation acquired teacher labels")
                batch["rows"].append(row)
                batch["progress"] = dict(stage="evaluation", arm=arm, world=world,
                                         complete_episodes=batch["actual"]["complete_episodes"])
                publish()
        batch["costs"] = cost_totals(batch["rows"])
        validate_counts(batch)
        batch["reading"] = read_comparisons(batch["rows"], protocol.evaluation_worlds,
                                            actual_learning=batch["actual_learning"])
        if source_identities(ROOT) != batch["source_sha256"]:
            raise RuntimeError("source changed during execution")
        batch["status"] = "COMPLETE"
        batch["finish_utc"] = datetime.now(timezone.utc).isoformat()
    except BaseException as error:
        batch["failure"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
        cost_rows = list(batch["rows"])
        if inflight:
            partial = {key: inflight[key] for key in ("arm", "world", "kind", "phase")}
            partial.update(policy_counts=sum_counts(inflight["policy_agents"]),
                           expert_counts=sum_counts(inflight["expert_agents"]),
                           feature_counts=sum_counts(inflight["feature_agents"]), **inflight["times"])
            batch["partial_episode"] = partial
            cost_rows.append(partial)
        batch["costs"] = cost_totals(cost_rows)
        batch["costs"]["incomplete"] = True
        batch["costs"]["scope"] += "; failed worker includes live partial-episode recorded counters, not a completed " \
                                    "scientific row; work inside the interrupted call may be unmeasured"
        publish()
        raise
    finally:
        if env is not None and hasattr(env, "close"):
            env.close()
    publish()
    return batch
