"""B01 zero-new-training reference study: shield margins x controllers on S7-S2/H3000.

Phases (``all`` runs them in this order): ``equivalence`` (N at production margins on the B09
worlds, CPU J recorded next to B09's CUDA J), ``null`` (N at production margins on B10's O
worlds, J and QoS/step recorded next to B10 O), ``heuristic-dev`` (central H1-H3 on the
development worlds; selection), ``reference`` (the selected variant with local information,
``Hlocal``) and ``grid`` (N and the selected central heuristic over the width-matched shield
settings).  Nothing is gated on a recorded difference.
"""

from __future__ import annotations

import json
import os
import resource
import sys
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _json_default,
    active_config,
    sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b09.persistence import write_summary

from .evaluation import PLAN_SOURCE, WorldTask, aggregate, make_eval_config, run_tasks, trace_arrays
from .feedback import PRODUCTION_PARAMS, FeedbackParams
from .heuristic import CONTROLLER_INFORMATION, VARIANTS, HeuristicParams
from .observation import S7S2_LAYOUT

OBJECT_ID = "ENERGY-RELAY-BENCHMARK-B01"
DIRECTION = "energy_relay_benchmark"
RUN_PHASES = ("equivalence", "null", "heuristic-dev", "reference", "grid")
PHASES = (*RUN_PHASES, "all")
HEURISTICS = ("H1", "H2", "H3")
LOCAL_CONTROLLER = "Hlocal"
CONTROLLERS = ("N", *HEURISTICS)
# Recorded B09 N endpoint (summary.json of b09_an_925031_a01, launch e5e53534c2c0).
B09_CHECKPOINT_SHA256 = "2ba395b9f2761a9a761bd648d399b525c61b7babdb84edbe293319d269eeff5a"
B09_POLICY_FINGERPRINT = "aa197872405be04a95f608989ce485566e34fa35117d44335663f5fd35d39dc0"
B09_N_PRIMARY_J = {  # evaluations.N_primary.worlds[*].raw_native_J (CUDA, policy seed 925031)
    952001: 862.7014303196436,
    952002: 1255.708904363555,
    952003: 1204.7857076563273,
    952004: 658.181633754916,
}
# B10 O panel (production shield, CUDA, policy seed 925031, H3000; launch 3be662f4ae59), used
# only as the device-null reference.  Source file and its sha256 (tracked in git):
B10_O_REFERENCE_PATH = "runs/uav_service_auxiliary/b10_oc_925031_a01/summary.json"
B10_O_REFERENCE_SHA256 = "2e3d82c43fea87d821259af3e3a69f6eb74381e78a239473a42c3b38019e7fa2"
B10_O_REFERENCE = {  # seed: (raw_native_J, qos_per_actual_step) from panels.O.worlds[*]
    953001: (1528.7640442916645, 0.5201438637751874),
    953002: (1557.0776805240653, 0.5296084166566922),
    953003: (769.1412170154532, 0.2667464976274547),
    953004: (934.648657462849, 0.3215961689303606),
    953005: (1365.1670074476274, 0.4649557558284792),
    953006: (941.2205531353746, 0.32310078360853683),
    953007: (1164.467726814188, 0.39859272901404713),
    953008: (900.6660804373346, 0.3108181950728065),
    953009: (583.6827453463374, 0.20326003500861214),
    953010: (916.5317867335237, 0.3151144327728363),
    953011: (1333.2259210176994, 0.45500044806702694),
    953012: (1286.412665955495, 0.43933749663958893),
    953013: (643.5494006364218, 0.22342062736613924),
    953014: (331.9111791247678, 0.11816499656207988),
    953015: (801.9737163230866, 0.27755349196124796),
    953016: (1108.216237066437, 0.37917232132035794),
    953017: (1630.5250222124844, 0.5537990367977282),
    953018: (1645.049300448085, 0.5590198567738366),
    953019: (1131.0059868328185, 0.38681434966597067),
    953020: (994.150642318319, 0.3411975077325165),
    953021: (1885.2972802308118, 0.6390832808780486),
    953022: (73.76571641294598, 0.034362505510490554),
    953023: (307.2354901892533, 0.10969721149221148),
    953024: (490.39211394104444, 0.17397857641223208),
    953025: (1537.654917747826, 0.5227745222510616),
    953026: (1384.8942212876193, 0.49130339060181183),
    953027: (1064.312239897153, 0.3746485563048156),
    953028: (-32.15356141596002, 0.0),
    953029: (703.1724050553105, 0.2432488675532097),
    953030: (1211.7072982565005, 0.414355421100984),
    953031: (1023.9035377061232, 0.3517882559504283),
    953032: (733.3629745252543, 0.25516142917685114),
}

NULL_PERCENTILES = (50, 95)
GRID_SETTINGS = ((0.0, 0.05), (0.0, 0.25), (0.0, 0.45), (0.0, 0.85),
                 (0.20, 0.25), (0.20, 0.45), (0.20, 0.65))
EXPOSURE_NOTE = ("955xxx/956xxx unexposed on S7 before B01; 953xxx = B10 O panel, null only; "
                 "952001–4 = B09 equivalence only; heuristic selection domain = dev_worlds only")


def default_workers() -> int:
    return max(1, min(8, (os.cpu_count() or 1) // 2))


DEFAULT_THREADS = 2


@dataclass(frozen=True)
class B01Spec:
    worlds: tuple[int, ...] = tuple(range(955001, 955033))           # reference + grid
    dev_worlds: tuple[int, ...] = tuple(range(956001, 956009))       # heuristic-dev only
    null_worlds: tuple[int, ...] = tuple(range(953001, 953033))      # B10 O worlds, null only
    equivalence_worlds: tuple[int, ...] = (952001, 952002, 952003, 952004)
    grid_settings: tuple[tuple[float, float], ...] = GRID_SETTINGS  # (enter, exit), ordered
    heuristic: str = "H1"            # selected variant when reference/grid run without dev
    controllers: tuple[str, ...] | None = None   # grid alone: None -> ("N", heuristic)
    threads: int = DEFAULT_THREADS
    workers: int = field(default_factory=default_workers)
    policy_seed: int = 925031   # B09/B10 evaluator seed: the null and equivalence phases compare device only
    replan_period: int = 30
    horizon: int = 3000
    checkpoint_sha256: str | None = B09_CHECKPOINT_SHA256
    policy_fingerprint: str | None = B09_POLICY_FINGERPRINT


def check_resources(spec: B01Spec, cpu_count: int | None = None) -> None:
    """Refuse oversubscription: workers x threads may not exceed the host's CPU count."""
    cpus = int(cpu_count if cpu_count is not None else (os.cpu_count() or 1))
    if spec.workers < 1 or spec.threads < 1:
        raise ValueError("workers and threads must be positive")
    if spec.workers * spec.threads > cpus:
        raise ValueError(
            f"workers x threads = {spec.workers} x {spec.threads} exceeds os.cpu_count() = {cpus}")


def feedback_grid(spec: B01Spec) -> list[FeedbackParams]:
    """The explicit ordered (enter, exit) settings."""
    return [FeedbackParams(enter, exit_) for enter, exit_ in spec.grid_settings]


def setting_width(params: FeedbackParams) -> float:
    return round(params.exit_margin - params.enter_margin, 2)


def matched_pair_id(params: FeedbackParams, spec: B01Spec) -> str | None:
    """``w<width>`` when >= 2 grid settings share this setting's width, else None."""
    width = setting_width(params)
    shared = sum(setting_width(other) == width for other in feedback_grid(spec))
    in_grid = any(other == params for other in feedback_grid(spec))
    return f"w{width:.2f}" if in_grid and shared >= 2 else None


def grid_record(spec: B01Spec) -> list[dict[str, Any]]:
    return [asdict(params) | {"label": params.label, "width": setting_width(params),
                              "matched_pair_id": matched_pair_id(params, spec)}
            for params in feedback_grid(spec)]


def world_roles(spec: B01Spec) -> dict[str, Any]:
    return {"worlds": list(spec.worlds), "dev_worlds": list(spec.dev_worlds),
            "null_worlds": list(spec.null_worlds),
            "equivalence_worlds": list(spec.equivalence_worlds),
            "exposure_note": EXPOSURE_NOTE}


def grid_controllers(spec: B01Spec) -> tuple[str, ...]:
    return tuple(spec.controllers) if spec.controllers is not None else ("N", spec.heuristic)


def heuristic_params(name: str, spec: B01Spec, selected: str | None = None) -> HeuristicParams:
    """H1-H3: central variants.  Hlocal: the selected central variant with local information."""
    if name == LOCAL_CONTROLLER:
        base = selected or spec.heuristic
        return replace(VARIANTS[base], replan_period=int(spec.replan_period), information="local")
    return replace(VARIANTS[name], replan_period=int(spec.replan_period))


def controller_information(controller: str, spec: B01Spec, selected: str | None = None) -> str:
    if controller == "N":
        return "legal-observation"
    return CONTROLLER_INFORMATION[heuristic_params(controller, spec, selected).information]


def phase_panels(phase: str, spec: B01Spec, controllers=None):
    """(controller, params, worlds) per panel; ``controllers`` overrides the grid's."""
    if phase == "equivalence":
        return [("N", PRODUCTION_PARAMS, tuple(spec.equivalence_worlds))]
    if phase == "null":
        return [("N", PRODUCTION_PARAMS, tuple(spec.null_worlds))]
    if phase == "heuristic-dev":
        return [(name, PRODUCTION_PARAMS, tuple(spec.dev_worlds)) for name in HEURISTICS]
    if phase == "reference":
        return [(LOCAL_CONTROLLER, PRODUCTION_PARAMS, tuple(spec.worlds))]
    if phase == "grid":
        chosen = grid_controllers(spec) if controllers is None else tuple(controllers)
        return [(controller, params, tuple(spec.worlds))
                for controller in chosen for params in feedback_grid(spec)]
    raise ValueError(f"phase must be one of {RUN_PHASES}")


def panel_name(controller: str, params: FeedbackParams) -> str:
    return f"{controller}_{params.label}"


def select_heuristic(panels: dict[str, dict]) -> tuple[str, dict[str, float]]:
    """Best heuristic by panel mean raw native J at production params; ties -> H order."""
    scores = {name: panels[panel_name(name, PRODUCTION_PARAMS)]["aggregate"]["mean_raw_native_J"]
              for name in HEURISTICS}
    best = max(HEURISTICS, key=lambda name: (scores[name], -HEURISTICS.index(name)))
    return best, scores


def null_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-world B01 (CPU) minus B10 O (CUDA) J and QoS/step; percentiles of |delta|.  Record only."""
    worlds, abs_j, abs_q = [], [], []
    for row in rows:
        seed = int(row["seed"])
        reference = B10_O_REFERENCE.get(seed)
        entry: dict[str, Any] = {"seed": seed, "failed": bool(row.get("failed"))}
        if not row.get("failed"):
            entry.update(J=row["raw_native_J"], qos_per_step=row["qos_per_step"],
                         actual_length=row["actual_length"])
        if reference is not None:
            entry.update(b10_J=reference[0], b10_qos_per_actual_step=reference[1])
        if reference is not None and not row.get("failed"):
            entry.update(delta_J=row["raw_native_J"] - reference[0],
                         delta_qos_per_step=row["qos_per_step"] - reference[1])
            abs_j.append(abs(entry["delta_J"]))
            abs_q.append(abs(entry["delta_qos_per_step"]))
        else:
            entry.update(delta_J=None, delta_qos_per_step=None)
        worlds.append(entry)
    block: dict[str, Any] = {
        "reference_path": B10_O_REFERENCE_PATH, "reference_sha256": B10_O_REFERENCE_SHA256,
        "reference_keys": ["raw_native_J", "qos_per_actual_step"],
        "sign": "B01 minus B10 O", "gate": None, "worlds": worlds, "compared_worlds": len(abs_j),
    }
    for label, values in (("J", abs_j), ("qos_per_step", abs_q)):
        array = np.asarray(values, dtype=np.float64)
        for q in NULL_PERCENTILES:
            block[f"abs_delta_{label}_p{q}"] = (float(np.percentile(array, q)) if array.size
                                                else None)
        block[f"abs_delta_{label}_max"] = float(array.max()) if array.size else None
    return block


def config_record(spec: B01Spec, phase: str, *, launch_sha: str, checkpoint, device: str,
                  argv) -> dict[str, Any]:
    config = make_eval_config(spec.horizon, spec.policy_seed)
    phases = RUN_PHASES if phase == "all" else (phase,)
    planned = {}
    for name in phases:
        if name == "grid" and phase == "all":
            planned[name] = {"controllers": ["N", "<selected_heuristic>"],
                             "grid_settings": grid_record(spec), "worlds": list(spec.worlds)}
        elif name == "reference" and phase == "all":
            planned[name] = {"controller": LOCAL_CONTROLLER,
                             "params_from": "<selected_heuristic> with information='local'",
                             "feedback": asdict(PRODUCTION_PARAMS), "worlds": list(spec.worlds)}
        else:
            planned[name] = [{"name": panel_name(c, p), "controller": c, "params": asdict(p),
                              "worlds": list(w)} for c, p, w in phase_panels(name, spec)]
    return {
        "object_id": OBJECT_ID,
        "launch_sha": launch_sha,
        "phase": phase,
        "argv": list(argv),
        "device": device,
        "os_cpu_count": os.cpu_count(),
        "spec": asdict(spec),
        "world_roles": world_roles(spec),
        "active": json.loads(json.dumps(active_config(config)), parse_constant=str),
        "checkpoint": None if checkpoint is None else str(checkpoint),
        "checkpoint_sha256": None if checkpoint is None else sha256_file(Path(checkpoint)),
        "grid_settings": grid_record(spec),
        "planned_panels": planned,
        "heuristic_selection_rule": ("max panel mean raw_native_J at (0, .05) over H1-H3 on "
                                     "dev_worlds; tie -> lower H index"),
        "heuristic_variants": {name: heuristic_params(name, spec).record() for name in VARIANTS},
        "local_heuristic": {"controller": LOCAL_CONTROLLER,
                            "params": heuristic_params(LOCAL_CONTROLLER, spec).record()
                            if phase != "all" else "selected variant with information='local'"},
        "controller_information": {name: controller_information(name, spec)
                                   for name in (*CONTROLLERS, LOCAL_CONTROLLER)},
        "heuristic_plan_source": PLAN_SOURCE,
        "observation_layout": S7S2_LAYOUT.record(),
        "b09_equivalence_reference_J": {str(k): v for k, v in B09_N_PRIMARY_J.items()},
        "b10_null_reference": {"path": B10_O_REFERENCE_PATH, "sha256": B10_O_REFERENCE_SHA256,
                               "worlds": {str(k): {"raw_native_J": v[0], "qos_per_actual_step": v[1]}
                                          for k, v in B10_O_REFERENCE.items()}},
        "null_percentiles": list(NULL_PERCENTILES),
        "controller_boundary": ("N: legal per-UAV observation only. H1-H3: central-information "
                                "reference; k-means/relay planning from ground-truth user and BS "
                                "xy at replan steps, own position/modes/shield from the legal "
                                "observation. Hlocal: the selected variant planned from the legal "
                                "observations only (pooled decoded users, observed BS, station-1 "
                                "ring search prior while fewer than n_service users are visible)."),
    }


def _progress(out: Path, event: dict[str, Any]) -> None:
    event = {"time": time.time(), **event}
    with (out / "progress.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=_json_default, allow_nan=False,
                                separators=(",", ":")) + "\n")
        handle.flush()


def run_native(*, out: Path, launch_sha: str, checkpoint: Path | None, phase: str,
               spec: B01Spec | None = None, device_name: str = "cpu", argv=None):
    spec = spec or B01Spec()
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}")
    check_resources(spec)
    if spec.heuristic not in HEURISTICS:
        raise ValueError(f"heuristic must be one of {HEURISTICS}")
    unknown = set(grid_controllers(spec)) - set(CONTROLLERS)
    if unknown:
        raise ValueError(f"unknown controllers {sorted(unknown)}")
    phases = RUN_PHASES if phase == "all" else (phase,)
    needs_n = phase == "all" or any(
        c == "N" for name in phases for c, _, _ in phase_panels(name, spec))
    if needs_n and checkpoint is None:
        raise ValueError("controller N requires --checkpoint")
    if checkpoint is not None and spec.checkpoint_sha256 is not None:
        if sha256_file(Path(checkpoint)) != spec.checkpoint_sha256:
            raise ValueError("checkpoint sha256 does not match the recorded B09 N endpoint")
    out = Path(out)
    if any((out / name).exists() for name in
           ("summary.json", "config.json", "progress.jsonl", *RUN_PHASES)):
        raise FileExistsError(f"B01 output already exists: {out}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    started = time.perf_counter()
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "phase": phase, "phases": list(phases),
        "device": device_name, "threads": spec.threads, "workers": spec.workers,
        "os_cpu_count": os.cpu_count(),
        "world_roles": world_roles(spec),
        "grid_settings": grid_record(spec),
        "controller_information": {name: controller_information(name, spec)
                                   for name in (*CONTROLLERS, LOCAL_CONTROLLER)},
        "heuristic_plan_source": PLAN_SOURCE,
        "counts": {"episodes_completed": 0, "steps": 0, "panels_completed": 0,
                   "failed_worlds": 0, "new_fits": 0, "optimizer_updates": 0},
        "panels": {}, "phase_results": {}, "artifacts": {},
    }
    write_summary(out / "config.json", config_record(
        spec, phase, launch_sha=launch_sha, checkpoint=checkpoint, device=device_name,
        argv=sys.argv if argv is None else argv))
    summary["artifacts"]["config.json"] = sha256_file(out / "config.json")
    write_summary(out / "summary.json", summary)
    _progress(out, {"event": "run_start", "phase": phase, "phases": list(phases),
                    "workers": spec.workers, "threads": spec.threads})
    selected = spec.heuristic

    def run_panel(phase_name: str, controller: str, params: FeedbackParams, worlds):
        name = panel_name(controller, params)
        root = out / phase_name
        (root / "panels").mkdir(parents=True, exist_ok=True)
        (root / "traces").mkdir(parents=True, exist_ok=True)
        _progress(out, {"event": "panel_start", "phase": phase_name, "panel": name,
                        "worlds": len(worlds)})
        panel_started = time.perf_counter()
        hparams = (heuristic_params(controller, spec, selected)
                   if controller.startswith("H") else None)
        tasks = [WorldTask(
            controller=controller, seed=int(seed), params=params, horizon=spec.horizon,
            policy_seed=spec.policy_seed, threads=spec.threads, device=device_name,
            checkpoint=None if controller != "N" else str(checkpoint),
            expected_checkpoint_sha256=spec.checkpoint_sha256 if controller == "N" else None,
            expected_policy_fingerprint=spec.policy_fingerprint if controller == "N" else None,
            heuristic=hparams, log_dir=str(out / "logs"),
        ) for seed in worlds]

        def advance(result):
            row = result["row"]
            summary["counts"]["episodes_completed"] += 1
            summary["counts"]["steps"] += int(row.get("actual_length", 0))
            summary["counts"]["failed_worlds"] += int(bool(row.get("failed")))
            _progress(out, {"event": "world_end", "phase": phase_name, "panel": name,
                            "seed": row["seed"], "failed": bool(row.get("failed")),
                            "episodes_completed": summary["counts"]["episodes_completed"]})

        results = run_tasks(tasks, spec.workers, on_result=advance)
        rows = [result["row"] for result in results]
        for row in rows:
            row.update(width=setting_width(params), matched_pair_id=matched_pair_id(params, spec))
        identities = {json.dumps(result["identity"], sort_keys=True) for result in results}
        panel = {"name": name, "phase": phase_name, "controller": controller,
                 "controller_information": controller_information(controller, spec, selected),
                 "params": asdict(params), "width": setting_width(params),
                 "matched_pair_id": matched_pair_id(params, spec),
                 "worlds": rows, "aggregate": aggregate(rows),
                 "failed_worlds": [row["seed"] for row in rows if row.get("failed")],
                 "policy_identity": [json.loads(item) for item in sorted(identities)],
                 "wall_seconds": time.perf_counter() - panel_started}
        if hparams is not None:
            panel["plan_source"] = PLAN_SOURCE if hparams.information == "central" else "legal-observation"
            panel["heuristic_params"] = hparams.record()
            if controller == LOCAL_CONTROLLER:
                panel["params_from_variant"] = selected
        if phase_name == "equivalence":
            # Record only: a CPU/CUDA J difference never stops the run.
            panel["b09_reference"] = [
                {"seed": row["seed"], "J": row.get("raw_native_J"),
                 "b09_J": B09_N_PRIMARY_J.get(row["seed"]),
                 "delta_J": (None if row["seed"] not in B09_N_PRIMARY_J or row.get("failed")
                             else row["raw_native_J"] - B09_N_PRIMARY_J[row["seed"]])}
                for row in rows]
        if phase_name == "null":
            panel["b10_reference"] = null_block(rows)
            summary["null"] = panel["b10_reference"]
        panel_path = root / "panels" / f"{name}.json"
        write_summary(panel_path, panel)
        trace_path = root / "traces" / f"{name}.npz"
        np.savez_compressed(trace_path, **trace_arrays(results))
        summary["artifacts"][str(panel_path.relative_to(out))] = sha256_file(panel_path)
        summary["artifacts"][str(trace_path.relative_to(out))] = sha256_file(trace_path)
        summary["panels"][f"{phase_name}/{name}"] = {
            key: panel[key] for key in panel if key != "name"}
        summary["counts"]["panels_completed"] += 1
        write_summary(out / "summary.json", summary)
        _progress(out, {"event": "panel_end", "phase": phase_name, "panel": name,
                        "wall_seconds": panel["wall_seconds"],
                        "mean_raw_native_J": panel["aggregate"].get("mean_raw_native_J"),
                        "failed_worlds": panel["failed_worlds"]})
        return panel

    current = phase
    try:
        dev_panels: dict[str, dict] = {}
        for phase_name in phases:
            current = phase_name
            controllers = None
            if phase_name in ("reference", "grid") and phase == "all":
                if "selected_heuristic" not in summary:
                    selected, scores = select_heuristic(dev_panels)
                    summary["selected_heuristic"] = selected
                    summary["heuristic_dev_mean_J"] = scores
                    _progress(out, {"event": "selected_heuristic", "phase": "heuristic-dev",
                                    "selected": selected, "mean_raw_native_J": scores})
                if phase_name == "grid":
                    controllers = ("N", selected)
            elif phase_name in ("reference", "grid"):
                summary["selected_heuristic"] = selected
                summary["selected_heuristic_source"] = "--heuristic (no heuristic-dev in this run)"
            planned = phase_panels(phase_name, spec, controllers)
            _progress(out, {"event": "phase_start", "phase": phase_name, "panels": len(planned)})
            phase_started = time.perf_counter()
            names = []
            for controller, params, worlds in planned:
                panel = run_panel(phase_name, controller, params, worlds)
                names.append(panel["name"])
                if phase_name == "heuristic-dev":
                    dev_panels[panel["name"]] = panel
            summary["phase_results"][phase_name] = {
                "panels": names, "wall_seconds": time.perf_counter() - phase_started}
            write_summary(out / "summary.json", summary)
            _progress(out, {"event": "phase_end", "phase": phase_name,
                            "wall_seconds": summary["phase_results"][phase_name]["wall_seconds"]})
        current = phase
        summary["status"] = "COMPLETE"
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc), "phase": current}
        raise
    finally:
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        summary.update(
            wall_seconds=time.perf_counter() - started,
            peak_rss_kib={"runner": int(own.ru_maxrss),
                          "largest_worker": int(children.ru_maxrss)},
            torch_threads_parent=torch.get_num_threads(),
        )
        write_summary(out / "summary.json", summary)
        _progress(out, {"event": "run_end", "phase": current, "status": summary["status"],
                        "failure": summary["failure"], "wall_seconds": summary["wall_seconds"]})
