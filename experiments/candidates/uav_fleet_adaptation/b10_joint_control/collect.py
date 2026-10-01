"""Complete episodes: all five old-mask queries, one install, four held ticks."""
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import critic_features
from .contract import DETERMINISTIC, ENDPOINTS, JOINT, PROGRAMS, array_digest
from .policies import Policy
from .records import add


DECISION_FIELDS = ("fallback", "action_index", "motion_index", "memo_hit", "features", "n_current", "n_peers",
                   "probabilities", "innovation", "entropy", "eligible", "requested_off", "hidden_preferred_off",
                   "off_probability", "motion_entropy", "gate_entropy", "logp", "off_score", "off_service",
                   "off_evaluated", "init_logit_max_abs", "init_probability_max_abs", "init_tv", "initial_fidelity")


def collect_episode(env, *, program, world, tape, parent, gate, out, protocol, counts, inflight,
                    actor=None, critic=None, block=None, group=None, policy_sha=None):
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    training = critic is not None
    kind = "training" if training else "evaluation"
    if program not in PROGRAMS or ((program in JOINT) != (actor is not None)) or env.n_uavs != 5:
        raise ValueError("declared B10 policy/model/host required")
    if training:
        if (program not in ENDPOINTS or block != ENDPOINTS.index(program) or type(group) is not int
                or world not in protocol.training_worlds[block][group * 2:group * 2 + 2] or tape is not None):
            raise ValueError("fixed complete training group required")
        root = protocol.training_motion_roots[block]
        identifier = f"training_{program}_g{group:03d}_w{world}"
    else:
        if (world not in protocol.worlds or block is not None or group is not None
                or tape not in ((None,) if program in DETERMINISTIC else (0, 1))):
            raise ValueError("fixed final-panel identity required")
        root = None if program in DETERMINISTIC else protocol.evaluation_motion_roots[tape]
        identifier = f"evaluation_{program}_w{world}_t{tape}"
    path = Path(out) / "raw" / (identifier + ".npz")
    if path.exists():
        raise FileExistsError("episode already has evidence")
    times = {f"{component}_{clock}_seconds": 0. for component in
             ("reset", "decision_query", "critic", "mask_refresh", "native_step", "raw_write")
             for clock in ("wall", "cpu")}
    wall, cpu = time.perf_counter(), time.process_time()
    add(counts, "explicit_reset_calls")
    obs, info = env.reset(seed=int(world))
    add(counts, "explicit_resets")
    add(counts, "native_dense_power_slots", 275)
    base = env.env
    add(counts, "native_unique_distance_pairs", int(base._path_loss_cache_misses))
    times["reset_wall_seconds"], times["reset_cpu_seconds"] = time.perf_counter() - wall, time.process_time() - cpu
    obs = np.asarray(obs, dtype=np.float32)
    positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
    users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
    expected_positions, expected_users = original_layout(world)
    if (obs.shape != (5, 104) or not np.isfinite(obs).all() or not base.transmitter_mask.all()
            or not np.array_equal(positions, expected_positions) or not np.array_equal(users, expected_users)
            or base.current_step != 0):
        raise AssertionError("original reset/layout/all-on contract changed")
    state = np.asarray(info["state"], dtype=np.float32) if training else None
    initial = dict(initial_users=users, initial_sinr=base.sinr_matrix.copy(),
                   initial_peer_sinr=base.uav_sinr_matrix.copy(), initial_connections=base.connections.copy(),
                   initial_generation=np.asarray(base._path_loss_cache_generation, dtype=np.int64))
    navs = np.asarray([initial_nav(obs[i]) for i in range(5)], dtype=np.int64)
    policies = [Policy(program, parent, gate, actor=actor, world=world, agent=i, sampling_root=root,
                       initial=program == "INIT90" or (training and group == 0)) for i in range(5)]
    inflight.update(id=identifier, kind=kind, program=program, world=world, tape=tape,
                    policy_agents=[p.counters for p in policies], times=times)
    raw = {key: [] for key in ("observations", "commands", "reward", "served", "sinr_quality", "sinr", "peer_sinr",
                               "connections", "transmitter_mask", "terminated", "truncated", "step_generation",
                               "step_path_loss_misses")}
    raw["positions"] = [positions.copy()]
    decision = {key: [] for key in ("nav_pre", "nav_next", "count_all", "prediction_all", *DECISION_FIELDS)}
    if program in JOINT:
        decision.update(logits=[], prior=[], prior_logits=[], prior_hidden=[])
    else:
        family = "C" if program == "CJ" else program.split("_", 1)[0]
        if family in ("P0", "Bstar0", "Hdirect"):
            decision.update(logits=[], hidden=[])
        if family not in ("P0", "Bstar0"):
            decision.update(policy_scores=[], policy_served=[], c_index=[])
        if family == "Hdirect":
            decision["parent_probabilities"] = []
    if training:
        decision.update(critic_states=[], critic_features=[], values=[])
    boundary = {key: [] for key in ("old_decision_mask", "installed_mask", "eligible_agent", "gate_count",
                                    "gate_innovation", "gate_prediction", "gate_requested_off", "gate_off", "gate_forced",
                                    "refresh_sinr", "refresh_peer_sinr", "refresh_connections", "refresh_observations",
                                    "refresh_generation", "refresh_path_loss_misses")}
    commands = np.zeros((5, 3), dtype=np.float32)
    for tick in range(protocol.horizon):
        inflight["tick"] = tick
        if tick % 4 == 0:
            old_mask = base.transmitter_mask.copy()
            eligible = (tick // 4) % 5
            if not old_mask[eligible]:
                raise AssertionError("rotating eligible member must be old-mask ON")
            before, answers = navs.copy(), []
            if training:
                wall, cpu = time.perf_counter(), time.process_time()
                if state.shape != (116,) or not np.isfinite(state).all():
                    raise ValueError("finite privileged native state required")
                feature = np.r_[critic_features(state, commands, np.zeros(5, dtype=np.int64)),
                                old_mask.astype(np.float32), np.eye(5, dtype=np.float32)[eligible]].astype(np.float32)
                with torch.inference_mode():
                    value = critic(torch.from_numpy(feature).reshape(1, 146)).reshape(-1)[0]
                add(counts, "collected_critic_rows")
                if not torch.isfinite(value):
                    raise FloatingPointError("nonfinite collection critic")
                decision["critic_states"].append(state.copy())
                decision["critic_features"].append(feature)
                decision["values"].append(np.float32(value.item()))
                times["critic_wall_seconds"] += time.perf_counter() - wall
                times["critic_cpu_seconds"] += time.process_time() - cpu
            wall, cpu = time.perf_counter(), time.process_time()
            for agent in range(5):
                add(counts, "motion_request_calls")
                answer = policies[agent].query(obs[agent], tick, int(navs[agent]))
                add(counts, "motion_requests")
                add(counts, "motion_draws", int(program not in DETERMINISTIC))
                if training:
                    add(counts, "collected_actor_rows")
                if (answer["features"].dtype != np.float32 or answer["features"].shape != (114,)
                        or not np.array_equal(answer["features"][:103], obs[agent, :103])
                        or not np.array_equal(answer["command"], COMMANDS[answer["motion_index"]])):
                    raise AssertionError("private feature/command provenance changed")
                commands[agent] = answer["command"]
                navs[agent] = answer["next_nav"]
                answers.append(answer)
            times["decision_query_wall_seconds"] += time.perf_counter() - wall
            times["decision_query_cpu_seconds"] += time.process_time() - cpu
            decision["nav_pre"].append(before)
            decision["nav_next"].append(navs.copy())
            for key in decision:
                if key not in ("nav_pre", "nav_next", "critic_states", "critic_features", "values"):
                    source = {"policy_scores": "scores", "policy_served": "served", "count_all": "gate_count",
                              "prediction_all": "gate_prediction"}.get(key, key)
                    decision[key].append([answer[source] for answer in answers])
            add(counts, "gate_opportunity_calls")
            add(counts, "gate_opportunities")
            gate_answer = dict(gate_count=answers[eligible]["gate_count"], gate_innovation=-1.,
                               gate_prediction=answers[eligible]["gate_prediction"],
                               gate_requested_off=answers[eligible]["requested_off"],
                               gate_off=answers[eligible]["requested_off"], gate_forced=False)
            mask = np.ones(5, dtype=bool)
            mask[eligible] = not gate_answer["gate_off"]
            generation, misses = base._path_loss_cache_generation, base._path_loss_cache_misses
            wall, cpu = time.perf_counter(), time.process_time()
            add(counts, "mask_install_calls")
            refreshed = base.set_transmitter_mask(mask)
            add(counts, "mask_installs")
            add(counts, "mask_refresh_dense_sinr_slots", 275)
            refreshed_rows = env._dict_to_array(refreshed).astype(np.float32)
            refreshed_misses = int(base._path_loss_cache_misses - misses)
            if (base.current_step != tick or base._path_loss_cache_generation != generation or refreshed_misses != 0
                    or not np.array_equal(base.uav_positions, positions) or not np.array_equal(base.transmitter_mask, mask)):
                raise AssertionError("setter moved time/position/channel or installed a different mask")
            times["mask_refresh_wall_seconds"] += time.perf_counter() - wall
            times["mask_refresh_cpu_seconds"] += time.process_time() - cpu
            boundary["old_decision_mask"].append(old_mask)
            boundary["installed_mask"].append(mask.copy())
            boundary["eligible_agent"].append(eligible)
            for key, value in gate_answer.items():
                boundary[key].append(value)
            for key, value in (("refresh_sinr", base.sinr_matrix), ("refresh_peer_sinr", base.uav_sinr_matrix),
                               ("refresh_connections", base.connections), ("refresh_observations", refreshed_rows)):
                boundary[key].append(value.copy())
            boundary["refresh_generation"].append(generation)
            boundary["refresh_path_loss_misses"].append(refreshed_misses)
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        raw["transmitter_mask"].append(base.transmitter_mask.copy())
        wall, cpu = time.perf_counter(), time.process_time()
        add(counts, "native_step_calls")
        next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
        for key, amount in (("native_steps", 1), (kind + "_native_steps", 1), ("native_uav_ticks", 5),
                            ("native_dense_power_slots", 275), ("native_unique_distance_pairs", int(base._path_loss_cache_misses))):
            add(counts, key, amount)
        times["native_step_wall_seconds"] += time.perf_counter() - wall
        times["native_step_cpu_seconds"] += time.process_time() - cpu
        reward, served, quality = native_reading(next_info)
        global_info = next_info["infos_dict"]["uav_0"]["global"]
        after = np.asarray(next_info["state_info"]["uav_positions"], dtype=np.float64).copy()
        if not np.array_equal(after, np.clip(positions + commands.astype(np.float64) * 30.,
                                            [0., 0., 50.], [1000., 1000., 150.])):
            raise AssertionError("native held motion mismatch")
        raw["positions"].append(after)
        for key, value in (("reward", reward), ("served", served), ("sinr_quality", quality),
                           ("sinr", np.asarray(global_info["sinr_matrix"]).copy()), ("peer_sinr", base.uav_sinr_matrix.copy()),
                           ("connections", np.asarray(global_info["connections"]).copy()), ("terminated", bool(terminated)),
                           ("truncated", bool(truncated)), ("step_generation", int(base._path_loss_cache_generation)),
                           ("step_path_loss_misses", int(base._path_loss_cache_misses))):
            raw[key].append(value)
        if bool(terminated) != (tick + 1 == protocol.horizon) or bool(truncated):
            raise AssertionError("unexpected native terminal boundary")
        obs = np.asarray(next_obs, dtype=np.float32)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise AssertionError("invalid next local rows")
        state = np.asarray(next_info["next_state"], dtype=np.float32) if training else None
        positions = after
    arrays = {key: np.asarray(value) for key, value in {**raw, **decision, **boundary}.items()}
    arrays.update(initial, terminal_observation=obs.copy(), decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64))
    if training:
        arrays["macro_rewards"] = arrays["reward"].reshape(-1, 4).sum(axis=1)
    wall, cpu = time.perf_counter(), time.process_time()
    np.savez_compressed(path, **arrays)
    identity = file_identity(path)
    identity["path"] = str(path.relative_to(out))
    times["raw_write_wall_seconds"], times["raw_write_cpu_seconds"] = time.perf_counter() - wall, time.process_time() - cpu
    from .reading import episode_metrics
    row = dict(id=identifier, kind=kind, program=program, world=world, tape=tape, block=block, group=group,
               motion_root=root, policy_sha256=policy_sha, raw=identity, **episode_metrics(arrays), **times,
               policy_counts=sum_counts(p.counters for p in policies), raw_array_bytes=sum(a.nbytes for a in arrays.values()),
               initial_state_sha256=array_digest(arrays["positions"][0], users),
               cpu_seconds=time.process_time() - started_cpu, wall_seconds=time.perf_counter() - started_wall,
               timing_scope="reset, private policy/critic calls, one mask install per boundary, native steps, checks and raw evidence")
    add(counts, "complete_episodes")
    add(counts, kind + "_episodes")
    inflight.clear()
    return row, arrays if training else None
