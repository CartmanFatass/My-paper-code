"""Acquire both complete intervention branches, fit four heads, evaluate once."""
from datetime import datetime, timezone
from pathlib import Path
import os
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_copy, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_initial_assets, verify_initial_assets
from .collect import collect_episode
from .contract import (
    CALIBRATION_SOURCE, FROZEN, HEADS, OBJECT, array_digest, evaluation_arms, new_counts, source_identities,
)
from .learning import fit_head
from .reading import acquisition_summary, comparisons, cost_totals, validate_counts


ROOT = Path(__file__).resolve().parents[4]


def _pair_context(first, second, rows, *, world, address, weight):
    for key in ("features", "hidden", "logits", "mu"):
        if not np.array_equal(first[key], second[key]):
            raise AssertionError("paired original context differs before the intervention: " + key)
    if first["nominal_action"] != second["nominal_action"] or rows[0]["initial_state_sha256"] != rows[1]["initial_state_sha256"]:
        raise AssertionError("paired original state/private proposal differs")
    return dict(features=first["features"], hidden=first["hidden"], logits=first["logits"], mu=first["mu"],
                action_a=first["action"], action_b=second["action"],
                delta_j=rows[0]["J"] - rows[1]["J"], weight=float(weight), world=int(world),
                address=int(address), J_a=rows[0]["J"], J_b=rows[1]["J"],
                uniform_a=first["uniform"], uniform_b=second["uniform"],
                nominal_action=first["nominal_action"])


def _save_dataset(out, lineage, contexts):
    data = {key: np.asarray([context[key] for context in contexts]) for key in contexts[0]}
    path = out / "data" / f"L{lineage}_pairs.npz"
    np.savez_compressed(path, **data)
    record = file_identity(path); record["path"] = str(path.relative_to(out))
    return data, dict(lineage=lineage, artifact=record,
                      data_sha256=array_digest(*(data[key] for key in sorted(data))),
                      array_keys=sorted(data), summary=acquisition_summary(data))


def _save_head(out, lineage, kind, head, optimizer, record, initial_sha, launch_sha, protocol, trace):
    path = out / "assets" / f"{kind}{lineage}.pt"
    if path.exists():
        raise FileExistsError("head endpoint already exists")
    state = state_copy(head)
    payload = dict(schema="uav_fleet_adaptation.b05.head.v1", endpoint=kind, lineage=lineage,
                   launch_sha=launch_sha, protocol=protocol.to_dict(), original_student_sha256=initial_sha,
                   state_dict=state, state_sha256=state_digest(state), optimizer=optimizer.state_dict(),
                   optimizer_steps=protocol.updates, dtype="float32", hidden_size=128, output_size=27,
                   trainable_parameters=sum(p.numel() for p in head.parameters()), training_trace=trace)
    torch.save(payload, path)
    found = file_identity(path)
    found.update(path=str(path.relative_to(out)), lineage=lineage, kind=kind, state_sha256=payload["state_sha256"],
                 original_student_sha256=initial_sha, optimizer_steps=protocol.updates,
                 trainable_parameters=payload["trainable_parameters"], training_trace=trace)
    return found


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
        raise ValueError("fixtures must be explicit nonproduction nonscientific inputs")
    started = time.perf_counter() if entry_start is None else entry_start
    cpu_started = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(p.name not in allowed for p in out.iterdir()):
        raise FileExistsError("existing scientific output; reconcile it, no retry/resume interface")
    for name in ("raw", "data", "assets"):
        (out / name).mkdir()
    counts = new_counts()
    batch = dict(object=OBJECT, state="INCOMPLETE", status="INCOMPLETE", launch_sha=launch_sha,
                 scientific_execution=scientific_invocation, protocol=protocol.to_dict(), expected=protocol.expected(),
                 actual=counts, admission=dict(admission or {}), rows=[], datasets=[], heads=[], fits=[], costs={},
                 initial_assets=[], start_utc=datetime.now(timezone.utc).isoformat(),
                 inherited_calibration=CALIBRATION_SOURCE,
                 runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                              device="cpu", actor_dtype="float32", density_dtype="float64", host=platform.node(),
                              torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                              thread_environment={k: os.environ.get(k) for k in
                                                  ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="entry through worker summary preparation, imports/init/native/fit/evaluation/shadows/serialization included; final write, reader/admission/support additional")
    env, inflight = None, {}

    def publish(full=False):
        batch.update(worker_wall_seconds=time.perf_counter() - started,
                     worker_cpu_seconds=time.process_time() - cpu_started,
                     worker_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out / "summary.json", batch)
        write_json(out / "progress.json", {key: batch.get(key) for key in
                                          ("state", "actual", "progress", "worker_wall_seconds", "worker_cpu_seconds")})

    def collect(**kwargs):
        row, context = collect_episode(env, protocol=protocol, out=out, counts=counts, inflight=inflight, **kwargs)
        batch["rows"].append(row)
        batch["progress"] = {key: row[key] for key in ("lineage", "kind", "arm", "world", "intervention")}
        publish()
        return row, context

    try:
        batch["sources"] = source_identities(ROOT)
        if not fixture:
            if file_identity(ROOT / CALIBRATION_SOURCE["reading_path"])["sha256"] != CALIBRATION_SOURCE["reading_sha256"]:
                raise ValueError("the previously paid calibration evidence changed")
        originals, batch["initial_assets"] = load_initial_assets(protocol, bindings=bindings, permit_fixture=fixture)
        write_json(out / "config.json", {key: batch[key] for key in
                                        ("object", "launch_sha", "scientific_execution", "protocol", "expected",
                                         "sources", "initial_assets", "runtime", "inherited_calibration")})
        publish(full=True)
        counts["constructor_calls"] += 1
        env = factory(protocol.acquisition_worlds[0][0])
        counts["constructors"] += 1
        counts["constructor_resets"] += 1
        endpoints = {}
        for lineage in range(2):
            original_sha = batch["initial_assets"][lineage]["state_sha256"]
            addresses, weights = protocol.addresses(lineage)
            contexts = []
            for j, world in enumerate(protocol.acquisition_worlds[lineage]):
                address = int(addresses[j])
                rows, branches = [], []
                for branch, root in (("a", protocol.intervention_a_roots[lineage]),
                                     ("b", protocol.intervention_b_roots[lineage])):
                    intervention = dict(pair_index=j, address=address, tick=4 * (address // 5),
                                        agent=address % 5, branch=branch, root=int(root), weight=float(weights[j]))
                    row, context = collect(lineage=lineage, kind="acquisition", arm="S", world=world,
                                           actor=originals[lineage], initial_sha=original_sha, intervention=intervention)
                    rows.append(row); branches.append(context)
                contexts.append(_pair_context(*branches, rows, world=world, address=address, weight=weights[j]))
                counts["acquisition_contexts"] += 1
                if (j + 1) % 64 == 0:
                    publish(full=True)
            data, dataset = _save_dataset(out, lineage, contexts)
            batch["datasets"].append(dataset)
            del contexts
            publish(full=True)
            for kind in HEADS:
                def progress(record):
                    batch["progress"] = dict(lineage=lineage, kind="fit", arm=kind,
                                             optimizer_steps=counts["head_optimizer_steps"], status=record["status"])
                    if counts["head_optimizer_steps"] % 32 == 0 or record["status"] in ("COMPLETE", "FAILED"):
                        publish()
                try:
                    head, optimizer, record = fit_head(kind, data, seed=protocol.minibatch_roots[lineage],
                                                       counts=counts, updates=protocol.updates,
                                                       batch_size=protocol.batch_size, progress=progress)
                except BaseException as error:
                    record = getattr(error, "fit_record", None)
                    if record is not None:
                        batch["interrupted_fit_record"] = record
                    interrupted_head, interrupted_optimizer = getattr(error, "fit_head", None), getattr(error, "fit_optimizer", None)
                    if interrupted_head is not None and interrupted_optimizer is not None:
                        path = out / "assets" / "interrupted_head.pt"
                        torch.save(dict(kind=kind, lineage=lineage, state_dict=state_copy(interrupted_head),
                                        optimizer=interrupted_optimizer.state_dict(), actual=dict(counts)), path)
                        found = file_identity(path); found["path"] = str(path.relative_to(out))
                        batch["interrupted_head"] = found
                    raise
                head.eval()
                trace_path = out / "data" / f"{kind}{lineage}_updates.json"
                write_json(trace_path, record)
                trace = file_identity(trace_path); trace["path"] = str(trace_path.relative_to(out))
                head_record = _save_head(out, lineage, kind, head, optimizer, record, original_sha,
                                         launch_sha, protocol, trace)
                batch["heads"].append(head_record)
                batch["fits"].append(dict(lineage=lineage, kind=kind, seed=protocol.minibatch_roots[lineage], trace=trace))
                endpoints[lineage, kind] = (head, head_record["state_sha256"])
                verify_initial_assets(originals, batch["initial_assets"])
                publish(full=True)
            del data
        # No final world is collected until both lineages and all four fits finish.
        for lineage in range(2):
            arms = evaluation_arms(lineage)
            original_sha = batch["initial_assets"][lineage]["state_sha256"]
            for wi, world in enumerate(protocol.evaluation_worlds[lineage]):
                rotation = wi % len(arms)
                for arm in arms[rotation:] + arms[:rotation]:
                    head, head_sha = endpoints.get((lineage, arm), (None, None))
                    collect(lineage=lineage, kind="evaluation", arm=arm, world=world,
                            actor=None if arm in ("C", "Q") else originals[lineage],
                            initial_sha=None if arm in ("C", "Q") else original_sha, head=head, head_sha=head_sha)
                if (wi + 1) % 8 == 0:
                    publish(full=True)
        batch["costs"] = cost_totals(batch["rows"], counts)
        validate_counts(batch, protocol)
        batch["comparisons"] = comparisons(batch["rows"], protocol)
        verify_initial_assets(originals, batch["initial_assets"])
        if source_identities(ROOT) != batch["sources"]:
            raise RuntimeError("source identity changed during execution")
        batch["state"] = batch["status"] = "COMPLETE"
        batch["finish_utc"] = datetime.now(timezone.utc).isoformat()
    except BaseException as error:
        batch["failure"] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        paid_rows = list(batch["rows"])
        if inflight:
            partial = {key: value for key, value in inflight.items() if key not in ("policy_agents", "times")}
            partial.update(policy_counts=sum_counts(inflight["policy_agents"]), **inflight["times"])
            batch["partial_episode"] = partial
            paid_rows.append(partial)
        batch["costs"] = cost_totals(paid_rows, counts)
        batch["costs"].update(incomplete=True, interrupted_call_work_may_be_unmeasured=True)
        publish(full=True)
        raise
    finally:
        if env is not None and hasattr(env, "close"):
            env.close()
    publish(full=True)
    return batch
