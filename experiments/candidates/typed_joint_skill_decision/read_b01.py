"""Admitted independent saved-artifact B01 reader; no model construction/backbone replay.

Functional layer arithmetic reconstructs scorers from bound state dictionaries.
Native arithmetic reads every paid trace once. Executed GPU choices remain the
reported policies; CPU discrepancies and their native consequences are explicit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

if __package__ in (None, ""):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from experiments.candidates.typed_joint_skill_decision import contract as c,models
from experiments.candidates.typed_joint_skill_decision.data import hash_file,read_trace
from experiments.candidates.typed_joint_skill_decision.run_b01_learning import (
    accepted_store,assert_prior,dataset_locator,representation_key,
)


def independent_numeric(features,*,reverse=False):
    """Independent field-to-layer mapping, sharing no candidate numeric encoder."""
    permitted = {"initial_uav_xyz","user_xy","bs_xyz","plans","legal_mask","display_order"}
    if set(features) != permitted:
        raise ValueError("reader found noncanonical feature fields")
    order = features["display_order"][::-1] if reverse else features["display_order"][:]
    plans = {p["construction_slot"]:p for p in features["plans"]}
    rows = []
    for slot in order:
        plan = plans[slot]
        geometry = [v for position in features["initial_uav_xyz"] for v in position]
        geometry.extend(v for position in features["user_xy"] for v in position)
        geometry.extend(features["bs_xyz"])
        geometry.extend(v for position in plan["assigned_targets_xyz"] for v in position)
        if len(geometry) != 139:
            raise ValueError("reader geometry width changed")
        row = [float(v)/5000. for v in geometry]
        row.extend(float(plan["kind"] == kind) for kind in ("kmeans_plain","subset_relay","subset_flat"))
        row.extend(float(plan["k"] == k) for k in (4,5,6))
        row.extend(float(slot == k) for k in range(8))
        rows.append(row)
    return rows,order


def functional_logits(state,inputs,arm):
    """No nn.Module, constructor, candidate predictor, optimizer or RNG calls."""
    import torch
    import torch.nn.functional as F
    x = torch.as_tensor(inputs,dtype=torch.float32,device="cpu")
    if any(t.dtype != torch.float32 or t.device.type != "cpu" for t in state.values()):
        raise ValueError("functional scorer weights violate float32 CPU contract")
    with torch.inference_mode():
        if arm == "N":
            expected = {f"{i}.{p}" for i in (0,2,4) for p in ("weight","bias")}
            if set(state) != expected:
                raise ValueError("numeric parameter names changed")
            x = F.gelu(F.linear(x,state["0.weight"],state["0.bias"]),approximate="none")
            x = F.gelu(F.linear(x,state["2.weight"],state["2.bias"]),approximate="none")
            result = F.linear(x,state["4.weight"],state["4.bias"])
        elif arm == "L":
            expected = {f"{i}.{p}" for i in (0,1,3) for p in ("weight","bias")}
            if set(state) != expected:
                raise ValueError("pretrained scorer parameter names changed")
            x = F.layer_norm(x,(1024,),state["0.weight"],state["0.bias"],eps=1e-5)
            x = F.gelu(F.linear(x,state["1.weight"],state["1.bias"]),approximate="none")
            result = F.linear(x,state["3.weight"],state["3.bias"])
        else:
            raise ValueError("unknown arm")
    if not torch.isfinite(result).all():
        raise ArithmeticError("nonfinite independent functional logits")
    return result.squeeze(-1).tolist()


def independent_soft_target(q):
    import numpy as np
    values = np.asarray(q,dtype=np.float64)
    shifted = np.exp((values-values.max())/.02)
    return (shifted/shifted.sum()).tolist()


def close_numbers(a,b,atol=1e-12):
    if abs(float(a)-float(b)) > atol:
        raise AssertionError(f"saved native arithmetic mismatch: {a} vs {b}")


def read_episode(dataset,relative,targets,reset,stored_result,bill):
    import numpy as np
    bill.enter("reader_episode_reads")
    logical = hashlib.sha256()
    series = {name:[] for name in ("contract_reward","coverage_backhauled",
                                  "frontend_capacity_with_path_mbps","mean_relays_per_routed_uav")}
    fields = reset["fields"]
    previous_pose = np.asarray(fields["uav_positions"],dtype=float)
    connections = np.asarray(fields["connections"],dtype=bool)
    prior_association = np.where(connections.any(axis=0),np.argmax(connections,axis=0),-1)
    routed = np.asarray([str(i) in fields["routing_paths"] for i in range(6)])
    prior_backhaul = np.any(connections&routed[:,None],axis=0)
    association_changes,backhaul_losses = 0,0
    rows,steps,pending,max_pose_error = 0,0,None,0.
    target = np.asarray(targets,dtype=float)
    for row in read_trace(dataset.root/relative):
        logical.update(c.encode_json(row))
        rows += 1
        kind = row["kind"]
        if rows == 1:
            if row != {"kind":"assigned_targets","assigned_targets_xyz":targets}:
                raise AssertionError("trace command identity changed")
            continue
        if rows == 2:
            if row != {"kind":"reset","identity":reset}:
                raise AssertionError("trace full reset identity changed")
            continue
        if kind == "step_request":
            if pending is not None or row["step"] != steps:
                raise AssertionError("duplicate/misordered step request")
            positions = np.asarray(row["positions_xyz"],dtype=float)
            if not np.array_equal(positions,previous_pose):
                raise AssertionError("trace live pose continuity changed")
            delta = target-positions
            distances = np.sqrt(np.sum(delta*delta,axis=1))
            expected = np.zeros((6,3),dtype=float)
            far = distances > 30.
            land = (distances > 1e-6)&~far
            expected[far] = delta[far]/distances[far,None]
            expected[land] = delta[land]/30.
            norms = np.sqrt(np.sum(expected*expected,axis=1))
            over = norms > 1.
            expected[over] /= norms[over,None]
            actions = np.asarray(row["actions"],dtype=float)
            if not np.allclose(expected,actions,rtol=0,atol=1e-12):
                raise AssertionError("frozen feedback/hold action differs")
            pending = actions
        elif kind == "step":
            if pending is None or row["step"] != steps+1:
                raise AssertionError("native transition without matching request")
            norms = np.sqrt(np.sum(pending*pending,axis=1))
            over = norms>1.
            pending[over] /= norms[over,None]
            expected_pose = previous_pose+30.*pending
            expected_pose[:,:2] = np.clip(expected_pose[:,:2],0,5000)
            expected_pose[:,2] = np.clip(expected_pose[:,2],50,150)
            previous_pose = np.asarray(row["positions_xyz"],dtype=float)
            error = float(np.max(np.abs(previous_pose-expected_pose)))
            max_pose_error = max(max_pose_error,error)
            if error > 1e-9:
                raise AssertionError("native move/landing/clipping reconstruction differs")
            info = row["reward_info"]
            for name in series:
                value = float(info[name])
                if not math.isfinite(value):
                    raise ValueError("nonfinite raw native series")
                series[name].append(value)
            association = np.asarray(row["user_association"],dtype=int)
            independent_backhaul = np.asarray([uav >= 0 and str(uav) in row["routing_paths"] for uav in association],dtype=bool)
            if not np.array_equal(independent_backhaul,np.asarray(row["backhauled_users_mask"],dtype=bool)):
                raise AssertionError("saved user backhaul mask disagrees with association/routing")
            coverage = float(independent_backhaul.sum())/50.
            close_numbers(coverage,info["coverage_backhauled"])
            close_numbers(.5*(coverage+info["throughput_term"]),info["contract_reward"])
            close_numbers(info["frontend_capacity_with_path_mbps"]*1e6/(6*20e6*math.log2(1001)),info["throughput_term"])
            close_numbers(sum(row["rewards"].values()),info["contract_reward"],1e-9)
            backhaul = np.asarray(row["backhauled_users_mask"],dtype=bool)
            association_changes += int(np.sum(association != prior_association))
            backhaul_losses += int(np.sum(prior_backhaul&~backhaul))
            prior_association,prior_backhaul = association,backhaul
            steps += 1
            if steps < 500 and any(row["terminations"].values()):
                raise AssertionError("early native termination")
            if steps == 500 and not all(row["terminations"].values()):
                raise AssertionError("missing H500 native termination")
            if any(row["truncations"].values()):
                raise AssertionError("unexpected native truncation")
            pending = None
        else:
            raise ValueError("unknown raw native row")
        bill.check()
    if steps != 500 or rows != 1002 or pending is not None:
        raise AssertionError("incomplete native trace")
    entry = dataset.files[relative]
    if logical.hexdigest() != entry["logical_sha256"]:
        raise AssertionError("native logical series digest changed")
    if np.max(np.linalg.norm(previous_pose-target,axis=1)) > 1e-6:
        raise AssertionError("native episode failed to arrive/hold")
    means = {name:float(np.mean(values,dtype=np.float64)) for name,values in series.items()}
    for name,value in means.items():
        close_numbers(value,stored_result[name+"_mean_all"])
        close_numbers(float(np.mean(series[name][-100:],dtype=np.float64)),stored_result[name+"_mean_final100"])
    close_numbers(means["coverage_backhauled"],stored_result["Q"])
    if association_changes != stored_result["association_change_count"] or backhaul_losses != stored_result["backhaul_loss_events"]:
        raise AssertionError("native association/backhaul events changed")
    return {"Q":means["coverage_backhauled"],"native_means":means,"association_change_count":association_changes,
            "backhaul_loss_events":backhaul_losses,"steps":steps,"logical_sha256":logical.hexdigest(),
            "max_pose_reconstruction_error":max_pose_error}


def ordinary_reconstruction(record,scores):
    import numpy as np
    features,labels = record["features"],record["labels"]
    initial = np.asarray(features["initial_uav_xyz"],dtype=float)
    initial_c = float(labels["ordinary"]["initial_native_static_info"]["coverage_backhauled"])
    rank_static,rank_travel = [],[]
    for plan in features["plans"]:
        slot = plan["construction_slot"]
        distances = np.linalg.norm(initial-np.asarray(plan["assigned_targets_xyz"],dtype=float),axis=1)
        dmax,total = float(distances.max()),float(distances.sum())
        static = float(labels["ordinary"]["static_by_slot"][str(slot)]["coverage_backhauled"])
        alpha = min(dmax/15000.,1.)
        rank_static.append((-static,dmax,total,slot))
        rank_travel.append((-((1-alpha)*static+alpha*initial_c),dmax,total,slot))
    chosen = {"static":min(rank_static)[-1],"travel":min(rank_travel)[-1]}
    if chosen != labels["ordinary"]["selected_slots"]:
        raise AssertionError("ordinary static/travel policy changed")
    slots = sorted(scores)
    fallback = {str(requested):requested if requested in slots else slots[0] for requested in range(8)}
    if fallback != labels["ordinary"]["fixed_policy_executed_slots"]:
        raise AssertionError("absent construction-slot fallback changed")
    return {**chosen,"fixed_executed_slots":fallback,
            "uniform_Q":sum(v["Q"] for v in scores.values())/len(scores),
            "menu_best_Q":max(v["Q"] for v in scores.values())}


def reconstruct_native(store,dataset):
    worlds = {}
    for record in dataset.records:
        address,labels = record["address"],record["labels"]
        store.current = {**address,"phase":"read_native"}
        reset = record["provenance"]["reset_identity"]
        scores = {}
        for plan in record["features"]["plans"]:
            slot = plan["construction_slot"]
            trace = labels["traces"][str(slot)]
            result = labels["candidate_results"][str(slot)]
            scores[slot] = read_episode(dataset,trace["path"],plan["assigned_targets_xyz"],reset,result,store.bill)
        q = [scores[s]["Q"] for s in labels["slot_order"]]
        for actual,expected in zip(q,labels["Q"]):
            close_numbers(actual,expected)
        soft = independent_soft_target(q)
        for actual,expected in zip(soft,labels["soft_targets"]):
            close_numbers(actual,expected,1e-14)
        value = {"address":address,"scores":scores,"soft_targets":soft,"ordinary":ordinary_reconstruction(record,scores),
                 "family_counts":{kind:sum(p["kind"]==kind for p in record["features"]["plans"]) for kind in c.KINDS},
                 "selection_report":record["provenance"]["selection_report"],"native_audit":labels["correctness_audit"]}
        if address["split"] == "test":
            planner = labels["full_planner"]
            menu = planner["menu"]
            targets = [menu["positions_xyz"][i] for i in menu["m_permutation"]]
            path = f"raw/b{address['block']}/test/{address['world']}/full_planner.jsonl.gz"
            value["planner"] = read_episode(dataset,path,targets,reset,planner["result"],store.bill)
            value["planner"]["static_evaluation_calls"] = planner["static_evaluation_calls"]
            value["planner"]["compute_menu_wall_seconds"] = planner["compute_menu_wall_seconds"]
        worlds[address["world"]] = value
        store.write_json(f"native/b{address['block']}/{address['split']}/{address['world']}.json",value,kind="independent_native_read")
        store.status("reading_native")
    return worlds


def read_update_chain(root,prefix,config,initial,final,records,bill):
    import numpy as np
    import torch
    previous = models.parameter_digest(initial)
    if previous != config["initial_sha256"]:
        raise AssertionError("saved initial model identity changed")
    rng = np.random.Generator(np.random.PCG64(config["order_seed"]))
    with (root/(prefix+"/updates.jsonl")).open("rb") as stream:
        count,exposures = 0,0
        for epoch in range(64):
            order = rng.permutation(256).tolist()
            for batch in range(8):
                line = stream.readline()
                if not line:
                    raise AssertionError("incomplete update/exposure chain")
                row = json.loads(line)
                indices = order[32*batch:32*(batch+1)]
                bill.enter("reader_updates_read")
                count += 1
                exposures += len(indices)
                expected_worlds = [records[i]["address"]["world"] for i in indices]
                expected_features = [c.digest(records[i]["features"]) for i in indices]
                if (row["update"] != count or row["epoch"] != epoch or row["batch"] != batch
                        or row["indices"] != indices or row["worlds"] != expected_worlds
                        or row["feature_sha256"] != expected_features or row["parameter_before_sha256"] != previous):
                    raise AssertionError("update identity/exposure/order/hash chain changed")
                if (not all(math.isfinite(row[key]) for key in ("loss","grad_l2","grad_max_absolute"))
                        or row["grad_l2"] < 0 or len(row["gradient_sha256"]) != 64):
                    raise AssertionError("invalid loss/gradient update evidence")
                previous = row["parameter_after_sha256"]
        if stream.readline():
            raise AssertionError("extra optimizer update")
    if previous != models.parameter_digest(final):
        raise AssertionError("final weights do not terminate update hash chain")
    optimizer = torch.load(root/(prefix+"/optimizer.pt"),map_location="cpu",weights_only=True)
    groups = optimizer["param_groups"]
    expected_lr = 1e-3 if config["arm"] == "N" else 1e-4
    if len(groups) != 1 or groups[0]["lr"] != expected_lr or groups[0]["weight_decay"] != 1e-4:
        raise AssertionError("endpoint AdamW configuration changed")
    if len(optimizer["state"]) != len(final):
        raise AssertionError("missing endpoint optimizer state")
    for value in optimizer["state"].values():
        if float(value["step"]) != 512 or any(not torch.isfinite(value[k]).all() for k in ("exp_avg","exp_avg_sq")):
            raise AssertionError("optimizer step/moment evidence changed")
    return {"updates":count,"contexts":exposures,"initial_sha256":models.parameter_digest(initial),
            "final_sha256":previous,"movement":models.tensor_movement(final,initial),
            "reliance":"saved chain/gradient/movement attestations; optimizer trajectory not independently replayed"}


def uncertainty(values):
    n = len(values)
    mean = sum(values)/n
    variance = sum((x-mean)**2 for x in values)/(n-1) if n>1 else 0.
    se = math.sqrt(variance/n)
    return {"n_worlds":n,"mean":mean,"sample_sd":math.sqrt(variance),"standard_error":se,
            "normal_approx_95_interval":[mean-1.96*se,mean+1.96*se]}


def require_members(files,paths):
    missing = sorted(set(paths)-set(files))
    if missing:
        raise ValueError(f"consumed learning artifact absent from bound manifest: {missing}")


def required_learning_paths(dataset):
    paths = ["config.json","summary.json","cache_index.json"]
    for record in dataset.records:
        paths.append(representation_key(record))
        if record["address"]["split"] == "test":
            paths.append(representation_key(record,True))
    for record in dataset.split(1,"train")[:16]:
        paths.append(f"correctness/{record['address']['world']}.json")
    for block in (1,2,3):
        for arm in ("N","L"):
            prefix = f"fits/b{block}/{arm}/"
            paths.extend(prefix+name for name in ("config.json","initial.pt","final.pt","optimizer.pt",
                "updates.jsonl","summary.json","initial-test.json","final-test.json","final-reverse-test.json"))
    return paths


def cost_readout(dataset,learning_root):
    """Read paid measurements only; assemble segmented online components honestly."""
    import torch
    config = json.loads((learning_root/"config.json").read_bytes())
    rows = []
    canonical_forward,codec_times,token_lengths,construction,matching,ordinary_static,ordinary_rank = [],[],[],[],[],[],[]
    endpoint_costs = []
    for block in (1,2,3):
        for arm in ("N","L"):
            for name in ("initial-test.json","final-test.json","final-reverse-test.json"):
                endpoint = json.loads((learning_root/f"fits/b{block}/{arm}/{name}").read_bytes())
                endpoint_costs.append({"block":block,"arm":arm,"endpoint":name,
                    "active_scorer_wall_seconds":endpoint["active_scorer_wall_seconds"],
                    "warm_scorer_seconds_per_world":endpoint["warm_scorer_seconds_per_world"]})
    for record in dataset.records:
        address = record["address"]
        provenance,ordinary = record["provenance"],record["labels"]["ordinary"]
        cache = torch.load(learning_root/representation_key(record),map_location="cpu",weights_only=True)
        build = provenance["construction_and_shadow_wall_seconds"]
        match = provenance["matching_wall_seconds"]
        static = ordinary["ordinary_static_package_wall_seconds"]
        rank = ordinary["ordinary_ranking_wall_seconds"]
        forward,codec = cache["full_forward_wall_seconds"],cache["codec_wall_seconds"]
        construction.append(build);matching.append(match);ordinary_static.append(static);ordinary_rank.append(rank)
        canonical_forward.append(forward);codec_times.append(codec);token_lengths.append(cache["full_tokens"])
        value = {"world":address["world"],"block":address["block"],"split":address["split"],
                 "common_construction_seconds":build,"common_matching_seconds":match,
                 "ordinary_M_plus_1_static_package_seconds":static,"ordinary_static_query_seconds":ordinary["ordinary_static_query_wall_seconds"],
                 "ordinary_rank_seconds":rank,"L_codec_seconds":codec,"L_full_source_call_seconds":forward,
                 "L_full_tokens":cache["full_tokens"],"ordinary_segmented_seconds":build+match+static+rank}
        if address["split"] == "test":
            # Endpoint per-world means are actually measured scorer panels, not an
            # invented timing for a specific individual object's fitted prediction.
            scorers = {arm:next(x["warm_scorer_seconds_per_world"] for x in endpoint_costs
                                if x["block"]==address["block"] and x["arm"]==arm and x["endpoint"]=="final-test.json")
                       for arm in ("N","L")}
            value["N_segmented_seconds"] = build+match+scorers["N"]
            value["L_segmented_seconds"] = build+match+codec+forward+scorers["L"]
            value["full_planner_compute_menu_seconds"] = record["labels"]["full_planner"]["compute_menu_wall_seconds"]
        rows.append(value)
    return {"worlds":rows,"cold_source_load":config["source"]["cold_load_wall_seconds"],
            "endpoint_scorer_panels":endpoint_costs,"canonical_full_source_call":uncertainty(canonical_forward),
            "codec":uncertainty(codec_times),"sequence_lengths":{"min":min(token_lengths),"max":max(token_lengths),
                                                              "mean":sum(token_lengths)/len(token_lengths)},
            "construction":uncertainty(construction),"matching":uncertainty(matching),
            "ordinary_static_package":uncertainty(ordinary_static),"ordinary_rank":uncertainty(ordinary_rank),
            "native_collector_bill":dataset.summary["bill"],"native_nested_helper_timings":dataset.summary.get("timings",{}),
            "limits":["segmented assembly, not a post-fit end-to-end online benchmark",
                      "N numeric input conversion, outer serialization and fresh host reset per-world online costs unmeasured separately",
                      "source cold load excludes interpreter/import startup; first codec call can include tokenizer cold load",
                      "offline cache does not remove L full encoder/two-head cost in deployment",
                      "full source call includes frozen original scorer and act head; segmented L also adds fitted adapter scorer",
                      "native helper timers overlap; process CPU/reserved GPU/global disk bills are authoritative"]}


def read_scorers(store,dataset,learning_root,worlds):
    import torch
    import numpy as np
    outputs = {}
    for block in (1,2,3):
        train,test = dataset.split(block,"train"),dataset.split(block,"test")
        fixed_means = {}
        for requested in range(8):
            readings = []
            for record in train:
                world = worlds[record["address"]["world"]]
                executed = world["ordinary"]["fixed_executed_slots"][str(requested)]
                readings.append(world["scores"][executed]["Q"])
            fixed_means[requested] = sum(readings)/len(readings)
        fixed = min(range(8),key=lambda requested:(-fixed_means[requested],requested))
        block_output = {"train_selected_requested_slot":fixed,"fixed_policy_training_means":fixed_means,
                        "fits":{},"worlds":{}}
        for arm in ("N","L"):
            prefix = f"fits/b{block}/{arm}"
            initial = torch.load(learning_root/(prefix+"/initial.pt"),map_location="cpu",weights_only=True)
            final = torch.load(learning_root/(prefix+"/final.pt"),map_location="cpu",weights_only=True)
            config = json.loads((learning_root/(prefix+"/config.json")).read_bytes())
            if (config["model_seed"] != c.BASES[block-1]+20001 or config["order_seed"] != c.BASES[block-1]+20002
                    or config["epochs"] != 64 or config["batch_size"] != 32 or config["arm"] != arm
                    or config["parameters"] != (105473 if arm=="N" else 1052673)):
                raise AssertionError("fixed fit configuration changed")
            block_output["fits"][arm] = read_update_chain(learning_root,prefix,config,initial,final,train,store.bill)
            if arm == "L":
                cache_identity = json.loads((learning_root/"cache_index.json").read_bytes())
                if models.parameter_digest(initial) != cache_identity["source_scorer_sha256"]:
                    raise AssertionError("L initial scorer differs from pinned source/cache scorer")
            reads = []
            stages = [("initial",initial,train,False),("final",final,train,False),
                      ("initial",initial,test,False),("final",final,test,False),("final",final,test,True)]
            for stage,state,records,reverse in stages:
                saved = {}
                if records is test:
                    name = f"{prefix}/{stage}{'-reverse' if reverse else ''}-test.json"
                    endpoint = json.loads((learning_root/name).read_bytes())
                    saved = {p["world"]:p for p in endpoint["predictions"]}
                    if set(saved) != {r["address"]["world"] for r in records}:
                        raise AssertionError("endpoint world set changed")
                for record in records:
                    world_id = record["address"]["world"]
                    store.current = {"phase":"read_scorer","block":block,"arm":arm,"stage":stage,
                                     "split":record["address"]["split"],"world":world_id,"reverse":reverse}
                    if arm == "N":
                        inputs,slots = independent_numeric(record["features"],reverse=reverse)
                    else:
                        cache = torch.load(learning_root/representation_key(record,reverse),map_location="cpu",weights_only=True)
                        slots = list(record["features"]["display_order"])
                        if reverse:
                            slots.reverse()
                        if (cache["slots"] != slots or cache["feature_sha256"] != c.digest(record["features"])
                                or cache["post_head_features"].dtype != torch.float32):
                            raise AssertionError("reader bound feature cache changed")
                        inputs = cache["post_head_features"]
                    store.bill.enter(f"reader_{arm}_contexts")
                    logits = functional_logits(state,inputs,arm)
                    # Independent argmax inversion; exact ties preserve display first.
                    selected = slots[max(range(len(slots)),key=lambda i:logits[i])]
                    world = worlds[world_id]
                    q = [world["scores"][slot]["Q"] for slot in slots]
                    pref = independent_soft_target(q)
                    shifted = np.asarray(logits,dtype=np.float64)-max(logits)
                    logprob = shifted-np.log(np.exp(shifted).sum())
                    row = {"world":world_id,"stage":stage,"split":record["address"]["split"],"reverse":reverse,
                           "slots":slots,"logits":logits,"selected_slot":selected,
                           "Q":world["scores"][selected]["Q"],"soft_CE":float(-np.dot(pref,logprob))}
                    if records is test:
                        executed = saved[world_id]
                        if executed["slots"] != slots or executed["feature_sha256"] != c.digest(record["features"]):
                            raise AssertionError("runner endpoint inversion/input changed")
                        executed_slot = executed["selected_slot"]
                        inferred = slots[max(range(len(slots)),key=lambda i:executed["logits"][i])]
                        if executed_slot != inferred:
                            raise AssertionError("runner endpoint logit-to-command inversion changed")
                        error = max(abs(a-b) for a,b in zip(logits,executed["logits"]))
                        row["runner_discrepancy"] = {"max_absolute_logit":error,"choice_changed":selected!=executed_slot,
                            "independent_minus_executed_Q":row["Q"]-world["scores"][executed_slot]["Q"],
                            "executed_slot":executed_slot,"executed_Q":world["scores"][executed_slot]["Q"],
                            "logits_within_tolerance":all(abs(a-b) <= models.FLOAT_TOLERANCE["atol"]+models.FLOAT_TOLERANCE["rtol"]*abs(b)
                                                          for a,b in zip(logits,executed["logits"]))}
                        name = arm+"_"+stage+("_reverse" if reverse else "")
                        block_output["worlds"].setdefault(world_id,{})[name] = {**row,"executed_native_means":world["scores"][executed_slot]["native_means"]}
                    reads.append(row)
                store.status("reading_scorers")
            train_metrics = {}
            for stage in ("initial","final"):
                subset = [r for r in reads if r["split"]=="train" and r["stage"]==stage]
                regrets = [worlds[r["world"]]["ordinary"]["menu_best_Q"]-r["Q"] for r in subset]
                concentration = {str(slot):sum(r["selected_slot"]==slot for r in subset) for slot in range(8)}
                train_metrics[stage] = {"soft_CE":uncertainty([r["soft_CE"] for r in subset]),
                                       "regret":uncertainty(regrets),"selected_slot_counts":concentration}
            block_output["fits"][arm]["train_metrics"] = train_metrics
            block_output["fits"][arm]["test_selected_slot_counts"] = {
                stage:{str(slot):sum(r["runner_discrepancy"]["executed_slot"]==slot for r in reads
                                      if r["split"]=="test" and r["stage"]==stage and not r["reverse"])
                       for slot in range(8)} for stage in ("initial","final")}
            store.write_json(f"scorers/b{block}/{arm}.json",{"readings":reads,"fit":block_output["fits"][arm]},kind="functional_scorer_read")
        # Preserve every test world, native tradeoff, failure/adverse increment and order effect.
        for record in test:
            wid = record["address"]["world"]
            world = worlds[wid]
            row = block_output["worlds"][wid]
            fixed_slot = world["ordinary"]["fixed_executed_slots"][str(fixed)]
            row["ordinary"] = {"fixed_Q":world["scores"][fixed_slot]["Q"],"fixed_slot":fixed_slot,
                "static_Q":world["scores"][world["ordinary"]["static"]]["Q"],
                "travel_Q":world["scores"][world["ordinary"]["travel"]]["Q"],
                "uniform_Q":world["ordinary"]["uniform_Q"],"menu_best_Q":world["ordinary"]["menu_best_Q"],
                "planner_Q":world["planner"]["Q"],"planner_static_evaluation_calls":world["planner"]["static_evaluation_calls"],
                "planner_compute_menu_wall_seconds":world["planner"]["compute_menu_wall_seconds"],
                "family_counts":world["family_counts"],"selection_report":world["selection_report"]}
            native_names = list(world["scores"][fixed_slot]["native_means"])
            row["ordinary"]["native_means"] = {
                "fixed":world["scores"][fixed_slot]["native_means"],
                "static":world["scores"][world["ordinary"]["static"]]["native_means"],
                "travel":world["scores"][world["ordinary"]["travel"]]["native_means"],
                "uniform":{name:sum(value["native_means"][name] for value in world["scores"].values())/len(world["scores"])
                           for name in native_names},"planner":world["planner"]["native_means"]}
        rows = list(block_output["worlds"].values())
        def executed(row,arm,stage="final",reverse=False):
            return row[arm+"_"+stage+("_reverse" if reverse else "")]["runner_discrepancy"]["executed_Q"]
        metrics = {"L_minus_N":[executed(r,"L")-executed(r,"N") for r in rows],
                   "menu_increment_over_fixed":[r["ordinary"]["menu_best_Q"]-r["ordinary"]["fixed_Q"] for r in rows]}
        for arm in ("N","L"):
            metrics[arm+"_regret"] = [r["ordinary"]["menu_best_Q"]-executed(r,arm) for r in rows]
            metrics[arm+"_learning_delta"] = [executed(r,arm)-executed(r,arm,"initial") for r in rows]
            metrics[arm+"_reverse_delta"] = [executed(r,arm,reverse=True)-executed(r,arm) for r in rows]
            for baseline in ("fixed","static","travel","uniform","planner"):
                metrics[arm+"_minus_"+baseline] = [executed(r,arm)-r["ordinary"][baseline+"_Q"] for r in rows]
        block_output["metrics"] = {name:uncertainty(values) for name,values in metrics.items()}
        absolute = {}
        for arm in ("N","L"):
            for stage in ("initial","final","final_reverse"):
                name = arm+"_"+stage
                absolute[name] = {field:uncertainty([r[name]["executed_native_means"][field] for r in rows])
                                  for field in rows[0][name]["executed_native_means"]}
        for name in ("fixed","static","travel","uniform","planner"):
            absolute[name] = {field:uncertainty([r["ordinary"]["native_means"][name][field] for r in rows])
                              for field in rows[0]["ordinary"]["native_means"][name]}
        block_output["absolute_native_means"] = absolute
        outputs[block] = block_output
        store.write_json(f"blocks/b{block}.json",block_output,kind="complete_block_read")
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed",type=int,required=True,choices=(0,))
    parser.add_argument("--launch-sha",required=True)
    parser.add_argument("--out","--out-dir",dest="out_dir",type=Path,required=True)
    parser.add_argument("--budget-ledger",type=Path,required=True)
    parser.add_argument("--budget-ledger-sha256",required=True)
    parser.add_argument("--dataset-input",type=Path,required=True)
    parser.add_argument("--dataset-input-sha256",required=True)
    parser.add_argument("--learning-input",type=Path,required=True)
    parser.add_argument("--learning-input-sha256",required=True)
    args = parser.parse_args(argv)
    from scripts.hmasd_admission import ENVIRONMENT_KEY,require_admission
    paths = json.loads(os.environ.get(ENVIRONMENT_KEY,"{}"))
    admission = require_admission(__file__,direction="typed_joint_skill_decision")
    store,admission,prior,root = accepted_store(__file__,args,admission,paths)
    try:
        threads = models.cpu_thread_environment()
        dataset_root,native_locator = dataset_locator(args.dataset_input,args.dataset_input_sha256)
        learning_root,learning_locator = dataset_locator(args.learning_input,args.learning_input_sha256)
        dataset = models.Dataset(dataset_root,native_locator["manifest_sha256"])
        dataset.require_source_sha(admission["sha"])
        learning_files = models.verify_manifest(learning_root,learning_locator["manifest_sha256"])
        require_members(learning_files,required_learning_paths(dataset))
        learning_summary = json.loads((learning_root/"summary.json").read_bytes())
        learning_config = json.loads((learning_root/"config.json").read_bytes())
        if (learning_summary["status"] != "complete" or learning_summary["dataset_manifest_sha256"] != native_locator["manifest_sha256"]
                or learning_summary["contract_sha256"] != c.digest(c.frozen_contract())):
            raise ValueError("incomplete/unmatched learning phase")
        if (learning_summary.get("launch_sha") != admission["sha"] or learning_config.get("admission",{}).get("sha") != admission["sha"]
                or learning_config["dataset_manifest_sha256"] != native_locator["manifest_sha256"]):
            raise ValueError("reader/native/learning sequential source identities differ")
        assert_prior(prior,learning_summary)
        if any(not any(p.is_relative_to(r) for r in store.bill.roots) for p in (dataset_root,learning_root)):
            raise ValueError("reader inputs missing from global disk bill")
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.set_default_dtype(torch.float32)
        store.write_json("config.json",{"admission":admission,"dataset_locator":native_locator,
            "dataset_locator_sha256":args.dataset_input_sha256,"learning_locator":learning_locator,
            "learning_locator_sha256":args.learning_input_sha256,"prior_bill_sha256":args.budget_ledger_sha256,
            "dtype":"float32","device":"cpu","torch_cpu_threads":1,"cpu_thread_environment":threads,
            "torch_version":torch.__version__,"tolerance":models.FLOAT_TOLERANCE},kind="reader_config")
        worlds = reconstruct_native(store,dataset)
        blocks = read_scorers(store,dataset,learning_root,worlds)
        costs = cost_readout(dataset,learning_root)
        store.write_json("costs.json",costs,kind="paid_cost_readout")
        if store.bill.delta["reader_N_contexts"] != 2688 or store.bill.delta["reader_L_contexts"] != 2688 or store.bill.delta["reader_updates_read"] != 3072:
            raise AssertionError("complete reader bill differs from declared contexts/updates")
        status = store.status("complete")
        effects = [blocks[b]["metrics"]["L_minus_N"]["mean"] for b in (1,2,3)]
        store.write_json("summary.json",{**status,"launch_sha":args.launch_sha,"contract_sha256":c.digest(c.frozen_contract()),
            "block_effects_L_minus_N":effects,"independent_downstream_replications":3,
            "block_metrics":{str(b):blocks[b]["metrics"] for b in blocks},
            "block_absolute_native_means":{str(b):blocks[b]["absolute_native_means"] for b in blocks},
            "fit_and_train_summaries":{str(b):blocks[b]["fits"] for b in blocks},
            "cost_readout":"costs.json","learning_gpu_peak":learning_summary["gpu_peak"],
            "frozen_state_sha256":learning_summary["frozen_state_sha256"],
            "native_worlds_read":len(worlds),"learning_manifest_sha256":learning_locator["manifest_sha256"],
            "reliance":["pinned source/checkpoint/full-source agreement and post-head cache; no encoder replay",
                        "saved 512-update chains and gradient/movement attestations; no Adam replay",
                        "static native queries trusted from bound source records; no static re-query"],
            "claim_scope":"one fixed data budget, same-distribution conditional package capability; no semantic/pretraining-causal/transfer/sample-efficiency/deployment claim"},kind="reader_summary")
        return 0
    except BaseException as exc:
        failed = store.status("failed_partial",exception_type=type(exc).__name__,exception=str(exc))
        (store.output/"failure.json").write_bytes(c.encode_json({**failed,"traceback":traceback.format_exc()}))
        raise
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
