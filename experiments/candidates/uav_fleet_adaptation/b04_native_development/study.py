"""The fixed two-asset reward-development and paid-calibration package."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import checkpoint, movement, state_copy, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_initial_assets, verify_initial_assets
from .collect import collect_episode
from .contract import CANDIDATES, FROZEN, OBJECT, candidate_spec, evaluation_plan, new_counts, source_identities
from .learning import fresh_critic, make_optimizers, update_group
from .reading import calibration_result, comparisons, cost_totals, validate_counts


ROOT = Path(__file__).resolve().parents[4]


def run_batch(out, launch_sha, *, admission=None, protocol=FROZEN, factory=None,
              scientific_invocation=False, bindings=None, entry_start=None, entry_cpu=None):
    protocol.validate()
    fixture = factory is not None
    if not fixture:
        if (not scientific_invocation or not admission or admission.get("sha") != launch_sha
                or protocol != FROZEN or bindings is not None):
            raise ValueError("native result work requires the admitted fixed production contract")
        from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
        factory = make_real
    elif scientific_invocation or protocol == FROZEN or bindings is None:
        raise ValueError("dependency-injected fixtures must be explicit, nonproduction and nonscientific")
    start_wall = time.perf_counter() if entry_start is None else entry_start
    start_cpu = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError("existing scientific output: reconcile it; no retry/resume interface exists")
    (out / "raw").mkdir()
    (out / "assets").mkdir()
    counts = new_counts()
    batch = dict(object=OBJECT, state="INCOMPLETE", status="INCOMPLETE", launch_sha=launch_sha,
                 scientific_execution=scientific_invocation, protocol=protocol.to_dict(),
                 expected_maximum=protocol.expected(), expected_realized=None, actual=counts,
                 rows=[], updates=[], initial_assets=[], final_assets=[], calibrations=[], evaluations=[],
                 costs={}, admission=dict(admission or {}), start_utc=datetime.now(timezone.utc).isoformat(),
                 runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                              device="cpu", actor_dtype="float32", density_dtype="float64", host=platform.node(),
                              torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                              thread_environment={k: os.environ.get(k) for k in
                                                  ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="entry through summary preparation including imports for run.py, construction, resets, "
                              "collection, updates, shadows, checks, asset/raw writes and previous progress/summary writes; "
                              "final self-report write excluded; engineering and reader are additional")
    env, actor, critic, actor_optimizer, critic_optimizer = None, None, None, None, None
    inflight = {}

    def publish(full=True):
        batch["worker_wall_seconds"] = time.perf_counter() - start_wall
        batch["worker_cpu_seconds"] = time.process_time() - start_cpu
        batch["worker_max_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        if full:
            write_json(out / "summary.json", batch)
        write_json(out / "progress.json", {k: batch.get(k) for k in
                                          ("state", "actual", "progress", "worker_wall_seconds", "worker_cpu_seconds")})

    def collect(**kwargs):
        row, rollout = collect_episode(env, protocol=protocol, out=out, counts=counts, inflight=inflight, **kwargs)
        batch["rows"].append(row)
        batch["progress"] = {k: row[k] for k in ("lineage", "kind", "arm", "world", "group")}
        publish(full=False)
        return row, rollout

    def save_final(lineage, initial_sha, critic_initial, groups):
        payload = checkpoint(actor)
        payload.update(endpoint="R", launch_sha=launch_sha, lineage=lineage, initial_sha256=initial_sha,
                       optimizer_steps=len(groups) * 4, protocol=protocol.to_dict(),
                       critic_initial_state=critic_initial, critic_state=state_copy(critic),
                       actor_optimizer=copy.deepcopy(actor_optimizer.state_dict()),
                       critic_optimizer=copy.deepcopy(critic_optimizer.state_dict()), groups=groups)
        path = out / "assets" / f"R{lineage}.pt"
        if path.exists():
            raise FileExistsError("a final endpoint is already present")
        torch.save(payload, path)
        record = file_identity(path)
        record.update(path=str(path.relative_to(out)), lineage=lineage, state_sha256=payload["state_sha256"],
                      initial_sha256=initial_sha, critic_initial_sha256=state_digest(critic_initial),
                      critic_final_sha256=state_digest(critic.state_dict()), optimizer_steps=payload["optimizer_steps"])
        batch["final_assets"].append(record)
        return copy.deepcopy(actor).eval()

    try:
        batch["sources"] = source_identities(ROOT)
        initial_models, batch["initial_assets"] = load_initial_assets(protocol, bindings=bindings, permit_fixture=fixture)
        write_json(out / "config.json", {k: batch[k] for k in
                                        ("object", "launch_sha", "scientific_execution", "protocol", "expected_maximum",
                                         "sources", "initial_assets", "runtime")})
        publish()
        counts["constructor_calls"] += 1
        env = factory(protocol.training_worlds[0][0])
        counts["constructors"] += 1
        counts["constructor_resets"] += 1
        final_models = []
        for lineage in range(2):
            actor = copy.deepcopy(initial_models[lineage]).eval()
            critic = fresh_critic(protocol.critic_seeds[lineage]).eval()
            actor_optimizer, critic_optimizer = make_optimizers(actor, critic)
            actor_initial, critic_initial = state_copy(actor), state_copy(critic)
            if actor_optimizer.state or critic_optimizer.state:
                raise AssertionError("continuation must start with two fresh optimizers")
            lineage_record = dict(lineage=lineage, initial_sha256=state_digest(actor_initial),
                                  critic_initial_sha256=state_digest(critic_initial), groups=[],
                                  initial_actor_optimizer_entries=0, initial_critic_optimizer_entries=0)
            batch["updates"].append(lineage_record)
            counts["fits_started"] += 1
            publish()
            worlds = protocol.training_worlds[lineage]
            for first in range(0, len(worlds), 2):
                group = first // 2
                before_actor, before_critic = state_digest(actor.state_dict()), state_digest(critic.state_dict())
                rollout = []
                for world in worlds[first:first + 2]:
                    _, data = collect(lineage=lineage, kind="training", arm="R", candidate="S_T1", world=world,
                                      sampling_root=protocol.training_roots[lineage], actor=actor, actor_sha=before_actor,
                                      critic=critic, group=group)
                    rollout.append(data)
                batch["progress"] = dict(lineage=lineage, stage="update", group=group)
                publish(full=False)
                wall, cpu = time.perf_counter(), time.process_time()
                record = dict(group=group, worlds=list(worlds[first:first + 2]), actor_before_sha=before_actor,
                              critic_before_sha=before_critic, status="INCOMPLETE")
                lineage_record["groups"].append(record)
                try:
                    update_group(actor, critic, actor_optimizer, critic_optimizer, rollout, counts,
                                 horizon=protocol.horizon, live_record=record)
                finally:
                    record.update(actor_after_sha=state_digest(actor.state_dict()),
                                  critic_after_sha=state_digest(critic.state_dict()),
                                  wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu)
                actor.eval(); critic.eval()
                publish(full=(group + 1) % 16 == 0)
            final_models.append(save_final(lineage, lineage_record["initial_sha256"], critic_initial,
                                           lineage_record["groups"]))
            lineage_record.update(actor_movement=movement(actor_initial, state_copy(actor)),
                                  critic_movement=movement(critic_initial, state_copy(critic)),
                                  final_sha256=state_digest(actor.state_dict()),
                                  critic_final_sha256=state_digest(critic.state_dict()))
            counts["fits_completed"] += 1
            verify_initial_assets(initial_models, batch["initial_assets"])
            publish()
        # Both training lineages finish before either untouched final panel exists.
        for lineage in range(2):
            counts["calibrations_started"] += 1
            for wi, world in enumerate(protocol.calibration_worlds(lineage)):
                rotation = wi % len(CANDIDATES)
                for candidate in CANDIDATES[rotation:] + CANDIDATES[:rotation]:
                    student = candidate_spec(candidate)["family"] == "S"
                    collect(lineage=lineage, kind="calibration", arm=candidate, candidate=candidate, world=world,
                            sampling_root=protocol.calibration_roots[lineage],
                            actor=initial_models[lineage] if student else None,
                            actor_sha=batch["initial_assets"][lineage]["state_sha256"] if student else None)
                if (wi + 1) % 8 == 0:
                    publish()
            batch["calibrations"].append(calibration_result(batch["rows"], lineage, protocol))
            counts["calibrations_completed"] += 1
            verify_initial_assets(initial_models, batch["initial_assets"])
            publish()
        plans = []
        for lineage in range(2):
            plan, reference = evaluation_plan(batch["calibrations"][lineage]["winner"],
                                               batch["initial_assets"][lineage]["state_sha256"],
                                               batch["final_assets"][lineage]["state_sha256"],
                                               protocol.evaluation_roots[lineage])
            plans.append(plan)
            batch["evaluations"].append(reference)
        batch["expected_realized"] = protocol.expected(tuple(not e["reused"] for e in batch["evaluations"]))
        publish()
        for lineage in range(2):
            plan = plans[lineage]
            for wi, world in enumerate(protocol.evaluation_worlds[lineage]):
                rotation = wi % len(plan)
                for arm, candidate, sha in plan[rotation:] + plan[:rotation]:
                    student = candidate_spec(candidate)["family"] == "S"
                    collect(lineage=lineage, kind="evaluation", arm=arm, candidate=candidate, world=world,
                            sampling_root=protocol.evaluation_roots[lineage], actor_sha=sha,
                            actor=(final_models[lineage] if arm == "R" else initial_models[lineage]) if student else None,
                            shadow_actor=initial_models[lineage] if arm == "R" else None,
                            shadow_sha=batch["initial_assets"][lineage]["state_sha256"] if arm == "R" else None)
                if (wi + 1) % 8 == 0:
                    publish()
        batch["costs"] = cost_totals(batch["rows"], counts)
        validate_counts(batch, protocol)
        batch["comparisons"] = comparisons(batch["rows"], protocol, batch["evaluations"])
        verify_initial_assets(initial_models, batch["initial_assets"])
        if source_identities(ROOT) != batch["sources"]:
            raise RuntimeError("source identity changed during execution")
        batch["state"] = batch["status"] = "COMPLETE"
        batch["finish_utc"] = datetime.now(timezone.utc).isoformat()
    except BaseException as error:
        batch["failure"] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        cost_rows = list(batch["rows"])
        if inflight:
            partial = {k: v for k, v in inflight.items() if k not in ("policy_agents", "times")}
            partial.update(policy_counts=sum_counts(inflight["policy_agents"]), **inflight["times"])
            batch["partial_episode"] = partial
            cost_rows.append(partial)
        batch["costs"] = cost_totals(cost_rows, counts)
        batch["costs"].update(incomplete=True, interrupted_call_work_may_be_unmeasured=True)
        if actor is not None and critic is not None:
            path = out / "assets" / "interrupted_training_state.pt"
            try:
                torch.save(dict(actor_state=state_copy(actor), critic_state=state_copy(critic),
                                actor_optimizer=actor_optimizer.state_dict(), critic_optimizer=critic_optimizer.state_dict(),
                                progress=batch.get("progress"), actual=counts), path)
                record = file_identity(path); record["path"] = str(path.relative_to(out))
                batch["interrupted_training_state"] = record
            except BaseException as save_error:
                batch["interrupted_state_save_error"] = repr(save_error)
        publish()
        raise
    finally:
        if env is not None and hasattr(env, "close"):
            env.close()
    publish()
    return batch
