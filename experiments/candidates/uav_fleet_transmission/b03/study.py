"""Fixed complete native C/R/T panel, with every T model branch preserved."""
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
from ..b02.controller import COUNT_KEYS, KINDS, empty_counts, trace_counts
from ..b02.study import COMPONENTS, SOURCE_PATHS as B02_SOURCE_PATHS, evaluate_episode, option_metrics
from .controller import ContinuationProgram
from .host import WORLD_FILE, WORLD_IDS, bound_worlds, make_env, seed

REPO = Path(__file__).resolve().parents[4]
DIRECTION = "uav_fleet_transmission"
OBJECT_ID = "fleet_complete_continuation_b03"
ARMS = ("C", "R", "T")
SOURCE_PATHS = B02_SOURCE_PATHS + tuple(
    f"experiments/candidates/uav_fleet_transmission/b03/{name}"
    for name in ("__init__.py", "host.py", "option.py", "controller.py", "surrogate.py",
                 "study.py", "reader.py", "run.py", "worlds.json"))
CEILINGS = dict(worker_state_mask_requests=22636832, model_physical_transitions=58880,
                candidate_transit_ticks=896000, ordinary_candidate_position_predictions=17635968)
SNAPSHOTS = ("positions", "observations", "states", "sinr", "connections", "peer_sinr",
             "visible_users", "visible_peers")


@dataclass(frozen=True)
class Spec:
    world_ids: tuple = WORLD_IDS
    n: int = 8
    horizon: int = 500
    cadence: int = 10
    option_t: int = 40
    bootstrap_seed: int = 29326991
    bootstrap_replicates: int = 10000


def source_bindings():
    return {path: {"sha256": sha256(REPO/path), "bytes": (REPO/path).stat().st_size}
            for path in SOURCE_PATHS}


def fixed_config():
    return {"object_id": OBJECT_ID, "direction": DIRECTION,
        "spec": json.loads(json.dumps(asdict(Spec()))), "arms": list(ARMS),
        "source_bindings": source_bindings(), "world_file": artifact(WORLD_FILE, REPO),
        "world_order": "ascending world; cyclic C/R/T starting at world index mod3",
        "ceilings": CEILINGS.copy(), "new_fits": 0, "updates": 0,
        "model_branch_scope": "C-stay and one original stationary champion per muted member; all460ticks",
        "original_R_source": "9928d34b54628baaa542961debb65c5ce7ef0f23"}


def write_trace(path, decisions):
    with gzip.open(path, "xt", encoding="utf-8") as stream:
        for decision in decisions:
            stream.write(json.dumps(decision, sort_keys=True, allow_nan=False) + "\n")


def compact_continuation(value):
    result = {key: item for key, item in value.items() if key not in ("branches", "original_R")}
    result["branches"] = []
    for branch in value["branches"]:
        plan = branch["plan"]
        result["branches"].append({"id": branch["id"], "physical_identity": branch["physical_identity"],
            "modeled_execution_identity": branch["modeled_execution_identity"],
            "stationary_candidate": None if plan is None else plan["selected"], "summary": branch["summary"]})
    result["original_R_initiated"] = value["original_R"]["initiated"]
    result["original_R_stationary_candidate"] = value["original_R"]["selected"]
    result["candidate_digest"] = value["original_R"]["candidate_digest"]
    result["candidate_count"] = value["original_R"]["candidate_count"]
    return result


def evaluate_T_episode(scene, runtime_seed, out):
    wall, cpu = time.perf_counter(), time.process_time()
    horizon = 500
    env = make_env(scene, horizon, runtime_seed)
    native = env.env.env
    obs, info = env.reset(seed=runtime_seed)
    state, old_mask = np.asarray(info["state"]), 255
    key = f"n8_T_w{scene.world_id}"
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    branch_artifacts, candidate_artifacts = [], []

    def branch_sink(identifier, result):
        path = raw_dir / f"{key}_model_{identifier}.npz"
        trace = raw_dir / f"{key}_model_{identifier}.jsonl.gz"
        with path.open("xb") as stream:
            np.savez_compressed(stream, **result["arrays"])
        write_trace(trace, result["decisions"])
        branch_artifacts.append({"id": identifier, "raw": artifact(path, out),
                                 "decisions": artifact(trace, out), "summary": result["summary"]})

    def candidate_sink(rows):
        path = raw_dir / f"{key}_stationary_candidates.npy"
        with path.open("xb") as stream:
            np.save(stream, rows, allow_pickle=False)
        candidate_artifacts.append(artifact(path, out))

    policy = ContinuationProgram(horizon, branch_sink, candidate_sink)
    raw = {k: [] for k in (*SNAPSHOTS, "actions", "mask", "components", "scalar_reward", "terminal")}
    decisions, counts = [], empty_counts()
    timings = {"controller_and_branch_record_cpu_seconds": 0., "native_and_record_cpu_seconds": 0.}
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
            position_predictions += 216 * int("motion" in decision)
            if "option" in decision:
                option_model_ticks += int(decision["option"]["counts"]["model_ticks"])
            timings["controller_and_branch_record_cpu_seconds"] += time.process_time() - mark
            decisions.append(decision)
            mark = time.process_time()
            if t % 10 == 0:
                native.set_transmitter_mask(mask_bits(new_mask, 8))
            raw["actions"].append(command.copy())
            raw["mask"].append(new_mask)
            obs, reward, terminated, truncated, info = env.step(command)
            state = np.asarray(info["next_state"])
            done = bool(terminated or truncated)
            if done != (t == horizon - 1):
                raise ValueError("native terminal differs from fixed horizon")
            component = info["reward_components"]["reward_info"]
            raw["components"].append([float(component[k]) for k in COMPONENTS])
            raw["scalar_reward"].append(float(reward))
            raw["terminal"].append(done)
            old_mask = new_mask
            snapshot()
            timings["native_and_record_cpu_seconds"] += time.process_time() - mark
    finally:
        env.close()
    if len(candidate_artifacts) != 1 or len(branch_artifacts) != len(policy.continuation["branches"]):
        raise ValueError("missing T shortlist or complete branch artifact")
    arrays = {key: np.asarray(value) for key, value in raw.items()}
    arrays["users"] = scene.user_positions.copy()
    raw_path, trace_path = raw_dir / f"{key}.npz", raw_dir / f"{key}.jsonl.gz"
    with raw_path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    write_trace(trace_path, decisions)
    timings.update(wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu)
    return {"arm": "T", "n": 8, "world_id": scene.world_id, "runtime_seed": runtime_seed,
        "steps": horizon, "complete": True, "metrics": metrics(arrays, 8),
        "option": option_metrics(policy.plan, arrays), "option_forecast_scope": "original stationary formula; complete model forecasts in continuation",
        "candidate_counts": counts, "calls": calls, "position_predictions": position_predictions,
        "option_model_ticks": option_model_ticks, "timing": timings,
        "raw": artifact(raw_path, out), "decisions": artifact(trace_path, out),
        "stationary_candidates": candidate_artifacts[0], "model_branches": branch_artifacts,
        "continuation": compact_continuation(policy.continuation)}


def verify_prefixes(out, rows):
    panel = {(r["arm"], r["world_id"]): r for r in rows}
    for world_id in sorted({r["world_id"] for r in rows}):
        with np.load(out/panel["C", world_id]["raw"]["path"], allow_pickle=False) as c:
            for arm in ("R", "T"):
                with np.load(out/panel[arm, world_id]["raw"]["path"], allow_pickle=False) as other:
                    if set(c.files) != set(other.files):
                        raise ValueError("native array keys differ across matched programs")
                    for key in c.files:
                        end = 41 if key in SNAPSHOTS else 40
                        a, b = (c[key], other[key]) if key == "users" else (c[key][:end], other[key][:end])
                        if not np.array_equal(a, b):
                            raise ValueError(f"C/{arm} native prefix differs for {world_id}/{key}")


def run_study(out, launch_sha, admission):
    wall, cpu = time.perf_counter(), time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    scenes, spec = bound_worlds(), Spec()
    out.mkdir(parents=True, exist_ok=True)
    if any((out/name).exists() for name in ("summary.json", "config.json", "raw", "reading.json")):
        raise FileExistsError("existing attempt; no implicit replay/resume")
    config = dict(fixed_config(), launch_sha=launch_sha, admission_command_sha256=admission["command_sha256"],
        versions={"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__})
    write_json(out/"config.json", config)
    summary = {"launch_sha": launch_sha, "config": config, "config_artifact": artifact(out/"config.json", out),
        "status": "worker", "worker_status": "incomplete", "episodes": [], "new_fits": 0, "updates": 0}
    write_json(out/"summary.json", summary)
    try:
        for index, world_id in enumerate(spec.world_ids):
            for offset in range(3):
                arm = ARMS[(index + offset) % 3]
                if arm == "T":
                    row = evaluate_T_episode(scenes[world_id], seed(world_id, 3, 8), out)
                else:
                    row = evaluate_episode(arm, scenes[world_id], 500, seed(world_id, 3, 8), out)
                summary["episodes"].append(row)
                write_json(out/"summary.json", summary)
                print(json.dumps({"worker_episodes_complete": len(summary["episodes"]), "world_id": world_id, "arm": arm}), flush=True)
        verify_prefixes(out, summary["episodes"])
        if source_bindings() != config["source_bindings"]:
            raise ValueError("source/input bytes mutated during collection")
        if len(summary["episodes"]) != 48 or sum(r["steps"] for r in summary["episodes"]) != 24000:
            raise ValueError("complete fixed panel missing")
        summary["worker_status"], summary["status"] = "complete", "collected"
        summary["worker_timing"] = {"wall_seconds": time.perf_counter() - wall,
            "cpu_seconds": time.process_time() - cpu, "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        from .reader import read_run
        read_run(out)
        summary["reading"] = artifact(out/"reading.json", out)
        summary["status"] = "complete"
        summary["total_timing"] = {"wall_seconds": time.perf_counter() - wall,
            "cpu_seconds": time.process_time() - cpu, "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        return summary
    except BaseException as exc:
        summary["failure_stage"] = "reader" if summary["status"] == "collected" else "worker"
        summary["status"], summary["error"] = "failed", f"{type(exc).__name__}: {exc}"
        summary["failed_timing"] = {"wall_seconds": time.perf_counter() - wall,
            "cpu_seconds": time.process_time() - cpu, "process_resources": process_resources()}
        write_json(out/"summary.json", summary)
        raise
