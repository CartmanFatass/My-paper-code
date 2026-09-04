from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.candidates.eociv_lite.b9r1 import experiment as b9r1


ROOT = Path(__file__).resolve().parents[5]
RUNNER = ROOT / "scripts" / "run_eociv_b9r1_receiver_addressed_credit.py"


def _row(**overrides: float) -> dict[str, float]:
    row = {
        "phi_0": 0.0,
        "phi_R": 2.0,
        "phi_S": 1.0,
        "Delta_R": 2.0,
        "J": 1.0,
        "receiver_correct_vs_anchor": 1.0,
        "receiver_correct_vs_source": 0.5,
        "source_correct_vs_anchor": 0.5,
        "receiver_two_arm_generic_gain": 0.0,
    }
    row.update(overrides)
    return row


def _aggregates(global_row: dict[str, float] | None = None) -> dict[str, object]:
    global_row = _row() if global_row is None else global_row
    return {
        "global": global_row,
        "by_anchor": {"A0": _row(), "A1": _row()},
        "leave_one_profile": {name: _row() for name in b9r1.PROFILE_NAMES},
        "leave_one_root": {str(index): _row() for index in range(8)},
    }


def test_full_count_factorization_is_exact() -> None:
    counts = b9r1.FULL_PLAN.expected_counts()
    assert counts["collection_episodes"] == 24
    assert counts["evaluation_episodes"] == 288
    assert counts["episodes"] == 312
    assert counts["environment_transitions"] == 14_976
    assert counts["policy_calls"] == 14_976
    assert counts["optimizer_calls"] == 4
    assert counts["receiver_optimizer_calls"] == 2
    assert counts["source_control_optimizer_calls"] == 2
    assert counts["critic_loss_calls"] == 0
    assert counts["global_clip_calls"] == 0
    assert counts["second_updates"] == 0


def test_exposure_line_matches_carded_anchor_budgets() -> None:
    expected = {
        "A0": (10.009484810505533, 6.808232535412728e-4),
        "A1": (8.103020076903935, 8.410061866172912e-4),
    }
    for anchor_id, (initial_l2, ratio) in expected.items():
        exposure = b9r1.exposure_for_anchor(anchor_id)
        assert exposure["active_parameter_count"] == 516
        assert exposure["one_step_adam_l2_upper_bound"] == pytest.approx(
            0.006814690014960328
        )
        assert exposure["initial_active_parameter_l2"] == pytest.approx(initial_l2)
        assert exposure["upper_bound_ratio_vs_initialization"] == pytest.approx(ratio)
        assert exposure["initialization_seed"] == b9r1.ANCHOR_SEEDS[anchor_id]


def test_branch_precedence_and_invalidity() -> None:
    assert b9r1.select_branch(_aggregates()) == b9r1.VALID_BRANCHES[0]

    damaged = _aggregates(_row(receiver_correct_vs_anchor=-0.1))
    assert b9r1.select_branch(damaged) == b9r1.VALID_BRANCHES[1]

    unsupported = _aggregates(_row(J=-0.1, Delta_R=0.5))
    unsupported["by_anchor"] = {
        "A0": _row(J=0.0, Delta_R=0.5),
        "A1": _row(J=-0.2, Delta_R=0.5),
    }
    assert b9r1.select_branch(unsupported) == b9r1.VALID_BRANCHES[2]

    mixed = _aggregates(_row(J=0.5, Delta_R=0.5))
    mixed["by_anchor"] = {
        "A0": _row(J=0.2, Delta_R=0.5),
        "A1": _row(J=-0.2, Delta_R=0.5),
    }
    assert b9r1.select_branch(mixed) == b9r1.VALID_BRANCHES[3]
    assert b9r1.select_branch(_aggregates(), valid=False) == b9r1.INVALID_BRANCH
    assert b9r1.select_branch({}) == b9r1.INVALID_BRANCH


def test_rss_failure_is_sticky_and_preserves_observed_peak(monkeypatch) -> None:
    observations = iter((100, OSError("rss unavailable"), 250))

    def observed_rss() -> int:
        value = next(observations)
        if isinstance(value, OSError):
            raise value
        return value

    monkeypatch.setattr(b9r1, "peak_rss_bytes", observed_rss)
    meter = b9r1.EpisodeBoundaryMeter.start()
    meter.check()
    meter.check()
    telemetry = meter.telemetry()
    assert telemetry["resources_unmeasured"] is True
    assert telemetry["peak_rss_bytes"] == 250
    assert telemetry["rss_measurement_error"] == "rss unavailable"


def test_failure_summary_keeps_partial_counts_and_phase(tmp_path: Path, monkeypatch) -> None:
    def fail_after_one_episode(plan, meter, progress):
        progress.phase = "collection:A0"
        b9r1._record_episode(progress.counts, "collection")
        raise RuntimeError("injected learner failure")

    monkeypatch.setattr(b9r1, "_run_science", fail_after_one_episode)
    summary = b9r1.run_experiment(
        mode="smoke",
        seed=b9r1.ROOT_SET_SELECTOR,
        run_root=tmp_path / "partial",
        repository_root=ROOT,
        exact_command=(sys.executable, "injected"),
    )
    assert summary["status"] == "INVALID_ATTEMPT"
    assert summary["scientific_polarity"] is None
    assert summary["failure_phase"] == "collection:A0"
    assert summary["counts"]["episodes"] == 1
    assert summary["counts"]["collection_episodes"] == 1
    assert "cells" not in summary
    assert "aggregates" not in summary


def test_smoke_runs_real_end_to_end_and_writes_summary(tmp_path: Path) -> None:
    run_root = tmp_path / "b9r1_smoke"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--mode",
            "smoke",
            "--seed",
            str(b9r1.ROOT_SET_SELECTOR),
            "--run-root",
            str(run_root),
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
    assert summary["counts"] == b9r1.SMOKE_PLAN.expected_counts()
    assert len(summary["cells"]) == 1
    assert summary["anchors"][0]["common_trajectory_count"] == 12
    assert summary["anchors"][0]["common_term_count"] == 288
    assert summary["anchors"][0]["same_trajectory_score_tensors"] is True
    assert summary["anchors"][0]["receiver_step"]["value_head_unchanged"] is True
    assert summary["anchors"][0]["source_control_step"]["value_head_unchanged"] is True
    assert summary["telemetry"]["wall_seconds"] < 60.0
    assert summary["telemetry"]["process_cpu_seconds"] <= 300.0
    assert summary["seed_semantics"]["does_not_change_actor_initialization_seeds"] is True
    assert summary["launch_sha"]
    assert summary["exact_command"]
