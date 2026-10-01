"""Full own-history episodes with one ego and four separately stateful teammates."""
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import critic_features
from .contract import ENDPOINTS, EGOS, array_digest, assignment
from .policies import Member


def add(counts, key, amount=1):
    counts[key] = counts.get(key, 0) + int(amount)


def collect_episode(env, *, ego, panel, world, tape, protocol, actors, out, counts, inflight,
                    head=None, critic=None, block=None, group=None, policy_sha=None):
    training = critic is not None
    if ego not in EGOS or panel not in ("T", "X") or type(tape) is not int:
        raise ValueError("undeclared episode")
    learned = ego in ENDPOINTS
    if learned != (head is not None) or (training and (not learned or panel != "T" or tape != 0
            or block not in (0, 1) or group is None or ego != ego[0] + str(block))):
        raise ValueError("invalid focal head/training episode")
    if training:
        if world not in protocol.training_worlds[block]:
            raise ValueError("training world outside selected block")
        motion_root, roster_root = protocol.training_roots[block], protocol.training_assignment_roots[block]
    else:
        if world not in protocol.worlds or tape not in range(len(protocol.evaluation_roots)) or group is not None:
            raise ValueError("evaluation outside fixed final panel")
        motion_root, roster_root = protocol.evaluation_roots[tape], protocol.evaluation_assignment_root
    kind = "training" if training else "evaluation"
    identifier = f"{kind}_{ego}_{panel}_w{world}_t{tape}"
    path = Path(out) / "raw" / (identifier + ".npz")
    partial = path.with_name(path.stem + "_partial.npz")
    if path.exists() or partial.exists():
        raise FileExistsError("episode already has full or partial evidence")
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    times = {f"{part}_{clock}_seconds": 0. for part in ("reset", "policy", "critic", "native_step", "raw_write")
             for clock in ("wall", "cpu")}
    add(counts, "roster_draws")
    roster_index, teammates = assignment(roster_root, world, tape, panel)
    laws = (ego[0] if learned else ego, *teammates)
    members = [Member(law, actors, world=world, agent=i, root=motion_root, head=head if i == 0 else None)
               for i, law in enumerate(laws)]
    if len({id(member) for member in members}) != 5:
        raise AssertionError("private member instances required")
    inflight.update(id=identifier, kind=kind, ego=ego, panel=panel, world=world, tape=tape, block=block,
                    group=group, policy_agents=[m.counters for m in members], times=times, tick=None)
    raw = {key: [] for key in ("observations", "commands", "reward", "served", "sinr_quality", "sinr", "peer_sinr",
                               "connections", "transmitter_mask", "positions", "terminated", "truncated",
                               "step_generation", "step_path_loss_misses", "history_descriptor", "history_matches",
                               "history_delta", "history_gate_counts", "history_n_peers")}
    decision = {key: [] for key in ("nav_pre", "nav_next", "features", "logits", "hidden", "probabilities",
                                    "action_index", "fallback", "memo_hit", "n_current", "n_peers", "innovation",
                                    "entropy", "logp", "policy_scores", "policy_served", "c_index", "parent_probabilities")}
    if learned:
        decision.update(contexts=[], base_logits=[])
    if training:
        decision.update(critic_states=[], critic_features=[], values=[])
    initial = {}
    try:
        wall, cpu = time.perf_counter(), time.process_time()
        add(counts, "explicit_reset_calls")
        obs, info = env.reset(seed=int(world))
        add(counts, "explicit_resets")
        add(counts, "native_dense_power_slots", 275)
        base = env.env
        add(counts, "native_unique_distance_pairs", int(base._path_loss_cache_misses))
        times["reset_wall_seconds"] += time.perf_counter() - wall
        times["reset_cpu_seconds"] += time.process_time() - cpu
        obs = np.asarray(obs, dtype=np.float32)
        positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
        users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
        state = np.asarray(info["state"], dtype=np.float32).copy() if training else None
        expected_positions, expected_users = original_layout(world)
        if (not np.array_equal(positions, expected_positions) or not np.array_equal(users, expected_users)
                or not base.transmitter_mask.all() or base.current_step != 0):
            raise AssertionError("original fixed N5/U50/all-on reset changed")
        initial.update(initial_users=users, initial_sinr=base.sinr_matrix.copy(),
                       initial_peer_sinr=base.uav_sinr_matrix.copy(), initial_connections=base.connections.copy(),
                       initial_generation=np.asarray(base._path_loss_cache_generation, dtype=np.int64))
        navs = np.asarray([initial_nav(row) for row in obs], dtype=np.int64)
        commands = np.zeros((5, 3), dtype=np.float32)
        raw["positions"].append(positions.copy())
        for tick in range(protocol.horizon):
            inflight["tick"] = tick
            if (obs.shape != (5, 104) or not np.isfinite(obs).all()
                    or not np.array_equal(obs[:, -1], np.full(5, tick / 256., dtype=np.float32))
                    or not base.transmitter_mask.all()):
                raise AssertionError("five finite private local rows/original clock/all-on required")
            wall, cpu = time.perf_counter(), time.process_time()
            history = members[0].ingest(obs[0].copy(), tick)
            times["policy_wall_seconds"] += time.perf_counter() - wall
            times["policy_cpu_seconds"] += time.process_time() - cpu
            # Fixed peers have no two-frame controller in the selected T/X rosters.
            for key in ("descriptor", "matches", "delta", "gate_counts", "n_peers"):
                raw["history_" + key].append(history[key])
            if tick % 4 == 0:
                if training:
                    if state.shape != (116,) or not np.isfinite(state).all():
                        raise ValueError("separate finite privileged critic state required")
                    feature = critic_features(state, commands, np.zeros(5, dtype=np.int64))
                    wall, cpu = time.perf_counter(), time.process_time()
                    with torch.inference_mode():
                        value = critic(torch.from_numpy(feature).reshape(1, 136)).reshape(-1)[0]
                    add(counts, "collected_critic_rows")
                    if not torch.isfinite(value):
                        raise FloatingPointError("collected critic value is nonfinite")
                    times["critic_wall_seconds"] += time.perf_counter() - wall
                    times["critic_cpu_seconds"] += time.process_time() - cpu
                    decision["critic_states"].append(state.copy())
                    decision["critic_features"].append(feature)
                    decision["values"].append(np.float32(value.item()))
                before, answers = navs.copy(), []
                wall, cpu = time.perf_counter(), time.process_time()
                for i, member in enumerate(members):
                    add(counts, "motion_request_calls")
                    answer = member.query(obs[i], tick, int(navs[i]))
                    add(counts, "motion_requests")
                    add(counts, "motion_draws", int(laws[i] not in ("C", "V", "R")))
                    add(counts, "collected_head_rows", int(laws[i] in ("F", "H")))
                    if (answer["features"].dtype != np.float32 or answer["features"].shape != (114,)
                            or not np.array_equal(answer["features"][:103], obs[i, :103])
                            or not np.array_equal(answer["command"], COMMANDS[answer["action_index"]])):
                        raise AssertionError("own local feature/command provenance changed")
                    commands[i], navs[i] = answer["command"], answer["next_nav"]
                    answers.append(answer)
                times["policy_wall_seconds"] += time.perf_counter() - wall
                times["policy_cpu_seconds"] += time.process_time() - cpu
                decision["nav_pre"].append(before)
                decision["nav_next"].append(navs.copy())
                for key in decision:
                    if key in ("nav_pre", "nav_next", "critic_states", "critic_features", "values"):
                        continue
                    if key in ("contexts", "base_logits"):
                        decision[key].append(answers[0]["context" if key == "contexts" else key])
                    else:
                        source = {"policy_scores": "scores", "policy_served": "served"}.get(key, key)
                        decision[key].append([answer[source] for answer in answers])
            inflight["policy_agents"] = [m.counters for m in members]
            raw["observations"].append(obs.copy())
            raw["commands"].append(commands.copy())
            raw["transmitter_mask"].append(base.transmitter_mask.copy())
            wall, cpu = time.perf_counter(), time.process_time()
            add(counts, "native_step_calls")
            next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
            add(counts, "native_steps")
            add(counts, kind + "_native_steps")
            add(counts, "native_uav_ticks", 5)
            add(counts, "native_dense_power_slots", 275)
            add(counts, "native_unique_distance_pairs", int(base._path_loss_cache_misses))
            times["native_step_wall_seconds"] += time.perf_counter() - wall
            times["native_step_cpu_seconds"] += time.process_time() - cpu
            reward, served, quality = native_reading(next_info)
            global_info = next_info["infos_dict"]["uav_0"]["global"]
            after = np.asarray(next_info["state_info"]["uav_positions"], dtype=np.float64).copy()
            if not np.array_equal(after, np.clip(positions + 30. * commands.astype(np.float64),
                                                [0., 0., 50.], [1000., 1000., 150.])):
                raise AssertionError("native held motion changed")
            raw["positions"].append(after)
            for key, value in (("reward", reward), ("served", served), ("sinr_quality", quality),
                               ("sinr", np.asarray(global_info["sinr_matrix"]).copy()),
                               ("peer_sinr", base.uav_sinr_matrix.copy()),
                               ("connections", np.asarray(global_info["connections"]).copy()),
                               ("terminated", bool(terminated)), ("truncated", bool(truncated)),
                               ("step_generation", int(base._path_loss_cache_generation)),
                               ("step_path_loss_misses", int(base._path_loss_cache_misses))):
                raw[key].append(value)
            if bool(terminated) != (tick + 1 == protocol.horizon) or bool(truncated):
                raise AssertionError("unexpected terminal/truncation boundary")
            obs, positions = np.asarray(next_obs, dtype=np.float32), after
            if training:
                state = np.asarray(next_info["next_state"], dtype=np.float32).copy()
        arrays = {key: np.asarray(value) for key, value in {**raw, **decision}.items()}
        arrays.update(initial, terminal_observation=obs.copy(), decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64),
                      macro_rewards=np.asarray(raw["reward"], dtype=np.float64).reshape(-1, 4).sum(axis=1, dtype=np.float64))
        wall, cpu = time.perf_counter(), time.process_time()
        np.savez_compressed(path, **arrays)
        identity = file_identity(path)
        identity["path"] = str(path.relative_to(out))
        times["raw_write_wall_seconds"] += time.perf_counter() - wall
        times["raw_write_cpu_seconds"] += time.process_time() - cpu
        from .reading import episode_metrics
        row = dict(id=identifier, kind=kind, ego=ego, panel=panel, world=world, tape=tape, block=block, group=group,
                   motion_root=motion_root, assignment_root=roster_root, assignment_index=roster_index, laws=list(laws),
                   policy_sha256=policy_sha, raw=identity, **episode_metrics(arrays), **times,
                   agent_policy_counts=[m.counters for m in members], policy_counts=sum_counts(m.counters for m in members),
                   initial_state_sha256=array_digest(arrays["positions"][0], users),
                   raw_array_bytes=sum(value.nbytes for value in arrays.values()),
                   cpu_seconds=time.process_time() - start_cpu, wall_seconds=time.perf_counter() - start_wall,
                   timing_scope="reset, private policy/tracker/critic calls, native steps, checks and evidence compression/hash")
        add(counts, "complete_episodes")
        add(counts, kind + "_episodes")
        inflight.clear()
        if not training:
            return row, None
        rollout = {key: arrays[key] for key in ("contexts", "base_logits", "critic_features", "values", "macro_rewards")}
        rollout.update({key: arrays[key][:, 0] for key in ("logits", "probabilities", "action_index", "logp")})
        return row, rollout
    except BaseException:
        inflight["policy_agents"] = [m.counters for m in members]
        try:
            if not partial.exists():
                arrays = {key: np.asarray(value) for key, value in {**raw, **decision}.items()}
                arrays.update(initial)
                np.savez_compressed(partial, **arrays)
                identity = file_identity(partial)
                identity["path"] = str(partial.relative_to(out))
                inflight["partial_raw"] = identity
        except BaseException as error:
            inflight["partial_raw_save_error"] = repr(error)
        raise
