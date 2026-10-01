"""One sequential two-fit purchase and fixed complete evaluation panel."""
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_assets
from .collect import collect_episode
from .contract import ENDPOINTS, FROZEN, OBJECT, source_identities
from .learning import JointActor, fresh_critic, make_optimizers, update_group
from .reading import comparisons
from .records import add, artifact, movement, nested_digest, state_copy

ROOT = Path(__file__).resolve().parents[4]


def costs(rows, counts, inflight=None):
    sources = [row["policy_counts"] for row in rows]
    if inflight and inflight.get("policy_agents"):
        sources.append(sum_counts(inflight["policy_agents"]))
    policy = sum_counts(sources)
    links = sum(policy.get(key, 0) for key in ("candidate_links", "setup_links", "helper_setup_links",
                                              "helper_extreme_links", "off_setup_links"))
    return dict(all_policy=policy, frozen_forward_rows=policy.get("neural_rows", 0) + policy.get("frozen_neural_rows", 0),
                joint_forward_rows=policy.get("joint_neural_rows", 0), controller_power_links=links,
                native_dense_power_slots=counts.get("native_dense_power_slots", 0),
                native_unique_distance_pairs=counts.get("native_unique_distance_pairs", 0),
                raw_uncompressed_array_bytes=sum(row["raw_array_bytes"] for row in rows),
                raw_compressed_file_bytes=sum(row["raw"]["bytes"] for row in rows),
                scope="Actual private episode/model-version caches; CJ eligible setup is repeated and charged. "
                      "Environment constructor radio slots included; optimizer, full reader and support separately counted.")


def validate_counts(actual, cost, protocol):
    expected = protocol.expected()
    exact = ("training_episodes", "evaluation_episodes", "complete_episodes", "explicit_resets", "native_steps",
             "training_native_steps", "evaluation_native_steps", "native_uav_ticks", "motion_requests", "motion_draws",
             "gate_opportunities", "gate_draws", "mask_installs", "mask_refresh_dense_sinr_slots", "collected_actor_rows",
             "collected_critic_rows", "actor_optimizer_steps", "critic_optimizer_steps", "actor_replay_rows",
             "critic_replay_rows", "density_identity_rows", "group_states", "constructor_resets",
             "native_dense_power_slots", "native_unique_distance_pairs")
    for key in exact:
        if type(actual.get(key)) is not int or actual[key] != expected[key]:
            raise AssertionError("complete B10 exposure differs: " + key)
    if actual["fits_started"] != 2 or actual["fits_completed"] != 2:
        raise AssertionError("two completed full joint fits required")
    for first, second in (("explicit_reset_calls", "explicit_resets"), ("native_step_calls", "native_steps"),
                          ("motion_request_calls", "motion_requests"), ("constructor_calls", "constructor_resets"),
                          ("gate_opportunity_calls", "gate_opportunities"), ("mask_install_calls", "mask_installs")):
        if actual.get(first, 0) != actual.get(second, 0):
            raise AssertionError("incomplete counted call: " + first)
    policy = cost["all_policy"]
    for key, reference in (("sampled_draws", "motion_draws"), ("law_evaluations", "motion_requests"),
                           ("joint_requests", "joint_collection_rows"), ("target_vectors", "Hdirect_target_vectors"),
                           ("score_tail_evaluations", "G_score_tail_calls"), ("gate_prediction_rows", "gate_prediction_rows"),
                           ("off_score_evaluations", "CJ_off_scores"), ("off_logical_ticks", "CJ_off_logical_ticks")):
        if policy[key] != expected[reference]:
            raise AssertionError("policy work differs: " + key)
    for value, reference in ((cost["frozen_forward_rows"], "frozen_forward_ceiling"),
                             (cost["joint_forward_rows"], "joint_forward_ceiling"),
                             (policy["helper_calls"], "helper_requests"), (policy["trajectories"], "C_path_ceiling"),
                             (policy["model_ticks"], "C_model_tick_ceiling"),
                             (policy["candidate_links"] + policy["setup_links"], "C_link_ceiling"),
                             (policy["helper_setup_links"] + policy["helper_extreme_links"], "helper_link_ceiling"),
                             (policy["off_setup_links"], "CJ_setup_link_ceiling"),
                             (cost["controller_power_links"], "controller_link_ceiling")):
        if not 0 <= value <= expected[reference]:
            raise AssertionError("private cached cost exceeds ceiling: " + reference)
    expected_fidelity = (4 + len(protocol.worlds) * 2) * protocol.horizon // 4
    if policy["initial_fidelity_rows"] != expected_fidelity:
        raise AssertionError("initial eligible fidelity coverage differs")


def _execute(out, parent, gate, env, protocol, batch, publish):
    protocol.validate()
    out = Path(out)
    counts, inflight = batch["actual"], batch["inflight"]
    parent_hash, gate_hash = state_digest(parent.state_dict()), nested_digest(gate)
    batch["initial_parent_state"], batch["initial_gate_state"] = parent_hash, gate_hash
    initial_actor = JointActor(parent, seed=protocol.actor_constructor_seed).eval()
    batch["initial_joint_state"] = state_digest(initial_actor.state_dict())
    endpoints, live = {}, {}
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as stream:
        def collect(**kwargs):
            row, rollout = collect_episode(env, parent=parent, gate=gate, protocol=protocol, out=out, counts=counts,
                                           inflight=inflight, **kwargs)
            batch["rows"].append(row)
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            batch["progress"] = {key: row[key] for key in ("kind", "program", "world", "tape", "group")}
            publish()
            return row, rollout
        try:
            for block, program in enumerate(ENDPOINTS):
                actor = JointActor(parent, seed=protocol.actor_constructor_seed).eval()
                critic = fresh_critic(protocol.critic_seeds[block]).eval()
                actor_opt, critic_opt = make_optimizers(actor, critic)
                live = dict(actor=actor, critic=critic, actor_optimizer=actor_opt, critic_optimizer=critic_opt)
                initial_states = {name: state_copy(model) for name, model in (("actor", actor), ("critic", critic))}
                if actor_opt.state or critic_opt.state or state_digest(actor.state_dict()) != batch["initial_joint_state"]:
                    raise AssertionError("fresh optimizer/identical original warm start required")
                fit = dict(program=program, block=block, status="INCOMPLETE", groups=[],
                           initial_actor_sha256=state_digest(initial_states["actor"]),
                           initial_critic_sha256=state_digest(initial_states["critic"]),
                           initial_actor_optimizer_sha256=nested_digest(actor_opt.state_dict()),
                           initial_critic_optimizer_sha256=nested_digest(critic_opt.state_dict()))
                batch["fits"].append(fit)
                add(counts, "fits_started")
                fit_wall, fit_cpu = time.perf_counter(), time.process_time()
                worlds = protocol.training_worlds[block]
                for first in range(0, len(worlds), 2):
                    group = first // 2
                    record = dict(group=group, worlds=list(worlds[first:first + 2]), status="COLLECTING")
                    payload = dict(program=program, block=block, group=group, launch_sha=batch.get("launch_sha"))
                    for name, model, optimizer in (("actor", actor, actor_opt), ("critic", critic, critic_opt)):
                        digest = state_digest(model.state_dict())
                        record[name + "_before_sha256"] = digest
                        record[name + "_optimizer_before_sha256"] = nested_digest(optimizer.state_dict())
                        payload[name + "_state"], payload[name + "_sha256"] = state_copy(model), digest
                    path = out / "assets" / f"{program}_group{group:03d}.pt"
                    if path.exists():
                        raise FileExistsError("precollection state already exists")
                    torch.save(payload, path)
                    record["precollection_state"] = artifact(path, out)
                    add(counts, "group_states")
                    fit["groups"].append(record)
                    rollouts = [collect(program=program, world=world, tape=None, actor=actor, critic=critic, block=block,
                                        group=group, policy_sha=record["actor_before_sha256"])[1]
                                for world in worlds[first:first + 2]]
                    batch["progress"] = dict(kind="update", program=program, group=group)
                    wall, cpu = time.perf_counter(), time.process_time()
                    try:
                        update_group(actor, critic, actor_opt, critic_opt, rollouts, counts,
                                     horizon=protocol.horizon, live_record=record)
                    finally:
                        for name, model, optimizer in (("actor", actor, actor_opt), ("critic", critic, critic_opt)):
                            record[name + "_after_sha256"] = state_digest(model.state_dict())
                            record[name + "_optimizer_after_sha256"] = nested_digest(optimizer.state_dict())
                        record.update(wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu)
                    actor.eval(); critic.eval()
                    publish(full=(group + 1) % 16 == 0)
                final = dict(program=program, block=block, launch_sha=batch.get("launch_sha"))
                for name, model, optimizer in (("actor", actor, actor_opt), ("critic", critic, critic_opt)):
                    final[name + "_state"], final[name + "_sha256"] = state_copy(model), state_digest(model.state_dict())
                    final[name + "_optimizer"] = copy.deepcopy(optimizer.state_dict())
                    fit["final_" + name + "_sha256"] = final[name + "_sha256"]
                    fit[name + "_movement"] = movement(initial_states[name], final[name + "_state"])
                path = out / "assets" / (program + ".pt")
                if path.exists():
                    raise FileExistsError("final endpoint already exists")
                torch.save(final, path)
                fit.update(status="COMPLETE", endpoint=artifact(path, out), wall_seconds=time.perf_counter() - fit_wall,
                           cpu_seconds=time.process_time() - fit_cpu)
                endpoints[program] = copy.deepcopy(actor).eval()
                add(counts, "fits_completed")
                publish(full=True)
            endpoints["INIT90"] = initial_actor
            for wi, world in enumerate(protocol.worlds):
                for program, tape in protocol.episode_order(wi):
                    actor = endpoints.get(program)
                    collect(program=program, world=world, tape=tape, actor=actor,
                            policy_sha=state_digest(actor.state_dict()) if actor is not None else None)
                publish(full=True)
        except BaseException:
            if live:
                try:
                    path = out / "assets" / "interrupted_training.pt"
                    torch.save(dict(actor_state=state_copy(live["actor"]), critic_state=state_copy(live["critic"]),
                                    actor_optimizer=live["actor_optimizer"].state_dict(),
                                    critic_optimizer=live["critic_optimizer"].state_dict(), progress=batch.get("progress"), actual=counts), path)
                    batch["interrupted_training"] = artifact(path, out)
                except BaseException as error:
                    batch["interrupted_training_save_error"] = repr(error)
            raise
    batch["episode_log"] = artifact(out / "episodes.jsonl", out)
    batch["final_parent_state"], batch["final_gate_state"] = state_digest(parent.state_dict()), nested_digest(gate)
    if (batch["final_parent_state"], batch["final_gate_state"]) != (parent_hash, gate_hash):
        raise AssertionError("original immutable parent/prior changed")
    batch["costs"] = costs(batch["rows"], counts)
    validate_counts(counts, batch["costs"], protocol)
    batch["comparisons"] = comparisons(batch["rows"], protocol)


def run_batch(out, launch_sha, *, admission, asset_paths, entry_start=None, entry_cpu=None):
    if not admission or admission.get("sha") != launch_sha:
        raise ValueError("production requires accepted exact-source admission")
    protocol = FROZEN
    wall, cpu = (time.perf_counter() if entry_start is None else entry_start), (time.process_time() if entry_cpu is None else entry_cpu)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError("scientific output exists; reconcile accepted operation")
    for name in ("raw", "assets"):
        (out / name).mkdir()
    counts = {key: 0 for key in ("fits_started", "fits_completed", "constructor_calls", "constructor_resets",
                                 "native_dense_power_slots", "native_unique_distance_pairs", "gate_draws")}
    batch = dict(object=OBJECT, state="INCOMPLETE", scientific_execution=True, launch_sha=launch_sha,
                 admission=dict(admission), protocol=protocol.to_dict(), expected=protocol.expected(), actual=counts,
                 start_utc=datetime.now(timezone.utc).isoformat(), rows=[], fits=[], inflight={}, sources={},
                 runtime=dict(python=platform.python_version(), compiler=platform.python_compiler(), numpy=np.__version__,
                              torch=str(torch.__version__), host=platform.node(), device="cpu", torch_threads=torch.get_num_threads(),
                              torch_interop_threads=torch.get_num_interop_threads(), deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                              thread_environment={key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="Runner entry through sequential worker including imports, model states, compression and summaries; "
                              "full reader follows. Staging/admission/support and final self-write separate.")
    env = None
    def publish(full=False):
        batch.update(worker_wall_seconds=time.perf_counter() - wall, worker_cpu_seconds=time.process_time() - cpu,
                     worker_max_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
        if full:
            write_json(out / "summary.json", batch)
        write_json(out / "progress.json", {key: batch.get(key) for key in
                   ("state", "actual", "progress", "worker_wall_seconds", "worker_cpu_seconds")})
    try:
        batch["sources"] = source_identities(ROOT)
        parent, gate, batch["inputs"] = load_assets(asset_paths)
        write_json(out / "config.json", {key: batch[key] for key in
                   ("object", "scientific_execution", "launch_sha", "protocol", "expected", "sources", "runtime", "inputs")})
        publish(full=True)
        from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import make_real, check_host
        add(counts, "constructor_calls")
        env = make_real(protocol.constructor_seed)
        add(counts, "constructor_resets")
        add(counts, "native_dense_power_slots", 275)
        add(counts, "native_unique_distance_pairs", int(env.env._path_loss_cache_misses))
        batch["host"] = check_host(env)
        _execute(out, parent, gate, env, protocol, batch, publish)
        if source_identities(ROOT) != batch["sources"]:
            raise AssertionError("accepted source changed")
        for name, path in asset_paths.items():
            if file_identity(path)["sha256"] != batch["inputs"][name]["sha256"]:
                raise AssertionError("consumed original asset changed")
        batch.update(state="COMPLETE", finish_utc=datetime.now(timezone.utc).isoformat())
    except BaseException:
        batch.update(state="FAILED", failure=traceback.format_exc(), finish_utc=datetime.now(timezone.utc).isoformat(),
                     interrupted_call_work_may_be_unmeasured=True)
        batch["costs"] = costs(batch["rows"], counts, batch["inflight"])
        raise
    finally:
        if env is not None:
            env.close()
        publish(full=True)
    return batch
