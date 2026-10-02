"""Explicit B03 allowance; B02 primitives remain immutable."""
from __future__ import annotations

import time

from ..b02 import evidence as e

LIMITS = {"static_calls": 1155699, "native_steps": 4500, "fits": 0,
          "cpu_seconds": 1800, "disk_bytes": 2684354560}
COUNTERS = e.COUNTERS + ("alias_gates", "reused_episodes", "prior_episode_reads", "selection_processes")


class Bill(e.Bill):
    def charge(self, name, n=1):
        with self.lock:
            self.values[COUNTERS.index(name)] += n
            value = self.values[COUNTERS.index(name)]
        if name in LIMITS and value > LIMITS[name]:
            raise RuntimeError(f"B03 limit exceeded: {name}={value}")
        if name in ("static_calls", "native_steps") and value % 100 == 0:
            self.check(sample_disk=False)

    def snapshot(self):
        with self.lock:
            counts = dict(zip(COUNTERS, list(self.values)))
        return {"counters": counts, "cpu": e.cpu(), "wall_seconds": time.perf_counter() - self.started,
                "disk_peak_bytes_including_prior": self.disk_peak, "disk_roots": self.roots,
                "limits": LIMITS, "gpu_forwards": 0, "new_training_label_queries": 0,
                "counter_semantics": "attempts before effect, completed after return; internal nested method counts are separate from explicit static calls; CPU self+live/reaped children counted once"}

    def check(self, sample_disk=True, pending=0):
        if e.cpu()["total_seconds"] + getattr(self, "prior_parent_cpu_seconds", 0.0) > LIMITS["cpu_seconds"]:
            raise RuntimeError("B03 cumulative CPU limit exceeded")
        now = time.perf_counter()
        # Reserve successive bounded chunks until the next disk sample; a fast
        # writer cannot spend the same cached headroom repeatedly within one second.
        reserved = getattr(self, "reserved_since_sample", 0)
        force_sample = pending > 0 and reserved + pending >= 8 * 1024 ** 2
        if sample_disk and (now - self.last_disk_time >= 1 or force_sample):
            self.disk_peak = max(self.disk_peak, self.immutable_allocated_bytes + e.allocated(self.roots[-1:]))
            self.last_disk_time = now
            reserved = 0
        # Includes manifest rewrite, progress and compact emergency failure ledger.
        metadata_headroom = 1024 ** 2
        if self.disk_peak + reserved + pending + metadata_headroom > LIMITS["disk_bytes"]:
            raise RuntimeError("B03 source/prior/output disk limit exceeded")
        self.reserved_since_sample = reserved + pending
