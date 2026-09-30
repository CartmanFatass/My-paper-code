"""Pure saved-output verification and fixed complete-use/learning contrasts."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t as student_t
import torch

from experiments.candidates.uav_local_history.b01.controller import COMMANDS, WAYPOINTS
from experiments.candidates.uav_local_history.b01.read_b01 import reconstruct_native
from .policy import sample_actions, templates
from .protocol import (ARMS, EVAL_WORLDS, HORIZON, MASTERS, OBJECT, TRAIN_EPISODES,
                       clock, elapsed, eval_world, expected_counts, identity,
                       train_world, write_json)

ROOT = Path(__file__).resolve().parents[4]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify_file(base, record):
    actual = identity(Path(base) / record["path"])
    require(actual["bytes"] == record["bytes"] and actual["sha256"] == record["sha256"],
            "artifact identity mismatch: " + record["path"])
    return Path(base) / record["path"]


def interval(values):
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    half = float(student_t.ppf(.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return dict(n=len(values), mean=mean, ci95=[mean - half, mean + half],
                min=float(values.min()), max=float(values.max()),
                positive=int((values > 0).sum()), negative=int((values < 0).sum()),
                zero=int((values == 0).sum()))


def verify_c_state(data):
    """Replay only waypoint/tie rules, using already paid saved candidate scores."""
    obs = data["observations"]
    own = obs[:, :, :3].astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
    nav = np.argmin(((own[0, :, None, :2] - WAYPOINTS[None]) ** 2).sum(axis=-1), axis=-1)
    for k, tick in enumerate(range(0, HORIZON, 4)):
        scores, service = data["macro_candidate_scores"][k], data["macro_candidate_service"][k]
        fallback = np.all(service == 0, axis=-1)
        require(np.array_equal(fallback, data["c_fallback"][tick]), "C fallback rule")
        selected = scores.argmax(axis=-1)
        for i in range(5):
            if fallback[i]:
                if np.linalg.norm(WAYPOINTS[nav[i]] - own[tick, i, :2]) <= 60:
                    nav[i] = (nav[i] + 1) % 10
                endpoint = np.clip(own[tick, i] + 120 * COMMANDS,
                                   [0, 0, 50], [1000, 1000, 150])
                target = np.r_[WAYPOINTS[nav[i]], 50.0]
                selected[i] = np.argmin(((endpoint - target) ** 2).sum(axis=-1))
        require(np.array_equal(selected, data["macro_c_index"][k]), "C selected label/tie rule")
        require(np.array_equal(np.broadcast_to(nav, (4, 5)), data["c_nav"][tick:tick + 4]),
                "C private waypoint state/hold rule")


def verify_episode(data, row, actor=None):
    shapes = dict(observations=(256, 5, 104), commands=(256, 5, 3),
                  c_commands=(256, 5, 3), c_nav=(256, 5), c_fallback=(256, 5),
                  c_selected_index=(256, 5), c_n_current=(256, 5), c_n_visible_peers=(256, 5),
                  post_positions=(256, 5, 3), displacements=(256, 5, 3), reward=(256,),
                  served=(256,), sinr_quality=(256,), true_users=(50, 2),
                  initial_positions=(5, 3), terminal_observation=(5, 104),
                  macro_context=(64, 5, 120), macro_c_index=(64, 5), macro_action=(64, 5),
                  macro_log_prob=(64, 5), macro_logits=(64, 5, 27), macro_entropy=(64, 5),
                  macro_values=(64,), macro_critic=(64, 136), macro_native_state=(64, 116),
                  macro_seeds=(64, 5), macro_candidate_scores=(64, 5, 27),
                  macro_candidate_service=(64, 5, 27), macro_reward=(64,))
    require(set(data) == set(shapes), "raw field contract")
    for key, shape in shapes.items():
        require(data[key].shape == shape and np.isfinite(data[key]).all(), "shape/finite: " + key)
    obs, cmd, context = data["observations"], data["commands"], data["macro_context"]
    require(obs.dtype == cmd.dtype == context.dtype == np.float32, "actor storage dtype")
    before = np.concatenate((data["initial_positions"][None], data["post_positions"][:-1]))
    post = np.clip(before + 30 * cmd, [0, 0, 50], [1000, 1000, 150])
    require(np.array_equal(post, data["post_positions"]), "command to physical displacement")
    require(np.array_equal(data["displacements"], post - before), "saved displacement")
    require(np.array_equal(cmd, np.repeat(COMMANDS[data["macro_action"]], 4, axis=0)), "learned hold")
    require(np.array_equal(data["c_commands"], np.repeat(COMMANDS[data["macro_c_index"]], 4, axis=0)), "nominal C hold")
    require(np.array_equal(data["c_selected_index"], np.repeat(data["macro_c_index"], 4, axis=0)), "C label hold")
    own = obs[:, :, :3].astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
    terminal = data["terminal_observation"][:, :3].astype(np.float64) * [1000, 1000, 100] + [0, 0, 50]
    require(np.max(abs(own - before)) < 1e-4 and np.max(abs(terminal - post[-1])) < 1e-4, "actual visited local position")
    previous = np.concatenate((np.zeros((1, 5, 3), np.float32), cmd[3:-1:4]), axis=0)
    packed = np.concatenate((obs[::4], data["c_commands"][::4], previous,
                             np.eye(10, dtype=np.float32)[data["c_nav"][::4]]), axis=-1)
    require(np.array_equal(context, packed), "exact local actor feature packing")
    state = data["macro_native_state"].copy()
    state_positions = state[:, :15].reshape(64, 5, 3)
    require(np.max(abs(state_positions - before[::4])) < 1e-4, "central critic state position")
    require(np.max(abs(state[:, 15:115].reshape(64, 50, 2) - data["true_users"])) < 1e-4,
            "central critic state world")
    state_positions[:, :, :2] /= 1000
    state_positions[:, :, 2] = (state_positions[:, :, 2] - 50) / 100
    state[:, 15:115] /= 1000
    commitment = np.concatenate((previous, np.zeros((64, 5, 1), np.float32)), axis=-1)
    require(np.array_equal(data["macro_critic"], np.concatenate((state, commitment.reshape(64, 20)), axis=-1)),
            "central critic input packing")
    valid_users = obs[:, :, 3:63].reshape(256, 5, 20, 3)[:, :, :, 2] > 0
    valid_peers = obs[:, :, 63:103].reshape(256, 5, 10, 4)[:, :, :, 3] > 0
    require(np.array_equal(valid_users.sum(-1), data["c_n_current"]), "C current user visibility")
    require(np.array_equal(valid_peers.sum(-1), data["c_n_visible_peers"]), "C peer visibility")
    n, p = valid_users[::4].sum(-1), valid_peers[::4].sum(-1)
    c_expected = dict(c_ingests=1280, c_decisions=320, c_trajectories=8640,
                      c_model_ticks=34560, c_objective_reductions=34560,
                      c_candidate_link_evaluations=int(108 * n.sum()),
                      c_setup_link_evaluations=int(((1 + p) * n).sum()),
                      c_fallback_decisions=int(data["c_fallback"][::4].sum()),
                      c_shadow_decisions=0, c_shadow_objective_reductions=0,
                      c_grid_power_evaluations=0, c_cache_matches=0,
                      c_cache_inserts=0, c_cache_evicts=0)
    c_expected["c_link_evaluations"] = c_expected["c_candidate_link_evaluations"] + c_expected["c_setup_link_evaluations"]
    for key, value in c_expected.items():
        require(row["counters"][key] == value, "actual C work from local visibility: " + key)
    verify_c_state(data)
    reward, served, quality = reconstruct_native(post, data["true_users"])
    require(np.max(abs(reward - data["reward"])) < 1e-12 and
            np.max(abs(quality - data["sinr_quality"])) < 1e-12 and
            np.array_equal(served, data["served"]), "independent all-on native objective")
    require(np.array_equal(data["macro_reward"], data["reward"].reshape(64, 4).sum(axis=1)), "four-tick reward sum")
    greedy = row["arm"] in ("C", "Lg")
    replay_rows = 0
    max_logit_error = 0.0
    for k in range(64):
        logits = torch.from_numpy(data["macro_logits"][k])
        if actor is not None:
            with torch.no_grad():
                replayed = actor(torch.from_numpy(context[k]), torch.from_numpy(data["macro_c_index"][k]))
            error = float((logits - replayed).abs().max())
            require(error < 2e-6, "endpoint actor input/parameter binding")
            max_logit_error = max(max_logit_error, error)
            replay_rows += 5
        action, logp, entropy, seeds = sample_actions(logits, domain="train" if row["training"] else "eval",
            master=row["master"], world_seed=row["world_seed"], macro_index=k, greedy=greedy)
        require(np.array_equal(action.numpy(), data["macro_action"][k]), "addressed action sample/decoder")
        require(np.array_equal(logp.numpy(), data["macro_log_prob"][k]), "actual category density")
        require(np.array_equal(entropy.numpy(), data["macro_entropy"][k]), "actual entropy")
        require(np.array_equal(np.full(5, -1, np.int64) if seeds is None else seeds.numpy(),
                               data["macro_seeds"][k]), "RNG address witness")
    if row["arm"] in ("C", "I"):
        expected = np.zeros((64, 5, 27), np.float32)
        np.put_along_axis(expected, data["macro_c_index"][..., None], np.float32(np.log(234.0)), axis=-1)
        require(np.array_equal(expected, data["macro_logits"]), "initial prior/zero correction")
    if row["arm"] == "C":
        require(np.array_equal(cmd, data["c_commands"]), "exact greedy initial C identity")
    departure = np.any(cmd != data["c_commands"], axis=-1)
    ordinary_post = np.clip(before + 30 * data["c_commands"], [0, 0, 50], [1000, 1000, 150])
    applied = np.any(post != ordinary_post, axis=-1)
    numbers = dict(J=float(reward.mean()), mean_served=float(served.mean()), mean_quality=float(quality.mean()),
                   zero_service_ticks=int((served == 0).sum()),
                   mean_agent_path_m=float(np.linalg.norm(data["displacements"], axis=-1).sum(axis=0).mean()),
                   requested_departure_decisions=int(departure[::4].sum()),
                   applied_departure_agent_ticks=int(applied.sum()),
                   boundary_alias_agent_ticks=int((departure & ~applied).sum()),
                   mean_entropy=float(data["macro_entropy"].mean()),
                   fallback_agent_decisions=int(data["c_fallback"][::4].sum()))
    for key, val in numbers.items():
        require(abs(row[key] - val) < 1e-11, "row reduction: " + key)
    return dict(endpoint_actor_rows=replay_rows, max_logit_error=max_logit_error,
                max_reward_error=float(np.max(abs(reward - data["reward"]))),
                action_histogram=np.bincount(data["macro_action"].ravel(), minlength=27),
                c_histogram=np.bincount(data["macro_c_index"].ravel(), minlength=27),
                world_digest=hashlib.sha256(data["true_users"].tobytes() + data["initial_positions"].tobytes()).hexdigest())


def read(run):
    started = clock()
    run = Path(run).resolve()
    summary = json.loads((run / "summary.json").read_text())
    require(summary["object"] == OBJECT and summary["status"] == "COMPLETE" and not summary["limits"], "complete study required")
    for key, expected in expected_counts().items():
        require(summary["counts"][key] == expected, "complete count: " + key)
    for record in summary["artifacts"].values():
        verify_file(run, record)
    config = json.loads((run / "config.json").read_text())
    require(config["launch_sha"] == summary["launch_sha"], "source binding")
    for record in config["source_identities"]:
        verify_file(ROOT, record)
    models = {}
    for block, fit in enumerate(summary["fits"]):
        master = MASTERS[block]
        require((fit["block"], fit["master"], fit["status"], fit["trained_episodes"]) ==
                (block, master, "COMPLETE", TRAIN_EPISODES), "fit identity")
        for endpoint in ("initial", "final"):
            path = verify_file(run, fit[endpoint + "_checkpoint"])
            checkpoint = torch.load(path, map_location="cpu", weights_only=True)
            require((checkpoint["object"], checkpoint["endpoint"], checkpoint["master"], checkpoint["launch_sha"]) ==
                    (OBJECT, endpoint, master, summary["launch_sha"]), "checkpoint binding")
            actor, critic = templates(master)
            if endpoint == "initial":
                require(all(torch.equal(checkpoint["actor"][k], v) for k, v in actor.state_dict().items()), "actor initialization draws")
                require(all(torch.equal(checkpoint["critic"][k], v) for k, v in critic.state_dict().items()), "critic initialization draws")
            actor.load_state_dict(checkpoint["actor"], strict=True)
            for optimizer in (checkpoint["actor_optimizer"], checkpoint["critic_optimizer"]):
                states = optimizer["state"]
                require((not states) if endpoint == "initial" else all(float(s["step"]) == 1024 for s in states.values()),
                        "optimizer step binding")
            models[(master, endpoint)] = actor.eval()
    training = [json.loads(line) for line in (run / "training.jsonl").read_text().splitlines()]
    evaluation = [json.loads(line) for line in (run / "evaluation.jsonl").read_text().splitlines()]
    updates = [json.loads(line) for line in (run / "updates.jsonl").read_text().splitlines()]
    require(evaluation == summary["rows"], "summary/evaluation row identity")
    require(len(training) == 1536 and len(evaluation) == 384 and len(updates) == 3072, "log coverage")
    for j, row in enumerate(training):
        block, episode = divmod(j, 512)
        require((row["block"], row["master"], row["episode"], row["world_seed"], row["arm"], row["training"]) ==
                (block, MASTERS[block], episode, train_world(block, episode), "train", True), "training world schedule")
    expected_order = [(b, j, a) for b in range(3) for j in range(32)
                      for a in ARMS[(b + j) % 4:] + ARMS[:(b + j) % 4]]
    for row, (b, j, a) in zip(evaluation, expected_order):
        require((row["block"], row["master"], row["world"], row["world_seed"], row["arm"], row["training"]) ==
                (b, MASTERS[b], j, eval_world(b, j), a, False), "rotated paired evaluation schedule")
    for j, record in enumerate(updates):
        b, rem = divmod(j, 1024)
        rollout, epoch = divmod(rem, 4)
        require((record["block"], record["master"], record["rollout"], record["epoch"]) ==
                (b, MASTERS[b], rollout, epoch), "update order")
        require((record["actor_table_lr"], record["actor_mlp_lr"], record["critic_lr"]) == (.01, .0003, .0003), "optimizer groups")
        require(record["actor_clipped_grad_norm"] <= .500001 and record["critic_clipped_grad_norm"] <= .500001, "gradient clipping")
    checks = dict(raw_files=0, raw_bytes=0, reconstructed_native_steps=0, endpoint_actor_rows=0,
                  max_reward_error=0., max_logit_error=0.)
    histograms = defaultdict(lambda: dict(action=np.zeros(27, np.int64), c=np.zeros(27, np.int64)))
    world_bindings = defaultdict(set)
    counters = defaultdict(int)
    for row in training + evaluation:
        path = verify_file(run, row["raw"])
        with np.load(path, allow_pickle=False) as raw:
            data = {key: raw[key] for key in raw.files}
        endpoint = "initial" if row["arm"] in ("C", "I") else "final"
        actor = None if row["training"] else models[(row["master"], endpoint)]
        facts = verify_episode(data, row, actor)
        checks["raw_files"] += 1
        checks["raw_bytes"] += row["raw"]["bytes"]
        checks["reconstructed_native_steps"] += HORIZON
        checks["endpoint_actor_rows"] += facts["endpoint_actor_rows"]
        for key in ("max_reward_error", "max_logit_error"):
            checks[key] = max(checks[key], facts[key])
        name = f"{row['master']}/{row['arm']}"
        histograms[name]["action"] += facts["action_histogram"]
        histograms[name]["c"] += facts["c_histogram"]
        world_bindings[row["world_seed"]].add(facts["world_digest"])
        for key, value in row["counters"].items():
            counters[key] += value
    require(len(world_bindings) == 1632 and all(len(v) == 1 for v in world_bindings.values()), "distinct training/evaluation paired worlds")
    for key, value in counters.items():
        require(summary["counts"][key] == value, "summed C nested work: " + key)
    table = {(row["block"], row["world"], row["arm"]): row for row in evaluation}
    contrasts = (("Lg", "C"), ("Ls", "I"), ("I", "C"), ("Lg", "Ls"), ("Ls", "C"), ("Lg", "I"))
    metrics = ("J", "mean_served", "mean_quality", "mean_agent_path_m")
    paired, contrast_reading = [], {}
    for a, b in contrasts:
        name = a + "-" + b
        contrast_reading[name] = {}
        for metric in metrics:
            blocks = [[table[(block, j, a)][metric] - table[(block, j, b)][metric] for j in range(32)] for block in range(3)]
            contrast_reading[name][metric] = dict(per_block=[interval(values) for values in blocks],
                outer_three_blocks=interval([np.mean(values) for values in blocks]),
                pooled_world_signs=dict(positive=int((np.asarray(blocks) > 0).sum()),
                                       negative=int((np.asarray(blocks) < 0).sum()),
                                       zero=int((np.asarray(blocks) == 0).sum())))
    for b in range(3):
        for j in range(32):
            arms = {a: table[(b, j, a)] for a in ARMS}
            delta = {a + "-" + c: {m: arms[a][m] - arms[c][m] for m in metrics} for a, c in contrasts}
            require(abs(delta["Lg-C"]["J"] - delta["Ls-I"]["J"] - delta["I-C"]["J"] - delta["Lg-Ls"]["J"]) < 1e-14,
                    "complete-use decomposition identity")
            paired.append(dict(block=b, world_seed=eval_world(b, j), contrasts=delta))
    mean_fields = metrics + ("mean_entropy", "mean_c_probability")
    sum_fields = ("zero_service_ticks", "requested_departure_decisions", "applied_departure_agent_ticks",
                  "boundary_alias_agent_ticks", "fallback_agent_decisions")
    arm_reading = {}
    for b in range(3):
        for a in ARMS:
            selected = [table[(b, j, a)] for j in range(32)]
            arm_reading[f"{MASTERS[b]}/{a}"] = dict(
                {m: float(np.mean([row[m] for row in selected])) for m in mean_fields},
                **{m: sum(row[m] for row in selected) for m in sum_fields},
                episode_J=[row["J"] for row in selected],
                wall_seconds=sum(row["resources"]["wall_seconds"] for row in selected))
    learning = {}
    for b, master in enumerate(MASTERS):
        block = training[b * 512:(b + 1) * 512]
        learning[str(master)] = dict(first32={m: float(np.mean([r[m] for r in block[:32]])) for m in mean_fields},
                                    last32={m: float(np.mean([r[m] for r in block[-32:]])) for m in mean_fields},
                                    exposure=summary["fits"][b]["movement_from_fit_start"])
    return dict(object=OBJECT + "-READING", status="COMPLETE", launch_sha=summary["launch_sha"],
                source_summary=identity(run / "summary.json", run), artifact_checks=checks,
                arms=arm_reading, contrasts=contrast_reading, paired_worlds=paired, training=learning,
                category_histograms={k: {field: v.tolist() for field, v in values.items()} for k, values in histograms.items()},
                counts=summary["counts"], worker_resources=summary["resources"], reader_resources=elapsed(started),
                interval_scope="Per-block paired-world intervals condition on its fit; outer n=3 includes training and distinct fresh-world variation. World signs do not create96 independent training replicates.",
                limitations=["No K-only fit: table-versus-contextual contribution is unresolved.",
                             "Lg-C is primary; Ls-I is necessary same-decoder learning. No decoder selection.",
                             "Accounting identity is descriptive, not causal mediation.",
                             "Saved training logits/densities and update records verified; optimizers were not rerun."])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    result = read(args.run)
    write_json(args.run / "reading.json", result)
    print(json.dumps(dict(status=result["status"], checks=result["artifact_checks"], resources=result["reader_resources"])))


if __name__ == "__main__":
    main()
