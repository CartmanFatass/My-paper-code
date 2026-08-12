"""Fail-closed one-shot launcher for CRTO-B1.

The simulator/trainer implementation is deliberately loaded only after command
validation and resource preflight.  Its two-stage execution boundary first
closes every seed's predictor/probe gate, then permits learned execution with
the frozen configuration, ledger, activity marker, and an atomic seed writer.
Every executed environment step remains accounted through the ledger.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import importlib
import json
import os
from pathlib import Path
import platform
import pickle
import time
from typing import Any, Callable, Mapping, Protocol

from .config import (
    ARTIFACT_KIND, CUT_ARMS, EVENT_CLASSES, LEDGER_FORMULAS, LEDGER_MAX_STEPS,
    OPTIONS, PRODUCTION_CONFIG, REGIMES, REVISION, RunConfig, TREATMENT,
    registered_ledger,
)


FROZEN_REVISION = "CRTO-B1-SCIENCE-20260812-04"


class IncompleteEngineeringResult(RuntimeError):
    """A registered resource or conformance boundary was crossed."""


def _rss_bytes() -> int:
    """Read an OS lifetime peak resident-memory value in bytes."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class _Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(_Counters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        process = kernel32.GetCurrentProcess()
        counters = _Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "Windows process RSS query failed")
        return int(counters.PeakWorkingSetSize)
    import resource
    observed = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Darwin reports bytes; Linux and the registered Unix execution hosts
    # report KiB.  Both values are lifetime maxima, never current RSS.
    return observed if platform.system() == "Darwin" else observed * 1024


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_json(path: Path, value: object) -> None:
    _atomic_bytes(
        path,
        (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8"),
    )


class ResourceLedger:
    """Immutable-category accounting for the eight registered step budgets."""

    def __init__(self, config: RunConfig) -> None:
        if not config.registered:
            raise IncompleteEngineeringResult("CRTO execution accepts only the registered configuration")
        self._config = config
        self._started = time.perf_counter()
        self._peak_rss_bytes = _rss_bytes()
        self._actual = defaultdict(int)
        self._completed_rows = defaultdict(int)
        self._check()

    def add(self, category: str, primitive_team_steps: int, *, completed_rows: int = 1) -> None:
        if category not in LEDGER_MAX_STEPS:
            raise IncompleteEngineeringResult(f"unregistered ledger category: {category}")
        if isinstance(primitive_team_steps, bool) or not isinstance(primitive_team_steps, int):
            raise TypeError("primitive_team_steps must be an integer")
        if primitive_team_steps < 0 or completed_rows < 0:
            raise IncompleteEngineeringResult("ledger entries cannot be negative")
        proposed = self._actual[category] + primitive_team_steps
        if proposed > LEDGER_MAX_STEPS[category]:
            raise IncompleteEngineeringResult(
                f"registered category cap breached: {category} {proposed}>{LEDGER_MAX_STEPS[category]}"
            )
        self._actual[category] = proposed
        self._completed_rows[category] += completed_rows
        self._check()

    def _check(self) -> None:
        self._peak_rss_bytes = max(self._peak_rss_bytes, _rss_bytes())
        total = sum(self._actual.values())
        elapsed = time.perf_counter() - self._started
        if total > self._config.registered_max_steps:
            raise IncompleteEngineeringResult("registered 10,715,136-step cap breached")
        if elapsed > self._config.wall_seconds:
            raise IncompleteEngineeringResult("registered 120-minute wall-time cap breached")
        if self._peak_rss_bytes > self._config.peak_rss_bytes:
            raise IncompleteEngineeringResult("registered 2-GiB RSS cap breached")

    def facts(self) -> dict[str, object]:
        self._check()
        return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        """Return durable accounting even after a cap has made execution incomplete."""
        actual = {category: int(self._actual[category]) for category in LEDGER_MAX_STEPS}
        return {
            "formulas": dict(LEDGER_FORMULAS),
            "maximum_steps": registered_ledger(),
            "actual_completed_steps": actual,
            "actual_total_steps": sum(actual.values()),
            "completed_rows": {category: int(self._completed_rows[category]) for category in LEDGER_MAX_STEPS},
            "wall_seconds": time.perf_counter() - self._started,
            "peak_rss_bytes": self._peak_rss_bytes,
            "cpu_workers": self._config.cpu_workers,
            "gpu_enabled": self._config.gpu_enabled,
            "all_categories_within_registered_maximum": all(
                actual[name] <= maximum for name, maximum in LEDGER_MAX_STEPS.items()
            ),
        }

    def assert_complete(self) -> None:
        """Enforce the seven exact panels; only illegal audit actions may save steps."""
        self._check()
        incomplete = {
            category: {"actual": self._actual[category], "required": maximum}
            for category, maximum in LEDGER_MAX_STEPS.items()
            if category != "audit_action_enumeration" and self._actual[category] != maximum
        }
        if incomplete:
            raise IncompleteEngineeringResult(
                f"registered non-audit ledger categories are not exact: {incomplete!r}"
            )


class ActivityMarker:
    """Records the exact non-retroactive CRTO scientific-activity boundary."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._value: dict[str, object] | None = None

    def mark_first_learned_optimizer_update(
        self, *, seed: int, arm: str, update_index: int, trajectory_count: int,
    ) -> None:
        if self._value is not None:
            raise IncompleteEngineeringResult("scientific activity marker may be written exactly once")
        if arm not in ("CRTO", "FULL-HISTORY-AUX-TERM"):
            raise IncompleteEngineeringResult("activity marker requires a learned arm")
        if update_index < 0 or trajectory_count <= 0:
            raise IncompleteEngineeringResult("invalid first learned optimizer update witness")
        witness = {
            "started": True,
            "criterion": f"first learned-arm optimizer update under {FROZEN_REVISION}",
            "seed": seed, "arm": arm, "update_index": update_index,
            "trajectory_count": trajectory_count,
        }
        _atomic_json(self._path, witness)
        self._value = witness

    def facts(self) -> dict[str, object]:
        return self._value or {
            "started": False,
            "criterion": f"first learned-arm optimizer update under {FROZEN_REVISION}",
        }


class SeedWriter:
    """Adapter-facing atomic writer restricted to one seed's output subtree."""

    def __init__(self, output_root: Path, seed: int) -> None:
        self.seed = seed
        self._root = output_root / "seeds" / f"seed_{seed}"

    def _target(self, relative_path: str) -> Path:
        candidate = (self._root / relative_path).resolve()
        root = self._root.resolve()
        if candidate == root or root not in candidate.parents:
            raise ValueError("seed artifact must remain inside its seed subtree")
        return candidate

    def write_json(self, relative_path: str, value: object) -> Path:
        target = self._target(relative_path)
        _atomic_json(target, value)
        return target

    def write_checkpoint(self, relative_path: str, payload: bytes) -> Path:
        target = self._target(relative_path)
        _atomic_bytes(target, payload)
        return target

    def write_pickle(self, relative_path: str, value: object) -> Path:
        """Persist a seed-local raw record without flattening host objects to JSON."""
        target = self._target(relative_path)
        _atomic_bytes(target, pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
        return target

    def artifact_path(self, relative_path: str) -> Path:
        """Reserve a seed-local path for a sibling's own atomic checkpoint writer."""
        return self._target(relative_path)


class _Preparer(Protocol):
    def __call__(
        self, *, seed: int, config: RunConfig, ledger: ResourceLedger, writer: SeedWriter,
    ) -> object: ...


class _PreparedSeedAdapter(Protocol):
    def __call__(
        self, *, prepared: object, ledger: ResourceLedger, activity: ActivityMarker,
        writer: SeedWriter,
    ) -> Mapping[str, object]: ...


class _FinalizeAdapter(Protocol):
    def __call__(
        self, per_seed_raw: Mapping[int, Mapping[str, object]], resources: Mapping[str, object],
    ) -> Mapping[str, object]: ...


def _load_execution_adapters() -> tuple[_Preparer, _PreparedSeedAdapter]:
    """Resolve preparation and learned-execution boundaries together."""
    try:
        module = importlib.import_module(".execution", __package__)
    except ImportError as error:
        raise IncompleteEngineeringResult(
            "CRTO execution adapter is unavailable; expected "
            "experiments.candidates.commitment_residual_triggered_options.execution preparation interfaces"
        ) from error
    preparer = getattr(module, "prepare_seed", None)
    adapter = getattr(module, "run_prepared_seed", None)
    if not callable(preparer) or not callable(adapter):
        raise IncompleteEngineeringResult(
            "CRTO execution adapter must export callable prepare_seed and run_prepared_seed"
        )
    return preparer, adapter


def _load_finalizer() -> _FinalizeAdapter:
    """Resolve the aggregate analysis boundary with the seed adapter."""
    try:
        module = importlib.import_module(".execution", __package__)
    except ImportError as error:
        raise IncompleteEngineeringResult(
            "CRTO execution adapter is unavailable; expected "
            "experiments.candidates.commitment_residual_triggered_options.execution.finalize"
        ) from error
    finalizer = getattr(module, "finalize", None)
    if not callable(finalizer):
        raise IncompleteEngineeringResult("CRTO execution adapter must export callable finalize")
    return finalizer


def _enforce_registered_runtime(config: RunConfig) -> None:
    if not config.registered or config.cpu_workers != 1 or config.gpu_enabled:
        raise IncompleteEngineeringResult("CRTO must run its exact one-CPU/no-GPU registered configuration")
    if config.revision != FROZEN_REVISION:
        raise IncompleteEngineeringResult(
            f"CRTO launcher is bound to {FROZEN_REVISION}, not {config.revision}"
        )
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible not in (None, "", "-1"):
        raise IncompleteEngineeringResult("CUDA_VISIBLE_DEVICES must be unset, empty, or -1 for CRTO")
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    import torch
    try:
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
    except RuntimeError as error:
        raise IncompleteEngineeringResult(
            "CRTO could not apply its one-CPU Torch thread limits"
        ) from error


def _manifest(config: RunConfig, output_root: Path, result_path: Path) -> dict[str, object]:
    return {
        "artifact_kind": ARTIFACT_KIND,
        "treatment": TREATMENT,
        "revision": REVISION,
        "production_command": (
            "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m "
            "experiments.candidates.commitment_residual_triggered_options "
            "train-evaluate-analyze --output-root <fresh-root> --result <fresh-result.json>"
        ),
        "output_root": str(output_root), "result_path": str(result_path),
        "configuration": asdict(config),
        "algorithm_seeds": list(config.algorithm_seeds), "regimes": list(REGIMES),
        "event_classes": list(EVENT_CLASSES), "options_in_tie_order": list(OPTIONS),
        "learned_arms": ["CRTO", "FULL-HISTORY-AUX-TERM"],
        "cut_arms": list(CUT_ARMS),
        "ledger": {"formulas": dict(LEDGER_FORMULAS), "maximum_steps": registered_ledger()},
        "result_schema": {
            "required_top_level": [
                "artifact_kind", "treatment", "revision", "manifest", "scientific_activity",
                "resource_ledger", "per_seed", "aggregate", "question_relevant_output_exists", "anomalies",
            ],
            "required_per_seed": [
                "seed", "predictor", "training", "hazard_development", "scored_evaluation",
                "donor_only", "mechanism_cuts", "audit", "checkpoints",
                "panel_identities", "raw_output_exists", "question_relevant_output_exists", "anomalies",
            ],
        },
    }


_SEED_REQUIRED_KEYS = frozenset(_manifest(PRODUCTION_CONFIG, Path("."), Path("result.json"))["result_schema"]["required_per_seed"])


def _validate_seed_result(seed: int, value: Mapping[str, object]) -> dict[str, object]:
    missing = sorted(_SEED_REQUIRED_KEYS.difference(value))
    if missing:
        raise IncompleteEngineeringResult(f"seed {seed} result omitted required fields: {', '.join(missing)}")
    if value["seed"] != seed:
        raise IncompleteEngineeringResult(f"seed adapter returned incorrect seed identity for {seed}")
    if value["raw_output_exists"] is not True:
        raise IncompleteEngineeringResult(f"seed {seed} did not return its complete raw execution output")
    if not isinstance(value["anomalies"], list):
        raise IncompleteEngineeringResult("per-seed anomalies must be a list")
    return dict(value)


def exercise(*, output_root: Path, result_path: Path, config: RunConfig = PRODUCTION_CONFIG) -> dict[str, object]:
    """Run exactly one complete frozen CRTO package, or raise an incomplete result."""
    output_root = output_root.resolve()
    result_path = result_path.resolve()
    if output_root.exists():
        raise FileExistsError("CRTO requires a fresh output root")
    if result_path.exists():
        raise FileExistsError("CRTO result path already exists")
    _enforce_registered_runtime(config)
    preparer, adapter = _load_execution_adapters()
    finalizer = _load_finalizer()
    output_root.mkdir(parents=True, exist_ok=False)
    manifest = _manifest(config, output_root, result_path)
    _atomic_json(output_root / "manifest.json", manifest)
    ledger = ResourceLedger(config)
    activity = ActivityMarker(output_root / "activity_start.json")
    per_seed: dict[str, object] = {}
    per_seed_raw: dict[int, dict[str, object]] = {}
    prepared: dict[int, object] = {}
    preactivity: dict[str, object] = {}
    try:
        # No learned optimizer may run until all eight seed-specific probes have
        # completed and passed.  Prepared objects remain in memory only.
        for seed in config.algorithm_seeds:
            prepared_seed = preparer(
                seed=seed, config=config, ledger=ledger, writer=SeedWriter(output_root, seed),
            )
            probe_report = getattr(prepared_seed, "probe_report", None)
            if not bool(getattr(probe_report, "passed", False)):
                raise IncompleteEngineeringResult(
                    f"seed {seed} failed the global preactivity decodability-probe gate"
                )
            prepared[seed] = prepared_seed
            preactivity[str(seed)] = {
                "probe": asdict(probe_report) if probe_report is not None else None,
                "passed": True,
            }
            ledger.facts()
        if tuple(sorted(prepared)) != tuple(config.algorithm_seeds):
            raise IncompleteEngineeringResult("global preactivity preparation omitted a registered seed")
        preactivity_resources = ledger.facts()
        preactivity_steps = preactivity_resources["actual_completed_steps"]
        if not isinstance(preactivity_steps, Mapping) or (
            preactivity_steps.get("predictor_data") != LEDGER_MAX_STEPS["predictor_data"]
            or any(count != 0 for name, count in preactivity_steps.items() if name != "predictor_data")
        ):
            raise IncompleteEngineeringResult(
                "global preactivity ledger must contain exactly the eight scripted predictor panels only"
            )
        _atomic_json(output_root / "global_preactivity.json", {
            "all_registered_seed_probes_passed": True, "per_seed": preactivity,
            "resource_ledger": preactivity_resources, "learned_activity_started": False,
        })
        for seed in config.algorithm_seeds:
            prepared_seed = prepared.pop(seed)
            row = _validate_seed_result(
                seed,
                adapter(prepared=prepared_seed, ledger=ledger, activity=activity,
                        writer=SeedWriter(output_root, seed)),
            )
            del prepared_seed
            raw = row.pop("_raw", None)
            if not isinstance(raw, Mapping):
                raise IncompleteEngineeringResult(f"seed {seed} omitted its in-memory raw record")
            _atomic_json(output_root / "seed_results" / f"seed_{seed}.json", row)
            per_seed_raw[seed] = dict(raw)
            per_seed[str(seed)] = row
            ledger.facts()
        if not activity.facts()["started"]:
            raise IncompleteEngineeringResult("complete execution lacked a learned optimizer activity marker")
        ledger.assert_complete()
        pre_analysis_resource_facts = ledger.facts()
        aggregate = dict(finalizer(per_seed_raw, pre_analysis_resource_facts))
        if not aggregate:
            raise IncompleteEngineeringResult("CRTO aggregate finalizer returned an empty result")
        # This boundary check includes pooled inference, the 100k trend loop,
        # and result assembly; a cap breach here must yield an incomplete run.
        resource_facts = ledger.facts()
        aggregate_packet_source = aggregate.get("result_packet")
        if not isinstance(aggregate_packet_source, Mapping):
            raise IncompleteEngineeringResult("CRTO aggregate finalizer omitted its result packet")
        from .analysis import resource_conformance
        post_analysis_resource_report = resource_conformance(
            resource_facts["actual_completed_steps"],  # type: ignore[arg-type]
            wall_seconds=float(resource_facts["wall_seconds"]),
            peak_rss_bytes=int(resource_facts["peak_rss_bytes"]),
            gpu_used=bool(resource_facts.get("gpu_enabled", False)),
            cpu_count=int(resource_facts.get("cpu_workers", 0)),
        )
        aggregate_packet = dict(aggregate_packet_source)
        aggregate_packet["resources"] = post_analysis_resource_report
        aggregate["result_packet"] = aggregate_packet
        aggregate["resources"] = post_analysis_resource_report
        aggregate_anomalies = aggregate_packet.get("anomalies")
        if not isinstance(aggregate_anomalies, list):
            raise IncompleteEngineeringResult("CRTO aggregate packet anomalies must be a list")
        result: dict[str, object] = {
            "artifact_kind": ARTIFACT_KIND, "treatment": TREATMENT, "revision": REVISION,
            "manifest": manifest, "scientific_activity": activity.facts(),
            "resource_ledger": resource_facts, "per_seed": per_seed,
            "preactivity": preactivity,
            "aggregate": aggregate,
            "question_relevant_output_exists": bool(aggregate_packet.get("question_relevant_output_exists", False)),
            "anomalies": list(aggregate_anomalies),
            "complete": True,
            "environment": {"python": platform.python_version(), "platform": platform.platform()},
        }
        _atomic_json(output_root / "raw_result.json", result)
        _atomic_json(result_path, result)
        return result
    except BaseException as error:
        incomplete = {
            "artifact_kind": ARTIFACT_KIND, "treatment": TREATMENT, "revision": REVISION,
            "manifest": manifest, "scientific_activity": activity.facts(),
            "resource_ledger": ledger.snapshot(), "per_seed": per_seed,
            "preactivity": preactivity,
            "question_relevant_output_exists": False,
            "anomalies": [{"kind": type(error).__name__, "message": str(error)}],
            "complete": False,
        }
        _atomic_json(output_root / "incomplete_result.json", incomplete)
        _atomic_json(result_path, incomplete)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the exact frozen CRTO-B1 package once")
    parser.add_argument("action", choices=("source-check", "train-evaluate-analyze"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--result", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "source-check":
        # This path imports no simulator/trainer and writes no artifacts.  It is
        # deliberately available for CM's preactivity source conformance check.
        print(json.dumps({
            "artifact_kind": ARTIFACT_KIND, "revision": REVISION,
            "registered_ledger": registered_ledger(),
            "production_command": _manifest(PRODUCTION_CONFIG, Path("<fresh-root>"), Path("<fresh-result.json>"))["production_command"],
        }, sort_keys=True))
        return 0
    if args.output_root is None or args.result is None:
        raise SystemExit("train-evaluate-analyze requires --output-root and --result")
    result = exercise(output_root=args.output_root, result_path=args.result)
    print(json.dumps({
        "result": str(args.result.resolve()), "complete": result["complete"],
        "activity_started": result["scientific_activity"]["started"],
        "actual_total_steps": result["resource_ledger"]["actual_total_steps"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
