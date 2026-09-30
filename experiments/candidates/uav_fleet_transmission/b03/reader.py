"""Replay every represented model program and all48 complete native episodes."""
import argparse
import gzip
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
from ..study import artifact, metrics, process_resources, sha256, write_json
from ..b02.controller import COUNT_KEYS, KINDS, empty_counts, trace_counts
from ..b02.reader import verify_episode as verify_reference_episode
from ..b02.study import COMPONENTS, option_metrics
from .controller import ContinuationProgram
from .host import WORLD_IDS, bound_worlds, seed
from .study import ARMS, CEILINGS, SNAPSHOTS, Spec, compact_continuation, fixed_config, verify_prefixes


def checked_path(out, binding):
    path = out / binding["path"]
    if not path.resolve().is_relative_to(out.resolve()) or not path.is_file():
        raise ValueError("artifact outside run or missing")
    if path.stat().st_size != binding["bytes"] or sha256(path) != binding["sha256"]:
        raise ValueError("saved artifact bytes differ")
    return path


def load_arrays(path):
    with np.load(path, allow_pickle=False) as source:
        return {key: source[key] for key in source.files}


def load_decisions(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


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
    if any(config.get(k) != v for k, v in expected_config.items()):
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
    expected = [(ARMS[(index + offset) % 3], w)
                for index, w in enumerate(WORLD_IDS) for offset in range(3)]
    rows = summary["episodes"]
    if [(r["arm"], r["world_id"]) for r in rows] != expected:
        raise ValueError("complete cyclic panel missing, reordered or duplicated")
    if any(r["n"] != 8 or r["steps"] != 500 or r["complete"] is not True
           or r["runtime_seed"] != seed(r["world_id"], 3, 8) for r in rows):
        raise ValueError("fixed native cell differs")
    return bound_worlds()


def verify_model_branch(out, saved, identifier, result):
    if saved["id"] != identifier or saved["summary"] != result["summary"]:
        raise ValueError("complete model branch identity/summary differs")
    arrays = load_arrays(checked_path(out, saved["raw"]))
    if set(arrays) != set(result["arrays"]):
        raise ValueError("model branch arrays differ")
    for key, expected in result["arrays"].items():
        if arrays[key].dtype != expected.dtype:
            raise ValueError(f"model branch dtype differs: {key}")
        _same(arrays[key], expected, f"model branch {identifier}/{key}")
    if load_decisions(checked_path(out, saved["decisions"])) != result["decisions"]:
        raise ValueError("complete model branch decision replay differs")


def verify_T_episode(row, out, scene):
    horizon = 500
    raw = load_arrays(checked_path(out, row["raw"]))
    decisions = load_decisions(checked_path(out, row["decisions"]))
    if len(decisions) != horizon or row["steps"] != horizon or row["complete"] is not True:
        raise ValueError("incomplete native T trajectory")
    shapes = {"positions": (501, 8, 3), "observations": (501, 8, 104), "states": (501, 133),
        "sinr": (501, 8, 50), "connections": (501, 8, 50), "peer_sinr": (501, 8, 8),
        "visible_users": (501, 8), "visible_peers": (501, 8), "actions": (500, 8, 3),
        "mask": (500,), "components": (500, 4), "scalar_reward": (500,), "terminal": (500,), "users": (50, 2)}
    if set(raw) != set(shapes):
        raise ValueError("native T saved array keys differ")
    for key, shape in shapes.items():
        if raw[key].shape != shape or (key not in ("sinr", "peer_sinr") and not np.isfinite(raw[key]).all()):
            raise ValueError(f"invalid native T saved array {key}")
    if raw["actions"].dtype != np.float32 or not np.isin(raw["actions"], [-1, 0, 1]).all():
        raise ValueError("native command dtype/alphabet differs")
    _same(raw["terminal"], np.arange(horizon) == horizon - 1, "terminal horizon")
    _same(raw["users"], scene.user_positions, "bound users")
    _same(raw["positions"][0], scene.uav_positions, "bound initial fleet")
    branches_checked = []
    candidates_checked = []

    def branch_sink(identifier, result):
        index = len(branches_checked)
        if index >= len(row["model_branches"]):
            raise ValueError("complete model branch missing")
        verify_model_branch(out, row["model_branches"][index], identifier, result)
        branches_checked.append(identifier)

    def candidate_sink(rows):
        path = checked_path(out, row["stationary_candidates"])
        saved = np.load(path, allow_pickle=False)
        if saved.dtype != rows.dtype:
            raise ValueError("stationary enumeration dtype differs")
        _same(saved, rows, "every original stationary candidate")
        candidates_checked.append(True)

    policy = ContinuationProgram(horizon, branch_sink, candidate_sink)
    old_mask, totals = 255, empty_counts()
    calls = {kind: 0 for kind in KINDS}
    predictions, model_ticks = 0, 0
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
            component = np.asarray([view.reward_info[k] for k in COMPONENTS])
            _same(raw["components"][t - 1], component, f"native full objective {t}")
            if abs(raw["scalar_reward"][t - 1] * 8 - component[3]) > 1e-14:
                raise ValueError("scalar/native N scaling differs")
        if t == horizon:
            break
        _same(raw["positions"][t + 1], predict_next(positions, raw["actions"][t]), f"native motion {t}")
        command, new_mask, decision = policy.select(t, raw["states"][t] if t % 10 == 0 else None, old_mask)
        if decision != decisions[t]:
            raise ValueError(f"complete T candidate/state-machine reconstruction differs at {t}")
        _same(raw["actions"][t], command, f"issued command {t}")
        if raw["mask"][t] != new_mask or (t % 10 and new_mask != old_mask):
            raise ValueError("issued mask/hold differs")
        trace_counts(decision, totals)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        predictions += 216 * int("motion" in decision)
        if "option" in decision:
            model_ticks += int(decision["option"]["counts"]["model_ticks"])
        old_mask = new_mask
    result = metrics(raw, 8)
    if (result != row["metrics"] or option_metrics(policy.plan, raw) != row["option"]
        or compact_continuation(policy.continuation) != row["continuation"]
        or totals != row["candidate_counts"] or calls != row["calls"]
        or predictions != row["position_predictions"] or model_ticks != row["option_model_ticks"]
        or not result["capacity_identity_holds"] or len(candidates_checked) != 1
        or len(branches_checked) != len(row["model_branches"])):
        raise ValueError("T aggregate/continuation/cost reconstruction differs")
    return totals


def verify_program_equivalence(out, rows):
    panel = {(r["arm"], r["world_id"]): r for r in rows}
    result = []
    for w in WORLD_IDS:
        trow, rrow = panel["T", w], panel["R", w]
        continuation = trow["continuation"]
        equal_program = continuation["selected_physical_identity"] == continuation["original_R_physical_identity"]
        c_raw = load_arrays(checked_path(out, panel["C", w]["raw"]))
        r_raw = load_arrays(checked_path(out, rrow["raw"]))
        t_raw = load_arrays(checked_path(out, trow["raw"]))
        if equal_program:
            for key in r_raw:
                _same(r_raw[key], t_raw[key], f"identical physical R/T program {w}/{key}")
        branch_values = {b["id"]: b for b in continuation["branches"]}
        comparisons = {}
        for arm, branch_name, raw in (("C", "stay", c_raw), ("R", continuation["original_R_branch"], r_raw),
                                      ("T", continuation["selected_branch"], t_raw)):
            forecast = branch_values[branch_name]["summary"]
            observed_J = float(sum(float(v) for v in raw["components"][40:, 3]))
            observed_service = int(raw["connections"][41:].sum())
            comparisons[arm] = {"model_branch": branch_name, "modeled_remaining_J": forecast["total_J"],
                "observed_remaining_J": observed_J, "J_model_minus_native": forecast["total_J"] - observed_J,
                "modeled_remaining_served": forecast["total_served"], "observed_remaining_served": observed_service,
                "service_model_minus_native": forecast["total_served"] - observed_service}
        aliases, model_aliases = {}, {}
        for branch in continuation["branches"]:
            aliases.setdefault(branch["physical_identity"], []).append(branch["id"])
            model_aliases.setdefault(branch["modeled_execution_identity"], []).append(branch["id"])
        candidate_rows = np.load(checked_path(out, trow["stationary_candidates"]), allow_pickle=False)
        candidate_aliases = {}
        for candidate in candidate_rows:
            # Member, horizontal commands, descent and duration determine the
            # fixed commitment; site indices can alias that same program.
            identity = tuple(int(candidate[i]) for i in (0, 2, 3, 4, 5))
            candidate_aliases.setdefault(identity, []).append([int(candidate[0]), int(candidate[1])])
        result.append({"world_id": w, "same_physical_R_T_program": equal_program,
            "same_R_T_commands": bool(np.array_equal(r_raw["actions"], t_raw["actions"])),
            "same_R_T_masks": bool(np.array_equal(r_raw["mask"], t_raw["mask"])),
            "same_R_T_positions": bool(np.array_equal(r_raw["positions"], t_raw["positions"])),
            "changed_command_ticks": int(np.any(r_raw["actions"] != t_raw["actions"], axis=(1, 2)).sum()),
            "changed_mask_ticks": int((r_raw["mask"] != t_raw["mask"]).sum()),
            "changed_position_snapshots": int(np.any(r_raw["positions"] != t_raw["positions"], axis=(1, 2)).sum()),
            "represented_physical_aliases": [ids for ids in aliases.values() if len(ids) > 1],
            "represented_model_execution_aliases": [ids for ids in model_aliases.values() if len(ids) > 1],
            "stationary_candidate_physical_aliases": [ids for ids in candidate_aliases.values() if len(ids) > 1],
            "forecast_vs_native": comparisons, "continuation": continuation,
            "R_option": rrow["option"], "T_option": trow["option"]})
    return result


def read_run(out):
    wall, cpu = time.perf_counter(), time.process_time()
    summary = json.loads((out / "summary.json").read_text())
    scenes = validate_worker(summary, out)
    spec, rows = Spec(), summary["episodes"]
    totals = {arm: empty_counts() for arm in ARMS}
    model_totals, reward_totals = empty_counts(), {k: 0 for k in COUNT_KEYS}
    model_transitions = model_predictions = model_branches = 0
    for index, row in enumerate(rows):
        if row["arm"] == "T":
            counts = verify_T_episode(row, out, scenes[row["world_id"]])
            for branch in row["model_branches"]:
                value = branch["summary"]
                if value["start_t"] != 40 or value["horizon"] != 500 or value["model_transitions"] != 460:
                    raise ValueError("incomplete model continuation")
                model_branches += 1
                model_transitions += value["model_transitions"]
                model_predictions += value["ordinary_candidate_position_predictions"]
                for kind in KINDS:
                    for key in COUNT_KEYS:
                        model_totals[kind][key] += value["controller_counts"][kind][key]
                for key in COUNT_KEYS:
                    reward_totals[key] += value["reward_counts"][key]
        else:
            for field in ("raw", "decisions"):
                checked_path(out, row[field])
            counts = verify_reference_episode(row, out, scene=scenes[row["world_id"]], horizon=500)
        for kind in KINDS:
            for key in COUNT_KEYS:
                totals[row["arm"]][kind][key] += counts[kind][key]
        print(json.dumps({"reader_episodes_verified": index + 1}), flush=True)
    verify_prefixes(out, rows)
    equivalence = verify_program_equivalence(out, rows)
    if (totals["C"]["motion"]["requested_candidates"] != 1728000
        or totals["C"]["mask"]["requested_candidates"] != 204000):
        raise ValueError("ordinary fixed candidate requests differ")
    native_requests = sum(totals[a][k]["requested_candidates"] for a in ARMS for k in KINDS)
    model_requests = sum(model_totals[k]["requested_candidates"] for k in KINDS) + reward_totals["requested_candidates"]
    costs = {"worker_state_mask_requests": native_requests + model_requests,
        "model_physical_transitions": model_transitions,
        "candidate_transit_ticks": sum(r["option_model_ticks"] for r in rows),
        "ordinary_candidate_position_predictions": sum(r["position_predictions"] for r in rows) + model_predictions}
    if any(costs[k] > CEILINGS[k] for k in CEILINGS) or not 16 <= model_branches <= 128:
        raise ValueError("fixed prospective cost ceiling exceeded")
    panel = {(r["arm"], r["world_id"]): r["metrics"] for r in rows}
    metric_names = ("J", "served", "quality", "height_penalty", "mean_path_per_uav", "ineligible",
        "eligible_unserved", "served_p05", "served_min", "zero_steps", "longest_zero_run", "active_mean")
    indices = np.random.RandomState(spec.bootstrap_seed).randint(0, 16, (spec.bootstrap_replicates, 16))
    comparisons = {f"{a}-{b}": {m: _paired(np.asarray([panel[a, w][m] - panel[b, w][m] for w in WORLD_IDS]),
        list(WORLD_IDS), indices) for m in metric_names} for a, b in (("T", "R"), ("T", "C"), ("R", "C"))}
    aggregates = {a: {m: float(np.mean([panel[a, w][m] for w in WORLD_IDS])) for m in metric_names} for a in ARMS}
    bindings = [r[f] for r in rows for f in ("raw", "decisions")]
    bindings += [r["stationary_candidates"] for r in rows if r["arm"] == "T"]
    bindings += [b[f] for r in rows if r["arm"] == "T" for b in r["model_branches"] for f in ("raw", "decisions")]
    if len({b["path"] for b in bindings}) != len(bindings):
        raise ValueError("duplicate artifact path in complete panel")
    result = {"status": "complete", "source_sha": summary["launch_sha"],
        "config_artifact": summary["config_artifact"], "episodes_verified": 48,
        "native_steps_verified": 24000, "native_snapshots_verified": 24048,
        "new_fits": 0, "updates": 0, "all_native_physics_observations_actions_checked": True,
        "all_C_R_T_decisions_reconstructed": True, "all_C_R_T_prefixes_exact_through_t39": True,
        "all_stationary_candidates_and_retained_model_branches_reconstructed": True,
        "worker_native_candidate_counts": totals, "reader_native_candidate_counts": totals,
        "worker_model_controller_counts": model_totals, "reader_model_controller_counts": model_totals,
        "worker_model_reward_counts": reward_totals, "reader_model_reward_counts": reward_totals,
        "native_control_requests": native_requests, "model_requests": model_requests,
        "worker_costs": costs, "reader_replayed_worker_costs": costs,
        "model_branches": model_branches, "bulk_bytes": sum(b["bytes"] for b in bindings),
        "aggregates": aggregates, "comparisons": comparisons, "worlds": equivalence,
        "uncertainty_scope": "paired percentile bootstrap over16fresh worlds, conditional on3deterministic programs; not learning replication, equivalence or unexecuted native labels",
        "bootstrap": {"seed": spec.bootstrap_seed, "replicates": spec.bootstrap_replicates},
        "timing": {"wall_seconds": time.perf_counter() - wall, "cpu_seconds": time.process_time() - cpu,
                   "process_resources": process_resources()}}
    write_json(out / "reading.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    read_run(parser.parse_args().run.resolve())
