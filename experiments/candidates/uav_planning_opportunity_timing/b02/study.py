"""One admitted 68-mission worker/full-reader operation with prefix retention."""
from copy import deepcopy
import os
import platform
import sys
import time
import traceback

import numpy as np
import torch

from experiments.candidates.uav_fleet_transmission.b02.host import make_env
from experiments.candidates.uav_fleet_transmission.b02.controller import KINDS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b02.study import COMPONENTS
from experiments.candidates.uav_fleet_transmission.b03.study import SNAPSHOTS
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.study import metrics
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.controller import TemporalProgram
from experiments.candidates.uav_planning_opportunity_timing.b01.controller import TimingProgram
from .controller import RollingProgram
from experiments.candidates.uav_planning_opportunity_timing.b01.evidence import EvidenceStore, compact_verified_segments, save_payload, write_catalog, write_trace
from .host import ALL_WORLD_IDS, AUDIT_WORLD, bound_worlds, seed
from .inputs import (ARMS, ROOT, RESOURCE_LIMITS, aggregate_costs, artifact, check_costs,
                     fixed_config, json_record, mission_order, same_array, same_record, write_json, episode_costs)
from .meter import Meter, allocated_bytes, resources

HISTORY_ARRAYS = ("history_positions", "history_commands", "history_users", "history_next_t")


def make_policy(arm, *, reuse, branch_sink=None, candidate_sink=None, segment_sink=None):
    if arm not in ARMS:
        raise ValueError("arm outside the selected four-arm purchase")
    cls = TemporalProgram if arm == "A2" else TimingProgram if arm == "A_E" else RollingProgram
    return cls(arm, 500, branch_sink, candidate_sink, reuse=reuse, segment_sink=segment_sink)


def evaluate_episode(arm, scene, phase, out, meter):
    start_wall, start_usage = time.monotonic(), resources()
    runtime_seed = seed(scene.world_id, 3, 8)
    raw_dir = out / "raw" / f"{phase}_n8_{arm}_w{scene.world_id}"
    raw_dir.mkdir(parents=True, exist_ok=False)
    store = EvidenceStore(out, raw_dir, meter)
    policy = make_policy(arm, reuse=True, branch_sink=store.branch_sink,
                         candidate_sink=store.candidate_sink, segment_sink=store.segment_sink)
    raw = {name: [] for name in (*SNAPSHOTS, *HISTORY_ARRAYS, "actions", "mask", "components", "scalar_reward", "terminal")}
    decisions, counts = [], empty_counts()
    calls, predictions = {kind: 0 for kind in KINDS}, 0
    timings = {"controller_and_branch_record_cpu_seconds": 0., "native_and_record_cpu_seconds": 0.,
               "environment_construction_cpu_seconds": 0., "explicit_reset_cpu_seconds": 0.}
    env = None
    complete = False
    try:
        meter.check()
        mark = time.process_time()
        env = make_env(scene, 500, runtime_seed)
        timings["environment_construction_cpu_seconds"] = time.process_time() - mark
        native = env.env.env
        mark = time.process_time()
        obs, info = env.reset(seed=runtime_seed)
        timings["explicit_reset_cpu_seconds"] = time.process_time() - mark
        state, old_mask = np.asarray(info["state"]), 255

        def snapshot():
            raw["positions"].append(native.uav_positions.copy())
            raw["observations"].append(np.asarray(obs).copy())
            raw["states"].append(state.copy())
            raw["sinr"].append(native.sinr_matrix.copy())
            raw["connections"].append(native.connections.copy())
            raw["peer_sinr"].append(native.uav_sinr_matrix.copy())
            raw["visible_users"].append([len(native._local_user_entries(i)[0][:20]) for i in range(8)])
            raw["visible_peers"].append([len(native._local_uav_entries(i)[0][:10]) for i in range(8)])

        snapshot()
        for t in range(500):
            meter.check()
            mark = time.process_time()
            command, new_mask, decision = policy.select(t, state if t % 10 == 0 else None, old_mask)
            if t % 10 and new_mask != old_mask:
                raise ValueError("mask changed between legal boundaries")
            trace_counts(decision, counts)
            for kind in KINDS:
                calls[kind] += int(kind in decision)
            predictions += 216 * int("motion" in decision)
            decisions.append(deepcopy(decision))
            for name, value in (("history_positions", policy.controller.positions),
                                ("history_commands", policy.controller.commands),
                                ("history_users", policy.controller.users),
                                ("history_next_t", policy.controller.next_t)):
                raw[name].append(np.asarray(value).copy())
            timings["controller_and_branch_record_cpu_seconds"] += time.process_time() - mark
            mark = time.process_time()
            if t % 10 == 0:
                native.set_transmitter_mask(mask_bits(new_mask, 8))
            raw["actions"].append(command.copy())
            raw["mask"].append(new_mask)
            obs, reward, terminated, truncated, info = env.step(command)
            state = np.asarray(info["next_state"])
            done = bool(terminated or truncated)
            if done != (t == 499):
                raise ValueError("native terminal differs from fixed H500")
            component = info["reward_components"]["reward_info"]
            raw["components"].append([float(component[name]) for name in COMPONENTS])
            raw["scalar_reward"].append(float(reward))
            raw["terminal"].append(done)
            old_mask = new_mask
            snapshot()
            timings["native_and_record_cpu_seconds"] += time.process_time() - mark
        complete = True
    finally:
        if env is not None:
            env.close()
        arrays = {name: np.asarray(values) for name, values in raw.items()}
        arrays["users"] = scene.user_positions.copy()
        native_path = raw_dir / "native.npz"
        with native_path.open("xb") as stream:
            np.savez_compressed(stream, **arrays)
        trace_path = raw_dir / "native.jsonl.gz"
        write_trace(trace_path, decisions)
        catalog = store.catalog(policy)
        catalog_path = raw_dir / "evidence.json.gz"
        write_catalog(catalog_path, catalog)
        # This exists for a failed cell as well, without claiming a complete outcome.
        write_json(raw_dir / "cell-status.json", {"phase": phase, "arm": arm, "world_id": scene.world_id,
            "complete": complete, "native_steps_retained": len(raw["terminal"]),
            "issued_decisions_retained": len(decisions), "model_branches_retained": len(store.branches),
            "segments_retained": len(store.segments), "banks_retained": len(store.banks),
            "resources_at_retention": resources()})
    end_usage = resources()
    timings.update(wall_seconds=time.monotonic() - start_wall,
                   cpu_seconds=end_usage["cpu_seconds"] - start_usage["cpu_seconds"])
    costs = episode_costs(catalog, counts, predictions)
    check_costs(costs, arm)
    work = [row["certificate"]["reuse"] for row in store.segments]
    logical = sum(row["logical_requested_candidates"] for row in work)
    actual = sum(row["actual_requested_candidates"] for row in work)
    reuse_costs = {"segment_logical_requests": logical, "segment_actual_requests": actual,
                  "computed_model_ticks": sum(row["computed_ticks"] for row in work),
                  "reused_model_ticks": sum(row["reused_ticks"] for row in work),
                  "worker_actual_requests": costs["worker_state_mask_requests"] - (logical - actual)}
    if reuse_costs["computed_model_ticks"] + reuse_costs["reused_model_ticks"] != costs["model_physical_transitions"]:
        raise ValueError("segment work and complete branch intervals disagree")
    meter.check(force_disk=True)
    return {"phase": phase, "arm": arm, "world_id": scene.world_id, "runtime_seed": runtime_seed,
            "n": 8, "steps": 500, "complete": True, "metrics": metrics(arrays, 8),
            "opportunity_times": sorted(policy.plans),
            "native_operation_counts": {"environment_factory_calls": 1, "explicit_resets": 1,
                                        "native_steps": 500, "retained_snapshots": 501},
            "native_candidate_counts": counts, "calls": calls, "position_predictions": predictions,
            "costs": costs, "reuse_costs": reuse_costs, "timing": timings,
            "raw": artifact(native_path, out), "decisions": artifact(trace_path, out),
            "evidence_catalog": artifact(catalog_path, out)}


def verify_prefixes(out, rows):
    """Already-paid native and first-search evidence; never another policy call."""
    from .inputs import checked_file, load_arrays, load_catalog, same_payload
    from experiments.candidates.uav_planning_opportunity_timing.b01.evidence import load_payload
    panel = {row["arm"]: row for row in rows}
    if set(panel) != set(ARMS) or len(rows) != 4:
        raise ValueError("incomplete matched prefix panel")
    arrays = {arm: load_arrays(checked_file(out, row["raw"])) for arm, row in panel.items()}
    for arm in ARMS[1:]:
        for name in arrays["A2"]:
            end = 41 if name in SNAPSHOTS else 40
            a, b = ((arrays["A2"][name], arrays[arm][name]) if name == "users"
                    else (arrays["A2"][name][:end], arrays[arm][name][:end]))
            same_array(a, b, f"all arms pre40 prefix/{arm}/{name}")
    end_t = panel["A_E"]["opportunity_times"][1]
    if panel["A_E4"]["opportunity_times"][1] != end_t:
        raise ValueError("A_E4/A_E actual second clocks differ")
    for name in arrays["A_E"]:
        end = end_t + 1 if name in SNAPSHOTS else end_t
        a, b = ((arrays["A_E"][name], arrays["A_E4"][name]) if name == "users"
                else (arrays["A_E"][name][:end], arrays["A_E4"][name][:end]))
        same_array(a, b, f"A_E4/A_E identical history through second input/{name}")
    cats = {arm: load_catalog(checked_file(out, panel[arm]["evidence_catalog"])) for arm in ARMS}
    same_record(cats["A_E"]["plans"]["40"], cats["A_E4"]["plans"]["40"], "identical first installed plan")
    same_record(cats["A_E"]["selections"]["40"], cats["A_E4"]["selections"]["40"], "identical first search record")
    for name in ("model_branches", "candidate_banks", "segments"):
        matched = {arm: [row for row in cats[arm][name] if row["id"].startswith("ae/first/")]
                   for arm in ("A_E", "A_E4")}
        left, right = matched["A_E"], matched["A_E4"]
        if not left or [row["id"] for row in left] != [row["id"] for row in right]:
            raise ValueError("first-search identity/order differs")
        for a, b in zip(left, right):
            if name == "candidate_banks":
                same_array(np.load(checked_file(out, a["raw"]), allow_pickle=False),
                           np.load(checked_file(out, b["raw"]), allow_pickle=False), "identical first candidate bank")
                same_record(cats["A_E"]["banks"][a["id"]], cats["A_E4"]["banks"][b["id"]], "first bank ledger")
            else:
                same_payload(load_payload(out, a), load_payload(out, b), "identical first model/segment payload")
                if name == "segments":
                    same_record(a["certificate"], b["certificate"], "identical first segment certificate")
    from .inputs import CONTRASTS
    programs = {}
    for a, b in CONTRASTS:
        def bits_equal(name):
            x, y = arrays[a][name], arrays[b][name]
            return x.shape == y.shape and x.dtype == y.dtype and x.tobytes() == y.tobytes()
        programs[a + "-" + b] = {"all_saved_native_arrays_bits_equal": all(bits_equal(k) for k in arrays[a]),
            "commands_bits_equal": bits_equal("actions"), "masks_bits_equal": bits_equal("mask"),
            "positions_bits_equal": bits_equal("positions"), "connections_bits_equal": bits_equal("connections"),
            "different_command_ticks": np.flatnonzero(np.any(arrays[a]["actions"] != arrays[b]["actions"], axis=(1, 2))).tolist(),
            "different_mask_ticks": np.flatnonzero(arrays[a]["mask"] != arrays[b]["mask"]).tolist()}
    choices = {arm: [{"ordinal": i + 1, "start_t": t, "initiated": bool(cats[arm]["plans"][str(t)]["initiated"]),
        "physical_identity": cats[arm]["selections"][str(t)]["selected_physical_identity"],
        "selected_branch": cats[arm]["selections"][str(t)]["selected_branch"],
        "member": cats[arm]["plans"][str(t)].get("member"),
        "commanded_arrival_t": cats[arm]["plans"][str(t)].get("arrival_t")}
        for i, t in enumerate(panel[arm]["opportunity_times"])] for arm in ARMS}
    return {"world_id": rows[0]["world_id"], "phase": rows[0]["phase"],
            "all_pre40_equal": True, "AE4_AE_native_prefix_equal_until_input_t": end_t,
            "AE4_AE_first_search_equal": True, "ID_mapping": "identity; ae/first denotes actual ordinal1",
            "program_comparisons": programs, "actual_choice_sequences": choices,
            "interpretation": "late stay is not a no-change gate; second selector already differs in A_E4"}


def run_study(args, admission, start_wall):
    from .reader import read_episode, summarize_reading, validate_worker
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    if any((out / name).exists() for name in ("summary.json", "config.json", "raw", "reading.json")):
        raise FileExistsError("existing scientific attempt; no replay/resume")
    config = dict(fixed_config(), launch_sha=args.launch_sha,
                  admission_command_sha256=admission["command_sha256"],
                  versions={"python": platform.python_version(), "python_executable": sys.executable,
                            "numpy": np.__version__, "torch": torch.__version__,
                            "torch_threads": torch.get_num_threads(), "torch_interop_threads": torch.get_num_interop_threads(),
                            "numerical_environment": {name: os.environ.get(name) for name in
                                ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}})
    write_json(out / "config.json", config)
    summary = {"launch_sha": args.launch_sha, "config": config, "config_artifact": artifact(out / "config.json", out),
               "status": "RUNNING", "worker_status": "incomplete", "reader_status": "incomplete",
               "episodes": [], "readings": [], "prefix_checks": [], "cleanup": [], "new_fits": 0, "updates": 0,
               "new_teacher_labels": 0}
    write_json(out / "summary.json", summary)
    meter = None
    try:
        meter = Meter(start_wall=start_wall, source=ROOT, out=out,
                      preparation_cpu=config["preparation"]["metered_cpu_seconds"], limits=RESOURCE_LIMITS)
        meter.arm()
        scenes = bound_worlds()
        order = mission_order()
        for first in range(0, len(order), 4):
            group = []
            for phase, world_id, arm in order[first:first + 4]:
                summary["current"] = {"phase": phase, "world_id": world_id, "arm": arm, "stage": "worker"}
                summary["resources"] = meter.record()
                write_json(out / "summary.json", summary)
                row = evaluate_episode(arm, scenes[world_id], phase, out, meter)
                summary["episodes"].append(row)
                group.append(row)
                summary["logical_worker_costs"] = aggregate_costs(summary["episodes"])
                write_json(out / "summary.json", summary)
            summary["prefix_checks"].append(verify_prefixes(out, group))
            for row in group:
                summary["current"] = {"phase": row["phase"], "world_id": row["world_id"],
                                      "arm": row["arm"], "stage": "full_reader"}
                write_json(out / "summary.json", summary)
                reading, catalog = read_episode(row, out, scenes[row["world_id"]], meter)
                summary["readings"].append(reading)
                before = allocated_bytes((out,))
                path = out / row["evidence_catalog"]["path"]
                cleanup = dict(world_id=row["world_id"], arm=row["arm"], phase=row["phase"])
                summary["cleanup"].append(cleanup)
                try:
                    compact_verified_segments(out, path, catalog, audit=cleanup)
                finally:
                    # Replacement references were published before any deletion.
                    # Retain their new binding even if an unlink/stop interrupted
                    # compaction, alongside the mutable partial-deletion ledger.
                    row["evidence_catalog"] = artifact(path, out)
                    reading["retained_evidence_catalog"] = row["evidence_catalog"]
                    cleanup["net_allocated_bytes_reclaimed"] = before - allocated_bytes((out,))
                meter.check(force_disk=True)
                summary["resources"] = meter.record()
                write_json(out / "summary.json", summary)
        summary["worker_status"] = "complete"
        summary["reader_status"] = "complete"
        validate_worker(summary, out)
        reading = summarize_reading(summary, out)
        write_json(out / "reading.json", reading)
        summary["reading"] = artifact(out / "reading.json", out)
        summary["status"] = "COMPLETE"
        summary.pop("current", None)
    except BaseException as error:
        if meter is not None:
            meter.close()
        summary["status"] = "FAILED_CLOSED"
        summary["failure"] = {"type": type(error).__name__, "message": str(error),
                              "traceback": traceback.format_exc(), "purchase_closed": True,
                              "missing_work_authorized": False}
        raise
    finally:
        if meter is not None:
            meter.close()
            summary["resources"] = meter.record(final=True)
        else:
            summary["resources_before_meter"] = resources()
        write_json(out / "summary.json", summary)
    return summary
