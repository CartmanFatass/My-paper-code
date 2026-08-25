from __future__ import annotations

import json

import numpy as np
import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.analysis import (
    classify_atomic,
    joint_max_t,
    load_and_validate_branch_fixture,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.gate_b import run_gate_b_fixture
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.lifecycle import LifecycleError, read_verified
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.model import run_synthetic_update
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.model import GateBModel
import torch


def test_exact_branch_fixture_covers_all_first_match_branches() -> None:
    payload = load_and_validate_branch_fixture()
    assert [case["expected_branch"] for case in payload["cases"]] == list(range(1, 16))


def test_support_failure_simple_rule_fallback_precedence() -> None:
    base = {"protocol_ok": True, "comp": True, "witness": True, "headroom": True, "precision": True, "support": False}
    assert classify_atomic({**base, "rule_fallback_i": True}) == (5, "SIMPLE_RULE_SUFFICIENT[IMMEDIATE]")
    assert classify_atomic({**base, "rule_fallback_h": True}) == (5, "SIMPLE_RULE_SUFFICIENT[HYSTERESIS]")


def test_joint_max_t_totalizes_identical_and_nonidentical_estimands() -> None:
    block = np.arange(24, dtype=np.float64)[:, None]
    values = np.concatenate((np.zeros((24, 1)), np.sin(block * 0.3), np.cos(block * 0.2)), axis=1)
    result = joint_max_t(values, resamples=1024, chunk_size=128)
    assert result["resamples"] == 1024
    assert result["estimands"] == 3
    assert result["lower"][0] == result["upper"][0] == 0.0
    assert result["all_finite"] is True


def test_synthetic_update_has_exact_batched_replay_shape() -> None:
    result = run_synthetic_update()
    assert result["lanes"] == 32
    assert result["transitions"] == 4096
    assert result["optimizer_steps"] == 32
    assert result["loss_count"] == 32
    assert result["losses_finite"] is True
    assert result["scientific_model"] is False


def test_gate_b_model_starts_at_literal_structured_embedding() -> None:
    model = GateBModel()
    hidden = torch.linspace(-1.0, 1.0, 4 * 128).reshape(4, 128)
    delta, alpha, readiness, beta = model.flex_residuals(hidden)
    assert torch.count_nonzero(delta).item() == 0
    assert torch.equal(alpha, torch.ones_like(alpha))
    assert torch.count_nonzero(readiness).item() == 0
    assert torch.count_nonzero(beta).item() == 0


def test_gate_b_complete_fixture_and_non_evaluable_resume(tmp_path) -> None:
    result = run_gate_b_fixture(tmp_path, resamples=1024)
    assert result["branch_case_count"] == 15
    assert result["branch_first_match_complete"] is True
    assert result["synthetic_evaluation"]["complete_rows"] == 48 * 5 * 2
    assert result["synthetic_evaluation"]["paired_fork_count"] == 48
    assert result["resume_evaluable"] is False
    payload = read_verified(tmp_path / "resume" / "synthetic-update-0001.json")
    assert payload["kind"] == "NON_EVALUABLE_TEST_RESUME"
    with pytest.raises(LifecycleError):
        # The exact create-only path may not be overwritten.
        from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r05.lifecycle import write_once_atomic
        write_once_atomic(tmp_path / "resume" / "synthetic-update-0001.json", payload)
