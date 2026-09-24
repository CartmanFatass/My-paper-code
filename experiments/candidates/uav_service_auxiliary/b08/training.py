"""B08 actual-transition collector using the common completed-segment learner."""

from __future__ import annotations

import gzip
import hashlib
import json
import resource
import time
from pathlib import Path

import numpy as np

from ..b01.native import (
    _bootstrap_values, _module_parameters, make_env, optimizer_steps,
    parameter_displacement, sha256_file,
)
from ..b03.native import assert_finite
from ..b04.evaluation import TRACE_FIELDS, metric_row
from ..b04.native import optimizer_state_steps, write_json
from ..b06.feedback import apply_feedback, decode_legal_observations
from ..b07.native import _native_raw_env, energy_ledger
from .metrics import aggregate_opportunity_summaries, recovery_opportunity_summary


def _digest(array):
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode())
    digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
    digest.update(value.tobytes())
    return digest.hexdigest()


def _execution_state(agent, observations, states, dones, env_steps, modes):
    """Copy live facts that an update/storage clear must not mutate."""
    live = np.flatnonzero(~dones)
    return {
        "observations": observations.copy(), "states": states.copy(),
        "dones": dones.copy(), "env_steps": env_steps.copy(), "feedback_modes": modes.copy(),
        "live_lanes": live,
        "team_skills": np.asarray([agent.env_team_skills[lane] for lane in live]),
        "agent_skills": np.asarray([agent.env_agent_skills[lane] for lane in live]),
        "skill_timers": np.asarray([agent.env_timers[lane] for lane in live]),
        "actor_hidden": agent.actor_hidden_np[live].copy(),
        "critic_hidden": agent.critic_hidden_np[live].copy(),
    }


def _episode_summary(rows, *, lane, episode, end_kind, time_step_seconds):
    arrays = {key: np.asarray([row[key] for row in rows]) for key in rows[0]}
    opportunity = recovery_opportunity_summary(arrays, arrays["metrics"],
                                              time_step_seconds=time_step_seconds)
    passed = ~arrays["mode"]
    anchor = opportunity["first_qualifying_exit_anchor"]
    window_passes = selected_member_passes = 0
    if anchor is not None:
        start, stop = int(anchor["anchor_step"]), int(anchor["window_stop_exclusive"])
        window_passes = int(passed[start:stop].sum())
        selected_member_passes = int(passed[start:stop, int(anchor["member"])].sum())
    return {
        "lane": int(lane), "episode": int(episode), "end_kind": end_kind,
        "budget_censored_episode": end_kind == "budget",
        "actual_steps": len(rows), "opportunity": opportunity,
        "actor_proposal_uav_steps": int(passed.size),
        "feedback_passed_proposal_uav_steps": int(passed.sum()),
        "feedback_mapped_command_uav_steps": int(arrays["command_changed"].sum()),
        "anchor_window_all_member_passed_proposal_uav_steps": window_passes,
        "anchor_window_selected_member_passed_proposal_uav_steps": selected_member_passes,
        "anchor_window_actual_joint_transitions": 0 if anchor is None else int(anchor["actual_window_steps"]),
        "raw_native_J": float(arrays["native_reward"].sum()),
        "actual_delivered_megabits": float(arrays["metrics"][:, TRACE_FIELDS.index(
            "delivered_end_to_end_throughput_mbps")].sum() * time_step_seconds),
    }


def train_arm(agent, config, spec, *, arm: str, out: Path, summary=None, progress=None):
    """Train exactly the supplied exposure; the CLI separately binds production sizes.

    A proposal is always the stored likelihood action. Only the submitted command
    is mapped by F. The original native transition supplies every reward/next input.
    Short native fixtures call this function without opening a production entry.
    """
    if arm not in ("N", "A") or not getattr(config, "ordinary_completed_segments", False):
        raise ValueError("B08 requires arm N/A and the common ordinary completed-segment path")
    if config.num_envs != spec.lanes or config.rollout_length != spec.rollout_length:
        raise ValueError("collector and learner dimensions differ")
    out = Path(out)
    if (out / "summary.json").exists():
        raise FileExistsError(f"training output already exists: {out}")
    out.mkdir(parents=True, exist_ok=True)
    if summary is None:
        summary = {}
    summary.update(
        status="INCOMPLETE", arm=arm, failure=None,
        counts={"transitions": 0, "agent_rows": 0, "phases": 0, "native_episodes": 0},
        training_episodes=[], phases=[], artifacts={},
        native_action_processing=("submitted command enters unchanged native adapter; later physical "
                                  "processing is represented by displacement/docking/energy facts; "
                                  "no native executed-action probability is claimed"),
    )
    started = time.perf_counter()
    initial_parameters = _module_parameters(agent)
    envs, raw_envs = [], []
    arrays = {}
    phase, completed_rows = 0, 0
    phase_saved = False
    timings = {name: 0.0 for name in ("collection", "update", "artifact")}

    def notify(event):
        write_json(out / "summary.json", summary)
        if progress is not None:
            progress({"arm": arm, **event})

    def artifact(path):
        summary["artifacts"][str(path.relative_to(out))] = {
            "sha256": sha256_file(path), "bytes": path.stat().st_size}

    def save_high(name, snapshot):
        path = out / (name + ".json.gz")
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            json.dump(snapshot, handle, allow_nan=False, separators=(",", ":"))
        artifact(path)

    def record(step, lane, values):
        for key, value in values.items():
            value = np.asarray(value)
            if key not in arrays:
                arrays[key] = np.zeros((spec.rollout_length, spec.lanes, *value.shape), dtype=value.dtype)
            arrays[key][step, lane] = value

    def save_phase(partial=False):
        path = out / f"training_{phase:02d}{'_partial' if partial else ''}.npz"
        length = max(completed_rows, int(np.flatnonzero(arrays["valid_execution"].any(axis=1))[-1]) + 1
                     if arrays["valid_execution"].any() else 0)
        payload = {key: value[:length] for key, value in arrays.items()}
        payload.update(metric_fields=np.asarray(TRACE_FIELDS), partial=np.asarray(partial))
        np.savez_compressed(path, **payload)
        artifact(path)

    try:
        for lane in range(spec.lanes):
            env = make_env(config, spec.seed + lane)
            envs.append(env)
            raw_envs.append(_native_raw_env(env))
        resets = [env.reset(seed=spec.seed + lane) for lane, env in enumerate(envs)]
        observations = np.asarray([row[0] for row in resets], dtype=np.float32)
        states = np.asarray([row[1]["state"] for row in resets], dtype=np.float32)
        positions = np.asarray([row[1]["state_info"]["uav_positions"] for row in resets], dtype=np.float64)
        dones = np.ones(spec.lanes, dtype=bool)
        env_steps = np.zeros(spec.lanes, dtype=np.int64)
        episode_ids = np.zeros(spec.lanes, dtype=np.int64)
        modes = np.zeros((spec.lanes, config.n_agents), dtype=bool)
        episode_rows = [[] for _ in envs]
        for phase in range(1, spec.rollouts + 1):
            completed_rows, phase_saved = 0, False
            arrays = {key: np.zeros((spec.rollout_length, spec.lanes), dtype=bool)
                      for key in ("valid_execution", "valid_diagnostics", "stored_transition")}
            stage = time.perf_counter()
            for step in range(spec.rollout_length):
                current_obs, current_states = observations.copy(), states.copy()
                proposals, _, step_data = agent.step(
                    current_states, current_obs, env_steps, dones, deterministic=False,
                    return_step_data=True, build_infos=False)
                proposals = np.asarray(proposals, dtype=np.float32).copy()
                next_obs, next_states, infos, rewards, ending = [], [], [], [], []
                for lane, (env, raw) in enumerate(zip(envs, raw_envs, strict=True)):
                    margins, batteries, stations, distances, vectors = decode_legal_observations(current_obs[lane])
                    mode_before = modes[lane].copy()
                    entered = exited = np.zeros(config.n_agents, dtype=bool)
                    submitted = proposals[lane].copy()
                    if arm == "A":
                        decision = apply_feedback(current_obs[lane], proposals[lane], modes[lane])
                        submitted, modes[lane] = decision.submitted_actions, decision.modes
                        entered, exited = decision.entered, decision.exited
                    battery = np.asarray(raw.uav_battery_ratios, dtype=np.float64).copy()
                    charging = np.asarray(raw.uav_charging, dtype=bool).copy()
                    obs, reward, terminated, truncated, info = env.step(submitted)
                    summary["counts"]["transitions"] += 1
                    summary["counts"]["agent_rows"] += config.n_agents
                    values = {
                        "valid_execution": True, "native_reward": float(reward),
                        "ends": np.asarray((terminated, truncated), dtype=bool),
                        "original_action": proposals[lane], "submitted_action": submitted,
                        "action_logprobs": np.asarray(step_data["action_logprobs"][lane], dtype=np.float32),
                        "agent_skills": step_data["agent_skills"][lane],
                        "team_skills": step_data["team_skills"][lane],
                        "skill_changed": step_data["skill_changed"][lane],
                        "skill_timer": step_data["skill_timer"][lane],
                        "episode_id": episode_ids[lane], "episode_step": env_steps[lane],
                        "interaction_index": (phase - 1) * spec.rollout_length + step,
                        "low_policy_version": phase - 1,
                        "mode_before": mode_before, "mode": modes[lane].copy(),
                        "entry": entered, "exit": exited,
                        "command_changed": np.any(submitted != proposals[lane], axis=-1),
                        "pre_legal_margin": margins, "pre_legal_battery": batteries,
                        "selected_station": stations, "station_distance_m": distances,
                        "station_vector_m": vectors,
                        "decision_state_sha256": np.asarray(_digest(current_states[lane]), dtype="S64"),
                        "decision_obs_sha256": np.asarray(_digest(current_obs[lane]), dtype="S64"),
                        # Preserve source facts before any derived closure/metric check.
                        "raw_physical_pre_battery": battery,
                        "raw_physical_post_battery": np.asarray(raw.uav_battery_ratios).copy(),
                        "raw_energy_consumed_wh": np.asarray(raw.last_energy_consumed_wh).copy(),
                        "raw_charger_input_wh": np.asarray(raw.last_energy_charged_wh).copy(),
                        "raw_native_clipped_positive_net_charge_wh": np.asarray(raw.last_net_energy_charged_wh).copy(),
                        "raw_reward_info_metrics": np.asarray([
                            info["reward_info"].get(field, np.nan) for field in TRACE_FIELDS]),
                    }
                    record(step, lane, values)
                    metrics = metric_row(reward, info["reward_info"])
                    ledger = energy_ledger(raw, battery, charging)
                    post_positions = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64)
                    values.update(ledger)
                    values.update(metrics=metrics, pre_position_m=positions[lane].copy(),
                                  post_position_m=post_positions.copy(),
                                  actual_displacement_m=post_positions - positions[lane],
                                  uav_dock_requests=np.asarray(raw.uav_dock_requests).copy(),
                                  uav_target_stations=np.asarray(raw.uav_target_stations).copy(),
                                  valid_diagnostics=True,
                                  next_obs_sha256=np.asarray(_digest(np.asarray(obs, dtype=np.float32)), dtype="S64"),
                                  next_state_sha256=np.asarray(_digest(np.asarray(info["next_state"], dtype=np.float32)), dtype="S64"))
                    record(step, lane, values)
                    positions[lane] = post_positions
                    episode_rows[lane].append({key: np.asarray(values[key]).copy() for key in (
                        "mode_before", "mode", "entry", "exit", "charger_input_wh",
                        "signed_stored_energy_delta_wh", "metrics", "command_changed", "native_reward")})
                    next_obs.append(np.asarray(obs, dtype=np.float32))
                    next_states.append(np.asarray(info["next_state"], dtype=np.float32))
                    rewards.append(float(reward))
                    ending.append((bool(terminated), bool(truncated)))
                    infos.append(info)
                next_obs, next_states = np.asarray(next_obs), np.asarray(next_states)
                next_dones = np.asarray(ending, dtype=bool).any(axis=-1)
                agent.store_transition_batch(
                    current_states, next_states, current_obs, next_obs, proposals,
                    np.asarray(rewards, dtype=np.float32), next_dones, infos_batch=infos,
                    rollout_step_idx=step, step_data=step_data)
                arrays["stored_transition"][step] = True
                collector_obs, collector_states = next_obs.copy(), next_states.copy()
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        summary["counts"]["native_episodes"] += 1
                        summary["training_episodes"].append(_episode_summary(
                            episode_rows[lane], lane=lane, episode=episode_ids[lane],
                            end_kind="terminated" if ending[lane][0] else "truncated",
                            time_step_seconds=float(config.time_step)))
                        episode_rows[lane] = []
                        agent.reset_env_state(lane)
                        obs, info = env.reset(seed=None)
                        collector_obs[lane] = np.asarray(obs, dtype=np.float32)
                        collector_states[lane] = np.asarray(info["state"], dtype=np.float32)
                        positions[lane] = np.asarray(info["state_info"]["uav_positions"], dtype=np.float64)
                        env_steps[lane] = 0
                        episode_ids[lane] += 1
                        modes[lane] = False
                    else:
                        env_steps[lane] += 1
                observations, states, dones = collector_obs, collector_states, next_dones
                completed_rows = step + 1
                if completed_rows % 100 == 0 or completed_rows == spec.rollout_length:
                    notify({"event": "collection", "phase": phase, "steps": completed_rows})
            timings["collection"] += time.perf_counter() - stage
            data = agent.rollout_buffer._get_full_rollout_data()
            if data is None or data["num_actual_steps"] != spec.rollout_length:
                raise RuntimeError("incomplete real rollout storage")
            np.testing.assert_array_equal(data["actions"], arrays["original_action"])
            np.testing.assert_array_equal(data["log_probs"], arrays["action_logprobs"])
            np.testing.assert_array_equal(data["reward_env"], np.broadcast_to(
                arrays["native_reward"].astype(np.float32)[..., None], data["reward_env"].shape))
            for key in ("rewards", "reward_env", "reward_team_disc", "reward_ind_disc", "values", "dones"):
                arrays["stored_" + key] = np.asarray(data[key]).copy()
            stage = time.perf_counter()
            save_phase()
            phase_saved = True
            before_live = _execution_state(agent, observations, states, dones, env_steps, modes)
            before_snapshot = agent.ordinary_high_level_snapshot()
            save_high(f"high_before_update_{phase:02d}", before_snapshot)
            before_parameters, before_optimizer = _module_parameters(agent), optimizer_state_steps(agent)
            timings["artifact"] += time.perf_counter() - stage
            stage = time.perf_counter()
            last_values = _bootstrap_values(agent, states, dones)
            native = agent.update(last_values=last_values, dones=dones,
                                  steps_in_buffer=spec.rollout_length,
                                  last_state=states, last_observations=observations)
            assert_finite(native)
            timings["update"] += time.perf_counter() - stage
            stage = time.perf_counter()
            high = agent.ordinary_high_level_snapshot(final=phase == spec.rollouts)
            save_high(f"high_after_update_{phase:02d}", high)
            audit_path = out / f"boundary_{phase:02d}.npz"
            np.savez_compressed(audit_path, **before_live, last_values=last_values,
                                low_advantages=agent.rollout_buffer.advantages,
                                low_returns=agent.rollout_buffer.returns,
                                gamma=np.asarray(config.gamma), gae_lambda=np.asarray(config.gae_lambda))
            artifact(audit_path)
            summary["phases"].append({
                "phase": phase, "native_update": native,
                "optimizer_before": before_optimizer, "optimizer_after": optimizer_state_steps(agent),
                "parameter_displacement_l2": parameter_displacement(before_parameters, agent),
                "high_counters": high["counters"],
                "consumed_high_records": len(high["consumed_records"]),
                "low_original_phase_rows": spec.lanes * spec.rollout_length * config.n_agents,
                "raw_native_J_by_lane": arrays["native_reward"].sum(axis=0),
                "metrics_sums_by_lane": {field: arrays["metrics"][..., col].sum(axis=0)
                                         for col, field in enumerate(TRACE_FIELDS)},
                "live_lanes_at_boundary": int((~dones).sum()),
            })
            if phase == spec.rollouts:
                summary["final_high_counters"] = high["counters"]
                # The full original decision facts remain in the gzip snapshot.
                summary["final_high_prefixes"] = [{key: row[key] for key in (
                    "lane_id", "episode_id", "decision_id", "duration", "reward_sum",
                    "start_phase_version", "low_policy_versions", "budget_censored")}
                    for row in high["pending_records"]]
            agent.clear_buffers()
            after_live = _execution_state(agent, observations, states, dones, env_steps, modes)
            for key in before_live:
                np.testing.assert_array_equal(before_live[key], after_live[key], err_msg=key)
            after_pending = agent.ordinary_high_level_snapshot()["pending_records"]
            if before_snapshot["pending_records"] != after_pending:
                raise RuntimeError("update/clear changed the live ordinary decision prefix")
            summary["phases"][-1]["live_execution_unchanged_by_update_clear"] = True
            summary["counts"]["phases"] = phase
            timings["artifact"] += time.perf_counter() - stage
            notify({"event": "phase_complete", "phase": phase})
            print(f"B08 arm={arm} phase={phase}/{spec.rollouts}", flush=True)
        for lane, rows in enumerate(episode_rows):
            if rows:
                summary["training_episodes"].append(_episode_summary(
                    rows, lane=lane, episode=episode_ids[lane], end_kind="budget",
                    time_step_seconds=float(config.time_step)))
        steps, movement = optimizer_steps(agent), parameter_displacement(initial_parameters, agent)
        if summary["counts"]["transitions"] != spec.transitions:
            raise RuntimeError("actual training exposure differs from contract")
        if any(value <= 0 for value in steps.values()) or any(value <= 0 for value in movement.values()):
            raise RuntimeError("a native learner did not update/move")
        prefixes = summary["final_high_prefixes"]
        if len(prefixes) > spec.lanes or sum(row["duration"] for row in prefixes) > spec.lanes * (config.k - 1):
            raise RuntimeError("final high censoring exceeds the fixed finite bound")
        if summary["final_high_counters"]["cross_version_completions"] > spec.lanes * (spec.rollouts - 1):
            raise RuntimeError("cross-version high segment count exceeds collection-boundary bound")
        episodes = summary["training_episodes"]
        summary.update(
            status="COMPLETE", optimizer_steps=steps, initialization_displacement_l2=movement,
            training_opportunity_aggregate=aggregate_opportunity_summaries([r["opportunity"] for r in episodes]),
            training_exposure={key: sum(row[key] for row in episodes) for key in (
                "actor_proposal_uav_steps", "feedback_passed_proposal_uav_steps",
                "feedback_mapped_command_uav_steps", "anchor_window_all_member_passed_proposal_uav_steps",
                "anchor_window_selected_member_passed_proposal_uav_steps",
                "anchor_window_actual_joint_transitions")})
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc),
                              "phase": phase, "fully_stored_rows_in_phase": completed_rows}
        if phase and arrays:
            if not phase_saved:
                save_phase(partial=True)
            save_high(f"high_partial_{phase:02d}", agent.ordinary_high_level_snapshot())
        raise
    finally:
        for env in envs:
            env.close()
        summary.update(wall_seconds=time.perf_counter() - started, stage_wall_seconds=timings,
                       peak_rss_kib=int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                       rss_scope="runner process high-water mark")
        notify({"event": "training_exit", "status": summary["status"]})
