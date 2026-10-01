"""Complete independent per-episode reconstruction plus saved-array pairing."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import traceback

from . import dispatch
from .config import ARMS, specification, validate_rows
from .source import verify_sources
from .reductions import close_tree, verify_companions, pair_actions, verify_actions, paired, verify_pairing
from experiments.candidates.uav_radio_uncertainty.b01.io import (
    identity, read_npz, write_json, resources,
)


def _json_binding(binding, root):
    path = Path(binding["path"]).resolve(strict=True)
    if path.parent != root or path.is_symlink():
        raise ValueError("config path differs")
    actual = identity(path)
    if any(actual[k] != binding[k] for k in ("bytes","sha256")):
        raise ValueError("config byte binding differs")
    return json.loads(path.read_bytes())


def validate_worker(worker, spec, expected_source, bindings, root):
    if worker["status"] != "COMPLETE" or worker["launch_sha"] != expected_source or worker["kind"] != spec["kind"]:
        raise ValueError("complete bound worker required")
    close_tree(worker["source_bindings"],bindings)
    close_tree(_json_binding(worker["config"],root),
               dict(spec,launch_sha=expected_source,source_bindings=bindings))
    validate_rows(worker["rows"],spec)
    episodes = 2*len(spec["worlds"])
    close_tree(worker["counts"],dict(fits=0,optimizer_updates=0,training_episodes=0,
        complete_episodes=episodes,native_steps=episodes*spec["horizon"],constructor_attempts=1))
    expected = [worker["constructor"]] + [binding for row in worker["rows"]
        for binding in (row["raw"],row["outcome_arrays"])]
    close_tree(worker["artifacts"],expected)
    paths, inodes = set(), set()
    for binding in expected:
        path = Path(binding["path"])
        resolved = path.resolve(strict=True)
        if path.is_symlink() or root not in resolved.parents or binding["write_status"] != "complete":
            raise ValueError("incomplete or external artifact")
        stat = resolved.stat()
        inode = (stat.st_dev,stat.st_ino)
        if resolved in paths or inode in inodes:
            raise ValueError("aliased artifact")
        paths.add(resolved)
        inodes.add(inode)
    if len(worker["paired_actions"]) != len(spec["worlds"]):
        raise ValueError("paired action count differs")


def verify_exposure(counts, spec, model):
    h, episodes = spec["horizon"], 2*len(spec["worlds"])
    fixed = dict(reference_current_c_calls=episodes*(h//4)*10,
        reference_native_normal_values=(1+episodes*(h+1))*250,
        reference_native_geometry_uniform_values=(1+episodes)*115,
        reference_native_user_sinr_calls=1+episodes*(h+1+h//4),
        reference_decisions=episodes*(h//4),reference_native_constructors_verified=1,
        reference_native_episodes_verified=episodes,
        reference_native_sensor_link_entries=len(spec["worlds"])*(h//4)*250,
        reference_native_pilot_slots=len(spec["worlds"])*(h//4)*50,
        reference_user_age_updates=episodes*h*50)
    for key,value in fixed.items():
        if counts[key] != value:
            raise ValueError("reader exposure differs: "+key)
    for reference,actual in (("reference_candidate_fleet_scores","candidate_fleet_scores"),
                             ("reference_model_normal_values","model_normal_values")):
        if counts[reference] != model[actual]:
            raise ValueError("actual partial model work differs: "+actual)


def read_result(summary_path, out, expected_hash, expected_source, admission,
                entry_started, kind="main"):
    out, summary_path = Path(out).resolve(), Path(summary_path).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out/"started.json").open("x",encoding="utf-8") as stream:
        json.dump(dict(worker_summary=str(summary_path),sha256=expected_hash,source=expected_source),stream)
    if any((out/name).exists() for name in ("summary.json","reading.json")):
        raise FileExistsError("existing B02 reading")
    counts = Counter(dict(new_environment_constructors=0,new_native_resets=0,
                          new_native_steps=0,fits=0,optimizer_updates=0))
    result = dict(status="READING",worker_source=expected_source,
                  reader_source=admission["sha"],admission=admission,
                  counts=counts,episodes=[],constructor=None,kind=kind)
    try:
        bindings = verify_sources()
        data = summary_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected_hash:
            raise ValueError("worker summary identity mismatch")
        result["worker_summary"] = identity(summary_path)
        worker = json.loads(data)
        spec = specification(kind)
        validate_worker(worker,spec,expected_source,bindings,summary_path.parent)
        import numpy as np
        import torch
        if np.__version__ != spec["numpy"]:
            raise RuntimeError("bound reader NumPy differs")
        torch.set_num_threads(1)
        # check.py calls the reader in its existing process; avoid a second
        # irreversible set_num_interop_threads call after collection.
        if kind == "main":
            torch.set_num_interop_threads(1)
        ctor = read_npz(worker["constructor"])
        if int(ctor["world"]) != spec["constructor_seed"] or int(ctor["horizon"]) != spec["horizon"]:
            raise ValueError("constructor identity differs")
        result["constructor"] = dispatch.module("U32_FULL","read_native").verify_constructor(ctor,counts)
        physical = Counter(result["constructor"]["physical_counts"])
        model, controller = Counter(), Counter()
        first, pair_index = None, 0
        for row in worker["rows"]:
            program = row["program"]
            result["current"] = dict(program=program,world=row["world"])
            raw, arrays = read_npz(row["raw"]), read_npz(row["outcome_arrays"])
            if (int(raw["world"]) != row["world"] or int(raw["horizon"]) != spec["horizon"]
                    or str(raw["arm"]) != ARMS[program] or str(raw["program"]) != program):
                raise ValueError("saved episode identity differs")
            # Original verifier reconstructs initial/physical/radio states,
            # every actual particle candidate and both current-C passes.
            audit = dispatch.verify_episode(program,raw,row,arrays,counts)
            audit["program"] = program
            verify_companions(raw,arrays,program,row["companions"])
            result["episodes"].append(audit)
            physical.update(row["physical_counts"])
            model.update(row["model_counts"])
            controller.update(row["controller_counts"])
            if first is None:
                first = raw
            else:
                pair_actions(first,raw)
                verify_actions(first,raw,worker["paired_actions"][pair_index])
                pair_index += 1
                first = None
            write_json(out/"progress.json",dict(complete=len(result["episodes"]),
                current=result["current"],counts=counts,resources=dict(resources(),wall_seconds=time.perf_counter()-entry_started)))
        if first is not None or pair_index != len(spec["worlds"]):
            raise ValueError("incomplete paired read")
        for name,value in (("physical_counts",physical),("model_counts",model),("controller_counts",controller)):
            close_tree(worker[name],dict(value))
        verify_exposure(counts,spec,model)
        reduced = paired(worker["rows"],spec)
        close_tree(worker["paired"],reduced)
        verify_pairing(worker["rows"],spec,reduced)
        # Detect input changes while the lengthy full reconstruction ran.
        if identity(summary_path)["sha256"] != expected_hash:
            raise ValueError("worker summary changed during reading")
        result.update(status="VERIFIED_COMPLETE",paired=reduced,
            paired_actions=worker["paired_actions"],source_bindings=bindings,
            physical_counts=dict(physical),model_counts=dict(model),controller_counts=dict(controller))
    except Exception as exc:
        result.update(status="INCOMPLETE_READING_FAILURE",error=dict(
            type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        result["resources"] = dict(resources(),wall_seconds=time.perf_counter()-entry_started)
        write_json(out/"reading.json",result)
        write_json(out/"summary.json",result)
    return result
