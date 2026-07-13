import numpy as np
import torch

from ha_ctse_process.r29_action_information import (
    classify_checkpoint,
    classify_family,
    evaluate_action_information,
    normalized_label_entropy,
)


def test_identical_skill_distributions_have_zero_information():
    means = torch.zeros(5, 4, 2)
    log_stds = torch.zeros_like(means)
    epsilon = torch.randn(7, 5, 4, 2, generator=torch.Generator().manual_seed(3))
    result = evaluate_action_information(means, log_stds, epsilon=epsilon)
    assert np.max(np.abs(result.active_reward)) < 1e-6
    assert np.max(np.abs(result.sham_reward)) < 1e-6


def test_separated_skill_distributions_reward_source_over_sham():
    means = torch.zeros(32, 4, 1)
    means[:, :, 0] = torch.tensor([-1.5, -0.5, 0.5, 1.5])
    log_stds = torch.full_like(means, -1.0)
    epsilon = torch.randn(
        64, 32, 4, 1, generator=torch.Generator().manual_seed(7)
    )
    result = evaluate_action_information(means, log_stds, epsilon=epsilon)
    assert float(result.active_reward.mean()) > 0.5
    assert float((result.active_by_row - result.sham_by_row).mean()) > 1.0
    assert np.all(result.active_by_skill > 0.3)


def test_entropy_and_fixed_gate_classification():
    labels = np.arange(400) % 4
    assert np.isclose(normalized_label_entropy(labels, 4), 1.0)
    status, reasons = classify_checkpoint(
        rows=6_000,
        resets=64,
        label_entropy=0.99,
        active_mean=0.02,
        minimum_skill_mean=0.01,
        active_minus_sham_lower=0.01,
        inactive_max_abs=1e-8,
    )
    assert status == "PASS"
    assert reasons == []
    failed, failed_reasons = classify_checkpoint(
        rows=6_000,
        resets=64,
        label_entropy=0.99,
        active_mean=0.0,
        minimum_skill_mean=0.0,
        active_minus_sham_lower=-0.01,
        inactive_max_abs=0.0,
    )
    assert failed == "FAIL"
    assert len(failed_reasons) == 3


def test_family_requires_final_and_two_checkpoint_passes():
    reports = [
        {"checkpoint_id": "arm0_update25", "status": "FAIL"},
        {"checkpoint_id": "arm0_update30", "status": "PASS"},
        {"checkpoint_id": "arm0_final", "status": "PASS"},
    ]
    status, classification, _next = classify_family(reports)
    assert status == "PASS"
    assert classification == "PASS_COUNTERFACTUAL_ACTION_INFORMATION_TARGET"
    reports[1]["status"] = "FAIL"
    status, classification, _next = classify_family(reports)
    assert status == "FAIL"
    assert classification == "FAIL_WEAK_ACTION_INFORMATION_TARGET"
