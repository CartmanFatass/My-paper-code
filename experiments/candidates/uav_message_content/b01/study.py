"""One fixed C/H/L native batch and readable paired reductions."""

import hashlib
import json
import math
import os
from pathlib import Path
import resource
import statistics
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from .learner import collect_episode, optimizer_for, update
from .model import build_arm, exposure, snapshot

MASTER, HORIZON, TRAIN, EVAL = 19431, 256, 512, 32
ARMS = ("C", "H", "L")


def write_json(path, value):
    target = Path(path)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, target)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tensor_hash(tensor):
    return hashlib.sha256(tensor.numpy().tobytes()).hexdigest()


def new_counts():
    keys = ("constructors", "explicit_resets", "fit_started", "train_episodes",
            "initial_eval_episodes", "final_eval_episodes", "train_team_steps",
            "initial_eval_team_steps", "final_eval_team_steps", "team_steps",
            "native_step_calls", "motion_samples", "content_samples",
            "content_credit_rows", "broadcasts", "attempts", "delivered_packets",
            "censored_packets", "rollouts", "optimizer_steps", "replayed_actor_rows",
            "evaluation_optimizer_steps")
    counts = dict.fromkeys(keys, 0)
    for phase in ("train", "initial_eval", "final_eval"):
        for event in ("motion_samples", "content_samples", "content_credit_rows",
                      "broadcasts", "delivered_packets", "censored_packets"):
            counts[f"{phase}_{event}"] = 0
    return counts


def run_arm(master, arm, out, *, factory=make_real, horizon=HORIZON, train=TRAIN,
            evaluation=EVAL, check=lambda: None, launch_sha=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    counts = new_counts()
    rows = []
    summary = dict(object="UAV-MESSAGE-CONTENT-B01", arm=arm, master=master,
                   launch_sha=launch_sha,
                   status="INCOMPLETE", counts=counts, rows=rows, limits=[],
                   configuration=dict(horizon=horizon, train=train, initial_eval=evaluation,
                                      final_eval=evaluation, chunk=32, epochs=4,
                                      dtype="float32", device="cpu", torch_threads=1,
                                      content_budget=7, RR_period=5, fee=.001),
                   scientific_invocation=factory is make_real, started_wall=time.time())
    actor = critic = initial = None
    base = 100000 * master
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file, \
         (out / "updates.jsonl").open("x", encoding="utf-8") as update_file:
        def emit(row):
            rows.append(row)
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            write_json(out / "summary.json", summary)

        try:
            check()
            actor, critic = build_arm(master, arm)
            initial = snapshot(actor, critic)
            summary["initial_tensor_sha256"] = {name: tensor_hash(value) for name, value in initial.items()}
            initial_file = out / "initial.pt"
            torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(),
                            arm=arm, master=master, input_size=171, critic_size=451), initial_file)
            summary["initial_checkpoint"] = dict(path=str(initial_file), sha256=sha256(initial_file))
            write_json(out / "summary.json", summary)
            env = factory(base + 1000)
            counts["constructors"] += 1
            for phase in ("initial_eval", "train", "final_eval"):
                if phase == "train":
                    counts["fit_started"] = 1
                    motion_rng, content_rng = generator(base + 21), generator(base + 22)
                    for rollout in range(train // 2):
                        episodes = []
                        for e in (2 * rollout, 2 * rollout + 1):
                            metadata = dict(arm=arm, master=master, phase=phase,
                                            episode=e, motion_seed=base + 21,
                                            content_seed=base + 22)
                            episodes.append(collect_episode(
                                env, actor, critic, arm, horizon, base + 1000 + e,
                                base + 6000 + e, motion_rng, content_rng,
                                metadata, counts, emit, check))
                        records = update(actor, critic, optimizer, episodes, counts, check)
                        counts["rollouts"] += 1
                        update_file.write(json.dumps(dict(rollout=rollout, epochs=records), allow_nan=False) + "\n")
                        update_file.flush()
                        write_json(out / "summary.json", summary)
                    summary["exposure"] = exposure(initial, actor, critic)
                    final_file = out / "final.pt"
                    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(),
                                    arm=arm, master=master, input_size=171, critic_size=451), final_file)
                    summary["final_checkpoint"] = dict(path=str(final_file), sha256=sha256(final_file))
                    summary["final_tensor_sha256"] = {name: tensor_hash(value) for name, value in snapshot(actor, critic).items()}
                    write_json(out / "summary.json", summary)
                    continue
                for e in range(evaluation):
                    metadata = dict(arm=arm, master=master, phase=phase,
                                    episode=e, motion_seed=base + 3000 + e,
                                    content_seed=base + 4000 + e)
                    raw_path = out / "raw" / f"{phase}_{e:02d}.npz"
                    collect_episode(env, actor, critic, arm, horizon,
                                    base + 2000 + e, base + 7000 + e,
                                    generator(base + 3000 + e), generator(base + 4000 + e),
                                    metadata, counts, emit, check, raw_path=raw_path)
                if phase == "initial_eval":
                    optimizer = optimizer_for(actor, critic)
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
            if initial is not None and actor is not None:
                summary["exposure"] = exposure(initial, actor, critic)
        finally:
            summary["finished_wall"] = time.time()
            write_json(out / "summary.json", summary)
    return summary


def panel(summary, phase):
    return [row for row in summary["rows"] if row["phase"] == phase]


def paired_values(first, second, metric):
    if any(a[metric] is None or b[metric] is None for a, b in zip(first, second)):
        return None
    differences = [a[metric] - b[metric] for a, b in zip(first, second)]
    if not all(math.isfinite(value) for value in differences):
        raise ValueError(f"nonfinite paired {metric}")
    return dict(differences=differences, mean=statistics.mean(differences),
                positive=sum(x > 0 for x in differences),
                adverse=sum(x < 0 for x in differences), worst_loss=min(differences))


def reduction(summaries, expected=EVAL, horizon=HORIZON, train=TRAIN):
    indexed = {item["arm"]: item for item in summaries}
    result = dict(complete=False, reading="INCOMPLETE", comparisons={}, own_learning={})
    if set(indexed) != set(ARMS):
        return result
    for arm in ARMS:
        item = indexed[arm]
        counts = item["counts"]
        if item["status"] != "COMPLETE" or counts["fit_started"] != 1:
            return result
        required = dict(train_episodes=train, initial_eval_episodes=expected,
                        final_eval_episodes=expected, train_team_steps=train * horizon,
                        initial_eval_team_steps=expected * horizon,
                        final_eval_team_steps=expected * horizon,
                        team_steps=(train + 2 * expected) * horizon,
                        motion_samples=(train + 2 * expected) * horizon * 5,
                        optimizer_steps=(train // 2) * 4, rollouts=train // 2,
                        replayed_actor_rows=train * horizon * 5 * 4,
                        evaluation_optimizer_steps=0,
                        broadcasts=(train + 2 * expected) * horizon,
                        attempts=(train + 2 * expected) * horizon)
        if any(counts.get(key) != value for key, value in required.items()):
            return result
        if counts["content_samples"] != ((train + 2 * expected) * horizon if arm == "L" else 0):
            return result
        if any([row["episode"] for row in panel(item, phase)] != list(range(length))
               for phase, length in (("train", train), ("initial_eval", expected),
                                     ("final_eval", expected))):
            return result
        if any(row["steps"] != horizon or row["attempts"] != horizon or
               row["accepted_packets"] != horizon or row["collided_attempts"] != 0 or
               not math.isclose(row["charge_per_tick"], .001, abs_tol=1e-10)
               for row in item["rows"]):
            return result
        if sum(row["delivered_packets"] for row in item["rows"]) != counts["delivered_packets"] or \
           sum(row["pending_at_end"] for row in item["rows"]) != counts["censored_packets"]:
            return result
        if item.get("scientific_invocation") and any(
            row["Q"] is None for phase in ("initial_eval", "final_eval")
            for row in panel(item, phase)):
            return result
    for phase in ("train", "initial_eval", "final_eval"):
        reference = panel(indexed["C"], phase)
        for arm in ("H", "L"):
            other = panel(indexed[arm], phase)
            if any((a["reset_seed"], a["channel_seed"], a["initial_scene_sha256"],
                    a["channel_sequence_sha256"]) !=
                   (b["reset_seed"], b["channel_seed"], b["initial_scene_sha256"],
                    b["channel_sequence_sha256"]) for a, b in zip(reference, other)):
                return result
    for arm in ARMS:
        initial_worlds = panel(indexed[arm], "initial_eval")
        final_worlds = panel(indexed[arm], "final_eval")
        if any((a["initial_scene_sha256"], a["channel_sequence_sha256"]) !=
               (b["initial_scene_sha256"], b["channel_sequence_sha256"])
               for a, b in zip(initial_worlds, final_worlds)):
            return result
    for arm in ("H", "L"):
        if indexed[arm]["initial_tensor_sha256"]["motion_receiver"] != indexed["C"]["initial_tensor_sha256"]["motion_receiver"] or \
           indexed[arm]["initial_tensor_sha256"]["critic"] != indexed["C"]["initial_tensor_sha256"]["critic"]:
            return result
    result["complete"] = True
    result["reading"] = "COMPLETE_NO_DIRECTIONAL_VERDICT"
    metrics = ("J_net", "J_physical", "served_users_per_tick", "Q", "charge_per_tick")
    try:
        for arm in ARMS:
            result["own_learning"][arm] = {
                metric: paired_values(panel(indexed[arm], "final_eval"),
                                      panel(indexed[arm], "initial_eval"), metric)
                for metric in metrics}
        for left, right in (("L", "H"), ("L", "C"), ("H", "C")):
            result["comparisons"][f"{left}-{right}"] = {
                phase: {metric: paired_values(panel(indexed[left], phase),
                                              panel(indexed[right], phase), metric)
                        for metric in metrics}
                for phase in ("initial_eval", "final_eval")}
    except ValueError:
        result.update(complete=False, reading="INCOMPLETE")
    return result


def run_batch(out, launch_sha, seed=MASTER, *, factory=make_real,
              horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    if seed != MASTER or train % 2 or horizon % 32:
        raise ValueError("invalid fixed study contract")
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "summary.json").exists() or any((output / arm).exists() for arm in ARMS):
        raise FileExistsError("scientific output already exists")
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    summaries = []
    batch = dict(object="UAV-MESSAGE-CONTENT-B01", launch_sha=launch_sha,
                 source_sha=launch_sha, master=seed, status="INCOMPLETE", arms=summaries,
                 started_wall=time.time(), limits=[],
                 expected=dict(arms=list(ARMS), fits=3, train_episodes=1536,
                               evaluation_episodes=192, team_steps=442368, optimizer_steps=3072))
    write_json(output / "summary.json", batch)
    for arm in ARMS:
        result = run_arm(seed, arm, output / arm, factory=factory, horizon=horizon,
                         train=train, evaluation=evaluation, launch_sha=launch_sha)
        summaries.append(result)
        batch["actual"] = {key: sum(item["counts"][key] for item in summaries)
                           for key in new_counts()}
        write_json(output / "summary.json", batch)
        if result["status"] != "COMPLETE":
            batch["limits"].append(f"{arm} incomplete")
            break
    batch["reduction"] = reduction(summaries, expected=evaluation, horizon=horizon, train=train)
    batch["status"] = "COMPLETE" if batch["reduction"]["complete"] else "INCOMPLETE"
    usage_end = resource.getrusage(resource.RUSAGE_SELF)
    batch["resources"] = dict(
        process_cpu_seconds_during_batch=(usage_end.ru_utime + usage_end.ru_stime
                                          - usage_start.ru_utime - usage_start.ru_stime),
        process_lifetime_peak_rss_kib_linux=usage_end.ru_maxrss,
        cpu_scope="RUSAGE_SELF user+system time delta over run_batch",
        rss_scope="RUSAGE_SELF process-lifetime high-water mark; Linux ru_maxrss is KiB")
    batch["finished_wall"] = time.time()
    write_json(output / "summary.json", batch)
    return batch
