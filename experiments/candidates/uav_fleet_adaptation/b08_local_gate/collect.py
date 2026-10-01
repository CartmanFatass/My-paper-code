"""Paid complete native branches and finals with old-mask decision timing."""
from pathlib import Path
import time

import numpy as np

from experiments.candidates.uav_fleet_adaptation.b02.controllers import COMMANDS, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.reading import sum_counts
from experiments.candidates.uav_local_history.b01.study import file_identity, native_reading
from .contract import FITTED, NEURAL, PROGRAMS, array_digest, gate_uniform
from .environment import original_layout
from .fit import capped_count, gate_features, predict
from .policies import Policy


def _add(counts, key, value=1):
    counts[key] = counts.get(key, 0) + value


def choose_gate(gate, answer, *, world, tick, gate_root, params=None, forced=None):
    count = capped_count(answer)
    uniform, prediction = -1., 0.
    if gate == "A":
        requested = False
    elif gate == "O":
        requested = True
    elif gate == "R":
        uniform = gate_uniform(gate_root, world, tick, (tick // 4) % 5)
        requested = uniform < .5
    elif gate == "ZERO":
        requested = count == 0
    elif gate in FITTED:
        if params is None:
            raise ValueError("fitted gate artifact required")
        prediction = float(predict(params, gate_features(answer, gate)))
        requested = prediction > 0.
    else:
        raise ValueError("unknown gate")
    if forced is not None and (gate != "R" or forced not in ("OFF", "ON")):
        raise ValueError("only acquisition R can be forced")
    executed = requested if forced is None else forced == "OFF"
    return dict(gate_count=count, gate_innovation=uniform, gate_prediction=prediction,
                gate_requested_off=bool(requested), gate_off=bool(executed), gate_forced=forced is not None)


def collect_episode(env, *, program, world, tape, actor, out, protocol, counts, inflight,
                    policy_sha, kind="evaluation", branch=None, force_tick=None, gate_params=None):
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    if program not in PROGRAMS or kind not in ("acquisition", "evaluation"):
        raise ValueError("unknown B08 episode identity")
    parent, gate = program.split("_", 1)
    if ((actor is None) != (parent not in NEURAL)) or env.n_uavs != 5:
        raise ValueError("parent actor/roster mismatch")
    if kind == "acquisition":
        if (program != "P0_R" or tape is not None or world not in protocol.training_worlds
                or branch not in ("OFF", "ON")
                or force_tick != protocol.force_tick(protocol.training_worlds.index(world)) or gate_params is not None):
            raise ValueError("invalid fixed acquisition branch")
        motion_root, gate_root = protocol.training_motion_root, protocol.training_gate_root
        identifier = f"acquisition_w{world}_{branch}"
    else:
        if (world not in protocol.worlds or branch is not None or force_tick is not None
                or tape not in ((None,) if parent == "C" else (0, 1))
                or ((gate_params is None) != (gate not in FITTED))):
            raise ValueError("invalid final episode identity/artifact")
        motion_root = None if parent == "C" else protocol.evaluation_motion_roots[tape]
        gate_root = protocol.evaluation_gate_roots[tape] if gate == "R" else None
        identifier = f"evaluation_{program}_w{world}_t{tape}"
    path = Path(out) / "raw" / (identifier + ".npz")
    if path.exists():
        raise FileExistsError("episode identity already has raw evidence")
    times = {f"{component}_{clock}_seconds": 0. for component in
             ("reset", "decision_query", "gate_query", "mask_refresh", "native_step", "raw_write")
             for clock in ("wall", "cpu")}
    wall, cpu = time.perf_counter(), time.process_time()
    _add(counts, "explicit_reset_calls")
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
    policies = [Policy(parent, actor, world=world, agent=i, sampling_root=motion_root) for i in range(5)]
    inflight.update(id=identifier, kind=kind, parent=parent, program=program, world=world, tape=tape,
                    branch=branch, policy_agents=[p.counters for p in policies], times=times)
    raw = {key: [] for key in ("observations", "commands", "reward", "served", "sinr_quality", "sinr", "peer_sinr",
                               "connections", "transmitter_mask", "terminated", "truncated", "step_generation",
                               "step_path_loss_misses")}
    raw["positions"] = [positions.copy()]
    decision = {key: [] for key in ("nav_pre", "nav_next", "fallback", "action_index", "memo_hit", "features",
                                    "n_current", "n_peers", "probabilities", "innovation", "entropy")}
    if parent in NEURAL:
        decision.update(logits=[], hidden=[])
    if parent not in ("P0", "Bstar0"):
        decision.update(policy_scores=[], policy_served=[], c_index=[])
    if parent == "Hdirect":
        decision["parent_probabilities"] = []
    boundary = {key: [] for key in ("old_decision_mask", "installed_mask", "eligible_agent", "gate_count",
                                    "gate_innovation", "gate_prediction", "gate_requested_off", "gate_off", "gate_forced",
                                    "refresh_sinr", "refresh_peer_sinr", "refresh_connections", "refresh_observations",
                                    "refresh_generation", "refresh_path_loss_misses")}
    commands = np.zeros((5, 3), dtype=np.float32)
    forced_features = None
    for tick in range(protocol.horizon):
        inflight["tick"] = tick
        if tick % 4 == 0:
            old_mask = base.transmitter_mask
            before, answers = navs.copy(), []
            wall, cpu = time.perf_counter(), time.process_time()
            for agent in range(5):
                _add(counts, "motion_request_calls")
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
            gate_answer = choose_gate(gate, answers[eligible], world=world, tick=tick, gate_root=gate_root,
                                      params=gate_params, forced=branch if tick == force_tick else None)
            _add(counts, "gate_opportunities")
            _add(counts, "gate_draws", int(gate == "R"))
            _add(counts, "forced_gate_decisions", int(tick == force_tick))
            if tick == force_tick:
                forced_features = dict(RAW=gate_features(answers[eligible], "RAW"),
                                       HIDDEN=gate_features(answers[eligible], "HIDDEN"))
            times["gate_query_wall_seconds"] += time.perf_counter() - wall
            times["gate_query_cpu_seconds"] += time.process_time() - cpu
            mask = np.ones(5, dtype=bool)
            mask[eligible] = not gate_answer["gate_off"]
            generation, misses = base._path_loss_cache_generation, base._path_loss_cache_misses
            wall, cpu = time.perf_counter(), time.process_time()
            _add(counts, "mask_install_calls")
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
    np.savez_compressed(path, **arrays)
    identity = file_identity(path)
    identity["path"] = str(path.relative_to(out))
    times["raw_write_wall_seconds"] = time.perf_counter() - wall
    times["raw_write_cpu_seconds"] = time.process_time() - cpu
    from .reading import episode_metrics
    row = dict(id=identifier, kind=kind, program=program, parent=parent, gate=gate, world=world, tape=tape,
               branch=branch, force_tick=force_tick, motion_root=motion_root, gate_root=gate_root,
               policy_sha256=policy_sha, raw=identity, **episode_metrics(arrays), **times,
               policy_counts=sum_counts(p.counters for p in policies),
               initial_state_sha256=array_digest(arrays["positions"][0], users),
               cpu_seconds=time.process_time() - started_cpu, wall_seconds=time.perf_counter() - started_wall,
               timing_scope="explicit reset, all actual motion/gate/setter/native queries, evidence/checks/compression/hash")
    _add(counts, "complete_episodes")
    _add(counts, kind + "_episodes")
    inflight.clear()
    return row, forced_features
