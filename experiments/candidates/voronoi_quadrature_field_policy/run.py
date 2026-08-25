"""Explicit, retained, one-process CPU lifecycle for frozen VQFP-B1 production."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any

# Bind native numerical backends before importing NumPy indirectly through analysis/Torch.
for _thread_environment in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_thread_environment] = "1"

import torch

from .analysis import (Inference, aggregate_associations, binding_support, direct_classification,
                       endpoint_headroom, infer, seed_metrics)
from .config import FrozenConfig, TRAINING_SEEDS, VQFP_REVISION
from .evaluation import CheckpointPanels, evaluate_checkpoint
from .host import make_episode
from .models import Arm, VQFPModel, copy_common_initialization
from .rng import CounterRNG
from .trainer import train_seed


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent,
                                     prefix=f".{path.name}.", suffix=".tmp") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _atomic_torch(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=path.parent,
                                     prefix=f".{path.name}.", suffix=".tmp") as handle:
        temporary = Path(handle.name)
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _rss_bytes() -> int:
    """Read the process working set without an optional monitoring dependency."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCountersEx(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                         ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                         ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                         ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                         ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                         ("PrivateUsage", ctypes.c_size_t)]
        counters = ProcessMemoryCountersEx()
        counters.cb = ctypes.sizeof(counters)
        get_current_process = ctypes.windll.kernel32.GetCurrentProcess
        get_current_process.restype = wintypes.HANDLE
        get_process_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = (wintypes.HANDLE, ctypes.POINTER(ProcessMemoryCountersEx), wintypes.DWORD)
        get_process_memory_info.restype = wintypes.BOOL
        if not get_process_memory_info(get_current_process(), ctypes.byref(counters), counters.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if os.uname().sysname == "Darwin" else value * 1024)


class ResourceGuard:
    """Hard execution guard: one CPU thread, wall/RSS cap, and exact ledger total."""

    def __init__(self, config: FrozenConfig) -> None:
        self.config = config
        self.started = time.monotonic()
        self.maximum_rss = _rss_bytes()
        self.counts = {key: 0 for key in config.static_accounting() if key != "total"}
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)

    def check(self) -> None:
        elapsed = time.monotonic() - self.started
        self.maximum_rss = max(self.maximum_rss, _rss_bytes())
        if elapsed > self.config.wall_hours * 3600:
            raise RuntimeError("frozen eight-hour wall-clock cap exceeded")
        if self.maximum_rss > self.config.ram_gib * 1024**3:
            raise RuntimeError("frozen 2 GiB RSS cap exceeded")

    def consume(self, category: str, count: int) -> None:
        self.check()
        if category not in self.counts:
            raise ValueError(f"unregistered resource category: {category}")
        self.counts[category] += count
        ceiling = self.config.static_accounting()[category]
        if self.counts[category] > ceiling:
            raise RuntimeError(f"registered {category} ledger exceeded")

    def snapshot(self, *, validate: bool = True) -> dict[str, Any]:
        if validate:
            self.check()
        return {"counts": {**self.counts, "total": sum(self.counts.values())},
                "elapsed_seconds": time.monotonic() - self.started,
                "maximum_rss_bytes": self.maximum_rss,
                "caps": {"cpu_processes": self.config.cpu_processes, "cpu_threads": 1,
                         "ram_gib": self.config.ram_gib, "wall_hours": self.config.wall_hours}}

    def close(self) -> dict[str, Any]:
        self.check()
        expected = self.config.static_accounting()
        if self.counts != {key: expected[key] for key in self.counts}:
            raise RuntimeError("incomplete registered transition/state ledger")
        return {"counts": {**self.counts, "total": sum(self.counts.values())},
                "elapsed_seconds": time.monotonic() - self.started,
                "maximum_rss_bytes": self.maximum_rss, "cpu_threads": 1,
                "cpu_processes": self.config.cpu_processes,
                "ram_gib_cap": self.config.ram_gib, "wall_hours_cap": self.config.wall_hours}


@dataclass(slots=True)
class SeedRun:
    seed: int
    vqfp: CheckpointPanels
    learned: CheckpointPanels
    metrics: Any
    binding_support: bool
    vqfp_training_summary: torch.Tensor
    learned_training_summary: torch.Tensor


def _paired_models(seed: int, device: torch.device) -> tuple[VQFPModel, VQFPModel]:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        vqfp = VQFPModel(Arm.VQFP).to(device)
    learned = VQFPModel(Arm.LEARNED).to(device)
    copy_common_initialization(vqfp, learned)
    vqfp.assert_frozen_parameter_count()
    learned.assert_frozen_parameter_count()
    return vqfp, learned


def _preflight(device: torch.device, config: FrozenConfig) -> dict[str, bool]:
    """Pre-activity deterministic conformance facts retained with the production result."""
    vqfp, learned = _paired_models(TRAINING_SEEDS[0], device)
    episode = make_episode(6, "IID", CounterRNG("preflight", VQFP_REVISION), device=device)
    previous = torch.full((episode.n,), -1, dtype=torch.long, device=device)
    signal = episode.cell_averages(0)
    edge = vqfp.edge_inputs(episode.positions, episode.gaps, episode.predecessor, episode.triplets, signal, previous)
    volumes = episode.volumes[episode.triplets]
    v_message, v_raw, _ = vqfp.aggregate(edge, volumes)
    l_message, _, l_gate = learned.aggregate(edge, volumes)
    q = torch.sum(volumes * signal[episode.triplets], dim=-1)
    tolerance = dict(atol=config.control_atol, rtol=config.control_rtol)
    facts = {"vqfp_40996_parameters": vqfp.nominal_parameter_count == config.nominal_parameters_per_arm,
             "learned_40996_parameters": learned.nominal_parameter_count == config.nominal_parameters_per_arm,
             "paired_common_initial_values": all(torch.equal(left, right) for left, right in zip(vqfp.parameters(), learned.parameters())),
             "gate_exactly_zero": bool(torch.count_nonzero(vqfp.edge_gate.weight) == 0 and torch.count_nonzero(vqfp.edge_gate.bias) == 0
                                       and torch.count_nonzero(learned.edge_gate.weight) == 0 and torch.count_nonzero(learned.edge_gate.bias) == 0),
             "learned_ell_exactly_zero": bool(torch.count_nonzero(l_gate) == 0),
             "ell_zero_aggregate_equality": bool(torch.allclose(v_message, l_message, **tolerance)),
             "raw_mass_identity": bool(torch.allclose(v_raw, q, **tolerance)),
             "positive_unit_volumes": bool(torch.all(episode.volumes > 0.0) and torch.allclose(episode.volumes.sum(), episode.volumes.new_tensor(1.0), **tolerance)),
             "distinct_triplets": bool(torch.all(torch.sort(episode.triplets, dim=-1).values[:, 1:] != torch.sort(episode.triplets, dim=-1).values[:, :-1]))}
    if not all(facts.values()):
        failed = ", ".join(key for key, value in facts.items() if not value)
        raise RuntimeError(f"pre-activity conformance failure: {failed}")
    return facts


def _zero_compute_complexity_facts(config: FrozenConfig) -> dict[str, Any]:
    return {"sparse_path": "one O(N log N) cyclic order/sort per episode; O(N) 3N edges/work/memory",
            "degree": "external degree 2; self-inclusive triplet 3 distinct senders",
            "search": "zero hypothetical trajectories; no rollout/tree/beam/adaptive search",
            "oracle": "evaluation-only O(N*3^3) per tick",
            "transition_state_ceiling": config.transition_state_ceiling,
            "nominal_parameters_per_arm": config.nominal_parameters_per_arm,
            "caps": {"processes": 1, "threads": 1, "ram_gib": 2, "wall_hours": 8},
            "static_analog_based_not_observed": {"conservative_wall_projection_hours": 6.5,
                                                   "conservative_peak_rss_projection_bytes": 1342177280}}


def _availability(seed_runs: list[SeedRun], preflight: dict[str, bool]) -> dict[str, bool]:
    learned = [row.learned for row in seed_runs]
    complete = len(seed_runs) == len(TRAINING_SEEDS)
    # Checkpoint reuse and no held-out exposure are construction invariants of this runner.
    return {"complete_paired_final_checkpoints": complete,
            "single_final_checkpoint_all_panels": complete,
            "exact_rule_containment_before_training": preflight["ell_zero_aggregate_equality"],
            "positive_volumes_and_unit_sum": preflight["positive_unit_volumes"],
            "no_heldout_training_or_selection": True,
            "P_oracle_headroom": complete and endpoint_headroom(learned, "P"),
            "R_oracle_headroom": complete and endpoint_headroom(learned, "R")}


def _retained_analysis(seed_runs: list[SeedRun], preflight: dict[str, bool]) -> dict[str, Any]:
    metrics = [row.metrics for row in seed_runs]
    inference = infer(metrics)
    support = all(row.binding_support for row in seed_runs)
    mechanism = {"K": inference.lower_quadrature > 0.02,
                 "M": inference.lower_return_contribution > 0.02,
                 "T": inference.lower_action_tv > 0.05,
                 "support_and_controls": support}
    availability = _availability(seed_runs, preflight)
    p_available = all(availability[key] for key in ("complete_paired_final_checkpoints", "single_final_checkpoint_all_panels",
                                                      "exact_rule_containment_before_training", "positive_volumes_and_unit_sum",
                                                      "no_heldout_training_or_selection", "P_oracle_headroom"))
    r_available = all(availability[key] for key in ("complete_paired_final_checkpoints", "single_final_checkpoint_all_panels",
                                                      "exact_rule_containment_before_training", "positive_volumes_and_unit_sum",
                                                      "no_heldout_training_or_selection", "R_oracle_headroom"))
    binding_ok = all(mechanism.values())
    noisy_reversal = inference.upper_noise < -0.03
    direct = direct_classification(inference, p_available=p_available, r_available=r_available,
                                   binding_ok=binding_ok, noisy_reversal=noisy_reversal)
    endpoint_labels = {"P": "UNAVAILABLE" if not p_available else ("POSITIVE" if inference.lower_performance > 0.03 else ("MATERIAL_REVERSE" if inference.upper_performance < -0.03 else "NEITHER")),
                       "R": "UNAVAILABLE" if not r_available else ("POSITIVE" if inference.lower_robustness > 0.03 else ("MATERIAL_REVERSE" if inference.upper_robustness < -0.03 else "NEITHER"))}
    cells: list[dict[str, Any]] = []
    from .analysis import cvar10, registered_even_median
    arm_aggregate: list[dict[str, Any]] = []
    heldout_differences: list[dict[str, Any]] = []
    control_facts: list[dict[str, Any]] = []
    support_facts: list[dict[str, Any]] = []
    headroom_inputs: list[dict[str, Any]] = []
    for row in seed_runs:
        for arm, panels in (("vqfp", row.vqfp), ("learned", row.learned)):
            for (n, regime), values in panels.ordinary_intact.items():
                cells.append({"seed": row.seed, "arm": arm, "N": n, "regime": regime,
                              "intact_mean": float(values.mean()), "intact_cvar10": cvar10(values),
                              "cut_mean": None if (n, regime) not in panels.ordinary_cut else float(panels.ordinary_cut[(n, regime)].mean()),
                              "raw_return": [float(trace.raw_return) for trace in panels.ordinary_traces[(n, regime)]],
                              "service_mass": [float(trace.service_mass) for trace in panels.ordinary_traces[(n, regime)]],
                              "cost": [float(trace.cost) for trace in panels.ordinary_traces[(n, regime)]],
                              "action_frequency": [trace.action_frequency.cpu().tolist() for trace in panels.ordinary_traces[(n, regime)]]
                              })
    for n in (4, 6, 10, 14):
        for regime in ("IID", "CLUSTER"):
            for arm, index in (("vqfp", 0), ("learned", 1)):
                values = [((row.vqfp, row.learned)[index].ordinary_intact[(n, regime)]) for row in seed_runs]
                arm_aggregate.append({"arm": arm, "N": n, "regime": regime,
                                      "equal_seed_mean": float(sum(float(item.mean()) for item in values) / len(values)),
                                      "equal_seed_cvar10": float(sum(cvar10(item) for item in values) / len(values))})
            if n in (4, 14):
                for row in seed_runs:
                    v, l = row.vqfp.ordinary_intact[(n, regime)], row.learned.ordinary_intact[(n, regime)]
                    heldout_differences.append({"seed": row.seed, "N": n, "regime": regime,
                                                "mean_difference": float(v.mean() - l.mean()),
                                                "cvar10_difference": cvar10(v) - cvar10(l)})
    for n in (4, 14):
        for regime in ("IID", "CLUSTER"):
            learned_values = [row.learned.ordinary_intact[(n, regime)] for row in seed_runs]
            headroom_inputs.append({"N": n, "regime": regime,
                                    "learned_equal_seed_mean": float(sum(float(x.mean()) for x in learned_values) / len(learned_values)),
                                    "learned_equal_seed_cvar10": float(sum(cvar10(x) for x in learned_values) / len(learned_values))})
    for row in seed_runs:
        for arm, panels in (("vqfp", row.vqfp), ("learned", row.learned)):
            for (n, name), control in panels.controls.items():
                control_facts.append({"seed": row.seed, "arm": arm, "N": n, "name": name,
                                      "passed": control.passed, "maximum_error": control.maximum_error, "states": control.states})
        for n in (4, 14):
            actions = torch.cat([record.intact_actions.flatten() for record in row.vqfp.conflict_replay[n]])
            frequency = torch.bincount(actions, minlength=3).float().div(actions.numel()).cpu().tolist()
            support_facts.append({"seed": row.seed, "N": n,
                                  "cluster_volume_cv_median": registered_even_median(row.vqfp.volume_cv[(n, "CLUSTER")]),
                                  "conflict_volume_cv_median": registered_even_median(row.vqfp.volume_cv[(n, "MEASURE-CONFLICT")]),
                                  "conflict_association_mean": float(row.vqfp.association_conflict[n].mean()),
                                  "intact_vqfp_action_frequency": frequency,
                                  "two_action_support": sum(value >= 0.05 for value in frequency) >= 2})
    heldout_aggregate = []
    for n in (4, 14):
        for regime in ("IID", "CLUSTER"):
            rows = [item for item in heldout_differences if item["N"] == n and item["regime"] == regime]
            heldout_aggregate.append({"N": n, "regime": regime,
                                      "equal_seed_mean_difference": float(sum(item["mean_difference"] for item in rows) / len(rows)),
                                      "equal_seed_cvar10_difference": float(sum(item["cvar10_difference"] for item in rows) / len(rows))})
    gamma = float(sum(row.metrics.gamma for row in seed_runs) / len(seed_runs))
    second_surface = direct == "DIRECT_VALUE_PLUS_CORRECTED_BINDING" and not noisy_reversal
    return {"preflight": preflight, "availability": availability, "mechanism_gates": mechanism,
            "inference": asdict(inference), "direct_classification": direct,
            "endpoint_labels": endpoint_labels, "gamma_seed": [row.metrics.gamma for row in seed_runs], "Gamma": gamma,
            "binding_without_direct_value": binding_ok and endpoint_labels["P"] != "POSITIVE" and endpoint_labels["R"] != "POSITIVE",
            "second_surface_activation": "ACTIVATE_UNTEMPERED_2D" if second_surface else "DO_NOT_ACTIVATE_UNTEMPERED_2D",
            "cell_summaries": cells,
            "aggregate_intact_cells": arm_aggregate,
            "heldout_seed_cell_differences": heldout_differences,
            "heldout_aggregate_cell_differences": heldout_aggregate,
            "headroom_inputs": headroom_inputs,
            "structural_controls": control_facts,
            "support_facts": support_facts,
            "aggregate_bypass_B": float(sum(row.metrics.bypass[n] for row in seed_runs for n in (4, 14)) / 24.0),
            "raw_summary_schema": {"ordinary_intact": "per episode raw_return/service_mass/cost/action_frequency",
                                   "ordinary_cut": "per episode raw_return/service_mass/cost/action_frequency",
                                   "conflict_intact_cut": "per episode raw_return/service_mass/cost/action_frequency in replay reports",
                                   "noisy": "per episode raw_return/service_mass/cost/action_frequency",
                                   "overlap": "omitted by EM clarification"},
            "noisy_modifier": "NOISY_PANEL_MATERIAL_REVERSAL" if noisy_reversal else "NO_NOISY_PANEL_MATERIAL_REVERSAL",
            "association_action_tv": aggregate_associations(metrics, "association_tv"),
            "association_return": aggregate_associations(metrics, "association_return"),
            "seed_metrics": [{"seed": row.seed, **asdict(row.metrics), "binding_support": row.binding_support} for row in seed_runs]}


def _run_production(output_root: Path, result_path: Path, snapshot: dict[str, Any]) -> Path:
    """Run B1 only through its explicit retained lifecycle and write final results atomically."""
    config = FrozenConfig()
    config.assert_registered_counts()
    device = torch.device("cpu")
    output_root = output_root.resolve()
    result_path = result_path.resolve()
    if result_path.parent != output_root and output_root not in result_path.parents:
        raise ValueError("--result must be inside the explicitly supplied --output-root")
    if output_root.exists() and (not output_root.is_dir() or any(output_root.iterdir())):
        raise FileExistsError("--output-root must be a fresh empty CM-owned directory")
    if result_path.exists():
        raise FileExistsError("--result must be a new path; overwrite or resume is forbidden")
    guard = ResourceGuard(config)
    def terminal_refresh() -> None:
        """Best-effort terminal peak sample for a failure receipt; never masks its cause."""
        try:
            snapshot.update(guard.snapshot(validate=True))
        except Exception:
            snapshot.update(guard.snapshot(validate=False))
    snapshot["_terminal_refresh"] = terminal_refresh
    command = f"C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m experiments.candidates.voronoi_quadrature_field_policy --execute --output-root {output_root} --result {result_path}"
    snapshot.update({"revision": VQFP_REVISION, "activity_begun": False,
                     "counts": dict(guard.counts), "maximum_rss_bytes": guard.maximum_rss})
    complexity = _zero_compute_complexity_facts(config)
    _atomic_json(output_root / "manifest.json", {"revision": VQFP_REVISION, "created_at": _utc_now(),
        "config": asdict(config), "ledger": config.static_accounting(), "activity_begun": False,
        "checkpoint_policy": "final_update_375_only", "device": "cpu", "threads": 1, "command": command, "zero_compute_complexity": complexity})
    snapshot["cm_owned_root"] = True
    preflight = _preflight(device, config)
    activity_written = False
    def before_step(count: int) -> None:
        nonlocal activity_written
        # Enforce the registered 256-transition resource allowance before mutation.
        consume("training", count)
        if not activity_written:
            # Durable before mutation: a step cannot occur if this write fails.
            _atomic_json(output_root / "activity.json", {"revision": VQFP_REVISION, "activity_begun": True,
                "first_optimizer_step_attempted_at": _utc_now(),
                "definition": "durably marked immediately before first optimizer mutation; a failing step is only an attempted update"})
            activity_written = True
            snapshot["activity_begun"] = True
    def consume(category: str, count: int) -> None:
        try:
            guard.consume(category, count)
        finally:
            snapshot.update(guard.snapshot(validate=False))
    def after_step(count: int) -> None:
        del count

    seed_runs: list[SeedRun] = []
    for seed in TRAINING_SEEDS:
        vqfp, learned = _paired_models(seed, device)
        _, _, vqfp_training_summary = train_seed(vqfp, seed, config, device=device, before_step=before_step, after_step=after_step)
        _atomic_torch(output_root / "checkpoints" / f"seed_{seed}_vqfp_update_375.pt", {"revision": VQFP_REVISION, "seed": seed, "arm": "vqfp", "update": 375, "state_dict": vqfp.state_dict()})
        _, _, learned_training_summary = train_seed(learned, seed, config, device=device, before_step=before_step, after_step=after_step)
        _atomic_torch(output_root / "checkpoints" / f"seed_{seed}_learned_update_375.pt", {"revision": VQFP_REVISION, "seed": seed, "arm": "learned", "update": 375, "state_dict": learned.state_dict()})
        vqfp_panels = evaluate_checkpoint(vqfp, seed, config, device=device, consume=consume)
        learned_panels = evaluate_checkpoint(learned, seed, config, device=device, consume=consume)
        seed_runs.append(SeedRun(seed, vqfp_panels, learned_panels, seed_metrics(vqfp_panels, learned_panels),
                                 binding_support(vqfp_panels, learned_panels, config),
                                 vqfp_training_summary, learned_training_summary))
    try:
        analysis = _retained_analysis(seed_runs, preflight)
        pre_persistence_resources = guard.snapshot()
        snapshot.update(pre_persistence_resources)
        retained = {"revision": VQFP_REVISION, "completed_at": _utc_now(), "pre_persistence_resources": pre_persistence_resources,
                    "analysis": analysis, "panels": seed_runs,
                    "training_summary_schema": {"shape": "[375,8,6] update/replicate-cell order", "columns": ["raw_return", "service_mass", "cost", "freq0", "freq0.5", "freq1"]},
                    "anomalies": [], "claim_ceiling": "finite noise-free exact-cell-average one-dimensional periodic host only"}
        _atomic_torch(result_path, retained)
        resources = guard.close()
    finally:
        snapshot.update(guard.snapshot(validate=False))
    _atomic_json(output_root / "completion.json", {"revision": VQFP_REVISION, "completed_at": _utc_now(),
        "command": command, "resources": resources, "result": str(result_path)})
    _atomic_json(output_root / "manifest.json", {"revision": VQFP_REVISION, "created_at": _utc_now(),
        "config": asdict(config), "ledger": config.static_accounting(), "activity_begun": activity_written,
        "checkpoint_policy": "final_update_375_only", "device": "cpu", "threads": 1,
        "result": str(result_path), "resources": resources, "command": command, "zero_compute_complexity": complexity})
    return result_path


def run_production(output_root: Path, result_path: Path) -> Path:
    """Write an atomic failure receipt for any interrupted/failed production lifecycle."""
    snapshot: dict[str, Any] = {"revision": VQFP_REVISION, "activity_begun": False,
                                "counts": {}, "resources": "not_initialized", "cm_owned_root": False}
    try:
        return _run_production(output_root, result_path, snapshot)
    except Exception as error:
        refresh = snapshot.pop("_terminal_refresh", None)
        if refresh is not None:
            try:
                refresh()
            except Exception:
                pass
        if snapshot["cm_owned_root"]:
            root = output_root.resolve()
            try:
                _atomic_json(root / "failure.json", {"revision": VQFP_REVISION, "failed_at": _utc_now(),
                    "error_type": type(error).__name__, "error": str(error), "snapshot": snapshot,
                    "scientific_classification": "NONE"})
            except Exception:
                pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the frozen VQFP-B1 production lifecycle.")
    parser.add_argument("--execute", action="store_true", help="explicitly apply the registered optimizer updates")
    parser.add_argument("--output-root", type=Path, required=True, help="fresh CM-owned output directory")
    parser.add_argument("--result", type=Path, required=True, help="new retained .pt result inside --output-root")
    args = parser.parse_args(argv)
    if not args.execute:
        parser.error("execution is deliberate: pass --execute to begin registered activity")
    print(run_production(args.output_root, args.result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
