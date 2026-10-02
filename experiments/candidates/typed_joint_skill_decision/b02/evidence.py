"""B02 bounded evidence, attempted-work billing, and admission input binding."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import time

LIMITS = {"static_calls": 2448408, "native_steps": 102000, "fits": 1,
          "cpu_seconds": 21600, "disk_bytes": 2 * 1024 ** 3}
COUNTERS = ("static_calls", "static_completed", "native_steps", "native_completed",
            "fits", "fits_completed", "hosts", "hosts_completed", "resets", "resets_completed",
            "radio_refresh_calls", "radio_refresh_completed", "reward_calls", "reward_completed",
            "routing_calls", "routing_completed", "link_update_calls", "link_update_completed",
            "frontend_capacity_calls", "frontend_capacity_completed",
            "path_loss_matrix_calls", "path_loss_matrix_completed", "scalar_sinr_calls", "scalar_sinr_completed",
            "matching_calls", "matching_completed", "reader_state_checks", "audit_episodes",
            "main_episodes", "spawn_attempts", "spawn_completed", "reader_reference_searches")
LAUNCH_FILES = {"launch-manifest.json", "launch-status.json", "status.json", "stdout.log",
                "stderr.log", "admission-preflight.json"}


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


def verify_inputs(manifest, source_root, input_root):
    if (manifest["schema"] != 1 or manifest["study"] != "b02_search_branch"
            or manifest["direction"] != "typed_joint_skill_decision"
            or manifest["arms"] != ["G", "L", "P"] or manifest["aliases"] != {"B": "G"}
            or manifest["test_worlds"] != list(range(107100000, 107100064))
            or manifest["audit_worlds"] != list(range(107100000, 107100004))
            or manifest["budget"] != {"cpu_seconds": 21600, "fits": 1, "gpu_forwards": 0,
                                       "incremental_disk_bytes": 2147483648, "native_steps": 102000,
                                       "new_training_labels": 0, "static_calls": 2448408}
            or manifest["fit"] != {"base_width": 15, "basis_width": 135, "dtype": "float64",
                                    "intercept": True, "lambda_sum_loss": 1.0,
                                    "training_rows": 192, "training_worlds": 64}):
        raise ValueError("frozen B02 contract mismatch")
    expected_sources = {"envs/pettingzoo/scenario2.py", "envs/pettingzoo/uav_env.py", "envs/pettingzoo/uav_radio.py",
                        *{f"experiments/candidates/coupled_host_joint_skills_stage1/{f}.py" for f in ("host", "menus", "planner", "run_gate")}}
    if set(manifest["pinned_upstream_sources"]) != expected_sources or manifest["historical_source_sha"] != "f589523191c670e215e3d719fc4f2cd01492c301":
        raise ValueError("complete declared upstream/historical source identity required")
    for path, digest in manifest["pinned_upstream_sources"].items():
        if sha(relative_path(source_root, path)) != digest:
            raise ValueError(f"upstream source mismatch: {path}")
    records = manifest["training_records"]
    worlds = list(range(1000, 1032)) + list(range(2000, 2032))
    if [r["world"] for r in records] != worlds or len({r["path"] for r in records}) != 64:
        raise ValueError("complete unique 64-world archive required")
    result = []
    for r in records:
        path = relative_path(input_root, r["path"])
        if path.stat().st_size != r["bytes"] or sha(path) != r["sha256"]:
            raise ValueError(f"archive byte identity mismatch: {path}")
        result.append(path)
    if sum(r["bytes"] for r in records) != manifest["training_record_bytes"] or manifest["training_record_bytes"] != 21529851:
        raise ValueError("archive byte total mismatch")
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


def allocated(roots):
    seen, total = set(), 0
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


class Bill:
    """Shared attempt counters; CPU totals include children exactly once when reaped."""
    def __init__(self, values, lock, roots, started=None):
        self.values, self.lock = values, lock
        self.roots = [str(Path(r).resolve()) for r in roots]
        self.started = time.perf_counter() if started is None else started
        self.disk_peak = 0
        self.last_disk_time = -float("inf")
        # Immutable admitted source/staging bytes are sampled once, not walked per effect.
        # Last root is the growing output; all roots must be disjoint (checked by the entry).
        self.immutable_allocated_bytes = allocated(self.roots[:-1])

    def charge(self, name, n=1):
        with self.lock:
            self.values[COUNTERS.index(name)] += n
            value = self.values[COUNTERS.index(name)]
        if name in LIMITS and value > LIMITS[name]:
            raise RuntimeError(f"B02 limit exceeded: {name}={value}")
        # Resource checks are amortized; the parent also samples a live child every second.
        if name in ("static_calls", "native_steps") and value % 100 == 0:
            self.check(sample_disk=False)

    def snapshot(self):
        with self.lock:
            counts = dict(zip(COUNTERS, list(self.values)))
        return {"counters": counts, "cpu": cpu(), "wall_seconds": time.perf_counter() - self.started,
                "incremental_disk_peak_bytes": self.disk_peak, "disk_roots": self.roots,
                "limits": LIMITS, "gpu_forwards": 0, "new_training_label_queries": 0,
                "counter_semantics": "attempts charged before call; completed only after successful return; internal method-level radio/routing/capacity/reward counts separate from explicit static calls; nested method counts are not independent RF-link queries or extra CPU sums"}

    def check(self, sample_disk=True, pending=0):
        if cpu()["total_seconds"] + getattr(self, "prior_parent_cpu_seconds", 0.0) > LIMITS["cpu_seconds"]:
            raise RuntimeError("B02 cumulative parent/child CPU limit exceeded")
        now = time.perf_counter()
        if sample_disk and now - self.last_disk_time >= 1.0:
            self.disk_peak = max(self.disk_peak, self.immutable_allocated_bytes + allocated(self.roots[-1:]))
            self.last_disk_time = now
        # Reserve bounded pending output rather than claiming unknown bytes are zero.
        if self.disk_peak + pending > LIMITS["disk_bytes"]:
            raise RuntimeError("B02 incremental disk limit exceeded")


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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = gzip.open(self.path, "xb", compresslevel=1)

    def write(self, row):
        data = encoded(row)
        if self.rows % 25 == 0:
            self.bill.check(pending=1024 ** 2)
        self.stream.write(data)
        self.rows += 1
        if self.rows % 25 == 0:
            self.stream.flush()

    def close(self):
        self.stream.close()


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
