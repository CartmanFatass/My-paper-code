"""Result-blind live process-group RSS canary for RCLE TBCFV r04.

This harness launches the actual closed one-block production worker path with
the already accepted synthetic protocol-canary context.  While all four
production children are executing, the parent samples current working-set RSS
for itself and every child in one polling snapshot.  It does not open the
scientific frontier, materialize coordinates, or inspect result values.
"""

from __future__ import annotations

import argparse
from concurrent.futures import Future, ProcessPoolExecutor
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import json
import hashlib
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from experiments.candidates.roster_consistent_latent_exploration_tbcfv import (  # noqa: E402
    empirical_runner as runner,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.empirical_contract import (  # noqa: E402
    canonical_json_bytes,
    canonical_source_identity,
    production_source_paths,
)
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.process_workers import (  # noqa: E402
    PROCESS_GROUP_RSS_CEILING,
    make_process_resource_object,
    make_spawn_payload,
    make_worker_authorization,
    run_production_block_worker,
    write_spawn_payload,
)
from tools.benchmarks import benchmark_rcle_tbcfv_r04_runner_chain as chain  # noqa: E402


SCHEMA = "RCLE_TBCFV_R04_LIVE_PRODUCTION_GROUP_RSS_CANARY_V1"
WORKERS = 4


if os.name == "nt":
    class _ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("page_fault_count", wintypes.DWORD),
            ("peak_working_set_size", ctypes.c_size_t),
            ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
            ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
        ]


def _current_rss_bytes(pid: int) -> int | None:
    if os.name == "nt":
        process_query_limited_information = 0x1000
        process_vm_read = 0x0010
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(_ProcessMemoryCounters),
            wintypes.DWORD,
        ]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        handle = kernel.OpenProcess(
            process_query_limited_information | process_vm_read, False, pid
        )
        if not handle:
            return None
        try:
            memory = _ProcessMemoryCounters()
            memory.cb = ctypes.sizeof(memory)
            if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                return None
            value = int(memory.working_set_size)
            return value if value > 0 else None
        finally:
            kernel.CloseHandle(handle)
    try:
        resident_pages = int((Path("/proc") / str(pid) / "statm").read_text().split()[1])
        return resident_pages * int(os.sysconf("SC_PAGE_SIZE"))
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None


def _sample_live_group(
    futures: Iterable[Future[dict[str, object]]], child_pids: tuple[int, ...]
) -> dict[str, object]:
    pending = tuple(futures)
    parent_pid = os.getpid()
    peak: dict[str, object] | None = None
    sample_count = 0
    all_children_executing_sample_count = 0
    deadline = time.monotonic() + 120.0
    while time.monotonic() < deadline:
        unfinished = sum(not future.done() for future in pending)
        parent_rss = _current_rss_bytes(parent_pid)
        child_rows = [
            {"pid": pid, "rss_bytes": rss}
            for pid in child_pids
            if (rss := _current_rss_bytes(pid)) is not None
        ]
        if parent_rss is not None and len(child_rows) == WORKERS:
            sample_count += 1
            if unfinished == WORKERS:
                all_children_executing_sample_count += 1
                total = parent_rss + sum(int(row["rss_bytes"]) for row in child_rows)
                if peak is None or total > int(peak["process_group_rss_bytes"]):
                    peak = {
                        "sampled_at_monotonic_ns": time.monotonic_ns(),
                        "parent_pid": parent_pid,
                        "parent_rss_bytes": parent_rss,
                        "child_processes": child_rows,
                        "unfinished_production_tasks": unfinished,
                        "process_group_rss_bytes": total,
                    }
        if unfinished == 0:
            break
        time.sleep(0.005)
    if peak is None or all_children_executing_sample_count == 0:
        raise RuntimeError("no simultaneous parent-plus-four-production-child RSS sample")
    return {
        "poll_interval_seconds": 0.005,
        "complete_group_sample_count": sample_count,
        "all_children_executing_sample_count": all_children_executing_sample_count,
        "peak_all_children_executing_sample": peak,
    }


def run(output: Path, scratch_parent: Path) -> dict[str, object]:
    scratch_parent = scratch_parent.resolve()
    scratch_parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="rcle_r04_live_rss_", dir=scratch_parent))
    source = canonical_source_identity(production_source_paths())
    native = runner.native_artifact_identity()
    native_binding_sha256 = hashlib.sha256(
        canonical_json_bytes(
            {
                "source_sha256": native["source_sha256"],
                "build_key": native["build_key"],
                "artifact_sha256": native["sha256"],
            }
        )
    ).hexdigest()
    base = scratch / "production_group"
    resource = make_process_resource_object(
        canonical_result_root=base / "canonical",
        private_scratch_roots=[base / f"private_{index}" for index in range(WORKERS)],
        source_set_sha256=str(source["source_set_sha256"]),
        native_binding_sha256=native_binding_sha256,
    )
    validated_at = datetime.now(timezone.utc)
    calls: list[tuple[str, dict[str, object], dict[str, object], dict[str, object]]] = []
    lease_document: dict[str, object] | None = None
    for block_index in range(WORKERS):
        payload = make_spawn_payload(
            resource,
            block_index=block_index,
            block_root_digest=f"{block_index + 700:064x}",
            native_source_sha256=chain.ACCEPTED_NATIVE_SOURCE_SHA256,
            native_build_key=chain.ACCEPTED_NATIVE_BUILD_KEY,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            test_only=False,
            test_steps=1,
        )
        context, lease_document = chain._protocol_canary_context(
            payload, failure_once=False, validated_at=validated_at
        )
        authorization = make_worker_authorization(
            resource, payload, production_context=context
        )
        payload_path = write_spawn_payload(
            Path(str(payload["private_scratch_root"])) / f"payload_{block_index:02d}.json",
            payload,
        )
        calls.append((str(payload_path), authorization, payload, context))
    assert lease_document is not None

    with ProcessPoolExecutor(
        max_workers=WORKERS, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        futures = [
            pool.submit(run_production_block_worker, path, authorization)
            for path, authorization, _, _ in calls
        ]
        child_pids = tuple(sorted(int(pid) for pid in pool._processes))  # type: ignore[attr-defined]
        if len(child_pids) != WORKERS:
            raise RuntimeError("production process pool did not create four children")
        simultaneous = _sample_live_group(futures, child_pids)
        rows = [future.result() for future in futures]

    returned_pids = tuple(sorted(int(row["worker_pid"]) for row in rows))
    if returned_pids != child_pids:
        raise RuntimeError("sampled child PIDs differ from production worker terminals")
    frontier, authority = chain._protocol_parent_frontier(
        Path(str(resource["canonical_result_root"])) / "frontier",
        calls[0][3],
        lease_document,
    )
    validated = []
    for row, (_, authorization, payload, _) in zip(rows, calls):
        manifest = runner._prevalidate_production_packet(
            frontier, authority, str(row["packet_path"]), payload, authorization
        )
        validated.append((int(manifest["block_index"]), str(row["packet_path"]), manifest))
    for _, packet_path, manifest in sorted(validated):
        runner._install_prevalidated_production_packet(frontier, packet_path, manifest)

    peak = simultaneous["peak_all_children_executing_sample"]
    assert isinstance(peak, dict)
    group_rss = int(peak["process_group_rss_bytes"])
    evidence: dict[str, object] = {
        "schema": SCHEMA,
        "mode": "FIXED_SYNTHETIC_RESULT_BLIND_REAL_PRODUCTION_CHILDREN",
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "source_set_sha256": source["source_set_sha256"],
        "workers": WORKERS,
        "spawn_method": "spawn",
        "production_child_pids": list(returned_pids),
        "simultaneous_rss": simultaneous,
        "process_group_rss_ceiling_bytes": PROCESS_GROUP_RSS_CEILING,
        "ceiling_pass": group_rss <= PROCESS_GROUP_RSS_CEILING,
        "all_packets_prevalidated_before_parent_install": True,
        "ordered_parent_install": [row[0] for row in sorted(validated)],
        "scientific_identity_materialized": False,
        "coordinate_materialized": False,
        "production_authority_used": False,
        "result_value_exposed": False,
        "scratch_root": str(scratch),
    }
    if evidence["ceiling_pass"] is not True:
        raise RuntimeError("live production process-group RSS exceeds frozen ceiling")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(evidence))
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scratch-parent", type=Path, required=True)
    args = parser.parse_args()
    evidence = run(args.output, args.scratch_parent)
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
