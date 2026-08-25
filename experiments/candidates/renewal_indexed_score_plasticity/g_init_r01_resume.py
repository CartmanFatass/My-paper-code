"""Blinded atomic continuation for the frozen RISP G-initialization R01 panel.

This module deliberately contains no coordinate construction.  The production
entry point supplies a fully validated certificate and calls the experiment's
production-only coordinate binder before any stochastic function is reachable.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import torch

import g_init_r01_experiment as experiment
import g_init_r01_coordinate_certificate as certificate_spec
import g_init_r01_native_backend as native_backend


FRONTIER_SCHEMA = "RISP-G-INIT-REACH-R01-RESUME-20260821-01"
DEFAULT_FRONTIER_NAME = "RISP_G_INIT_REACH_R01_RESUME"
DEFAULT_RESULT_ROOT_NAME = "RISP_G_INIT_REACH_R01_RESULTS"
DEFAULT_RESULT_NAME = "RISP_G_INIT_REACH_R01_COMPLETE.json"


class SliceExpired(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _peak_rss_bytes() -> int | None:
    try:
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                       ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                       ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                       ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                       ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters(); counters.cb = ctypes.sizeof(counters)
        psapi = ctypes.WinDLL("psapi", use_last_error=True); kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_current_process = kernel32.GetCurrentProcess; get_current_process.restype = wintypes.HANDLE
        info = psapi.GetProcessMemoryInfo; info.argtypes = (wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD)
        if not info(get_current_process(), ctypes.byref(counters), counters.cb):
            return None
        return int(counters.PeakWorkingSetSize)
    except Exception:
        return None


def _required(name: str) -> Any:
    try:
        return getattr(experiment, name)
    except AttributeError as error:
        raise RuntimeError(f"g_init_r01_experiment missing required R01 interface: {name}") from error


def unit_plan() -> tuple[tuple[str, int, str, int | None], ...]:
    seeds, arms, cells = _required("ALGORITHM_SEEDS"), _required("ARMS"), _required("CELL_FAMILIES")
    plan = tuple(("TRAIN", seed, arm, None) for seed in seeds for arm in arms) + tuple(
        ("EVAL", seed, cell, schedule) for seed in seeds for cell in cells for schedule in range(5))
    if len(plan) != 352 or len(arms) != 2 or len(cells) != 4:
        raise RuntimeError("R01 panel must be exactly 32 training plus 320 evaluation units")
    return plan


def _unit_id(item: tuple[str, int, str, int | None]) -> str:
    phase, seed, name, schedule = item
    safe = name.replace("/", "_").replace("|", "__")
    return f"{'train' if phase == 'TRAIN' else 'eval'}__seed_{seed:02d}__{safe}" + ("" if schedule is None else f"__schedule_{schedule}")


@dataclass
class Frontier:
    root: Path; result_root: Path; certificate: Path; slice_wall_seconds: float; rss_limit_bytes: int; started: float
    worker_count: int = certificate_spec.WORKER_COUNT
    process_group_rss_limit_bytes: int = certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES

    @property
    def result(self) -> Path: return self.result_root / DEFAULT_RESULT_NAME
    @property
    def receipts(self) -> Path: return self.root / "slice_receipts"
    def elapsed(self) -> float: return time.monotonic() - self.started
    def paths(self, item: tuple[str, int, str, int | None]) -> tuple[Path, Path]:
        directory = self.root / ("training_units" if item[0] == "TRAIN" else "evaluation_units")
        packet = directory / f"{_unit_id(item)}.json"
        return packet, directory / f"{_unit_id(item)}.commit.json"
    def assert_resources(self) -> None:
        peak = _peak_rss_bytes()
        if peak is not None and peak > self.process_group_rss_limit_bytes:
            raise RuntimeError(f"parent peak RSS {peak} exceeds process-group limit {self.process_group_rss_limit_bytes}")
    def committed(self, item: tuple[str, int, str, int | None]) -> bool:
        packet_path, commit_path = self.paths(item)
        if not packet_path.exists() and not commit_path.exists(): return False
        if not packet_path.exists() or not commit_path.exists(): raise RuntimeError(f"torn atomic unit {packet_path}")
        packet, commit = _load_json(packet_path), _load_json(commit_path)
        phase, seed, name, schedule = item
        expected_schema = _required("TRAINING_SCHEMA") if phase == "TRAIN" else _required("EVALUATION_SCHEMA")
        forbidden_test_fields = {"namespace", "fixture_root", "test_fixture_revision"}
        if (commit.get("sha256") != _sha256(packet_path) or commit.get("schema") != FRONTIER_SCHEMA
                or commit.get("science_revision") != _required("SCIENCE_REVISION")
                or commit.get("binding_class") != "PRODUCTION" or commit.get("test_fixture") is not False
                or packet.get("schema") != expected_schema or packet.get("science_revision") != _required("SCIENCE_REVISION")
                or packet.get("registered") is not True or packet.get("algorithm_seed") != seed
                or packet.get("binding_class") != "PRODUCTION" or packet.get("test_fixture") is not False
                or forbidden_test_fields.intersection(packet) or forbidden_test_fields.intersection(commit)):
            raise RuntimeError(f"invalid atomic unit {packet_path}")
        if phase == "TRAIN" and packet.get("arm") != name: raise RuntimeError(f"training identity mismatch {packet_path}")
        if phase == "EVAL" and (packet.get("cell") != name or packet.get("schedule_id") != schedule): raise RuntimeError(f"evaluation identity mismatch {packet_path}")
        return True


def _certificate_binding(certificate: Path, frontier: Path | None = None, result_root: Path | None = None) -> dict[str, Any]:
    frontier = certificate_spec.PRODUCTION_FRONTIER if frontier is None else frontier
    result_root = certificate_spec.PRODUCTION_RESULT_ROOT if result_root is None else result_root
    certificate_spec.assert_production_paths(certificate, frontier, result_root)
    data = _load_json(certificate)
    required = {
        "certificate_schema": certificate_spec.CERTIFICATE_SCHEMA,
        "science_revision": _required("SCIENCE_REVISION"),
        "coordinate_schema": _required("COORDINATE_SCHEMA"),
        "coordinate_binding_activity_started": True,
        "technical_acceptance": True,
        "model_or_optimizer_materialized": False,
        "training_or_evaluation_executed": False,
        "partial_scientific_values_exposed": False,
        "immutable_inputs": certificate_spec.immutable_inputs(),
        "source_manifest": certificate_spec.source_manifest(),
        "registered_panel": certificate_spec.registered_panel(),
    }
    if any(data.get(key) != value for key, value in required.items()): raise RuntimeError("coordinate certificate binding mismatch")
    root = data.get("coordinate_root")
    if not certificate_spec._valid_root(root) or root in certificate_spec.FORBIDDEN_ROOTS: raise RuntimeError("invalid or excluded coordinate root")
    expected_paths = {"certificate": str(certificate_spec.PRODUCTION_CERTIFICATE), "frontier": str(certificate_spec.PRODUCTION_FRONTIER), "result_root": str(certificate_spec.PRODUCTION_RESULT_ROOT), "result": str(certificate_spec.PRODUCTION_RESULT_ROOT / certificate_spec.RESULT_NAME)}
    expected_production = {
        "interpreter": certificate_spec.INTERPRETER,
        "working_directory": str(certificate_spec.ROOT),
        "command": certificate_spec.production_command(),
        **certificate_spec.LEASE_BINDING_INTERFACE["resources"],
    }
    if data.get("paths") != expected_paths or data.get("production") != expected_production:
        raise RuntimeError("production command or path binding mismatch")
    backend_record: dict[str, Any] | None = None
    for key in ("backend_binding", "lease_binding"):
        binding = data.get(key)
        if not isinstance(binding, dict) or not isinstance(binding.get("path"), str) or not isinstance(binding.get("sha256"), str): raise RuntimeError(f"missing {key} interface")
        bound_path = Path(binding["path"])
        if key == "backend_binding": backend_record = certificate_spec.validate_backend_binding(bound_path)
        else: certificate_spec.validate_lease_binding(bound_path)
        if certificate_spec._sha(bound_path) != binding["sha256"]: raise RuntimeError(f"{key} hash mismatch")
    # This runs before the sole production coordinate binder in the entrypoint.
    # Local native build success cannot substitute for shared-registry acceptance.
    observed_preflight = native_backend.production_preflight(batch_width=32)
    if backend_record is None or _shared_preflight_semantics(observed_preflight.get("shared")) != _shared_preflight_semantics(backend_record.get("shared_functional_acceptance")):
        raise RuntimeError("live shared native preflight does not match accepted backend binding")
    if _local_native_semantics(observed_preflight.get("local")) != _local_native_semantics(backend_record.get("native_artifact")):
        raise RuntimeError("live local native identity does not match accepted backend binding")
    return data


def _local_native_semantics(value: object) -> dict[str, Any]:
    if not isinstance(value, dict): return {}
    runtime = value.get("runtime_abi") if isinstance(value.get("runtime_abi"), dict) else {}
    return {
        "schema": value.get("schema"), "artifact_sha256": value.get("artifact_sha256"),
        "build_key": value.get("build_key"), "source_sha256": value.get("source_sha256"),
        "abi_version": value.get("abi_version"), "struct_sizes": runtime.get("struct_sizes"),
        "batch_widths": value.get("batch_widths"), "full_reset_step_cpp": value.get("full_reset_step_cpp"),
        "python_environment_state": value.get("python_environment_state"),
        "python_reset_step_transition": value.get("python_reset_step_transition"),
        "python_fallback": value.get("python_fallback"),
    }


def _shared_preflight_semantics(value: object) -> dict[str, Any]:
    if not isinstance(value, dict): return {}
    native = value.get("native") if isinstance(value.get("native"), dict) else {}
    return {
        "schema": value.get("schema"), "component": value.get("component"),
        "backend": value.get("backend"), "batch_width": value.get("batch_width"),
        "native_boundary": value.get("native_boundary"),
        "full_reset_step_cpp": value.get("full_reset_step_cpp"),
        "python_fallback": value.get("python_fallback"),
        "native_binding_kind": native.get("binding_kind"),
        "native_artifact_sha256": native.get("artifact_sha256"),
    }


def _initialize(frontier: Frontier) -> dict[str, Any]:
    certificate = _certificate_binding(frontier.certificate, frontier.root, frontier.result_root)
    for path in (frontier.root, frontier.result_root, frontier.root / "training_units", frontier.root / "evaluation_units", frontier.receipts): path.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": FRONTIER_SCHEMA, "science_revision": _required("SCIENCE_REVISION"), "coordinate_schema": _required("COORDINATE_SCHEMA"), "coordinate_root": certificate["coordinate_root"], "certificate": str(frontier.certificate.resolve()), "certificate_sha256": _sha256(frontier.certificate), "registered_atomic_units": 352, "production_workers": frontier.worker_count, "cpu_cores": certificate_spec.CPU_CORES, "gpu": False, "partial_scientific_values_exposed": False, "result": str(frontier.result.resolve())}
    path = frontier.root / "manifest.json"
    if path.exists():
        if _load_json(path) != manifest: raise RuntimeError("frontier manifest mismatch")
    else: _required("atomic_write_json")(path, manifest)
    return certificate


def _write_unit(frontier: Frontier, item: tuple[str, int, str, int | None], packet: dict[str, Any]) -> None:
    packet_path, commit_path = frontier.paths(item); packet_path.parent.mkdir(parents=True, exist_ok=True)
    _required("atomic_write_json")(packet_path, packet)
    _required("atomic_write_json")(commit_path, {"schema": FRONTIER_SCHEMA, "science_revision": _required("SCIENCE_REVISION"), "binding_class": "PRODUCTION", "test_fixture": False, "unit": packet_path.stem, "sha256": _sha256(packet_path)})


def _states(frontier: Frontier, seed: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for arm in _required("ARMS"):
        item = ("TRAIN", seed, arm, None)
        if not frontier.committed(item): raise RuntimeError(f"evaluation reached before training {seed} {arm}")
        # Preserve the production schema/revision/binding/seed provenance
        # envelope; the experiment consumer validates it before final_state.
        result[arm] = _load_json(frontier.paths(item)[0])
    return result


def _next_receipt(frontier: Frontier) -> Path:
    index = 0
    while (frontier.receipts / f"slice_{index:04d}.json").exists(): index += 1
    return frontier.receipts / f"slice_{index:04d}.json"


def _prior_resource_accounting(frontier: Frontier) -> dict[str, Any]:
    zero = {
        "committed_batches": 0, "worker_cpu_seconds": 0.0,
        "worker_wall_seconds": 0.0, "parallel_batch_wall_seconds": 0.0,
        "parent_cpu_seconds": 0.0, "slice_elapsed_seconds": 0.0,
        "worker_peak_rss_max_bytes": 0, "process_group_rss_max_bytes": 0,
    }
    if not frontier.receipts.is_dir(): return zero
    paths = sorted(frontier.receipts.glob("slice_*.json"))
    if not paths: return zero
    latest = _load_json(paths[-1]).get("cumulative_resource_accounting")
    return {**zero, **latest} if isinstance(latest, dict) else zero


def _batch_resource_accounting(results: list[dict[str, Any]]) -> dict[str, Any]:
    peaks: dict[int, int] = {}
    for result in results:
        if result.get("peak_rss_bytes") is not None:
            pid, peak = int(result["pid"]), int(result["peak_rss_bytes"])
            peaks[pid] = max(peaks.get(pid, 0), peak)
    parent_peak = _peak_rss_bytes() or 0
    return {
        "worker_cpu_seconds": sum(float(result.get("worker_cpu_seconds", 0.0)) for result in results),
        "worker_wall_seconds": sum(float(result.get("worker_wall_seconds", 0.0)) for result in results),
        "parallel_batch_wall_seconds": max((float(result.get("worker_wall_seconds", 0.0)) for result in results), default=0.0),
        "worker_peak_rss_max_bytes": max(peaks.values(), default=0),
        "process_group_rss_max_bytes": sum(peaks.values()) + parent_peak,
    }


def _aggregate_ledger(training: list[dict[str, Any]], evaluation: list[dict[str, Any]]) -> dict[str, int]:
    """Aggregate non-result sampler counters while counting paired init once."""
    totals: dict[str, int] = {}
    arms = tuple(_required("ARMS"))
    for seed in _required("ALGORITHM_SEEDS"):
        representative = next(unit for unit in training if unit["algorithm_seed"] == seed and unit["arm"] == arms[0])
        for kind, count in representative["sampler_audit"]["calls"].items():
            if kind == "INIT_MODEL": totals[kind] = totals.get(kind, 0) + int(count)
    for packet in (*training, *evaluation):
        for kind, count in packet["sampler_audit"]["calls"].items():
            if kind != "INIT_MODEL": totals[kind] = totals.get(kind, 0) + int(count)
    return dict(sorted(totals.items()))


@contextmanager
def _exclusive_frontier(root: Path):
    import msvcrt
    root.mkdir(parents=True, exist_ok=True); lock = root / "PRODUCTION.lock"
    with lock.open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0: handle.write(b"\0"); handle.flush()
        handle.seek(0)
        try: msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error: raise RuntimeError(f"frontier already active: {root}") from error
        try: yield
        finally: handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _finalize(frontier: Frontier) -> None:
    training, evaluation = [], []
    for item in unit_plan():
        if not frontier.committed(item): raise RuntimeError("finalization reached incomplete frontier")
        (training if item[0] == "TRAIN" else evaluation).append(_load_json(frontier.paths(item)[0]))
    analysis = _required("analyze_complete")(training, evaluation)
    if analysis.get("schema") != _required("RESULT_SCHEMA") or analysis.get("complete_panel") is not True: raise RuntimeError("analyzer did not produce exact complete panel")
    ledger = _aggregate_ledger(training, evaluation)
    if ledger != _required("expected_complete_ledger")(): raise RuntimeError("complete ledger mismatch")
    retained = {**analysis, "structural_certificate": _required("structural_certificate")(), "ledger": ledger, "coordinate_schema": _required("COORDINATE_SCHEMA"), "coordinate_root": _certificate_binding(frontier.certificate, frontier.root, frontier.result_root)["coordinate_root"], "training_unit_paths": [str(frontier.paths(item)[0].resolve()) for item in unit_plan() if item[0] == "TRAIN"], "evaluation_unit_paths": [str(frontier.paths(item)[0].resolve()) for item in unit_plan() if item[0] == "EVAL"], "peak_rss_bytes": _peak_rss_bytes(), "partial_scientific_values_exposed": False}
    _required("atomic_write_json")(frontier.result, retained)
    _required("atomic_write_json")(frontier.root / "FINAL_COMPLETE.commit.json", {"schema": FRONTIER_SCHEMA, "science_revision": _required("SCIENCE_REVISION"), "result": str(frontier.result.resolve()), "result_sha256": _sha256(frontier.result), "complete_panel": True})


def _validate_retained_complete(frontier: Frontier) -> None:
    certificate = _certificate_binding(frontier.certificate, frontier.root, frontier.result_root)
    result = _load_json(frontier.result)
    expected = {
        "schema": _required("RESULT_SCHEMA"), "science_revision": _required("SCIENCE_REVISION"),
        "coordinate_schema": _required("COORDINATE_SCHEMA"), "coordinate_root": certificate["coordinate_root"],
        "complete_panel": True,
    }
    if any(result.get(key) != value for key, value in expected.items()): raise RuntimeError("retained result binding mismatch")
    final_path = frontier.root / "FINAL_COMPLETE.commit.json"
    final = _load_json(final_path) if final_path.is_file() else None
    if final != {"schema": FRONTIER_SCHEMA, "science_revision": _required("SCIENCE_REVISION"), "result": str(frontier.result.resolve()), "result_sha256": _sha256(frontier.result), "complete_panel": True}:
        raise RuntimeError("FINAL_COMPLETE hash binding mismatch")


def _run_one(frontier: Frontier, item: tuple[str, int, str, int | None], guard: Callable[[], None]) -> None:
    phase, seed, name, schedule = item
    packet = _required("run_training_unit")(seed, name, progress_guard=guard) if phase == "TRAIN" else _required("run_evaluation_unit")(seed, name, int(schedule), _states(frontier, seed), progress_guard=guard)
    frontier.assert_resources(); _write_unit(frontier, item, packet)


def _semantic_packet_sha256(packet: dict[str, Any]) -> str:
    """Hash deterministic packet semantics, excluding wall-clock telemetry."""
    semantic = {key: value for key, value in packet.items() if key != "elapsed_seconds"}
    encoded = json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _isolated_unit_worker(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute one independently atomic unit without frontier write authority."""
    binding = payload.get("binding_class")
    root = payload.get("root")
    item = payload.get("item")
    if binding not in ("TEST_ONLY", "PRODUCTION") or not isinstance(root, str):
        raise RuntimeError("isolated worker binding is invalid")
    if any(key in payload for key in ("frontier", "frontier_root", "result_root", "packet_path", "commit_path")):
        raise RuntimeError("worker payload must not expose frontier paths")
    if binding == "PRODUCTION":
        if payload.get("validated_production_binding") is not True:
            raise RuntimeError("production worker requires parent-validated binding")
        native_backend.production_preflight(batch_width=32)
        if experiment.coordinate_root() is None:
            experiment.configure_production_coordinate_root(root, validated_production_binding=True)
        elif experiment.coordinate_root() != root or experiment.fixture_root() is not None:
            raise RuntimeError("worker production coordinate binding mismatch")
    else:
        if experiment.fixture_root() is None:
            experiment.configure_test_fixture_root(root)
        elif experiment.fixture_root() != root or experiment.coordinate_root() is not None:
            raise RuntimeError("worker TEST fixture binding mismatch")
    if not isinstance(item, (tuple, list)) or len(item) != 4:
        raise RuntimeError("invalid isolated unit identity")
    phase, seed, name, schedule = item
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    per_worker_limit = int(payload.get("per_worker_rss_limit_bytes", certificate_spec.PER_WORKER_RSS_LIMIT_BYTES))
    deadline = payload.get("deadline_monotonic")
    def guard() -> None:
        peak = _peak_rss_bytes()
        if peak is not None and peak > per_worker_limit:
            raise RuntimeError(f"worker peak RSS {peak} exceeds limit {per_worker_limit}")
        if deadline is not None and time.monotonic() >= float(deadline):
            raise SliceExpired("slice reserve reached before atomic batch completion")
    guard()
    worker_cpu_started = time.process_time()
    worker_wall_started = time.perf_counter()
    if phase == "TRAIN":
        if binding == "PRODUCTION":
            packet = experiment.run_training_unit(int(seed), str(name), progress_guard=guard)
        else:
            packet = experiment.run_training_unit(
                int(seed), str(name), updates=int(payload.get("updates", 1)),
                episodes=int(payload.get("episodes", 2)), progress_guard=guard,
            )
    elif phase == "EVAL":
        if binding == "PRODUCTION":
            packet = experiment.run_evaluation_unit(
                int(seed), str(name), int(schedule), payload.get("checkpoint_states", {}),
                progress_guard=guard,
            )
        else:
            packet = experiment.run_evaluation_unit(
                int(seed), str(name), int(schedule), payload.get("checkpoint_states", {}),
                episodes=int(payload.get("episodes", 1)), progress_guard=guard,
            )
    else:
        raise RuntimeError("invalid isolated unit phase")
    guard()
    expected_registered = binding == "PRODUCTION"
    if packet.get("binding_class") != binding or packet.get("registered") is not expected_registered:
        raise RuntimeError("isolated worker emitted packet for the wrong binding")
    return {
        "item": tuple(item), "packet": packet,
        "semantic_sha256": _semantic_packet_sha256(packet),
        "pid": os.getpid(), "peak_rss_bytes": _peak_rss_bytes(),
        "worker_cpu_seconds": time.process_time() - worker_cpu_started,
        "worker_wall_seconds": time.perf_counter() - worker_wall_started,
    }


def _validate_worker_result(payload: dict[str, Any], result: dict[str, Any]) -> None:
    expected_item = tuple(payload["item"])
    if tuple(result.get("item", ())) != expected_item:
        raise RuntimeError("worker returned wrong unit identity")
    packet = result.get("packet")
    phase, seed, name, schedule = expected_item
    binding = payload["binding_class"]
    if binding == "PRODUCTION":
        expected_schema = experiment.TRAINING_SCHEMA if phase == "TRAIN" else experiment.EVALUATION_SCHEMA
        expected_revision = experiment.SCIENCE_REVISION
        registered, test_fixture = True, False
    else:
        expected_schema = experiment.TEST_TRAINING_SCHEMA if phase == "TRAIN" else experiment.TEST_EVALUATION_SCHEMA
        expected_revision = experiment.TEST_FIXTURE_REVISION
        registered, test_fixture = False, True
    identity_ok = (
        isinstance(packet, dict)
        and packet.get("schema") == expected_schema
        and packet.get("science_revision") == expected_revision
        and packet.get("binding_class") == binding
        and packet.get("test_fixture") is test_fixture
        and packet.get("registered") is registered
        and packet.get("algorithm_seed") == seed
        and result.get("semantic_sha256") == _semantic_packet_sha256(packet)
    )
    if phase == "TRAIN":
        identity_ok = identity_ok and packet.get("arm") == name
    else:
        identity_ok = identity_ok and packet.get("cell") == name and packet.get("schedule_id") == schedule
    if not identity_ok:
        raise RuntimeError("parent rejected worker packet hash or identity")


def execute_units_ordered(
    payloads: list[dict[str, Any]], *, worker_count: int,
    install: Callable[[tuple[str, int, str, int | None], dict[str, Any]], None] | None = None,
    per_worker_rss_limit_bytes: int = certificate_spec.PER_WORKER_RSS_LIMIT_BYTES,
    process_group_rss_limit_bytes: int = certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES,
    max_worker_count: int = certificate_spec.WORKER_COUNT,
) -> list[dict[str, Any]]:
    """Bounded process plan; parent installs only after all succeed.

    Workers never receive frontier paths.  Any worker exception cancels pending
    futures and installs nothing, while successful packets are installed in the
    exact input plan order only after the whole bounded batch is available.
    """
    if isinstance(worker_count, bool) or not isinstance(worker_count, int) or not 1 <= worker_count <= max_worker_count:
        raise ValueError(f"worker_count must be in [1, {max_worker_count}]")
    bindings = {payload.get("binding_class") for payload in payloads}
    if not payloads or len(bindings) != 1 or not bindings.issubset({"TEST_ONLY", "PRODUCTION"}):
        raise ValueError("one nonempty homogeneous binding batch is required")
    if any("per_worker_rss_limit_bytes" not in payload for payload in payloads):
        payloads = [{**payload, "per_worker_rss_limit_bytes": per_worker_rss_limit_bytes} for payload in payloads]
    context = multiprocessing.get_context("spawn")
    ordered: list[dict[str, Any] | None] = [None] * len(payloads)
    with ProcessPoolExecutor(max_workers=worker_count, mp_context=context) as executor:
        futures = {executor.submit(_isolated_unit_worker, payload): index for index, payload in enumerate(payloads)}
        try:
            for future in as_completed(futures):
                index = futures[future]
                result = future.result()
                _validate_worker_result(payloads[index], result)
                ordered[index] = result
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    if any(result is None for result in ordered):
        raise RuntimeError("worker batch ended with a missing atomic unit")
    complete = [result for result in ordered if result is not None]
    peak_by_pid: dict[int, int] = {}
    for result in complete:
        if result.get("peak_rss_bytes") is not None:
            pid, peak = int(result["pid"]), int(result["peak_rss_bytes"])
            peak_by_pid[pid] = max(peak_by_pid.get(pid, 0), peak)
    worker_peaks = list(peak_by_pid.values())
    if any(peak > per_worker_rss_limit_bytes for peak in worker_peaks):
        raise RuntimeError("worker batch exceeded per-worker RSS ceiling")
    parent_peak = _peak_rss_bytes() or 0
    if sum(worker_peaks) + parent_peak > process_group_rss_limit_bytes:
        raise RuntimeError("worker batch exceeded process-group RSS ceiling")
    if install is not None:
        for result in complete:
            install(tuple(result["item"]), result["packet"])
    return complete


def execute_test_units_ordered(
    payloads: list[dict[str, Any]], *, worker_count: int,
    install: Callable[[tuple[str, int, str, int | None], dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    return execute_units_ordered(
        payloads, worker_count=worker_count, install=install,
        process_group_rss_limit_bytes=3 * 1024**3, max_worker_count=4,
    )


def _production_worker_payload(
    frontier: Frontier, certificate: dict[str, Any],
    item: tuple[str, int, str, int | None], deadline_monotonic: float,
) -> dict[str, Any]:
    phase, seed, _name, _schedule = item
    payload: dict[str, Any] = {
        "binding_class": "PRODUCTION",
        "validated_production_binding": True,
        "root": certificate["coordinate_root"],
        "item": item,
        "deadline_monotonic": deadline_monotonic,
        "per_worker_rss_limit_bytes": frontier.rss_limit_bytes,
    }
    if phase == "EVAL":
        # Evaluation receives immutable packet values only after both training
        # coordinates for its seed have parent-owned commits.
        payload["checkpoint_states"] = _states(frontier, seed)
    if any(key in payload for key in ("frontier", "frontier_root", "result_root", "packet_path", "commit_path")):
        raise RuntimeError("production worker payload exposed a frontier path")
    return payload


def _next_atomic_batch(
    frontier: Frontier, plan: tuple[tuple[str, int, str, int | None], ...],
) -> tuple[tuple[str, int, str, int | None], ...]:
    first_index = next((index for index, item in enumerate(plan) if not frontier.committed(item)), None)
    if first_index is None:
        return ()
    phase = plan[first_index][0]
    batch: list[tuple[str, int, str, int | None]] = []
    for item in plan[first_index:]:
        if item[0] != phase or len(batch) == frontier.worker_count:
            break
        if not frontier.committed(item):
            batch.append(item)
    return tuple(batch)


def _run_slice_locked(frontier: Frontier) -> dict[str, Any]:
    parent_cpu_started = time.process_time()
    if frontier.slice_wall_seconds <= 0: raise ValueError("slice wall seconds must be positive")
    if frontier.worker_count != certificate_spec.WORKER_COUNT:
        raise RuntimeError("production worker count does not match the validated ceiling")
    torch.set_num_threads(1)
    try: torch.set_num_interop_threads(1)
    except RuntimeError: pass
    certificate = _initialize(frontier)
    if not _required("structural_certificate")().get("passed"): raise RuntimeError("structural certificate failed")
    plan = unit_plan(); before = sum(frontier.committed(item) for item in plan)
    prior_resources = _prior_resource_accounting(frontier)
    slice_resources: dict[str, Any] = {
        "committed_batches": 0, "worker_cpu_seconds": 0.0,
        "worker_wall_seconds": 0.0, "parallel_batch_wall_seconds": 0.0,
        "worker_peak_rss_max_bytes": 0, "process_group_rss_max_bytes": 0,
    }
    resource_ceiling_fence_reached = False
    if frontier.result.exists():
        _validate_retained_complete(frontier)
        status = "COMPLETE"
    else:
        while True:
            batch = _next_atomic_batch(frontier, plan)
            if not batch:
                break
            observed_cpu_seconds = (
                float(prior_resources["worker_cpu_seconds"]) + float(prior_resources["parent_cpu_seconds"])
                + float(slice_resources["worker_cpu_seconds"])
                + (time.process_time() - parent_cpu_started)
            )
            observed_wall_seconds = float(prior_resources["slice_elapsed_seconds"]) + frontier.elapsed()
            if (observed_cpu_seconds >= certificate_spec.COMPLETE_CPU_HOURS_UPPER * 3600
                    or observed_wall_seconds >= certificate_spec.COMPLETE_WALL_SECONDS_UPPER):
                resource_ceiling_fence_reached = True
                break
            frontier.assert_resources()
            if frontier.elapsed() + 300 >= frontier.slice_wall_seconds:
                break
            deadline = frontier.started + frontier.slice_wall_seconds - 300
            payloads = [_production_worker_payload(frontier, certificate, item, deadline) for item in batch]
            try:
                results = execute_units_ordered(
                    payloads, worker_count=frontier.worker_count,
                    per_worker_rss_limit_bytes=frontier.rss_limit_bytes,
                    process_group_rss_limit_bytes=frontier.process_group_rss_limit_bytes,
                    install=lambda item, packet: _write_unit(frontier, item, packet),
                )
                observed = _batch_resource_accounting(results)
                slice_resources["committed_batches"] += 1
                for key in ("worker_cpu_seconds", "worker_wall_seconds", "parallel_batch_wall_seconds"):
                    slice_resources[key] += observed[key]
                for key in ("worker_peak_rss_max_bytes", "process_group_rss_max_bytes"):
                    slice_resources[key] = max(slice_resources[key], observed[key])
            except SliceExpired:
                # No packet was installed: the same coordinates remain next in
                # plan order for a later authorized slice.
                break
        if sum(frontier.committed(item) for item in plan) == 352: _finalize(frontier); status = "COMPLETE"
        else: status = "PARTIAL"
    after = sum(frontier.committed(item) for item in plan)
    slice_elapsed = frontier.elapsed()
    slice_resources["parent_cpu_seconds"] = time.process_time() - parent_cpu_started
    slice_resources["slice_elapsed_seconds"] = slice_elapsed
    cumulative = {
        "committed_batches": int(prior_resources["committed_batches"]) + int(slice_resources["committed_batches"]),
        **{
            key: float(prior_resources[key]) + float(slice_resources[key])
            for key in ("worker_cpu_seconds", "worker_wall_seconds", "parallel_batch_wall_seconds", "parent_cpu_seconds", "slice_elapsed_seconds")
        },
        "worker_peak_rss_max_bytes": max(int(prior_resources["worker_peak_rss_max_bytes"]), int(slice_resources["worker_peak_rss_max_bytes"])),
        "process_group_rss_max_bytes": max(int(prior_resources["process_group_rss_max_bytes"]), int(slice_resources["process_group_rss_max_bytes"])),
    }
    cumulative["total_cpu_hours"] = (cumulative["worker_cpu_seconds"] + cumulative["parent_cpu_seconds"]) / 3600.0
    cumulative["cpu_ceiling_hours"] = certificate_spec.COMPLETE_CPU_HOURS_UPPER
    cumulative["wall_ceiling_seconds"] = certificate_spec.COMPLETE_WALL_SECONDS_UPPER
    cumulative["resource_observation_only_no_panel_selection"] = True
    receipt = {"schema": FRONTIER_SCHEMA, "science_revision": _required("SCIENCE_REVISION"), "status": status, "committed_atomic_units_before": before, "committed_atomic_units_after": after, "registered_atomic_units": 352, "production_workers": frontier.worker_count, "elapsed_seconds": slice_elapsed, "peak_rss_bytes": _peak_rss_bytes(), "slice_resource_accounting": slice_resources, "cumulative_resource_accounting": cumulative, "resource_ceiling_fence_reached": resource_ceiling_fence_reached, "resource_ceiling_fence_has_no_scientific_or_panel_selection_meaning": True, "blinded_frontier_unchanged_on_uncommitted_batch": True, "partial_scientific_values_exposed": False}
    path = _next_receipt(frontier); _required("atomic_write_json")(path, receipt)
    return {"schema": FRONTIER_SCHEMA, "status": status, "receipt": str(path.resolve()), "result": str(frontier.result.resolve()), "partial_scientific_values_exposed": False}


def run_slice(
    frontier_root: Path, result_root: Path, certificate: Path, slice_wall_seconds: float,
    per_worker_rss_limit_bytes: int, process_group_rss_limit_bytes: int,
    worker_count: int,
) -> dict[str, Any]:
    if (slice_wall_seconds != certificate_spec.SLICE_WALL_SECONDS
            or per_worker_rss_limit_bytes != certificate_spec.PER_WORKER_RSS_LIMIT_BYTES
            or process_group_rss_limit_bytes != certificate_spec.PROCESS_GROUP_RSS_LIMIT_BYTES
            or worker_count != certificate_spec.WORKER_COUNT):
        raise RuntimeError("runtime resources do not match the validated lease ceiling")
    with _exclusive_frontier(frontier_root.resolve()):
        return _run_slice_locked(Frontier(
            frontier_root.resolve(), result_root.resolve(), certificate.resolve(),
            slice_wall_seconds, per_worker_rss_limit_bytes, time.monotonic(),
            worker_count, process_group_rss_limit_bytes,
        ))


def default_paths(module_path: Path) -> tuple[Path, Path]:
    parent = module_path.parent
    return parent / DEFAULT_FRONTIER_NAME, parent / DEFAULT_RESULT_ROOT_NAME
