import numpy as np
import pytest
import torch

from ha_ctse_process.r26_g1_dataset import G1WindowBatch, grouped_reset_split
from scripts.analyze_r26_g1_behavior import (
    FitConfig,
    VARIANTS,
    analyze_checkpoint,
    cluster_bootstrap_difference,
    fit_classifier,
    gate_checkpoint,
    score_classifier,
    variant_batch,
)


def _synthetic_batch(*, behavior_coded: bool, seed: int) -> G1WindowBatch:
    rng = np.random.default_rng(seed)
    resets = np.repeat(np.arange(12, dtype=np.int64), 12)
    rows = int(resets.size)
    labels = np.tile(np.repeat(np.arange(3, dtype=np.int64), 4), 12)
    action_means = np.asarray(
        [[-2.0, 0.0, 1.0, 0.5], [0.0, 2.0, -1.0, 0.0], [2.0, -1.0, 0.0, -0.5]],
        dtype=np.float32,
    )
    effect_means = np.asarray(
        [[1.5, -1.0, 0.0, 0.5], [-1.0, 0.5, 1.5, 0.0], [0.0, 1.0, -1.5, 1.0]],
        dtype=np.float32,
    )
    if behavior_coded:
        post_action = action_means[labels] + rng.normal(0.0, 0.15, (rows, 4))
        post_effect = effect_means[labels] + rng.normal(0.0, 0.15, (rows, 4))
    else:
        post_action = rng.normal(0.0, 1.0, (rows, 4))
        post_effect = rng.normal(0.0, 1.0, (rows, 4))
    pre_action = rng.normal(0.0, 1.0, (rows, 4))
    pre_effect = rng.normal(0.0, 1.0, (rows, 4))
    return G1WindowBatch(
        label=labels,
        post_action=post_action.astype(np.float32),
        post_effect=post_effect.astype(np.float32),
        pre_action=pre_action.astype(np.float32),
        pre_effect=pre_effect.astype(np.float32),
        pre_valid=np.ones(rows, dtype=np.float32),
        prior_context=rng.normal(0.0, 1.0, (rows, 6)).astype(np.float32),
        reset_id=resets,
        reset_seed=26000 + resets,
        episode_id=resets,
        env_id=resets % 2,
        agent_id=np.arange(rows, dtype=np.int64) % 6,
        duration_idx=(np.arange(rows, dtype=np.int64) // 6) % 4,
        segment_length=np.full(rows, 10, dtype=np.int64),
        checkpoint_id=np.full(rows, "synthetic_update25"),
        checkpoint_update=np.full(rows, 25, dtype=np.int64),
    )


@pytest.fixture
def g1_batch() -> G1WindowBatch:
    batch = _synthetic_batch(behavior_coded=True, seed=1)
    indices = np.asarray([0, 1, 2, 3, 12, 13, 24, 25, 36, 48, 60, 72])
    return batch.take(indices)


@pytest.fixture
def g1_behavior_batch() -> G1WindowBatch:
    return _synthetic_batch(behavior_coded=True, seed=2)


@pytest.fixture
def g1_noise_batch() -> G1WindowBatch:
    return _synthetic_batch(behavior_coded=False, seed=3)


def _fit_and_score(
    batch: G1WindowBatch,
    kind: str,
    *,
    seed: int,
) -> tuple[object, object, object]:
    split = grouped_reset_split(batch, seed=26011)
    fitted = fit_classifier(
        kind=kind,
        train=batch.take(split.train),
        validation=batch.take(split.validation),
        num_skills=3,
        config=FitConfig(
            max_steps=80,
            patience=4,
            hidden_dim=24,
            lr=3e-3,
            validation_interval=5,
        ),
        device=torch.device("cpu"),
        seed=seed,
    )
    train_score = score_classifier(fitted.model, kind, batch.take(split.train))
    test_score = score_classifier(fitted.model, kind, batch.take(split.test))
    return fitted, train_score, test_score


def run_synthetic_checkpoint_analysis(batch: G1WindowBatch) -> dict[str, object]:
    split = grouped_reset_split(batch, seed=26011)
    behavior_fit, behavior_train, behavior = _fit_and_score(batch, "behavior", seed=31)
    full_fit, full_train, full = _fit_and_score(batch, "full", seed=32)
    prior_fit, prior_train, prior = _fit_and_score(batch, "prior", seed=33)
    pre_batch, _ = variant_batch(batch, "pre_only", seed=34)
    pre_fit, pre_train, pre = _fit_and_score(pre_batch, "behavior", seed=34)

    matched_nulls: dict[str, dict[str, object]] = {}
    for offset, variant in enumerate(
        ("agent_matched", "duration_matched", "agent_duration_matched")
    ):
        null_batch, unchanged = variant_batch(batch, variant, seed=40 + offset)
        _, _, null_score = _fit_and_score(null_batch, "behavior", seed=40 + offset)
        interval = cluster_bootstrap_difference(
            behavior.correct.astype(np.float64),
            null_score.correct.astype(np.float64),
            batch.take(split.test).reset_id,
            reps=100,
            seed=50 + offset,
        )
        matched_nulls[variant] = {
            "accuracy_difference": behavior.accuracy - null_score.accuracy,
            "bootstrap": interval,
            "unchanged_fraction": unchanged,
        }

    counts = np.bincount(batch.label, minlength=3).astype(np.float64)
    probabilities = counts[counts > 0] / counts.sum()
    normalized_entropy = float(
        -(probabilities * np.log(probabilities)).sum() / np.log(3.0)
    )
    return {
        "valid": True,
        "underpowered": False,
        "normalized_label_entropy": normalized_entropy,
        "full_minus_prior_accuracy": full.accuracy - prior.accuracy,
        "behavior_post_minus_pre_accuracy": behavior.accuracy - pre.accuracy,
        "matched_nulls": matched_nulls,
        "overfit_warning": any(
            train.accuracy - test.accuracy > 0.20
            for train, test in (
                (behavior_train, behavior),
                (full_train, full),
                (prior_train, prior),
                (pre_train, pre),
            )
        ),
        "early_stop_steps": {
            "behavior": behavior_fit.best_step,
            "full": full_fit.best_step,
            "prior": prior_fit.best_step,
            "pre": pre_fit.best_step,
        },
    }


def test_grouped_null_does_not_fallback_for_singletons(g1_batch):
    variant, unchanged = variant_batch(g1_batch, "agent_duration_matched", seed=17)
    groups = np.stack([g1_batch.agent_id, g1_batch.duration_idx], axis=1)
    for group in np.unique(groups, axis=0):
        idx = np.flatnonzero(np.all(groups == group, axis=1))
        if idx.size == 1:
            assert variant.label[idx[0]] == g1_batch.label[idx[0]]
    assert 0.0 <= unchanged <= 1.0


def test_fit_does_not_accept_test_rows(g1_behavior_batch):
    split = grouped_reset_split(g1_behavior_batch, seed=26011)
    fitted = fit_classifier(
        kind="behavior",
        train=g1_behavior_batch.take(split.train),
        validation=g1_behavior_batch.take(split.validation),
        num_skills=3,
        config=FitConfig(max_steps=200, patience=10, hidden_dim=32, lr=3e-3),
        device=torch.device("cpu"),
        seed=19,
    )
    metrics = score_classifier(fitted.model, "behavior", g1_behavior_batch.take(split.test))
    assert metrics.accuracy > 0.70
    assert fitted.best_step < 200


def test_noise_behavior_does_not_clear_gate(g1_noise_batch):
    result = run_synthetic_checkpoint_analysis(g1_noise_batch)
    decision = gate_checkpoint(result)
    assert decision.status != "PASS"


def test_cluster_bootstrap_is_deterministic():
    reset_ids = np.repeat(np.arange(8), 4)
    real = np.linspace(0.2, 0.8, reset_ids.size)
    null = real - 0.1
    first = cluster_bootstrap_difference(real, null, reset_ids, reps=200, seed=7)
    second = cluster_bootstrap_difference(real, null, reset_ids, reps=200, seed=7)
    assert first == second
    assert first.lower > 0.0


def test_checkpoint_analysis_reuses_model_seed_for_every_variant(g1_behavior_batch):
    result = analyze_checkpoint(
        g1_behavior_batch,
        num_skills=3,
        config=FitConfig(
            max_steps=1,
            patience=1,
            hidden_dim=8,
            lr=3e-3,
            validation_interval=1,
        ),
        device=torch.device("cpu"),
        split_seed=26011,
        model_seed=26012,
        null_seed=26013,
        bootstrap_reps=10,
        bootstrap_seed=26014,
    )
    assert tuple(result["variants"]) == VARIANTS
    seeds = {
        model["model_seed"]
        for variant in result["variants"].values()
        for model in variant["models"].values()
    }
    assert seeds == {26012}
