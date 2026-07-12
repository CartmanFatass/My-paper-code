"""Frozen low-actor capacity diagnostics for R27-G1."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F


STATIC_SKL_MIN = 0.02
STATIC_STDMEAN_MIN = 0.20
RECURRENT_RETENTION_MAX = 0.50
INACTIVE_TOLERANCE = 1e-8
PARITY_TOLERANCE = 1e-6
SYNTHETIC_ACCURACY_MIN = 0.90
SYNTHETIC_MACRO_F1_MIN = 0.90
SYNTHETIC_ACTIVE_MINUS_SHAM_MIN = 0.50
SYNTHETIC_GENERALIZATION_GAP_MAX = 0.20
SYNTHETIC_SHAM_MARGIN = 0.10
MIN_BOOTSTRAP_RESET_GROUPS = 5


def static_capacity_thresholds() -> dict[str, object]:
    """Return the immutable per-checkpoint static decision thresholds."""

    return {
        "symmetric_kl_min": STATIC_SKL_MIN,
        "standardized_mean_distance_min": STATIC_STDMEAN_MIN,
        "bootstrap_lower": "> 0.0",
        "inactive_tolerance": INACTIVE_TOLERANCE,
        "parity_tolerance": PARITY_TOLERANCE,
    }


def synthetic_capacity_thresholds(num_skills: int) -> dict[str, object]:
    """Return the immutable per-seed synthetic decision thresholds."""

    return {
        "active_accuracy_min": SYNTHETIC_ACCURACY_MIN,
        "active_macro_f1_min": SYNTHETIC_MACRO_F1_MIN,
        "active_minus_sham_accuracy_min": SYNTHETIC_ACTIVE_MINUS_SHAM_MIN,
        "bootstrap_lower": "> 0.0",
        "sham_accuracy_max": 1.0 / int(num_skills) + SYNTHETIC_SHAM_MARGIN,
        "train_minus_test_accuracy_max": SYNTHETIC_GENERALIZATION_GAP_MAX,
    }


@dataclass(frozen=True)
class CapacitySnapshotBatch:
    observation: np.ndarray
    actor_hidden: np.ndarray
    natural_skill: np.ndarray
    previous_skill: np.ndarray
    duration_idx: np.ndarray
    skill_age: np.ndarray
    episode_done_mask: np.ndarray
    reset_id: np.ndarray
    reset_seed: np.ndarray
    episode_id: np.ndarray
    env_id: np.ndarray
    agent_id: np.ndarray
    checkpoint_id: np.ndarray
    checkpoint_update: np.ndarray

    def take(self, indices: np.ndarray) -> "CapacitySnapshotBatch":
        idx = np.asarray(indices, dtype=np.int64)
        return CapacitySnapshotBatch(
            **{
                field: np.asarray(getattr(self, field))[idx]
                for field in self.__dataclass_fields__
            }
        )


@dataclass(frozen=True)
class ResetSplit:
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray
    train_reset_ids: tuple[int, ...]
    validation_reset_ids: tuple[int, ...]
    test_reset_ids: tuple[int, ...]


@dataclass(frozen=True)
class BootstrapInterval:
    mean: float
    lower: float
    upper: float


@dataclass(frozen=True)
class ActorForwardBatch:
    gamma: torch.Tensor
    beta: torch.Tensor
    film_feature: torch.Tensor
    post_gru_feature: torch.Tensor
    action_mean: torch.Tensor
    action_logstd: torch.Tensor
    deterministic_action: torch.Tensor
    new_hidden: torch.Tensor


@dataclass(frozen=True)
class SyntheticRows:
    observation: np.ndarray
    actor_hidden: np.ndarray
    true_skill: np.ndarray
    fake_skill: np.ndarray
    reset_id: np.ndarray

    def take(self, indices: np.ndarray) -> "SyntheticRows":
        idx = np.asarray(indices, dtype=np.int64)
        return SyntheticRows(
            observation=np.asarray(self.observation)[idx],
            actor_hidden=np.asarray(self.actor_hidden)[idx],
            true_skill=np.asarray(self.true_skill)[idx],
            fake_skill=np.asarray(self.fake_skill)[idx],
            reset_id=np.asarray(self.reset_id)[idx],
        )


@dataclass(frozen=True)
class SyntheticFitConfig:
    learning_rate: float = 3e-4
    batch_size: int = 256
    max_steps: int = 1000
    validation_interval: int = 25
    patience: int = 20
    min_delta: float = 1e-4


@dataclass(frozen=True)
class SyntheticScore:
    accuracy: float
    macro_f1: float
    target_mse: float
    correct: np.ndarray
    predicted_skill: np.ndarray
    reset_id: np.ndarray


FLOAT_FIELDS = ("observation", "actor_hidden")
INT_FIELDS = (
    "natural_skill",
    "previous_skill",
    "duration_idx",
    "skill_age",
    "reset_id",
    "reset_seed",
    "episode_id",
    "env_id",
    "agent_id",
    "checkpoint_update",
)


def validate_capacity_snapshots(
    batch: CapacitySnapshotBatch,
) -> CapacitySnapshotBatch:
    arrays = {
        field: np.asarray(getattr(batch, field))
        for field in CapacitySnapshotBatch.__dataclass_fields__
    }
    rows = int(arrays["natural_skill"].reshape(-1).size)
    for field, values in arrays.items():
        if values.ndim == 0 or int(values.shape[0]) != rows:
            raise ValueError(f"{field} must have {rows} rows")
    for field in FLOAT_FIELDS:
        if not np.isfinite(arrays[field]).all():
            raise ValueError(f"{field} contains non-finite values")
    if arrays["observation"].ndim != 2 or arrays["actor_hidden"].ndim != 2:
        raise ValueError("observation and actor_hidden must be rank-2")

    values: dict[str, np.ndarray] = {}
    for field, array in arrays.items():
        if field in FLOAT_FIELDS:
            values[field] = np.asarray(array, dtype=np.float32)
        elif field in INT_FIELDS:
            values[field] = np.asarray(array, dtype=np.int64).reshape(-1)
        elif field == "episode_done_mask":
            values[field] = np.asarray(array, dtype=np.bool_).reshape(-1)
        else:
            values[field] = np.asarray(array, dtype=np.str_).reshape(-1)
    return CapacitySnapshotBatch(**values)


def write_capacity_snapshot_shard(
    path: Path, batch: CapacitySnapshotBatch
) -> None:
    validated = validate_capacity_snapshots(batch)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        **{
            field: getattr(validated, field)
            for field in CapacitySnapshotBatch.__dataclass_fields__
        },
    )


def read_capacity_snapshot_shards(root: Path) -> CapacitySnapshotBatch:
    paths = sorted(Path(root).glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no capacity snapshot shards under {root}")

    fields = tuple(CapacitySnapshotBatch.__dataclass_fields__)
    chunks: dict[str, list[np.ndarray]] = {field: [] for field in fields}
    for path in paths:
        with np.load(path, allow_pickle=False) as data:
            missing = [field for field in fields if field not in data]
            if missing:
                raise ValueError(f"{path} missing fields: {missing}")
            shard = validate_capacity_snapshots(
                CapacitySnapshotBatch(**{field: data[field] for field in fields})
            )
            for field in fields:
                chunks[field].append(np.asarray(getattr(shard, field)))
    return validate_capacity_snapshots(
        CapacitySnapshotBatch(
            **{
                field: np.concatenate(chunks[field], axis=0)
                for field in fields
            }
        )
    )


def grouped_reset_split(reset_id: np.ndarray, seed: int) -> ResetSplit:
    ids = np.unique(np.asarray(reset_id, dtype=np.int64).reshape(-1))
    if ids.size < 5:
        raise ValueError("at least five reset groups are required")
    shuffled = ids.copy()
    np.random.default_rng(int(seed)).shuffle(shuffled)
    n_test = max(1, int(np.floor(0.2 * shuffled.size)))
    n_validation = max(1, int(np.floor(0.2 * shuffled.size)))
    test_ids = np.sort(shuffled[:n_test])
    validation_ids = np.sort(shuffled[n_test : n_test + n_validation])
    train_ids = np.sort(shuffled[n_test + n_validation :])
    reset_values = np.asarray(reset_id, dtype=np.int64).reshape(-1)
    return ResetSplit(
        train=np.flatnonzero(np.isin(reset_values, train_ids)),
        validation=np.flatnonzero(np.isin(reset_values, validation_ids)),
        test=np.flatnonzero(np.isin(reset_values, test_ids)),
        train_reset_ids=tuple(int(value) for value in train_ids),
        validation_reset_ids=tuple(int(value) for value in validation_ids),
        test_reset_ids=tuple(int(value) for value in test_ids),
    )


def cluster_bootstrap_difference(
    active: np.ndarray,
    control: np.ndarray,
    reset_ids: np.ndarray,
    *,
    reps: int,
    seed: int,
) -> BootstrapInterval:
    active_values = np.asarray(active, dtype=np.float64).reshape(-1)
    control_values = np.asarray(control, dtype=np.float64).reshape(-1)
    groups = np.asarray(reset_ids, dtype=np.int64).reshape(-1)
    if (
        active_values.shape != control_values.shape
        or active_values.shape != groups.shape
    ):
        raise ValueError("active, control, and reset_ids must be row-aligned")
    if int(reps) <= 0:
        raise ValueError("reps must be positive")
    unique_groups = np.unique(groups)
    if unique_groups.size < 5:
        raise ValueError("at least five reset groups are required for bootstrap")

    rng = np.random.default_rng(int(seed))
    estimates = np.empty(int(reps), dtype=np.float64)
    for index in range(int(reps)):
        sampled = rng.choice(
            unique_groups, size=unique_groups.size, replace=True
        )
        rows = np.concatenate(
            [np.flatnonzero(groups == group) for group in sampled]
        )
        estimates[index] = float(
            (active_values[rows] - control_values[rows]).mean()
        )
    return BootstrapInterval(
        mean=float((active_values - control_values).mean()),
        lower=float(np.quantile(estimates, 0.025)),
        upper=float(np.quantile(estimates, 0.975)),
    )


def _require_supported_actor(actor: Any) -> None:
    if getattr(actor, "action_space_type", None) != "continuous":
        raise ValueError("R27 static audit requires a continuous low actor")
    if getattr(actor, "actor_team_film", None) is not None:
        raise ValueError("R27 static audit requires actor_team_film to be disabled")
    action_out = actor.actor_act.action_out
    if type(action_out).__name__ != "TanhDiagGaussian":
        raise ValueError("R27 static audit requires TanhDiagGaussian")


def forward_actor_snapshot(
    actor: Any,
    observations: torch.Tensor,
    skills: torch.Tensor,
    actor_hidden: torch.Tensor,
    *,
    inactive_film: bool,
) -> ActorForwardBatch:
    """Read one actor transition without retaining gradients or runtime state."""

    _require_supported_actor(actor)
    obs = torch.as_tensor(
        observations, dtype=torch.float32, device=actor.device
    )
    skill = torch.as_tensor(skills, dtype=torch.long, device=actor.device)
    hidden = torch.as_tensor(
        actor_hidden, dtype=torch.float32, device=actor.device
    )
    if obs.ndim != 2 or obs.shape[1] != actor.obs_dim:
        raise ValueError("observations do not match actor.obs_dim")
    if hidden.ndim != 2 or hidden.shape != (obs.shape[0], actor.hidden_dim):
        raise ValueError("actor_hidden does not match actor batch and hidden_dim")
    if skill.ndim != 1 or skill.shape[0] != obs.shape[0]:
        raise ValueError("skills must have one value per observation")

    with torch.no_grad():
        base = actor.actor_base(obs)
        raw_film = actor.actor_film(
            F.one_hot(skill, num_classes=actor.n_skills).float()
        )
        gamma, beta = torch.chunk(raw_film, 2, dim=-1)
        if inactive_film:
            gamma = torch.ones_like(gamma)
            beta = torch.zeros_like(beta)
        film_feature = gamma * base + beta
        masks = torch.ones(
            obs.shape[0], 1, dtype=torch.float32, device=actor.device
        )
        post_gru, new_hidden = actor.actor_rnn(film_feature, hidden, masks)
        distribution = actor.actor_act.action_out._distribution(post_gru)
        action_mean = distribution.mean
        action_logstd = distribution.scale.log()
        deterministic_action = torch.tanh(action_mean)
    return ActorForwardBatch(
        gamma=gamma.detach(),
        beta=beta.detach(),
        film_feature=film_feature.detach(),
        post_gru_feature=post_gru.detach(),
        action_mean=action_mean.detach(),
        action_logstd=action_logstd.detach(),
        deterministic_action=deterministic_action.detach(),
        new_hidden=new_hidden.detach(),
    )


def symmetric_kl_diag_gaussian(
    mean_a: torch.Tensor,
    logstd_a: torch.Tensor,
    mean_b: torch.Tensor,
    logstd_b: torch.Tensor,
) -> torch.Tensor:
    """Symmetric KL for row-aligned diagonal Gaussian distributions."""

    var_a = torch.exp(2.0 * logstd_a)
    var_b = torch.exp(2.0 * logstd_b)
    delta_sq = (mean_a - mean_b).pow(2)
    kl_ab = 0.5 * (
        2.0 * (logstd_b - logstd_a)
        + (var_a + delta_sq) / var_b
        - 1.0
    ).sum(dim=-1)
    kl_ba = 0.5 * (
        2.0 * (logstd_a - logstd_b)
        + (var_b + delta_sq) / var_a
        - 1.0
    ).sum(dim=-1)
    return 0.5 * (kl_ab + kl_ba)


def _bootstrap_dict(interval: BootstrapInterval) -> dict[str, float]:
    return {
        "mean": interval.mean,
        "lower": interval.lower,
        "upper": interval.upper,
    }


def _condition_metrics(
    active: ActorForwardBatch,
    inactive: ActorForwardBatch,
    reset_ids: np.ndarray,
    *,
    rows: int,
    num_skills: int,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    pairs = tuple(combinations(range(int(num_skills)), 2))
    if not pairs:
        raise ValueError("at least two skills are required")

    for label, output in (("active", active), ("inactive", inactive)):
        for field in ActorForwardBatch.__dataclass_fields__:
            value = getattr(output, field)
            if not bool(torch.isfinite(value).all().item()):
                raise FloatingPointError(
                    f"non-finite {label} actor-forward field: {field}"
                )

    def shaped(value: torch.Tensor) -> torch.Tensor:
        return value.reshape(int(rows), int(num_skills), value.shape[-1])

    active_mean = shaped(active.action_mean)
    active_logstd = shaped(active.action_logstd)
    inactive_mean = shaped(inactive.action_mean)
    inactive_logstd = shaped(inactive.action_logstd)
    active_film = shaped(active.film_feature)
    active_post_gru = shaped(active.post_gru_feature)

    active_skl_pairs: list[torch.Tensor] = []
    inactive_skl_pairs: list[torch.Tensor] = []
    active_stdmean_pairs: list[torch.Tensor] = []
    inactive_stdmean_pairs: list[torch.Tensor] = []
    film_pairs: list[torch.Tensor] = []
    post_gru_pairs: list[torch.Tensor] = []
    shared_logstd_error = 0.0
    for first, second in pairs:
        active_skl_pairs.append(
            symmetric_kl_diag_gaussian(
                active_mean[:, first],
                active_logstd[:, first],
                active_mean[:, second],
                active_logstd[:, second],
            )
        )
        inactive_skl_pairs.append(
            symmetric_kl_diag_gaussian(
                inactive_mean[:, first],
                inactive_logstd[:, first],
                inactive_mean[:, second],
                inactive_logstd[:, second],
            )
        )
        active_std = torch.exp(active_logstd[:, first])
        inactive_std = torch.exp(inactive_logstd[:, first])
        active_stdmean_pairs.append(
            torch.linalg.vector_norm(
                (active_mean[:, first] - active_mean[:, second]) / active_std,
                dim=-1,
            )
        )
        inactive_stdmean_pairs.append(
            torch.linalg.vector_norm(
                (inactive_mean[:, first] - inactive_mean[:, second])
                / inactive_std,
                dim=-1,
            )
        )
        film_pairs.append(
            torch.linalg.vector_norm(
                active_film[:, first] - active_film[:, second], dim=-1
            )
        )
        post_gru_pairs.append(
            torch.linalg.vector_norm(
                active_post_gru[:, first] - active_post_gru[:, second], dim=-1
            )
        )
        shared_logstd_error = max(
            shared_logstd_error,
            float(
                torch.max(
                    torch.abs(
                        active_logstd[:, first] - active_logstd[:, second]
                    )
                ).item()
            ),
        )

    active_skl_by_row = torch.stack(active_skl_pairs, dim=1).mean(dim=1)
    inactive_skl_by_row = torch.stack(inactive_skl_pairs, dim=1).mean(dim=1)
    active_stdmean_by_row = torch.stack(active_stdmean_pairs, dim=1).mean(dim=1)
    inactive_stdmean_by_row = torch.stack(inactive_stdmean_pairs, dim=1).mean(
        dim=1
    )
    film_by_pair = torch.stack(film_pairs, dim=1)
    post_gru_by_pair = torch.stack(post_gru_pairs, dim=1)
    derived_tensors = (
        active_skl_by_row,
        inactive_skl_by_row,
        active_stdmean_by_row,
        inactive_stdmean_by_row,
        film_by_pair,
        post_gru_by_pair,
    )
    if not all(
        bool(torch.isfinite(value).all().item()) for value in derived_tensors
    ):
        raise FloatingPointError("non-finite static derived evidence")
    interval = cluster_bootstrap_difference(
        active_skl_by_row.cpu().numpy(),
        inactive_skl_by_row.cpu().numpy(),
        reset_ids,
        reps=int(bootstrap_reps),
        seed=int(bootstrap_seed),
    )
    mean_skl = float(active_skl_by_row.mean().item())
    mean_stdmean = float(active_stdmean_by_row.mean().item())
    scalar_values = np.asarray(
        [
            mean_skl,
            mean_stdmean,
            interval.mean,
            interval.lower,
            interval.upper,
            shared_logstd_error,
            float(film_by_pair.mean().item()),
            float(post_gru_by_pair.mean().item()),
        ],
        dtype=np.float64,
    )
    if not np.isfinite(scalar_values).all():
        raise FloatingPointError("non-finite static scalar evidence")
    return {
        "mean_skl": mean_skl,
        "mean_stdmean_distance": mean_stdmean,
        "bootstrap": _bootstrap_dict(interval),
        "film_feature_between": float(film_by_pair.mean().item()),
        "post_gru_feature_between": float(post_gru_by_pair.mean().item()),
        "inactive_max_abs_skl": float(
            torch.stack(inactive_skl_pairs, dim=1).abs().max().item()
        ),
        "inactive_max_stdmean_distance": float(
            torch.stack(inactive_stdmean_pairs, dim=1).max().item()
        ),
        "shared_logstd_max_abs_error": shared_logstd_error,
        "finite": True,
        "pass": bool(
            shared_logstd_error <= PARITY_TOLERANCE
            and mean_skl >= STATIC_SKL_MIN
            and mean_stdmean >= STATIC_STDMEAN_MIN
            and interval.lower > 0.0
        ),
    }


def _parity_metrics(
    actor: Any,
    observations: torch.Tensor,
    skills: torch.Tensor,
    hidden: torch.Tensor,
    diagnostic: ActorForwardBatch,
) -> dict[str, object]:
    with torch.no_grad():
        live_action, _, _, _, live_hidden, _ = actor.act(
            observations,
            skills,
            hidden.clone(),
            torch.zeros(
                observations.shape[0],
                actor.state_dim,
                dtype=torch.float32,
                device=actor.device,
            ),
            torch.zeros(
                observations.shape[0], dtype=torch.long, device=actor.device
            ),
            torch.zeros(
                observations.shape[0],
                actor.hidden_dim,
                dtype=torch.float32,
                device=actor.device,
            ),
            deterministic=True,
        )
    action_error = float(
        torch.max(torch.abs(diagnostic.deterministic_action - live_action)).item()
    )
    hidden_error = float(
        torch.max(torch.abs(diagnostic.new_hidden - live_hidden)).item()
    )
    if not (
        bool(torch.isfinite(live_action).all().item())
        and bool(torch.isfinite(live_hidden).all().item())
        and np.isfinite(action_error)
        and np.isfinite(hidden_error)
    ):
        raise FloatingPointError("non-finite live parity evidence")
    return {
        "max_action_abs_error": action_error,
        "max_hidden_abs_error": hidden_error,
        "pass": bool(
            action_error <= PARITY_TOLERANCE
            and hidden_error <= PARITY_TOLERANCE
        ),
    }


def evaluate_static_checkpoint(
    actor: Any,
    batch: CapacitySnapshotBatch,
    *,
    checkpoint_id: str,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    """Enumerate every skill at identical observations and hidden states."""

    snapshots = validate_capacity_snapshots(batch)
    rows = int(snapshots.natural_skill.size)
    reset_count = int(np.unique(snapshots.reset_id).size)
    if rows == 0 or reset_count < 5:
        return {
            "checkpoint_id": str(checkpoint_id),
            "rows": rows,
            "reset_groups": reset_count,
            "num_skills": int(actor.n_skills),
            "thresholds": static_capacity_thresholds(),
            "status": "UNDERPOWERED",
            "reason": "at least five reset groups with snapshot rows are required",
        }
    if snapshots.observation.shape[1] != actor.obs_dim:
        raise ValueError("snapshot observation dimension does not match actor")
    if snapshots.actor_hidden.shape[1] != actor.hidden_dim:
        raise ValueError("snapshot hidden dimension does not match actor")

    device = actor.device
    num_skills = int(actor.n_skills)
    observations = torch.as_tensor(
        snapshots.observation, dtype=torch.float32, device=device
    ).repeat_interleave(num_skills, dim=0)
    skills = torch.arange(num_skills, device=device).repeat(rows)
    rollout_hidden = torch.as_tensor(
        snapshots.actor_hidden, dtype=torch.float32, device=device
    ).repeat_interleave(num_skills, dim=0)
    zero_hidden = torch.zeros_like(rollout_hidden)

    condition_reports: dict[str, dict[str, object]] = {}
    active_outputs: dict[str, ActorForwardBatch] = {}
    for offset, (name, hidden) in enumerate(
        (("zero_h", zero_hidden), ("rollout_h", rollout_hidden))
    ):
        active = forward_actor_snapshot(
            actor, observations, skills, hidden, inactive_film=False
        )
        inactive = forward_actor_snapshot(
            actor, observations, skills, hidden, inactive_film=True
        )
        active_outputs[name] = active
        try:
            condition_reports[name] = _condition_metrics(
                active,
                inactive,
                snapshots.reset_id,
                rows=rows,
                num_skills=num_skills,
                bootstrap_reps=int(bootstrap_reps),
                bootstrap_seed=int(bootstrap_seed) + offset,
            )
        except FloatingPointError as error:
            return {
                "checkpoint_id": str(checkpoint_id),
                "rows": rows,
                "reset_groups": reset_count,
                "num_skills": num_skills,
                "status": "INVALID",
                "reason": str(error),
            }

    try:
        parity = _parity_metrics(
            actor,
            observations,
            skills,
            rollout_hidden,
            active_outputs["rollout_h"],
        )
    except FloatingPointError as error:
        return {
            "checkpoint_id": str(checkpoint_id),
            "rows": rows,
            "reset_groups": reset_count,
            "num_skills": num_skills,
            "status": "INVALID",
            "reason": str(error),
        }
    inactive_max_skl = max(
        float(condition_reports[name]["inactive_max_abs_skl"])
        for name in condition_reports
    )
    inactive_max_distance = max(
        float(condition_reports[name]["inactive_max_stdmean_distance"])
        for name in condition_reports
    )
    zero_skl = float(condition_reports["zero_h"]["mean_skl"])
    rollout_skl = float(condition_reports["rollout_h"]["mean_skl"])
    retention = rollout_skl / max(zero_skl, INACTIVE_TOLERANCE)
    gamma_grid = active_outputs["zero_h"].gamma.reshape(
        rows, num_skills, actor.hidden_dim
    )
    beta_grid = active_outputs["zero_h"].beta.reshape(
        rows, num_skills, actor.hidden_dim
    )
    gamma_reference = gamma_grid[0]
    beta_reference = beta_grid[0]
    film_code_consistency_error = max(
        float(torch.max(torch.abs(gamma_grid - gamma_reference)).item()),
        float(torch.max(torch.abs(beta_grid - beta_reference)).item()),
    )
    invalid = bool(
        inactive_max_skl > INACTIVE_TOLERANCE
        or inactive_max_distance > INACTIVE_TOLERANCE
        or not parity["pass"]
        or film_code_consistency_error > PARITY_TOLERANCE
        or not all(bool(report["finite"]) for report in condition_reports.values())
    )
    status = (
        "INVALID"
        if invalid
        else (
            "PASS"
            if bool(condition_reports["zero_h"]["pass"])
            or bool(condition_reports["rollout_h"]["pass"])
            else "FAIL"
        )
    )
    return {
        "checkpoint_id": str(checkpoint_id),
        "rows": rows,
        "reset_groups": reset_count,
        "num_skills": num_skills,
        "zero_h": condition_reports["zero_h"],
        "rollout_h": condition_reports["rollout_h"],
        "hidden_retention_ratio": float(retention),
        "film_code_parameters": {
            "gamma_by_skill": gamma_reference.detach().cpu().tolist(),
            "beta_by_skill": beta_reference.detach().cpu().tolist(),
            "consistency_max_abs_error": film_code_consistency_error,
        },
        "inactive_control": {
            "max_abs_symmetric_kl": inactive_max_skl,
            "max_stdmean_distance": inactive_max_distance,
        },
        "parity": parity,
        "thresholds": static_capacity_thresholds(),
        "status": status,
    }


def gate_static_family(reports: list[dict[str, object]]) -> dict[str, object]:
    """Apply checkpoint-family stability and recurrent-washout rules."""

    if any(report.get("status") == "INVALID" for report in reports):
        return {
            "status": "INVALID",
            "zero_h_pass": False,
            "rollout_h_pass": False,
            "recurrent_washout": False,
        }
    valid = [
        report
        for report in reports
        if report.get("status") not in ("UNDERPOWERED", "INVALID")
    ]
    if len(valid) < 2:
        return {
            "status": "UNDERPOWERED",
            "zero_h_pass": False,
            "rollout_h_pass": False,
            "recurrent_washout": False,
        }
    zero_count = sum(bool(report["zero_h"]["pass"]) for report in valid)
    rollout_count = sum(bool(report["rollout_h"]["pass"]) for report in valid)
    zero_fail_count = len(valid) - zero_count
    rollout_fail_count = len(valid) - rollout_count
    washout_count = sum(
        bool(report["zero_h"]["pass"])
        and float(report["rollout_h"]["mean_skl"]) < STATIC_SKL_MIN
        and float(report["hidden_retention_ratio"])
        < RECURRENT_RETENTION_MAX
        for report in valid
    )
    def condition_status(pass_count: int, fail_count: int) -> str:
        if pass_count >= 2:
            return "PASS"
        if fail_count >= 2:
            return "FAIL"
        return "UNDERPOWERED"

    zero_status = condition_status(zero_count, zero_fail_count)
    rollout_status = condition_status(rollout_count, rollout_fail_count)
    zero_pass = zero_status == "PASS"
    rollout_pass = rollout_status == "PASS"
    family_status = (
        "UNDERPOWERED"
        if "UNDERPOWERED" in (zero_status, rollout_status)
        else ("PASS" if zero_pass or rollout_pass else "FAIL")
    )
    return {
        "status": family_status,
        "valid_checkpoints": len(valid),
        "zero_h_pass_count": zero_count,
        "zero_h_fail_count": zero_fail_count,
        "rollout_h_pass_count": rollout_count,
        "rollout_h_fail_count": rollout_fail_count,
        "washout_count": washout_count,
        "zero_h_status": zero_status,
        "rollout_h_status": rollout_status,
        "zero_h_pass": zero_pass,
        "rollout_h_pass": rollout_pass,
        "recurrent_washout": washout_count >= 2,
    }


def build_orthogonal_codebook(
    num_skills: int,
    action_dim: int,
    *,
    seed: int,
    norm: float,
) -> np.ndarray:
    """Build a fixed row-orthogonal codebook in raw action-mean space."""

    if int(num_skills) <= 1:
        raise ValueError("num_skills must be greater than one")
    if int(action_dim) <= 0:
        raise ValueError("action_dim must be positive")
    if int(num_skills) > int(action_dim):
        raise ValueError("orthogonal codebook requires num_skills <= action_dim")
    if not np.isfinite(norm) or float(norm) <= 0.0:
        raise ValueError("norm must be finite and positive")
    matrix = np.random.default_rng(int(seed)).normal(
        size=(int(action_dim), int(num_skills))
    )
    q, _ = np.linalg.qr(matrix)
    return (q[:, : int(num_skills)].T * float(norm)).astype(np.float32)


def _validate_synthetic_rows(rows: SyntheticRows) -> SyntheticRows:
    values = {
        field: np.asarray(getattr(rows, field))
        for field in SyntheticRows.__dataclass_fields__
    }
    count = int(values["true_skill"].reshape(-1).size)
    for field, value in values.items():
        if value.ndim == 0 or int(value.shape[0]) != count:
            raise ValueError(f"{field} must have {count} rows")
    if values["observation"].ndim != 2 or values["actor_hidden"].ndim != 2:
        raise ValueError("synthetic observations and hidden states must be rank-2")
    if not np.isfinite(values["observation"]).all():
        raise ValueError("synthetic observation contains non-finite values")
    if not np.isfinite(values["actor_hidden"]).all():
        raise ValueError("synthetic actor_hidden contains non-finite values")
    return SyntheticRows(
        observation=np.asarray(values["observation"], dtype=np.float32),
        actor_hidden=np.asarray(values["actor_hidden"], dtype=np.float32),
        true_skill=np.asarray(values["true_skill"], dtype=np.int64).reshape(-1),
        fake_skill=np.asarray(values["fake_skill"], dtype=np.int64).reshape(-1),
        reset_id=np.asarray(values["reset_id"], dtype=np.int64).reshape(-1),
    )


def build_balanced_synthetic_rows(
    batch: CapacitySnapshotBatch,
    indices: np.ndarray,
    num_skills: int,
    *,
    seed: int,
) -> SyntheticRows:
    """Cross each source snapshot with every true skill and a fake marginal."""

    if int(num_skills) <= 1:
        raise ValueError("num_skills must be greater than one")
    source = validate_capacity_snapshots(batch).take(
        np.asarray(indices, dtype=np.int64)
    )
    rows = int(source.reset_id.size)
    if rows == 0:
        raise ValueError("synthetic split cannot be empty")
    observations = np.repeat(source.observation, int(num_skills), axis=0)
    hidden = np.repeat(source.actor_hidden, int(num_skills), axis=0)
    reset_ids = np.repeat(source.reset_id, int(num_skills), axis=0)
    true_skill = np.tile(
        np.arange(int(num_skills), dtype=np.int64), rows
    )
    rng = np.random.default_rng(int(seed))
    fake_skill = np.concatenate(
        [rng.permutation(int(num_skills)) for _ in range(rows)]
    ).astype(np.int64)
    return _validate_synthetic_rows(
        SyntheticRows(
            observation=observations,
            actor_hidden=hidden,
            true_skill=true_skill,
            fake_skill=fake_skill,
            reset_id=reset_ids,
        )
    )


def _actor_raw_mean_for_training(
    actor: Any,
    observations: torch.Tensor,
    skills: torch.Tensor,
    actor_hidden: torch.Tensor,
) -> torch.Tensor:
    """Differentiable counterpart of the frozen active diagnostic forward."""

    _require_supported_actor(actor)
    obs = torch.as_tensor(
        observations, dtype=torch.float32, device=actor.device
    )
    skill = torch.as_tensor(skills, dtype=torch.long, device=actor.device)
    hidden = torch.as_tensor(
        actor_hidden, dtype=torch.float32, device=actor.device
    )
    base = actor.actor_base(obs)
    raw_film = actor.actor_film(
        F.one_hot(skill, num_classes=actor.n_skills).float()
    )
    gamma, beta = torch.chunk(raw_film, 2, dim=-1)
    film_feature = gamma * base + beta
    masks = torch.ones(
        obs.shape[0], 1, dtype=torch.float32, device=actor.device
    )
    post_gru, _ = actor.actor_rnn(film_feature, hidden, masks)
    return actor.actor_act.action_out._distribution(post_gru).mean


def _minibatch_schedule(
    row_count: int,
    config: SyntheticFitConfig,
    *,
    seed: int,
) -> tuple[np.ndarray, ...]:
    if int(row_count) <= 0:
        raise ValueError("row_count must be positive")
    if int(config.batch_size) <= 0 or int(config.max_steps) <= 0:
        raise ValueError("batch_size and max_steps must be positive")
    rng = np.random.default_rng(int(seed))
    batch_size = min(int(config.batch_size), int(row_count))
    return tuple(
        np.asarray(
            rng.choice(int(row_count), size=batch_size, replace=False),
            dtype=np.int64,
        )
        for _ in range(int(config.max_steps))
    )


def _actor_state_sha256(actor: Any) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(actor.state_dict().items()):
        if not name.startswith("actor_"):
            continue
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _actor_parameter_count(actor: Any) -> int:
    return int(sum(parameter.numel() for parameter in actor.actor_update_parameters()))


def _minibatch_schedule_sha256(schedule: tuple[np.ndarray, ...]) -> str:
    digest = hashlib.sha256()
    for indices in schedule:
        values = np.asarray(indices, dtype=np.int64)
        digest.update(np.asarray(values.shape, dtype=np.int64).tobytes())
        digest.update(values.tobytes())
    return digest.hexdigest()


def _array_payload_sha256(named_arrays: dict[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for name, array in sorted(named_arrays.items()):
        value = np.ascontiguousarray(np.asarray(array))
        digest.update(name.encode("utf-8"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(np.asarray(value.shape, dtype=np.int64).tobytes())
        digest.update(value.tobytes())
    return digest.hexdigest()


def _synthetic_rows_sha256(rows: SyntheticRows) -> str:
    return _array_payload_sha256(
        {
            field: np.asarray(getattr(rows, field))
            for field in SyntheticRows.__dataclass_fields__
        }
    )


def _synthetic_targets_sha256(
    codebook: np.ndarray, true_skill: np.ndarray
) -> str:
    targets = np.asarray(codebook, dtype=np.float32)[
        np.asarray(true_skill, dtype=np.int64)
    ]
    return _array_payload_sha256({"targets": targets})


def _optimizer_contract(optimizer: torch.optim.Optimizer) -> dict[str, object]:
    defaults = optimizer.defaults
    return {
        "class": f"{type(optimizer).__module__}.{type(optimizer).__qualname__}",
        "learning_rate": float(defaults["lr"]),
        "betas": [float(value) for value in defaults["betas"]],
        "eps": float(defaults["eps"]),
        "weight_decay": float(defaults["weight_decay"]),
        "amsgrad": bool(defaults["amsgrad"]),
        "maximize": bool(defaults.get("maximize", False)),
        "foreach": defaults.get("foreach"),
        "capturable": bool(defaults.get("capturable", False)),
        "differentiable": bool(defaults.get("differentiable", False)),
        "fused": defaults.get("fused"),
    }


def _synthetic_thresholds(num_skills: int) -> dict[str, object]:
    return synthetic_capacity_thresholds(num_skills)


def _decide_synthetic_seed_gate(
    *,
    active_accuracy: float,
    active_macro_f1: float,
    active_minus_sham_accuracy: float,
    bootstrap_lower: float,
    sham_accuracy: float,
    generalization_gap: float,
    evidence_finite: bool,
    control_contract_valid: bool,
    support_sufficient: bool,
    num_skills: int = 4,
) -> tuple[str, bool, list[str]]:
    """Apply the pre-registered seed gate with explicit precedence."""

    if not support_sufficient:
        return "UNDERPOWERED", False, ["bootstrap reset support is insufficient"]
    if not evidence_finite:
        return "INVALID", False, ["non-finite synthetic evidence"]
    if not control_contract_valid:
        return "INVALID", False, ["active/sham control contract failed"]

    checks = (
        (active_accuracy >= SYNTHETIC_ACCURACY_MIN, "active accuracy below threshold"),
        (active_macro_f1 >= SYNTHETIC_MACRO_F1_MIN, "active macro-F1 below threshold"),
        (
            active_minus_sham_accuracy >= SYNTHETIC_ACTIVE_MINUS_SHAM_MIN,
            "active-minus-sham accuracy below threshold",
        ),
        (bootstrap_lower > 0.0, "bootstrap lower bound is not positive"),
        (
            sham_accuracy <= 1.0 / int(num_skills) + SYNTHETIC_SHAM_MARGIN,
            "sham accuracy above threshold",
        ),
        (
            generalization_gap <= SYNTHETIC_GENERALIZATION_GAP_MAX,
            "train-minus-test accuracy above threshold",
        ),
    )
    reasons = [reason for passed, reason in checks if not passed]
    return ("PASS", True, []) if not reasons else ("FAIL", False, reasons)


def _synthetic_target(
    codebook: np.ndarray,
    true_skill: np.ndarray,
    device: torch.device,
) -> torch.Tensor:
    return torch.as_tensor(
        np.asarray(codebook, dtype=np.float32)[
            np.asarray(true_skill, dtype=np.int64)
        ],
        dtype=torch.float32,
        device=device,
    )


def _synthetic_loss(
    actor: Any,
    rows: SyntheticRows,
    input_label_field: str,
    codebook: np.ndarray,
    device: torch.device,
) -> torch.Tensor:
    labels = np.asarray(getattr(rows, input_label_field), dtype=np.int64)
    predicted = _actor_raw_mean_for_training(
        actor,
        torch.as_tensor(rows.observation, dtype=torch.float32, device=device),
        torch.as_tensor(labels, dtype=torch.long, device=device),
        torch.as_tensor(rows.actor_hidden, dtype=torch.float32, device=device),
    )
    return F.mse_loss(
        predicted, _synthetic_target(codebook, rows.true_skill, device)
    )


def fit_synthetic_clone(
    *,
    source_actor: Any,
    train: SyntheticRows,
    validation: SyntheticRows,
    input_label_field: str,
    codebook: np.ndarray,
    minibatches: tuple[np.ndarray, ...],
    config: SyntheticFitConfig,
    device: torch.device,
) -> dict[str, object]:
    """Fit one disposable actor clone using validation-only early stopping."""

    if input_label_field not in ("true_skill", "fake_skill"):
        raise ValueError("input_label_field must be true_skill or fake_skill")
    if int(config.validation_interval) <= 0 or int(config.patience) <= 0:
        raise ValueError("validation_interval and patience must be positive")
    train_rows = _validate_synthetic_rows(train)
    validation_rows = _validate_synthetic_rows(validation)
    clone = copy.deepcopy(source_actor).to(device)
    clone.device = torch.device(device)
    initial_actor_sha256 = _actor_state_sha256(clone)
    actor_parameter_count = _actor_parameter_count(clone)
    clone.train()
    optimizer = torch.optim.Adam(
        clone.actor_update_parameters(), lr=float(config.learning_rate)
    )
    optimizer_contract = _optimizer_contract(optimizer)
    minibatch_schedule_sha256 = _minibatch_schedule_sha256(minibatches)
    train_rows_sha256 = _synthetic_rows_sha256(train_rows)
    validation_rows_sha256 = _synthetic_rows_sha256(validation_rows)
    train_targets_sha256 = _synthetic_targets_sha256(
        codebook, train_rows.true_skill
    )
    validation_targets_sha256 = _synthetic_targets_sha256(
        codebook, validation_rows.true_skill
    )
    best_validation_loss = float("inf")
    best_step = 0
    best_state: dict[str, torch.Tensor] | None = None
    stale_checks = 0
    validation_evaluations = 0
    train_losses: list[float] = []
    validation_losses: list[dict[str, float | int]] = []

    for step, indices in enumerate(minibatches, start=1):
        if step > int(config.max_steps):
            break
        batch = train_rows.take(indices)
        optimizer.zero_grad(set_to_none=True)
        loss = _synthetic_loss(
            clone, batch, input_label_field, codebook, torch.device(device)
        )
        if not bool(torch.isfinite(loss).item()):
            raise FloatingPointError("non-finite synthetic training loss")
        loss.backward()
        optimizer.step()
        train_losses.append(float(loss.detach().item()))

        should_validate = (
            step % int(config.validation_interval) == 0
            or step == min(len(minibatches), int(config.max_steps))
        )
        if not should_validate:
            continue
        clone.eval()
        with torch.no_grad():
            validation_loss = float(
                _synthetic_loss(
                    clone,
                    validation_rows,
                    input_label_field,
                    codebook,
                    torch.device(device),
                ).item()
            )
        if not np.isfinite(validation_loss):
            raise FloatingPointError("non-finite synthetic validation loss")
        clone.train()
        validation_evaluations += 1
        validation_losses.append({"step": step, "loss": validation_loss})
        if validation_loss < best_validation_loss - float(config.min_delta):
            best_validation_loss = validation_loss
            best_step = step
            best_state = copy.deepcopy(clone.state_dict())
            stale_checks = 0
        else:
            stale_checks += 1
        if stale_checks >= int(config.patience):
            break

    if best_state is None:
        raise RuntimeError("synthetic fit performed no validation evaluation")
    clone.load_state_dict(best_state)
    clone.eval()
    return {
        "model": clone,
        "best_step": int(best_step),
        "best_validation_loss": float(best_validation_loss),
        "train_losses": train_losses,
        "validation_losses": validation_losses,
        "validation_evaluations": int(validation_evaluations),
        "initial_actor_sha256": initial_actor_sha256,
        "actor_parameter_count": actor_parameter_count,
        "optimizer_contract": optimizer_contract,
        "minibatch_schedule_sha256": minibatch_schedule_sha256,
        "train_rows_sha256": train_rows_sha256,
        "validation_rows_sha256": validation_rows_sha256,
        "train_targets_sha256": train_targets_sha256,
        "validation_targets_sha256": validation_targets_sha256,
    }


def _macro_f1(
    truth: np.ndarray, prediction: np.ndarray, num_skills: int
) -> float:
    scores: list[float] = []
    for skill in range(int(num_skills)):
        true_positive = int(np.sum((truth == skill) & (prediction == skill)))
        false_positive = int(np.sum((truth != skill) & (prediction == skill)))
        false_negative = int(np.sum((truth == skill) & (prediction != skill)))
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(0.0 if denominator == 0 else 2.0 * true_positive / denominator)
    return float(np.mean(scores))


def score_synthetic_clone(
    actor: Any,
    rows: SyntheticRows,
    *,
    input_label_field: str,
    codebook: np.ndarray,
    device: torch.device,
) -> SyntheticScore:
    values = _validate_synthetic_rows(rows)
    labels = np.asarray(getattr(values, input_label_field), dtype=np.int64)
    with torch.no_grad():
        predicted_mean = _actor_raw_mean_for_training(
            actor,
            torch.as_tensor(values.observation, dtype=torch.float32, device=device),
            torch.as_tensor(labels, dtype=torch.long, device=device),
            torch.as_tensor(values.actor_hidden, dtype=torch.float32, device=device),
        )
        target = _synthetic_target(codebook, values.true_skill, device)
        distances = torch.cdist(
            predicted_mean,
            torch.as_tensor(codebook, dtype=torch.float32, device=device),
        )
        prediction = distances.argmin(dim=1).cpu().numpy().astype(np.int64)
        mse = float(F.mse_loss(predicted_mean, target).item())
    if not (
        bool(torch.isfinite(predicted_mean).all().item())
        and bool(torch.isfinite(target).all().item())
        and bool(torch.isfinite(distances).all().item())
        and np.isfinite(mse)
    ):
        raise FloatingPointError("non-finite synthetic score")
    truth = np.asarray(values.true_skill, dtype=np.int64)
    correct = prediction == truth
    return SyntheticScore(
        accuracy=float(correct.mean()),
        macro_f1=_macro_f1(truth, prediction, int(codebook.shape[0])),
        target_mse=mse,
        correct=correct,
        predicted_skill=prediction,
        reset_id=np.asarray(values.reset_id, dtype=np.int64),
    )


def _synthetic_split_support(
    batch: CapacitySnapshotBatch, split: ResetSplit
) -> dict[str, int]:
    reset_ids = np.asarray(batch.reset_id, dtype=np.int64)

    def count_groups(indices: np.ndarray) -> int:
        values = np.asarray(indices, dtype=np.int64)
        return int(np.unique(reset_ids[values]).size) if values.size else 0

    return {
        "train_rows": int(np.asarray(split.train).size),
        "validation_rows": int(np.asarray(split.validation).size),
        "test_rows": int(np.asarray(split.test).size),
        "train_reset_groups": count_groups(split.train),
        "validation_reset_groups": count_groups(split.validation),
        "test_reset_groups": count_groups(split.test),
    }


def _terminal_synthetic_seed_report(
    *,
    seed: int,
    status: str,
    reasons: list[str],
    num_skills: int,
    source_actor_sha256_before: str,
    source_actor_sha256_after: str,
    source_actor_parameter_count: int,
    support: dict[str, int],
) -> dict[str, object]:
    return {
        "seed": int(seed),
        "status": status,
        "pass": False,
        "reasons": list(reasons),
        "support": dict(support),
        "source_actor_sha256_before": source_actor_sha256_before,
        "source_actor_sha256_after": source_actor_sha256_after,
        "source_actor_sha256_equal": source_actor_sha256_before
        == source_actor_sha256_after,
        "source_actor_parameter_count": int(source_actor_parameter_count),
        "thresholds": _synthetic_thresholds(num_skills),
    }


def _fit_evidence_is_finite(fit: dict[str, object]) -> bool:
    values = [float(fit["best_validation_loss"])]
    values.extend(float(value) for value in fit["train_losses"])
    values.extend(
        float(item["loss"]) for item in fit["validation_losses"]
    )
    return bool(np.isfinite(np.asarray(values, dtype=np.float64)).all())


def evaluate_synthetic_seed(
    source_actor: Any,
    batch: CapacitySnapshotBatch,
    split: ResetSplit,
    codebook: np.ndarray,
    *,
    seed: int,
    config: SyntheticFitConfig,
    device: torch.device,
    bootstrap_reps: int,
) -> dict[str, object]:
    """Run one paired active/fake-label capacity control seed."""

    num_skills = int(source_actor.n_skills)
    source_actor_sha256_before = _actor_state_sha256(source_actor)
    source_actor_parameter_count = _actor_parameter_count(source_actor)
    try:
        validated_batch = validate_capacity_snapshots(batch)
        support = _synthetic_split_support(validated_batch, split)
    except (IndexError, ValueError) as error:
        source_after = _actor_state_sha256(source_actor)
        return _terminal_synthetic_seed_report(
            seed=seed,
            status="INVALID",
            reasons=[f"invalid snapshot/split contract: {error}"],
            num_skills=num_skills,
            source_actor_sha256_before=source_actor_sha256_before,
            source_actor_sha256_after=source_after,
            source_actor_parameter_count=source_actor_parameter_count,
            support={},
        )

    support_sufficient = bool(
        support["train_rows"] > 0
        and support["validation_rows"] > 0
        and support["test_rows"] > 0
        and support["test_reset_groups"] >= MIN_BOOTSTRAP_RESET_GROUPS
    )
    if not support_sufficient:
        return _terminal_synthetic_seed_report(
            seed=seed,
            status="UNDERPOWERED",
            reasons=[
                f"bootstrap requires at least {MIN_BOOTSTRAP_RESET_GROUPS} test reset groups"
            ],
            num_skills=num_skills,
            source_actor_sha256_before=source_actor_sha256_before,
            source_actor_sha256_after=_actor_state_sha256(source_actor),
            source_actor_parameter_count=source_actor_parameter_count,
            support=support,
        )

    codebook_values = np.asarray(codebook, dtype=np.float32)
    expected_codebook_shape = (num_skills, int(source_actor.action_dim))
    if (
        codebook_values.shape != expected_codebook_shape
        or not np.isfinite(codebook_values).all()
    ):
        return _terminal_synthetic_seed_report(
            seed=seed,
            status="INVALID",
            reasons=[
                "codebook shape or finite-value contract failed: "
                f"expected {expected_codebook_shape}, got {codebook_values.shape}"
            ],
            num_skills=num_skills,
            source_actor_sha256_before=source_actor_sha256_before,
            source_actor_sha256_after=_actor_state_sha256(source_actor),
            source_actor_parameter_count=source_actor_parameter_count,
            support=support,
        )

    try:
        train = build_balanced_synthetic_rows(
            validated_batch, split.train, num_skills, seed=int(seed) + 100
        )
        validation = build_balanced_synthetic_rows(
            validated_batch, split.validation, num_skills, seed=int(seed) + 200
        )
        test = build_balanced_synthetic_rows(
            validated_batch, split.test, num_skills, seed=int(seed) + 300
        )
    except ValueError as error:
        return _terminal_synthetic_seed_report(
            seed=seed,
            status="INVALID",
            reasons=[f"invalid balanced synthetic rows: {error}"],
            num_skills=num_skills,
            source_actor_sha256_before=source_actor_sha256_before,
            source_actor_sha256_after=_actor_state_sha256(source_actor),
            source_actor_parameter_count=source_actor_parameter_count,
            support=support,
        )

    minibatches = _minibatch_schedule(
        train.true_skill.size, config, seed=int(seed) + 400
    )
    schedule_sha256 = _minibatch_schedule_sha256(minibatches)
    source_actor_sha256_after_active = source_actor_sha256_before
    source_actor_sha256_after = source_actor_sha256_before
    try:
        active_fit = fit_synthetic_clone(
            source_actor=source_actor,
            train=train,
            validation=validation,
            input_label_field="true_skill",
            codebook=codebook_values,
            minibatches=minibatches,
            config=config,
            device=device,
        )
        source_actor_sha256_after_active = _actor_state_sha256(source_actor)
        sham_fit = fit_synthetic_clone(
            source_actor=source_actor,
            train=train,
            validation=validation,
            input_label_field="fake_skill",
            codebook=codebook_values,
            minibatches=minibatches,
            config=config,
            device=device,
        )
        source_actor_sha256_after = _actor_state_sha256(source_actor)
        active_train = score_synthetic_clone(
            active_fit["model"],
            train,
            input_label_field="true_skill",
            codebook=codebook_values,
            device=device,
        )
        active_test = score_synthetic_clone(
            active_fit["model"],
            test,
            input_label_field="true_skill",
            codebook=codebook_values,
            device=device,
        )
        sham_test = score_synthetic_clone(
            sham_fit["model"],
            test,
            input_label_field="fake_skill",
            codebook=codebook_values,
            device=device,
        )
        interval = cluster_bootstrap_difference(
            active_test.correct.astype(np.float64),
            sham_test.correct.astype(np.float64),
            active_test.reset_id,
            reps=int(bootstrap_reps),
            seed=int(seed) + 500,
        )
    except FloatingPointError as error:
        source_actor_sha256_after = _actor_state_sha256(source_actor)
        return _terminal_synthetic_seed_report(
            seed=seed,
            status="INVALID",
            reasons=[f"non-finite synthetic evidence: {error}"],
            num_skills=num_skills,
            source_actor_sha256_before=source_actor_sha256_before,
            source_actor_sha256_after=source_actor_sha256_after,
            source_actor_parameter_count=source_actor_parameter_count,
            support=support,
        )

    accuracy_difference = active_test.accuracy - sham_test.accuracy
    generalization_gap = active_train.accuracy - active_test.accuracy
    source_immutable = bool(
        source_actor_sha256_before
        == source_actor_sha256_after_active
        == source_actor_sha256_after
    )
    initialization_equal = bool(
        active_fit["initial_actor_sha256"]
        == sham_fit["initial_actor_sha256"]
        == source_actor_sha256_before
    )
    parameter_count_equal = bool(
        int(active_fit["actor_parameter_count"])
        == int(sham_fit["actor_parameter_count"])
        == source_actor_parameter_count
    )
    schedule_equal = bool(
        active_fit["minibatch_schedule_sha256"]
        == sham_fit["minibatch_schedule_sha256"]
        == schedule_sha256
    )
    optimizer_equal = bool(
        active_fit["optimizer_contract"] == sham_fit["optimizer_contract"]
    )
    train_rows_equal = bool(
        active_fit["train_rows_sha256"] == sham_fit["train_rows_sha256"]
    )
    validation_rows_equal = bool(
        active_fit["validation_rows_sha256"]
        == sham_fit["validation_rows_sha256"]
    )
    train_targets_equal = bool(
        active_fit["train_targets_sha256"]
        == sham_fit["train_targets_sha256"]
    )
    validation_targets_equal = bool(
        active_fit["validation_targets_sha256"]
        == sham_fit["validation_targets_sha256"]
    )
    control_contract_valid = bool(
        source_immutable
        and initialization_equal
        and parameter_count_equal
        and schedule_equal
        and optimizer_equal
        and train_rows_equal
        and validation_rows_equal
        and train_targets_equal
        and validation_targets_equal
    )
    evidence_values = np.asarray(
        [
            active_train.accuracy,
            active_train.macro_f1,
            active_train.target_mse,
            active_test.accuracy,
            active_test.macro_f1,
            active_test.target_mse,
            sham_test.accuracy,
            sham_test.macro_f1,
            sham_test.target_mse,
            accuracy_difference,
            generalization_gap,
            interval.mean,
            interval.lower,
            interval.upper,
        ],
        dtype=np.float64,
    )
    evidence_finite = bool(
        np.isfinite(evidence_values).all()
        and _fit_evidence_is_finite(active_fit)
        and _fit_evidence_is_finite(sham_fit)
    )
    status, passed, reasons = _decide_synthetic_seed_gate(
        active_accuracy=active_test.accuracy,
        active_macro_f1=active_test.macro_f1,
        active_minus_sham_accuracy=accuracy_difference,
        bootstrap_lower=interval.lower,
        sham_accuracy=sham_test.accuracy,
        generalization_gap=generalization_gap,
        evidence_finite=evidence_finite,
        control_contract_valid=control_contract_valid,
        support_sufficient=support_sufficient,
        num_skills=num_skills,
    )
    if not source_immutable:
        reasons.insert(0, "source actor changed during disposable clone fitting")
    if not initialization_equal:
        reasons.append("active/sham initialization mismatch")
    if not parameter_count_equal:
        reasons.append("active/sham parameter-count mismatch")
    if not schedule_equal:
        reasons.append("active/sham minibatch-schedule mismatch")
    if not optimizer_equal:
        reasons.append("active/sham optimizer mismatch")
    if not (train_rows_equal and validation_rows_equal):
        reasons.append("active/sham row-set mismatch")
    if not (train_targets_equal and validation_targets_equal):
        reasons.append("active/sham target-row mismatch")
    return {
        "seed": int(seed),
        "status": status,
        "pass": passed,
        "reasons": reasons,
        "support": support,
        "evidence_finite": evidence_finite,
        "control_contract_valid": control_contract_valid,
        "synthetic_code_accuracy": active_test.accuracy,
        "synthetic_code_macro_f1": active_test.macro_f1,
        "synthetic_target_mse": active_test.target_mse,
        "synthetic_train_accuracy": active_train.accuracy,
        "sham_accuracy": sham_test.accuracy,
        "synthetic_active_minus_sham_accuracy": accuracy_difference,
        "synthetic_train_minus_test_accuracy": generalization_gap,
        "active_minus_sham_bootstrap": _bootstrap_dict(interval),
        "active_best_step": int(active_fit["best_step"]),
        "sham_best_step": int(sham_fit["best_step"]),
        "validation_evaluations": {
            "active": int(active_fit["validation_evaluations"]),
            "sham": int(sham_fit["validation_evaluations"]),
        },
        "test_evaluations": {"active": 1, "sham": 1},
        "initial_actor_sha256": source_actor_sha256_before,
        "source_actor_sha256_before": source_actor_sha256_before,
        "source_actor_sha256_after_active_fit": source_actor_sha256_after_active,
        "source_actor_sha256_after": source_actor_sha256_after,
        "source_actor_sha256_equal": source_immutable,
        "active_initial_actor_sha256": active_fit["initial_actor_sha256"],
        "sham_initial_actor_sha256": sham_fit["initial_actor_sha256"],
        "active_sham_initialization_equal": initialization_equal,
        "source_actor_parameter_count": source_actor_parameter_count,
        "active_actor_parameter_count": int(active_fit["actor_parameter_count"]),
        "sham_actor_parameter_count": int(sham_fit["actor_parameter_count"]),
        "active_sham_parameter_count_equal": parameter_count_equal,
        "minibatch_schedule_sha256": schedule_sha256,
        "active_minibatch_schedule_sha256": active_fit[
            "minibatch_schedule_sha256"
        ],
        "sham_minibatch_schedule_sha256": sham_fit[
            "minibatch_schedule_sha256"
        ],
        "active_sham_shared_minibatch_schedule": schedule_equal,
        "active_optimizer_contract": active_fit["optimizer_contract"],
        "sham_optimizer_contract": sham_fit["optimizer_contract"],
        "active_train_rows_sha256": active_fit["train_rows_sha256"],
        "sham_train_rows_sha256": sham_fit["train_rows_sha256"],
        "active_validation_rows_sha256": active_fit[
            "validation_rows_sha256"
        ],
        "sham_validation_rows_sha256": sham_fit[
            "validation_rows_sha256"
        ],
        "active_train_targets_sha256": active_fit["train_targets_sha256"],
        "sham_train_targets_sha256": sham_fit["train_targets_sha256"],
        "active_validation_targets_sha256": active_fit[
            "validation_targets_sha256"
        ],
        "sham_validation_targets_sha256": sham_fit[
            "validation_targets_sha256"
        ],
        "thresholds": _synthetic_thresholds(num_skills),
    }


def gate_synthetic_family(
    seed_reports: list[dict[str, object]],
) -> dict[str, object]:
    if any(report.get("status") == "INVALID" for report in seed_reports):
        return {
            "status": "INVALID",
            "pass": False,
            "passing_seeds": 0,
            "failed_seeds": 0,
        }
    valid = [
        report
        for report in seed_reports
        if report.get("status") not in ("UNDERPOWERED", "INVALID")
    ]
    passing = sum(bool(report.get("pass")) for report in valid)
    failed = sum(not bool(report.get("pass")) for report in valid)
    if passing >= 2:
        status = "PASS"
    elif failed >= 2:
        status = "FAIL"
    else:
        status = "UNDERPOWERED"
    return {
        "status": status,
        "pass": status == "PASS",
        "passing_seeds": passing,
        "failed_seeds": failed,
        "valid_seeds": len(valid),
    }


def classify_capacity_autopsy(
    static_family: dict[str, object],
    synthetic_family: dict[str, object],
) -> dict[str, object]:
    """Emit one pre-registered R27-G1 root-cause classification."""

    if (
        static_family.get("status") == "INVALID"
        or synthetic_family.get("status") == "INVALID"
    ):
        return {
            "classification": "INVALID",
            "reasons": ["instrument contract failed"],
        }
    if (
        static_family.get("status") == "UNDERPOWERED"
        or synthetic_family.get("status") == "UNDERPOWERED"
    ):
        return {
            "classification": "UNDERPOWERED",
            "reasons": ["family support is insufficient"],
        }
    if bool(synthetic_family.get("pass")) and bool(
        static_family.get("recurrent_washout")
    ):
        return {
            "classification": "RECURRENT_WASHOUT",
            "reasons": [
                "zero-h capacity is lost under rollout hidden state"
            ],
        }
    if bool(synthetic_family.get("pass")) and bool(
        static_family.get("rollout_h_pass")
    ):
        return {
            "classification": "STATIC_USED_OBSERVATIONAL_MISS",
            "reasons": [
                "trained actor has immediate z-conditioned action separation"
            ],
        }
    if bool(synthetic_family.get("pass")) and not bool(
        static_family.get("rollout_h_pass")
    ):
        return {
            "classification": "CAPACITY_PRESENT_OBJECTIVE_MISSING",
            "reasons": [
                "clone learns the code but trained actor does not use it"
            ],
        }
    if int(synthetic_family.get("failed_seeds", 0)) >= 2:
        return {
            "classification": "STATIC_PATH_CAPACITY_WEAK",
            "reasons": ["active clone fails the fixed synthetic gate"],
        }
    return {
        "classification": "UNDERPOWERED",
        "reasons": ["no classification has two-of-three support"],
    }
