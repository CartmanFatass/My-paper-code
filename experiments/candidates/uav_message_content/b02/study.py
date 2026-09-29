"""Fixed B/O/L continuation from the retained C checkpoint."""

import hashlib
import json
import os
from pathlib import Path
import resource
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import optimizer_for
from .learner import collect_episode, update
from .model import SOURCE_SHA256, build_arm, exposure, load_warm_start, snapshot

MASTERS = (19451, 19452, 19453)
ARMS = ("B", "O", "L")
HORIZON, TRAIN, EVAL = 256, 512, 32
EVAL_BASE = 1945000000


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
            "evaluation_optimizer_steps", "diagnostic_forward_calls")
    counts = dict.fromkeys(keys, 0)
    for phase in ("train", "initial_eval", "final_eval"):
        for event in ("motion_samples", "content_samples", "content_credit_rows",
                      "broadcasts", "delivered_packets", "censored_packets"):
            counts[f"{phase}_{event}"] = 0
    return counts


def run_arm(master, arm, out, checkpoint_bytes, checkpoint_sha256, *,
            factory=make_real, horizon=HORIZON, train=TRAIN, evaluation=EVAL,
            check=lambda: None, launch_sha=None, checkpoint_path=None):
    if master not in MASTERS or arm not in ARMS or train % 2 or horizon % 32:
        raise ValueError("invalid fixed continuation cell")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    counts, rows = new_counts(), []
    summary = dict(object="UAV-MESSAGE-CONTENT-B02", master=master, arm=arm,
                   directory=str(out), launch_sha=launch_sha, status="INCOMPLETE",
                   counts=counts, rows=rows, limits=[],
                   warm_start=dict(path=str(checkpoint_path), sha256=checkpoint_sha256),
                   configuration=dict(horizon=horizon, train=train, initial_eval=evaluation,
                                      final_eval=evaluation, chunk=32, epochs=4,
                                      dtype="float32", device="cpu",
                                      torch_threads=torch.get_num_threads(),
                                      torch_interop_threads=torch.get_num_interop_threads(),
                                      content_dimensions=1, RR_period=5, fee=.001,
                                      train_world_base=100000 * master + 1000,
                                      train_channel_base=100000 * master + 6000,
                                      train_motion_seed=100000 * master + 21,
                                      train_content_seed=100000 * master + 22,
                                      eval_world_base=EVAL_BASE + 2000,
                                      eval_channel_base=EVAL_BASE + 7000,
                                      eval_motion_base=EVAL_BASE + 3000,
                                      eval_content_base=EVAL_BASE + 4000),
                   scientific_invocation=factory is make_real, started_wall=time.time())
    actor = critic = initial = None
    base = 100000 * master
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file, \
         (out / "updates.jsonl").open("x", encoding="utf-8") as update_file:
        def emit(row):
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            if row["phase"] != "train":
                rows.append(row)
            write_json(out / "summary.json", summary)

        try:
            check()
            actor, critic = build_arm(master, arm)
            load_warm_start(actor, critic, checkpoint_bytes, checkpoint_sha256)
            initial = snapshot(actor, critic)
            summary["initial_tensor_sha256"] = {k: tensor_hash(v) for k, v in initial.items()}
            initial_file = out / "initial.pt"
            torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(),
                            arm=arm, master=master, input_size=171, critic_size=451,
                            inherited_sha256=checkpoint_sha256), initial_file)
            summary["initial_checkpoint"] = dict(path=str(initial_file), sha256=sha256(initial_file))
            write_json(out / "summary.json", summary)
            env = factory(base + 1000)
            counts["constructors"] += 1
            for phase in ("initial_eval", "train", "final_eval"):
                if phase == "train":
                    optimizer = optimizer_for(actor, critic)
                    counts["fit_started"] = 1
                    write_json(out / "summary.json", summary)
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

                        def emit_update(record):
                            update_file.write(json.dumps(dict(rollout=rollout, **record),
                                                         allow_nan=False) + "\n")
                            update_file.flush()
                            write_json(out / "summary.json", summary)

                        update(actor, critic, optimizer, episodes, counts, check,
                               emit_update=emit_update)
                        counts["rollouts"] += 1
                        write_json(out / "summary.json", summary)
                    summary["exposure"] = exposure(initial, actor, critic)
                    final_file = out / "final.pt"
                    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(),
                                    arm=arm, master=master, input_size=171, critic_size=451,
                                    inherited_sha256=checkpoint_sha256), final_file)
                    summary["final_checkpoint"] = dict(path=str(final_file), sha256=sha256(final_file))
                    summary["final_tensor_sha256"] = {
                        k: tensor_hash(v) for k, v in snapshot(actor, critic).items()}
                    write_json(out / "summary.json", summary)
                    continue
                for e in range(evaluation):
                    metadata = dict(arm=arm, master=master, phase=phase, episode=e,
                                    motion_seed=EVAL_BASE + 3000 + e,
                                    content_seed=EVAL_BASE + 4000 + e)
                    collect_episode(env, actor, critic, arm, horizon,
                                    EVAL_BASE + 2000 + e, EVAL_BASE + 7000 + e,
                                    generator(EVAL_BASE + 3000 + e),
                                    generator(EVAL_BASE + 4000 + e),
                                    metadata, counts, emit, check,
                                    raw_path=out / "raw" / f"{phase}_{e:02d}.npz")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
            if initial is not None and actor is not None:
                summary["exposure"] = exposure(initial, actor, critic)
        finally:
            summary["finished_wall"] = time.time()
            write_json(out / "summary.json", summary)
    return summary


def panel(cell, phase):
    return [row for row in cell["rows"] if row["phase"] == phase]


def validate_cells(cells, *, horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    result = dict(complete=False, reading="INCOMPLETE")
    if [(c["master"], c["arm"]) for c in cells] != [
            (m, a) for m in MASTERS for a in ARMS]:
        return result
    steps = (train + 2 * evaluation) * horizon
    for cell in cells:
        c = cell["counts"]
        required = dict(fit_started=1, train_episodes=train,
                        initial_eval_episodes=evaluation, final_eval_episodes=evaluation,
                        train_team_steps=train * horizon,
                        initial_eval_team_steps=evaluation * horizon,
                        final_eval_team_steps=evaluation * horizon,
                        team_steps=steps, native_step_calls=steps,
                        optimizer_steps=2 * train, rollouts=train // 2,
                        replayed_actor_rows=4 * train * horizon * 5,
                        motion_samples=5 * steps, broadcasts=steps, attempts=steps,
                        diagnostic_forward_calls=2 * evaluation * horizon,
                        evaluation_optimizer_steps=0,
                        content_samples=steps if cell["arm"] == "L" else 0)
        if cell["status"] != "COMPLETE" or any(c.get(k) != v for k, v in required.items()):
            return result
        if len(cell["rows"]) != 2 * evaluation or any(
                [r["episode"] for r in panel(cell, phase)] != list(range(evaluation))
                for phase in ("initial_eval", "final_eval")):
            return result
        if any(r["steps"] != horizon or r["attempts"] != horizon or
               r["accepted_packets"] != horizon or r["collided_attempts"] != 0 or
               abs(r["charge_per_tick"] - .001) > 1e-10 or
               (cell["scientific_invocation"] and r["Q"] is None)
               for r in cell["rows"]):
            return result
    for phase in ("initial_eval", "final_eval"):
        reference = panel(cells[0], phase)
        for cell in cells[1:]:
            if any((a["reset_seed"], a["channel_seed"], a["initial_scene_sha256"],
                    a["channel_sequence_sha256"]) !=
                   (b["reset_seed"], b["channel_seed"], b["initial_scene_sha256"],
                    b["channel_sequence_sha256"]) for a, b in zip(
                        reference, panel(cell, phase))):
                return result
    initial = panel(cells[0], "initial_eval")
    if any(a["action_sequence_sha256"] != b["action_sequence_sha256"]
           for cell in cells for a, b in zip(initial, panel(cell, "initial_eval"))):
        return result
    result.update(complete=True, reading="COMPLETE_READY_FOR_SEPARATE_READER")
    return result


def run_batch(out, launch_sha, checkpoint, checkpoint_sha256=SOURCE_SHA256,
              seed=MASTERS[0], *, factory=make_real, horizon=HORIZON,
              train=TRAIN, evaluation=EVAL):
    if seed != MASTERS[0] or train % 2 or horizon % 32 or (
            factory is make_real and (horizon, train, evaluation) != (HORIZON, TRAIN, EVAL)):
        raise ValueError("invalid fixed study contract")
    checkpoint = Path(checkpoint)
    checkpoint_bytes = checkpoint.read_bytes()
    if hashlib.sha256(checkpoint_bytes).hexdigest() != checkpoint_sha256:
        raise ValueError("C checkpoint digest mismatch")
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "summary.json").exists() or any((output / str(m)).exists() for m in MASTERS):
        raise FileExistsError("scientific output already exists")
    torch.set_num_threads(1)
    cells = []
    batch = dict(object="UAV-MESSAGE-CONTENT-B02", launch_sha=launch_sha,
                 source_sha=launch_sha,
                 warm_start=dict(path=str(checkpoint), sha256=checkpoint_sha256,
                                 bytes=len(checkpoint_bytes)),
                 status="INCOMPLETE", cells=cells, started_wall=time.time(), limits=[],
                 expected=dict(masters=list(MASTERS), arms=list(ARMS), fits=9,
                               train_episodes=4608, evaluation_episodes=576,
                               team_steps=1327104, optimizer_steps=9216,
                               replayed_actor_rows=23592960,
                               diagnostic_forward_calls=147456))
    write_json(output / "summary.json", batch)
    try:
        for master in MASTERS:
            (output / str(master)).mkdir()
            for arm in ARMS:
                cell = run_arm(master, arm, output / str(master) / arm,
                               checkpoint_bytes, checkpoint_sha256, factory=factory,
                               horizon=horizon, train=train, evaluation=evaluation,
                               launch_sha=launch_sha, checkpoint_path=checkpoint)
                cells.append(cell)
                batch["actual"] = {
                    key: sum(item["counts"][key] for item in cells) for key in new_counts()}
                write_json(output / "summary.json", batch)
                if cell["status"] != "COMPLETE":
                    batch["limits"].append(f"{master}/{arm} incomplete")
                    break
            if batch["limits"]:
                break
        batch["reduction"] = validate_cells(cells, horizon=horizon, train=train,
                                             evaluation=evaluation)
        batch["status"] = "COMPLETE" if batch["reduction"]["complete"] else "INCOMPLETE"
    except Exception as error:
        batch["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        usage_end = resource.getrusage(resource.RUSAGE_SELF)
        batch["resources"] = dict(
            torch_threads=torch.get_num_threads(),
            torch_interop_threads=torch.get_num_interop_threads(),
            process_cpu_seconds_during_batch=(usage_end.ru_utime + usage_end.ru_stime
                                              - usage_start.ru_utime - usage_start.ru_stime),
            process_lifetime_peak_rss_kib_linux=usage_end.ru_maxrss,
            cpu_scope="RUSAGE_SELF user+system time delta over run_batch",
            rss_scope="RUSAGE_SELF process-lifetime high-water mark; Linux ru_maxrss is KiB")
        batch["finished_wall"] = time.time()
        write_json(output / "summary.json", batch)
    return batch
