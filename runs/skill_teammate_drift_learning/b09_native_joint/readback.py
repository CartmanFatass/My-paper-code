"""B09 artifact/trace arithmetic audit; no learner, environment, fit or forward call.

Run from the repository root with the science Python. This reads frozen observations
and response tables only; diagnostics below are retrospective, not new endpoints.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE = "efe9ce4f39cdb9147d28bbb5c00e7be91dbfca55"
TRUE = np.array([[.1, .4, .4, .1], [.4, .1, .1, .4]])


def read(path):
    return json.loads(path.read_text())


def load(path):
    with np.load(path, allow_pickle=False) as data:
        result = {key: data[key] for key in data.files}
    assert all(a.dtype != object and np.isfinite(a).all() for a in result.values())
    return result


def exact(a, b):
    np.testing.assert_array_equal(a, b)


def close(a, b):
    np.testing.assert_allclose(a, b, atol=2e-12, rtol=2e-12)


def project(p):
    first, second = p[..., 2] + p[..., 3], p[..., 1] + p[..., 3]
    return np.stack(((1-first)*(1-second), (1-first)*second,
                     first*(1-second), first*second), axis=-1)


def physical(a):
    """Reconcile movement, recorded SINR assignment, components and reward scaling.

    This does not independently solve the channel model or rebuild observations.
    """
    positions = a["pre_positions"] + a["issued_actions"] * np.float32(30.)
    positions[..., :2] = np.clip(positions[..., :2], 0., 1000.)
    positions[..., 2] = np.clip(positions[..., 2], 50., 150.)
    exact(positions, a["after_positions"])
    sinr = a["after_sinr"][..., 0]
    best = np.argmax(sinr, axis=-1)
    expected = (np.arange(3) == best[..., None]) & (np.max(sinr, axis=-1)[..., None] >= 0.)
    exact(expected, a["after_connections"][..., 0])
    coverage = expected.sum(axis=-1)
    quality = (np.clip(sinr/30., 0., 1.) * expected).sum(axis=-1) / np.maximum(coverage, 1)
    energy = (positions[..., 2].mean(axis=-1)-50.)/100. * .1
    reward = .7*coverage + .3*quality - energy
    close(np.stack((coverage, quality, energy, reward), axis=-1), a["reward_components"])
    close(reward, a["team_reward"])
    close(reward/3., a["adapter_reward"])


def labels(a):
    radial = a["pre_positions"][..., :2] - np.array([500., 500.])
    radii = np.linalg.norm(radial, axis=-1)
    assert np.all(radii > 1e-12)  # No central tie in these saved actual rows.
    radial = radial / radii[..., None]
    dot = (radial*a["issued_actions"][..., :2]).sum(axis=-1)
    bits = (dot < 0).astype(np.int8)
    assert np.all(np.abs(np.abs(dot)-1.) < 1e-6)
    exact(bits[:, 0], a["focal_bit"])
    exact(bits[:, 1:], a["teammate_bits"])
    exact(2*bits[:, 1] + bits[:, 2], a["joint_row"])
    exact(a["issued_actions"][..., 2], np.zeros_like(a["issued_actions"][..., 2]))


def episode(a, rows):
    exact(a["tick"][rows], np.arange(64))
    for before, after in (("pre_positions", "after_positions"),
                          ("pre_observations", "after_observations"),
                          ("pre_connections", "after_connections"),
                          ("pre_sinr", "after_sinr")):
        exact(a[before][rows[1:]], a[after][rows[:-1]])
    done = np.arange(64) == 63
    exact(a["terminated"][rows], done)
    exact(a["terminal_agents"][rows], np.repeat(done[:, None], 3, axis=1))
    assert not a["truncated"][rows].any() and not a["truncated_agents"][rows].any()
    return math.fsum(a["adapter_reward"][rows])


summary = read(ROOT/"summary.json")
assert summary["status"] == "COMPLETE"
assert summary["launch_sha"] == SOURCE
assert summary["started_fits"] == summary["completed_fits"] == 3
assert summary["seeds"] == [95401, 95402, 95403]
assert read(ROOT/"process-exit.json")["exit_code"] == 0
digests = read(ROOT/"artifacts.json")
for rel, digest in digests.items():
    assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() == digest
manifest = read(ROOT/"source-manifest.json")
for record in manifest["files"].values():
    frozen = subprocess.check_output(["git", "show", SOURCE+":"+record["path"]], cwd=REPO)
    assert hashlib.sha256(frozen).hexdigest() == record["sha256"]

blocks = []
for seed in summary["seeds"]:
    folder = ROOT/f"seed_{seed}"
    for rel, digest in read(folder/"artifacts.json").items():
        assert digests[f"seed_{seed}/"+rel] == digest
    t, e, s = [load(folder/(name+".npz")) for name in ("training", "evaluation", "state")]
    b = read(folder/"summary.json")
    assert b["launch_sha"] == SOURCE
    exact(t["version"], np.repeat([0, 1], 64))
    exact(t["tick"], np.tile(np.arange(64), 2))
    assert len(e["tick"]) == 1024
    for a in (t, e):
        physical(a)
        labels(a)
    counts = np.zeros((2, 4), dtype=np.int64)
    exact(counts, s["initial_counts"])
    close(s["initial_probabilities"], np.full((2, 4), .25))
    snapshots = {}
    for i in range(128):
        version, row = int(t["version"][i]), int(t["joint_row"][i])
        exact(counts, t["counts_before"][i])
        p = (counts[version]+.5)/(counts[version].sum()+2.)
        close(p, t["probabilities_before"][i])
        close(project(p), t["projected_probabilities_before"][i])
        close(-math.log(p[row]), t["joint_log_loss"][i])
        close(-math.log(project(p)[row]), t["projected_log_loss"][i])
        assert row == np.searchsorted(np.cumsum(TRUE[version]), t["external_uniform"][i], side="right")
        assert t["focal_bit"][i] == int(t["focal_uniform"][i] >= .5)
        exact(t["rng_address"][i], [seed, 0, version, 0, i % 64])
        counts[version, row] += 1
        exact(counts, t["counts_after"][i])
        if version == 1 and (i-63) in (16, 64):
            snapshots[i-63] = counts.copy()
    exact(counts, s["final_counts"])
    exact(counts.sum(axis=1), s["final_updates"])
    close((counts+.5)/(counts.sum(axis=1)[:, None]+2.), s["final_probabilities"])
    for version in (0, 1):
        episode(t, np.flatnonzero(t["version"] == version))
    exact(t["terminal_id"], np.where(t["tick"] == 63, t["version"], -1))

    n = len(e["tick"])
    selected = (np.arange(n), e["focal_bit"], e["joint_row"])
    for field in ("adapter_reward", "team_reward", "after_positions", "after_observations",
                  "after_connections", "after_sinr", "reward_components", "terminated", "truncated",
                  "terminal_agents", "truncated_agents", "issued_actions"):
        exact(e["response_"+field][selected], e[field])
    source_digest = np.broadcast_to(e["response_source_state_digest"][:, None, None, :], (n, 2, 4, 32))
    exact(source_digest, e["response_clone_pre_digest"])
    assert e["response_source_state_unchanged"].all()
    table_physical = {key: value for key, value in
                      ((field, e["response_"+field]) for field in
                       ("issued_actions", "after_positions", "after_connections", "after_sinr",
                        "reward_components", "team_reward", "adapter_reward"))}
    table_physical["pre_positions"] = e["pre_positions"][:, None, None, :, :]
    physical(table_physical)
    table = e["response_adapter_reward"]
    jq = np.stack([table[i] @ e["joint_probabilities"][i] for i in range(n)])
    mq = np.stack([table[i] @ e["projected_probabilities"][i] for i in range(n)])
    tq = (table*TRUE[1]).sum(axis=-1)
    close(jq, e["joint_values"])
    close(mq, e["projected_values"])
    close(tq, e["true_values_after_choice"])
    # Independent arithmetic readback with the native table's matmul order for ties.
    choices_j = (jq[:, 1] > jq[:, 0]).astype(int)
    choices_m = (mq[:, 1] > mq[:, 0]).astype(int)
    exact(choices_j, e["joint_choice"])
    exact(choices_m, e["projected_choice"])
    exact(np.where(e["view"] == 0, choices_j, choices_m), e["focal_bit"])
    selected_true = tq[np.arange(n), e["focal_bit"]]
    close(selected_true, e["true_chosen_value_after_choice"])
    close(tq.max(axis=1)-selected_true, e["true_one_step_regret_after_choice"])
    jr = tq.max(axis=1)-tq[np.arange(n), choices_j]
    mr = tq.max(axis=1)-tq[np.arange(n), choices_m]
    exact(e["joint_row"], np.searchsorted(np.cumsum(TRUE[1]), e["external_uniform"], side="right"))
    exact(e["terminal_id"], np.where(e["tick"] == 63, e["episode"], -1))
    reductions, snapshots_compare = {}, {}
    for cp_index, cp in enumerate((16, 64)):
        subset = e["snapshot_step"] == cp
        count = snapshots[cp]
        exact(count, s["snapshot_counts"][cp_index])
        exact(count.sum(axis=1), s["snapshot_updates"][cp_index])
        probs = (count+.5)/(count.sum(axis=1)[:, None]+2.)
        close(probs, s["snapshot_probabilities"][cp_index])
        exact(e["frozen_counts"][subset], np.broadcast_to(count, (512, 2, 4)))
        close(e["joint_probabilities"][subset], np.broadcast_to(probs[1], (512, 4)))
        close(e["projected_probabilities"][subset], np.broadcast_to(project(probs[1]), (512, 4)))
        diagnostics, returns, episode_pairs = {}, {}, []
        for view in (0, 1):
            selected_rows = subset & (e["view"] == view)
            diagnostics[str(view)] = {
                "visited_ticks": int(selected_rows.sum()),
                "choice_disagreement_ticks": int(np.count_nonzero((choices_j != choices_m) & selected_rows)),
                "J_true_one_step_regret_mean_on_these_states": float(jr[selected_rows].mean()),
                "M_true_one_step_regret_mean_on_these_states": float(mr[selected_rows].mean()),
                "J_better_ticks": int(np.count_nonzero((mr-jr > 1e-12) & selected_rows)),
                "J_worse_ticks": int(np.count_nonzero((jr-mr > 1e-12) & selected_rows)),
            }
            returns[view] = []
            for ep in range(4):
                rows = np.flatnonzero(selected_rows & (e["episode"] == ep))
                ret = episode(e, rows)
                returns[view].append(ret)
                for key, field in (("cumulative_adapter_reward", "adapter_reward"),
                                   ("cumulative_team_reward", "team_reward")):
                    saved = next(x for x in b["episode_returns"] if x["snapshot_step"] == cp
                                 and x["view"] == ("J_emp", "M_proj")[view] and x["episode"] == ep)
                    close(math.fsum(e[field][rows]), saved[key])
                exact(e["rng_address"][rows], np.array([[seed, 1, 2, ep, tick] for tick in range(64)]))
        for ep in range(4):
            j = np.flatnonzero(subset & (e["view"] == 0) & (e["episode"] == ep))
            m = np.flatnonzero(subset & (e["view"] == 1) & (e["episode"] == ep))
            for field in ("rng_address", "external_uniform", "joint_row", "teammate_bits"):
                exact(e[field][j], e[field][m])
            exact(e["pre_positions"][j[0]], e["pre_positions"][m[0]])
            # Teammate closed-loop dynamics depend only on their positions and private bit.
            exact(e["after_positions"][j, 1:], e["after_positions"][m, 1:])
            disagree = np.flatnonzero(e["focal_bit"][j] != e["focal_bit"][m])
            served_j = e["after_connections"][j].sum(axis=(1, 2))
            served_m = e["after_connections"][m].sum(axis=(1, 2))
            pair = {
                "episode": ep, "J_minus_M_return": returns[0][ep]-returns[1][ep],
                "first_focal_bit_divergence_tick": int(disagree[0]) if len(disagree) else None,
                "focal_bit_differences_at_paired_ticks": len(disagree),
                "J_served_ticks": int(served_j.sum()), "M_served_ticks": int(served_m.sum()),
                "J_serving_agent_counts": e["after_connections"][j, :, 0].sum(axis=0).tolist(),
                "M_serving_agent_counts": e["after_connections"][m, :, 0].sum(axis=0).tolist(),
                "J_minus_M_by_16tick_quarters": [math.fsum(e["adapter_reward"][j[k:k+16]]-
                                                          e["adapter_reward"][m[k:k+16]]) for k in range(0, 64, 16)],
                "coverage_return_difference": float((served_j.sum()-served_m.sum())*.7/3.),
                "quality_return_difference": float(.1*math.fsum(e["reward_components"][j, 1]-e["reward_components"][m, 1])),
                "conditional_immediate_value_difference_along_own_recorded_paths": math.fsum(selected_true[j]-selected_true[m]),
                "realization_residual_difference": math.fsum(e["adapter_reward"][j]-selected_true[j])-
                                                    math.fsum(e["adapter_reward"][m]-selected_true[m]),
                "J_focal_inward_commands": int(e["focal_bit"][j].sum()),
                "M_focal_inward_commands": int(e["focal_bit"][m].sum()),
                "J_final_focal_radius": float(np.linalg.norm(e["after_positions"][j[-1], 0, :2]-[500., 500.])),
                "M_final_focal_radius": float(np.linalg.norm(e["after_positions"][m[-1], 0, :2]-[500., 500.])),
            }
            close(pair["coverage_return_difference"]+pair["quality_return_difference"], pair["J_minus_M_return"])
            episode_pairs.append(pair)
        paired = [x["J_minus_M_return"] for x in episode_pairs]
        saved = b["reductions"]["by_snapshot"][str(cp)]
        close(returns[0], saved["J_emp_cumulative_adapter_rewards"])
        close(returns[1], saved["M_proj_cumulative_adapter_rewards"])
        close(paired, saved["paired_J_minus_M_adapter_returns"])
        close(math.fsum(paired)/4, saved["mean_J_minus_M_adapter_return"])
        reductions[str(cp)] = {"paired_episode_returns": paired, "mean": math.fsum(paired)/4,
                               "same_state_diagnostics_by_occupancy_view": diagnostics, "episodes": episode_pairs}
    for view in (0, 1):
        first = np.flatnonzero((e["snapshot_step"] == 16) & (e["view"] == view))
        last = np.flatnonzero((e["snapshot_step"] == 64) & (e["view"] == view))
        for field in ("rng_address", "external_uniform", "joint_row"):
            exact(e[field][first], e[field][last])
        snapshots_compare[str(view)] = {
            "focal_bit_differences_at_paired_ticks": int(np.count_nonzero(e["focal_bit"][first] != e["focal_bit"][last])),
            "different_reward_ticks": int(np.count_nonzero(e["adapter_reward"][first] != e["adapter_reward"][last])),
        }
    blocks.append({"seed": seed, "by_snapshot": reductions, "16_versus_64_actual_trace": snapshots_compare,
                   "target_prequential_joint_log_loss": float(t["joint_log_loss"][64:].mean()),
                   "target_prequential_projected_log_loss": float(t["projected_log_loss"][64:].mean())})

primaries = [b["by_snapshot"]["64"]["mean"] for b in blocks]
close(primaries, summary["reduction"]["paired_seed_values"])
close(math.fsum(primaries)/3., summary["reduction"]["three_block_mean"])
result = {
    "status": "PASS", "scientific_source": SOURCE,
    "science_digests_checked": len(digests), "source_files_at_frozen_commit_checked": len(manifest["files"]),
    "training_rows_checked": 384, "evaluation_rows_checked": 3072, "saved_planner_branches_checked": 24576,
    "new_fits": 0, "new_native_step_calls": 0, "new_probability_or_network_queries": 0,
    "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "limits": "Arithmetic readback of stored evidence, not independent channel or observation reconstruction; same-state regret diagnostics do not estimate continuation values or fresh replication.",
    "primary_seed_values": primaries, "primary_mean": math.fsum(primaries)/3., "blocks": blocks,
}
(ROOT/"readback.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+"\n")
print(json.dumps({k: v for k, v in result.items() if k != "blocks"}, indent=2))
