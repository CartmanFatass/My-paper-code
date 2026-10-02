"""One real-observation E/B replay plus independent recorded-table/native checks."""
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
from itertools import permutations
import json
import multiprocessing
from pathlib import Path
import time
import traceback
import numpy as np
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import reader as original
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.reader import (
    UnavailableTruth, numeric_row_equal, check_native, check_partial_native,
    compare_records, change_reading, first_difference, children_cpu,
    apply_feedback_params, PRODUCTION_PARAMS, own_positions, own_energy, station_counts,
    world_row, mechanism_row, absolute_station_xy, position_diagnostics,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.budget import execute_budgeted, check_worker_stop
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import CANDIDATE_DTYPE as OLD_DTYPE
from .capture import plan_record
from .contract import (ARMS, CONTRASTS, HORIZON, OBJECT, array_digest, equal, expected_counts,
    identity, jobs, source_binding, sum_counts, telemetry, write_json, reference_evidence)
from .controller import ReplayBoundary, make_controller
from .metrics import comparisons, episode_metrics


def check_assignment_contract(raw, arm):
    """Rank recorded criteria independently: no new flight/RF/policy query."""
    ordinary_view = dict(raw, candidate_records=np.empty(0, dtype=OLD_DTYPE),
                         plan_targets=raw["plan_ordinary_targets"])
    original.check_assignment_contract(ordinary_view, "C")
    records = raw["candidate_records"]
    for k, tick in enumerate(raw["plan_step"]):
        ordinary = raw["plan_ordinary_targets"][k]
        eligible = raw["plan_eligible"][k]
        uavs = np.flatnonzero(eligible)
        m = len(uavs)
        equal(raw["plan_m"][k], m, "actual service-member count")
        equal(raw["plan_eligible_uavs"][k], np.pad(uavs, (0, 6-m), constant_values=-1), "eligible row order")
        columns = np.sort(raw["plan_assignment_column"][k, uavs])
        base_columns = raw["plan_assignment_column"][k, uavs]
        equal(raw["plan_target_columns"][k], np.pad(columns, (0, 6-m), constant_values=-1), "original target labels")
        equal(raw["plan_base_columns"][k], np.pad(base_columns, (0, 6-m), constant_values=-1), "actual C base labels")
        group = records[records["step"] == tick]
        edges = raw["edge_records"][raw["edge_records"]["step"] == tick]
        returns = raw["return_records"][raw["return_records"]["step"] == tick]
        equal(raw["plan_fallback"][k], int(m < 2), "sparse-only fallback")
        if m < 2:
            if len(group) or len(edges) or len(returns):
                raise AssertionError("analytical work on sparse C fallback")
            equal(raw["plan_targets"][k], ordinary, "fallback actual C targets")
            continue
        menu = list(permutations(map(int, columns)))
        base = menu.index(tuple(map(int, base_columns)))
        equal(len(group), len(menu), "full and only m-factorial menu")
        equal(raw["plan_candidate_count"][k], len(menu), "captured menu count")
        equal(raw["plan_base_index"][k], base, "actual base index")
        equal(len(edges), m*m, "one cached flight/slack edge per pair")
        equal(len(returns), m, "one cached return per destination")
        for table in (group, edges, returns):
            if not table["started"].all() or not table["completed"].all():
                raise AssertionError("incomplete row inside complete captured plan")
        for index, (record, perm) in enumerate(zip(group, menu)):
            equal(record["index"], index, "literal permutation index")
            equal(record["m"], m, "candidate member count")
            equal(record["columns"], np.pad(perm, (0, 6-m), constant_values=-1), "complete ordered column tuple")
            if not np.isfinite(record["energy"]) or not np.isfinite(record["slacks"][:m]).all():
                raise AssertionError("nonfinite ranked values")
            if not np.isnan(record["slacks"][m:]).all() or np.any(np.diff(record["slacks"][:m]) < 0):
                raise AssertionError("sorted slack vector or padding differs")
        # The saved complete criteria were separately recomputed by the one replay.
        # This scan independently applies the complete ordering, without recomputing edges/criteria.
        tail = lambda j: (float(group[j]["energy"]), j != base, menu[j])
        if arm == "E":
            winner = min(range(len(menu)), key=tail)
        else:
            maximum = max(tuple(row["slacks"][:m]) for row in group)
            top = [j for j in range(len(menu)) if tuple(group[j]["slacks"][:m]) == maximum]
            winner = min(top, key=tail)
        equal(raw["plan_selected_candidate"][k], winner, "independent exact full-criterion winner")
        equal(np.flatnonzero(group["selected"]), [winner], "one actual selected row")
        equal(raw["plan_selected_columns"][k], group[winner]["columns"], "selected provenance")
        target = ordinary.copy()
        target[uavs] = raw["plan_priority"][k, np.asarray(menu[winner])]
        equal(raw["plan_targets"][k], target, "actual committed labelled targets")
        equal(raw["plan_selected_alias"][k], bool(winner != base and
              np.array_equal(target, ordinary, equal_nan=True)), "selected coordinate alias")
        equal(raw["plan_targets"][k, ~eligible], ordinary[~eligible], "noneligible relay/ring/NaN preserved")


def compare_audit_prefix(actual, recorded, complete):
    for name in ("candidate_records", "edge_records", "return_records"):
        a, b = actual[name], recorded[name]
        if a.shape != b.shape or a.dtype != b.dtype:
            raise AssertionError(name + " recorded prefix shape/dtype")
        for index, (left, right) in enumerate(zip(a, b)):
            if complete or right["completed"]:
                equal(left, right, name + "/" + str(index))
            else:
                # An interrupted computation has no completed answer to reconstruct.
                for field in ("step", "index", "m"):
                    equal(left[field], right[field], name + "/interrupted-identity/" + field)
                if left["completed"] or left["started"]:
                    raise AssertionError("reader executed an unfinished recorded effect")


def check_public_parameters(row):
    expected = dict(time_step=1., max_speed=30., max_vertical_speed_mps=5.,
        battery_capacity_wh=160., return_reserve_ratio=.10, limp_home_speed_mps=3.,
        P0=79.86, Pi=88.63, v0=4.03, k1=3/120**2, k2=1/(2*4.03**2),
        k3=.5*.6*1.225*.05*.503, P_z_coeff=15.)
    for name, value in expected.items():
        equal(row["native_parameters"][name], value, "frozen public law/" + name)


def replay_episode(raw, row, phase, progress=None):
    complete = row.get("status") == "completed"
    arm = row["arm"]
    n = int(row["actual_length"] if complete else raw["recorded_decision_steps"])
    controller = make_controller(arm)
    controller.reset()
    controller.set_replay_prefix(raw)
    modes, previous_done = np.zeros(8, dtype=bool), np.ones(1, dtype=bool)
    verified = attempts = shield_attempts = plan_index = 0
    boundary = None
    missing = set()

    def saved(name, index, value):
        if name not in raw:
            if complete:
                raise AssertionError("missing saved field: " + name)
            missing.add(name)
            return
        equal(raw[name][index], value, "actual replay/" + name)

    try:
        for tick in range(n):
            obs = raw["observations"][tick]
            attempts += 1
            proposal = controller.propose(obs, UnavailableTruth(), tick, previous_done, modes.copy())
            saved("proposed", tick, proposal)
            saved("target_xy", tick, controller.targets_xy)
            xyz = np.column_stack((controller.heuristic.targets_xy, np.full(8, 100.0)))
            saved("decision_targets_xyz", tick, xyz)
            shield_attempts += 1
            decision = apply_feedback_params(obs, proposal, modes, PRODUCTION_PARAMS)
            for name, value in dict(submitted=decision.submitted_actions, mode=decision.modes,
                entered=decision.entered, exited=decision.exited, return_margin=decision.margins,
                nearest_station=decision.selected_stations, nearest_station_distance_m=decision.station_distances_m).items():
                saved(name, tick, value)
            saved("own_xyz", tick, own_positions(obs))
            held = own_energy(obs)
            saved("station_occupancy", tick, station_counts(decision.selected_stations, held["charging"]))
            saved("station_queue", tick, station_counts(decision.selected_stations, held["waiting_steps"] > 0))
            post = own_energy(raw["observations"][tick + 1])
            for name in ("charging", "waiting_steps", "battery"):
                saved(name, tick, post[name])
            saved("dock_bit", tick, decision.submitted_actions[:, 3] > .5)
            if tick % 30 == 0:
                compare_records(raw, plan_record(controller, tick), plan_index, "actual E/B plan")
                plan_index += 1
            modes = decision.modes
            previous_done[:] = raw.get("ends", raw["native_ends"])[tick].any()
            verified += 1
            if progress is not None and verified % 100 == 0:
                progress(dict(verified=verified, policy_counts=controller.counters, shield_calls=shield_attempts))
        inflight = not complete and any(np.any(raw[key]["step"] == n)
            for key in ("candidate_records", "edge_records", "return_records"))
        if inflight:
            attempts += 1
            try:
                proposal = controller.propose(raw["observations"][n], UnavailableTruth(), n,
                    previous_done, modes.copy())
            except ReplayBoundary as error:
                boundary = str(error)
            else:
                if int(raw["recorded_native_steps"]) > n:
                    shield_attempts += 1
                    decision = apply_feedback_params(raw["observations"][n], proposal, modes, PRODUCTION_PARAMS)
                    equal(decision.submitted_actions, raw["submitted"][n], "inflight submitted action")
        compare_audit_prefix(controller.audit_arrays(), raw, complete)
        equal(plan_index, len(raw.get("plan_step", [])), "all actual captured plans")
        counts = controller.counters
        if complete:
            check_public_parameters(row)
            if any(counts.get(k, 0) != v for k, v in expected_counts(arm, n).items()):
                raise AssertionError("replay primitive clock/count mismatch")
            if counts != row["policy_counts"]:
                raise AssertionError("actual worker/reader analytical counters differ")
            reduced = world_row(row["seed"], raw["reward"], raw["metrics"], raw["ends"], raw, time_step_s=1.)
            reduced.update(mechanism_row(raw, absolute_station_xy(raw["observations"][0])))
            reduced.update(position_diagnostics(raw["metrics"], raw, area_size_m=8000., floor_m=50.))
            numeric_row_equal(row, reduced, "original full evaluator reduction")
            numeric_row_equal(row, episode_metrics(raw), "independent E/B native/criterion reduction")
        deployment = row.get("policy_counts") or {}
        omitted = {k: int(v)-int(counts.get(k, 0)) for k, v in deployment.items() if int(v) != int(counts.get(k, 0))}
        if not complete and any(v < 0 for v in omitted.values()):
            raise AssertionError("partial reader exceeded recorded attempts")
        return dict(status="verified" if complete else "partial-prefix-verified", policy_counts=counts,
            deployment_attempted_counts=deployment, unreplayed_attempted_or_uncertain_counts=omitted,
            verified_actual_proposals=verified, verified_feedback_calls=verified, shield_calls=shield_attempts,
            inflight_proposals_replayed=attempts-verified, replay_boundary=boundary,
            candidate_records_checked=len(raw["candidate_records"]),
            edge_records_checked=len(raw["edge_records"]), return_records_checked=len(raw["return_records"]),
            missing_saved_decision_fields=sorted(missing), new_native_steps=0,
            ranking_scope="exact on complete plans; interrupted flags and unknown outputs remain unverified")
    finally:
        if progress is not None:
            progress(dict(verified=verified, attempted_calls=attempts, policy_counts=controller.counters,
                          shield_calls=shield_attempts, replay_boundary=boundary))
        controller.close()


def read_world(payload):
    job,rows,out_string,phase,reference_root=payload
    out=Path(out_string)
    wall,cpu=time.perf_counter(),time.process_time()
    checked,reference_checked,trajectories=[],[],{}
    native_checks = []
    state={}
    progress_path=out/"reading_raw"/(str(job["seed"])+".progress.json")

    def progress(value):
        state.update(value)
        write_json(progress_path,dict(**job,status="running",**state))
        check_worker_stop(out)

    def load_raw(folder,row,artifact):
        path=(folder/artifact["path"]).resolve()
        if not path.is_relative_to((folder/"raw").resolve()):
            raise AssertionError("raw path escaped canonical evidence")
        found=identity(path)
        if any(found[k]!=artifact[k] for k in ("sha256","bytes")):
            raise AssertionError("raw identity differs")
        with np.load(path,allow_pickle=False) as archive:
            return {key:archive[key] for key in archive.files}

    def retain_trajectory(arm,raw):
        names=("truth_user_xyz","truth_uav_xyz","truth_bs_xyz","truth_station_xyz",
               "submitted","proposed","decision_targets_xyz")
        trajectories[arm]={key:raw[key].copy() for key in names}
        trajectories[arm]["initial_observations"]=raw["observations"][0].copy()

    def native_check(raw, row, *, complete, reference=False):
        # Preserve completed public-law reading even if a later replay/reduction
        # fails. An interrupted vector check is an unknown prefix, never zero.
        item = dict(arm=row["arm"], reference=reference, status="started",
                    recorded_motion_power_rows_upper_bound=8*int(row["actual_length"]) if complete else 0)
        native_checks.append(item)
        progress(dict(native_checks=native_checks))
        result = check_native(raw,row,phase) if complete else check_partial_native(raw,row)
        item.update(status="completed", **result)
        progress(dict(native_checks=native_checks))
        return result

    try:
        import torch
        torch.set_num_threads(1)
        for row in rows:
            state=dict(arm=row["arm"],verified=0)
            complete=row.get("status")=="completed"
            artifact=row.get("raw") if complete else row.get("partial",row.get("incomplete_raw"))
            if artifact is None:
                checked.append(dict(arm=row["arm"],seed=row["seed"],native=None,
                    replay=dict(status="unverifiable-no-saved-input",policy_counts={},
                        deployment_attempted_counts=row.get("policy_counts") or {},
                        unreplayed_attempted_or_uncertain_counts=row.get("policy_counts") or {},
                        verified_actual_proposals=0,verified_feedback_calls=0,
                        new_native_steps=0)))
                continue
            raw=load_raw(out,row,artifact)
            native=native_check(raw,row,complete=complete)
            if complete:
                check_assignment_contract(raw,row["arm"])
            replay=replay_episode(raw,row,phase,progress)
            checked.append(dict(arm=row["arm"],seed=row["seed"],native=native,replay=replay))
            state={}
            if complete:
                retain_trajectory(row["arm"],raw)
            del raw
        # Already byte-bound by parent; this call reads compact identities, then this
        # world verifies/reduces its three original C/H_A/H_T records. No replay.
        reference=reference_evidence(reference_root,phase,verify_raw=False,verify_sources=False)
        reference_rows=[r for r in reference["rows"] if r["seed"]==job["seed"]]
        for row in reference_rows:
            check_worker_stop(out)
            raw=load_raw(Path(row["reference_directory"]),row,row["raw"])
            native=native_check(raw,row,complete=True,reference=True)
            numeric_row_equal(row,original.episode_metrics(raw),"frozen reference native reductions")
            reference_checked.append(dict(seed=row["seed"],arm=row["arm"],raw=row["raw"],native=native,
                source_sha=row["reference_source_sha"],controller_replays=0,model_queries=0,new_native_steps=0))
            retain_trajectory(row["arm"],raw)
            del raw
        pairs=[]
        combined={(r["seed"],r["arm"]):r for r in rows+reference_rows}
        for left,right in CONTRASTS:
            if left not in trajectories or right not in trajectories:
                continue
            a,b=trajectories[left],trajectories[right]
            prefix=min(len(a["truth_user_xyz"]),len(b["truth_user_xyz"]))
            equal(a["truth_user_xyz"][:prefix],b["truth_user_xyz"][:prefix],"full common-prefix users")
            for name in ("truth_uav_xyz","truth_bs_xyz","truth_station_xyz"):
                equal(a[name][0],b[name][0],"common reset: "+name)
            equal(a["initial_observations"],b["initial_observations"],"common reset observations")
            user_left=np.asarray(combined[job["seed"],left]["individual_service"]["cumulative_qos_seconds"])
            user_right=np.asarray(combined[job["seed"],right]["individual_service"]["cumulative_qos_seconds"])
            delta=user_left-user_right
            pairs.append(dict(contrast=left+"-"+right,observed_common_boundaries=prefix,
                first_position_divergence_boundary=first_difference(a["truth_uav_xyz"][:prefix],b["truth_uav_xyz"][:prefix]),
                first_proposal_divergence_tick=first_difference(a["proposed"][:prefix-1],b["proposed"][:prefix-1]),
                first_submitted_divergence_tick=first_difference(a["submitted"][:prefix-1],b["submitted"][:prefix-1]),
                target_xyz_changes=change_reading(a["decision_targets_xyz"],b["decision_targets_xyz"]),
                proposed_changes=change_reading(a["proposed"],b["proposed"]),
                submitted_changes=change_reading(a["submitted"],b["submitted"]),
                physical_xyz_changes=change_reading(a["truth_uav_xyz"],b["truth_uav_xyz"]),
                user_path_sha256=array_digest(a["truth_user_xyz"][:prefix]),
                individual_qos_seconds_delta=delta.tolist(),better_users=int((delta>0).sum()),
                worse_users=int((delta<0).sum()),equal_users=int((delta==0).sum())))
        complete=all(r.get("status")=="completed" for r in rows)
        result=dict(**job,status="completed" if complete else "partial",episodes=checked,
            native_checks=native_checks,
            reference_episodes=reference_checked,common_prefix_pairs=pairs,
            frozen_reference_verified=len(reference_checked)==3,
            **{"reader_worker_"+k:v for k,v in telemetry(wall,cpu).items()})
        write_json(progress_path,dict(**job,status=result["status"],episodes=len(checked),reference_episodes=len(reference_checked)))
        return result
    except BaseException as error:
        result=dict(**job,status="failed",error=repr(error),traceback=traceback.format_exc(),
            episodes=checked,reference_episodes=reference_checked,inflight=state,native_checks=native_checks,
            **{"reader_worker_"+k:v for k,v in telemetry(wall,cpu).items()})
        write_json(progress_path,result)
        return result


def read_result(out, workers, budget):
    out = Path(out)
    if workers not in (1, 2) or any((out / name).exists() for name in ("reading.json", "reading_worlds.json", "reading_raw")):
        raise ValueError("invalid worker count or a reader was already started; no automatic replay")
    wall, cpu, child_cpu = time.perf_counter(), time.process_time(), children_cpu()
    config = json.loads((out / "config.json").read_text())
    summary = json.loads((out / "summary.json").read_text())
    rows = json.loads((out / "perworld.json").read_text())
    phase = config["phase"]
    reference=reference_evidence(config["frozen_reference"]["root"],phase)
    if {k:v for k,v in reference.items() if k!="rows"}!=config["frozen_reference"]:
        raise AssertionError("reference evidence changed since native input check")
    if config["object"] != OBJECT or summary["object"] != OBJECT or config["jobs"] != jobs(phase):
        raise AssertionError("unfrozen panel")
    if summary["status"] not in ("complete", "incomplete") or summary["launch_sha"] != config["launch_sha"]:
        raise AssertionError("native summary status/source binding")
    if config["source_binding"] != source_binding():
        raise AssertionError("reader source differs from native input binding")
    expected_jobs = jobs(phase)
    declared = {job["job_key"]: job for job in expected_jobs}
    keys = [row["job_key"] for row in rows]
    if len(set(keys)) != len(keys) or any(key not in declared for key in keys):
        raise AssertionError("undeclared or duplicate actual job")
    equal(keys, [job["job_key"] for job in expected_jobs if job["job_key"] in keys], "logical actual world/arm order")
    for row in rows:
        if {key: row[key] for key in ("job_key", "seed", "arm", "limit")} != declared[row["job_key"]]:
            raise AssertionError("native row differs from declared job")
        if row.get("status") not in ("completed", "failed", "cancelled", "unreconciled"):
            raise AssertionError("unknown actual episode status")
    if summary["status"] == "complete" and (keys != [job["job_key"] for job in expected_jobs]
                                            or any(row["status"] != "completed" for row in rows)):
        raise AssertionError("incomplete reported complete panel")
    manifest = json.loads((out / "manifest.json").read_text())
    if manifest["object"] != OBJECT or manifest["launch_sha"] != config["launch_sha"]:
        raise AssertionError("manifest source/object identity differs")
    for name, expected in (manifest["artifacts"] | manifest["raw"]).items():
        path = (out / name).resolve()
        if not path.is_relative_to(out.resolve()):
            raise AssertionError("manifest path escaped output")
        actual = identity(path)
        if any(actual[key] != expected[key] for key in ("sha256", "bytes")):
            raise AssertionError("saved artifact changed: " + name)
    raw_files = {str(path.relative_to(out)) for path in (out / "raw").iterdir()}
    if raw_files != set(manifest["raw"]):
        raise AssertionError("unexpected or missing native raw artifact")
    unreported_evidence = []
    for job in expected_jobs:
        if job["job_key"] in keys:
            continue
        stem = job["job_key"].replace("/", "_")
        progress_path = out / "raw" / (stem + ".progress.json")
        item = dict(**job, replay_status="not-replayed-no-authoritative-episode-row",
                    raw_artifacts={name: value for name, value in manifest["raw"].items()
                                   if name in (f"raw/{stem}.npz", f"raw/{stem}.partial.npz")})
        if progress_path.exists():
            saved_progress = json.loads(progress_path.read_text())
            if any(saved_progress.get(key) != job[key] for key in ("job_key", "seed", "arm", "limit")):
                raise AssertionError("unreported progress job binding differs")
            item.update(last_preserved_progress=saved_progress,
                        known_attempted_count_lower_bound=saved_progress.get("policy_counts") or {},
                        count_scope="last preserved progress; later missing attempts remain unknown")
        else:
            item.update(known_attempted_count_lower_bound={}, count_scope="no attempt count evidence")
        unreported_evidence.append(item)
    (out / "reading_raw").mkdir()
    worlds = sorted({row["seed"] for row in rows})
    plan = [dict(job_key=str(seed), seed=seed) for seed in worlds]
    results, submitted = [], []

    def on_result(result):
        results.append(result)
        results.sort(key=lambda item: item["seed"])
        write_json(out / "reading_worlds.json", results)

    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as pool:
        _, errors = execute_budgeted(pool, plan, workers,
            lambda job: (job, [row for row in rows if row["seed"] == job["seed"]], str(out), phase, reference["root"]),
            on_result, submitted, worker_fn=read_world, budget=budget)
    audit_ok = len(results) == len(worlds) and all(r["status"] in ("completed", "partial") for r in results) and not errors
    complete = audit_ok and summary["status"] == "complete"
    episodes = [episode for world in results for episode in world.get("episodes", [])]
    replay_counts = sum_counts(e["replay"]["policy_counts"] for e in episodes)
    failed_attempts = sum_counts(r.get("inflight", {}).get("policy_counts", {}) for r in results if r["status"] == "failed")
    attempted_counts = sum_counts((replay_counts, failed_attempts))
    result = dict(object=OBJECT, phase=phase, launch_sha=config["launch_sha"],
                  status="VERIFIED" if complete else "INCOMPLETE_BUDGET" if budget.stopped else "PARTIAL" if audit_ok else "FAILED",
                  source_binding=config["source_binding"], worlds=len(worlds), episodes=len(rows),
                  reader_workers=workers, submitted_worlds=submitted, errors=errors,
                  budget_checkpoint=budget.last, budget_stopped=budget.stopped,
                  replay_counts=replay_counts, replay_attempted_counts=attempted_counts,
                  failed_replay_attempted_counts=failed_attempts,
                  deployment_reported_attempted_counts=sum_counts(row.get("policy_counts") or {} for row in rows),
                  preserved_unreplayed_attempted_or_uncertain_counts=sum_counts(
                      e["replay"].get("unreplayed_attempted_or_uncertain_counts", {}) for e in episodes),
                  verified_actual_proposals=sum(e["replay"]["verified_actual_proposals"] for e in episodes),
                  verified_feedback_calls=sum(e["replay"]["verified_feedback_calls"] for e in episodes),
                  reader_shield_calls=sum(e["replay"].get("shield_calls", 0) for e in episodes)
                      + sum(r.get("inflight", {}).get("shield_calls", 0) for r in results if r["status"] == "failed"),
                  native_transitions_checked=sum((e.get("native") or {}).get("native_transitions_checked", 0) for e in episodes),
                  unreported_jobs=[job for job in expected_jobs if job["job_key"] not in keys],
                  unreported_job_evidence=unreported_evidence,
                  unreported_attempted_count_lower_bound=sum_counts(
                      item["known_attempted_count_lower_bound"] for item in unreported_evidence),
                  deployment_unstarted_jobs=summary.get("unstarted_jobs", []),
                  reader_worker_cpu_seconds_sum=sum(r.get("reader_worker_cpu_seconds", 0.) for r in results),
                  reader_worker_wall_seconds_sum=sum(r.get("reader_worker_wall_seconds", 0.) for r in results),
                  reader_worker_peak_rss_kib_max=max((r.get("reader_worker_peak_rss_kib", 0) for r in results), default=None),
                  reaped_reader_cpu_seconds=children_cpu()-child_cpu,
                  **{"reader_parent_"+key: value for key, value in telemetry(wall, cpu).items()},
                  new_native_steps=0, model_resets=0, model_native_steps=0,
                  new_fits=0, new_labels=0, optimizer_updates=0,
                  model_vs_native="declared legal FP32 to FP64 unimpeded arrival intent; no native benefit or safety equality imposed")
    result["analytical_counts"] = attempted_counts
    result["old_rf_calls"] = result["old_tracker_calls"] = result["private_models"] = 0
    native_checks = [entry for r in results for entry in r.get("native_checks", [])]
    result["recorded_motion_power_argument_rows"] = 8 * sum(
        entry.get("native_transitions_checked", 0) for entry in native_checks if entry["status"] == "completed")
    result["interrupted_recorded_motion_power_rows_upper_bound"] = sum(
        entry["recorded_motion_power_rows_upper_bound"] for entry in native_checks if entry["status"] != "completed")
    if complete:
        completed_counts = sum_counts(e["replay"]["policy_counts"] for e in episodes)
        if completed_counts != summary["policy_counts"]:
            raise AssertionError("whole-reader actual-work call counts differ from deployment")
        if phase == "scientific":
            result["paired"] = comparisons(rows + reference["rows"])
            if result["paired"] != summary["paired"]:
                raise AssertionError("paired complete-world reductions differ")
        result["frozen_reference_verified"] = all(r["frozen_reference_verified"] for r in results)
        result["reference_native_transitions_checked"] = sum(e["native"]["native_transitions_checked"] for r in results for e in r["reference_episodes"])
        result["reference_controller_replays"] = 0
        result["reference_model_queries"] = 0
    write_json(out / "reading.json", result)
    if not audit_ok and not budget.stopped:
        raise RuntimeError("full actual-call reader audit failed; complete/partial native collection preserved")
    return result
