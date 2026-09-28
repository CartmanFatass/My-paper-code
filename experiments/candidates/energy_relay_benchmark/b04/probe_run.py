"""Orchestration of ``b04_geometry_probe_a01`` Blocks 0-2 (records, progress, manifest).

Outputs under ``<out>``: ``block0/{blob_stat,heading_stat,speed_stat,capacity_vs_distance}.json``,
``block1/{conditions,readings,identity_gate}.json`` + ``proposals.npz``,
``block2/paired_rotation.json``, ``progress.jsonl`` (one event per world x condition x t),
``manifest.json`` and ``summary.json`` (status for the launcher).  Workers: spawn pool over worlds, serial when ``workers <= 1``.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import torch

from ..b01.evaluation import WorldTask, make_eval_config
from ..b01.feedback import PRODUCTION_PARAMS
from . import deployment_readers, geometry_probe as gp, readings as rd

ROOT = Path(__file__).resolve().parents[4]
CHECKPOINT = "runs/energy_relay_benchmark/b02_s1_set_a01r/checkpoints/c06"
NODE_TRACE = ("runs/energy_relay_benchmark/b02_s1_eval_c06_a01/checkpoint-eval/traces/"
              "L_c06_deterministic_e0.00_x0.05.npz")
RECORDED_PANEL = ("runs/energy_relay_benchmark/b02_s1_eval_c06_a01/checkpoint-eval/panels/"
                  "L_c06_deterministic_e0.00_x0.05.json")
WORLDS = tuple(range(955001, 955033))
TRACE_MATCH_M = 1.0
CAPACITY_WORLD = 955001
MOBILITY_NOTE = ("Block 2 ROT reflects every entity at t = 0 only; user-mobility (RPGM) random draws "
                 "after t = 0 are not reflected, so the rotated world is a reflection in distribution, "
                 "not path-wise.")


def _clean(value):
    return gp._jsonable(value)


def write_json(path: Path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(_clean(payload), indent=1, sort_keys=True, allow_nan=False),
                         encoding="utf-8")
    os.replace(temporary, path)


def progress(out: Path, event: dict) -> None:
    with (Path(out) / "progress.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_clean({"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                        **event}), sort_keys=True) + "\n")


def _fresh(directory: Path) -> Path:
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError(f"{directory} already holds outputs")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def run_pool(function: Callable, tasks: Iterable, workers: int, on_result: Callable) -> list:
    tasks = list(tasks)
    results = []
    if int(workers) <= 1 or len(tasks) <= 1:
        for task in tasks:
            results.append(function(task))
            on_result(results[-1])
    else:
        with multiprocessing.get_context("spawn").Pool(processes=min(int(workers), len(tasks))) as pool:
            for result in pool.imap(function, tasks, chunksize=1):
                results.append(result)
                on_result(result)
    return results


def run_block0(out: Path, *, access: dict | None, root: Path = ROOT, threads: int = 2) -> dict:
    directory = _fresh(Path(out) / "block0")
    torch.set_num_threads(int(threads))
    sources = deployment_readers.block0(str(directory), access=access, root=str(root))
    for name in sources:
        progress(out, {"block": 0, "group": name})
    config = make_eval_config(gp.HORIZON, 925031)
    write_json(directory / "capacity_vs_distance.json", gp.capacity_vs_distance(config, CAPACITY_WORLD))
    return {"groups": sources, "access_join": access is not None}


def load_access(out: Path) -> dict | None:
    path = Path(out) / "block1" / "conditions.json"
    if not path.exists():
        return None
    worlds = json.loads(path.read_text(encoding="utf-8"))["worlds"]
    return {int(seed): int(row["users_in_access_range_t0"]) for seed, row in worlds.items()}


def run_block1(out: Path, *, worlds, checkpoint: Path, workers: int, threads: int,
               node_trace: Path | None) -> dict:
    directory = _fresh(Path(out) / "block1")
    logs = directory / "logs"
    logs.mkdir()
    tasks = [gp.ProbeTask(seed=int(seed), checkpoint_dir=str(checkpoint), threads=int(threads),
                          node_trace=str(node_trace) if node_trace else None, log_dir=str(logs))
             for seed in worlds]

    def advance(result):
        for t in gp.QUERY_STEPS:
            for condition in gp.CONDITIONS:
                progress(out, {"block": 1, "seed": result["seed"], "condition": condition, "t": t})

    results = sorted(run_pool(gp.probe_world, tasks, workers, advance), key=lambda r: r["seed"])
    logs.rmdir()
    seeds = [r["seed"] for r in results]
    arrays = {key: np.stack([r["arrays"][key] for r in results]) for key in results[0]["arrays"]}
    matching = np.array([[r["conditions"][c].get("matching", list(range(arrays["proposals"].shape[-2])))
                          for c in gp.CONDITIONS] for r in results], dtype=np.int64)
    exact = np.array([[r["conditions"][c].get("exact_match", [True] * matching.shape[-1])
                       for c in gp.CONDITIONS] for r in results], dtype=bool)
    np.savez_compressed(directory / "proposals.npz", seeds=np.asarray(seeds, dtype=np.int64),
                        conditions=np.asarray(gp.CONDITIONS), query_steps=np.asarray(gp.QUERY_STEPS),
                        planners=np.asarray(gp.PLANNERS), matching=matching, exact_match=exact, **arrays)
    write_json(directory / "conditions.json", {
        "conditions": list(gp.CONDITIONS), "declared_consistent_in_support": gp.DECLARED,
        "rules": {"displacement_m": gp.DISPLACEMENT_M, "bs_sign": gp.BS_SIGN_RULE,
                  "cluster": gp.CL_CLUSTER, "cluster_axes": gp.CL_AXES,
                  "cluster_sign": "toward the central square's centre along the axis",
                  "st_rng": f"RandomState([seed, {gp.ST_RNG_SALT}])",
                  "matching": f"pairs < {gp.MATCH_EXACT_M} m first, remainder by min-cost assignment",
                  "reflections": {k: list(v) for k, v in gp.REFLECTIONS.items()}},
        "support_rules": gp.SUPPORT_RULES,
        "worlds": {str(r["seed"]): {"users_in_access_range_t0": r["users_in_access_range_t0"],
                                    "conditions": r["conditions"]} for r in results}})
    write_json(directory / "readings.json", rd.readings(arrays, matching, exact))
    rows = {str(r["seed"]): {"gate_a_id_equals_reset": r["gate_a"],
                             "trace_max_abs_m": (r["trace"] or {}).get("max_abs_m"),
                             "trace_match": (None if not r["trace"] or r["trace"]["max_abs_m"] is None
                                             else bool(r["trace"]["max_abs_m"] <= TRACE_MATCH_M)),
                             "id_construct_max_abs_obs_state": r["diagnostics"]["id_construct_max_abs"],
                             "id_query_repeat_exact": r["diagnostics"]["id_query_repeat_exact"],
                             "hidden_digests_per_t": {t: len(v) for t, v in r["diagnostics"]["hidden_digest"].items()},
                             "wall_seconds": r["wall_seconds"]} for r in results}
    gate = {"gate_passed": bool(len(results) == len(list(worlds)) and all(r["gate_a"] for r in results)),
            "gate_rule": "(a) constructed ID observations and state equal plain env.reset(seed) bitwise for every seed",
            "trace_match_tolerance_m": TRACE_MATCH_M, "node_trace": str(node_trace) if node_trace else None,
            "trace_match_all": all(row["trace_match"] for row in rows.values()),
            "seeds": rows}
    write_json(directory / "identity_gate.json", gate)
    timings = {key: float(np.mean([np.mean(r["diagnostics"]["timings_s"][key]) for r in results]))
               for key in ("plan_conditions", "construct_world_ID_t0", "condition_query", "id_step")}
    return {"worlds": seeds, "identity": results[0]["identity"], "gate_passed": gate["gate_passed"],
            "id_prefix_steps": gp.PREFIX_STEPS * len(results), "constructed_worlds":
            len(results) * len(gp.QUERY_STEPS) * len(gp.CONDITIONS), "mean_timings_s": timings}


def run_block2(out: Path, *, worlds, checkpoint: Path, workers: int, threads: int,
               recorded_panel: Path, horizon: int = gp.HORIZON) -> dict:
    directory = _fresh(Path(out) / "block2")
    logs = directory / "logs"
    logs.mkdir()
    record = json.loads((Path(checkpoint) / "record.json").read_text(encoding="utf-8"))
    tasks = [WorldTask(controller="L", seed=int(seed), params=PRODUCTION_PARAMS, horizon=int(horizon),
                       policy_seed=int(record["training_seed"]), threads=int(threads),
                       checkpoint=str(Path(checkpoint) / record["agent_pt"]),
                       expected_checkpoint_sha256=record["agent_pt_sha256"],
                       expected_policy_fingerprint=record["policy_fingerprint"],
                       log_dir=str(logs), checkpoint_record=str(Path(checkpoint) / "record.json"))
             for seed in worlds]

    def advance(result):
        progress(out, {"block": 2, "seed": result["row"]["seed"], "condition": result["condition"], "t": "H"})

    jobs = [(condition, task) for task in tasks for condition in ("ID", "ROT")]
    results = run_pool(gp.block2_episode, jobs, workers, advance)
    logs.rmdir()
    by = {c: sorted((r for r in results if r["condition"] == c), key=lambda r: r["row"]["seed"])
          for c in ("ID", "ROT")}
    rows = {c: [{**r["row"], "in_support": r["construction"]["in_support"]} for r in by[c]] for c in by}
    panel = json.loads(Path(recorded_panel).read_text(encoding="utf-8"))
    payload = paired = gp.paired_rotation(rows["ROT"], rows["ID"], panel)
    payload.update(condition="ROT", horizon=int(horizon), recorded_panel=str(recorded_panel),
                   recorded_panel_sha256=_sha256(Path(recorded_panel)),
                   primary="summary.primary_rot_minus_local_id (local ROT - local ID, same host, same path)",
                   local_id_rows=rows["ID"], rotated_rows=rows["ROT"],
                   constructions={str(r["row"]["seed"]): r["construction"] for r in by["ROT"]},
                   identity=[r["identity"] for r in results][:1],
                   mobility_note=MOBILITY_NOTE)
    write_json(directory / "paired_rotation.json", payload)
    return {"worlds": [r["row"]["seed"] for r in by["ROT"]], "episodes": len(results),
            "local_id_episodes": len(by["ID"]), "rot_episodes": len(by["ROT"]),
            "steps": int(sum(r["row"]["actual_length"] for r in results)),
            "summary": paired["summary"],
            "mean_episode_wall_s": float(np.mean([r["row"]["wall_seconds"] for r in results]))}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def module_sources(root: Path = ROOT) -> dict[str, str]:
    """sha256 of every loaded module file inside the checkout."""
    result = {}
    for module in list(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if not path:
            continue
        path = Path(path).resolve()
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if path.suffix == ".py" and path.is_file():
            result[relative.as_posix()] = _sha256(path)
    return dict(sorted(result.items()))


def input_identities(checkpoint: Path, node_trace: Path | None, recorded_panel: Path | None) -> dict:
    """Digests of the gitignored inputs (outside the admitted snapshot's SHA and command digest).
    The saved ``agent.pt`` must match the digest its own ``record.json`` carries."""
    checkpoint = Path(checkpoint)
    record = json.loads((checkpoint / "record.json").read_text(encoding="utf-8"))
    agent = checkpoint / record["agent_pt"]
    agent_sha = _sha256(agent)
    if agent_sha != record["agent_pt_sha256"]:
        raise RuntimeError(f"{agent}: sha256 {agent_sha} != record.json agent_pt_sha256 "
                           f"{record['agent_pt_sha256']}")
    identities = {"checkpoint_record": {"path": str(checkpoint / "record.json"),
                                        "sha256": _sha256(checkpoint / "record.json"),
                                        "launch_sha": record.get("launch_sha")},
                  "agent_pt": {"path": str(agent), "sha256": agent_sha, "bytes": agent.stat().st_size}}
    for name, path in (("node_trace", node_trace), ("recorded_panel", recorded_panel)):
        identities[name] = ({"path": str(path), "sha256": _sha256(path)}
                            if path is not None and Path(path).is_file() else None)
    return identities


def write_manifest(out: Path, *, command: str, launch_sha: str, argv, threads: int, workers: int,
                   checkpoint: Path, blocks: dict, started: float, data_root: Path = ROOT,
                   inputs: dict | None = None) -> dict:
    record = json.loads((Path(checkpoint) / "record.json").read_text(encoding="utf-8"))
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:   # pragma: no cover
        head = None
    manifest = {
        "kind": "zero_fit_probe_of_saved_model", "probe": Path(out).name, "command": command,
        "data_root": str(data_root), "code_root": str(ROOT),
        "launch_sha": launch_sha, "git_head": head, "argv": list(argv),
        "new_episodes": {"block1_id_prefixes": len(blocks.get("block1", {}).get("worlds", [])),
                         "block1_prefix_steps": blocks.get("block1", {}).get("id_prefix_steps", 0),
                         "block1_constructed_worlds": blocks.get("block1", {}).get("constructed_worlds", 0),
                         "block2_full_episodes": blocks.get("block2", {}).get("episodes", 0),
                         "block2_local_id_episodes": blocks.get("block2", {}).get("local_id_episodes", 0),
                         "block2_rot_episodes": blocks.get("block2", {}).get("rot_episodes", 0),
                         "block2_steps": blocks.get("block2", {}).get("steps", 0)},
        "fits": 0, "block2_rotation": MOBILITY_NOTE,
        "checkpoint": str(checkpoint), "checkpoint_sha256": record["agent_pt_sha256"], "inputs": inputs,
        "policy_fingerprint": record["policy_fingerprint"], "training_seed": record["training_seed"],
        "interpreter": sys.executable, "torch_version": torch.__version__, "threads": int(threads),
        "workers": int(workers), "os_cpu_count": os.cpu_count(), "blocks": blocks,
        "sources": module_sources(), "wall_seconds": time.perf_counter() - started,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    write_json(Path(out) / "manifest.json", manifest)
    return manifest


def run(command: str, *, out: Path, launch_sha: str, workers: int = 1, threads: int = 2,
        worlds=WORLDS, checkpoint: Path | None = None, node_trace: Path | None = None,
        recorded_panel: Path | None = None, data_root: Path = ROOT, argv=None) -> dict:
    """``data_root`` is the checkout that holds ``runs/`` (gitignored checkpoints, traces and
    panels); under a ``--snapshot`` launch the code root is a source worktree without them."""
    if workers < 1 or threads < 1 or workers * threads > (os.cpu_count() or 1):
        raise ValueError("workers x threads must be positive and within os.cpu_count()")
    data_root = Path(data_root)
    checkpoint = Path(checkpoint) if checkpoint is not None else data_root / CHECKPOINT
    node_trace = Path(node_trace) if node_trace is not None else data_root / NODE_TRACE
    recorded_panel = Path(recorded_panel) if recorded_panel is not None else data_root / RECORDED_PANEL
    started = time.perf_counter()
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    blocks: dict[str, Any] = {}
    inputs = input_identities(checkpoint, node_trace if command in ("block1", "all") else None,
                              recorded_panel if command in ("block2", "all") else None)
    summary = {"probe": Path(out).name, "command": command, "launch_sha": launch_sha, "data_root": str(data_root),
               "code_root": str(ROOT), "inputs": inputs,
               "status": "INCOMPLETE", "failure": None, "worlds": [int(w) for w in worlds]}
    write_json(out / "summary.json", summary)
    try:
        if command in ("block1", "all"):
            blocks["block1"] = run_block1(out, worlds=worlds, checkpoint=checkpoint, workers=workers,
                                          threads=threads, node_trace=node_trace)
        if command in ("block0", "all"):
            blocks["block0"] = run_block0(out, access=load_access(out), root=data_root, threads=threads)
        if command in ("block2", "all"):
            blocks["block2"] = run_block2(out, worlds=worlds, checkpoint=checkpoint, workers=workers,
                                          threads=threads, recorded_panel=recorded_panel)
        summary["status"] = "COMPLETE"
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        summary["blocks"] = {name: {key: value for key, value in block.items() if key != "groups"}
                             for name, block in blocks.items()}
        summary["wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)
    return write_manifest(out, command=command, launch_sha=launch_sha, argv=argv or sys.argv,
                          threads=threads, workers=workers, checkpoint=checkpoint, blocks=blocks,
                          started=started, data_root=data_root, inputs=inputs)
