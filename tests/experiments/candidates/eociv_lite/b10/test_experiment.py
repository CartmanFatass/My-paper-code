from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from experiments.candidates.eociv_lite.b10 import experiment as b10


ROOT = Path(__file__).resolve().parents[5]
RUNNER = ROOT / "scripts" / "run_eociv_b10_receiver_credit_frozen_score_exposure_curve.py"


def _metric_row(**overrides: float) -> dict[str, float]:
    row = {metric: 1.0 for metric in b10.METRICS}
    row["phi_0"] = 0.0
    row.update(overrides)
    return row


def _aggregates() -> dict[str, object]:
    return {
        "global": _metric_row(),
        "by_initialization": {anchor: _metric_row() for anchor in b10.ANCHOR_IDS},
        "leave_one_profile": {profile: _metric_row() for profile in b10.PROFILE_NAMES},
        "leave_one_root": {str(index): _metric_row() for index in range(8)},
    }


def test_manifest_order_and_full_count_factorization() -> None:
    tapes = b10.load_collection_tapes(ROOT)
    assert len(tapes) == 36
    assert [row["tape_index"] for row in tapes] == list(range(36))
    assert [row["collection_root"] for row in tapes[:4]] == [990100, 990101, 990102, 990103]
    assert tapes[-1]["anchor_id"] == "A2"
    assert tapes[-1]["forced_critical_shock_tuple"] == ["B", "B"]
    counts = b10.FULL_PLAN.expected_counts()
    assert counts["collection_episodes"] == 36
    assert counts["evaluation_episodes"] == 1008
    assert counts["episodes"] == 1044
    assert counts["environment_transitions"] == 50112
    assert counts["policy_calls"] == 50112
    assert counts["optimizer_calls"] == 96
    assert counts["gradient_computations"] == 6
    assert counts["gradient_recomputations"] == 0
    assert counts["critic_updates"] == 0
    assert counts["retry"] == counts["rescue"] == counts["sweep"] == 0


def test_exposure_line_matches_three_carded_initializations() -> None:
    expected = {
        "A0": (10.009484810505533, 0.0006808232535412728),
        "A1": (8.103020076903935, 0.0008410061866172912),
        "A2": (9.23913725716857, 0.0007375894334368576),
    }
    for anchor, (initial_l2, one_ratio) in expected.items():
        exposure = b10.exposure_for_anchor(anchor)
        assert exposure["active_parameter_count"] == 516
        assert exposure["initial_active_parameter_l2"] == pytest.approx(initial_l2)
        assert exposure["one_step_adam_l2_upper_bound"] == pytest.approx(0.006814690014960328)
        assert exposure["one_step_upper_ratio_vs_initialization"] == pytest.approx(one_ratio)
        assert exposure["sixteen_step_triangle_l2_upper_bound"] == pytest.approx(
            0.10903504023936525
        )


def test_fixed_gradient_adam_evolves_moments_without_mutating_gradient(monkeypatch) -> None:
    actor = b10._new_actor("A0")
    anchor_state = b10._clone_state(actor)
    gradient = tuple(torch.full_like(parameter, 0.125)
                     for _, parameter in b10._actor_parameters(actor))
    counts = b10.empty_counts()
    meter = b10.BoundaryMeter.start()
    endpoints, facts, rows = b10._apply_fixed_gradient_branch(
        "A0", anchor_state, gradient, b10.RECEIVER_ADDRESSED, counts, meter
    )
    assert set(endpoints) == {1, 4, 16}
    assert len(rows) == 16
    assert [row["optimizer_state_steps"] for row in rows] == [[index] for index in range(1, 17)]
    assert all(row["same_fixed_gradient_before_step"] for row in rows)
    assert all(row["same_fixed_gradient_after_step"] for row in rows)
    assert facts["empty_optimizer_state_before"] is True
    assert facts["fixed_gradient_tensor_equal_before_vs_after_16_steps"] is True
    assert facts["value_parameters_unchanged"] is True
    assert counts["optimizer_calls"] == 16
    assert counts["receiver_optimizer_calls"] == 16
    assert counts["gradient_recomputations"] == 0
    assert rows[0]["actual_l2_displacement"] < rows[3]["actual_l2_displacement"]
    assert rows[3]["actual_l2_displacement"] < rows[15]["actual_l2_displacement"]


def test_terminal_branch_uses_only_m16_and_all_robust_families() -> None:
    aggregates = _aggregates()
    assert b10.select_branch(aggregates) == b10.EDGE_BRANCH
    aggregates["global"]["J_1"] = -100.0
    aggregates["global"]["Delta_R4"] = -100.0
    assert b10.select_branch(aggregates) == b10.EDGE_BRANCH
    aggregates["leave_one_root"]["7"]["J_16"] = 0.0
    assert b10.select_branch(aggregates) == b10.NOT_SUPPORTED_BRANCH
    aggregates = _aggregates()
    aggregates["by_initialization"]["A2"]["R_16_v0"] = -1e-12
    assert b10.select_branch(aggregates) == b10.NOT_SUPPORTED_BRANCH
    aggregates = _aggregates()
    aggregates["global"]["J_16"] = float("nan")
    assert b10.select_branch(aggregates) == b10.INVALID_BRANCH
    assert b10.select_branch({}, valid=False) == b10.INVALID_BRANCH


def test_rss_failure_is_sticky_and_partial_failure_has_no_scientific_payload(
    tmp_path: Path, monkeypatch,
) -> None:
    observations = iter((100, OSError("rss unavailable"), 250))

    def observed_rss() -> int:
        value = next(observations)
        if isinstance(value, OSError):
            raise value
        return value

    monkeypatch.setattr(b10.b9r1, "peak_rss_bytes", observed_rss)
    meter = b10.BoundaryMeter.start()
    meter.check("episode")
    meter.check("adam")
    telemetry = meter.telemetry()
    assert telemetry["resources_unmeasured"] is True
    assert telemetry["peak_rss_bytes"] == 250
    assert telemetry["rss_measurement_error"] == "rss unavailable"

    def fail_after_one_episode(plan, run_meter, progress, repository_root):
        progress.phase = "collection:A0"
        b10._record_episode(progress.counts, "collection")
        raise RuntimeError("injected learner failure")

    monkeypatch.setattr(b10, "_run_science", fail_after_one_episode)
    monkeypatch.setattr(b10.b9r1, "peak_rss_bytes", lambda: 100)
    summary = b10.run_experiment(
        mode="smoke",
        seed=b10.ROOT_SET_SELECTOR,
        run_root=tmp_path / "partial",
        repository_root=ROOT,
        exact_command=(sys.executable, "injected"),
    )
    assert summary["status"] == b10.INVALID_BRANCH
    assert summary["evidence_class"] == "NONE / SMOKE_ONLY"
    assert summary["result_bearing"] is False
    assert summary["scientific_polarity"] is None
    assert summary["failure_phase"] == "collection:A0"
    assert summary["counts"]["episodes"] == 1
    assert "cells" not in summary
    assert "aggregates" not in summary
    assert "optimizer_step_rows" not in summary

    full_summary = b10.run_experiment(
        mode="full",
        seed=b10.ROOT_SET_SELECTOR,
        run_root=tmp_path / "full_metadata_only",
        repository_root=ROOT,
        exact_command=(sys.executable, "injected-full"),
    )
    assert full_summary["evidence_class"] == "B / EXPLORE"
    assert full_summary["result_bearing"] is True
    assert full_summary["scientific_polarity"] is None


def test_smoke_runs_real_toy_path_and_never_calls_scientific_branch(
    tmp_path: Path, monkeypatch,
) -> None:
    run_root = tmp_path / "b10_smoke"
    completed = subprocess.run(
        [
            sys.executable, str(RUNNER), "--mode", "smoke",
            "--seed", str(b10.ROOT_SET_SELECTOR), "--run-root", str(run_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    summary = json.loads((run_root / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "SMOKE_COMPLETE"
    assert summary["branch"] == "SMOKE_COMPLETE"
    assert summary["evidence_class"] == "NONE / SMOKE_ONLY"
    assert summary["result_bearing"] is False
    assert summary["scientific_polarity"] is None
    assert summary["counts"] == b10.SMOKE_PLAN.expected_counts()
    assert len(summary["cells"]) == 1
    assert len(summary["cells"][0]["Y"]) == 7
    assert len(summary["optimizer_step_rows"]) == 32
    assert summary["common_trajectory_and_complete_score_identity"] is True
    assert summary["anchors"][0]["common_batch"]["trajectory_count"] == 12
    assert summary["anchors"][0]["common_batch"]["term_count"] == 288
    assert all(
        fact["empty_optimizer_state_before"]
        for fact in summary["anchors"][0]["branch_initial_and_fixed_gradient_facts"]
    )
    assert summary["counts"]["gradient_recomputations"] == 0
    assert summary["telemetry"]["wall_seconds"] < 60.0
    assert summary["seed_semantics"]["does_not_change_anchor_initialization_seeds"] is True
    assert summary["launch_sha"]
    assert summary["exact_command"]
