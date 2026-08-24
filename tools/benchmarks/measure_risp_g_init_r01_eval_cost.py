"""Result-blind grouped-EVAL cost measurement for the accepted RISP R01 bytes.

Importing this module performs no file access, native load, process creation, or
measurement.  ``main`` is deliberately unusable without a separate, one-shot
authorization manifest which binds this component manifest and an unused output
path.  The component never accepts a production coordinate or payload path.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import functools
import hashlib
import importlib
import inspect
import json
import multiprocessing
from multiprocessing.connection import wait as wait_connections
import os
from pathlib import Path
import sys
import threading
import time
from typing import Any, Callable, Iterator, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
COMPONENT_MANIFEST = (
    ROOT
    / "experiments"
    / "candidates"
    / "renewal_indexed_score_plasticity"
    / "RISP_G_INIT_REACH_R01_EVAL_MEASUREMENT_COMPONENT_MANIFEST_20260823.json"
)
CANDIDATE = ROOT / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
AUTHORIZATION_SCHEMA = "RISP-G-INIT-REACH-R01-EVAL-MEASUREMENT-AUTHORIZATION-V1"
OUTPUT_SCHEMA = "RISP-G-INIT-REACH-R01-EVAL-MEASUREMENT-RESOURCE-ACCOUNTING-V1"
WORKER_PAYLOAD_SCHEMA = "RISP-G-INIT-REACH-R01-EVAL-MEASUREMENT-WORKER-FIXTURE-V1"
STAGES = (
    "CPP_BATCHED_ENVIRONMENT",
    "PYTHON_INTERACTIVE_EVENT_ADAPTER",
    "EXACT_INTERVAL_AND_ADDRESSING",
    "TRACE_REPLAY",
    "PYTORCH_FLOAT64_FORWARD_NO_GRAD",
    "PROCESS_ORCHESTRATION",
)
GROUPS = ((0, 16), (16, 32), (32, 48), (48, 64))
CELLS = (
    "G-START/ZERO-CENTER-INTACT",
    "ZERO-START/ZERO-CENTER-INTACT",
    "UNIFORM",
    "STATE-ORACLE",
)
PRODUCTION_SCHEMAS = frozenset(
    {
        "RISP-G-INIT-REACH-R01-LAZY-SHAKE256-PREFIX-20260821-01",
        "RISP-G-INIT-REACH-R01-RESULT-20260821-01",
        "RISP-G-INIT-REACH-R01-TRAINING-UNIT-20260821-01",
        "RISP-G-INIT-REACH-R01-EVALUATION-UNIT-20260821-01",
        "RISP-G-INIT-REACH-R01-STRUCTURAL-CERTIFICATE-20260821-01",
        "RISP-G-INIT-REACH-R01-RESUME-20260821-01",
    }
)
FORBIDDEN_INPUT_KEY_PARTS = (
    "coordinate",
    "frontier",
    "checkpoint_path",
    "result_path",
    "result_root",
    "partial",
    "unit_path",
    "commit_path",
    "receipt",
    "certificate_path",
)
FORBIDDEN_PATH_PARTS = (
    "coordinate",
    "frontier",
    "checkpoint",
    "results",
    "result",
    "partial",
    "training_units",
    "evaluation_units",
    "commit",
    "receipt",
    "certificate",
)


class MeasurementRefused(RuntimeError):
    """A fail-closed construction, authorization, or resource refusal."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise MeasurementRefused("JSON document must be an object")
    return value


def _valid_hex64(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _reject_production_material(value: object, *, key_path: tuple[str, ...] = ()) -> None:
    """Reject production schemas and payload/path-shaped authorization fields."""
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key).lower()
            if any(part in key for part in FORBIDDEN_INPUT_KEY_PARTS):
                raise MeasurementRefused(
                    f"authorization contains forbidden production field at {'.'.join((*key_path, key))}"
                )
            _reject_production_material(child, key_path=(*key_path, key))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_production_material(child, key_path=(*key_path, str(index)))
    elif isinstance(value, str) and value in PRODUCTION_SCHEMAS:
        raise MeasurementRefused("authorization contains a production R01 schema")


def _validate_output_path(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_absolute() or resolved == ROOT:
        raise MeasurementRefused("output must be one exact file path")
    lowered_parts = tuple(part.lower() for part in resolved.parts)
    if any(token in part for part in lowered_parts for token in FORBIDDEN_PATH_PARTS):
        raise MeasurementRefused("output path resembles a forbidden R01 production path")
    if resolved.suffix.lower() != ".json":
        raise MeasurementRefused("output must be a JSON file")
    if not resolved.parent.is_dir():
        raise MeasurementRefused("authorized output parent must already exist")
    return resolved


def _validate_authorization_manifest_path(path: Path) -> Path:
    resolved = path.resolve()
    lowered_parts = tuple(part.lower() for part in resolved.parts)
    if any(token in part for part in lowered_parts for token in FORBIDDEN_PATH_PARTS):
        raise MeasurementRefused("authorization manifest is located in a forbidden R01 production path")
    if resolved.suffix.lower() != ".json" or not resolved.is_file():
        raise MeasurementRefused("authorization manifest must be one existing JSON file")
    return resolved


def load_component_manifest() -> tuple[dict[str, Any], str]:
    manifest = _load_json_object(COMPONENT_MANIFEST)
    validate_component_manifest(manifest)
    return manifest, _sha256(COMPONENT_MANIFEST)


def validate_component_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("schema") != "RISP-G-INIT-REACH-R01-EVAL-MEASUREMENT-COMPONENT-V1":
        raise MeasurementRefused("component manifest schema mismatch")
    if manifest.get("armed") is not False or manifest.get("measurement_authority") is not False:
        raise MeasurementRefused("component manifest must remain unarmed")
    fixture = manifest.get("fixture")
    if not isinstance(fixture, Mapping):
        raise MeasurementRefused("fixture declaration is missing")
    if (
        fixture.get("namespace_class") != "TEST_ONLY"
        or fixture.get("namespace") != "TEST/RISP-G-INIT-REACH/CERTIFICATE-FIXTURE/V1"
        or fixture.get("registered") is not False
        or fixture.get("test_fixture") is not True
        or not _valid_hex64(fixture.get("fixture_root"))
    ):
        raise MeasurementRefused("fixture declaration is not permanently TEST-only")
    grouped = manifest.get("grouped_eval")
    if not isinstance(grouped, Mapping):
        raise MeasurementRefused("grouped EVAL declaration is missing")
    observed_groups = tuple(tuple(int(item) for item in pair) for pair in grouped.get("episode_groups", ()))
    if (
        observed_groups != GROUPS
        or grouped.get("episodes_per_fixture") != 64
        or grouped.get("agent_lanes_per_group") != 32
        or grouped.get("workers") != 2
        or grouped.get("start_method") != "spawn"
    ):
        raise MeasurementRefused("grouped EVAL shape is not exact four-by-width-16/two-spawn-worker")
    strata = manifest.get("strata")
    if not isinstance(strata, list) or len(strata) != 20:
        raise MeasurementRefused("manifest must retain exactly twenty strata")
    pairs: set[tuple[int, str]] = set()
    seeds: set[int] = set()
    for stratum in strata:
        if not isinstance(stratum, Mapping):
            raise MeasurementRefused("stratum must be an object")
        schedule_id, cell = stratum.get("schedule_id"), stratum.get("cell")
        fixture_seeds = stratum.get("fixture_seeds")
        if schedule_id not in range(5) or cell not in CELLS:
            raise MeasurementRefused("unknown schedule-by-cell stratum")
        if not isinstance(fixture_seeds, list) or len(fixture_seeds) != 2:
            raise MeasurementRefused("every stratum requires exactly two fixtures")
        if any(isinstance(seed, bool) or not isinstance(seed, int) or seed in range(16) for seed in fixture_seeds):
            raise MeasurementRefused("fixture seeds must not impersonate registered R01 seeds")
        pairs.add((int(schedule_id), str(cell)))
        seeds.update(int(seed) for seed in fixture_seeds)
    if pairs != {(schedule, cell) for schedule in range(5) for cell in CELLS} or len(seeds) != 40:
        raise MeasurementRefused("strata do not form the exact 5x4/40-fixture plan")
    limits = manifest.get("limits")
    required_limits = {
        "maximum_batches": 20,
        "maximum_fixture_units": 40,
        "maximum_incremental_cpu_seconds": 28800,
        "maximum_foreground_wall_seconds": 13800,
        "workers": 2,
        "cpu_cores": 2,
        "gpu": False,
        "per_worker_rss_limit_bytes": 1073741824,
        "process_group_rss_limit_bytes": 2684354560,
        "scratch_limit_bytes": 1073741824,
        "durable_output_limit_bytes": 67108864,
        "dispatches": 1,
        "automatic_relaunch": False,
    }
    if not isinstance(limits, Mapping) or dict(limits) != required_limits:
        raise MeasurementRefused("measurement resource envelope changed")
    if tuple(manifest.get("stages", ())) != STAGES:
        raise MeasurementRefused("six-stage measurement declaration changed")


def validate_authorization(
    authorization: Mapping[str, Any], *, component_sha256: str, output_path: Path,
    limits: Mapping[str, Any],
) -> None:
    _reject_production_material(authorization)
    required = {
        "schema": AUTHORIZATION_SCHEMA,
        "authorized": True,
        "authorized_activity": "ONE_RESULT_BLIND_GROUPED_EVAL_MEASUREMENT",
        "component_manifest_sha256": component_sha256,
        "output_path": str(output_path),
        "dispatches": 1,
        "automatic_relaunch": False,
        "limits": dict(limits),
    }
    for key, expected in required.items():
        if authorization.get(key) != expected:
            raise MeasurementRefused(f"authorization field {key!r} is absent or mismatched")
    if not _valid_hex64(authorization.get("authorization_id")):
        raise MeasurementRefused("authorization_id must be a fresh 64-hex identifier")
    if set(authorization) != {*required, "authorization_id"}:
        raise MeasurementRefused("authorization contains fields outside the closed schema")


def worker_payloads_for_stratum(
    manifest: Mapping[str, Any], stratum: Mapping[str, Any], component_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fixture = manifest["fixture"]
    payloads = tuple(
        {
            "schema": WORKER_PAYLOAD_SCHEMA,
            "component_sha256": component_sha256,
            "namespace_class": "TEST_ONLY",
            "namespace": fixture["namespace"],
            "fixture_root": fixture["fixture_root"],
            "stratum_id": stratum["id"],
            "lane": lane,
            "fixture_seed": int(seed),
            "schedule_id": int(stratum["schedule_id"]),
            "cell": str(stratum["cell"]),
        }
        for lane, seed in enumerate(stratum["fixture_seeds"])
    )
    for payload in payloads:
        if any(isinstance(value, Path) for value in payload.values()):
            raise MeasurementRefused("worker payload contains a path object")
        if set(payload) != {
            "schema", "component_sha256", "namespace_class", "namespace",
            "fixture_root", "stratum_id", "lane", "fixture_seed", "schedule_id", "cell",
        }:
            raise MeasurementRefused("worker payload schema drifted")
    return payloads  # type: ignore[return-value]


def _protected_snapshot(manifest: Mapping[str, Any]) -> dict[str, dict[str, int | str]]:
    entries: dict[str, tuple[Path, str]] = {}
    for relative, expected in manifest["protected_files"].items():
        entries[str(relative)] = (ROOT / str(relative), str(expected))
    backend = manifest["accepted_backend_record"]
    entries["accepted_backend_record"] = (ROOT / str(backend["path"]), str(backend["sha256"]))
    native = manifest["accepted_native"]
    entries["accepted_native_dll"] = (Path(str(native["artifact_path"])), str(native["artifact_sha256"]))
    snapshot: dict[str, dict[str, int | str]] = {}
    for label, (path, expected) in entries.items():
        if not path.is_file():
            raise MeasurementRefused(f"protected file is missing: {label}")
        observed = _sha256(path)
        if observed != expected:
            raise MeasurementRefused(f"protected hash mismatch: {label}")
        stat = path.stat()
        snapshot[label] = {"sha256": observed, "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    if snapshot["accepted_native_dll"]["size_bytes"] != int(native["artifact_size_bytes"]):
        raise MeasurementRefused("accepted native DLL size mismatch")
    return snapshot


def _load_runtime(manifest: Mapping[str, Any]) -> dict[str, Any]:
    candidate_text = str(CANDIDATE)
    if candidate_text not in sys.path:
        sys.path.insert(0, candidate_text)
    native = importlib.import_module("g_init_r01_native_backend")
    # The shared registry imports the package-qualified name.  Bind both names
    # to one already-patched object before the registry can reach its loader.
    sys.modules[
        "experiments.candidates.renewal_indexed_score_plasticity.g_init_r01_native_backend"
    ] = native
    experiment = importlib.import_module("g_init_r01_experiment")
    shared = importlib.import_module("envs.native.production_backend")
    accepted = manifest["accepted_native"]
    artifact = Path(str(accepted["artifact_path"])).resolve()
    expected_key = str(accepted["build_key"])
    current_key = native._current_loader_cache_key(None)
    if current_key[1] != expected_key:
        raise MeasurementRefused("current native build key differs from the accepted cache key")
    expected_cache = artifact.parent.resolve()
    if Path(current_key[0]).resolve() / expected_key != expected_cache:
        raise MeasurementRefused("accepted DLL is not at the current source/runtime cache key")

    def strict_compiled_path(cache_key: tuple[str, str]) -> Path:
        if cache_key != current_key:
            raise MeasurementRefused("native resolver requested an unaccepted cache key")
        if not artifact.is_file() or _sha256(artifact) != accepted["artifact_sha256"]:
            raise MeasurementRefused("accepted native DLL is absent or changed; compilation is forbidden")
        return artifact

    native._compiled_path = strict_compiled_path
    capability = shared.backend_capability(str(accepted["component"]))
    semantics = {
        "component": capability.component,
        "production_backend": capability.production_backend,
        "native_boundary": capability.native_boundary,
        "batch_api": capability.batch_api,
        "full_reset_step_cpp": capability.full_reset_step_cpp,
    }
    expected_semantics = {
        "component": accepted["component"],
        "production_backend": accepted["backend"],
        "native_boundary": accepted["native_boundary"],
        "batch_api": True,
        "full_reset_step_cpp": True,
    }
    if semantics != expected_semantics or accepted.get("python_fallback") is not False:
        raise MeasurementRefused("live shared registry semantics differ from the accepted component")
    loaded = native.require_cpp_batched_backend()
    loaded_path = Path(str(vars(loaded).get("_name", ""))).resolve()
    if loaded_path != artifact or _sha256(loaded_path) != accepted["artifact_sha256"]:
        raise MeasurementRefused("strict native resolver loaded a different artifact")
    source = inspect.getsource(experiment._evaluate_episode_group_native).lower()
    forbidden = tuple(str(token).lower() for token in manifest["trace_replay"]["forbidden_helper_tokens"])
    if any(token in source for token in forbidden):
        raise MeasurementRefused("grouped EVAL helper contains a TRAIN/replay call")
    return {"native": native, "experiment": experiment, "shared": shared}


def _rss_bytes(*, peak: bool) -> int | None:
    try:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        )
        if not psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb,
        ):
            return None
        return int(counters.PeakWorkingSetSize if peak else counters.WorkingSetSize)
    except Exception:
        return None


@dataclass
class _Frame:
    stage: str
    wall_started_ns: int
    cpu_started_ns: int
    child_wall_ns: int = 0
    child_cpu_ns: int = 0


class StageLedger:
    """Nested exclusive CPU/wall timers with active-stage RSS tagging."""

    def __init__(self) -> None:
        self.wall_ns = {stage: 0 for stage in STAGES}
        self.cpu_ns = {stage: 0 for stage in STAGES}
        self.rss_max_bytes: dict[str, int] = {}
        self._stack: list[_Frame] = []
        self._lock = threading.Lock()

    def _sample(self, stage: str | None = None) -> None:
        rss = _rss_bytes(peak=False)
        if rss is None:
            return
        with self._lock:
            label = stage or (self._stack[-1].stage if self._stack else "UNCLASSIFIED_DIAGNOSTIC")
            self.rss_max_bytes[label] = max(self.rss_max_bytes.get(label, 0), rss)

    @contextmanager
    def measure(self, stage: str) -> Iterator[None]:
        if stage not in STAGES or stage in ("TRACE_REPLAY", "PROCESS_ORCHESTRATION"):
            raise MeasurementRefused("invalid directly timed stage")
        frame = _Frame(stage, time.perf_counter_ns(), time.process_time_ns())
        with self._lock:
            self._stack.append(frame)
        self._sample(stage)
        try:
            yield
        finally:
            wall_elapsed = time.perf_counter_ns() - frame.wall_started_ns
            cpu_elapsed = time.process_time_ns() - frame.cpu_started_ns
            self._sample(stage)
            with self._lock:
                if not self._stack or self._stack[-1] is not frame:
                    raise MeasurementRefused("diagnostic timer stack corrupted")
                self._stack.pop()
                wall_exclusive = wall_elapsed - frame.child_wall_ns
                cpu_exclusive = cpu_elapsed - frame.child_cpu_ns
                if wall_exclusive < 0 or cpu_exclusive < 0:
                    raise MeasurementRefused("diagnostic exclusive timer became negative")
                self.wall_ns[stage] += wall_exclusive
                self.cpu_ns[stage] += cpu_exclusive
                if self._stack:
                    self._stack[-1].child_wall_ns += wall_elapsed
                    self._stack[-1].child_cpu_ns += cpu_elapsed

    def active_stage(self) -> str:
        with self._lock:
            return self._stack[-1].stage if self._stack else "UNCLASSIFIED_DIAGNOSTIC"


class _RssObserver:
    def __init__(self, ledger: StageLedger) -> None:
        self._ledger = ledger
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="risp-rss-observer", daemon=True)

    def _run(self) -> None:
        while not self._stop.wait(0.01):
            self._ledger._sample(self._ledger.active_stage())

    def __enter__(self) -> "_RssObserver":
        self._ledger._sample("UNCLASSIFIED_DIAGNOSTIC")
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=2.0)
        if self._thread.is_alive():
            raise MeasurementRefused("diagnostic RSS observer did not stop")
        self._ledger._sample("UNCLASSIFIED_DIAGNOSTIC")


def _timed_function(function: Callable[..., Any], ledger: StageLedger, stage: str) -> Callable[..., Any]:
    @functools.wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        with ledger.measure(stage):
            return function(*args, **kwargs)
    return wrapped


@contextmanager
def _diagnostic_hooks(runtime: Mapping[str, Any], ledger: StageLedger) -> Iterator[dict[str, int]]:
    from unittest.mock import patch

    experiment, native = runtime["experiment"], runtime["native"]
    real_host = native.NativeInteractiveBatch
    trace_calls = {"count": 0}

    class TimedNativeInteractiveBatch:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            with ledger.measure("CPP_BATCHED_ENVIRONMENT"):
                self._inner = real_host(*args, **kwargs)
            self.initial = self._inner.initial

        def step(self, *args: Any, **kwargs: Any) -> Any:
            with ledger.measure("CPP_BATCHED_ENVIRONMENT"):
                return self._inner.step(*args, **kwargs)

        def step_active(self, *args: Any, **kwargs: Any) -> Any:
            with ledger.measure("CPP_BATCHED_ENVIRONMENT"):
                return self._inner.step_active(*args, **kwargs)

        def close(self) -> None:
            with ledger.measure("CPP_BATCHED_ENVIRONMENT"):
                self._inner.close()

        def __enter__(self) -> "TimedNativeInteractiveBatch":
            return self

        def __exit__(self, *_: object) -> None:
            self.close()

        def __getattr__(self, name: str) -> Any:
            return getattr(self._inner, name)

    def forbidden_trace(*_args: Any, **_kwargs: Any) -> Any:
        trace_calls["count"] += 1
        raise MeasurementRefused("TRACE_REPLAY became reachable from grouped EVAL")

    exact_names = (
        "exact_cat", "bit_prefix", "event_identity", "_event_token", "affinity_interval",
        "interval_float", "interval_int", "interval_ratio", "interval_vector_floats",
        "iadd", "idiv_positive", "imul", "isub", "isum", "rounded_float",
    )
    torch_names = ("load_model", "_slow_bundle", "_behavior_bundle", "_recurrence_bundle")
    with ExitStack() as stack:
        stack.enter_context(patch.object(native, "NativeInteractiveBatch", TimedNativeInteractiveBatch))
        for name in exact_names:
            if hasattr(experiment, name):
                stack.enter_context(
                    patch.object(
                        experiment, name,
                        _timed_function(getattr(experiment, name), ledger, "EXACT_INTERVAL_AND_ADDRESSING"),
                    )
                )
        for name in torch_names:
            stack.enter_context(
                patch.object(
                    experiment, name,
                    _timed_function(getattr(experiment, name), ledger, "PYTORCH_FLOAT64_FORWARD_NO_GRAD"),
                )
            )
        for name in ("_train_episode", "_train_episode_group_native"):
            stack.enter_context(patch.object(experiment, name, forbidden_trace))
        yield trace_calls


def _checkpoint_packet(experiment: Any, seed: int, arm: str) -> dict[str, Any]:
    import torch

    zero_slow = {
        "w1": torch.zeros((8, 2), dtype=torch.float64),
        "w2": torch.zeros((4, 8), dtype=torch.float64),
        "w3": torch.zeros((3, 4), dtype=torch.float64),
    }
    model = experiment.TrackModel(seed, arm, slow_arrays=zero_slow)
    state = experiment.state_dict_json(model)
    return {
        "schema": experiment.TEST_TRAINING_SCHEMA,
        "science_revision": experiment.TEST_FIXTURE_REVISION,
        "binding_class": "TEST_ONLY",
        "test_fixture": True,
        "registered": False,
        "algorithm_seed": seed,
        "arm": arm,
        "updates": 1,
        "episodes_per_batch": 2,
        "conclusion_update": experiment.REGISTERED_UPDATES,
        "test_fixture_benchmark_reduced": True,
        "final_state": state,
    }


def _run_grouped_fixture_body(
    runtime: Mapping[str, Any], payload: Mapping[str, Any], ledger: StageLedger | None,
) -> str:
    experiment = runtime["experiment"]
    seed, schedule_id, cell = int(payload["fixture_seed"]), int(payload["schedule_id"]), str(payload["cell"])
    arm, mode = experiment._cell_parts(cell)
    model = None
    slow_cache: dict[int, Any] = {}
    if arm is not None:
        checkpoint = _checkpoint_packet(experiment, seed, arm)
        state = experiment._checkpoint_state_from_training_packet(checkpoint, arm, "TEST_ONLY", seed)
        model = experiment.load_model(seed, arm, state)
        slow_cache = {
            tau: experiment._slow_bundle(model, experiment._observation(tau, duration))
            for tau, duration, _ in experiment.schedule_rows(schedule_id)
        }
    audit = experiment.SamplerAudit()
    summary = experiment.EvalSummary()
    observed_groups: list[tuple[int, int]] = []
    for start, stop in GROUPS:
        _worker_resource_guard(payload)
        if ledger is None:
            experiment._evaluate_episode_group_native(
                seed=seed, schedule_id=schedule_id, episodes=tuple(range(start, stop)),
                arm=arm, mode=mode, model=model, slow_cache=slow_cache,
                audit=audit, summary=summary,
            )
        else:
            with ledger.measure("PYTHON_INTERACTIVE_EVENT_ADAPTER"):
                experiment._evaluate_episode_group_native(
                    seed=seed, schedule_id=schedule_id, episodes=tuple(range(start, stop)),
                    arm=arm, mode=mode, model=model, slow_cache=slow_cache,
                    audit=audit, summary=summary,
                )
        observed_groups.append((start, stop))
        _worker_resource_guard(payload)
    rows = experiment.schedule_rows(schedule_id)
    expected_decisions = len(rows) * 64 * 2
    expected_updates = (len(rows) - 1) * 64 * 2 if arm is not None else 0
    expected_audit = {
        "INIT_SECTOR": 128,
        "ACTION": expected_decisions,
        "MOTION": expected_decisions,
        "ACK": expected_decisions,
    }
    if observed_groups != list(GROUPS):
        raise MeasurementRefused("grouped helper call order changed")
    if summary.decisions != expected_decisions or summary.updates != expected_updates:
        raise MeasurementRefused("grouped EVAL lifecycle census mismatch")
    if audit.calls != expected_audit:
        raise MeasurementRefused("grouped EVAL event census mismatch")
    if summary.direct_tv_max_residual > 2.0**-40:
        raise MeasurementRefused("grouped EVAL direct-mixture equivalence failed")
    if mode == "INTACT":
        expected_rows = {0: 47, 1: 23, 2: 15, 3: 7, 4: 23}[schedule_id] * 64 * 2
        if len(summary.tv_values) != expected_rows or len(summary.delta_values) != expected_rows:
            raise MeasurementRefused("grouped EVAL learned diagnostic census mismatch")
    structural = {
        "helper": "_evaluate_episode_group_native",
        "groups": GROUPS,
        "schedule_id": schedule_id,
        "cell": cell,
        "fixture_lane": int(payload["lane"]),
        "lifecycle_census_valid": True,
        "event_census_valid": True,
        "summary_values_serialized": False,
    }
    return _json_sha256(structural)


def _run_grouped_fixture(
    runtime: Mapping[str, Any], payload: Mapping[str, Any], ledger: StageLedger | None,
) -> str:
    torch = importlib.import_module("torch")
    with torch.no_grad():
        return _run_grouped_fixture_body(runtime, payload, ledger)


def _pass_a(
    runtime: Mapping[str, Any], payload: Mapping[str, Any], *, cpu_started: int | None = None,
    wall_started: int | None = None,
) -> dict[str, Any]:
    cpu_started = time.process_time_ns() if cpu_started is None else cpu_started
    wall_started = time.perf_counter_ns() if wall_started is None else wall_started
    digest = _run_grouped_fixture(runtime, payload, None)
    wall_ns, cpu_ns = time.perf_counter_ns() - wall_started, time.process_time_ns() - cpu_started
    peak_rss = _rss_bytes(peak=True)
    if peak_rss is None:
        raise MeasurementRefused("pass A worker RSS is unavailable")
    return {
        "fixture_id": f"{payload['stratum_id']}::lane_{payload['lane']}",
        "structural_equivalence_sha256": digest,
        "worker_wall_ns": wall_ns,
        "worker_cpu_ns": cpu_ns,
        "worker_peak_rss_bytes": peak_rss,
        "pid": os.getpid(),
        "forecast_eligible": True,
    }


def _pass_b(
    runtime: Mapping[str, Any], payload: Mapping[str, Any], *, cpu_started: int | None = None,
    wall_started: int | None = None,
) -> dict[str, Any]:
    ledger = StageLedger()
    cpu_started = time.process_time_ns() if cpu_started is None else cpu_started
    wall_started = time.perf_counter_ns() if wall_started is None else wall_started
    with _RssObserver(ledger):
        with _diagnostic_hooks(runtime, ledger) as trace_calls:
            digest = _run_grouped_fixture(runtime, payload, ledger)
    wall_ns, cpu_ns = time.perf_counter_ns() - wall_started, time.process_time_ns() - cpu_started
    if trace_calls["count"] != 0:
        raise MeasurementRefused("TRACE_REPLAY call census is nonzero")
    applicable = {
        "CPP_BATCHED_ENVIRONMENT",
        "PYTHON_INTERACTIVE_EVENT_ADAPTER",
        "EXACT_INTERVAL_AND_ADDRESSING",
    }
    if str(payload["cell"]) not in ("UNIFORM", "STATE-ORACLE"):
        applicable.add("PYTORCH_FLOAT64_FORWARD_NO_GRAD")
    if any(stage not in ledger.rss_max_bytes for stage in applicable):
        raise MeasurementRefused("applicable diagnostic stage has no RSS observation")
    measured_wall = sum(ledger.wall_ns[stage] for stage in STAGES)
    measured_cpu = sum(ledger.cpu_ns[stage] for stage in STAGES)
    wall_residual = wall_ns - measured_wall
    cpu_residual = cpu_ns - measured_cpu
    tolerance_ns = 2_000_000
    if wall_residual < -tolerance_ns or cpu_residual < -tolerance_ns:
        raise MeasurementRefused("diagnostic attribution has a negative residual")
    wall_residual, cpu_residual = max(0, wall_residual), max(0, cpu_residual)
    wall_closure = abs(wall_ns - (measured_wall + wall_residual))
    cpu_closure = abs(cpu_ns - (measured_cpu + cpu_residual))
    if wall_closure > tolerance_ns or cpu_closure > tolerance_ns:
        raise MeasurementRefused("diagnostic accounting closure exceeded tolerance")
    stage_rows: dict[str, Any] = {}
    for stage in STAGES[:-1]:
        if stage == "TRACE_REPLAY":
            stage_rows[stage] = {
                "status": "NOT_APPLICABLE_SOURCE_PROVED",
                "calls": 0,
                "wall_ns": 0,
                "cpu_ns": 0,
                "rss_max_bytes": None,
            }
        elif stage not in applicable:
            stage_rows[stage] = {
                "status": "NOT_APPLICABLE_BY_CELL",
                "wall_ns": 0,
                "cpu_ns": 0,
                "rss_max_bytes": None,
            }
        else:
            stage_rows[stage] = {
                "status": "DIAGNOSTIC_ONLY",
                "wall_ns": ledger.wall_ns[stage],
                "cpu_ns": ledger.cpu_ns[stage],
                "rss_max_bytes": ledger.rss_max_bytes[stage],
            }
    peak_rss = _rss_bytes(peak=True)
    if peak_rss is None:
        raise MeasurementRefused("pass B worker RSS is unavailable")
    return {
        "fixture_id": f"{payload['stratum_id']}::lane_{payload['lane']}",
        "structural_equivalence_sha256": digest,
        "worker_wall_ns": wall_ns,
        "worker_cpu_ns": cpu_ns,
        "worker_peak_rss_bytes": peak_rss,
        "pid": os.getpid(),
        "stages": stage_rows,
        "unclassified_residual_wall_ns": wall_residual,
        "unclassified_residual_cpu_ns": cpu_residual,
        "accounting_closure_wall_ns": wall_closure,
        "accounting_closure_cpu_ns": cpu_closure,
        "forecast_eligible": False,
    }


def _validate_worker_payload(payload: Mapping[str, Any], manifest: Mapping[str, Any], component_sha: str) -> None:
    if payload.get("schema") != WORKER_PAYLOAD_SCHEMA or payload.get("component_sha256") != component_sha:
        raise MeasurementRefused("worker payload binding mismatch")
    if payload.get("namespace_class") != "TEST_ONLY" or payload.get("namespace") != manifest["fixture"]["namespace"]:
        raise MeasurementRefused("worker payload is not permanently TEST-only")
    if payload.get("fixture_root") != manifest["fixture"]["fixture_root"]:
        raise MeasurementRefused("worker fixture root mismatch")
    if payload.get("fixture_seed") in range(16) or payload.get("cell") not in CELLS or payload.get("schedule_id") not in range(5):
        raise MeasurementRefused("worker attempted a production identity")
    deadline = payload.get("foreground_deadline_monotonic")
    rss_limit = payload.get("per_worker_rss_limit_bytes")
    if not isinstance(deadline, (int, float)) or isinstance(deadline, bool) or deadline <= time.perf_counter():
        raise MeasurementRefused("worker foreground deadline is absent or expired")
    if rss_limit != manifest["limits"]["per_worker_rss_limit_bytes"]:
        raise MeasurementRefused("worker RSS ceiling differs from the frozen manifest")


def _worker_resource_guard(payload: Mapping[str, Any]) -> None:
    if time.perf_counter() >= float(payload["foreground_deadline_monotonic"]):
        raise MeasurementRefused("worker reached the foreground wall ceiling")
    peak = _rss_bytes(peak=True)
    if peak is None:
        raise MeasurementRefused("worker RSS guard is unavailable")
    if peak > int(payload["per_worker_rss_limit_bytes"]):
        raise MeasurementRefused("worker reached the per-worker RSS ceiling")


def _worker_entry(payload: dict[str, Any], pass_a_sender: Any, diagnostic_release: Any) -> dict[str, Any]:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    pass_a_cpu_started, pass_a_wall_started = time.process_time_ns(), time.perf_counter_ns()
    manifest, component_sha = load_component_manifest()
    _validate_worker_payload(payload, manifest, component_sha)
    _protected_snapshot(manifest)
    runtime = _load_runtime(manifest)
    torch = importlib.import_module("torch")
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    if torch.cuda.is_initialized():
        raise MeasurementRefused("GPU state is initialized in a CPU-only worker")
    experiment = runtime["experiment"]
    if experiment.coordinate_root() is not None:
        raise MeasurementRefused("worker imported with a production coordinate binding")
    if experiment.fixture_root() is None:
        experiment.configure_test_fixture_root(str(payload["fixture_root"]))
    elif experiment.fixture_root() != payload["fixture_root"]:
        raise MeasurementRefused("worker TEST fixture binding mismatch")
    pass_a = _pass_a(
        runtime, payload, cpu_started=pass_a_cpu_started, wall_started=pass_a_wall_started,
    )
    pass_a_sender.send(pass_a)
    pass_a_sender.close()
    release = diagnostic_release.recv()
    diagnostic_release.close()
    if release != "BEGIN_DIAGNOSTIC_PASS_B":
        raise MeasurementRefused("diagnostic pass was not released by the parent boundary")
    pass_b_cpu_started, pass_b_wall_started = time.process_time_ns(), time.perf_counter_ns()
    _protected_snapshot(manifest)
    runtime = _load_runtime(manifest)
    diagnostic = _pass_b(
        runtime, payload, cpu_started=pass_b_cpu_started, wall_started=pass_b_wall_started,
    )
    if pass_a["structural_equivalence_sha256"] != diagnostic["structural_equivalence_sha256"]:
        raise MeasurementRefused("pass A and pass B structural equivalence digests differ")
    return {"pass_a": pass_a, "pass_b": diagnostic}


def _remaining_seconds(started: float, limit: int) -> float:
    remaining = float(limit) - (time.perf_counter() - started)
    if remaining <= 0:
        raise MeasurementRefused("foreground wall ceiling reached")
    return remaining


def _run_batch(
    payloads: Sequence[dict[str, Any]], *, wall_started: float, wall_limit: int,
    per_worker_rss_limit_bytes: int,
) -> dict[str, Any]:
    if len(payloads) != 2:
        raise MeasurementRefused("one logical batch requires exactly two fixtures")
    context = multiprocessing.get_context("spawn")
    pass_a_pipes = [context.Pipe(duplex=False) for _ in payloads]
    release_pipes = [context.Pipe(duplex=False) for _ in payloads]
    batch_started, batch_cpu_started = time.perf_counter_ns(), time.process_time_ns()
    futures = []
    with ProcessPoolExecutor(max_workers=2, mp_context=context) as executor:
        try:
            for index, payload in enumerate(payloads):
                pass_a_receiver, pass_a_sender = pass_a_pipes[index]
                release_receiver, _release_sender = release_pipes[index]
                dispatched_payload = {
                    **payload,
                    "foreground_deadline_monotonic": wall_started + wall_limit,
                    "per_worker_rss_limit_bytes": per_worker_rss_limit_bytes,
                }
                futures.append(
                    executor.submit(_worker_entry, dispatched_payload, pass_a_sender, release_receiver)
                )
            receivers = [pair[0] for pair in pass_a_pipes]
            pending = set(receivers)
            pass_a_rows: dict[Any, dict[str, Any]] = {}
            while pending:
                timeout = min(0.25, _remaining_seconds(wall_started, wall_limit))
                ready = wait_connections(tuple(pending), timeout=timeout)
                for connection in ready:
                    pass_a_rows[connection] = connection.recv()
                    pending.remove(connection)
                if not ready:
                    for future in futures:
                        if future.done():
                            future.result()
            pass_a_boundary_wall_ns = time.perf_counter_ns() - batch_started
            pass_a_parent_cpu_ns = time.process_time_ns() - batch_cpu_started
            diagnostic_started, diagnostic_cpu_started = time.perf_counter_ns(), time.process_time_ns()
            for _receiver, sender in release_pipes:
                sender.send("BEGIN_DIAGNOSTIC_PASS_B")
            results = [future.result(timeout=_remaining_seconds(wall_started, wall_limit)) for future in futures]
            diagnostic_boundary_wall_ns = time.perf_counter_ns() - diagnostic_started
            diagnostic_parent_cpu_ns = time.process_time_ns() - diagnostic_cpu_started
        except BaseException:
            for _receiver, sender in release_pipes:
                try:
                    sender.send("ABORT_PASS_B")
                except (BrokenPipeError, EOFError, OSError):
                    pass
            for future in futures:
                future.cancel()
            raise
    for receiver, sender in pass_a_pipes:
        receiver.close()
        sender.close()
    for receiver, sender in release_pipes:
        receiver.close()
        sender.close()
    ordered_pass_a = [pass_a_rows[pair[0]] for pair in pass_a_pipes]
    if any(result["pass_a"] != row for result, row in zip(results, ordered_pass_a)):
        raise MeasurementRefused("worker final return changed its pass A record")
    pids = {int(result["pass_a"]["pid"]) for result in results}
    if len(pids) != 2:
        raise MeasurementRefused("logical batch did not use exactly two spawn workers")
    max_b_wall = max(int(result["pass_b"]["worker_wall_ns"]) for result in results)
    orchestration_wall = max(0, diagnostic_boundary_wall_ns - max_b_wall)
    orchestration_rss = _rss_bytes(peak=True)
    if orchestration_rss is None:
        raise MeasurementRefused("parent RSS is unavailable")
    for result in results:
        a, b = result["pass_a"], result["pass_b"]
        b["instrumentation_overhead"] = {
            "worker_wall_delta_ns": int(b["worker_wall_ns"]) - int(a["worker_wall_ns"]),
            "worker_cpu_delta_ns": int(b["worker_cpu_ns"]) - int(a["worker_cpu_ns"]),
            "worker_wall_ratio": None if not a["worker_wall_ns"] else b["worker_wall_ns"] / a["worker_wall_ns"],
            "worker_cpu_ratio": None if not a["worker_cpu_ns"] else b["worker_cpu_ns"] / a["worker_cpu_ns"],
            "forecast_input": False,
        }
    return {
        "stratum_id": payloads[0]["stratum_id"],
        "pass_a_batch": {
            "wall_ns": pass_a_boundary_wall_ns,
            "parent_cpu_ns": pass_a_parent_cpu_ns,
            "forecast_input": True,
        },
        "pass_b_batch": {
            "wall_ns": diagnostic_boundary_wall_ns,
            "parent_cpu_ns": diagnostic_parent_cpu_ns,
            "forecast_input": False,
            "stage": {
                "name": "PROCESS_ORCHESTRATION",
                "status": "DIAGNOSTIC_ONLY",
                "wall_ns": orchestration_wall,
                "cpu_ns": diagnostic_parent_cpu_ns,
                "rss_max_bytes": orchestration_rss,
            },
        },
        "fixtures": results,
    }


def _cap_accounting(batch: Mapping[str, Any], limits: Mapping[str, Any]) -> dict[str, int]:
    worker_cpu = sum(
        int(fixture[pass_name]["worker_cpu_ns"])
        for fixture in batch["fixtures"]
        for pass_name in ("pass_a", "pass_b")
    )
    parent_cpu = int(batch["pass_a_batch"]["parent_cpu_ns"]) + int(batch["pass_b_batch"]["parent_cpu_ns"])
    worker_peaks = [int(fixture["pass_b"]["worker_peak_rss_bytes"]) for fixture in batch["fixtures"]]
    parent_peak = _rss_bytes(peak=True)
    if parent_peak is None:
        raise MeasurementRefused("parent peak RSS is unavailable")
    if any(value > limits["per_worker_rss_limit_bytes"] for value in worker_peaks):
        raise MeasurementRefused("per-worker RSS ceiling exceeded")
    group_peak = parent_peak + sum(worker_peaks)
    if group_peak > limits["process_group_rss_limit_bytes"]:
        raise MeasurementRefused("process-group RSS ceiling exceeded")
    return {
        "incremental_cpu_ns": worker_cpu + parent_cpu,
        "process_group_peak_rss_bytes": group_peak,
        "per_worker_peak_rss_max_bytes": max(worker_peaks),
    }


def _projection(completed: Sequence[Mapping[str, Any]], weight: int) -> dict[str, Any]:
    low_cpu = central_cpu = high_cpu = central_wall = high_wall = 0
    for batch in completed:
        worker_cpu = [int(row["pass_a"]["worker_cpu_ns"]) for row in batch["fixtures"]]
        batch_wall = int(batch["pass_a_batch"]["wall_ns"])
        parent_cpu = int(batch["pass_a_batch"]["parent_cpu_ns"])
        low_cpu += weight * (parent_cpu + 2 * min(worker_cpu))
        central_cpu += weight * (parent_cpu + sum(worker_cpu))
        high_cpu += weight * (parent_cpu + 2 * max(worker_cpu))
        central_wall += weight * batch_wall
        high_wall += weight * max(batch_wall, *(int(row["pass_a"]["worker_wall_ns"]) for row in batch["fixtures"]))
    return {
        "forecast_source": "PASS_A_UNINSTRUMENTED_ONLY",
        "projected_batches": len(completed) * weight,
        "cpu_ns_low": low_cpu,
        "cpu_ns_central": central_cpu,
        "cpu_ns_empirical_high": high_cpu,
        "wall_ns_central": central_wall,
        "wall_ns_empirical_high": high_wall,
        "unobserved_tail_status": "RETAINED_EXPLICITLY_NO_PROBABILISTIC_UPPER_BOUND",
    }


def _assert_redacted_output(value: object, *, key_path: tuple[str, ...] = ()) -> None:
    forbidden_value_keys = {
        "action", "actions", "ack", "acks", "reward", "rewards", "belief", "beliefs",
        "offline", "qualification", "qualifications", "tensor", "tensors", "packet", "packets", "q",
    }
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key).lower()
            segments = set(key.replace("-", "_").split("_"))
            if segments.intersection(forbidden_value_keys):
                raise MeasurementRefused(
                    f"durable output contains a forbidden payload-value field at {'.'.join((*key_path, key))}"
                )
            _assert_redacted_output(child, key_path=(*key_path, key))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_redacted_output(child, key_path=(*key_path, str(index)))
    elif isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
        raise MeasurementRefused("durable output contains a non-finite number")


def _encoded_output(payload: Mapping[str, Any], limit: int) -> bytes:
    _assert_redacted_output(payload)
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > limit:
        raise MeasurementRefused("durable output ceiling exceeded")
    return encoded


def _atomic_replace(path: Path, payload: Mapping[str, Any], limit: int) -> None:
    encoded = _encoded_output(payload, limit)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.exists():
        raise MeasurementRefused("atomic output temporary path already exists")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def run_authorized_measurement(authorization_path: Path, output_path: Path) -> dict[str, Any]:
    output = _validate_output_path(output_path)
    if output.exists():
        raise MeasurementRefused("one-shot output already exists; relaunch is forbidden")
    manifest, component_sha = load_component_manifest()
    authorization = _load_json_object(_validate_authorization_manifest_path(authorization_path))
    validate_authorization(
        authorization, component_sha256=component_sha, output_path=output,
        limits=manifest["limits"],
    )
    before = _protected_snapshot(manifest)
    _load_runtime(manifest)
    limits = manifest["limits"]
    prestart = {
        "schema": OUTPUT_SCHEMA,
        "status": "PRESTART_DISPATCH_CLAIMED",
        "authorization_id": authorization["authorization_id"],
        "component_manifest_sha256": component_sha,
        "production_identity_materialized": False,
        "dispatches_claimed": 1,
        "automatic_relaunch": False,
        "accounting": {"completed_batches": [], "uncommitted_attempt": None},
    }
    _atomic_replace(output, prestart, int(limits["durable_output_limit_bytes"]))
    wall_started = time.perf_counter()
    completed: list[dict[str, Any]] = []
    cumulative_cpu_ns = 0
    uncommitted: dict[str, Any] | None = None
    try:
        for index, stratum in enumerate(manifest["strata"]):
            if index >= limits["maximum_batches"] or len(completed) * 2 >= limits["maximum_fixture_units"]:
                raise MeasurementRefused("batch or fixture cap reached before plan completion")
            uncommitted = {"stratum_id": stratum["id"], "batch_index": index, "committed": False}
            payloads = worker_payloads_for_stratum(manifest, stratum, component_sha)
            batch = _run_batch(
                payloads, wall_started=wall_started,
                wall_limit=int(limits["maximum_foreground_wall_seconds"]),
                per_worker_rss_limit_bytes=int(limits["per_worker_rss_limit_bytes"]),
            )
            cap = _cap_accounting(batch, limits)
            cumulative_cpu_ns += cap["incremental_cpu_ns"]
            if cumulative_cpu_ns > int(limits["maximum_incremental_cpu_seconds"]) * 1_000_000_000:
                raise MeasurementRefused("incremental CPU ceiling exceeded")
            batch["resource_cap_accounting"] = cap
            completed.append(batch)
            uncommitted = None
        if len(completed) != 20 or sum(len(batch["fixtures"]) for batch in completed) != 40:
            raise MeasurementRefused("completed plan does not contain 20 batches/40 fixtures")
        after = _protected_snapshot(manifest)
        if before != after:
            raise MeasurementRefused("protected bytes or mtimes changed during measurement")
        result = {
            "schema": OUTPUT_SCHEMA,
            "status": "COMPLETED_UNCOMMITTED_TO_R01",
            "authorization_id": authorization["authorization_id"],
            "component_manifest_sha256": component_sha,
            "production_identity_materialized": False,
            "production_payload_accessed": False,
            "gpu": False,
            "dispatches_claimed": 1,
            "automatic_relaunch": False,
            "protected_before": before,
            "protected_after": after,
            "protected_unchanged": True,
            "limits": limits,
            "resource_totals": {
                "incremental_cpu_ns": cumulative_cpu_ns,
                "foreground_wall_ns": int((time.perf_counter() - wall_started) * 1_000_000_000),
                "logical_scratch_bytes": 0,
            },
            "forecast": _projection(
                completed, int(manifest["projection"]["production_two_worker_batches_per_stratum"]),
            ),
            "accounting": {"completed_batches": completed, "uncommitted_attempt": None},
            "scientific_interpretation": False,
            "r01_commit_or_frontier_effect": False,
        }
        _atomic_replace(output, result, int(limits["durable_output_limit_bytes"]))
        return result
    except BaseException as error:
        failure = {
            "schema": OUTPUT_SCHEMA,
            "status": "FAILED_CLOSED_UNCOMMITTED",
            "authorization_id": authorization["authorization_id"],
            "component_manifest_sha256": component_sha,
            "production_identity_materialized": False,
            "production_payload_accessed": False,
            "dispatches_claimed": 1,
            "automatic_relaunch": False,
            "failure_class": type(error).__name__,
            "accounting": {"completed_batches": completed, "uncommitted_attempt": uncommitted},
            "scientific_interpretation": False,
            "r01_commit_or_frontier_effect": False,
        }
        _atomic_replace(output, failure, int(limits["durable_output_limit_bytes"]))
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run_authorized_measurement(args.authorization_manifest, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
