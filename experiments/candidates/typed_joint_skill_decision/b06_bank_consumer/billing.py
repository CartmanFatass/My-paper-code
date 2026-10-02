"""Sequential crash-visible B04 counters; actual investment has no defaults."""
from __future__ import annotations
import contextlib
import mmap
import os
from pathlib import Path
import struct
import time
from experiments.candidates.typed_joint_skill_decision.b04 import evidence as old
from . import contract as c

COUNTERS = old.COUNTERS + ("raw_constructions", "raw_completed", "gpu_child_microseconds", "refused_effects")
Q = struct.Struct("<Q")
CAPS = {key: value for key, value in old.LIMITS.items() if key != "gpu_reserved_microseconds"}
CAPS.update(static_calls=1383760, bank_worlds=0, label_rebuild_worlds=0, raw_constructions=1536,
            hosts=2464, resets=4784, matching_calls=2464, spawn_attempts=1160)


class Shared:
    def __init__(self, path, create=False):
        self.path = Path(path)
        self.file = self.path.open("x+b" if create else "r+b", buffering=0)
        if create:
            self.file.truncate(len(COUNTERS) * Q.size)
        if os.fstat(self.file.fileno()).st_size != len(COUNTERS) * Q.size:
            raise ValueError("consumer counter block size mismatch")
        self.buffer = mmap.mmap(self.file.fileno(), len(COUNTERS) * Q.size)

    def __getitem__(self, index):
        return Q.unpack_from(self.buffer, index * Q.size)[0]

    def __setitem__(self, index, value):
        Q.pack_into(self.buffer, index * Q.size, value)

    def get(self, name):
        return self[COUNTERS.index(name)]

    def charge(self, name, n=1):
        if type(n) is not int or n < 0:
            raise ValueError("nonnegative integer charge required")
        index = COUNTERS.index(name)
        current = self[index]
        if name in CAPS and current + n > CAPS[name]:
            self[COUNTERS.index("refused_effects")] += 1
            raise RuntimeError("consumer effect cap before invocation: " + name)
        self[index] = current + n

    def snapshot(self):
        return {name: self[i] for i, name in enumerate(COUNTERS)}

    def flush(self):
        self.buffer.flush()
        os.fsync(self.file.fileno())

    def close(self):
        self.buffer.flush()
        os.fsync(self.file.fileno())
        self.buffer.close()
        self.file.close()


class Bill(old.Bill):
    # Reuse frozen rows/rows_done and GPU phase context including synchronization. No old limits.
    def __init__(self, shared, deployment, *, child=False, prior_parent_cpu_seconds=0):
        self.shared = self.values = shared
        self.lock = contextlib.nullcontext()
        self.deployment = deployment
        self.preparation = c.preparation_cost(deployment["prior_preparation_cost"])
        self.limits = deployment["limits"]
        self.roots = deployment["disk_roots"]
        self.started = deployment["started_monotonic"]
        self.child = child
        self.prior_parent_cpu_seconds = prior_parent_cpu_seconds
        self.gpu_started = None
        self.gpu_cleanup_errors = []
        self.disk_peak, self.last_disk_time, self.reserved = 0, -float("inf"), 0
        self.current_gpu_child_seconds = 0.
        self.check()

    def charge(self, name, n=1):
        self.shared.charge(name, n)
        if name in ("static_calls", "native_steps") and self.shared.get(name) % 100 == 0:
            self.check(sample_disk=False)

    def counter_snapshot(self):
        return self.shared.snapshot()

    def check(self, sample_disk=True, pending=0):
        self.gpu_tick()
        usage = old.cpu()
        total_cpu = usage["total_seconds"] + (self.prior_parent_cpu_seconds if self.child else 0)
        if self.preparation["cpu_limit_scope"] == "inside_consumer_cpu_limit":
            total_cpu += self.preparation["known_cpu_seconds"]
        wall = time.monotonic() - self.started
        gpu = self.shared.get("gpu_child_microseconds") / 1e6 + self.current_gpu_child_seconds
        if total_cpu > self.limits["cpu_seconds"] or wall > self.limits["wall_seconds"] or gpu > self.limits["gpu_child_seconds"]:
            raise RuntimeError("actual consumer CPU/GPU-child/wall investment exhausted")
        now = time.monotonic()
        if sample_disk and (now - self.last_disk_time >= 2 or self.reserved + pending >= 8 * 1024 ** 2):
            self.disk_peak = max(self.disk_peak, old.allocated(self.roots))
            self.last_disk_time, self.reserved = now, 0
        if self.disk_peak + self.reserved + pending + 2 * 1024 ** 2 > self.limits["disk_bytes"]:
            raise RuntimeError("actual scoped consumer disk investment exhausted")
        self.reserved += pending

    def seal_counts(self, store):
        self.shared.flush()
        if "shared-counters.bin" in store.files:
            store.check("shared-counters.bin")
        else:
            store.register("shared-counters.bin")

    def snapshot(self):
        self.gpu_tick()
        usage = old.cpu()
        execution = usage["total_seconds"] + (self.prior_parent_cpu_seconds if self.child else 0)
        paid = self.preparation["known_cpu_seconds"]
        return {"counters": self.counter_snapshot(), "cpu": usage,
                "known_consumer_cpu_seconds_including_preparation": execution + paid,
                "cpu_seconds_charged_to_selected_limit": execution + (paid if self.preparation["cpu_limit_scope"] == "inside_consumer_cpu_limit" else 0),
                "wall_seconds": time.monotonic() - self.started,
                "gpu_phase_seconds": self.shared.get("gpu_reserved_microseconds") / 1e6,
                "gpu_child_seconds": self.shared.get("gpu_child_microseconds") / 1e6 + self.current_gpu_child_seconds,
                "disk_peak_allocated_bytes": self.disk_peak, "disk_roots": self.roots,
                "limits": self.limits, "gpu_cleanup_errors": list(self.gpu_cleanup_errors),
                "prior_bank_cost": self.deployment["prior_bank_cost"],
                "prior_preparation_cost": self.preparation,
                "support_cpu": "unmetered support unknown; not zero",
                "counter_semantics": "attempts before effect/completions after return; shared partials survive child exit; no bank rebuild"}


def count_complete(counts, cases):
    required = {"fits": 6, "fits_completed": 6, "updates": 24576, "updates_completed": 24576,
                "training_world_presentations": 786432, "training_candidate_presentations": 12582912,
                "training_completed_candidates": 12582912,
                "bank_worlds": 0, "label_rebuild_worlds": 0, "native_steps": 584000, "native_completed": 584000,
                "main_episodes": 1152, "audit_episodes": 16, "spawn_attempts": 1160, "spawn_completed": 1160,
                "reader_state_checks": 585168, "functional_contexts": 6144, "endpoint_contexts": 6144,
                "cold_contexts": 768, "engineering_contexts": 16, "hosts": 2464, "hosts_completed": 2464,
                "resets": 4784, "resets_completed": 4784, "raw_constructions": 1536, "raw_completed": 1536,
                "matching_calls": 2464, "matching_completed": 2464, "refused_effects": 0}
    if len(cases) != 1152 or any(counts[k] != value for k, value in required.items()):
        raise AssertionError("complete remaining scientific work/count mismatch")
    static = sum(case["selection_counts"]["static_calls"] for case in cases) + 1152 + 585168
    if counts["static_calls"] != static or counts["static_completed"] != static or static > 1383760:
        raise AssertionError("actual remaining static work mismatch; prior B05 is separate")
    for phase in old.ROW_PHASES:
        if counts[phase + "_candidate_presentations"] != counts[phase + "_completed_candidates"]:
            raise AssertionError("incomplete candidate attempt stream " + phase)
    if counts["all_candidate_presentations"] > 15471824:
        raise AssertionError("total candidate ceiling exceeded")
    if counts["all_candidate_presentations"] != sum(counts[p + "_candidate_presentations"] for p in old.ROW_PHASES):
        raise AssertionError("full padded candidate cost identity mismatch")
