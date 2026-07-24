"""Train, evaluate, analyze, and validate UAV temporary-service-loss G1."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
import time
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.uav_temp_loss_g1 import (
    FIXED_MASK_REC,
    HORIZON,
    PPO_PASSES,
    PREFIX_NORMALIZED_OPEN_ROSTER,
    LossCell,
    MatchedContinuousRecurrentPolicy,
    PersistentUAVVectorEnv,
    collect_uav_trajectory,
    compute_episode_metrics,
    evaluate_uav_controller,
    evaluate_uav_policy,
    load_uav_checkpoint,
    make_uav_loss_ledger,
    maximum_state_difference,
    model_state_copy,
    optimize_uav_update,
    save_uav_checkpoint,
)


SOURCE_FAMILY = "UAV_TEMPORARY_SERVICE_LOSS_G1"
RUN_SCHEMA = "hmasd.uav_temp_loss_g1.run.v2"
EVALUATION_SCHEMA = "hmasd.uav_temp_loss_g1.evaluation.v2"
EVALUATION_ROW_SCHEMA = "hmasd.uav_temp_loss_g1.evaluation_row.v2"
ANALYSIS_SCHEMA = "hmasd.uav_temp_loss_g1.analysis.v2"
LAUNCH_SCHEMA = "hmasd.uav_temp_loss_g1.launch.v1"
RESUME_SCHEMA = "hmasd.uav_temp_loss_g1.resume.v1"
RESUME_COMMIT_SCHEMA = "hmasd.uav_temp_loss_g1.resume_commit.v1"
FINAL_CHECKPOINT_COMMIT_SCHEMA = "hmasd.uav_temp_loss_g1.final_checkpoint_commit.v1"
TRAIN_MANIFEST_COMMIT_SCHEMA = "hmasd.uav_temp_loss_g1.train_manifest_commit.v1"
EVALUATION_LAUNCH_SCHEMA = "hmasd.uav_temp_loss_g1.evaluation_launch.v1"
EVALUATION_CHUNK_SCHEMA = "hmasd.uav_temp_loss_g1.evaluation_chunk.v1"
EVALUATION_CHUNK_COMMIT_SCHEMA = "hmasd.uav_temp_loss_g1.evaluation_chunk_commit.v1"
EVALUATION_MANIFEST_COMMIT_SCHEMA = "hmasd.uav_temp_loss_g1.evaluation_manifest_commit.v1"
SOURCE_SCREEN_LAUNCH_SCHEMA = "hmasd.uav_temp_loss_g1.source_screen_launch.v1"
SOURCE_SCREEN_SCHEMA = "hmasd.uav_temp_loss_g1.source_screen.v1"
SOURCE_SCREEN_COMMIT_SCHEMA = "hmasd.uav_temp_loss_g1.source_screen_commit.v1"
FORMAL_AUTHORIZATION_TOKEN = "AUTHORIZE_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_CPU_V1"

TRAIN_COMPLETE = "TRAIN_COMPLETE"
TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE = "TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE"

ARM_NAMES = (FIXED_MASK_REC, PREFIX_NORMALIZED_OPEN_ROSTER)
CONTROL_NAMES = ("constructive", "no_reallocation")
SUBJECT_NAMES = ARM_NAMES + CONTROL_NAMES
EVALUATION_CELLS = (
    LossCell.NO_DISTURBANCE,
    LossCell.IID_SINGLE,
    LossCell.LATE_LONG_SINGLE,
    LossCell.OVERLAPPING_DOUBLE,
)
ACTION_MODES = ("deterministic", "stochastic")
STRATA = tuple((cell.value, mode) for cell in EVALUATION_CELLS for mode in ACTION_MODES)
ACCESS_CELL_COUNT = len(EVALUATION_CELLS)

ACCESS_THRESHOLD = 1.0
EVENT_ACCESS_FLOOR = 0.80
ORDINARY_ACCESS_FLOOR = 0.90
CONSTRUCTIVE_FLOOR = 0.90
LOAD_BEARING_MARGIN = 0.10
SERVICE_GAIN_MARGIN = 0.03
REJOIN_GAIN_MARGIN = 0.02
ORDINARY_NONINFERIORITY_MARGIN = -0.02
REPLAY_TOLERANCE = 1.0e-6
LEARNING_RATE = 3.0e-4

INVALID_RESULT = "INVALID_UAV_TEMP_LOSS_G1"
SOURCE_NON_IDENTIFIABLE_RESULT = "SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1"
NO_ACCESS_RESULT = "NO_ACCESS_UAV_TEMP_LOSS_G1"
UNDERPOWERED_RESULT = "UNDERPOWERED_ACCESS_UAV_TEMP_LOSS_G1"
MASK_SUFFICIENT_RESULT = "USABLE_MASK_SUFFICIENT_UAV_TEMP_LOSS_G1"
DYNAMIC_SUPPORTED_RESULT = "DYNAMIC_LIFECYCLE_SUPPORTED_UAV_TEMP_LOSS_G1"
MIXED_RESULT = "MIXED_ANOMALOUS_UAV_TEMP_LOSS_G1"
NONFORMAL_RESULT = "NONFORMAL_UAV_TEMP_LOSS_G1_EXERCISE_COMPLETE"


@dataclass(frozen=True)
class RunConfig:
    replicates: int
    updates: int
    num_envs: int
    horizon: int
    ppo_passes: int
    evaluation_episodes: int
    evaluation_batch_size: int
    bootstrap_resamples: int
    checkpoint_selection: str = "final_only"


@dataclass(frozen=True)
class SeedRegistry:
    model_initialization: int = 181_200
    training_ledger: int = 181_400
    training_environment: int = 181_600
    training_action: int = 181_800
    evaluation_ledger: int = 182_000
    evaluation_environment: int = 182_200
    evaluation_action: int = 182_400
    control: int = 182_600
    bootstrap: int = 182_800


FORMAL_CONFIG = RunConfig(
    replicates=3,
    updates=200,
    num_envs=16,
    horizon=500,
    ppo_passes=4,
    evaluation_episodes=128,
    evaluation_batch_size=16,
    bootstrap_resamples=10_000,
)
EXERCISE_CONFIG = RunConfig(
    replicates=1,
    updates=1,
    num_envs=1,
    horizon=16,
    ppo_passes=1,
    evaluation_episodes=1,
    evaluation_batch_size=1,
    bootstrap_resamples=256,
)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_json_immutable(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_jsonl_immutable(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if type(value) is not dict:
            raise ValueError(f"{path}:{line_number} must contain one JSON object")
        rows.append(value)
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def configure_runtime(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _replicate_seeds(replicate: int) -> dict[str, int]:
    offset = int(replicate) * 1000
    return {name: int(value) + offset for name, value in asdict(SeedRegistry()).items()}


def _validate_source_commit(source_commit: object, *, formal: bool) -> str:
    if type(source_commit) is not str or not source_commit:
        raise ValueError("source commit must be a non-empty string")
    if formal and re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("formal source commit must be a 40-character lowercase Git commit")
    return source_commit


def _validate_launch(
    *, formal: bool, authorization_token: str | None, config: RunConfig
) -> None:
    if formal:
        if authorization_token != FORMAL_AUTHORIZATION_TOKEN:
            raise ValueError("formal UAV G1 authorization token mismatch")
        if config != FORMAL_CONFIG:
            raise ValueError("formal UAV G1 counts differ from the frozen contract")
    elif authorization_token is not None:
        raise ValueError("nonformal UAV G1 run cannot carry a formal authorization token")
    values = (
        config.replicates,
        config.updates,
        config.num_envs,
        config.horizon,
        config.ppo_passes,
        config.evaluation_episodes,
        config.evaluation_batch_size,
        config.bootstrap_resamples,
    )
    if any(type(value) is not int or value <= 0 for value in values):
        raise ValueError("UAV G1 run counts must be positive exact integers")
    if formal and config.horizon != HORIZON:
        raise ValueError("UAV G1 horizon must remain 500 physical steps")
    if not formal and config.horizon > HORIZON:
        raise ValueError("nonformal UAV G1 horizon cannot exceed the physical horizon")
    if config.evaluation_episodes % config.evaluation_batch_size != 0:
        raise ValueError("evaluation episodes must divide into equal persistent batches")


def _ledgers(cell: LossCell, episode_ids: Sequence[int], seed: int):
    return [make_uav_loss_ledger(cell, episode_id, ledger_seed=seed) for episode_id in episode_ids]


def _environment_seeds(base: int, episode_ids: Sequence[int]) -> list[int]:
    return [int(base) + int(episode_id) for episode_id in episode_ids]


def _ledger_payload(ledger: Any) -> dict[str, Any]:
    return {
        "ledger_id": ledger.ledger_id,
        "intervals": [
            {"owner": row.owner, "onset": row.onset, "duration": row.duration}
            for row in ledger.intervals
        ],
    }


def _checkpoint_reference(replicate: int, arm: str) -> str:
    if arm not in ARM_NAMES:
        raise ValueError("checkpoint arm is outside the learned comparator set")
    return f"checkpoints/replicate_{int(replicate)}_{arm}.pt"


def _confined_reference(root: Path, reference: object, *, expected: str) -> Path:
    if type(reference) is not str or reference != expected:
        raise ValueError("artifact reference is not the canonical registered path")
    if "\\" in reference or Path(reference).is_absolute() or Path(reference).as_posix() != reference:
        raise ValueError("artifact reference is not canonical/confined")
    candidate = root / reference
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("artifact reference escapes the run root") from error
    if not candidate.is_file():
        raise ValueError("referenced artifact file is missing")
    return candidate


def _registered_checkpoints(
    root: Path, manifest: Mapping[str, Any]
) -> dict[tuple[int, str], str]:
    config = RunConfig(**manifest["config"])
    expected_pairs = {
        (replicate, arm)
        for replicate in range(config.replicates)
        for arm in ARM_NAMES
    }
    results = manifest.get("training_results")
    references = manifest.get("checkpoint_references")
    if type(results) is not list or type(references) is not list:
        raise ValueError("final checkpoint inventory is missing")
    if manifest.get("status") == TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE:
        if results or references:
            raise ValueError("source-screen-skipped training retained learned checkpoints")
        if (root / "checkpoints").exists() or (root / "resume").exists():
            raise ValueError("source-screen-skipped training retained learned artifacts")
        return {}
    if manifest.get("status") != TRAIN_COMPLETE:
        raise ValueError("training status is not a registered terminal state")
    if len(results) != len(expected_pairs) or len(references) != len(expected_pairs):
        raise ValueError("final checkpoint inventory count mismatch")
    registered: dict[tuple[int, str], str] = {}
    for row in results:
        if type(row) is not dict:
            raise ValueError("training checkpoint row is malformed")
        replicate = row.get("replicate")
        arm = row.get("arm")
        if type(replicate) is not int or type(arm) is not str:
            raise ValueError("training checkpoint pair is malformed")
        pair = (replicate, arm)
        if pair not in expected_pairs or pair in registered:
            raise ValueError("final checkpoint pair inventory is duplicate or misdirected")
        expected_reference = _checkpoint_reference(replicate, arm)
        checkpoint_path = _confined_reference(
            root, row.get("checkpoint"), expected=expected_reference
        )
        checkpoint_sha256 = row.get("checkpoint_sha256")
        if (
            type(checkpoint_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", checkpoint_sha256) is None
            or _sha256_file(checkpoint_path) != checkpoint_sha256
        ):
            raise ValueError("final checkpoint SHA-256 content binding mismatch")
        marker_reference = _final_checkpoint_marker_reference(expected_reference)
        marker_path = _confined_reference(
            root, marker_reference, expected=marker_reference
        )
        if _read_json(marker_path) != {
            "schema": FINAL_CHECKPOINT_COMMIT_SCHEMA,
            "replicate": replicate,
            "arm": arm,
            "completed_updates": config.updates,
            "checkpoint_reference": expected_reference,
            "checkpoint_sha256": checkpoint_sha256,
        }:
            raise ValueError("final checkpoint completion marker mismatch")
        registered[pair] = expected_reference
    if set(registered) != expected_pairs:
        raise ValueError("final checkpoint pair inventory is incomplete")
    if (
        len(set(references)) != len(expected_pairs)
        or set(references) != set(registered.values())
    ):
        raise ValueError("final checkpoint reference inventory is duplicate or incomplete")
    return registered


def _evaluation_checkpoint_inventory(
    registered: Mapping[tuple[int, str], str],
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    digests = {
        (int(row["replicate"]), str(row["arm"])): str(row["checkpoint_sha256"])
        for row in manifest["training_results"]
    }
    return [
        {
            "replicate": replicate,
            "arm": arm,
            "reference": registered[(replicate, arm)],
            "sha256": digests[(replicate, arm)],
        }
        for replicate, arm in sorted(registered, key=lambda pair: (pair[0], ARM_NAMES.index(pair[1])))
    ]


def _trajectory_audit(trajectory: Any) -> dict[str, float]:
    inactive = ~trajectory.active_mask
    inactive_action = torch.where(inactive.unsqueeze(-1), trajectory.actions, 0.0).abs()
    inactive_logp = torch.where(inactive, trajectory.old_log_probs, 0.0).abs()
    hidden_delta = torch.where(
        inactive.unsqueeze(-1), trajectory.hidden_after - trajectory.hidden_before, 0.0
    ).abs()
    return {
        "inactive_action_max_abs": float(inactive_action.max()),
        "inactive_logp_max_abs": float(inactive_logp.max()),
        "inactive_hidden_change_max_abs": float(hidden_delta.max()),
    }


def _launch_identity(
    *,
    source_commit: str,
    formal: bool,
    authorization_token: str | None,
    config: RunConfig,
) -> dict[str, Any]:
    return {
        "schema": LAUNCH_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": formal,
        "authorization_token": authorization_token,
        "config": asdict(config),
        "seed_registry": asdict(SeedRegistry()),
        "runtime": _runtime_identity(),
    }


def _open_or_create_launch(root: Path, identity: Mapping[str, Any]) -> bool:
    launch_path = root / "launch_identity.json"
    if not root.exists():
        root.mkdir(parents=True, exist_ok=False)
        _write_json_immutable(launch_path, identity)
        return False
    if not root.is_dir() or not launch_path.is_file():
        raise ValueError("existing UAV G1 root has no complete launch identity")
    existing = _read_json(launch_path)
    if existing != identity:
        raise ValueError("existing UAV G1 launch identity mismatch")
    if not (root / "train_manifest.json").exists() and any(
        (root / name).exists()
        for name in ("evaluation_manifest.json", "analysis_result.json")
    ):
        raise ValueError("existing UAV G1 root has a conflicting terminal artifact")
    return True


def _resume_directory(root: Path, replicate: int, arm: str) -> Path:
    return root / "resume" / f"replicate_{int(replicate)}" / arm


def _resume_base(update: int, attempt: int) -> str:
    return f"update_{int(update):06d}_attempt_{int(attempt):04d}"


def _resume_references(
    root: Path, replicate: int, arm: str, update: int, attempt: int
) -> dict[str, str]:
    directory = _resume_directory(root, replicate, arm).relative_to(root).as_posix()
    base = _resume_base(update, attempt)
    return {
        "checkpoint": f"{directory}/{base}.pt",
        "metadata": f"{directory}/{base}.metadata.json",
        "commit": f"{directory}/{base}.complete.json",
    }


def _resume_fragment_keys(directory: Path) -> dict[Path, tuple[int, int]]:
    result: dict[Path, tuple[int, int]] = {}
    pattern = re.compile(
        r"update_(\d{6})_attempt_(\d{4})(?:\.pt|\.metadata\.json|\.complete\.json)$"
    )
    if not directory.is_dir():
        return result
    for path in directory.iterdir():
        match = pattern.fullmatch(path.name)
        if match is not None and path.is_file():
            result[path] = (int(match.group(1)), int(match.group(2)))
    return result


def _latest_resume_commit(
    root: Path, replicate: int, arm: str
) -> tuple[dict[str, Any] | None, int]:
    directory = _resume_directory(root, replicate, arm)
    fragments = _resume_fragment_keys(directory)
    complete: list[tuple[tuple[int, int], dict[str, Any]]] = []
    committed_paths: set[Path] = set()
    for path, key in fragments.items():
        if not path.name.endswith(".complete.json"):
            continue
        try:
            marker = _read_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            continue
        expected = _resume_references(root, replicate, arm, *key)
        checkpoint_sha256 = marker.get("checkpoint_sha256")
        metadata_sha256 = marker.get("metadata_sha256")
        expected_marker = {
            "schema": RESUME_COMMIT_SCHEMA,
            "replicate": replicate,
            "arm": arm,
            "completed_updates": key[0],
            "attempt": key[1],
            "references": expected,
            "checkpoint_sha256": checkpoint_sha256,
            "metadata_sha256": metadata_sha256,
        }
        if (
            marker != expected_marker
            or any(
                type(value) is not str
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
                for value in (checkpoint_sha256, metadata_sha256)
            )
            or _sha256_file(
                _confined_reference(
                    root, expected["checkpoint"], expected=expected["checkpoint"]
                )
            )
            != checkpoint_sha256
            or _sha256_file(
                _confined_reference(
                    root, expected["metadata"], expected=expected["metadata"]
                )
            )
            != metadata_sha256
        ):
            # A parseable completion marker is a claimed durable commit; a
            # malformed claim is tamper/conflict, not an ignorable fragment.
            raise ValueError("resume completion marker is malformed or misdirected")
        complete.append((key, marker))
        committed_paths.update(root / reference for reference in expected.values())
    ignored = len(set(fragments) - committed_paths)
    if not complete:
        return None, ignored
    complete.sort(key=lambda item: item[0])
    return complete[-1][1], ignored


def _next_resume_attempt(root: Path, replicate: int, arm: str, update: int) -> int:
    keys = _resume_fragment_keys(_resume_directory(root, replicate, arm)).values()
    attempts = [attempt for found_update, attempt in keys if found_update == update]
    attempt = 0 if not attempts else max(attempts) + 1
    if attempt > 9999:
        raise ValueError("resume attempt namespace is exhausted")
    return attempt


def _empty_cumulative() -> dict[str, Any]:
    return {
        "maximum_errors": {
            "logp_max_error": 0.0,
            "joint_logp_max_error": 0.0,
            "value_max_error": 0.0,
            "hidden_max_error": 0.0,
            "prefix_max_error": 0.0,
            "inactive_logp_max_abs": 0.0,
            "inactive_action_max_abs": 0.0,
            "inactive_hidden_change_max_abs": 0.0,
        },
        "finite_updates": True,
        "active_tokens": 0,
        "maximum_gradient_norm": 0.0,
    }


def _validate_cumulative(value: object) -> dict[str, Any]:
    expected = _empty_cumulative()
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError("resume cumulative audit state is malformed")
    maximum = value.get("maximum_errors")
    if type(maximum) is not dict or set(maximum) != set(expected["maximum_errors"]):
        raise ValueError("resume cumulative error maxima are malformed")
    normalized_maximum = {
        name: _finite_number(name, maximum[name]) for name in expected["maximum_errors"]
    }
    if any(number < 0.0 for number in normalized_maximum.values()):
        raise ValueError("resume cumulative error maximum is negative")
    if type(value.get("finite_updates")) is not bool:
        raise ValueError("resume cumulative finite flag is malformed")
    active_tokens = value.get("active_tokens")
    if type(active_tokens) is not int or active_tokens < 0:
        raise ValueError("resume cumulative active-token count is malformed")
    gradient = _finite_number("maximum_gradient_norm", value.get("maximum_gradient_norm"))
    if gradient < 0.0:
        raise ValueError("resume cumulative gradient maximum is negative")
    return {
        "maximum_errors": normalized_maximum,
        "finite_updates": value["finite_updates"],
        "active_tokens": active_tokens,
        "maximum_gradient_norm": gradient,
    }


def _restore_resume_commit(
    root: Path,
    marker: Mapping[str, Any],
    *,
    launch: Mapping[str, Any],
    replicate: int,
    arm: str,
    config: RunConfig,
    seeds: Mapping[str, int],
    model: MatchedContinuousRecurrentPolicy,
    optimizer: torch.optim.Optimizer,
    spec: Mapping[str, int],
) -> tuple[int, dict[str, Any]]:
    update = marker.get("completed_updates")
    attempt = marker.get("attempt")
    if (
        type(update) is not int
        or type(attempt) is not int
        or not 1 <= update <= config.updates
        or attempt < 0
    ):
        raise ValueError("resume completion coordinate is outside the run contract")
    references = _resume_references(root, replicate, arm, update, attempt)
    if marker.get("references") != references:
        raise ValueError("resume completion references changed")
    metadata_path = _confined_reference(
        root, references["metadata"], expected=references["metadata"]
    )
    checkpoint_path = _confined_reference(
        root, references["checkpoint"], expected=references["checkpoint"]
    )
    metadata = _read_json(metadata_path)
    if (
        metadata.get("schema") != RESUME_SCHEMA
        or metadata.get("launch_identity") != launch
        or metadata.get("replicate") != replicate
        or metadata.get("arm") != arm
        or metadata.get("completed_updates") != update
        or metadata.get("next_episode_id") != update * config.num_envs
        or metadata.get("attempt") != attempt
        or metadata.get("checkpoint_reference") != references["checkpoint"]
        or metadata.get("seed_contract") != dict(seeds)
        or metadata.get("environment_spec") != dict(spec)
    ):
        raise ValueError("resume metadata identity/progress mismatch")
    cumulative = _validate_cumulative(metadata.get("cumulative"))
    bundle = load_uav_checkpoint(
        checkpoint_path,
        model=model,
        optimizer=optimizer,
        expected_seed_contract=seeds,
    )
    if (
        bundle.get("completed_updates") != update
        or bundle.get("next_episode_id") != update * config.num_envs
    ):
        raise ValueError("resume checkpoint progress mismatch")
    return update, cumulative


def _validate_written_resume(
    root: Path,
    marker: Mapping[str, Any],
    *,
    launch: Mapping[str, Any],
    replicate: int,
    arm: str,
    config: RunConfig,
    seeds: Mapping[str, int],
    model: MatchedContinuousRecurrentPolicy,
    optimizer: torch.optim.Optimizer,
    spec: Mapping[str, int],
    expected_cumulative: Mapping[str, Any],
) -> None:
    clone = MatchedContinuousRecurrentPolicy(
        int(spec["observation_dim"]),
        int(spec["critic_state_dim"]),
        routing_mode=arm,
    )
    clone_optimizer = torch.optim.Adam(clone.parameters(), lr=LEARNING_RATE)
    update, cumulative = _restore_resume_commit(
        root,
        marker,
        launch=launch,
        replicate=replicate,
        arm=arm,
        config=config,
        seeds=seeds,
        model=clone,
        optimizer=clone_optimizer,
        spec=spec,
    )
    if update != marker["completed_updates"] or cumulative != expected_cumulative:
        raise ValueError("new resume pair does not reproduce cumulative state")
    if maximum_state_difference(model_state_copy(model), model_state_copy(clone)) != 0.0:
        raise ValueError("new resume checkpoint does not reproduce model state")
    if not _nested_tensor_equal(optimizer.state_dict(), clone_optimizer.state_dict()):
        raise ValueError("new resume checkpoint does not reproduce optimizer state")


def _cleanup_older_resume_fragments(
    root: Path, replicate: int, arm: str, *, newest: tuple[int, int]
) -> None:
    directory = _resume_directory(root, replicate, arm)
    for path, key in _resume_fragment_keys(directory).items():
        if key >= newest:
            continue
        try:
            path.resolve().relative_to(directory.resolve())
        except ValueError as error:
            raise ValueError("resume cleanup target escapes its pair directory") from error
        path.unlink()


def _commit_resume_update(
    root: Path,
    *,
    launch: Mapping[str, Any],
    replicate: int,
    arm: str,
    completed_updates: int,
    config: RunConfig,
    seeds: Mapping[str, int],
    model: MatchedContinuousRecurrentPolicy,
    optimizer: torch.optim.Optimizer,
    spec: Mapping[str, int],
    cumulative: Mapping[str, Any],
) -> dict[str, Any]:
    attempt = _next_resume_attempt(root, replicate, arm, completed_updates)
    references = _resume_references(
        root, replicate, arm, completed_updates, attempt
    )
    checkpoint_path = root / references["checkpoint"]
    if checkpoint_path.exists():
        raise ValueError("immutable resume checkpoint path already exists")
    save_uav_checkpoint(
        checkpoint_path,
        model=model,
        optimizer=optimizer,
        completed_updates=completed_updates,
        next_episode_id=completed_updates * config.num_envs,
        seed_contract=seeds,
    )
    metadata = {
        "schema": RESUME_SCHEMA,
        "launch_identity": dict(launch),
        "replicate": replicate,
        "arm": arm,
        "completed_updates": completed_updates,
        "next_episode_id": completed_updates * config.num_envs,
        "attempt": attempt,
        "checkpoint_reference": references["checkpoint"],
        "seed_contract": dict(seeds),
        "environment_spec": dict(spec),
        "cumulative": dict(cumulative),
    }
    _write_json_immutable(root / references["metadata"], metadata)
    checkpoint_sha256 = _sha256_file(root / references["checkpoint"])
    metadata_sha256 = _sha256_file(root / references["metadata"])
    marker = {
        "schema": RESUME_COMMIT_SCHEMA,
        "replicate": replicate,
        "arm": arm,
        "completed_updates": completed_updates,
        "attempt": attempt,
        "references": references,
        "checkpoint_sha256": checkpoint_sha256,
        "metadata_sha256": metadata_sha256,
    }
    _write_json_immutable(root / references["commit"], marker)
    _validate_written_resume(
        root,
        marker,
        launch=launch,
        replicate=replicate,
        arm=arm,
        config=config,
        seeds=seeds,
        model=model,
        optimizer=optimizer,
        spec=spec,
        expected_cumulative=cumulative,
    )
    _cleanup_older_resume_fragments(
        root, replicate, arm, newest=(completed_updates, attempt)
    )
    return marker


def _after_resume_commit(
    *, replicate: int, arm: str, completed_updates: int
) -> None:
    """Test injection seam; production execution deliberately does nothing."""


def _nested_tensor_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
        return isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor) and torch.equal(left, right)
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _nested_tensor_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(
            _nested_tensor_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def _final_checkpoint_marker_reference(reference: str) -> str:
    return f"{reference}.complete.json"


def _ensure_final_checkpoint(
    root: Path,
    *,
    replicate: int,
    arm: str,
    config: RunConfig,
    seeds: Mapping[str, int],
    model: MatchedContinuousRecurrentPolicy,
    optimizer: torch.optim.Optimizer,
    spec: Mapping[str, int],
) -> tuple[float, str]:
    reference = _checkpoint_reference(replicate, arm)
    marker_reference = _final_checkpoint_marker_reference(reference)
    checkpoint = root / reference
    marker_path = root / marker_reference
    marker: dict[str, Any] | None = None
    if marker_path.is_file():
        try:
            candidate = _read_json(marker_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            candidate = None
        checkpoint_digest = _sha256_file(checkpoint) if checkpoint.is_file() else None
        expected_marker = {
            "schema": FINAL_CHECKPOINT_COMMIT_SCHEMA,
            "replicate": replicate,
            "arm": arm,
            "completed_updates": config.updates,
            "checkpoint_reference": reference,
            "checkpoint_sha256": checkpoint_digest,
        }
        if candidate == expected_marker:
            marker = candidate
        else:
            # With no valid completion marker, both files are nonterminal
            # fragments. The final resume pair has already been validated.
            marker_path.unlink()
            if checkpoint.exists():
                checkpoint.unlink()
    elif checkpoint.exists():
        checkpoint.unlink()
    if marker is None:
        save_uav_checkpoint(
            checkpoint,
            model=model,
            optimizer=optimizer,
            completed_updates=config.updates,
            next_episode_id=config.updates * config.num_envs,
            seed_contract=seeds,
        )
    confined = _confined_reference(root, reference, expected=reference)
    checkpoint_digest = _sha256_file(confined)
    clone = MatchedContinuousRecurrentPolicy(
        int(spec["observation_dim"]),
        int(spec["critic_state_dim"]),
        routing_mode=arm,
    )
    clone_optimizer = torch.optim.Adam(clone.parameters(), lr=LEARNING_RATE)
    bundle = load_uav_checkpoint(
        confined,
        model=clone,
        optimizer=clone_optimizer,
        expected_seed_contract=seeds,
    )
    if (
        bundle.get("completed_updates") != config.updates
        or bundle.get("next_episode_id") != config.updates * config.num_envs
        or maximum_state_difference(model_state_copy(model), model_state_copy(clone)) != 0.0
        or not _nested_tensor_equal(optimizer.state_dict(), clone_optimizer.state_dict())
    ):
        raise ValueError("final checkpoint does not match the validated resume state")
    if marker is None:
        _write_json_immutable(
            marker_path,
            {
                "schema": FINAL_CHECKPOINT_COMMIT_SCHEMA,
                "replicate": replicate,
                "arm": arm,
                "completed_updates": config.updates,
                "checkpoint_reference": reference,
                "checkpoint_sha256": checkpoint_digest,
            },
        )
    return (
        maximum_state_difference(model_state_copy(model), model_state_copy(clone)),
        checkpoint_digest,
    )


def _terminal_training_complete(root: Path) -> bool:
    marker_path = root / "train_manifest.complete.json"
    if not marker_path.is_file():
        return False
    try:
        marker = _read_json(marker_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return False
    manifest_sha256 = marker.get("manifest_sha256")
    expected = {
        "schema": TRAIN_MANIFEST_COMMIT_SCHEMA,
        "manifest_reference": "train_manifest.json",
        "manifest_sha256": manifest_sha256,
    }
    if (
        marker != expected
        or type(manifest_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is None
    ):
        raise ValueError("terminal training completion marker conflicts")
    manifest_path = _confined_reference(
        root, marker["manifest_reference"], expected="train_manifest.json"
    )
    if _sha256_file(manifest_path) != manifest_sha256:
        raise ValueError("terminal training completion marker conflicts")
    return True


def _write_training_terminal(root: Path, manifest: Mapping[str, Any]) -> Path:
    manifest_path = root / "train_manifest.json"
    manifest_marker = root / "train_manifest.complete.json"
    if manifest_marker.exists():
        manifest_marker.unlink()
    if manifest_path.exists():
        manifest_path.unlink()
    _write_json_immutable(manifest_path, manifest)
    _write_json_immutable(
        manifest_marker,
        {
            "schema": TRAIN_MANIFEST_COMMIT_SCHEMA,
            "manifest_reference": "train_manifest.json",
            "manifest_sha256": _sha256_file(manifest_path),
        },
    )
    return manifest_path


def train_run(
    root: Path,
    *,
    source_commit: str,
    formal: bool,
    authorization_token: str | None = None,
    config: RunConfig | None = None,
) -> Path:
    root = Path(root)
    chosen = FORMAL_CONFIG if formal else (config or EXERCISE_CONFIG)
    _validate_launch(formal=formal, authorization_token=authorization_token, config=chosen)
    source_commit = _validate_source_commit(source_commit, formal=formal)
    configure_runtime(SeedRegistry().model_initialization)
    launch = _launch_identity(
        source_commit=source_commit,
        formal=formal,
        authorization_token=authorization_token,
        config=chosen,
    )
    root_preexisted = _open_or_create_launch(root, launch)
    if _terminal_training_complete(root):
        manifest = _read_json(root / "train_manifest.json")
        if any(
            manifest.get(name) != expected
            for name, expected in (
                ("schema", RUN_SCHEMA),
                ("source_family", SOURCE_FAMILY),
                ("source_commit", source_commit),
                ("formal", formal),
                ("authorization_token", authorization_token),
                ("config", asdict(chosen)),
                ("seed_registry", asdict(SeedRegistry())),
                ("runtime", launch["runtime"]),
            )
        ):
            raise ValueError("terminal training manifest conflicts with launch identity")
        status = manifest.get("status")
        if status not in {TRAIN_COMPLETE, TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE}:
            raise ValueError("terminal training manifest has an unregistered status")
        if not formal and status != TRAIN_COMPLETE:
            raise ValueError("nonformal training cannot be source-screen skipped")
        if formal:
            screen = _validate_source_screen(root, launch=launch, config=chosen)
            if manifest.get("source_screen") != _source_screen_binding(root, screen):
                raise ValueError("training manifest source-screen binding mismatch")
            if (status == TRAIN_COMPLETE) is not bool(screen["source_identifiable"]):
                raise ValueError("training terminal state conflicts with source screen")
        elif "source_screen" in manifest:
            raise ValueError("nonformal training unexpectedly carries a source screen")
        _registered_checkpoints(root, manifest)
        return root / "train_manifest.json"
    if any((root / name).exists() for name in ("evaluation_manifest.json", "analysis_result.json")):
        raise ValueError("nonterminal training root contains later-stage artifacts")
    started = time.perf_counter()
    source_screen_binding: dict[str, Any] | None = None
    if formal:
        source_screen = _run_source_screen(root, launch=launch, config=chosen)
        source_screen_binding = _source_screen_binding(root, source_screen)
        if not source_screen["source_identifiable"]:
            if (root / "checkpoints").exists() or (root / "resume").exists():
                raise ValueError("failed source screen encountered learned training artifacts")
            return _write_training_terminal(
                root,
                {
                    "schema": RUN_SCHEMA,
                    "source_family": SOURCE_FAMILY,
                    "source_commit": source_commit,
                    "formal": True,
                    "authorization_token": authorization_token,
                    "status": TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE,
                    "runtime": _runtime_identity(),
                    "config": asdict(chosen),
                    "seed_registry": asdict(SeedRegistry()),
                    "arms": list(ARM_NAMES),
                    "training_results": [],
                    "checkpoint_references": [],
                    "source_screen": source_screen_binding,
                    "wall_seconds": time.perf_counter() - started,
                    "resume_telemetry": {
                        "root_preexisted": root_preexisted,
                        "resumed_pairs": 0,
                        "resume_commits_written": 0,
                        "ignored_incomplete_fragments": 0,
                    },
                },
            )
    checkpoint_references: list[str] = []
    training_rows: list[dict[str, Any]] = []
    resumed_pairs = 0
    resume_commits_written = 0
    ignored_incomplete_fragments = 0
    for replicate in range(chosen.replicates):
        seeds = _replicate_seeds(replicate)
        for arm in ARM_NAMES:
            first_ids = tuple(range(chosen.num_envs))
            first_ledgers = _ledgers(LossCell.IID_SINGLE, first_ids, seeds["training_ledger"])
            with PersistentUAVVectorEnv(
                first_ledgers,
                _environment_seeds(seeds["training_environment"], first_ids),
            ) as vector_env:
                spec = vector_env.spec()
                configure_runtime(seeds["model_initialization"])
                fixed_initial = MatchedContinuousRecurrentPolicy(
                    int(spec["observation_dim"]),
                    int(spec["critic_state_dim"]),
                    routing_mode=FIXED_MASK_REC,
                )
                configure_runtime(seeds["model_initialization"])
                open_initial = MatchedContinuousRecurrentPolicy(
                    int(spec["observation_dim"]),
                    int(spec["critic_state_dim"]),
                    routing_mode=PREFIX_NORMALIZED_OPEN_ROSTER,
                )
                initialization_error = maximum_state_difference(
                    model_state_copy(fixed_initial), model_state_copy(open_initial)
                )
                configure_runtime(seeds["model_initialization"])
                model = MatchedContinuousRecurrentPolicy(
                    int(spec["observation_dim"]),
                    int(spec["critic_state_dim"]),
                    routing_mode=arm,
                ).to(torch.device("cpu"))
                optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
                initial_state = model_state_copy(model)
                marker, ignored = _latest_resume_commit(root, replicate, arm)
                ignored_incomplete_fragments += ignored
                completed_updates = 0
                cumulative = _empty_cumulative()
                if marker is not None:
                    completed_updates, cumulative = _restore_resume_commit(
                        root,
                        marker,
                        launch=launch,
                        replicate=replicate,
                        arm=arm,
                        config=chosen,
                        seeds=seeds,
                        model=model,
                        optimizer=optimizer,
                        spec=spec,
                    )
                    resumed_pairs += 1
                for update in range(completed_updates, chosen.updates):
                    episode_ids = tuple(
                        range(update * chosen.num_envs, (update + 1) * chosen.num_envs)
                    )
                    if update:
                        ledgers = _ledgers(
                            LossCell.IID_SINGLE, episode_ids, seeds["training_ledger"]
                        )
                        vector_env.reset(
                            ledgers=ledgers,
                            environment_seeds=_environment_seeds(
                                seeds["training_environment"], episode_ids
                            ),
                        )
                    trajectory = collect_uav_trajectory(
                        model,
                        vector_env,
                        episode_ids=episode_ids,
                        action_seed=seeds["training_action"],
                        device=torch.device("cpu"),
                        horizon=chosen.horizon,
                    )
                    audit = _trajectory_audit(trajectory)
                    metrics = optimize_uav_update(
                        model,
                        optimizer,
                        trajectory,
                        device=torch.device("cpu"),
                        ppo_passes=chosen.ppo_passes,
                    )
                    cumulative["finite_updates"] = bool(
                        cumulative["finite_updates"] and bool(metrics["finite_update"])
                    )
                    cumulative["active_tokens"] += trajectory.active_token_count
                    cumulative["maximum_gradient_norm"] = max(
                        float(cumulative["maximum_gradient_norm"]),
                        float(metrics["gradient_norm"]),
                    )
                    for name in cumulative["maximum_errors"]:
                        cumulative["maximum_errors"][name] = max(
                            float(cumulative["maximum_errors"][name]),
                            float((metrics | audit).get(name, 0.0)),
                        )
                    _commit_resume_update(
                        root,
                        launch=launch,
                        replicate=replicate,
                        arm=arm,
                        completed_updates=update + 1,
                        config=chosen,
                        seeds=seeds,
                        model=model,
                        optimizer=optimizer,
                        spec=spec,
                        cumulative=cumulative,
                    )
                    resume_commits_written += 1
                    _after_resume_commit(
                        replicate=replicate,
                        arm=arm,
                        completed_updates=update + 1,
                    )
                # The final resume pair is the recovery authority; the separate
                # canonical checkpoint remains the sole conclusion-bearing one.
                if chosen.updates <= 0:
                    raise ValueError("training completed without a resume authority")
                roundtrip_error, checkpoint_sha256 = _ensure_final_checkpoint(
                    root,
                    replicate=replicate,
                    arm=arm,
                    config=chosen,
                    seeds=seeds,
                    model=model,
                    optimizer=optimizer,
                    spec=spec,
                )
                reference = _checkpoint_reference(replicate, arm)
                checkpoint_references.append(reference)
                training_rows.append(
                    {
                        "arm": arm,
                        "replicate": replicate,
                        "seeds": seeds,
                        "checkpoint": reference,
                        "checkpoint_sha256": checkpoint_sha256,
                        "parameter_count": model.parameter_count,
                        "environment_transitions": chosen.updates
                        * chosen.num_envs
                        * chosen.horizon,
                        "updates": chosen.updates,
                        "optimizer_steps": chosen.updates * chosen.ppo_passes,
                        "episodes": chosen.updates * chosen.num_envs,
                        "active_tokens": cumulative["active_tokens"],
                        "finite_updates": cumulative["finite_updates"],
                        "maximum_gradient_norm": cumulative["maximum_gradient_norm"],
                        "maximum_errors": cumulative["maximum_errors"],
                        "parameter_drift": maximum_state_difference(
                            initial_state, model_state_copy(model)
                        ),
                        "checkpoint_roundtrip_max_error": roundtrip_error,
                        "paired_initialization_max_error": initialization_error,
                    }
                )
    manifest = {
        "schema": RUN_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": formal,
        "authorization_token": authorization_token,
        "status": TRAIN_COMPLETE,
        "runtime": _runtime_identity(),
        "config": asdict(chosen),
        "seed_registry": asdict(SeedRegistry()),
        "arms": list(ARM_NAMES),
        "training_results": training_rows,
        "checkpoint_references": checkpoint_references,
        "wall_seconds": time.perf_counter() - started,
        "resume_telemetry": {
            "root_preexisted": root_preexisted,
            "resumed_pairs": resumed_pairs,
            "resume_commits_written": resume_commits_written,
            "ignored_incomplete_fragments": ignored_incomplete_fragments,
        },
    }
    if source_screen_binding is not None:
        manifest["source_screen"] = source_screen_binding
    return _write_training_terminal(root, manifest)


def _evaluation_identity(
    manifest: Mapping[str, Any], registered: Mapping[tuple[int, str], str], *, exercise: bool
) -> dict[str, Any]:
    identity = {
        "schema": EVALUATION_LAUNCH_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": manifest["formal"],
        "exercise": exercise,
        "config": manifest["config"],
        "runtime": _runtime_identity(),
        "checkpoint_references": _evaluation_checkpoint_inventory(registered, manifest),
    }
    if manifest["formal"]:
        identity["source_screen"] = manifest["source_screen"]
    return identity


def _open_evaluation_launch(root: Path, identity: Mapping[str, Any]) -> bool:
    path = root / "evaluation_launch_identity.json"
    if path.exists():
        if not path.is_file() or _read_json(path) != identity:
            raise ValueError("existing evaluation launch identity mismatch")
        return True
    _write_json_immutable(path, identity)
    return False


def _evaluation_terminal_complete(root: Path) -> bool:
    marker_path = root / "evaluation_manifest.complete.json"
    if not marker_path.is_file():
        return False
    try:
        marker = _read_json(marker_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return False
    expected = {
        "schema": EVALUATION_MANIFEST_COMMIT_SCHEMA,
        "manifest_reference": "evaluation_manifest.json",
        "rows_reference": "evaluation_rows.jsonl",
    }
    if marker != expected:
        raise ValueError("terminal evaluation completion marker conflicts")
    _confined_reference(root, "evaluation_manifest.json", expected="evaluation_manifest.json")
    _confined_reference(root, "evaluation_rows.jsonl", expected="evaluation_rows.jsonl")
    return True


def _evaluation_chunk_key(
    *, kind: str, replicate: int, subject: str, cell: LossCell,
    mode: str, start: int, count: int,
) -> dict[str, Any]:
    if kind not in {"learned", "control", "exercise"}:
        raise ValueError("evaluation chunk kind is invalid")
    return {
        "kind": kind,
        "replicate": int(replicate),
        "subject": subject,
        "cell": cell.value,
        "mode": mode,
        "start_episode": int(start),
        "episode_count": int(count),
    }


def _expected_evaluation_chunk_keys(
    config: RunConfig, *, exercise: bool, control_only: bool = False
) -> list[dict[str, Any]]:
    if exercise and control_only:
        raise ValueError("exercise evaluation cannot request formal control-only inventory")
    keys: list[dict[str, Any]] = []
    for replicate in range(config.replicates):
        if exercise:
            for subject in SUBJECT_NAMES:
                keys.append(
                    _evaluation_chunk_key(
                        kind="exercise",
                        replicate=replicate,
                        subject=subject,
                        cell=LossCell.NO_DISTURBANCE,
                        mode="deterministic",
                        start=0,
                        count=config.evaluation_batch_size,
                    )
                )
            continue
        if not control_only:
            for arm in ARM_NAMES:
                for cell in EVALUATION_CELLS:
                    for mode in ACTION_MODES:
                        for start in range(
                            0, config.evaluation_episodes, config.evaluation_batch_size
                        ):
                            keys.append(
                                _evaluation_chunk_key(
                                    kind="learned",
                                    replicate=replicate,
                                    subject=arm,
                                    cell=cell,
                                    mode=mode,
                                    start=start,
                                    count=config.evaluation_batch_size,
                                )
                            )
        for cell in EVALUATION_CELLS:
            for control in CONTROL_NAMES:
                for start in range(
                    0, config.evaluation_episodes, config.evaluation_batch_size
                ):
                    keys.append(
                        _evaluation_chunk_key(
                            kind="control",
                            replicate=replicate,
                            subject=control,
                            cell=cell,
                            mode="paired_modes",
                            start=start,
                            count=config.evaluation_batch_size,
                        )
                    )
    return keys


def _assemble_committed_evaluation_rows(
    root: Path,
    *,
    config: RunConfig,
    exercise: bool,
    identity: Mapping[str, Any],
    registered: Mapping[tuple[int, str], str],
    control_only: bool = False,
    control_identity: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in _expected_evaluation_chunk_keys(
        config, exercise=exercise, control_only=control_only
    ):
        chunk_identity = (
            control_identity if key["kind"] == "control" else identity
        )
        if chunk_identity is None:
            raise ValueError("control chunk assembly has no source-screen identity")
        chunk_rows, _ignored = _latest_evaluation_chunk(
            root, key=key, identity=chunk_identity, registered=registered
        )
        if chunk_rows is None:
            raise ValueError("evaluation terminal assembly is missing a completed chunk")
        rows.extend(chunk_rows)
    return rows


def _evaluation_chunk_directory(root: Path, key: Mapping[str, Any]) -> Path:
    return (
        root
        / "evaluation_chunks"
        / str(key["kind"])
        / f"replicate_{int(key['replicate'])}"
        / str(key["subject"])
        / str(key["cell"])
        / str(key["mode"])
        / f"batch_{int(key['start_episode']):06d}"
    )


def _evaluation_chunk_references(
    root: Path, key: Mapping[str, Any], attempt: int
) -> dict[str, str]:
    directory = _evaluation_chunk_directory(root, key).relative_to(root).as_posix()
    base = f"attempt_{int(attempt):04d}"
    return {
        "chunk": f"{directory}/{base}.json",
        "commit": f"{directory}/{base}.complete.json",
    }


def _evaluation_chunk_fragments(directory: Path) -> dict[Path, int]:
    result: dict[Path, int] = {}
    pattern = re.compile(r"attempt_(\d{4})(?:\.json|\.complete\.json)$")
    if not directory.is_dir():
        return result
    for path in directory.iterdir():
        match = pattern.fullmatch(path.name)
        if match is not None and path.is_file():
            result[path] = int(match.group(1))
    return result


def _validate_chunk_rows(
    rows: object,
    *,
    key: Mapping[str, Any],
    identity: Mapping[str, Any],
    registered: Mapping[tuple[int, str], str],
) -> list[dict[str, Any]]:
    if type(rows) is not list or any(type(row) is not dict for row in rows):
        raise ValueError("evaluation chunk rows are malformed")
    count = int(key["episode_count"])
    exercise = bool(identity["exercise"])
    expected_count = count * (2 if key["kind"] == "control" else 1)
    if len(rows) != expected_count:
        raise ValueError("evaluation chunk row count mismatch")
    expected_episodes = set(
        range(int(key["start_episode"]), int(key["start_episode"]) + count)
    )
    observed: set[tuple[int, str]] = set()
    for row in rows:
        if (
            row.get("source_family") != SOURCE_FAMILY
            or row.get("source_commit") != identity["source_commit"]
            or row.get("formal") is not identity["formal"]
            or row.get("replicate") != key["replicate"]
            or row.get("subject") != key["subject"]
            or row.get("cell") != key["cell"]
            or row.get("episode_id") not in expected_episodes
        ):
            raise ValueError("evaluation chunk row identity mismatch")
        if key["kind"] == "control":
            if row.get("action_mode") not in ACTION_MODES:
                raise ValueError("control chunk action-mode inventory mismatch")
        elif row.get("action_mode") != key["mode"]:
            raise ValueError("evaluation chunk action mode mismatch")
        subject = str(key["subject"])
        expected_checkpoint = (
            registered[(int(key["replicate"]), subject)]
            if subject in ARM_NAMES
            else None
        )
        if row.get("checkpoint_reference") != expected_checkpoint:
            raise ValueError("evaluation chunk checkpoint reference mismatch")
        if exercise and row.get("exercise") is not True:
            raise ValueError("exercise chunk row identity mismatch")
        observed.add((int(row["episode_id"]), str(row["action_mode"])))
    expected_observed = {
        (episode, mode)
        for episode in expected_episodes
        for mode in (ACTION_MODES if key["kind"] == "control" else (str(key["mode"]),))
    }
    if observed != expected_observed:
        raise ValueError("evaluation chunk episode/mode inventory mismatch")
    return rows


def _latest_evaluation_chunk(
    root: Path,
    *,
    key: Mapping[str, Any],
    identity: Mapping[str, Any],
    registered: Mapping[tuple[int, str], str],
) -> tuple[list[dict[str, Any]] | None, int]:
    directory = _evaluation_chunk_directory(root, key)
    fragments = _evaluation_chunk_fragments(directory)
    complete: list[tuple[int, dict[str, Any]]] = []
    committed_paths: set[Path] = set()
    for path, attempt in fragments.items():
        if not path.name.endswith(".complete.json"):
            continue
        try:
            marker = _read_json(path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            continue
        references = _evaluation_chunk_references(root, key, attempt)
        chunk_sha256 = marker.get("chunk_sha256")
        expected_marker = {
            "schema": EVALUATION_CHUNK_COMMIT_SCHEMA,
            "key": dict(key),
            "attempt": attempt,
            "references": references,
            "chunk_sha256": chunk_sha256,
        }
        if (
            marker != expected_marker
            or type(chunk_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", chunk_sha256) is None
            or _sha256_file(
                _confined_reference(
                    root, references["chunk"], expected=references["chunk"]
                )
            )
            != chunk_sha256
        ):
            raise ValueError("evaluation chunk completion marker is malformed")
        complete.append((attempt, marker))
        committed_paths.update(root / reference for reference in references.values())
    ignored = len(set(fragments) - committed_paths)
    if not complete:
        return None, ignored
    attempt, marker = max(complete, key=lambda item: item[0])
    reference = marker["references"]["chunk"]
    chunk = _read_json(_confined_reference(root, reference, expected=reference))
    if (
        chunk.get("schema") != EVALUATION_CHUNK_SCHEMA
        or chunk.get("evaluation_identity") != identity
        or chunk.get("key") != dict(key)
        or chunk.get("attempt") != attempt
    ):
        raise ValueError("evaluation chunk identity mismatch")
    rows = _validate_chunk_rows(
        chunk.get("rows"), key=key, identity=identity, registered=registered
    )
    return rows, ignored


def _commit_evaluation_chunk(
    root: Path,
    *,
    key: Mapping[str, Any],
    identity: Mapping[str, Any],
    registered: Mapping[tuple[int, str], str],
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    fragments = _evaluation_chunk_fragments(_evaluation_chunk_directory(root, key))
    attempt = 0 if not fragments else max(fragments.values()) + 1
    if attempt > 9999:
        raise ValueError("evaluation chunk attempt namespace is exhausted")
    references = _evaluation_chunk_references(root, key, attempt)
    payload = {
        "schema": EVALUATION_CHUNK_SCHEMA,
        "evaluation_identity": dict(identity),
        "key": dict(key),
        "attempt": attempt,
        "rows": list(rows),
    }
    _write_json_immutable(root / references["chunk"], payload)
    chunk_sha256 = _sha256_file(root / references["chunk"])
    marker = {
        "schema": EVALUATION_CHUNK_COMMIT_SCHEMA,
        "key": dict(key),
        "attempt": attempt,
        "references": references,
        "chunk_sha256": chunk_sha256,
    }
    _write_json_immutable(root / references["commit"], marker)
    loaded, _ignored = _latest_evaluation_chunk(
        root, key=key, identity=identity, registered=registered
    )
    if loaded != list(rows):
        raise ValueError("written evaluation chunk does not reproduce rows")
    directory = _evaluation_chunk_directory(root, key)
    for path, old_attempt in _evaluation_chunk_fragments(directory).items():
        if old_attempt >= attempt:
            continue
        try:
            path.resolve().relative_to(directory.resolve())
        except ValueError as error:
            raise ValueError("evaluation chunk cleanup escapes its directory") from error
        path.unlink()
    return loaded


def _after_evaluation_chunk_commit(*, key: Mapping[str, Any]) -> None:
    """Test injection seam; production execution deliberately does nothing."""


def _source_screen_identity(
    run_identity: Mapping[str, Any], *, config: RunConfig
) -> dict[str, Any]:
    if run_identity.get("formal") is not True:
        raise ValueError("source screen is formal-only")
    return {
        "schema": SOURCE_SCREEN_LAUNCH_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": run_identity["source_commit"],
        "formal": True,
        "exercise": False,
        "authorization_token": run_identity["authorization_token"],
        "config": asdict(config),
        "seed_registry": asdict(SeedRegistry()),
        "runtime": _runtime_identity(),
    }


def _open_source_screen_launch(root: Path, identity: Mapping[str, Any]) -> None:
    path = root / "source_screen_launch_identity.json"
    if path.exists():
        if not path.is_file() or _read_json(path) != identity:
            raise ValueError("existing source-screen launch identity mismatch")
        return
    _write_json_immutable(path, identity)


def _source_screen_terminal_complete(root: Path) -> bool:
    marker_path = root / "source_screen.complete.json"
    if not marker_path.is_file():
        return False
    try:
        marker = _read_json(marker_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return False
    reference = "source_screen.json"
    artifact = _confined_reference(root, marker.get("artifact_reference"), expected=reference)
    digest = marker.get("artifact_sha256")
    expected = {
        "schema": SOURCE_SCREEN_COMMIT_SCHEMA,
        "artifact_reference": reference,
        "artifact_sha256": digest,
    }
    if (
        marker != expected
        or type(digest) is not str
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        or _sha256_file(artifact) != digest
    ):
        raise ValueError("source-screen completion marker is malformed")
    return True


def _source_screen_binding(
    root: Path, screen: Mapping[str, Any]
) -> dict[str, Any]:
    artifact = _confined_reference(root, "source_screen.json", expected="source_screen.json")
    if not _source_screen_terminal_complete(root):
        raise ValueError("source-screen terminal completion marker is missing")
    return {
        "reference": "source_screen.json",
        "complete_reference": "source_screen.complete.json",
        "sha256": _sha256_file(artifact),
        "source_identifiable": bool(screen["source_identifiable"]),
    }


def _ensure_control_chunks_for_replicate(
    root: Path,
    *,
    run_identity: Mapping[str, Any],
    config: RunConfig,
    identity: Mapping[str, Any],
    replicate: int,
) -> tuple[list[dict[str, Any]], int, int, int]:
    seeds = _replicate_seeds(replicate)
    inventory: list[tuple[dict[str, Any], list[dict[str, Any]] | None]] = []
    ignored_total = 0
    for cell in EVALUATION_CELLS:
        for control in CONTROL_NAMES:
            for start in range(
                0, config.evaluation_episodes, config.evaluation_batch_size
            ):
                key = _evaluation_chunk_key(
                    kind="control",
                    replicate=replicate,
                    subject=control,
                    cell=cell,
                    mode="paired_modes",
                    start=start,
                    count=config.evaluation_batch_size,
                )
                existing, ignored = _latest_evaluation_chunk(
                    root, key=key, identity=identity, registered={}
                )
                ignored_total += ignored
                inventory.append((key, existing))
    missing = any(existing is None for _key, existing in inventory)
    initial_ids = tuple(range(config.evaluation_batch_size))
    vector_env = None
    if missing:
        initial_ledgers = _ledgers(
            EVALUATION_CELLS[0], initial_ids, seeds["evaluation_ledger"]
        )
        vector_env = PersistentUAVVectorEnv(
            initial_ledgers,
            _environment_seeds(seeds["evaluation_environment"], initial_ids),
        )
    rows: list[dict[str, Any]] = []
    reused = written = 0
    try:
        for key, existing in inventory:
            if existing is not None:
                rows.extend(existing)
                reused += 1
                continue
            assert vector_env is not None
            cell = LossCell(key["cell"])
            control = str(key["subject"])
            start = int(key["start_episode"])
            episode_ids = tuple(range(start, start + config.evaluation_batch_size))
            ledgers = _ledgers(cell, episode_ids, seeds["evaluation_ledger"])
            vector_env.reset(
                ledgers=ledgers,
                environment_seeds=_environment_seeds(
                    seeds["evaluation_environment"], episode_ids
                ),
            )
            qos = evaluate_uav_controller(
                vector_env, kind=control, horizon=config.horizon
            )
            chunk_rows: list[dict[str, Any]] = []
            for column, (episode_id, ledger) in enumerate(zip(episode_ids, ledgers)):
                metrics = compute_episode_metrics(qos[:, column], ledger)
                for mode in ACTION_MODES:
                    chunk_rows.append(
                        _evaluation_row(
                            manifest=run_identity,
                            subject=control,
                            replicate=replicate,
                            cell=cell,
                            mode=mode,
                            episode_id=episode_id,
                            ledger=ledger,
                            metrics=metrics,
                            checkpoint_reference=None,
                        )
                    )
            committed = _commit_evaluation_chunk(
                root,
                key=key,
                identity=identity,
                registered={},
                rows=chunk_rows,
            )
            written += 1
            _after_evaluation_chunk_commit(key=key)
            rows.extend(committed)
    finally:
        if vector_env is not None:
            vector_env.close()
    return rows, reused, written, ignored_total


def _validate_source_control_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    run_identity: Mapping[str, Any],
    config: RunConfig,
) -> None:
    expected = (
        config.replicates
        * len(CONTROL_NAMES)
        * len(EVALUATION_CELLS)
        * len(ACTION_MODES)
        * config.evaluation_episodes
    )
    if len(rows) != expected:
        raise ValueError("source-screen control row count mismatch")
    paired: dict[tuple[int, str, str, int], dict[str, str]] = {}
    for row in rows:
        if row.get("subject") not in CONTROL_NAMES:
            raise ValueError("source-screen inventory contains a learned subject")
        _validate_evaluation_row(
            row, manifest=run_identity, config=config, registered={}
        )
        key = (
            int(row["replicate"]),
            str(row["cell"]),
            str(row["action_mode"]),
            int(row["episode_id"]),
        )
        subjects = paired.setdefault(key, {})
        subject = str(row["subject"])
        if subject in subjects:
            raise ValueError("source-screen paired key contains a duplicate control")
        subjects[subject] = str(row["ledger_id"])
    if any(
        set(subjects) != set(CONTROL_NAMES) or len(set(subjects.values())) != 1
        for subjects in paired.values()
    ):
        raise ValueError("source-screen controls do not share exact episode ledgers")


def _source_screen_payload(
    run_identity: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    config: RunConfig,
) -> dict[str, Any]:
    _validate_source_control_rows(rows, run_identity=run_identity, config=config)
    intervals = source_control_intervals(
        rows,
        config=config,
        resamples=config.bootstrap_resamples,
        seed=int(run_identity["seed_registry"]["bootstrap"]),
    )
    identification = _source_identification(intervals)
    return {
        "schema": SOURCE_SCREEN_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": run_identity["source_commit"],
        "formal": True,
        "status": "SOURCE_SCREEN_COMPLETE",
        "runtime": _runtime_identity(),
        "config": asdict(config),
        "seed_registry": asdict(SeedRegistry()),
        "evaluation_row_count": len(rows),
        "evaluation_chunk_count": len(
            _expected_evaluation_chunk_keys(
                config, exercise=False, control_only=True
            )
        ),
        "metrics": intervals,
        "source_identification": identification,
        "source_identifiable": all(identification.values()),
        "conclusion_bearing": False,
        "thresholds": {
            "constructive": CONSTRUCTIVE_FLOOR,
            "load_bearing": LOAD_BEARING_MARGIN,
        },
    }


def _validate_source_screen(
    root: Path, *, launch: Mapping[str, Any], config: RunConfig
) -> dict[str, Any]:
    identity = _source_screen_identity(launch, config=config)
    if _read_json(root / "source_screen_launch_identity.json") != identity:
        raise ValueError("source-screen launch identity mismatch")
    if not _source_screen_terminal_complete(root):
        raise ValueError("source-screen terminal completion marker is missing")
    rows = _assemble_committed_evaluation_rows(
        root,
        config=config,
        exercise=False,
        identity=identity,
        registered={},
        control_only=True,
        control_identity=identity,
    )
    expected = _source_screen_payload(launch, rows, config=config)
    actual = _read_json(root / "source_screen.json")
    if actual != expected:
        raise ValueError("source-screen artifact does not reproduce frozen evidence")
    return actual


def _run_source_screen(
    root: Path, *, launch: Mapping[str, Any], config: RunConfig
) -> dict[str, Any]:
    identity = _source_screen_identity(launch, config=config)
    _open_source_screen_launch(root, identity)
    if _source_screen_terminal_complete(root):
        return _validate_source_screen(root, launch=launch, config=config)
    rows: list[dict[str, Any]] = []
    for replicate in range(config.replicates):
        replicate_rows, _reused, _written, _ignored = _ensure_control_chunks_for_replicate(
            root,
            run_identity=launch,
            config=config,
            identity=identity,
            replicate=replicate,
        )
        rows.extend(replicate_rows)
    payload = _source_screen_payload(launch, rows, config=config)
    artifact = root / "source_screen.json"
    marker = root / "source_screen.complete.json"
    if marker.exists():
        marker.unlink()
    if artifact.exists():
        artifact.unlink()
    _write_json_immutable(artifact, payload)
    _write_json_immutable(
        marker,
        {
            "schema": SOURCE_SCREEN_COMMIT_SCHEMA,
            "artifact_reference": "source_screen.json",
            "artifact_sha256": _sha256_file(artifact),
        },
    )
    return _validate_source_screen(root, launch=launch, config=config)


def _write_evaluation_terminal(
    root: Path,
    *,
    rows: Sequence[Mapping[str, Any]],
    evaluation: Mapping[str, Any],
) -> Path:
    marker_path = root / "evaluation_manifest.complete.json"
    if marker_path.exists():
        marker_path.unlink()
    for path in (root / "evaluation_rows.jsonl", root / "evaluation_manifest.json"):
        if path.exists():
            path.unlink()
    _write_jsonl_immutable(root / "evaluation_rows.jsonl", rows)
    _write_json_immutable(root / "evaluation_manifest.json", evaluation)
    _write_json_immutable(
        marker_path,
        {
            "schema": EVALUATION_MANIFEST_COMMIT_SCHEMA,
            "manifest_reference": "evaluation_manifest.json",
            "rows_reference": "evaluation_rows.jsonl",
        },
    )
    return root / "evaluation_manifest.json"


def _evaluation_row(
    *, manifest: Mapping[str, Any], subject: str, replicate: int, cell: LossCell,
    mode: str, episode_id: int, ledger: Any, metrics: Mapping[str, Any],
    checkpoint_reference: str | None,
) -> dict[str, Any]:
    return {
        "schema": EVALUATION_ROW_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": manifest["formal"],
        "subject": subject,
        "checkpoint_reference": checkpoint_reference,
        "replicate": replicate,
        "cell": cell.value,
        "action_mode": mode,
        "episode_id": episode_id,
        **_ledger_payload(ledger),
        "J_event": metrics["J_event"],
        "J_rejoin": metrics["J_rejoin"],
        "Q_ordinary": metrics["Q_ordinary"],
    }


def evaluate_run(root: Path) -> Path:
    root = Path(root)
    manifest = _read_json(root / "train_manifest.json")
    if (
        manifest.get("status")
        not in {TRAIN_COMPLETE, TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE}
        or not _terminal_training_complete(root)
    ):
        raise ValueError("UAV G1 evaluation requires terminal training closure")
    config = RunConfig(**manifest["config"])
    configure_runtime(SeedRegistry().model_initialization)
    if manifest["formal"]:
        launch = _read_json(root / "launch_identity.json")
        screen = _validate_source_screen(root, launch=launch, config=config)
        if manifest.get("source_screen") != _source_screen_binding(root, screen):
            raise ValueError("evaluation source-screen binding mismatch")
    registered = _registered_checkpoints(root, manifest)
    exercise_mode = not bool(manifest["formal"])
    identity = _evaluation_identity(manifest, registered, exercise=exercise_mode)
    launch_preexisted = _open_evaluation_launch(root, identity)
    if _evaluation_terminal_complete(root):
        evaluation = _read_json(root / "evaluation_manifest.json")
        if evaluation.get("evaluation_identity") != identity:
            raise ValueError("terminal evaluation identity mismatch")
        if exercise_mode:
            _validate_exercise_evaluation(root, manifest, evaluation)
        else:
            _validate_evaluation_artifacts(root, manifest, evaluation)
        return root / "evaluation_manifest.json"
    if exercise_mode:
        return _evaluate_exercise_run(root, manifest, config, registered, identity, launch_preexisted)
    if manifest["status"] == TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE:
        return _evaluate_source_skipped_run(
            root, manifest, config, identity, launch_preexisted
        )
    return _evaluate_formal_run(root, manifest, config, registered, identity, launch_preexisted)


def _evaluate_formal_run(
    root: Path,
    manifest: Mapping[str, Any],
    config: RunConfig,
    registered: Mapping[tuple[int, str], str],
    identity: Mapping[str, Any],
    launch_preexisted: bool,
) -> Path:
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    reused = written = ignored_total = 0
    for replicate in range(config.replicates):
        seeds = _replicate_seeds(replicate)
        initial_ids = tuple(range(config.evaluation_batch_size))
        initial_ledgers = _ledgers(
            EVALUATION_CELLS[0], initial_ids, seeds["evaluation_ledger"]
        )
        environment_seeds = _environment_seeds(
            seeds["evaluation_environment"], initial_ids
        )
        for arm in ARM_NAMES:
            inventory: list[tuple[dict[str, Any], list[dict[str, Any]] | None]] = []
            for cell in EVALUATION_CELLS:
                for mode in ACTION_MODES:
                    for start in range(
                        0, config.evaluation_episodes, config.evaluation_batch_size
                    ):
                        key = _evaluation_chunk_key(
                            kind="learned",
                            replicate=replicate,
                            subject=arm,
                            cell=cell,
                            mode=mode,
                            start=start,
                            count=config.evaluation_batch_size,
                        )
                        existing, ignored = _latest_evaluation_chunk(
                            root, key=key, identity=identity, registered=registered
                        )
                        ignored_total += ignored
                        inventory.append((key, existing))
            missing = any(existing is None for _key, existing in inventory)
            vector_env = (
                PersistentUAVVectorEnv(initial_ledgers, environment_seeds)
                if missing
                else None
            )
            try:
                model: MatchedContinuousRecurrentPolicy | None = None
                if vector_env is not None:
                    spec = vector_env.spec()
                    model = MatchedContinuousRecurrentPolicy(
                        int(spec["observation_dim"]),
                        int(spec["critic_state_dim"]),
                        routing_mode=arm,
                    )
                    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
                    load_uav_checkpoint(
                        root / registered[(replicate, arm)],
                        model=model,
                        optimizer=optimizer,
                        expected_seed_contract=seeds,
                    )
                for key, existing in inventory:
                    if existing is not None:
                        rows.extend(existing)
                        reused += 1
                        continue
                    assert vector_env is not None and model is not None
                    cell = LossCell(key["cell"])
                    mode = str(key["mode"])
                    start = int(key["start_episode"])
                    episode_ids = tuple(
                        range(start, start + config.evaluation_batch_size)
                    )
                    ledgers = _ledgers(cell, episode_ids, seeds["evaluation_ledger"])
                    vector_env.reset(
                        ledgers=ledgers,
                        environment_seeds=_environment_seeds(
                            seeds["evaluation_environment"], episode_ids
                        ),
                    )
                    qos = evaluate_uav_policy(
                        model,
                        vector_env,
                        episode_ids=episode_ids,
                        action_seed=seeds["evaluation_action"],
                        device=torch.device("cpu"),
                        deterministic=mode == "deterministic",
                        horizon=config.horizon,
                    )
                    chunk_rows = [
                        _evaluation_row(
                            manifest=manifest,
                            subject=arm,
                            replicate=replicate,
                            cell=cell,
                            mode=mode,
                            episode_id=episode_id,
                            ledger=ledger,
                            metrics=compute_episode_metrics(qos[:, column], ledger),
                            checkpoint_reference=registered[(replicate, arm)],
                        )
                        for column, (episode_id, ledger) in enumerate(
                            zip(episode_ids, ledgers)
                        )
                    ]
                    committed = _commit_evaluation_chunk(
                        root,
                        key=key,
                        identity=identity,
                        registered=registered,
                        rows=chunk_rows,
                    )
                    written += 1
                    _after_evaluation_chunk_commit(key=key)
                    rows.extend(committed)
            finally:
                if vector_env is not None:
                    vector_env.close()
        control_rows, control_reused, control_written, control_ignored = (
            _ensure_control_chunks_for_replicate(
                root,
                run_identity=manifest,
                config=config,
                identity=_source_screen_identity(manifest, config=config),
                replicate=replicate,
            )
        )
        rows.extend(control_rows)
        reused += control_reused
        written += control_written
        ignored_total += control_ignored
    evaluation = {
        "schema": EVALUATION_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": True,
        "status": "EVALUATION_COMPLETE",
        "runtime": _runtime_identity(),
        "config": manifest["config"],
        "evaluation_rows_reference": "evaluation_rows.jsonl",
        "evaluation_row_count": len(rows),
        "checkpoint_references": _evaluation_checkpoint_inventory(registered, manifest),
        "evaluation_identity": identity,
        "wall_seconds": time.perf_counter() - started,
        "resume_telemetry": {
            "launch_preexisted": launch_preexisted,
            "chunks_reused": reused,
            "chunks_written": written,
            "ignored_incomplete_fragments": ignored_total,
        },
    }
    return _write_evaluation_terminal(root, rows=rows, evaluation=evaluation)


def _evaluate_source_skipped_run(
    root: Path,
    manifest: Mapping[str, Any],
    config: RunConfig,
    identity: Mapping[str, Any],
    launch_preexisted: bool,
) -> Path:
    started = time.perf_counter()
    source_identity = _source_screen_identity(manifest, config=config)
    rows = _assemble_committed_evaluation_rows(
        root,
        config=config,
        exercise=False,
        identity=identity,
        registered={},
        control_only=True,
        control_identity=source_identity,
    )
    _validate_source_control_rows(rows, run_identity=manifest, config=config)
    evaluation = {
        "schema": EVALUATION_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": True,
        "status": "EVALUATION_COMPLETE",
        "training_status": TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE,
        "runtime": _runtime_identity(),
        "config": manifest["config"],
        "evaluation_rows_reference": "evaluation_rows.jsonl",
        "evaluation_row_count": len(rows),
        "checkpoint_references": [],
        "evaluation_identity": identity,
        "wall_seconds": time.perf_counter() - started,
        "resume_telemetry": {
            "launch_preexisted": launch_preexisted,
            "chunks_reused": len(
                _expected_evaluation_chunk_keys(
                    config, exercise=False, control_only=True
                )
            ),
            "chunks_written": 0,
            "ignored_incomplete_fragments": 0,
        },
    }
    return _write_evaluation_terminal(root, rows=rows, evaluation=evaluation)


def _evaluate_exercise_run(
    root: Path,
    manifest: Mapping[str, Any],
    config: RunConfig,
    registered: Mapping[tuple[int, str], str],
    identity: Mapping[str, Any],
    launch_preexisted: bool,
) -> Path:
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    reused = written = ignored_total = 0
    for replicate in range(config.replicates):
        seeds = _replicate_seeds(replicate)
        episode_ids = tuple(range(config.evaluation_batch_size))
        ledgers = _ledgers(
            LossCell.NO_DISTURBANCE, episode_ids, seeds["evaluation_ledger"]
        )
        environment_seeds = _environment_seeds(
            seeds["evaluation_environment"], episode_ids
        )
        for subject in SUBJECT_NAMES:
            key = _evaluation_chunk_key(
                kind="exercise",
                replicate=replicate,
                subject=subject,
                cell=LossCell.NO_DISTURBANCE,
                mode="deterministic",
                start=0,
                count=config.evaluation_batch_size,
            )
            existing, ignored = _latest_evaluation_chunk(
                root, key=key, identity=identity, registered=registered
            )
            ignored_total += ignored
            if existing is not None:
                rows.extend(existing)
                reused += 1
                continue
            with PersistentUAVVectorEnv(ledgers, environment_seeds) as vector_env:
                if subject in ARM_NAMES:
                    spec = vector_env.spec()
                    model = MatchedContinuousRecurrentPolicy(
                        int(spec["observation_dim"]),
                        int(spec["critic_state_dim"]),
                        routing_mode=subject,
                    )
                    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
                    load_uav_checkpoint(
                        root / registered[(replicate, subject)],
                        model=model,
                        optimizer=optimizer,
                        expected_seed_contract=seeds,
                    )
                    qos = evaluate_uav_policy(
                        model,
                        vector_env,
                        episode_ids=episode_ids,
                        action_seed=seeds["evaluation_action"],
                        device=torch.device("cpu"),
                        deterministic=True,
                        horizon=config.horizon,
                    )
                    checkpoint_reference = registered[(replicate, subject)]
                else:
                    qos = evaluate_uav_controller(
                        vector_env, kind=subject, horizon=config.horizon
                    )
                    checkpoint_reference = None
            chunk_rows = [
                {
                    "schema": EVALUATION_ROW_SCHEMA,
                    "source_family": SOURCE_FAMILY,
                    "source_commit": manifest["source_commit"],
                    "formal": False,
                    "exercise": True,
                    "subject": subject,
                    "checkpoint_reference": checkpoint_reference,
                    "replicate": replicate,
                    "cell": LossCell.NO_DISTURBANCE.value,
                    "action_mode": "deterministic",
                    "episode_id": episode_id,
                    **_ledger_payload(ledger),
                    "observed_steps": config.horizon,
                    "mean_qos": float(qos[:, column].mean()),
                }
                for column, (episode_id, ledger) in enumerate(zip(episode_ids, ledgers))
            ]
            committed = _commit_evaluation_chunk(
                root,
                key=key,
                identity=identity,
                registered=registered,
                rows=chunk_rows,
            )
            written += 1
            _after_evaluation_chunk_commit(key=key)
            rows.extend(committed)
    evaluation = {
        "schema": EVALUATION_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": False,
        "exercise": True,
        "status": "EVALUATION_COMPLETE",
        "runtime": _runtime_identity(),
        "config": manifest["config"],
        "evaluation_rows_reference": "evaluation_rows.jsonl",
        "evaluation_row_count": len(rows),
        "checkpoint_references": _evaluation_checkpoint_inventory(registered, manifest),
        "evaluation_identity": identity,
        "wall_seconds": time.perf_counter() - started,
        "resume_telemetry": {
            "launch_preexisted": launch_preexisted,
            "chunks_reused": reused,
            "chunks_written": written,
            "ignored_incomplete_fragments": ignored_total,
        },
    }
    return _write_evaluation_terminal(root, rows=rows, evaluation=evaluation)


def _finite_number(name: str, value: object) -> float:
    if type(value) not in (int, float) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def select_result_branch(predicate_inputs: Mapping[str, object]) -> str:
    for name in ("operational_valid", "source_identifiable"):
        if type(predicate_inputs.get(name)) is not bool:
            raise ValueError(f"{name} must be an exact boolean")
    numeric = {
        name: _finite_number(name, predicate_inputs.get(name))
        for name in (
            "access_lcb", "access_ucb", "fixed_access_lcb", "open_access_lcb",
            "g_svc_lcb", "g_svc_ucb", "g_rejoin_lcb", "g_rejoin_ucb",
            "g_ordinary_lcb", "g_ordinary_ucb",
        )
    }
    if not predicate_inputs["operational_valid"]:
        return INVALID_RESULT
    if not predicate_inputs["source_identifiable"]:
        return SOURCE_NON_IDENTIFIABLE_RESULT
    if numeric["access_ucb"] < ACCESS_THRESHOLD:
        return NO_ACCESS_RESULT
    if numeric["access_lcb"] < ACCESS_THRESHOLD <= numeric["access_ucb"]:
        return UNDERPOWERED_RESULT
    if (
        numeric["fixed_access_lcb"] >= ACCESS_THRESHOLD
        and numeric["g_svc_ucb"] <= SERVICE_GAIN_MARGIN
        and numeric["g_rejoin_ucb"] <= REJOIN_GAIN_MARGIN
    ):
        return MASK_SUFFICIENT_RESULT
    if (
        numeric["open_access_lcb"] >= ACCESS_THRESHOLD
        and numeric["g_svc_lcb"] > SERVICE_GAIN_MARGIN
        and numeric["g_rejoin_lcb"] > REJOIN_GAIN_MARGIN
        and numeric["g_ordinary_lcb"] >= ORDINARY_NONINFERIORITY_MARGIN
    ):
        return DYNAMIC_SUPPORTED_RESULT
    return MIXED_RESULT


def _arrays_from_rows(
    rows: Sequence[Mapping[str, Any]], config: RunConfig
) -> dict[str, dict[str, np.ndarray]]:
    shape = (config.replicates, len(STRATA), config.evaluation_episodes)
    values = {
        subject: {
            "J_event": np.full(shape, np.nan),
            "J_rejoin": np.full(shape, np.nan),
            "Q_ordinary": np.full(shape, np.nan),
        }
        for subject in SUBJECT_NAMES
    }
    stratum_index = {value: index for index, value in enumerate(STRATA)}
    for row in rows:
        subject = str(row["subject"])
        index = (
            int(row["replicate"]),
            stratum_index[(str(row["cell"]), str(row["action_mode"]))],
            int(row["episode_id"]),
        )
        for metric in ("J_event", "Q_ordinary"):
            if not np.isnan(values[subject][metric][index]):
                raise ValueError("duplicate UAV G1 evaluation row")
            values[subject][metric][index] = float(row[metric])
        rejoin = row["J_rejoin"]
        values[subject]["J_rejoin"][index] = np.nan if rejoin is None else float(rejoin)
    for subject in SUBJECT_NAMES:
        if np.isnan(values[subject]["J_event"]).any() or np.isnan(
            values[subject]["Q_ordinary"]
        ).any():
            raise ValueError("UAV G1 evaluation inventory is incomplete")
    return values


def _interval(draws: np.ndarray, point: float) -> dict[str, float]:
    return {
        "lcb95": float(np.quantile(draws, 0.025)),
        "mean": float(point),
        "ucb95": float(np.quantile(draws, 0.975)),
    }


def source_control_intervals(
    rows: Sequence[Mapping[str, Any]],
    *,
    config: RunConfig,
    resamples: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    shape = (config.replicates, len(STRATA), config.evaluation_episodes)
    arrays = {
        subject: np.full(shape, np.nan, dtype=np.float64)
        for subject in CONTROL_NAMES
    }
    stratum_index = {value: index for index, value in enumerate(STRATA)}
    for row in rows:
        subject = str(row["subject"])
        if subject not in arrays:
            raise ValueError("source-control estimator received a learned subject")
        index = (
            int(row["replicate"]),
            stratum_index[(str(row["cell"]), str(row["action_mode"]))],
            int(row["episode_id"]),
        )
        if not np.isnan(arrays[subject][index]):
            raise ValueError("duplicate source-control evaluation row")
        arrays[subject][index] = float(row["J_event"])
    if any(np.isnan(array).any() for array in arrays.values()):
        raise ValueError("source-control evaluation inventory is incomplete")
    constructive = arrays["constructive"]
    no_reallocation = arrays["no_reallocation"]
    disturbed = np.array(
        [cell != LossCell.NO_DISTURBANCE.value for cell, _mode in STRATA]
    )
    points = {
        "constructive_j_event": float(constructive.mean()),
        "constructive_minus_no_reallocation": float(
            (constructive[:, disturbed] - no_reallocation[:, disturbed]).mean()
        ),
    }
    draws = {
        name: np.empty(resamples, dtype=np.float64) for name in points
    }
    rng = np.random.default_rng(int(seed))
    replicate_count, stratum_count, episode_count = constructive.shape
    strata = np.arange(stratum_count)[None, None, :, None]
    offset = 0
    while offset < resamples:
        batch = min(64, resamples - offset)
        replicate_indices = rng.integers(
            0, replicate_count, size=(batch, replicate_count)
        )
        episode_indices = rng.integers(
            0, episode_count, size=(batch, replicate_count, episode_count)
        )

        def sampled(array: np.ndarray) -> np.ndarray:
            return array[
                replicate_indices[:, :, None, None],
                strata,
                episode_indices[:, :, None, :],
            ]

        constructive_draw = sampled(constructive)
        no_reallocation_draw = sampled(no_reallocation)
        section = slice(offset, offset + batch)
        draws["constructive_j_event"][section] = constructive_draw.mean(
            axis=(1, 2, 3)
        )
        draws["constructive_minus_no_reallocation"][section] = (
            constructive_draw[:, :, disturbed]
            - no_reallocation_draw[:, :, disturbed]
        ).mean(axis=(1, 2, 3))
        offset += batch
    return {
        name: _interval(draws[name], point) for name, point in points.items()
    }


def _source_identification(
    intervals: Mapping[str, Mapping[str, float]],
) -> dict[str, bool]:
    return {
        "source_law_and_pairing_pass": True,
        "constructive_feasibility_pass": intervals["constructive_j_event"]["mean"]
        >= CONSTRUCTIVE_FLOOR,
        "disturbed_load_bearing_pass": intervals[
            "constructive_minus_no_reallocation"
        ]["lcb95"]
        > LOAD_BEARING_MARGIN,
    }


def hierarchical_stratified_intervals(
    values: Mapping[str, Mapping[str, np.ndarray]], *, resamples: int, seed: int
) -> dict[str, dict[str, float]]:
    reference = values[ARM_NAMES[0]]["J_event"]
    if (
        reference.ndim != 3
        or reference.shape[1] != len(STRATA)
        or len(STRATA) != ACCESS_CELL_COUNT * len(ACTION_MODES)
        or ACCESS_CELL_COUNT != 4
    ):
        raise ValueError("hierarchical arrays must be replicate x stratum x episode")
    replicate_count, stratum_count, episode_count = reference.shape
    for subject in SUBJECT_NAMES:
        for metric in ("J_event", "J_rejoin", "Q_ordinary"):
            if values[subject][metric].shape != reference.shape:
                raise ValueError("hierarchical paired arrays do not share shape")
    disturbed = np.array([cell != LossCell.NO_DISTURBANCE.value for cell, _ in STRATA])
    point_access: dict[str, float] = {}
    point_cell_access: dict[str, np.ndarray] = {}
    point_stratum_access: dict[str, np.ndarray] = {}
    for arm in ARM_NAMES:
        j = values[arm]["J_event"]
        q = values[arm]["Q_ordinary"]
        stratum_j = j.mean(axis=(0, 2))
        stratum_q = q.mean(axis=(0, 2))
        cell_j = j.reshape(
            replicate_count, ACCESS_CELL_COUNT, len(ACTION_MODES), episode_count
        ).mean(axis=(0, 2, 3))
        cell_q = q.reshape(
            replicate_count, ACCESS_CELL_COUNT, len(ACTION_MODES), episode_count
        ).mean(axis=(0, 2, 3))
        point_stratum_access[arm] = np.minimum(
            stratum_j / EVENT_ACCESS_FLOOR,
            stratum_q / ORDINARY_ACCESS_FLOOR,
        )
        point_cell_access[arm] = np.minimum(
            cell_j / EVENT_ACCESS_FLOOR,
            cell_q / ORDINARY_ACCESS_FLOOR,
        )
        point_access[arm] = float(point_cell_access[arm].min())
    points = {
        "fixed_access": point_access[FIXED_MASK_REC],
        "open_access": point_access[PREFIX_NORMALIZED_OPEN_ROSTER],
        "max_access": max(point_access.values()),
        "g_svc": float(
            (values[PREFIX_NORMALIZED_OPEN_ROSTER]["J_event"] - values[FIXED_MASK_REC]["J_event"]).mean()
        ),
        "g_rejoin": float(
            np.nanmean(
                values[PREFIX_NORMALIZED_OPEN_ROSTER]["J_rejoin"][:, disturbed]
                - values[FIXED_MASK_REC]["J_rejoin"][:, disturbed]
            )
        ),
        "g_ordinary": float(
            (values[PREFIX_NORMALIZED_OPEN_ROSTER]["Q_ordinary"] - values[FIXED_MASK_REC]["Q_ordinary"]).mean()
        ),
        "constructive_j_event": float(values["constructive"]["J_event"].mean()),
        "constructive_minus_no_reallocation": float(
            (
                values["constructive"]["J_event"][:, disturbed]
                - values["no_reallocation"]["J_event"][:, disturbed]
            ).mean()
        ),
    }
    arm_prefix = {
        FIXED_MASK_REC: "fixed",
        PREFIX_NORMALIZED_OPEN_ROSTER: "open",
    }
    for arm in ARM_NAMES:
        prefix = arm_prefix[arm]
        for cell_index, cell in enumerate(EVALUATION_CELLS):
            points[f"{prefix}_access_cell:{cell.value}"] = float(
                point_cell_access[arm][cell_index]
            )
        for stratum_index, (cell, mode) in enumerate(STRATA):
            points[f"{prefix}_access_stratum:{cell}:{mode}"] = float(
                point_stratum_access[arm][stratum_index]
            )
    draws = {name: np.empty(resamples, dtype=np.float64) for name in points}
    rng = np.random.default_rng(int(seed))
    offset = 0
    strata = np.arange(stratum_count)[None, None, :, None]
    while offset < resamples:
        batch = min(64, resamples - offset)
        replicate_indices = rng.integers(
            0, replicate_count, size=(batch, replicate_count)
        )
        episode_indices = rng.integers(
            0, episode_count, size=(batch, replicate_count, episode_count)
        )

        def sampled(subject: str, metric: str) -> np.ndarray:
            array = values[subject][metric]
            return array[
                replicate_indices[:, :, None, None],
                strata,
                episode_indices[:, :, None, :],
            ]

        fixed_j = sampled(FIXED_MASK_REC, "J_event")
        fixed_q = sampled(FIXED_MASK_REC, "Q_ordinary")
        open_j = sampled(PREFIX_NORMALIZED_OPEN_ROSTER, "J_event")
        open_q = sampled(PREFIX_NORMALIZED_OPEN_ROSTER, "Q_ordinary")
        fixed_stratum_access = np.minimum(
            fixed_j.mean(axis=(1, 3)) / EVENT_ACCESS_FLOOR,
            fixed_q.mean(axis=(1, 3)) / ORDINARY_ACCESS_FLOOR,
        )
        open_stratum_access = np.minimum(
            open_j.mean(axis=(1, 3)) / EVENT_ACCESS_FLOOR,
            open_q.mean(axis=(1, 3)) / ORDINARY_ACCESS_FLOOR,
        )
        fixed_cell_access = np.minimum(
            fixed_j.reshape(
                batch,
                replicate_count,
                ACCESS_CELL_COUNT,
                len(ACTION_MODES),
                episode_count,
            ).mean(axis=(1, 3, 4))
            / EVENT_ACCESS_FLOOR,
            fixed_q.reshape(
                batch,
                replicate_count,
                ACCESS_CELL_COUNT,
                len(ACTION_MODES),
                episode_count,
            ).mean(axis=(1, 3, 4))
            / ORDINARY_ACCESS_FLOOR,
        )
        open_cell_access = np.minimum(
            open_j.reshape(
                batch,
                replicate_count,
                ACCESS_CELL_COUNT,
                len(ACTION_MODES),
                episode_count,
            ).mean(axis=(1, 3, 4))
            / EVENT_ACCESS_FLOOR,
            open_q.reshape(
                batch,
                replicate_count,
                ACCESS_CELL_COUNT,
                len(ACTION_MODES),
                episode_count,
            ).mean(axis=(1, 3, 4))
            / ORDINARY_ACCESS_FLOOR,
        )
        fixed_access = fixed_cell_access.min(axis=1)
        open_access = open_cell_access.min(axis=1)
        section = slice(offset, offset + batch)
        draws["fixed_access"][section] = fixed_access
        draws["open_access"][section] = open_access
        draws["max_access"][section] = np.maximum(fixed_access, open_access)
        for arm, cell_accesses, stratum_accesses in (
            (FIXED_MASK_REC, fixed_cell_access, fixed_stratum_access),
            (PREFIX_NORMALIZED_OPEN_ROSTER, open_cell_access, open_stratum_access),
        ):
            prefix = arm_prefix[arm]
            for cell_index, cell in enumerate(EVALUATION_CELLS):
                draws[f"{prefix}_access_cell:{cell.value}"][section] = cell_accesses[
                    :, cell_index
                ]
            for stratum_index, (cell, mode) in enumerate(STRATA):
                draws[f"{prefix}_access_stratum:{cell}:{mode}"][section] = (
                    stratum_accesses[:, stratum_index]
                )
        draws["g_svc"][section] = (open_j - fixed_j).mean(axis=(1, 2, 3))
        draws["g_ordinary"][section] = (open_q - fixed_q).mean(axis=(1, 2, 3))
        draws["g_rejoin"][section] = np.nanmean(
            sampled(PREFIX_NORMALIZED_OPEN_ROSTER, "J_rejoin")[:, :, disturbed]
            - sampled(FIXED_MASK_REC, "J_rejoin")[:, :, disturbed],
            axis=(1, 2, 3),
        )
        constructive = sampled("constructive", "J_event")
        no_reallocation = sampled("no_reallocation", "J_event")
        draws["constructive_j_event"][section] = constructive.mean(axis=(1, 2, 3))
        draws["constructive_minus_no_reallocation"][section] = (
            constructive[:, :, disturbed] - no_reallocation[:, :, disturbed]
        ).mean(axis=(1, 2, 3))
        offset += batch
    return {name: _interval(draws[name], point) for name, point in points.items()}


def _operational_errors(manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    grouped: dict[int, list[Mapping[str, Any]]] = {}
    for row in manifest.get("training_results", []):
        grouped.setdefault(int(row["replicate"]), []).append(row)
        maximum = row.get("maximum_errors", {})
        if not row.get("finite_updates"):
            errors.append(f"{row.get('arm')} replicate {row.get('replicate')} nonfinite update")
        if float(row.get("maximum_gradient_norm", 0.0)) <= 0.0:
            errors.append(f"{row.get('arm')} replicate {row.get('replicate')} no gradient")
        for name in (
            "logp_max_error", "joint_logp_max_error", "value_max_error",
            "hidden_max_error", "prefix_max_error",
        ):
            if float(maximum.get(name, float("inf"))) > REPLAY_TOLERANCE:
                errors.append(f"{row.get('arm')} replicate {row.get('replicate')} {name}")
        for name in (
            "inactive_logp_max_abs", "inactive_action_max_abs",
            "inactive_hidden_change_max_abs",
        ):
            if float(maximum.get(name, float("inf"))) != 0.0:
                errors.append(f"{row.get('arm')} replicate {row.get('replicate')} {name}")
        if float(row.get("checkpoint_roundtrip_max_error", float("inf"))) != 0.0:
            errors.append(f"{row.get('arm')} replicate {row.get('replicate')} checkpoint")
        if float(row.get("paired_initialization_max_error", float("inf"))) != 0.0:
            errors.append(f"replicate {row.get('replicate')} initialization mismatch")
    for replicate, rows in grouped.items():
        if len(rows) != len(ARM_NAMES):
            errors.append(f"replicate {replicate} arm inventory")
        elif len({int(row["parameter_count"]) for row in rows}) != 1:
            errors.append(f"replicate {replicate} parameter mismatch")
        elif len({int(row["environment_transitions"]) for row in rows}) != 1:
            errors.append(f"replicate {replicate} exposure mismatch")
    return errors


def _analysis_payload(
    manifest: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    config = RunConfig(**manifest["config"])
    values = _arrays_from_rows(rows, config)
    intervals = hierarchical_stratified_intervals(
        values,
        resamples=config.bootstrap_resamples,
        seed=int(manifest["seed_registry"]["bootstrap"]),
    )
    operational_errors = _operational_errors(manifest)
    operational_valid = not operational_errors
    source_identification = _source_identification(intervals)
    source_identifiable = all(source_identification.values())
    predicate_inputs = {
        "operational_valid": operational_valid,
        "source_identifiable": source_identifiable,
        "access_lcb": intervals["max_access"]["lcb95"],
        "access_ucb": intervals["max_access"]["ucb95"],
        "fixed_access_lcb": intervals["fixed_access"]["lcb95"],
        "open_access_lcb": intervals["open_access"]["lcb95"],
        "g_svc_lcb": intervals["g_svc"]["lcb95"],
        "g_svc_ucb": intervals["g_svc"]["ucb95"],
        "g_rejoin_lcb": intervals["g_rejoin"]["lcb95"],
        "g_rejoin_ucb": intervals["g_rejoin"]["ucb95"],
        "g_ordinary_lcb": intervals["g_ordinary"]["lcb95"],
        "g_ordinary_ucb": intervals["g_ordinary"]["ucb95"],
    }
    result = select_result_branch(predicate_inputs)
    if not manifest["formal"] and operational_valid:
        result = NONFORMAL_RESULT
    return {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": manifest["formal"],
        "status": "COMPLETE" if operational_valid else "INVALID",
        "operational_valid": operational_valid,
        "operational_errors": operational_errors,
        "source_identifiable": source_identifiable,
        "source_identification": source_identification,
        "metrics": intervals,
        "access_contract": {
            "cells": [cell.value for cell in EVALUATION_CELLS],
            "action_modes_averaged_within_cell": list(ACTION_MODES),
            "worst_over_cell_count": ACCESS_CELL_COUNT,
        },
        "predicate_inputs": predicate_inputs,
        "result": result,
        "thresholds": {
            "access": ACCESS_THRESHOLD,
            "constructive": CONSTRUCTIVE_FLOOR,
            "load_bearing": LOAD_BEARING_MARGIN,
            "service_gain": SERVICE_GAIN_MARGIN,
            "rejoin_gain": REJOIN_GAIN_MARGIN,
            "ordinary_noninferiority": ORDINARY_NONINFERIORITY_MARGIN,
        },
        "config": manifest["config"],
    }


def _source_skipped_analysis_payload(
    manifest: Mapping[str, Any], screen: Mapping[str, Any]
) -> dict[str, Any]:
    operational_errors = _operational_errors(manifest)
    operational_valid = not operational_errors
    source_identifiable = bool(screen["source_identifiable"])
    predicate_inputs = {
        "operational_valid": operational_valid,
        "source_identifiable": source_identifiable,
        "access_lcb": 0.0,
        "access_ucb": 0.0,
        "fixed_access_lcb": 0.0,
        "open_access_lcb": 0.0,
        "g_svc_lcb": 0.0,
        "g_svc_ucb": 0.0,
        "g_rejoin_lcb": 0.0,
        "g_rejoin_ucb": 0.0,
        "g_ordinary_lcb": 0.0,
        "g_ordinary_ucb": 0.0,
    }
    return {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": True,
        "status": "COMPLETE" if operational_valid else "INVALID",
        "operational_valid": operational_valid,
        "operational_errors": operational_errors,
        "source_identifiable": source_identifiable,
        "source_identification": screen["source_identification"],
        "metrics": screen["metrics"],
        "learned_gates_evaluated": False,
        "predicate_inputs": predicate_inputs,
        "result": select_result_branch(predicate_inputs),
        "thresholds": {
            "access": ACCESS_THRESHOLD,
            "constructive": CONSTRUCTIVE_FLOOR,
            "load_bearing": LOAD_BEARING_MARGIN,
            "service_gain": SERVICE_GAIN_MARGIN,
            "rejoin_gain": REJOIN_GAIN_MARGIN,
            "ordinary_noninferiority": ORDINARY_NONINFERIORITY_MARGIN,
        },
        "config": manifest["config"],
    }


def analyze_run(root: Path) -> Path:
    root = Path(root)
    manifest = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    if not manifest.get("formal"):
        rows = _validate_exercise_evaluation(root, manifest, evaluation)
        payload = _exercise_analysis_payload(manifest, rows)
        _write_json(root / "analysis_result.json", payload)
        return root / "analysis_result.json"
    _validate_evaluation_artifacts(root, manifest, evaluation)
    if manifest.get("status") == TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE:
        config = RunConfig(**manifest["config"])
        launch = _read_json(root / "launch_identity.json")
        screen = _validate_source_screen(root, launch=launch, config=config)
        payload = _source_skipped_analysis_payload(manifest, screen)
        _write_json(root / "analysis_result.json", payload)
        return root / "analysis_result.json"
    rows = _read_jsonl(root / evaluation["evaluation_rows_reference"])
    payload = _analysis_payload(manifest, rows)
    _write_json(root / "analysis_result.json", payload)
    return root / "analysis_result.json"


def _validate_evaluation_row(
    row: Mapping[str, Any], *, manifest: Mapping[str, Any], config: RunConfig,
    registered: Mapping[tuple[int, str], str],
) -> None:
    exact = {
        "schema": EVALUATION_ROW_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": manifest["formal"],
    }
    for name, expected in exact.items():
        if row.get(name) != expected or type(row.get(name)) is not type(expected):
            raise ValueError(f"evaluation row {name} mismatch")
    if row.get("subject") not in SUBJECT_NAMES:
        raise ValueError("evaluation row subject mismatch")
    if type(row.get("replicate")) is not int or not 0 <= row["replicate"] < config.replicates:
        raise ValueError("evaluation row replicate mismatch")
    if row.get("cell") not in {cell.value for cell in EVALUATION_CELLS}:
        raise ValueError("evaluation row cell mismatch")
    if row.get("action_mode") not in ACTION_MODES:
        raise ValueError("evaluation row action mode mismatch")
    subject = str(row["subject"])
    expected_checkpoint = (
        registered[(int(row["replicate"]), subject)] if subject in ARM_NAMES else None
    )
    if row.get("checkpoint_reference") != expected_checkpoint:
        raise ValueError("evaluation row checkpoint reference mismatch")
    episode_id = row.get("episode_id")
    if type(episode_id) is not int or not 0 <= episode_id < config.evaluation_episodes:
        raise ValueError("evaluation row episode mismatch")
    seeds = _replicate_seeds(int(row["replicate"]))
    ledger = make_uav_loss_ledger(
        LossCell(row["cell"]), episode_id, ledger_seed=seeds["evaluation_ledger"]
    )
    if row.get("ledger_id") != ledger.ledger_id or row.get("intervals") != _ledger_payload(ledger)["intervals"]:
        raise ValueError("evaluation row ledger provenance mismatch")
    for name in ("J_event", "Q_ordinary"):
        value = _finite_number(name, row.get(name))
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"evaluation row {name} outside support")
    rejoin = row.get("J_rejoin")
    if ledger.cell is LossCell.NO_DISTURBANCE:
        if rejoin is not None or float(row["J_event"]) != 1.0:
            raise ValueError("NO_DISTURBANCE metric identity mismatch")
    elif not 0.0 <= _finite_number("J_rejoin", rejoin) <= 1.0:
        raise ValueError("evaluation row J_rejoin outside support")


def _validate_evaluation_artifacts(
    root: Path, manifest: Mapping[str, Any], evaluation: Mapping[str, Any]
) -> list[dict[str, Any]]:
    if not _evaluation_terminal_complete(root):
        raise ValueError("evaluation terminal completion marker is missing")
    if evaluation.get("schema") != EVALUATION_SCHEMA or evaluation.get("status") != "EVALUATION_COMPLETE":
        raise ValueError("evaluation manifest schema/status mismatch")
    for name in ("source_family", "source_commit", "formal", "config"):
        expected = SOURCE_FAMILY if name == "source_family" else manifest[name]
        if evaluation.get(name) != expected:
            raise ValueError(f"train/evaluation {name} mismatch")
    runtime = evaluation.get("runtime", {})
    if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1:
        raise ValueError("evaluation runtime is not CPU one-thread")
    registered = _registered_checkpoints(root, manifest)
    skipped = manifest.get("status") == TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE
    if skipped:
        if evaluation.get("training_status") != TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE:
            raise ValueError("control-only evaluation training state mismatch")
    elif "training_status" in evaluation:
        raise ValueError("learned evaluation unexpectedly carries a skipped state")
    expected_identity = _evaluation_identity(manifest, registered, exercise=False)
    if evaluation.get("evaluation_identity") != expected_identity:
        raise ValueError("evaluation launch identity mismatch")
    if evaluation.get("checkpoint_references") != _evaluation_checkpoint_inventory(registered, manifest):
        raise ValueError("evaluation checkpoint inventory mismatch")
    row_path = _confined_reference(
        root,
        evaluation.get("evaluation_rows_reference"),
        expected="evaluation_rows.jsonl",
    )
    rows = _read_jsonl(row_path)
    config = RunConfig(**manifest["config"])
    expected_subjects = CONTROL_NAMES if skipped else SUBJECT_NAMES
    expected = (
        config.replicates
        * len(expected_subjects)
        * len(EVALUATION_CELLS)
        * len(ACTION_MODES)
        * config.evaluation_episodes
    )
    if len(rows) != expected or evaluation.get("evaluation_row_count") != expected:
        raise ValueError("evaluation row count mismatch")
    assembled = _assemble_committed_evaluation_rows(
        root,
        config=config,
        exercise=False,
        identity=expected_identity,
        registered=registered,
        control_only=skipped,
        control_identity=_source_screen_identity(manifest, config=config),
    )
    if rows != assembled:
        raise ValueError("evaluation terminal rows differ from committed chunk assembly")
    paired: dict[tuple[int, str, str, int], dict[str, str]] = {}
    for row in rows:
        _validate_evaluation_row(
            row, manifest=manifest, config=config, registered=registered
        )
        key = (
            int(row["replicate"]), str(row["cell"]), str(row["action_mode"]),
            int(row["episode_id"]),
        )
        subjects = paired.setdefault(key, {})
        subject = str(row["subject"])
        if subject in subjects:
            raise ValueError("paired key contains a duplicate subject")
        subjects[subject] = str(row["ledger_id"])
    if any(
        set(subjects) != set(expected_subjects) or len(set(subjects.values())) != 1
        for subjects in paired.values()
    ):
        raise ValueError("paired subjects do not share exact episode ledgers")
    return rows


def _validate_exercise_evaluation(
    root: Path, manifest: Mapping[str, Any], evaluation: Mapping[str, Any]
) -> list[dict[str, Any]]:
    if not _evaluation_terminal_complete(root):
        raise ValueError("exercise terminal completion marker is missing")
    if manifest.get("formal") is not False or evaluation.get("exercise") is not True:
        raise ValueError("exercise evaluation identity mismatch")
    if (
        evaluation.get("schema") != EVALUATION_SCHEMA
        or evaluation.get("status") != "EVALUATION_COMPLETE"
        or evaluation.get("source_family") != SOURCE_FAMILY
        or evaluation.get("source_commit") != manifest.get("source_commit")
        or evaluation.get("formal") is not False
        or evaluation.get("config") != manifest.get("config")
    ):
        raise ValueError("exercise evaluation manifest mismatch")
    runtime = evaluation.get("runtime", {})
    if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1:
        raise ValueError("exercise evaluation runtime is not CPU one-thread")
    registered = _registered_checkpoints(root, manifest)
    expected_identity = _evaluation_identity(manifest, registered, exercise=True)
    if evaluation.get("evaluation_identity") != expected_identity:
        raise ValueError("exercise launch identity mismatch")
    if evaluation.get("checkpoint_references") != _evaluation_checkpoint_inventory(registered, manifest):
        raise ValueError("exercise checkpoint inventory mismatch")
    row_path = _confined_reference(
        root,
        evaluation.get("evaluation_rows_reference"),
        expected="evaluation_rows.jsonl",
    )
    rows = _read_jsonl(row_path)
    config = RunConfig(**manifest["config"])
    expected = config.replicates * len(SUBJECT_NAMES)
    if len(rows) != expected or evaluation.get("evaluation_row_count") != expected:
        raise ValueError("exercise evaluation row count mismatch")
    assembled = _assemble_committed_evaluation_rows(
        root,
        config=config,
        exercise=True,
        identity=expected_identity,
        registered=registered,
    )
    if rows != assembled:
        raise ValueError("exercise terminal rows differ from committed chunk assembly")
    inventory: dict[int, set[str]] = {}
    for row in rows:
        for name, expected_value in (
            ("schema", EVALUATION_ROW_SCHEMA),
            ("source_family", SOURCE_FAMILY),
            ("source_commit", manifest["source_commit"]),
            ("formal", False),
            ("exercise", True),
            ("cell", LossCell.NO_DISTURBANCE.value),
            ("action_mode", "deterministic"),
            ("episode_id", 0),
            ("observed_steps", config.horizon),
        ):
            if row.get(name) != expected_value or type(row.get(name)) is not type(expected_value):
                raise ValueError(f"exercise row {name} mismatch")
        replicate = row.get("replicate")
        subject = row.get("subject")
        if type(replicate) is not int or not 0 <= replicate < config.replicates:
            raise ValueError("exercise row replicate mismatch")
        if subject not in SUBJECT_NAMES:
            raise ValueError("exercise row subject mismatch")
        expected_checkpoint = (
            registered[(replicate, str(subject))] if subject in ARM_NAMES else None
        )
        if row.get("checkpoint_reference") != expected_checkpoint:
            raise ValueError("exercise row checkpoint reference mismatch")
        inventory.setdefault(replicate, set()).add(str(subject))
        seeds = _replicate_seeds(replicate)
        ledger = make_uav_loss_ledger(
            LossCell.NO_DISTURBANCE, 0, ledger_seed=seeds["evaluation_ledger"]
        )
        if row.get("ledger_id") != ledger.ledger_id or row.get("intervals") != []:
            raise ValueError("exercise ledger provenance mismatch")
        qos = _finite_number("mean_qos", row.get("mean_qos"))
        if not 0.0 <= qos <= 1.0:
            raise ValueError("exercise mean QoS outside support")
    if any(subjects != set(SUBJECT_NAMES) for subjects in inventory.values()):
        raise ValueError("exercise subject inventory mismatch")
    return rows


def _exercise_analysis_payload(
    manifest: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    operational_errors = _operational_errors(manifest)
    operational_valid = not operational_errors
    means = {
        subject: float(np.mean([row["mean_qos"] for row in rows if row["subject"] == subject]))
        for subject in SUBJECT_NAMES
    }
    return {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": False,
        "exercise": True,
        "status": "COMPLETE" if operational_valid else "INVALID",
        "operational_valid": operational_valid,
        "operational_errors": operational_errors,
        "source_identifiable": False,
        "source_identification": "not_evaluated_in_nonformal_smoke",
        "metrics": {"descriptive_mean_qos": means, "observed_steps": manifest["config"]["horizon"]},
        "predicate_inputs": None,
        "result": NONFORMAL_RESULT if operational_valid else INVALID_RESULT,
        "config": manifest["config"],
    }


def validate_run_artifacts(root: Path, *, require_formal: bool) -> None:
    root = Path(root)
    manifest = _read_json(root / "train_manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    analysis = _read_json(root / "analysis_result.json")
    status = manifest.get("status")
    if (
        manifest.get("schema") != RUN_SCHEMA
        or status not in {TRAIN_COMPLETE, TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE}
    ):
        raise ValueError("training manifest schema/status mismatch")
    if manifest.get("source_family") != SOURCE_FAMILY:
        raise ValueError("training source family mismatch")
    formal = manifest.get("formal")
    if type(formal) is not bool:
        raise ValueError("formal flag must be an exact boolean")
    if require_formal and formal is not True:
        raise ValueError("formal validation rejects nonformal/exercise artifacts")
    config = RunConfig(**manifest["config"])
    _validate_launch(
        formal=formal,
        authorization_token=manifest.get("authorization_token"),
        config=config,
    )
    _validate_source_commit(manifest.get("source_commit"), formal=formal)
    launch = _read_json(root / "launch_identity.json")
    expected_launch = _launch_identity(
        source_commit=str(manifest["source_commit"]),
        formal=formal,
        authorization_token=manifest.get("authorization_token"),
        config=config,
    )
    if launch != expected_launch or manifest.get("runtime") != launch.get("runtime"):
        raise ValueError("training launch/runtime identity mismatch")
    if not _terminal_training_complete(root):
        raise ValueError("training terminal completion marker is missing")
    if formal and config != FORMAL_CONFIG:
        raise ValueError("formal config mismatch")
    if manifest.get("seed_registry") != asdict(SeedRegistry()):
        raise ValueError("seed registry mismatch")
    runtime = manifest.get("runtime", {})
    if runtime.get("backend") != "cpu" or runtime.get("torch_threads") != 1:
        raise ValueError("training runtime is not CPU one-thread")
    registered = _registered_checkpoints(root, manifest)
    screen: dict[str, Any] | None = None
    if formal:
        screen = _validate_source_screen(root, launch=launch, config=config)
        if manifest.get("source_screen") != _source_screen_binding(root, screen):
            raise ValueError("training manifest source-screen binding mismatch")
        if (status == TRAIN_COMPLETE) is not bool(screen["source_identifiable"]):
            raise ValueError("training terminal state conflicts with source screen")
    elif status != TRAIN_COMPLETE or "source_screen" in manifest:
        raise ValueError("nonformal training terminal state mismatch")
    for row in manifest["training_results"]:
        expected_exposure = config.updates * config.num_envs * config.horizon
        if (
            row.get("updates") != config.updates
            or row.get("optimizer_steps") != config.updates * config.ppo_passes
            or row.get("episodes") != config.updates * config.num_envs
            or row.get("environment_transitions") != expected_exposure
        ):
            raise ValueError("learned-arm training exposure mismatch")
        pair = (int(row["replicate"]), str(row["arm"]))
        checkpoint = _confined_reference(
            root, row["checkpoint"], expected=registered[pair]
        )
        bundle = torch.load(checkpoint, map_location="cpu", weights_only=False)
        seeds = _replicate_seeds(int(row["replicate"]))
        if (
            bundle.get("routing_mode") != row["arm"]
            or bundle.get("completed_updates") != config.updates
            or bundle.get("next_episode_id") != config.updates * config.num_envs
            or bundle.get("seed_contract") != seeds
        ):
            raise ValueError("final checkpoint provenance/exposure mismatch")
    if formal:
        rows = _validate_evaluation_artifacts(root, manifest, evaluation)
        expected_analysis = (
            _source_skipped_analysis_payload(manifest, screen)
            if status == TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE
            else _analysis_payload(manifest, rows)
        )
    else:
        rows = _validate_exercise_evaluation(root, manifest, evaluation)
        expected_analysis = _exercise_analysis_payload(manifest, rows)
    if analysis != expected_analysis:
        raise ValueError("analysis does not reproduce the frozen paired estimator")
    residue = [
        path for path in root.rglob("*")
        if path.name.endswith(".tmp") or "latest" in path.name.lower()
    ]
    if residue:
        raise ValueError("run retains temporary/latest residue")


def validate_formal_result(root: Path) -> None:
    validate_run_artifacts(root, require_formal=True)


def exercise(root: Path, *, source_commit: str = "NONFORMAL_WORKTREE") -> Path:
    train_run(
        root,
        source_commit=source_commit,
        formal=False,
        authorization_token=None,
        config=EXERCISE_CONFIG,
    )
    evaluate_run(root)
    result = analyze_run(root)
    validate_run_artifacts(root, require_formal=False)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    train = subparsers.add_parser("train")
    train.add_argument("--run-root", type=Path, required=True)
    train.add_argument("--source-commit", required=True)
    train.add_argument("--formal", action="store_true")
    train.add_argument("--authorization-token")
    for command in ("evaluate", "analyze", "validate-formal"):
        item = subparsers.add_parser(command)
        item.add_argument("--run-root", type=Path, required=True)
    exercise_parser = subparsers.add_parser("exercise")
    exercise_parser.add_argument("--run-root", type=Path, required=True)
    exercise_parser.add_argument("--source-commit", default="NONFORMAL_WORKTREE")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "train":
        result = train_run(
            args.run_root,
            source_commit=args.source_commit,
            formal=bool(args.formal),
            authorization_token=args.authorization_token,
        )
    elif args.command == "evaluate":
        result = evaluate_run(args.run_root)
    elif args.command == "analyze":
        result = analyze_run(args.run_root)
    elif args.command == "validate-formal":
        validate_formal_result(args.run_root)
        result = args.run_root / "analysis_result.json"
    else:
        result = exercise(args.run_root, source_commit=args.source_commit)
    print(result)


if __name__ == "__main__":
    main()
