"""Capped result-blind native construction benchmark for VQFP VNPA r03."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import time

from experiments.candidates.vqfp_vnpa_r03.contract import SCIENCE_CARD_SHA256
from experiments.candidates.vqfp_vnpa_r03.lifecycle import COMPETENCE_FIELDS, PrivateGeneration, WorkRange, input_identity
from experiments.candidates.vqfp_vnpa_r03.native_backend import artifact_identity, fixture_audit, synthetic_benchmark
from experiments.candidates.vqfp_vnpa_r03.reference_oracle import fixture_audit as reference_audit


def _rss() -> int:
    try:
        import psutil
        return int(psutil.Process().memory_info().rss)
    except Exception:
        try:
            import ctypes
            from ctypes import wintypes
            class Counters(ctypes.Structure):
                _fields_=[("cb",wintypes.DWORD),("PageFaultCount",wintypes.DWORD),
                          ("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),
                          ("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),
                          ("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),
                          ("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t)]
            counters=Counters();counters.cb=ctypes.sizeof(counters)
            kernel32=ctypes.WinDLL("kernel32",use_last_error=True);psapi=ctypes.WinDLL("psapi",use_last_error=True)
            kernel32.GetCurrentProcess.argtypes=[];kernel32.GetCurrentProcess.restype=wintypes.HANDLE
            psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
            psapi.GetProcessMemoryInfo.restype=wintypes.BOOL
            if psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
                return int(counters.WorkingSetSize)
        except Exception:
            pass
        return 0


def run() -> dict[str, object]:
    wall0=time.perf_counter();cpu0=time.process_time();rss0=_rss();native=fixture_audit();reference=reference_audit()
    if native!=reference:raise RuntimeError("native/reference exact fixture mismatch")
    measurements=[]
    for width in (8,32,64):
        w0=time.perf_counter();c0=time.process_time();stats=synthetic_benchmark(width=width,candidates=8,episodes=16,draws=64);elapsed=max(time.perf_counter()-w0,1e-9);cpu=max(time.process_time()-c0,1e-9)
        measurements.append({**stats,"wall_seconds":elapsed,"cpu_seconds":cpu,
                             "policy_cell_states_per_s":stats["policy_cell_states"]/elapsed,
                             "resample_blocks_per_s":stats["resample_blocks"]/elapsed})
    best=max(measurements,key=lambda x:x["policy_cell_states_per_s"])
    lifecycle0=time.perf_counter();lifecycle_cpu0=time.process_time()
    with tempfile.TemporaryDirectory(prefix="vqfp_r03_result_blind_") as temporary:
        generation=PrivateGeneration(temporary,input_identity(science_card_sha256=SCIENCE_CARD_SHA256),synthetic_test=True)
        ranges=(WorkRange("development",0,4),WorkRange("development",4,8))
        for index,work in enumerate(ranges):
            generation.commit_range(work,opaque_digest=(f"{index+1:064x}"),complete_count=4)
        first_missing=generation.first_missing("development",8)
        final=generation.publish_complete(expected_ranges=ranges,competence={field:True for field in COMPETENCE_FIELDS})
        lifecycle_bytes=sum(path.stat().st_size for path in Path(temporary).rglob("*") if path.is_file())
        assert final.is_file() and first_missing==8
    lifecycle_wall=time.perf_counter()-lifecycle0;lifecycle_cpu=time.process_time()-lifecycle_cpu0
    identity=artifact_identity();rss=max(rss0,_rss())
    return {"schema":"VQFP_VNPA_R03_RESULT_BLIND_CONSTRUCTION_BENCHMARK_V1",
            "native_reference_exact":True,"fixture_sha256":__import__("hashlib").sha256(native).hexdigest(),
            "measurements":measurements,"selected_width":best["width"],
            "lifecycle_measurement":{"wall_seconds":lifecycle_wall,"cpu_seconds":lifecycle_cpu,
                                     "durable_bytes_before_cleanup":lifecycle_bytes,"first_missing":first_missing},
            "exact_fallback_evidence":{"fixture_predicates":8,
                                       "integer_backend":"vendor-free signed arbitrary-width base-2^32",
                                       "fixed_width_fast_path":"certified uint64 quotient/remainder only",
                                       "all_rational_normalization_and_comparisons_arbitrary_width":True,
                                       "fallback_counter_available":False},
            "observed_dominant_bottleneck":"exact rational treatment/FREE/LR fixture kernel",
            "projection":None,
            "projection_status":"FULL_CHAIN_PROJECTION_UNAVAILABLE_MISSING_NATIVE_STAGES",
            "missing_measurement_seams":["accepted_host_bank","oracle","search_finalist_validation",
                                         "ten_arm_evaluation","state_stratified_episode_bootstrap",
                                         "J_R_composite_rank_terminal","native_serialization_resume",
                                         "parallel_worker_group_RSS","scratch_and_full_durable_IO"],
            "observed":{"wall_seconds":time.perf_counter()-wall0,"cpu_seconds":time.process_time()-cpu0,
                        "cpu_utilization_fraction":min((time.process_time()-cpu0)/max(time.perf_counter()-wall0,1e-9),1.0),
                        "rss_bytes":rss,"workers":1,"scratch_bytes":0,
                        "durable_bytes":Path(identity["artifact"]).stat().st_size+lifecycle_bytes},
            "artifact_identity":identity,"question_relevant_output":"none"}


def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--output")
    args=parser.parse_args();payload=run();encoded=json.dumps(payload,sort_keys=True,indent=2)
    if args.output:
        path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(encoded+"\n",encoding="utf-8")
    else:print(encoded)
    return 0


if __name__=="__main__":raise SystemExit(main())
