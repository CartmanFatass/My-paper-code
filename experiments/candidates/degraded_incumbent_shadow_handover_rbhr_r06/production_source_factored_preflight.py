"""Result-blind fail-closed preflight for the incomplete source-factored chain."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import ctypes
import hashlib
import os
from pathlib import Path
import tempfile
import time
from typing import Iterator, Mapping, Sequence

from . import production_backend as _production_backend
from .production_backend import (
    ProductionBackendError, empty_step_rows, native_batch_from_rows, source_factored_test_fixture,
)
from .production_contract import TestAuthority
from .production_train_reset import build_train_reset_wave
from .production_source_factored_contract import (
    CLAIM_ROWS, MAX_FORK_TICKS, MAX_PREFIX_TICKS, TOTAL_TRAINING_TRANSITIONS,
    TOTAL_UPDATES, canonical_json_bytes, complete_claim_inventory,
    production_readiness_gap_inventory,
)


def _process_counters() -> Mapping[str, object]:
    row = {"pid": os.getpid(), "rss_bytes": 0, "io_read_bytes": 0, "io_write_bytes": 0}
    if os.name != "nt":
        return row
    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentProcess.argtypes = []; kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    process = kernel32.GetCurrentProcess()
    class Memory(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_uint32), ("page_faults", ctypes.c_uint32),
                    ("peak_working_set", ctypes.c_size_t), ("working_set", ctypes.c_size_t),
                    ("quota_peak_paged", ctypes.c_size_t), ("quota_paged", ctypes.c_size_t),
                    ("quota_peak_nonpaged", ctypes.c_size_t), ("quota_nonpaged", ctypes.c_size_t),
                    ("pagefile", ctypes.c_size_t), ("peak_pagefile", ctypes.c_size_t)]
    class Io(ctypes.Structure):
        _fields_ = [("read_ops", ctypes.c_uint64), ("write_ops", ctypes.c_uint64),
                    ("other_ops", ctypes.c_uint64), ("read_bytes", ctypes.c_uint64),
                    ("write_bytes", ctypes.c_uint64), ("other_bytes", ctypes.c_uint64)]
    memory = Memory(); memory.cb = ctypes.sizeof(memory); io = Io()
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    kernel32.GetProcessIoCounters.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.GetProcessIoCounters.restype = ctypes.c_int
    if psapi.GetProcessMemoryInfo(process, ctypes.byref(memory), memory.cb):
        row["rss_bytes"] = int(memory.working_set)
        row["peak_rss_bytes"] = int(memory.peak_working_set)
    if kernel32.GetProcessIoCounters(process, ctypes.byref(io)):
        row["io_read_bytes"] = int(io.read_bytes); row["io_write_bytes"] = int(io.write_bytes)
    return row


def _cache_file_inventory(root: Path) -> Mapping[str, Mapping[str, object]]:
    if not root.is_dir():
        return {}
    result: dict[str, Mapping[str, object]] = {}
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        payload = path.read_bytes()
        result[path.relative_to(root).as_posix()] = {
            "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return result


def _native_cache_root() -> Path:
    return Path(tempfile.gettempdir()) / "hmasd_dish_rbhr_r06_production"


def _load_cached_test_library() -> tuple[ctypes.CDLL | None, Mapping[str, object]]:
    """Read and load one source-matched cached TEST ABI without building it."""

    cache_root = _native_cache_root().resolve()
    source = (Path(__file__).with_name("native") / "rbhr_r06_production_backend.cpp").read_bytes()
    source_digest = hashlib.sha256(source).hexdigest()
    candidates: list[tuple[Path, Path]] = []
    if cache_root.is_dir():
        for directory in sorted(path for path in cache_root.iterdir() if path.is_dir()):
            if len(directory.name) != 64 or any(character not in "0123456789abcdef" for character in directory.name):
                continue
            snapshot = directory / "rbhr_r06_production_backend.source.cpp"
            artifact = directory / "rbhr_r06_production_backend.dll"
            if snapshot.is_file() and artifact.is_file() and snapshot.read_bytes() == source:
                candidates.append((directory, artifact))
    base = {
        "scope": "READ_ONLY_PREEXISTING_NATIVE_TEST_CACHE",
        "cache_root": str(cache_root),
        "cache_root_present": cache_root.is_dir(),
        "source_sha256": source_digest,
        "matching_candidate_count": len(candidates),
        "toolchain_discovery_called": False,
        "compiler_called": False,
        "cache_write_attempted": False,
        "process_tree_measurement_complete": True,
    }
    if len(candidates) != 1:
        status = "CACHE_ABSENT" if not candidates else "CACHE_AMBIGUOUS"
        return None, {**base, "status": status, "dynamic_test_probe_available": False}
    directory, artifact = candidates[0]
    before = _cache_file_inventory(directory)
    try:
        library = _production_backend._configure(ctypes.CDLL(str(artifact.resolve())))
    except (AttributeError, OSError, ProductionBackendError) as error:
        message = str(error).encode("ascii", "backslashreplace").decode("ascii")
        return None, {
            **base, "status": "CACHE_ABI_INVALID", "dynamic_test_probe_available": False,
            "build_key": directory.name, "artifact": str(artifact.resolve()), "error": message,
        }
    after = _cache_file_inventory(directory)
    if before != after:
        raise ProductionBackendError("read-only native cache changed during preflight load")
    return library, {
        **base, "status": "CACHE_ACCEPTED", "dynamic_test_probe_available": True,
        "build_key": directory.name, "artifact": str(artifact.resolve()),
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "artifact_bytes": artifact.stat().st_size,
        "abi_version": int(library.dish_rbhr_r06_prod_abi_version()),
        "cache_inventory_unchanged": True,
    }


@contextmanager
def _use_read_only_cached_library(library: ctypes.CDLL) -> Iterator[None]:
    """Keep legacy TEST helpers on the prevalidated DLL without cache lookup."""

    original = _production_backend.require_cpp_batched_production_backend
    _production_backend.require_cpp_batched_production_backend = lambda: library
    try:
        yield
    finally:
        _production_backend.require_cpp_batched_production_backend = original


def run_preflight(*, repository_root: Path, run_root: Path) -> Mapping[str, object]:
    repository = Path(repository_root).resolve(); receipt_root = Path(run_root).resolve()
    if not (repository / "AGENTS.md").is_file():
        raise ValueError("repository root differs")
    if receipt_root.exists():
        raise ValueError("TEST-only preflight receipt root must be absent")
    started_wall = time.perf_counter(); started_cpu = time.process_time(); before = _process_counters()
    library, native_cache = _load_cached_test_library()
    branches: tuple[str, ...] = (); metadata: Mapping[str, object] = {}
    ordinary_mode0_rejected = False; ordinary_mode0_rejection_code = None
    if library is not None:
        with _use_read_only_cached_library(library):
            authority = TestAuthority()
            admitted, rows = source_factored_test_fixture(2, authority)
            branches, _observations, metadata = admitted.clone_promotion_source_batches(rows)
            fixed_master = hashlib.sha256(b"TEST/DISH/PROMOTION-SOURCE-FORK/R01/PREFLIGHT/V1").digest()
            ordinary = native_batch_from_rows(build_train_reset_wave(
                fixed_master, block=0, arm="STRUCTURED", episode_wave=0,
            ))
            try:
                ordinary.clone_promotion_source(empty_step_rows(ordinary.width))
            except ProductionBackendError as error:
                if str(error) != "native promotion-source clone rejected batch (2)":
                    raise
                ordinary_mode0_rejected = True; ordinary_mode0_rejection_code = 2
    native_source = (Path(__file__).with_name("native") / "rbhr_r06_production_backend.cpp").read_text(encoding="utf-8")
    predicate_start = native_source.index("inline bool source_factored_combined_predicate")
    predicate_end = native_source.index("\n}\n", predicate_start) + 3
    predicate_source = native_source[predicate_start:predicate_end]
    static_mode0_refusal = (
        "(s.test_mode!=1&&s.test_mode!=2)" in predicate_source and
        "s.test_mode==0" in predicate_source
    )
    inventory = complete_claim_inventory()
    after = _process_counters()
    gaps = production_readiness_gap_inventory()
    preflight_gaps = ([] if library is not None else [
        "PREEXISTING_SOURCE_MATCHED_TEST_NATIVE_" + str(native_cache["status"]),
    ])
    receipt = {
        "schema": "DISH_PROMOTION_SOURCE_FORK_R01_PREFLIGHT_RECEIPT_V1",
        "passed": False, "status": "NOT_READY", "result_blind": True,
        "preflight_receipt_root": str(receipt_root), "scientific_run_root_created": False,
        "master_created": False, "scientific_master_created": False,
        "fixed_test_master_used": library is not None,
        "model_initialized": False, "checkpoint_created": False,
        "scientific_coordinate_executed": False, "fixed_test_reset_instantiated": library is not None,
        "side_effect_accounting": {
            "total_filesystem_effects_claimed_receipt_only": True,
            "requested_root_contains_only_canonical_receipt": True,
            "preexisting_native_cache_read_only": True,
            "native_toolchain_or_compile_child_processes": 0,
            "native_cache": native_cache,
        },
        "native_probe": {
            "scope": "ACCEPTED_TEST_ONLY_TRANSACTION_SENTINEL_NOT_HOST_CONFORMANCE",
            "dynamic_test_clone_executed": library is not None,
            "ordinary_mode0_clone_rejected": ordinary_mode0_rejected,
            "ordinary_mode0_clone_rejection_code": ordinary_mode0_rejection_code,
            "static_test_predicate_explicitly_rejects_mode0": static_mode0_refusal,
            "accepted_test_clone_branches": list(branches),
            "accepted_test_parent_immutable": metadata.get("parent_byte_immutable") if metadata else None,
            "production_source_factored_sidecar_abi_present": False,
            "production_post_arrival_observation_conformance": False,
        },
        "exact_ledgers": {
            "training_jobs": 24, "updates": TOTAL_UPDATES,
            "training_transitions": TOTAL_TRAINING_TRANSITIONS, "claim_rows": len(inventory),
            "max_prefix_ticks": MAX_PREFIX_TICKS, "max_three_branch_fork_ticks": MAX_FORK_TICKS,
            "inference_resamples": 99_999,
        },
        "measured_process": {
            "scope": "single_process_read_only_cache_and_sentinel_scope",
            "process_tree_measurement_complete": True,
            "native_toolchain_or_compile_child_processes": 0,
            "cpu_seconds": time.process_time() - started_cpu,
            "wall_seconds": time.perf_counter() - started_wall,
            "rss_bytes": int(after.get("rss_bytes", 0)),
            "peak_rss_bytes": int(after.get("peak_rss_bytes", after.get("rss_bytes", 0))),
            "io_read_bytes_delta": max(0, int(after.get("io_read_bytes", 0)) - int(before.get("io_read_bytes", 0))),
            "io_write_bytes_delta": max(0, int(after.get("io_write_bytes", 0)) - int(before.get("io_write_bytes", 0))),
            "workers_observed": 1, "cpu_threads_requested": 1, "device": "cpu", "gpu_count": 0,
            "scientific_scratch_bytes_created": 0, "scientific_durable_bytes_created": 0,
            "preflight_receipt_bytes_excluded_from_scientific_resources": True,
        },
        "preflight_gaps": preflight_gaps,
        "gap_inventory": gaps,
    }
    payload = canonical_json_bytes(receipt)
    receipt_root.mkdir(parents=True, exist_ok=False)
    receipt_path = receipt_root / "preflight-receipt.json"
    staged_path = receipt_root / f".preflight-receipt.{os.getpid()}.tmp"
    with staged_path.open("xb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    os.replace(staged_path, receipt_path)
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    args = parser.parse_args(argv)
    receipt = run_preflight(repository_root=args.repository_root, run_root=args.run_root)
    print(canonical_json_bytes(receipt).decode("ascii"), end="")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
