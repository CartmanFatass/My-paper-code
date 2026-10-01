"""Complete offline reading of the fixed worker, with no new native episode."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from . import contract as c
from . import protocol as p
from .io import read_npz,write_json,resources,identity
from .metrics import paired
from .read_model import verify_decision
from .read_native import verify_native,verify_constructor
from .read_outcomes import verify_c,verify_outcomes,verify_pairing,equal_tree


def verify_episode(raw,row,arrays,counts):
    native=verify_native(raw,counts)
    reconstructed=native.pop("reconstructed_observations")
    evidence=unpack_records(raw)
    assert evidence["failure_snapshot"] is None
    verify_c(raw,evidence,counts,reconstructed)
    sites=np.frombuffer(raw["map_packet"].tobytes(),dtype="<i4").reshape(50,2).astype(np.float64)
    model=Counter()
    for record in evidence["decisions"]:
        verify_decision(record,sites,counts)
        model.update(record["counts"])
    equal_tree(row["model_counts"],dict(model))
    equal_tree(row["physical_counts"],native["physical_counts"])
    equal_tree(row["controller_counts"],dict(zip(raw["controller_counter_names"].tolist(),
                                               raw["controller_counter_values"].sum(axis=0).tolist())))
    assert row["world"]==int(raw["world"]) and row["arm"]==str(raw["arm"]) and row["steps"]==int(raw["horizon"])
    assert row["failure"] is None
    verify_outcomes(raw,evidence["decisions"],row["outcome"],arrays,counts)
    return dict(native=native,model_counts=dict(model),raw=row.get("raw"))


def read_result(summary_path,out,expected_hash,expected_source,admission,entry_started):
    out,summary_path=Path(out).resolve(),Path(summary_path).resolve(strict=True)
    out.mkdir(parents=True,exist_ok=True)
    with (out/"started.json").open("x",encoding="utf-8") as stream:
        json.dump(dict(summary=str(summary_path),sha256=expected_hash,source=expected_source),stream)
    summary_bytes=summary_path.read_bytes()
    if hashlib.sha256(summary_bytes).hexdigest()!=expected_hash:
        raise ValueError("worker summary identity mismatch")
    worker=json.loads(summary_bytes)
    if worker["status"]!="COMPLETE" or worker["launch_sha"]!=expected_source:
        raise ValueError("complete bound worker required")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    counts=Counter(dict(new_environment_constructors=0,new_native_resets=0,new_native_steps=0,
                        fits=0,optimizer_updates=0))
    result=dict(status="READING",worker_summary=identity(summary_path),worker_source=expected_source,
        reader_source=admission["sha"],admission=admission,counts=counts,episodes=[],constructor=None)
    try:
        expected_order=[(arm,world) for world in c.WORLD_SEEDS for arm in c.arm_order(world)]
        assert [(row["arm"],row["world"]) for row in worker["rows"]]==expected_order
        equal_tree(worker["counts"],dict(fits=0,optimizer_updates=0,training_episodes=0,
                                        complete_episodes=64,native_steps=16384,constructor_attempts=1))
        ctor=read_npz(worker["constructor"])
        assert int(ctor["world"])==c.CONSTRUCTOR_SEED and int(ctor["horizon"])==256
        result["constructor"]=verify_constructor(ctor,counts)
        physical=Counter(result["constructor"]["physical_counts"])
        model,controller=Counter(),Counter()
        paired_initial={}
        for row in worker["rows"]:
            raw=read_npz(row["raw"])
            arrays=read_npz(row["outcome_arrays"])
            result["current"]=dict(arm=row["arm"],world=row["world"])
            assert int(raw["horizon"])==c.HORIZON
            digest=p.array_digest(raw["positions"][0],raw["users"],raw["residual"][0])
            previous=paired_initial.setdefault(row["world"],digest)
            assert previous==digest
            audit=verify_episode(raw,row,arrays,counts)
            result["episodes"].append(audit)
            physical.update(row["physical_counts"])
            model.update(row["model_counts"])
            controller.update(row["controller_counts"])
            result["resources"]=dict(resources(),wall_seconds=time.perf_counter()-entry_started)
            write_json(out/"progress.json",dict(complete=len(result["episodes"]),current=result["current"],
                                              counts=counts,resources=result["resources"]))
        equal_tree(worker["physical_counts"],dict(physical))
        equal_tree(worker["model_counts"],dict(model))
        equal_tree(worker["controller_counts"],dict(controller))
        # All rows were independently reduced above; pairing adds no RNG or physics.
        reduced=paired(worker["rows"])
        equal_tree(worker["paired"],reduced)
        verify_pairing(worker["rows"],reduced)
        assert counts["reference_current_c_calls"]==40960
        assert counts["reference_native_normal_values"]==4112250
        assert counts["reference_native_geometry_uniform_values"]==7475
        assert counts["reference_native_user_sinr_calls"]==20545
        assert counts["reference_decisions"]==4096
        assert counts["reference_candidate_fleet_scores"]==model["candidate_fleet_scores"]
        assert counts["reference_model_normal_values"]==model["model_normal_values"]
        result.update(status="VERIFIED_COMPLETE",paired=reduced,physical_counts=dict(physical),model_counts=dict(model))
    except Exception as exc:
        result.update(status="INCOMPLETE_READING_FAILURE",error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        result["resources"]=dict(resources(),wall_seconds=time.perf_counter()-entry_started)
        write_json(out/"reading.json",result)
    return result
