"""Full uncompressed replay and independent saved-native formula reconstruction."""
from copy import deepcopy
import json
from types import SimpleNamespace
import time

import numpy as np

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_fleet_transmission.control import predict_next
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.reader import _native_view, _public_state, _same
from experiments.candidates.uav_fleet_transmission.study import metrics
from experiments.candidates.uav_fleet_transmission.b02.controller import KINDS, empty_counts, trace_counts
from experiments.candidates.uav_fleet_transmission.b02.study import COMPONENTS
from experiments.candidates.uav_fleet_transmission.b03.option import physical_identity
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.reader import verify_certificate
from experiments.candidates.uav_planning_opportunity_timing.b01.evidence import load_payload, segment_payload
from .host import AUDIT_WORLD, WORLD_IDS, seed
from .inputs import (ARMS, BOOTSTRAP_SEED, DIRECTION, aggregate_costs, artifact, check_costs,
                     checked_file, fixed_config, json_record, load_arrays, load_catalog, load_trace,
                     mission_order, payload_binding, same_array, same_payload, same_record, episode_costs, CONTRASTS)
from .meter import resources

from experiments.candidates.uav_planning_opportunity_timing.b01.reader import (
    _decode_envelope, _validate_arrays, plan_reading, choice_reading, individual_continuity,
)

METRICS = ("J", "served", "quality", "height_penalty", "mean_path_per_uav", "ineligible",
           "eligible_unserved", "served_p05", "served_min", "zero_steps", "longest_zero_run", "active_mean")


def validate_worker(summary, out):
    config = summary["config"]
    fixed = fixed_config()
    if set(config) != set(fixed) | {"launch_sha", "admission_command_sha256", "versions"}:
        raise ValueError("unexpected executable config fields")
    for key, value in fixed.items():
        same_record(config[key], value, f"fixed input/{key}")
    if (summary["launch_sha"] != config["launch_sha"] or
            json.loads(checked_file(out, summary["config_artifact"]).read_text()) != config):
        raise ValueError("worker/source config binding differs")
    manifest = json.loads((out / "launch-manifest.json").read_text())
    if (manifest.get("acceptance") != "accepted" or manifest.get("sha") != summary["launch_sha"]
            or manifest.get("direction") != DIRECTION
            or manifest.get("command_sha256") != config["admission_command_sha256"]):
        raise ValueError("accepted native operation binding differs")
    expected = mission_order()
    if [(r["phase"], r["world_id"], r["arm"]) for r in summary["episodes"]] != expected:
        raise ValueError("missing, duplicated or reordered selected mission")
    if [(r["phase"], r["world_id"], r["arm"]) for r in summary["readings"]] != expected:
        raise ValueError("missing, duplicated or reordered full reading")
    for row in summary["episodes"]:
        if row["n"] != 8 or row["steps"] != 500 or row["complete"] is not True:
            raise ValueError("incomplete mission")
        if row["runtime_seed"] != seed(row["world_id"], 3, 8):
            raise ValueError("runtime stream differs")
        check_costs(row["costs"], row["arm"])
    same_record(aggregate_costs(summary["episodes"]), summary["logical_worker_costs"], "whole worker bill")
    if (sum(len(row["opportunity_times"]) for row in summary["episodes"]) != 204
            or len(summary["prefix_checks"]) != 17
            or [(r["phase"], r["world_id"]) for r in summary["prefix_checks"]]
                != [(phase, w) for phase, w, _ in expected[::4]]):
        raise ValueError("incomplete actual choices or matched-world identity readings")


def _catalog(row, out):
    catalog = load_catalog(checked_file(out, row["evidence_catalog"]))
    if set(catalog) != {"plans", "selections", "banks", "model_branches", "candidate_banks", "segments"}:
        raise ValueError("evidence catalog fields differ")
    for name in ("model_branches", "candidate_banks", "segments"):
        identities = [item["id"] for item in catalog[name]]
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate evidence identity")
    times = row["opportunity_times"]
    expected_count = 4 if row["arm"] in ("G_E4", "A_E4") else 2
    if (len(times) != expected_count or any(type(t) is not int for t in times)
            or times[0] != 40 or times != sorted(set(times))
            or set(catalog["plans"]) != {str(t) for t in times}
            or set(catalog["selections"]) != {str(t) for t in times}):
        raise ValueError("missing, repeated or extra actual planning opportunity")
    for i, t in enumerate(times):
        if t % 10 or not 40 <= t <= 190:
            raise ValueError("actual clock outside the fixed absolute schedule")
        plan, selection = catalog["plans"][str(t)], catalog["selections"][str(t)]
        if plan.get("start_t", 40) != t or selection["start_t"] != t:
            raise ValueError("actual plan/selection clock binding differs")
        same_record(selection["selected_plan"], plan, "selected/installed plan")
        if plan["initiated"]:
            if plan["duration"] not in (10, 20, 30, 40) or plan["arrival_t"] != t + plan["duration"]:
                raise ValueError("invalid commanded actual arrival")
        elif plan["duration"] != 0 or plan["arrival_t"] is not None:
            raise ValueError("stay carries an actual commitment")
        if i + 1 < len(times):
            expected = 120 if row["arm"] == "A2" else t + (plan["duration"] if plan["initiated"] else 0) + 10
            if times[i + 1] != expected:
                raise ValueError("actual opportunity clock violates selected rule")
    return catalog


def read_episode(row, out, scene, meter):
    # Import only the explicit program constructor. Its reuse=False path invokes
    # frozen B03/B04 reference simulations for A2 and new full loops for E/rolling.
    from .study import make_policy
    start_wall, start_usage = time.monotonic(), resources()
    raw = load_arrays(checked_file(out, row["raw"]))
    decisions = load_trace(checked_file(out, row["decisions"]))
    catalog = _catalog(row, out)
    _validate_arrays(raw, scene)
    if len(decisions) != 500:
        raise ValueError("incomplete issued decision trace")
    branches = {record["id"]: record for record in catalog["model_branches"]}
    checked_branches, checked_banks, checked_segments, work_records = [], [], [], []

    def branch_sink(identifier, result):
        i = len(checked_branches)
        if i >= len(catalog["model_branches"]):
            raise ValueError("extra replayed complete branch")
        record = catalog["model_branches"][i]
        if record["id"] != identifier:
            raise ValueError("complete model branch order/identity differs")
        same_payload(result, load_payload(out, record), f"full uncompressed branch/{identifier}")
        summary = result["summary"]
        if summary["model_transitions"] != 500 - summary["start_t"]:
            raise ValueError("full modeled branch has incomplete suffix")
        checked_branches.append(identifier)
        meter.check()

    def candidate_sink(identifier, rows):
        i = len(checked_banks)
        if i >= len(catalog["candidate_banks"]):
            raise ValueError("extra replayed stationary bank")
        record = catalog["candidate_banks"][i]
        if record["id"] != identifier:
            raise ValueError("stationary bank identity/order differs")
        same_array(np.load(checked_file(out, record["raw"]), allow_pickle=False), rows,
                   f"complete regenerated stationary rows/{identifier}")
        checked_banks.append(identifier)
        meter.check()

    def segment_sink(identifier, result):
        i = len(checked_segments)
        if i >= len(catalog["segments"]):
            raise ValueError("extra regenerated segment")
        saved = catalog["segments"][i]
        if saved["id"] != identifier:
            raise ValueError("segment identity/order differs")
        same_payload(result, segment_payload(out, saved, branches), f"fresh uncompressed segment/{identifier}")
        cert = result["certificate"]
        reference = SimpleNamespace(payload={k: result[k] for k in ("arrays", "summary", "decisions")},
            start=cert["start_t"], end=cert["end_t"], kind=saved["kind"], plan_bound=True,
            expected_plan=deepcopy(cert["plan"]), entry_mask=cert["entry"]["mask"],
            entry_commands=_decode_envelope(cert["entry"]["commands"]),
            entry_users=_decode_envelope(cert["entry"]["users"]))
        work = verify_certificate(identifier, {key: saved[key] for key in ("id", "certificate", "scientific")},
                                  reference, True)
        work_records.append(dict(id=identifier, **work))
        checked_segments.append(identifier)
        meter.check()

    policy = make_policy(row["arm"], reuse=False, branch_sink=branch_sink,
                         candidate_sink=candidate_sink, segment_sink=segment_sink)
    old_mask, totals = 255, empty_counts()
    calls, predictions = {kind: 0 for kind in KINDS}, 0
    view = _native_view(8, raw["users"], 500)
    for t in range(501):
        meter.check()
        positions = raw["positions"][t]
        mask = mask_bits(255 if t == 0 else int(raw["mask"][t - 1]), 8)
        loss = uav_radio.free_space_user_path_loss(positions, raw["users"])
        sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=mask)
        connections = uav_radio.greedy_connection_assignment(sinr, 0., 10)
        _same(raw["sinr"][t], sinr, f"native user radio/{t}")
        _same(raw["connections"][t], connections, f"native assignment/{t}")
        view.uav_positions, view.sinr_matrix, view.connections = positions, sinr, connections
        view._transmitter_mask = mask
        view._uav_uav_path_loss_matrix = MultiUAVEnv._compute_uav_path_loss_matrix(view)
        view.uav_sinr_matrix = MultiUAVEnv._compute_uav_uav_sinr_matrix(view)
        view.current_step = t
        _same(raw["peer_sinr"][t], view.uav_sinr_matrix, f"native peer radio/{t}")
        _same(raw["states"][t], _public_state(positions, raw["users"], t, 500), f"public FP32 state/{t}")
        for member in range(8):
            observation = MultiUAVEnv._get_observation_vectorized(view, f"uav_{member}")["obs"]
            _same(raw["observations"][t, member], observation, f"native observation/{t}/{member}")
        _same(raw["visible_users"][t], [len(view._local_user_entries(i)[0][:20]) for i in range(8)], f"user slots/{t}")
        _same(raw["visible_peers"][t], [len(view._local_uav_entries(i)[0][:10]) for i in range(8)], f"peer slots/{t}")
        if t:
            UAVBaseStationEnv._compute_reward(view)
            components = np.asarray([view.reward_info[key] for key in COMPONENTS])
            _same(raw["components"][t - 1], components, f"native reward/{t}")
            if abs(raw["scalar_reward"][t - 1] * 8 - components[3]) > 1e-14:
                raise ValueError("scalar/native N8 scaling differs")
        if t == 500:
            break
        _same(raw["positions"][t + 1], predict_next(positions, raw["actions"][t]), f"native motion/{t}")
        command, new_mask, decision = policy.select(t, raw["states"][t] if t % 10 == 0 else None, old_mask)
        same_record(decision, decisions[t], f"entire native private-history decision/{t}")
        same_array(raw["actions"][t], command, f"issued command/{t}")
        for name, expected in (("history_positions", policy.controller.positions),
                               ("history_commands", policy.controller.commands),
                               ("history_users", policy.controller.users),
                               ("history_next_t", policy.controller.next_t)):
            same_array(raw[name][t], expected, f"actual private history/{name}/{t}")
        if raw["mask"][t] != new_mask or (t % 10 and new_mask != old_mask):
            raise ValueError("native issued mask/hold differs")
        trace_counts(decision, totals)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        predictions += 216 * int("motion" in decision)
        old_mask = new_mask
    same_record(json_record(policy.plans), catalog["plans"], "actual plans")
    same_record(json_record(policy.selections), catalog["selections"], "actual selections")
    same_record(json_record(policy.banks), catalog["banks"], "all stationary bank ledgers")
    for key, actual in (("metrics", metrics(raw, 8)), ("native_candidate_counts", totals),
                        ("calls", calls), ("position_predictions", predictions)):
        same_record(actual, row[key], f"native aggregate/{key}")
    if (len(checked_branches) != len(catalog["model_branches"]) or len(checked_banks) != len(catalog["candidate_banks"])
            or len(checked_segments) != len(catalog["segments"]) or not row["metrics"]["capacity_identity_holds"]):
        raise ValueError("incomplete replay or failed capacity identity")
    costs = episode_costs(catalog, totals, predictions)
    same_record(costs, row["costs"], "full reader regenerated query ledger")
    check_costs(costs, row["arm"])
    times = row["opportunity_times"]
    if row["arm"] != "A2":
        for i, start in enumerate(times[:-1]):
            plan = catalog["plans"][str(start)]
            if not plan["initiated"]:
                continue
            member, next_t = plan["member"], times[i + 1]
            if not (int(raw["mask"][next_t - 1]) & (1 << member)):
                raise ValueError("immediately previous mover lost its required early hold")
            following = catalog["selections"][str(next_t)]
            if any(b["plan"] is not None and b["plan"]["member"] == member for b in following["branches"]):
                raise ValueError("immediately previous mover illegally entered next menu")
    result = {"phase": row["phase"], "world_id": row["world_id"], "arm": row["arm"],
        "opportunity_times": times, "verified_catalog_before_compaction": row["evidence_catalog"], "complete": True,
        "all_native_snapshots": 501, "native_motion_reward_checks": 500,
        "native_reconstruction_counts": {"user_path_loss": 501, "user_sinr": 501, "greedy_assignment": 501,
            "peer_path_loss": 501, "peer_sinr": 501, "observations": 4008, "public_reports": 501,
            "user_visibility": 4008, "peer_visibility": 4008, "motion": 500, "reward": 500},
        "full_reader_costs": costs, "uncompressed_model_ticks": costs["model_physical_transitions"],
        "segment_checks": work_records, "forecasts": forecast_comparisons(row, catalog, raw, out),
        "plan_readings": {str(t): actual_choice_reading(catalog, raw, t, ordinal + 1)
                          for ordinal, t in enumerate(times)},
        "choice_reading": choice_reading(catalog), "individual_continuity": individual_continuity(raw),
        "timing": {"wall_seconds": time.monotonic() - start_wall,
                   "cpu_seconds": resources()["cpu_seconds"] - start_usage["cpu_seconds"]}}
    return result, catalog


def forecast_windows(arm, times):
    """The ranking tail and the actual future actor agree only on these intervals."""
    windows = []
    for ordinal, start in enumerate(times, 1):
        next_t = times[ordinal] if ordinal < len(times) else None
        prefix_only = ((arm == "G_E4" and ordinal < 4)
                       or (arm == "A_E4" and ordinal < 3))
        windows.append((ordinal, start, next_t if prefix_only else 500,
                        "before_next_actual_selection" if prefix_only else "complete_remaining_program"))
        if arm == "A_E4" and ordinal == 3:
            windows.append((ordinal, start, next_t, "third_choice_additional_prefix_diagnostic"))
    return windows


def forecast_comparisons(row, catalog, raw, out):
    readings = []
    for ordinal, start, end, scope in forecast_windows(row["arm"], row["opportunity_times"]):
        selection = catalog["selections"][str(start)]
        identifier = selection["selected_model_branch"]
        branch = next(b for b in catalog["model_branches"] if b["id"] == identifier)
        model = load_arrays(checked_file(out, branch["raw"]))
        count = end - start
        reward = model["reward_components"][:count]
        served = raw["connections"][start + 1:end + 1].sum(axis=(1, 2))
        modeled_j = sum(float(x) for x in reward[:, 0])
        actual_j = sum(float(x) for x in raw["components"][start:end, 3])
        inner = branch["summary"].get("inner_selection")
        next_actual_t = row["opportunity_times"][ordinal] if ordinal < len(row["opportunity_times"]) else None
        next_actual = catalog["selections"][str(next_actual_t)] if next_actual_t is not None else None
        model_next = None
        if inner is not None:
            modeled_t = inner["start_t"]
            model_next = {"modeled_t": modeled_t, "modeled_branch": inner["selected_branch"],
                "modeled_physical_identity": inner["selected_physical_identity"],
                "actual_t": next_actual_t,
                "actual_branch": next_actual["selected_branch"] if next_actual else None,
                "actual_physical_identity": next_actual["selected_physical_identity"] if next_actual else None,
                "same_clock_and_physical_choice": bool(next_actual and modeled_t == next_actual_t
                    and inner["selected_physical_identity"] == next_actual["selected_physical_identity"]),
                "qualification": "modeled next selector is ordinary; actual next is anticipatory at A_E4 ordinals2/3"}
        command = model["actions"][:count]
        actual_command = raw["actions"][start:end]
        readings.append({"ordinal": ordinal, "start_t": start, "end_t": end, "scope": scope,
            "model_branch": identifier, "model_raw": branch["raw"], "native_raw": row["raw"],
            "model_total_J": modeled_j, "native_total_J": actual_j, "model_minus_native_J": modeled_j - actual_j,
            "model_minus_native_served": int(reward[:, 1].sum()) - int(served.sum()),
            "equal_per_tick_service": bool(np.array_equal(reward[:, 1], served)),
            "equal_commands": bool(np.array_equal(command, actual_command)),
            "equal_command_bits": command.dtype == actual_command.dtype and command.tobytes() == actual_command.tobytes(),
            "equal_masks": bool(np.array_equal(model["masks"][:count], raw["mask"][start:end])),
            "different_command_ticks": (start + np.flatnonzero(np.any(command != actual_command, axis=(1, 2)))).tolist(),
            "different_mask_ticks": (start + np.flatnonzero(model["masks"][:count] != raw["mask"][start:end])).tolist(),
            "different_service_ticks": (start + np.flatnonzero(reward[:, 1] != served)).tolist(),
            "max_coordinate_abs_error_m": float(np.max(np.abs(model["positions"][:count + 1] - raw["positions"][start:end + 1]))),
            "modeled_actual_next_choice": model_next,
            "interpretation": "lawful forecast discrepancy is a reading, not a full-reader bitwise failure"})
    return readings


def actual_choice_reading(catalog, raw, start, ordinal):
    plan, selection = catalog["plans"][str(start)], catalog["selections"][str(start)]
    entering_mask = int(raw["mask"][start - 1])
    branches = selection["branches"]
    eligible = np.flatnonzero(~mask_bits(entering_mask, 8)).tolist()
    result = {**plan_reading(plan, raw, start), "ordinal": ordinal, "start_t": start,
        "entering_mask": entering_mask, "eligible_members": eligible, "menu_branches": len(branches),
        "stationary_rows": selection["original_R"]["candidate_count"],
        "requested_choice": selection["selected_branch"], "executed_choice": "commit" if plan["initiated"] else "stay",
        "opportunity_consumed": True, "commanded_duration": plan["duration"],
        "selected_model_branch": selection["selected_model_branch"],
        "same_member_as_earlier_nonadjacent": False}
    members = [b["plan"]["member"] for b in branches if b["plan"] is not None]
    if members != eligible:
        raise ValueError("actual complete member menu differs from entering mask")
    if len(branches) != len(eligible) + 1 or branches[0]["id"] != "stay":
        raise ValueError("actual menu lacks exactly one stay plus each champion")
    if plan["initiated"]:
        arrival, member = plan["arrival_t"], plan["member"]
        motion = np.linalg.norm(np.diff(raw["positions"][start:arrival + 1, member], axis=0), axis=1)
        moved = np.flatnonzero(motion != 0)
        result.update(actual_motion_ticks=int(len(moved)),
            last_nonzero_motion_t=None if not len(moved) else start + int(moved[-1]),
            same_member_as_earlier_nonadjacent=any(p["initiated"] and p["member"] == member
                for clock, p in catalog["plans"].items() if int(clock) < start
                and int(clock) != sorted(int(k) for k in catalog["plans"] if int(k) < start)[-1]))
    else:
        result.update(actual_motion_ticks=None, last_nonzero_motion_t=None)
    return result


def paired_metric(values, sample):
    values = np.asarray(values, np.float64)
    total = float(values.sum())
    order = np.argsort(-values, kind="stable")
    return {"per_world": [{"world_id": w, "difference": float(x)} for w, x in zip(WORLD_IDS, values)],
        "mean": float(values.mean()), "median": float(np.median(values)),
        "positive": int((values > 0).sum()), "zero": int((values == 0).sum()), "negative": int((values < 0).sum()),
        "minimum_difference": float(values.min()), "maximum_difference": float(values.max()),
        "paired_world_percentile_95": np.quantile(values[sample].mean(axis=1), [.025, .975]).tolist(),
        "signed_net_contribution_shares": None if total == 0 else [
            {"world_id": w, "share": float(x / total)} for w, x in zip(WORLD_IDS, values)],
        "largest_positive_contribution_world": int(WORLD_IDS[int(order[0])]) if values[order[0]] > 0 else None,
        "largest_absolute_contribution_world": int(WORLD_IDS[int(np.argmax(np.abs(values)))]),
        "contribution_scope": "signed net shares may exceed1 or be negative; zero total leaves shares undefined"}


def individual_comparison(a, b, panel, read_panel):
    differences, losses_in_team_positive = [], []
    for w in WORLD_IDS:
        left = read_panel[w, a]["individual_continuity"]["per_user"]
        right = read_panel[w, b]["individual_continuity"]["per_user"]
        team_j = panel[w, a]["metrics"]["J"] - panel[w, b]["metrics"]["J"]
        team_service = panel[w, a]["metrics"]["served"] - panel[w, b]["metrics"]["served"]
        if [r["user"] for r in left] != list(range(50)) or [r["user"] for r in right] != list(range(50)):
            raise ValueError("incomplete paired user rows")
        for x, y in zip(left, right):
            delta = x["served_user_ticks"] - y["served_user_ticks"]
            gap = x["longest_unserved_gap"] - y["longest_unserved_gap"]
            row = {"world_id": w, "user": x["user"], "served_tick_difference": delta,
                "longest_gap_difference": gap, "served_ticks_a": x["served_user_ticks"],
                "served_ticks_b": y["served_user_ticks"], "longest_gap_a": x["longest_unserved_gap"],
                "longest_gap_b": y["longest_unserved_gap"],
                "new_never_served": x["served_user_ticks"] == 0 < y["served_user_ticks"],
                "rescued_never_served": y["served_user_ticks"] == 0 < x["served_user_ticks"],
                "team_J_positive": team_j > 0, "team_service_positive": team_service > 0}
            differences.append(row)
            if (delta < 0 or gap > 0) and (team_j > 0 or team_service > 0):
                losses_in_team_positive.append(row)
    return {"per_user_world": differences, "user_world_records": 800,
        "served_tick_positive": sum(r["served_tick_difference"] > 0 for r in differences),
        "served_tick_equal": sum(r["served_tick_difference"] == 0 for r in differences),
        "served_tick_negative": sum(r["served_tick_difference"] < 0 for r in differences),
        "longest_gap_improved": sum(r["longest_gap_difference"] < 0 for r in differences),
        "longest_gap_equal": sum(r["longest_gap_difference"] == 0 for r in differences),
        "longest_gap_worsened": sum(r["longest_gap_difference"] > 0 for r in differences),
        "new_never_served": sum(r["new_never_served"] for r in differences),
        "rescued_never_served": sum(r["rescued_never_served"] for r in differences),
        "worst_served_tick_loss": min(r["served_tick_difference"] for r in differences),
        "worst_longest_gap_increase": max(r["longest_gap_difference"] for r in differences),
        "losses_with_team_positive_metric": losses_in_team_positive,
        "scope": "paired user records nested within16 worlds; gaps retain both mission-edge censoring in episode readings"}


def summarize_reading(summary, out):
    rows = [row for row in summary["episodes"] if row["phase"] == "result"]
    panel = {(r["world_id"], r["arm"]): r for r in rows}
    read_panel = {(r["world_id"], r["arm"]): r for r in summary["readings"] if r["phase"] == "result"}
    if len(rows) != 64 or set(panel) != {(w, arm) for w in WORLD_IDS for arm in ARMS} or set(read_panel) != set(panel):
        raise ValueError("complete16-world paired result panel and readings required")
    sample = np.random.default_rng(BOOTSTRAP_SEED).integers(0, 16, size=(10000, 16))
    comparisons = {}
    for a, b in CONTRASTS:
        metrics_read = {metric: paired_metric([panel[w, a]["metrics"][metric] - panel[w, b]["metrics"][metric]
                                              for w in WORLD_IDS], sample) for metric in METRICS}
        metrics_read["J"].update(adverse_worlds=metrics_read["J"]["negative"],
                                  worst_J_difference=metrics_read["J"]["minimum_difference"])
        comparisons[a + "-" + b] = metrics_read
    worker_costs = aggregate_costs(summary["episodes"])
    reader_costs = {name: sum(r["full_reader_costs"][name] for r in summary["readings"]) for name in worker_costs}
    same_record(reader_costs, worker_costs, "full reader logical cost equals worker logical bill")
    by_arm = {}
    for arm in ARMS:
        worker = [r for r in summary["episodes"] if r["arm"] == arm]
        read = [r for r in summary["readings"] if r["arm"] == arm]
        by_arm[arm] = {"missions": len(worker), "native_steps": sum(r["steps"] for r in worker),
            "opportunities": sum(len(r["opportunity_times"]) for r in worker),
            "worker_cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in worker),
            "reader_cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in read),
            "logical_worker_costs": {k: sum(r["costs"][k] for r in worker) for k in worker_costs},
            "actual_worker_requests": sum(r["reuse_costs"]["worker_actual_requests"] for r in worker),
            "result_opportunity_times": [r["opportunity_times"] for r in worker if r["phase"] == "result"]}
    return {"status": "COMPLETE", "launch_sha": summary["launch_sha"],
        "scientific_scope": "exploratory finite rolling two-layer ordinary planning; no fit, learning or confirmation",
        "new_fits": 0, "updates": 0, "new_teacher_labels": 0,
        "audit_world_excluded_from_estimand": AUDIT_WORLD, "result_world_ids": list(WORLD_IDS),
        "all_native_snapshots_reconstructed": 68 * 501, "all_native_motion_reward_checks": 34000,
        "actual_opportunities": 204, "all_branches_banks_and_native_decisions_reconstructed": True,
        "worker_reuse_independently_checked_against_uncompressed_arrays": True,
        "primary": "A_E4-A_E", "matched_rights": "A_E4-G_E4", "comparisons": comparisons,
        "arm_means": {arm: {metric: float(np.mean([panel[w, arm]["metrics"][metric] for w in WORLD_IDS]))
                              for metric in METRICS} for arm in ARMS},
        "individual_comparisons": {a + "-" + b: individual_comparison(a, b, panel, read_panel) for a, b in CONTRASTS},
        "logical_worker_costs": worker_costs, "uncompressed_reader_costs": reader_costs, "arm_costs": by_arm,
        "actual_worker_requests": sum(r["reuse_costs"]["worker_actual_requests"] for r in summary["episodes"]),
        "computed_worker_model_ticks": sum(r["reuse_costs"]["computed_model_ticks"] for r in summary["episodes"]),
        "reused_worker_model_ticks": sum(r["reuse_costs"]["reused_model_ticks"] for r in summary["episodes"]),
        "worker_episode_cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in summary["episodes"]),
        "reader_episode_cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in summary["readings"]),
        "matched_program_readings": summary["prefix_checks"], "episode_readings": summary["readings"],
        "interval_scope": "paired-world exploratory uncertainty using common bootstrap draws;16 worlds, not68/800 replicates",
        "reading_rule": "late stay is not a package rejection gate; local model gains do not rescue native losses"}

