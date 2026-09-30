"""Fixed, paired four-program native evaluation and separately charged full reader."""
import json
import platform
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.study import artifact, process_resources, write_json
from experiments.candidates.uav_fleet_transmission.b02.controller import KINDS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b02.study import COMPONENTS, option_metrics
from experiments.candidates.uav_fleet_transmission.b03.study import SNAPSHOTS, write_trace

from .contract import ARMS, FIT_FILE, fixed_config, source_bindings
from .controller import make_program
from .host import WORLD_IDS, bound_worlds, make_env, seed
from .outcomes import complete_metrics


def evaluate_episode(arm, scene, runtime_seed, out, fitted):
    wall, cpu = time.perf_counter(), time.process_time()
    env = make_env(scene, 500, runtime_seed)
    native = env.env.env
    obs, info = env.reset(seed=runtime_seed)
    state, old_mask = np.asarray(info["state"]), 255
    key = f"n8_{arm}_w{scene.world_id}"
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    policy = make_program(arm, fitted if arm == "L2_E" else None)
    raw = {k: [] for k in (*SNAPSHOTS, "actions", "mask", "components", "scalar_reward", "terminal")}
    decisions, counts, branches, bank_artifacts = [], empty_counts(), [], []
    calls = {kind: 0 for kind in KINDS}
    predictions = option_ticks = 0
    timing = {"controller_cpu_seconds": 0., "controller_wall_seconds": 0.,
              "native_and_record_cpu_seconds": 0., "diagnostic_export_cpu_seconds": 0.,
              "diagnostic_export_wall_seconds": 0.}

    def snapshot():
        raw["positions"].append(native.uav_positions.copy())
        raw["observations"].append(np.asarray(obs).copy())
        raw["states"].append(state.copy())
        raw["sinr"].append(native.sinr_matrix.copy())
        raw["connections"].append(native.connections.copy())
        raw["peer_sinr"].append(native.uav_sinr_matrix.copy())
        raw["visible_users"].append([len(native._local_user_entries(i)[0][:20]) for i in range(8)])
        raw["visible_peers"].append([len(native._local_uav_entries(i)[0][:10]) for i in range(8)])

    snapshot()
    try:
        for t in range(500):
            cw, cc = time.perf_counter(), time.process_time()
            command, new_mask, decision = policy.select(t, state if t % 10 == 0 else None, old_mask)
            timing["controller_cpu_seconds"] += time.process_time() - cc
            timing["controller_wall_seconds"] += time.perf_counter() - cw
            if t % 10 and new_mask != old_mask:
                raise ValueError("mask changed between legal reports")
            trace_counts(decision, counts)
            for kind in KINDS:
                calls[kind] += int(kind in decision)
            predictions += 216 * int("motion" in decision)
            if "option" in decision:
                option_ticks += int(decision["option"]["counts"]["model_ticks"])
            decisions.append(decision)
            pending = policy.take_artifacts()
            if pending is not None:
                ew, ec = time.perf_counter(), time.process_time()
                path = raw_dir / f"{key}_stationary_candidates.npy"
                with path.open("xb") as stream:
                    np.save(stream, pending["candidate_rows"], allow_pickle=False)
                bank_artifacts.append(artifact(path, out))
                for identifier, result in pending["branches"]:
                    path = raw_dir / f"{key}_model_{identifier}.npz"
                    trace = raw_dir / f"{key}_model_{identifier}.jsonl.gz"
                    with path.open("xb") as stream:
                        np.savez_compressed(stream, **result["arrays"])
                    write_trace(trace, result["decisions"])
                    branches.append({"id": identifier, "raw": artifact(path, out),
                                     "decisions": artifact(trace, out), "summary": result["summary"],
                                     "reuse": result["reuse"]})
                timing["diagnostic_export_cpu_seconds"] += time.process_time() - ec
                timing["diagnostic_export_wall_seconds"] += time.perf_counter() - ew
            mark = time.process_time()
            if t % 10 == 0:
                native.set_transmitter_mask(mask_bits(new_mask, 8))
            raw["actions"].append(command.copy())
            raw["mask"].append(new_mask)
            obs, reward, terminated, truncated, info = env.step(command)
            state = np.asarray(info["next_state"])
            done = bool(terminated or truncated)
            if done != (t == 499):
                raise ValueError("native terminal differs from fixed H500")
            component = info["reward_components"]["reward_info"]
            raw["components"].append([float(component[k]) for k in COMPONENTS])
            raw["scalar_reward"].append(float(reward))
            raw["terminal"].append(done)
            old_mask = new_mask
            snapshot()
            timing["native_and_record_cpu_seconds"] += time.process_time() - mark
    finally:
        env.close()
    if len(bank_artifacts) != 1 or len(branches) != len(policy.selection["branches"]):
        raise ValueError("complete stationary bank or model artifact is missing")
    arrays = {k: np.asarray(v) for k, v in raw.items()}
    arrays["users"] = scene.user_positions.copy()
    path, trace = raw_dir / f"{key}.npz", raw_dir / f"{key}.jsonl.gz"
    ew, ec = time.perf_counter(), time.process_time()
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    write_trace(trace, decisions)
    timing["diagnostic_export_cpu_seconds"] += time.process_time() - ec
    timing["diagnostic_export_wall_seconds"] += time.perf_counter() - ew
    timing.update(selection_cpu_seconds=policy.selection_timing["cpu_seconds"],
                  selection_wall_seconds=policy.selection_timing["wall_seconds"])
    timing.update({k: v for k,v in policy.selection_timing.items() if k not in ("cpu_seconds", "wall_seconds")})
    timing.setdefault("shortlist_cpu_seconds", 0.)
    timing.setdefault("shortlist_wall_seconds", 0.)
    row = {"arm": arm, "n": 8, "world_id": scene.world_id, "runtime_seed": runtime_seed,
            "steps": 500, "complete": True, "metrics": complete_metrics(arrays),
            "option": option_metrics(policy.plan, arrays), "selection": policy.selection,
            "candidate_counts": counts, "calls": calls, "position_predictions": predictions,
            "option_model_ticks": option_ticks, "timing": timing,
            "raw": artifact(path, out), "decisions": artifact(trace, out),
            "stationary_candidates": bank_artifacts[0], "model_branches": branches}
    timing.update(cpu_seconds=time.process_time() - cpu, wall_seconds=time.perf_counter() - wall)
    return row


def verify_prefixes(out, rows):
    panel = {(r["arm"], r["world_id"]): r for r in rows}
    for world_id in WORLD_IDS:
        with np.load(out/panel["R", world_id]["raw"]["path"], allow_pickle=False) as base:
            for arm in ARMS[1:]:
                with np.load(out/panel[arm, world_id]["raw"]["path"], allow_pickle=False) as other:
                    if set(base.files) != set(other.files):
                        raise ValueError("native array keys differ across fixed programs")
                    for key in base.files:
                        end = 41 if key in SNAPSHOTS else 40
                        a, b = (base[key], other[key]) if key == "users" else (base[key][:end], other[key][:end])
                        if not np.array_equal(a, b):
                            raise ValueError(f"paired R/{arm} prefix differs: {world_id}/{key}")


def run_study(out, launch_sha, admission, fit_sha256):
    wall, cpu = time.perf_counter(), time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    config = dict(fixed_config(fit_sha256), launch_sha=launch_sha,
                  admission_command_sha256=admission["command_sha256"],
                  versions={"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__})
    from .reader import validate_fit
    fitted, _ = validate_fit(config)
    scenes = bound_worlds()
    out.mkdir(parents=True, exist_ok=True)
    if any((out/name).exists() for name in ("summary.json", "config.json", "raw", "reading.json")):
        raise FileExistsError("existing B07 evaluation attempt; no implicit replay/resume")
    write_json(out/"config.json", config)
    summary = {"launch_sha": launch_sha, "config": config, "config_artifact": artifact(out/"config.json", out),
               "status": "worker", "worker_status": "incomplete", "episodes": [], "new_fits": 0,
               "inherited_B06_fits": 1, "updates": 0, "new_training_acquisition": 0}
    write_json(out/"summary.json", summary)
    try:
        for index, world_id in enumerate(WORLD_IDS):
            for offset in range(4):
                arm = ARMS[(index + offset) % 4]
                row = evaluate_episode(arm, scenes[world_id], seed(world_id, 3, 8), out, fitted)
                summary["episodes"].append(row)
                write_json(out/"summary.json", summary)
                print(json.dumps({"worker_episodes_complete": len(summary["episodes"]),
                                  "world_id": world_id, "arm": arm}), flush=True)
        verify_prefixes(out, summary["episodes"])
        if source_bindings() != config["source_bindings"] or artifact(FIT_FILE, FIT_FILE.parents[3])["sha256"] != fit_sha256:
            raise ValueError("published source/fit input changed during evaluation")
        if len(summary["episodes"]) != 64 or sum(r["steps"] for r in summary["episodes"]) != 32000:
            raise ValueError("complete fixed evaluation panel missing")
        summary["worker_status"], summary["status"] = "complete", "collected"
        summary["worker_timing"] = {"wall_seconds": time.perf_counter() - wall,
                                    "cpu_seconds": time.process_time() - cpu}
        write_json(out/"summary.json", summary)
        from .reader import read_run
        read_run(out)
        summary["reading"] = artifact(out/"reading.json", out)
        summary["status"] = "complete"
        summary["total_timing"] = {"wall_seconds": time.perf_counter() - wall,
                                  "cpu_seconds": time.process_time() - cpu,
                                  "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        return summary
    except BaseException as exc:
        summary["failure_stage"] = "reader" if summary["status"] == "collected" else "worker"
        summary["status"], summary["error"] = "failed", f"{type(exc).__name__}: {exc}"
        summary["failed_timing"] = {"wall_seconds": time.perf_counter() - wall,
                                   "cpu_seconds": time.process_time() - cpu,
                                   "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        raise
