"""Fixed complete native T/G2/A2 panel and streamed nested-model evidence."""
from dataclasses import asdict, dataclass
import gzip
import json
import platform
from pathlib import Path
import re
import time

import numpy as np
import torch

from ..host import mask_bits
from ..study import artifact, metrics, process_resources, sha256, write_json
from ..b02.controller import COUNT_KEYS, KINDS, empty_counts, trace_counts
from ..b02.study import COMPONENTS
from ..b03.study import SOURCE_PATHS as B03_SOURCE_PATHS, SNAPSHOTS, write_trace
from .controller import TemporalProgram
from .host import WORLD_FILE, WORLD_IDS, bound_worlds, make_env, seed

REPO = Path(__file__).resolve().parents[4]
DIRECTION = "uav_fleet_transmission"
OBJECT_ID = "fleet_temporal_complementarity_b04"
ARMS = ("T", "G2", "A2")
SOURCE_PATHS = B03_SOURCE_PATHS + tuple(
    f"experiments/candidates/uav_fleet_transmission/b04/{name}"
    for name in ("__init__.py", "host.py", "option.py", "controller.py", "surrogate.py",
                 "study.py", "reader.py", "run.py", "worlds.json"))
CEILINGS = {"worker_state_mask_requests": 181214800,
            "model_physical_transitions": 663040,
            "candidate_transit_ticks": 5824000,
            "stationary_candidate_rows": 145600}
ARM_REQUEST_CEILINGS = {"T": 17337168, "G2": 30259136, "A2": 133618496}


@dataclass(frozen=True)
class Spec:
    world_ids: tuple = WORLD_IDS
    n: int = 8
    horizon: int = 500
    cadence: int = 10
    first_t: int = 40
    second_t: int = 120
    bootstrap_seed: int = 29497991
    bootstrap_replicates: int = 10000


def source_bindings():
    return {path: {"sha256": sha256(REPO / path), "bytes": (REPO / path).stat().st_size}
            for path in SOURCE_PATHS}


def fixed_config():
    return {"object_id": OBJECT_ID, "direction": DIRECTION,
            "spec": json.loads(json.dumps(asdict(Spec()))), "arms": list(ARMS),
            "source_bindings": source_bindings(), "world_file": artifact(WORLD_FILE, REPO),
            "world_order": "ascending world; cyclic T/G2/A2 starting at world index mod3",
            "ceilings": CEILINGS.copy(), "arm_request_ceilings": ARM_REQUEST_CEILINGS.copy(),
            "new_fits": 0, "updates": 0, "cycle_reuse": False,
            "original_T_source": "02e8c1adc5a625037490facc6388e4b8bc9fd74e",
            "primary": "complete native mean J: A2-G2",
            "secondary": ["G2-T", "A2-T"],
            "model_branch_scope": "all first champions plus stay; every inner T120 search and outer chosen suffix; actual120 replan",
            "inner_outer_state": "inner starts decoded FP32 report; outer retains its unrounded physical coordinates",
            "strict_decline": "equal total J declines; A2 stay-first includes T120"}


def write_catalog(path, value):
    with path.open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as stream:
            stream.write((json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode())


def read_catalog(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def identifier_path(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", identifier):
        raise ValueError("invalid model evidence identifier")
    return Path(*identifier.split("/"))


def json_record(value):
    """Freeze JSON records and normalize only dictionary-key serialization."""
    return json.loads(json.dumps(value, sort_keys=True, allow_nan=False))


def zero_counts():
    return {key: 0 for key in COUNT_KEYS}


def add_counts(target, source):
    for key in COUNT_KEYS:
        value = source[key]
        if type(value) is not int or value < 0:
            raise ValueError("invalid scientific query counter")
        target[key] += value


def episode_costs(catalog, native_counts, position_predictions):
    """Banks are counted once by identity; option trace copies are not new work."""
    native = zero_counts()
    for kind in KINDS:
        if kind != "option":
            add_counts(native, native_counts[kind])
    model_control, model_reward, banks = zero_counts(), zero_counts(), zero_counts()
    model_ticks, predictions = 0, position_predictions
    for branch in catalog["model_branches"]:
        summary = branch["summary"]
        model_ticks += summary["model_transitions"]
        predictions += summary["ordinary_candidate_position_predictions"]
        for kind in KINDS:
            if kind != "option":
                add_counts(model_control, summary["controller_counts"][kind])
        add_counts(model_reward, summary["reward_counts"])
    transit_ticks, candidate_rows = 0, 0
    if set(catalog["banks"]) != {item["id"] for item in catalog["candidate_banks"]}:
        raise ValueError("stationary bank ledger differs from retained artifacts")
    for bank in catalog["banks"].values():
        add_counts(banks, bank["counts"])
        transit_ticks += bank["counts"]["model_ticks"]
        candidate_rows += bank["candidate_count"]
    total = zero_counts()
    for source in (native, model_control, model_reward, banks):
        add_counts(total, source)
    return {"native_controller_counts_excluding_banks": native,
            "model_controller_counts_excluding_banks": model_control,
            "model_reward_counts": model_reward, "stationary_bank_counts": banks,
            "all_state_mask_counts": total,
            "worker_state_mask_requests": total["requested_candidates"],
            "model_physical_transitions": model_ticks,
            "candidate_transit_ticks": transit_ticks,
            "stationary_candidate_rows": candidate_rows,
            "ordinary_candidate_position_predictions": predictions,
            "model_branches": len(catalog["model_branches"]),
            "stationary_banks": len(catalog["candidate_banks"])}


def evaluate_episode(arm, scene, runtime_seed, out):
    wall, cpu = time.perf_counter(), time.process_time()
    horizon = 500
    env = make_env(scene, horizon, runtime_seed)
    native = env.env.env
    obs, info = env.reset(seed=runtime_seed)
    state, old_mask = np.asarray(info["state"]), 255
    key = f"n8_{arm}_w{scene.world_id}"
    raw_dir = out / "raw" / key
    raw_dir.mkdir(parents=True, exist_ok=False)
    branch_artifacts, candidate_artifacts = [], []
    branch_ids, bank_ids = set(), set()

    def branch_sink(identifier, result):
        if identifier in branch_ids:
            raise ValueError("duplicate model branch identity")
        branch_ids.add(identifier)
        path = (raw_dir / "models" / identifier_path(identifier)).with_suffix(".npz")
        trace = path.with_suffix(".jsonl.gz")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            np.savez_compressed(stream, **result["arrays"])
        write_trace(trace, result["decisions"])
        branch_artifacts.append({"id": identifier, "raw": artifact(path, out),
                                 "decisions": artifact(trace, out),
                                 "summary": json_record(result["summary"])})

    def candidate_sink(identifier, rows):
        if identifier in bank_ids:
            raise ValueError("duplicate stationary bank identity")
        bank_ids.add(identifier)
        path = (raw_dir / "banks" / identifier_path(identifier)).with_suffix(".npy")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            np.save(stream, rows, allow_pickle=False)
        candidate_artifacts.append({"id": identifier, "raw": artifact(path, out)})

    policy = TemporalProgram(arm, horizon, branch_sink, candidate_sink)
    raw = {key: [] for key in (*SNAPSHOTS, "actions", "mask", "components", "scalar_reward", "terminal")}
    decisions, counts = [], empty_counts()
    calls = {kind: 0 for kind in KINDS}
    position_predictions = 0
    timings = {"controller_and_branch_record_cpu_seconds": 0., "native_and_record_cpu_seconds": 0.}

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
        for t in range(horizon):
            mark = time.process_time()
            command, new_mask, decision = policy.select(t, state if t % 10 == 0 else None, old_mask)
            if t % 10 and new_mask != old_mask:
                raise ValueError("mask changed between legal boundaries")
            trace_counts(decision, counts)
            for kind in KINDS:
                calls[kind] += int(kind in decision)
            position_predictions += 216 * int("motion" in decision)
            decisions.append(decision)
            timings["controller_and_branch_record_cpu_seconds"] += time.process_time() - mark
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
            raw["components"].append([float(component[name]) for name in COMPONENTS])
            raw["scalar_reward"].append(float(reward))
            raw["terminal"].append(done)
            old_mask = new_mask
            snapshot()
            timings["native_and_record_cpu_seconds"] += time.process_time() - mark
    finally:
        env.close()
        # Retain charged completed branches and native prefix even on technical failure.
        arrays = {name: np.asarray(value) for name, value in raw.items()}
        arrays["users"] = scene.user_positions.copy()
        raw_path, trace_path = raw_dir / "native.npz", raw_dir / "native.jsonl.gz"
        with raw_path.open("xb") as stream:
            np.savez_compressed(stream, **arrays)
        write_trace(trace_path, decisions)
        catalog = {"plans": json_record(policy.plans), "selections": json_record(policy.selections),
                   "banks": json_record(policy.banks), "model_branches": branch_artifacts,
                   "candidate_banks": candidate_artifacts}
        catalog_path = raw_dir / "evidence.json.gz"
        write_catalog(catalog_path, catalog)
    timings.update(wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu)
    if len(decisions) != horizon:
        raise ValueError("incomplete native trajectory")
    return {"arm": arm, "n": 8, "world_id": scene.world_id, "runtime_seed": runtime_seed,
            "steps": horizon, "complete": True, "metrics": metrics(arrays, 8),
            "native_candidate_counts": counts, "calls": calls,
            "position_predictions": position_predictions, "timing": timings,
            "costs": episode_costs(catalog, counts, position_predictions),
            "raw": artifact(raw_path, out), "decisions": artifact(trace_path, out),
            "evidence_catalog": artifact(catalog_path, out)}


def verify_prefixes(out, rows):
    panel = {(row["arm"], row["world_id"]): row for row in rows}
    for world_id in WORLD_IDS:
        with np.load(out / panel["T", world_id]["raw"]["path"], allow_pickle=False) as reference:
            for arm, length in (("G2", 120), ("A2", 40)):
                with np.load(out / panel[arm, world_id]["raw"]["path"], allow_pickle=False) as other:
                    if set(reference.files) != set(other.files):
                        raise ValueError("matched native array keys differ")
                    for key in reference.files:
                        end = length + 1 if key in SNAPSHOTS else length
                        a, b = ((reference[key], other[key]) if key == "users"
                                else (reference[key][:end], other[key][:end]))
                        if not np.array_equal(a, b):
                            raise ValueError(f"T/{arm} prefix differs for {world_id}/{key}")


def run_study(out, launch_sha, admission):
    wall, cpu = time.perf_counter(), time.process_time()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    scenes, spec = bound_worlds(), Spec()
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("summary.json", "config.json", "raw", "reading.json")):
        raise FileExistsError("existing attempt; no implicit replay/resume")
    config = dict(fixed_config(), launch_sha=launch_sha,
                  admission_command_sha256=admission["command_sha256"],
                  versions={"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__})
    write_json(out / "config.json", config)
    summary = {"launch_sha": launch_sha, "config": config,
               "config_artifact": artifact(out / "config.json", out),
               "status": "worker", "worker_status": "incomplete", "episodes": [], "new_fits": 0, "updates": 0}
    write_json(out / "summary.json", summary)
    try:
        for index, world_id in enumerate(spec.world_ids):
            for offset in range(3):
                arm = ARMS[(index + offset) % 3]
                row = evaluate_episode(arm, scenes[world_id], seed(world_id, 3, 8), out)
                summary["episodes"].append(row)
                write_json(out / "summary.json", summary)
                print(json.dumps({"worker_episodes_complete": len(summary["episodes"]),
                                  "world_id": world_id, "arm": arm}), flush=True)
        verify_prefixes(out, summary["episodes"])
        if source_bindings() != config["source_bindings"]:
            raise ValueError("source/input bytes mutated during collection")
        if len(summary["episodes"]) != 48 or sum(row["steps"] for row in summary["episodes"]) != 24000:
            raise ValueError("complete fixed panel missing")
        summary["worker_status"], summary["status"] = "complete", "collected"
        summary["worker_timing"] = {"wall_seconds": time.perf_counter() - wall,
                                    "cpu_seconds": time.process_time() - cpu,
                                    "process_resources": process_resources()}
        write_json(out / "summary.json", summary)
        from .reader import read_run
        read_run(out)
        summary["reading"] = artifact(out / "reading.json", out)
        summary["status"] = "complete"
        summary["total_timing"] = {"wall_seconds": time.perf_counter() - wall,
                                   "cpu_seconds": time.process_time() - cpu,
                                   "process_resources": process_resources()}
        write_json(out / "summary.json", summary)
        return summary
    except BaseException as exc:
        summary["failure_stage"] = "reader" if summary["status"] == "collected" else "worker"
        summary["status"], summary["error"] = "failed", f"{type(exc).__name__}: {exc}"
        summary["failed_timing"] = {"wall_seconds": time.perf_counter() - wall,
                                    "cpu_seconds": time.process_time() - cpu,
                                    "process_resources": process_resources()}
        write_json(out / "summary.json", summary)
        raise
