"""Saved-data reconstruction of all native transitions and C/J/R choices."""
import argparse
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import time

import numpy as np

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from ..control import predict_next
from ..host import mask_bits
from ..reader import _native_view, _paired, _public_state, _same
from ..study import metrics, process_resources, sha256, write_json
from .controller import COUNT_KEYS, KINDS, Program, empty_counts, trace_counts
from .host import WORLD_IDS, bound_worlds, seed, world
from .study import ARMS, COMPONENTS, DIRECTION, OBJECT_ID, Spec, option_metrics, source_bindings, verify_prefixes


def validate_worker(summary):
    config = summary["config"]
    spec = json.loads(json.dumps(asdict(Spec())))
    if summary.get("worker_status") != "complete":
        raise ValueError("full worker was not completed")
    if summary.get("new_fits") != 0 or summary.get("updates") != 0:
        raise ValueError("fixed zero-fit count differs")
    if (config["object_id"] != OBJECT_ID or config["direction"] != DIRECTION
        or config["spec"] != spec or config["arms"] != list(ARMS)
        or config["source_bindings"] != source_bindings()
        or config["launch_sha"] != summary["launch_sha"]
        or len(summary["launch_sha"]) != 40):
        raise ValueError("fixed source or configuration differs")
    expected = {(arm,w) for arm in ARMS for w in WORLD_IDS}
    rows = summary["episodes"]
    actual = [(r["arm"],r["world_id"]) for r in rows]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("complete panel missing or duplicated")
    if any(r["n"] != 8 or r["steps"] != 500 or r["complete"] is not True
           or r["runtime_seed"] != seed(r["world_id"],3,8) for r in rows):
        raise ValueError("fixed native cell differs")
    bound_worlds()


def verify_episode(row, out, scene=None, horizon=500):
    if scene is None:
        scene = world(row["world_id"])
    for field in ("raw", "decisions"):
        binding = row[field]
        path = out/binding["path"]
        if path.stat().st_size != binding["bytes"] or sha256(path) != binding["sha256"]:
            raise ValueError("saved artifact bytes differ")
    with np.load(out/row["raw"]["path"], allow_pickle=False) as source:
        raw = {key: source[key] for key in source.files}
    with gzip.open(out/row["decisions"]["path"], "rt", encoding="utf-8") as stream:
        decisions = [json.loads(line) for line in stream]
    if len(decisions) != horizon or row["steps"] != horizon or row["complete"] is not True:
        raise ValueError("incomplete native trajectory")
    shapes = {"positions":(horizon+1,8,3), "observations":(horizon+1,8,104),
        "states":(horizon+1,133), "sinr":(horizon+1,8,50), "connections":(horizon+1,8,50),
        "peer_sinr":(horizon+1,8,8), "visible_users":(horizon+1,8), "visible_peers":(horizon+1,8),
        "actions":(horizon,8,3), "mask":(horizon,), "components":(horizon,4),
        "scalar_reward":(horizon,), "terminal":(horizon,), "users":(50,2)}
    for key, shape in shapes.items():
        if raw[key].shape != shape or (key not in ("sinr", "peer_sinr") and not np.isfinite(raw[key]).all()):
            raise ValueError(f"invalid native saved array {key}")
    if raw["actions"].dtype != np.float32 or not np.isin(raw["actions"],[-1,0,1]).all():
        raise ValueError("native command dtype/alphabet differs")
    _same(raw["terminal"],np.arange(horizon)==horizon-1,"terminal horizon")
    _same(raw["users"],scene.user_positions,"bound users")
    _same(raw["positions"][0],scene.uav_positions,"bound initial fleet")
    policy, old_mask = Program(row["arm"],horizon), 255
    totals, calls = empty_counts(), {kind:0 for kind in KINDS}
    predictions, model_ticks = 0, 0
    view = _native_view(8,raw["users"],horizon)
    for t in range(horizon+1):
        positions = raw["positions"][t]
        mask = mask_bits(255 if t==0 else int(raw["mask"][t-1]),8)
        loss = uav_radio.free_space_user_path_loss(positions,raw["users"])
        sinr = uav_radio.user_sinr_from_path_loss(loss,transmitter_mask=mask)
        connections = uav_radio.greedy_connection_assignment(sinr,0.,10)
        _same(raw["sinr"][t],sinr,f"native radio {t}")
        _same(raw["connections"][t],connections,f"native assignment {t}")
        view.uav_positions,view.sinr_matrix,view.connections = positions,sinr,connections
        view._transmitter_mask = mask
        view._uav_uav_path_loss_matrix = MultiUAVEnv._compute_uav_path_loss_matrix(view)
        view.uav_sinr_matrix = MultiUAVEnv._compute_uav_uav_sinr_matrix(view)
        view.current_step = t
        _same(raw["peer_sinr"][t],view.uav_sinr_matrix,f"native peer radio {t}")
        _same(raw["states"][t],_public_state(positions,raw["users"],t,horizon),f"public FP32 state {t}")
        for member in range(8):
            observation = MultiUAVEnv._get_observation_vectorized(view,f"uav_{member}")["obs"]
            _same(raw["observations"][t,member],observation,f"native local view {t}/{member}")
        _same(raw["visible_users"][t], [len(view._local_user_entries(i)[0][:20]) for i in range(8)],f"user slot count {t}")
        _same(raw["visible_peers"][t], [len(view._local_uav_entries(i)[0][:10]) for i in range(8)],f"peer slot count {t}")
        if t:
            UAVBaseStationEnv._compute_reward(view)
            component = np.asarray([view.reward_info[k] for k in COMPONENTS])
            _same(raw["components"][t-1],component,f"native full objective {t}")
            if abs(raw["scalar_reward"][t-1]*8-component[3])>1e-14:
                raise ValueError("scalar/native N scaling differs")
        if t==horizon:
            break
        _same(raw["positions"][t+1],predict_next(positions,raw["actions"][t]),f"native motion {t}")
        command,new_mask,decision = policy.select(t,raw["states"][t] if t%10==0 else None,old_mask)
        if decision != decisions[t]:
            raise ValueError(f"complete candidate/state-machine reconstruction differs at {t}")
        _same(raw["actions"][t],command,f"issued command {t}")
        if raw["mask"][t] != new_mask or (t%10 and new_mask != old_mask):
            raise ValueError("issued mask/hold differs")
        trace_counts(decision,totals)
        for kind in KINDS:
            calls[kind] += int(kind in decision)
        predictions += 216*int("motion" in decision or "joint" in decision)
        if "option" in decision:
            model_ticks += int(decision["option"]["counts"]["model_ticks"])
        old_mask = new_mask
    result, option = metrics(raw,8), option_metrics(policy.plan,raw)
    if (result!=row["metrics"] or option!=row["option"] or totals!=row["candidate_counts"]
        or calls!=row["calls"] or predictions!=row["position_predictions"]
        or model_ticks!=row["option_model_ticks"] or not result["capacity_identity_holds"]):
        raise ValueError("aggregate/option/cost reconstruction differs")
    return totals


def read_run(out):
    wall,cpu = time.perf_counter(),time.process_time()
    summary = json.loads((out/"summary.json").read_text())
    validate_worker(summary)
    spec,rows = Spec(),summary["episodes"]
    totals = {arm:empty_counts() for arm in ARMS}
    for index,row in enumerate(rows):
        counts = verify_episode(row,out)
        for kind in KINDS:
            for key in COUNT_KEYS:
                totals[row["arm"]][kind][key] += counts[kind][key]
        print(json.dumps({"reader_episodes_verified":index+1}),flush=True)
    verify_prefixes(out,rows)
    if (totals["C"]["motion"]["requested_candidates"] != 1728000
        or totals["C"]["mask"]["requested_candidates"] != 204000
        or totals["J"]["motion"]["requested_candidates"] != 1555200
        or totals["J"]["joint"]["requested_candidates"] != 44064000):
        raise ValueError("ordinary/joint fixed candidate requests differ")
    radio_requests = sum(totals[a][k]["requested_candidates"] for a in ARMS for k in KINDS)
    predictions = sum(r["position_predictions"] for r in rows)
    model_ticks = sum(r["option_model_ticks"] for r in rows)
    if radio_requests>50918864 or predictions>5184000 or model_ticks>448000:
        raise ValueError("fixed prospective cost ceiling exceeded")
    panel = {(r["arm"],r["world_id"]):r["metrics"] for r in rows}
    metric_names = ("J","served","quality","height_penalty","mean_path_per_uav","ineligible",
        "eligible_unserved","served_p05","served_min","zero_steps","longest_zero_run","active_mean")
    indices = np.random.RandomState(spec.bootstrap_seed).randint(0,16,(spec.bootstrap_replicates,16))
    comparisons = {f"{a}-{b}":{m:_paired(np.asarray([panel[a,w][m]-panel[b,w][m] for w in WORLD_IDS]),
        list(WORLD_IDS),indices) for m in metric_names} for a,b in (("R","C"),("J","C"),("R","J"))}
    aggregates = {a:{m:float(np.mean([panel[a,w][m] for w in WORLD_IDS])) for m in metric_names} for a in ARMS}
    result = {"status":"complete","source_sha":summary["launch_sha"],"episodes_verified":48,
        "native_steps_verified":24000,"native_snapshots_verified":24048,"new_fits":0,"updates":0,
        "all_native_physics_observations_actions_checked":True,
        "all_C_J_R_decisions_reconstructed":True,"all_C_R_prefixes_exact_through_t39":True,
        "worker_candidate_counts":totals,"reader_candidate_counts":totals,
        "radio_requests":radio_requests,"position_predictions":predictions,"option_model_ticks":model_ticks,
        "aggregates":aggregates,"comparisons":comparisons,
        "option_worlds":[{"world_id":r["world_id"],**r["option"]} for r in rows if r["arm"]=="R"],
        "uncertainty_scope":"paired percentile bootstrap over16fresh worlds, conditional on3deterministic programs; not learning replication or equivalence",
        "bootstrap":{"seed":spec.bootstrap_seed,"replicates":spec.bootstrap_replicates},
        "timing":{"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu,
                  "process_resources":process_resources()}}
    write_json(out/"reading.json",result)
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run",type=Path)
    read_run(parser.parse_args().run)
