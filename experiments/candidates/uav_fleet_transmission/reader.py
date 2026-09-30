"""Full saved-data B01 reading: native physics and every declared control decision."""
from __future__ import annotations
import argparse
import gzip
import json
from pathlib import Path
import resource
import time

import numpy as np

from envs.pettingzoo import uav_radio
from envs.pettingzoo.uav_env import MultiUAVEnv
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from .control import OrdinaryController, choose_mask, decode_public_state, predict_next
from .host import mask_bits, world
from .study import ARMS, DIRECTION, OBJECT_ID, Spec, frozen, metrics, sha256, write_json

COUNT_KEYS = ("requested_candidates", "scored_candidates", "cached_candidates",
              "geometry_rows_computed", "geometry_rows_reused")


def validate_worker(summary):
    """A full trajectory panel cannot override a failed freeze/source check."""
    acceptable_status = summary.get("status") in ("collected", "complete") or (
        summary.get("status") == "failed" and summary.get("failure_stage") == "reader")
    if not acceptable_status or summary.get("worker_status") != "complete":
        raise ValueError("worker did not complete its source/freeze checks")
    if (summary.get("schema"), summary.get("direction"), summary.get("object_id"),
        summary.get("new_fits"), summary.get("updates")) != (1,DIRECTION,OBJECT_ID,0,0):
        raise ValueError("worker result identity differs")
    config = summary["config"]
    if (config.get("launch_sha") != summary.get("launch_sha")
        or config.get("source_training_sha") != frozen.PRODUCER_SHA
        or config.get("object_id") != OBJECT_ID or config.get("direction") != DIRECTION
        or tuple(config.get("arms", ())) != ARMS
        or config.get("expected_episodes") != 160 or config.get("expected_native_steps") != 80000
        or config.get("expected_mask_requests") != 648000 or config.get("expected_motion_requests") != 2592000):
        raise ValueError("worker fixed source/config binding differs")
    assets, checks = summary["assets"], summary["frozen_checks"]
    if set(assets) != {"H6","SET"} or set(checks) != {"4","8"}:
        raise ValueError("worker lacks both assets or N freeze checks")
    for arm, seed, tag in frozen.SOURCE_POLICIES:
        asset = assets[arm]
        if asset["source"] != {"arm":arm,"seed":seed,"tag":tag}:
            raise ValueError("frozen asset source differs")
        expected_hash = {"H6":"98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343",
                         "SET":"03f4f070e30b34fb61cd45820f1579ebde185c9417468689bd0c2e7ef60c0a3b"}[arm]
        if any(asset.get(key) != expected_hash for key in
               ("checkpoint_sha256_before","checkpoint_sha256_after")):
            raise ValueError("frozen checkpoint before/after identity differs")
        if asset["checkpoint_record"]["sha256"] != expected_hash:
            raise ValueError("frozen checkpoint record differs")
        for n in ("4","8"):
            if set(checks[n]) != {"H6","SET"}:
                raise ValueError("worker lacks both arm freeze checks")
            check = checks[n][arm]
            if (check["initial_digest"] != asset["source_final_digest"]
                or check["final_digest"] != asset["source_final_digest"]
                or check["normalizers_unchanged"] is not True
                or not check["optimizer_calls"] or any(check["optimizer_calls"].values())):
                raise ValueError("failed parameter/normalizer/optimizer freeze evidence")


def _same(actual, expected, name):
    if not np.array_equal(actual, expected):
        raise ValueError(f"saved-data mismatch: {name}")


def _public_state(positions, users, t, horizon):
    n = len(positions)
    uav32, user32 = positions.astype(np.float32), users.astype(np.float32)
    padded = np.zeros((8, 3), dtype=np.float32)
    padded[:n, :2] = uav32[:, :2]/1000.0
    padded[:n, 2] = (uav32[:, 2]-50.0)/100.0
    valid = np.zeros(8, dtype=np.float32)
    valid[:n] = 1
    return np.concatenate((padded.ravel(), valid, (user32/1000.0).ravel(),
                           np.asarray([t/horizon], dtype=np.float32)))


def _native_view(n, users, horizon):
    """A read-only-formula receiver, without environment construction/reset/step/RNG."""
    view = object.__new__(UAVBaseStationEnv)
    for key, value in dict(n_uavs=n, n_users=50, user_positions=users, area_size=1000,
            height_range=(50, 150), min_sinr=0, max_connections=10,
            max_observed_users=20, max_observed_uavs=10, max_steps=horizon,
            coverage_weight=.7, quality_weight=.3, channel_model="free_space",
            carrier_frequency=2e9, tx_power=23, noise_power=-80, use_fdma=False,
            enable_transmitter_mask=True).items():
        setattr(view, key, value)
    return view


def verify_episode(row: dict, out: Path, spec: Spec) -> tuple[dict, dict]:
    n, arm, world_id, horizon = row["n"], row["arm"], row["world_id"], spec.horizon
    for field in ("raw", "decisions"):
        binding = row[field]
        path = out / binding["path"]
        if path.stat().st_size != binding["bytes"] or sha256(path) != binding["sha256"]:
            raise ValueError(f"artifact identity differs: {binding['path']}")
    with np.load(out / row["raw"]["path"], allow_pickle=False) as source:
        raw = {key: source[key] for key in source.files}
    with gzip.open(out / row["decisions"]["path"], "rt", encoding="utf-8") as stream:
        decisions = [json.loads(line) for line in stream]
    if len(decisions) != horizon or not row["complete"] or row["steps"] != horizon:
        raise ValueError("incomplete native episode")
    expected_shapes = {"positions": (horizon+1,n,3), "observations": (horizon+1,n,104),
        "states": (horizon+1,133), "sinr": (horizon+1,n,50),
        "connections": (horizon+1,n,50), "peer_sinr": (horizon+1,n,n),
        "actions": (horizon,n,3), "raw_actions": (horizon,n,3), "mask": (horizon,),
        "components": (horizon,4), "scalar_reward": (horizon,), "terminal": (horizon,),
        "users": (50,2), "visible_users": (horizon+1,n), "visible_peers": (horizon+1,n)}
    for key, shape in expected_shapes.items():
        if raw[key].shape != shape:
            raise ValueError(f"wrong shape for {key}: {raw[key].shape}")
        if key not in ("sinr", "peer_sinr") and not np.isfinite(raw[key]).all():
            raise ValueError(f"nonfinite saved {key}")
    _same(raw["actions"], np.clip(raw["raw_actions"], -1, 1), "original clip law")
    _same(raw["terminal"], np.arange(horizon) == horizon-1, "terminal time")
    scene = world(world_id)
    _same(raw["users"], scene.user_positions, "independent user stream")
    _same(raw["positions"][0], scene.uav_positions[:n], "fleet prefix reset")
    expected_counts = {"actor_calls": 0 if arm == "C_E" else horizon,
        "motion_calls": horizon if arm == "C_E" else 0,
        "mask_calls": horizon//10 if arm.endswith("_E") else 0}
    if row["counts"] != expected_counts:
        raise ValueError("actor/motion/mask invocation counts differ")
    controller = OrdinaryController(n) if arm == "C_E" else None
    old_mask = (1 << n)-1
    counts = {kind: {key: 0 for key in COUNT_KEYS} for kind in ("motion", "mask")}
    view = _native_view(n, raw["users"], horizon)
    for t in range(horizon+1):
        positions = raw["positions"][t]
        # Physics at saved observation t uses the mask that completed transition t-1.
        mask = mask_bits((1 << n)-1 if t == 0 else int(raw["mask"][t-1]), n)
        loss = uav_radio.free_space_user_path_loss(positions, raw["users"])
        sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=mask)
        connections = uav_radio.greedy_connection_assignment(sinr, 0., 10)
        _same(raw["sinr"][t], sinr, f"native user radio t{t}")
        _same(raw["connections"][t], connections, f"native assignment t{t}")
        view.uav_positions, view.sinr_matrix, view.connections = positions, sinr, connections
        view._transmitter_mask = mask
        view._uav_uav_path_loss_matrix = MultiUAVEnv._compute_uav_path_loss_matrix(view)
        view.uav_sinr_matrix = MultiUAVEnv._compute_uav_uav_sinr_matrix(view)
        view.current_step = t
        _same(raw["peer_sinr"][t], view.uav_sinr_matrix, f"native peer visibility t{t}")
        _same(raw["states"][t], _public_state(positions, raw["users"], t, horizon),
              f"public state representation t{t}")
        for member in range(n):
            observation = MultiUAVEnv._get_observation_vectorized(view, f"uav_{member}")["obs"]
            _same(raw["observations"][t,member], observation, f"native local observation t{t}/{member}")
        if t > 0:
            UAVBaseStationEnv._compute_reward(view)
            component = np.asarray([view.reward_info[k] for k in
                ("coverage_reward", "quality_reward", "energy_penalty", "total_reward")])
            _same(raw["components"][t-1], component, f"native all-UAV objective t{t}")
            # The adapter averages N identical J/N values; summation can round.
            if abs(raw["scalar_reward"][t-1]*n-component[3]) > 1e-14:
                raise ValueError("original scalar/native N scaling differs")
        if t == horizon:
            break
        _same(raw["positions"][t+1], predict_next(positions, raw["actions"][t]),
              f"actual per-axis clipped motion t{t}")
        decision = decisions[t]
        if decision["t"] != t or decision["old_mask"] != old_mask:
            raise ValueError("old-mask decision order differs")
        boundary = t % 10 == 0
        if controller is not None:
            command, predicted, trace = controller.select(t, raw["states"][t] if boundary else None, old_mask)
            _same(raw["actions"][t], command, f"ordinary full coordinate search t{t}")
            if decision["motion"] != trace:
                raise ValueError(f"ordinary candidate reconstruction differs t{t}")
            for key in COUNT_KEYS:
                counts["motion"][key] += trace[key]
        elif boundary:
            public_position, _ = decode_public_state(raw["states"][t], n)
            predicted = predict_next(public_position, raw["actions"][t])
        if boundary and arm.endswith("_E"):
            _, users = decode_public_state(raw["states"][t], n)
            old_mask, trace = choose_mask(users, predicted, old_mask)
            if decision["mask_search"] != trace:
                raise ValueError(f"mask candidate reconstruction differs t{t}")
            for key in COUNT_KEYS:
                counts["mask"][key] += trace[key]
        elif "mask_search" in decision:
            raise ValueError("mask refreshed off cadence or in all-on arm")
        if decision["issued_mask"] != old_mask or raw["mask"][t] != old_mask:
            raise ValueError("issued/held mask differs from fixed decision")
    result = metrics(raw, n)
    if row["metrics"] != result or not result["capacity_identity_holds"]:
        raise ValueError("saved aggregate or native capacity identity differs")
    return result, counts


def _paired(values: np.ndarray, ids: list[int], indices: np.ndarray):
    means = values[indices].mean(axis=1)
    return {"mean": float(values.mean()), "p95_world_bootstrap": np.quantile(means, [.025,.975]).tolist(),
            "per_world": [{"world_id": world_id, "difference": float(value)} for world_id, value in zip(ids,values)],
            "positive_worlds": int((values>0).sum()), "negative_worlds": int((values<0).sum()),
            "zero_worlds": int((values==0).sum()), "minimum": float(values.min()), "maximum": float(values.max())}


def read_run(out: Path):
    wall, cpu = time.perf_counter(), time.process_time()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    summary = json.loads((out / "summary.json").read_text())
    validate_worker(summary)
    spec_data = summary["config"]["spec"]
    spec = Spec(**{**spec_data, "ns": tuple(spec_data["ns"]), "world_ids": tuple(spec_data["world_ids"])})
    if spec != Spec():
        raise ValueError("saved complete-panel configuration differs from the fixed B01 study")
    expected = {(n, arm, world_id) for n in spec.ns for arm in ARMS for world_id in spec.world_ids}
    rows = summary["episodes"]
    actual = [(r["n"],r["arm"],r["world_id"]) for r in rows]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("full finite panel missing or duplicated")
    totals = {kind: {key: 0 for key in COUNT_KEYS} for kind in ("motion", "mask")}
    for i, row in enumerate(rows):
        _, counts = verify_episode(row, out, spec)
        for kind in totals:
            for key in COUNT_KEYS:
                totals[kind][key] += counts[kind][key]
        if (i+1) % 10 == 0:
            print(json.dumps({"reader_episodes_verified": i+1}), flush=True)
    if totals["motion"]["requested_candidates"] != summary["config"]["expected_motion_requests"]:
        raise ValueError("full motion candidate count differs")
    if totals["mask"]["requested_candidates"] != summary["config"]["expected_mask_requests"]:
        raise ValueError("full mask candidate count differs")
    panel = {(r["n"],r["arm"],r["world_id"]):r["metrics"] for r in rows}
    metric_names = ("J", "served", "quality", "height_penalty", "mean_path_per_uav", "ineligible",
                    "eligible_unserved", "served_p05", "zero_steps", "active_mean")
    indices = np.random.RandomState(spec.bootstrap_seed).randint(0,len(spec.world_ids),
        (spec.bootstrap_replicates,len(spec.world_ids)))
    comparisons, interactions, aggregates = {}, {}, {}
    for n in spec.ns:
        for arm in ARMS:
            aggregates[f"N{n}/{arm}"] = {metric: float(np.mean([panel[n,arm,w][metric] for w in spec.world_ids]))
                                          for metric in metric_names}
        pairs = [("H6_E","H6_all"),("SET_E","SET_all"),("H6_E","C_E"),("SET_E","C_E"),
                 ("H6_E","SET_E"),("H6_all","SET_all")]
        for candidate, baseline in pairs:
            comparisons[f"N{n}/{candidate}-{baseline}"] = {
                metric: _paired(np.asarray([panel[n,candidate,w][metric]-panel[n,baseline,w][metric]
                                           for w in spec.world_ids]), list(spec.world_ids), indices)
                for metric in metric_names}
    for arm in ("H6","SET"):
        interactions[arm] = {metric: _paired(np.asarray([
            (panel[8,arm+"_E",w][metric]-panel[8,arm+"_all",w][metric])
            -(panel[4,arm+"_E",w][metric]-panel[4,arm+"_all",w][metric])
            for w in spec.world_ids]), list(spec.world_ids),indices) for metric in metric_names}
    result = {"status": "complete", "source_sha": summary["launch_sha"],
        "episodes_verified": len(rows), "native_steps_verified": sum(r["steps"] for r in rows),
        "new_fits": 0, "updates": 0, "all_saved_native_physics_observations_actions_checked": True,
        "every_C_motion_pass_and_E_mask_set_reconstructed": True,
        "worker_candidate_counts": totals, "reader_candidate_counts": totals,
        "native_physics_snapshots_verified": len(rows)*(spec.horizon+1),
        "aggregates": aggregates, "comparisons": comparisons, "N8_minus_N4_E_increment_interactions": interactions,
        "uncertainty_scope": "paired percentile world bootstrap, conditional on two fixed old training instances; not training replication or equivalence",
        "bootstrap": {"seed": spec.bootstrap_seed,"replicates":spec.bootstrap_replicates},
        "timing": {"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu,
                   "user_seconds":resource.getrusage(resource.RUSAGE_SELF).ru_utime-usage_start.ru_utime,
                   "system_seconds":resource.getrusage(resource.RUSAGE_SELF).ru_stime-usage_start.ru_stime,
                   "peak_rss_kib_process":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   "rss_scope":"process lifetime; not a separate reader peak"}}
    write_json(out / "reading.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    read_run(parser.parse_args().run)
