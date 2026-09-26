"""B11 stored-array arithmetic audit; no native calls, training or policy evaluation."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OLD = ROOT.parent / "b09_native_joint"
PREVIOUS = ROOT.parent / "b10_fixed_radial_controls"
SOURCE = "6adcfcd4bd9912f68b29d3664ea6ded935eecc60"
PLAN = "548ae30195031322d38804b3ac90bd37cb4d2b44"
TRUE_Q = np.array([[.1,.4,.4,.1],[.4,.1,.1,.4]])
CELLS = [(law, table, f"{('source','target')[law]}_law_{('source','target')[table]}_table")
         for law in range(2) for table in range(2)]
CONTRASTS = ("D_source", "D_target", "interaction_sum")

def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    with np.load(path, allow_pickle=False) as z:
        a = {key: z[key] for key in z.files}
    assert all(value.dtype != object and np.isfinite(value).all() for value in a.values())
    return a


def exact(x, y):
    np.testing.assert_array_equal(x, y)


def close(x, y):
    np.testing.assert_allclose(x, y, atol=2e-12, rtol=2e-12)


def physical(a):
    position = a["pre_positions"] + a["issued_actions"]*np.float32(30.)
    position[..., :2] = np.clip(position[..., :2], 0., 1000.)
    position[..., 2] = np.clip(position[..., 2], 50., 150.)
    exact(position, a["after_positions"])
    sinr = a["after_sinr"][..., 0]
    best = sinr.argmax(axis=-1)
    connections = (np.arange(3) == best[..., None]) & (sinr.max(axis=-1)[..., None] >= 0)
    exact(connections, a["after_connections"][..., 0])
    cover = connections.sum(axis=-1)
    quality = (np.clip(sinr/30., 0., 1.)*connections).sum(axis=-1)/np.maximum(cover, 1)
    energy = (position[..., 2].mean(axis=-1)-50.)/100.*.1
    reward = .7*cover + .3*quality - energy
    close(np.stack((cover, quality, energy, reward), axis=-1), a["reward_components"])
    close(reward, a["team_reward"])
    close(reward/3., a["adapter_reward"])
summary = read(ROOT / "summary.json")
assert summary["status"] == "COMPLETE" and summary["launch_sha"] == SOURCE
assert summary["plan_source"] == PLAN and summary["seeds"] == [95401,95402,95403]
assert summary["started_evaluation_blocks"] == summary["completed_evaluation_blocks"] == 3
assert summary["started_new_fits"] == summary["completed_new_fits"] == 0
assert summary["total_native_step_calls"] == 110592
assert read(ROOT / "process-exit.json")["exit_code"] == 0
digests = read(ROOT / "artifacts.json")
for path, digest in digests.items():
    assert sha(ROOT / path) == digest
source_manifest = read(ROOT / "source-manifest.json")
for item in source_manifest["files"].values():
    data = subprocess.check_output(["git","show", SOURCE + ":" + item["path"]], cwd=REPO)
    assert hashlib.sha256(data).hexdigest() == item["sha256"]
inputs = read(ROOT / "input-manifest.json")
assert inputs["plan_source"] == PLAN
assert inputs["b09_evidence_commit"] == "69a55e71d9f1bca4e8cdd204adce256cd05a7676"
assert sha(OLD / "artifacts.json") == inputs["root_artifacts_sha256"]
old_digests = read(OLD / "artifacts.json")
input_paths = {"artifacts.json","summary.json","source-manifest.json"}
for path in ("summary.json","source-manifest.json"):
    assert sha(OLD / path) == old_digests[path]

blocks = []
for seed in summary["seeds"]:
    folder = ROOT / f"seed_{seed}"
    for path, digest in read(folder / "artifacts.json").items():
        assert digests[f"seed_{seed}/" + path] == digest
    for path, digest in inputs["verified_seeds"][str(seed)].items():
        relative = f"seed_{seed}/" + path
        assert sha(OLD / relative) == old_digests[relative] == digest
        input_paths.add(relative)
    state, previous = load(folder / "frozen_state.npz"), load(OLD / f"seed_{seed}/state.npz")
    assert state.keys() == previous.keys()
    for key in state:
        exact(state[key], previous[key])
    exact(state["final_updates"], [64,64])
    exact(state["final_counts"].sum(axis=1), [64,64])
    probabilities = state["final_probabilities"]
    exact(probabilities, (state["final_counts"] + .5) / 66.)
    t, q = load(folder / "trajectory.npz"), load(folder / "planning.npz")
    bsummary = read(folder / "summary.json")
    assert bsummary["seed"] == bsummary["rng_master_seed"] == seed
    n = 4096
    assert len(t["tick"]) == len(q["tick"]) == n
    physical(t)
    physical({key.removeprefix("response_"): value for key,value in q.items()
              if key.startswith("response_")})
    assert q["response_source_state_unchanged"].all()
    exact(q["response_clone_pre_digest"],
          np.broadcast_to(q["response_source_state_digest"][:,None,None,:], (n,2,4,32)))
    exact(q["source_probabilities"], np.broadcast_to(probabilities[0], (n,4)))
    exact(q["target_probabilities"], np.broadcast_to(probabilities[1], (n,4)))
    candidate_values = np.stack([np.stack([reward @ p for p in probabilities])
                                 for reward in q["response_adapter_reward"]])
    choices = (candidate_values[:,:,1] > candidate_values[:,:,0]).astype(int)
    true_values = np.stack([reward @ TRUE_Q[law]
                           for reward,law in zip(q["response_adapter_reward"],q["law_id"])])
    candidate_true = np.take_along_axis(true_values, choices, axis=1)
    regrets = true_values.max(axis=1)[:,None] - candidate_true
    close(candidate_values, q["candidate_values"])
    exact(choices, q["candidate_choices"])
    close(true_values, q["true_law_values_after_choices"])
    close(candidate_true, q["candidate_true_chosen_values_after_choice"])
    close(regrets, q["candidate_true_regrets_after_choice"])
    exact(q["trajectory_index"], np.arange(n))
    exact(t["planner_record_index"], np.arange(n))
    exact(t["law_id"], q["law_id"])
    exact(t["table_id"], q["actual_table_id"])
    focal, mate = t["focal_bit"], t["joint_row"]
    exact(choices[np.arange(n),t["table_id"]], focal)
    exact(q["selected_focal_bit"], focal)
    selected = (np.arange(n),focal,mate)
    for key in ("issued_actions","after_positions","after_observations","after_connections",
                "after_sinr","adapter_reward","team_reward","reward_components","terminated",
                "truncated","terminal_agents","truncated_agents"):
        exact(q["response_"+key][selected], t[key])
    close(true_values[np.arange(n),focal], q["actual_true_chosen_value_after_choice"])
    close(true_values.max(axis=1)-true_values[np.arange(n),focal],q["actual_true_regret_after_choice"])
    exact(t["rng_address"][:,1:3],np.broadcast_to([3,3],(n,2)))
    for law in (0,1):
        rows = t["law_id"] == law
        exact(t["joint_row"][rows], np.searchsorted(np.cumsum(TRUE_Q[law]),t["external_uniform"][rows],side="right"))
    radial = t["pre_positions"][...,:2] - [500.,500.]
    radii = np.linalg.norm(radial,axis=-1)
    assert np.all(radii > 1e-12)
    dot = ((radial/radii[...,None])*t["issued_actions"][...,:2]).sum(axis=-1)
    assert np.all(np.abs(np.abs(dot)-1.) < 1e-6)
    bits = (dot < 0).astype(int)
    exact(bits[:,0],focal)
    exact(bits[:,1:],t["teammate_bits"])
    exact(2*bits[:,1]+bits[:,2],mate)

    returns, diagnostics, occupancy = {}, {}, {}
    for law,table,label in CELLS:
        returns[label], diagnostics[label] = [], []
        for ep in range(16):
            idx = np.flatnonzero((t["law_id"]==law)&(t["table_id"]==table)&(t["episode"]==ep))
            exact(t["tick"][idx],np.arange(64))
            exact(t["rng_address"][idx],np.array([[seed,3,3,ep,tick] for tick in range(64)]))
            done = np.arange(64)==63
            exact(t["terminated"][idx],done)
            exact(t["terminal_agents"][idx],np.broadcast_to(done[:,None],(64,3)))
            assert not t["truncated"][idx].any() and not t["truncated_agents"][idx].any()
            exact(t["terminal_id"][idx],np.where(done,ep,-1))
            for before,after in (("pre_positions","after_positions"),("pre_observations","after_observations"),
                                 ("pre_connections","after_connections"),("pre_sinr","after_sinr")):
                exact(t[before][idx[1:]],t[after][idx[:-1]])
            value = math.fsum(t["adapter_reward"][idx])
            returns[label].append(value)
            close(value,bsummary["reduction"]["episode_adapter_returns"][label][ep])
            close(math.fsum(t["team_reward"][idx]),bsummary["reduction"]["episode_team_returns"][label][ep])
            diagnostics[label].append({"episode":ep,"inward_commands":int(focal[idx].sum()),
                "direction_switches":int(np.count_nonzero(focal[idx][1:]!=focal[idx][:-1])),
                "served_ticks":int(t["after_connections"][idx].sum()),
                "service_owner_counts":t["after_connections"][idx,:,0].sum(axis=0).tolist(),
                "coverage_sum":float(t["reward_components"][idx,0].sum()),
                "quality_sum":float(t["reward_components"][idx,1].sum())})
        rows = (q["law_id"]==law)&(q["actual_table_id"]==table)
        delta = regrets[rows,1-law] - regrets[rows,law]
        disagree = choices[rows,0] != choices[rows,1]
        saved = bsummary["occupancy_regret_diagnostics"][label]
        close(delta,saved["same_state_mismatched_minus_matched_regrets"])
        close(math.fsum(delta)/1024.,saved["mean_same_state_mismatched_minus_matched_regret"])
        assert int(disagree.sum()) == saved["candidate_disagreements"]
        for kind,mask in (("better",delta>0),("equal",delta==0),("worse",delta<0)):
            assert int(mask.sum()) == saved[f"matched_{kind}_count"]
            assert int((mask&disagree).sum()) == saved[f"matched_{kind}_on_disagreement_count"]
        occupancy[label] = {"states":1024,"disagreements":int(disagree.sum()),
            "matched_better":int((delta>0).sum()),"matched_worse":int((delta<0).sum()),
            "mean_same_state_mismatched_minus_matched_regret":float(math.fsum(delta)/1024.)}
    for ep in range(16):
        indices = [np.flatnonzero((t["law_id"]==law)&(t["table_id"]==table)&(t["episode"]==ep))
                   for law,table,_ in CELLS]
        for idx in indices[1:]:
            for key in ("rng_address","external_uniform","geometry_slots","environment_seed"):
                exact(t[key][indices[0]],t[key][idx])
            exact(t["pre_positions"][indices[0][0]],t["pre_positions"][idx[0]])
        for left,right in ((0,1),(2,3)):
            for key in ("joint_row","teammate_bits"):
                exact(t[key][indices[left]],t[key][indices[right]])
            exact(t["after_positions"][indices[left],1:],t["after_positions"][indices[right],1:])
        for left,right in ((0,2),(1,3)):
            exact(choices[indices[left][0]],choices[indices[right][0]])
    addresses = set(map(tuple,t["rng_address"]))
    for filename in (OLD/f"seed_{seed}/training.npz",OLD/f"seed_{seed}/evaluation.npz",
                     PREVIOUS/f"seed_{seed}/trajectory.npz"):
        old = load(filename)
        assert addresses.isdisjoint(map(tuple,old["rng_address"]))
    ds = np.asarray(returns[CELLS[0][2]])-returns[CELLS[1][2]]
    dt = np.asarray(returns[CELLS[3][2]])-returns[CELLS[2][2]]
    contrasts = {}
    for name,values in zip(CONTRASTS,(ds,dt,ds+dt)):
        mean = math.fsum(values)/16.
        sd = math.sqrt(math.fsum((float(x)-mean)**2 for x in values)/15.)
        saved = bsummary["reduction"]["contrasts"][name]
        close(values,saved["paired_world_adapter_returns"])
        close(mean,saved["base_mean_adapter_return"])
        close(sd,saved["paired_world_sample_standard_deviation"])
        contrasts[name] = {"paired_worlds":values.tolist(),"mean":mean,"sample_sd":sd}
    blocks.append({"seed":seed,"contrasts":contrasts,"returns":returns,
                   "actual_cell_diagnostics":diagnostics,"same_state_occupancy_diagnostics":occupancy})

root_values = {}
for name in CONTRASTS:
    means = [block["contrasts"][name]["mean"] for block in blocks]
    mean = math.fsum(means)/3.
    mcse = math.sqrt(math.fsum(block["contrasts"][name]["sample_sd"]**2/16. for block in blocks)/9.)
    close(means,summary["reduction"]["base_means"][name])
    close(mean,summary["reduction"]["equal_weight_three_base_means"][name])
    close(mcse,summary["reduction"]["conditional_fixed_base_monte_carlo_standard_errors"][name])
    root_values[name] = {"bases":means,"mean":mean,"conditional_fixed_base_mcse":mcse}
result = {"status":"PASS","scientific_source":SOURCE,"science_digests_checked":len(digests),
    "unique_input_digests_checked":len(input_paths),"source_digests_checked":len(source_manifest["files"]),
    "actual_rows_checked":12288,"planner_rows_checked":12288,"saved_branches_checked":98304,
    "new_fits":0,"new_native_calls":0,"new_probability_or_network_queries":0,
    "audit_script_sha256":sha(Path(__file__)),"contrasts":root_values,"blocks":blocks,
    "limits":"Stored-trace arithmetic, conditioned on three old bases/six tables; no new environment, policy or training replication."}
(ROOT/"readback.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
print(json.dumps({key:value for key,value in result.items() if key!="blocks"},indent=2))
