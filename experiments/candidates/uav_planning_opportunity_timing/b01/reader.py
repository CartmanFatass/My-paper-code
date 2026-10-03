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
from experiments.candidates.uav_fleet_transmission.b04.study import episode_costs
from experiments.candidates.uav_parent_adaptation.b08_exact_planning_reuse.reader import verify_certificate
from .evidence import load_payload, segment_payload
from .host import AUDIT_WORLD, WORLD_IDS, seed
from .inputs import (ARMS, BOOTSTRAP_SEED, DIRECTION, aggregate_costs, artifact, check_costs,
                     checked_file, fixed_config, json_record, load_arrays, load_catalog, load_trace,
                     mission_order, payload_binding, same_array, same_payload, same_record)
from .meter import resources

METRICS = ("J", "served", "quality", "height_penalty", "mean_path_per_uav", "ineligible",
           "eligible_unserved", "served_p05", "served_min", "zero_steps", "longest_zero_run", "active_mean")
CONTRASTS = (("A_E", "A2"), ("G_E", "A2"), ("G_E", "G2"), ("A_E", "G_E"), ("A2", "G2"), ("A_E", "G2"))


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


def _decode_envelope(value):
    return np.frombuffer(bytes.fromhex(value["hex"]), dtype=np.dtype(value["dtype"])).reshape(value["shape"]).copy()


def _catalog(row, out):
    catalog = load_catalog(checked_file(out, row["evidence_catalog"]))
    if set(catalog) != {"plans", "selections", "banks", "model_branches", "candidate_banks", "segments"}:
        raise ValueError("evidence catalog fields differ")
    for name in ("model_branches", "candidate_banks", "segments"):
        identities = [item["id"] for item in catalog[name]]
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate evidence identity")
    times = {"40", str(row["second_t"])}
    if set(catalog["plans"]) != times or set(catalog["selections"]) != times:
        raise ValueError("missing or extra actual planning opportunity")
    first = catalog["plans"]["40"]
    expected_second = 120 if row["arm"] in ("G2", "A2") else (
        50 if not first["initiated"] else 40 + first["duration"] + 10)
    if row["second_t"] != expected_second:
        raise ValueError("actual second clock violates selected rule")
    return catalog


def _validate_arrays(raw, scene):
    shapes = {"positions": (501, 8, 3), "observations": (501, 8, 104), "states": (501, 133),
        "sinr": (501, 8, 50), "connections": (501, 8, 50), "peer_sinr": (501, 8, 8),
        "visible_users": (501, 8), "visible_peers": (501, 8), "actions": (500, 8, 3),
        "mask": (500,), "components": (500, 4), "scalar_reward": (500,), "terminal": (500,),
        "users": (50, 2), "history_positions": (500, 8, 3), "history_commands": (500, 8, 3),
        "history_users": (500, 50, 2), "history_next_t": (500,)}
    if set(raw) != set(shapes):
        raise ValueError("saved native array fields differ")
    for name, shape in shapes.items():
        if raw[name].shape != shape or (name not in ("sinr", "peer_sinr") and not np.isfinite(raw[name]).all()):
            raise ValueError(f"native array shape/finiteness differs: {name}")
    if raw["actions"].dtype != np.float32 or not np.isin(raw["actions"], [-1, 0, 1]).all():
        raise ValueError("native command dtype/alphabet differs")
    same_array(raw["terminal"], np.arange(500) == 499, "native terminal horizon")
    same_array(raw["users"], scene.user_positions, "bound user stream")
    same_array(raw["positions"][0], scene.uav_positions, "bound fleet stream")


def read_episode(row, out, scene, meter):
    # Import only the explicit program constructor. Its reuse=False path invokes
    # frozen B03/B04 reference simulations for G2/A2 and the new full loop for E.
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
    first = catalog["plans"]["40"]
    if row["arm"] in ("G_E", "A_E") and first["initiated"]:
        if not (int(raw["mask"][row["second_t"] - 1]) & (1 << first["member"])):
            raise ValueError("first mover lost its required early hold")
        second_selection = catalog["selections"][str(row["second_t"])]
        if any(b["plan"] is not None and b["plan"]["member"] == first["member"]
               for b in second_selection["branches"]):
            raise ValueError("first mover illegally entered early second menu")
    result = {"phase": row["phase"], "world_id": row["world_id"], "arm": row["arm"],
        "verified_catalog_before_compaction": row["evidence_catalog"], "complete": True,
        "all_native_snapshots": 501, "native_motion_reward_checks": 500,
        "full_reader_costs": costs, "uncompressed_model_ticks": costs["model_physical_transitions"],
        "segment_checks": work_records, "forecasts": [forecast_comparison(row, catalog, raw, t, out)
                                                         for t in (40, row["second_t"])],
        "plan_readings": {str(t): plan_reading(catalog["plans"][str(t)], raw, t)
                          for t in (40, row["second_t"])},
        "choice_reading": choice_reading(catalog), "individual_continuity": individual_continuity(raw),
        "timing": {"wall_seconds": time.monotonic() - start_wall,
                   "cpu_seconds": resources()["cpu_seconds"] - start_usage["cpu_seconds"]}}
    return result, catalog


def forecast_comparison(row, catalog, raw, start, out):
    identifier = catalog["selections"][str(start)]["selected_model_branch"]
    branch = next(b for b in catalog["model_branches"] if b["id"] == identifier)
    model = load_arrays(checked_file(out, branch["raw"]))
    end = row["second_t"] if row["arm"] in ("G2", "G_E") and start == 40 else 500
    count = end - start
    model_rewards = model["reward_components"][:count]
    served = raw["connections"][start + 1:end + 1].sum(axis=(1, 2))
    predicted_j = sum(float(x) for x in model_rewards[:, 0])
    actual_j = sum(float(x) for x in raw["components"][start:end, 3])
    return {"start_t": start, "end_t": end, "model_branch": identifier,
        "scope": "C-only prediction before its unmodeled second decision" if end < 500
                 else "complete forecast against actual suffix including any fresh second replan",
        "model_total_J": predicted_j, "native_total_J": actual_j, "model_minus_native_J": predicted_j - actual_j,
        "model_minus_native_served": int(model_rewards[:, 1].sum()) - int(served.sum()),
        "equal_per_tick_service": bool(np.array_equal(model_rewards[:, 1], served)),
        "equal_commands": bool(np.array_equal(model["actions"][:count], raw["actions"][start:end])),
        "equal_masks": bool(np.array_equal(model["masks"][:count], raw["mask"][start:end])),
        "max_coordinate_abs_error_m": float(np.max(np.abs(model["positions"][:count + 1] - raw["positions"][start:end + 1])))}


def plan_reading(plan, raw, start):
    if not plan["initiated"]:
        return {"initiated": False, "physical_identity": "stay"}
    arrival, member = plan["arrival_t"], plan["member"]
    active = (raw["mask"][arrival:] & (1 << member)) != 0
    off = np.flatnonzero(~active)
    position = raw["positions"]
    path = np.linalg.norm(np.diff(position[start:arrival + 1, member], axis=0), axis=1)
    return {"initiated": True, "member": member, "site": plan["site"], "duration": plan["duration"],
        "arrival_t": arrival, "physical_identity": physical_identity(plan),
        "actual_arrival_mask": int(raw["mask"][arrival]), "actual_transit_path_m": float(path.sum()),
        "zero_path": bool(np.all(path == 0)),
        "active_ticks_before_first_remute": len(active) if not len(off) else int(off[0]),
        "first_remute_t": None if not len(off) else arrival + int(off[0]),
        "transit_J": float(sum(float(x) for x in raw["components"][start:arrival, 3])),
        "transit_served_user_ticks": int(raw["connections"][start + 1:arrival + 1].sum()),
        "arrival_hold_J": float(raw["components"][arrival:arrival + 10, 3].sum())}


def choice_reading(catalog):
    result = {}
    for clock, selection in catalog["selections"].items():
        branches = selection["branches"]
        physical = [b["physical_identity"] for b in branches]
        execution = [json.dumps(b["modeled_execution_identity"], sort_keys=True) for b in branches]
        result[clock] = {"selected_branch": selection["selected_branch"], "branch_count": len(branches),
            "physical_alias_count": len(physical) - len(set(physical)),
            "execution_alias_count": len(execution) - len(set(execution)),
            "nonpositive_champions_kept": sum(b["plan"] is not None and
                 b["plan"]["predicted_total_J"] <= b["plan"]["stay_total_J"] for b in branches),
            "candidate_second_clocks": [{"branch": b["id"], "second_t": b.get("second_t",
                b["summary"].get("second_t"))} for b in branches]}
    return result


def individual_continuity(raw):
    served = raw["connections"][1:].any(axis=1)
    rows = []
    for user in range(50):
        values = served[:, user]
        gaps, start = [], None
        for t, yes in enumerate(values):
            if not yes and start is None:
                start = t
            if yes and start is not None:
                gaps.append({"start_tick": start, "end_tick_exclusive": t, "length": t - start,
                             "left_censored": start == 0, "right_censored": False})
                start = None
        if start is not None:
            gaps.append({"start_tick": start, "end_tick_exclusive": 500, "length": 500 - start,
                         "left_censored": start == 0, "right_censored": True})
        rows.append({"user": user, "served_user_ticks": int(values.sum()),
                     "longest_unserved_gap": max((g["length"] for g in gaps), default=0), "gaps": gaps})
    return {"clock": "post-transition ticks0..499; censored mission edges retained", "per_user": rows,
            "never_served_users": sum(r["served_user_ticks"] == 0 for r in rows),
            "worst_longest_unserved_gap": max(r["longest_unserved_gap"] for r in rows),
            "total_served_user_ticks": int(served.sum())}


def summarize_reading(summary, out):
    rows = [row for row in summary["episodes"] if row["phase"] == "result"]
    panel = {(r["world_id"], r["arm"]): r for r in rows}
    if len(panel) != 64:
        raise ValueError("complete16-world paired result panel required")
    sample = np.random.default_rng(BOOTSTRAP_SEED).integers(0, 16, size=(10000, 16))
    comparisons = {}
    for a, b in CONTRASTS:
        metrics_read = {}
        for metric in METRICS:
            values = np.asarray([panel[w, a]["metrics"][metric] - panel[w, b]["metrics"][metric] for w in WORLD_IDS], np.float64)
            metrics_read[metric] = {"per_world": [{"world_id": w, "difference": float(x)} for w, x in zip(WORLD_IDS, values)],
                "mean": float(values.mean()), "median": float(np.median(values)),
                "positive": int((values > 0).sum()), "zero": int((values == 0).sum()), "negative": int((values < 0).sum()),
                "minimum_difference": float(values.min()), "maximum_difference": float(values.max()),
                "paired_world_percentile_95": np.quantile(values[sample].mean(axis=1), [.025, .975]).tolist()}
            if metric == "J":
                metrics_read[metric].update(adverse_worlds=int((values < 0).sum()), worst_J_difference=float(values.min()))
        comparisons[a + "-" + b] = metrics_read
    worker_costs = aggregate_costs(summary["episodes"])
    reader_costs = {name: sum(r["full_reader_costs"][name] for r in summary["readings"]) for name in worker_costs}
    same_record(reader_costs, worker_costs, "full reader logical cost equals worker logical bill")
    return {"status": "COMPLETE", "launch_sha": summary["launch_sha"],
        "scientific_scope": "exploratory complete ordinary timing/anticipation package; no fit, learned timing or confirmation",
        "audit_world_excluded_from_estimand": AUDIT_WORLD, "result_world_ids": list(WORLD_IDS),
        "all_native_snapshots_reconstructed": 68 * 501, "all_native_motion_reward_checks": 34000,
        "all_branches_banks_and_native_decisions_reconstructed": True,
        "worker_reuse_independently_checked_against_uncompressed_arrays": True,
        "primary": "A_E-A2", "comparisons": comparisons,
        "arm_means": {arm: {metric: float(np.mean([panel[w, arm]["metrics"][metric] for w in WORLD_IDS]))
                              for metric in METRICS} for arm in ARMS},
        "logical_worker_costs": worker_costs, "uncompressed_reader_costs": reader_costs,
        "actual_worker_requests": sum(r["reuse_costs"]["worker_actual_requests"] for r in summary["episodes"]),
        "computed_worker_model_ticks": sum(r["reuse_costs"]["computed_model_ticks"] for r in summary["episodes"]),
        "reused_worker_model_ticks": sum(r["reuse_costs"]["reused_model_ticks"] for r in summary["episodes"]),
        "worker_episode_cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in summary["episodes"]),
        "reader_episode_cpu_seconds": sum(r["timing"]["cpu_seconds"] for r in summary["readings"]),
        "episode_readings": summary["readings"],
        "interval_scope": "descriptive paired-world uncertainty; same bootstrap world draws for every arm/metric; no equivalence margin"}
