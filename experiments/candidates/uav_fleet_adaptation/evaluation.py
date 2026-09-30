"""Fixed final N8 evaluation under the inherited old-mask motion-then-E contract."""
from __future__ import annotations

from dataclasses import dataclass
import gzip
import json
from pathlib import Path
import time

import numpy as np
import torch

from experiments.candidates.uav_fleet_transmission.control import (
    OrdinaryController, choose_mask, decode_public_state, predict_next,
)
from experiments.candidates.uav_fleet_transmission.host import mask_bits
from experiments.candidates.uav_fleet_transmission.study import (
    artifact, frozen, metrics,
)
from .host import EVAL_WORLD_IDS, make_env, runtime_seed

ARMS = ("I_E", "A_E", "F_E", "C_E")
COUNT_KEYS = ("requested_candidates", "scored_candidates", "cached_candidates",
              "geometry_rows_computed", "geometry_rows_reused")


@dataclass(frozen=True)
class EvalSpec:
    world_ids: tuple[int, ...] = EVAL_WORLD_IDS
    horizon: int = 500
    cadence: int = 10
    bootstrap_seed: int = 26093017
    bootstrap_replicates: int = 10000


def evaluate_episode(arm: str, world_id: int, agent, out: Path,
                     spec: EvalSpec = EvalSpec()) -> dict:
    """The native object is used only by the executor and evidence recorder."""
    if arm not in ARMS or (agent is None) != (arm == "C_E"):
        raise ValueError("fixed endpoint/agent mismatch")
    wall, cpu = time.perf_counter(), time.process_time()
    n = 8
    env = make_env(world_id, spec.horizon)
    native = env.env.env
    seed = runtime_seed(world_id)
    frozen.seed_rng(seed)
    if agent is not None:
        agent.reset_env_state(0)
    obs, info = env.reset(seed=seed)
    state = np.asarray(info["state"])
    old_mask = 255
    ordinary = OrdinaryController(n) if arm == "C_E" else None
    raw = {key: [] for key in (
        "positions", "observations", "states", "sinr", "connections", "peer_sinr",
        "visible_users", "visible_peers", "raw_actions", "actions", "action_logprobs",
        "mask", "scalar_reward", "components", "terminal", "runtime_after_action")}
    decisions = []
    timing = {key: 0. for key in (
        "actor_cpu_seconds", "motion_cpu_seconds", "mask_cpu_seconds", "native_and_record_cpu_seconds")}
    counts = {"actor_calls": 0, "motion_calls": 0, "mask_calls": 0}
    candidate_counts = {kind: {key: 0 for key in COUNT_KEYS} for kind in ("motion", "mask")}

    def snapshot():
        raw["positions"].append(native.uav_positions.copy())
        raw["observations"].append(np.asarray(obs).copy())
        raw["states"].append(state.copy())
        raw["sinr"].append(native.sinr_matrix.copy())
        raw["connections"].append(native.connections.copy())
        raw["peer_sinr"].append(native.uav_sinr_matrix.copy())
        raw["visible_users"].append([
            len(native._local_user_entries(i)[0][:native.max_observed_users]) for i in range(n)])
        raw["visible_peers"].append([
            len(native._local_uav_entries(i)[0][:native.max_observed_uavs]) for i in range(n)])

    snapshot()
    steps, dones = np.zeros(1, dtype=np.int64), np.zeros(1, dtype=bool)
    try:
        with torch.no_grad():
            for t in range(spec.horizon):
                boundary = t % spec.cadence == 0
                decision = {"t": t, "old_mask": old_mask}
                if agent is not None:
                    start = time.process_time()
                    actions, _, data = agent.step(
                        state[None], np.asarray(obs)[None], steps, dones,
                        deterministic=True, return_step_data=True, build_infos=False)
                    frozen.finite((actions, data), "fleet adaptation endpoint policy output")
                    command = np.clip(actions[0], -1., 1.)
                    raw["raw_actions"].append(actions[0].copy())
                    raw["action_logprobs"].append(np.asarray(data["action_logprobs"])[0].reshape(-1).copy())
                    raw["runtime_after_action"].append(frozen.runtime_state_digest(agent))
                    counts["actor_calls"] += 1
                    timing["actor_cpu_seconds"] += time.process_time() - start
                    if boundary:
                        public_position, public_users = decode_public_state(state, n)
                        predicted = predict_next(public_position, command)
                else:
                    start = time.process_time()
                    command, predicted, trace = ordinary.select(t, state if boundary else None, old_mask)
                    decision["motion"] = trace
                    raw["raw_actions"].append(command.copy())
                    raw["action_logprobs"].append(np.zeros(n, dtype=np.float32))
                    raw["runtime_after_action"].append("")
                    counts["motion_calls"] += 1
                    for key in COUNT_KEYS:
                        candidate_counts["motion"][key] += trace[key]
                    timing["motion_cpu_seconds"] += time.process_time() - start
                    if boundary:
                        _, public_users = decode_public_state(state, n)
                if boundary:
                    start = time.process_time()
                    old_mask, trace = choose_mask(public_users, predicted, old_mask)
                    decision["mask_search"] = trace
                    counts["mask_calls"] += 1
                    for key in COUNT_KEYS:
                        candidate_counts["mask"][key] += trace[key]
                    # The actor already used the previous mask's observation exactly once.
                    native.set_transmitter_mask(mask_bits(old_mask, n))
                    timing["mask_cpu_seconds"] += time.process_time() - start
                decision["issued_mask"] = old_mask
                decisions.append(decision)
                start = time.process_time()
                raw["actions"].append(command.copy())
                raw["mask"].append(old_mask)
                obs, reward, terminated, truncated, info = env.step(command)
                state = np.asarray(info["next_state"])
                done = bool(terminated or truncated)
                if done != (t == spec.horizon - 1):
                    raise ValueError("endpoint native terminal boundary differs")
                components = info["reward_components"]["reward_info"]
                raw["components"].append([float(components[k]) for k in frozen.COMPONENTS])
                raw["scalar_reward"].append(float(reward))
                raw["terminal"].append(done)
                snapshot()
                dones[0], steps[0] = done, t + 1
                timing["native_and_record_cpu_seconds"] += time.process_time() - start
    finally:
        env.close()
    arrays = {key: np.asarray(value) for key, value in raw.items()}
    arrays["users"] = native.user_positions.copy()
    key = f"{arm}_w{world_id}"
    raw_path = out / "raw" / "evaluation" / f"{key}.npz"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    decision_path = raw_path.with_suffix(".jsonl.gz")
    with gzip.open(decision_path, "xt", encoding="utf-8") as stream:
        for row in decisions:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    timing.update(wall_seconds=time.perf_counter() - wall, cpu_seconds=time.process_time() - cpu)
    return {"arm": arm, "n": n, "world_id": world_id, "runtime_seed": seed,
            "steps": spec.horizon, "complete": True, "metrics": metrics(arrays, n),
            "counts": counts, "candidate_counts": candidate_counts, "timing": timing,
            "raw": artifact(raw_path, out), "decisions": artifact(decision_path, out)}
