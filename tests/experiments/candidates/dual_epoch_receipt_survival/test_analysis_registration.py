from __future__ import annotations

import numpy as np
import pytest

from experiments.candidates.dual_epoch_receipt_survival.analysis import (
    analyze_registered, interval95, summarize_arm,
)
from experiments.candidates.dual_epoch_receipt_survival.domain import (
    GRU_DUAL, GRU_ORACLE, GRU_RAW, GRU_SNAPSHOT, GRU_UNBOUND,
    GRU_VALIDITY, LEARNED_ARMS,
)
from experiments.candidates.dual_epoch_receipt_survival.generator import generate_examples
from experiments.candidates.dual_epoch_receipt_survival import run
from experiments.candidates.dual_epoch_receipt_survival.run import CAPS, DECLARED_COUNTS


def _partition_probabilities(examples, arm):
    values = np.zeros((len(examples), 3), dtype=np.float64)
    for index, row in enumerate(examples):
        correct = int(row.correct_action)
        if arm in (GRU_DUAL, GRU_ORACLE):
            values[index, correct] = 1.0
        elif arm == GRU_SNAPSHOT:
            values[index] = 1 / 3
        elif arm == GRU_UNBOUND:
            if row.authentication:
                values[index, 2] = 0.5
                values[index, row.displayed_bit] = 0.5
            else:
                values[index, 2] = 1.0
        elif arm == GRU_VALIDITY:
            if row.live:
                values[index, 0:2] = 0.5
            else:
                values[index, 2] = 1.0
        elif arm == GRU_RAW:
            values[index] = 1 / 3
    return values


def test_analysis_reports_all_cells_q_w_greedy_flips_and_subtype_probabilities():
    examples = generate_examples(13, "test")
    summaries = {arm: summarize_arm(examples, _partition_probabilities(examples, arm))
                 for arm in LEARNED_ARMS}
    assert summaries[GRU_DUAL]["refined_cell_count"] == 90
    assert len(summaries[GRU_DUAL]["per_refined_cell"]) == 90
    assert summaries[GRU_DUAL]["W"] == 1.0
    assert summaries[GRU_SNAPSHOT]["W"] == pytest.approx(1 / 3)
    assert summaries[GRU_UNBOUND]["W"] == 0.5
    assert summaries[GRU_VALIDITY]["W"] == 0.5
    assert summaries[GRU_ORACLE]["worst_cell_greedy_top_one_accuracy"] == 1.0
    assert set(summaries[GRU_DUAL]["matched_action_flips"]) == {
        "owner_survival", "lease_survival", "authentication", "content"
    }
    assert set(summaries[GRU_DUAL]["action_probabilities_by_authentication_subtype"]) == {
        "GENUINE", "PAYLOAD_FLIP_BAD_TAG", "FOREIGN_ISSUER"
    }


def test_t_intervals_and_paired_support_statements_use_ten_seed_values():
    examples = generate_examples(13, "test")
    arms = {arm: summarize_arm(examples, _partition_probabilities(examples, arm))
            for arm in LEARNED_ARMS}
    rows = [{"test": arms} for _ in range(10)]
    result = analyze_registered(rows)
    assert result["per_arm"][GRU_DUAL]["mean_W_student_t_95"] == {
        "mean": 1.0, "lower": 1.0, "upper": 1.0, "standard_error": 0.0, "n": 10,
    }
    assert result["paired_dual_minus_comparator"][GRU_ORACLE]["student_t_95"]["lower"] == 0.0
    assert result["statements"]["learned_verifier_sufficiency"] is True
    assert result["statements"]["finite_budget_abstraction_advantage_over_raw"] is True
    assert interval95(range(10))["n"] == 10


def test_registered_runner_exposes_only_full_frozen_counts_and_caps():
    assert DECLARED_COUNTS == {
        "base_seeds": 10, "learned_arms": 6,
        "superblocks_per_seed": {"train": 576, "validation": 192, "test": 576},
        "examples_per_arm_seed": {"train": 9216, "validation": 3072, "test": 9216},
        "training_epochs": 20, "training_example_passes": 11_059_200,
        "validation_plus_test_example_passes": 737_280,
        "total_learned_example_passes": 11_796_480, "final_checkpoints": 60,
    }
    assert CAPS == {
        "cpu_workers": 1, "learned_example_passes": 12_000_000,
        "wall_seconds": 3_600, "peak_rss_bytes": 2 * 1024**3,
    }


def test_cap_monitor_reads_positive_process_rss_and_retains_peak():
    monitor = run.CapMonitor()
    monitor.check()
    first = monitor.peak_rss
    assert first > 0
    monitor.check()
    assert monitor.peak_rss >= first
    usage = monitor.usage()
    assert usage["peak_rss_bytes"] >= first
    assert usage["peak_rss_bytes"] <= CAPS["peak_rss_bytes"]


def test_cap_monitor_fails_closed_when_rss_measurement_fails(monkeypatch):
    monitor = run.CapMonitor()

    def unavailable():
        raise OSError(5, "GetProcessMemoryInfo failed")

    monkeypatch.setattr(run, "_rss_bytes", unavailable)
    with pytest.raises(OSError, match="GetProcessMemoryInfo failed"):
        monitor.check()
