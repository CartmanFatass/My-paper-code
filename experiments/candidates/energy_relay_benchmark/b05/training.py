"""B training of ``b05_canonical_frame_a01``: the frozen B02 SET recipe under the SW canonical frame.

``collect_and_train_canonical`` is ``b02/training.py::collect_and_train`` with the episode-level
frame threaded through; ``B05Spec.canonical`` selects it ("sw") or the unchanged B02 function
("off", called directly, so the plain path is B02's code object).  The loop keeps two copies of
every lane input:

* physical (as the env returned them): the shield ``apply_feedback(obs_phys, a_phys, modes)``,
  ``env.step(submitted_phys)``, the mapped-command count and every reward/metric;
* canonical (``frame.canonical_inputs`` with the lane's frame): ``agent.step`` (current own and
  joint observations, the state, and through them the k = 10 held central snapshot the agent
  builds from what it is fed), ``store_transition_batch`` (states, next states, observations,
  next observations, the canonical proposals; log-probabilities/values come from
  ``step_data``), ``_bootstrap_values`` and ``agent.update(last_state, last_observations)``.

A lane's frame is chosen by ``sw_frame`` from the physical reset observation (initial reset and
every reset after a native ending), before that observation is transformed, and held to the
episode end; the terminal next observation of an ending episode is transformed with the ending
episode's frame.  ``infos_batch`` stays physical: in this recipe the agent reads it only through
``_extract_reward_info`` for process segments, which ``use_process_exploration = False`` disables
(hmasd/agent.py 4288-4292, 1937-1941).

``run_training`` is ``b02/training.py::run_training`` (config.json, c00 before any collection,
checkpoints at the recipe's marks, summary, progress, resume) with ``b05_recipe()`` and this
collector in place of B02's (``mock.patch.object`` on the module global it calls, as b04 routes
``make_env``), plus ``manifest.json``.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from unittest import mock

import numpy as np

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _bootstrap_values, make_env, optimizer_steps, sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b03.native import assert_finite
from experiments.candidates.uav_service_auxiliary.b04.evaluation import metric_row
from experiments.candidates.uav_service_auxiliary.b06.feedback import apply_feedback
from experiments.candidates.uav_service_auxiliary.b09.persistence import write_summary

from ..b02 import training as b02_training
from ..b02.configuration import (
    OBJECT_ID as B02_OBJECT_ID, PROGRAMME as B02_PROGRAMME, RECIPE_NOTES as B02_RECIPE_NOTES,
    TRAINING_SEEDS, B02Spec, actor_input_width, assert_production, config_dict,
    make_b02_config,
)
from ..b02.training import (
    PPO_NOT_EXPOSED, PPO_UPDATE_KEYS, QOS, Recipe, _scalar_update,
    collect_and_train as plain_collect_and_train,
)
from .frame import (
    ROOT, adapter_record, canonical_inputs, canonical_observations, canonical_state,
    physical_actions, sw_frame,
)

OBJECT_ID = "ENERGY-RELAY-BENCHMARK-B05"
PROGRAMME = "SET-shield-on-1.2M-canonical-sw"
FRAME_RULES: dict[str, Callable[[Any], Any] | None] = {"sw": sw_frame, "off": None}


@dataclass(frozen=True)
class B05Spec(B02Spec):
    """``B02Spec`` plus the wrapper flag: "sw" (B) or "off" (B02's collector unchanged)."""
    canonical: str = "sw"


def production_spec(seed: int) -> B05Spec:
    """The frozen B02 production exposure (``assert_production``) with the SW wrapper on."""
    if int(seed) not in TRAINING_SEEDS:
        raise ValueError(f"unplanned B05 training seed {seed}; declared {TRAINING_SEEDS}")
    spec = B05Spec(seed=int(seed), canonical="sw")
    assert_production(spec)
    return spec


def frame_rule_of(spec) -> Callable[[Any], Any] | None:
    name = getattr(spec, "canonical", "off")
    if name not in FRAME_RULES:
        raise ValueError(f"unknown canonical flag {name!r}; expected one of {sorted(FRAME_RULES)}")
    return FRAME_RULES[name]


def collect_and_train_canonical(agent, config, spec: B02Spec, *, feedback: bool = True,
                                after_rollout: Callable[[int, dict[str, Any]], None] | None = None,
                                observe_step: Callable[[Any, dict[str, Any], int], None] | None = None,
                                start_rollout: int = 0, start_transitions: int = 0,
                                env_seed: int | None = None,
                                record_hook: Callable[[int], dict[str, Any]] | None = None,
                                frame_rule: Callable[[Any], Any] | None = None) -> dict[str, Any]:
    """B02's ``collect_and_train`` with the lane frame (arguments and contract as B02's).

    ``frame_rule`` (default: from ``spec.canonical``) maps a physical reset observation to a G4
    element; with ``spec.canonical == "off"`` and no ``frame_rule`` the call is B02's function.
    Additions to B02's records: each ``episodes_completed`` row carries its ``frame``; each rollout
    record lists ``frames_chosen`` (lane, lane-episode index, element, rollout step of the reset;
    None for the run's initial resets, listed in its first rollout) for the resets made while
    collecting that rollout, and ``lane_frames_at_boundary``.
    """
    rule = frame_rule if frame_rule is not None else frame_rule_of(spec)
    if rule is None:
        return plain_collect_and_train(
            agent, config, spec, feedback=feedback, after_rollout=after_rollout,
            observe_step=observe_step, start_rollout=start_rollout,
            start_transitions=start_transitions, env_seed=env_seed, record_hook=record_hook)
    if config.num_envs != spec.lanes or config.rollout_length != spec.rollout_length:
        raise ValueError("collector and learner dimensions differ")
    if not 0 <= int(start_rollout) < spec.rollouts:
        raise ValueError(f"start_rollout {start_rollout} outside [0, {spec.rollouts})")
    if int(start_transitions) < 0:
        raise ValueError(f"start_transitions {start_transitions} is negative")
    seed = spec.seed if env_seed is None else int(env_seed)
    n_agents = int(config.n_agents)
    result: dict[str, Any] = {"counts": {"transitions": int(start_transitions), "rollouts": 0,
                                         "native_episodes": 0},
                              "rollouts": [], "wall": {"collection": 0.0, "update": 0.0}}
    envs = []
    try:
        for lane in range(spec.lanes):
            envs.append(make_env(config, seed + lane))
        resets = [env.reset(seed=seed + lane) for lane, env in enumerate(envs)]
        # Physical inputs as the env returned them (every physical consumer reads these).
        physical_obs = np.asarray([row[0] for row in resets], dtype=np.float32)
        physical_states = np.asarray([row[1]["state"] for row in resets], dtype=np.float32)
        frames = [rule(physical_obs[lane]) for lane in range(spec.lanes)]
        initial_frames = [{"lane": lane, "episode": 0, "frame": frames[lane].name, "step": None}
                          for lane in range(spec.lanes)]
        # Canonical inputs (every agent consumer reads these).
        observations = np.empty_like(physical_obs)
        states = np.empty_like(physical_states)
        for lane in range(spec.lanes):
            observations[lane], states[lane] = canonical_inputs(
                physical_obs[lane], physical_states[lane], frames[lane])
        dones = np.ones(spec.lanes, dtype=bool)
        env_steps = np.zeros(spec.lanes, dtype=np.int64)
        episode_ids = np.zeros(spec.lanes, dtype=np.int64)
        modes = np.zeros((spec.lanes, n_agents), dtype=bool)
        episode = [dict(J=0.0, qos=0.0, steps=0, mode=0, mapped=0) for _ in envs]
        for rollout in range(int(start_rollout) + 1, spec.rollouts + 1):
            shape = (spec.rollout_length, spec.lanes)
            proposals_seen = np.zeros((*shape, n_agents, int(config.action_dim)), dtype=np.float32)
            logprobs_seen = None
            rewards_seen = np.zeros(shape, dtype=np.float32)
            lane_J = np.zeros(spec.lanes)
            lane_qos = np.zeros(spec.lanes)
            mapped = mode_steps = entries = exits = 0
            completed: list[dict[str, Any]] = []
            frames_chosen, initial_frames = initial_frames, []
            stage = time.perf_counter()
            for step in range(spec.rollout_length):
                current_obs, current_states = observations.copy(), states.copy()
                current_physical_obs = physical_obs.copy()
                proposals, _, step_data = agent.step(
                    current_states, current_obs, env_steps, dones, deterministic=False,
                    return_step_data=True, build_infos=False)
                proposals = np.asarray(proposals, dtype=np.float32).copy()   # canonical
                if observe_step is not None:
                    observe_step(agent, step_data, step)
                logprobs = np.asarray(step_data["action_logprobs"], dtype=np.float32)
                if logprobs_seen is None:
                    logprobs_seen = np.zeros((spec.rollout_length, *logprobs.shape), dtype=np.float32)
                logprobs_seen[step] = logprobs
                proposals_seen[step] = proposals
                next_obs, next_states, infos, rewards, ending = [], [], [], [], []
                next_physical_obs, next_physical_states = [], []
                for lane, env in enumerate(envs):
                    proposal = physical_actions(proposals[lane], frames[lane])
                    submitted = proposal.copy()
                    if feedback:
                        decision = apply_feedback(current_physical_obs[lane], proposal, modes[lane])
                        submitted, modes[lane] = decision.submitted_actions, decision.modes
                        entries += int(decision.entered.sum())
                        exits += int(decision.exited.sum())
                    obs, reward, terminated, truncated, info = env.step(submitted)
                    result["counts"]["transitions"] += 1
                    qos = float(metric_row(reward, info["reward_info"])[QOS])
                    changed = int(np.any(submitted != proposal, axis=-1).sum())
                    in_mode = int(modes[lane].sum())
                    rewards_seen[step, lane] = float(reward)
                    lane_J[lane] += float(reward)
                    lane_qos[lane] += qos
                    mapped += changed
                    mode_steps += in_mode
                    for key, value in (("J", float(reward)), ("qos", qos), ("steps", 1),
                                       ("mode", in_mode), ("mapped", changed)):
                        episode[lane][key] += value
                    obs = np.asarray(obs, dtype=np.float32)
                    next_state = np.asarray(info["next_state"], dtype=np.float32)
                    next_physical_obs.append(obs)
                    next_physical_states.append(next_state)
                    # The episode's own frame, also for its terminal next observation.
                    next_obs.append(canonical_observations(obs, frames[lane]))
                    next_states.append(canonical_state(next_state, frames[lane]))
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
                collector_physical_obs = np.asarray(next_physical_obs)
                collector_physical_states = np.asarray(next_physical_states)
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
                            "shield_mapping_share": row["mapped"] / (row["steps"] * n_agents),
                            "frame": frames[lane].name})
                        episode[lane] = dict(J=0.0, qos=0.0, steps=0, mode=0, mapped=0)
                        result["counts"]["native_episodes"] += 1
                        agent.reset_env_state(lane)
                        obs, info = env.reset(seed=None)
                        obs = np.asarray(obs, dtype=np.float32)
                        state = np.asarray(info["state"], dtype=np.float32)
                        frames[lane] = rule(obs)   # chosen before the new episode is transformed
                        collector_physical_obs[lane], collector_physical_states[lane] = obs, state
                        collector_obs[lane], collector_states[lane] = canonical_inputs(
                            obs, state, frames[lane])
                        env_steps[lane] = 0
                        episode_ids[lane] += 1
                        modes[lane] = False
                        frames_chosen.append({"lane": lane, "episode": int(episode_ids[lane]),
                                              "frame": frames[lane].name, "step": step})
                    else:
                        env_steps[lane] += 1
                observations, states, dones = collector_obs, collector_states, next_dones
                physical_obs, physical_states = collector_physical_obs, collector_physical_states
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
                "frames_chosen": frames_chosen,
                "lane_frames_at_boundary": [frame.name for frame in frames],
            }
            if record_hook is not None:
                extra = record_hook(rollout)
                if set(extra) & set(record):
                    raise RuntimeError(f"record_hook overwrites {sorted(set(extra) & set(record))}")
                record.update(extra)
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


def b05_recipe() -> Recipe:
    """B02's SET recipe (config, construction, checkpoint rule) with B05's labels and frame record."""
    frame = adapter_record()
    return Recipe(
        object_id=OBJECT_ID, programme=PROGRAMME, make_config=make_b02_config,
        config_dict=config_dict, actor_input_width=actor_input_width,
        recipe_notes={**B02_RECIPE_NOTES,
                      "canonical_frame": ("episode-level SW spawn-corner G4 wrapper in the "
                                          "collector (b05/training.py); recipe otherwise B02's")},
        label="B05",
        record_fields={"canonical_frame": frame,
                       "base_recipe": {"object_id": B02_OBJECT_ID, "programme": B02_PROGRAMME}})


def run_training(*, out: Path, launch_sha: str, spec: B05Spec, device_name: str = "cuda",
                 threads: int = 4, argv=None, resume_from: Path | None = None,
                 resume_source_sha: str | None = None) -> dict[str, Any]:
    """B02 ``run_training`` with ``b05_recipe()`` and ``collect_and_train_canonical``; manifest.json."""
    if not isinstance(spec, B05Spec):
        raise TypeError("B05 run_training needs a B05Spec (the canonical flag)")
    frame_rule_of(spec)
    out = Path(out)
    existing = [name for name in ("summary.json", "config.json", "progress.jsonl", "checkpoints",
                                  "manifest.json") if (out / name).exists()]
    if existing:
        raise FileExistsError(f"B05 training output already exists: {out} ({existing})")
    summary: dict[str, Any] | None = None
    failure = None
    try:
        with mock.patch.object(b02_training, "collect_and_train", collect_and_train_canonical):
            summary = b02_training.run_training(
                out=out, launch_sha=launch_sha, spec=spec, device_name=device_name,
                threads=threads, argv=argv, resume_from=resume_from,
                resume_source_sha=resume_source_sha, recipe=b05_recipe())
        return summary
    except Exception as exc:
        failure = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        if (out / "summary.json").exists():
            write_manifest(out, kind="training", launch_sha=launch_sha, argv=argv,
                           extra={"canonical": spec.canonical, "failure": failure})


def write_manifest(out: Path, *, kind: str, launch_sha: str, argv=None,
                   data_root: Path | None = None, extra: dict[str, Any] | None = None) -> dict:
    """``manifest.json``: frame rule + adapter sha256, code/data roots, sha256 of every file under
    ``out`` (checkpoints included) except the manifest and launcher-owned records."""
    import subprocess
    import sys

    out = Path(out)
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:   # pragma: no cover
        head = None
    launcher_owned = {"launch-manifest.json", "launch-status.json", "admission-preflight.json",
                      "process-exit.json", "stderr.log", "stdout.log", "manifest.json"}
    files = sorted(path for path in out.rglob("*") if path.is_file()
                   and path.relative_to(out).as_posix() not in launcher_owned
                   and "logs" not in path.relative_to(out).parts)
    checkpoints = {}
    for record_path in sorted(out.glob("checkpoints/c*/record.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        checkpoints[record_path.parent.name] = {
            "agent_pt_sha256": record.get("agent_pt_sha256"),
            "policy_fingerprint": record.get("policy_fingerprint"),
            "rollout": record.get("rollout"), "transitions": record.get("transitions")}
    manifest = {
        "object_id": OBJECT_ID, "programme": PROGRAMME, "kind": kind, "launch_sha": launch_sha,
        "git_head": head, "argv": list(sys.argv if argv is None else argv),
        "code_root": str(ROOT), "data_root": str(ROOT if data_root is None else data_root),
        "canonical_frame": adapter_record(), "checkpoints": checkpoints,
        "artifacts": {path.relative_to(out).as_posix(): {"sha256": sha256_file(path),
                                                         "bytes": path.stat().st_size}
                      for path in files},
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **(extra or {})}
    write_summary(out / "manifest.json", manifest)
    return manifest
