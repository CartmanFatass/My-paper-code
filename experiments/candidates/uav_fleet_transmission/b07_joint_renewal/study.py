"""One fixed complete C/Q10 panel; no pilots, fits or outcome-based expansion."""
from pathlib import Path
import platform
import resource
import time
import traceback
import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from .collect import collect_episode
from .contract import CELLS, FROZEN, OBJECT, cell_name, source_identities, write_json
from .reading import comparisons


def _execute(out, launch_sha, *, protocol, env_factory, repo, admission, scientific_invocation,
             entry_wall=None, entry_cpu=None):
    if not scientific_invocation and (protocol == FROZEN or set(protocol.worlds) & set(FROZEN.worlds)):
        raise ValueError("synthetic fixture cannot use production worlds or protocol")
    if scientific_invocation and protocol != FROZEN:
        raise ValueError("production panel must use the frozen protocol")
    protocol.validate()
    out, repo = Path(out), Path(repo)
    started_wall = time.perf_counter() if entry_wall is None else entry_wall
    started_cpu = time.process_time() if entry_cpu is None else entry_cpu
    if (out / "config.json").exists() or (out / "raw").exists():
        raise FileExistsError("refusing to repeat an existing worker")
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    order = [dict(arm=arm, schedule=schedule, world=world, q=q, tape=tape)
             for wi, world in enumerate(protocol.worlds)
             for arm, schedule, q, tape in protocol.episode_order(wi)]
    config = dict(object=OBJECT, launch_sha=launch_sha, protocol=protocol.to_dict(),
                  source_identities=source_identities(repo), admission=admission,
                  scientific_invocation=scientific_invocation, processing_order=order,
                  phase_offsets={str(world): protocol.phase_offsets(world).tolist() for world in protocol.worlds},
                  runtime=dict(python=platform.python_version(), platform=platform.platform(), numpy=np.__version__,
                               torch=torch.__version__, torch_threads=torch.get_num_threads(),
                               torch_interop_threads=torch.get_num_interop_threads(),
                               deterministic_algorithms=torch.are_deterministic_algorithms_enabled()),
                  expected_exact=protocol.expected(), worker_uncached_ceiling=protocol.model_ceiling(),
                  reader_full_ceiling=protocol.model_ceiling(),
                  precision="CPU one thread; original FP32 commands/features; FP64 scores/probabilities/native coordinates",
                  model_horizon="Original C four-tick forecast, including mission-end extrapolation; execution1-7 ticks",
                  timing_scope="worker entry includes imports/initialization; episode component timings are disjoint",
                  new_fits=0, training_assets=[], physical_clock_energy_measured=False)
    write_json(out / "config.json", config)
    counts = {key: 0 for key in protocol.expected()}
    rows, inflight, env = [], {}, None
    summary = dict(state="STARTED", object=OBJECT, launch_sha=launch_sha, counts=counts, episodes=rows, inflight=inflight)
    try:
        counts["constructor_resets"] += 1
        env = env_factory(protocol.worlds[0])
        for cell in order:
            row = collect_episode(env, **cell, protocol=protocol, out=out, counts=counts, inflight=inflight)
            rows.append(row)
            write_json(out / "progress.json", dict(state="RUNNING", counts=counts,
                       last=cell, complete_episodes=len(rows)))
        protocol.check_counts(counts)
        for world in protocol.worlds:
            if len({row["initial_state_sha256"] for row in rows if row["world"] == world}) != 1:
                raise AssertionError("same-world initial states differ")
        summary.update(state="COMPLETE", paired=comparisons(rows, protocol),
                       policy_counts={cell_name(arm, schedule): sum_counts(row["policy_counts"] for row in rows
                                      if row["arm"] == arm and row["schedule"] == schedule) for arm, schedule in CELLS},
                       native_dense_power_slots=275 * (counts["native_steps"] + counts["explicit_resets"]
                                                       + counts["constructor_resets"]))
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
        write_json(out / "progress.json", dict(state=summary["state"], counts=counts, complete_episodes=len(rows)))
    return summary


def run_batch(out, launch_sha, *, admission, entry_wall, entry_cpu):
    if admission.get("sha") != launch_sha:
        raise ValueError("source identity must match admitted entry")
    repo = Path(__file__).resolve().parents[4]
    source_identities(repo)
    from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
    return _execute(out, launch_sha, protocol=FROZEN, env_factory=make_real, repo=repo,
                    admission=admission, scientific_invocation=True, entry_wall=entry_wall, entry_cpu=entry_cpu)
