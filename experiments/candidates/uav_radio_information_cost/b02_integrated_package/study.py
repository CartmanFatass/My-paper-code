"""One complete fixed purchase, recording paid work before any reduction."""

from collections import Counter
from pathlib import Path
import platform
import time
import traceback

from . import dispatch
from .config import specification, expected_order, validate_rows
from .source import verify_sources
from .reductions import companions, paired, pair_actions
from experiments.candidates.uav_radio_uncertainty.b01.io import (
    write_json, save_evidence, read_npz, identity, artifact_bytes, resources,
)


def run_batch(out, launch_sha, admission, entry_started, kind="main"):
    if admission["sha"] != launch_sha:
        raise ValueError("admission/source mismatch")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    # An atomic exclusive claim prevents overwrite/retry of partial paid work.
    with (out/"started.json").open("x", encoding="utf-8") as stream:
        stream.write('{"study":"b02_integrated_package"}\n')
    if any((out/name).exists() for name in ("config.json","summary.json")):
        raise FileExistsError("existing B02 attempt")
    spec = specification(kind)
    result = dict(status="RUNNING", launch_sha=launch_sha, admission=admission,
        kind=kind, rows=[], artifacts=[], constructor=None, paired_actions=[],
        counts=dict(fits=0,optimizer_updates=0,training_episodes=0,
                    complete_episodes=0,native_steps=0,constructor_attempts=0))
    env = None
    try:
        bindings = verify_sources()
        config = dict(spec, launch_sha=launch_sha, source_bindings=bindings)
        write_json(out/"config.json", config)
        result["config"] = identity(out/"config.json")
        result["source_bindings"] = bindings
        import numpy as np
        import torch
        from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
        result["runtime"] = dict(python=platform.python_version(),numpy=np.__version__,
            torch=torch.__version__,host=platform.node())
        if np.__version__ != spec["numpy"]:
            raise RuntimeError("bound NumPy version differs")
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        result["counts"]["constructor_attempts"] = 1
        env = dispatch.module("U32_FULL","environment").make_env(
            spec["constructor_seed"], horizon=spec["horizon"])
        result["constructor"] = {}
        save_evidence(out/"raw"/"constructor.npz",
            dispatch.module("U32_FULL","collect").constructor_witness(env),
            result["artifacts"], result["constructor"])
        first_binding = None
        for program, world in expected_order(spec):
            result["current"] = dict(program=program,world=world)
            raw, row, failure = dispatch.collect(env,world,program,spec["horizon"])
            result["rows"].append(row)
            result["counts"]["native_steps"] += row["steps"]
            result["counts"]["complete_episodes"] += int(failure is None and row["steps"] == spec["horizon"])
            row["raw"] = {}
            save_evidence(out/"raw"/f"{program}_{world}.npz",raw,
                          result["artifacts"],row["raw"])
            if failure is not None:
                raise failure
            records = unpack_records(raw)["decisions"]
            row["outcome"], arrays = dispatch.outcomes(program,raw,records)
            row["outcome_arrays"] = {}
            save_evidence(out/"outcomes"/f"{program}_{world}.npz",arrays,
                          result["artifacts"],row["outcome_arrays"])
            # New reductions consume persisted bytes; no new scientific query.
            saved_raw, saved_arrays = read_npz(row["raw"]), read_npz(row["outcome_arrays"])
            row["companions"] = companions(saved_raw,saved_arrays,program)
            if first_binding is None:
                first_binding = row["raw"]
            else:
                result["paired_actions"].append(pair_actions(read_npz(first_binding),saved_raw))
                first_binding = None
            result["resources"] = dict(resources(),wall_seconds=time.perf_counter()-entry_started)
            write_json(out/"progress.json",dict(completed=len(result["rows"]),current=result["current"],resources=result["resources"]))
            write_json(out/"summary.json",result)
        validate_rows(result["rows"],spec)
        if first_binding is not None:
            raise ValueError("unpaired final episode")
        result["paired"] = paired(result["rows"],spec)
        result["status"] = "COMPLETE"
    except Exception as exc:
        result.update(status="INCOMPLETE_TECHNICAL_FAILURE",error=dict(
            type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        if env is not None:
            result["physical_counts"] = env.env.physical_counters
            try:
                env.close()
            except Exception as exc:
                result.update(status="INCOMPLETE_TECHNICAL_FAILURE",close_error=dict(type=type(exc).__name__,message=str(exc)))
        for key in ("model_counts","controller_counts"):
            total = Counter()
            for row in result["rows"]:
                total.update(row[key])
            result[key] = dict(total)
        result["resources"] = dict(resources(),wall_seconds=time.perf_counter()-entry_started,
            canonical_artifact_bytes=artifact_bytes(result["artifacts"]))
        write_json(out/"summary.json",result)
    return result


def run_check(out, launch_sha, admission, entry_started):
    worker = run_batch(out,launch_sha,admission,entry_started,kind="check")
    if worker["status"] != "COMPLETE":
        return worker
    from .reader import read_result
    summary = Path(out)/"summary.json"
    reading = read_result(summary,Path(out)/"read",identity(summary)["sha256"],
                          launch_sha,admission,entry_started,kind="check")
    write_json(Path(out)/"check.json",dict(status=reading["status"],
        worker_summary=identity(summary),reading=identity(Path(out)/"read"/"summary.json"),
        launch_sha=launch_sha,counts=worker["counts"],reader_counts=reading["counts"]))
    return reading
