"""One admitted target construction, two fixed fits, and the fixed final panel."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import torch
import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.model import state_copy, state_digest, movement
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN as OLD_PROTOCOL
from experiments.candidates.uav_fleet_adaptation.b06_count_development.environment import make_real
from experiments.candidates.uav_fleet_adaptation.b06_count_development.model import make_inherited, make_optimizer, checkpoint
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import verify_inputs, load_actors, load_dataset
from .collect import collect_episode
from .contract import FITS, FROZEN, INPUT_ROOT, INPUT_MANIFEST_SHA256, NEURAL, OBJECT, new_counts, source_identities
from .data import prepare_targets
from .reading import comparisons
from .training import train_phase


ROOT = Path(__file__).resolve().parents[4]


def artifact(path, root):
    result = file_identity(path)
    result["path"] = str(path.relative_to(root))
    return result


def costs(rows, counts, inflight=None):
    full_c = sum_counts(r["policy_counts"] for r in rows if r["arm"] not in NEURAL)
    helper = sum_counts(r["policy_counts"] for r in rows if r["arm"] in NEURAL)
    pending = sum_counts(inflight.get("policy_agents", [])) if inflight else {}
    if pending:
        if inflight["arm"] in NEURAL:
            helper = sum_counts((helper, pending))
        else:
            full_c = sum_counts((full_c, pending))
    links = sum(full_c.get(k, 0) + helper.get(k, 0) for k in
                ("candidate_links", "setup_links", "helper_setup_links", "helper_extreme_links"))
    return dict(full_C_programs=full_c, helper_programs=helper,
                deployed_neural_rows=full_c.get("neural_rows", 0) + helper.get("neural_rows", 0),
                parent_target_neural_rows=counts["parent_target_forwards"],
                outside_fit_neural_rows=counts["parent_target_forwards"] + full_c.get("neural_rows", 0) + helper.get("neural_rows", 0),
                fit_forward_rows=counts["sample_presentations"], controller_power_links=links,
                native_dense_slots=counts["native_dense_slots"],
                total_modeled_power_links=links + counts["native_dense_slots"],
                target_vectors=counts["target_rows"] + full_c.get("target_vectors", 0),
                scope="Actual cached work; requested rows also retained. Native dense slots count constructor/reset/layout/steps. "
                      "Optimizer presentations separate. Direct T/H reuse C features; no redundant helper charged.")


def validate_counts(actual, cost, protocol=FROZEN):
    expected = protocol.expected()
    for key in ("optimizer_steps", "sample_presentations", "parent_target_forwards", "target_rows",
                "constructor_resets", "explicit_resets", "layout_refreshes", "native_steps", "native_uav_ticks",
                "native_dense_slots", "evaluation_episodes", "policy_decisions", "sampled_draws",
                "new_acquisition_steps", "new_calibrations"):
        if type(actual[key]) is not int or actual[key] != expected[key]:
            raise AssertionError("B07 completed exposure changed: " + key)
    for key in ("fits_started", "fits_completed"):
        if actual[key] != 2:
            raise AssertionError("B07 fit count changed")
    pairs = (("constructor_calls", "constructors"), ("constructors", "constructor_resets"),
             ("explicit_reset_calls", "explicit_resets"), ("layout_refresh_calls", "layout_refreshes"),
             ("native_step_calls", "native_steps"), ("policy_query_calls", "policy_decisions"),
             ("parent_target_forward_calls", "parent_target_forwards"), ("target_vector_calls", "target_rows"))
    if any(actual[a] != actual[b] for a, b in pairs):
        raise AssertionError("incomplete counted call in completed study")
    if (cost["full_C_programs"]["requests"] != expected["full_C_requests"]
            or cost["helper_programs"]["requests"] != expected["deployed_helper_requests"]
            or cost["deployed_neural_rows"] > expected["deployed_neural_requests"]):
        raise AssertionError("final program exposure changed")


def run_batch(out, launch_sha, *, admission, entry_start=None, entry_cpu=None):
    if not admission or admission.get("sha") != launch_sha:
        raise ValueError("production requires its accepted exact source")
    protocol = FROZEN
    protocol.validate()
    wall = time.perf_counter() if entry_start is None else entry_start
    cpu = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError("scientific output exists; reconcile the accepted operation")
    for name in ("raw", "data", "assets", "diagnostics"):
        (out / name).mkdir()
    counts, inflight = new_counts(), {}
    env = current_actor = current_optimizer = None
    batch = dict(object=OBJECT, state="INCOMPLETE", launch_sha=launch_sha, scientific_execution=True,
                 admission=dict(admission), protocol=protocol.to_dict(), expected=protocol.expected(), actual=counts,
                 input_root=str(INPUT_ROOT), input_manifest_sha256=INPUT_MANIFEST_SHA256,
                 sources={}, rows=[], fits=[], checkpoints=[], costs={},
                 start_utc=datetime.now(timezone.utc).isoformat(),
                 runtime=dict(python=platform.python_version(), compiler=platform.python_compiler(),
                              numpy=np.__version__, torch=torch.__version__, host=platform.node(), device="cpu",
                              torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
                              deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                              thread_environment={k: os.environ.get(k) for k in
                                                  ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="runner entry through target construction, both fits, final panel and summaries; "
                              "complete reader follows in same accepted process; staging/support separate")

    def publish(full=False):
        batch.update(worker_wall_seconds=time.perf_counter() - wall, worker_cpu_seconds=time.process_time() - cpu,
                     worker_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out / "summary.json", batch)
        write_json(out / "progress.json", {k: batch.get(k) for k in
                                          ("state", "actual", "progress", "worker_wall_seconds", "worker_cpu_seconds")})

    def progress(value):
        batch["progress"] = value
        publish()

    try:
        batch["sources"] = source_identities(ROOT)
        manifest = verify_inputs()
        batch["staging"] = json.loads((INPUT_ROOT / "staging-receipt.json").read_text())
        if batch["staging"]["input_manifest_sha256"] != INPUT_MANIFEST_SHA256:
            raise ValueError("staging receipt binds different source metadata")
        parent_state, parent, fixed = load_actors(ROOT, manifest=manifest)
        dataset = load_dataset(manifest)
        batch["initial_state_sha256"] = state_digest(parent.state_dict())
        batch["fixed_F0_state_sha256"] = state_digest(fixed.state_dict())
        write_json(out / "config.json", {key: batch[key] for key in
                   ("object", "launch_sha", "scientific_execution", "protocol", "expected", "input_root",
                    "input_manifest_sha256", "sources", "runtime", "initial_state_sha256", "fixed_F0_state_sha256")})
        publish(full=True)
        targets, batch["targets"] = prepare_targets(parent, manifest, dataset, out, counts, progress=progress)
        publish(full=True)
        endpoints = {}
        for arm in FITS:
            fit_wall, fit_cpu = time.perf_counter(), time.process_time()
            counts["fits_started"] += 1
            actor = make_inherited(parent_state, protocol.actor_constructor_seed)
            before = state_copy(actor)
            optimizer = make_optimizer(actor, OLD_PROTOCOL)
            current_actor, current_optimizer = actor, optimizer
            records = []
            for phase, rows in enumerate(protocol.expected()["datasets"]):
                def epoch_progress(p, epoch):
                    progress(dict(kind="optimizer", arm=arm, phase=p, epoch=epoch))
                record = train_phase(actor, optimizer, dataset[0][:rows], targets[arm][:rows], phase, counts,
                                     protocol=OLD_PROTOCOL, shuffle_root=protocol.shuffle_root, progress=epoch_progress)
                records.append(record)
                path = out / "assets" / f"{arm}_phase{phase}.pt"
                if path.exists():
                    raise FileExistsError("phase checkpoint already exists")
                saved = checkpoint(actor, optimizer)
                saved.update(schema="uav_fleet_adaptation.b07.full_actor.v1", endpoint=arm, phase=phase,
                             launch_sha=launch_sha, protocol=protocol.to_dict(),
                             initial_state_sha256=batch["initial_state_sha256"],
                             input_manifest_sha256=INPUT_MANIFEST_SHA256, targets_sha256=record["targets_sha256"])
                torch.save(saved, path)
                batch["checkpoints"].append(dict(artifact(path, out), arm=arm, phase=phase,
                                                state_sha256=state_digest(actor.state_dict()),
                                                optimizer_steps=saved["optimizer_steps"], training_record=record))
                publish(full=True)
            actor.eval().requires_grad_(False)
            endpoints[arm] = actor
            batch["fits"].append(dict(arm=arm, phases=records, initial_state_sha256=state_digest(before),
                                      final_state_sha256=state_digest(actor.state_dict()),
                                      movement=movement(before, state_copy(actor)),
                                      count_branch_l2=float(torch.linalg.vector_norm(actor.count_weight.double())),
                                      count_branch_changed=int(torch.count_nonzero(actor.count_weight)),
                                      cpu_seconds=time.process_time() - fit_cpu, wall_seconds=time.perf_counter() - fit_wall,
                                      timing_scope="fresh Adam, three static target phases and checkpoint serialization; no acquisition"))
            counts["fits_completed"] += 1
            current_actor = current_optimizer = None
            publish(full=True)
        actors = dict(P0=parent, Bstar0=parent, F0=fixed, T=endpoints["T"], H=endpoints["H"],
                      Tdirect=parent, Hdirect=parent)
        identities = {arm: state_digest(actor.state_dict()) for arm, actor in actors.items()}
        counts["constructor_calls"] += 1
        env = make_real(5, protocol.environment_constructor_seed)
        counts["constructors"] += 1
        counts["constructor_resets"] += 1
        counts["native_dense_slots"] += 275
        for wi, world in enumerate(protocol.worlds):
            for arm, tape in protocol.episode_order(wi):
                row = collect_episode(env, arm=arm, world=world, tape=tape, actor=actors.get(arm),
                                      policy_sha=identities.get(arm), out=out, protocol=protocol,
                                      counts=counts, inflight=inflight)
                batch["rows"].append(row)
                progress(dict(kind="evaluation", arm=arm, world=world, tape=tape))
            publish(full=True)
        if any(state_digest(actor.state_dict()) != identities[arm] for arm, actor in actors.items()):
            raise AssertionError("frozen deployed actor mutated")
        verify_inputs()
        batch["costs"] = costs(batch["rows"], counts)
        validate_counts(counts, batch["costs"])
        batch["comparisons"] = comparisons(batch["rows"], protocol)
        batch.update(state="COMPLETE", finish_utc=datetime.now(timezone.utc).isoformat())
    except BaseException as error:
        batch.update(state="FAILED", failure=traceback.format_exc(), inflight=inflight,
                     interrupted_call_work_may_be_unmeasured=True, finish_utc=datetime.now(timezone.utc).isoformat())
        if hasattr(error, "phase_record"):
            batch["failed_phase"] = error.phase_record
        if current_actor is not None:
            path = out / "assets" / "failed_current_actor.pt"
            try:
                partial = checkpoint(current_actor, current_optimizer)
            except BaseException:
                batch["failed_checkpoint_validation"] = traceback.format_exc()
                partial = dict(state_dict=state_copy(current_actor), optimizer=current_optimizer.state_dict(),
                               incomplete_optimizer_state=True)
            torch.save(partial, path)
            batch["failed_current_actor"] = artifact(path, out)
        batch["costs"] = costs(batch["rows"], counts, inflight)
        raise
    finally:
        if env is not None:
            env.close()
        publish(full=True)
    return batch
