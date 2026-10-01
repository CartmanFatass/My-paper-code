"""One sequential four-fit purchase, with every precollection state retained."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import movement, state_copy, state_digest
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import artifact, load_raw
from experiments.candidates.uav_local_history.b01.study import file_identity, write_json
from .assets import load_parents
from .collect import add, collect_episode
from .contract import ENDPOINTS, FROZEN, OBJECT, source_identities
from .learning import ResponseHead, fresh_critic, make_optimizers, update_group
from .reading import comparisons

ROOT = Path(__file__).resolve().parents[4]


def nested_digest(value):
    """Stable value hash for optimizer ledgers, including scalar tensor steps."""
    digest = hashlib.sha256()
    def visit(item):
        if isinstance(item, torch.Tensor):
            array = item.detach().cpu().contiguous().numpy()
            digest.update(b"tensor" + str(array.dtype).encode() + repr(array.shape).encode() + array.tobytes())
        elif isinstance(item, dict):
            digest.update(b"dict")
            for key in sorted(item, key=repr):
                visit(key)
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            digest.update(type(item).__name__.encode())
            for part in item:
                visit(part)
        else:
            digest.update((type(item).__name__ + ":" + repr(item)).encode())
    visit(value)
    return digest.hexdigest()


def costs(rows, counts, inflight=None):
    sources = [row["policy_counts"] for row in rows]
    if inflight and inflight.get("policy_agents"):
        sources.append(sum_counts(inflight["policy_agents"]))
    policy = sum_counts(sources)
    links = sum(policy.get(key, 0) for key in
                ("candidate_links", "setup_links", "helper_setup_links", "helper_extreme_links", "moving_link_evaluations"))
    return dict(all_policy=policy, frozen_forward_rows=policy.get("neural_rows", 0),
                head_rows=policy.get("head_rows", 0), controller_power_links=links,
                native_dense_power_slots=counts.get("native_dense_power_slots", 0),
                native_unique_distance_pairs=counts.get("native_unique_distance_pairs", 0),
                raw_uncompressed_array_bytes=sum(row["raw_array_bytes"] for row in rows),
                raw_compressed_file_bytes=sum(row["raw"]["bytes"] for row in rows),
                scope="Actual episode-private cached work. V/R ingest every primitive row and have no planning cache; "
                      "H uses tracker only. Constructor radio slots are additional to episode exposure. "
                      "Optimizer/reconstruction/support work are separately counted.")


def validate_counts(actual, cost, protocol):
    expected = protocol.expected()
    exact = ("training_episodes", "evaluation_episodes", "complete_episodes", "explicit_resets", "native_steps",
             "training_native_steps", "evaluation_native_steps", "native_uav_ticks", "motion_requests", "motion_draws",
             "roster_draws", "collected_head_rows", "collected_critic_rows", "head_optimizer_steps", "critic_optimizer_steps",
             "head_replay_rows", "critic_replay_rows", "density_identity_rows", "group_states")
    for key in exact:
        if type(actual.get(key)) is not int or actual[key] != expected[key]:
            raise AssertionError("complete B09 exposure differs: " + key)
    if actual["fits_started"] != 4 or actual["fits_completed"] != 4:
        raise AssertionError("four completed response fits required")
    constructors = actual.get("constructor_resets", 0)
    if actual["native_dense_power_slots"] != expected["native_dense_power_slots"] + 275 * constructors:
        raise AssertionError("native reset/step radio count differs")
    if actual["native_unique_distance_pairs"] != 260 * (expected["native_steps"] + expected["explicit_resets"] + constructors):
        raise AssertionError("native distance count differs")
    for first, second in (("explicit_reset_calls", "explicit_resets"), ("native_step_calls", "native_steps"),
                          ("motion_request_calls", "motion_requests"), ("constructor_calls", "constructor_resets")):
        if actual.get(first, 0) != actual.get(second, 0):
            raise AssertionError("incomplete counted call: " + first)
    policy = cost["all_policy"]
    for key, reference in (("sampled_draws", "motion_draws"), ("law_evaluations", "motion_requests"),
                           ("head_rows", "collected_head_rows"), ("target_vectors", "Hdirect_target_vectors"),
                           ("score_tail_evaluations", "G_score_tail_calls"), ("tracker_ingests", "motion_tracker_ingests")):
        if policy[key] != expected[reference]:
            raise AssertionError("policy exact work differs: " + key)
    ceilings = {"neural_rows": "frozen_forward_ceiling", "helper_calls": "helper_request_ceiling",
                "trajectories": "C_path_ceiling", "model_ticks": "C_modeled_tick_ceiling",
                "pair_gates": "motion_pair_gate_ceiling", "moving_link_evaluations": "V_R_moving_link_ceiling"}
    for key, reference in ceilings.items():
        if not 0 <= policy[key] <= expected[reference]:
            raise AssertionError("cached work exceeds declared ceiling: " + key)
    if policy["candidate_links"] + policy["setup_links"] > expected["C_link_ceiling"]:
        raise AssertionError("C links exceed declared ceiling")
    if policy["helper_setup_links"] + policy["helper_extreme_links"] > expected["helper_link_ceiling"]:
        raise AssertionError("helper links exceed declared ceiling")


def _execute(out, actors, env, protocol, batch, publish):
    """Also exercised by the declared short synthetic fake-environment fixture."""
    protocol.validate()
    out = Path(out)
    counts, inflight = batch["actual"], batch["inflight"]
    parent_hashes = {name: state_digest(actor.state_dict()) for name, actor in actors.items()}
    batch["initial_parent_states"] = parent_hashes
    endpoints = {}
    live = {}
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as stream:
        def collect(**kwargs):
            row, rollout = collect_episode(env, actors=actors, protocol=protocol, out=out, counts=counts,
                                           inflight=inflight, **kwargs)
            batch["rows"].append(row)
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            batch["progress"] = {key: row[key] for key in ("kind", "ego", "panel", "world", "tape", "group")}
            publish()
            return row, rollout

        try:
            for block, kind in protocol.fit_order():
                ego = kind + str(block)
                head, critic = ResponseHead().eval(), fresh_critic(protocol.critic_seeds[block]).eval()
                head_opt, critic_opt = make_optimizers(head, critic)
                live = dict(head=head, critic=critic, head_optimizer=head_opt, critic_optimizer=critic_opt)
                initial_head, initial_critic = state_copy(head), state_copy(critic)
                if head_opt.state or critic_opt.state:
                    raise AssertionError("fresh independent optimizers required")
                fit = dict(ego=ego, block=block, kind=kind, status="INCOMPLETE", groups=[],
                           initial_head_sha256=state_digest(initial_head), initial_critic_sha256=state_digest(initial_critic),
                           initial_head_optimizer_sha256=nested_digest(head_opt.state_dict()),
                           initial_critic_optimizer_sha256=nested_digest(critic_opt.state_dict()))
                batch["fits"].append(fit)
                add(counts, "fits_started")
                fit_wall, fit_cpu = time.perf_counter(), time.process_time()
                worlds = protocol.training_worlds[block]
                for first in range(0, len(worlds), 2):
                    group = first // 2
                    before_head, before_critic = state_digest(head.state_dict()), state_digest(critic.state_dict())
                    record = dict(group=group, worlds=list(worlds[first:first + 2]), status="COLLECTING",
                                  head_before_sha256=before_head, critic_before_sha256=before_critic,
                                  head_optimizer_before_sha256=nested_digest(head_opt.state_dict()),
                                  critic_optimizer_before_sha256=nested_digest(critic_opt.state_dict()))
                    path = out / "assets" / f"{ego}_group{group:03d}.pt"
                    if path.exists():
                        raise FileExistsError("precollection state already exists")
                    payload = dict(ego=ego, block=block, group=group, launch_sha=batch.get("launch_sha"),
                                   head_state=state_copy(head), critic_state=state_copy(critic),
                                   head_sha256=before_head, critic_sha256=before_critic)
                    torch.save(payload, path)
                    record["precollection_state"] = artifact(path, out)
                    add(counts, "group_states")
                    fit["groups"].append(record)
                    rollouts = []
                    for world in worlds[first:first + 2]:
                        _, rollout = collect(ego=ego, panel="T", world=world, tape=0, head=head, critic=critic,
                                             block=block, group=group, policy_sha=before_head)
                        rollouts.append(rollout)
                    if group == 0 and any(not np.array_equal(rollout["logits"], rollout["base_logits"]) for rollout in rollouts):
                        raise AssertionError("zero initialization must exactly reproduce the original P0 logits/law")
                    batch["progress"] = dict(kind="update", ego=ego, group=group)
                    update_wall, update_cpu = time.perf_counter(), time.process_time()
                    try:
                        update_group(head, critic, head_opt, critic_opt, rollouts, counts,
                                     horizon=protocol.horizon, live_record=record)
                    finally:
                        record.update(head_after_sha256=state_digest(head.state_dict()),
                                      critic_after_sha256=state_digest(critic.state_dict()),
                                      head_optimizer_after_sha256=nested_digest(head_opt.state_dict()),
                                      critic_optimizer_after_sha256=nested_digest(critic_opt.state_dict()),
                                      wall_seconds=time.perf_counter() - update_wall, cpu_seconds=time.process_time() - update_cpu)
                    head.eval()
                    critic.eval()
                    publish(full=(group + 1) % 16 == 0)
                final = dict(ego=ego, block=block, launch_sha=batch.get("launch_sha"),
                             head_state=state_copy(head), critic_state=state_copy(critic),
                             head_sha256=state_digest(head.state_dict()), critic_sha256=state_digest(critic.state_dict()),
                             head_optimizer=copy.deepcopy(head_opt.state_dict()), critic_optimizer=copy.deepcopy(critic_opt.state_dict()))
                path = out / "assets" / (ego + ".pt")
                if path.exists():
                    raise FileExistsError("endpoint already exists")
                torch.save(final, path)
                fit.update(status="COMPLETE", endpoint=artifact(path, out), final_head_sha256=final["head_sha256"],
                           final_critic_sha256=final["critic_sha256"], head_movement=movement(initial_head, final["head_state"]),
                           critic_movement=movement(initial_critic, final["critic_state"]),
                           wall_seconds=time.perf_counter() - fit_wall, cpu_seconds=time.process_time() - fit_cpu)
                endpoints[ego] = copy.deepcopy(head).eval()
                add(counts, "fits_completed")
                publish(full=True)
            for wi, world in enumerate(protocol.worlds):
                for ego, panel, tape in protocol.episode_order(wi):
                    head = endpoints.get(ego)
                    collect(ego=ego, panel=panel, world=world, tape=tape, head=head,
                            policy_sha=state_digest(head.state_dict()) if head is not None else None)
                publish(full=True)
        except BaseException:
            if live:
                try:
                    path = out / "assets" / "interrupted_training.pt"
                    torch.save(dict(head_state=state_copy(live["head"]), critic_state=state_copy(live["critic"]),
                                    head_optimizer=live["head_optimizer"].state_dict(),
                                    critic_optimizer=live["critic_optimizer"].state_dict(), progress=batch.get("progress"),
                                    actual=counts), path)
                    batch["interrupted_training"] = artifact(path, out)
                except BaseException as error:
                    batch["interrupted_training_save_error"] = repr(error)
            raise
    batch["episode_log"] = artifact(out / "episodes.jsonl", out)
    final_parent_hashes = {name: state_digest(actor.state_dict()) for name, actor in actors.items()}
    if final_parent_hashes != parent_hashes:
        raise AssertionError("immutable parent weights changed")
    batch["final_parent_states"] = final_parent_hashes
    batch["costs"] = costs(batch["rows"], counts)
    validate_counts(counts, batch["costs"], protocol)
    batch["comparisons"] = comparisons(batch["rows"], protocol)


def run_batch(out, launch_sha, *, admission, parent_paths, entry_start=None, entry_cpu=None):
    if not admission or admission.get("sha") != launch_sha:
        raise ValueError("production requires accepted exact-source admission")
    protocol = FROZEN
    wall = time.perf_counter() if entry_start is None else entry_start
    cpu = time.process_time() if entry_cpu is None else entry_cpu
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    allowed = {"launch-status.json", "launch-manifest.json", "admission-preflight.json", "stdout.log", "stderr.log"}
    if any(path.name not in allowed for path in out.iterdir()):
        raise FileExistsError("scientific output exists; reconcile accepted operation")
    for name in ("raw", "assets"):
        (out / name).mkdir()
    counts = {key: 0 for key in ("fits_started", "fits_completed", "constructor_calls", "constructor_resets",
                                 "native_dense_power_slots", "native_unique_distance_pairs")}
    batch = dict(object=OBJECT, state="INCOMPLETE", scientific_execution=True, launch_sha=launch_sha,
                 admission=dict(admission), protocol=protocol.to_dict(), expected=protocol.expected(), actual=counts,
                 start_utc=datetime.now(timezone.utc).isoformat(), rows=[], fits=[], inflight={}, sources={},
                 runtime=dict(python=platform.python_version(), compiler=platform.python_compiler(), numpy=np.__version__,
                              torch=str(torch.__version__), host=platform.node(), device="cpu", torch_threads=torch.get_num_threads(),
                              torch_interop_threads=torch.get_num_interop_threads(), deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
                              thread_environment={key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}),
                 timing_scope="Runner entry through sequential worker including imports, state snapshots, compression and summaries; "
                              "complete reader follows. Staging/admission/support and final self-write separate.")
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
        actors, batch["parents"] = load_parents(parent_paths)
        write_json(out / "config.json", {key: batch[key] for key in
                   ("object", "scientific_execution", "launch_sha", "protocol", "expected", "sources", "runtime", "parents")})
        publish(full=True)
        from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
        add(counts, "constructor_calls")
        env = make_real(protocol.constructor_seed)
        add(counts, "constructor_resets")
        add(counts, "native_dense_power_slots", 275)
        add(counts, "native_unique_distance_pairs", int(env.env._path_loss_cache_misses))
        fixed = dict(n_uavs=5, n_users=50, max_steps=256, max_speed=30, channel_model="free_space", min_sinr=3.,
                     max_connections=10, enable_transmitter_mask=False, max_observed_users=20, max_observed_uavs=10,
                     channel_backend="vectorized", use_shadowing=False, paper_reward=False, use_fdma=False)
        if any(getattr(env.env, key) != value for key, value in fixed.items()):
            raise AssertionError("original native host contract changed")
        batch["host"] = fixed
        _execute(out, actors, env, protocol, batch, publish)
        if source_identities(ROOT) != batch["sources"]:
            raise AssertionError("accepted source changed")
        for name, path in parent_paths.items():
            if file_identity(path)["sha256"] != batch["parents"][name]["sha256"]:
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
