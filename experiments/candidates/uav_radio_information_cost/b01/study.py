"""One fixed complete 32-world paired purchase; no automatic retry or resume."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import platform
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_user_waiting.b02.storage import unpack_records
from . import contract as c
from .collect import collect_episode,constructor_witness
from experiments.candidates.uav_radio_uncertainty.b01.environment import make_env
from .io import write_json,save_evidence,artifact_bytes,resources
from .metrics import outcomes,paired,paired_actions


def run_batch(out,launch_sha,admission,entry_started):
    out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=True)
    with (out/"started.json").open("x",encoding="utf-8") as stream:
        stream.write('{"study":"b01_pilot_package_a01"}\n')
    if any((out/name).exists() for name in ("config.json","summary.json")):
        raise FileExistsError("existing study; no implicit retry")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    summary=dict(status="RUNNING",launch_sha=launch_sha,admission=admission,rows=[],constructor=None,
        counts=dict(fits=0,optimizer_updates=0,training_episodes=0,complete_episodes=0,native_steps=0),
        runtime=dict(python=platform.python_version(),numpy=np.__version__,torch=torch.__version__,host=platform.node()),
        current=None,artifacts=[],paired_actions=[])
    config=dict(direction=c.DIRECTION,tag=c.TAG,launch_sha=launch_sha,worlds=list(c.WORLD_SEEDS),arms=list(c.ARMS),
        order=[list(c.arm_order(world)) for world in c.WORLD_SEEDS],horizon=c.HORIZON,constructor_seed=c.CONSTRUCTOR_SEED,
        physical_address=[c.PHYSICAL_NAMESPACE,c.PHYSICAL_ROOT,"world","state_tick"],
        model_address=None,numpy=c.NUMPY_VERSION,dependency_commit=c.DEPENDENCY_COMMIT,
        sigma_db=c.SIGMA_DB,correlation_metres=c.CORRELATION_METRES,
        packages={arm:c.arm_settings(arm) for arm in c.ARMS})
    write_json(out/"config.json",config)
    env=None
    try:
        if np.__version__!=c.NUMPY_VERSION:
            raise RuntimeError("bound NumPy version differs")
        summary["counts"]["constructor_attempts"]=1
        env=make_env(c.CONSTRUCTOR_SEED)
        summary["constructor"]={}
        save_evidence(out/"raw"/"constructor.npz",constructor_witness(env),summary["artifacts"],summary["constructor"])
        for world in c.WORLD_SEEDS:
            first_raw = None
            for arm in c.arm_order(world):
                summary["current"]=dict(world=world,arm=arm)
                raw,row,failure=collect_episode(env,world,arm)
                # Register all paid work before persistence or reduction can fail.
                summary["rows"].append(row)
                summary["counts"]["native_steps"]+=row["steps"]
                summary["counts"]["complete_episodes"]+=int(failure is None and row["steps"]==c.HORIZON)
                row["raw"]={}
                save_evidence(out/"raw"/f"{arm}_{world}.npz",raw,summary["artifacts"],row["raw"])
                if failure is not None:
                    raise failure
                evidence=unpack_records(raw)
                row["outcome"],arrays=outcomes(raw,evidence["decisions"])
                row["outcome_arrays"]={}
                save_evidence(out/"outcomes"/f"{arm}_{world}.npz",arrays,summary["artifacts"],row["outcome_arrays"])
                if first_raw is None:
                    first_raw = raw
                else:
                    summary["paired_actions"].append(paired_actions(first_raw,raw))
                summary["resources"]=dict(resources(),wall_seconds=time.perf_counter()-entry_started)
                write_json(out/"progress.json",dict(completed=len(summary["rows"]),current=summary["current"],resources=summary["resources"]))
                write_json(out/"summary.json",summary)
        summary["paired"]=paired(summary["rows"])
        summary["status"]="COMPLETE"
    except Exception as exc:
        summary.update(status="INCOMPLETE_TECHNICAL_FAILURE",error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    finally:
        if env is not None:
            summary["physical_counts"]=env.env.physical_counters
            try:
                env.close()
            except Exception as exc:
                summary["close_error"]=dict(type=type(exc).__name__,message=str(exc))
                summary["status"]="INCOMPLETE_TECHNICAL_FAILURE"
        model,controller=Counter(),Counter()
        for row in summary["rows"]:
            model.update(row["model_counts"])
            controller.update(row["controller_counts"])
        summary["model_counts"],summary["controller_counts"]=dict(model),dict(controller)
        summary["resources"]=dict(resources(),wall_seconds=time.perf_counter()-entry_started,
            canonical_artifact_bytes=artifact_bytes(summary["artifacts"]))
        write_json(out/"summary.json",summary)
    return summary
