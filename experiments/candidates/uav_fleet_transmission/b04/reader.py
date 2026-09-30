"""Reconstruct every nested branch and all 48 complete native trajectories."""
import argparse
import json
from pathlib import Path
import re
import time

import numpy as np

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from ..control import predict_next
from ..host import mask_bits
from ..reader import _native_view, _paired, _public_state, _same
from ..study import artifact, metrics, process_resources, write_json
from ..b02.controller import KINDS, empty_counts, trace_counts
from ..b02.study import COMPONENTS
from ..b03.option import branch_id, physical_identity
from ..b03.reader import checked_path, load_arrays, load_decisions, verify_model_branch
from .controller import TemporalProgram
from .host import WORLD_IDS, bound_worlds, seed
from .study import (ARMS, ARM_REQUEST_CEILINGS, CEILINGS, SNAPSHOTS, Spec,
                    episode_costs, fixed_config, json_record, read_catalog, verify_prefixes)

METRICS = ("J", "served", "quality", "height_penalty", "mean_path_per_uav", "ineligible",
           "eligible_unserved", "served_p05", "served_min", "zero_steps", "longest_zero_run", "active_mean")


def validate_worker(summary, out):
    if summary.get("worker_status") != "complete" or summary.get("status") not in ("collected", "complete"):
        raise ValueError("full worker was not completed successfully")
    if summary.get("new_fits") != 0 or summary.get("updates") != 0:
        raise ValueError("fixed zero-fit count differs")
    config = summary["config"]
    if (not re.fullmatch(r"[0-9a-f]{40}", summary["launch_sha"])
            or config["launch_sha"] != summary["launch_sha"]
            or not isinstance(config.get("admission_command_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", config["admission_command_sha256"])):
        raise ValueError("source or accepted operation identity differs")
    expected_config = fixed_config()
    if any(config.get(key) != value for key, value in expected_config.items()):
        raise ValueError("fixed source or configuration differs")
    if set(config) != set(expected_config) | {"launch_sha", "admission_command_sha256", "versions"}:
        raise ValueError("unexpected executable configuration field")
    path = checked_path(out, summary["config_artifact"])
    if path != out / "config.json" or json.loads(path.read_text()) != config:
        raise ValueError("saved configuration differs from worker binding")
    manifest = json.loads((out / "launch-manifest.json").read_text())
    if (manifest.get("acceptance") != "accepted" or manifest.get("sha") != summary["launch_sha"]
            or manifest.get("direction") != config["direction"]
            or manifest.get("command_sha256") != config["admission_command_sha256"]):
        raise ValueError("worker admission differs from accepted launch manifest")
    expected = [(ARMS[(index + offset) % 3], world_id)
                for index, world_id in enumerate(WORLD_IDS) for offset in range(3)]
    rows = summary["episodes"]
    if [(row["arm"], row["world_id"]) for row in rows] != expected:
        raise ValueError("complete cyclic panel missing, reordered or duplicated")
    if any(row["n"] != 8 or row["steps"] != 500 or row["complete"] is not True
           or row["runtime_seed"] != seed(row["world_id"], 3, 8) for row in rows):
        raise ValueError("fixed native cell differs")
    return bound_worlds()


def evidence_catalog(row, out):
    catalog = read_catalog(checked_path(out, row["evidence_catalog"]))
    if set(catalog) != {"plans", "selections", "banks", "model_branches", "candidate_banks"}:
        raise ValueError("evidence catalog fields differ")
    for name in ("model_branches", "candidate_banks"):
        identities = [item["id"] for item in catalog[name]]
        if len(set(identities)) != len(identities):
            raise ValueError("duplicated branch or bank identity")
    times = {"40"} if row["arm"] == "T" else {"40", "120"}
    if set(catalog["plans"]) != times or set(catalog["selections"]) != times:
        raise ValueError("actual scheduled selection missing or duplicated")
    return catalog


def verify_episode(row, out, scene):
    horizon = 500
    raw = load_arrays(checked_path(out, row["raw"]))
    decisions = load_decisions(checked_path(out, row["decisions"]))
    catalog = evidence_catalog(row, out)
    if len(decisions) != horizon:
        raise ValueError("incomplete native decision trace")
    shapes = {"positions": (501, 8, 3), "observations": (501, 8, 104), "states": (501, 133),
              "sinr": (501, 8, 50), "connections": (501, 8, 50), "peer_sinr": (501, 8, 8),
              "visible_users": (501, 8), "visible_peers": (501, 8), "actions": (500, 8, 3),
              "mask": (500,), "components": (500, 4), "scalar_reward": (500,),
              "terminal": (500,), "users": (50, 2)}
    if set(raw) != set(shapes):
        raise ValueError("native saved array keys differ")
    for key, shape in shapes.items():
        if raw[key].shape != shape or (key not in ("sinr", "peer_sinr") and not np.isfinite(raw[key]).all()):
            raise ValueError(f"invalid native saved array {key}")
    if raw["actions"].dtype != np.float32 or not np.isin(raw["actions"], [-1, 0, 1]).all():
        raise ValueError("native command dtype/alphabet differs")
    _same(raw["terminal"], np.arange(horizon) == horizon - 1, "terminal horizon")
    _same(raw["users"], scene.user_positions, "bound users")
    _same(raw["positions"][0], scene.uav_positions, "bound initial fleet")
    branches_checked, banks_checked = [], []

    def branch_sink(identifier, result):
        index = len(branches_checked)
        if index >= len(catalog["model_branches"]):
            raise ValueError("complete model branch missing")
        verify_model_branch(out, catalog["model_branches"][index], identifier, result)
        summary = result["summary"]
        if summary["start_t"] not in (40, 120) or summary["model_transitions"] != 500 - summary["start_t"]:
            raise ValueError("represented complete model branch has wrong interval")
        branches_checked.append(identifier)

    def candidate_sink(identifier, rows):
        index = len(banks_checked)
        if index >= len(catalog["candidate_banks"]):
            raise ValueError("stationary candidate bank missing")
        record = catalog["candidate_banks"][index]
        if record["id"] != identifier:
            raise ValueError("stationary bank identity/order differs")
        saved = np.load(checked_path(out, record["raw"]), allow_pickle=False)
        if saved.dtype != rows.dtype:
            raise ValueError("stationary enumeration dtype differs")
        _same(saved, rows, "every original stationary candidate")
        banks_checked.append(identifier)

    policy = TemporalProgram(row["arm"], horizon, branch_sink, candidate_sink)
    old_mask, totals = 255, empty_counts()
    calls = {kind: 0 for kind in KINDS}
    predictions = 0
    view = _native_view(8, raw["users"], horizon)
    for t in range(horizon + 1):
        positions = raw["positions"][t]
        mask = mask_bits(255 if t == 0 else int(raw["mask"][t - 1]), 8)
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
        _same(raw["states"][t], _public_state(positions, raw["users"], t, horizon), f"public FP32 state {t}")
        for member in range(8):
            observation = MultiUAVEnv._get_observation_vectorized(view, f"uav_{member}")["obs"]
            _same(raw["observations"][t, member], observation, f"native local view {t}/{member}")
        _same(raw["visible_users"][t], [len(view._local_user_entries(i)[0][:20]) for i in range(8)], f"user slot count {t}")
        _same(raw["visible_peers"][t], [len(view._local_uav_entries(i)[0][:10]) for i in range(8)], f"peer slot count {t}")
        if t:
            UAVBaseStationEnv._compute_reward(view)
            component = np.asarray([view.reward_info[key] for key in COMPONENTS])
            _same(raw["components"][t - 1], component, f"native full objective {t}")
            if abs(raw["scalar_reward"][t - 1] * 8 - component[3]) > 1e-14:
                raise ValueError("scalar/native N scaling differs")
        if t == horizon:
            break
        _same(raw["positions"][t + 1], predict_next(positions, raw["actions"][t]), f"native motion {t}")
        command, new_mask, decision = policy.select(t, raw["states"][t] if t % 10 == 0 else None, old_mask)
        if json_record(decision) != decisions[t]:
            raise ValueError(f"complete temporal state-machine reconstruction differs at {t}")
        _same(raw["actions"][t], command, f"issued command {t}")
        if raw["mask"][t] != new_mask or (t % 10 and new_mask != old_mask):
            raise ValueError("issued mask/hold differs")
        trace_counts(decision, totals)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        predictions += 216 * int("motion" in decision)
        old_mask = new_mask
    result = metrics(raw, 8)
    if (result != row["metrics"] or json_record(policy.plans) != catalog["plans"]
            or json_record(policy.selections) != catalog["selections"]
            or json_record(policy.banks) != catalog["banks"]
            or totals != row["native_candidate_counts"] or calls != row["calls"]
            or predictions != row["position_predictions"] or not result["capacity_identity_holds"]
            or len(banks_checked) != len(catalog["candidate_banks"])
            or len(branches_checked) != len(catalog["model_branches"])):
        raise ValueError("native aggregate, temporal selections or cost reconstruction differs")
    costs = episode_costs(catalog, totals, predictions)
    if costs != row["costs"]:
        raise ValueError("complete primitive/bank/model query ledger differs")
    return catalog


def forecast_comparison(row, catalog, raw, start, out):
    selection = catalog["selections"][str(start)]
    identifier = selection["selected_model_branch"]
    branches = {item["id"]: item for item in catalog["model_branches"]}
    record = branches[identifier]
    model = load_arrays(checked_path(out, record["raw"]))
    end = 120 if row["arm"] == "G2" and start == 40 else 500
    count = end - start
    model_reward = model["reward_components"][:count]
    native_served = raw["connections"][start + 1:end + 1].sum(axis=(1, 2))
    return {"start_t": start, "end_t": end, "model_branch": identifier,
            "scope": "G2 first forecast checked only before its additional native120decision" if end == 120
                     else "complete forecast versus actual continuation; later replanning may change the program",
            "model_total_J": float(sum(float(value) for value in model_reward[:, 0])),
            "native_total_J": float(sum(float(value) for value in raw["components"][start:end, 3])),
            "model_minus_native_J": float(sum(float(value) for value in model_reward[:, 0]))
                                    - float(sum(float(value) for value in raw["components"][start:end, 3])),
            "model_minus_native_served": int(model_reward[:, 1].sum()) - int(native_served.sum()),
            "equal_per_tick_service": bool(np.array_equal(model_reward[:, 1], native_served)),
            "equal_commands": bool(np.array_equal(model["actions"][:count], raw["actions"][start:end])),
            "equal_masks": bool(np.array_equal(model["masks"][:count], raw["mask"][start:end])),
            "max_coordinate_abs_error_m": float(np.max(np.abs(model["positions"][:count + 1]
                                                               - raw["positions"][start:end + 1])))}


def plan_reading(plan, raw, start):
    if plan is None or not plan["initiated"]:
        return {"initiated": False, "physical_identity": "stay"}
    arrival, member = plan["arrival_t"], plan["member"]
    active = (raw["mask"][arrival:] & (1 << member)) != 0
    off = np.flatnonzero(~active)
    return {"initiated": True, "member": member, "site": plan["site"],
            "duration": plan["duration"], "arrival_t": arrival,
            "physical_identity": physical_identity(plan),
            "actual_arrival_mask": int(raw["mask"][arrival]),
            "transit_J": float(sum(float(value) for value in raw["components"][start:arrival, 3])),
            "transit_served": int(raw["connections"][start + 1:arrival + 1].sum()),
            "activated_steps_after_arrival": int(active.sum()),
            "first_remute_t": int(arrival + off[0]) if len(off) else None,
            "selected_stationary_candidate": plan["selected"]}


def world_readings(out, rows, catalogs):
    panel = {(row["arm"], row["world_id"]): row for row in rows}
    readings = []
    for world_id in WORLD_IDS:
        raw = {arm: load_arrays(checked_path(out, panel[arm, world_id]["raw"])) for arm in ARMS}
        records = {arm: catalogs[arm, world_id] for arm in ARMS}
        first = {arm: records[arm]["plans"]["40"] for arm in ARMS}
        if physical_identity(first["T"]) != physical_identity(first["G2"]):
            raise ValueError("T and G2 selected different first physical commitments")
        equal_first = physical_identity(first["A2"]) == physical_identity(first["G2"])
        if equal_first:
            for key in raw["A2"]:
                _same(raw["A2"][key], raw["G2"][key], f"same first commitment with same120policy {world_id}/{key}")
        a2_branches = {item["id"]: item for item in records["A2"]["model_branches"]}
        chosen_id = records["A2"]["selections"]["40"]["selected_model_branch"]
        g2_id = f"a2/first/{branch_id(first['G2'])}/outer"
        modeled_delta = a2_branches[chosen_id]["summary"]["total_J"] - a2_branches[g2_id]["summary"]["total_J"]
        if modeled_delta < 0:
            raise ValueError("A2 finite model selection lost to its represented G2 first option")
        forecasts, plans, aliases = {}, {}, {}
        for arm in ARMS:
            times = (40,) if arm == "T" else (40, 120)
            forecasts[arm] = {str(start): forecast_comparison(panel[arm, world_id], records[arm], raw[arm], start, out)
                              for start in times}
            plans[arm] = {str(start): plan_reading(records[arm]["plans"][str(start)], raw[arm], start) for start in times}
            bank_aliases = {}
            for bank in records[arm]["candidate_banks"]:
                candidates = np.load(checked_path(out, bank["raw"]), allow_pickle=False)
                groups = {}
                for candidate in candidates:
                    identity = tuple(int(candidate[index]) for index in (0, 2, 3, 4, 5))
                    groups.setdefault(identity, []).append([int(candidate[0]), int(candidate[1])])
                bank_aliases[bank["id"]] = [group for group in groups.values() if len(group) > 1]
            aliases[arm] = bank_aliases
        a2 = raw["A2"]
        g2 = raw["G2"]
        readings.append({"world_id": world_id, "plans": plans,
            "same_first_commitment_A2_G2": equal_first,
            "first_physical_trajectory_changed_A2_G2": bool(
                not np.array_equal(a2["positions"][40:121], g2["positions"][40:121])
                or not np.array_equal(a2["mask"][40:120], g2["mask"][40:120])),
            "first_changed_command_ticks": int(np.any(a2["actions"][40:120] != g2["actions"][40:120], axis=(1, 2)).sum()),
            "complete_changed_command_ticks": int(np.any(a2["actions"] != g2["actions"], axis=(1, 2)).sum()),
            "complete_changed_mask_ticks": int((a2["mask"] != g2["mask"]).sum()),
            "modeled_A2_minus_G2_first_choice_J": modeled_delta,
            "modeled_G2_first_outer_branch": g2_id,
            "A2_selected_outer_summary": a2_branches[chosen_id]["summary"],
            "actual_second_A2_selection": records["A2"]["selections"]["120"],
            "forecast_vs_native": forecasts, "stationary_physical_aliases": aliases})
    return readings


def read_run(out):
    wall, cpu = time.perf_counter(), time.process_time()
    summary = json.loads((out / "summary.json").read_text())
    scenes = validate_worker(summary, out)
    spec, rows = Spec(), summary["episodes"]
    catalogs, bindings = {}, []
    for index, row in enumerate(rows):
        catalog = verify_episode(row, out, scenes[row["world_id"]])
        catalogs[row["arm"], row["world_id"]] = catalog
        bindings.extend(row[field] for field in ("raw", "decisions", "evidence_catalog"))
        bindings.extend(branch[field] for branch in catalog["model_branches"] for field in ("raw", "decisions"))
        bindings.extend(bank["raw"] for bank in catalog["candidate_banks"])
        print(json.dumps({"reader_episodes_verified": index + 1, "world_id": row["world_id"], "arm": row["arm"]}), flush=True)
    if len({binding["path"] for binding in bindings}) != len(bindings):
        raise ValueError("duplicate artifact path in complete panel")
    verify_prefixes(out, rows)
    worlds = world_readings(out, rows, catalogs)
    costs = {key: sum(row["costs"][key] for row in rows) for key in (
        *CEILINGS, "ordinary_candidate_position_predictions", "model_branches", "stationary_banks")}
    if any(costs[key] > limit for key, limit in CEILINGS.items()):
        raise ValueError("prospective complete request/transition ceiling exceeded")
    arm_costs = {arm: {key: sum(row["costs"][key] for row in rows if row["arm"] == arm)
                       for key in costs} for arm in ARMS}
    if any(arm_costs[arm]["worker_state_mask_requests"] > ARM_REQUEST_CEILINGS[arm] for arm in ARMS):
        raise ValueError("prospective program request ceiling exceeded")
    panel = {(row["arm"], row["world_id"]): row["metrics"] for row in rows}
    indices = np.random.RandomState(spec.bootstrap_seed).randint(0, 16, (spec.bootstrap_replicates, 16))
    comparisons = {f"{a}-{b}": {metric: _paired(np.asarray([panel[a, world][metric] - panel[b, world][metric]
        for world in WORLD_IDS]), list(WORLD_IDS), indices) for metric in METRICS}
        for a, b in (("A2", "G2"), ("G2", "T"), ("A2", "T"))}
    aggregates = {arm: {metric: float(np.mean([panel[arm, world][metric] for world in WORLD_IDS]))
                         for metric in METRICS} for arm in ARMS}
    result = {"status": "complete", "source_sha": summary["launch_sha"],
              "config_artifact": summary["config_artifact"], "episodes_verified": 48,
              "native_steps_verified": 24000, "native_snapshots_verified": 24048,
              "new_fits": 0, "updates": 0, "all_native_physics_observations_actions_checked": True,
              "all_nested_branches_and_stationary_candidates_reconstructed": True,
              "all_native_decisions_reconstructed": True, "common_prefix_exact_through_t39": True,
              "T_G2_prefix_exact_through_t119": True, "cycle_reuse": False,
              "worker_costs": costs, "reader_replayed_worker_costs": costs,
              "arm_costs": arm_costs, "bulk_bytes": sum(binding["bytes"] for binding in bindings),
              "bulk_artifacts": len(bindings), "aggregates": aggregates,
              "comparisons": comparisons, "worlds": worlds,
              "uncertainty_scope": "paired percentile bootstrap over16fresh worlds for3fixed deterministic programs; not learning replication or native labels for unexecuted alternatives",
              "bootstrap": {"seed": spec.bootstrap_seed, "replicates": spec.bootstrap_replicates},
              "timing": {"wall_seconds": time.perf_counter() - wall,
                         "cpu_seconds": time.process_time() - cpu, "process_resources": process_resources()}}
    write_json(out / "reading.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    read_run(parser.parse_args().run.resolve())
