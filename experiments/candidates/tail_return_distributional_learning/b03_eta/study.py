"""Fixed six-fit execution and descriptive reading for the S_eta successor."""
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import resource
import time
import traceback

import numpy as np
import torch

from experiments.candidates.tail_return_distributional_learning.trdl_b01 import learner as old
from experiments.candidates.tail_return_distributional_learning.trdl_b01 import study as old_study
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import exposure, snapshot
from . import learner
from .metrics import MeasuredEnv

MASTERS = (9621, 9622, 9623)
ORDER = tuple((master, arm) for master in MASTERS for arm in learner.ARMS)
TRAIN_EPISODES = old.TRAIN_EPISODES
EVAL_EPISODES = old.EVAL_EPISODES
EXPECTED_STEPS = (TRAIN_EPISODES + EVAL_EPISODES) * old.HORIZON


@contextmanager
def timed(timings, key):
    started = time.monotonic()
    try:
        yield
    finally:
        timings[key] += time.monotonic() - started


def write_json(path, payload):
    path = Path(path)
    path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def require_movement(exposure_row):
    if not isinstance(exposure_row, dict):
        raise ValueError("missing learner movement evidence")
    for group in ("common_actor", "critic", "total"):
        row = exposure_row.get(group)
        if (not isinstance(row, dict) or isinstance(row.get("parameters"), bool)
                or not isinstance(row.get("parameters"), int) or row["parameters"] <= 0):
            raise ValueError(f"missing {group} movement evidence")
        for field in ("initial_norm", "final_norm", "displacement", "relative_displacement"):
            value = row.get(field)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"invalid {group} {field} movement evidence")


def collect_measured(env, *args, **kwargs):
    emit = args[7]
    args = list(args)
    def measured_emit(row):
        row.update(env.episode_metrics())
        emit(row)
    args[7] = measured_emit
    return old.collect_episode(env, *args, **kwargs)


def frozen_diagnostics(batch, batch_number):
    def stats(values):
        values = values.detach().float()
        return dict(mean=float(values.mean()), std=float(values.std(unbiased=False)),
                    min=float(values.min()), max=float(values.max()))
    return dict(batch=batch_number, eta=float(batch["eta"]),
                W=stats(batch["scores"]), baseline=stats(batch["baseline"]),
                advantages=stats(batch["advantages"]),
                strictly_negative_W=int((batch["scores"] < 0).sum()))


def run_fit(master, arm, out, launch_sha):
    if (master, arm) not in ORDER:
        raise ValueError("unregistered b03_eta fit")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    counts = old_study.new_counts()
    timings = dict(initialization=0., training_collection=0., frozen_baselines=0.,
                   updates=0., checkpoint_publication=0., final_evaluation=0.)
    summary = dict(status="incomplete", arm=arm, seed=master, launch_sha=launch_sha,
                   counts=counts, timings_seconds=timings, horizon=old.HORIZON,
                   training_episodes=TRAIN_EPISODES, evaluation_episodes=EVAL_EPISODES,
                   batch_episodes=old.BATCH, epochs=old.EPOCHS, alpha=old.ALPHA,
                   critic_input=138 if arm == "S_eta" else 137,
                   critic_outputs=1 if arm == "S_eta" else 32,
                   device="cpu", dtype="float32", torch_threads=torch.get_num_threads(),
                   scientific_class="B/EXPLORE")
    env = actor = critic = initial = None
    final_rows = []
    summary["frozen_batches"] = []
    started = time.monotonic()

    def emit(handle, row):
        handle.write(json.dumps(dict(arm=arm, seed=master, **row), allow_nan=False) + "\n")
        handle.flush()

    try:
        with timed(timings, "initialization"):
            actor, critic = learner.models(master, arm)
            initial = snapshot(actor, critic)
            optimizer = old.optimizer_for(actor, critic)
            counts["constructor_calls"] += 1
            env = MeasuredEnv(make_real(100000 * master + 1000))
            counts["constructor_resets"] += 1
        train_rng = learner.action_generator(master, arm)
        with (out / "episodes.jsonl").open("w", encoding="utf-8") as episodes_file, (
                out / "updates.jsonl").open("w", encoding="utf-8") as updates_file:
            for batch_number in range(TRAIN_EPISODES // old.BATCH):
                rollouts = []
                with timed(timings, "training_collection"):
                    for offset in range(old.BATCH):
                        episode = batch_number * old.BATCH + offset
                        rollout, _ = collect_measured(
                            env, actor, 100000 * master + 1000 + episode, train_rng,
                            "train", episode, lambda: None, counts,
                            lambda row: emit(episodes_file, row))
                        rollouts.append(rollout)
                with timed(timings, "frozen_baselines"):
                    batch = learner.frozen_batch(critic, rollouts)
                    summary["frozen_batches"].append(frozen_diagnostics(batch, batch_number))
                with timed(timings, "updates"):
                    def emit_update(row):
                        row["clipping_active"] = row["grad_norm"] > .5
                        emit(updates_file, dict(batch=batch_number, **row))
                    learner.update(actor, critic, optimizer, batch, lambda: None, counts,
                                   emit_update)
                print(json.dumps(dict(event="batch_complete", seed=master, arm=arm,
                                      batch=batch_number, counts=counts)), flush=True)
            with timed(timings, "checkpoint_publication"):
                actor.eval()
                critic.eval()
                checkpoint = out / "checkpoint.pt"
                torch.save(dict(arm=arm, seed=master, launch_sha=launch_sha,
                                actor=actor.state_dict(), critic=critic.state_dict(),
                                optimizer_steps=counts["optimizer_steps"]), checkpoint)
                summary["checkpoint_sha256"] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
            with timed(timings, "final_evaluation"):
                for episode in range(EVAL_EPISODES):
                    _, row = collect_measured(
                        env, actor, 100000 * master + 2000 + episode,
                        learner.action_generator(master, arm, episode), "eval", episode,
                        lambda: None, counts, lambda result: emit(episodes_file, result))
                    final_rows.append(row)
                    if (episode + 1) % 16 == 0:
                        print(json.dumps(dict(event="eval_progress", seed=master,
                                              arm=arm, episodes=episode + 1)), flush=True)
        if (counts["train_episodes"] != TRAIN_EPISODES or counts["eval_episodes"] != EVAL_EPISODES
                or counts["optimizer_steps"] != 128 or counts["team_steps"] != EXPECTED_STEPS):
            raise ValueError("fit exposure incomplete")
        summary["endpoint"] = compact_endpoint(final_rows)
    except Exception as error:
        summary["failure"] = f"{type(error).__name__}: {error}"
        summary["traceback"] = traceback.format_exc()
        print(summary["failure"], flush=True)
    finally:
        summary["complete_final_worlds"] = len(final_rows)
        if initial is not None:
            try:
                if all(torch.isfinite(p).all() for module in (actor, critic) for p in module.parameters()):
                    summary["learner_exposure"] = exposure(initial, actor, critic)
                    require_movement(summary["learner_exposure"])
                else:
                    raise ValueError("nonfinite parameters")
            except Exception as error:
                summary["learner_exposure_error"] = str(error)
                summary.pop("learner_exposure", None)
        if "endpoint" in summary and "failure" not in summary:
            if "learner_exposure_error" in summary or "learner_exposure" not in summary:
                summary["failure"] = "required learner movement evidence unavailable"
            else:
                summary["status"] = "complete"
        if env is not None:
            try:
                env.close()
            except Exception as error:
                summary["close_error"] = str(error)
        summary["peak_rss_bytes"] = old_study.peak_rss_bytes()
        summary["resources_unmeasured"] = summary["peak_rss_bytes"] is None
        summary["resource_scope"] = "single runner process high-water through this fit"
        summary["wall_seconds"] = time.monotonic() - started
        write_json(out / "summary.json", summary)
    return summary


def compact_endpoint(rows):
    values = np.asarray([row["J"] for row in rows], dtype=np.float64)
    endpoint = old.endpoint(values)
    del endpoint["returns"]
    for key in ("served_users", "service_component", "sinr_quality", "sinr_component"):
        endpoint[key + "_mean"] = float(np.mean([row[key] for row in rows]))
    return endpoint


def run_batch(out, launch_sha, entry_start=None, entry_cpu=None):
    out = Path(out)
    if (out / "summary.json").exists() or (out / "raw").exists():
        raise FileExistsError("b03_eta scientific outputs already exist")
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir()
    started = time.monotonic()
    cpu_start = time.process_time()
    entry_start = started if entry_start is None else entry_start
    current_cpu = resource.getrusage(resource.RUSAGE_SELF)
    entry_cpu = (current_cpu.ru_utime, current_cpu.ru_stime) if entry_cpu is None else entry_cpu
    report = dict(status="incomplete", launch_sha=launch_sha,
                  planned_fits=[dict(seed=m, arm=a) for m, a in ORDER], fits=[])
    def publish_progress():
        current = resource.getrusage(resource.RUSAGE_SELF)
        report["batch_wall_seconds"] = time.monotonic() - started
        report["batch_process_cpu_seconds"] = time.process_time() - cpu_start
        report["runner_wall_seconds_through_summary"] = time.monotonic() - entry_start
        report["runner_user_cpu_seconds"] = current.ru_utime - entry_cpu[0]
        report["runner_system_cpu_seconds"] = current.ru_stime - entry_cpu[1]
        report["peak_rss_bytes_process_high_water"] = old_study.peak_rss_bytes()
        report["resource_scope"] = ("single runner process; batch wall/CPU start after imports/admission; "
                                    "completed batch values include final reader; runner wall/user/system CPU start at entry and end before "
                                    "this summary write; RSS is process high-water, not per-fit independent peak")
        write_json(out / "summary.json", report)
    for master, arm in ORDER:
        try:
            fit = run_fit(master, arm, out / "raw" / f"{master}_{arm}", launch_sha)
        except Exception as error:
            report["fits"].append(dict(seed=master, arm=arm, status="incomplete",
                                       failure=f"{type(error).__name__}: {error}"))
            publish_progress()
            return report
        report["fits"].append(dict(seed=master, arm=arm, status=fit["status"],
                                   summary=f"raw/{master}_{arm}/summary.json",
                                   counts=fit["counts"], endpoint=fit.get("endpoint"),
                                   failure=fit.get("failure")))
        publish_progress()
        if fit["status"] != "complete":
            return report
    read_batch(out)
    report = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    publish_progress()
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))


def _interval(values):
    values = np.asarray(values, dtype=np.float64)
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    half = 4.302652729911275 * sd / math.sqrt(3)
    return dict(mean=mean, sd=sd, t95_df2=[mean - half, mean + half])


def read_batch(out):
    out = Path(out)
    report = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    if report["launch_sha"] == "" or [(f["seed"], f["arm"]) for f in report["fits"]] != list(ORDER):
        raise ValueError("batch does not contain the fixed six fits")
    if any(f["status"] != "complete" for f in report["fits"]):
        raise ValueError("incomplete fits have no batch verdict")
    pairs = []
    for master in MASTERS:
        rows = {}
        for arm in learner.ARMS:
            fit_path = out / "raw" / f"{master}_{arm}"
            fit = json.loads((fit_path / "summary.json").read_text(encoding="utf-8"))
            counts = fit["counts"]
            if (fit["status"] != "complete" or fit["seed"] != master or fit["arm"] != arm
                    or fit["launch_sha"] != report["launch_sha"]
                    or counts["train_episodes"] != TRAIN_EPISODES
                    or counts["eval_episodes"] != EVAL_EPISODES
                    or counts["optimizer_steps"] != 128
                    or counts["team_steps"] != EXPECTED_STEPS):
                raise ValueError("invalid completed fit binding or exposure")
            require_movement(fit.get("learner_exposure"))
            with (fit_path / "episodes.jsonl").open(encoding="utf-8") as handle:
                episode_rows = [json.loads(line) for line in handle]
            training = [r for r in episode_rows if r["phase"] == "train"]
            final = [r for r in episode_rows if r["phase"] == "eval"]
            with (fit_path / "updates.jsonl").open(encoding="utf-8") as handle:
                update_rows = [json.loads(line) for line in handle]
            if (len(training) != TRAIN_EPISODES or len(update_rows) != 128
                    or any(r.get("arm") != arm or r.get("seed") != master for r in episode_rows)
                    or any(r.get("arm") != arm or r.get("seed") != master for r in update_rows)
                    or [r["episode"] for r in training] != list(range(TRAIN_EPISODES))
                    or [r["reset_seed"] for r in training] !=
                    [100000 * master + 1000 + e for e in range(TRAIN_EPISODES)]
                    or any(r["steps"] != old.HORIZON for r in training)
                    or [(r["batch"], r["epoch"], r["optimizer_step"]) for r in update_rows] !=
                    [(b, epoch, b * old.EPOCHS + epoch + 1)
                     for b in range(TRAIN_EPISODES // old.BATCH) for epoch in range(old.EPOCHS)]
                    or len(fit["frozen_batches"]) != 32):
                raise ValueError("invalid training or update stream")
            if (len(final) != EVAL_EPISODES or [r["episode"] for r in final] != list(range(EVAL_EPISODES))
                    or [r["reset_seed"] for r in final] !=
                    [100000 * master + 2000 + e for e in range(EVAL_EPISODES)]
                    or any(r["steps"] != old.HORIZON for r in final)):
                raise ValueError("invalid final world panel")
            rows[arm] = final
        s, q = rows["S_eta"], rows["Q32"]
        se, qe = old.endpoint([r["J"] for r in s]), old.endpoint([r["J"] for r in q])
        delta = qe["lower_tail"] - se["lower_tail"]
        differences = {name: float(np.mean([qr[name] - sr[name] for sr, qr in zip(s, q)]))
                       for name in ("J", "served_users", "service_component",
                                    "sinr_quality", "sinr_component")}
        pairs.append(dict(seed=master, delta_tail=delta,
                          delta_mean=qe["mean"] - se["mean"],
                          paired_world_mean_differences=differences,
                          adverse_worlds=[dict(episode=e, delta_J=q[e]["J"] - s[e]["J"],
                                               delta_served_users=q[e]["served_users"] - s[e]["served_users"],
                                               delta_sinr_quality=q[e]["sinr_quality"] - s[e]["sinr_quality"])
                                          for e in range(EVAL_EPISODES)
                                          if q[e]["J"] < s[e]["J"]]))
    tails = [pair["delta_tail"] for pair in pairs]
    means = [pair["delta_mean"] for pair in pairs]
    recurrence = ("Q32_RECURRING" if all(x > 0 for x in tails) and np.mean(tails) > .01 else
                  "S_ETA_RECURRING" if all(x < 0 for x in tails) and np.mean(tails) < -.01 else
                  "MIXED_OR_SMALL")
    report.update(status="complete", pairs=pairs, tail_contrast=_interval(tails),
                  mean_contrast=_interval(means), recurrence=recurrence,
                  interval_note="Descriptive Student t95, df=2, three independent training pairs; assumes approximately normal training-pair effects. Worlds are nested, not extra training replicates.",
                  claim_ceiling="exploratory finite package comparison")
    write_json(out / "summary.json", report)
    return report
