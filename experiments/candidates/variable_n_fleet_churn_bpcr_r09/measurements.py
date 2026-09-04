"""Result-blind native throughput/RSS/storage measurement hooks."""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Sequence

from .contracts import canonical_json_bytes
from .native_backend import (
    NativeInteractiveBatch,
    run_native_bcrh_batch,
    run_native_episode_batch,
    run_native_fixture_batch,
)


def _rss_bytes() -> int:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[("cb",wintypes.DWORD),("PageFaultCount",wintypes.DWORD),("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t)]
        counters=Counters();counters.cb=ctypes.sizeof(Counters)
        kernel32=ctypes.WinDLL("kernel32",use_last_error=True)
        kernel32.GetCurrentProcess.argtypes=[];kernel32.GetCurrentProcess.restype=ctypes.c_void_p
        process=kernel32.GetCurrentProcess()
        psapi=ctypes.WinDLL("psapi",use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype=wintypes.BOOL
        if not psapi.GetProcessMemoryInfo(process,ctypes.byref(counters),counters.cb):
            raise OSError("GetProcessMemoryInfo failed")
        return int(counters.WorkingSetSize)
    import resource
    scale=1 if os.uname().sysname=="Darwin" else 1024
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*scale


def measure_native_conformance(fixtures: Sequence[object], *, kind: str) -> dict[str, object]:
    if kind not in ("interactive_episode", "episode", "bcrh_general", "bcrh_certificate") or not fixtures:
        raise ValueError("measurement requires a nonempty general/certificate fixture batch")
    rss_before=_rss_bytes();started=time.perf_counter()
    if kind=="interactive_episode":
        batch=NativeInteractiveBatch(fixtures)
        try:
            observations=tuple(row["next_observation"] for row in batch.initial)
            for _ in range(6):
                commands=tuple(fixture.post_commands[int(observation["epoch"])] for fixture,observation in zip(fixtures,observations))
                records=batch.step(commands);observations=tuple(row["next_observation"] for row in records)
        finally:batch.close()
    elif kind=="episode":records=run_native_episode_batch(fixtures)
    elif kind=="bcrh_general":records=run_native_bcrh_batch(fixtures)
    else:records=run_native_fixture_batch(fixtures)
    elapsed=time.perf_counter()-started;rss_after=_rss_bytes()
    # Values are digested and discarded: the hook reports implementation cost,
    # never a question-relevant endpoint or comparator result.
    encoded=canonical_json_bytes(records)
    return {"schema":"VNFC-BPCR-R09-RESULT-BLIND-MEASUREMENT-v1","kind":kind,"batch_width":len(fixtures),"elapsed_seconds":elapsed,"items_per_second":len(fixtures)/elapsed,"rss_before_bytes":rss_before,"rss_after_bytes":rss_after,"rss_delta_bytes":rss_after-rss_before,"canonical_uncompressed_bytes":len(encoded),"canonical_sha256":hashlib.sha256(encoded).hexdigest(),"question_relevant_values_retained":False}
