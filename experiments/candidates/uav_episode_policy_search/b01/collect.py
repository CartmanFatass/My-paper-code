"""Complete training/final episodes with old-mask queries and four held ticks."""
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import NEURAL, LEARNERS, array_digest, episode_id, validate_identity, dimension
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.fit import capped_count
from .policies import Policy


def _add(counts, key, value=1):
    counts[key] = counts.get(key, 0) + value


def choose_gate(gate, answer):
    count = capped_count(answer)
    if gate not in ('A', 'ZERO'): raise ValueError('undeclared transmitter rights')
    off = gate == 'ZERO' and count == 0
    return dict(gate_count=count, gate_innovation=-1., gate_prediction=0.,
                gate_requested_off=off, gate_off=off, gate_forced=False)


def collect_episode(env, *, identity, actor, out, protocol, counts, inflight,
                    policy_sha, theta=None, persist=lambda: None):
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    validate_identity(identity, protocol)
    program, world, tape = (identity[k] for k in ('program', 'world', 'tape'))
    kind, motion_root = identity['kind'], identity['motion_root']
    learner = program in LEARNERS
    parent, gate = ('P0', 'A') if learner else program.split('_', 1)
    family = identity['family'] if learner else None
    zero_check = kind == 'training' and identity['iteration'] == 0
    if ((theta is None) != (not learner)) or ((actor is None) != (parent not in NEURAL)):
        raise ValueError('episode actor/head binding')
    if learner and (not isinstance(theta,np.ndarray) or theta.dtype!=np.float64 or theta.shape!=(dimension(family),) or not np.isfinite(theta).all()):
        raise ValueError('finite FP64 whole-episode parameters required before effects')
    identifier = episode_id(identity)
    path = Path(out) / "raw" / (identifier + ".npz")
    if path.exists():
        raise FileExistsError("episode identity already has raw evidence")
    times = {f"{component}_{clock}_seconds": 0. for component in
             ("reset", "decision_query", "gate_query", "mask_refresh", "native_step", "raw_write")
             for clock in ("wall", "cpu")}
    wall, cpu = time.perf_counter(), time.process_time()
    inflight.clear()
    inflight.update(identity, id=identifier, effect="reset", attempted_tick=0)
    _add(counts, "explicit_reset_calls")
    persist()
    obs, info = env.reset(seed=int(world))
    _add(counts, "explicit_resets")
    _add(counts, "native_dense_power_slots", 275)
    base = env.env
    _add(counts, "native_unique_distance_pairs", int(base._path_loss_cache_misses))
    times["reset_wall_seconds"], times["reset_cpu_seconds"] = time.perf_counter() - wall, time.process_time() - cpu
    obs = np.asarray(obs, dtype=np.float32)
    positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64).copy()
    users = np.asarray(info["state_info"]["user_positions"], dtype=np.float64).copy()
    expected_positions, expected_users = original_layout(world)
    if (obs.shape != (5, 104) or not np.isfinite(obs).all()
            or not np.array_equal(positions, expected_positions) or not np.array_equal(users, expected_users)
            or not base.transmitter_mask.all() or base.current_step != 0):
        raise AssertionError("original reset/layout/all-on contract changed")
    initial = dict(initial_users=users, initial_sinr=base.sinr_matrix.copy(),
                   initial_peer_sinr=base.uav_sinr_matrix.copy(), initial_connections=base.connections.copy(),
                   initial_generation=np.asarray(base._path_loss_cache_generation, dtype=np.int64))
    navs = np.asarray([initial_nav(obs[i]) for i in range(5)], dtype=np.int64)
    policies = [Policy(parent, actor, world=world, agent=i, sampling_root=motion_root, family=family, theta=theta, zero_check=zero_check) for i in range(5)]
    inflight.update(id=identifier, kind=kind, parent=parent, program=program, world=world, tape=tape,
                    policy_agents=[p.counters for p in policies], times=times)
    raw = {key: [] for key in ("observations", "commands", "reward", "served", "sinr_quality", "sinr", "peer_sinr",
                               "connections", "transmitter_mask", "terminated", "truncated", "step_generation",
                               "step_path_loss_misses")}
    raw["positions"] = [positions.copy()]
    decision = {key: [] for key in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit", "features",
                                    "n_current", "n_peers", "probabilities", "innovation", "entropy")}
    if parent in NEURAL:
        decision.update(logits=[], hidden=[])
    if learner:
        decision.update(head_logits=[], p0_probabilities=[], p0_action_index=[], zero_head_error=[])
    if parent not in ("P0", "Bstar0"):
        decision.update(policy_scores=[], policy_served=[], c_index=[])
    if parent == "Hdirect":
        decision["parent_probabilities"] = []
    boundary = {key: [] for key in ("old_decision_mask", "installed_mask", "eligible_agent", "gate_count",
                                    "gate_innovation", "gate_prediction", "gate_requested_off", "gate_off", "gate_forced",
                                    "refresh_sinr", "refresh_peer_sinr", "refresh_connections", "refresh_observations",
                                    "refresh_generation", "refresh_path_loss_misses")}
    commands = np.zeros((5, 3), dtype=np.float32)
    for tick in range(protocol.horizon):
        inflight["tick"] = tick
        if tick % 4 == 0:
            old_mask = base.transmitter_mask
            before, answers = navs.copy(), []
            wall, cpu = time.perf_counter(), time.process_time()
            for agent in range(5):
                _add(counts, "motion_request_calls")
                inflight.update(effect="policy_query", agent=agent)
                persist()
                answer = policies[agent].query(obs[agent], tick, int(navs[agent]))
                _add(counts, "motion_requests")
                _add(counts, "motion_draws", int(parent != "C"))
                if (answer["features"].dtype != np.float32 or answer["features"].shape != (114,)
                        or not np.array_equal(answer["features"][:103], obs[agent, :103])
                        or not np.array_equal(answer["command"], COMMANDS[answer["action_index"]])):
                    raise AssertionError("motion feature/command provenance changed")
                commands[agent] = answer["command"]
                navs[agent] = answer["next_nav"]
                answers.append(answer)
            times["decision_query_wall_seconds"] += time.perf_counter() - wall
            times["decision_query_cpu_seconds"] += time.process_time() - cpu
            decision["nav_pre"].append(before)
            decision["nav_next"].append(navs.copy())
            for key in decision:
                if key not in ("nav_pre", "nav_next"):
                    source = {"policy_scores": "scores", "policy_served": "served"}.get(key, key)
                    decision[key].append([answer[source] for answer in answers])
            eligible = (tick // 4) % 5
            wall, cpu = time.perf_counter(), time.process_time()
            _add(counts, "gate_opportunity_calls")
            gate_answer = choose_gate(gate, answers[eligible])
            _add(counts, "gate_opportunities")
            _add(counts, "zero_decisions", int(gate == "ZERO"))
            times["gate_query_wall_seconds"] += time.perf_counter() - wall
            times["gate_query_cpu_seconds"] += time.process_time() - cpu
            mask = np.ones(5, dtype=bool)
            mask[eligible] = not gate_answer["gate_off"]
            generation, misses = base._path_loss_cache_generation, base._path_loss_cache_misses
            wall, cpu = time.perf_counter(), time.process_time()
            _add(counts, "mask_install_calls")
            inflight["effect"] = "mask_install"
            persist()
            refreshed = base.set_transmitter_mask(mask)
            _add(counts, "mask_installs")
            _add(counts, "mask_refresh_dense_sinr_slots", 275)
            refreshed_rows = env._dict_to_array(refreshed).astype(np.float32)
            refreshed_misses = int(base._path_loss_cache_misses - misses)
            if (base.current_step != tick or base._path_loss_cache_generation != generation
                    or refreshed_misses != 0 or not np.array_equal(base.uav_positions, positions)
                    or not np.array_equal(base.transmitter_mask, mask)):
                raise AssertionError("setter moved time/position/channel or installed a different mask")
            times["mask_refresh_wall_seconds"] += time.perf_counter() - wall
            times["mask_refresh_cpu_seconds"] += time.process_time() - cpu
            boundary["old_decision_mask"].append(old_mask.copy())
            boundary["installed_mask"].append(mask.copy())
            boundary["eligible_agent"].append(eligible)
            for key, value in gate_answer.items():
                boundary[key].append(value)
            for key, value in (("refresh_sinr", base.sinr_matrix), ("refresh_peer_sinr", base.uav_sinr_matrix),
                               ("refresh_connections", base.connections), ("refresh_observations", refreshed_rows)):
                boundary[key].append(value.copy())
            boundary["refresh_generation"].append(generation)
            boundary["refresh_path_loss_misses"].append(refreshed_misses)
            # obs deliberately remains the OLD returned row; refreshed_rows is evidence only.
        raw["observations"].append(obs.copy())
        raw["commands"].append(commands.copy())
        raw["transmitter_mask"].append(base.transmitter_mask)
        wall, cpu = time.perf_counter(), time.process_time()
        _add(counts, "native_step_calls")
        inflight["effect"] = "native_step"
        persist()
        next_obs, _, terminated, truncated, next_info = env.step(commands.copy())
        _add(counts, "native_steps")
        _add(counts, kind + "_native_steps")
        _add(counts, "native_uav_ticks", 5)
        _add(counts, "native_dense_power_slots", 275)
        _add(counts, "native_unique_distance_pairs", int(base._path_loss_cache_misses))
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
                           ("sinr", np.asarray(global_info["sinr_matrix"]).copy()),
                           ("peer_sinr", base.uav_sinr_matrix.copy()),
                           ("connections", np.asarray(global_info["connections"]).copy()),
                           ("terminated", bool(terminated)), ("truncated", bool(truncated)),
                           ("step_generation", int(base._path_loss_cache_generation)),
                           ("step_path_loss_misses", int(base._path_loss_cache_misses))):
            raw[key].append(value)
        if bool(terminated) != (tick + 1 == protocol.horizon) or bool(truncated):
            raise AssertionError("unexpected native terminal boundary")
        obs = np.asarray(next_obs, dtype=np.float32)
        if obs.shape != (5, 104) or not np.isfinite(obs).all():
            raise AssertionError("invalid next local rows")
        positions = after
    arrays = {key: np.asarray(value) for key, value in {**raw, **decision, **boundary}.items()}
    arrays.update(initial, terminal_observation=obs.copy(),
                  decision_ticks=np.arange(0, protocol.horizon, 4, dtype=np.int64))
    wall, cpu = time.perf_counter(), time.process_time()
    _add(counts, "raw_write_calls")
    inflight["effect"] = "raw_write"
    persist()
    np.savez_compressed(path, **arrays)
    _add(counts, "raw_writes")
    raw_identity = file_identity(path)
    raw_identity["path"] = str(path.relative_to(out))
    times["raw_write_wall_seconds"] = time.perf_counter() - wall
    times["raw_write_cpu_seconds"] = time.process_time() - cpu
    from .reading import episode_metrics
    row = dict(identity, id=identifier, parent=parent, gate=gate,
               theta_sha256=array_digest(theta) if learner else None, zero_check=zero_check,
               policy_sha256=policy_sha, raw=raw_identity, **episode_metrics(arrays), **times,
               policy_counts=sum_counts(p.counters for p in policies),
               initial_state_sha256=array_digest(arrays["positions"][0], users),
               cpu_seconds=time.process_time() - started_cpu, wall_seconds=time.perf_counter() - started_wall,
               timing_scope="explicit reset, all actual motion/gate/setter/native queries, evidence/checks/compression/hash")
    _add(counts, "complete_episodes")
    _add(counts, kind + "_episodes")
    inflight.clear()
    return row
