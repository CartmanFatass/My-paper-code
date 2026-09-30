"""Full native/model replay and independent learned-shortlist reconstruction."""
import json
import math
import time

import numpy as np

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_fleet_transmission.control import predict_next
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.reader import _native_view, _paired, _public_state, _same
from experiments.candidates.uav_fleet_transmission.study import artifact, process_resources, write_json
from experiments.candidates.uav_fleet_transmission.b02.controller import COUNT_KEYS, KINDS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b02.study import COMPONENTS, option_metrics
from experiments.candidates.uav_fleet_transmission.b03.reader import checked_path, load_arrays, load_decisions, verify_model_branch
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization.fit import scalar_features
from experiments.candidates.uav_parent_adaptation.b06_continuation_amortization.reader import validate_fit, verify_reuse

from .contract import ARMS, BOOTSTRAP_SEED, CEILINGS, CONTRASTS, validate_operation
from .controller import make_program
from .host import WORLD_IDS, bound_worlds, seed
from .outcomes import METRIC_NAMES, complete_metrics
from .study import verify_prefixes


def verify_shortlist(report, old_mask, selection, stay_score, fitted):
    """Scalar features, independent score arithmetic/order, and complete final rank.

    This audit does not invoke the learned selector or its ranking helpers. The
    separate original full model replay establishes the branch return inputs.
    """
    candidates, identifiers = selection["champion_candidates"], selection["champion_ids"]
    record = selection["learner"]
    features = scalar_features(report, old_mask, candidates, stay_score)
    recorded_features = np.asarray(record["features"], dtype=np.float64).reshape(-1, 12)
    if recorded_features.shape != features.shape or not np.isfinite(recorded_features).all():
        raise ValueError("independent shortlist feature shape differs")
    feature_error = float(np.max(np.abs(features-recorded_features))) if len(features) else 0.
    beta, means, scales = (np.asarray(fitted[k], dtype=np.float64) for k in ("beta", "means", "scales"))
    standardized = (features-means)/scales
    residuals = np.asarray([beta[0]+math.fsum(float(row[j]*beta[j+1]) for j in range(12))
                            for row in standardized])
    advantages = features[:, 0] + residuals
    errors = [feature_error]
    for key, expected in (("standardized_features", standardized),
                          ("predicted_residuals", residuals), ("predicted_advantages", advantages)):
        actual = np.asarray(record[key], dtype=np.float64)
        if key == "standardized_features":
            actual = actual.reshape(-1, 12)
        if actual.shape != expected.shape or not np.isfinite(actual).all():
            raise ValueError("independent shortlist prediction shape/finite differs")
        errors.append(float(np.max(np.abs(actual-expected))) if actual.size else 0.)
    if max(errors) > 1e-12:
        raise ValueError("independent deployment feature/score audit differs")
    zero = bool(np.all(beta == 0))
    if record["zero_beta_fallback"] != zero:
        raise ValueError("independent zero coefficient status differs")

    def rank(i):
        c = candidates[i]
        first = c["predicted_total_J"] if zero else float(advantages[i])
        return (first, c["predicted_total_served"], -c["path"], -c["duration"], -c["member"], -c["site"])

    order = sorted(range(len(candidates)), key=rank, reverse=True)
    chosen = order[:2]
    if (selection["ordered_champion_indices"] != order
            or selection["ordered_champion_ids"] != [identifiers[i] for i in order]
            or selection["shortlist_indices"] != chosen
            or selection["shortlist_ids"] != [identifiers[i] for i in chosen]):
        raise ValueError("independent learned shortlist order differs")
    branches = selection["branches"]
    if ([b["id"] for b in branches] != ["stay", *[identifiers[i] for i in chosen]]
            or branches[0]["stationary_candidate"] is not None
            or [b["stationary_candidate"] for b in branches[1:]] != [candidates[i] for i in chosen]):
        raise ValueError("complete top2-plus-stay branch menu differs")

    def complete_rank(b):
        c, value = b["stationary_candidate"], b["summary"]
        rest = (0., 0, 0, 0) if c is None else (-c["path"], -c["duration"], -c["member"], -c["site"])
        return (value["total_J"], value["total_served"], *rest)

    best = max(branches, key=complete_rank)
    final = best if best["summary"]["total_J"] > branches[0]["summary"]["total_J"] else branches[0]
    if (selection["selected_branch"] != final["id"]
            or selection["selected_physical_identity"] != final["physical_identity"]
            or selection["initiated"] != (final["id"] != "stay")):
        raise ValueError("independent exact final selection/stay tie differs")
    distances = 50*int(old_mask).bit_count()+sum(50*int(c["predicted_mask"]).bit_count()
        +(int(c["predicted_mask"]) & ~(1 << c["member"])).bit_count() for c in candidates)
    if record["feature_distance_pairs"] != distances or record["coefficient_products"] != 13*len(candidates):
        raise ValueError("independent learned feature/inference work differs")
    return {"maximum_scalar_feature_error": feature_error, "maximum_scalar_score_error": max(errors[1:]),
            "champions": len(candidates), "modeled_branches": len(branches),
            "selected_branch": final["id"], "shortlist_ids": selection["shortlist_ids"],
            "all_predicted_advantages_negative": bool(len(advantages) and np.all(advantages < 0))}


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
    policy = make_program(row["arm"], fitted if row["arm"] == "L2_E" else None, reference=True)
    old_mask, totals, calls = 255, empty_counts(), {kind: 0 for kind in KINDS}
    predictions = option_ticks = banks = 0
    branch_certificates = []
    shortlist_audit = None
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
            if row["arm"] == "L2_E":
                shortlist_audit = verify_shortlist(raw["states"][40], old_mask,
                    policy.selection, policy.plan["stay_score"], fitted)
        trace_counts(decision, totals)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        predictions += 216*int("motion" in decision)
        if "option" in decision:
            option_ticks += int(decision["option"]["counts"]["model_ticks"])
        old_mask = new_mask
    actual_metrics = complete_metrics(raw)
    if (actual_metrics != row["metrics"] or option_metrics(policy.plan, raw) != row["option"]
            or policy.selection != row["selection"] or totals != row["candidate_counts"]
            or calls != row["calls"] or predictions != row["position_predictions"]
            or option_ticks != row["option_model_ticks"] or banks != 1 or not actual_metrics["capacity_identity_holds"]):
        raise ValueError("native reduction/control count differs")
    return {"counts": totals, "reuse": branch_certificates, "shortlist_audit": shortlist_audit}


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
            or summary["new_fits"] != 0 or summary["updates"] != 0 or summary["inherited_B06_fits"] != 1
            or summary["new_training_acquisition"] != 0):
        raise ValueError("complete fixed evaluation worker missing")
    validate_operation(summary, out)
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
    names = METRIC_NAMES
    indices = np.random.RandomState(BOOTSTRAP_SEED).randint(0,16,(10000,16))
    contrasts = CONTRASTS
    comparisons = {f"{a}-{b}": {m: _paired(np.asarray([panel[a,w]["metrics"][m]-panel[b,w]["metrics"][m] for w in WORLD_IDS]),
        list(WORLD_IDS), indices) for m in names} for a,b in contrasts}
    aggregates = {a: {m: float(np.mean([panel[a,w]["metrics"][m] for w in WORLD_IDS])) for m in names} for a in ARMS}
    timing_names = tuple(rows[0]["timing"])
    timings = {a: {m: float(np.mean([panel[a,w]["timing"][m] for w in WORLD_IDS])) for m in timing_names} for a in ARMS}
    timing_comparisons = {f"{a}-{b}": {m: _paired(np.asarray([panel[a,w]["timing"][m]-panel[b,w]["timing"][m] for w in WORLD_IDS]),
        list(WORLD_IDS), indices) for m in timing_names} for a,b in contrasts}
    if any(not np.isfinite(v) or v < 0 for r in rows for v in r["timing"].values()):
        raise ValueError("invalid recorded complete cost timing")
    ratios = {}
    for denominator in ("K2_E", "T_E"):
        ratios["L2_E/" + denominator] = {}
        for name in ("selection_cpu_seconds", "controller_cpu_seconds", "cpu_seconds",
                     "selection_wall_seconds", "controller_wall_seconds", "wall_seconds"):
            numerator_values = np.asarray([panel["L2_E",w]["timing"][name] for w in WORLD_IDS])
            denominator_values = np.asarray([panel[denominator,w]["timing"][name] for w in WORLD_IDS])
            if np.any(denominator_values <= 0):
                raise ValueError("positive complete timing required for ratios")
            ratios["L2_E/" + denominator][name] = {
                "ratio_of_means": float(numerator_values.mean()/denominator_values.mean()),
                "p95_world_bootstrap": np.quantile(numerator_values[indices].mean(axis=1)
                    /denominator_values[indices].mean(axis=1), [.025,.975]).tolist()}
    for w in WORLD_IDS:
        l2, k2 = panel["L2_E",w], panel["K2_E",w]
        if (len(l2["model_branches"]) != len(k2["model_branches"])
                or l2["selection"]["candidate_count"] != k2["selection"]["candidate_count"]):
            raise ValueError("shortlist branch/bank resources differ")
    shortlist_audits = [a["shortlist_audit"] for a in audits if a["shortlist_audit"] is not None]
    if len(shortlist_audits) != 16:
        raise ValueError("complete independent learned shortlist audit missing")
    bindings = [r[f] for r in rows for f in ("raw", "decisions", "stationary_candidates")]
    bindings += [b[f] for r in rows for b in r["model_branches"] for f in ("raw", "decisions")]
    if len({b["path"] for b in bindings}) != len(bindings):
        raise ValueError("duplicated evaluation artifact path")
    result = {"status": "complete", "source_sha": summary["launch_sha"], "config_artifact": summary["config_artifact"],
              "fit_artifact": summary["config"]["fit_artifact"], "episodes_verified":64, "native_steps_verified":32000,
              "native_snapshots_verified":32064, "new_fits":0, "updates":0, "inherited_B06_fits":1, "new_training_acquisition":0,
              "all_native_physics_observations_actions_checked":True,
              "all_stationary_candidates_and_original_full_models_replayed":True,
              "all_optimized_model_arrays_bitwise_equal_original":True,
              "all_cycle_sources_and_costs_independently_reconstructed":True,
              "all_prefixes_exact_through_t39":True, "worker_native_candidate_counts":totals,
              "worker_actual_costs":costs, "worker_logical_costs_without_reuse":logical_costs,
              "reader_full_replay_costs":dict(logical_costs, native_steps=0, episodes=0),
              "reader_native_episodes_reconstructed":64, "reader_new_native_transitions":0,
              "worker_native_control_requests":native_requests, "worker_actual_model_requests":actual_requests,
              "worker_logical_model_requests":logical_requests,
              "reuse": {"computed_ticks":costs["model_physical_transitions"],
                        "reused_ticks":sum(c["reused_ticks"] for c in certificates),
                        "branches_with_recurrence":sum(c["first_repeat"] is not None for c in certificates),
                        "branches_without_recurrence":sum(c["first_repeat"] is None for c in certificates)},
              "shortlist_audits":shortlist_audits,
              "maximum_deployment_scalar_feature_error":max(a["maximum_scalar_feature_error"] for a in shortlist_audits),
              "maximum_deployment_scalar_score_error":max(a["maximum_scalar_score_error"] for a in shortlist_audits),
              "all_shortlist_orders_and_exact_final_choices_independently_checked":True,
              "matched_shortlist_branch_counts":True,
              "aggregates":aggregates, "comparisons":comparisons, "timing_ratios":ratios,
              "primary_contrast":"L2_E-K2_E", "no_adoption_threshold":True,
              "mean_recorded_timings":timings, "paired_timing_comparisons":timing_comparisons,
              "L2_E_feature_distance_pairs":sum(r["selection"]["learner"]["feature_distance_pairs"] for r in rows if r["arm"] == "L2_E"),
              "L2_E_coefficient_products":sum(r["selection"]["learner"]["coefficient_products"] for r in rows if r["arm"] == "L2_E"),
              "worlds":worlds, "bulk_bytes":sum(b["bytes"] for b in bindings),
              "historical_fit_timing_not_new":fit_summary["total_timing"],
              "prior_paid_acquisition_CPU_seconds":1222.447506,
              "uncertainty_scope":"paired percentile bootstrap over16fresh worlds conditional on one fixed learned fit and four programs; 16 training worlds, not58 independent training units; fresh evaluation models cannot train or tune the fixed artifact",
              "bootstrap":{"seed":BOOTSTRAP_SEED,"replicates":10000},
              "timing":{"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu,
                        "process_resources":process_resources()}}
    write_json(out/"reading.json",result)
    return result
