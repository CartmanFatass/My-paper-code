"""Source-bound frozen-policy evaluation for the five-cell native S1 load panel."""

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

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.agent_count_generalization.adapter import CountAdapter
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC as SOURCE_DEFAULT_SPEC,
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
    optimizer_counts,
    seed_rng,
    write_json,
)
from experiments.candidates.agent_count_generalization.action_law_b02.probe import (
    restore_checkpoint,
)
from .scenes import make_native_scene, service_diagnostics


OBJECT_ID = "s1_load_critical_member_b01"
DIRECTION = "load_critical_member_generalization"
PRODUCER_SHA = "89486d32ea569728f39d6e21b53f8a7c8854e74c"
SOURCE_DIRECTION = "agent_count_generalization"
SOURCE_OBJECT_ID = "s1_action_law_b03"
SOURCE_POLICIES = (
    ("H6", 942201, "s1_action_law_b03_h6_clip_s942201"),
    ("SET", 943201, "s1_action_law_b03_set_clip_s943201"),
)
CELLS = ((4, 10), (4, 20), (8, 5), (8, 10), (6, 10))
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
TRACKED_SOURCE_ROOT = REPOSITORY_ROOT / "runs" / SOURCE_DIRECTION
_RUNTIME_FIELDS = (
    "env_timers",
    "env_team_skills",
    "env_agent_skills",
    "env_log_probs",
    "env_hidden_states",
    "env_prev_hidden_states",
    "env_reward_sums",
    "env_pending_high_level",
    "env_skill_ages",
    "env_skill_duration_remaining",
    "env_skill_duration_target",
    "actor_hidden_np",
    "critic_hidden_np",
    "prev_actor_hidden_np",
    "prev_critic_hidden_np",
    "_hidden_state_array_valid",
    "_central_snapshot_states",
    "_central_snapshot_obs",
    "_central_snapshot_valid",
)


@dataclass(frozen=True)
class ProbeSpec:
    cells: tuple[tuple[int, int], ...] = CELLS
    world_ids: tuple[int, ...] = tuple(range(16))
    horizon: int = 500
    source_num_envs: int = 16
    torch_threads: int = 4


DEFAULT_SPEC = ProbeSpec()


@dataclass(frozen=True)
class SourcePolicy:
    arm: str
    seed: int
    tag: str


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _array_digest(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(f"{value.dtype}|{value.shape}".encode("ascii"))
    digest.update(value.tobytes())
    return digest.hexdigest()


def _canonical_update(digest: Any, value: Any) -> None:
    if torch.is_tensor(value):
        value = value.detach().cpu().contiguous().numpy()
    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        digest.update(f"array|{array.dtype}|{array.shape}|".encode("ascii"))
        digest.update(array.tobytes())
    elif isinstance(value, dict):
        digest.update(b"dict{")
        for key in sorted(value, key=lambda item: repr(item)):
            _canonical_update(digest, key)
            _canonical_update(digest, value[key])
        digest.update(b"}")
    elif isinstance(value, (tuple, list)):
        digest.update(f"{type(value).__name__}[".encode("ascii"))
        for item in value:
            _canonical_update(digest, item)
        digest.update(b"]")
    elif isinstance(value, np.generic):
        _canonical_update(digest, value.item())
    elif value is None or isinstance(value, (bool, int, float, str, bytes)):
        digest.update(f"{type(value).__name__}:".encode("ascii"))
        digest.update(value if isinstance(value, bytes) else repr(value).encode("utf-8"))
    else:
        raise TypeError(f"unsupported canonical fingerprint value {type(value).__name__}")


def canonical_digest(value: Any) -> str:
    digest = hashlib.sha256()
    _canonical_update(digest, value)
    return digest.hexdigest()


def runtime_state_digest(agent: Any) -> str:
    state = {
        name: getattr(agent, name)
        for name in _RUNTIME_FIELDS
        if hasattr(agent, name)
    }
    buffer = getattr(agent, "rollout_buffer", None)
    if buffer is not None and hasattr(buffer, "get_sampler_rng_state"):
        state["rollout_buffer_sampler_rng"] = buffer.get_sampler_rng_state()
    return canonical_digest(state)


def _rng_digest() -> str:
    return canonical_digest(
        {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.random.get_rng_state(),
        }
    )


def runtime_seed(world_id: int, n_uavs: int) -> int:
    state = np.random.SeedSequence(
        [260922, 6, int(world_id), 3, int(n_uavs)]
    ).generate_state(1, dtype=np.uint32)
    return int(state[0])


def _committed_bytes(path: Path, repository_root: Path) -> tuple[bytes, dict[str, Any]]:
    path = path.resolve()
    repository_root = repository_root.resolve()
    try:
        relative = path.relative_to(repository_root).as_posix()
    except ValueError as exc:
        raise ValueError("source summary is outside its binding repository") from exc
    working = path.read_bytes()
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "show", f"HEAD:{relative}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(f"source summary is not committed at HEAD: {relative}")
    if working != completed.stdout:
        raise ValueError(f"source summary working bytes differ from HEAD: {relative}")
    return completed.stdout, {
        "path": relative,
        "git_revision": "HEAD",
        "sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "bytes": len(completed.stdout),
        "working_bytes_identical": True,
    }


def _source_spec(summary: dict[str, Any]) -> FitSpec:
    recorded = summary.get("spec")
    if not isinstance(recorded, dict):
        raise ValueError("B03 source summary lacks its FitSpec")
    fields = {}
    for name, default in vars(SOURCE_DEFAULT_SPEC).items():
        if name not in recorded:
            raise ValueError(f"B03 source FitSpec is missing {name}")
        fields[name] = tuple(recorded[name]) if isinstance(default, tuple) else recorded[name]
    spec = FitSpec(**fields)
    if (
        spec.train_n,
        spec.test_ns,
        spec.horizon,
        spec.train_lanes,
        spec.eval_lanes,
        spec.rollouts,
        spec.panels,
        spec.torch_threads,
    ) != (6, (4, 6, 8), 500, 16, 16, 45, (0, 15, 30, 45), 4):
        raise ValueError("B03 source FitSpec differs from the selected production contract")
    return spec


def _checkpoint_record(summary: dict[str, Any]) -> dict[str, Any]:
    matches = [
        row
        for row in summary.get("checkpoints", [])
        if row.get("path") == "checkpoint_45.pt"
    ]
    if len(matches) != 1:
        raise ValueError("B03 source must bind exactly one checkpoint_45.pt")
    record = matches[0]
    if not isinstance(record.get("bytes"), int) or record["bytes"] <= 0:
        raise ValueError("B03 checkpoint byte count is invalid")
    if not isinstance(record.get("sha256"), str) or len(record["sha256"]) != 64:
        raise ValueError("B03 checkpoint SHA-256 is invalid")
    return record


def load_source_policy(
    checkpoint_root: Path,
    source: SourcePolicy,
    *,
    tracked_summary_root: Path = TRACKED_SOURCE_ROOT,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, Any]:
    """Load one committed, completed B03 clip/final45 source and external checkpoint."""
    expected = {policy[0]: policy for policy in SOURCE_POLICIES}
    if source.arm not in expected or tuple((source.arm, source.seed, source.tag)) != expected[source.arm]:
        raise ValueError("source is outside the fixed H6/SET B03 clip pair")
    summary_path = Path(tracked_summary_root) / source.tag / "summary.json"
    source_bytes, summary_identity = _committed_bytes(summary_path, Path(repository_root))
    summary = json.loads(source_bytes.decode("utf-8"))
    checks = {
        "schema": 1,
        "object_id": SOURCE_OBJECT_ID,
        "direction": SOURCE_DIRECTION,
        "arm": source.arm,
        "training_action_law": "clip",
        "seed": source.seed,
        "tag": source.tag,
        "launch_sha": PRODUCER_SHA,
        "status": "complete",
        "fit_started": True,
        "evaluation_action_law": "clip",
    }
    for key, expected_value in checks.items():
        if summary.get(key) != expected_value:
            raise ValueError(
                f"B03 source {source.tag} {key} mismatch: "
                f"{summary.get(key)!r} != {expected_value!r}"
            )
    cell = summary.get("cell")
    if not isinstance(cell, dict) or any(
        cell.get(key) != value
        for key, value in {
            "arm": source.arm,
            "law": "clip",
            "seed": source.seed,
            "tag": source.tag,
        }.items()
    ):
        raise ValueError("B03 source cell identity is inconsistent")
    spec = _source_spec(summary)
    expected_counts = {
        "training_team_steps": 360_000,
        "stored_team_steps": 360_000,
        "training_episodes": 720,
        "terminal_resets": 720,
        "updates": 45,
        "evaluation_team_steps": 96_000,
        "evaluation_episodes": 192,
    }
    if summary.get("counts") != expected_counts:
        raise ValueError("B03 source exposure counts are incomplete or changed")
    final_panels = [
        row for row in summary.get("panels", []) if row.get("after_rollout") == 45
    ]
    if sorted(row.get("test_n") for row in final_panels) != [4, 6, 8]:
        raise ValueError("B03 source lacks exactly one final panel for N4/N6/N8")
    for panel in final_panels:
        if (
            panel.get("status") != "complete"
            or panel.get("steps") != 8_000
            or panel.get("episodes") != 16
            or not isinstance(panel.get("config"), dict)
        ):
            raise ValueError("B03 final panel is incomplete")

    record = _checkpoint_record(summary)
    checkpoint = Path(checkpoint_root) / source.tag / record["path"]
    if checkpoint.stat().st_size != record["bytes"]:
        raise ValueError("B03 checkpoint byte-size mismatch")
    checkpoint_digest = file_sha256(checkpoint)
    if checkpoint_digest != record["sha256"]:
        raise ValueError("B03 checkpoint SHA-256 mismatch")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    required = {
        "schema",
        "direction",
        "launch_sha",
        "rollout",
        "config",
        "modules",
        "normalizers",
        "usage",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("B03 checkpoint payload schema differs")
    payload_checks = {
        "schema": 1,
        "direction": SOURCE_DIRECTION,
        "launch_sha": PRODUCER_SHA,
        "rollout": 45,
    }
    for key, expected_value in payload_checks.items():
        if payload.get(key) != expected_value:
            raise ValueError(f"B03 checkpoint payload {key} mismatch")
    if payload.get("config") != summary.get("config"):
        raise ValueError("B03 checkpoint and completed summary configs differ")
    config_checks = {
        "count_arm": source.arm,
        "seed": source.seed,
        "n_agents": 6,
        "n_uavs": 6,
        "num_envs": 16,
        "rollout_length": 500,
        "episode_length": 500,
        "k": 10,
    }
    for key, expected_value in config_checks.items():
        if payload["config"].get(key) != expected_value:
            raise ValueError(f"B03 checkpoint config {key} mismatch")
    if summary.get("initial_digest_matches_expected") is not True:
        raise ValueError("B03 completed source lacks a successful initial-digest check")
    final_digest = summary.get("final_parameter_normalizer_digest")
    if not isinstance(final_digest, str) or len(final_digest) != 64:
        raise ValueError("B03 completed source lacks its final model/normalizer digest")
    return {
        "source": source,
        "summary": summary,
        "summary_path": summary_path,
        "summary_identity": summary_identity,
        "source_spec": spec,
        "checkpoint": checkpoint,
        "checkpoint_record": record,
        "checkpoint_sha256_before": checkpoint_digest,
        "payload": payload,
    }


def _make_env(n_uavs: int, capacity: int, world_id: int, horizon: int, seed: int):
    native = make_native_scene(
        n_uavs=n_uavs,
        capacity=capacity,
        world_id=world_id,
        horizon=horizon,
    )
    return CountAdapter(ParallelToArrayAdapter(native, seed=seed))


def _assert_reconstructed_config(config: Any, record: dict[str, Any], n_uavs: int) -> None:
    rebuilt = config_dict(config)
    payload = record["payload"]["config"]
    allowed = {"n_agents", "n_uavs", "batch_size", "discriminator_batch_size"}
    changed = {
        key: (payload.get(key), rebuilt.get(key))
        for key in set(payload) | set(rebuilt)
        if payload.get(key) != rebuilt.get(key) and key not in allowed
    }
    if changed:
        raise ValueError(f"reconstructed policy behavior changed: {changed}")
    if rebuilt["n_agents"] != n_uavs or rebuilt["n_uavs"] != n_uavs:
        raise ValueError("reconstructed config has the wrong roster")
    if rebuilt["num_envs"] != 16 or rebuilt["k"] != 10:
        raise ValueError("reconstructed config lost num_envs16 or k10")
    panels = [
        row
        for row in record["summary"]["panels"]
        if row.get("after_rollout") == 45 and row.get("test_n") == n_uavs
    ]
    if len(panels) != 1 or rebuilt != panels[0]["config"]:
        raise ValueError(f"reconstructed config differs from final N={n_uavs} panel")


def _normalizer_record(agent: Any) -> dict[str, Any]:
    result = {}
    for name in NORMALIZERS:
        normalizer = getattr(agent, name, None)
        if normalizer is None:
            result[name] = None
        else:
            result[name] = {
                field: {
                    "dtype": str(np.asarray(value).dtype),
                    "shape": list(np.asarray(value).shape),
                    "value": jsonable(value),
                }
                for field, value in vars(normalizer).items()
            }
    return result


def _save_trace(path: Path, trace: dict[str, np.ndarray]) -> dict[str, Any]:
    partial = path.with_suffix(path.suffix + ".partial")
    with partial.open("wb") as stream:
        np.savez_compressed(stream, **trace)
    partial.replace(path)
    return {
        "path": path.name,
        "sha256": file_sha256(path),
        "bytes": path.stat().st_size,
        "arrays": {
            name: {"shape": list(value.shape), "dtype": str(value.dtype)}
            for name, value in trace.items()
        },
    }


def _trace_from_lists(values: dict[str, list[Any]]) -> dict[str, np.ndarray]:
    result = {}
    for name, rows in values.items():
        if name.startswith("runtime_"):
            result[name] = np.asarray(rows, dtype="U64")
        elif name == "identity_reasons":
            result[name] = np.asarray(rows, dtype=str)
        else:
            result[name] = np.asarray(rows)
    return result


def _world_summary(trace: dict[str, np.ndarray], n_uavs: int) -> dict[str, Any]:
    components = {
        name: float(np.mean(trace[f"component_{name}"])) for name in COMPONENTS
    }
    scalar_return = float(np.sum(trace["scalar_reward"]))
    j_value = n_uavs * scalar_return / len(trace["scalar_reward"])
    if not np.isclose(j_value, components["total_reward"], atol=1e-7, rtol=1e-6):
        raise ValueError("native J/component identity failed")
    return {
        "J": float(j_value),
        "scalar_return": scalar_return,
        "component_means": components,
        "mean_e_i": np.mean(trace["e_i"], axis=0).tolist(),
        "mean_served": float(np.mean(trace["served_count"])),
        "mean_eligible": float(np.mean(trace["eligible_count"])),
        "mean_eligible_unserved": float(np.mean(trace["eligible_unserved_count"])),
        "mean_ineligible": float(np.mean(trace["ineligible_count"])),
        "mean_occupancy_rate": float(np.mean(trace["occupancy_rate"])),
        "full_uav_step_rate": float(np.mean(trace["full_uav_rate"])),
        "overflow_uav_steps": int(np.sum(trace["overflow_uavs"])),
        "overflow_uav_step_denominator": int(len(trace["overflow_uavs"]) * n_uavs),
        "missed_eligible_users": int(np.sum(trace["eligible_unserved_count"])),
        "missed_eligible_user_denominator": int(np.sum(trace["eligible_count"])),
        "visibility_truncated_entries": int(np.sum(trace["visibility_truncated"])),
        "visibility_eligible_entry_denominator": int(np.sum(trace["visibility_denominator"])),
        "quality_normalized_sum_mean": float(np.mean(trace["quality_sum"])),
        "quality_normalized_mean": float(np.mean(trace["quality_mean"])),
        "capacity_identity_applicable_all": bool(trace["identity_applicable"].all()),
        "capacity_identity_holds_all_applicable": bool(
            trace["identity_holds"][trace["identity_applicable"]].all()
        ),
        "capacity_identity_interpretation_quarantined": bool(
            not trace["identity_applicable"].all()
            or not trace["identity_holds"][trace["identity_applicable"]].all()
        ),
        "capacity_identity_reasons": sorted(set(trace["identity_reasons"].tolist())),
        "maximum_eligible_uavs_per_user": int(trace["maximum_eligible_uavs"].max()),
    }


def evaluate_cell(
    record: dict[str, Any],
    n_uavs: int,
    capacity: int,
    out: Path,
    spec: ProbeSpec,
    *,
    progress: Callable[[int, int], None],
    after_step: Callable[[dict[str, Any]], None] | None = None,
    world_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Evaluate one package/cell; tests may inject failure after a counted native step."""
    source: SourcePolicy = record["source"]
    first_seed = runtime_seed(spec.world_ids[0], n_uavs)
    config_env = _make_env(
        n_uavs, capacity, spec.world_ids[0], spec.horizon, first_seed
    )
    agent = None
    handles = []
    try:
        seed_rng(source.seed)
        config = make_config(
            source.arm,
            [config_env] * spec.source_num_envs,
            source.seed,
            record["source_spec"],
        )
        _assert_reconstructed_config(config, record, n_uavs)
        agent = build_agent(config, str(Path(out) / "runtime_logs" / source.arm.lower() / f"n{n_uavs}c{capacity}"))
        restore_checkpoint(agent, record["payload"])
        agent.train(False)
        calls, handles = optimizer_counts(agent)
        model_before = digest_agent(agent)
        if model_before != record["summary"]["final_parameter_normalizer_digest"]:
            raise ValueError(
                "restored model/normalizer digest differs from completed B03 source"
            )
        normalizers_before = _normalizer_record(agent)
        worlds = []
        diagnostic_rng_unchanged = True
        raw_actions_unchanged = True
        logprobs_unchanged = True

        for world_id in spec.world_ids:
            seed = runtime_seed(world_id, n_uavs)
            env = _make_env(n_uavs, capacity, world_id, spec.horizon, seed)
            try:
                seed_rng(seed)
                agent.reset_env_state(0)
                observations, info = env.reset(seed=seed)
                state = np.asarray(info["state"])
                observation = np.asarray(observations)
                native = env.env.env
                values: dict[str, list[Any]] = {
                    "observations": [observation.copy()],
                    "encoded_states": [state.copy()],
                    "native_positions": [np.asarray(native.uav_positions).copy()],
                    "native_user_positions": [np.asarray(native.user_positions).copy()],
                    "sinr": [np.asarray(native.sinr_matrix).copy()],
                    "connections": [np.asarray(native.connections).copy()],
                    "runtime_before_action": [runtime_state_digest(agent)],
                    "runtime_after_action": [],
                    "raw_actions": [],
                    "executed_actions": [],
                    "action_logprobs": [],
                    "scalar_reward": [],
                }
                for name in COMPONENTS:
                    values[f"component_{name}"] = []
                for name in (
                    "e_i",
                    "served_count",
                    "eligible_count",
                    "eligible_unserved_count",
                    "ineligible_count",
                    "occupancy_rate",
                    "full_uav_rate",
                    "overflow_uavs",
                    "visibility_truncated",
                    "visibility_denominator",
                    "quality_sum",
                    "quality_mean",
                    "identity_applicable",
                    "identity_holds",
                    "identity_reasons",
                    "maximum_eligible_uavs",
                ):
                    values[name] = []

                trace_name = (
                    f"trace_{source.arm.lower()}_n{n_uavs}_c{capacity}_w{world_id:02d}.npz"
                )
                trace_path = Path(out) / trace_name
                steps_completed = 0
                terminal_observed = False
                try:
                    steps = np.zeros(1, dtype=np.int64)
                    dones = np.zeros(1, dtype=bool)
                    with torch.no_grad():
                        for t in range(spec.horizon):
                            raw, _value, data = agent.step(
                                state[None, :],
                                observation[None, :, :],
                                steps,
                                dones,
                                deterministic=True,
                                return_step_data=True,
                                build_infos=False,
                            )
                            finite((raw, data), "load probe policy output")
                            raw_before = raw.copy()
                            logprob_before = np.asarray(data["action_logprobs"]).copy()
                            executed = np.clip(raw, -1.0, 1.0)
                            raw_actions_unchanged &= np.array_equal(raw, raw_before)
                            logprobs_unchanged &= np.array_equal(
                                np.asarray(data["action_logprobs"]), logprob_before
                            )
                            values["runtime_after_action"].append(runtime_state_digest(agent))
                            values["raw_actions"].append(raw[0].copy())
                            values["executed_actions"].append(executed[0].copy())
                            values["action_logprobs"].append(np.squeeze(logprob_before[0]).copy())

                            next_observation, reward, terminated, truncated, step_info = env.step(
                                executed[0]
                            )
                            done = bool(terminated or truncated)
                            terminal_observed = terminal_observed or done
                            steps_completed += 1
                            progress(1, int(done))
                            if after_step is not None:
                                after_step(
                                    {
                                        "source": source,
                                        "n_uavs": n_uavs,
                                        "capacity": capacity,
                                        "world_id": world_id,
                                        "step": t,
                                        "steps_completed": steps_completed,
                                        "terminal_observed": done,
                                    }
                                )

                            rng_before = _rng_digest()
                            diagnostic = service_diagnostics(native)
                            diagnostic_rng_unchanged &= rng_before == _rng_digest()
                            components = step_info["reward_components"]["reward_info"]
                            finite(
                                (next_observation, step_info["next_state"], components),
                                "load probe transition",
                            )
                            for name in COMPONENTS:
                                values[f"component_{name}"].append(float(components[name]))
                            values["scalar_reward"].append(float(reward))
                            values["e_i"].append(diagnostic["e_i"])
                            counts = diagnostic["user_counts"]
                            values["served_count"].append(counts["served"])
                            values["eligible_count"].append(counts["eligible"])
                            values["eligible_unserved_count"].append(
                                counts["eligible_unserved"]
                            )
                            values["ineligible_count"].append(counts["ineligible"])
                            values["occupancy_rate"].append(
                                diagnostic["occupancy"]["rate"]
                            )
                            values["full_uav_rate"].append(
                                diagnostic["full_uavs"]["rate"]
                            )
                            values["overflow_uavs"].append(
                                sum(
                                    int(row["e_i"] > capacity)
                                    for row in diagnostic["per_uav"]
                                )
                            )
                            values["visibility_truncated"].append(
                                diagnostic["visible_user_truncation"]["numerator"]
                            )
                            values["visibility_denominator"].append(
                                diagnostic["visible_user_truncation"]["denominator"]
                            )
                            quality = diagnostic["quality_composition"]
                            values["quality_sum"].append(quality["normalized_sinr_sum"])
                            values["quality_mean"].append(quality["normalized_sinr_mean"])
                            identity = diagnostic["capacity_identity"]
                            values["identity_applicable"].append(identity["applicable"])
                            values["identity_holds"].append(
                                bool(identity["holds"]) if identity["applicable"] else False
                            )
                            values["identity_reasons"].append(
                                json.dumps(identity["reasons"], sort_keys=True)
                            )
                            values["maximum_eligible_uavs"].append(
                                diagnostic["at_most_one_eligible"][
                                    "maximum_eligible_uavs_per_user"
                                ]
                            )

                            state = np.asarray(step_info["next_state"])
                            observation = np.asarray(next_observation)
                            values["observations"].append(observation.copy())
                            values["encoded_states"].append(state.copy())
                            values["native_positions"].append(
                                np.asarray(native.uav_positions).copy()
                            )
                            values["native_user_positions"].append(
                                np.asarray(native.user_positions).copy()
                            )
                            values["sinr"].append(np.asarray(native.sinr_matrix).copy())
                            values["connections"].append(
                                np.asarray(native.connections).copy()
                            )
                            # Environment stepping and diagnostics cannot mutate agent runtime;
                            # the post-action fingerprint is therefore the next pre-action one.
                            values["runtime_before_action"].append(
                                values["runtime_after_action"][-1]
                            )
                            dones[0] = done
                            steps[0] += 1
                            if done != (t == spec.horizon - 1):
                                raise ValueError("unexpected load-probe terminal boundary")
                    if not dones[0]:
                        raise ValueError("load probe missed fixed terminal boundary")
                    trace = _trace_from_lists(values)
                    trace_record = _save_trace(trace_path, trace)
                    world_row = {
                        "world_id": world_id,
                        "runtime_seed": seed,
                        "status": "complete",
                        "steps": steps_completed,
                        "episode_complete": terminal_observed,
                        "native_terminal_observed": terminal_observed,
                        **_world_summary(trace, n_uavs),
                        "trace": trace_record,
                    }
                    worlds.append(world_row)
                    if world_progress is not None:
                        world_progress(world_row)
                except Exception:
                    trace = _trace_from_lists(values)
                    partial_name = trace_path.with_name(trace_path.stem + "_partial.npz")
                    trace_record = _save_trace(partial_name, trace)
                    world_row = {
                        "world_id": world_id,
                        "runtime_seed": seed,
                        "status": "failed",
                        "steps": steps_completed,
                        "episode_complete": terminal_observed,
                        "native_terminal_observed": terminal_observed,
                        "trace": trace_record,
                    }
                    worlds.append(world_row)
                    if world_progress is not None:
                        world_progress(world_row)
                    raise
            finally:
                env.close()

        if any(calls.values()):
            raise ValueError(f"load probe made optimizer calls: {calls}")
        if digest_agent(agent) != model_before or _normalizer_record(agent) != normalizers_before:
            raise ValueError("load probe modified checkpoint parameters or normalizers")
        if not diagnostic_rng_unchanged:
            raise ValueError("load-probe diagnostics consumed global RNG")
        if not raw_actions_unchanged or not logprobs_unchanged:
            raise ValueError("action mapping mutated policy outputs or log probabilities")
        if file_sha256(record["checkpoint"]) != record["checkpoint_sha256_before"]:
            raise ValueError("source checkpoint changed during evaluation")

        return {
            "status": "complete",
            "arm": source.arm,
            "seed": source.seed,
            "source_tag": source.tag,
            "test_n": n_uavs,
            "capacity": capacity,
            "total_capacity": n_uavs * capacity,
            "steps": len(spec.world_ids) * spec.horizon,
            "episodes": len(spec.world_ids),
            "worlds": worlds,
            "J": [row["J"] for row in worlds],
            "component_means": {
                name: [row["component_means"][name] for row in worlds] for name in COMPONENTS
            },
            "model_normalizer_digest_before": model_before,
            "model_normalizer_digest_after": digest_agent(agent),
            "normalizers": normalizers_before,
            "optimizer_calls": calls.copy(),
            "training_team_steps": 0,
            "updates": 0,
            "checkpoint_sha256_before": record["checkpoint_sha256_before"],
            "checkpoint_sha256_after": file_sha256(record["checkpoint"]),
            "diagnostics_consumed_no_global_rng": diagnostic_rng_unchanged,
            "policy_outputs_unchanged_by_mapping": raw_actions_unchanged,
            "action_logprobs_unchanged_by_mapping": logprobs_unchanged,
            "config": config_dict(config),
            "active_inference_rows": 1,
        }
    finally:
        for handle in handles:
            handle.remove()
        config_env.close()
        del agent


def _load_trace(out: Path, record: dict[str, Any]) -> dict[str, np.ndarray]:
    path = Path(out) / record["path"]
    if file_sha256(path) != record["sha256"]:
        raise ValueError(f"trace digest mismatch: {path.name}")
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def _signed(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "values": array.tolist(),
        "mean": float(array.mean()),
        "sample_std": float(array.std(ddof=1)) if len(array) > 1 else None,
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "negative": int(np.count_nonzero(array < 0)),
        "zero": int(np.count_nonzero(array == 0)),
        "positive": int(np.count_nonzero(array > 0)),
        "unit": "paired world; descriptive only",
    }


def compare_capacity_pair(
    low: dict[str, Any], high: dict[str, Any], out: Path
) -> dict[str, Any]:
    for field in ("arm", "seed", "source_tag", "test_n"):
        if low[field] != high[field]:
            raise ValueError(f"capacity pair differs at {field}")
    if low["capacity"] >= high["capacity"]:
        raise ValueError("capacity pair is not low-to-high")
    worlds = []
    exact_fields = (
        "raw_actions",
        "executed_actions",
        "action_logprobs",
        "observations",
        "encoded_states",
        "native_positions",
        "native_user_positions",
        "sinr",
        "runtime_before_action",
        "runtime_after_action",
    )
    for low_world, high_world in zip(low["worlds"], high["worlds"], strict=True):
        if low_world["world_id"] != high_world["world_id"]:
            raise ValueError("capacity pair world ordering differs")
        left = _load_trace(out, low_world["trace"])
        right = _load_trace(out, high_world["trace"])
        mismatched = [name for name in exact_fields if not np.array_equal(left[name], right[name])]
        if mismatched:
            raise ValueError(
                f"same-policy N={low['test_n']} capacity trajectories differ: {mismatched}"
            )
        components = {}
        for name in COMPONENTS:
            difference = high_world["component_means"][name] - low_world["component_means"][name]
            components[name] = float(difference)
        if components["energy_penalty"] != 0.0:
            raise ValueError("height penalty did not cancel in a same-N capacity pair")
        delta_j = high_world["J"] - low_world["J"]
        decomposed = 0.7 * components["coverage_reward"] + 0.3 * components["quality_reward"]
        if not np.isclose(delta_j, decomposed, atol=1e-7, rtol=1e-6):
            raise ValueError("capacity-effect component decomposition failed")
        worlds.append(
            {
                "world_id": low_world["world_id"],
                "delta_J": float(delta_j),
                "component_deltas": components,
                "delta_mean_served": float(
                    high_world["mean_served"] - low_world["mean_served"]
                ),
                "all_runtime_and_trajectory_fields_exact": True,
            }
        )
    return {
        "arm": low["arm"],
        "test_n": low["test_n"],
        "low_capacity": low["capacity"],
        "high_capacity": high["capacity"],
        "worlds": worlds,
        "delta_J": _signed([row["delta_J"] for row in worlds]),
        "delta_mean_served": _signed([row["delta_mean_served"] for row in worlds]),
        "component_deltas": {
            name: _signed([row["component_deltas"][name] for row in worlds])
            for name in COMPONENTS
        },
        "exact_same_policy_capacity_trajectories": True,
        "height_cancels": True,
    }


def reduce_results(cells: list[dict[str, Any]], capacity_pairs: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {(arm, n, capacity) for arm, _seed, _tag in SOURCE_POLICIES for n, capacity in CELLS}
    by_key = {(cell["arm"], cell["test_n"], cell["capacity"]): cell for cell in cells}
    if set(by_key) != expected or any(cell.get("status") != "complete" for cell in cells):
        raise ValueError("five-cell reduction requires all ten completed policy cells")
    world_ids = [row["world_id"] for row in next(iter(by_key.values()))["worlds"]]

    gaps = {}
    for n, capacity in CELLS:
        h6 = by_key[("H6", n, capacity)]
        set_cell = by_key[("SET", n, capacity)]
        values = [a - b for a, b in zip(h6["J"], set_cell["J"], strict=True)]
        component_gaps = {}
        for name in COMPONENTS:
            component_gaps[name] = [
                a - b
                for a, b in zip(
                    h6["component_means"][name],
                    set_cell["component_means"][name],
                    strict=True,
                )
            ]
        for index, value in enumerate(values):
            expected_value = (
                0.7 * component_gaps["coverage_reward"][index]
                + 0.3 * component_gaps["quality_reward"][index]
                - component_gaps["energy_penalty"][index]
            )
            if not np.isclose(value, expected_value, atol=1e-7, rtol=1e-6):
                raise ValueError("H6-SET component decomposition failed")
        gaps[(n, capacity)] = {
            "N": n,
            "capacity": capacity,
            "total_capacity": n * capacity,
            "H6_minus_SET": _signed(values),
            "component_gaps": {name: _signed(rows) for name, rows in component_gaps.items()},
        }

    pair_by = {(row["arm"], row["test_n"]): row for row in capacity_pairs}
    d_by_n = {}
    for n in (4, 8):
        h6_pair = pair_by[("H6", n)]
        set_pair = pair_by[("SET", n)]
        h6 = h6_pair["delta_J"]["values"]
        set_values = set_pair["delta_J"]["values"]
        d_values = [a - b for a, b in zip(h6, set_values, strict=True)]
        component_d = {
            name: [
                a - b
                for a, b in zip(
                    h6_pair["component_deltas"][name]["values"],
                    set_pair["component_deltas"][name]["values"],
                    strict=True,
                )
            ]
            for name in COMPONENTS
        }
        for index, value in enumerate(d_values):
            expected_value = (
                0.7 * component_d["coverage_reward"][index]
                + 0.3 * component_d["quality_reward"][index]
                - component_d["energy_penalty"][index]
            )
            if not np.isclose(value, expected_value, atol=1e-7, rtol=1e-6):
                raise ValueError("D_N component decomposition failed")
        d_by_n[str(n)] = {
            "D": _signed(d_values),
            "component_D": {name: _signed(values) for name, values in component_d.items()},
        }

    matched_k = {}
    for total, low_key, high_key in (
        (40, (4, 10), (8, 5)),
        (80, (4, 20), (8, 10)),
    ):
        matched_k[str(total)] = _signed(
            [
                high - low
                for low, high in zip(
                    gaps[low_key]["H6_minus_SET"]["values"],
                    gaps[high_key]["H6_minus_SET"]["values"],
                    strict=True,
                )
            ]
        )
    c10 = {}
    for left, right in ((4, 6), (6, 8), (4, 8)):
        c10[f"N{right}_minus_N{left}"] = _signed(
            [
                high - low
                for low, high in zip(
                    gaps[(left, 10)]["H6_minus_SET"]["values"],
                    gaps[(right, 10)]["H6_minus_SET"]["values"],
                    strict=True,
                )
            ]
        )
    return {
        "world_ids": world_ids,
        "gaps": {f"N{n}_c{capacity}": row for (n, capacity), row in gaps.items()},
        "absolute_capacity_effects": capacity_pairs,
        "D_N": d_by_n,
        "matched_total_capacity_cross_N_residual": matched_k,
        "same_c10_secondary_contrast": c10,
        "inference_limit": (
            "descriptive paired-world spread only; one frozen training instance per package"
        ),
    }


def _assert_scientific_spec(spec: ProbeSpec) -> None:
    if spec != DEFAULT_SPEC:
        raise ValueError("production entry binds the full five-cell 16-world x 500-step ProbeSpec")


def _refuse_existing_scientific_outputs(out: Path) -> None:
    conflicts = []
    for name in ("summary.json", "summary.json.partial", "error.txt", "runtime_logs"):
        if (out / name).exists():
            conflicts.append(name)
    for pattern in (
        "trace_*.npz",
        "trace_*.npz.partial",
        "cell_*.json",
        "cell_*.json.partial",
        "pair_*.json",
        "pair_*.json.partial",
    ):
        conflicts.extend(path.name for path in out.glob(pattern))
    if conflicts:
        raise ValueError(f"existing scientific outputs require reconciliation: {sorted(set(conflicts))}")


def run_probe_impl(
    out: Path,
    checkpoint_root: Path,
    launch_sha: str,
    admission: dict[str, Any],
    spec: ProbeSpec,
    *,
    tracked_summary_root: Path = TRACKED_SOURCE_ROOT,
    repository_root: Path = REPOSITORY_ROOT,
    command_start: float | None = None,
    after_step: Callable[[dict[str, Any]], None] | None = None,
) -> int:
    """Technical core. The production wrapper fixes spec and committed source locations."""
    out = Path(out)
    checkpoint_root = Path(checkpoint_root)
    out.mkdir(parents=True, exist_ok=True)
    _refuse_existing_scientific_outputs(out)
    started = time.perf_counter()
    command_start = started if command_start is None else command_start
    summary: dict[str, Any] = {
        "schema": 1,
        "object_id": OBJECT_ID,
        "direction": DIRECTION,
        "launch_sha": launch_sha,
        "admission": admission,
        "status": "initializing",
        "failure": None,
        "spec": jsonable(vars(spec)),
        "producer_sha": PRODUCER_SHA,
        "source_policies": [
            {"arm": arm, "seed": seed, "tag": tag} for arm, seed, tag in SOURCE_POLICIES
        ],
        "input_checkpoints": [],
        "cells": [],
        "capacity_pairs": [],
        "aggregates": None,
        "trace_indexing": {
            "base": "zero-based",
            "transition": (
                "observation/state/position/SINR/connection[t] precede action[t]; "
                "action[t] and old_logprob[t] produce successor arrays[t+1]"
            ),
        },
        "counts": {
            "fits": 0,
            "training_team_steps": 0,
            "training_episodes": 0,
            "updates": 0,
            "optimizer_calls": 0,
            "evaluation_team_steps": 0,
            "evaluation_episodes": 0,
            "completed_cells": 0,
            "completed_worlds": 0,
            "technical_input_checks": 0,
        },
        "runtime": {
            "python": sys.version,
            "torch": torch.__version__,
            "numpy": np.__version__,
            "device": "cpu",
            "policy_dtype": "float32",
            "physical_position_dtype": "float64",
            "torch_threads": spec.torch_threads,
            "source_num_envs": spec.source_num_envs,
            "active_inference_rows": 1,
            "thread_environment": {
                name: os.environ.get(name)
                for name in (
                    "OMP_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
            },
        },
        "interpretation_limits": [
            "fixed-policy service conversion; capacity is not an actor input",
            "worlds are paired layout units, not independent training replications",
            "matched total capacity does not isolate a pure count effect",
        ],
    }

    def publish(boundary: str) -> None:
        summary["last_boundary"] = boundary
        summary["command_wall_seconds"] = time.perf_counter() - command_start
        summary["run_probe_wall_seconds"] = time.perf_counter() - started
        write_json(out / "summary.json", summary)

    publish("admitted")
    active_cell: dict[str, Any] | None = None
    try:
        torch.set_num_threads(spec.torch_threads)
        records = []
        for arm, seed, tag in SOURCE_POLICIES:
            row = {"arm": arm, "seed": seed, "tag": tag, "status": "verifying"}
            summary["input_checkpoints"].append(row)
            try:
                record = load_source_policy(
                    checkpoint_root,
                    SourcePolicy(arm, seed, tag),
                    tracked_summary_root=tracked_summary_root,
                    repository_root=repository_root,
                )
            except Exception as exc:
                row.update(status="failed", failure=f"{type(exc).__name__}: {exc}")
                publish(f"source {tag} refused")
                raise
            records.append(record)
            row.update(
                status="verified",
                committed_summary=record["summary_identity"],
                checkpoint=str(record["checkpoint"]),
                checkpoint_sha256=record["checkpoint_sha256_before"],
                checkpoint_bytes=record["checkpoint_record"]["bytes"],
                rollout=45,
            )
            summary["counts"]["technical_input_checks"] += 1
            publish(f"source {tag} verified")

        summary["status"] = "evaluating"
        for record in records:
            by_n: dict[int, dict[int, dict[str, Any]]] = {}
            for n_uavs, capacity in spec.cells:
                cell = {
                    "arm": record["source"].arm,
                    "seed": record["source"].seed,
                    "source_tag": record["source"].tag,
                    "test_n": n_uavs,
                    "capacity": capacity,
                    "status": "running",
                    "steps": 0,
                    "episodes": 0,
                    "worlds": [],
                }
                summary["cells"].append(cell)
                active_cell = cell
                publish(f"{record['source'].arm} N={n_uavs} c={capacity} starting")

                def progress(steps: int, episodes: int) -> None:
                    cell["steps"] += steps
                    cell["episodes"] += episodes
                    summary["counts"]["evaluation_team_steps"] += steps
                    summary["counts"]["evaluation_episodes"] += episodes

                def record_world(row: dict[str, Any]) -> None:
                    cell["worlds"].append(row)
                    if row["status"] == "complete":
                        summary["counts"]["completed_worlds"] += 1

                result = evaluate_cell(
                    record,
                    n_uavs,
                    capacity,
                    out,
                    spec,
                    progress=progress,
                    after_step=after_step,
                    world_progress=record_world,
                )
                if (cell["steps"], cell["episodes"]) != (result["steps"], result["episodes"]):
                    raise ValueError("live cell progress differs from completed result")
                cell.clear()
                cell.update(result)
                summary["counts"]["completed_cells"] += 1
                summary["counts"]["optimizer_calls"] += sum(result["optimizer_calls"].values())
                write_json(out / f"cell_{result['arm'].lower()}_n{n_uavs}_c{capacity}.json", result)
                publish(f"{record['source'].arm} N={n_uavs} c={capacity} complete")
                by_n.setdefault(n_uavs, {})[capacity] = result
                active_cell = None

            for n_uavs in (4, 8):
                capacities = sorted(by_n[n_uavs])
                pair = compare_capacity_pair(
                    by_n[n_uavs][capacities[0]], by_n[n_uavs][capacities[1]], out
                )
                summary["capacity_pairs"].append(pair)
                write_json(out / f"pair_{record['source'].arm.lower()}_n{n_uavs}.json", pair)

        summary["aggregates"] = reduce_results(summary["cells"], summary["capacity_pairs"])
        expected_steps = len(SOURCE_POLICIES) * len(spec.cells) * len(spec.world_ids) * spec.horizon
        expected_episodes = len(SOURCE_POLICIES) * len(spec.cells) * len(spec.world_ids)
        if summary["counts"]["evaluation_team_steps"] != expected_steps:
            raise ValueError("evaluation transition count is incomplete")
        if summary["counts"]["evaluation_episodes"] != expected_episodes:
            raise ValueError("evaluation episode count is incomplete")
        if any(
            summary["counts"][name]
            for name in ("fits", "training_team_steps", "training_episodes", "updates", "optimizer_calls")
        ):
            raise ValueError("frozen evaluation reported learning work")
        summary["status"] = "complete"
        return_code = 0
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
        if active_cell is not None and active_cell.get("status") == "running":
            active_cell.update(status="failed", failure=failure)
        summary.update(status="failed", failure=failure)
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


def run_probe(
    out: Path,
    checkpoint_root: Path,
    launch_sha: str,
    admission: dict[str, Any],
    *,
    command_start: float | None = None,
) -> int:
    _assert_scientific_spec(DEFAULT_SPEC)
    return run_probe_impl(
        out,
        checkpoint_root,
        launch_sha,
        admission,
        DEFAULT_SPEC,
        command_start=command_start,
    )
