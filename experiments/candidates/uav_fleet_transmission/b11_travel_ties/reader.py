"""One full H_T replay; immutable C/H_A evidence gets only byte/native-metric reads."""
from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
from pathlib import Path
import time
import traceback
import numpy as np
from experiments.candidates.uav_fleet_transmission.b10_service_assignment import reader as original
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.reader import (
    UnavailableTruth, numeric_row_equal, check_native, check_partial_native,
    IdentityReading, bind_slots, compare_records, compare_candidate_prefix,
    change_reading, first_difference, children_cpu, pool_forecast_stats, finish_forecast_stats,
    apply_feedback_params, PRODUCTION_PARAMS, own_positions, own_energy, station_counts,
    world_row, mechanism_row, absolute_station_xy, position_diagnostics,
)
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.budget import execute_budgeted,check_worker_stop
from experiments.candidates.uav_fleet_transmission.b10_service_assignment.trace import CANDIDATE_DTYPE
from .capture import memory_record,plan_record
from .contract import (ARMS,HORIZON,OBJECT,SAMPLES,array_digest,equal,expected_counts,
    identity,jobs,source_binding,sum_counts,telemetry,write_json,reference_evidence)
from .controller import ReplayBoundary,make_controller
from .metrics import comparisons,episode_metrics


def validate_candidate_records(raw,arm,complete):
    if arm!="H_T":
        raise AssertionError("B11 may only replay H_T")
    return original.validate_candidate_records(raw,"H_A",complete)


def check_assignment_contract(raw):
    """Independent literal selection, followed by frozen unchanged-menu/provenance checks.

    The temporary old-winner view is solely for the original source's audit API;
    actual H_T selected state is checked here and replayed without modification.
    No controller, nominal or radio call occurs in this function.
    """
    view=dict(raw)
    for name in ("candidate_records","plan_targets","plan_selected_candidate","plan_selected_pair"):
        view[name]=raw[name].copy()
    for k,step in enumerate(raw["plan_step"]):
        indices=np.flatnonzero(raw["candidate_records"]["step"]==step)
        group=raw["candidate_records"][indices]
        if not len(group):
            equal(raw["plan_h_selected"][k],-1,"unscored old H index")
            equal(raw["plan_tie_changed"][k],False,"unscored tie change")
            equal(raw["plan_top_score_mask"][k],np.zeros(16,bool),"unscored top mask")
            equal(raw["plan_min_travel_mask"][k],np.zeros(16,bool),"unscored travel mask")
            continue
        score=group["score"];travel=group["forecast_travel"]
        if not np.isfinite(score).all() or not np.isfinite(travel).all():
            raise AssertionError("nonfinite completed H_T ranking values")
        old=int(np.argmax(score))
        top=score==np.max(score)
        shortest=top & (travel==np.min(travel[top]))
        winner=0 if top[0] else int(np.flatnonzero(shortest)[0])
        equal(raw["plan_h_selected"][k],old,"original literal H winner")
        equal(raw["plan_top_score_mask"][k],np.pad(top,(0,16-len(top))),"exact top-score set")
        equal(raw["plan_min_travel_mask"][k],np.pad(shortest,(0,16-len(top))),"exact min-travel top set")
        equal(raw["plan_tie_changed"][k],winner!=old,"actual tie choice changed")
        equal(raw["plan_selected_candidate"][k],winner,"actual H_T winner")
        equal(np.flatnonzero(group["selected"]),[winner],"single actual H_T selected flag")
        equal(raw["plan_selected_pair"][k],[group[winner]["pair_left"],group[winner]["pair_right"]],"H_T actual pair")
        equal(raw["plan_targets"][k],group[winner]["targets"][:,:2],"H_T actual committed targets")
        view["plan_selected_candidate"][k]=old
        view["plan_selected_pair"][k]=[group[old]["pair_left"],group[old]["pair_right"]]
        view["plan_targets"][k]=group[old]["targets"][:,:2]
        view["candidate_records"]["selected"][indices]=False
        view["candidate_records"]["selected"][indices[old]]=True
    original.check_assignment_contract(view,"H_A")


def replay_episode(raw, row, phase, progress=None):
    complete = row.get("status", "completed") == "completed"
    arm = row["arm"]
    records = validate_candidate_records(raw, arm, complete)
    unverified_ranking_step = None
    if not complete and len(records):
        step = int(records[-1]["step"])
        in_step = records["step"] == step
        if step not in raw.get("plan_step", []) and not records["selected"][in_step].any():
            unverified_ranking_step = step
    n = int(row["actual_length"] if complete else np.asarray(raw["recorded_decision_steps"]).item())
    if n < 0 or len(raw["observations"]) <= n:
        raise AssertionError("decision prefix lacks lawful boundary observations")
    controller = make_controller(arm)
    controller.reset()
    if arm == "H_T":
        controller.replay_prefix = records
    modes, previous_done = np.zeros(8, dtype=bool), np.ones(1, dtype=bool)
    binding = IdentityReading()
    plan_index = verified = attempts = reference_lloyd = shield_attempts = 0
    boundary = None
    actual_counts = {}
    missing = set()

    def saved(name, index, value, label):
        if name not in raw:
            if complete:
                raise AssertionError(label + "/missing " + name)
            missing.add(name)
            return
        if index >= len(raw[name]):
            raise AssertionError(label + "/short " + name)
        equal(raw[name][index], value, label)

    def counts():
        if arm == "REFERENCE":
            return expected_counts(arm, verified) | {"proposals": attempts, "lloyd_solves": reference_lloyd}
        return dict(controller.counters)

    try:
        for tick in range(n):
            obs = raw["observations"][tick]
            attempts += 1
            try:
                proposal = controller.propose(obs, UnavailableTruth(), tick, previous_done, modes.copy())
            except ReplayBoundary as error:
                raise AssertionError("boundary inside a recorded completed decision") from error
            equal(proposal, raw["proposed"][tick], "actual-path proposed commands")
            saved("target_xy", tick, controller.targets_xy, "actual held targets")
            targets_xyz = getattr(controller, "targets_xyz", None)
            if targets_xyz is None:
                targets_xyz = np.column_stack((controller.heuristic.targets_xy, np.full(8, 100.0)))
            saved("decision_targets_xyz", tick, targets_xyz, "actual held xyz targets")
            shield_attempts += 1
            decision = apply_feedback_params(obs, proposal, modes, PRODUCTION_PARAMS)
            for name, value in dict(submitted=decision.submitted_actions, mode=decision.modes,
                                    entered=decision.entered, exited=decision.exited,
                                    return_margin=decision.margins, nearest_station=decision.selected_stations,
                                    nearest_station_distance_m=decision.station_distances_m).items():
                saved(name, tick, value, "actual feedback: " + name)
            saved("own_xyz", tick, own_positions(obs), "decoded decision position")
            held = own_energy(obs)
            saved("station_occupancy", tick, station_counts(decision.selected_stations, held["charging"]),
                  "decision-time occupancy decode")
            saved("station_queue", tick, station_counts(decision.selected_stations, held["waiting_steps"] > 0),
                  "decision-time queue decode")
            post = own_energy(raw["observations"][tick + 1])
            for name in ("charging", "waiting_steps", "battery"):
                saved(name, tick, post[name], "post-step energy decode: " + name)
            saved("dock_bit", tick, decision.submitted_actions[:, 3] > .5, "dock command")
            current_plan = plan_index if tick % 30 == 0 else None
            if current_plan is not None:
                compare_records(raw, plan_record(controller, tick), plan_index, "actual plan")
                plan_index += 1
            slots, silent = bind_slots(raw, tick)
            binding.counts["slot_records"] += int(np.count_nonzero(slots >= 0))
            binding.counts["silent_true_slots"] += silent
            if arm == "H_T":
                trace = controller.last_trace
                compare_records(raw, memory_record(trace), tick, "actual primitive memory")
                binding.step(raw, tick, trace, slots, current_plan, "H_A")
            modes = decision.modes
            previous_done[:] = raw.get("ends", raw["native_ends"])[tick].any()
            verified += 1
            if arm == "REFERENCE" and current_plan is not None:
                reference_lloyd += int(raw["plan_user_count"][current_plan] > 0)
            if progress is not None and verified % 100 == 0:
                progress(dict(verified=verified, policy_counts=counts()))
        # The recorder attaches decisions AFTER native transitions. An interrupted
        # replan can therefore exist at n without a saved decision/plan/track row.
        # Candidate records are the positive evidence permitting this single call.
        if not complete and len(records) and int(records[-1]["step"]) == n:
            attempts += 1
            try:
                proposal = controller.propose(raw["observations"][n], UnavailableTruth(), n,
                                              previous_done, modes.copy())
            except ReplayBoundary as error:
                boundary = str(error)
            else:
                # A full modeled search may have finished before capture/native
                # failed. Check its saved candidate outputs; do not invent an end.
                if len(raw.get("submitted", [])) > n:
                    shield_attempts += 1
                    decision = apply_feedback_params(raw["observations"][n], proposal, modes, PRODUCTION_PARAMS)
                    equal(decision.submitted_actions, raw["submitted"][n], "inflight actual submitted command")
        actual = controller.audit_arrays()["candidate_records"] if hasattr(controller, "audit_arrays") else np.empty(0, CANDIDATE_DTYPE)
        compare_candidate_prefix(actual, records, unverified_ranking_step=unverified_ranking_step)
        equal(plan_index, len(raw.get("plan_step", [])), "all and only captured actual plans")
        actual_counts = counts()
        if complete:
            fixed = expected_counts(arm, n)
            if any(actual_counts.get(key, 0) != value for key, value in fixed.items()):
                raise AssertionError("replay primitive accounting")
            if actual_counts != row["policy_counts"]:
                raise AssertionError("deployment/replay actual-work count mismatch")
            original = world_row(row["seed"], raw["reward"], raw["metrics"], raw["ends"], raw, time_step_s=1.)
            original.update(mechanism_row(raw, absolute_station_xy(raw["observations"][0])))
            original.update(position_diagnostics(raw["metrics"], raw, area_size_m=8000., floor_m=50.))
            numeric_row_equal(row, original, "original evaluator reductions")
            numeric_row_equal(row, episode_metrics(raw), "independent complete-mission reductions")
        deployment = row.get("policy_counts") or {}
        omitted = {key: int(value) - int(actual_counts.get(key, 0)) for key, value in deployment.items()
                   if int(value) != int(actual_counts.get(key, 0))}
        if not complete and any(value < 0 for value in omitted.values()):
            raise AssertionError("partial replay overran recorded attempted work")
        return dict(status="verified" if complete else "partial-prefix-verified",
                    policy_counts=actual_counts, deployment_attempted_counts=deployment,
                    unreplayed_attempted_or_uncertain_counts=omitted,
                    recorded_rf_attempts_without_output=int(np.sum(records["rf_started"] - records["rf_completed"])),
                    replay_boundary=boundary, candidate_records_checked=len(records),
                    unverified_candidate_ranking_step=unverified_ranking_step,
                    preserved_unverified_ranking_flags=[dict(index=int(record["index"]),
                        accepted=bool(record["accepted"]), selected=bool(record["selected"]))
                        for record in records if int(record["step"]) == unverified_ranking_step],
                    ranking_scope="exact on captured complete plans; interrupted final plan flags preserved, false does not prove rejection",
                    identity_reading=binding.result(), verified_actual_proposals=verified,
                    verified_feedback_calls=verified, shield_calls=shield_attempts,
                    inflight_proposals_replayed=attempts-verified,
                    missing_saved_decision_fields=sorted(missing),
                    new_native_steps=0, partial_native_scope="complete recorded decisions only; no missing output reconstructed")
    finally:
        if progress is not None:
            progress(dict(verified=verified, attempted_calls=attempts, policy_counts=counts(),
                          shield_calls=shield_attempts,
                          replay_boundary=boundary,
                          failed_call_count_scope="actual replay attempts; deployment interrupted suffix separately preserved"))
        close = getattr(controller, "close", None)
        if close is not None:
            close()


def read_world(payload):
    job,rows,out_string,phase,reference_root=payload
    out=Path(out_string)
    wall,cpu=time.perf_counter(),time.process_time()
    checked,reference_checked,trajectories=[],[],{}
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
                        identity_reading=IdentityReading().result(),new_native_steps=0)))
                continue
            raw=load_raw(out,row,artifact)
            native=check_native(raw,row,phase) if complete else check_partial_native(raw,row)
            if complete:
                check_assignment_contract(raw)
            replay=replay_episode(raw,row,phase,progress)
            checked.append(dict(arm=row["arm"],seed=row["seed"],native=native,replay=replay))
            state={}
            if complete:
                retain_trajectory(row["arm"],raw)
            del raw
        # Already byte-bound by parent; this call reads compact identities, then this
        # world verifies and reduces only its two original C/H_A records. No replay.
        reference=reference_evidence(reference_root,phase,verify_raw=False)
        reference_rows=[r for r in reference["rows"] if r["seed"]==job["seed"]]
        for row in reference_rows:
            check_worker_stop(out)
            raw=load_raw(Path(reference["directory"]),row,row["raw"])
            native=check_native(raw,row,phase)
            numeric_row_equal(row,original.episode_metrics(raw),"frozen reference native reductions")
            reference_checked.append(dict(seed=row["seed"],arm=row["arm"],raw=row["raw"],native=native,
                source_sha=reference["descriptor"]["launch_sha"],controller_replays=0,model_queries=0,new_native_steps=0))
            retain_trajectory(row["arm"],raw)
            del raw
        pairs=[]
        combined={(r["seed"],r["arm"]):r for r in rows+reference_rows}
        for left,right in (("H_T","H_A"),("H_T","C")):
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
            reference_episodes=reference_checked,common_prefix_pairs=pairs,
            frozen_reference_verified=len(reference_checked)==2,
            **{"reader_worker_"+k:v for k,v in telemetry(wall,cpu).items()})
        write_json(progress_path,dict(**job,status=result["status"],episodes=len(checked),reference_episodes=len(reference_checked)))
        return result
    except BaseException as error:
        result=dict(**job,status="failed",error=repr(error),traceback=traceback.format_exc(),
            episodes=checked,reference_episodes=reference_checked,inflight=state,
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
                  model_vs_native="declared FP32 decoding/FP64 nominal and post-energy sample; omitted guard/intermediate association/PBRS/event penalties; no equality imposed")
    result["identity_totals"] = {
        arm: sum_counts(e["replay"]["identity_reading"]["counts"] for e in episodes if e["arm"] == arm)
        for arm in ARMS}
    result["forecast_by_world"] = [dict(seed=e["seed"], arm=e["arm"],
         replay_status=e["replay"]["status"], **e["replay"]["identity_reading"])
         for e in episodes if e["arm"] == "H_T"]
    result["forecast_totals"] = {}
    for arm in ("H_T",):
        per_tau = {}
        for tau in SAMPLES:
            values = []
            for e in episodes:
                if e["arm"] != arm:
                    continue
                item = dict(e["replay"]["identity_reading"]["per_tau"][str(tau)])
                item["worst_rows"] = [dict(seed=e["seed"], **row) for row in item["worst_rows"]]
                values.append(item)
            per_tau[str(tau)] = finish_forecast_stats(pool_forecast_stats(values))
        result["forecast_totals"][arm] = dict(per_tau=per_tau,
             combined=finish_forecast_stats(pool_forecast_stats(per_tau.values())),
             scope="recorded origin identities on this arm's own path; partial censoring retained")
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
