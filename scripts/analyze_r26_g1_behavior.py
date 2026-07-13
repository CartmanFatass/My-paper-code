"""Held-out R26-G1a individual-skill behavior screening analyzer."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Mapping

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ha_ctse_process.r26_g1_dataset import (  # noqa: E402
    G1DataError,
    G1WindowBatch,
    SplitIndices,
    grouped_reset_split,
    read_g1_window_shards,
)


VARIANTS = (
    "real",
    "shuffled",
    "fake_marginal",
    "agent_matched",
    "duration_matched",
    "agent_duration_matched",
    "pre_only",
    "action_only",
    "effect_only",
    "context_only",
)
MATCHED_NULLS = ("agent_matched", "duration_matched", "agent_duration_matched")
KINDS = ("behavior", "prior", "full")
EARLY_STOP_MIN_DELTA = 1e-4
OVERFIT_ACCURACY_GAP = 0.20


def _threshold_metadata() -> dict[str, object]:
    return {
        "normalized_label_entropy_min": 0.8,
        "accuracy_gain_min": 0.05,
        "matched_null_difference": "> 0.0",
        "matched_null_bootstrap_lower": "> 0.0",
        "overfit_train_minus_test_accuracy": "> 0.20",
        "early_stop_min_delta": EARLY_STOP_MIN_DELTA,
    }


class AnalysisInvalidError(ValueError):
    """Analysis failure carrying checkpoint-row audit context."""

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        rows: list[dict[str, object]] | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.rows = [] if rows is None else rows

    def as_dict(self) -> dict[str, object]:
        return {
            "type": type(self).__name__,
            "message": str(self),
            "stage": self.stage,
            "rows": self.rows,
        }


@dataclass(frozen=True)
class FitConfig:
    max_steps: int = 1000
    patience: int = 20
    hidden_dim: int = 128
    lr: float = 3e-3
    validation_interval: int = 5


@dataclass(frozen=True)
class FitResult:
    model: torch.nn.Module
    best_step: int
    train_loss: float
    validation_loss: float


@dataclass(frozen=True)
class Score:
    accuracy: float
    macro_f1: float
    cross_entropy: float
    true_log_prob: np.ndarray
    correct: np.ndarray


@dataclass(frozen=True)
class BootstrapInterval:
    mean: float
    lower: float
    upper: float


@dataclass(frozen=True)
class GateDecision:
    status: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class VariantSplitBatches:
    train: G1WindowBatch
    validation: G1WindowBatch
    test: G1WindowBatch
    unchanged_fractions: dict[str, float]
    seeds: dict[str, int]

    @property
    def unchanged_fraction(self) -> float:
        batches = (self.train, self.validation, self.test)
        names = ("train", "validation", "test")
        rows = np.asarray([batch.label.size for batch in batches], dtype=np.float64)
        if float(rows.sum()) == 0.0:
            return 1.0
        values = np.asarray(
            [self.unchanged_fractions[name] for name in names], dtype=np.float64
        )
        return float(np.sum(rows * values) / rows.sum())


class _Classifier(torch.nn.Module):
    def __init__(
        self,
        *,
        kind: str,
        action_dim: int,
        effect_dim: int,
        context_dim: int,
        hidden_dim: int,
        num_skills: int,
    ) -> None:
        super().__init__()
        if kind not in KINDS:
            raise ValueError(f"unknown classifier kind: {kind}")
        self.kind = kind
        self.num_skills = int(num_skills)
        self.action_encoder = torch.nn.Sequential(
            torch.nn.Linear(int(action_dim), int(hidden_dim)), torch.nn.ReLU()
        )
        self.effect_encoder = torch.nn.Sequential(
            torch.nn.Linear(int(effect_dim), int(hidden_dim)), torch.nn.ReLU()
        )
        self.context_encoder = torch.nn.Sequential(
            torch.nn.Linear(int(context_dim), int(hidden_dim)), torch.nn.ReLU()
        )
        stream_count = {"behavior": 2, "prior": 1, "full": 3}[kind]
        self.head = torch.nn.Sequential(
            torch.nn.Linear(stream_count * int(hidden_dim), int(hidden_dim)),
            torch.nn.ReLU(),
            torch.nn.Linear(int(hidden_dim), int(num_skills)),
        )

    def forward(
        self,
        action: torch.Tensor,
        effect: torch.Tensor,
        context: torch.Tensor,
    ) -> torch.Tensor:
        streams: list[torch.Tensor] = []
        if self.kind in ("behavior", "full"):
            streams.extend(
                [self.action_encoder(action), self.effect_encoder(effect)]
            )
        if self.kind in ("prior", "full"):
            streams.append(self.context_encoder(context))
        return self.head(torch.cat(streams, dim=1))


def _matrix(values: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a two-dimensional matrix")
    if array.shape[0] == 0:
        raise ValueError(f"{name} must contain at least one row")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains non-finite values")
    return array


def _batch_arrays(
    batch: G1WindowBatch,
    *,
    num_skills: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    action = _matrix(batch.post_action, "post_action")
    effect = _matrix(batch.post_effect, "post_effect")
    context = _matrix(batch.prior_context, "prior_context")
    labels = np.asarray(batch.label, dtype=np.int64).reshape(-1)
    rows = int(labels.size)
    for name, values in (
        ("post_action", action),
        ("post_effect", effect),
        ("prior_context", context),
    ):
        if int(values.shape[0]) != rows:
            raise ValueError(f"{name} has {values.shape[0]} rows, expected {rows}")
    if np.any(labels < 0) or np.any(labels >= int(num_skills)):
        raise ValueError("label lies outside [0, num_skills)")
    return action, effect, context, labels


def _analysis_row_identities(
    batch: G1WindowBatch,
    indices: np.ndarray,
) -> list[dict[str, object]]:
    fields = (
        "reset_id",
        "reset_seed",
        "episode_id",
        "env_id",
        "agent_id",
        "checkpoint_id",
        "checkpoint_update",
    )
    arrays = {
        field: np.asarray(getattr(batch, field)).reshape(-1) for field in fields
    }
    rows: list[dict[str, object]] = []
    for row_index in np.asarray(indices, dtype=np.int64).reshape(-1):
        row: dict[str, object] = {"row_index": int(row_index)}
        for field, values in arrays.items():
            value = values[int(row_index)]
            row[field] = str(value) if field == "checkpoint_id" else int(value)
        rows.append(row)
    return rows


def _finite_loss(
    losses: torch.Tensor,
    *,
    stage: str,
    batch: G1WindowBatch,
) -> torch.Tensor:
    non_finite = (
        torch.nonzero(~torch.isfinite(losses), as_tuple=False)
        .reshape(-1)
        .detach()
        .cpu()
        .numpy()
    )
    if non_finite.size:
        display_stage = stage.replace("_", " ")
        raise AnalysisInvalidError(
            f"{display_stage} is non-finite",
            stage=stage,
            rows=_analysis_row_identities(batch, non_finite),
        )
    reduced = losses.mean()
    if not bool(torch.isfinite(reduced).item()):
        display_stage = stage.replace("_", " ")
        raise AnalysisInvalidError(
            f"{display_stage} is non-finite after reduction",
            stage=stage,
            rows=_analysis_row_identities(batch, np.arange(losses.numel())),
        )
    return reduced


def _tensor(values: np.ndarray, device: torch.device, dtype: torch.dtype) -> torch.Tensor:
    return torch.as_tensor(values, dtype=dtype, device=device).detach()


def _model_logits(
    model: torch.nn.Module,
    batch: G1WindowBatch,
) -> tuple[torch.Tensor, torch.Tensor]:
    if not isinstance(model, _Classifier):
        raise TypeError("model must be an R26-G1a classifier")
    device = next(model.parameters()).device
    action, effect, context, labels = _batch_arrays(
        batch, num_skills=model.num_skills
    )
    logits = model(
        _tensor(action, device, torch.float32),
        _tensor(effect, device, torch.float32),
        _tensor(context, device, torch.float32),
    )
    return logits, _tensor(labels, device, torch.long)


def fit_classifier(
    *,
    kind: str,
    train: G1WindowBatch,
    validation: G1WindowBatch,
    num_skills: int,
    config: FitConfig,
    device: torch.device,
    seed: int,
) -> FitResult:
    """Fit from train/validation only and restore the best validation state."""
    if kind not in KINDS:
        raise ValueError(f"unknown classifier kind: {kind}")
    if int(num_skills) < 2:
        raise ValueError("num_skills must be at least two")
    if min(
        int(config.max_steps),
        int(config.patience),
        int(config.hidden_dim),
        int(config.validation_interval),
    ) <= 0:
        raise ValueError("fit step, patience, width, and interval must be positive")
    if float(config.lr) <= 0.0:
        raise ValueError("learning rate must be positive")

    torch.manual_seed(int(seed))
    if device.type == "cuda":
        torch.cuda.manual_seed_all(int(seed))
    train_arrays = _batch_arrays(train, num_skills=int(num_skills))
    validation_arrays = _batch_arrays(validation, num_skills=int(num_skills))
    for index, name in enumerate(("post_action", "post_effect", "prior_context")):
        if train_arrays[index].shape[1] != validation_arrays[index].shape[1]:
            raise ValueError(f"train/validation {name} dimensions differ")

    model = _Classifier(
        kind=kind,
        action_dim=int(train_arrays[0].shape[1]),
        effect_dim=int(train_arrays[1].shape[1]),
        context_dim=int(train_arrays[2].shape[1]),
        hidden_dim=int(config.hidden_dim),
        num_skills=int(num_skills),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(config.lr))
    best_loss = float("inf")
    best_step = 0
    best_state: dict[str, torch.Tensor] | None = None
    stale_checks = 0

    for step in range(1, int(config.max_steps) + 1):
        model.train()
        optimizer.zero_grad(set_to_none=True)
        train_logits, train_labels = _model_logits(model, train)
        loss = _finite_loss(
            torch.nn.functional.cross_entropy(
                train_logits, train_labels, reduction="none"
            ),
            stage="training_loss",
            batch=train,
        )
        loss.backward()
        optimizer.step()

        should_validate = (
            step % int(config.validation_interval) == 0
            or step == int(config.max_steps)
        )
        if not should_validate:
            continue
        model.eval()
        with torch.no_grad():
            validation_logits, validation_labels = _model_logits(model, validation)
            validation_loss = float(
                _finite_loss(
                    torch.nn.functional.cross_entropy(
                        validation_logits, validation_labels, reduction="none"
                    ),
                    stage="validation_loss",
                    batch=validation,
                ).item()
            )
        if validation_loss < best_loss - EARLY_STOP_MIN_DELTA:
            best_loss = validation_loss
            best_step = step
            best_state = copy.deepcopy(model.state_dict())
            stale_checks = 0
        else:
            stale_checks += 1
            if stale_checks >= int(config.patience):
                break

    if best_state is None:
        raise RuntimeError("validation never produced a finite model state")
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        train_logits, train_labels = _model_logits(model, train)
        restored_train_loss = float(
            _finite_loss(
                torch.nn.functional.cross_entropy(
                    train_logits, train_labels, reduction="none"
                ),
                stage="restored_training_loss",
                batch=train,
            ).item()
        )
    return FitResult(
        model=model,
        best_step=int(best_step),
        train_loss=restored_train_loss,
        validation_loss=float(best_loss),
    )


def score_classifier(
    model: torch.nn.Module,
    kind: str,
    batch: G1WindowBatch,
) -> Score:
    """Score a held-out batch without updating or selecting the fitted model."""
    if not isinstance(model, _Classifier) or model.kind != kind:
        raise ValueError("score kind must match the fitted classifier kind")
    model.eval()
    with torch.no_grad():
        logits, labels = _model_logits(model, batch)
        log_probabilities = torch.nn.functional.log_softmax(logits, dim=1)
        predictions = torch.argmax(log_probabilities, dim=1)
        row_ids = torch.arange(labels.shape[0], device=labels.device)
        true_log_prob = log_probabilities[row_ids, labels]
    labels_np = labels.cpu().numpy()
    predictions_np = predictions.cpu().numpy()
    correct = predictions_np == labels_np
    f1_values: list[float] = []
    for label in range(model.num_skills):
        true_positive = int(np.sum((predictions_np == label) & (labels_np == label)))
        false_positive = int(np.sum((predictions_np == label) & (labels_np != label)))
        false_negative = int(np.sum((predictions_np != label) & (labels_np == label)))
        denominator = 2 * true_positive + false_positive + false_negative
        f1_values.append(0.0 if denominator == 0 else 2 * true_positive / denominator)
    true_log_prob_np = true_log_prob.cpu().numpy().astype(np.float64, copy=False)
    return Score(
        accuracy=float(correct.mean()),
        macro_f1=float(np.mean(f1_values)),
        cross_entropy=float(-true_log_prob_np.mean()),
        true_log_prob=true_log_prob_np,
        correct=correct,
    )


def _shuffle_within(
    labels: np.ndarray,
    groups: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    group_matrix = np.asarray(groups).reshape(labels.shape[0], -1)
    shuffled = labels.copy()
    for group in np.unique(group_matrix, axis=0):
        indices = np.flatnonzero(np.all(group_matrix == group, axis=1))
        if indices.size > 1:
            shuffled[indices] = labels[indices[rng.permutation(indices.size)]]
    return shuffled


def variant_batch(
    batch: G1WindowBatch,
    variant: str,
    seed: int,
) -> tuple[G1WindowBatch, float]:
    if variant not in VARIANTS:
        raise ValueError(f"unknown R26-G1a variant: {variant}")
    rng = np.random.default_rng(int(seed))
    original_labels = np.asarray(batch.label, dtype=np.int64).reshape(-1)
    labels = original_labels.copy()
    post_action = np.asarray(batch.post_action, dtype=np.float32).copy()
    post_effect = np.asarray(batch.post_effect, dtype=np.float32).copy()

    if variant == "shuffled":
        labels = labels[rng.permutation(labels.size)]
    elif variant == "fake_marginal":
        values, counts = np.unique(labels, return_counts=True)
        labels = rng.choice(values, size=labels.size, p=counts / counts.sum())
    elif variant == "agent_matched":
        labels = _shuffle_within(labels, batch.agent_id, rng)
    elif variant == "duration_matched":
        labels = _shuffle_within(labels, batch.duration_idx, rng)
    elif variant == "agent_duration_matched":
        groups = np.stack([batch.agent_id, batch.duration_idx], axis=1)
        labels = _shuffle_within(labels, groups, rng)
    elif variant == "pre_only":
        pre_action = np.asarray(batch.pre_action, dtype=np.float32)
        pre_effect = np.asarray(batch.pre_effect, dtype=np.float32)
        if pre_action.shape != post_action.shape or pre_effect.shape != post_effect.shape:
            raise ValueError("pre/post feature dimensions must match for pre_only")
        post_action = pre_action.copy()
        post_effect = pre_effect.copy()
    elif variant == "action_only":
        post_effect = np.zeros_like(post_effect)
    elif variant == "effect_only":
        post_action = np.zeros_like(post_action)

    unchanged_fraction = (
        1.0 if labels.size == 0 else float(np.mean(labels == original_labels))
    )
    return (
        replace(
            batch,
            label=np.asarray(labels, dtype=np.int64),
            post_action=post_action,
            post_effect=post_effect,
        ),
        unchanged_fraction,
    )


def _variant_split_seed(seed: int, variant: str, split_name: str) -> int:
    variant_index = VARIANTS.index(variant) + 1
    split_index = ("train", "validation", "test").index(split_name) + 1
    return int(
        (int(seed) + 1_000_003 * variant_index + 10_007 * split_index) % (2**32)
    )


def _transform_split_batches(
    train: G1WindowBatch,
    validation: G1WindowBatch,
    test: G1WindowBatch,
    variant: str,
    seed: int,
) -> VariantSplitBatches:
    transformed: dict[str, G1WindowBatch] = {}
    unchanged: dict[str, float] = {}
    seeds: dict[str, int] = {}
    for split_name, split_batch in (
        ("train", train),
        ("validation", validation),
        ("test", test),
    ):
        split_seed = _variant_split_seed(seed, variant, split_name)
        transformed[split_name], unchanged[split_name] = variant_batch(
            split_batch, variant, split_seed
        )
        seeds[split_name] = split_seed
    return VariantSplitBatches(
        train=transformed["train"],
        validation=transformed["validation"],
        test=transformed["test"],
        unchanged_fractions=unchanged,
        seeds=seeds,
    )


def variant_split_batches(
    batch: G1WindowBatch,
    split: SplitIndices,
    variant: str,
    seed: int,
) -> VariantSplitBatches:
    """Apply a variant independently after the fixed reset split is known."""
    return _transform_split_batches(
        batch.take(split.train),
        batch.take(split.validation),
        batch.take(split.test),
        variant,
        seed,
    )


def cluster_bootstrap_difference(
    real: np.ndarray,
    null: np.ndarray,
    reset_ids: np.ndarray,
    *,
    reps: int,
    seed: int,
) -> BootstrapInterval:
    real_values = np.asarray(real, dtype=np.float64).reshape(-1)
    null_values = np.asarray(null, dtype=np.float64).reshape(-1)
    groups = np.asarray(reset_ids, dtype=np.int64).reshape(-1)
    if real_values.size == 0 or not (
        real_values.size == null_values.size == groups.size
    ):
        raise ValueError("bootstrap arrays must have the same non-zero row count")
    if not np.isfinite(real_values).all() or not np.isfinite(null_values).all():
        raise ValueError("bootstrap values must be finite")
    if int(reps) <= 0:
        raise ValueError("bootstrap reps must be positive")
    unique_groups = np.unique(groups)
    row_groups = [np.flatnonzero(groups == group) for group in unique_groups]
    differences = real_values - null_values
    rng = np.random.default_rng(int(seed))
    samples = np.empty(int(reps), dtype=np.float64)
    for rep in range(int(reps)):
        selected = rng.integers(0, len(row_groups), size=len(row_groups))
        sampled_rows = np.concatenate([row_groups[index] for index in selected])
        samples[rep] = float(differences[sampled_rows].mean())
    lower, upper = np.quantile(samples, [0.025, 0.975])
    return BootstrapInterval(
        mean=float(differences.mean()), lower=float(lower), upper=float(upper)
    )


def _bootstrap_lower(value: object) -> float:
    if isinstance(value, BootstrapInterval):
        return float(value.lower)
    if isinstance(value, Mapping):
        return float(value["lower"])
    raise TypeError("bootstrap interval must be a BootstrapInterval or mapping")


def gate_checkpoint(result: Mapping[str, object]) -> GateDecision:
    if not bool(result.get("valid", True)):
        return GateDecision("INVALID", ("checkpoint analysis is invalid",))
    if bool(result.get("underpowered", False)):
        return GateDecision("UNDERPOWERED", ("a required split lacks label support",))
    if bool(result.get("overfit_warning", False)):
        return GateDecision("INVALID", ("train/test overfit warning invalidates the read",))

    reasons: list[str] = []
    entropy = float(result.get("normalized_label_entropy", float("nan")))
    full_gain = float(result.get("full_minus_prior_accuracy", float("nan")))
    post_gain = float(
        result.get("behavior_post_minus_pre_accuracy", float("nan"))
    )
    if not np.isfinite([entropy, full_gain, post_gain]).all():
        return GateDecision("INVALID", ("a required gate metric is non-finite",))
    if entropy < 0.8:
        reasons.append(f"normalized label entropy {entropy:.6f} is below 0.8")
    if full_gain < 0.05:
        reasons.append(f"full-minus-prior accuracy {full_gain:.6f} is below 0.05")
    if post_gain < 0.05:
        reasons.append(f"post-minus-pre accuracy {post_gain:.6f} is below 0.05")

    matched = result.get("matched_nulls")
    if not isinstance(matched, Mapping) or any(name not in matched for name in MATCHED_NULLS):
        return GateDecision("INVALID", ("matched-null evidence is incomplete",))
    null_differences: dict[str, float] = {}
    for name in MATCHED_NULLS:
        row = matched[name]
        if not isinstance(row, Mapping):
            return GateDecision("INVALID", (f"{name} evidence is malformed",))
        difference = float(row.get("accuracy_difference", float("nan")))
        if not np.isfinite(difference):
            return GateDecision("INVALID", (f"{name} difference is non-finite",))
        null_differences[name] = difference
        if difference <= 0.0:
            reasons.append(f"real does not beat {name} ({difference:.6f})")
    strongest_name = min(null_differences, key=null_differences.get)
    strongest_row = matched[strongest_name]
    assert isinstance(strongest_row, Mapping)
    try:
        lower = _bootstrap_lower(strongest_row["bootstrap"])
    except (KeyError, TypeError, ValueError):
        return GateDecision("INVALID", ("strongest matched-null interval is missing",))
    if not np.isfinite(lower):
        return GateDecision("INVALID", ("strongest matched-null interval is non-finite",))
    if lower <= 0.0:
        reasons.append(
            f"strongest matched-null bootstrap lower bound {lower:.6f} is not above zero"
        )

    if not reasons:
        return GateDecision("PASS", ("all five pre-registered checkpoint gates pass",))
    null_uncertainty = any("matched" in reason or "does not beat" in reason for reason in reasons)
    return GateDecision("MIXED" if null_uncertainty else "FAIL", tuple(reasons))


def _score_summary(score: Score) -> dict[str, float]:
    return {
        "accuracy": score.accuracy,
        "macro_f1": score.macro_f1,
        "cross_entropy": score.cross_entropy,
    }


def _fit_variant(
    batches: VariantSplitBatches,
    *,
    kind: str,
    num_skills: int,
    config: FitConfig,
    device: torch.device,
    seed: int,
) -> tuple[dict[str, object], Score, Score]:
    fitted = fit_classifier(
        kind=kind,
        train=batches.train,
        validation=batches.validation,
        num_skills=num_skills,
        config=config,
        device=device,
        seed=seed,
    )
    train_score = score_classifier(fitted.model, kind, batches.train)
    test_score = score_classifier(fitted.model, kind, batches.test)
    summary: dict[str, object] = {
        "kind": kind,
        "model_seed": int(seed),
        "best_step": fitted.best_step,
        "train_loss": fitted.train_loss,
        "validation_loss": fitted.validation_loss,
        "train": _score_summary(train_score),
        "test": _score_summary(test_score),
        "train_test_accuracy_gap": train_score.accuracy - test_score.accuracy,
    }
    return summary, train_score, test_score


def _label_statistics(labels: np.ndarray, num_skills: int) -> dict[str, object]:
    counts = np.bincount(
        np.asarray(labels, dtype=np.int64), minlength=int(num_skills)
    ).astype(np.int64)
    total = int(counts.sum())
    probabilities = counts[counts > 0].astype(np.float64) / max(total, 1)
    entropy = float(-(probabilities * np.log(probabilities)).sum())
    normalized = entropy / np.log(int(num_skills)) if int(num_skills) > 1 else 0.0
    return {
        "counts": counts.tolist(),
        "normalized_entropy": float(normalized),
        "maximum_fraction": float(counts.max(initial=0) / max(total, 1)),
    }


def _split_summary(split: SplitIndices) -> dict[str, object]:
    return {
        "train_rows": int(split.train.size),
        "validation_rows": int(split.validation.size),
        "test_rows": int(split.test.size),
        "train_reset_ids": split.train_reset_ids.tolist(),
        "validation_reset_ids": split.validation_reset_ids.tolist(),
        "test_reset_ids": split.test_reset_ids.tolist(),
    }


def _missing_split_support(
    active_labels: set[int],
    batches: VariantSplitBatches,
) -> dict[str, list[int]]:
    return {
        name: sorted(active_labels - set(np.unique(split_batch.label).tolist()))
        for name, split_batch in (
            ("train", batches.train),
            ("validation", batches.validation),
            ("test", batches.test),
        )
        if active_labels - set(np.unique(split_batch.label).tolist())
    }


def _pre_valid_batches(
    batches: VariantSplitBatches,
    *,
    variant: str,
    seed: int,
) -> VariantSplitBatches:
    filtered: list[G1WindowBatch] = []
    for batch in (batches.train, batches.validation, batches.test):
        indices = np.flatnonzero(np.asarray(batch.pre_valid).reshape(-1) > 0.5)
        filtered.append(batch.take(indices))
    return _transform_split_batches(*filtered, variant=variant, seed=seed)


def _variant_split_summary(batches: VariantSplitBatches) -> dict[str, object]:
    return {
        "train_rows": int(batches.train.label.size),
        "validation_rows": int(batches.validation.label.size),
        "test_rows": int(batches.test.label.size),
        "train_reset_ids": np.unique(batches.train.reset_id).astype(int).tolist(),
        "validation_reset_ids": np.unique(batches.validation.reset_id).astype(int).tolist(),
        "test_reset_ids": np.unique(batches.test.reset_id).astype(int).tolist(),
    }


def heldout_correctness_evidence(
    batch: G1WindowBatch,
    *,
    full: Score,
    prior: Score,
) -> list[dict[str, object]]:
    rows = int(np.asarray(batch.label).size)
    if full.correct.shape != (rows,) or prior.correct.shape != (rows,):
        raise AnalysisInvalidError(
            "held-out correctness evidence is misaligned",
            stage="heldout_correctness_export",
        )
    evidence: list[dict[str, object]] = []
    for index in range(rows):
        evidence.append(
            {
                "test_row": int(index),
                "reset_id": int(batch.reset_id[index]),
                "reset_seed": int(batch.reset_seed[index]),
                "episode_id": int(batch.episode_id[index]),
                "env_id": int(batch.env_id[index]),
                "agent_id": int(batch.agent_id[index]),
                "duration_idx": int(batch.duration_idx[index]),
                "label": int(batch.label[index]),
                "checkpoint_id": str(batch.checkpoint_id[index]),
                "checkpoint_update": int(batch.checkpoint_update[index]),
                "full_correct": bool(full.correct[index]),
                "prior_correct": bool(prior.correct[index]),
            }
        )
    return evidence


def analyze_checkpoint(
    batch: G1WindowBatch,
    *,
    num_skills: int,
    config: FitConfig,
    device: torch.device,
    split_seed: int,
    model_seed: int,
    null_seed: int,
    bootstrap_reps: int,
    bootstrap_seed: int,
) -> dict[str, object]:
    split = grouped_reset_split(batch, seed=int(split_seed))
    labels = np.asarray(batch.label, dtype=np.int64)
    label_stats = _label_statistics(labels, int(num_skills))
    checkpoint_ids = np.unique(np.asarray(batch.checkpoint_id).astype(str))
    checkpoint_updates = np.unique(np.asarray(batch.checkpoint_update, dtype=np.int64))
    if checkpoint_ids.size != 1 or checkpoint_updates.size != 1:
        raise ValueError("analyzer input must contain exactly one checkpoint identity")

    active_labels = set(np.unique(labels).tolist())
    real_splits = variant_split_batches(batch, split, "real", seed=int(null_seed))
    post_valid_splits = _pre_valid_batches(
        real_splits, variant="real", seed=int(null_seed)
    )
    pre_valid_splits = _pre_valid_batches(
        real_splits, variant="pre_only", seed=int(null_seed)
    )
    missing_support = _missing_split_support(active_labels, real_splits)
    missing_pre_valid = _missing_split_support(active_labels, post_valid_splits)
    test_labels = labels[split.test]
    majority_accuracy = None
    if test_labels.size:
        majority_accuracy = float(
            np.bincount(test_labels, minlength=int(num_skills)).max()
            / test_labels.size
        )
    result: dict[str, object] = {
        "checkpoint_id": str(checkpoint_ids[0]),
        "checkpoint_update": int(checkpoint_updates[0]),
        "rows": int(labels.size),
        "label_stats": label_stats,
        "normalized_label_entropy": label_stats["normalized_entropy"],
        "split": {"seed": int(split_seed), **_split_summary(split)},
        "pre_valid_comparison": _variant_split_summary(post_valid_splits),
        "missing_split_labels": missing_support,
        "missing_pre_valid_labels": missing_pre_valid,
        "majority_accuracy": majority_accuracy,
        "valid": True,
        "underpowered": bool(missing_support or missing_pre_valid),
        "variants": {},
        "matched_nulls": {},
        "thresholds": _threshold_metadata(),
    }
    if missing_support or missing_pre_valid:
        decision = gate_checkpoint(result)
        result["gate"] = asdict(decision)
        return result

    variants: dict[str, dict[str, object]] = {}
    row_scores: dict[str, Score] = {}
    train_scores: dict[str, Score] = {}
    for variant in VARIANTS:
        transformed = (
            pre_valid_splits
            if variant == "pre_only"
            else variant_split_batches(batch, split, variant, seed=int(null_seed))
        )
        kinds = KINDS if variant == "real" else (("prior",) if variant == "context_only" else ("behavior",))
        models: dict[str, object] = {}
        for kind in kinds:
            summary, train_score, test_score = _fit_variant(
                transformed,
                kind=kind,
                num_skills=int(num_skills),
                config=config,
                device=device,
                seed=int(model_seed),
            )
            models[kind] = summary
            key = f"{variant}:{kind}"
            row_scores[key] = test_score
            train_scores[key] = train_score
        variants[variant] = {
            "unchanged_fraction": transformed.unchanged_fraction,
            "unchanged_fractions": transformed.unchanged_fractions,
            "split_seeds": transformed.seeds,
            "models": models,
        }

    post_summary, post_train, post = _fit_variant(
        post_valid_splits,
        kind="behavior",
        num_skills=int(num_skills),
        config=config,
        device=device,
        seed=int(model_seed),
    )
    variants["pre_only"]["comparison_post_model"] = post_summary
    row_scores["post_valid:behavior"] = post
    train_scores["post_valid:behavior"] = post_train

    behavior = row_scores["real:behavior"]
    prior = row_scores["real:prior"]
    full = row_scores["real:full"]
    pre = row_scores["pre_only:behavior"]
    test_reset_ids = np.asarray(real_splits.test.reset_id, dtype=np.int64)
    pre_valid_test_reset_ids = np.asarray(
        post_valid_splits.test.reset_id, dtype=np.int64
    )
    primary_intervals = {
        "full_minus_prior_accuracy": asdict(
            cluster_bootstrap_difference(
                full.correct,
                prior.correct,
                test_reset_ids,
                reps=int(bootstrap_reps),
                seed=int(bootstrap_seed),
            )
        ),
        "behavior_post_minus_pre_accuracy": asdict(
            cluster_bootstrap_difference(
                post.correct,
                pre.correct,
                pre_valid_test_reset_ids,
                reps=int(bootstrap_reps),
                seed=int(bootstrap_seed) + 1,
            )
        ),
    }
    matched_nulls: dict[str, dict[str, object]] = {}
    for offset, name in enumerate(MATCHED_NULLS):
        null_score = row_scores[f"{name}:behavior"]
        interval = cluster_bootstrap_difference(
            behavior.correct,
            null_score.correct,
            test_reset_ids,
            reps=int(bootstrap_reps),
            seed=int(bootstrap_seed) + 10 + offset,
        )
        matched_nulls[name] = {
            "accuracy_difference": behavior.accuracy - null_score.accuracy,
            "bootstrap": asdict(interval),
            "unchanged_fraction": variants[name]["unchanged_fraction"],
        }

    true_log_gain = full.true_log_prob - prior.true_log_prob
    overfit_probe_keys = {
        "real:behavior",
        "real:prior",
        "real:full",
        "post_valid:behavior",
        "pre_only:behavior",
        *(f"{name}:behavior" for name in MATCHED_NULLS),
    }
    overfit_reasons = [
        key
        for key, train_score in train_scores.items()
        if key in overfit_probe_keys
        and train_score.accuracy - row_scores[key].accuracy > OVERFIT_ACCURACY_GAP
    ]
    result.update(
        {
            "variants": variants,
            "full_minus_prior_accuracy": full.accuracy - prior.accuracy,
            "behavior_minus_prior_accuracy": behavior.accuracy - prior.accuracy,
            "behavior_post_minus_pre_accuracy": post.accuracy - pre.accuracy,
            "full_minus_prior_true_log_prob_mean": float(true_log_gain.mean()),
            "full_minus_prior_true_log_prob_positive_fraction": float(
                np.mean(true_log_gain > 0.0)
            ),
            "primary_bootstrap": primary_intervals,
            "matched_nulls": matched_nulls,
            "overfit_warning": bool(overfit_reasons),
            "overfit_reasons": overfit_reasons,
            "overfit_probe_keys": sorted(overfit_probe_keys),
            "seeds": {
                "split": int(split_seed),
                "model": int(model_seed),
                "null": int(null_seed),
                "bootstrap": int(bootstrap_seed),
            },
            "fit_config": asdict(config),
            "heldout_row_correctness": heldout_correctness_evidence(
                real_splits.test,
                full=full,
                prior=prior,
            ),
        }
    )
    decision = gate_checkpoint(result)
    result["gate"] = asdict(decision)
    return result


def _invalid_result(
    error: Exception,
    *,
    batch: G1WindowBatch | None = None,
    source: Path | str | None = None,
) -> dict[str, object]:
    if isinstance(error, (G1DataError, AnalysisInvalidError)):
        details = error.as_dict()
    else:
        details = {
            "type": type(error).__name__,
            "message": str(error),
            "rows": [],
        }
    if source is not None and not details.get("source"):
        details["source"] = str(source)

    checkpoint_ids: list[str] = []
    checkpoint_updates: list[int] = []
    rows = details.get("rows", [])
    if isinstance(rows, list):
        checkpoint_ids.extend(
            str(row["checkpoint_id"])
            for row in rows
            if isinstance(row, Mapping) and "checkpoint_id" in row
        )
        checkpoint_updates.extend(
            int(row["checkpoint_update"])
            for row in rows
            if isinstance(row, Mapping) and "checkpoint_update" in row
        )
    if batch is not None:
        checkpoint_ids.extend(np.asarray(batch.checkpoint_id).astype(str).tolist())
        checkpoint_updates.extend(
            np.asarray(batch.checkpoint_update, dtype=np.int64).astype(int).tolist()
        )
    unique_ids = sorted(set(checkpoint_ids))
    unique_updates = sorted(set(checkpoint_updates))
    decision = GateDecision("INVALID", (str(error),))
    return {
        "checkpoint_id": unique_ids[0] if len(unique_ids) == 1 else "unknown",
        "checkpoint_update": unique_updates[0] if len(unique_updates) == 1 else None,
        "rows": 0 if batch is None else int(np.asarray(batch.label).size),
        "valid": False,
        "underpowered": False,
        "variants": {},
        "matched_nulls": {},
        "thresholds": _threshold_metadata(),
        "error": details,
        "gate": asdict(decision),
    }


def analyze_checkpoint_to_reports(
    batch: G1WindowBatch,
    output_dir: Path,
    **analysis_kwargs: object,
) -> dict[str, object]:
    try:
        result = analyze_checkpoint(batch, **analysis_kwargs)
    except Exception as error:
        _write_reports(
            Path(output_dir), _invalid_result(error, batch=batch)
        )
        raise
    _write_reports(Path(output_dir), result)
    return result


def _write_reports(output_dir: Path, result: Mapping[str, object]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "r26_g1_behavior.json"
    md_path = output_dir / "r26_g1_behavior.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    heldout_rows = result.get("heldout_row_correctness")
    if isinstance(heldout_rows, list):
        (output_dir / "r26_g1_heldout_row_correctness.json").write_text(
            json.dumps(
                {
                    "schema": "r26-g1-heldout-row-correctness-v1",
                    "checkpoint_id": result.get("checkpoint_id"),
                    "checkpoint_update": result.get("checkpoint_update"),
                    "rows": heldout_rows,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    gate = result.get("gate", {})
    variants = result.get("variants", {})
    lines = [
        "# R26-G1a Individual-Skill Behavior Screen",
        "",
        f"- Checkpoint: `{result.get('checkpoint_id', 'unknown')}`",
        f"- Gate: **{gate.get('status', 'INVALID') if isinstance(gate, Mapping) else 'INVALID'}**",
        f"- Rows: {result.get('rows', 0)}",
    ]
    error = result.get("error")
    if isinstance(error, Mapping):
        lines.extend(
            [
                "",
                "## Invalid analysis",
                "",
                f"- Type: `{error.get('type', 'unknown')}`",
                f"- Message: {error.get('message', 'unknown error')}",
                f"- Source: `{error.get('source', 'unknown')}`",
                f"- Rows: `{json.dumps(error.get('rows', []), sort_keys=True)}`",
            ]
        )
    split = result.get("split")
    if isinstance(split, Mapping):
        lines.extend(
            [
                "",
                "## Split",
                "",
                f"- Train rows: {split.get('train_rows', 0)}; Train resets: `{split.get('train_reset_ids', [])}`",
                f"- Validation rows: {split.get('validation_rows', 0)}; Validation resets: `{split.get('validation_reset_ids', [])}`",
                f"- Test rows: {split.get('test_rows', 0)}; Test resets: `{split.get('test_reset_ids', [])}`",
            ]
        )
        comparison = result.get("pre_valid_comparison")
        if isinstance(comparison, Mapping):
            lines.append(
                "- Valid-pre comparison rows: train={train}, validation={validation}, test={test}".format(
                    train=comparison.get("train_rows", 0),
                    validation=comparison.get("validation_rows", 0),
                    test=comparison.get("test_rows", 0),
                )
            )
    label_stats = result.get("label_stats")
    if isinstance(label_stats, Mapping):
        majority_accuracy = result.get("majority_accuracy")
        majority_text = "unavailable"
        if isinstance(majority_accuracy, (int, float, np.integer, np.floating)):
            majority_value = float(majority_accuracy)
            if np.isfinite(majority_value):
                majority_text = f"{majority_value:.6f}"
        lines.extend(
            [
                "",
                "## Baselines",
                "",
                f"- Label counts: `{label_stats.get('counts', [])}`",
                f"- Normalized label entropy: {float(label_stats.get('normalized_entropy', 0.0)):.6f}",
                f"- Maximum label fraction: {float(label_stats.get('maximum_fraction', 0.0)):.6f}",
                f"- Majority accuracy: {majority_text}",
            ]
        )
    gate_status = gate.get("status") if isinstance(gate, Mapping) else None
    if gate_status == "UNDERPOWERED":
        missing_split_labels = result.get("missing_split_labels")
        missing_pre_valid_labels = result.get("missing_pre_valid_labels")
        split_support_text = (
            json.dumps(dict(missing_split_labels), sort_keys=True)
            if isinstance(missing_split_labels, Mapping)
            else "unavailable"
        )
        pre_valid_support_text = (
            json.dumps(dict(missing_pre_valid_labels), sort_keys=True)
            if isinstance(missing_pre_valid_labels, Mapping)
            else "unavailable"
        )
        lines.extend(
            [
                "",
                "## Label support",
                "",
                f"- Missing split labels: `{split_support_text}`",
                f"- Missing valid-pre labels: `{pre_valid_support_text}`",
            ]
        )
    thresholds = result.get("thresholds")
    if isinstance(thresholds, Mapping):
        lines.extend(
            [
                "",
                "## Thresholds",
                "",
                "| threshold | pre-registered value |",
                "| --- | ---: |",
            ]
        )
        for name, value in thresholds.items():
            lines.append(f"| {name} | `{value}` |")
    primary = result.get("primary_bootstrap")
    if isinstance(primary, Mapping):
        lines.extend(
            [
                "",
                "## Primary differences",
                "",
                "| metric | value | Bootstrap 95% CI |",
                "| --- | ---: | ---: |",
            ]
        )
        for name in (
            "full_minus_prior_accuracy",
            "behavior_post_minus_pre_accuracy",
        ):
            interval = primary.get(name, {})
            if not isinstance(interval, Mapping):
                interval = {}
            lines.append(
                "| {name} | {value:.6f} | [{lower:.6f}, {upper:.6f}] |".format(
                    name=name,
                    value=float(result.get(name, 0.0)),
                    lower=float(interval.get("lower", 0.0)),
                    upper=float(interval.get("upper", 0.0)),
                )
            )
    matched_nulls = result.get("matched_nulls")
    if isinstance(matched_nulls, Mapping) and matched_nulls:
        lines.extend(
            [
                "",
                "## Matched nulls",
                "",
                "| null | real-minus-null accuracy | Bootstrap 95% CI | unchanged fraction |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for name in MATCHED_NULLS:
            row = matched_nulls.get(name, {})
            if not isinstance(row, Mapping):
                continue
            interval = row.get("bootstrap", {})
            if not isinstance(interval, Mapping):
                interval = {}
            lines.append(
                "| {name} | {difference:.6f} | [{lower:.6f}, {upper:.6f}] | {unchanged:.6f} |".format(
                    name=name,
                    difference=float(row.get("accuracy_difference", 0.0)),
                    lower=float(interval.get("lower", 0.0)),
                    upper=float(interval.get("upper", 0.0)),
                    unchanged=float(row.get("unchanged_fraction", 0.0)),
                )
            )
    lines.extend(
        [
            "",
            "## Variant scores",
            "",
            "| variant | kind | unchanged | best step | test accuracy | macro-F1 | cross-entropy | train-test gap |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if isinstance(variants, Mapping):
        for variant in VARIANTS:
            row = variants.get(variant, {})
            if not isinstance(row, Mapping):
                continue
            models = row.get("models", {})
            if not isinstance(models, Mapping):
                continue
            for kind, model_row in models.items():
                if not isinstance(model_row, Mapping):
                    continue
                test = model_row.get("test", {})
                if not isinstance(test, Mapping):
                    continue
                lines.append(
                    "| {variant} | {kind} | {unchanged:.6f} | {step} | {accuracy:.6f} | "
                    "{f1:.6f} | {ce:.6f} | {gap:.6f} |".format(
                        variant=variant,
                        kind=kind,
                        unchanged=float(row.get("unchanged_fraction", 0.0)),
                        step=int(model_row.get("best_step", 0)),
                        accuracy=float(test.get("accuracy", 0.0)),
                        f1=float(test.get("macro_f1", 0.0)),
                        ce=float(test.get("cross_entropy", 0.0)),
                        gap=float(model_row.get("train_test_accuracy_gap", 0.0)),
                    )
                )
    if isinstance(gate, Mapping):
        lines.extend(["", "## Gate reasons", ""])
        for reason in gate.get("reasons", []):
            lines.append(f"- {reason}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_analysis(
    input_dir: Path,
    output_dir: Path,
    *,
    num_skills: int,
    device: str,
    split_seed: int = 26011,
    model_seed: int = 26012,
    null_seed: int = 26013,
    max_steps: int = 1000,
    patience: int = 20,
    validation_interval: int = 5,
    hidden_dim: int = 128,
    lr: float = 0.003,
    bootstrap_reps: int = 2000,
    bootstrap_seed: int = 26014,
) -> dict[str, object]:
    output_path = Path(output_dir)
    try:
        torch_device = torch.device(str(device))
        if torch_device.type == "cpu":
            raise ValueError("real R26-G1a analysis requires CUDA; CPU is unit-test only")
        if torch_device.type != "cuda":
            raise ValueError(f"unsupported analysis device: {device}")
        batch = read_g1_window_shards(Path(input_dir))
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested for R26-G1a analysis but is unavailable")
    except Exception as error:
        _write_reports(
            output_path, _invalid_result(error, source=Path(input_dir))
        )
        raise
    return analyze_checkpoint_to_reports(
        batch,
        output_path,
        num_skills=int(num_skills),
        config=FitConfig(
            max_steps=int(max_steps),
            patience=int(patience),
            hidden_dim=int(hidden_dim),
            lr=float(lr),
            validation_interval=int(validation_interval),
        ),
        device=torch_device,
        split_seed=int(split_seed),
        model_seed=int(model_seed),
        null_seed=int(null_seed),
        bootstrap_reps=int(bootstrap_reps),
        bootstrap_seed=int(bootstrap_seed),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze frozen R26-G1a individual-skill behavior windows."
    )
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--num_skills", type=int, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--split_seed", type=int, default=26011)
    parser.add_argument("--model_seed", type=int, default=26012)
    parser.add_argument("--null_seed", type=int, default=26013)
    parser.add_argument("--max_steps", type=int, default=1000)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--validation_interval", type=int, default=5)
    parser.add_argument("--hidden_dim", type=int, default=128)
    parser.add_argument("--lr", type=float, default=0.003)
    parser.add_argument("--bootstrap_reps", type=int, default=2000)
    parser.add_argument("--bootstrap_seed", type=int, default=26014)
    args = parser.parse_args()
    run_analysis(
        Path(args.input_dir),
        Path(args.output_dir),
        num_skills=args.num_skills,
        device=args.device,
        split_seed=args.split_seed,
        model_seed=args.model_seed,
        null_seed=args.null_seed,
        max_steps=args.max_steps,
        patience=args.patience,
        validation_interval=args.validation_interval,
        hidden_dim=args.hidden_dim,
        lr=args.lr,
        bootstrap_reps=args.bootstrap_reps,
        bootstrap_seed=args.bootstrap_seed,
    )


if __name__ == "__main__":
    main()
