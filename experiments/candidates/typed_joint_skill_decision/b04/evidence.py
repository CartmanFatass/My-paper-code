"""B04 compact, exclusive evidence and cumulative admitted work accounting."""
from __future__ import annotations
import contextlib
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import time

LAUNCH_FILES = {"launch-manifest.json", "launch-status.json", "status.json", "stdout.log", "stderr.log", "admission-preflight.json"}
NATIVE_COUNTERS = ("static_calls", "static_completed", "native_steps", "native_completed", "fits", "fits_completed",
 "hosts", "hosts_completed", "resets", "resets_completed", "radio_refresh_calls", "radio_refresh_completed",
 "reward_calls", "reward_completed", "routing_calls", "routing_completed", "link_update_calls", "link_update_completed",
 "frontend_capacity_calls", "frontend_capacity_completed", "path_loss_matrix_calls", "path_loss_matrix_completed",
 "scalar_sinr_calls", "scalar_sinr_completed", "matching_calls", "matching_completed", "reader_state_checks", "audit_episodes",
 "main_episodes", "spawn_attempts", "spawn_completed")
ROW_PHASES = ("training", "endpoint", "functional_reader", "cold", "engineering")
COUNTERS = NATIVE_COUNTERS + ("updates", "updates_completed", "training_world_presentations", "all_candidate_presentations",
 "gpu_reserved_microseconds", "bank_worlds", "label_rebuild_worlds", "functional_contexts", "endpoint_contexts", "cold_contexts", "engineering_contexts") + tuple(
 k for phase in ROW_PHASES for k in (phase + "_candidate_presentations", phase + "_valid_candidates", phase + "_completed_candidates"))
LIMITS = {"static_calls": 8682080, "native_steps": 584000, "fits": 6, "updates": 24576,
 "training_world_presentations": 786432, "all_candidate_presentations": 15471824,
 "training_candidate_presentations": 12582912, "endpoint_candidate_presentations": 1357824,
 "functional_reader_candidate_presentations": 1357824, "cold_candidate_presentations": 169728,
 "engineering_candidate_presentations": 3536, "gpu_reserved_microseconds": 14400000000}
CPU_LIMIT, DISK_LIMIT = 28800, 7516192768


def plain(value):
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value

def encoded(value):
    return (json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 ** 2), b""):
            h.update(block)
    return h.hexdigest()

def bound_json(path, digest):
    path = Path(path).resolve(strict=True)
    if sha(path) != digest:
        raise ValueError(f"input hash mismatch: {path}")
    return json.loads(path.read_bytes())

def relative_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("artifact path must be relative and contained")
    result = (Path(root) / p).resolve()
    if Path(root).resolve() not in result.parents:
        raise ValueError("artifact escaped root")
    return result

def cpu():
    own = resource.getrusage(resource.RUSAGE_SELF)
    kids = resource.getrusage(resource.RUSAGE_CHILDREN)
    live_seconds, live_pids = 0.0, []
    children_file = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children")
    if children_file.exists():
        for token in children_file.read_text().split():
            try:
                fields = Path(f"/proc/{token}/stat").read_text().rsplit(")", 1)[1].split()
                live_seconds += (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")
                live_pids.append(int(token))
            except FileNotFoundError:
                pass
    return {"self_seconds": own.ru_utime + own.ru_stime,
            "reaped_children_seconds": kids.ru_utime + kids.ru_stime,
            "live_children_seconds": live_seconds, "live_children_pids": live_pids,
            "total_seconds": own.ru_utime + own.ru_stime + kids.ru_utime + kids.ru_stime + live_seconds,
            "self_peak_rss_kib": own.ru_maxrss, "children_max_peak_rss_kib": kids.ru_maxrss,
            "rss_scope": "separate process maxima, not summed simultaneous peak"}

def allocated(roots, seen=None):
    seen, total = (set() if seen is None else seen), 0
    for root in roots:
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
            for path in [Path(directory), *[Path(directory) / f for f in files]]:
                try:
                    s = path.lstat()
                except FileNotFoundError:
                    continue
                key = (s.st_dev, s.st_ino)
                if key not in seen:
                    total += s.st_blocks * 512
                    seen.add(key)
    return total

class Store:
    def __init__(self, root, bill):
        self.root, self.bill = Path(root), bill
        self.root.mkdir(parents=True, exist_ok=True)
        unknown = [p.name for p in self.root.iterdir()
                   if p.name not in LAUNCH_FILES and not p.name.startswith(".hmasd-launch-")]
        if unknown:
            raise ValueError(f"output already holds non-launcher evidence: {unknown}")
        self.files = {}

    def write(self, relative, value):
        path = relative_path(self.root, relative)
        data = encoded(value)
        self.bill.check(pending=len(data) + 65536)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        self.register(relative)
        return path

    def write_gzip(self, relative, value):
        path = relative_path(self.root, relative)
        data = encoded(value)
        compressed = gzip.compress(data, compresslevel=1, mtime=0)
        self.bill.check(pending=len(compressed) + 65536)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as f:
            f.write(compressed)
            f.flush()
            os.fsync(f.fileno())
        self.register(relative, content_format="gzip-json", uncompressed_bytes=len(data),
                      record_count=len(value) if isinstance(value, list) else None)
        return path

    def register(self, relative, **metadata):
        path = relative_path(self.root, relative)
        self.files[str(relative)] = {"sha256": sha(path), "bytes": path.stat().st_size, **metadata}
        (self.root / "artifact-manifest.json").write_bytes(encoded({"schema": 1, "files": self.files}))

    def progress(self, phase, **fields):
        value = {"phase": phase, **fields, "bill": self.bill.snapshot()}
        (self.root / "progress.json").write_bytes(encoded(value))

    def failure(self, exc):
        raw = self.root / "raw"
        if raw.exists():
            for p in raw.rglob("*"):
                relative = str(p.relative_to(self.root))
                if p.is_file() and relative not in self.files:
                    self.register(relative)  # Interrupted/failed calls retain even incomplete streams.
        self.progress("failed", error_type=type(exc).__name__, error=str(exc))
        (self.root / "failure.json").write_bytes(encoded({"type": type(exc).__name__, "error": str(exc),
                                                        "bill": self.bill.snapshot(), "retry": False}))

class Trace:
    def __init__(self, path, bill):
        self.path, self.bill, self.rows = Path(path), bill, 0
        self.format_wall = self.format_cpu = self.write_wall = self.write_cpu = 0.
        self.allocated_bytes = 0
        self.bill.check(pending=1024**2)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = gzip.open(self.path, "xb", compresslevel=1)

    def write(self, row):
        wall, cpu_start = time.perf_counter(), time.process_time()
        data = encoded(row)
        self.format_wall += time.perf_counter()-wall
        self.format_cpu += time.process_time()-cpu_start
        wall, cpu_start = time.perf_counter(), time.process_time()
        self.stream.write(data)
        self.rows += 1
        if self.rows % 25 == 0:
            self.stream.flush()
        self.write_wall += time.perf_counter()-wall
        self.write_cpu += time.process_time()-cpu_start
        if self.rows % 25 == 0:
            allocation = self.path.stat().st_blocks*512
            delta = max(0,allocation-self.allocated_bytes)
            self.allocated_bytes = allocation
            self.bill.check(pending=delta)

    def close(self):
        wall, cpu_start = time.perf_counter(), time.process_time()
        self.stream.close()
        self.write_wall += time.perf_counter()-wall
        self.write_cpu += time.process_time()-cpu_start

    def timing(self):
        return {'rows':self.rows,'format_wall_seconds':self.format_wall,'format_cpu_seconds':self.format_cpu,
                'write_compress_flush_wall_seconds':self.write_wall,'write_compress_flush_cpu_seconds':self.write_cpu,
                'scope':'instrumentation inside complete latency; excludes budget checks and state copying'}

def read_trace(path):
    with gzip.open(path, "rb") as f:
        for line in f:
            yield json.loads(line)

def verify_outputs(root, files):
    for relative, expected in files.items():
        p = relative_path(root, relative)
        if p.stat().st_size != expected["bytes"] or sha(p) != expected["sha256"]:
            raise ValueError(f"artifact changed: {relative}")

def load_output(root, files, relative):
    if relative not in files:
        raise ValueError(f"unbound artifact: {relative}")
    return json.loads(relative_path(root, relative).read_bytes())


class Bill:
    """Shared counters, live/reaped CPU and serialized GPU reservation; no global reset."""
    def __init__(self, values, lock, roots, immutable_roots):
        self.values, self.lock = values, lock
        # Count nested roots once; output is inside the canonical direction runs root.
        all_roots = {str(Path(p).resolve()) for p in roots}
        self.roots = sorted(p for p in all_roots if not any(Path(q) in Path(p).parents for q in all_roots if q != p))
        frozen = {str(Path(p).resolve()) for p in immutable_roots}
        if not frozen <= set(self.roots):
            raise ValueError('immutable disk roots must be disjoint declared roots')
        self.immutable_roots = sorted(frozen)
        self.mutable_roots = [p for p in self.roots if p not in frozen]
        self.immutable_inodes = set()
        self.immutable_allocated = allocated(self.immutable_roots,self.immutable_inodes)
        self.started = time.perf_counter()
        self.disk_peak, self.last_disk_time, self.reserved = 0, -float('inf'), 0
        self.gpu_started = None
        self.gpu_cleanup_errors = []
        self.prior_parent_cpu_seconds = 0.
        self.check()

    def charge(self, name, n=1):
        if type(n) is not int or n < 0:
            raise ValueError("nonnegative integer charge required")
        with self.lock:
            i = COUNTERS.index(name)
            self.values[i] += n
            current = self.values[i]
        if name in LIMITS and current > LIMITS[name]:
            raise RuntimeError(f"B04 hard count ceiling: {name}={current}")
        if name in ("static_calls", "native_steps") and current % 100 == 0:
            self.check(sample_disk=False)

    def rows(self, phase, physical, valid=None):
        self.check(sample_disk=False)
        self.charge("all_candidate_presentations", physical)
        self.charge(phase + "_candidate_presentations", physical)
        self.charge(phase + "_valid_candidates", physical if valid is None else valid)

    def rows_done(self, phase, physical):
        self.charge(phase + "_completed_candidates", physical)

    def gpu_tick(self):
        if self.gpu_started is not None:
            now = time.perf_counter()
            micros = max(0, round((now - self.gpu_started) * 1e6))
            self.gpu_started = now
            with self.lock:
                self.values[COUNTERS.index('gpu_reserved_microseconds')] += micros

    @contextlib.contextmanager
    def gpu(self):
        if self.gpu_started is not None:
            raise RuntimeError("nested GPU reservation")
        self.gpu_started = time.perf_counter()  # Before CUDA initialization/cold load.
        failed = False
        try:
            yield
        except BaseException:
            failed = True
            raise
        finally:
            # Include synchronization, CPU staging, logging and idle gaps in this phase.
            import torch
            try:
                if torch.cuda.is_initialized():
                    torch.cuda.synchronize()
            except BaseException as cleanup_error:
                self.gpu_cleanup_errors.append(repr(cleanup_error))
                if not failed:
                    raise
            finally:
                self.gpu_tick()
                self.gpu_started = None
            if not failed:
                self.check(sample_disk=False)

    def check(self, sample_disk=True, pending=0):
        self.gpu_tick()
        if self.counter_snapshot()['gpu_reserved_microseconds'] > LIMITS['gpu_reserved_microseconds']:
            raise RuntimeError('B04 reserved GPU wall ceiling')
        if cpu()["total_seconds"] + self.prior_parent_cpu_seconds > CPU_LIMIT:
            raise RuntimeError("B04 cumulative CPU ceiling")
        now = time.perf_counter()
        if sample_disk and (now - self.last_disk_time >= 2 or self.reserved + pending >= 8 * 1024 ** 2):
            self.disk_peak = max(self.disk_peak, self.immutable_allocated+allocated(self.mutable_roots,set(self.immutable_inodes)))
            self.last_disk_time, self.reserved = now, 0
        if self.disk_peak + self.reserved + pending + 2*1024 ** 2 > DISK_LIMIT:
            raise RuntimeError("B04 full scoped allocated disk ceiling")
        self.reserved += pending

    def snapshot(self):
        self.gpu_tick()
        counters = self.counter_snapshot()
        return {"counters": counters, "cpu": cpu(), "wall_seconds": time.perf_counter() - self.started,
                "gpu_reserved_wall_seconds": counters["gpu_reserved_microseconds"] / 1e6,
                "disk_peak_allocated_bytes": self.disk_peak, "disk_roots": self.roots,
                "immutable_disk_roots":self.immutable_roots,"immutable_source_asset_allocated_bytes":self.immutable_allocated,
                "gpu_cleanup_errors":list(self.gpu_cleanup_errors),
                "cpu_ceiling_seconds": CPU_LIMIT, "disk_ceiling_bytes": DISK_LIMIT, "ceilings": LIMITS,
                "counter_semantics": "attempts before effect, completions after return; physically computed padding included; method-level internal calls separate; CPU self+live/reaped children counted once",
                "support_cpu": "unmetered support unknown; not zero"}

    def counter_snapshot(self):
        """Read paid integer counters without a new resource checkpoint during recording."""
        with self.lock:
            return dict(zip(COUNTERS, list(self.values)))


def npz_write(store, relative, arrays):
    import numpy as np
    path = relative_path(store.root, relative)
    store.bill.check(pending=sum(a.nbytes for a in arrays.values()) + 1024 ** 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        np.savez_compressed(stream, **arrays)
        stream.flush()
        os.fsync(stream.fileno())
    store.register(relative, content_format="numpy-npz-no-pickle")
    return path


def torch_write(store, relative, value):
    import torch
    path = relative_path(store.root, relative)
    store.bill.check(pending=16 * 1024 ** 2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        torch.save(value, stream)
        stream.flush()
        os.fsync(stream.fileno())
    store.register(relative, content_format="torch-weights-only")
    return path


def checked_torch(path, digest):
    import torch
    if sha(path) != digest:
        raise ValueError("checkpoint digest mismatch")
    return torch.load(path, map_location='cpu', weights_only=True)


class Diagnostics:
    """Stream every check so millions of successful checks do not accumulate in RAM."""
    def __init__(self,store):
        self.store,self.relative,self.count=store,'raw/reader/checks.jsonl.gz',0
        self.trace=Trace(relative_path(store.root,self.relative),store.bill)
        self.closed=False
    def append(self,row):
        self.trace.write(row);self.count+=1
    def __len__(self):
        return self.count
    def close(self):
        if not self.closed:
            self.trace.close();self.store.register(self.relative,content_format='gzip-jsonl',record_count=self.count)
            self.closed=True
