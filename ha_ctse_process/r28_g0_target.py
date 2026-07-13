"""R28-G0 offline action-process target calibration.

This module consumes completed R27-G2 reset shards and registered frozen R25
checkpoints.  It performs no environment replay and no policy update.
"""

from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import torch
import torch.nn.functional as F

from ha_ctse_process.r27_g2_analysis import late_action_features
from ha_ctse_process.r27_g2_collector import (
    ACTION_DIM,
    N_AGENTS,
    N_SKILLS,
    R27G2ResetArtifact,
)
from ha_ctse_process.r27_g2_runtime import R27G2ContractError


EXPERIMENT_ID = "EXP-20260713-r28-g0-action-process-target-calibration"
DESIGN_PATH = "docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md"

REGISTERED_CHECKPOINTS: dict[str, dict[str, Any]] = {
    "arm0_update25": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt",
        "update": 25,
        "total_steps": 800000,
    },
    "arm0_update30": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt",
        "update": 30,
        "total_steps": 960000,
    },
    "arm0_final": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt",
        "update": 32,
        "total_steps": 1000000,
    },
}
CHECKPOINT_IDS = tuple(REGISTERED_CHECKPOINTS)
DURATION_STEPS = (10, 20, 30, 40)
DURATION_SLICES = {
    10: slice(0, 10),
    20: slice(10, 20),
    30: slice(20, 30),
    40: slice(30, 40),
}
FIT_SEED = 28021
SHAM_SEED = 28022
BOOTSTRAP_SEED = 28023
BOOTSTRAP_REPS = 10_000
LR = 3e-3
WEIGHT_DECAY = 1e-4
MAX_STEPS = 1_000
VALIDATE_EVERY = 5
PATIENCE_VALIDATIONS = 20
MIN_DELTA = 1e-4
STD_FLOOR = 1e-6
CONTEXT_WIDTH = 269
STREAM_WIDTH = 12
HEAD_INPUT_WIDTH = 281
SCIENTIFIC_CONTRACT: dict[str, Any] = {
    "experiment_id": EXPERIMENT_ID,
    "checkpoint_ids": list(CHECKPOINT_IDS),
    "checkpoint_slots": copy.deepcopy(REGISTERED_CHECKPOINTS),
    "r27_shards": "exactly 192 decision-grade r27-g2-reset-v2 shards",
    "device": "cuda",
    "zero_environment_steps": True,
    "zero_policy_updates": True,
    "duration_steps": list(DURATION_STEPS),
    "splits": {"test": [0, 11], "validation": [12, 23], "train": [24, 63]},
    "fit_seed": FIT_SEED,
    "sham_seed": SHAM_SEED,
    "bootstrap_seed": BOOTSTRAP_SEED,
    "bootstrap_reps": BOOTSTRAP_REPS,
    "head_input_width": HEAD_INPUT_WIDTH,
    "optimizer": {
        "name": "Adam",
        "lr": LR,
        "weight_decay": WEIGHT_DECAY,
        "max_steps": MAX_STEPS,
        "validate_every": VALIDATE_EVERY,
        "patience_validations": PATIENCE_VALIDATIONS,
        "min_delta": MIN_DELTA,
        "standard_deviation_floor": STD_FLOOR,
    },
    "design_path": DESIGN_PATH,
}


class EvidenceError(ValueError):
    """Malformed or non-finite R28-G0 evidence."""


class UnderpoweredEvidenceError(EvidenceError):
    """Well-formed evidence that cannot satisfy registered support floors."""


@dataclass(frozen=True)
class BootstrapInterval:
    estimate: float
    lower: float
    upper: float
    reps: int
    seed: int


@dataclass(frozen=True)
class HeadArtifact:
    name: str
    mean: np.ndarray
    std: np.ndarray
    weight: np.ndarray
    bias: np.ndarray
    temperature: float
    optimizer_steps: int
    validation_evaluations: int


@dataclass(frozen=True)
class HeadScore:
    name: str
    train_accuracy: float
    validation_accuracy: float
    test_accuracy: float
    test_macro_f1: float
    duration_test_accuracy: dict[int, float]
    accuracy_interval: BootstrapInterval
    train_minus_test: float
    optimizer_steps: int
    validation_evaluations: int
    temperature: float
    log_prob_true: np.ndarray
    predictions: np.ndarray


@dataclass(frozen=True)
class CheckpointDataset:
    checkpoint_id: str
    reset_ids: np.ndarray
    agents: np.ndarray
    labels: np.ndarray
    duration_steps: np.ndarray
    duration_ids: np.ndarray
    phase_ids: np.ndarray
    context: np.ndarray
    f_post: np.ndarray
    f_pre: np.ndarray
    pulse_reset_ids: np.ndarray
    pulse_agents: np.ndarray
    pulse_labels: np.ndarray
    pulse_duration_steps: np.ndarray
    pulse_context: np.ndarray
    pulse_f_post: np.ndarray
    pulse_f_pre: np.ndarray


@dataclass(frozen=True)
class CheckpointResult:
    checkpoint_id: str
    status: Literal["PASS", "FAIL", "INVALID", "UNDERPOWERED"]
    classification: str
    reasons: tuple[str, ...]
    support: dict[str, Any]
    q_full: HeadScore | None
    q_context: HeadScore | None
    q_pre: HeadScore | None
    q_full_artifact: HeadArtifact | None
    q_context_artifact: HeadArtifact | None
    q_pre_artifact: HeadArtifact | None
    metrics: dict[str, Any]
    support_envelope: dict[str, Any] | None


def jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return str(value)


def _finite_array(name: str, value: Any, *, ndim: int | None = None) -> np.ndarray:
    array = np.asarray(value)
    if ndim is not None and array.ndim != ndim:
        raise EvidenceError(f"{name} must have {ndim} dimensions, got {array.ndim}")
    if array.size == 0:
        raise EvidenceError(f"{name} must not be empty")
    if not np.issubdtype(array.dtype, np.number):
        raise EvidenceError(f"{name} must be numeric")
    array = np.asarray(array, dtype=np.float64)
    if not np.isfinite(array).all():
        raise EvidenceError(f"{name} contains non-finite values")
    return array


def _labels(name: str, value: Any, shape: tuple[int, ...]) -> np.ndarray:
    raw = np.asarray(value)
    if raw.shape != shape:
        raise EvidenceError(f"{name} shape mismatch: expected {shape}, got {raw.shape}")
    if not np.issubdtype(raw.dtype, np.integer):
        if not np.issubdtype(raw.dtype, np.number) or not np.equal(raw, np.floor(raw)).all():
            raise EvidenceError(f"{name} must contain integer labels")
    labels = np.asarray(raw, dtype=np.int64)
    if np.any((labels < 0) | (labels >= N_SKILLS)):
        raise EvidenceError(f"{name} labels must be in 0..{N_SKILLS - 1}")
    return labels


def _accuracy(truth: np.ndarray, prediction: np.ndarray) -> float:
    truth = np.asarray(truth, dtype=np.int64).reshape(-1)
    prediction = np.asarray(prediction, dtype=np.int64).reshape(-1)
    if truth.shape != prediction.shape or truth.size == 0:
        raise EvidenceError("classification truth/prediction mismatch")
    return float(np.mean(truth == prediction))


def _macro_f1(truth: np.ndarray, prediction: np.ndarray) -> float:
    truth = np.asarray(truth, dtype=np.int64).reshape(-1)
    prediction = np.asarray(prediction, dtype=np.int64).reshape(-1)
    values: list[float] = []
    for label in range(N_SKILLS):
        tp = float(np.sum((truth == label) & (prediction == label)))
        fp = float(np.sum((truth != label) & (prediction == label)))
        fn = float(np.sum((truth == label) & (prediction != label)))
        denom = 2.0 * tp + fp + fn
        values.append(0.0 if denom == 0.0 else 2.0 * tp / denom)
    return float(np.mean(values))


def reset_cluster_interval(
    reset_ids: np.ndarray,
    values: np.ndarray,
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int = BOOTSTRAP_SEED,
) -> BootstrapInterval:
    ids = np.asarray(reset_ids, dtype=np.int64).reshape(-1)
    vals = _finite_array("bootstrap values", values, ndim=1)
    if ids.shape != vals.shape:
        raise EvidenceError("bootstrap reset ids and values must align")
    unique = np.unique(ids)
    if unique.size == 0:
        raise EvidenceError("bootstrap requires at least one reset")
    cluster_values = np.asarray([vals[ids == reset_id].mean() for reset_id in unique])
    rng = np.random.default_rng(int(seed))
    draws = rng.integers(0, cluster_values.size, size=(int(reps), cluster_values.size))
    samples = cluster_values[draws].mean(axis=1)
    return BootstrapInterval(
        estimate=float(cluster_values.mean()),
        lower=float(np.quantile(samples, 0.025)),
        upper=float(np.quantile(samples, 0.975)),
        reps=int(reps),
        seed=int(seed),
    )


def _split_masks(reset_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ids = np.asarray(reset_ids, dtype=np.int64)
    return ids >= 24, (ids >= 12) & (ids <= 23), ids <= 11


def phase_id_for_prefix(prefix_steps: int) -> int:
    return min(int(prefix_steps) // 100, 2)


def one_hot(indices: np.ndarray, width: int) -> np.ndarray:
    idx = np.asarray(indices, dtype=np.int64).reshape(-1)
    if np.any((idx < 0) | (idx >= int(width))):
        raise EvidenceError("one-hot index outside registered range")
    out = np.zeros((idx.size, int(width)), dtype=np.float32)
    out[np.arange(idx.size), idx] = 1.0
    return out


def load_actor_base(checkpoint_path: str | Path, device: str | torch.device) -> torch.nn.Sequential:
    checkpoint = torch.load(Path(checkpoint_path), map_location="cpu")
    low_state = checkpoint.get("low")
    if not isinstance(low_state, dict):
        raise EvidenceError("checkpoint is missing low actor state")
    required = {
        "actor_base.mlp.0.weight": (256, None),
        "actor_base.mlp.0.bias": (256,),
        "actor_base.mlp.2.weight": (256, 256),
        "actor_base.mlp.2.bias": (256,),
    }
    missing = [key for key in required if key not in low_state]
    if missing:
        raise EvidenceError(f"checkpoint missing actor_base keys: {missing}")
    first_weight = low_state["actor_base.mlp.0.weight"]
    if first_weight.ndim != 2 or first_weight.shape[0] != 256:
        raise EvidenceError("actor_base first linear shape mismatch")
    obs_dim = int(first_weight.shape[1])
    model = torch.nn.Sequential(
        torch.nn.Linear(obs_dim, 256),
        torch.nn.ReLU(),
        torch.nn.Linear(256, 256),
        torch.nn.ReLU(),
    ).to(torch.device(device))
    state = {
        "0.weight": low_state["actor_base.mlp.0.weight"],
        "0.bias": low_state["actor_base.mlp.0.bias"],
        "2.weight": low_state["actor_base.mlp.2.weight"],
        "2.bias": low_state["actor_base.mlp.2.bias"],
    }
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _branch_index(
    artifact: R27G2ResetArtifact,
    *,
    kind: str,
    focal_agent: int,
    target_skill: int,
) -> int:
    mask = (
        (artifact.branch_kind == str(kind))
        & (artifact.branch_focal_agent == int(focal_agent))
        & (artifact.branch_target_skill == int(target_skill))
    )
    matches = np.flatnonzero(mask)
    if matches.size != 1:
        raise EvidenceError(
            f"branch lookup failed kind={kind} agent={focal_agent} target={target_skill}"
        )
    return int(matches[0])


def _status_failures(
    manifest: dict[str, Any],
    artifact: R27G2ResetArtifact | None,
    *,
    checkpoint_id: str,
    reset_id: int,
) -> tuple[str, ...]:
    failures: list[str] = []
    status = str(manifest.get("status", ""))
    if status not in {"OK", "EXCLUDED", "INVALID"}:
        failures.append(f"{checkpoint_id}/reset_{reset_id:02d} unknown status {status!r}")
    if manifest.get("checkpoint_id") != checkpoint_id:
        failures.append(f"{checkpoint_id}/reset_{reset_id:02d} checkpoint_id mismatch")
    if int(manifest.get("reset_id", -1)) != int(reset_id):
        failures.append(f"{checkpoint_id}/reset_{reset_id:02d} reset_id mismatch")
    if manifest.get("artifact_schema") not in (None, "r27-g2-reset-v2"):
        failures.append(f"{checkpoint_id}/reset_{reset_id:02d} artifact schema mismatch")
    if status == "OK":
        if artifact is None:
            failures.append(f"{checkpoint_id}/reset_{reset_id:02d} OK without artifact")
        elif not bool(np.all(artifact.branch_completed)):
            failures.append(f"{checkpoint_id}/reset_{reset_id:02d} incomplete branch matrix")
    return tuple(failures)


def read_checkpoint_shards(
    r27_run_root: str | Path,
    checkpoint_id: str,
) -> tuple[list[R27G2ResetArtifact | None], list[dict[str, Any]], tuple[str, ...]]:
    root = Path(r27_run_root) / checkpoint_id / "resets"
    manifests = sorted(root.glob("reset_*/reset_manifest.json"))
    if len(manifests) != 64:
        raise EvidenceError(f"{checkpoint_id} requires exactly 64 reset manifests")
    artifacts: list[R27G2ResetArtifact | None] = []
    manifest_values: list[dict[str, Any]] = []
    failures: list[str] = []
    for expected_reset, manifest_path in enumerate(manifests):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise EvidenceError(f"manifest is not a JSON object: {manifest_path}")
        artifact: R27G2ResetArtifact | None = None
        artifact_name = manifest.get("artifact")
        if artifact_name:
            expected_name = f"reset_{expected_reset:04d}.npz"
            if str(artifact_name) != expected_name:
                failures.append(f"{checkpoint_id}/reset_{expected_reset:02d} artifact name mismatch")
            else:
                artifact = R27G2ResetArtifact.read(manifest_path.parent / expected_name)
        elif manifest.get("status") != "INVALID":
            failures.append(f"{checkpoint_id}/reset_{expected_reset:02d} missing artifact")
        failures.extend(
            _status_failures(
                manifest,
                artifact,
                checkpoint_id=checkpoint_id,
                reset_id=expected_reset,
            )
        )
        artifacts.append(artifact)
        manifest_values.append(manifest)
    return artifacts, manifest_values, tuple(dict.fromkeys(failures))


def build_dataset(
    checkpoint_id: str,
    artifacts: list[R27G2ResetArtifact | None],
    manifests: list[dict[str, Any]],
    *,
    actor_base: torch.nn.Module,
    device: str | torch.device,
) -> tuple[CheckpointDataset | None, dict[str, Any], tuple[str, ...]]:
    if len(artifacts) != 64 or len(manifests) != 64:
        raise EvidenceError("R28-G0 adapter requires 64 reset records")
    target_device = torch.device(device)
    failures: list[str] = []
    reset_ids: list[int] = []
    agents: list[int] = []
    labels: list[int] = []
    duration_steps: list[int] = []
    duration_ids: list[int] = []
    phase_ids: list[int] = []
    post_rows: list[np.ndarray] = []
    pre_rows: list[np.ndarray] = []
    context_rows: list[np.ndarray] = []
    pulse_reset_ids: list[int] = []
    pulse_agents: list[int] = []
    pulse_labels: list[int] = []
    pulse_duration_steps: list[int] = []
    pulse_context_rows: list[np.ndarray] = []
    pulse_post_rows: list[np.ndarray] = []
    pulse_pre_rows: list[np.ndarray] = []
    valid_reset_ids: list[int] = []

    for reset_id, (artifact, manifest) in enumerate(zip(artifacts, manifests)):
        if str(manifest.get("status")) != "OK" or artifact is None:
            continue
        valid_reset_ids.append(reset_id)
        prefix = int(artifact.prefix_steps)
        phase = phase_id_for_prefix(prefix)
        pre_actions = np.tanh(np.asarray(artifact.prefix_pre_tanh_mean[-10:], dtype=np.float64))
        if pre_actions.shape != (10, N_AGENTS, ACTION_DIM):
            failures.append(f"{checkpoint_id}/reset_{reset_id:02d} pre-window shape mismatch")
            continue
        reference_obs = np.asarray(artifact.local_observation[0, 0], dtype=np.float32)
        with torch.no_grad():
            phi = actor_base(
                torch.as_tensor(reference_obs, dtype=torch.float32, device=target_device)
            ).detach().cpu().numpy()
        if phi.shape != (N_AGENTS, 256) or not np.isfinite(phi).all():
            failures.append(f"{checkpoint_id}/reset_{reset_id:02d} actor-base context mismatch")
            continue
        for agent_id in range(N_AGENTS):
            f_pre = late_action_features(pre_actions[:, agent_id, :])
            base_context = np.concatenate(
                (
                    phi[agent_id].astype(np.float32),
                    one_hot(np.asarray([agent_id]), N_AGENTS)[0],
                    np.zeros(4, dtype=np.float32),
                    one_hot(np.asarray([phase]), 3)[0],
                )
            )
            if base_context.shape != (CONTEXT_WIDTH,):
                raise AssertionError("R28-G0 context width drifted")
            for label in range(N_SKILLS):
                hold_branch = _branch_index(
                    artifact, kind="hold", focal_agent=agent_id, target_skill=label
                )
                if not bool(artifact.branch_completed[hold_branch]):
                    continue
                for duration_index, duration in enumerate(DURATION_STEPS):
                    window = DURATION_SLICES[duration]
                    post = np.tanh(
                        np.asarray(
                            artifact.live_pre_tanh_mean[hold_branch, window, agent_id],
                            dtype=np.float64,
                        )
                    )
                    context = base_context.copy()
                    context[256 + N_AGENTS + duration_index] = 1.0
                    reset_ids.append(reset_id)
                    agents.append(agent_id)
                    labels.append(label)
                    duration_steps.append(duration)
                    duration_ids.append(duration_index)
                    phase_ids.append(phase)
                    post_rows.append(late_action_features(post))
                    pre_rows.append(f_pre)
                    context_rows.append(context)
                    if duration >= 20 and label != int(artifact.branch_natural_skill[hold_branch]):
                        pulse_branch = _branch_index(
                            artifact,
                            kind="pulse",
                            focal_agent=agent_id,
                            target_skill=label,
                        )
                        if bool(artifact.branch_completed[pulse_branch]):
                            pulse = np.tanh(
                                np.asarray(
                                    artifact.live_pre_tanh_mean[pulse_branch, window, agent_id],
                                    dtype=np.float64,
                                )
                            )
                            pulse_reset_ids.append(reset_id)
                            pulse_agents.append(agent_id)
                            pulse_labels.append(label)
                            pulse_duration_steps.append(duration)
                            pulse_context_rows.append(context.copy())
                            pulse_post_rows.append(late_action_features(pulse))
                            pulse_pre_rows.append(f_pre)
    if failures:
        return None, {"valid_reset_ids": valid_reset_ids}, tuple(dict.fromkeys(failures))
    if not labels:
        return None, {"valid_reset_ids": valid_reset_ids}, ("no valid OK samples",)
    dataset = CheckpointDataset(
        checkpoint_id=checkpoint_id,
        reset_ids=np.asarray(reset_ids, dtype=np.int64),
        agents=np.asarray(agents, dtype=np.int64),
        labels=np.asarray(labels, dtype=np.int64),
        duration_steps=np.asarray(duration_steps, dtype=np.int64),
        duration_ids=np.asarray(duration_ids, dtype=np.int64),
        phase_ids=np.asarray(phase_ids, dtype=np.int64),
        context=np.asarray(context_rows, dtype=np.float32),
        f_post=np.asarray(post_rows, dtype=np.float32),
        f_pre=np.asarray(pre_rows, dtype=np.float32),
        pulse_reset_ids=np.asarray(pulse_reset_ids, dtype=np.int64),
        pulse_agents=np.asarray(pulse_agents, dtype=np.int64),
        pulse_labels=np.asarray(pulse_labels, dtype=np.int64),
        pulse_duration_steps=np.asarray(pulse_duration_steps, dtype=np.int64),
        pulse_context=np.asarray(pulse_context_rows, dtype=np.float32).reshape(-1, CONTEXT_WIDTH),
        pulse_f_post=np.asarray(pulse_post_rows, dtype=np.float32).reshape(-1, STREAM_WIDTH),
        pulse_f_pre=np.asarray(pulse_pre_rows, dtype=np.float32).reshape(-1, STREAM_WIDTH),
    )
    support = support_summary(dataset)
    return dataset, support, ()


def support_summary(dataset: CheckpointDataset) -> dict[str, Any]:
    ids = np.unique(dataset.reset_ids)
    train, val, test = _split_masks(ids)
    prefix_counts = [int(np.sum(ids % 3 == value)) for value in range(3)]
    split_prefix_counts = []
    for mask in (train, val, test):
        subset = ids[mask]
        split_prefix_counts.append([int(np.sum(subset % 3 == value)) for value in range(3)])
    return {
        "valid_resets": int(ids.size),
        "prefix_counts": prefix_counts,
        "split_counts": {
            "train": int(np.sum(train)),
            "validation": int(np.sum(val)),
            "test": int(np.sum(test)),
        },
        "split_prefix_counts": {
            "train": split_prefix_counts[0],
            "validation": split_prefix_counts[1],
            "test": split_prefix_counts[2],
        },
        "rows": int(dataset.labels.size),
        "pulse_pairs": int(dataset.pulse_labels.size),
    }


def support_reasons(support: dict[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if int(support["valid_resets"]) < 48:
        reasons.append(f"valid resets {support['valid_resets']} < 48")
    if any(int(value) < 14 for value in support["prefix_counts"]):
        reasons.append(f"prefix counts {support['prefix_counts']} below 14")
    split = support["split_counts"]
    if int(split["train"]) < 32 or int(split["validation"]) < 9 or int(split["test"]) < 9:
        reasons.append(f"split counts {split} below 32/9/9")
    prefixes = support["split_prefix_counts"]
    if any(int(value) < 10 for value in prefixes["train"]):
        reasons.append(f"train prefix counts {prefixes['train']} below 10")
    if any(int(value) < 3 for value in prefixes["validation"]):
        reasons.append(f"validation prefix counts {prefixes['validation']} below 3")
    if any(int(value) < 3 for value in prefixes["test"]):
        reasons.append(f"test prefix counts {prefixes['test']} below 3")
    if int(support["pulse_pairs"]) <= 0:
        reasons.append("no matched pulse persistence pairs")
    return tuple(reasons)


def head_input(stream: np.ndarray, context: np.ndarray) -> np.ndarray:
    stream = _finite_array("stream", stream, ndim=2)
    context = _finite_array("context", context, ndim=2)
    if stream.shape[0] != context.shape[0] or stream.shape[1] != STREAM_WIDTH:
        raise EvidenceError("stream/context row or width mismatch")
    if context.shape[1] != CONTEXT_WIDTH:
        raise EvidenceError("context width mismatch")
    return np.concatenate((stream, context), axis=1).astype(np.float32)


def fit_head(
    name: str,
    train_x: np.ndarray,
    train_y: np.ndarray,
    validation_x: np.ndarray,
    validation_y: np.ndarray,
    *,
    device: str | torch.device,
) -> HeadArtifact:
    train_x = _finite_array("train_x", train_x, ndim=2)
    validation_x = _finite_array("validation_x", validation_x, ndim=2)
    if train_x.shape[1] != HEAD_INPUT_WIDTH or validation_x.shape[1] != HEAD_INPUT_WIDTH:
        raise EvidenceError("head input width mismatch")
    train_y = _labels("train_y", train_y, (train_x.shape[0],))
    validation_y = _labels("validation_y", validation_y, (validation_x.shape[0],))
    mean = train_x.mean(axis=0, dtype=np.float64)
    std = np.maximum(train_x.std(axis=0, ddof=0, dtype=np.float64), STD_FLOOR)
    target_device = torch.device(device)

    def tensor(values: np.ndarray) -> torch.Tensor:
        standardized = (values - mean) / std
        if not np.isfinite(standardized).all():
            raise EvidenceError(f"{name} standardization produced non-finite values")
        return torch.as_tensor(standardized, dtype=torch.float32, device=target_device)

    x_train = tensor(train_x)
    x_val = tensor(validation_x)
    y_train = torch.as_tensor(train_y, dtype=torch.long, device=target_device)
    y_val = torch.as_tensor(validation_y, dtype=torch.long, device=target_device)
    fork_devices = [target_device.index or torch.cuda.current_device()] if target_device.type == "cuda" else []
    with torch.random.fork_rng(devices=fork_devices):
        torch.manual_seed(FIT_SEED)
        if fork_devices:
            torch.cuda.manual_seed_all(FIT_SEED)
        model = torch.nn.Linear(HEAD_INPUT_WIDTH, N_SKILLS).to(target_device)
        optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
        best_loss = float("inf")
        best_state: dict[str, torch.Tensor] | None = None
        stale = 0
        validations = 0
        optimizer_steps = 0
        for step in range(1, MAX_STEPS + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model(x_train), y_train)
            if not bool(torch.isfinite(loss).item()):
                raise EvidenceError(f"{name} non-finite training loss")
            loss.backward()
            optimizer.step()
            optimizer_steps = step
            if step % VALIDATE_EVERY:
                continue
            model.eval()
            with torch.no_grad():
                val_loss = float(F.cross_entropy(model(x_val), y_val).item())
            if not np.isfinite(val_loss):
                raise EvidenceError(f"{name} non-finite validation loss")
            validations += 1
            if val_loss < best_loss - MIN_DELTA:
                best_loss = val_loss
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
                stale = 0
            else:
                stale += 1
            if stale >= PATIENCE_VALIDATIONS:
                break
        if best_state is None:
            raise EvidenceError(f"{name} never produced a valid validation state")
        model.load_state_dict(best_state, strict=True)
        temperature = calibrate_temperature(model, x_val, y_val)
        weight = model.weight.detach().cpu().numpy().astype(np.float32)
        bias = model.bias.detach().cpu().numpy().astype(np.float32)
    return HeadArtifact(
        name=name,
        mean=mean.astype(np.float32),
        std=std.astype(np.float32),
        weight=weight,
        bias=bias,
        temperature=float(temperature),
        optimizer_steps=int(optimizer_steps),
        validation_evaluations=int(validations),
    )


def calibrate_temperature(
    model: torch.nn.Module,
    validation_x: torch.Tensor,
    validation_y: torch.Tensor,
) -> float:
    grid = torch.logspace(
        np.log10(0.05),
        np.log10(10.0),
        steps=401,
        dtype=torch.float32,
        device=validation_x.device,
    )
    model.eval()
    with torch.no_grad():
        logits = model(validation_x)
        losses = torch.stack([F.cross_entropy(logits / temp, validation_y) for temp in grid])
    index = int(torch.argmin(losses).item())
    return float(grid[index].item())


def score_head(
    artifact: HeadArtifact,
    x: np.ndarray,
    labels: np.ndarray,
    reset_ids: np.ndarray,
    duration_steps: np.ndarray,
    *,
    device: str | torch.device,
) -> HeadScore:
    x = _finite_array("score x", x, ndim=2)
    labels = _labels("score labels", labels, (x.shape[0],))
    ids = np.asarray(reset_ids, dtype=np.int64).reshape(-1)
    durations = np.asarray(duration_steps, dtype=np.int64).reshape(-1)
    if labels.shape != ids.shape or labels.shape != durations.shape:
        raise EvidenceError("score labels/reset/duration alignment mismatch")
    standardized = (x - artifact.mean) / artifact.std
    model = torch.nn.Linear(HEAD_INPUT_WIDTH, N_SKILLS).to(torch.device(device))
    model.load_state_dict(
        {
            "weight": torch.as_tensor(artifact.weight, dtype=torch.float32, device=torch.device(device)),
            "bias": torch.as_tensor(artifact.bias, dtype=torch.float32, device=torch.device(device)),
        },
        strict=True,
    )
    model.eval()
    with torch.no_grad():
        logits = model(torch.as_tensor(standardized, dtype=torch.float32, device=torch.device(device)))
        log_probs = F.log_softmax(logits / float(artifact.temperature), dim=1)
        predictions = log_probs.argmax(dim=1).detach().cpu().numpy().astype(np.int64)
        true_logp = log_probs[
            torch.arange(labels.size, device=log_probs.device),
            torch.as_tensor(labels, dtype=torch.long, device=log_probs.device),
        ].detach().cpu().numpy()
    train_mask, validation_mask, test_mask = _split_masks(ids)
    duration_accuracy = {
        int(duration): _accuracy(labels[test_mask & (durations == duration)], predictions[test_mask & (durations == duration)])
        for duration in DURATION_STEPS
        if np.any(test_mask & (durations == duration))
    }
    test_values = (labels[test_mask] == predictions[test_mask]).astype(np.float64)
    interval = reset_cluster_interval(ids[test_mask], test_values)
    return HeadScore(
        name=artifact.name,
        train_accuracy=_accuracy(labels[train_mask], predictions[train_mask]),
        validation_accuracy=_accuracy(labels[validation_mask], predictions[validation_mask]),
        test_accuracy=_accuracy(labels[test_mask], predictions[test_mask]),
        test_macro_f1=_macro_f1(labels[test_mask], predictions[test_mask]),
        duration_test_accuracy=duration_accuracy,
        accuracy_interval=interval,
        train_minus_test=_accuracy(labels[train_mask], predictions[train_mask])
        - _accuracy(labels[test_mask], predictions[test_mask]),
        optimizer_steps=artifact.optimizer_steps,
        validation_evaluations=artifact.validation_evaluations,
        temperature=artifact.temperature,
        log_prob_true=true_logp,
        predictions=predictions,
    )


def sham_labels(dataset: CheckpointDataset) -> np.ndarray:
    labels = dataset.labels.copy()
    result = labels.copy()
    rng = np.random.default_rng(SHAM_SEED)
    for reset_id in np.unique(dataset.reset_ids):
        for agent in range(N_AGENTS):
            for duration in DURATION_STEPS:
                mask = (
                    (dataset.reset_ids == reset_id)
                    & (dataset.agents == agent)
                    & (dataset.duration_steps == duration)
                )
                if np.sum(mask) != N_SKILLS:
                    continue
                shift = int(rng.integers(1, N_SKILLS))
                result[mask] = (labels[mask] + shift) % N_SKILLS
    return result


def support_envelope(
    dataset: CheckpointDataset,
    *,
    train_mask: np.ndarray,
    validation_mask: np.ndarray,
) -> dict[str, Any]:
    train_features = dataset.f_post[train_mask]
    train_labels = dataset.labels[train_mask]
    train_durations = dataset.duration_steps[train_mask]
    validation_features = dataset.f_post[validation_mask]
    validation_labels = dataset.labels[validation_mask]
    validation_durations = dataset.duration_steps[validation_mask]
    means = np.zeros((len(DURATION_STEPS), N_SKILLS, STREAM_WIDTH), dtype=np.float64)
    variances = np.zeros_like(means)
    thresholds = np.zeros((len(DURATION_STEPS), N_SKILLS), dtype=np.float64)
    for duration_index, duration in enumerate(DURATION_STEPS):
        duration_train = train_features[train_durations == duration]
        if duration_train.size == 0:
            raise UnderpoweredEvidenceError(f"no train rows for duration {duration}")
        pooled_var = np.var(duration_train, axis=0, ddof=0)
        for label in range(N_SKILLS):
            mask = (train_durations == duration) & (train_labels == label)
            if not np.any(mask):
                raise UnderpoweredEvidenceError(f"no train rows for duration {duration} label {label}")
            cls = train_features[mask]
            means[duration_index, label] = cls.mean(axis=0)
            variances[duration_index, label] = np.maximum(
                0.90 * np.var(cls, axis=0, ddof=0) + 0.10 * pooled_var,
                STD_FLOOR,
            )
            val_mask = (validation_durations == duration) & (validation_labels == label)
            if not np.any(val_mask):
                raise UnderpoweredEvidenceError(f"no validation rows for duration {duration} label {label}")
            d2 = np.sum(
                np.square(validation_features[val_mask] - means[duration_index, label])
                / variances[duration_index, label],
                axis=1,
            )
            thresholds[duration_index, label] = float(np.quantile(d2, 0.95, method="linear"))
    return {
        "means": means.astype(np.float32),
        "variances": variances.astype(np.float32),
        "thresholds": thresholds.astype(np.float32),
        "future_ood_kill_fraction": 0.20,
    }


def envelope_coverage(envelope: dict[str, Any], features: np.ndarray, labels: np.ndarray, durations: np.ndarray) -> float:
    means = np.asarray(envelope["means"], dtype=np.float64)
    variances = np.asarray(envelope["variances"], dtype=np.float64)
    thresholds = np.asarray(envelope["thresholds"], dtype=np.float64)
    flags: list[bool] = []
    for feature, label, duration in zip(features, labels, durations):
        duration_index = DURATION_STEPS.index(int(duration))
        d2 = float(np.sum(np.square(feature - means[duration_index, int(label)]) / variances[duration_index, int(label)]))
        flags.append(d2 <= thresholds[duration_index, int(label)])
    if not flags:
        raise EvidenceError("support envelope coverage requires at least one row")
    return float(np.mean(np.asarray(flags, dtype=np.bool_)))


def analyze_dataset(
    dataset: CheckpointDataset,
    *,
    device: str | torch.device,
) -> CheckpointResult:
    support = support_summary(dataset)
    reasons = list(support_reasons(support))
    if reasons:
        return CheckpointResult(
            checkpoint_id=dataset.checkpoint_id,
            status="UNDERPOWERED",
            classification="UNDERPOWERED",
            reasons=tuple(reasons),
            support=support,
            q_full=None,
            q_context=None,
            q_pre=None,
            q_full_artifact=None,
            q_context_artifact=None,
            q_pre_artifact=None,
            metrics={},
            support_envelope=None,
        )
    train_mask, validation_mask, test_mask = _split_masks(dataset.reset_ids)
    x_full = head_input(dataset.f_post, dataset.context)
    x_context = head_input(np.zeros_like(dataset.f_post), dataset.context)
    x_pre = head_input(dataset.f_pre, dataset.context)
    full_artifact = fit_head(
        "q_full",
        x_full[train_mask],
        dataset.labels[train_mask],
        x_full[validation_mask],
        dataset.labels[validation_mask],
        device=device,
    )
    context_artifact = fit_head(
        "q_context",
        x_context[train_mask],
        dataset.labels[train_mask],
        x_context[validation_mask],
        dataset.labels[validation_mask],
        device=device,
    )
    pre_artifact = fit_head(
        "q_pre",
        x_pre[train_mask],
        dataset.labels[train_mask],
        x_pre[validation_mask],
        dataset.labels[validation_mask],
        device=device,
    )
    q_full = score_head(full_artifact, x_full, dataset.labels, dataset.reset_ids, dataset.duration_steps, device=device)
    q_context = score_head(context_artifact, x_context, dataset.labels, dataset.reset_ids, dataset.duration_steps, device=device)
    q_pre = score_head(pre_artifact, x_pre, dataset.labels, dataset.reset_ids, dataset.duration_steps, device=device)
    sham = sham_labels(dataset)
    sham_full = score_head(full_artifact, x_full, sham, dataset.reset_ids, dataset.duration_steps, device=device)
    s_real = q_full.log_prob_true - np.maximum(q_context.log_prob_true, q_pre.log_prob_true)
    s_real_interval = reset_cluster_interval(dataset.reset_ids[test_mask], s_real[test_mask])
    full_context_gain = q_full.test_accuracy - q_context.test_accuracy
    full_pre_gain = q_full.test_accuracy - q_pre.test_accuracy
    full_context_gain_interval = reset_cluster_interval(
        dataset.reset_ids[test_mask],
        (dataset.labels[test_mask] == q_full.predictions[test_mask]).astype(np.float64)
        - (dataset.labels[test_mask] == q_context.predictions[test_mask]).astype(np.float64),
    )
    full_pre_gain_interval = reset_cluster_interval(
        dataset.reset_ids[test_mask],
        (dataset.labels[test_mask] == q_full.predictions[test_mask]).astype(np.float64)
        - (dataset.labels[test_mask] == q_pre.predictions[test_mask]).astype(np.float64),
    )
    envelope = support_envelope(dataset, train_mask=train_mask, validation_mask=validation_mask)
    test_envelope_coverage = envelope_coverage(
        envelope,
        dataset.f_post[test_mask],
        dataset.labels[test_mask],
        dataset.duration_steps[test_mask],
    )
    pulse_diffs: list[float] = []
    pulse_reset_ids: list[int] = []
    pulse_by_duration: dict[int, float] = {}
    if dataset.pulse_labels.size:
        x_pulse_full = head_input(dataset.pulse_f_post, dataset.pulse_context)
        x_pulse_context = head_input(np.zeros_like(dataset.pulse_f_post), dataset.pulse_context)
        x_pulse_pre = head_input(dataset.pulse_f_pre, dataset.pulse_context)
        pulse_full = score_head(
            full_artifact,
            x_pulse_full,
            dataset.pulse_labels,
            dataset.pulse_reset_ids,
            dataset.pulse_duration_steps,
            device=device,
        )
        pulse_context = score_head(
            context_artifact,
            x_pulse_context,
            dataset.pulse_labels,
            dataset.pulse_reset_ids,
            dataset.pulse_duration_steps,
            device=device,
        )
        pulse_pre = score_head(
            pre_artifact,
            x_pulse_pre,
            dataset.pulse_labels,
            dataset.pulse_reset_ids,
            dataset.pulse_duration_steps,
            device=device,
        )
        pulse_test = dataset.pulse_reset_ids <= 11
        for reset_id, agent, label, duration, pulse_value in zip(
            dataset.pulse_reset_ids[pulse_test],
            dataset.pulse_agents[pulse_test],
            dataset.pulse_labels[pulse_test],
            dataset.pulse_duration_steps[pulse_test],
            pulse_full.log_prob_true[pulse_test]
            - np.maximum(
                pulse_context.log_prob_true[pulse_test],
                pulse_pre.log_prob_true[pulse_test],
            ),
        ):
            hold_matches = np.flatnonzero(
                (dataset.reset_ids == int(reset_id))
                & (dataset.agents == int(agent))
                & (dataset.labels == int(label))
                & (dataset.duration_steps == int(duration))
            )
            if hold_matches.size != 1:
                raise EvidenceError("hold/pulse key alignment mismatch")
            hold_value = float(s_real[int(hold_matches[0])])
            pulse_diffs.append(hold_value - float(pulse_value))
            pulse_reset_ids.append(int(reset_id))
        if pulse_diffs:
            diff_array = np.asarray(pulse_diffs, dtype=np.float64)
            pulse_reset_array = np.asarray(pulse_reset_ids, dtype=np.int64)
            for duration in (20, 30, 40):
                duration_values = [
                    float(value)
                    for value, pulse_duration in zip(
                        diff_array, dataset.pulse_duration_steps[pulse_test]
                    )
                    if int(pulse_duration) == duration
                ]
                if duration_values:
                    pulse_by_duration[duration] = float(np.mean(duration_values))
    if pulse_diffs:
        pulse_interval = reset_cluster_interval(np.asarray(pulse_reset_ids), np.asarray(pulse_diffs))
    else:
        pulse_interval = BootstrapInterval(estimate=0.0, lower=0.0, upper=0.0, reps=BOOTSTRAP_REPS, seed=BOOTSTRAP_SEED)
    metrics: dict[str, Any] = {
        "qfull_minus_context_accuracy_gain": full_context_gain,
        "qfull_minus_context_gain_interval": full_context_gain_interval,
        "qfull_minus_pre_accuracy_gain": full_pre_gain,
        "qfull_minus_pre_gain_interval": full_pre_gain_interval,
        "mean_s_real_interval": s_real_interval,
        "hold_minus_pulse_s_real_interval": pulse_interval,
        "hold_minus_pulse_s_real_by_duration": pulse_by_duration,
        "sham_accuracy": sham_full.test_accuracy,
        "support_heldout_coverage": test_envelope_coverage,
    }
    checks = (
        (q_full.test_accuracy >= 0.40, f"q_full test accuracy {q_full.test_accuracy:.6g} < 0.40"),
        (q_full.test_macro_f1 >= 0.40, f"q_full macro-F1 {q_full.test_macro_f1:.6g} < 0.40"),
        (all(q_full.duration_test_accuracy.get(duration, 0.0) >= 0.40 for duration in DURATION_STEPS), "at least one duration accuracy < 0.40"),
        (q_full.accuracy_interval.lower > 0.25, f"q_full accuracy lower {q_full.accuracy_interval.lower:.6g} <= 0.25"),
        (full_context_gain >= 0.05 and full_context_gain_interval.lower > 0.0, "q_full-context gain gate failed"),
        (full_pre_gain >= 0.05 and full_pre_gain_interval.lower > 0.0, "q_full-pre gain gate failed"),
        (s_real_interval.lower > 0.0, f"mean s_real lower {s_real_interval.lower:.6g} <= 0"),
        (pulse_interval.lower > 0.0, f"hold-pulse lower {pulse_interval.lower:.6g} <= 0"),
        (all(pulse_by_duration.get(duration, 0.0) > 0.0 for duration in (20, 30, 40)), "a pulse duration point estimate is not positive"),
        (sham_full.test_accuracy <= 0.35, f"sham accuracy {sham_full.test_accuracy:.6g} > 0.35"),
        (all(head.train_minus_test <= 0.20 for head in (q_full, q_context, q_pre)), "at least one train-test gap > 0.20"),
        (test_envelope_coverage >= 0.90, f"support coverage {test_envelope_coverage:.6g} < 0.90"),
    )
    fail_reasons = tuple(reason for passed, reason in checks if not passed)
    return CheckpointResult(
        checkpoint_id=dataset.checkpoint_id,
        status="PASS" if not fail_reasons else "FAIL",
        classification="PASS_TARGET_NULLS" if not fail_reasons else "FAIL_TARGET",
        reasons=fail_reasons,
        support=support,
        q_full=q_full,
        q_context=q_context,
        q_pre=q_pre,
        q_full_artifact=full_artifact,
        q_context_artifact=context_artifact,
        q_pre_artifact=pre_artifact,
        metrics=metrics,
        support_envelope=envelope,
    )


def classify_family(results: list[CheckpointResult]) -> tuple[str, str]:
    if len(results) != 3:
        raise EvidenceError("R28-G0 family classification requires three checkpoints")
    by_id = {item.checkpoint_id: item for item in results}
    if any(item.status == "INVALID" for item in results):
        return "INVALID", "INVALID"
    if any(item.status == "UNDERPOWERED" for item in results):
        return "UNDERPOWERED", "UNDERPOWERED"
    final_pass = by_id["arm0_final"].status == "PASS"
    earlier_pass = any(by_id[item].status == "PASS" for item in ("arm0_update25", "arm0_update30"))
    pass_count = sum(item.status == "PASS" for item in results)
    if final_pass and earlier_pass:
        return "PASS", "PASS_TARGET_NULLS"
    if pass_count == 0:
        return "FAIL", "FAIL_TARGET"
    return "MIXED", "MIXED_TARGET"


def scorer_payload(result: CheckpointResult) -> dict[str, Any]:
    if result.status != "PASS" or result.checkpoint_id != "arm0_final":
        raise EvidenceError("only a passing final checkpoint may produce the frozen scorer")
    return {
        "experiment_id": EXPERIMENT_ID,
        "checkpoint_id": result.checkpoint_id,
        "authorized_for_g1_package_review": True,
        "reward_launch_authorized": False,
        "heads": {
            "q_full": jsonable(result.q_full_artifact),
            "q_context": jsonable(result.q_context_artifact),
            "q_pre": jsonable(result.q_pre_artifact),
        },
        "support_envelope": jsonable(result.support_envelope),
        "scientific_contract": SCIENTIFIC_CONTRACT,
    }
