"""One-process operation billing and conservative, non-restarting stop guards."""
import math
import os
from pathlib import Path
import resource
import signal
import time


class OperationLimit(RuntimeError):
    pass


def resources():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"self_user_seconds": own.ru_utime, "self_system_seconds": own.ru_stime,
            "children_user_seconds": children.ru_utime, "children_system_seconds": children.ru_stime,
            "peak_rss_kib": own.ru_maxrss,
            "cpu_seconds": own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime}


def allocated_bytes(roots):
    """Count each allocated inode once; never follow source/output symlinks."""
    seen, total, pending = set(), 0, [Path(p) for p in roots]
    while pending:
        path = pending.pop()
        if not path.exists() and not path.is_symlink():
            continue
        stat = path.lstat()
        identity = stat.st_dev, stat.st_ino
        if identity in seen:
            continue
        seen.add(identity)
        total += stat.st_blocks * 512
        if path.is_dir() and not path.is_symlink():
            pending.extend(path.iterdir())
    return total


def local_overlap():
    """Read-only process inventory, restricted to HMASD scientific command paths."""
    rows = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            fields = (entry / "cmdline").read_bytes().decode(errors="replace").split("\0")
            paths = [v for v in fields if v.endswith(".py") and any(
                key in v for key in ("experiments/candidates/", "scripts/run_", "hmasd_launch.py"))]
            if paths:
                rows.append({"pid": int(entry.name), "entry_paths": paths})
        except (OSError, ProcessLookupError):
            continue
    return sorted(rows, key=lambda row: row["pid"])


class Meter:
    def __init__(self, *, start_wall, source, out, preparation_cpu, limits):
        self.start_wall, self.preparation_cpu = start_wall, float(preparation_cpu)
        if not math.isfinite(self.preparation_cpu) or self.preparation_cpu < 0:
            raise ValueError("invalid metered preparation CPU")
        self.roots, self.limits = (Path(source), Path(out)), dict(limits)
        self.disk_bytes = self.peak_disk_bytes = 0
        self.last_disk_check = float("-inf")
        self.samples = 0
        self.armed = False
        self.stop_reason = None
        self.overlap_start = local_overlap()
        self.check(force_disk=True)

    def check(self, *, force_disk=False):
        if self.stop_reason is not None:
            raise OperationLimit(self.stop_reason)
        usage = resources()
        cpu = self.preparation_cpu + usage["cpu_seconds"]
        wall = time.monotonic() - self.start_wall
        self.samples += 1
        if cpu >= self.limits["aggregate_metered_cpu_seconds"] - self.limits["finalization_cpu_reserve_seconds"]:
            self.stop("aggregate preparation/worker/reader CPU stop boundary")
        if wall >= self.limits["operation_wall_seconds"] - self.limits["finalization_wall_reserve_seconds"]:
            self.stop("operation wall stop boundary")
        now = time.monotonic()
        if force_disk or now - self.last_disk_check >= 5:
            self.disk_bytes = allocated_bytes(self.roots)
            self.peak_disk_bytes = max(self.peak_disk_bytes, self.disk_bytes)
            self.last_disk_check = now
            if self.disk_bytes >= self.limits["allocated_bytes"] - self.limits["allocation_reserve_bytes"]:
                self.stop("source/evidence/transient allocated-byte stop boundary")
        return usage

    def stop(self, reason):
        self.stop_reason = str(reason)
        # A resource exception closes science permanently. Restore the guards
        # before unwinding into evidence retention, so repeated SIGXCPU cannot
        # interrupt the explicitly reserved finalization work.
        self.close()
        raise OperationLimit(self.stop_reason)

    def arm(self):
        """Signals bound long branches as well as the cooperative callback checks."""
        def stop(signum, frame):
            self.stop(f"operation resource signal {signum}")
        self.old_cpu_handler = signal.signal(signal.SIGXCPU, stop)
        self.old_alarm_handler = signal.signal(signal.SIGALRM, stop)
        remaining_total = (self.limits["aggregate_metered_cpu_seconds"] - self.preparation_cpu
                           - self.limits["finalization_cpu_reserve_seconds"])
        own = resources()
        soft = max(1, math.ceil(remaining_total - own["children_user_seconds"] - own["children_system_seconds"]))
        self.old_cpu_limit = resource.getrlimit(resource.RLIMIT_CPU)
        old_soft, old_hard = self.old_cpu_limit
        if old_soft != resource.RLIM_INFINITY:
            soft = min(soft, old_soft)
        if old_hard != resource.RLIM_INFINITY:
            soft = min(soft, old_hard)
        self.armed = True
        resource.setrlimit(resource.RLIMIT_CPU, (soft, old_hard))
        remaining_wall = (self.limits["operation_wall_seconds"] - self.limits["finalization_wall_reserve_seconds"]
                          - (time.monotonic() - self.start_wall))
        signal.setitimer(signal.ITIMER_REAL, max(.001, remaining_wall))

    def close(self):
        if self.armed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            resource.setrlimit(resource.RLIMIT_CPU, self.old_cpu_limit)
            signal.signal(signal.SIGXCPU, self.old_cpu_handler)
            signal.signal(signal.SIGALRM, self.old_alarm_handler)
            self.armed = False

    def record(self, *, final=False):
        usage = resources()
        if final:
            self.disk_bytes = allocated_bytes(self.roots)
            self.peak_disk_bytes = max(self.peak_disk_bytes, self.disk_bytes)
        return {**usage, "preparation_cpu_seconds": self.preparation_cpu,
                "aggregate_metered_cpu_seconds": self.preparation_cpu + usage["cpu_seconds"],
                "operation_wall_seconds": time.monotonic() - self.start_wall,
                "allocated_bytes_latest": self.disk_bytes, "allocated_bytes_peak_observed": self.peak_disk_bytes,
                "allocated_roots": [str(p) for p in self.roots], "check_count": self.samples,
                "overlap_start": self.overlap_start, "overlap_at_record": local_overlap() if final else None,
                "scope": "one process including imports and numerical threads; reaped children separate;"
                         " preparation CPU once; launcher/support/finalization after this sample separately recorded",
                "disk_scope": "allocated inodes in source snapshot and output, including directories, no symlink targets",
                "stop_reserves": {k: v for k, v in self.limits.items() if "reserve" in k}}
