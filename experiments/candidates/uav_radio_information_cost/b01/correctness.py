"""Exactly two H8 integration streams and their complete pure offline reading."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_radio_uncertainty.b01.environment import make_env
from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from . import contract as c
from .collect import collect_episode, constructor_witness
from .io import write_json, save_evidence, artifact_bytes, resources, read_npz
from .metrics import outcomes
from .reader import verify_episode
from .read_native import verify_constructor


def run_correctness(out, launch_sha, admission, entry_started):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out / "started.json").open("x", encoding="utf-8") as stream:
        stream.write('{"check":"two package H8 streams,16 native steps"}\n')
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    counts = Counter(dict(new_reader_native_steps=0, new_reader_resets=0,
                          fits=0, optimizer_updates=0))
    summary = dict(status="CHECKING", launch_sha=launch_sha, admission=admission,
        constructor=None, rows=[], artifacts=[], reader_counts=counts,
        counts=dict(fits=0,optimizer_updates=0,native_steps=0,complete_episodes=0))
    env = None
    try:
        if np.__version__ != c.NUMPY_VERSION:
            raise RuntimeError("fixed NumPy version differs")
        summary["counts"]["constructor_attempts"] = 1
        env = make_env(c.FIXTURE_CONSTRUCTOR_SEED, horizon=8)
        summary["constructor"] = {}
        save_evidence(out/"raw"/"constructor.npz", constructor_witness(env),
                      summary["artifacts"], summary["constructor"])
        summary["constructor_reading"] = verify_constructor(read_npz(summary["constructor"]), counts)
        for arm in c.ARMS:
            raw, row, failure = collect_episode(env, c.FIXTURE_SEED, arm, horizon=8)
            summary["rows"].append(row)
            summary["counts"]["native_steps"] += row["steps"]
            summary["counts"]["complete_episodes"] += int(failure is None and row["steps"]==8)
            row["raw"] = {}
            save_evidence(out/"raw"/(arm+".npz"), raw, summary["artifacts"], row["raw"])
            if failure is not None:
                raise failure
            evidence = unpack_records(raw)
            row["outcome"], arrays = outcomes(raw, evidence["decisions"])
            row["outcome_arrays"] = {}
            save_evidence(out/"outcomes"/(arm+".npz"), arrays,
                          summary["artifacts"], row["outcome_arrays"])
            # The persisted bytes, including the absence of PRIOR sensor arrays,
            # are the input to the reader. No second native episode is created.
            row["reading"] = verify_episode(read_npz(row["raw"]), row,
                                           read_npz(row["outcome_arrays"]), counts)
            write_json(out/"progress.json",summary)
        assert summary["counts"]["native_steps"] == 16
        assert counts["reference_native_normal_values"] == 4750
        assert counts["reference_native_geometry_uniform_values"] == 345
        assert counts["reference_native_user_sinr_calls"] == 23
        assert counts["reference_current_c_calls"] == 40
        assert counts["reference_decisions"] == 4
        assert counts["reference_native_sensor_link_entries"] == 500
        assert counts["reference_native_pilot_slots"] == 100
        assert counts["reference_candidate_fleet_scores"] == sum(
            row["model_counts"].get("candidate_fleet_scores",0) for row in summary["rows"])
        assert counts["reference_model_normal_values"] == 0
        summary["status"] = "VERIFIED_COMPLETE"
    except Exception as exc:
        summary.update(status="INCOMPLETE_CORRECTNESS_FAILURE",
            error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        if env is not None:
            summary["physical_counts"] = env.env.physical_counters
            try:
                env.close()
            except Exception as exc:
                summary.update(status="INCOMPLETE_CORRECTNESS_FAILURE",
                               close_error=dict(type=type(exc).__name__,message=str(exc)))
        summary["resources"] = dict(resources(),wall_seconds=time.perf_counter()-entry_started,
                                    canonical_artifact_bytes=artifact_bytes(summary["artifacts"]))
        write_json(out/"summary.json",summary)
    return summary
