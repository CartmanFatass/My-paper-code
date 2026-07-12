"""Run the frozen R27-G1 low-actor capacity autopsy."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator, Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.low_actor_capacity_audit import (  # noqa: E402
    CapacitySnapshotBatch,
    INACTIVE_TOLERANCE,
    MIN_BOOTSTRAP_RESET_GROUPS,
    PARITY_TOLERANCE,
    RECURRENT_RETENTION_MAX,
    STATIC_SKL_MIN,
    STATIC_STDMEAN_MIN,
    SyntheticFitConfig,
    _actor_parameter_count,
    _actor_state_sha256,
    _decide_synthetic_seed_gate,
    _terminal_synthetic_seed_report,
    build_orthogonal_codebook,
    classify_capacity_autopsy,
    evaluate_static_checkpoint,
    evaluate_synthetic_seed,
    gate_static_family,
    gate_synthetic_family,
    grouped_reset_split,
    read_capacity_snapshot_shards,
    static_capacity_thresholds,
    synthetic_capacity_thresholds,
    write_capacity_snapshot_shard,
)


REGISTERED_CHECKPOINTS: dict[str, dict[str, object]] = {
    "arm0_update25": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt",
        "update_idx": 25,
        "total_steps": 800000,
        "sha256": "3f6404cd54e75f3f39af0cffb56c444dda78acd05993f1b6efd9cdc77ad9ca54",
    },
    "arm0_update30": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt",
        "update_idx": 30,
        "total_steps": 960000,
        "sha256": "6553e97c032e54f0a19cf801e451298d6b56232720d82a8e26abbdb7171acabc",
    },
    "arm0_final": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt",
        "update_idx": 32,
        "total_steps": 1000000,
        "sha256": "eeaa4f7ec32314d47be818f20c76758c47a97b7881aa997511a2660bb5632c36",
    },
}
SCIENTIFIC_SYNTHETIC_SEEDS = (17, 23, 41)
SCIENTIFIC_DECISION_THRESHOLDS: dict[str, object] = {
    "static_checkpoint": static_capacity_thresholds(),
    "static_family": {
        "agreeing_checkpoints_min": 2,
        "recurrent_retention_max": RECURRENT_RETENTION_MAX,
    },
    "synthetic_seed": synthetic_capacity_thresholds(4),
    "synthetic_family": {
        "passing_seeds_min": 2,
        "fixed_seed_count": len(SCIENTIFIC_SYNTHETIC_SEEDS),
        "minimum_reset_groups": MIN_BOOTSTRAP_RESET_GROUPS,
    },
    "codebook_norm": 0.5,
}
SCIENTIFIC_CONTRACT: dict[str, object] = {
    "experiment_id": "EXP-20260711-r27-g1-low-actor-capacity-autopsy",
    "checkpoint_ids": list(REGISTERED_CHECKPOINTS),
    "n_resets": 64,
    "num_envs": 64,
    "collector_backend": "subproc",
    "collector_start_method": "spawn",
    "parallel_collection_schedule": "step_major_env_id_ascending",
    "seed": 1,
    "n_agents": 6,
    "scenario": "energy",
    "preset": "S7-S1",
    "skill_interval": 10,
    "episode_max_steps": 500,
    "bootstrap_reps": 1000,
    "static_bootstrap_seed": 27021,
    "split_seed": 27011,
    "codebook_seed": 27030,
    "synthetic_seeds": list(SCIENTIFIC_SYNTHETIC_SEEDS),
    "learning_rate": 3e-4,
    "batch_size": 256,
    "max_steps": 1000,
    "validation_interval": 25,
    "patience": 20,
    "min_delta": 1e-4,
    "decision_thresholds": SCIENTIFIC_DECISION_THRESHOLDS,
}


def _stable_payload_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


SCIENTIFIC_CONTRACT_SHA256 = _stable_payload_sha256(SCIENTIFIC_CONTRACT)


def _path_matches_registered(actual: str | Path, expected: str) -> bool:
    actual_parts = tuple(part.lower() for part in Path(actual).parts)
    expected_parts = tuple(part.lower() for part in Path(expected).parts)
    return (
        len(actual_parts) >= len(expected_parts)
        and actual_parts[-len(expected_parts) :] == expected_parts
    )


def _require_exact_value(
    args: argparse.Namespace, name: str, expected: object
) -> None:
    actual = getattr(args, name)
    if isinstance(expected, float):
        equal = float(actual) == float(expected)
    elif isinstance(expected, tuple):
        equal = tuple(actual) == expected
    else:
        equal = actual == expected
    if not equal:
        raise ValueError(f"{name} must equal {expected!r}; got {actual!r}")


def validate_scientific_args(args: argparse.Namespace) -> dict[str, object]:
    """Resolve the immutable R27 contract before any scientific output write."""

    if bool(getattr(args, "non_scientific_fixture", False)):
        return {
            "mode": "NON_SCIENTIFIC_FIXTURE",
            "eligible_for_aggregate": False,
            "scientific_contract_sha256": SCIENTIFIC_CONTRACT_SHA256,
        }
    if args.command not in ("collect-static", "synthetic"):
        return {
            "mode": "R27_G1_SCIENTIFIC",
            "eligible_for_aggregate": True,
            "scientific_contract_sha256": SCIENTIFIC_CONTRACT_SHA256,
        }

    for name, expected in (
        ("config", "ha_ctse_process.config"),
        ("scenario", "energy"),
        ("preset", "S7-S1"),
        ("seed", 1),
        ("n_agents", 6),
    ):
        _require_exact_value(args, name, expected)
    if not str(args.device).lower().startswith("cuda"):
        raise ValueError("device must be CUDA for the scientific contract")

    if args.command == "collect-static":
        checkpoint_id = str(args.checkpoint_id)
        if checkpoint_id not in REGISTERED_CHECKPOINTS:
            raise ValueError(
                "checkpoint_id must be one of "
                f"{tuple(REGISTERED_CHECKPOINTS)}"
            )
        registered = REGISTERED_CHECKPOINTS[checkpoint_id]
        _require_exact_value(args, "checkpoint_update", registered["update_idx"])
        if not _path_matches_registered(args.checkpoint, str(registered["path"])):
            raise ValueError(
                f"checkpoint path does not match registered {checkpoint_id} path"
            )
        for name, expected in (
            ("skill_interval", 10),
            ("n_resets", 64),
            ("num_envs", 64),
            ("collector_backend", "subproc"),
            ("collector_start_method", "spawn"),
            ("episode_max_steps", 500),
            ("bootstrap_reps", 1000),
            ("bootstrap_seed", 27021),
        ):
            _require_exact_value(args, name, expected)
    else:
        registered = REGISTERED_CHECKPOINTS["arm0_final"]
        if not _path_matches_registered(args.checkpoint, str(registered["path"])):
            raise ValueError("synthetic checkpoint must be registered arm0_final")
        for name, expected in (
            ("split_seed", 27011),
            ("codebook_seed", 27030),
            ("synthetic_seeds", SCIENTIFIC_SYNTHETIC_SEEDS),
            ("learning_rate", 3e-4),
            ("batch_size", 256),
            ("max_steps", 1000),
            ("validation_interval", 25),
            ("patience", 20),
            ("min_delta", 1e-4),
            ("bootstrap_reps", 1000),
        ):
            _require_exact_value(args, name, expected)
    return {
        "mode": "R27_G1_SCIENTIFIC",
        "eligible_for_aggregate": True,
        "scientific_contract_sha256": SCIENTIFIC_CONTRACT_SHA256,
        "resolved_contract": copy.deepcopy(SCIENTIFIC_CONTRACT),
    }


@dataclass(frozen=True)
class SnapshotCollectorStats:
    resets: int
    renewal_events: int
    snapshot_rows: int


_RUNTIME_ATTRIBUTES = (
    "active_skills",
    "active_duration_indices",
    "duration_remaining",
    "skill_age",
    "has_active_skill",
    "active_team_codes",
    "team_intent_remaining",
    "team_intent_age",
    "low_actor_hxs",
    "low_critic_hxs",
    "_last_low_context",
    "segments",
    "situation_debouncer",
    "per_agent_situation_debouncer",
    "situation_hazard_guard",
    "_last_situation_state",
    "_last_agent_situation_state",
    "_team_transition_open",
    "_team_transition_closed",
    "_team_transition_env_steps",
    "_team_intent_boundary_count",
    "_team_intent_boundary_trunc_fracs",
    "_team_intent_boundary_trunc_by_duration",
    "_team_intent_dwell_checks",
    "_team_intent_age_check_samples",
    "_situation_diag_events",
    "_agent_situation_diag_events",
    "_situation_hazard_forced_renewals",
    "_situation_hazard_events",
)


@contextmanager
def preserve_agent_runtime(agent: Any) -> Iterator[None]:
    """Restore mutable rollout state after a frozen reset collection."""

    missing = object()
    originals: dict[str, Any] = {}
    for name in _RUNTIME_ATTRIBUTES:
        value = getattr(agent, name, missing)
        if value is not missing:
            originals[name] = value
    for name, value in copy.deepcopy(originals).items():
        setattr(agent, name, value)
    try:
        yield
    finally:
        for name, value in originals.items():
            setattr(agent, name, value)


def require_cuda_device(device: str) -> torch.device:
    requested = str(device).strip().lower()
    if requested != "cuda" and not requested.startswith("cuda:"):
        raise ValueError("R27-G1 scientific audit requires --device cuda")
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA was requested for R27-G1 but is unavailable; CPU fallback is forbidden"
        )
    return torch.device(requested)


def _state_from_info(info: Any, previous: Any = None) -> np.ndarray | None:
    mapping = info if isinstance(info, dict) else {}
    state = mapping.get("next_state", mapping.get("state", previous))
    if state is None:
        return None
    return np.asarray(state, dtype=np.float32).reshape(-1)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_registered_checkpoint_identity(
    args: argparse.Namespace,
    metadata: dict[str, object],
    *,
    loaded_update: int,
    checkpoint_sha256: str,
    scientific_contract: dict[str, object],
) -> dict[str, object]:
    """Bind a loaded checkpoint to one exact pre-registered R25 arm0 artifact."""

    if not bool(scientific_contract.get("eligible_for_aggregate")):
        return {
            "mode": "NON_SCIENTIFIC_FIXTURE",
            "eligible_for_aggregate": False,
        }
    checkpoint_id = (
        str(args.checkpoint_id)
        if args.command == "collect-static"
        else "arm0_final"
    )
    if checkpoint_id not in REGISTERED_CHECKPOINTS:
        raise ValueError(f"unregistered checkpoint identity: {checkpoint_id}")
    registered = REGISTERED_CHECKPOINTS[checkpoint_id]
    errors: list[str] = []
    if not _path_matches_registered(args.checkpoint, str(registered["path"])):
        errors.append("checkpoint path does not match registered artifact")
    if int(loaded_update) != int(registered["update_idx"]):
        errors.append(
            f"loaded update {loaded_update} != {registered['update_idx']}"
        )
    if str(checkpoint_sha256).lower() != str(registered["sha256"]).lower():
        errors.append("checkpoint SHA256 does not match registered artifact")
    expected_metadata = {
        "update_idx": int(registered["update_idx"]),
        "total_steps": int(registered["total_steps"]),
        "n_agents": 6,
        "n_skills": 4,
        "preset": "S7-S1",
        "scenario": "energy",
        "low_actor_condition_on_team_code": False,
        "enable_team_intent": True,
    }
    for name, expected in expected_metadata.items():
        if metadata.get(name) != expected:
            errors.append(
                f"checkpoint metadata {name}={metadata.get(name)!r} != {expected!r}"
            )
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "mode": "R27_G1_SCIENTIFIC",
        "eligible_for_aggregate": True,
        "checkpoint_id": checkpoint_id,
        "checkpoint_path": str(registered["path"]),
        "checkpoint_update": int(registered["update_idx"]),
        "checkpoint_total_steps": int(registered["total_steps"]),
        "checkpoint_sha256": str(registered["sha256"]),
        "scientific_contract_sha256": SCIENTIFIC_CONTRACT_SHA256,
    }


def _snapshot_shards_sha256(snapshot_dir: Path) -> str:
    paths = sorted(Path(snapshot_dir).glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no snapshot shards under {snapshot_dir}")
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode("utf-8"))
        digest.update(bytes.fromhex(_file_sha256(path)))
    return digest.hexdigest()


def _snapshot_shard_contract_errors(snapshot_dir: Path) -> list[str]:
    paths = sorted(Path(snapshot_dir).glob("*.npz"))
    actual = [path.name for path in paths]
    expected = [f"reset_{reset_id:04d}.npz" for reset_id in range(64)]
    if actual != expected:
        return [
            "snapshot shards must be exactly reset_0000.npz through "
            f"reset_0063.npz; found {len(actual)} files"
        ]
    errors: list[str] = []
    for reset_id, path in enumerate(paths):
        try:
            with np.load(path, allow_pickle=False) as data:
                expected_fields = {
                    "env_id": reset_id,
                    "reset_id": reset_id,
                    "episode_id": reset_id,
                    "reset_seed": reset_id + 1,
                }
                for field, expected_value in expected_fields.items():
                    values = np.asarray(data[field], dtype=np.int64).reshape(-1)
                    if values.size and not np.all(values == expected_value):
                        errors.append(
                            f"{path.name} {field} mapping mismatch"
                        )
        except (KeyError, OSError, ValueError) as error:
            errors.append(f"{path.name} identity read failed: {error}")
    return errors


def _parallel_manifest_contract_valid(manifest: dict[str, object]) -> bool:
    expected_ids = {str(env_id): env_id for env_id in range(64)}
    expected_seeds = {str(env_id): env_id + 1 for env_id in range(64)}
    active_steps = manifest.get("active_steps_by_env")
    termination_reasons = manifest.get("termination_reason_by_env")
    return bool(
        manifest.get("num_envs") == 64
        and manifest.get("collector_backend") == "subproc"
        and manifest.get("collector_start_method") == "spawn"
        and manifest.get("parallel_collection_schedule")
        == "step_major_env_id_ascending"
        and manifest.get("env_id_to_reset_id") == expected_ids
        and manifest.get("env_id_to_reset_seed") == expected_seeds
        and isinstance(active_steps, dict)
        and set(active_steps) == set(expected_ids)
        and all(
            isinstance(value, int) and 1 <= value <= 500
            for value in active_steps.values()
        )
        and isinstance(termination_reasons, dict)
        and set(termination_reasons) == set(expected_ids)
        and set(termination_reasons.values())
        <= {"terminated", "truncated", "step_limit"}
    )


def _read_json_strict(path: Path) -> dict[str, object]:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON constant {value} in {path}")

    payload = json.loads(
        Path(path).read_text(encoding="utf-8"), parse_constant=reject_constant
    )
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def validate_synthetic_snapshot_source(
    snapshot_dir: Path,
    snapshots: CapacitySnapshotBatch,
    *,
    scientific_contract: dict[str, object],
) -> dict[str, object]:
    """Bind synthetic fitting to the registered arm0-final snapshot artifact."""

    if not bool(scientific_contract.get("eligible_for_aggregate")):
        return {
            "mode": "NON_SCIENTIFIC_FIXTURE",
            "eligible_for_aggregate": False,
        }
    snapshot_root = Path(snapshot_dir)
    manifest_path = snapshot_root.parent / "collector_manifest.json"
    manifest = _read_json_strict(manifest_path)
    registered = REGISTERED_CHECKPOINTS["arm0_final"]
    actual_snapshot_sha256 = _snapshot_shards_sha256(snapshot_root)
    checkpoint_ids = set(
        np.asarray(snapshots.checkpoint_id, dtype=np.str_).reshape(-1).tolist()
    )
    checkpoint_updates = set(
        np.asarray(snapshots.checkpoint_update, dtype=np.int64)
        .reshape(-1)
        .tolist()
    )
    errors: list[str] = []
    errors.extend(_snapshot_shard_contract_errors(snapshot_root))
    if checkpoint_ids != {"arm0_final"} or checkpoint_updates != {32}:
        errors.append(
            "snapshot rows are not arm0_final/update32: "
            f"ids={sorted(checkpoint_ids)}, updates={sorted(checkpoint_updates)}"
        )
    checks = (
        (
            manifest.get("checkpoint_id") == "arm0_final",
            "collector manifest checkpoint_id mismatch",
        ),
        (
            manifest.get("checkpoint_update") == 32,
            "collector manifest update mismatch",
        ),
        (
            _path_matches_registered(
                str(manifest.get("checkpoint", "")), str(registered["path"])
            ),
            "collector manifest checkpoint path mismatch",
        ),
        (
            str(manifest.get("checkpoint_sha256_before", "")).lower()
            == str(registered["sha256"]).lower(),
            "collector manifest checkpoint hash mismatch",
        ),
        (
            manifest.get("checkpoint_sha256_equal") is True
            and manifest.get("policy_parameter_sha256_equal") is True,
            "collector manifest immutability flags failed",
        ),
        (
            manifest.get("n_resets") == 64
            and manifest.get("reset_seeds") == list(range(1, 65)),
            "collector manifest reset contract mismatch",
        ),
        (
            _parallel_manifest_contract_valid(manifest),
            "collector manifest parallel contract mismatch",
        ),
        (
            str(manifest.get("device", "")).lower().startswith("cuda"),
            "collector manifest device is not CUDA",
        ),
        (
            manifest.get("snapshot_shards_sha256")
            == actual_snapshot_sha256,
            "snapshot shard hash does not match collector manifest",
        ),
        (
            manifest.get("scientific_contract_sha256")
            == SCIENTIFIC_CONTRACT_SHA256
            and bool(
                manifest.get("scientific_contract", {}).get(
                    "eligible_for_aggregate", False
                )
            ),
            "collector manifest is not scientific-contract eligible",
        ),
    )
    errors.extend(reason for passed, reason in checks if not passed)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "mode": "R27_G1_SCIENTIFIC",
        "eligible_for_aggregate": True,
        "source_collector_manifest": str(manifest_path),
        "source_collector_manifest_sha256": _file_sha256(manifest_path),
        "source_snapshot_shards_sha256": actual_snapshot_sha256,
        "source_checkpoint_sha256": str(registered["sha256"]),
    }


def policy_parameter_sha256(agent: Any) -> str:
    digest = hashlib.sha256()
    seen_modules: set[int] = set()
    for attribute, value in sorted(vars(agent).items()):
        if not isinstance(value, torch.nn.Module) or id(value) in seen_modules:
            continue
        seen_modules.add(id(value))
        for name, parameter in sorted(value.named_parameters()):
            tensor = parameter.detach().cpu().contiguous()
            digest.update(f"{attribute}.{name}".encode("utf-8"))
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(np.asarray(tensor.shape, dtype=np.int64).tobytes())
            digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _set_eval_mode(agent: Any) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if isinstance(value, torch.nn.Module) and id(value) not in seen:
            seen.add(id(value))
            value.eval()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    Path(path).write_text(
        json.dumps(
            _jsonable(payload), indent=2, sort_keys=True, allow_nan=False
        )
        + "\n",
        encoding="utf-8",
    )


def _rows_to_batch(
    rows: list[dict[str, Any]],
    *,
    observation_dim: int,
    hidden_dim: int,
) -> CapacitySnapshotBatch:
    if not rows:
        return CapacitySnapshotBatch(
            observation=np.zeros((0, int(observation_dim)), dtype=np.float32),
            actor_hidden=np.zeros((0, int(hidden_dim)), dtype=np.float32),
            natural_skill=np.zeros(0, dtype=np.int64),
            previous_skill=np.zeros(0, dtype=np.int64),
            duration_idx=np.zeros(0, dtype=np.int64),
            skill_age=np.zeros(0, dtype=np.int64),
            episode_done_mask=np.zeros(0, dtype=np.bool_),
            reset_id=np.zeros(0, dtype=np.int64),
            reset_seed=np.zeros(0, dtype=np.int64),
            episode_id=np.zeros(0, dtype=np.int64),
            env_id=np.zeros(0, dtype=np.int64),
            agent_id=np.zeros(0, dtype=np.int64),
            checkpoint_id=np.zeros(0, dtype=np.str_),
            checkpoint_update=np.zeros(0, dtype=np.int64),
        )
    return CapacitySnapshotBatch(
        observation=np.stack([row["observation"] for row in rows]).astype(
            np.float32
        ),
        actor_hidden=np.stack([row["actor_hidden"] for row in rows]).astype(
            np.float32
        ),
        natural_skill=np.asarray(
            [row["natural_skill"] for row in rows], dtype=np.int64
        ),
        previous_skill=np.asarray(
            [row["previous_skill"] for row in rows], dtype=np.int64
        ),
        duration_idx=np.asarray(
            [row["duration_idx"] for row in rows], dtype=np.int64
        ),
        skill_age=np.asarray([row["skill_age"] for row in rows], dtype=np.int64),
        episode_done_mask=np.asarray(
            [row["episode_done_mask"] for row in rows], dtype=np.bool_
        ),
        reset_id=np.asarray([row["reset_id"] for row in rows], dtype=np.int64),
        reset_seed=np.asarray(
            [row["reset_seed"] for row in rows], dtype=np.int64
        ),
        episode_id=np.asarray(
            [row["episode_id"] for row in rows], dtype=np.int64
        ),
        env_id=np.asarray([row["env_id"] for row in rows], dtype=np.int64),
        agent_id=np.asarray([row["agent_id"] for row in rows], dtype=np.int64),
        checkpoint_id=np.asarray(
            [row["checkpoint_id"] for row in rows], dtype=np.str_
        ),
        checkpoint_update=np.asarray(
            [row["checkpoint_update"] for row in rows], dtype=np.int64
        ),
    )


def collect_capacity_reset(
    env: Any,
    agent: Any,
    *,
    reset_id: int,
    reset_seed: int,
    episode_id: int,
    skill_interval: int,
    episode_max_steps: int,
    checkpoint_id: str,
    checkpoint_update: int,
) -> tuple[CapacitySnapshotBatch, SnapshotCollectorStats]:
    """Collect natural renewal snapshots without retaining runtime mutation."""

    if int(skill_interval) <= 0 or int(episode_max_steps) <= 0:
        raise ValueError("skill_interval and episode_max_steps must be positive")
    rows: list[dict[str, Any]] = []
    renewals = 0
    with preserve_agent_runtime(agent):
        obs, info = env.reset(seed=int(reset_seed))
        obs = np.asarray(obs, dtype=np.float32)
        if obs.ndim != 2 or int(obs.shape[0]) != int(agent.n_agents):
            raise ValueError("environment observation must have one row per agent")
        state = _state_from_info(info)
        agent.reset_env_state(0)
        if hasattr(agent.segments, "active"):
            agent.segments.active[0] = [None for _ in range(int(agent.n_agents))]

        observation_dim = int(obs.shape[1])
        hidden_dim = int(np.asarray(agent.low_actor_hxs[0, 0]).size)
        for step in range(int(episode_max_steps)):
            previous_segments = list(agent.segments.active[0])
            pre_assignment_hidden = np.asarray(
                agent.low_actor_hxs[0], dtype=np.float32
            ).copy()
            with torch.no_grad():
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=int(step),
                    k=int(skill_interval),
                    env_id=0,
                    deterministic=False,
                )
            current_segments = list(agent.segments.active[0])
            changed = [
                agent_id
                for agent_id, (before, after) in enumerate(
                    zip(previous_segments, current_segments)
                )
                if after is not None and after is not before
            ]
            for agent_id in changed:
                renewals += 1
                segment = current_segments[agent_id]
                rows.append(
                    {
                        "observation": np.asarray(
                            obs[agent_id], dtype=np.float32
                        ).copy(),
                        "actor_hidden": pre_assignment_hidden[agent_id].copy(),
                        "natural_skill": int(segment.skill),
                        "previous_skill": int(getattr(segment, "prev_skill", 0)),
                        "duration_idx": int(segment.duration_idx),
                        "skill_age": int(getattr(segment, "skill_age_prev", 0)),
                        "episode_done_mask": False,
                        "reset_id": int(reset_id),
                        "reset_seed": int(reset_seed),
                        "episode_id": int(episode_id),
                        "env_id": 0,
                        "agent_id": int(agent_id),
                        "checkpoint_id": str(checkpoint_id),
                        "checkpoint_update": int(checkpoint_update),
                    }
                )
            with torch.no_grad():
                actions, _, _ = agent.act_low(
                    obs,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
            next_obs, _reward, terminated, truncated, next_info = env.step(
                actions
            )
            obs = np.asarray(next_obs, dtype=np.float32)
            state = _state_from_info(next_info, previous=state)
            if bool(terminated or truncated):
                break

    batch = _rows_to_batch(
        rows, observation_dim=observation_dim, hidden_dim=hidden_dim
    )
    return batch, SnapshotCollectorStats(
        resets=1, renewal_events=renewals, snapshot_rows=len(rows)
    )


def collect_capacity_parallel(
    env_collector: Any,
    agent: Any,
    *,
    base_seed: int,
    n_resets: int,
    skill_interval: int,
    episode_max_steps: int,
    checkpoint_id: str,
    checkpoint_update: int,
) -> tuple[
    dict[int, CapacitySnapshotBatch],
    SnapshotCollectorStats,
    dict[str, object],
]:
    """Collect one frozen episode per environment in step-major order."""

    if int(skill_interval) <= 0 or int(episode_max_steps) <= 0:
        raise ValueError("skill_interval and episode_max_steps must be positive")
    if int(n_resets) <= 0 or int(env_collector.num_envs) != int(n_resets):
        raise ValueError("parallel collection requires one reset per environment")

    rows_by_env: dict[int, list[dict[str, Any]]] = {
        env_id: [] for env_id in range(int(n_resets))
    }
    renewals = 0
    active_steps = {env_id: 0 for env_id in range(int(n_resets))}
    termination_reasons = {
        env_id: "step_limit" for env_id in range(int(n_resets))
    }

    with preserve_agent_runtime(agent):
        observations, states, _infos = env_collector.reset_all(int(base_seed))
        if len(observations) != int(n_resets) or len(states) != int(n_resets):
            raise ValueError("parallel reset result count mismatch")
        observations = [
            np.asarray(observation, dtype=np.float32)
            for observation in observations
        ]
        for env_id, observation in enumerate(observations):
            if (
                observation.ndim != 2
                or int(observation.shape[0]) != int(agent.n_agents)
            ):
                raise ValueError(
                    "environment observation must have one row per agent"
                )
            agent.reset_env_state(env_id)
            if hasattr(agent.segments, "active"):
                agent.segments.active[env_id] = [
                    None for _ in range(int(agent.n_agents))
                ]

        observation_dim = int(observations[0].shape[1])
        hidden_dim = int(np.asarray(agent.low_actor_hxs[0, 0]).size)
        active = set(range(int(n_resets)))
        for step in range(int(episode_max_steps)):
            indexed_actions: list[tuple[int, Any]] = []
            for env_id in sorted(active):
                observation = observations[env_id]
                previous_segments = list(agent.segments.active[env_id])
                pre_assignment_hidden = np.asarray(
                    agent.low_actor_hxs[env_id], dtype=np.float32
                ).copy()
                with torch.no_grad():
                    agent.maybe_assign_skills(
                        observation,
                        state=states[env_id],
                        step=int(step),
                        k=int(skill_interval),
                        env_id=env_id,
                        deterministic=False,
                    )
                current_segments = list(agent.segments.active[env_id])
                changed = [
                    agent_id
                    for agent_id, (before, after) in enumerate(
                        zip(previous_segments, current_segments)
                    )
                    if after is not None and after is not before
                ]
                for agent_id in changed:
                    renewals += 1
                    segment = current_segments[agent_id]
                    rows_by_env[env_id].append(
                        {
                            "observation": np.asarray(
                                observation[agent_id], dtype=np.float32
                            ).copy(),
                            "actor_hidden": pre_assignment_hidden[
                                agent_id
                            ].copy(),
                            "natural_skill": int(segment.skill),
                            "previous_skill": int(
                                getattr(segment, "prev_skill", 0)
                            ),
                            "duration_idx": int(segment.duration_idx),
                            "skill_age": int(
                                getattr(segment, "skill_age_prev", 0)
                            ),
                            "episode_done_mask": False,
                            "reset_id": env_id,
                            "reset_seed": int(base_seed) + env_id,
                            "episode_id": env_id,
                            "env_id": env_id,
                            "agent_id": int(agent_id),
                            "checkpoint_id": str(checkpoint_id),
                            "checkpoint_update": int(checkpoint_update),
                        }
                    )
                with torch.no_grad():
                    actions, _, _ = agent.act_low(
                        observation,
                        env_id=env_id,
                        deterministic=False,
                        state=states[env_id],
                    )
                indexed_actions.append((env_id, actions))

            results = env_collector.step_selected(indexed_actions)
            for env_id in sorted(results):
                result = results[env_id]
                active_steps[env_id] += 1
                observations[env_id] = np.asarray(
                    result.obs, dtype=np.float32
                )
                states[env_id] = _state_from_info(
                    result.info, previous=states[env_id]
                )
                if bool(result.terminated):
                    termination_reasons[env_id] = "terminated"
                    active.remove(env_id)
                elif bool(result.truncated):
                    termination_reasons[env_id] = "truncated"
                    active.remove(env_id)
            if not active:
                break

    batches = {
        env_id: _rows_to_batch(
            rows_by_env[env_id],
            observation_dim=observation_dim,
            hidden_dim=hidden_dim,
        )
        for env_id in range(int(n_resets))
    }
    total_rows = sum(len(rows) for rows in rows_by_env.values())
    evidence: dict[str, object] = {
        "env_id_to_reset_id": {
            str(env_id): env_id for env_id in range(int(n_resets))
        },
        "env_id_to_reset_seed": {
            str(env_id): int(base_seed) + env_id
            for env_id in range(int(n_resets))
        },
        "active_steps_by_env": {
            str(env_id): active_steps[env_id]
            for env_id in range(int(n_resets))
        },
        "termination_reason_by_env": {
            str(env_id): termination_reasons[env_id]
            for env_id in range(int(n_resets))
        },
    }
    return (
        batches,
        SnapshotCollectorStats(
            resets=int(n_resets),
            renewal_events=renewals,
            snapshot_rows=total_rows,
        ),
        evidence,
    )


def _configure_agent(args: argparse.Namespace):
    from ha_ctse_process import train as train_mod

    config = train_mod.load_config(args.config, args.preset or None)
    config.scenario = train_mod.normalize_scenario(args.scenario)
    metadata = train_mod.load_checkpoint_metadata(args.checkpoint)
    train_mod.apply_checkpoint_structure(config, args, metadata)
    if int(args.n_agents) > 0 and metadata.get("n_agents") is None:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(
            int(args.n_agents),
            int(getattr(config, "max_observed_uavs", args.n_agents)),
        )
    env = train_mod.create_env(
        config, config.scenario, int(args.seed), rank=0, scale_mode="eval"
    )
    _obs, info = env.reset(seed=int(args.seed))
    state = _state_from_info(info)
    agent = train_mod.create_agent(
        config,
        args,
        env,
        num_envs=1,
        state_dim=None if state is None else int(state.size),
    )
    _total_steps, loaded_update = train_mod.load_checkpoint(
        args.checkpoint, agent, load_optimizers=False
    )
    _set_eval_mode(agent)
    return config, metadata, env, agent, int(loaded_update)


def _configure_parallel_agent(args: argparse.Namespace):
    from ha_ctse_process import train as train_mod

    config = train_mod.load_config(args.config, args.preset or None)
    config.scenario = train_mod.normalize_scenario(args.scenario)
    metadata = train_mod.load_checkpoint_metadata(args.checkpoint)
    train_mod.apply_checkpoint_structure(config, args, metadata)
    if int(args.n_agents) > 0 and metadata.get("n_agents") is None:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(
            int(args.n_agents),
            int(getattr(config, "max_observed_uavs", args.n_agents)),
        )
    env_collector = train_mod.create_collector(
        config,
        args,
        scale_mode="eval",
        num_envs=int(args.num_envs),
    )
    try:
        env_spec = SimpleNamespace(**env_collector.spec)
        agent = train_mod.create_agent(
            config,
            args,
            env_spec,
            num_envs=int(args.num_envs),
            state_dim=int(env_collector.spec["state_dim"]),
        )
        _total_steps, loaded_update = train_mod.load_checkpoint(
            args.checkpoint, agent, load_optimizers=False
        )
        _set_eval_mode(agent)
    except Exception:
        env_collector.close()
        raise
    return config, metadata, env_collector, agent, int(loaded_update)


def _static_markdown(report: dict[str, object]) -> str:
    zero = report.get("zero_h", {})
    rollout = report.get("rollout_h", {})
    inactive = report.get("inactive_control", {})
    parity = report.get("parity", {})
    return "\n".join(
        [
            f"# R27 Static Capacity: {report.get('checkpoint_id', '')}",
            "",
            f"- Status: `{report.get('status')}`",
            f"- Snapshot rows: {report.get('rows', 0)}",
            f"- Zero-h symmetric KL: {zero.get('mean_skl', 'n/a')}",
            f"- Zero-h standardized mean distance: {zero.get('mean_stdmean_distance', 'n/a')}",
            f"- Rollout-h symmetric KL: {rollout.get('mean_skl', 'n/a')}",
            f"- Rollout-h standardized mean distance: {rollout.get('mean_stdmean_distance', 'n/a')}",
            f"- Hidden retention ratio: {report.get('hidden_retention_ratio', 'n/a')}",
            f"- Inactive maximum symmetric KL: {inactive.get('max_abs_symmetric_kl', 'n/a')}",
            f"- Live parity: {parity.get('pass', False)}",
            "",
            "## Fixed Gates",
            "",
            "- symmetric KL >= 0.02 nats",
            "- standardized action-mean distance >= 0.20",
            "- reset-cluster bootstrap lower bound > 0",
            "- inactive identity separation <= 1e-8",
            "",
            "## Prohibited Next Actions",
            "",
            "No q_A, q_d, q_D, or intrinsic reward is authorized by this checkpoint read.",
            "",
        ]
    )


def run_collect_static(args: argparse.Namespace) -> dict[str, object]:
    require_cuda_device(args.device)
    scientific_contract = validate_scientific_args(args)
    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    output_dir = Path(args.output_dir)
    snapshot_dir = output_dir / "capacity_snapshots"

    np.random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    torch.cuda.manual_seed_all(int(args.seed))
    config, metadata, env_collector, agent, loaded_update = (
        _configure_parallel_agent(args)
    )
    checkpoint_id = str(args.checkpoint_id or checkpoint.stem)
    checkpoint_update = (
        int(args.checkpoint_update)
        if args.checkpoint_update is not None
        else int(metadata.get("update_idx") or loaded_update)
    )
    file_hash_before = _file_sha256(checkpoint)
    try:
        checkpoint_identity = validate_registered_checkpoint_identity(
            args,
            metadata,
            loaded_update=loaded_update,
            checkpoint_sha256=file_hash_before,
            scientific_contract=scientific_contract,
        )
    except Exception:
        env_collector.close()
        raise
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    parameter_hash_before = policy_parameter_sha256(agent)
    reset_seeds = [
        int(args.seed) + env_id for env_id in range(int(args.n_resets))
    ]
    try:
        batches, totals, parallel_evidence = collect_capacity_parallel(
                env_collector,
                agent,
                base_seed=int(args.seed),
                n_resets=int(args.n_resets),
                skill_interval=int(args.skill_interval),
                episode_max_steps=int(args.episode_max_steps),
                checkpoint_id=checkpoint_id,
                checkpoint_update=checkpoint_update,
        )
        for reset_id, batch in batches.items():
            write_capacity_snapshot_shard(
                snapshot_dir / f"reset_{reset_id:04d}.npz", batch
            )
        snapshots = read_capacity_snapshot_shards(snapshot_dir)
        static_report = evaluate_static_checkpoint(
            agent.low,
            snapshots,
            checkpoint_id=checkpoint_id,
            bootstrap_reps=int(args.bootstrap_reps),
            bootstrap_seed=int(args.bootstrap_seed),
        )
        snapshot_shards_sha256 = _snapshot_shards_sha256(snapshot_dir)
    finally:
        env_collector.close()

    file_hash_after = _file_sha256(checkpoint)
    parameter_hash_after = policy_parameter_sha256(agent)
    immutable = bool(
        file_hash_before == file_hash_after
        and parameter_hash_before == parameter_hash_after
    )
    if not immutable:
        static_report = dict(static_report)
        static_report["status"] = "INVALID"
        static_report["immutability_failure"] = True
    static_report = dict(static_report)
    static_report.update(
        {
            "checkpoint_update": checkpoint_update,
            "source_checkpoint_sha256": file_hash_before,
            "snapshot_shards_sha256": snapshot_shards_sha256,
            "scientific_contract_sha256": scientific_contract[
                "scientific_contract_sha256"
            ],
        }
    )
    static_path = output_dir / "static_capacity.json"
    _write_json(static_path, static_report)
    manifest: dict[str, object] = {
        "status": static_report.get("status"),
        "checkpoint": str(checkpoint),
        "checkpoint_id": checkpoint_id,
        "checkpoint_update": checkpoint_update,
        "checkpoint_sha256_before": file_hash_before,
        "checkpoint_sha256_after": file_hash_after,
        "checkpoint_sha256_equal": file_hash_before == file_hash_after,
        "policy_parameter_sha256_before": parameter_hash_before,
        "policy_parameter_sha256_after": parameter_hash_after,
        "policy_parameter_sha256_equal": parameter_hash_before
        == parameter_hash_after,
        "checkpoint_metadata": _jsonable(metadata),
        "parameter_counts": _jsonable(agent.parameter_counts()),
        "device": str(args.device),
        "n_resets": int(args.n_resets),
        "num_envs": int(args.num_envs),
        "collector_backend": str(args.collector_backend),
        "collector_start_method": str(args.collector_start_method),
        "parallel_collection_schedule": "step_major_env_id_ascending",
        "reset_seeds": reset_seeds,
        **parallel_evidence,
        "stats": asdict(totals),
        "field_names": list(CapacitySnapshotBatch.__dataclass_fields__),
        "observation_dim": int(snapshots.observation.shape[1]),
        "hidden_dim": int(snapshots.actor_hidden.shape[1]),
        "config_scenario": str(config.scenario),
        "checkpoint_identity": checkpoint_identity,
        "snapshot_shards_sha256": snapshot_shards_sha256,
        "static_report_sha256": _file_sha256(static_path),
        "scientific_contract": scientific_contract,
        "scientific_contract_sha256": scientific_contract[
            "scientific_contract_sha256"
        ],
    }
    _write_json(output_dir / "collector_manifest.json", manifest)
    (output_dir / "static_capacity.md").write_text(
        _static_markdown(static_report), encoding="utf-8"
    )
    if not immutable:
        raise RuntimeError("source checkpoint or policy parameters changed")
    return {"manifest": manifest, "static": static_report}


def _synthetic_markdown(report: dict[str, object]) -> str:
    lines = [
        "# R27 Synthetic Capacity Control",
        "",
        f"- Family status: `{report.get('status')}`",
        f"- Passing seeds: {report.get('passing_seeds', 0)}",
        f"- Failed seeds: {report.get('failed_seeds', 0)}",
        "",
        "## Fixed Gates",
        "",
        "- active accuracy and macro-F1 >= 0.90",
        "- active minus sham accuracy >= 0.50",
        "- sham accuracy <= 0.35",
        "- train minus test accuracy <= 0.20",
        "",
    ]
    for seed_report in report.get("seed_reports", []):
        lines.extend(
            [
                f"### Seed {seed_report['seed']}",
                "",
                f"- status: `{seed_report['status']}`",
                f"- reasons: {seed_report.get('reasons', [])}",
                f"- support: {seed_report.get('support', {})}",
                f"- active accuracy: {seed_report.get('synthetic_code_accuracy', 'n/a')}",
                f"- sham accuracy: {seed_report.get('sham_accuracy', 'n/a')}",
                f"- evidence finite: {seed_report.get('evidence_finite', 'n/a')}",
                f"- control contract valid: {seed_report.get('control_contract_valid', 'n/a')}",
                f"- source actor immutable: {seed_report.get('source_actor_sha256_equal', False)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Prohibited Next Actions",
            "",
            "No q_A, q_d, q_D, or intrinsic reward is authorized before final classification review.",
            "",
        ]
    )
    return "\n".join(lines)


def run_synthetic(args: argparse.Namespace) -> dict[str, object]:
    device = require_cuda_device(args.device)
    scientific_contract = validate_scientific_args(args)
    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    snapshot_dir = Path(args.snapshot_dir)
    snapshots = read_capacity_snapshot_shards(snapshot_dir)
    output_dir = Path(args.output_dir)

    config, metadata, env, agent, loaded_update = _configure_agent(args)
    del config
    file_hash_before = _file_sha256(checkpoint)
    try:
        checkpoint_identity = validate_registered_checkpoint_identity(
            args,
            metadata,
            loaded_update=loaded_update,
            checkpoint_sha256=file_hash_before,
            scientific_contract=scientific_contract,
        )
        snapshot_binding = validate_synthetic_snapshot_source(
            snapshot_dir,
            snapshots,
            scientific_contract=scientific_contract,
        )
    except Exception:
        env.close()
        raise
    output_dir.mkdir(parents=True, exist_ok=True)
    parameter_hash_before = policy_parameter_sha256(agent)
    try:
        codebook = build_orthogonal_codebook(
            int(agent.low.n_skills),
            int(agent.low.action_dim),
            seed=int(args.codebook_seed),
            norm=float(SCIENTIFIC_DECISION_THRESHOLDS["codebook_norm"]),
        )
        fit_config = SyntheticFitConfig(
            learning_rate=float(args.learning_rate),
            batch_size=int(args.batch_size),
            max_steps=int(args.max_steps),
            validation_interval=int(args.validation_interval),
            patience=int(args.patience),
            min_delta=float(args.min_delta),
        )
        available_reset_groups = int(np.unique(snapshots.reset_id).size)
        if available_reset_groups < MIN_BOOTSTRAP_RESET_GROUPS:
            actor_hash = _actor_state_sha256(agent.low)
            support = {
                "available_rows": int(np.asarray(snapshots.reset_id).size),
                "available_reset_groups": available_reset_groups,
                "train_rows": 0,
                "validation_rows": 0,
                "test_rows": 0,
                "train_reset_groups": 0,
                "validation_reset_groups": 0,
                "test_reset_groups": 0,
            }
            seed_reports = [
                _terminal_synthetic_seed_report(
                    seed=int(seed),
                    status="UNDERPOWERED",
                    reasons=[
                        "at least five represented reset groups are required"
                    ],
                    num_skills=int(agent.low.n_skills),
                    source_actor_sha256_before=actor_hash,
                    source_actor_sha256_after=actor_hash,
                    source_actor_parameter_count=_actor_parameter_count(agent.low),
                    support=support,
                )
                for seed in args.synthetic_seeds
            ]
            split_report = {
                "train_reset_ids": [],
                "validation_reset_ids": [],
                "test_reset_ids": [],
            }
        else:
            split = grouped_reset_split(
                snapshots.reset_id, seed=int(args.split_seed)
            )
            seed_reports = [
                evaluate_synthetic_seed(
                    agent.low,
                    snapshots,
                    split,
                    codebook,
                    seed=int(seed),
                    config=fit_config,
                    device=device,
                    bootstrap_reps=int(args.bootstrap_reps),
                )
                for seed in args.synthetic_seeds
            ]
            split_report = {
                "train_reset_ids": list(split.train_reset_ids),
                "validation_reset_ids": list(split.validation_reset_ids),
                "test_reset_ids": list(split.test_reset_ids),
            }
        family = gate_synthetic_family(seed_reports)
    finally:
        env.close()

    file_hash_after = _file_sha256(checkpoint)
    parameter_hash_after = policy_parameter_sha256(agent)
    immutable = bool(
        file_hash_before == file_hash_after
        and parameter_hash_before == parameter_hash_after
    )
    if not immutable:
        family = dict(family)
        family["status"] = "INVALID"
        family["pass"] = False
    report: dict[str, object] = {
        **family,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256_before": file_hash_before,
        "checkpoint_sha256_after": file_hash_after,
        "checkpoint_sha256_equal": file_hash_before == file_hash_after,
        "policy_parameter_sha256_before": parameter_hash_before,
        "policy_parameter_sha256_after": parameter_hash_after,
        "policy_parameter_sha256_equal": parameter_hash_before
        == parameter_hash_after,
        "device": str(args.device),
        "split": split_report,
        "codebook": codebook.tolist(),
        "codebook_norm": SCIENTIFIC_DECISION_THRESHOLDS["codebook_norm"],
        "fit_config": asdict(fit_config),
        "seed_reports": seed_reports,
        "thresholds": SCIENTIFIC_DECISION_THRESHOLDS["synthetic_seed"],
        "parameter_counts": _jsonable(agent.parameter_counts()),
        "checkpoint_identity": checkpoint_identity,
        **snapshot_binding,
        "scientific_contract": scientific_contract,
        "scientific_contract_sha256": scientific_contract[
            "scientific_contract_sha256"
        ],
    }
    _write_json(output_dir / "synthetic_control.json", report)
    (output_dir / "synthetic_control.md").write_text(
        _synthetic_markdown(report), encoding="utf-8"
    )
    if not immutable:
        raise RuntimeError("source checkpoint or policy parameters changed")
    return report


def _aggregate_markdown(report: dict[str, object]) -> str:
    artifact_identity = report.get("artifact_identity", {})
    static_thresholds = SCIENTIFIC_DECISION_THRESHOLDS["static_checkpoint"]
    static_family_thresholds = SCIENTIFIC_DECISION_THRESHOLDS["static_family"]
    synthetic_thresholds = SCIENTIFIC_DECISION_THRESHOLDS["synthetic_seed"]
    synthetic_family_thresholds = SCIENTIFIC_DECISION_THRESHOLDS[
        "synthetic_family"
    ]
    lines = [
        "# R27-G1 Low-Actor Capacity Autopsy",
        "",
        f"- Classification: `{report['classification']}`",
        f"- Reasons: {'; '.join(report['reasons'])}",
        f"- Static family: `{report['static_family']['status']}`",
        f"- Synthetic family: `{report['synthetic_family']['status']}`",
        f"- Artifact identity: `{artifact_identity.get('pass', False)}`",
        f"- Scientific contract SHA256: `{artifact_identity.get('scientific_contract_sha256', 'n/a')}`",
        "",
        "## Fixed Thresholds",
        "",
        f"- symmetric KL >= {static_thresholds['symmetric_kl_min']} nats",
        f"- standardized action-mean distance >= {static_thresholds['standardized_mean_distance_min']}",
        "- active-minus-control reset-bootstrap lower bound > 0.0",
        f"- inactive tolerance <= {static_thresholds['inactive_tolerance']}",
        f"- parity tolerance <= {static_thresholds['parity_tolerance']}",
        f"- agreeing checkpoints >= {static_family_thresholds['agreeing_checkpoints_min']}",
        f"- recurrent retention < {static_family_thresholds['recurrent_retention_max']} for washout",
        f"- synthetic active accuracy >= {synthetic_thresholds['active_accuracy_min']}",
        f"- synthetic macro-F1 >= {synthetic_thresholds['active_macro_f1_min']}",
        f"- synthetic active-minus-sham accuracy >= {synthetic_thresholds['active_minus_sham_accuracy_min']}",
        "- synthetic active-minus-sham bootstrap lower bound > 0.0",
        f"- synthetic sham accuracy <= {synthetic_thresholds['sham_accuracy_max']}",
        f"- synthetic train-minus-test accuracy <= {synthetic_thresholds['train_minus_test_accuracy_max']}",
        f"- passing synthetic seeds >= {synthetic_family_thresholds['passing_seeds_min']} of {synthetic_family_thresholds['fixed_seed_count']}",
        f"- minimum represented reset groups = {synthetic_family_thresholds['minimum_reset_groups']}",
        f"- codebook norm = {SCIENTIFIC_DECISION_THRESHOLDS['codebook_norm']}",
        "",
        "## Static Checkpoints",
        "",
    ]
    manifests = report.get("collector_manifests", [])
    for index, static in enumerate(report.get("static_reports", [])):
        manifest = manifests[index] if index < len(manifests) else {}
        zero = static.get("zero_h", {})
        rollout = static.get("rollout_h", {})
        inactive = static.get("inactive_control", {})
        parameter_counts = manifest.get("parameter_counts", {})
        lines.extend(
            [
                f"### {static.get('checkpoint_id', 'unknown')}",
                "",
                f"- status: `{static.get('status')}`",
                f"- zero-h KL / standardized distance / pass: {zero.get('mean_skl', 'n/a')} / {zero.get('mean_stdmean_distance', 'n/a')} / {zero.get('pass', False)}",
                f"- rollout-h KL / standardized distance / pass: {rollout.get('mean_skl', 'n/a')} / {rollout.get('mean_stdmean_distance', 'n/a')} / {rollout.get('pass', False)}",
                f"- FiLM / post-GRU separation (rollout-h): {rollout.get('film_feature_between', 'n/a')} / {rollout.get('post_gru_feature_between', 'n/a')}",
                f"- hidden retention ratio: {static.get('hidden_retention_ratio', 'n/a')}",
                f"- inactive KL / standardized distance: {inactive.get('max_abs_symmetric_kl', 'n/a')} / {inactive.get('max_stdmean_distance', 'n/a')}",
                f"- live parity: {static.get('parity', {}).get('pass', False)}",
                f"- checkpoint SHA256: {manifest.get('checkpoint_sha256_before', 'n/a')}",
                f"- checkpoint / policy immutable: {manifest.get('checkpoint_sha256_equal', False)} / {manifest.get('policy_parameter_sha256_equal', False)}",
            ]
        )
        for name, value in parameter_counts.items():
            lines.append(f"- {name}: {value}")
        lines.append("")

    synthetic = report.get("synthetic_report", {})
    lines.extend(
        [
            "## Synthetic Active/Sham Control",
            "",
            f"- family status: `{synthetic.get('status')}`",
            f"- passing / failed seeds: {synthetic.get('passing_seeds', 0)} / {synthetic.get('failed_seeds', 0)}",
            f"- checkpoint SHA256: {synthetic.get('checkpoint_sha256_before', 'n/a')}",
            f"- checkpoint / policy immutable: {synthetic.get('checkpoint_sha256_equal', False)} / {synthetic.get('policy_parameter_sha256_equal', False)}",
        ]
    )
    for name, value in synthetic.get("parameter_counts", {}).items():
        lines.append(f"- {name}: {value}")
    lines.append("")
    for seed_report in synthetic.get("seed_reports", []):
        bootstrap = seed_report.get("active_minus_sham_bootstrap", {})
        lines.extend(
            [
                f"### Seed {seed_report.get('seed')}",
                "",
                f"- status: `{seed_report.get('status')}`",
                f"- reasons: {seed_report.get('reasons', [])}",
                f"- reset support: {seed_report.get('support', {})}",
                f"- active accuracy / macro-F1: {seed_report.get('synthetic_code_accuracy')} / {seed_report.get('synthetic_code_macro_f1')}",
                f"- macro-F1: {seed_report.get('synthetic_code_macro_f1')}",
                f"- target MSE: {seed_report.get('synthetic_target_mse')}",
                f"- sham accuracy: {seed_report.get('sham_accuracy')}",
                f"- active-minus-sham accuracy / bootstrap lower: {seed_report.get('synthetic_active_minus_sham_accuracy')} / {bootstrap.get('lower')}",
                f"- train-minus-test accuracy: {seed_report.get('synthetic_train_minus_test_accuracy')}",
                f"- active/sham initialization equal: {seed_report.get('active_sham_initialization_equal', False)}",
                f"- active/sham parameter count equal: {seed_report.get('active_sham_parameter_count_equal', False)}",
                f"- active/sham shared minibatch schedule: {seed_report.get('active_sham_shared_minibatch_schedule', False)}",
                f"- evidence finite / control contract valid: {seed_report.get('evidence_finite', 'n/a')} / {seed_report.get('control_contract_valid', 'n/a')}",
                f"- source actor SHA256 before / after: {seed_report.get('source_actor_sha256_before', seed_report.get('initial_actor_sha256', 'n/a'))} / {seed_report.get('source_actor_sha256_after', 'n/a')}",
                f"- minibatch schedule SHA256: {seed_report.get('minibatch_schedule_sha256', 'n/a')}",
                f"- optimizer contracts equal: {seed_report.get('active_optimizer_contract') == seed_report.get('sham_optimizer_contract') if seed_report.get('active_optimizer_contract') is not None else 'n/a'}",
                f"- train row hashes equal: {seed_report.get('active_train_rows_sha256') == seed_report.get('sham_train_rows_sha256') if seed_report.get('active_train_rows_sha256') is not None else 'n/a'}",
                f"- validation row hashes equal: {seed_report.get('active_validation_rows_sha256') == seed_report.get('sham_validation_rows_sha256') if seed_report.get('active_validation_rows_sha256') is not None else 'n/a'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision Boundary",
            "",
            "This reward-off audit classifies the existing low-actor path; it does not change the algorithm.",
            "",
            "## Prohibited Next Actions",
            "",
            "No q_A, q_d, q_D, or intrinsic reward may be enabled before controller review of this classification.",
            "No actor redesign, hidden reset, or long training run is authorized by this file alone.",
            "",
        ]
    )
    return "\n".join(lines)


def _recompute_static_leaf(
    report: dict[str, object], checkpoint_id: str
) -> tuple[dict[str, object], list[str]]:
    status = report.get("status")
    errors: list[str] = []
    if report.get("thresholds") != SCIENTIFIC_DECISION_THRESHOLDS[
        "static_checkpoint"
    ]:
        errors.append(f"{checkpoint_id} threshold evidence mismatch")
    if status in ("INVALID", "UNDERPOWERED"):
        return copy.deepcopy(report), errors
    recomputed = copy.deepcopy(report)
    condition_passes: dict[str, bool] = {}
    condition_finite: dict[str, bool] = {}
    try:
        for name in ("zero_h", "rollout_h"):
            condition = report[name]
            bootstrap = condition["bootstrap"]
            numeric = np.asarray(
                [
                    condition["mean_skl"],
                    condition["mean_stdmean_distance"],
                    condition["shared_logstd_max_abs_error"],
                    condition["film_feature_between"],
                    condition["post_gru_feature_between"],
                    bootstrap["mean"],
                    bootstrap["lower"],
                    bootstrap["upper"],
                ],
                dtype=np.float64,
            )
            finite = bool(
                condition.get("finite") is True and np.isfinite(numeric).all()
            )
            passed = bool(
                finite
                and float(condition["shared_logstd_max_abs_error"])
                <= PARITY_TOLERANCE
                and float(condition["mean_skl"]) >= STATIC_SKL_MIN
                and float(condition["mean_stdmean_distance"])
                >= STATIC_STDMEAN_MIN
                and float(bootstrap["lower"]) > 0.0
            )
            condition_passes[name] = passed
            condition_finite[name] = finite
            if condition.get("pass") is not passed:
                errors.append(
                    f"{checkpoint_id} {name} pass mismatch: "
                    f"reported {condition.get('pass')!r}, recomputed {passed!r}"
                )
            recomputed[name]["pass"] = passed

        expected_retention = float(report["rollout_h"]["mean_skl"]) / max(
            float(report["zero_h"]["mean_skl"]), INACTIVE_TOLERANCE
        )
        if not np.isclose(
            float(report["hidden_retention_ratio"]),
            expected_retention,
            rtol=1e-9,
            atol=1e-12,
        ):
            errors.append(
                f"{checkpoint_id} hidden retention mismatch: "
                f"reported {report['hidden_retention_ratio']!r}, "
                f"recomputed {expected_retention!r}"
            )
        recomputed["hidden_retention_ratio"] = expected_retention

        inactive = report["inactive_control"]
        parity = report["parity"]
        film = report["film_code_parameters"]
        gamma = np.asarray(film["gamma_by_skill"], dtype=np.float64)
        beta = np.asarray(film["beta_by_skill"], dtype=np.float64)
        scalar_values = np.asarray(
            [
                report["hidden_retention_ratio"],
                inactive["max_abs_symmetric_kl"],
                inactive["max_stdmean_distance"],
                parity["max_action_abs_error"],
                parity["max_hidden_abs_error"],
                film["consistency_max_abs_error"],
            ],
            dtype=np.float64,
        )
        all_finite = bool(
            np.isfinite(scalar_values).all()
            and gamma.size > 0
            and beta.size > 0
            and np.isfinite(gamma).all()
            and np.isfinite(beta).all()
            and all(condition_finite.values())
        )
        parity_pass = bool(
            all_finite
            and float(parity["max_action_abs_error"]) <= PARITY_TOLERANCE
            and float(parity["max_hidden_abs_error"]) <= PARITY_TOLERANCE
        )
        if parity.get("pass") is not parity_pass:
            errors.append(
                f"{checkpoint_id} parity pass mismatch: "
                f"reported {parity.get('pass')!r}, recomputed {parity_pass!r}"
            )
        recomputed["parity"]["pass"] = parity_pass
        invalid = bool(
            not all_finite
            or float(inactive["max_abs_symmetric_kl"])
            > INACTIVE_TOLERANCE
            or float(inactive["max_stdmean_distance"])
            > INACTIVE_TOLERANCE
            or not parity_pass
            or float(film["consistency_max_abs_error"])
            > PARITY_TOLERANCE
        )
        expected_status = (
            "INVALID"
            if invalid
            else (
                "PASS"
                if condition_passes["zero_h"]
                or condition_passes["rollout_h"]
                else "FAIL"
            )
        )
    except (KeyError, TypeError, ValueError) as error:
        expected_status = "INVALID"
        errors.append(f"{checkpoint_id} static leaf evidence incomplete: {error}")
    if status != expected_status:
        errors.append(
            f"{checkpoint_id} static status mismatch: "
            f"reported {status!r}, recomputed {expected_status!r}"
        )
    recomputed["status"] = expected_status
    return recomputed, errors


def _recompute_synthetic_seed_leaf(
    report: dict[str, object]
) -> tuple[dict[str, object], list[str]]:
    seed = report.get("seed")
    reported_status = report.get("status")
    errors: list[str] = []
    if report.get("thresholds") != SCIENTIFIC_DECISION_THRESHOLDS[
        "synthetic_seed"
    ]:
        errors.append(f"seed {seed} threshold evidence mismatch")
    if reported_status in ("INVALID", "UNDERPOWERED"):
        if report.get("pass") is not False:
            errors.append(f"seed {seed} terminal status must have pass=False")
        return {"seed": seed, "status": reported_status, "pass": False}, errors

    try:
        bootstrap = report["active_minus_sham_bootstrap"]
        numeric = np.asarray(
            [
                report["synthetic_code_accuracy"],
                report["synthetic_code_macro_f1"],
                report["synthetic_target_mse"],
                report["synthetic_train_accuracy"],
                report["sham_accuracy"],
                report["synthetic_active_minus_sham_accuracy"],
                report["synthetic_train_minus_test_accuracy"],
                bootstrap["mean"],
                bootstrap["lower"],
                bootstrap["upper"],
            ],
            dtype=np.float64,
        )
        evidence_finite = bool(np.isfinite(numeric).all())
        support_sufficient = bool(
            int(report["support"]["test_reset_groups"]) >= 5
        )
        source_equal = bool(
            report["source_actor_sha256_before"]
            == report["source_actor_sha256_after_active_fit"]
            == report["source_actor_sha256_after"]
        )
        initialization_equal = bool(
            report["active_initial_actor_sha256"]
            == report["sham_initial_actor_sha256"]
            == report["source_actor_sha256_before"]
        )
        parameter_count_equal = bool(
            int(report["active_actor_parameter_count"])
            == int(report["sham_actor_parameter_count"])
            == int(report["source_actor_parameter_count"])
        )
        schedule_equal = bool(
            report["active_minibatch_schedule_sha256"]
            == report["sham_minibatch_schedule_sha256"]
            == report["minibatch_schedule_sha256"]
        )
        optimizer_equal = bool(
            report["active_optimizer_contract"]
            == report["sham_optimizer_contract"]
        )
        optimizer_contract = report["active_optimizer_contract"]
        optimizer_registered = bool(
            str(optimizer_contract.get("class", ""))
            == "torch.optim.adam.Adam"
            and float(optimizer_contract.get("learning_rate")) == 3e-4
            and list(optimizer_contract.get("betas", [])) == [0.9, 0.999]
            and float(optimizer_contract.get("eps")) == 1e-8
            and float(optimizer_contract.get("weight_decay")) == 0.0
            and optimizer_contract.get("amsgrad") is False
            and optimizer_contract.get("maximize") is False
        )
        rows_equal = bool(
            report["active_train_rows_sha256"]
            == report["sham_train_rows_sha256"]
            and report["active_validation_rows_sha256"]
            == report["sham_validation_rows_sha256"]
        )
        targets_equal = bool(
            report["active_train_targets_sha256"]
            == report["sham_train_targets_sha256"]
            and report["active_validation_targets_sha256"]
            == report["sham_validation_targets_sha256"]
        )
        control_valid = bool(
            source_equal
            and initialization_equal
            and parameter_count_equal
            and schedule_equal
            and optimizer_equal
            and optimizer_registered
            and rows_equal
            and targets_equal
        )
        expected_accuracy_difference = float(
            report["synthetic_code_accuracy"]
        ) - float(report["sham_accuracy"])
        expected_generalization_gap = float(
            report["synthetic_train_accuracy"]
        ) - float(report["synthetic_code_accuracy"])
        if not np.isclose(
            float(report["synthetic_active_minus_sham_accuracy"]),
            expected_accuracy_difference,
            rtol=1e-9,
            atol=1e-12,
        ):
            errors.append(
                f"seed {seed} active-minus-sham accuracy mismatch"
            )
        if not np.isclose(
            float(report["synthetic_train_minus_test_accuracy"]),
            expected_generalization_gap,
            rtol=1e-9,
            atol=1e-12,
        ):
            errors.append(f"seed {seed} train-minus-test accuracy mismatch")
        if not np.isclose(
            float(bootstrap["mean"]),
            expected_accuracy_difference,
            rtol=1e-9,
            atol=1e-12,
        ):
            errors.append(f"seed {seed} bootstrap mean mismatch")
        expected_status, expected_pass, _reasons = _decide_synthetic_seed_gate(
            active_accuracy=float(report["synthetic_code_accuracy"]),
            active_macro_f1=float(report["synthetic_code_macro_f1"]),
            active_minus_sham_accuracy=expected_accuracy_difference,
            bootstrap_lower=float(bootstrap["lower"]),
            sham_accuracy=float(report["sham_accuracy"]),
            generalization_gap=expected_generalization_gap,
            evidence_finite=evidence_finite,
            control_contract_valid=control_valid,
            support_sufficient=support_sufficient,
            num_skills=4,
        )
        reported_claims = {
            "evidence_finite": evidence_finite,
            "control_contract_valid": control_valid,
            "source_actor_sha256_equal": source_equal,
            "active_sham_initialization_equal": initialization_equal,
            "active_sham_parameter_count_equal": parameter_count_equal,
            "active_sham_shared_minibatch_schedule": schedule_equal,
        }
        for name, expected in reported_claims.items():
            if report.get(name) is not expected:
                errors.append(
                    f"seed {seed} {name} mismatch: "
                    f"reported {report.get(name)!r}, recomputed {expected!r}"
                )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        expected_status = "INVALID"
        expected_pass = False
        errors.append(f"seed {seed} leaf evidence incomplete: {error}")
    if reported_status != expected_status or report.get("pass") is not expected_pass:
        errors.append(
            f"seed {seed} status/pass mismatch: reported "
            f"{reported_status!r}/{report.get('pass')!r}, recomputed "
            f"{expected_status!r}/{expected_pass!r}"
        )
    return {
        "seed": seed,
        "status": expected_status,
        "pass": expected_pass,
    }, errors


def _scientific_contract_evidence_valid(payload: dict[str, object]) -> bool:
    contract = payload.get("scientific_contract", {})
    return bool(
        payload.get("scientific_contract_sha256")
        == SCIENTIFIC_CONTRACT_SHA256
        and contract.get("mode") == "R27_G1_SCIENTIFIC"
        and contract.get("eligible_for_aggregate") is True
        and contract.get("scientific_contract_sha256")
        == SCIENTIFIC_CONTRACT_SHA256
        and contract.get("resolved_contract") == SCIENTIFIC_CONTRACT
        and _stable_payload_sha256(contract.get("resolved_contract"))
        == SCIENTIFIC_CONTRACT_SHA256
    )


def validate_aggregate_artifacts(
    run_root: Path,
    checkpoint_ids: list[str],
    static_reports: list[dict[str, object]],
    collector_manifests: list[dict[str, object]],
    synthetic_report: dict[str, object],
) -> tuple[list[str], dict[str, object], dict[str, object]]:
    """Validate leaf identities and recompute both family summaries."""

    errors: list[str] = []
    recomputed_static_reports: list[dict[str, object]] = []
    for checkpoint_id, report in zip(checkpoint_ids, static_reports):
        recomputed, leaf_errors = _recompute_static_leaf(report, checkpoint_id)
        recomputed_static_reports.append(recomputed)
        errors.extend(leaf_errors)
    static_family = gate_static_family(recomputed_static_reports)
    seed_reports = synthetic_report.get("seed_reports", [])
    if not isinstance(seed_reports, list):
        seed_reports = []
        errors.append("synthetic seed_reports must be a list")
    seed_ids = [report.get("seed") for report in seed_reports if isinstance(report, dict)]
    if seed_ids != list(SCIENTIFIC_SYNTHETIC_SEEDS):
        errors.append(
            "synthetic seeds must be exactly "
            f"{list(SCIENTIFIC_SYNTHETIC_SEEDS)}; got {seed_ids}"
        )
    recomputed_seed_reports: list[dict[str, object]] = []
    for report in seed_reports:
        if not isinstance(report, dict):
            errors.append("synthetic seed report must be an object")
            continue
        recomputed, leaf_errors = _recompute_synthetic_seed_leaf(report)
        recomputed_seed_reports.append(recomputed)
        errors.extend(leaf_errors)
    synthetic_family = gate_synthetic_family(recomputed_seed_reports)
    for key, expected in synthetic_family.items():
        if synthetic_report.get(key) != expected:
            errors.append(
                f"synthetic top-level {key}={synthetic_report.get(key)!r} "
                f"!= recomputed {expected!r}"
            )

    for checkpoint_id, static_report, manifest in zip(
        checkpoint_ids, static_reports, collector_manifests
    ):
        registered = REGISTERED_CHECKPOINTS[checkpoint_id]
        static_path = run_root / checkpoint_id / "static_capacity.json"
        snapshot_dir = run_root / checkpoint_id / "capacity_snapshots"
        expected_hash = str(registered["sha256"]).lower()
        checkpoint_identity = manifest.get("checkpoint_identity", {})
        errors.extend(
            f"{checkpoint_id} {reason}"
            for reason in _snapshot_shard_contract_errors(snapshot_dir)
        )
        try:
            actual_snapshot_sha256 = _snapshot_shards_sha256(snapshot_dir)
        except OSError as error:
            actual_snapshot_sha256 = ""
            errors.append(f"{checkpoint_id} snapshot read failed: {error}")
        checks = (
            (
                static_report.get("checkpoint_id") == checkpoint_id,
                f"{checkpoint_id} static report checkpoint_id mismatch",
            ),
            (
                static_report.get("checkpoint_update")
                == int(registered["update_idx"]),
                f"{checkpoint_id} static report update mismatch",
            ),
            (
                str(static_report.get("source_checkpoint_sha256", "")).lower()
                == expected_hash,
                f"{checkpoint_id} static report checkpoint hash mismatch",
            ),
            (
                static_report.get("scientific_contract_sha256")
                == SCIENTIFIC_CONTRACT_SHA256,
                f"{checkpoint_id} static report contract mismatch",
            ),
            (
                manifest.get("checkpoint_id") == checkpoint_id,
                f"{checkpoint_id} manifest checkpoint_id mismatch",
            ),
            (
                manifest.get("checkpoint_update")
                == int(registered["update_idx"]),
                f"{checkpoint_id} manifest update mismatch",
            ),
            (
                _path_matches_registered(
                    str(manifest.get("checkpoint", "")),
                    str(registered["path"]),
                ),
                f"{checkpoint_id} manifest path mismatch",
            ),
            (
                str(manifest.get("checkpoint_sha256_before", "")).lower()
                == expected_hash,
                f"{checkpoint_id} manifest checkpoint hash mismatch",
            ),
            (
                str(manifest.get("checkpoint_sha256_after", "")).lower()
                == expected_hash,
                f"{checkpoint_id} manifest post-run checkpoint hash mismatch",
            ),
            (
                manifest.get("checkpoint_sha256_equal") is True
                and manifest.get("policy_parameter_sha256_equal") is True
                and bool(manifest.get("policy_parameter_sha256_before"))
                and manifest.get("policy_parameter_sha256_before")
                == manifest.get("policy_parameter_sha256_after"),
                f"{checkpoint_id} source immutability flags failed",
            ),
            (
                checkpoint_identity.get("eligible_for_aggregate") is True
                and checkpoint_identity.get("checkpoint_id") == checkpoint_id
                and checkpoint_identity.get("checkpoint_update")
                == int(registered["update_idx"])
                and str(checkpoint_identity.get("checkpoint_sha256", "")).lower()
                == expected_hash
                and checkpoint_identity.get("scientific_contract_sha256")
                == SCIENTIFIC_CONTRACT_SHA256,
                f"{checkpoint_id} registered checkpoint identity mismatch",
            ),
            (
                manifest.get("n_resets") == 64,
                f"{checkpoint_id} n_resets mismatch",
            ),
            (
                _parallel_manifest_contract_valid(manifest),
                f"{checkpoint_id} parallel collector contract mismatch",
            ),
            (
                manifest.get("reset_seeds") == list(range(1, 65)),
                f"{checkpoint_id} reset seeds mismatch",
            ),
            (
                str(manifest.get("device", "")).lower().startswith("cuda"),
                f"{checkpoint_id} device is not CUDA",
            ),
            (
                _scientific_contract_evidence_valid(manifest),
                f"{checkpoint_id} manifest is not scientific-contract eligible",
            ),
            (
                manifest.get("static_report_sha256")
                == _file_sha256(static_path),
                f"{checkpoint_id} static report file hash mismatch",
            ),
            (
                manifest.get("snapshot_shards_sha256")
                == static_report.get("snapshot_shards_sha256"),
                f"{checkpoint_id} snapshot hash mismatch",
            ),
            (
                manifest.get("snapshot_shards_sha256")
                == actual_snapshot_sha256,
                f"{checkpoint_id} snapshot files changed after collection",
            ),
        )
        errors.extend(reason for passed, reason in checks if not passed)

    final_manifest_path = run_root / "arm0_final" / "collector_manifest.json"
    final_manifest = collector_manifests[-1]
    final_registered = REGISTERED_CHECKPOINTS["arm0_final"]
    final_hash = str(final_registered["sha256"]).lower()
    synthetic_checkpoint_identity = synthetic_report.get(
        "checkpoint_identity", {}
    )
    synthetic_checks = (
        (
            _path_matches_registered(
                str(synthetic_report.get("checkpoint", "")),
                str(final_registered["path"]),
            ),
            "synthetic checkpoint path is not registered arm0_final",
        ),
        (
            str(synthetic_report.get("checkpoint_sha256_before", "")).lower()
            == final_hash,
            "synthetic checkpoint hash mismatch",
        ),
        (
            str(synthetic_report.get("checkpoint_sha256_after", "")).lower()
            == final_hash,
            "synthetic post-run checkpoint hash mismatch",
        ),
        (
            synthetic_report.get("checkpoint_sha256_equal") is True
            and synthetic_report.get("policy_parameter_sha256_equal") is True
            and bool(synthetic_report.get("policy_parameter_sha256_before"))
            and synthetic_report.get("policy_parameter_sha256_before")
            == synthetic_report.get("policy_parameter_sha256_after"),
            "synthetic source immutability flags failed",
        ),
        (
            synthetic_checkpoint_identity.get("eligible_for_aggregate") is True
            and synthetic_checkpoint_identity.get("checkpoint_id")
            == "arm0_final"
            and synthetic_checkpoint_identity.get("checkpoint_update") == 32
            and str(
                synthetic_checkpoint_identity.get("checkpoint_sha256", "")
            ).lower()
            == final_hash
            and synthetic_checkpoint_identity.get(
                "scientific_contract_sha256"
            )
            == SCIENTIFIC_CONTRACT_SHA256,
            "synthetic registered checkpoint identity mismatch",
        ),
        (
            str(synthetic_report.get("device", "")).lower().startswith("cuda"),
            "synthetic device is not CUDA",
        ),
        (
            _scientific_contract_evidence_valid(synthetic_report),
            "synthetic report is not scientific-contract eligible",
        ),
        (
            synthetic_report.get("codebook_norm")
            == SCIENTIFIC_DECISION_THRESHOLDS["codebook_norm"]
            and synthetic_report.get("fit_config")
            == asdict(SyntheticFitConfig()),
            "synthetic fit contract mismatch",
        ),
        (
            synthetic_report.get("thresholds")
            == SCIENTIFIC_DECISION_THRESHOLDS["synthetic_seed"],
            "synthetic top-level threshold evidence mismatch",
        ),
        (
            synthetic_report.get("source_collector_manifest_sha256")
            == _file_sha256(final_manifest_path),
            "synthetic collector-manifest binding mismatch",
        ),
        (
            synthetic_report.get("source_snapshot_shards_sha256")
            == final_manifest.get("snapshot_shards_sha256"),
            "synthetic snapshot binding mismatch",
        ),
    )
    errors.extend(reason for passed, reason in synthetic_checks if not passed)
    return errors, static_family, synthetic_family


def run_aggregate(args: argparse.Namespace) -> dict[str, object]:
    run_root = Path(args.run_root)
    checkpoint_ids = [str(value) for value in args.checkpoint_ids]
    if checkpoint_ids != ["arm0_update25", "arm0_update30", "arm0_final"]:
        raise ValueError("aggregate requires exact arm0 update25/update30/final order")
    try:
        static_reports = [
            _read_json_strict(
                run_root / checkpoint_id / "static_capacity.json"
            )
            for checkpoint_id in checkpoint_ids
        ]
        collector_manifests = [
            _read_json_strict(
                run_root / checkpoint_id / "collector_manifest.json"
            )
            for checkpoint_id in checkpoint_ids
        ]
        synthetic_report = _read_json_strict(
            run_root / "synthetic_control.json"
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result: dict[str, object] = {
            "classification": "INVALID",
            "reasons": [f"artifact read failed: {error}"],
            "checkpoint_ids": checkpoint_ids,
            "static_family": {
                "status": "INVALID",
                "zero_h_pass": False,
                "rollout_h_pass": False,
                "recurrent_washout": False,
            },
            "synthetic_family": {
                "status": "INVALID",
                "pass": False,
                "passing_seeds": 0,
                "failed_seeds": 0,
            },
            "static_reports": [],
            "collector_manifests": [],
            "synthetic_report": {},
            "artifact_identity": {
                "pass": False,
                "errors": [str(error)],
                "scientific_contract_sha256": SCIENTIFIC_CONTRACT_SHA256,
            },
            "decision_thresholds": copy.deepcopy(
                SCIENTIFIC_DECISION_THRESHOLDS
            ),
            "prohibited_next_actions": [
                "q_A/q_d/q_D or intrinsic reward",
                "actor redesign or hidden reset",
                "long training before classification review",
            ],
        }
        _write_json(run_root / "r27_capacity_autopsy.json", result)
        (run_root / "r27_capacity_autopsy.md").write_text(
            _aggregate_markdown(result), encoding="utf-8"
        )
        return result
    identity_errors, static_family, synthetic_family = validate_aggregate_artifacts(
        run_root,
        checkpoint_ids,
        static_reports,
        collector_manifests,
        synthetic_report,
    )
    classification = (
        {"classification": "INVALID", "reasons": identity_errors}
        if identity_errors
        else classify_capacity_autopsy(static_family, synthetic_family)
    )
    result: dict[str, object] = {
        **classification,
        "checkpoint_ids": checkpoint_ids,
        "static_family": static_family,
        "synthetic_family": synthetic_family,
        "static_reports": static_reports,
        "collector_manifests": collector_manifests,
        "synthetic_report": synthetic_report,
        "artifact_identity": {
            "pass": not identity_errors,
            "errors": identity_errors,
            "scientific_contract_sha256": SCIENTIFIC_CONTRACT_SHA256,
        },
        "decision_thresholds": copy.deepcopy(SCIENTIFIC_DECISION_THRESHOLDS),
        "prohibited_next_actions": [
            "q_A/q_d/q_D or intrinsic reward",
            "actor redesign or hidden reset",
            "long training before classification review",
        ],
    }
    _write_json(run_root / "r27_capacity_autopsy.json", result)
    (run_root / "r27_capacity_autopsy.md").write_text(
        _aggregate_markdown(result), encoding="utf-8"
    )
    return result


def _add_checkpoint_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--preset", default="S7-S1")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--n-agents", dest="n_agents", type=int, default=6)
    parser.add_argument("--device", default="cuda")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Frozen R27-G1 low-actor capacity autopsy"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect = subparsers.add_parser("collect-static")
    _add_checkpoint_args(collect)
    collect.add_argument("--output-dir", required=True)
    collect.add_argument("--checkpoint-id", default="")
    collect.add_argument("--checkpoint-update", type=int, default=None)
    collect.add_argument("--skill-interval", type=int, default=10)
    collect.add_argument("--n-resets", type=int, default=64)
    collect.add_argument("--num-envs", type=int, default=64)
    collect.add_argument(
        "--collector-backend", choices=("subproc", "sync"), default="subproc"
    )
    collect.add_argument(
        "--collector-start-method",
        choices=("spawn", "fork", "forkserver"),
        default="spawn",
    )
    collect.add_argument("--episode-max-steps", type=int, default=500)
    collect.add_argument("--bootstrap-reps", type=int, default=1000)
    collect.add_argument("--bootstrap-seed", type=int, default=27021)
    collect.add_argument("--non-scientific-fixture", action="store_true")

    synthetic = subparsers.add_parser("synthetic")
    _add_checkpoint_args(synthetic)
    synthetic.add_argument("--snapshot-dir", required=True)
    synthetic.add_argument("--output-dir", required=True)
    synthetic.add_argument("--split-seed", type=int, default=27011)
    synthetic.add_argument("--codebook-seed", type=int, default=27030)
    synthetic.add_argument(
        "--synthetic-seeds", type=int, nargs="+", default=[17, 23, 41]
    )
    synthetic.add_argument("--learning-rate", type=float, default=3e-4)
    synthetic.add_argument("--batch-size", type=int, default=256)
    synthetic.add_argument("--max-steps", type=int, default=1000)
    synthetic.add_argument("--validation-interval", type=int, default=25)
    synthetic.add_argument("--patience", type=int, default=20)
    synthetic.add_argument("--min-delta", type=float, default=1e-4)
    synthetic.add_argument("--bootstrap-reps", type=int, default=1000)
    synthetic.add_argument("--non-scientific-fixture", action="store_true")

    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--run-root", required=True)
    aggregate.add_argument("--checkpoint-ids", nargs="+", required=True)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main() -> None:
    args = parse_args()
    if args.command == "collect-static":
        result = run_collect_static(args)
    elif args.command == "synthetic":
        result = run_synthetic(args)
    else:
        result = run_aggregate(args)
    print(json.dumps(_jsonable(result), sort_keys=True))


if __name__ == "__main__":
    main()
