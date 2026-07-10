from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from ha_ctse_process.r26_g1_dataset import G1WindowBatch, grouped_reset_split
from scripts import analyze_r26_g1_behavior as behavior_analyzer
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
    assert result["thresholds"] == {
        "normalized_label_entropy_min": 0.8,
        "accuracy_gain_min": 0.05,
        "matched_null_difference": "> 0.0",
        "matched_null_bootstrap_lower": "> 0.0",
        "overfit_train_minus_test_accuracy": "> 0.20",
        "early_stop_min_delta": 1e-4,
    }


def test_label_null_train_and_validation_ignore_original_test_labels(
    g1_behavior_batch,
):
    split = grouped_reset_split(g1_behavior_batch, seed=26011)
    changed_labels = g1_behavior_batch.label.copy()
    changed_labels[split.test] = (changed_labels[split.test] + 1) % 3
    changed = replace(g1_behavior_batch, label=changed_labels)

    for variant in (
        "shuffled",
        "fake_marginal",
        "agent_matched",
        "duration_matched",
        "agent_duration_matched",
    ):
        first = behavior_analyzer.variant_split_batches(
            g1_behavior_batch, split, variant, seed=26013
        )
        second = behavior_analyzer.variant_split_batches(
            changed, split, variant, seed=26013
        )
        assert np.array_equal(first.train.label, second.train.label)
        assert np.array_equal(first.validation.label, second.validation.label)

    first = behavior_analyzer.variant_split_batches(
        g1_behavior_batch, split, "fake_marginal", seed=26013
    )
    second = behavior_analyzer.variant_split_batches(
        changed, split, "fake_marginal", seed=26013
    )
    config = FitConfig(
        max_steps=5,
        patience=1,
        hidden_dim=8,
        lr=3e-3,
        validation_interval=1,
    )
    fitted_first = fit_classifier(
        kind="behavior",
        train=first.train,
        validation=first.validation,
        num_skills=3,
        config=config,
        device=torch.device("cpu"),
        seed=26012,
    )
    fitted_second = fit_classifier(
        kind="behavior",
        train=second.train,
        validation=second.validation,
        num_skills=3,
        config=config,
        device=torch.device("cpu"),
        seed=26012,
    )
    for name, values in fitted_first.model.state_dict().items():
        assert torch.equal(values, fitted_second.model.state_dict()[name])


def test_post_minus_pre_uses_identical_valid_rows(g1_behavior_batch):
    pre_valid = np.ones_like(g1_behavior_batch.pre_valid)
    for reset_id in np.unique(g1_behavior_batch.reset_id):
        reset_rows = np.flatnonzero(g1_behavior_batch.reset_id == reset_id)
        for label in (1, 2):
            label_rows = reset_rows[g1_behavior_batch.label[reset_rows] == label]
            pre_valid[label_rows[:3]] = 0.0
    pre_action = g1_behavior_batch.post_action.copy()
    pre_effect = g1_behavior_batch.post_effect.copy()
    pre_action[pre_valid == 0.0] = 0.0
    pre_effect[pre_valid == 0.0] = 0.0
    batch = replace(
        g1_behavior_batch,
        pre_action=pre_action,
        pre_effect=pre_effect,
        pre_valid=pre_valid,
    )

    result = analyze_checkpoint(
        batch,
        num_skills=3,
        config=FitConfig(
            max_steps=80,
            patience=4,
            hidden_dim=24,
            lr=3e-3,
            validation_interval=5,
        ),
        device=torch.device("cpu"),
        split_seed=26011,
        model_seed=26012,
        null_seed=26013,
        bootstrap_reps=50,
        bootstrap_seed=26014,
    )
    comparison = result["pre_valid_comparison"]
    assert comparison["train_rows"] < result["split"]["train_rows"]
    assert comparison["validation_rows"] < result["split"]["validation_rows"]
    assert comparison["test_rows"] < result["split"]["test_rows"]
    assert result["behavior_post_minus_pre_accuracy"] == pytest.approx(0.0)


def test_post_minus_pre_reports_underpowered_when_valid_rows_lose_a_label(
    tmp_path: Path,
    g1_behavior_batch,
):
    pre_valid = (g1_behavior_batch.label != 2).astype(np.float32)
    batch = replace(g1_behavior_batch, pre_valid=pre_valid)
    result = analyze_checkpoint(
        batch,
        num_skills=3,
        config=FitConfig(max_steps=1, patience=1, hidden_dim=8, validation_interval=1),
        device=torch.device("cpu"),
        split_seed=26011,
        model_seed=26012,
        null_seed=26013,
        bootstrap_reps=10,
        bootstrap_seed=26014,
    )
    assert result["underpowered"] is True
    assert result["gate"]["status"] == "UNDERPOWERED"
    assert result["missing_pre_valid_labels"] == {
        "train": [2],
        "validation": [2],
        "test": [2],
    }
    split = grouped_reset_split(batch, seed=26011)
    test_counts = np.bincount(batch.label[split.test], minlength=3)
    expected_majority = float(test_counts.max() / split.test.size)
    assert result["majority_accuracy"] == pytest.approx(expected_majority)

    behavior_analyzer._write_reports(tmp_path, result)
    markdown = (tmp_path / "r26_g1_behavior.md").read_text()
    assert f"- Majority accuracy: {expected_majority:.6f}" in markdown
    assert "- Missing split labels: `{}`" in markdown
    assert (
        '- Missing valid-pre labels: `{"test": [2], "train": [2], '
        '"validation": [2]}`'
        in markdown
    )

    unavailable_result = dict(result)
    unavailable_result.pop("majority_accuracy")
    unavailable_dir = tmp_path / "unavailable"
    behavior_analyzer._write_reports(unavailable_dir, unavailable_result)
    unavailable_markdown = (
        unavailable_dir / "r26_g1_behavior.md"
    ).read_text()
    assert "- Majority accuracy: unavailable" in unavailable_markdown


def test_nonfinite_input_writes_invalid_reports(
    tmp_path: Path,
    g1_behavior_batch,
):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    post_action = g1_behavior_batch.post_action.copy()
    post_action[5, 2] = np.nan
    broken = replace(g1_behavior_batch, post_action=post_action)
    shard_path = input_dir / "reset_005.npz"
    np.savez_compressed(
        shard_path,
        **{
            field: getattr(broken, field)
            for field in G1WindowBatch.__dataclass_fields__
        },
    )

    with pytest.raises(ValueError, match="post_action"):
        behavior_analyzer.run_analysis(
            input_dir,
            output_dir,
            num_skills=3,
            device="cuda",
            max_steps=1,
            patience=1,
            validation_interval=1,
            hidden_dim=8,
            bootstrap_reps=10,
        )

    payload = json.loads((output_dir / "r26_g1_behavior.json").read_text())
    assert payload["gate"]["status"] == "INVALID"
    assert payload["error"]["field"] == "post_action"
    assert payload["error"]["source"].endswith("reset_005.npz")
    assert payload["error"]["rows"][0]["row_index"] == 5
    assert payload["error"]["rows"][0]["checkpoint_id"] == "synthetic_update25"
    markdown = (output_dir / "r26_g1_behavior.md").read_text()
    assert "**INVALID**" in markdown
    assert "reset_005.npz" in markdown


def test_nonfinite_loss_writes_invalid_reports(
    tmp_path: Path,
    g1_behavior_batch,
):
    huge = np.full_like(g1_behavior_batch.post_action, np.finfo(np.float32).max)
    batch = replace(g1_behavior_batch, post_action=huge)

    with pytest.raises(ValueError, match="training loss"):
        behavior_analyzer.analyze_checkpoint_to_reports(
            batch,
            tmp_path,
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

    payload = json.loads((tmp_path / "r26_g1_behavior.json").read_text())
    assert payload["gate"]["status"] == "INVALID"
    assert payload["error"]["stage"] == "training_loss"
    assert payload["error"]["rows"]
    assert payload["error"]["rows"][0]["checkpoint_id"] == "synthetic_update25"


def test_same_seeds_reproduce_actual_analysis_outputs(g1_behavior_batch):
    kwargs = dict(
        num_skills=3,
        config=FitConfig(
            max_steps=2,
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
    first = analyze_checkpoint(g1_behavior_batch, **kwargs)
    second = analyze_checkpoint(g1_behavior_batch, **kwargs)
    assert first == second


def test_cpu_real_run_is_rejected_with_invalid_report(tmp_path: Path):
    output_dir = tmp_path / "output"
    with pytest.raises(ValueError, match="requires CUDA"):
        behavior_analyzer.run_analysis(
            tmp_path / "unused-input",
            output_dir,
            num_skills=3,
            device="cpu",
        )
    payload = json.loads((output_dir / "r26_g1_behavior.json").read_text())
    assert payload["gate"]["status"] == "INVALID"
    assert payload["error"]["type"] == "ValueError"


def test_analyzer_absolute_entrypoint_bootstraps_repository_imports(tmp_path: Path):
    analyzer = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "analyze_r26_g1_behavior.py"
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [sys.executable, str(analyzer), "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "usage:" in completed.stdout.lower()


def test_markdown_contains_complete_gate_evidence(
    tmp_path: Path,
    g1_behavior_batch,
):
    result = analyze_checkpoint(
        g1_behavior_batch,
        num_skills=3,
        config=FitConfig(
            max_steps=2,
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
    behavior_analyzer._write_reports(tmp_path, result)
    markdown = (tmp_path / "r26_g1_behavior.md").read_text()
    for required in (
        "## Split",
        "Train resets",
        "Normalized label entropy",
        "Majority accuracy",
        "## Thresholds",
        "overfit_train_minus_test_accuracy",
        "## Primary differences",
        "full_minus_prior_accuracy",
        "behavior_post_minus_pre_accuracy",
        "## Matched nulls",
        "agent_matched",
        "duration_matched",
        "agent_duration_matched",
        "Bootstrap 95% CI",
        "## Gate reasons",
    ):
        assert required in markdown
