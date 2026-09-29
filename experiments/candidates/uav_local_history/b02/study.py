"""Complete fixed-exposure categorical-policy learning and native evaluation."""

import hashlib
import json
import os
from pathlib import Path
import resource
import time

import numpy as np
from scipy.stats import t as student_t
import torch

from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real, critic_features
from experiments.candidates.uav_local_history.b01.controller import COMMANDS, LocalController
from experiments.candidates.uav_local_history.b01.study import (
    audit_points, collect_episode as collect_ordinary, file_identity, native_reading, write_json,
)
from .inputs import ObservationHistory, current_only
from .model import templates, sample_action, optimizers
from .update import update

MASTERS = (291021, 291022, 291023)
EVAL_SEEDS = tuple(range(29102000, 29102032))
TRAIN_EPISODES = 512
HORIZON = 256


def count(counts, key, amount=1):
    counts[key] = counts.get(key, 0) + amount


def json_line(stream, value):
    stream.write(json.dumps(value, allow_nan=False) + "\n")
    stream.flush()


def parameter_vector(model):
    return torch.cat([p.detach().flatten() for p in model.parameters()]).clone()


def save_checkpoint(path, actor, critic, master, phase, **extra):
    torch.save(dict(actor=actor.state_dict(), critic=critic.state_dict(), master=master,
                    phase=phase, **extra), path)
    return file_identity(path)


@torch.no_grad()
def collect_learned(env, actor, critic, master, phase, reset_seed, action_rng, out, counts,
                    *, horizon=HORIZON):
    started = time.perf_counter()
    training = phase == "train"
    phase_count = "train" if training else "eval"
    obs, info = env.reset(seed=reset_seed)
    count(counts, "explicit_resets")
    if np.asarray(obs).shape != (5, 104):
        raise ValueError("five native local observation rows required")
    state = info["state"]
    users = np.array(info["state_info"]["user_positions"], copy=True)
    positions = np.array(info["state_info"]["uav_positions"], copy=True)
    initial_positions = positions.copy()
    initial_world_sha = hashlib.sha256(users.tobytes() + positions.tobytes()).hexdigest()
    histories = [ObservationHistory() for _ in range(5)]
    last = np.zeros((5, 3), dtype=np.float32)
    action_counts = np.zeros(27, dtype=np.int64)
    path_length = np.zeros(5)
    storage = {key: [] for key in ("context", "points", "valid", "critic", "action", "logp", "value", "reward")}
    raw = {key: [] for key in ("observations", "commands", "post_positions", "reward", "served", "sinr_quality",
                               "n_current", "n_cached", "n_absent")}
    decision_raw = {key: [] for key in ("context", "points", "valid", "logits", "action", "logp",
                                        "shadow_logits", "shadow_action", "shadow_executed_disagreement")}
    reward_values, service_values, quality_values, entropy_values = [], [], [], []
    boundary_steps = lower_steps = absent_decisions = shadow_disagreements = 0
    maximum_cache = max_age = 0
    cache_sum = absent_sum = max_error = 0.0
    unmatched = duplicates = ambiguous = 0
    macro_reward = 0.0
    for clock in range(horizon):
        for agent, history in enumerate(histories):
            before_distances = history.association_distance_evaluations
            before_counts = {k: history.cache.counters[k] for k in ("cache_matches", "cache_inserts", "cache_evicts")}
            history.ingest(obs[agent].copy(), clock)
            count(counts, "learned_cache_ingests")
            count(counts, "association_distance_evaluations", history.association_distance_evaluations - before_distances)
            for key, previous in before_counts.items():
                count(counts, "learned_" + key, history.cache.counters[key] - previous)
        n_current = np.array([int(h.cache.current_mask.sum()) for h in histories])
        n_cached = np.array([len(h.cache.points) for h in histories])
        n_absent = n_cached - n_current
        maximum_cache = max(maximum_cache, int(n_cached.max()))
        cache_sum += n_cached.sum()
        absent_sum += n_absent.sum()
        for history in histories:
            if len(history.cache.points):
                max_age = max(max_age, int((clock - history.cache.last_seen).max()))
        if clock % 4 == 0:
            features = [h.features(last[i]) for i, h in enumerate(histories)]
            context = torch.from_numpy(np.stack([x[0] for x in features]))
            points = torch.from_numpy(np.stack([x[1] for x in features]))
            valid = torch.from_numpy(np.stack([x[2] for x in features]))
            logits = actor(context, points, valid)
            if not torch.isfinite(logits).all():
                raise FloatingPointError("nonfinite behavior logits")
            action, logp, entropy = sample_action(logits, action_rng, greedy=not training)
            if not torch.isfinite(logp).all() or not torch.isfinite(entropy).all():
                raise FloatingPointError("nonfinite categorical terms")
            command = COMMANDS[action.numpy()].copy()
            action_counts += np.bincount(action.numpy(), minlength=27)
            entropy_values.append(float(entropy.mean()))
            absent_decisions += int((n_absent > 0).sum())
            count(counts, f"{phase_count}_actor_forward_calls")
            count(counts, f"{phase_count}_actor_forward_rows", 5)
            count(counts, f"{phase_count}_agent_decisions", 5)
            if training:
                cx = torch.from_numpy(critic_features(state, last, np.zeros(5, dtype=np.int64)))
                value = critic(cx)
                if not torch.isfinite(value):
                    raise FloatingPointError("nonfinite behavior value")
                count(counts, "behavior_critic_forward_calls")
                count(counts, "behavior_critic_forward_rows")
                for key, value in (("context", context), ("points", points), ("valid", valid),
                                   ("critic", cx), ("action", action), ("logp", logp), ("value", value)):
                    storage[key].append(value.clone())
            else:
                shadow_points, shadow_valid = current_only(points.numpy(), valid.numpy())
                shadow_logits = actor(context, torch.from_numpy(shadow_points), torch.from_numpy(shadow_valid))
                shadow_action, _, _ = sample_action(shadow_logits, greedy=True)
                executed = []
                for agent, history in enumerate(histories):
                    trajectories = LocalController._trajectories(history.own)
                    executed.append(not np.array_equal(trajectories[int(action[agent])],
                                                       trajectories[int(shadow_action[agent])]))
                    audit = audit_points(history.cache.points, users)
                    max_error = max(max_error, audit["max_error_m"])
                    unmatched += audit["unmatched"]
                    duplicates += audit["duplicate_matches"]
                    ambiguous += audit["ambiguous_matches"]
                shadow_disagreements += sum(executed)
                count(counts, "diagnostic_actor_forward_calls")
                count(counts, "diagnostic_actor_forward_rows", 5)
                for key, value in (("context", context.numpy()), ("points", points.numpy()), ("valid", valid.numpy()),
                                   ("logits", logits.numpy()), ("action", action.numpy()), ("logp", logp.numpy()),
                                   ("shadow_logits", shadow_logits.numpy()), ("shadow_action", shadow_action.numpy()),
                                   ("shadow_executed_disagreement", np.array(executed))):
                    decision_raw[key].append(value.copy())
        if not training:
            raw["observations"].append(obs.copy())
            raw["commands"].append(command.copy())
            for name, value in (("n_current", n_current), ("n_cached", n_cached), ("n_absent", n_absent)):
                raw[name].append(value.copy())
        count(counts, "native_step_calls")
        next_obs, _averaged_reward, terminated, truncated, info = env.step(command)
        count(counts, "team_steps")
        count(counts, f"{phase_count}_team_steps")
        reward, served, quality = native_reading(info)
        after = np.array(info["state_info"]["uav_positions"], copy=True)
        path_length += np.linalg.norm(after - positions, axis=1)
        boundary_steps += int(((after[:, :2] <= .001) | (after[:, :2] >= 999.999)).any(axis=1).sum())
        lower_steps += int((after[:, 2] <= 50.001).sum())
        reward_values.append(reward)
        service_values.append(served)
        quality_values.append(quality)
        macro_reward += reward
        if training and clock % 4 == 3:
            storage["reward"].append(torch.tensor(macro_reward, dtype=torch.float32))
            macro_reward = 0.0
        if not training:
            raw["post_positions"].append(after.copy())
            raw["reward"].append(reward)
            raw["served"].append(served)
            raw["sinr_quality"].append(quality)
        if bool(terminated or truncated) != (clock + 1 == horizon):
            raise RuntimeError(f"unexpected native boundary at {clock + 1}/{horizon}")
        obs, state, positions = next_obs, info["next_state"], after
        last[:] = command
    counts["complete_episodes"] += 1
    count(counts, f"{phase_count}_episodes")
    row = dict(arm=f"L{0 if phase == 'initial' else 1}", master=master, phase=phase, seed=reset_seed,
               steps=horizon, J=float(np.mean(reward_values)), return_sum=float(np.sum(reward_values)),
               mean_served=float(np.mean(service_values)), min_served=int(min(service_values)),
               service_p10=float(np.quantile(service_values, .1)), zero_service_steps=int(np.sum(np.array(service_values) == 0)),
               mean_sinr_quality=float(np.mean(quality_values)), coverage_reward=.7 * float(np.mean(service_values)) / 50,
               quality_reward=.3 * float(np.mean(quality_values)), mean_path_length_m=float(path_length.mean()),
               xy_boundary_uav_steps=boundary_steps, lower_altitude_uav_steps=lower_steps,
               action_counts=action_counts.tolist(), mean_categorical_entropy=float(np.mean(entropy_values)),
               mean_cached_points=float(cache_sum / horizon / 5), mean_absent_points=float(absent_sum / horizon / 5),
               max_cached_points=maximum_cache, max_absent_age=max_age, absent_point_decisions=absent_decisions,
               shadow_executed_disagreements=shadow_disagreements if not training else None,
               max_cache_position_error_m=max_error if not training else None,
               unmatched_cache_point_observations=unmatched if not training else None,
               duplicate_cache_match_observations=duplicates if not training else None,
               ambiguous_cache_match_observations=ambiguous if not training else None,
               initial_world_sha256=initial_world_sha, wall_seconds=time.perf_counter() - started)
    if not training:
        arrays = {key: np.asarray(value) for key, value in raw.items()}
        arrays.update({key: np.asarray(value) for key, value in decision_raw.items()})
        arrays.update(true_users=users, initial_positions=initial_positions, terminal_observation=obs.copy(),
                      decision_time=np.arange(0, horizon, 4))
        raw_path = Path(out) / "raw" / f"{row['arm']}_{master}_{reset_seed}.npz"
        np.savez_compressed(raw_path, **arrays)
        row["raw"] = file_identity(raw_path)
    return row, ({key: torch.stack(value) for key, value in storage.items()} if training else None)


def effect(values):
    values = np.asarray(values, dtype=np.float64)
    half = float(student_t.ppf(.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else None
    mean = float(values.mean())
    return dict(mean=mean, differences=values.tolist(), descriptive_t95=None if half is None else [mean - half, mean + half],
                positive=int((values > 0).sum()), negative=int((values < 0).sum()), zero=int((values == 0).sum()))


def summarize(rows, masters, eval_seeds):
    index = {(r["arm"], r.get("master"), r["seed"]): r for r in rows}
    if len(index) != len(rows) or len(rows) != (2 + 2 * len(masters)) * len(eval_seeds):
        raise ValueError("incomplete or duplicate fixed endpoint panel")
    metrics = ("J", "mean_served", "mean_sinr_quality", "min_served", "service_p10",
               "zero_service_steps", "mean_path_length_m", "xy_boundary_uav_steps")
    result = {"instance_comparisons": {}, "training_instance_means": {}, "ordinary_H_minus_C": {}}
    for metric in metrics:
        result["ordinary_H_minus_C"][metric] = effect([
            index[("H", None, s)][metric] - index[("C", None, s)][metric] for s in eval_seeds])
    for comparator in ("L0", "H", "C"):
        per_master = {}
        for master in masters:
            per_master[str(master)] = {metric: effect([
                index[("L1", master, seed)][metric] - index[(comparator, master if comparator == "L0" else None, seed)][metric]
                for seed in eval_seeds]) for metric in metrics}
        result["instance_comparisons"]["L1_minus_" + comparator] = per_master
        result["training_instance_means"]["L1_minus_" + comparator] = {
            metric: effect([per_master[str(master)][metric]["mean"] for master in masters]) for metric in metrics}
    result["unit"] = "three independent training instances on one common world panel; world intervals are descriptive within instance"
    return result


def run_batch(out, launch_sha, *, factory=make_real, masters=MASTERS, train_episodes=TRAIN_EPISODES,
              eval_seeds=EVAL_SEEDS, horizon=HORIZON, entry_start=None):
    if train_episodes % 2 or horizon % 4:
        raise ValueError("complete two-episode rollouts and four-step commitments required")
    start = time.perf_counter() if entry_start is None else entry_start
    usage = resource.getrusage(resource.RUSAGE_SELF)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "summary.json").exists() or (out / "raw").exists():
        raise FileExistsError("refusing to replace scientific output")
    for name in ("raw", "checkpoints", "training"):
        (out / name).mkdir()
    counts = dict(constructors=0, explicit_resets=0, native_step_calls=0, team_steps=0, complete_episodes=0,
                  fit_started=0, fit_completed=0, optimizer_steps=0, train_team_steps=0, eval_team_steps=0)
    config = dict(masters=list(masters), eval_seeds=list(eval_seeds), train_episodes=train_episodes, horizon=horizon,
                  train_seed_rule="29110000 + 1000 * block_index + episode_index", parameter_seed_rule="100000 * master + 11",
                  action_seed_rule="100000 * master + 29", commands=COMMANDS.tolist(), decision_period=4,
                  actor_context=107, cache_shape=[64, 7], cache_capacity=64, association_tolerance_m=.01,
                  critic_input=136, discount=1, critic_return_scale=256, rollout_episodes=2, ppo_epochs=4,
                  actor_lr=.0003, critic_lr=.0003, clip_ratio=.2, entropy_coefficient=.01, grad_clip=.5,
                  evaluation="argmax, sole initialization/final, same32worlds; nonmutating current-cache shadow",
                  planned_fits=len(masters), planned_train_steps=len(masters) * train_episodes * horizon,
                  planned_eval_steps=(2 + 2 * len(masters)) * len(eval_seeds) * horizon, threads=1, launch_sha=launch_sha)
    summary = dict(object="UAV-LOCAL-HISTORY-B02", status="INCOMPLETE", launch_sha=launch_sha, config=config,
                   scientific_invocation=factory is make_real, counts=counts, rows=[], fits=[], limits=[])
    write_json(out / "config.json", config)
    write_json(out / "summary.json", summary)
    env = None
    try:
        env = factory(eval_seeds[0])
        counts["constructors"] += 1
        for index, seed in enumerate(eval_seeds):
            for arm in (("C", "H") if index % 2 == 0 else ("H", "C")):
                before_steps = counts["team_steps"]
                try:
                    row = collect_ordinary(env, arm, seed, out, counts, horizon=horizon)
                finally:
                    counts["eval_team_steps"] += counts["team_steps"] - before_steps
                count(counts, "eval_episodes")
                summary["rows"].append(row)
                write_json(out / "summary.json", summary)
        for block, master in enumerate(masters):
            fit_start, fit_cpu = time.perf_counter(), time.process_time()
            actor, critic = templates(master)
            actor_start, critic_start = parameter_vector(actor), parameter_vector(critic)
            initial = save_checkpoint(out / "checkpoints" / f"initial_{master}.pt", actor, critic, master, "initial")
            fit = dict(master=master, status="INITIALIZED", initial=initial,
                       actor_parameters=actor_start.numel(), critic_parameters=critic_start.numel())
            summary["fits"].append(fit)
            action_rng = torch.Generator(device="cpu").manual_seed(100000 * master + 29)
            for seed in eval_seeds:
                row, _ = collect_learned(env, actor, critic, master, "initial", seed, None, out, counts, horizon=horizon)
                summary["rows"].append(row)
                write_json(out / "summary.json", summary)
            aopt, copt = optimizers(actor, critic)
            counts["fit_started"] += 1
            fit["status"] = "TRAINING"
            training_rows = []
            episode_path = out / "training" / f"episodes_{master}.jsonl"
            update_path = out / "training" / f"updates_{master}.jsonl"
            with episode_path.open("w", encoding="utf-8") as ep_stream, update_path.open("w", encoding="utf-8") as up_stream:
                episodes = []
                for episode in range(train_episodes):
                    reset_seed = 29110000 + 1000 * block + episode
                    row, rollout = collect_learned(env, actor, critic, master, "train", reset_seed, action_rng, out, counts, horizon=horizon)
                    json_line(ep_stream, row)
                    training_rows.append(row)
                    episodes.append(rollout)
                    if len(episodes) == 2:
                        def emit(record):
                            json_line(up_stream, dict(master=master, rollout=episode // 2, **record))
                        update(actor, critic, aopt, copt, episodes, counts, emit=emit)
                        episodes.clear()
                    if (episode + 1) % 16 == 0 or episode + 1 == train_episodes:
                        fit["completed_training_episodes"] = episode + 1
                        write_json(out / "summary.json", summary)
                        print(json.dumps(dict(master=master, episode=episode + 1, train_steps=counts["train_team_steps"],
                                              J=row["J"], elapsed_seconds=time.perf_counter() - start)), flush=True)
            counts["fit_completed"] += 1
            fit.update(status="TRAINED", train_episodes=train_episodes,
                       actor_displacement=float((parameter_vector(actor) - actor_start).norm()),
                       critic_displacement=float((parameter_vector(critic) - critic_start).norm()),
                       training_first64_J=float(np.mean([r["J"] for r in training_rows[:64]])),
                       training_last64_J=float(np.mean([r["J"] for r in training_rows[-64:]])),
                       training_mean_entropy=float(np.mean([r["mean_categorical_entropy"] for r in training_rows])),
                       training_action_counts=np.sum([r["action_counts"] for r in training_rows], axis=0).tolist(),
                       training_episodes=file_identity(episode_path), training_updates=file_identity(update_path))
            fit["final"] = save_checkpoint(out / "checkpoints" / f"final_{master}.pt", actor, critic, master, "final",
                                           actor_optimizer=aopt.state_dict(), critic_optimizer=copt.state_dict(),
                                           action_rng_state=action_rng.get_state())
            for seed in eval_seeds:
                row, _ = collect_learned(env, actor, critic, master, "final", seed, None, out, counts, horizon=horizon)
                summary["rows"].append(row)
                write_json(out / "summary.json", summary)
            fit.update(status="COMPLETE", wall_seconds=time.perf_counter() - fit_start,
                       process_cpu_seconds=time.process_time() - fit_cpu)
        if counts["train_team_steps"] != config["planned_train_steps"] or counts["eval_team_steps"] != config["planned_eval_steps"]:
            raise RuntimeError("fixed exposure count mismatch")
        if counts["optimizer_steps"] != len(masters) * train_episodes // 2 * 8:
            raise RuntimeError("fixed optimizer exposure mismatch")
        summary["comparisons"] = summarize(summary["rows"], masters, eval_seeds)
        summary["status"] = "COMPLETE"
    except Exception as error:
        summary["limits"].append(f"{type(error).__name__}: {error}")
    finally:
        if env is not None:
            try:
                env.close()
            except Exception as error:
                summary["status"] = "INCOMPLETE"
                summary["limits"].append(f"environment close: {type(error).__name__}: {error}")
        final_usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = dict(wall_seconds_from_runner_entry=time.perf_counter() - start,
                                    user_seconds_batch=final_usage.ru_utime - usage.ru_utime,
                                    system_seconds_batch=final_usage.ru_stime - usage.ru_stime,
                                    process_lifetime_peak_rss_kib_linux=final_usage.ru_maxrss,
                                    torch_threads=torch.get_num_threads(), interop_threads=torch.get_num_interop_threads(),
                                    thread_environment={k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")})
        summary["artifacts"] = dict(raw_files=len(summary["rows"]), raw_bytes=sum(r["raw"]["bytes"] for r in summary["rows"]))
        write_json(out / "summary.json", summary)
    return summary
