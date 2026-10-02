"""Independent complete trace/update arithmetic, inherited from original B01."""
from __future__ import annotations
import hashlib
import math
import json
from . import contract as c, models
from .data import read_trace


def independent_soft_target(q):
    import numpy as np
    q = np.asarray(q,dtype=np.float64)
    p = np.exp((q-q.max())/.02)
    return (p/p.sum()).tolist()

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
            "max_pose_reconstruction_error":max_pose_error,"service_tail":service_tail(series["coverage_backhauled"])}


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
        for alias in labels["correctness_audit"]:
            store.bill.enter("reader_alias_reads")
            slot=alias["construction_slot"]
            if (alias["identical"] is not True or alias["logical_sha256"]!=scores[slot]["logical_sha256"]
                    or alias["retained_trace"]!=labels["traces"][str(slot)]["path"]):
                raise ValueError("native audit alias binding mismatch")
        value = {"address":address,"scores":scores,"soft_targets":soft,"ordinary":ordinary_reconstruction(record,scores),
                 "family_counts":{kind:sum(p["kind"]==kind for p in record["features"]["plans"]) for kind in c.KINDS},
                 "selection_report":record["provenance"]["selection_report"],"native_audit":labels["correctness_audit"]}
        if address["split"] == "fresh":
            planner = labels["full_planner"]
            menu = planner["menu"]
            targets = [menu["positions_xyz"][i] for i in menu["m_permutation"]]
            path = f"raw/b{address['block']}/fresh/{address['world']}/full_planner.jsonl.gz"
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
                        or row["grad_l2"] <= 0 or len(row["gradient_sha256"]) != 64):
                    raise AssertionError("invalid loss/gradient update evidence")
                previous = row["parameter_after_sha256"]
        if stream.readline():
            raise AssertionError("extra optimizer update")
    if previous != models.parameter_digest(final):
        raise AssertionError("final weights do not terminate update hash chain")
    optimizer = torch.load(root/(prefix+"/optimizer.pt"),map_location="cpu",weights_only=True)
    groups = optimizer["param_groups"]
    expected_lr = 1e-3
    if (len(groups) != 1 or groups[0]["lr"] != expected_lr or groups[0]["weight_decay"] != 1e-4
            or tuple(groups[0]["betas"]) != (.9,.999) or groups[0]["eps"] != 1e-8):
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




def service_tail(values):
    import numpy as np
    if len(values)!=500 or not all(math.isfinite(v) and 0<=v<=1 for v in values):
        raise ValueError('service tail requires complete H500 bounded coverage')
    longest=run=0
    for value in values:
        run=run+1 if value==0 else 0
        longest=max(longest,run)
    return {'minimum':min(values),'p10':float(np.quantile(values,.1)),
            'zero_steps':sum(v==0 for v in values),'longest_zero_run':longest,
            'final100_mean':sum(values[-100:])/100}
