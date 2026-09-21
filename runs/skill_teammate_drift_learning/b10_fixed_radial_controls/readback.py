"""Arithmetic B10 readback. No environment, learner, policy forward or simulation."""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
OLD = ROOT.parent / "b09_native_joint"
SOURCE = "3072f05072ec7628f2463bc7ae3b621343d7ca58"
POLICIES = ("J_emp", "M_proj", "IN", "OUT")
CONTRASTS = {"J_minus_IN": (0, 2), "J_minus_OUT": (0, 3),
             "J_minus_M": (0, 1), "M_minus_OUT": (1, 3)}


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


summary = read(ROOT/"summary.json")
assert summary["status"] == "COMPLETE" and summary["launch_sha"] == SOURCE
assert summary["started_evaluation_blocks"] == summary["completed_evaluation_blocks"] == 3
assert summary["started_new_fits"] == summary["completed_new_fits"] == 0
assert summary["seeds"] == [95401, 95402, 95403]
assert read(ROOT/"process-exit.json")["exit_code"] == 0
digests = read(ROOT/"artifacts.json")
for path, value in digests.items():
    assert sha(ROOT/path) == value
source_manifest = read(ROOT/"source-manifest.json")
for item in source_manifest["files"].values():
    frozen = subprocess.check_output(["git", "show", SOURCE+":"+item["path"]], cwd=REPO)
    assert hashlib.sha256(frozen).hexdigest() == item["sha256"]
inputs = read(ROOT/"input-manifest.json")
assert inputs["b09_evidence_commit"] == "69a55e71d9f1bca4e8cdd204adce256cd05a7676"
assert sha(OLD/"artifacts.json") == inputs["root_artifacts_sha256"]
old_digests = read(OLD/"artifacts.json")
input_paths = {"artifacts.json", "summary.json", "source-manifest.json"}
for path in ("summary.json", "source-manifest.json"):
    assert sha(OLD/path) == old_digests[path]

blocks = []
for seed in summary["seeds"]:
    folder = ROOT/f"seed_{seed}"
    for path, digest in read(folder/"artifacts.json").items():
        assert digests[f"seed_{seed}/"+path] == digest
    for path, digest in inputs["verified_seeds"][str(seed)].items():
        relative = f"seed_{seed}/"+path
        assert sha(OLD/relative) == old_digests[relative] == digest
        input_paths.add(relative)
    state = load(folder/"frozen_state.npz")
    previous = load(OLD/f"seed_{seed}"/"state.npz")
    assert state.keys() == previous.keys()
    for key in state:
        exact(state[key], previous[key])
    exact(state["final_updates"], [64, 64])
    exact(state["final_counts"].sum(axis=1), [64, 64])
    p = state["final_probabilities"][1]
    a, b = p[2]+p[3], p[1]+p[3]
    m = np.array([(1-a)*(1-b), (1-a)*b, a*(1-b), a*b])
    t, q = load(folder/"trajectory.npz"), load(folder/"planning.npz")
    bsummary = read(folder/"summary.json")
    assert bsummary["frozen_base_seed"] == seed
    assert len(t["tick"]) == 1024 and len(q["tick"]) == 512
    physical(t)
    physical({name.removeprefix("response_"): array for name, array in q.items() if name.startswith("response_")})
    assert q["response_source_state_unchanged"].all()
    exact(q["response_clone_pre_digest"], np.broadcast_to(q["response_source_state_digest"][:, None, None, :], (512, 2, 4, 32)))
    exact(q["joint_probabilities"], np.broadcast_to(p, (512, 4)))
    exact(q["projected_probabilities"], np.broadcast_to(m, (512, 4)))
    jq = np.stack([table @ p for table in q["response_adapter_reward"]])
    mq = np.stack([table @ m for table in q["response_adapter_reward"]])
    tq = np.stack([table @ np.array([.4, .1, .1, .4]) for table in q["response_adapter_reward"]])
    close(jq, q["joint_values"])
    close(mq, q["projected_values"])
    close(tq, q["true_values_after_choice"])
    choices = np.stack((jq[:, 1] > jq[:, 0], mq[:, 1] > mq[:, 0]), axis=1).astype(int)
    exact(choices, q["choices"])
    rows = q["trajectory_index"]
    exact(rows, np.arange(512))
    exact(t["planner_record_index"][rows], np.arange(512))
    focal, teammate = t["focal_bit"][rows], t["joint_row"][rows]
    exact(choices[np.arange(512), q["policy_index"]], focal)
    selected = (np.arange(512), focal, teammate)
    for key in ("issued_actions", "after_positions", "after_observations", "after_connections",
                "after_sinr", "adapter_reward", "team_reward", "reward_components", "terminated",
                "truncated", "terminal_agents", "truncated_agents"):
        exact(q["response_"+key][selected], t[key][rows])
    close(tq[np.arange(512), focal], q["true_chosen_value_after_choice"])
    close(tq.max(axis=1)-tq[np.arange(512), focal], q["true_regret_after_choice"])
    exact(t["focal_bit"][t["policy_index"] == 2], np.ones(256, dtype=int))
    exact(t["focal_bit"][t["policy_index"] == 3], np.zeros(256, dtype=int))
    exact(t["planner_record_index"][t["policy_index"] >= 2], np.full(512, -1))
    exact(t["rng_address"][:, 1:3], np.broadcast_to([2, 2], (1024, 2)))
    exact(t["joint_row"], np.searchsorted(np.cumsum([.4, .1, .1, .4]), t["external_uniform"], side="right"))
    radial = t["pre_positions"][..., :2]-[500., 500.]
    radii = np.linalg.norm(radial, axis=-1)
    assert np.all(radii > 1e-12)
    dot = ((radial/radii[..., None])*t["issued_actions"][..., :2]).sum(axis=-1)
    assert np.all(np.abs(np.abs(dot)-1.) < 1e-6)
    bits = (dot < 0).astype(int)
    exact(bits[:, 0], t["focal_bit"])
    exact(bits[:, 1:], t["teammate_bits"])
    exact(2*bits[:, 1]+bits[:, 2], t["joint_row"])
    returns, diagnostics = {}, {}
    for policy, name in enumerate(POLICIES):
        returns[name] = []
        diagnostics[name] = []
        for ep in range(4):
            idx = np.flatnonzero((t["policy_index"] == policy) & (t["episode"] == ep))
            exact(t["tick"][idx], np.arange(64))
            exact(t["rng_address"][idx], np.array([[seed, 2, 2, ep, tick] for tick in range(64)]))
            done = np.arange(64) == 63
            exact(t["terminated"][idx], done)
            exact(t["terminal_agents"][idx], np.broadcast_to(done[:, None], (64, 3)))
            assert not t["truncated"][idx].any() and not t["truncated_agents"][idx].any()
            exact(t["terminal_id"][idx], np.where(done, ep, -1))
            for before, after in (("pre_positions", "after_positions"),
                                  ("pre_observations", "after_observations"),
                                  ("pre_connections", "after_connections"), ("pre_sinr", "after_sinr")):
                exact(t[before][idx[1:]], t[after][idx[:-1]])
            ret = math.fsum(t["adapter_reward"][idx])
            returns[name].append(ret)
            close(ret, bsummary["reduction"]["episode_adapter_returns"][name][ep])
            close(math.fsum(t["team_reward"][idx]), bsummary["reduction"]["episode_team_returns"][name][ep])
            diagnostics[name].append({
                "episode": ep, "inward_commands": int(t["focal_bit"][idx].sum()),
                "unserved_ticks": int(64-t["after_connections"][idx].sum()),
                "service_owner_counts": t["after_connections"][idx, :, 0].sum(axis=0).tolist(),
                "coverage_sum": float(t["reward_components"][idx, 0].sum()),
                "quality_sum": float(t["reward_components"][idx, 1].sum()),
                "final_focal_radius": float(np.linalg.norm(t["after_positions"][idx[-1], 0, :2]-[500., 500.])),
            })
        close(math.fsum(returns[name])/4., bsummary["reduction"]["base_mean_adapter_returns"][name])
    for ep in range(4):
        paired = [np.flatnonzero((t["policy_index"] == policy) & (t["episode"] == ep)) for policy in range(4)]
        for idx in paired[1:]:
            for key in ("rng_address", "external_uniform", "teammate_bits", "joint_row", "geometry_slots", "environment_seed"):
                exact(t[key][paired[0]], t[key][idx])
            exact(t["pre_positions"][paired[0][0]], t["pre_positions"][idx[0]])
            exact(t["after_positions"][paired[0], 1:], t["after_positions"][idx, 1:])
        for key in ("focal_bit", "issued_actions", "pre_positions", "after_positions", "pre_observations",
                    "after_observations", "after_connections", "after_sinr", "reward_components", "adapter_reward", "team_reward"):
            exact(t[key][paired[1]], t[key][paired[3]])
    # Recorded namespaces are disjoint; no new random worlds are generated for this audit.
    for name in ("training", "evaluation"):
        old = load(OLD/f"seed_{seed}"/(name+".npz"))
        assert set(map(tuple, t["rng_address"])).isdisjoint(map(tuple, old["rng_address"]))
    contrasts = {}
    for name, (left, right) in CONTRASTS.items():
        values = [x-y for x, y in zip(returns[POLICIES[left]], returns[POLICIES[right]])]
        mean = math.fsum(values)/4.
        close(values, bsummary["reduction"]["contrasts"][name]["paired_episode_adapter_returns"])
        close(mean, bsummary["reduction"]["contrasts"][name]["base_mean_adapter_return"])
        contrasts[name] = {"paired_episodes": values, "mean": mean}
    blocks.append({"seed": seed, "returns": returns, "contrasts": contrasts,
                   "actual_policy_diagnostics": diagnostics, "M_equals_OUT_complete_saved_traces": True})

root_values = {}
for name in CONTRASTS:
    values = [block["contrasts"][name]["mean"] for block in blocks]
    mean = math.fsum(values)/3.
    close(values, summary["reduction"]["base_means"][name])
    close(mean, summary["reduction"]["equal_weight_three_base_means"][name])
    root_values[name] = {"bases": values, "mean": mean}
result = {
    "status": "PASS", "scientific_source": SOURCE, "science_digests_checked": len(digests),
    "unique_input_digests_checked": len(input_paths), "source_digests_checked": len(source_manifest["files"]),
    "actual_rows_checked": 3072, "planner_rows_checked": 1536, "saved_branches_checked": 12288,
    "new_fits": 0, "new_native_calls": 0, "new_probability_or_network_queries": 0,
    "audit_script_sha256": sha(Path(__file__)), "contrasts": root_values, "blocks": blocks,
    "limits": "Stored-trace arithmetic; not an independent channel solve, new policy evaluation or fresh training replication.",
}
(ROOT/"readback.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
print(json.dumps({k: v for k, v in result.items() if k != "blocks"}, indent=2))
