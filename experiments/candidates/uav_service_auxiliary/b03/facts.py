"""Native panels and zero-update common-fact diagnostics for B03."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch

from hmasd.agent import HMASDAgent
from ..b01.auxiliary import future_window_targets
from ..b01.native import (
    METRIC_FIELDS, _sync_agent, _terminal_kind, initialization_fingerprint,
    make_env, preserved_rng, seed_everything, sha256_file,
)

FACT_SCHEMA = "uav_service_auxiliary_b03_facts_v2"


def array_digest(**arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(arrays.items()):
        array = np.ascontiguousarray(value)
        digest.update(name.encode())
        digest.update(str(array.dtype).encode())
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes())
    return digest.hexdigest()


def episode(agent, env, seed: int, *, collect_facts: bool = False):
    """Retain the frozen execution path; add commands and a true battery minimum."""
    agent.reset_env_state(0)
    observations, info = env.reset(seed=int(seed))
    state = np.asarray(info["state"], dtype=np.float32)
    previous_done = np.ones(1, dtype=bool)
    totals = {field: 0.0 for field in METRIC_FIELDS}
    rows = {name: [] for name in ("observations", "skills", "actions", "dones", "qos")}
    raw_j, battery_minimum = 0.0, float("inf")
    terminated = truncated = False
    length = 0
    while length < int(agent.config.episode_length):
        actions, _, step_data = agent.step(
            state[None], observations[None], np.asarray([length]), previous_done,
            deterministic=True, return_step_data=True, build_infos=False,
        )
        if collect_facts:
            rows["observations"].append(np.asarray(observations, dtype=np.float32).copy())
            rows["skills"].append(np.asarray(step_data["agent_skills"][0], dtype=np.int64).copy())
            rows["actions"].append(np.asarray(actions[0], dtype=np.float32).copy())
        next_obs, reward, terminated, truncated, info = env.step(actions[0])
        done = bool(terminated or truncated)
        reward_info = info["reward_info"]
        if not np.isfinite(float(reward)):
            raise FloatingPointError("non-finite native evaluation reward")
        raw_j += float(reward)
        for field in METRIC_FIELDS:
            value = float(reward_info[field])
            if not np.isfinite(value):
                raise FloatingPointError(f"non-finite native metric {field}")
            totals[field] += value
        battery_minimum = min(battery_minimum, float(reward_info["battery_min_ratio"]))
        if collect_facts:
            rows["dones"].append(done)
            rows["qos"].append(float(reward_info["qos_satisfaction_ratio"]))
        observations = np.asarray(next_obs, dtype=np.float32)
        state = np.asarray(info["next_state"], dtype=np.float32)
        previous_done[:] = done
        length += 1
        if done:
            break
    if not (terminated or truncated):
        raise RuntimeError("panel reached horizon without native termination/truncation")
    row = {
        "seed": int(seed), "raw_native_J": raw_j, "native_J_per_step": raw_j / length,
        "actual_length": length, "terminal_type": _terminal_kind(terminated, truncated),
        "episode_minimum_battery_ratio": battery_minimum,
    }
    for field, value in totals.items():
        row[f"{field}_sum"] = value
        row[f"{field}_per_step"] = value / length
    arrays = None
    if collect_facts:
        arrays = {name: np.asarray(value, dtype={"skills": np.int64, "dones": np.bool_}.get(name, np.float32))
                  for name, value in rows.items()}
    return row, arrays


def evaluate(agent, config, seeds: Iterable[int], device, *, policy_seed: int,
             log_dir: Path, fact_path: Path | None = None,
             fact_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    seeds = tuple(int(seed) for seed in seeds)
    if not seeds:
        raise ValueError("empty evaluation panel")
    arrays = {}
    with preserved_rng():
        seed_everything(policy_seed, device)
        eval_config = copy.deepcopy(config)
        eval_config.num_envs = 1
        eval_config.calculate_and_set_buffer_sizes()
        evaluator = HMASDAgent(eval_config, log_dir=str(log_dir), device=device)
        _sync_agent(agent, evaluator)
        evaluator.train(False)
        worlds = []
        for index, seed in enumerate(seeds):
            env = make_env(eval_config, seed)
            try:
                row, facts = episode(evaluator, env, seed, collect_facts=fact_path is not None)
            finally:
                env.close()
            worlds.append(row)
            if facts is not None:
                arrays.update({f"episode_{index}_{name}": value for name, value in facts.items()})
                arrays[f"episode_{index}_seed"] = np.asarray(seed, dtype=np.int64)
        if fact_path is not None:
            metadata = dict(fact_metadata or {})
            metadata["policy_sha256"] = initialization_fingerprint(agent)
            metadata["seeds"] = list(seeds)
            metadata["new_optimizer_updates"] = 0
            arrays["schema"] = np.asarray(FACT_SCHEMA)
            arrays["metadata"] = np.asarray(json.dumps(metadata, sort_keys=True))
            fact_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(fact_path, **arrays)
    fields = [key for key, value in worlds[0].items()
              if isinstance(value, (int, float)) and key not in {"seed", "actual_length"}]
    aggregate = {f"mean_{key}": float(np.mean([row[key] for row in worlds])) for key in fields}
    aggregate["primary_native_J_mean"] = aggregate["mean_raw_native_J"]
    aggregate["worlds"] = len(worlds)
    result = {"worlds": worlds, "aggregate": aggregate,
              "actual_transitions": sum(row["actual_length"] for row in worlds),
              "new_optimizer_updates": 0}
    if fact_path is not None:
        result["facts_sha256"] = sha256_file(fact_path)
    return result


def fact_indices(archive) -> list[int]:
    if str(archive["schema"].item()) != FACT_SCHEMA:
        raise ValueError("B03 fact schema mismatch (raw commands are required)")
    indices = sorted(int(key.split("_")[1]) for key in archive.files if key.endswith("_observations"))
    if not indices or indices != list(range(len(indices))):
        raise ValueError("fact episodes must be a nonempty contiguous sequence")
    return indices


def read_episode(archive, index: int) -> dict[str, np.ndarray]:
    data = {name: archive[f"episode_{index}_{name}"] for name in
            ("observations", "skills", "actions", "dones", "qos")}
    obs = data["observations"]
    if obs.ndim != 3 or min(obs.shape) <= 0:
        raise ValueError("invalid factual observation shape")
    time, agents, _ = obs.shape
    expected = {"skills": (time, agents), "actions": (time, agents, 4),
                "dones": (time,), "qos": (time,)}
    if any(data[key].shape != shape for key, shape in expected.items()):
        raise ValueError("invalid factual input shapes")
    if any(not np.isfinite(value).all() for value in data.values()):
        raise ValueError("non-finite factual values")
    if data["dones"].dtype != np.bool_ or np.any(data["dones"][:-1]) or not data["dones"][-1]:
        raise ValueError("one fact episode must end at its only terminal transition")
    return data


def copy_initial_facts(source: Path, digest: str, destination: Path, *, seeds,
                       policy_sha256: str, block_seed: int) -> str:
    if sha256_file(source) != digest:
        raise ValueError("initial facts digest mismatch")
    with np.load(source, allow_pickle=False) as archive:
        indices = fact_indices(archive)
        metadata = json.loads(str(archive["metadata"].item()))
        if metadata.get("kind") != "initial" or metadata.get("block_seed") != block_seed:
            raise ValueError("initial facts kind or block mismatch")
        if metadata.get("policy_sha256") != policy_sha256:
            raise ValueError("initial facts policy fingerprint mismatch")
        observed = tuple(int(archive[f"episode_{i}_seed"]) for i in indices)
        if observed != tuple(seeds):
            raise ValueError("initial facts seed mismatch")
        for index in indices:
            read_episode(archive, index)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if sha256_file(destination) != digest:
        raise RuntimeError("initial facts copy changed")
    return digest


def effective_rank(features: np.ndarray) -> dict[str, Any]:
    values = np.asarray(features, dtype=np.float64)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise ValueError("rank requires finite rows by features")
    if len(values) < 2:
        return {"rows": len(values), "total_variance": None, "effective_rank": None, "degenerate": None}
    centered = values - values.mean(axis=0)
    eigenvalues = np.linalg.eigvalsh(centered.T @ centered / len(values)).clip(min=0)
    total = float(eigenvalues.sum())
    if total == 0:
        return {"rows": len(values), "total_variance": 0.0, "effective_rank": 0.0, "degenerate": True}
    probabilities = eigenvalues[eigenvalues > 0] / total
    return {"rows": len(values), "total_variance": total,
            "effective_rank": float(np.exp(-np.sum(probabilities * np.log(probabilities)))),
            "degenerate": False}


def _calibration_arrays(calibration):
    if calibration is None:
        return None
    return np.asarray(calibration["mu"], dtype=np.float64), np.asarray(calibration["scale"], dtype=np.float64)


def score_arrays(arrays: dict[str, np.ndarray], *, calibration, window: int) -> dict[str, Any]:
    """Episode-equal scoring, also used to finish the saved rollout-zero readout."""
    indices = sorted(int(key.split("_")[1]) for key in arrays if key.endswith("_service_predictions"))
    coordinates = _calibration_arrays(calibration)
    rows = []
    for index in indices:
        prefix = f"episode_{index}_"
        prediction = arrays[prefix + "service_predictions"].astype(np.float64)
        observations = arrays[prefix + "normalized_observations"].astype(np.float64)
        target, valid = future_window_targets(arrays[prefix + "qos"][:, None],
                                             arrays[prefix + "dones"][:, None], window=window)
        valid = valid[:, 0].numpy()
        labels = target[:, 0].numpy().astype(np.float64)
        row = {"index": index, "seed": int(arrays[prefix + "seed"]),
               "valid_team_rows": int(valid.sum()), "valid_agent_rows": int(valid.sum() * prediction.shape[-1]),
               "service_mse": None, "service_training_mean_mse": None,
               "observation_mse": None, "persistence_mse": None, "training_mean_mse": None}
        if valid.any():
            row["service_mse"] = float(np.mean((prediction[valid] - labels[valid, None]) ** 2))
            if coordinates is not None:
                mu, scale = coordinates
                times = np.flatnonzero(valid)
                if np.any(times + 1 >= len(observations)):
                    raise ValueError("valid generic target has no next observation")
                target_obs = (observations[times + 1] - mu) / scale
                pred = arrays[prefix + "observation_predictions"][times].astype(np.float64)
                persistence = (observations[times] - mu) / scale
                row["observation_mse"] = float(np.mean((pred - target_obs) ** 2))
                row["persistence_mse"] = float(np.mean((persistence - target_obs) ** 2))
                row["training_mean_mse"] = float(np.mean(target_obs ** 2))
                row["service_training_mean_mse"] = float(np.mean((labels[valid] - calibration["service_target_mean"]) ** 2))
        rows.append(row)
    result = {"episodes": rows, "episode_count": len(rows),
              "episodes_without_valid_windows": sum(row["valid_team_rows"] == 0 for row in rows),
              "valid_agent_rows": sum(row["valid_agent_rows"] for row in rows),
              "weighting": "equal episodes with complete windows; missing episodes explicitly counted",
              "new_optimizer_updates": 0, "calibration_available": coordinates is not None}
    for key in ("service_mse", "observation_mse", "persistence_mse", "training_mean_mse", "service_training_mean_mse"):
        values = [row[key] for row in rows if row[key] is not None]
        result[key] = float(np.mean(values)) if values else None
        result[f"{key}_episodes"] = len(values)
    return result


def replay_facts(auxiliary, agent, facts_path: Path, *, save_arrays: Path | None = None) -> dict[str, Any]:
    """Replay from reset, using the actor's existing normalization without updating it."""
    outputs, feature_samples, variation = {}, [], []
    with preserved_rng(), np.load(facts_path, allow_pickle=False) as archive:
        indices = fact_indices(archive)
        counts = []
        for index in indices:
            data = read_episode(archive, index)
            _, valid = future_window_targets(data["qos"][:, None], data["dones"][:, None], window=auxiliary.window)
            counts.append(int(valid.sum()) * data["observations"].shape[1])
        total = sum(counts)
        sample_indices = np.unique(np.linspace(0, total - 1, min(512, total), dtype=np.int64)) if total else np.empty(0, np.int64)
        offset = 0
        for index, count in zip(indices, counts, strict=True):
            data = read_episode(archive, index)
            obs = data["observations"][:, None]
            normalized = np.asarray(agent._normalize_observations(obs, update=False), dtype=np.float32)
            prediction = auxiliary.predict_all(
                agent.skill_discoverer.actor, obs, data["skills"][:, None], data["dones"][:, None],
                actions=data["actions"][:, None], normalized_observations=normalized,
            )
            prefix = f"episode_{index}_"
            outputs[prefix + "service_predictions"] = prediction["service"].detach().cpu().numpy()[:, 0]
            outputs[prefix + "observation_predictions"] = prediction["observation"].detach().cpu().numpy()[:, 0]
            outputs[prefix + "normalized_observations"] = normalized[:, 0]
            for name in ("qos", "dones"):
                outputs[prefix + name] = data[name]
            outputs[prefix + "seed"] = archive[prefix + "seed"]
            _, valid = future_window_targets(data["qos"][:, None], data["dones"][:, None], window=auxiliary.window)
            valid = valid[:, 0].numpy()
            features = prediction["features"].detach().cpu().numpy()[:, 0]
            legal = features[valid]
            local_indices = sample_indices[(sample_indices >= offset) & (sample_indices < offset + count)] - offset
            feature_samples.append(legal.reshape(-1, features.shape[-1])[local_indices])
            offset += count
            per_agent = [float(np.var(legal[:, i].astype(np.float64), axis=0).sum()) if len(legal) else None
                         for i in range(features.shape[1])]
            segments = []
            for segment in np.array_split(legal, 4, axis=0):
                segments.append([float(np.var(segment[:, i].astype(np.float64), axis=0).sum()) if len(segment) else None
                                 for i in range(features.shape[1])])
            variation.append({"episode": index, "per_agent_total_variance": per_agent,
                              "quarter_episode_per_agent_total_variance": segments})
        sampled = np.concatenate(feature_samples, axis=0)
        outputs["feature_sample_indices"] = sample_indices
        outputs["feature_samples"] = sampled
        result = score_arrays(outputs, calibration=auxiliary.calibration_state(), window=auxiliary.window)
        result["features"] = {**effective_rank(sampled), "sample_indices": sample_indices.tolist(), "variation": variation}
        result["facts_sha256"] = sha256_file(facts_path)
        result["source"] = json.loads(str(archive["metadata"].item()))
    if save_arrays is not None:
        np.savez_compressed(save_arrays, **outputs)
        result["prediction_arrays_sha256"] = sha256_file(save_arrays)
    return result


def finish_initial_scores(result: dict[str, Any], prediction_path: Path, calibration, window: int):
    """Apply first-training-rollout coordinates to saved pre-training predictions."""
    with np.load(prediction_path, allow_pickle=False) as saved:
        scores = score_arrays(dict(saved), calibration=calibration, window=window)
    result.update(scores)
    result["scale_applied_to_saved_initial_predictions"] = True
