"""B02: compare raw and coordinate-clipped execution of six frozen B01 policies."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import subprocess
import sys
import time
import traceback
from typing import Any, Callable

import numpy as np
import torch

from experiments.candidates.agent_count_generalization.adapter import make_envs
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC as B01_SPEC,
    DIRECTION,
    FitSpec,
    config_dict,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import build_agent
from experiments.candidates.agent_count_generalization.runner import (
    COMPONENTS,
    NORMALIZERS,
    digest_agent,
    finite,
    jsonable,
    model_modules,
    native_components,
    optimizer_counts,
    reset_all,
    seed_rng,
    write_json,
)


OBJECT_ID = "s1_action_law_b02_probe"
B01_LAUNCH_SHA = "5a250d97e3ea12d33067e9c00c250cefa12b5e25"
MAPS = ("raw", "clip")
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
TRACKED_B01_SUMMARY_ROOT = REPOSITORY_ROOT / "runs" / DIRECTION
SOURCE_POLICIES = (
    ("H6", 914201, "s1_count_b01_h6_s914201"),
    ("H6", 914307, "s1_count_b01_h6_s914307"),
    ("H6", 914413, "s1_count_b01_h6_s914413"),
    ("SET", 915201, "s1_count_b01_set_s915201"),
    ("SET", 915307, "s1_count_b01_set_s915307"),
    ("SET", 915413, "s1_count_b01_set_s915413"),
)


@dataclass(frozen=True)
class ProbeSpec:
    test_ns: tuple[int, ...] = (4, 6, 8)
    horizon: int = 500
    eval_lanes: int = 16
    panel_seed_base: int = 982000
    torch_threads: int = 4


DEFAULT_SPEC = ProbeSpec()


@dataclass(frozen=True)
class SourcePolicy:
    arm: str
    seed: int
    tag: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _array_digest(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(value.dtype).encode("ascii"))
    digest.update(repr(value.shape).encode("ascii"))
    digest.update(value.tobytes())
    return digest.hexdigest()


def _rng_digest() -> str:
    """Fingerprint global RNGs without advancing them."""
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    np_state = np.random.get_state()
    digest.update(str(np_state[0]).encode("ascii"))
    digest.update(np.asarray(np_state[1]).tobytes())
    digest.update(repr(np_state[2:]).encode("ascii"))
    digest.update(torch.get_rng_state().cpu().numpy().tobytes())
    return digest.hexdigest()


def _load_bound_summary(path: Path, tracked_summary_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    working_bytes = path.read_bytes()
    source_bytes = working_bytes
    committed_binding = Path(tracked_summary_root).resolve() == TRACKED_B01_SUMMARY_ROOT.resolve()
    if committed_binding:
        relative = path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()
        source_bytes = subprocess.run(
            ["git", "-C", str(REPOSITORY_ROOT), "show", f"HEAD:{relative}"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        if working_bytes != source_bytes:
            raise ValueError(f"tracked B01 summary working bytes differ from HEAD: {relative}")
    value = json.loads(source_bytes.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object at {path}")
    return value, {
        "path": str(path),
        "sha256": hashlib.sha256(source_bytes).hexdigest(),
        "bytes": len(source_bytes),
        "binding": "HEAD git blob plus identical working bytes" if committed_binding
                   else "internal technical fixture bytes",
    }


def _checkpoint_record(summary: dict[str, Any]) -> dict[str, Any]:
    matches = [row for row in summary.get("checkpoints", [])
               if row.get("path") == "checkpoint_45.pt"]
    if len(matches) != 1:
        raise ValueError("B01 summary must bind exactly one checkpoint_45.pt")
    row = matches[0]
    if not isinstance(row.get("bytes"), int) or row["bytes"] <= 0:
        raise ValueError("B01 checkpoint byte count is invalid")
    if not isinstance(row.get("sha256"), str) or len(row["sha256"]) != 64:
        raise ValueError("B01 checkpoint SHA-256 is invalid")
    return row


def load_source_policy(
    checkpoint_root: Path,
    source: SourcePolicy,
    *,
    tracked_summary_root: Path = TRACKED_B01_SUMMARY_ROOT,
) -> dict[str, Any]:
    """Verify the tracked B01 record and deserialize its bound rollout-45 payload."""
    fit_root = checkpoint_root / source.tag
    # The summary is part of this evaluator's committed source.  The external
    # checkpoint root is mutable result storage and therefore cannot vouch for
    # its own digest, size, arm, seed, or launch identity.
    summary_path = Path(tracked_summary_root) / source.tag / "summary.json"
    summary, summary_identity = _load_bound_summary(summary_path, Path(tracked_summary_root))
    expected = {
        "direction": DIRECTION,
        "arm": source.arm,
        "seed": source.seed,
        "launch_sha": B01_LAUNCH_SHA,
        "status": "complete",
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(
                f"B01 summary {source.tag} {key} mismatch: {summary.get(key)!r} != {value!r}"
            )
    if summary.get("fit_started") is not True:
        raise ValueError(f"B01 summary {source.tag} is not a completed fit")
    for n in DEFAULT_SPEC.test_ns:
        panels = [
            row for row in summary.get("panels", [])
            if row.get("after_rollout") == 45 and row.get("test_n") == n
        ]
        if len(panels) != 1 or panels[0].get("status") != "complete" or not isinstance(
            panels[0].get("config"), dict
        ):
            raise ValueError(f"B01 summary {source.tag} lacks one complete final N={n} panel")
    record = _checkpoint_record(summary)
    checkpoint = fit_root / record["path"]
    if checkpoint.stat().st_size != record["bytes"]:
        raise ValueError(f"checkpoint byte-size mismatch for {source.tag}")
    digest = file_sha256(checkpoint)
    if digest != record["sha256"]:
        raise ValueError(f"checkpoint SHA-256 mismatch for {source.tag}")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict):
        raise ValueError(f"checkpoint payload for {source.tag} is not a mapping")
    required = {"schema", "direction", "launch_sha", "rollout", "config", "modules",
                "normalizers", "usage"}
    if set(payload) != required:
        raise ValueError(f"checkpoint payload keys differ for {source.tag}: {sorted(payload)}")
    checks = {
        "schema": 1,
        "direction": DIRECTION,
        "launch_sha": B01_LAUNCH_SHA,
        "rollout": 45,
    }
    for key, value in checks.items():
        if payload.get(key) != value:
            raise ValueError(f"checkpoint payload {key} mismatch for {source.tag}")
    config = payload.get("config")
    if not isinstance(config, dict) or config.get("count_arm") != source.arm:
        raise ValueError(f"checkpoint arm mismatch for {source.tag}")
    if config.get("seed") != source.seed or config.get("n_agents") != 6:
        raise ValueError(f"checkpoint seed/train roster mismatch for {source.tag}")
    if not isinstance(payload.get("modules"), dict) or not isinstance(
        payload.get("normalizers"), dict
    ):
        raise ValueError(f"checkpoint learned-state structure is invalid for {source.tag}")
    return {
        "source": source,
        "fit_root": fit_root,
        "summary_path": summary_path,
        "summary": summary,
        "summary_identity": summary_identity,
        "checkpoint": checkpoint,
        "checkpoint_record": record,
        "payload": payload,
        "checkpoint_sha256_before": digest,
    }


def _restore_normalizer(target: Any, saved: Any, name: str) -> None:
    if saved is None:
        if target is not None:
            raise ValueError(f"checkpoint disables {name} but target constructed it")
        return
    if target is None or not isinstance(saved, dict):
        raise ValueError(f"checkpoint/target {name} presence mismatch")
    target_fields = vars(target)
    if set(saved) != set(target_fields):
        raise ValueError(
            f"{name} fields mismatch: checkpoint={sorted(saved)}, target={sorted(target_fields)}"
        )
    for field, value in saved.items():
        current = target_fields[field]
        if isinstance(current, np.ndarray):
            restored = np.asarray(value, dtype=current.dtype)
            if restored.shape != current.shape:
                raise ValueError(f"{name}.{field} shape mismatch")
            setattr(target, field, restored.copy())
        elif isinstance(current, np.generic):
            setattr(target, field, np.asarray(value, dtype=current.dtype)[()])
        elif isinstance(current, bool):
            if not isinstance(value, bool):
                raise ValueError(f"{name}.{field} type mismatch")
            setattr(target, field, value)
        elif isinstance(current, int):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name}.{field} type mismatch")
            setattr(target, field, type(current)(value))
        elif isinstance(current, float):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name}.{field} type mismatch")
            setattr(target, field, type(current)(value))
        else:
            raise ValueError(f"unsupported normalizer field {name}.{field}: {type(current).__name__}")


def restore_checkpoint(agent: Any, payload: dict[str, Any]) -> None:
    """Strict module and normalizer restoration into a freshly built N-specific runtime."""
    targets = model_modules(agent)
    saved_modules = payload["modules"]
    if set(saved_modules) != set(targets):
        raise ValueError(
            f"checkpoint module set mismatch: checkpoint={sorted(saved_modules)}, "
            f"target={sorted(targets)}"
        )
    for name, module in targets.items():
        expected = module.state_dict()
        saved = saved_modules[name]
        if set(saved) != set(expected):
            raise ValueError(f"checkpoint {name} state keys mismatch")
        for key, tensor in expected.items():
            value = saved[key]
            if not torch.is_tensor(value):
                raise ValueError(f"checkpoint {name}.{key} is not a tensor")
            if value.shape != tensor.shape or value.dtype != tensor.dtype:
                raise ValueError(
                    f"checkpoint {name}.{key} metadata mismatch: "
                    f"{tuple(value.shape)}/{value.dtype} != {tuple(tensor.shape)}/{tensor.dtype}"
                )
        module.load_state_dict(saved, strict=True)
    saved_normalizers = payload["normalizers"]
    if set(saved_normalizers) != set(NORMALIZERS):
        raise ValueError("checkpoint normalizer set mismatch")
    for name in NORMALIZERS:
        _restore_normalizer(getattr(agent, name, None), saved_normalizers[name], name)
    agent.train(False)


def _source_model_spec(source_record: dict[str, Any], probe: ProbeSpec):
    recorded = source_record["summary"].get("spec", {})
    payload_config = source_record["payload"]["config"]
    required = {
        "hidden_size": int(payload_config["hidden_size"]),
        "n_heads": int(payload_config["n_heads"]),
        "n_layers": int(payload_config["n_encoder_layers"]),
        "ppo_epochs": int(payload_config["ppo_epochs"]),
        "sequence_batch_size": int(payload_config["sequence_batch_size"]),
        "coordinator_batch_size": int(payload_config["coordinator_batch_size"]),
    }
    for key, value in required.items():
        if int(recorded.get(key, -1)) != value:
            raise ValueError(f"B01 summary/payload architecture mismatch at {key}")
    if int(payload_config["n_decoder_layers"]) != required["n_layers"]:
        raise ValueError("B01 payload encoder/decoder layer count mismatch")
    fields = {}
    for key, default in vars(B01_SPEC).items():
        if key not in recorded:
            raise ValueError(f"B01 summary spec is missing {key}")
        value = recorded[key]
        fields[key] = tuple(value) if isinstance(default, tuple) else value
    source_spec = FitSpec(**fields)
    if (source_spec.horizon, source_spec.eval_lanes, source_spec.torch_threads) != (
        probe.horizon, probe.eval_lanes, probe.torch_threads
    ):
        raise ValueError("B02 runtime dimensions disagree with the tracked B01 construction")
    return source_spec


def _assert_reconstructed_config(
    config: Any, payload_config: dict[str, Any], tracked_summary: dict[str, Any], n: int
) -> None:
    rebuilt = config_dict(config)
    allowed = {"n_agents", "n_uavs", "batch_size", "discriminator_batch_size"}
    unexpected = {
        key: (payload_config.get(key), rebuilt.get(key))
        for key in set(payload_config) | set(rebuilt)
        if payload_config.get(key) != rebuilt.get(key) and key not in allowed
    }
    if unexpected:
        raise ValueError(f"rebuilt evaluation config changed policy behavior fields: {unexpected}")
    if rebuilt["n_agents"] != n or rebuilt["n_uavs"] != n:
        raise ValueError("rebuilt evaluation config has the wrong test roster")
    if n == 6 and any(payload_config.get(key) != rebuilt.get(key) for key in allowed):
        raise ValueError("N=6 evaluation config does not exactly reconstruct the checkpoint config")
    panel = next(row for row in tracked_summary["panels"]
                 if row["after_rollout"] == 45 and row["test_n"] == n)
    if rebuilt != panel["config"]:
        differences = {
            key: (panel["config"].get(key), rebuilt.get(key))
            for key in set(panel["config"]) | set(rebuilt)
            if panel["config"].get(key) != rebuilt.get(key)
        }
        raise ValueError(f"rebuilt config differs from tracked final N={n} evaluator: {differences}")


def _normalizer_record(agent: Any) -> dict[str, Any]:
    result = {}
    for name in NORMALIZERS:
        normalizer = getattr(agent, name, None)
        if normalizer is None:
            result[name] = None
            continue
        fields = {}
        for field, value in vars(normalizer).items():
            array = np.asarray(value)
            fields[field] = {
                "dtype": str(array.dtype),
                "shape": list(array.shape),
                "value": jsonable(value),
            }
        result[name] = {"type": type(normalizer).__name__, "fields": fields}
    return result


def _native(env: Any) -> Any:
    native = env.env.env
    positions = np.asarray(native.uav_positions)
    if not np.issubdtype(positions.dtype, np.floating):
        raise ValueError(f"native position storage is not floating: {positions.dtype}")
    return native


def _movement_prediction(native: Any, before: np.ndarray, action: np.ndarray):
    unbounded = np.empty_like(before)
    clipped = np.empty_like(before)
    for agent in range(before.shape[0]):
        velocity = action[agent] * native.max_speed
        candidate = before[agent] + velocity * native.time_step
        unbounded[agent] = candidate
        bounded = candidate.copy()
        bounded[0] = np.clip(bounded[0], 0, native.area_size)
        bounded[1] = np.clip(bounded[1], 0, native.area_size)
        bounded[2] = np.clip(bounded[2], *native.height_range)
        clipped[agent] = bounded
    return unbounded, clipped


def _dtype_tolerance(dtype: np.dtype, scale: float) -> dict[str, float]:
    info = np.finfo(dtype)
    return {"atol": float(8 * info.eps * max(1.0, abs(scale))), "rtol": float(8 * info.eps)}


def _rate(numerator: int, denominator: int) -> dict[str, Any]:
    if denominator <= 0:
        raise ValueError("diagnostic rate denominator must be positive")
    return {"numerator": int(numerator), "denominator": int(denominator),
            "rate": float(numerator / denominator)}


def map_actions(actions: np.ndarray, low: np.ndarray, high: np.ndarray,
                execution_map: str) -> np.ndarray:
    """Return the separately owned environment action without mutating policy output."""
    if execution_map == "raw":
        return actions.copy()
    if execution_map == "clip":
        return np.clip(actions, low, high)
    raise ValueError(f"unknown execution map {execution_map}")


def _new_lane_diag() -> dict[str, Any]:
    return {
        "raw_coordinate_violations": 0,
        "raw_uav_violations": 0,
        "raw_team_step_violations": 0,
        "map_changed_coordinates": 0,
        "map_changed_uavs": 0,
        "map_changed_team_steps": 0,
        "raw_excess_sum": 0.0,
        "raw_excess_max": 0.0,
        "raw_attempted_l2_sum": 0.0,
        "raw_attempted_l2_max": 0.0,
        "executed_attempted_l2_sum": 0.0,
        "executed_attempted_l2_max": 0.0,
        "realized_l2_sum": 0.0,
        "realized_l2_max": 0.0,
        "boundary_truncated_coordinates": 0,
        "boundary_truncated_uavs": 0,
        "boundary_truncated_team_steps": 0,
        "boundary_occupied_coordinates": 0,
        "movement_prediction_exact_coordinates": 0,
        "movement_prediction_max_abs_error": 0.0,
    }


def _finish_lane_diag(row: dict[str, Any], horizon: int, n: int) -> dict[str, Any]:
    coordinate_den = horizon * n * 3
    uav_den = horizon * n
    result = {
        "raw_coordinate_violations": _rate(row["raw_coordinate_violations"], coordinate_den),
        "raw_uav_violations": _rate(row["raw_uav_violations"], uav_den),
        "raw_team_step_violations": _rate(row["raw_team_step_violations"], horizon),
        "map_changed_coordinates": _rate(row["map_changed_coordinates"], coordinate_den),
        "map_changed_uavs": _rate(row["map_changed_uavs"], uav_den),
        "map_changed_team_steps": _rate(row["map_changed_team_steps"], horizon),
        "boundary_truncated_coordinates": _rate(row["boundary_truncated_coordinates"], coordinate_den),
        "boundary_truncated_uavs": _rate(row["boundary_truncated_uavs"], uav_den),
        "boundary_truncated_team_steps": _rate(row["boundary_truncated_team_steps"], horizon),
        "boundary_occupied_coordinates": _rate(row["boundary_occupied_coordinates"], coordinate_den),
        "movement_prediction_exact_coordinates": _rate(
            row["movement_prediction_exact_coordinates"], coordinate_den
        ),
        "raw_excess_mean_per_coordinate": row["raw_excess_sum"] / coordinate_den,
        "raw_excess_max": row["raw_excess_max"],
        "raw_attempted_displacement_l2_mean_per_uav_step": row["raw_attempted_l2_sum"] / uav_den,
        "raw_attempted_displacement_l2_max": row["raw_attempted_l2_max"],
        "executed_attempted_displacement_l2_mean_per_uav_step": row[
            "executed_attempted_l2_sum"
        ] / uav_den,
        "executed_attempted_displacement_l2_max": row["executed_attempted_l2_max"],
        "realized_displacement_l2_mean_per_uav_step": row["realized_l2_sum"] / uav_den,
        "realized_displacement_l2_max": row["realized_l2_max"],
        "movement_prediction_max_abs_error": row["movement_prediction_max_abs_error"],
    }
    return jsonable(result)


def _save_trace(path: Path, arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    partial = path.with_suffix(path.suffix + ".partial")
    with partial.open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    partial.replace(path)
    return {
        "path": path.name,
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "index_semantics": {
            "base": "zero-based",
            "transition": (
                "pre_map_actions[t] and executed_actions[t] map native_positions[t] and "
                "encoded_states[t] to native_positions[t+1] and encoded_states[t+1]"
            ),
        },
        "arrays": {
            key: {"shape": list(value.shape), "dtype": str(value.dtype),
                  "sha256": _array_digest(value)}
            for key, value in arrays.items()
        },
    }


def evaluate_map(
    source_record: dict[str, Any],
    n: int,
    execution_map: str,
    out: Path,
    probe: ProbeSpec,
    step_progress: Callable[[int, int], None] | None = None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    """Evaluate one independent source-policy/N/action-map runtime."""
    if execution_map not in MAPS:
        raise ValueError(f"unknown execution map {execution_map}")
    source: SourcePolicy = source_record["source"]
    world_seed = probe.panel_seed_base + 100 * n
    runtime_seed = world_seed + 51
    seed_rng(runtime_seed)
    envs = make_envs(probe.eval_lanes, world_seed, n, probe.horizon)
    target = None
    hooks = []
    try:
        fit_spec = _source_model_spec(source_record, probe)
        config = make_config(source.arm, envs, source.seed, fit_spec)
        _assert_reconstructed_config(
            config, source_record["payload"]["config"], source_record["summary"], n
        )
        target = build_agent(config, str(out / "logs" / f"{source.arm.lower()}_{source.seed}_n{n}_{execution_map}"))
        restore_checkpoint(target, source_record["payload"])
        for lane in range(probe.eval_lanes):
            target.reset_env_state(lane)
        calls, hooks = optimizer_counts(target)
        model_before = digest_agent(target)
        states, observations = reset_all(envs)
        steps = np.zeros(probe.eval_lanes, dtype=np.int64)
        dones = np.zeros(probe.eval_lanes, dtype=bool)

        native_positions = [np.asarray(_native(env).uav_positions) for env in envs]
        position_dtype = native_positions[0].dtype
        if any(value.dtype != position_dtype for value in native_positions):
            raise ValueError("native lanes disagree on position dtype")
        tolerance = _dtype_tolerance(position_dtype, max(float(_native(envs[0]).area_size),
                                                           float(_native(envs[0]).height_range[1])))
        first_native = _native(envs[0])
        native_contract = {
            "area_size": float(first_native.area_size),
            "height_range": [float(value) for value in first_native.height_range],
            "max_speed": float(first_native.max_speed),
            "time_step": float(first_native.time_step),
            "position_dtype": str(position_dtype),
        }
        for env in envs[1:]:
            native = _native(env)
            candidate = {
                "area_size": float(native.area_size),
                "height_range": [float(value) for value in native.height_range],
                "max_speed": float(native.max_speed),
                "time_step": float(native.time_step),
                "position_dtype": str(np.asarray(native.uav_positions).dtype),
            }
            if candidate != native_contract:
                raise ValueError("B02 native lanes disagree on the movement contract")
        low = np.asarray(envs[0].action_space.low)
        high = np.asarray(envs[0].action_space.high)
        if low.shape != (n, 3) or high.shape != (n, 3):
            raise ValueError("native action-space shape mismatch")
        if not np.array_equal(low, np.full((n, 3), -1.0, dtype=low.dtype)) or not np.array_equal(
            high, np.full((n, 3), 1.0, dtype=high.dtype)
        ):
            raise ValueError("B02 is bound to the declared coordinate bounds [-1, 1]")

        trace = {
            "pre_map_actions": np.empty((probe.horizon, probe.eval_lanes, n, 3), dtype=np.float32),
            "executed_actions": np.empty((probe.horizon, probe.eval_lanes, n, 3), dtype=np.float32),
            "action_logprobs": np.empty((probe.horizon, probe.eval_lanes, n), dtype=np.float32),
            "native_positions": np.empty(
                (probe.horizon + 1, probe.eval_lanes, n, 3), dtype=position_dtype
            ),
            "encoded_states": np.empty(
                (probe.horizon + 1, probe.eval_lanes, states.shape[-1]), dtype=states.dtype
            ),
        }
        trace["native_positions"][0] = np.stack(native_positions)
        trace["encoded_states"][0] = states
        initial_observations_digest = _array_digest(observations)
        returns = np.zeros(probe.eval_lanes, dtype=np.float64)
        components = {key: np.zeros(probe.eval_lanes, dtype=np.float64) for key in COMPONENTS}
        lane_diags = [_new_lane_diag() for _ in range(probe.eval_lanes)]
        diagnostic_rng_unchanged = True
        raw_arrays_unchanged = True
        logprob_arrays_unchanged = True

        with torch.no_grad():
            for t in range(probe.horizon):
                actions, _, data = target.step(
                    states, observations, steps, dones,
                    deterministic=True, return_step_data=True, build_infos=False,
                )
                finite((actions, data), "B02 frozen evaluation")
                actions = np.asarray(actions)
                logprobs = np.asarray(data["action_logprobs"])
                if actions.shape != (probe.eval_lanes, n, 3):
                    raise ValueError("B02 policy action roster mismatch")
                if logprobs.shape != (probe.eval_lanes, n):
                    raise ValueError("B02 action log-probability roster mismatch")
                if actions.dtype != np.float32 or logprobs.dtype != np.float32:
                    raise ValueError("B02 policy action/log-probability dtype must remain float32")
                actions_before = actions.copy()
                logprobs_before = logprobs.copy()
                rng_before = _rng_digest()
                executed = map_actions(actions, low, high, execution_map)
                diagnostic_rng_unchanged &= rng_before == _rng_digest()
                raw_arrays_unchanged &= np.array_equal(actions, actions_before)
                logprob_arrays_unchanged &= np.array_equal(logprobs, logprobs_before)
                trace["pre_map_actions"][t] = actions
                trace["executed_actions"][t] = executed
                trace["action_logprobs"][t] = logprobs

                next_states, next_observations = [], []
                for lane, env in enumerate(envs):
                    native = _native(env)
                    before = np.asarray(native.uav_positions).copy()
                    unbounded, predicted = _movement_prediction(native, before, executed[lane])
                    raw_attempt = actions[lane] * native.max_speed * native.time_step
                    executed_attempt = executed[lane] * native.max_speed * native.time_step
                    excess = np.maximum(np.abs(actions[lane]) - 1.0, 0.0)
                    violations = excess > 0
                    changed = executed[lane] != actions[lane]

                    obs, reward, terminated, truncated, info = env.step(executed[lane])
                    if step_progress is not None:
                        step_progress(1, int(bool(terminated or truncated)))
                    after = np.asarray(native.uav_positions).copy()
                    if not np.allclose(after, predicted, **tolerance):
                        raise ValueError("native movement disagrees with source-order prediction")
                    prediction_error = np.abs(after - predicted)
                    exact_prediction = after == predicted
                    bounds_low = np.asarray([0.0, 0.0, native.height_range[0]], dtype=position_dtype)
                    bounds_high = np.asarray(
                        [native.area_size, native.area_size, native.height_range[1]],
                        dtype=position_dtype,
                    )
                    truncated_coords = unbounded != predicted
                    occupied = np.isclose(after, bounds_low, **tolerance) | np.isclose(
                        after, bounds_high, **tolerance
                    )
                    realized = after - before
                    diag = lane_diags[lane]
                    diag["raw_coordinate_violations"] += int(violations.sum())
                    diag["raw_uav_violations"] += int(violations.any(axis=1).sum())
                    diag["raw_team_step_violations"] += int(violations.any())
                    diag["map_changed_coordinates"] += int(changed.sum())
                    diag["map_changed_uavs"] += int(changed.any(axis=1).sum())
                    diag["map_changed_team_steps"] += int(changed.any())
                    diag["raw_excess_sum"] += float(excess.sum())
                    diag["raw_excess_max"] = max(diag["raw_excess_max"], float(excess.max()))
                    raw_norm = np.linalg.norm(raw_attempt, axis=1)
                    executed_norm = np.linalg.norm(executed_attempt, axis=1)
                    realized_norm = np.linalg.norm(realized, axis=1)
                    diag["raw_attempted_l2_sum"] += float(raw_norm.sum())
                    diag["raw_attempted_l2_max"] = max(diag["raw_attempted_l2_max"], float(raw_norm.max()))
                    diag["executed_attempted_l2_sum"] += float(executed_norm.sum())
                    diag["executed_attempted_l2_max"] = max(
                        diag["executed_attempted_l2_max"], float(executed_norm.max())
                    )
                    diag["realized_l2_sum"] += float(realized_norm.sum())
                    diag["realized_l2_max"] = max(diag["realized_l2_max"], float(realized_norm.max()))
                    diag["boundary_truncated_coordinates"] += int(truncated_coords.sum())
                    diag["boundary_truncated_uavs"] += int(truncated_coords.any(axis=1).sum())
                    diag["boundary_truncated_team_steps"] += int(truncated_coords.any())
                    diag["boundary_occupied_coordinates"] += int(occupied.sum())
                    diag["movement_prediction_exact_coordinates"] += int(exact_prediction.sum())
                    diag["movement_prediction_max_abs_error"] = max(
                        diag["movement_prediction_max_abs_error"], float(prediction_error.max())
                    )

                    parts = native_components(info, reward, n)
                    returns[lane] += reward
                    for key in COMPONENTS:
                        components[key][lane] += parts[key]
                    next_states.append(info["next_state"])
                    next_observations.append(obs)
                    dones[lane] = bool(terminated or truncated)
                states = np.stack(next_states)
                observations = np.stack(next_observations)
                trace["native_positions"][t + 1] = np.stack(
                    [np.asarray(_native(env).uav_positions) for env in envs]
                )
                trace["encoded_states"][t + 1] = states
                steps += 1
                if dones.any() and (t != probe.horizon - 1 or not dones.all()):
                    raise ValueError("unexpected B02 terminal boundary")

        if not dones.all():
            raise ValueError("B02 evaluation did not reach its fixed horizon")
        if any(calls.values()):
            raise ValueError(f"B02 made optimizer calls: {calls}")
        if digest_agent(target) != model_before:
            raise ValueError("B02 modified checkpoint parameters or normalizers")
        if not raw_arrays_unchanged or not logprob_arrays_unchanged:
            raise ValueError("execution mapping mutated policy output or its log probabilities")
        if not diagnostic_rng_unchanged:
            raise ValueError("B02 diagnostics consumed a global RNG")

        component_means = {key: values / probe.horizon for key, values in components.items()}
        j = n * returns / probe.horizon
        if not np.allclose(j, component_means["total_reward"], atol=1e-7, rtol=1e-6):
            raise ValueError("B02 native J/component identity failed")
        trace_name = f"trace_{source.arm.lower()}_{source.seed}_n{n}_{execution_map}.npz"
        trace_record = _save_trace(out / trace_name, trace)
        result = {
            "status": "complete",
            "arm": source.arm,
            "seed": source.seed,
            "source_tag": source.tag,
            "test_n": n,
            "execution_map": execution_map,
            "world_seeds": list(range(world_seed, world_seed + probe.eval_lanes)),
            "runtime_seed": runtime_seed,
            "steps": probe.horizon * probe.eval_lanes,
            "episodes": probe.eval_lanes,
            "J": j.tolist(),
            "scalar_returns": returns.tolist(),
            "component_means": jsonable(component_means),
            "optimizer_calls": calls.copy(),
            "frozen_weights_and_normalizers": True,
            "model_digest": model_before,
            "normalizers": _normalizer_record(target),
            "initial_encoded_states_sha256": _array_digest(trace["encoded_states"][0]),
            "initial_native_positions_sha256": _array_digest(trace["native_positions"][0]),
            "initial_observations_sha256": initial_observations_digest,
            "native_position_dtype": str(position_dtype),
            "native_environment": native_contract,
            "movement_tolerance": tolerance,
            "action_bounds": {"low": -1.0, "high": 1.0},
            "policy_outputs_unchanged_by_mapping": raw_arrays_unchanged,
            "action_logprobs_unchanged_by_mapping": logprob_arrays_unchanged,
            "diagnostics_consumed_no_global_rng": diagnostic_rng_unchanged,
            "lane_diagnostics": [
                {"world_seed": world_seed + lane,
                 **_finish_lane_diag(row, probe.horizon, n)}
                for lane, row in enumerate(lane_diags)
            ],
            "trace": trace_record,
            "config": config_dict(config),
        }
        return result, trace
    finally:
        for hook in hooks:
            hook.remove()
        for env in envs:
            env.close()
        del target


def _first_difference(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    if a.shape != b.shape:
        raise ValueError("paired trace shapes differ")
    difference = np.abs(a.astype(np.float64) - b.astype(np.float64))
    mask = a != b
    where = np.argwhere(mask)
    first = where[0].tolist() if len(where) else None
    return {
        "index_base": "zero-based",
        "exact_identity": bool(not mask.any()),
        "first_differing_index": first,
        "differing_elements": int(mask.sum()),
        "max_abs_difference": float(difference.max()) if difference.size else 0.0,
    }


def compare_maps(raw: dict[str, Any], clip: dict[str, Any],
                 raw_trace: dict[str, np.ndarray], clip_trace: dict[str, np.ndarray]) -> dict[str, Any]:
    for field in ("arm", "seed", "test_n", "world_seeds"):
        if raw[field] != clip[field]:
            raise ValueError(f"raw/clip pair differs at {field}")
    starts = {
        "encoded_state": _first_difference(
            raw_trace["encoded_states"][0], clip_trace["encoded_states"][0]
        ),
        "native_position": _first_difference(
            raw_trace["native_positions"][0], clip_trace["native_positions"][0]
        ),
    }
    if not all(row["exact_identity"] for row in starts.values()):
        raise ValueError("raw/clip runtimes did not start from identical actual states")
    if raw["initial_observations_sha256"] != clip["initial_observations_sha256"]:
        raise ValueError("raw/clip runtimes did not start from identical observations")
    if raw["model_digest"] != clip["model_digest"]:
        raise ValueError("raw/clip runtimes did not restore identical models/normalizers")
    if raw["normalizers"] != clip["normalizers"]:
        raise ValueError("raw/clip runtimes did not restore identical normalizer values/types")
    if raw["runtime_seed"] != clip["runtime_seed"]:
        raise ValueError("raw/clip runtimes used different runtime seeds")
    comparisons = {
        "pre_map_actions": _first_difference(
            raw_trace["pre_map_actions"], clip_trace["pre_map_actions"]
        ),
        "executed_actions": _first_difference(
            raw_trace["executed_actions"], clip_trace["executed_actions"]
        ),
        "native_positions": _first_difference(
            raw_trace["native_positions"], clip_trace["native_positions"]
        ),
        "encoded_states": _first_difference(
            raw_trace["encoded_states"], clip_trace["encoded_states"]
        ),
        "action_logprobs": _first_difference(
            raw_trace["action_logprobs"], clip_trace["action_logprobs"]
        ),
    }
    lane_rows = []
    raw_j, clip_j = np.asarray(raw["J"]), np.asarray(clip["J"])
    for lane, world_seed in enumerate(raw["world_seeds"]):
        raw_pre = raw_trace["pre_map_actions"][:, lane]
        clip_pre = clip_trace["pre_map_actions"][:, lane]
        raw_executed = raw_trace["executed_actions"][:, lane]
        clip_executed = clip_trace["executed_actions"][:, lane]
        raw_position = raw_trace["native_positions"][:, lane]
        clip_position = clip_trace["native_positions"][:, lane]
        raw_state = raw_trace["encoded_states"][:, lane]
        clip_state = clip_trace["encoded_states"][:, lane]
        action_changed = raw_executed != clip_executed
        changed_step = action_changed.reshape(action_changed.shape[0], -1).any(axis=1)
        same_start = (
            (raw_position[:-1] == clip_position[:-1]).reshape(len(changed_step), -1).all(axis=1)
            & (raw_state[:-1] == clip_state[:-1]).reshape(len(changed_step), -1).all(axis=1)
            & (raw_pre == clip_pre).reshape(len(changed_step), -1).all(axis=1)
        )
        same_successor = (
            (raw_position[1:] == clip_position[1:]).reshape(len(changed_step), -1).all(axis=1)
            & (raw_state[1:] == clip_state[1:]).reshape(len(changed_step), -1).all(axis=1)
        )
        comparable_change = same_start & changed_step
        absorbed = comparable_change & same_successor
        component_rows = {}
        for name in COMPONENTS:
            raw_value = float(raw["component_means"][name][lane])
            clip_value = float(clip["component_means"][name][lane])
            component_rows[name] = {
                "raw": raw_value, "clip": clip_value, "clip_minus_raw": clip_value - raw_value
            }
        first_steps = {}
        for name, index_kind, left, right in (
            ("pre_map_action", "action_t", raw_pre, clip_pre),
            ("executed_action", "action_t", raw_executed, clip_executed),
            ("native_position", "position_t", raw_position, clip_position),
            ("encoded_state", "state_t", raw_state, clip_state),
        ):
            difference = left != right
            per_step = difference.reshape(difference.shape[0], -1).any(axis=1)
            indices = np.flatnonzero(per_step)
            numeric = np.abs(left.astype(np.float64) - right.astype(np.float64))
            first_steps[name] = {
                "trace_index_zero_based": None if not len(indices) else int(indices[0]),
                "index_kind": index_kind,
                "max_abs_difference": float(numeric.max()) if numeric.size else 0.0,
                "exact_identity": bool(not difference.any()),
            }
        lane_rows.append({
            "world_seed": world_seed,
            "J_raw": float(raw_j[lane]),
            "J_clip": float(clip_j[lane]),
            "d": float(clip_j[lane] - raw_j[lane]),
            "components": component_rows,
            "first_divergence_step": first_steps,
            "changed_action_steps": _rate(int(changed_step.sum()), len(changed_step)),
            "same_start_mapping_changed_steps": _rate(int(comparable_change.sum()), len(changed_step)),
            "same_start_mapping_changed_same_exact_successor_steps": _rate(
                int(absorbed.sum()), len(changed_step)
            ),
        })
    return {
        "arm": raw["arm"],
        "seed": raw["seed"],
        "test_n": raw["test_n"],
        "trace_index_semantics": {
            "base": "zero-based",
            "transition": (
                "action[t] maps native position/state[t] to native position/state[t+1]; "
                "all first-divergence step indices are zero-based"
            ),
        },
        "identical_starts": starts,
        "trajectory_comparison": comparisons,
        "worlds": lane_rows,
        "J_raw_mean": float(raw_j.mean()),
        "J_clip_mean": float(clip_j.mean()),
        "d_mean": float((clip_j - raw_j).mean()),
        "inactive_mapping_all_worlds": bool(comparisons["executed_actions"]["exact_identity"]),
        "exact_same_position_trajectory": bool(comparisons["native_positions"]["exact_identity"]),
        "exact_same_encoded_state_trajectory": bool(comparisons["encoded_states"]["exact_identity"]),
    }


def reduce_results(cells: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> dict[str, Any]:
    complete = [cell for cell in cells if cell.get("status") == "complete"]
    expected = len(SOURCE_POLICIES) * len(DEFAULT_SPEC.test_ns) * len(MAPS)
    if len(complete) != expected:
        raise ValueError(f"B02 reduction requires {expected} complete cells, got {len(complete)}")
    by_key = {(cell["arm"], cell["seed"], cell["test_n"], cell["execution_map"]): cell
              for cell in complete}
    gaps: dict[str, Any] = {}
    for n in DEFAULT_SPEC.test_ns:
        gaps[str(n)] = {}
        for execution_map in MAPS:
            arm_means = {}
            for arm in ("H6", "SET"):
                values = [value for (a, _seed, count, law), cell in by_key.items()
                          if a == arm and count == n and law == execution_map
                          for value in cell["J"]]
                arm_means[arm] = float(np.mean(values))
            gaps[str(n)][execution_map] = {
                "arm_J_means": arm_means,
                "H6_minus_SET": arm_means["H6"] - arm_means["SET"],
            }
        gaps[str(n)]["K_gap_clip_minus_gap_raw"] = (
            gaps[str(n)]["clip"]["H6_minus_SET"] - gaps[str(n)]["raw"]["H6_minus_SET"]
        )
        gaps[str(n)]["arm_clip_minus_raw"] = {
            arm: gaps[str(n)]["clip"]["arm_J_means"][arm]
                 - gaps[str(n)]["raw"]["arm_J_means"][arm]
            for arm in ("H6", "SET")
        }
    unseen = {}
    for execution_map in MAPS:
        unseen[execution_map] = float(np.mean([
            gaps[str(n)][execution_map]["H6_minus_SET"] for n in (4, 8)
        ]))
    unseen_arm_changes = {
        arm: float(np.mean([gaps[str(n)]["arm_clip_minus_raw"][arm] for n in (4, 8)]))
        for arm in ("H6", "SET")
    }
    return {
        "per_policy_d": [{key: row[key] for key in ("arm", "seed", "test_n", "d_mean")}
                         for row in pairs],
        "by_n": gaps,
        "unseen_equal_weight_gap": unseen,
        "unseen_equal_weight_arm_clip_minus_raw": unseen_arm_changes,
        "unseen_K_gap_clip_minus_gap_raw": unseen["clip"] - unseen["raw"],
        "unit": "three old policy training units per arm; worlds and policies equally weighted",
    }


def _assert_scientific_spec(spec: ProbeSpec) -> None:
    if spec != DEFAULT_SPEC:
        raise ValueError("scientific B02 entry binds the full fixed ProbeSpec")


def run_probe(
    out: Path,
    checkpoint_root: Path,
    launch_sha: str,
    admission: dict[str, Any],
    spec: ProbeSpec = DEFAULT_SPEC,
    *,
    command_start: float | None = None,
) -> int:
    """Run the admitted full B02 panel. Tests call lower-level helpers for tiny fixtures."""
    _assert_scientific_spec(spec)
    out = Path(out)
    checkpoint_root = Path(checkpoint_root)
    if (out / "summary.json").exists():
        raise ValueError("existing scientific summary; reconcile the original B02 attempt")
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if command_start is None:
        command_start = started
    summary: dict[str, Any] = {
        "schema": 1,
        "object_id": OBJECT_ID,
        "direction": DIRECTION,
        "launch_sha": launch_sha,
        "admission": admission,
        "status": "initializing",
        "failure": None,
        "spec": jsonable(vars(spec)),
        "source_policies": [
            {"arm": arm, "seed": seed, "tag": tag} for arm, seed, tag in SOURCE_POLICIES
        ],
        "input_checkpoints": [],
        "cells": [],
        "pairs": [],
        "aggregates": None,
        "counts": {
            "fits": 0,
            "training_team_steps": 0,
            "training_episodes": 0,
            "updates": 0,
            "optimizer_calls": 0,
            "evaluation_team_steps": 0,
            "evaluation_episodes": 0,
            "technical_checks": 0,
        },
        "runtime": {
            "python": sys.version,
            "torch": torch.__version__,
            "numpy": np.__version__,
            "device": "cpu",
            "policy_dtype": "float32",
            "torch_threads": spec.torch_threads,
            "thread_environment": {
                name: os.environ.get(name) for name in
                ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")
            },
        },
        "interpretation_limits": [
            "fixed-policy deployment intervention; it does not change or identify training exposure",
            "three old training units per arm; no population ranking, equivalence, or confirmation claim",
            "K can reflect SET improvement, H6 loss, or both; absolute map changes are retained",
        ],
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_probe_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    publish("admitted")
    try:
        torch.set_num_threads(spec.torch_threads)
        records = []
        for arm, seed, tag in SOURCE_POLICIES:
            input_row = {"arm": arm, "seed": seed, "source_tag": tag, "status": "verifying"}
            summary["input_checkpoints"].append(input_row)
            try:
                record = load_source_policy(checkpoint_root, SourcePolicy(arm, seed, tag))
            except Exception as exc:
                input_row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                publish(f"input {tag} failed")
                raise
            records.append(record)
            input_row.update({
                "arm": arm,
                "seed": seed,
                "source_tag": tag,
                "summary": str(record["summary_path"]),
                "tracked_summary_identity": record["summary_identity"],
                "checkpoint": str(record["checkpoint"]),
                "rollout": 45,
                "bytes": record["checkpoint_record"]["bytes"],
                "sha256": record["checkpoint_record"]["sha256"],
                "launch_sha": B01_LAUNCH_SHA,
                "status": "verified",
            })
            summary["counts"]["technical_checks"] += 1
            publish(f"verified input {tag}")

        summary["status"] = "evaluating"
        for record in records:
            source: SourcePolicy = record["source"]
            for n in spec.test_ns:
                map_results, map_traces = {}, {}
                for execution_map in MAPS:
                    cell = {
                        "arm": source.arm,
                        "seed": source.seed,
                        "source_tag": source.tag,
                        "test_n": n,
                        "execution_map": execution_map,
                        "status": "running",
                        "steps": 0,
                        "episodes": 0,
                    }
                    summary["cells"].append(cell)
                    publish(f"{source.tag} N={n} {execution_map} starting")
                    try:
                        def account(team_steps: int, episodes: int) -> None:
                            cell["steps"] += int(team_steps)
                            cell["episodes"] += int(episodes)
                            summary["counts"]["evaluation_team_steps"] += int(team_steps)
                            summary["counts"]["evaluation_episodes"] += int(episodes)

                        result, trace = evaluate_map(
                            record, n, execution_map, out, spec, step_progress=account
                        )
                        if (cell["steps"], cell["episodes"]) != (
                            result["steps"], result["episodes"]
                        ):
                            raise ValueError("B02 live progress disagrees with completed cell counts")
                        cell.clear()
                        cell.update(result)
                        map_results[execution_map], map_traces[execution_map] = result, trace
                        summary["counts"]["optimizer_calls"] += sum(result["optimizer_calls"].values())
                        write_json(
                            out / f"cell_{source.arm.lower()}_{source.seed}_n{n}_{execution_map}.json",
                            result,
                        )
                        publish(f"{source.tag} N={n} {execution_map} complete")
                    except Exception as exc:
                        cell.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                        write_json(
                            out / f"cell_{source.arm.lower()}_{source.seed}_n{n}_{execution_map}.json",
                            cell,
                        )
                        raise
                pair = compare_maps(
                    map_results["raw"], map_results["clip"],
                    map_traces["raw"], map_traces["clip"],
                )
                summary["pairs"].append(pair)
                write_json(out / f"pair_{source.arm.lower()}_{source.seed}_n{n}.json", pair)
                del map_traces
                publish(f"{source.tag} N={n} paired")
            digest_after = file_sha256(record["checkpoint"])
            if digest_after != record["checkpoint_sha256_before"]:
                raise ValueError(f"source checkpoint changed during B02: {source.tag}")
            input_row = next(row for row in summary["input_checkpoints"]
                             if row["source_tag"] == source.tag)
            input_row["sha256_after"] = digest_after
            input_row["unchanged"] = True

        expected_steps = len(SOURCE_POLICIES) * len(MAPS) * len(spec.test_ns) * \
            spec.eval_lanes * spec.horizon
        expected_episodes = len(SOURCE_POLICIES) * len(MAPS) * len(spec.test_ns) * spec.eval_lanes
        if summary["counts"]["evaluation_team_steps"] != expected_steps:
            raise ValueError("B02 evaluation team-step count mismatch")
        if summary["counts"]["evaluation_episodes"] != expected_episodes:
            raise ValueError("B02 evaluation episode count mismatch")
        if summary["counts"]["optimizer_calls"] != 0:
            raise ValueError("B02 is a zero-optimizer probe")
        summary["aggregates"] = reduce_results(summary["cells"], summary["pairs"])
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        summary.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
        (out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        return_code = 1
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["resources"] = {
            "command_wall_seconds": time.perf_counter() - command_start,
            "run_probe_wall_seconds": time.perf_counter() - started,
            "cpu_user_seconds": usage.ru_utime,
            "cpu_system_seconds": usage.ru_stime,
            "peak_rss_kib": usage.ru_maxrss,
            "rss_scope": "scientific process Linux RUSAGE_SELF",
            "resources_unmeasured": ["peak_scratch_bytes"],
        }
        publish(summary["status"])
    return return_code
