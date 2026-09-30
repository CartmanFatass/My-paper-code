"""Complete fixed C/J/R native episodes, artifacts and exact input binding."""
from dataclasses import asdict, dataclass
import gzip
import json
import platform
from pathlib import Path
import time

import numpy as np
import torch

from ..host import mask_bits
from ..study import artifact, metrics, process_resources, sha256, write_json
from .controller import COUNT_KEYS, KINDS, Program, empty_counts, trace_counts
from .host import WORLD_FILE, WORLD_IDS, bound_worlds, make_env, seed

REPO = Path(__file__).resolve().parents[4]
DIRECTION = "uav_fleet_transmission"
OBJECT_ID = "fleet_silent_repositioning_b02"
ARMS = ("C", "J", "R")
SOURCE_PATHS = (
    "experiments/candidates/uav_fleet_transmission/b02/host.py",
    "experiments/candidates/uav_fleet_transmission/b02/controller.py",
    "experiments/candidates/uav_fleet_transmission/b02/option.py",
    "experiments/candidates/uav_fleet_transmission/b02/study.py",
    "experiments/candidates/uav_fleet_transmission/b02/reader.py",
    "experiments/candidates/uav_fleet_transmission/b02/run.py",
    "experiments/candidates/uav_fleet_transmission/b02/worlds.json",
    "experiments/candidates/uav_fleet_transmission/host.py",
    "experiments/candidates/uav_fleet_transmission/control.py",
    "experiments/candidates/uav_fleet_transmission/study.py",
    "experiments/candidates/uav_fleet_transmission/reader.py",
    "experiments/candidates/agent_count_generalization/adapter.py",
    "envs/pettingzoo/scenario1.py", "envs/pettingzoo/uav_env.py",
    "envs/pettingzoo/uav_radio.py", "envs/pettingzoo/env_adapter.py")
COMPONENTS = ("coverage_reward", "quality_reward", "energy_penalty", "total_reward")


@dataclass(frozen=True)
class Spec:
    world_ids: tuple = WORLD_IDS
    n: int = 8
    horizon: int = 500
    cadence: int = 10
    option_t: int = 40
    bootstrap_seed: int = 26093024
    bootstrap_replicates: int = 10000


def source_bindings():
    return {path: {"sha256": sha256(REPO/path), "bytes": (REPO/path).stat().st_size}
            for path in SOURCE_PATHS}


def option_metrics(plan, raw):
    if plan is None:
        return None
    if not plan["initiated"]:
        return {"initiated": False, "stay_total_J": plan["stay_total_J"],
                "predicted_total_J": plan["predicted_total_J"], "selected": plan["selected"]}
    arrival, member = plan["arrival_t"], plan["member"]
    active = (raw["mask"][arrival:] & (1 << member)) != 0
    first_off = np.flatnonzero(~active)
    return {"initiated": True, "member": member, "site": plan["site"],
        "duration": plan["duration"], "arrival_t": arrival,
        "predicted_mask": plan["predicted_mask"], "actual_arrival_mask": int(raw["mask"][arrival]),
        "predicted_total_J": plan["predicted_total_J"], "stay_total_J": plan["stay_total_J"],
        "predicted_total_served": plan["predicted_total_served"],
        "stay_total_served": plan["stay_total_served"],
        "realized_remaining_J_sum": float(raw["components"][40:,3].sum()),
        "realized_remaining_served_sum": int(raw["connections"][41:].sum()),
        "transit_J_sum": float(raw["components"][40:arrival,3].sum()),
        "transit_served_sum": int(raw["connections"][41:arrival+1].sum()),
        "activated_steps_after_arrival": int(active.sum()),
        "initial_contiguous_active_steps": int(first_off[0]) if len(first_off) else int(len(active)),
        "remuted": bool(len(first_off)),
        "first_remute_t": int(arrival+first_off[0]) if len(first_off) else None,
        "selected": plan["selected"]}


def evaluate_episode(arm, scene, horizon, runtime_seed, out):
    wall, cpu = time.perf_counter(), time.process_time()
    env = make_env(scene, horizon, runtime_seed)
    native = env.env.env
    obs, info = env.reset(seed=runtime_seed)
    state = np.asarray(info["state"])
    policy, old_mask = Program(arm, horizon), 255
    raw = {k: [] for k in ("positions", "observations", "states", "sinr", "connections",
        "peer_sinr", "visible_users", "visible_peers", "actions", "mask", "components",
        "scalar_reward", "terminal")}
    decisions, counts = [], empty_counts()
    timings = {"controller_cpu_seconds": 0., "native_and_record_cpu_seconds": 0.}
    calls = {kind: 0 for kind in KINDS}
    position_predictions, option_model_ticks = 0, 0

    def snapshot():
        raw["positions"].append(native.uav_positions.copy())
        raw["observations"].append(np.asarray(obs).copy())
        raw["states"].append(state.copy())
        raw["sinr"].append(native.sinr_matrix.copy())
        raw["connections"].append(native.connections.copy())
        raw["peer_sinr"].append(native.uav_sinr_matrix.copy())
        raw["visible_users"].append([len(native._local_user_entries(i)[0][:native.max_observed_users]) for i in range(8)])
        raw["visible_peers"].append([len(native._local_uav_entries(i)[0][:native.max_observed_uavs]) for i in range(8)])
    snapshot()
    try:
        for t in range(horizon):
            mark = time.process_time()
            command, new_mask, decision = policy.select(t, state if t % 10 == 0 else None, old_mask)
            if t % 10 and new_mask != old_mask:
                raise ValueError("mask changed between legal boundaries")
            trace_counts(decision, counts)
            for kind in KINDS:
                calls[kind] += int(kind in decision)
            position_predictions += 8*27*int("motion" in decision or "joint" in decision)
            if "option" in decision:
                option_model_ticks += int(decision["option"]["counts"]["model_ticks"])
            timings["controller_cpu_seconds"] += time.process_time()-mark
            decisions.append(decision)
            mark = time.process_time()
            if t % 10 == 0:
                native.set_transmitter_mask(mask_bits(new_mask, 8))
            raw["actions"].append(command.copy())
            raw["mask"].append(new_mask)
            obs, reward, terminated, truncated, info = env.step(command)
            state = np.asarray(info["next_state"])
            done = bool(terminated or truncated)
            if done != (t == horizon-1):
                raise ValueError("native terminal differs from fixed horizon")
            component = info["reward_components"]["reward_info"]
            raw["components"].append([float(component[k]) for k in COMPONENTS])
            raw["scalar_reward"].append(float(reward))
            raw["terminal"].append(done)
            old_mask = new_mask
            snapshot()
            timings["native_and_record_cpu_seconds"] += time.process_time()-mark
    finally:
        env.close()
    arrays = {key: np.asarray(value) for key, value in raw.items()}
    arrays["users"] = scene.user_positions.copy()
    key = f"n8_{arm}_w{scene.world_id}"
    raw_path, trace_path = out/"raw"/f"{key}.npz", out/"raw"/f"{key}.jsonl.gz"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    with gzip.open(trace_path, "xt", encoding="utf-8") as stream:
        for decision in decisions:
            stream.write(json.dumps(decision, sort_keys=True, allow_nan=False)+"\n")
    timings.update(wall_seconds=time.perf_counter()-wall, cpu_seconds=time.process_time()-cpu)
    return {"arm": arm, "n": 8, "world_id": scene.world_id, "runtime_seed": runtime_seed,
        "steps": horizon, "complete": True, "metrics": metrics(arrays, 8),
        "option": option_metrics(policy.plan, arrays), "candidate_counts": counts,
        "calls": calls, "position_predictions": position_predictions, "option_model_ticks": option_model_ticks,
        "timing": timings, "raw": artifact(raw_path, out), "decisions": artifact(trace_path, out)}


def verify_prefixes(out, rows):
    panel = {(r["arm"], r["world_id"]): r for r in rows}
    for world_id in sorted({r["world_id"] for r in rows}):
        with np.load(out/panel["C",world_id]["raw"]["path"], allow_pickle=False) as c, \
             np.load(out/panel["R",world_id]["raw"]["path"], allow_pickle=False) as r:
            for key in c.files:
                end = 41 if key in ("positions", "observations", "states", "sinr", "connections",
                                    "peer_sinr", "visible_users", "visible_peers") else 40
                actual, expected = (c[key], r[key]) if key == "users" else (c[key][:end], r[key][:end])
                if not np.array_equal(actual, expected):
                    raise ValueError(f"C/R native prefix differs for {world_id}/{key}")


def run_study(out, launch_sha, admission):
    wall, cpu = time.perf_counter(), time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    scenes, spec = bound_worlds(), Spec()
    out.mkdir(parents=True, exist_ok=True)
    if (out/"summary.json").exists():
        raise FileExistsError("existing attempt; no implicit replay/resume")
    config = {"object_id": OBJECT_ID, "direction": DIRECTION, "launch_sha": launch_sha,
        "spec": asdict(spec), "arms": ARMS, "source_bindings": source_bindings(),
        "world_file": artifact(WORLD_FILE, REPO), "admission_operation": admission.get("operation_id"),
        "world_order": "ascending world; cyclic C/J/R starting at world index mod3",
        "radio_request_ceiling": 50918864, "position_prediction_ceiling": 5184000,
        "option_model_tick_ceiling": 448000, "new_fits": 0, "updates": 0,
        "versions": {"python":platform.python_version(), "numpy": np.__version__, "torch": torch.__version__}}
    write_json(out/"config.json", config)
    summary = {"launch_sha": launch_sha, "config": config, "status": "worker",
               "worker_status": "incomplete", "episodes": [], "new_fits": 0, "updates": 0}
    write_json(out/"summary.json", summary)
    try:
        for index, world_id in enumerate(spec.world_ids):
            for offset in range(3):
                arm = ARMS[(index+offset) % 3]
                row = evaluate_episode(arm, scenes[world_id], spec.horizon, seed(world_id,3,8), out)
                summary["episodes"].append(row)
                write_json(out/"summary.json", summary)
                print(json.dumps({"worker_episodes_complete": len(summary["episodes"]),
                                  "world_id": world_id, "arm": arm}), flush=True)
        verify_prefixes(out, summary["episodes"])
        if source_bindings() != config["source_bindings"]:
            raise ValueError("source/input bytes mutated during collection")
        if len(summary["episodes"]) != 48 or sum(r["steps"] for r in summary["episodes"]) != 24000:
            raise ValueError("complete fixed panel missing")
        summary["worker_status"], summary["status"] = "complete", "collected"
        summary["worker_timing"] = {"wall_seconds": time.perf_counter()-wall,
            "cpu_seconds": time.process_time()-cpu, "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        from .reader import read_run
        read_run(out)
        summary["reading"] = artifact(out/"reading.json", out)
        summary["status"] = "complete"
        summary["total_timing"] = {"wall_seconds": time.perf_counter()-wall,
            "cpu_seconds": time.process_time()-cpu, "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        return summary
    except BaseException as exc:
        summary["failure_stage"] = "reader" if summary["status"] == "collected" else "worker"
        summary["status"], summary["error"] = "failed", f"{type(exc).__name__}: {exc}"
        summary["failed_timing"] = {"wall_seconds": time.perf_counter()-wall,
                                    "cpu_seconds": time.process_time()-cpu, "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        raise
