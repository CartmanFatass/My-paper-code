"""Six fixed residual fits and one common-contract frozen reference panel."""

import hashlib
import json
import os
from pathlib import Path
import resource
import time

import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator
from .collector import collect_episode
from .model import (
    SOURCE_COMMIT, SOURCE_INHERITED_SHA256, SOURCE_SHA256, build_arm, exposure,
    load_base, load_warm_start, parameter_snapshot,
)
from .update import optimizers_for, update_motion

MASTERS = (19601, 19602, 19603)
ARMS = ("M_G", "M_O")
HORIZON, TRAIN, EVAL = 256, 512, 32
EVAL_BASE = 1960000000


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tensor_hash(tensor):
    return hashlib.sha256(tensor.detach().numpy().tobytes()).hexdigest()


def new_counts():
    return dict.fromkeys((
        "constructors", "explicit_resets", "fit_started", "train_episodes", "final_eval_episodes",
        "train_team_steps", "final_eval_team_steps", "team_steps", "native_step_calls", "motion_samples",
        "broadcasts", "attempts", "delivered_packets", "censored_packets", "rollouts", "optimizer_steps",
        "actor_optimizer_steps", "critic_optimizer_steps", "replayed_actor_rows", "evaluation_optimizer_steps",
        "diagnostic_forward_calls", "behavior_actor_forward_calls", "behavior_actor_forward_rows",
        "behavior_critic_forward_calls", "behavior_critic_forward_rows", "ppo_actor_forward_calls",
        "ppo_actor_forward_rows", "ppo_critic_forward_calls", "ppo_critic_forward_rows",
    ), 0)


def resources_since(start):
    end = resource.getrusage(resource.RUSAGE_SELF)
    return dict(
        torch_threads=torch.get_num_threads(), torch_interop_threads=torch.get_num_interop_threads(),
        process_user_seconds=end.ru_utime - start.ru_utime,
        process_system_seconds=end.ru_stime - start.ru_stime,
        process_cpu_seconds_during_batch=end.ru_utime + end.ru_stime - start.ru_utime - start.ru_stime,
        process_lifetime_peak_rss_kib_linux=end.ru_maxrss,
        cpu_scope="RUSAGE_SELF user+system delta; one scientific worker",
        rss_scope="RUSAGE_SELF lifetime high-water mark, Linux KiB; not a per-cell incremental peak",
    )


def source_binding(checkpoint_path, checkpoint_sha256):
    return dict(path=str(checkpoint_path), sha256=checkpoint_sha256, source_commit=SOURCE_COMMIT,
                arm="B", master=19451, inherited_sha256=SOURCE_INHERITED_SHA256)


def save_checkpoint(path, actor, critic, arm, master, launch_sha):
    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), arm=arm, master=master,
                    input_size=186, critic_size=526, inherited_sha256=SOURCE_SHA256,
                    correction_bound=.10, source_sha=launch_sha), path)
    return dict(path=str(path), sha256=sha256(path), bytes=Path(path).stat().st_size)


def run_cell(master, arm, out, checkpoint_bytes, checkpoint_sha256, *, factory=make_real,
             horizon=HORIZON, train=TRAIN, evaluation=EVAL, check=lambda: None,
             launch_sha=None, checkpoint_path=None):
    if master not in MASTERS or arm not in ARMS or train % 2 or horizon % 32:
        raise ValueError("invalid fixed continuation cell")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    counts, rows = new_counts(), []
    started_usage = resource.getrusage(resource.RUSAGE_SELF)
    summary = dict(
        object="UAV-MESSAGE-CONTENT-B05-CELL", master=master, arm=arm, directory=str(out),
        launch_sha=launch_sha, status="INCOMPLETE", counts=counts, rows=rows, limits=[],
        warm_start=source_binding(checkpoint_path, checkpoint_sha256),
        configuration=dict(
            horizon=horizon, train=train, final_eval=evaluation, chunk=32, epochs=4,
            episodes_per_rollout=2, residual_shape=[250, 64, 3], correction_bound=.10,
            correction_units="pre_tanh_mean", frozen_base=True, frozen_log_std=True,
            dtype="float32", device="cpu", payload_floats=10, RR_period=5, fee=.001,
            optimizer="Adam", learning_rate=.0003, betas=[.9, .999], eps=1e-8,
            weight_decay=0, separate_actor_critic_optimizers=True, gradient_clip_each=.5,
            gamma=1., terminal_bootstrap=False, policy_clip=.2, critic_loss_weight=.5,
            gaussian_entropy_weight=.01, construction_seed=100000 * master + 11,
            train_world_base=100000 * master + 1000, train_channel_base=100000 * master + 6000,
            train_motion_seed=100000 * master + 21, eval_world_base=EVAL_BASE + 2000,
            eval_channel_base=EVAL_BASE + 7000, eval_motion_base=EVAL_BASE + 3000,
        ),
        scientific_invocation=factory is make_real, started_wall=time.time(),
    )
    actor = critic = initial = None
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

        try:
            check()
            actor, critic = build_arm(master, arm)
            load_warm_start(actor, critic, checkpoint_bytes, checkpoint_sha256)
            initial = parameter_snapshot(actor, critic)
            summary["initial_tensor_sha256"] = {key: tensor_hash(value) for key, value in initial.items()}
            summary["inherited_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            summary["initial_checkpoint"] = save_checkpoint(out / "initial.pt", actor, critic, arm, master, launch_sha)
            write_json(out / "summary.json", summary)
            env = factory(base + 1000)
            counts["constructors"] += 1
            actor_optimizer, critic_optimizer = optimizers_for(actor, critic)
            motion_rng = generator(base + 21)
            counts["fit_started"] = 1
            for rollout in range(train // 2):
                episodes = []
                for e in (2 * rollout, 2 * rollout + 1):
                    metadata = dict(arm=arm, master=master, phase="train", episode=e, motion_seed=base + 21)
                    episodes.append(collect_episode(
                        env, actor, critic, arm, horizon, base + 1000 + e, base + 6000 + e,
                        motion_rng, metadata, counts, emit, check,
                    ))
                update_motion(actor, critic, actor_optimizer, critic_optimizer, episodes, counts, check,
                              emit_update=lambda row: emit_update(dict(rollout=rollout, **row)))
                counts["rollouts"] += 1
                write_json(out / "summary.json", summary)
            summary["exposure"] = exposure(initial, actor, critic)
            summary["final_tensor_sha256"] = {
                key: tensor_hash(value) for key, value in parameter_snapshot(actor, critic).items()
            }
            if summary["initial_tensor_sha256"]["base_actor"] != summary["final_tensor_sha256"]["base_actor"]:
                raise RuntimeError("frozen base parameter identity failed")
            summary["final_checkpoint"] = save_checkpoint(out / "final.pt", actor, critic, arm, master, launch_sha)
            for e in range(evaluation):
                metadata = dict(arm=arm, master=master, phase="final_eval", episode=e,
                                motion_seed=EVAL_BASE + 3000 + e)
                collect_episode(
                    env, actor, critic, arm, horizon, EVAL_BASE + 2000 + e, EVAL_BASE + 7000 + e,
                    generator(EVAL_BASE + 3000 + e), metadata, counts, emit, check,
                    raw_path=out / "raw" / f"final_{e:02d}.npz",
                )
            after_eval = {key: tensor_hash(value) for key, value in parameter_snapshot(actor, critic).items()}
            if after_eval != summary["final_tensor_sha256"]:
                raise RuntimeError("evaluation mutated parameters")
            summary["after_eval_tensor_sha256"] = after_eval
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
            if initial is not None:
                summary["exposure"] = exposure(initial, actor, critic)
        finally:
            summary["finished_wall"] = time.time()
            summary["resources"] = resources_since(started_usage)
            summary["episode_stream_sha256"] = sha256(out / "episodes.jsonl")
            summary["update_stream_sha256"] = sha256(out / "updates.jsonl")
            write_json(out / "summary.json", summary)
    return summary


def run_b40(out, checkpoint_bytes, checkpoint_sha256, *, factory=make_real,
            horizon=HORIZON, evaluation=EVAL, check=lambda: None, launch_sha=None, checkpoint_path=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    counts, rows = new_counts(), []
    started_usage = resource.getrusage(resource.RUSAGE_SELF)
    summary = dict(object="UAV-MESSAGE-CONTENT-B05-B40", master=19451, arm="B40", directory=str(out),
                   launch_sha=launch_sha, status="INCOMPLETE", counts=counts, rows=rows, limits=[],
                   warm_start=source_binding(checkpoint_path, checkpoint_sha256), started_wall=time.time(),
                   scientific_invocation=factory is make_real,
                   configuration=dict(horizon=horizon, final_eval=evaluation, train=0, payload_floats=10))
    with (out / "episodes.jsonl").open("x", encoding="utf-8") as episode_file:
        def emit(row):
            episode_file.write(json.dumps(row, allow_nan=False) + "\n")
            episode_file.flush()
            rows.append(row)
            write_json(out / "summary.json", summary)

        try:
            actor, critic = load_base(checkpoint_bytes, checkpoint_sha256)
            initial = torch.cat([p.detach().flatten() for p in actor.parameters()])
            summary["initial_base_sha256"] = tensor_hash(initial)
            summary["inherited_sigma"] = actor.log_std.detach().clamp(-5, 2).exp().tolist()
            env = factory(EVAL_BASE + 2000)
            counts["constructors"] += 1
            for e in range(evaluation):
                metadata = dict(arm="B40", master=19451, phase="final_eval", episode=e,
                                motion_seed=EVAL_BASE + 3000 + e)
                collect_episode(
                    env, actor, critic, "B40", horizon, EVAL_BASE + 2000 + e, EVAL_BASE + 7000 + e,
                    generator(EVAL_BASE + 3000 + e), metadata, counts, emit, check,
                    raw_path=out / "raw" / f"final_{e:02d}.npz",
                )
            summary["final_base_sha256"] = tensor_hash(torch.cat([p.detach().flatten() for p in actor.parameters()]))
            if summary["initial_base_sha256"] != summary["final_base_sha256"]:
                raise RuntimeError("B40 parameter identity failed")
            summary["status"] = "COMPLETE"
        except Exception as error:
            summary["limits"].append(f"{type(error).__name__}: {error}")
        finally:
            summary["finished_wall"] = time.time()
            summary["resources"] = resources_since(started_usage)
            summary["episode_stream_sha256"] = sha256(out / "episodes.jsonl")
            write_json(out / "summary.json", summary)
    return summary


def expected_counts(arm, horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    baseline = arm == "B40"
    ntrain = 0 if baseline else train
    steps = (ntrain + evaluation) * horizon
    return dict(
        constructors=1, explicit_resets=ntrain + evaluation, fit_started=int(not baseline),
        train_episodes=ntrain, final_eval_episodes=evaluation, train_team_steps=ntrain * horizon,
        final_eval_team_steps=evaluation * horizon, team_steps=steps, native_step_calls=steps,
        motion_samples=steps * 5, broadcasts=steps, attempts=steps, rollouts=ntrain // 2,
        optimizer_steps=ntrain * 2, actor_optimizer_steps=ntrain * 2, critic_optimizer_steps=ntrain * 2,
        replayed_actor_rows=ntrain * horizon * 20, evaluation_optimizer_steps=0,
        diagnostic_forward_calls=evaluation * horizon if arm == "M_O" else 0,
        behavior_actor_forward_calls=steps, behavior_actor_forward_rows=steps * 5,
        behavior_critic_forward_calls=ntrain * horizon, behavior_critic_forward_rows=ntrain * horizon,
        ppo_actor_forward_calls=ntrain * 2, ppo_actor_forward_rows=ntrain * horizon * 20,
        ppo_critic_forward_calls=ntrain * 2, ppo_critic_forward_rows=ntrain * horizon * 4,
    )


def validate_cells(cells, b40, *, horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    if [(cell["master"], cell["arm"]) for cell in cells] != [(m, a) for m in MASTERS for a in ARMS]:
        return dict(complete=False, reason="missing or unordered cells")
    reference = None
    for cell in [*cells, b40]:
        expected = expected_counts(cell["arm"], horizon, train, evaluation)
        if cell["status"] != "COMPLETE" or any(cell["counts"].get(k) != v for k, v in expected.items()):
            return dict(complete=False, reason=f"count/status mismatch {cell['master']}/{cell['arm']}")
        if cell["counts"]["delivered_packets"] + cell["counts"]["censored_packets"] != expected["team_steps"]:
            return dict(complete=False, reason="transport count mismatch")
        if len(cell["rows"]) != evaluation or [row["episode"] for row in cell["rows"]] != list(range(evaluation)):
            return dict(complete=False, reason="panel row mismatch")
        for row in cell["rows"]:
            if (row["steps"] != horizon or row["attempts"] != horizon or row["accepted_packets"] != horizon
                    or row["collided_attempts"] or abs(row["charge_per_tick"] - .001) > 1e-10):
                return dict(complete=False, reason="native row mismatch")
        witnesses = [(row["reset_seed"], row["channel_seed"], row["motion_seed"], row["initial_scene_sha256"],
                      row["channel_sequence_sha256"]) for row in cell["rows"]]
        if reference is None:
            reference = witnesses
        elif witnesses != reference:
            return dict(complete=False, reason="unpaired final panel")
    return dict(complete=True, reading="COMPLETE_READY_FOR_SEPARATE_READER")


def run_batch(out, launch_sha, checkpoint, checkpoint_sha256=SOURCE_SHA256, seed=MASTERS[0], *,
              factory=make_real, horizon=HORIZON, train=TRAIN, evaluation=EVAL):
    if seed != MASTERS[0] or train % 2 or horizon % 32 or (
            factory is make_real and (horizon, train, evaluation) != (HORIZON, TRAIN, EVAL)):
        raise ValueError("invalid fixed B05 contract")
    checkpoint = Path(checkpoint)
    checkpoint_bytes = checkpoint.read_bytes()
    if sha256(checkpoint) != checkpoint_sha256 or checkpoint_sha256 != SOURCE_SHA256:
        raise ValueError("B19451 checkpoint digest mismatch")
    start_usage = resource.getrusage(resource.RUSAGE_SELF)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists() or any((out / str(m)).exists() for m in MASTERS) or (out / "B40").exists():
        raise FileExistsError("scientific output already exists")
    torch.set_num_threads(1)
    cells = []
    batch = dict(
        object="UAV-MESSAGE-CONTENT-B05", launch_sha=launch_sha, source_sha=launch_sha, status="INCOMPLETE",
        cells=cells, b40=None, warm_start=dict(source_binding(checkpoint, checkpoint_sha256), bytes=len(checkpoint_bytes)),
        started_wall=time.time(), limits=[],
        expected=dict(masters=list(MASTERS), arms=list(ARMS), policy_fits=6, predictor_instances=0,
                      train_episodes=3072, evaluation_episodes=224, native_team_steps=843776,
                      optimizer_steps=6144, actor_optimizer_steps=6144, critic_optimizer_steps=6144,
                      replayed_actor_rows=15728640),
    )
    write_json(out / "summary.json", batch)
    try:
        for master in MASTERS:
            (out / str(master)).mkdir()
            for arm in ARMS:
                batch["active_cell"] = f"{master}/{arm}"
                write_json(out / "summary.json", batch)
                cell = run_cell(master, arm, out / str(master) / arm, checkpoint_bytes, checkpoint_sha256,
                                factory=factory, horizon=horizon, train=train, evaluation=evaluation,
                                launch_sha=launch_sha, checkpoint_path=checkpoint)
                cells.append(cell)
                batch["actual"] = {key: sum(c["counts"][key] for c in cells) for key in new_counts()}
                write_json(out / "summary.json", batch)
                if cell["status"] != "COMPLETE":
                    batch["limits"].append(f"{master}/{arm} incomplete")
                    break
            if batch["limits"]:
                break
        if not batch["limits"]:
            batch["active_cell"] = "B40"
            write_json(out / "summary.json", batch)
            batch["b40"] = run_b40(out / "B40", checkpoint_bytes, checkpoint_sha256, factory=factory,
                                    horizon=horizon, evaluation=evaluation, launch_sha=launch_sha,
                                    checkpoint_path=checkpoint)
            batch["actual"] = {key: sum(c["counts"][key] for c in [*cells, batch["b40"]]) for key in new_counts()}
            batch["reduction"] = validate_cells(cells, batch["b40"], horizon=horizon, train=train, evaluation=evaluation)
            batch["status"] = "COMPLETE" if batch["reduction"]["complete"] else "INCOMPLETE"
        batch["active_cell"] = None
    except Exception as error:
        batch["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        batch["finished_wall"] = time.time()
        batch["resources"] = resources_since(start_usage)
        write_json(out / "summary.json", batch)
    return batch
