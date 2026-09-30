"""Pure saved-data reading of the complete warm-start study, without policy/env execution."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import resource
import time

import numpy as np

from envs.pettingzoo import uav_radio
from envs.pettingzoo.scenario1 import UAVBaseStationEnv
from envs.pettingzoo.uav_env import MultiUAVEnv
from experiments.candidates.uav_fleet_transmission.control import (
    OrdinaryController, choose_mask, decode_public_state, predict_next,
)
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.reader import (
    _native_view, _paired, _public_state, _same,
)
from experiments.candidates.uav_fleet_transmission.study import metrics, sha256, write_json
from .evaluation import ARMS, COUNT_KEYS, EvalSpec
from .host import EVAL_WORLD_IDS, TRAIN_WORLD_IDS, runtime_seed, world

DIRECTION = "uav_fleet_adaptation"
OBJECT_ID = "fleet_adaptation_b01"
PARENT_SHA256 = "98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343"
EXPECTED_OPTIMIZERS = {"coordinator": 480, "discoverer_actor": 96000,
    "discoverer_critic": 96000, "team_discriminator": 480, "individual_discriminator": 1920}


def checked_artifact(base: Path, binding: dict) -> Path:
    path = base / binding["path"]
    if path.stat().st_size != binding["bytes"] or sha256(path) != binding["sha256"]:
        raise ValueError(f"artifact identity differs: {path}")
    return path


def verify_native_arrays(raw: dict, world_id: int, horizon: int = 500) -> dict:
    """Reconstruct original native physics, quantized feedback, clipping and all-vehicle reward."""
    n = 8
    shapes = {"positions": (horizon+1,n,3), "observations": (horizon+1,n,104),
        "states": (horizon+1,133), "sinr": (horizon+1,n,50),
        "connections": (horizon+1,n,50), "actions": (horizon,n,3),
        "raw_actions": (horizon,n,3), "mask": (horizon,), "components": (horizon,4),
        "scalar_reward": (horizon,), "users": (50,2),
        "visible_users": (horizon+1,n), "visible_peers": (horizon+1,n)}
    for key, shape in shapes.items():
        if raw[key].shape != shape:
            raise ValueError(f"wrong native shape for {key}: {raw[key].shape}")
        if key != "sinr" and not np.isfinite(raw[key]).all():
            raise ValueError(f"nonfinite {key}")
    _same(raw["actions"], np.clip(raw["raw_actions"], -1, 1), "raw Gaussian execution clipping")
    scene = world(world_id)
    _same(raw["users"], scene.user_positions, "world users")
    _same(raw["positions"][0], scene.uav_positions, "world fleet")
    view = _native_view(n, raw["users"], horizon)
    for t in range(horizon+1):
        positions = raw["positions"][t]
        active = mask_bits(255 if t == 0 else int(raw["mask"][t-1]), n)
        loss = uav_radio.free_space_user_path_loss(positions, raw["users"])
        sinr = uav_radio.user_sinr_from_path_loss(loss, transmitter_mask=active)
        connections = uav_radio.greedy_connection_assignment(sinr, 0., 10)
        _same(raw["sinr"][t], sinr, f"native SINR t{t}")
        _same(raw["connections"][t], connections, f"native assignment t{t}")
        view.uav_positions, view.sinr_matrix, view.connections = positions, sinr, connections
        view._transmitter_mask = active
        view._uav_uav_path_loss_matrix = MultiUAVEnv._compute_uav_path_loss_matrix(view)
        view.uav_sinr_matrix = MultiUAVEnv._compute_uav_uav_sinr_matrix(view)
        view.current_step = t
        if "peer_sinr" in raw:
            _same(raw["peer_sinr"][t], view.uav_sinr_matrix, f"native peer SINR t{t}")
        _same(raw["states"][t], _public_state(positions, raw["users"], t, horizon), f"state t{t}")
        for member in range(n):
            obs = MultiUAVEnv._get_observation_vectorized(view, f"uav_{member}")["obs"]
            _same(raw["observations"][t,member], obs, f"native local feedback t{t}/{member}")
            _same(raw["visible_users"][t,member],
                  len(view._local_user_entries(member)[0][:view.max_observed_users]), "user visibility")
            _same(raw["visible_peers"][t,member],
                  len(view._local_uav_entries(member)[0][:view.max_observed_uavs]), "peer visibility")
        if t:
            UAVBaseStationEnv._compute_reward(view)
            component = np.asarray([view.reward_info[key] for key in (
                "coverage_reward", "quality_reward", "energy_penalty", "total_reward")])
            _same(raw["components"][t-1], component, f"native reward t{t}")
            if abs(raw["scalar_reward"][t-1]*n-component[3]) > 1e-14:
                raise ValueError("native reward/J-over-N scaling differs")
        if t < horizon:
            _same(raw["positions"][t+1], predict_next(positions, raw["actions"][t]), f"motion t{t}")
    result = metrics(raw, n)
    if not result["capacity_identity_holds"]:
        raise ValueError("native eligibility/capacity identity differs")
    return result


def verify_evaluation(row: dict, out: Path, spec: EvalSpec) -> tuple[dict, dict]:
    raw_path = checked_artifact(out, row["raw"])
    decision_path = checked_artifact(out, row["decisions"])
    with np.load(raw_path, allow_pickle=False) as source:
        raw = {key: source[key] for key in source.files}
    with gzip.open(decision_path, "rt", encoding="utf-8") as stream:
        decisions = [json.loads(line) for line in stream]
    h, arm = spec.horizon, row["arm"]
    if len(decisions) != h or row["steps"] != h or row["complete"] is not True or row["n"] != 8:
        raise ValueError("incomplete evaluation episode")
    if row["runtime_seed"] != runtime_seed(row["world_id"]):
        raise ValueError("evaluation runtime seed differs")
    _same(raw["terminal"], np.arange(h) == h-1, "evaluation terminal boundary")
    expected_calls = {"actor_calls": 0 if arm == "C_E" else h,
        "motion_calls": h if arm == "C_E" else 0, "mask_calls": h//10}
    if row["counts"] != expected_calls:
        raise ValueError("evaluation actor/motion/mask invocation counts differ")
    if raw["action_logprobs"].shape != (h,8) or not np.isfinite(raw["action_logprobs"]).all():
        raise ValueError("invalid evaluation log-probabilities")
    result = verify_native_arrays(raw, row["world_id"], h)
    if result != row["metrics"]:
        raise ValueError("evaluation native metrics differ")
    ordinary = OrdinaryController(8) if arm == "C_E" else None
    old_mask = 255
    counts = {kind: {key: 0 for key in COUNT_KEYS} for kind in ("motion", "mask")}
    for t, decision in enumerate(decisions):
        boundary = t % 10 == 0
        if decision["t"] != t or decision["old_mask"] != old_mask:
            raise ValueError("evaluation old-mask decision order differs")
        if ordinary is not None:
            command, predicted, trace = ordinary.select(t, raw["states"][t] if boundary else None, old_mask)
            _same(raw["actions"][t], command, "ordinary old-mask motion")
            if decision["motion"] != trace:
                raise ValueError("ordinary candidate reconstruction differs")
            for key in COUNT_KEYS:
                counts["motion"][key] += trace[key]
        elif boundary:
            positions, _ = decode_public_state(raw["states"][t], 8)
            predicted = predict_next(positions, raw["actions"][t])
        if boundary:
            _, users = decode_public_state(raw["states"][t], 8)
            old_mask, trace = choose_mask(users, predicted, old_mask)
            if trace != decision["mask_search"]:
                raise ValueError("evaluation E candidate reconstruction differs")
            for key in COUNT_KEYS:
                counts["mask"][key] += trace[key]
        elif "mask_search" in decision:
            raise ValueError("E refreshed outside its fixed cadence")
        if decision["issued_mask"] != old_mask or raw["mask"][t] != old_mask:
            raise ValueError("evaluation issued/held mask differs")
    if counts != row["candidate_counts"]:
        raise ValueError("evaluation candidate counts differ")
    return result, counts


def summarize_evaluation(rows: list[dict], spec: EvalSpec) -> dict:
    panel = {(r["arm"],r["world_id"]): r["metrics"] for r in rows}
    names = ("J", "served", "quality", "height_penalty", "mean_height", "mean_path_per_uav",
             "ineligible", "eligible_unserved", "served_p05", "served_min", "zero_steps",
             "longest_zero_run", "active_mean", "all_on_fraction", "mask_switches",
             "mean_visible_user_slots", "mean_visible_peer_slots")
    ids = list(spec.world_ids)
    indices = np.random.RandomState(spec.bootstrap_seed).randint(0,len(ids),(spec.bootstrap_replicates,len(ids)))
    aggregates = {arm: {name: float(np.mean([panel[arm,w][name] for w in ids])) for name in names}
                  for arm in ARMS}
    pairs = (("F_E","A_E"), ("F_E","I_E"), ("F_E","C_E"), ("A_E","I_E"), ("A_E","C_E"),
             ("I_E","C_E"))
    comparisons = {f"{candidate}-{baseline}": {
        name: _paired(np.asarray([panel[candidate,w][name]-panel[baseline,w][name] for w in ids]), ids, indices)
        for name in names} for candidate,baseline in pairs}
    return {"aggregates": aggregates, "comparisons": comparisons,
        "uncertainty_scope": "paired world-bootstrap descriptions conditional on one selected parent and one continuation per training condition; not training replication or equivalence",
        "bootstrap": {"seed": spec.bootstrap_seed, "replicates": spec.bootstrap_replicates}}


def verify_sampler(audit: dict) -> None:
    expected_calls = {key:value//32 for key,value in EXPECTED_OPTIMIZERS.items()}
    if (audit["optimizer_calls"] != expected_calls or audit["configured_epochs"] != 15
            or audit["num_actual_time_steps"] != 500 or audit["dropped_time_tail_steps"] != 0):
        raise ValueError("actual update/epoch/tail accounting differs")
    discoverer = audit["discoverer"]
    if (discoverer["batches"] != [[10,32]]*3000 or discoverer["sample_presentations"] != 960000
            or discoverer["valid_presentations"] != 960000):
        raise ValueError("actual recurrent sampler exposure differs")
    coordinator = audit["coordinator"]
    if coordinator["batch_sizes"] != [800]*15 or coordinator["sample_presentations"] != 12000:
        raise ValueError("actual coordinator sampler exposure differs")
    for kind, records, sizes, samples in (("team",8000,[8000]*15,120000),
                                          ("individual",64000,[16000]*60,960000)):
        row = audit["discriminator"][kind]
        if row["records"] != records or row["batch_sizes"] != sizes or row["sample_presentations"] != samples:
            raise ValueError(f"actual {kind} discriminator exposure differs")


def verify_fit(arm: str, binding: dict, out: Path) -> dict:
    fit_path = checked_artifact(out,binding["summary"])
    fit = json.loads(fit_path.read_text())
    base = fit_path.parent
    checked_artifact(base,fit["checkpoint"])
    expected_counts = {"training_team_steps":256000,"stored_team_steps":256000,
        "training_episodes":512,"updates":32,"terminal_resets":512,"actor_calls":16000,
        "evaluation_team_steps":0,"evaluation_episodes":0,"update_attempts":32}
    if (fit["status"] != "complete" or fit["direction"] != DIRECTION or fit["arm"] != arm
            or fit["fit_seed"] != 29316101 or fit["spec"] != {"groups":32,"lanes":16,"horizon":500}
            or fit["counts"] != expected_counts or fit["optimizer_calls"] != EXPECTED_OPTIMIZERS
            or fit["initialization"]["parameter_normalizer_digest"] != binding["initial_digest"]
            or fit["final_parameter_normalizer_digest"] != binding["final_digest"]
            or fit["checkpoint"] != binding["checkpoint"] or fit["parameter_motion"] != binding["parameter_motion"]
            or fit["source_checkpoint"]["sha256"] != PARENT_SHA256):
        raise ValueError("complete fit identity or counters differ")
    initial = fit["initialization"]
    if (any(initial["optimizer_state_entries"].values()) or any(initial["buffer_env_lengths"])
            or initial["discriminator_records"] != 0):
        raise ValueError("warm-start inherited optimizer or replay state")
    for key,value in {"n_agents":8,"n_uavs":8,"num_envs":16,"state_dim":133,"obs_dim":104,
                      "k":10,"rollout_length":500,"episode_length":500,"sequence_batch_size":32,
                      "ppo_epochs":15,"discriminator_batch_size":16000,"coordinator_batch_size":1280,
                      "use_obsnorm":False,"use_statenorm":False,"use_central_snapshot_in_flat_actor":False}.items():
        if fit["config"].get(key) != value:
            raise ValueError(f"fit config changed {key}")
    if len(fit["rollouts"]) != 32:
        raise ValueError("fit rollout inventory differs")
    candidate_counts = {key:0 for key in COUNT_KEYS}
    rows = []
    reset_digests = []
    optimizer_total = {key:0 for key in EXPECTED_OPTIMIZERS}
    snapshot_count = 0
    for group,row in enumerate(fit["rollouts"],1):
        ids = TRAIN_WORLD_IDS[(group-1)*16:group*16]
        if row["group"] != group or row["world_ids"] != list(ids):
            raise ValueError("fit world order differs")
        verify_sampler(row["sampler_audit"])
        if row["optimizer_delta"] != row["sampler_audit"]["optimizer_calls"]:
            raise ValueError("group optimizer delta differs from sampler audit")
        for key in optimizer_total:
            optimizer_total[key] += row["optimizer_delta"][key]
        trace = checked_artifact(base,row["collection"])
        with np.load(trace,allow_pickle=False) as source:
            arrays = {key:source[key] for key in source.files}
        _same(arrays["world_ids"],np.asarray(ids),"training world addresses")
        for key in ("raw_actions","actions","action_logprobs","states","observations"):
            if arrays[key].dtype != np.float32:
                raise ValueError(f"inherited FP32 {key} changed")
        for key in ("dones","terminated","truncated","old_mask","requested_mask","mask","skill_changed","stored_valid","high_level_valid"):
            if arrays[key].shape != (500,16):
                raise ValueError(f"training {key} shape differs")
        terminal = np.zeros((500,16),bool)
        terminal[-1] = True
        _same(arrays["dones"],terminal,"training done boundary")
        _same(np.logical_or(arrays["terminated"],arrays["truncated"]),terminal,"training term/trunc union")
        _same(arrays["stored_valid"],np.ones((500,16)),"stored rollout validity")
        _same(arrays["requested_mask"],arrays["mask"],"requested/executed masks")
        expected_old = np.concatenate((np.full((1,16),255),arrays["mask"][:-1]),axis=0)
        _same(arrays["old_mask"],expected_old,"old-mask feedback cadence")
        changed = np.broadcast_to((np.arange(500)%10 == 0)[:,None],(500,16))
        _same(arrays["skill_changed"],changed,"inherited ten-tick skill clock")
        _same(arrays["high_level_valid"],changed,"stored high-level decision clock")
        if arrays["action_logprobs"].shape != (500,16,8) or not np.isfinite(arrays["action_logprobs"]).all():
            raise ValueError("stored raw log-probabilities invalid")
        for key in ("reward_env","reward_team_disc","reward_ind_disc","learner_rewards","values"):
            if arrays[key].shape != (500,16,8) or not np.isfinite(arrays[key]).all():
                raise ValueError(f"training learner evidence invalid: {key}")
        if len(row["per_world"]) != 16:
            raise ValueError("training per-world metrics inventory differs")
        decisions = {(d["t"],d["lane"]):d for d in row["mask_decisions"]}
        expected_decisions = {(t,lane) for t in range(0,500,10) for lane in range(16)} if arm == "F" else set()
        if len(decisions) != len(row["mask_decisions"]) or set(decisions) != expected_decisions:
            raise ValueError("training E decision inventory differs")
        for lane,world_id in enumerate(ids):
            raw = {key:arrays[key][:,lane] for key in (
                "positions","states","observations","sinr","connections","raw_actions","actions",
                "mask","components","scalar_reward","visible_users","visible_peers")}
            raw["users"] = arrays["users"][lane]
            native = verify_native_arrays(raw,world_id)
            expected_world = {"world_id":world_id,**native,"scalar_return":float(raw["scalar_reward"].sum())}
            if row["per_world"][lane] != expected_world:
                raise ValueError("saved training native metrics differ")
            rows.append(expected_world)
            snapshot_count += 501
            old_mask = 255
            for t in range(500):
                if arm == "F" and t % 10 == 0:
                    positions,users = decode_public_state(raw["states"][t],8)
                    selected,trace = choose_mask(users,predict_next(positions,raw["actions"][t]),old_mask)
                    decision = decisions[t,lane]
                    expected_decision = {"t":t,"lane":lane,"world_id":world_id,"old_mask":old_mask,
                        "selected_mask":selected,"selected_score":trace["selected_score"],"old_score":trace["old_score"],
                        "counts":{key:trace[key] for key in COUNT_KEYS}}
                    if decision != expected_decision:
                        raise ValueError("training E reconstruction differs")
                    for key in COUNT_KEYS:
                        candidate_counts[key] += trace[key]
                    old_mask = selected
                if raw["mask"][t] != old_mask:
                    raise ValueError("training E held mask or all-on arm differs")
        reset_digests.append(row["reset_digest"])
        print(json.dumps({"reader_training_arm":arm,"groups_verified":group}),flush=True)
    if optimizer_total != EXPECTED_OPTIMIZERS or candidate_counts["requested_candidates"] != (6528000 if arm == "F" else 0):
        raise ValueError("fit total optimizer or E count differs")
    if candidate_counts["requested_candidates"] != binding["mask_requests"]:
        raise ValueError("outer training E binding differs")
    names = ("J","served","quality","height_penalty","ineligible","eligible_unserved","served_p05",
             "served_min","zero_steps","longest_zero_run","mean_path_per_uav","active_mean","all_on_fraction")
    return {"status":"complete","episodes_verified":len(rows),"native_steps_verified":len(rows)*500,
        "native_snapshots_verified":snapshot_count,"optimizer_calls":optimizer_total,
        "mask_candidate_counts":candidate_counts,"initial_digest":binding["initial_digest"],
        "final_digest":binding["final_digest"],"parameter_motion":binding["parameter_motion"],
        "reset_digests":reset_digests,"initialization":initial,
        "post_restore_fit_rng_digest":fit["post_restore_fit_rng_digest"],
        "per_world":rows,"aggregate_training_metrics":{name:float(np.mean([r[name] for r in rows])) for name in names}}


def read_run(out: Path) -> dict:
    from .study import validate_worker
    wall, cpu = time.perf_counter(), time.process_time()
    summary = json.loads((out / "summary.json").read_text())
    validate_worker(summary)
    fits = {arm:verify_fit(arm,summary["fits"][arm],out) for arm in ("A","F")}
    if (fits["A"]["reset_digests"] != fits["F"]["reset_digests"]
            or fits["A"]["post_restore_fit_rng_digest"] != fits["F"]["post_restore_fit_rng_digest"]
            or fits["A"]["initialization"] != fits["F"]["initialization"]):
        raise ValueError("A/F did not share the declared parent/fresh runtime/exogenous scenes")
    spec = EvalSpec()
    rows = summary["episodes"]
    expected = {(arm,w) for arm in ARMS for w in EVAL_WORLD_IDS}
    observed = [(r["arm"],r["world_id"]) for r in rows]
    if len(observed) != len(expected) or set(observed) != expected:
        raise ValueError("incomplete or duplicated evaluation inventory")
    totals = {kind: {key: 0 for key in COUNT_KEYS} for kind in ("motion", "mask")}
    for i,row in enumerate(rows,1):
        _, counts = verify_evaluation(row,out,spec)
        for kind in totals:
            for key in COUNT_KEYS:
                totals[kind][key] += counts[kind][key]
        if i % 16 == 0:
            print(json.dumps({"reader_eval_episodes":i}), flush=True)
    if totals["motion"]["requested_candidates"] != 3456000 or totals["mask"]["requested_candidates"] != 1632000:
        raise ValueError("evaluation algorithmic request count differs")
    result = {"status":"complete", "source_sha":summary["launch_sha"],
        "training":fits,"new_fits":2,"outer_updates":64,"training_steps_verified":512000,
        "evaluation_episodes_verified":len(rows), "evaluation_steps_verified":64000,
        "total_native_steps_verified":576000,
        "native_physics_snapshots_verified":sum(fit["native_snapshots_verified"] for fit in fits.values())+128*501,
        "worker_and_reader_mask_requests":8160000,"worker_and_reader_motion_requests":3456000,
        "scope":"complete saved native physics/feedback/actions/masks and sampler/optimizer accounting; no actor/GRU/optimizer replay",
        "evaluation_candidate_counts":totals, **summarize_evaluation(rows,spec),
        "timing":{"wall_seconds":time.perf_counter()-wall, "cpu_seconds":time.process_time()-cpu,
                  "peak_rss_kib_process":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  "rss_scope":"process lifetime, not a separate reader peak"}}
    write_json(out / "reading.json",result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run",type=Path)
    read_run(parser.parse_args().run)
