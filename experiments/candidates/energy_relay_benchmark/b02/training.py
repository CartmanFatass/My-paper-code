"""B02 SET training: B09's collector semantics with minimal persistence and checkpoints.

``b09/training.py::train_arm`` cannot be called for the SET agent: it requires
``config.ordinary_completed_segments`` (which ``HMASDAgent`` refuses together with the mappo
switch's ``disable_high_level_training``), calls ``agent.ordinary_high_level_snapshot`` (which
raises when that path is off) and finally requires every one of the five learners to have
stepped and moved (the high-level coordinator and both discriminators never step under mappo).
``collect_and_train`` therefore copies its transition/update body -- b09/training.py lines
153-159 (lane envs and seeded resets), 167-178 (``agent.step`` batched route, sampled), 184-193
(feedback on the submitted command only), 247-250 (``store_transition_batch`` with the
proposals), 252-270 (lane reset after a native ending), 276-283 (buffer checks), 294-297
(bootstrap + ``update``) and 328 (``clear_buffers``) -- in the same order.  Dropped: the
per-phase npz, high-level snapshots, boundary npz, per-episode raw JSON, energy ledger and
observation digests (read-only diagnostics; ~670 MB per 30 rollouts in B09).  The collector's
contract is unchanged: a proposal is the stored likelihood action; only the submitted command
is mapped by F; the original native transition supplies every reward and next input.  Parity
with ``train_arm`` on an ordinary HMASD config is pinned by test.
"""

from __future__ import annotations

import json
import resource
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _bootstrap_values, active_config, initialization_fingerprint, make_env, optimizer_steps,
    seed_everything, sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b03.native import assert_finite
from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS, metric_row
from experiments.candidates.uav_service_auxiliary.b06.feedback import (
    PRODUCTION_LAYOUT, apply_feedback,
)
from experiments.candidates.uav_service_auxiliary.b09.persistence import (
    append_progress, write_summary,
)
from hmasd.agent import HMASDAgent

from ..b01.feedback import PRODUCTION_PARAMS
from .configuration import (
    CHECKPOINT_RULE, OBJECT_ID, PROGRAMME, RECIPE_NOTES, B02Spec, actor_input_width,
    checkpoint_rollouts, config_dict, make_b02_config, spec_record,
)

QOS = TRACE_FIELDS.index("qos_satisfaction_ratio")
# The B06 layout pins the margins; B01's PRODUCTION_PARAMS names the same pair.
if (PRODUCTION_LAYOUT.enter_margin, PRODUCTION_LAYOUT.exit_margin) != (
        PRODUCTION_PARAMS.enter_margin, PRODUCTION_PARAMS.exit_margin):
    raise RuntimeError("B06 production layout and B01 PRODUCTION_PARAMS disagree")
# Update statistics ``HMASDAgent.update`` returns for the low-level PPO learner.  Approximate
# KL and clip fraction are computed inside ``update_discoverer_from_rollout`` and discarded.
PPO_UPDATE_KEYS = ("action_entropy", "discoverer_policy_loss", "discoverer_value_loss",
                   "discoverer_loss", "avg_discoverer_val", "discoverer_actor_lr",
                   "discoverer_critic_lr")
PPO_NOT_EXPOSED = ("approx_kl", "clip_fraction")


def _scalar_update(native: dict[str, Any]) -> dict[str, Any]:
    return {key: float(value) for key, value in native.items()
            if isinstance(value, (int, float, np.integer, np.floating))
            and not isinstance(value, bool)}


def collect_and_train(agent, config, spec: B02Spec, *, feedback: bool = True,
                      after_rollout: Callable[[int, dict[str, Any]], None] | None = None,
                      observe_step: Callable[[Any, dict[str, Any], int], None] | None = None,
                      ) -> dict[str, Any]:
    """Collect ``spec.rollouts`` rollouts of ``spec.lanes x spec.rollout_length`` and update after each.

    ``after_rollout(rollout, record)`` runs after ``update`` and ``clear_buffers`` of each
    rollout (checkpoint point).  ``observe_step(agent, step_data, step)`` runs right after each
    ``agent.step`` (tests).  Neither may draw random numbers.
    """
    if config.num_envs != spec.lanes or config.rollout_length != spec.rollout_length:
        raise ValueError("collector and learner dimensions differ")
    n_agents = int(config.n_agents)
    result: dict[str, Any] = {"counts": {"transitions": 0, "rollouts": 0, "native_episodes": 0},
                              "rollouts": [], "wall": {"collection": 0.0, "update": 0.0}}
    envs = []
    try:
        for lane in range(spec.lanes):
            envs.append(make_env(config, spec.seed + lane))
        resets = [env.reset(seed=spec.seed + lane) for lane, env in enumerate(envs)]
        observations = np.asarray([row[0] for row in resets], dtype=np.float32)
        states = np.asarray([row[1]["state"] for row in resets], dtype=np.float32)
        dones = np.ones(spec.lanes, dtype=bool)
        env_steps = np.zeros(spec.lanes, dtype=np.int64)
        episode_ids = np.zeros(spec.lanes, dtype=np.int64)
        modes = np.zeros((spec.lanes, n_agents), dtype=bool)
        episode = [dict(J=0.0, qos=0.0, steps=0, mode=0, mapped=0) for _ in envs]
        for rollout in range(1, spec.rollouts + 1):
            shape = (spec.rollout_length, spec.lanes)
            proposals_seen = np.zeros((*shape, n_agents, int(config.action_dim)), dtype=np.float32)
            logprobs_seen = None
            rewards_seen = np.zeros(shape, dtype=np.float32)
            lane_J = np.zeros(spec.lanes)
            lane_qos = np.zeros(spec.lanes)
            mapped = mode_steps = entries = exits = 0
            completed: list[dict[str, Any]] = []
            stage = time.perf_counter()
            for step in range(spec.rollout_length):
                current_obs, current_states = observations.copy(), states.copy()
                proposals, _, step_data = agent.step(
                    current_states, current_obs, env_steps, dones, deterministic=False,
                    return_step_data=True, build_infos=False)
                proposals = np.asarray(proposals, dtype=np.float32).copy()
                if observe_step is not None:
                    observe_step(agent, step_data, step)
                logprobs = np.asarray(step_data["action_logprobs"], dtype=np.float32)
                if logprobs_seen is None:
                    logprobs_seen = np.zeros((spec.rollout_length, *logprobs.shape), dtype=np.float32)
                logprobs_seen[step] = logprobs
                proposals_seen[step] = proposals
                next_obs, next_states, infos, rewards, ending = [], [], [], [], []
                for lane, env in enumerate(envs):
                    submitted = proposals[lane].copy()
                    if feedback:
                        decision = apply_feedback(current_obs[lane], proposals[lane], modes[lane])
                        submitted, modes[lane] = decision.submitted_actions, decision.modes
                        entries += int(decision.entered.sum())
                        exits += int(decision.exited.sum())
                    obs, reward, terminated, truncated, info = env.step(submitted)
                    result["counts"]["transitions"] += 1
                    qos = float(metric_row(reward, info["reward_info"])[QOS])
                    changed = int(np.any(submitted != proposals[lane], axis=-1).sum())
                    in_mode = int(modes[lane].sum())
                    rewards_seen[step, lane] = float(reward)
                    lane_J[lane] += float(reward)
                    lane_qos[lane] += qos
                    mapped += changed
                    mode_steps += in_mode
                    for key, value in (("J", float(reward)), ("qos", qos), ("steps", 1),
                                       ("mode", in_mode), ("mapped", changed)):
                        episode[lane][key] += value
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
                collector_obs, collector_states = next_obs.copy(), next_states.copy()
                for lane, env in enumerate(envs):
                    if next_dones[lane]:
                        row = episode[lane]
                        completed.append({
                            "lane": lane, "episode": int(episode_ids[lane]),
                            "end_kind": "terminated" if ending[lane][0] else "truncated",
                            "length": int(row["steps"]), "native_J": row["J"],
                            "qos_per_step": row["qos"] / row["steps"],
                            "J_per_step": row["J"] / row["steps"],
                            "f_mode_uav_step_share": row["mode"] / (row["steps"] * n_agents),
                            "shield_mapping_share": row["mapped"] / (row["steps"] * n_agents)})
                        episode[lane] = dict(J=0.0, qos=0.0, steps=0, mode=0, mapped=0)
                        result["counts"]["native_episodes"] += 1
                        agent.reset_env_state(lane)
                        obs, info = env.reset(seed=None)
                        collector_obs[lane] = np.asarray(obs, dtype=np.float32)
                        collector_states[lane] = np.asarray(info["state"], dtype=np.float32)
                        env_steps[lane] = 0
                        episode_ids[lane] += 1
                        modes[lane] = False
                    else:
                        env_steps[lane] += 1
                observations, states, dones = collector_obs, collector_states, next_dones
            collection_s = time.perf_counter() - stage
            data = agent.rollout_buffer._get_full_rollout_data()
            if data is None or data["num_actual_steps"] != spec.rollout_length:
                raise RuntimeError("incomplete real rollout storage")
            np.testing.assert_array_equal(data["actions"], proposals_seen)
            np.testing.assert_array_equal(data["log_probs"], logprobs_seen)
            np.testing.assert_array_equal(data["reward_env"], np.broadcast_to(
                rewards_seen[..., None], data["reward_env"].shape))
            stage = time.perf_counter()
            last_values = _bootstrap_values(agent, states, dones)
            native = agent.update(last_values=last_values, dones=dones,
                                  steps_in_buffer=spec.rollout_length,
                                  last_state=states, last_observations=observations)
            assert_finite(native)
            live = np.flatnonzero(~dones)
            timers_before = {int(lane): agent.env_timers.get(int(lane)) for lane in live}
            agent.clear_buffers()
            timers_after = {int(lane): agent.env_timers.get(int(lane)) for lane in live}
            update_s = time.perf_counter() - stage
            result["wall"]["collection"] += collection_s
            result["wall"]["update"] += update_s
            submitted_commands = spec.rollout_length * spec.lanes * n_agents
            update = _scalar_update(native)
            record = {
                "rollout": rollout, "transitions": result["counts"]["transitions"],
                "rollout_transitions": spec.rollout_length * spec.lanes,
                "lane_native_J": lane_J.tolist(),
                "lane_qos_per_step": (lane_qos / spec.rollout_length).tolist(),
                "episodes_completed": completed,
                "submitted_commands": submitted_commands,
                "f_mapped_commands": mapped,
                "shield_mapping_share": mapped / submitted_commands,
                "f_mode_uav_steps": mode_steps,
                "f_mode_uav_step_share": mode_steps / submitted_commands,
                "shield_entries": entries, "shield_exits": exits,
                "optimizer_steps": optimizer_steps(agent),
                "ppo": {key: update.get(key) for key in PPO_UPDATE_KEYS}
                       | {key: None for key in PPO_NOT_EXPOSED},
                "native_update": update,
                "live_lanes_at_boundary": int(live.size),
                "live_lane_timers_reset_by_clear": int(sum(
                    timers_before[lane] != timers_after[lane] for lane in timers_before)),
                "collection_seconds": collection_s, "update_seconds": update_s,
            }
            result["rollouts"].append(record)
            result["counts"]["rollouts"] = rollout
            if after_rollout is not None:
                after_rollout(rollout, record)
        if result["counts"]["transitions"] != spec.transitions:
            raise RuntimeError("actual training exposure differs from contract")
        return result
    finally:
        for env in envs:
            env.close()


def new_agent(config, *, device: torch.device, log_dir: Path, seed: int):
    """``seed_everything(seed)`` then ``HMASDAgent(config)``, as b08 ``new_initialized_agent``.

    b08's ``initialization_identity`` hashes all four modules and fails on the discriminators
    the mappo switch leaves as None; the identity here is B01's parameter fingerprint (None
    modules skipped) plus the rollout sampler state.
    """
    seed_everything(int(seed), device)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=device)
    return agent, {"policy_fingerprint": initialization_fingerprint(agent),
                   "rollout_sampler_state": agent.rollout_buffer.get_sampler_rng_state()}


def save_checkpoint(agent, config, spec: B02Spec, out: Path, index: int, *, rollout: int,
                    transitions: int, started: float, launch_sha: str) -> dict[str, Any]:
    """``checkpoints/c{ii}/agent.pt`` (``HMASDAgent.save_model``, as B09 wrote N/endpoint) + record.json.

    No random draw: ``save_model`` serialises state dicts (and reads the sampler RNG state);
    the digests below read tensors and bytes only.
    """
    root = Path(out) / "checkpoints" / f"c{index:02d}"
    if root.exists():
        raise FileExistsError(f"checkpoint already exists: {root}")
    root.mkdir(parents=True)
    path = root / "agent.pt"
    agent.save_model(path)
    record = {
        "object_id": OBJECT_ID, "programme": PROGRAMME, "launch_sha": launch_sha,
        "checkpoint": f"c{index:02d}", "rollout": int(rollout), "transitions": int(transitions),
        "optimizer_steps": optimizer_steps(agent),
        "wall_seconds": time.perf_counter() - started,
        "agent_pt": "agent.pt", "agent_pt_sha256": sha256_file(path),
        "agent_pt_bytes": path.stat().st_size,
        "policy_fingerprint": initialization_fingerprint(agent),
        "training_seed": int(spec.seed), "config": config_dict(config),
    }
    write_summary(root / "record.json", record)
    return record


def run_training(*, out: Path, launch_sha: str, spec: B02Spec, device_name: str = "cuda",
                 threads: int = 4, argv=None) -> dict[str, Any]:
    """One SET fit: config.json, c00, 200 rollouts with checkpoints, summary.json, progress.jsonl."""
    out = Path(out)
    if any((out / name).exists() for name in ("summary.json", "config.json", "progress.jsonl",
                                              "checkpoints")):
        raise FileExistsError(f"B02 training output already exists: {out}")
    config = make_b02_config(spec)
    device = torch.device(device_name)
    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("B02 CUDA was requested but is unavailable")
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(int(threads))
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError("B02 requires Torch FP32 default dtype")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    cpu_start = resource.getrusage(resource.RUSAGE_SELF)
    schedule = checkpoint_rollouts(spec)
    write_summary(out / "config.json", {
        "object_id": OBJECT_ID, "programme": PROGRAMME, "launch_sha": launch_sha,
        "argv": list(sys.argv if argv is None else argv), "device": str(device),
        "torch_threads": int(threads), "seed": int(spec.seed), "spec": spec_record(spec),
        "config": config_dict(config), "active": json.loads(json.dumps(active_config(config)), parse_constant=str),
        "recipe_notes": RECIPE_NOTES, "checkpoint_rule": CHECKPOINT_RULE,
        "training_feedback": {"layout": asdict(PRODUCTION_LAYOUT),
                              "params": asdict(PRODUCTION_PARAMS)},
        "actor_input_width": actor_input_width(config),
        "ppo_update_keys": list(PPO_UPDATE_KEYS), "ppo_not_exposed": list(PPO_NOT_EXPOSED),
    })
    summary: dict[str, Any] = {
        "object_id": OBJECT_ID, "programme": PROGRAMME, "status": "INCOMPLETE", "failure": None,
        "launch_sha": launch_sha, "seed": int(spec.seed), "device": str(device),
        "torch_threads": int(threads),
        "counts": {"transitions": 0, "rollouts": 0, "native_episodes": 0, "checkpoints": 0},
        "checkpoint_rollouts": list(schedule), "rollouts": [], "checkpoints": {},
        "artifacts": {"config.json": sha256_file(out / "config.json")},
    }
    write_summary(out / "summary.json", summary)

    def checkpoint(agent, index, rollout, transitions):
        record = save_checkpoint(agent, config, spec, out, index, rollout=rollout,
                                 transitions=transitions, started=started, launch_sha=launch_sha)
        summary["checkpoints"][record["checkpoint"]] = {
            key: record[key] for key in ("rollout", "transitions", "optimizer_steps",
                                         "wall_seconds", "agent_pt_sha256", "policy_fingerprint")}
        summary["counts"]["checkpoints"] += 1
        append_progress(out, {"event": "checkpoint", **summary["checkpoints"][record["checkpoint"]],
                              "checkpoint": record["checkpoint"]}, dict(summary["counts"]))

    try:
        agent, identity = new_agent(config, device=device, log_dir=out / "logs", seed=spec.seed)
        summary["initialization"] = identity
        width = int(agent.skill_discoverer.central_input_dim) + int(config.obs_dim)
        if width != actor_input_width(config):
            raise RuntimeError(f"flag-on actor input width {width} != {actor_input_width(config)}")
        summary["actor_input_width"] = width
        checkpoint(agent, 0, 0, 0)
        write_summary(out / "summary.json", summary)

        def after_rollout(rollout, record):
            summary["rollouts"].append(record)
            summary["counts"].update(transitions=record["transitions"], rollouts=rollout,
                                     native_episodes=summary["counts"]["native_episodes"]
                                     + len(record["episodes_completed"]))
            append_progress(out, {"event": "rollout", **record}, dict(summary["counts"]))
            if rollout in schedule:
                checkpoint(agent, schedule.index(rollout) + 1, rollout, record["transitions"])
            write_summary(out / "summary.json", summary)
            print(f"B02 rollout {rollout}/{spec.rollouts} transitions={record['transitions']}",
                  flush=True)

        result = collect_and_train(agent, config, spec, feedback=True, after_rollout=after_rollout)
        if summary["counts"]["checkpoints"] != len(schedule) + 1:
            raise RuntimeError("checkpoint count differs from the schedule")
        steps = optimizer_steps(agent)
        if steps["low_actor"] <= 0 or steps["low_critic"] <= 0:
            raise RuntimeError("the low-level learner did not update")
        summary.update(status="COMPLETE", optimizer_steps=steps, collector_wall=result["wall"])
        return summary
    except Exception as exc:
        summary["failure"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        wall = time.perf_counter() - started
        summary.update(
            wall_seconds=wall, cpu_user_seconds=usage.ru_utime - cpu_start.ru_utime,
            cpu_system_seconds=usage.ru_stime - cpu_start.ru_stime,
            peak_rss_kib=int(usage.ru_maxrss), rss_scope="runner process high-water mark",
            seconds_per_transition=(wall / summary["counts"]["transitions"]
                                    if summary["counts"]["transitions"] else None))
        write_summary(out / "summary.json", summary)
        append_progress(out, {"event": "training_exit", "status": summary["status"]},
                        dict(summary["counts"]))
