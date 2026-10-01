"""One fixed complete panel; no fits, pilots or outcome-selected continuation."""
from pathlib import Path
import platform
import resource
import time
import traceback
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from .assets import load_assets, verify_assets, verify_calibration
from .collect import collect_episode
from .contract import (CELLS, FROZEN, OBJECT, actor_for, cell_name, source_identities, write_json)
from .reading import comparisons


def _execute(out, launch_sha, *, protocol, models, records, env_factory, repo, admission,
             scientific_invocation, entry_wall=None, entry_cpu=None):
    if not scientific_invocation and (protocol == FROZEN or set(protocol.worlds) & set(FROZEN.worlds)):
        raise ValueError("synthetic fixture cannot use production worlds or protocol")
    protocol.validate()
    out, repo = Path(out), Path(repo)
    started_wall = time.perf_counter() if entry_wall is None else entry_wall
    started_cpu = time.process_time() if entry_cpu is None else entry_cpu
    if (out / "config.json").exists() or (out / "raw").exists():
        raise FileExistsError("refusing to repeat an existing worker")
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    config = dict(object=OBJECT, launch_sha=launch_sha, protocol=protocol.to_dict(), assets=records,
                  calibration=verify_calibration(repo) if scientific_invocation else {"fixture": True},
                  source_identities=source_identities(repo), admission=admission,
                  scientific_invocation=scientific_invocation, aliases={"Bstar_L1/H4": "S_L1/H4"},
                  runtime=dict(python=platform.python_version(), platform=platform.platform(),
                               numpy=np.__version__, torch=torch.__version__, torch_threads=torch.get_num_threads(),
                               torch_interop_threads=torch.get_num_interop_threads(),
                               deterministic_algorithms=torch.are_deterministic_algorithms_enabled()),
                  expected_exact=protocol.expected(), query_bounds=protocol.query_bounds(),
                  precision="CPU 1 thread; FP32 original actor/commands; FP64 scores/probabilities/native coordinates",
                  model_horizon="Original C/G four-tick forecast, including mission-end extrapolation; execution 1-4 ticks",
                  timing_scope="worker entry includes imports/assets; episode component timings are disjoint")
    write_json(out / "config.json", config)
    counts = {key: 0 for key in (*protocol.expected(), *protocol.query_bounds())}
    rows, inflight, env = [], {}, None
    summary = dict(state="STARTED", object=OBJECT, launch_sha=launch_sha, counts=counts, episodes=rows, inflight=inflight)
    try:
        verify_assets(models, records)
        counts["constructor_resets"] += 1
        env = env_factory(protocol.worlds[0])
        for wi, world in enumerate(protocol.worlds):
            for arm, mode, tape in protocol.episode_order(wi):
                row = collect_episode(env, arm=arm, mode=mode, world=world, tape=tape, protocol=protocol,
                                      actor=actor_for(arm, models), out=out, counts=counts, inflight=inflight)
                rows.append(row)
                write_json(out / "progress.json", dict(state="RUNNING", counts=counts,
                           last=dict(arm=arm, mode=mode, world=world, tape=tape), complete_episodes=len(rows)))
        protocol.check_counts(counts)
        for world in protocol.worlds:
            if len({r["initial_state_sha256"] for r in rows if r["world"] == world}) != 1:
                raise AssertionError("same-world initial states differ")
        verify_assets(models, records)
        summary.update(state="COMPLETE", paired=comparisons(rows, protocol),
                       policy_counts={cell_name(arm, mode): sum_counts(r["policy_counts"] for r in rows
                                      if r["arm"] == arm and r["mode"] == mode) for arm, mode in CELLS},
                       native_dense_power_slots=275 * (counts["native_steps"] + counts["explicit_resets"] + counts["constructor_resets"]))
    except BaseException as error:
        summary.update(state="FAILED", error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        if env is not None and hasattr(env, "close"):
            env.close()
        summary.update(worker_cpu_seconds=time.process_time() - started_cpu,
                       worker_wall_seconds=time.perf_counter() - started_wall,
                       process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(out / "summary.json", summary)
    return summary


def run_batch(out, launch_sha, *, admission, entry_wall, entry_cpu):
    if admission.get("sha") != launch_sha:
        raise ValueError("source identity must match admitted entry")
    repo = Path(__file__).resolve().parents[4]
    source_identities(repo)
    verify_calibration(repo)
    models, records = load_assets()
    from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
    return _execute(out, launch_sha, protocol=FROZEN, models=models, records=records, env_factory=make_real,
                    repo=repo, admission=admission, scientific_invocation=True,
                    entry_wall=entry_wall, entry_cpu=entry_cpu)
