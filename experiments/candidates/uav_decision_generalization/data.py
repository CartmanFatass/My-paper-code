"""Compact streaming evidence and cumulative B01 accounting (no native imports).

Counters distinguish call entry from successful return. Failed calls consume allowance,
while completed steps/episodes are separately visible. No producer recovery/retry exists.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import time
from typing import Any

from .contract import (MAX_CORRECTNESS_EPISODES, MAX_CPU_SECONDS, MAX_DISK_BYTES,
                       MAX_NATIVE_STEPS, MAX_STATIC_CALLS, encode_json)

COUNTERS = (
    "native_step_calls", "native_steps_completed", "static_evaluation_calls", "static_evaluations_completed",
    "reset_calls", "resets_completed", "host_construction_calls", "hosts_constructed", "candidate_build_calls",
    "candidate_builds_completed", "matching_calls", "matchings_completed", "candidate_episode_calls",
    "candidate_episodes_completed", "planner_episode_calls", "planner_episodes_completed", "correctness_episode_calls",
    "correctness_episodes_completed", "planner_menu_calls", "planner_menus_completed", "worlds_completed", "trace_rows_written",
    "fit_calls", "fits_completed", "optimizer_update_calls", "optimizer_updates_completed",
    "training_A_contexts", "training_R_contexts", "endpoint_A_contexts", "endpoint_R_contexts", "endpoint_N_contexts",
    "reader_A_contexts", "reader_R_contexts", "reader_N_contexts", "reader_episode_reads", "reader_alias_reads", "reader_updates_read",
)
LIMITS = {"native_step_calls":MAX_NATIVE_STEPS,"static_evaluation_calls":MAX_STATIC_CALLS,
          "correctness_episode_calls":16,"candidate_episode_calls":3072,"planner_episode_calls":384,
          "fit_calls":6,"optimizer_update_calls":3072,"training_A_contexts":49152,"training_R_contexts":49152,
          "endpoint_A_contexts":2304,"endpoint_R_contexts":2304,"endpoint_N_contexts":384,
          "reader_A_contexts":2304,"reader_R_contexts":2304,"reader_N_contexts":384,
          "reader_episode_reads":3456,"reader_alias_reads":16,"reader_updates_read":3072}
MAX_GPU_SECONDS = 3600
LAUNCHER_FILES = {"launch-manifest.json", "launch-status.json", "stdout.log", "stderr.log",
                  "admission-preflight.json"}


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cpu_seconds() -> float:
    # Include finished native build/helper children, if imported dependencies create them.
    return sum(r.ru_utime + r.ru_stime for r in (
        resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


def allocated_bytes(roots: list[Path]) -> int:
    """Count unique inodes across declared global disk roots; do not follow symlinks."""
    seen, total = set(), 0
    def charge(path):
        nonlocal total
        stat = path.lstat()
        key = (stat.st_dev, stat.st_ino)
        if key not in seen:
            seen.add(key)
            total += stat.st_blocks * 512
    for root in roots:
        if not root.exists():
            continue
        charge(root)
        if root.is_dir():
            for directory, folders, files in os.walk(root, followlinks=False):
                for name in folders + files:
                    charge(Path(directory) / name)
    return total


class BudgetExceeded(RuntimeError):
    pass


class Bill:
    """A DM-supplied prior bill binds previous setup/probes and global disk roots.

    JSON input: schema=1, prior_counters (all COUNTERS), prior_cpu_seconds,
    disk_roots (canonical absolute directories containing output + weights + isolated
    runtime and every other retained study object). This runner adds only its delta;
    the next phase consumes the terminal cumulative bill. The roots' completeness
    is a DM declaration, not something the collector can infer from host disk use.
    """
    def __init__(self, ledger: dict[str, Any], output: Path, *, source_root: Path | None = None):
        if ledger.get("schema") != 1 or set(ledger) != {
                "schema", "prior_counters", "prior_cpu_seconds", "prior_gpu_seconds", "disk_roots"}:
            raise ValueError("invalid prior bill schema")
        prior = ledger["prior_counters"]
        if set(prior) != set(COUNTERS) or any(type(v) is not int or v < 0 for v in prior.values()):
            raise ValueError("prior bill must state all nonnegative integer counters")
        seconds = ledger["prior_cpu_seconds"]
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not 0 <= seconds <= MAX_CPU_SECONDS:
            raise ValueError("invalid cumulative prior CPU bill")
        gpu_seconds = ledger["prior_gpu_seconds"]
        if (isinstance(gpu_seconds, bool) or not isinstance(gpu_seconds, (int, float))
                or not 0 <= gpu_seconds <= MAX_GPU_SECONDS):
            raise ValueError("invalid cumulative prior GPU bill")
        roots = ledger["disk_roots"]
        if not isinstance(roots, list) or not roots or any(not isinstance(x, str) for x in roots):
            raise ValueError("global disk roots are required")
        self.roots = [Path(x) for x in roots]
        self.root_categories = {"declared_study_roots":list(roots),"source_snapshot":[],"inherited_evidence":[],"sequential_study_evidence":[]}
        self.own_peak_allocated = 0
        if source_root is not None:
            if not source_root.is_absolute() or source_root.resolve() != source_root or not source_root.is_dir():
                raise ValueError("admitted source_root must be canonical existing absolute directory")
            self.roots.append(source_root)
            self.root_categories["source_snapshot"].append(str(source_root))
        if any(not p.is_absolute() or p.resolve() != p or not p.is_dir() for p in self.roots):
            raise ValueError("disk roots must be existing canonical absolute directories")
        if not any(output.is_relative_to(root) for root in self.roots):
            raise ValueError("output is outside declared global disk roots")
        self.prior, self.delta = dict(prior), dict.fromkeys(COUNTERS, 0)
        self.prior_cpu = float(seconds)
        self.prior_gpu = float(gpu_seconds)
        self.gpu_elapsed = 0.0
        self.gpu_started = None
        # Start before importing any native dependency; setup overhead remains in the bill.
        self.started_wall, self.started_cpu = time.perf_counter(), 0.0
        self.peak_allocated = 0
        self.output = output
        self.disk_other = 0
        self.disk_own = 0
        self.disk_paths = {}
        self.last_disk_refresh = -float("inf")
        self.check(disk=True)

    def refresh_disk(self):
        # A full global scan on every step would dwarf native collection. Track
        # each collector-owned file's actual allocated blocks between scans; refresh
        # other declared study roots at least every 30 wall seconds.
        paths = []
        if self.output.exists():
            paths.append(self.output)
            for directory, folders, files in os.walk(self.output, followlinks=False):
                paths.extend(Path(directory) / name for name in folders + files)
        self.disk_paths = {str(p): p.lstat().st_blocks * 512 for p in paths}
        self.disk_own = sum(self.disk_paths.values())
        self.own_peak_allocated = max(self.own_peak_allocated,self.disk_own)
        self.disk_other = allocated_bytes(self.roots) - self.disk_own
        self.last_disk_refresh = time.perf_counter()

    def observe_file(self, path: Path, *, parents=True):
        # Each raw chunk updates its one file; new parent directories are also
        # charged. This observes actual blocks without scanning the trace corpus.
        while path.is_relative_to(self.output):
            previous = self.disk_paths.get(str(path), 0)
            if path.exists():
                self.disk_paths[str(path)] = path.lstat().st_blocks * 512
            else:
                self.disk_paths.pop(str(path), None)
            self.disk_own += self.disk_paths.get(str(path), 0) - previous
            if not parents:
                break
            if path == self.output:
                break
            path = path.parent
        self.own_peak_allocated = max(self.own_peak_allocated,self.disk_own)
        used = self.disk_other + self.disk_own
        self.peak_allocated = max(self.peak_allocated, used)

    def total(self, name):
        return self.prior[name] + self.delta[name]

    def enter(self, name, count=1):
        if type(count) is not int or count < 0:
            raise ValueError("counter increment must be nonnegative integer")
        self.check()
        if name in LIMITS and self.total(name) + count > LIMITS[name]:
            raise BudgetExceeded(f"{name} allowance exhausted")
        self.delta[name] += count

    def complete(self, name):
        self.delta[name] += 1

    def gpu_seconds(self):
        return self.gpu_elapsed + (time.perf_counter() - self.gpu_started if self.gpu_started is not None else 0)

    def start_gpu(self):
        self.check()
        if self.gpu_started is not None:
            raise ValueError("GPU bill window already active")
        self.gpu_started = time.perf_counter()

    def stop_gpu(self):
        if self.gpu_started is not None:
            self.gpu_elapsed += time.perf_counter() - self.gpu_started
            self.gpu_started = None

    def check(self, *, disk=False, pending_bytes=0):
        if self.prior_cpu + cpu_seconds() - self.started_cpu >= MAX_CPU_SECONDS:
            raise BudgetExceeded("cumulative CPU ceiling reached")
        if self.prior_gpu + self.gpu_seconds() >= MAX_GPU_SECONDS:
            raise BudgetExceeded("cumulative GPU ceiling reached")
        for name, limit in LIMITS.items():
            if self.total(name) > limit:
                raise BudgetExceeded(f"cumulative {name} ceiling exceeded")
        if disk:
            if time.perf_counter() - self.last_disk_refresh >= 30:
                self.refresh_disk()
            used = self.disk_other + self.disk_own
            self.peak_allocated = max(self.peak_allocated, used)
            # Conservative reservation for the next uncompressed chunk and filesystem blocks.
            if MAX_DISK_BYTES is not None and used + pending_bytes + 65536 > MAX_DISK_BYTES:
                raise BudgetExceeded("declared global allocated-disk ceiling reached")

    def snapshot(self):
        return {"delta_counters": dict(self.delta),
                "cumulative_counters": {k: self.total(k) for k in COUNTERS},
                "process_and_finished_children_cpu_seconds": cpu_seconds() - self.started_cpu,
                "cumulative_cpu_seconds": self.prior_cpu + cpu_seconds() - self.started_cpu,
                "gpu_reserved_wall_seconds": self.gpu_seconds(),
                "cumulative_gpu_seconds": self.prior_gpu + self.gpu_seconds(),
                "gpu_scope": "elapsed reserved GPU window; caller synchronizes at boundaries; fit and fresh endpoints charged, independent CPU reader uses zero GPU",
                "wall_seconds": time.perf_counter() - self.started_wall,
                "process_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                "global_peak_allocated_bytes_observed": self.peak_allocated,
                "disk_roots": [str(root) for root in self.roots],
                "disk_root_categories": self.root_categories,
                "current_phase_new_evidence_peak_allocated_bytes":self.own_peak_allocated,
                "current_phase_new_evidence_allocated_bytes":self.disk_own,
                "new_evidence_scope":"only current output directory; prior phase study roots and inherited roots listed separately",
                "disk_measurement": "collector files actual allocated blocks after each flushed chunk; global roots refreshed every 30 wall seconds",
                "counter_semantics": "call entry charged, failed calls retained; completed counters only successful returns",
                "rss_scope": "single collector process peak, Linux KiB converted to bytes"}


class Store:
    """Fresh output, one raw trace copy, hashed streaming manifest; never resume."""
    def __init__(self, output: Path, bill: Bill):
        if output.exists():
            if (not output.is_dir() or not (output / "launch-manifest.json").is_file()
                    or any((p.name not in LAUNCHER_FILES
                            and not (p.name.startswith(".hmasd-launch-") and p.name.endswith(".tmp")))
                           or not p.is_file() or p.is_symlink()
                           for p in output.iterdir())):
                raise FileExistsError("output contains prior scientific or non-launcher evidence")
        else:
            output.mkdir(parents=False, exist_ok=False)
        self.output, self.bill = output, bill
        self.manifest = (output / "manifest.jsonl").open("xb")
        self.manifest_rows = 0
        self.current = None
        self.bytes_written = 0
        self.bill.observe_file(output)

    def locate(self, path):
        result = self.output / path
        if result.resolve() != result or not result.is_relative_to(self.output):
            raise ValueError("noncanonical output path")
        result.parent.mkdir(parents=True, exist_ok=True)
        return result

    def append_manifest(self, entry):
        data = encode_json(entry)
        self.manifest.write(data)
        self.manifest.flush()
        os.fsync(self.manifest.fileno())
        self.manifest_rows += 1
        self.bytes_written += len(data)
        self.bill.observe_file(self.output / "manifest.jsonl")

    def record_file(self, path: Path, **metadata):
        entry = {"path": str(path.relative_to(self.output)), "bytes": path.stat().st_size,
                 "sha256": hash_file(path), **metadata}
        self.append_manifest(entry)
        return entry

    def write_json(self, relative, value, **metadata):
        data = encode_json(value)
        self.bill.check(disk=True, pending_bytes=len(data))
        path = self.locate(relative)
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        self.bytes_written += len(data)
        self.bill.observe_file(path)
        return self.record_file(path, **metadata)

    def status(self, status, **extra):
        # Replace only this collector's own compact status. No scores or test Q in progress.
        value = {"schema": 1, "status": status, "current": self.current,
                 "bill": self.bill.snapshot(), "manifest_rows": self.manifest_rows,
                 "encoded_data_and_manifest_bytes": self.bytes_written, **extra}
        data = encode_json(value)
        partial = self.output / "progress.json.partial"
        with partial.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(partial, self.output / "progress.json")
        self.bill.observe_file(self.output / "progress.json")
        return value

    def close(self):
        self.manifest.flush()
        os.fsync(self.manifest.fileno())
        self.manifest.close()


class Trace:
    """One gzip JSONL per episode: reset identity then every native step in bounded chunks.

    Logical digest excludes timing/provenance and allows the paid reversed-order audit
    to compare every saved native value without retaining a duplicate trace. Failed
    audits retain the actual mismatching series in their partial file.
    """
    def __init__(self, store: Store, path: str, header: dict[str, Any]):
        self.store, self.path = store, store.locate(path)
        self.file = self.path.open("xb")
        self.stream = gzip.GzipFile(filename="", mode="wb", fileobj=self.file, mtime=0)
        self.logical = hashlib.sha256()
        self.steps = 0
        self.rows = 0
        self.pending_bytes = 0
        self.store.bill.observe_file(self.path)
        try:
            self.write(header)
        except BaseException:
            self.close("partial")
            raise

    def write(self, row):
        data = encode_json(row)
        # At most 32 rows between flushes. Exceptions close and retain all rows;
        # an uncatchable kill can lose at most that buffered suffix, explicitly
        # leaving a partial stream rather than pretending to have completed it.
        self.store.bill.check(disk=True, pending_bytes=self.pending_bytes + len(data))
        self.logical.update(data)
        self.stream.write(data)
        self.rows += 1
        self.pending_bytes += len(data)
        if self.rows % 32 == 0:
            self.stream.flush()
            self.file.flush()
            self.store.bill.observe_file(self.path, parents=False)
            self.pending_bytes = 0
        self.store.bytes_written += len(data)
        self.store.bill.complete("trace_rows_written")
        if row.get("kind") == "step":
            self.steps += 1

    def close(self, status):
        self.stream.close()
        self.file.flush()
        os.fsync(self.file.fileno())
        self.file.close()
        self.store.bill.observe_file(self.path)
        return self.store.record_file(self.path, kind="native_trace", status=status,
                                      steps=self.steps, logical_sha256=self.logical.hexdigest())


def read_trace(path: Path):
    with gzip.open(path, "rb") as stream:
        for line in stream:
            yield json.loads(line)
