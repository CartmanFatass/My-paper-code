"""Read every native outcome, replay frozen full models, and audit exact reuse."""
from copy import deepcopy
import hashlib
import json
import struct
import time

import numpy as np

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_fleet_transmission.control import predict_next
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.reader import _native_view, _paired, _public_state, _same
from experiments.candidates.uav_fleet_transmission.study import artifact, metrics, process_resources, write_json
from experiments.candidates.uav_fleet_transmission.b02.controller import COUNT_KEYS, KINDS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b02.study import COMPONENTS, option_metrics
from experiments.candidates.uav_fleet_transmission.b03.reader import checked_path, load_arrays, load_decisions, verify_model_branch

from .contract import ARMS, BOOTSTRAP_SEED, CEILINGS, FIT_FILE, REPO
from .controller import AmortizedProgram
from .fit import audit_solution, logical_manifest, scalar_features, validate_operation
from .host import WORLD_IDS, bound_worlds, seed
from .study import verify_prefixes


def validate_fit(config):
    """Evaluation consumes the complete published fit; it never solves again."""
    paths = {k: checked_path(REPO, v) for k,v in config["fit_inputs"].items()}
    if paths["ranker.json"] != FIT_FILE or config["fit_artifact"] != config["fit_inputs"]["ranker.json"]:
        raise ValueError("ranker path/binding differs")
    summary = json.loads(paths["summary.json"].read_text())
    if (summary["status"] != "complete" or summary["new_fits"] != 1 or summary["updates"] != 0
            or summary["new_native_steps"] != 0 or summary["new_training_acquisition"] != 0
            or summary["new_scorer_requests"] != 0):
        raise ValueError("complete single-fit provenance missing")
    validate_operation(summary, FIT_FILE.parent, "fit")
    for field, filename in (("ranker", "ranker.json"), ("reading", "reading.json"), ("training_rows", "training_rows.json")):
        if checked_path(FIT_FILE.parent, summary[field]) != paths[filename]:
            raise ValueError("fit result artifact differs")
    reading = json.loads(paths["reading.json"].read_text())
    fitted = json.loads(paths["ranker.json"].read_text())
    data = json.loads(paths["training_rows.json"].read_text())
    if (reading["status"] != "complete" or reading["source_sha"] != summary["launch_sha"]
            or reading["ranker"] != summary["ranker"] or reading["training_rows"] != summary["training_rows"]
            or reading["data_audit"]["rows"] != 58 or reading["data_audit"]["worlds"] != 16
            or reading["numerical_audit"]["rank"] != 13
            or logical_manifest(fitted["source_manifest"]) != logical_manifest(data["manifest"])):
        raise ValueError("fit reading/lineage differs")
    audit_solution(data, fitted, resolve=False)
    return fitted, summary


def verify_reuse(saved, full, entering_commands, candidate):
    """Derive every cache source/count independently from original full outputs."""
    arrays, decisions = full["arrays"], full["decisions"]
    barrier = 40 if candidate is None else 40 + int(candidate["duration"])
    cache, source_times, first_repeat = {}, [], None
    actual, logical = empty_counts(), empty_counts()
    computed = predictions = actual_predictions = 0
    reward = {k: 0 for k in COUNT_KEYS}
    actual_reward = {k: 0 for k in COUNT_KEYS}
    users = arrays["reports"][0, 32:132].astype("<f4", copy=False).tobytes()
    for index, decision in enumerate(decisions):
        t = index + 40
        key = None
        if t > barrier:
            commands = entering_commands if index == 0 else arrays["actions"][index-1]
            key = (struct.pack("<qq", t % 40, int(decision["old_mask"]))
                   + arrays["positions"][index].astype("<f8", copy=False).tobytes()
                   + arrays["controller_estimates"][index].astype("<f8", copy=False).tobytes()
                   + commands.astype("<f4", copy=False).tobytes() + users)
        source_t = cache.get(key) if key is not None else None
        executed = source_t is None
        if source_t is None:
            source_t = t
            computed += 1
            trace_counts(decision, actual)
            actual_predictions += int(decision.get("motion", {}).get("requested_candidates", 0))
            if key is not None:
                cache[key] = t
        else:
            if first_repeat is None:
                first_repeat = {"source_t": source_t, "repeat_t": t, "period": t-source_t,
                                "phase": t % 40, "entering_mask": decision["old_mask"],
                                "key_sha256": hashlib.sha256(key).hexdigest()}
            earlier = deepcopy(decisions[source_t-40])
            earlier["t"] = t
            if earlier != decision:
                raise ValueError("equal byte states failed full decision equivalence")
            for name in ("actions", "masks", "reward_components"):
                if arrays[name][index].tobytes() != arrays[name][source_t-40].tobytes():
                    raise ValueError("equal byte states failed full transition/reward equivalence")
            for name in ("positions", "controller_estimates"):
                if arrays[name][index+1].tobytes() != arrays[name][source_t-39].tobytes():
                    raise ValueError("equal byte states failed next-state equivalence")
        source_times.append(source_t)
        trace_counts(decision, logical)
        predictions += int(decision.get("motion", {}).get("requested_candidates", 0))
        unique_rows = len({row.astype("<f8", copy=False).tobytes() for row in arrays["positions"][index+1]})
        step_reward = dict(requested_candidates=1, scored_candidates=1, cached_candidates=0,
                           geometry_rows_computed=unique_rows, geometry_rows_reused=8-unique_rows)
        for name in COUNT_KEYS:
            reward[name] += step_reward[name]
            if executed:
                actual_reward[name] += step_reward[name]
    count = len(decisions)
    lr = sum(v["requested_candidates"] for v in logical.values())
    ar = sum(v["requested_candidates"] for v in actual.values())
    expected = dict(schema="exact_ordinary_recurrence.v1",
        key_layout="<i8 phase40,mask; <f8 physical[8,3],estimated[8,3]; <f4 issued[8,3],public_users[50,2]",
        eligibility_after_t=barrier, computed_ticks=computed, reused_ticks=count-computed,
        logical_controller_calls=count, actual_controller_calls=computed,
        logical_reward_calls=count, actual_reward_calls=computed,
        logical_controller_counts=logical, actual_controller_counts=actual,
        logical_reward_counts=reward, actual_reward_counts=actual_reward,
        logical_controller_requests=lr, actual_controller_requests=ar,
        logical_reward_requests=count, actual_reward_requests=computed,
        logical_requested_candidates=lr+count, actual_requested_candidates=ar+computed,
        logical_candidate_position_predictions=predictions, actual_candidate_position_predictions=actual_predictions,
        first_repeat=first_repeat, source_times=source_times)
    if saved != expected or full["summary"]["reward_counts"] != reward or full["summary"]["controller_counts"] != logical:
        raise ValueError("exact-reuse certificate or original full counts differ")
    return expected


def verify_episode(row, out, scene, fitted):
    raw = load_arrays(checked_path(out, row["raw"]))
    decisions = load_decisions(checked_path(out, row["decisions"]))
    shapes = {"positions": (501,8,3), "observations": (501,8,104), "states": (501,133),
              "sinr": (501,8,50), "connections": (501,8,50), "peer_sinr": (501,8,8),
              "visible_users": (501,8), "visible_peers": (501,8), "actions": (500,8,3),
              "mask": (500,), "components": (500,4), "scalar_reward": (500,), "terminal": (500,), "users": (50,2)}
    if set(raw) != set(shapes) or len(decisions) != 500:
        raise ValueError("complete native data keys/decisions differ")
    for key, shape in shapes.items():
        if raw[key].shape != shape or (key not in ("sinr", "peer_sinr") and not np.isfinite(raw[key]).all()):
            raise ValueError("invalid native array: " + key)
    if (raw["actions"].dtype != np.float32 or raw["states"].dtype != np.float32
            or not np.isin(raw["actions"], [-1,0,1]).all()):
        raise ValueError("native command/public report dtype or alphabet differs")
    _same(raw["terminal"], np.arange(500) == 499, "fixed native horizon")
    _same(raw["users"], scene.user_positions, "bound users")
    _same(raw["positions"][0], scene.uav_positions, "bound initial fleet")
    policy = AmortizedProgram(row["arm"], fitted if row["arm"] == "L" else None, reference=True)
    old_mask, totals, calls = 255, empty_counts(), {kind: 0 for kind in KINDS}
    predictions = option_ticks = banks = 0
    branch_certificates = []
    feature_error = None
    view = _native_view(8, raw["users"], 500)
    for t in range(501):
        positions = raw["positions"][t]
        mask = mask_bits(255 if t == 0 else int(raw["mask"][t-1]), 8)
        loss = uav_radio.free_space_user_path_loss(positions, raw["users"])
        sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=mask)
        connections = uav_radio.greedy_connection_assignment(sinr, 0., 10)
        _same(raw["sinr"][t], sinr, f"native radio {t}")
        _same(raw["connections"][t], connections, f"native assignment {t}")
        view.uav_positions, view.sinr_matrix, view.connections = positions, sinr, connections
        view._transmitter_mask = mask
        view._uav_uav_path_loss_matrix = MultiUAVEnv._compute_uav_path_loss_matrix(view)
        view.uav_sinr_matrix = MultiUAVEnv._compute_uav_uav_sinr_matrix(view)
        view.current_step = t
        _same(raw["peer_sinr"][t], view.uav_sinr_matrix, f"native peer radio {t}")
        _same(raw["states"][t], _public_state(positions, raw["users"], t, 500), f"public report {t}")
        for member in range(8):
            obs = MultiUAVEnv._get_observation_vectorized(view, f"uav_{member}")["obs"]
            _same(raw["observations"][t,member], obs, f"native observation {t}/{member}")
        _same(raw["visible_users"][t], [len(view._local_user_entries(i)[0][:20]) for i in range(8)], f"visible users {t}")
        _same(raw["visible_peers"][t], [len(view._local_uav_entries(i)[0][:10]) for i in range(8)], f"visible peers {t}")
        if t:
            UAVBaseStationEnv._compute_reward(view)
            component = np.asarray([view.reward_info[k] for k in COMPONENTS])
            _same(raw["components"][t-1], component, f"native objective {t}")
            if abs(raw["scalar_reward"][t-1]*8-component[3]) > 1e-14:
                raise ValueError("native scalar reward N-scaling differs")
        if t == 500:
            break
        _same(raw["positions"][t+1], predict_next(positions, raw["actions"][t]), f"native motion {t}")
        command, new_mask, decision = policy.select(t, raw["states"][t] if t % 10 == 0 else None, old_mask)
        if decision != decisions[t]:
            raise ValueError(f"full ordinary/reference policy trace differs: {row['arm']}/{t}")
        _same(raw["actions"][t], command, f"issued command {t}")
        if raw["mask"][t] != new_mask or (t % 10 and old_mask != new_mask):
            raise ValueError("legal issued mask/hold differs")
        pending = policy.take_artifacts()
        if pending is not None:
            bank = np.load(checked_path(out, row["stationary_candidates"]), allow_pickle=False)
            if bank.dtype != pending["candidate_rows"].dtype or not np.array_equal(bank, pending["candidate_rows"]):
                raise ValueError("all original stationary candidate rows differ")
            banks += 1
            if len(pending["branches"]) != len(row["model_branches"]):
                raise ValueError("complete branch set differs")
            for index, (identifier, full) in enumerate(pending["branches"]):
                saved = row["model_branches"][index]
                verify_model_branch(out, saved, identifier, full)
                # The optimized engine promises every output bit, not just a
                # numerical tolerance. Original reader checks remain additional.
                saved_arrays = load_arrays(checked_path(out, saved["raw"]))
                if any(saved_arrays[k].tobytes() != a.tobytes() for k,a in full["arrays"].items()):
                    raise ValueError("exact optimized/full-reference model bits differ")
                candidate = policy.selection["branches"][index]["stationary_candidate"]
                branch_certificates.append(verify_reuse(saved["reuse"], full, raw["actions"][39], candidate))
            if row["arm"] == "L":
                features = scalar_features(raw["states"][40], old_mask, policy.selection["champion_candidates"], policy.plan["stay_score"])
                record = policy.selection["learner"]
                feature_error = float(np.max(np.abs(features-np.asarray(record["features"])))) if len(features) else 0.
                if feature_error > 1e-12:
                    raise ValueError("independent deployment feature audit differs")
        trace_counts(decision, totals)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        predictions += 216*int("motion" in decision)
        if "option" in decision:
            option_ticks += int(decision["option"]["counts"]["model_ticks"])
        old_mask = new_mask
    actual_metrics = metrics(raw, 8)
    if (actual_metrics != row["metrics"] or option_metrics(policy.plan, raw) != row["option"]
            or policy.selection != row["selection"] or totals != row["candidate_counts"]
            or calls != row["calls"] or predictions != row["position_predictions"]
            or option_ticks != row["option_model_ticks"] or banks != 1 or not actual_metrics["capacity_identity_holds"]):
        raise ValueError("native reduction/control count differs")
    return {"counts": totals, "reuse": branch_certificates, "maximum_scalar_feature_error": feature_error}


def world_comparisons(out, rows):
    panel = {(r["arm"],r["world_id"]): r for r in rows}
    result = []
    for world in WORLD_IDS:
        raw = {a: load_arrays(checked_path(out, panel[a,world]["raw"])) for a in ARMS}
        changes, forecasts = {}, {}
        branches = {b["id"]: b for b in panel["T_E",world]["selection"]["branches"]}
        for arm in ARMS:
            identity = panel[arm,world]["selection"]["selected_physical_identity"]
            for other in ARMS:
                if identity == panel[other,world]["selection"]["selected_physical_identity"]:
                    if any(raw[arm][k].tobytes() != raw[other][k].tobytes() for k in raw[arm]):
                        raise ValueError("identical selected physical programs had different native outcomes")
            changes[arm] = {"selected_branch": panel[arm,world]["selection"]["selected_branch"],
                           "physical_identity": identity,
                           "command_ticks_different_from_R": int(np.any(raw[arm]["actions"] != raw["R"]["actions"],axis=(1,2)).sum()),
                           "mask_ticks_different_from_R": int((raw[arm]["mask"] != raw["R"]["mask"]).sum())}
            branch = branches[panel[arm,world]["selection"]["selected_branch"]]["summary"]
            native_J = sum(float(v) for v in raw[arm]["components"][40:,3])
            native_served = int(raw[arm]["connections"][41:].sum())
            forecasts[arm] = {"modeled_remaining_J": branch["total_J"], "native_remaining_J": native_J,
                              "model_minus_native_J": branch["total_J"]-native_J,
                              "modeled_remaining_served": branch["total_served"], "native_remaining_served": native_served,
                              "model_minus_native_served": branch["total_served"]-native_served}
        result.append({"world_id": world, "programs": changes, "forecast_vs_native": forecasts})
    return result


def read_run(out):
    wall, cpu = time.perf_counter(), time.process_time()
    summary = json.loads((out/"summary.json").read_text())
    if (summary["worker_status"] != "complete" or summary["status"] not in ("collected", "complete")
            or summary["new_fits"] != 0 or summary["updates"] != 0 or summary["cumulative_B06_fits"] != 1):
        raise ValueError("complete fixed evaluation worker missing")
    validate_operation(summary, out, "evaluate", summary["config"]["fit_artifact"]["sha256"])
    fitted, fit_summary = validate_fit(summary["config"])
    rows = summary["episodes"]
    expected = [(ARMS[(index+offset)%4], world) for index,world in enumerate(WORLD_IDS) for offset in range(4)]
    if [(r["arm"],r["world_id"]) for r in rows] != expected:
        raise ValueError("complete cyclic four-program panel differs")
    if any(r["n"] != 8 or r["steps"] != 500 or r["complete"] is not True
           or r["runtime_seed"] != seed(r["world_id"],3,8) for r in rows):
        raise ValueError("fixed evaluation cell differs")
    scenes = bound_worlds()
    totals, audits = {arm: empty_counts() for arm in ARMS}, []
    for index,row in enumerate(rows):
        audit = verify_episode(row, out, scenes[row["world_id"]], fitted)
        audits.append(audit)
        for kind in KINDS:
            for key in COUNT_KEYS:
                totals[row["arm"]][kind][key] += audit["counts"][kind][key]
        print(json.dumps({"reader_episodes_verified": index+1}), flush=True)
    verify_prefixes(out, rows)
    worlds = world_comparisons(out, rows)
    certificates = [c for a in audits for c in a["reuse"]]
    native_requests = sum(v["requested_candidates"] for a in totals.values() for v in a.values())
    actual_requests = sum(c["actual_requested_candidates"] for c in certificates)
    logical_requests = sum(c["logical_requested_candidates"] for c in certificates)
    costs = {"worker_state_mask_requests": native_requests+actual_requests,
             "model_physical_transitions": sum(c["computed_ticks"] for c in certificates),
             "candidate_transit_ticks": sum(r["option_model_ticks"] for r in rows),
             "stationary_candidate_rows": sum(r["selection"]["candidate_count"] for r in rows),
             "model_branches": len(certificates), "native_steps": 32000, "episodes": len(rows)}
    logical_costs = dict(costs, worker_state_mask_requests=native_requests+logical_requests,
                         model_physical_transitions=sum(c["logical_controller_calls"] for c in certificates))
    if any(costs[k] > CEILINGS[k] or logical_costs[k] > CEILINGS[k] for k in CEILINGS):
        raise ValueError("declared complete cost ceiling exceeded")
    panel = {(r["arm"],r["world_id"]): r for r in rows}
    names = ("J", "served", "quality", "height_penalty", "mean_path_per_uav", "ineligible",
             "eligible_unserved", "served_p05", "served_min", "zero_steps", "longest_zero_run", "active_mean")
    indices = np.random.RandomState(BOOTSTRAP_SEED).randint(0,16,(10000,16))
    contrasts = (("L","R"), ("L","T_E"), ("L","K2_E"), ("T_E","R"), ("K2_E","R"), ("T_E","K2_E"))
    comparisons = {f"{a}-{b}": {m: _paired(np.asarray([panel[a,w]["metrics"][m]-panel[b,w]["metrics"][m] for w in WORLD_IDS]),
        list(WORLD_IDS), indices) for m in names} for a,b in contrasts}
    aggregates = {a: {m: float(np.mean([panel[a,w]["metrics"][m] for w in WORLD_IDS])) for m in names} for a in ARMS}
    timing_names = tuple(rows[0]["timing"])
    timings = {a: {m: float(np.mean([panel[a,w]["timing"][m] for w in WORLD_IDS])) for m in timing_names} for a in ARMS}
    timing_comparisons = {f"{a}-{b}": {m: _paired(np.asarray([panel[a,w]["timing"][m]-panel[b,w]["timing"][m] for w in WORLD_IDS]),
        list(WORLD_IDS), indices) for m in timing_names} for a,b in contrasts}
    if any(not np.isfinite(v) or v < 0 for r in rows for v in r["timing"].values()):
        raise ValueError("invalid recorded complete cost timing")
    retention = np.asarray([(panel["L",w]["metrics"]["J"]-panel["R",w]["metrics"]["J"])
                           -.75*(panel["T_E",w]["metrics"]["J"]-panel["R",w]["metrics"]["J"]) for w in WORLD_IDS])
    cpu_ratio = timings["L"]["selection_cpu_seconds"]/timings["T_E"]["selection_cpu_seconds"]
    lcpu = np.asarray([panel["L",w]["timing"]["selection_cpu_seconds"] for w in WORLD_IDS])
    tcpu = np.asarray([panel["T_E",w]["timing"]["selection_cpu_seconds"] for w in WORLD_IDS])
    target = {"linear_retention_contrast": _paired(retention,list(WORLD_IDS),indices),
              "positive_T_E_minus_R": aggregates["T_E"]["J"] > aggregates["R"]["J"],
              "retention_point_pass": float(retention.mean()) >= 0,
              "selection_mean_CPU_L_over_T_E": cpu_ratio, "CPU_point_pass": cpu_ratio <= .5,
              "selection_mean_CPU_ratio_bootstrap95": np.percentile(lcpu[indices].mean(axis=1)/tcpu[indices].mean(axis=1),[2.5,97.5]).tolist(),
              "interpretation": "exploratory point target; no adoption, equivalence, robustness, or population-learning guarantee"}
    target["point_target_pass"] = target["positive_T_E_minus_R"] and target["retention_point_pass"] and target["CPU_point_pass"]
    bindings = [r[f] for r in rows for f in ("raw", "decisions", "stationary_candidates")]
    bindings += [b[f] for r in rows for b in r["model_branches"] for f in ("raw", "decisions")]
    if len({b["path"] for b in bindings}) != len(bindings):
        raise ValueError("duplicated evaluation artifact path")
    result = {"status": "complete", "source_sha": summary["launch_sha"], "config_artifact": summary["config_artifact"],
              "fit_artifact": summary["config"]["fit_artifact"], "episodes_verified":64, "native_steps_verified":32000,
              "native_snapshots_verified":32064, "new_fits":0, "updates":0, "cumulative_B06_fits":1,
              "all_native_physics_observations_actions_checked":True,
              "all_stationary_candidates_and_original_full_models_replayed":True,
              "all_optimized_model_arrays_bitwise_equal_original":True,
              "all_cycle_sources_and_costs_independently_reconstructed":True,
              "all_prefixes_exact_through_t39":True, "worker_native_candidate_counts":totals,
              "worker_actual_costs":costs, "worker_logical_costs_without_reuse":logical_costs,
              "reader_full_replay_costs":logical_costs, "reader_new_native_transitions":0,
              "worker_native_control_requests":native_requests, "worker_actual_model_requests":actual_requests,
              "worker_logical_model_requests":logical_requests,
              "reuse": {"computed_ticks":costs["model_physical_transitions"],
                        "reused_ticks":sum(c["reused_ticks"] for c in certificates),
                        "branches_with_recurrence":sum(c["first_repeat"] is not None for c in certificates),
                        "branches_without_recurrence":sum(c["first_repeat"] is None for c in certificates)},
              "maximum_deployment_scalar_feature_error":max(a["maximum_scalar_feature_error"] or 0 for a in audits),
              "aggregates":aggregates, "comparisons":comparisons, "exploratory_target":target,
              "mean_recorded_timings":timings, "paired_timing_comparisons":timing_comparisons,
              "L_feature_distance_pairs":sum(r["selection"]["learner"]["feature_distance_pairs"] for r in rows if r["arm"] == "L"),
              "L_coefficient_products":sum(r["selection"]["learner"]["coefficient_products"] for r in rows if r["arm"] == "L"),
              "worlds":worlds, "bulk_bytes":sum(b["bytes"] for b in bindings),
              "fit_timing":fit_summary["total_timing"],
              "prior_paid_acquisition_CPU_seconds":1222.447506,
              "uncertainty_scope":"paired percentile bootstrap over16fresh worlds conditional on one fixed learned fit and four programs; 16 training worlds, not58 independent training units; no new native branch labels",
              "bootstrap":{"seed":BOOTSTRAP_SEED,"replicates":10000},
              "timing":{"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu,
                        "process_resources":process_resources()}}
    write_json(out/"reading.json",result)
    return result
