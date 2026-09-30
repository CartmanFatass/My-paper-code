"""One fresh inheritance lineage, reusing verified ordinary controls without execution."""
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
from experiments.candidates.uav_fleet_adaptation.b02.collect import collect_episode
from .contract import NEW_ARMS, FROZEN, OBJECT, PHASES, SOURCE_PINS, source_identities, validate_counts
from experiments.candidates.uav_fleet_adaptation.b02.model import (
    checkpoint, make_optimizer, make_student, movement, state_copy, state_digest, train_phase,
)
from experiments.candidates.uav_fleet_adaptation.b02.reading import cost_totals, sum_counts
from experiments.candidates.uav_fleet_adaptation.b02.study import new_counts
from .reading import read_comparisons
from .retained import load_retained


ROOT = Path(__file__).resolve().parents[4]


def run_batch(out, launch_sha, *, retained_out, admission=None, protocol=FROZEN, factory=None,
              scientific_invocation=False, fixture_binding=None, entry_start=None, entry_cpu=None):
    protocol.validate()
    if factory is None:
        if not scientific_invocation or not admission or admission.get("sha") != launch_sha or protocol != FROZEN or fixture_binding is not None:
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
    batch = dict(object=OBJECT, status="INCOMPLETE", launch_sha=launch_sha,
                 scientific_invocation=scientific_invocation, protocol=protocol.to_dict(), expected=protocol.expected(),
                 actual=new_counts(), rows=[], phases=[], assets={}, costs={}, retained={},
                 start_utc=datetime.now(timezone.utc).isoformat(), admission=dict(admission or {}),
                 environment=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                                  device="cpu", dtype="float32", host=platform.node(),
                                  torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                                  thread_environment={name: os.environ.get(name) for name in
                                                      ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="worker entry through last completed summary preparation, including imports when invoked "
                              "by run.py, retained-control validation, environment construction, resets, all new collection/training/checks, serialization "
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
        # This guard precedes even the native constructor's unscored reset.
        retained = load_retained(retained_out, protocol, repo=ROOT,
                                 permit_fixture=not scientific_invocation, binding=fixture_binding)
        batch["retained"] = {key: retained[key] for key in
                             ("root", "binding", "original_protocol", "rows", "source_sha256", "raw_verification")}
        batch["retained"].update(
            already_paid=True, new_native_steps=0,
            previous_screens=retained["old_reading"]["screens"],
            original_assets=retained["old_assets"],
            costs=cost_totals(retained["rows"]),
            timing_scope="unchanged historical controls measured in the original B02 operation; no new execution")
        config = {key: batch[key] for key in ("object", "launch_sha", "scientific_invocation", "protocol", "expected",
                                             "source_sha256", "environment")}
        config["retained"] = {key: batch["retained"][key] for key in
                              ("root", "binding", "original_protocol", "already_paid", "new_native_steps")}
        write_json(out / "config.json", config)
        publish()
        model = make_student(protocol.init_seed).eval()
        initial = state_copy(model)
        if state_digest(initial) == retained["old_assets"]["S0"]["state_sha256"]:
            raise AssertionError("fresh initialization reproduced the prior initial actor")
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
            order = NEW_ARMS[wi % len(NEW_ARMS):] + NEW_ARMS[:wi % len(NEW_ARMS)]
            for arm in order:
                asset = "S" if arm in ("S_greedy", "S_sampled") else arm
                actor = endpoints[asset]
                policy_sha = batch["assets"][asset]["state_sha256"]
                row, cases = collect_episode(env, arm=arm, world=world, out=out, protocol=protocol,
                                             counts=batch["actual"], kind="evaluation", actor=actor,
                                             policy_sha=policy_sha, inflight=inflight)
                # Preserve complete paid exposure even if the cross-run reset guard fails.
                batch["rows"].append(row)
                if cases is not None:
                    raise AssertionError("evaluation acquired teacher labels")
                controls = [r for r in retained["rows"] if r["world"] == world]
                if len(controls) != 2 or any(row["initial_state_sha256"] != r["initial_state_sha256"] for r in controls):
                    raise AssertionError("new evaluation reset differs from source-bound retained world")
                batch["progress"] = dict(stage="evaluation", arm=arm, world=world,
                                         complete_episodes=batch["actual"]["complete_episodes"])
                publish()
        batch["costs"] = cost_totals(batch["rows"])
        validate_counts(batch)
        batch["reading"] = read_comparisons(batch["rows"], batch["retained"], protocol.evaluation_worlds,
                                            actual_learning=batch["actual_learning"])
        if source_identities(ROOT) != batch["source_sha256"]:
            raise RuntimeError("source changed during execution")
        final_retained = load_retained(retained_out, protocol, repo=ROOT,
                                       permit_fixture=not scientific_invocation, binding=fixture_binding)
        if any(final_retained[key] != retained[key] for key in ("root", "binding", "rows", "source_sha256")):
            raise RuntimeError("retained controls changed during execution")
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
