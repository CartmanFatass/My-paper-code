"""One fixed four-fit producer, shared final panel and retained adverse/failed work."""
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_copy, state_digest, movement
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_initial_assets, verify_initial_assets
from .collect import collect_episode
from .contract import CALIBRATION_SOURCE, COUNTS, FINAL_COUNTS, FITS, FROZEN, OBJECT, array_digest, new_counts, source_identities
from .environment import make_real
from .model import checkpoint, make_inherited, make_optimizer, train_phase
from .reading import comparisons, cost_totals, validate_counts

ROOT = Path(__file__).resolve().parents[4]


def _artifact(path, out):
    record = file_identity(path)
    record["path"] = str(path.relative_to(out))
    return record


def _save_phase(out, lineage, arm, phase, actor, optimizer, launch_sha, protocol, initial_sha, record):
    path = out / "assets" / f"{arm}{lineage}_phase{phase}.pt"
    if path.exists():
        raise FileExistsError("phase checkpoint exists")
    saved = checkpoint(actor, optimizer)
    saved.update(schema="uav_fleet_adaptation.b06.full_actor.v1", endpoint=arm, lineage=lineage,
                 phase=phase, launch_sha=launch_sha, protocol=protocol.to_dict(), original_state_sha256=initial_sha,
                 optimizer_steps=sum(protocol.expected()["phase_updates"][:phase + 1]))
    torch.save(saved, path)
    return dict(_artifact(path, out), lineage=lineage, arm=arm, phase=phase,
                state_sha256=state_digest(actor.state_dict()), optimizer_steps=saved["optimizer_steps"],
                training_record=record)


def run_batch(out, launch_sha, *, admission, entry_start=None, entry_cpu=None):
    protocol = FROZEN
    if not admission or admission.get("sha") != launch_sha:
        raise ValueError("production requires the accepted exact source")
    started = time.perf_counter() if entry_start is None else entry_start
    cpu_started = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(p.name not in allowed for p in out.iterdir()):
        raise FileExistsError("scientific output already exists; reconcile, do not retry")
    for name in ("raw", "data", "assets"):
        (out / name).mkdir()
    counts, envs, inflight = new_counts(), {}, {}
    current_actor = current_optimizer = None
    batch = dict(object=OBJECT, state="INCOMPLETE", launch_sha=launch_sha, scientific_execution=True,
                 protocol=protocol.to_dict(), expected=protocol.expected(), actual=counts,
                 admission=dict(admission), sources={}, initial_assets=[], rows=[], datasets=[],
                 checkpoints=[], fits=[], costs={}, fixture_saved_checks={},
                 start_utc=datetime.now(timezone.utc).isoformat(),
                 inherited_calibration=CALIBRATION_SOURCE,
                 runtime=dict(python=platform.python_version(), numpy=np.__version__, torch=torch.__version__,
                              host=platform.node(), device="cpu", actor_dtype="float32", density_dtype="float64",
                              torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                              thread_environment={k: os.environ.get(k) for k in
                                                  ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="runner entry through producer, including imports, constructors, native correctness fixture, acquisition, fitting, final collection and serialization; reader/support additional")

    def publish(full=False):
        batch.update(worker_wall_seconds=time.perf_counter() - started,
                     worker_cpu_seconds=time.process_time() - cpu_started,
                     worker_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out / "summary.json", batch)
        write_json(out / "progress.json", {k: batch.get(k) for k in
                                          ("state", "actual", "progress", "worker_wall_seconds", "worker_cpu_seconds")})

    def collect(**kwargs):
        row, cases = collect_episode(envs[kwargs["n"]], protocol=protocol, out=out, counts=counts,
                                     inflight=inflight, **kwargs)
        batch["rows"].append(row)
        batch["progress"] = {key: row[key] for key in ("kind", "lineage", "arm", "n", "world", "phase", "tape")}
        publish()
        return row, cases

    try:
        batch["sources"] = source_identities(ROOT)
        if file_identity(ROOT / CALIBRATION_SOURCE["reading_path"])["sha256"] != CALIBRATION_SOURCE["reading_sha256"]:
            raise ValueError("paid calibration source changed")
        original_states, originals, batch["initial_assets"] = load_initial_assets()
        original_generalized_sha = [state_digest(m.state_dict()) for m in originals]
        write_json(out / "config.json", {key: batch[key] for key in
                                        ("object", "launch_sha", "scientific_execution", "protocol", "expected",
                                         "sources", "initial_assets", "runtime", "inherited_calibration")})
        publish(full=True)
        for n, seed in zip(COUNTS, protocol.environment_constructor_seeds):
            counts["constructor_calls"] += 1
            envs[n] = make_real(n, seed)
            counts["constructors"] += 1
            counts["constructor_resets"] += 1
            counts["native_dense_slots"] += n * (50 + n)
        for n in COUNTS:
            row, _ = collect(arm="C", lineage=None, kind="fixture", world=protocol.fixture_world, n=n)
            from .audit import check_episode
            with np.load(out / row["raw"]["path"], allow_pickle=False) as archive:
                batch["fixture_saved_checks"][str(n)] = check_episode(dict(archive), row, protocol)
        fixture_rows = [r for r in batch["rows"] if r["kind"] == "fixture"]
        if len({r["shared_layout_sha256"] for r in fixture_rows}) != 1:
            raise AssertionError("native correctness fixture lacks one nested cross-count layout")
        endpoints = {}
        for lineage in (0, 1):
            initial_sha = batch["initial_assets"][lineage]["state_sha256"]
            for arm in FITS:
                fit_wall, fit_cpu = time.perf_counter(), time.process_time()
                counts["fits_started"] += 1
                actor = make_inherited(original_states[lineage], protocol.actor_constructor_seeds[lineage]).eval()
                before = state_copy(actor)
                optimizer = make_optimizer(actor, protocol)
                current_actor, current_optimizer = actor, optimizer
                chunks, records = [], []
                for phase in range(3):
                    new_chunks = []
                    actor_sha = state_digest(actor.state_dict())
                    for j, world in enumerate(protocol.phase_worlds(lineage, phase)):
                        n = protocol.acquisition_count(arm, j)
                        _, cases = collect(arm=arm, lineage=lineage, kind="acquisition", world=world, n=n,
                                           phase=phase, actor=None if phase == 0 else actor,
                                           policy_sha=None if phase == 0 else actor_sha)
                        new_chunks.append(cases)
                    phase_data = tuple(np.concatenate([case[i] for case in new_chunks], axis=0) for i in range(3))
                    path = out / "data" / f"{arm}{lineage}_phase{phase}.npz"
                    np.savez_compressed(path, features=phase_data[0], labels=phase_data[1], fleet_counts=phase_data[2])
                    batch["datasets"].append(dict(lineage=lineage, arm=arm, phase=phase, artifact=_artifact(path, out),
                                                  rows=len(phase_data[1]), data_sha256=array_digest(*phase_data)))
                    chunks.append(phase_data)
                    del new_chunks
                    accumulated = tuple(np.concatenate([case[i] for case in chunks], axis=0) for i in range(3))

                    def progress(p, epoch):
                        batch["progress"] = dict(kind="optimizer", lineage=lineage, arm=arm, phase=p, epoch=epoch)
                        publish()

                    record = train_phase(actor, optimizer, *accumulated, phase, protocol, counts,
                                         protocol.shuffle_roots[lineage], progress=progress)
                    records.append(record)
                    artifact = _save_phase(out, lineage, arm, phase, actor, optimizer, launch_sha,
                                           protocol, initial_sha, record)
                    batch["checkpoints"].append(artifact)
                    publish(full=True)
                    del accumulated
                if arm == "F" and torch.count_nonzero(actor.count_weight).item() != 0:
                    raise AssertionError("N5-only branch moved despite zero input and zero decay")
                endpoints[lineage, arm] = actor.eval()
                batch["fits"].append(dict(lineage=lineage, arm=arm, phases=records,
                                          original_state_sha256=initial_sha,
                                          generalized_initial_sha256=state_digest(before),
                                          final_state_sha256=state_digest(actor.state_dict()),
                                          movement=movement(before, state_copy(actor)),
                                          count_branch_l2=float(torch.linalg.vector_norm(actor.count_weight.double())),
                                          count_branch_changed=int(torch.count_nonzero(actor.count_weight)),
                                          wall_seconds=time.perf_counter() - fit_wall,
                                          cpu_seconds=time.process_time() - fit_cpu,
                                          timing_scope="complete fit including its acquisition, dataset writing and three optimizer phases"))
                counts["fits_completed"] += 1
                publish(full=True)
                del chunks, optimizer
                current_actor = current_optimizer = None
        for n in FINAL_COUNTS:
            for world in protocol.evaluation_worlds:
                collect(arm="C", lineage=None, kind="evaluation", world=world, n=n)
                for tape in (0, 1):
                    collect(arm="Q", lineage=None, kind="evaluation", world=world, n=n, tape=tape)
                for lineage in (0, 1):
                    for arm in ("P", "F", "M", *(("Bstar",) if lineage == 0 else ())):
                        actor = originals[lineage] if arm in ("P", "Bstar") else endpoints[lineage, arm]
                        for tape in (0, 1):
                            collect(arm=arm, lineage=lineage, kind="evaluation", world=world, n=n,
                                    tape=tape, actor=actor, policy_sha=state_digest(actor.state_dict()))
        for model, expected in zip(originals, original_generalized_sha):
            if state_digest(model.state_dict()) != expected:
                raise AssertionError("fixed original parameter program mutated")
        verify_initial_assets()
        batch["costs"] = cost_totals(batch["rows"])
        validate_counts(counts, batch["costs"], protocol)
        batch["comparisons"] = comparisons(batch["rows"], protocol)
        batch.update(state="COMPLETE", finish_utc=datetime.now(timezone.utc).isoformat())
    except BaseException as error:
        batch["failure"] = traceback.format_exc()
        batch["inflight"] = inflight
        if hasattr(error, "phase_record"):
            batch["failed_phase"] = error.phase_record
        if current_actor is not None:
            failed_path = out / "assets" / "failed_current_actor.pt"
            try:
                partial_checkpoint = checkpoint(current_actor, current_optimizer)
            except BaseException:
                # Preserve a partial Adam step even when it fails normal checkpoint
                # consistency checks; never conceal the original training error.
                batch["failed_checkpoint_validation"] = traceback.format_exc()
                partial_checkpoint = dict(state_dict=state_copy(current_actor),
                                          optimizer=current_optimizer.state_dict(),
                                          incomplete_optimizer_state=True)
            torch.save(partial_checkpoint, failed_path)
            batch["failed_current_actor"] = _artifact(failed_path, out)
        batch["costs"] = cost_totals(batch["rows"], inflight=inflight)
        batch.update(state="FAILED", finish_utc=datetime.now(timezone.utc).isoformat())
        raise
    finally:
        for env in envs.values():
            env.close()
        publish(full=True)
    return batch
