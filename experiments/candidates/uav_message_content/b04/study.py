"""Fixed nine-fit B04 continuation and one frozen-B panel."""

import hashlib
import json
import os
from pathlib import Path
import resource
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import optimizer_for
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from .learner import collect_episode, update_motion, update_predictor
from .model import (SOURCE_COMMIT, SOURCE_INHERITED_SHA256, SOURCE_SHA256,
                    build_arm, exposure, load_base, load_warm_start,
                    parameter_snapshot)

MASTERS = (19501, 19502, 19503)
ARMS = ("G", "O", "F")
HORIZON, TRAIN, EVAL = 256, 512, 32
EVAL_BASE = 1950000000


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tensor_hash(tensor):
    return hashlib.sha256(tensor.numpy().tobytes()).hexdigest()


def new_counts():
    return dict.fromkeys(("constructors", "explicit_resets", "fit_started", "train_episodes",
                          "final_eval_episodes", "train_team_steps", "final_eval_team_steps",
                          "team_steps", "native_step_calls", "motion_samples", "broadcasts",
                          "attempts", "delivered_packets", "censored_packets", "rollouts",
                          "optimizer_steps", "replayed_actor_rows", "predictor_forwards",
                          "eligible_labels", "predictor_updates", "predictor_rows",
                          "evaluation_optimizer_steps", "diagnostic_forward_calls",
                          "behavior_actor_forward_calls", "behavior_actor_forward_rows",
                          "behavior_critic_forward_calls", "behavior_critic_forward_rows",
                          "ppo_actor_forward_calls", "ppo_actor_forward_rows",
                          "ppo_critic_forward_calls", "ppo_critic_forward_rows"), 0)


def _save_checkpoint(path, actor, critic, predictor, arm, master, inherited_sha256):
    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(),
                    predictor=None if predictor is None else predictor.state_dict(),
                    arm=arm, master=master, input_size=186, critic_size=526,
                    inherited_sha256=inherited_sha256), path)
    return dict(path=str(path), sha256=sha256(path))


def run_cell(master, arm, out, checkpoint_bytes, checkpoint_sha256, *,
             factory=make_real, horizon=HORIZON, train=TRAIN, evaluation=EVAL,
             check=lambda: None, launch_sha=None, checkpoint_path=None):
    if master not in MASTERS or arm not in ARMS or train % 2 or horizon % 32:
        raise ValueError("invalid fixed continuation cell")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    counts, rows = new_counts(), []
    summary = dict(object="UAV-MESSAGE-CONTENT-B04-CELL", master=master, arm=arm,
                   directory=str(out), launch_sha=launch_sha, status="INCOMPLETE",
                   counts=counts, rows=rows, limits=[],
                   warm_start=dict(path=str(checkpoint_path), sha256=checkpoint_sha256,
                                   source_commit=SOURCE_COMMIT, arm="B", master=19451,
                                   inherited_sha256=SOURCE_INHERITED_SHA256),
                   configuration=dict(horizon=horizon, train=train, final_eval=evaluation,
                                      chunk=32, epochs=4, predictor_epochs=4,
                                      dtype="float32", device="cpu",
                                      torch_threads=torch.get_num_threads(),
                                      torch_interop_threads=torch.get_num_interop_threads(),
                                      payload_floats=10, RR_period=5, fee=.001,
                                      train_world_base=100000 * master + 1000,
                                      train_channel_base=100000 * master + 6000,
                                      train_motion_seed=100000 * master + 21,
                                      predictor_construction_seed=100000 * master + 12,
                                      eval_world_base=EVAL_BASE + 2000,
                                      eval_channel_base=EVAL_BASE + 7000,
                                      eval_motion_base=EVAL_BASE + 3000),
                   scientific_invocation=factory is make_real, started_wall=time.time())
    actor = critic = predictor = initial = None
    base = 100000 * master
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file, \
         (out / "updates.jsonl").open("x", encoding="utf-8") as update_file:
        def emit(row):
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            if row["phase"] == "final_eval":
                rows.append(row)
            write_json(out / "summary.json", summary)

        def emit_update(record):
            update_file.write(json.dumps(record, allow_nan=False) + "\n")
            update_file.flush()
            write_json(out / "summary.json", summary)

        try:
            check()
            actor, critic, predictor = build_arm(master, arm)
            load_warm_start(actor, critic, checkpoint_bytes, checkpoint_sha256)
            initial = parameter_snapshot(actor, critic, predictor)
            summary["initial_tensor_sha256"] = {k: tensor_hash(v) for k, v in initial.items()}
            summary["initial_checkpoint"] = _save_checkpoint(
                out / "initial.pt", actor, critic, predictor, arm, master, checkpoint_sha256)
            write_json(out / "summary.json", summary)
            env = factory(base + 1000)
            counts["constructors"] += 1
            optimizer = optimizer_for(actor, critic)
            predictor_optimizer = (torch.optim.Adam(predictor.parameters(), lr=3e-4,
                betas=(.9, .999), eps=1e-8, weight_decay=0, amsgrad=False,
                foreach=False, fused=False) if predictor is not None else None)
            motion_rng = generator(base + 21)
            counts["fit_started"] = 1
            write_json(out / "summary.json", summary)
            for rollout in range(train // 2):
                episodes, label_batches = [], []
                for e in (2 * rollout, 2 * rollout + 1):
                    metadata = dict(arm=arm, master=master, phase="train", episode=e,
                                    motion_seed=base + 21)
                    episode, labels = collect_episode(
                        env, actor, critic, predictor, arm, horizon,
                        base + 1000 + e, base + 6000 + e, motion_rng,
                        metadata, counts, emit, check)
                    episodes.append(episode)
                    if labels is not None:
                        label_batches.append(labels)
                update_motion(actor, critic, optimizer, episodes, counts, check,
                              emit_update=lambda r: emit_update(dict(rollout=rollout, **r)))
                if predictor is not None:
                    update_predictor(predictor, predictor_optimizer, label_batches, counts, check,
                                     emit_update=lambda r: emit_update(dict(rollout=rollout, **r)))
                counts["rollouts"] += 1
                write_json(out / "summary.json", summary)
            summary["exposure"] = exposure(initial, actor, critic, predictor)
            summary["final_checkpoint"] = _save_checkpoint(
                out / "final.pt", actor, critic, predictor, arm, master, checkpoint_sha256)
            summary["final_tensor_sha256"] = {
                k: tensor_hash(v) for k, v in parameter_snapshot(actor, critic, predictor).items()}
            write_json(out / "summary.json", summary)
            for e in range(evaluation):
                metadata = dict(arm=arm, master=master, phase="final_eval", episode=e,
                                motion_seed=EVAL_BASE + 3000 + e)
                collect_episode(env, actor, critic, predictor, arm, horizon,
                                EVAL_BASE + 2000 + e, EVAL_BASE + 7000 + e,
                                generator(EVAL_BASE + 3000 + e), metadata, counts, emit, check,
                                raw_path=out / "raw" / f"final_{e:02d}.npz")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
            if initial is not None and actor is not None:
                summary["exposure"] = exposure(initial, actor, critic, predictor)
        finally:
            summary["finished_wall"] = time.time()
            write_json(out / "summary.json", summary)
    return summary


def run_b0(out, checkpoint_bytes, checkpoint_sha256, *, factory=make_real,
           horizon=HORIZON, evaluation=EVAL, check=lambda: None, launch_sha=None,
           checkpoint_path=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    counts, rows = new_counts(), []
    summary = dict(object="UAV-MESSAGE-CONTENT-B04-B0", master=19451, arm="B0",
                   directory=str(out), launch_sha=launch_sha, status="INCOMPLETE",
                   counts=counts, rows=rows, limits=[],
                   warm_start=dict(path=str(checkpoint_path), sha256=checkpoint_sha256,
                                   source_commit=SOURCE_COMMIT, arm="B", master=19451,
                                   inherited_sha256=SOURCE_INHERITED_SHA256),
                   scientific_invocation=factory is make_real,
                   configuration=dict(horizon=horizon, final_eval=evaluation, payload_floats=7,
                                      train=0, torch_threads=torch.get_num_threads(),
                                      torch_interop_threads=torch.get_num_interop_threads()))
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file:
        def emit(row):
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            rows.append(row)
            write_json(out / "summary.json", summary)

        try:
            actor, critic = load_base(checkpoint_bytes, checkpoint_sha256)
            env = factory(EVAL_BASE + 2000)
            counts["constructors"] += 1
            for e in range(evaluation):
                metadata = dict(arm="B0", master=19451, phase="final_eval", episode=e,
                                motion_seed=EVAL_BASE + 3000 + e)
                collect_episode(env, actor, critic, None, "B0", horizon,
                                EVAL_BASE + 2000 + e, EVAL_BASE + 7000 + e,
                                generator(EVAL_BASE + 3000 + e), metadata, counts, emit, check,
                                raw_path=out / "raw" / f"final_{e:02d}.npz")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
        finally:
            write_json(out / "summary.json", summary)
    return summary


def validate_cells(cells, b0, *, horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    if [(c["master"], c["arm"]) for c in cells] != [(m, a) for m in MASTERS for a in ARMS]:
        return dict(complete=False, reason="missing or unordered cells")
    reference = None
    for cell in [*cells, b0]:
        is_b0 = cell is b0
        steps = (0 if is_b0 else train * horizon) + evaluation * horizon
        expected = dict(train_episodes=0 if is_b0 else train,
                        final_eval_episodes=evaluation,
                        train_team_steps=0 if is_b0 else train * horizon,
                        final_eval_team_steps=evaluation * horizon,
                        team_steps=steps, native_step_calls=steps,
                        motion_samples=5 * steps, broadcasts=steps, attempts=steps,
                        rollouts=0 if is_b0 else train // 2,
                        optimizer_steps=0 if is_b0 else 2 * train,
                        replayed_actor_rows=0 if is_b0 else 4 * train * horizon * 5,
                        predictor_updates=(2 * train if cell["arm"] == "F" else 0),
                        predictor_forwards=(steps if cell["arm"] == "F" else 0),
                        evaluation_optimizer_steps=0,
                        diagnostic_forward_calls=(evaluation * horizon if cell["arm"] in ("O", "F") else 0),
                        behavior_actor_forward_calls=steps,
                        behavior_actor_forward_rows=5 * steps,
                        behavior_critic_forward_calls=steps,
                        behavior_critic_forward_rows=steps,
                        ppo_actor_forward_calls=0 if is_b0 else 2 * train,
                        ppo_actor_forward_rows=0 if is_b0 else 4 * train * horizon * 5,
                        ppo_critic_forward_calls=0 if is_b0 else 2 * train,
                        ppo_critic_forward_rows=0 if is_b0 else 4 * train * horizon)
        if cell["status"] != "COMPLETE" or any(cell["counts"].get(k) != v for k, v in expected.items()):
            return dict(complete=False, reason=f"count/status mismatch {cell['master']}/{cell['arm']}")
        if (cell["counts"]["delivered_packets"] + cell["counts"]["censored_packets"] != steps or
            cell["counts"]["predictor_rows"] != 4 * cell["counts"]["eligible_labels"]):
            return dict(complete=False, reason=f"transport/predictor count mismatch {cell['master']}/{cell['arm']}")
        if len(cell["rows"]) != evaluation or [r["episode"] for r in cell["rows"]] != list(range(evaluation)):
            return dict(complete=False, reason=f"panel rows mismatch {cell['master']}/{cell['arm']}")
        for row in cell["rows"]:
            if (row["steps"] != horizon or row["attempts"] != horizon or
                row["accepted_packets"] != horizon or row["collided_attempts"] or
                abs(row["charge_per_tick"] - .001) > 1e-10 or
                (cell.get("scientific_invocation") and row["Q"] is None)):
                return dict(complete=False, reason=f"native row mismatch {cell['master']}/{cell['arm']}")
        witnesses = [(r["reset_seed"], r["channel_seed"], r["initial_scene_sha256"],
                      r["channel_sequence_sha256"]) for r in cell["rows"]]
        if reference is None:
            reference = witnesses
        elif witnesses != reference:
            return dict(complete=False, reason=f"unpaired panel {cell['master']}/{cell['arm']}")
    return dict(complete=True, reading="COMPLETE_READY_FOR_SEPARATE_READER")


def run_batch(out, launch_sha, checkpoint, checkpoint_sha256=SOURCE_SHA256,
              seed=MASTERS[0], *, factory=make_real, horizon=HORIZON,
              train=TRAIN, evaluation=EVAL):
    if seed != MASTERS[0] or train % 2 or horizon % 32 or (
            factory is make_real and (horizon, train, evaluation) != (HORIZON, TRAIN, EVAL)):
        raise ValueError("invalid fixed B04 study contract")
    checkpoint = Path(checkpoint)
    checkpoint_bytes = checkpoint.read_bytes()
    if hashlib.sha256(checkpoint_bytes).hexdigest() != checkpoint_sha256 or checkpoint_sha256 != SOURCE_SHA256:
        raise ValueError("B19451 checkpoint digest mismatch")
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "summary.json").exists() or any((output / str(m)).exists() for m in MASTERS) or (output / "B0").exists():
        raise FileExistsError("scientific output already exists")
    torch.set_num_threads(1)
    cells = []
    batch = dict(object="UAV-MESSAGE-CONTENT-B04", launch_sha=launch_sha,
                 source_sha=launch_sha, status="INCOMPLETE", cells=cells, b0=None,
                 warm_start=dict(path=str(checkpoint), sha256=checkpoint_sha256,
                                 bytes=len(checkpoint_bytes), source_commit=SOURCE_COMMIT,
                                 arm="B", master=19451,
                                 inherited_sha256=SOURCE_INHERITED_SHA256),
                 started_wall=time.time(), limits=[],
                 expected=dict(masters=list(MASTERS), arms=list(ARMS), policy_fits=9,
                               predictor_instances=3, train_episodes=4608,
                               evaluation_episodes=320, native_team_steps=1261568,
                               optimizer_steps=9216, predictor_updates=3072,
                               replayed_actor_rows=23592960))
    write_json(output / "summary.json", batch)
    try:
        for master in MASTERS:
            (output / str(master)).mkdir()
            for arm in ARMS:
                cell = run_cell(master, arm, output / str(master) / arm,
                                checkpoint_bytes, checkpoint_sha256, factory=factory,
                                horizon=horizon, train=train, evaluation=evaluation,
                                launch_sha=launch_sha, checkpoint_path=checkpoint)
                cells.append(cell)
                batch["actual"] = {key: sum(c["counts"][key] for c in cells) for key in new_counts()}
                write_json(output / "summary.json", batch)
                if cell["status"] != "COMPLETE":
                    batch["limits"].append(f"{master}/{arm} incomplete")
                    break
            if batch["limits"]:
                break
        if not batch["limits"]:
            batch["b0"] = run_b0(output / "B0", checkpoint_bytes, checkpoint_sha256,
                                 factory=factory, horizon=horizon, evaluation=evaluation,
                                 launch_sha=launch_sha, checkpoint_path=checkpoint)
            batch["actual"] = {key: sum(c["counts"][key] for c in [*cells, batch["b0"]])
                               for key in new_counts()}
            batch["reduction"] = validate_cells(cells, batch["b0"], horizon=horizon,
                                                 train=train, evaluation=evaluation)
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
