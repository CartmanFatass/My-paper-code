from __future__ import annotations

import ctypes
import gzip
import json
import os
import pickle
import tempfile
import threading
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

import torch

from .analyze import analyze_stage1
from .config import REGISTERED, REVISION, SEEDS, TREATMENT_ID
from .evaluation import audit_source, complexity_audit, evaluate_seed
from .generator import SeedBanks, build_seed_banks
from .models import parameter_counts
from .trainer import load_checkpoint, train_seed


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"): return value.item()
    if isinstance(value, Path): return str(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, default=_json_default); stream.write("\n")
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def atomic_jsonl_gz(path: Path, rows: list[dict] | tuple[dict, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent); os.close(fd)
    try:
        with gzip.open(temporary, "wt", encoding="utf-8", newline="\n") as stream:
            for row in rows: stream.write(json.dumps(row, sort_keys=True, default=_json_default) + "\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def atomic_pickle_gz(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent); os.close(fd)
    try:
        with gzip.open(temporary, "wb") as stream: pickle.dump(value, stream, protocol=5)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def _read_pickle_gz(path: Path) -> SeedBanks:
    with gzip.open(path, "rb") as stream: value = pickle.load(stream)
    if not isinstance(value, SeedBanks): raise RuntimeError(f"invalid retained bank at {path}")
    return value


def _read_jsonl_gz(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


class _ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t)]


def _rss_bytes() -> int:
    counters = _ProcessMemoryCountersEx(); counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.WorkingSetSize)


class _ResourceSampler:
    def __init__(self) -> None:
        self.peak_rss = _rss_bytes(); self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
    def _run(self) -> None:
        while not self.stop.wait(.05): self.peak_rss = max(self.peak_rss, _rss_bytes())
    def __enter__(self): self.thread.start(); return self
    def __exit__(self, *_): self.stop.set(); self.thread.join(); self.peak_rss = max(self.peak_rss, _rss_bytes())


def _enforce(start_wall: float, peak_rss: int) -> None:
    if time.perf_counter() - start_wall > 90 * 60: raise RuntimeError("VNFC-B3 Stage-1 90-minute envelope exceeded")
    if peak_rss > 2 * 1024**3: raise RuntimeError("VNFC-B3 Stage-1 2-GiB RSS envelope exceeded")


def _bank_summary(banks: SeedBanks) -> dict:
    raw = len(banks.ledger); calls = sum(int(row["logical_calls"]) for row in banks.ledger)
    return {"seed": banks.seed, "raw_bases_scanned": raw, "derived_variant_records": 4 * raw,
            "certificate_solver_calls": calls,
            "training_retained_raw_indices": {str(i): [p.raw_index for p in panels] for i, panels in banks.training.items()},
            "conclusion_retained_raw_indices": {str(i): [p.raw_index for p in panels] for i, panels in banks.conclusion.items()}}


def run_stage1(output_root: Path, result_path: Path) -> dict:
    output_root = output_root.resolve(); result_path = result_path.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = REGISTERED.manifest(); manifest_path = output_root / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
        raise RuntimeError("output root contains a non-v6 or otherwise incompatible manifest")
    atomic_json(manifest_path, manifest)
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    timer = time.get_clock_info("perf_counter")
    audit_environment = {
        "host_class": "Windows single-process CPU", "physical_precision": "numpy.float64",
        "model_precision": "torch.float32", "torch_num_threads": 1, "torch_num_interop_threads": 1,
        "blas_thread_limit": 1, "allocator_mode": "Python Floyd max-heap immutable Edge records",
        "model_mode": "torch.no_grad sequential unbatched", "timer": "time.perf_counter_ns",
        "timer_resolution_seconds": timer.resolution, "timer_monotonic": timer.monotonic,
    }
    torch.set_num_threads(1)
    try: torch.set_num_interop_threads(1)
    except RuntimeError: pass
    banks_by_seed: dict[int, SeedBanks] = {}; bank_reports: list[dict] = []
    training_reports: list[dict] = []; evaluation_reports: list[dict] = []; models = {}; all_rows: list[dict] = []
    with _ResourceSampler() as resources:
        # Complete both disjoint finite banks before the first learned optimizer step.
        for seed in SEEDS:
            bank_path = output_root / "banks" / f"seed_{seed}_v6.pkl.gz"
            ledger_path = output_root / "certificates" / f"seed_{seed}_ledger.jsonl.gz"
            summary_path = output_root / "certificates" / f"seed_{seed}_summary.json"
            if bank_path.exists() and ledger_path.exists() and summary_path.exists():
                banks = _read_pickle_gz(bank_path)
                if banks.seed != seed: raise RuntimeError("retained bank seed mismatch")
            else:
                banks = build_seed_banks(seed, lambda: _enforce(start_wall, resources.peak_rss))
                atomic_pickle_gz(bank_path, banks); atomic_jsonl_gz(ledger_path, banks.ledger)
                atomic_json(summary_path, _bank_summary(banks))
            banks_by_seed[seed] = banks; bank_reports.append(_bank_summary(banks))
            _enforce(start_wall, resources.peak_rss)
        raw_total = sum(r["raw_bases_scanned"] for r in bank_reports)
        variant_total = sum(r["derived_variant_records"] for r in bank_reports)
        call_total = sum(r["certificate_solver_calls"] for r in bank_reports)
        if raw_total > 5120 or variant_total > 20480 or call_total > 122880:
            raise RuntimeError(f"bank cap exceeded raw={raw_total} variants={variant_total} calls={call_total}")

        def mark_activity(fact: dict) -> None:
            path = output_root / "activity_start.json"
            if not path.exists():
                atomic_json(path, {"schema": "VNFC-B3-ACTIVITY-v6", "reached": True,
                    "criterion": "first optimizer update after complete frozen banks", **fact})

        for seed in SEEDS:
            checkpoint = output_root / "checkpoints" / f"g_release_seed_{seed}_update_32.pt"
            report_path = output_root / "training" / f"seed_{seed}.json"
            if checkpoint.exists() and report_path.exists():
                model, metadata = load_checkpoint(checkpoint); report = json.loads(report_path.read_text(encoding="utf-8"))
                for key in ("seed", "arm", "final_update", "trials", "optimizer_steps", "parameter_count"):
                    if metadata[key] != report[key]: raise RuntimeError(f"checkpoint/report mismatch seed={seed} field={key}")
            else:
                model, report = train_seed(seed, banks_by_seed[seed], checkpoint, mark_activity)
                atomic_json(report_path, report)
            models[seed] = model; training_reports.append(report); _enforce(start_wall, resources.peak_rss)

        for seed in SEEDS:
            row_path = output_root / "evaluation" / f"seed_{seed}_world_rows.jsonl.gz"
            report_path = output_root / "evaluation" / f"seed_{seed}_summary.json"
            if row_path.exists() and report_path.exists():
                rows = _read_jsonl_gz(row_path); report = json.loads(report_path.read_text(encoding="utf-8"))
            else:
                rows, report = evaluate_seed(seed, models[seed], banks_by_seed[seed])
                atomic_jsonl_gz(row_path, rows); atomic_json(report_path, report)
            all_rows.extend(rows); evaluation_reports.append(report); _enforce(start_wall, resources.peak_rss)

        source = audit_source(banks_by_seed[1601])
        audit = complexity_audit(models[1601], source, audit_environment)
        audit["process_peak_rss_bytes_at_completion"] = resources.peak_rss
        audit["process_peak_rss_le_2GiB"] = resources.peak_rss <= 2 * 1024**3
        atomic_json(output_root / "complexity_audit.json", audit); _enforce(start_wall, resources.peak_rss)
        analysis = analyze_stage1(all_rows, evaluation_reports, training_reports, audit, resources.peak_rss)
    wall, cpu = time.perf_counter() - start_wall, time.process_time() - start_cpu
    result = {
        "schema": REGISTERED.result_schema, "treatment_id": TREATMENT_ID, "revision": REVISION,
        "stage": 1, "manifest": manifest, "bank_construction": {"seeds": bank_reports,
            "raw_bases_scanned": raw_total, "derived_variant_records": variant_total,
            "certificate_solver_calls": call_total, "tagged_conclusion_ceilings": 6144},
        "analysis": analysis, "training": training_reports, "evaluation": evaluation_reports,
        "complexity_audit": audit,
        "operation_totals": {"training": {str(r["seed"]): r["allocator_totals"] for r in training_reports},
            "evaluation": {str(r["seed"]): r["operation_totals"] for r in evaluation_reports}},
        "resources": {"wall_seconds": wall, "cpu_seconds": cpu, "peak_rss_bytes": resources.peak_rss,
            "within_90_minutes": wall <= 5400, "within_2_gib": resources.peak_rss <= 2 * 1024**3},
        "architecture": parameter_counts(models[1601]), "stage2_compute_launched": False,
        "material_anomalies": [failure for report in evaluation_reports for failure in
            report["complexity_failures"] + report["row_order_invariance_failures"]],
        "what_remains_unknown": ["arbitrary-N and growing-task behavior", "Stage-2 pressure and lease effects",
            "kinematic, connectivity, UAV, and safety behavior"],
    }
    atomic_json(result_path, result)
    return result
