"""Complete, source-bound native S1 fleet transmission evaluation (no training)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
from pathlib import Path
import resource
import time
from typing import Any

import numpy as np
import torch

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.load_critical_member_generalization.load_probe import probe as frozen
from .host import FleetS1, mask_bits, runtime_seed, world
from .control import OrdinaryController, choose_mask, decode_public_state, predict_next

DIRECTION = "uav_fleet_transmission"
OBJECT_ID = "fleet_transmission_b01"
ARMS = ("H6_all", "H6_E", "SET_all", "SET_E", "C_E")
WORLD_IDS = tuple(range(29310000, 29310016))
REPO = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Spec:
    world_ids: tuple[int, ...] = WORLD_IDS
    ns: tuple[int, ...] = (4, 8)
    horizon: int = 500
    cadence: int = 10
    torch_threads: int = 4
    bootstrap_seed: int = 26093014
    bootstrap_replicates: int = 10000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    partial.replace(path)


def artifact(path: Path, base: Path) -> dict:
    return {"path": str(path.relative_to(base)), "bytes": path.stat().st_size,
            "sha256": sha256(path)}


def make_env(n: int, world_id: int, horizon: int):
    native = FleetS1(n_uavs=n, world_id=world_id, horizon=horizon)
    return CountAdapter(ParallelToArrayAdapter(native, seed=runtime_seed(world_id, n)))


def load_agents(records: dict, n: int, env, out: Path):
    agents, bindings, hooks = {}, {}, []
    for arm, record in records.items():
        frozen.seed_rng(record["source"].seed)
        config = frozen.make_config(arm, [env] * 16, record["source"].seed,
                                    record["source_spec"])
        frozen._assert_reconstructed_config(config, record, n)
        agent = frozen.build_agent(config, str(out / "runtime_logs" / f"{arm}_n{n}"))
        frozen.restore_checkpoint(agent, record["payload"])
        agent.train(False)
        digest = frozen.digest_agent(agent)
        if digest != record["summary"]["final_parameter_normalizer_digest"]:
            raise ValueError("restored parameter/normalizer identity differs from final45")
        calls, handles = frozen.optimizer_counts(agent)
        hooks.extend(handles)
        agents[arm] = agent
        bindings[arm] = {"initial_digest": digest,
                         "normalizers": frozen._normalizer_record(agent), "calls": calls}
    return agents, bindings, hooks


def check_agents(agents: dict, bindings: dict) -> dict:
    checks = {}
    for arm, agent in agents.items():
        before = bindings[arm]
        final = frozen.digest_agent(agent)
        normalizers_unchanged = frozen._normalizer_record(agent) == before["normalizers"]
        if final != before["initial_digest"] or not normalizers_unchanged or any(before["calls"].values()):
            raise ValueError("fixed evaluation changed parameters/normalizers or called optimizer")
        checks[arm] = {"initial_digest": before["initial_digest"], "final_digest": final,
                       "normalizers_unchanged": normalizers_unchanged,
                       "optimizer_calls": dict(before["calls"])}
    return checks


def _longest_true(values: np.ndarray) -> int:
    best = current = 0
    for value in values:
        current = current + 1 if value else 0
        best = max(best, current)
    return best


def metrics(raw: dict[str, np.ndarray], n: int) -> dict:
    connections = raw["connections"][1:]
    sinr = raw["sinr"][1:]
    eligible = sinr >= 0.0
    served = connections.sum(axis=(1, 2))
    eligible_users = eligible.any(axis=1).sum(axis=1)
    quality = raw["components"][:, 1]
    positions = raw["positions"]
    path = np.linalg.norm(np.diff(positions, axis=0), axis=2).sum(axis=0)
    active = np.asarray([int(v).bit_count() for v in raw["mask"]])
    return {
        "J": float(raw["components"][:, 3].mean()), "served": float(served.mean()),
        "quality": float(quality.mean()), "height_penalty": float(raw["components"][:, 2].mean()),
        "mean_height": float(positions[1:, :, 2].mean()),
        "eligible": float(eligible_users.mean()), "ineligible": float((50-eligible_users).mean()),
        "eligible_unserved": float((eligible_users-served).mean()),
        "mean_path_per_uav": float(path.mean()), "total_team_path": float(path.sum()),
        "per_uav_path": path.tolist(), "served_p05": float(np.quantile(served, .05)),
        "served_min": int(served.min()), "zero_steps": int((served == 0).sum()),
        "longest_zero_run": _longest_true(served == 0),
        "active_mean": float(active.mean()), "active_min": int(active.min()),
        "all_on_fraction": float((active == n).mean()),
        "mask_switches": int(np.count_nonzero(np.diff(np.r_[(1 << n)-1, raw["mask"]]))),
        "mean_visible_user_slots": float(raw["visible_users"][1:].mean()),
        "mean_visible_peer_slots": float(raw["visible_peers"][1:].mean()),
        "capacity_identity_holds": bool(np.array_equal(np.minimum(eligible.sum(axis=2), 10).sum(axis=1), served)),
    }


def evaluate_episode(arm: str, n: int, world_id: int, spec: Spec, agent,
                     out: Path) -> dict:
    """One closed-loop episode. Public controllers never receive the native object."""
    episode_wall, episode_cpu = time.perf_counter(), time.process_time()
    env = make_env(n, world_id, spec.horizon)
    native = env.env.env
    seed = runtime_seed(world_id, n)
    frozen.seed_rng(seed)
    if agent is not None:
        agent.reset_env_state(0)
    obs, info = env.reset(seed=seed)
    state = np.asarray(info["state"])
    old_mask = (1 << n) - 1
    ordinary = OrdinaryController(n) if arm == "C_E" else None
    raw: dict[str, list] = {k: [] for k in (
        "positions", "observations", "states", "sinr", "connections", "peer_sinr",
        "visible_users", "visible_peers", "raw_actions", "actions", "action_logprobs",
        "mask", "scalar_reward", "components", "terminal", "runtime_after_action")}
    decisions = []
    timing = {"actor_cpu_seconds": 0., "motion_cpu_seconds": 0., "mask_cpu_seconds": 0.,
              "native_and_record_cpu_seconds": 0.}
    counts = {"actor_calls": 0, "motion_calls": 0, "mask_calls": 0}

    def snapshot():
        raw["positions"].append(native.uav_positions.copy())
        raw["observations"].append(np.asarray(obs).copy())
        raw["states"].append(state.copy())
        raw["sinr"].append(native.sinr_matrix.copy())
        raw["connections"].append(native.connections.copy())
        raw["peer_sinr"].append(native.uav_sinr_matrix.copy())
        raw["visible_users"].append([len(native._local_user_entries(i)[0][:native.max_observed_users]) for i in range(n)])
        raw["visible_peers"].append([len(native._local_uav_entries(i)[0][:native.max_observed_uavs]) for i in range(n)])

    snapshot()
    steps, dones = np.zeros(1, dtype=np.int64), np.zeros(1, dtype=bool)
    try:
        with torch.no_grad():
            for t in range(spec.horizon):
                boundary = t % spec.cadence == 0
                decision = {"t": t, "old_mask": old_mask}
                if agent is not None:
                    start = time.process_time()
                    actions, _, data = agent.step(state[None, :], np.asarray(obs)[None, :, :],
                        steps, dones, deterministic=True, return_step_data=True, build_infos=False)
                    frozen.finite((actions, data), "fleet frozen policy output")
                    command = np.clip(actions[0], -1.0, 1.0)
                    raw["raw_actions"].append(actions[0].copy())
                    raw["action_logprobs"].append(np.asarray(data["action_logprobs"])[0].reshape(-1).copy())
                    raw["runtime_after_action"].append(frozen.runtime_state_digest(agent))
                    counts["actor_calls"] += 1
                    timing["actor_cpu_seconds"] += time.process_time() - start
                    if boundary:
                        public_position, public_users = decode_public_state(state, n)
                        predicted = predict_next(public_position, command)
                else:
                    start = time.process_time()
                    command, predicted, trace = ordinary.select(t, state if boundary else None, old_mask)
                    decision["motion"] = trace
                    raw["raw_actions"].append(command.copy())
                    raw["action_logprobs"].append(np.zeros(n, dtype=np.float32))
                    raw["runtime_after_action"].append("")
                    counts["motion_calls"] += 1
                    timing["motion_cpu_seconds"] += time.process_time()-start
                    if boundary:
                        _, public_users = decode_public_state(state, n)
                if boundary and arm.endswith("_E"):
                    start = time.process_time()
                    old_mask, trace = choose_mask(public_users, predicted, old_mask)
                    decision["mask_search"] = trace
                    counts["mask_calls"] += 1
                    # Setter-generated refreshed observations are deliberately discarded:
                    # this tick's actor has already advanced once using old-mask feedback.
                    native.set_transmitter_mask(mask_bits(old_mask, n))
                    timing["mask_cpu_seconds"] += time.process_time()-start
                decision["issued_mask"] = old_mask
                decisions.append(decision)
                start = time.process_time()
                raw["actions"].append(command.copy())
                raw["mask"].append(old_mask)
                obs, reward, terminated, truncated, info = env.step(command)
                state = np.asarray(info["next_state"])
                done = bool(terminated or truncated)
                if done != (t == spec.horizon-1):
                    raise ValueError("native terminal boundary differs from full panel")
                components = info["reward_components"]["reward_info"]
                raw["components"].append([float(components[k]) for k in frozen.COMPONENTS])
                raw["scalar_reward"].append(float(reward))
                raw["terminal"].append(done)
                snapshot()
                dones[0], steps[0] = done, t+1
                timing["native_and_record_cpu_seconds"] += time.process_time()-start
    finally:
        env.close()
    arrays = {key: np.asarray(value) for key, value in raw.items()}
    arrays["users"] = native.user_positions.copy()
    if not np.all(np.isfinite(arrays["actions"])):
        raise ValueError("nonfinite executed action")
    # Every recorded component follows original COMPONENTS order.
    if tuple(frozen.COMPONENTS) != ("coverage_reward", "quality_reward", "energy_penalty", "total_reward"):
        raise ValueError("native component order changed")
    key = f"n{n}_{arm}_w{world_id}"
    raw_path = out / "raw" / f"{key}.npz"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    decision_path = out / "raw" / f"{key}.jsonl.gz"
    with gzip.open(decision_path, "xt", encoding="utf-8") as stream:
        for row in decisions:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False)+"\n")
    timing.update(wall_seconds=time.perf_counter()-episode_wall,
                  cpu_seconds=time.process_time()-episode_cpu)
    return {"arm": arm, "n": n, "world_id": world_id, "runtime_seed": seed,
            "steps": spec.horizon, "complete": True, "metrics": metrics(arrays, n),
            "counts": counts, "timing": timing,
            "raw": artifact(raw_path, out), "decisions": artifact(decision_path, out)}


def run_study(out: Path, checkpoint_root: Path, launch_sha: str, admission: dict,
              spec: Spec = Spec()) -> dict:
    started, cpu_started = time.perf_counter(), time.process_time()
    torch.set_num_threads(spec.torch_threads)
    torch.set_num_interop_threads(1)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists():
        raise FileExistsError("scientific summary exists; no replay or resume is implemented")
    config = {"object_id": OBJECT_ID, "direction": DIRECTION, "launch_sha": launch_sha,
              "spec": asdict(spec), "arms": ARMS, "source_training_sha": frozen.PRODUCER_SHA,
              "checkpoint_root": str(checkpoint_root), "admission_operation": admission.get("operation_id"),
              "world_address": [260930, 14], "world_streams": {"users": 1, "fleet": 2, "runtime": 3},
              "world_order": "N4 then N8; world increasing; cyclic five-arm order by world index",
              "components": list(frozen.COMPONENTS), "new_fits": 0, "updates": 0,
              "expected_episodes": 160, "expected_native_steps": 80000,
              "expected_mask_requests": 648000, "expected_motion_requests": 2592000}
    write_json(out / "config.json", config)
    summary = {"schema": 1, "object_id": OBJECT_ID, "direction": DIRECTION,
               "launch_sha": launch_sha, "status": "loading", "config": config,
               "episodes": [], "frozen_checks": {}, "new_fits": 0, "updates": 0}
    write_json(out / "summary.json", summary)
    try:
        records = {p[0]: frozen.load_source_policy(checkpoint_root, frozen.SourcePolicy(*p))
                   for p in frozen.SOURCE_POLICIES}
        summary["assets"] = {arm: {"source": asdict(record["source"]),
                "summary_identity": record["summary_identity"],
                "checkpoint": str(record["checkpoint"]),
                "checkpoint_record": record["checkpoint_record"],
                "checkpoint_sha256_before": record["checkpoint_sha256_before"],
                "lineage_counts": record["summary"]["counts"],
                "source_final_digest": record["summary"]["final_parameter_normalizer_digest"]}
            for arm, record in records.items()}
        summary["status"] = "running"
        for n in spec.ns:
            config_env = make_env(n, spec.world_ids[0], spec.horizon)
            agents, bindings, hooks = load_agents(records, n, config_env, out)
            try:
                for world_index, world_id in enumerate(spec.world_ids):
                    ordered = ARMS[world_index % len(ARMS):]+ARMS[:world_index % len(ARMS)]
                    for arm in ordered:
                        agent = agents.get(arm.split("_")[0])
                        row = evaluate_episode(arm, n, world_id, spec, agent, out)
                        summary["episodes"].append(row)
                        summary["native_steps"] = sum(r["steps"] for r in summary["episodes"])
                        write_json(out / "summary.json", summary)
                        print(json.dumps({"episode": len(summary["episodes"]), "n": n,
                                          "world": world_id, "arm": arm}), flush=True)
                summary["frozen_checks"][str(n)] = check_agents(agents, bindings)
            finally:
                for handle in hooks:
                    handle.remove()
                for agent in agents.values():
                    if getattr(agent, "writer", None):
                        agent.writer.close()
                config_env.close()
                del agents
        for arm, record in records.items():
            digest_after = sha256(record["checkpoint"])
            if digest_after != record["checkpoint_sha256_before"]:
                raise ValueError("checkpoint mutated during evaluation")
            summary["assets"][arm]["checkpoint_sha256_after"] = digest_after
        expected_cells = {(n, arm, world_id) for n in spec.ns for arm in ARMS for world_id in spec.world_ids}
        actual_cells = {(row["n"], row["arm"], row["world_id"]) for row in summary["episodes"]}
        if actual_cells != expected_cells or len(summary["episodes"]) != len(expected_cells):
            raise ValueError("incomplete or duplicated full panel")
        summary["worker_status"] = "complete"
        summary["status"] = "collected"
        summary["worker_timing"] = {"wall_seconds": time.perf_counter()-started,
                                     "cpu_seconds": time.process_time()-cpu_started,
                                     "peak_rss_kib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        write_json(out / "summary.json", summary)
        # Reading consumes only saved trajectories; it never invokes an actor or environment step.
        from .reader import read_run
        read_run(out)
        summary["reading"] = artifact(out / "reading.json", out)
        summary["status"] = "complete"
        summary["total_timing"] = {"wall_seconds": time.perf_counter()-started,
                                    "cpu_seconds": time.process_time()-cpu_started,
                                    "peak_rss_kib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        write_json(out / "summary.json", summary)
        return summary
    except BaseException as exc:
        summary["failure_stage"] = "reader" if summary["status"] == "collected" else summary["status"]
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        summary["failed_timing"] = {"wall_seconds": time.perf_counter()-started,
                                    "cpu_seconds": time.process_time()-cpu_started}
        write_json(out / "summary.json", summary)
        raise
