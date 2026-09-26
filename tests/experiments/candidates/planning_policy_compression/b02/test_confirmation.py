import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.finite_model_decision_value.b01.host import Worlds
from experiments.candidates.finite_model_decision_value.b01.study import sha256
from experiments.candidates.planning_policy_compression.b02.study import (
    Config, exact_sign_decision, run_study,
)


@pytest.fixture
def tiny():
    return Config(block_seeds=(5101, 5102, 5103, 5104, 5105),
        block_model_seeds=(5201, 5202, 5203, 5204, 5205),
        evaluation_seeds=(5301, 5302, 5303, 5304, 5305),
        evaluation_model_seeds=(5401, 5402, 5403, 5404, 5405),
        initial_contexts=1, rollout_contexts=1, evaluation_contexts=1,
        horizon=48, batch=1, epochs=(1, 1), train_batch=2, particles=2)


def test_exact_sign_and_ties():
    for positives, expected_p in enumerate((1., .96875, .8125, .5, .1875, .03125)):
        totals = (1,) * positives + (0,) * (5 - positives)
        assert exact_sign_decision(totals)["exact_one_sided_p"] == expected_p
    all_positive = exact_sign_decision((1, 2, 3, 4, 5))
    assert all_positive["confirmed"]
    assert all_positive["exact_one_sided_p"] == .03125
    assert all_positive["one_sided_95_clopper_pearson_lower"] == pytest.approx(.05 ** .2)
    four = exact_sign_decision((1, 2, 3, 4, -999))
    assert not four["confirmed"] and four["exact_one_sided_p"] == .1875
    tie = exact_sign_decision((1, 2, 3, 4, 0))
    assert tie["tied_blocks"] == 1 and tie["nonpositive_blocks"] == 1
    assert not tie["confirmed"] and tie["exact_one_sided_p"] == .1875
    assert exact_sign_decision((0, -1, -2, -3, -4))["one_sided_95_clopper_pearson_lower"] == 0
    assert exact_sign_decision((1, 0, 0, 0, 0))["exact_one_sided_p"] == .96875
    with pytest.raises(ValueError):
        exact_sign_decision((1, 2, 3, 4))
    with pytest.raises(ValueError):
        exact_sign_decision((1.1, 2, 3, 4, 5))


def test_five_block_complete_and_independent_panels(tmp_path, tiny):
    out = tmp_path / "fixture"
    summary = run_study(out, "fixture-sha", tiny)
    assert summary["state"] == "COMPLETE"
    counts = summary["counts"]
    assert counts["policy_fits_started"] == counts["policy_fits_completed"] == 10
    assert counts["blocks_completed"] == 5
    assert counts["optimizer_updates"] == 40  # 10*(1 stage1 + 3 stage2)
    assert counts["processed_agent_time_rows"] == 10 * 2 * 48 * (1 + 3)
    assert counts["endpoint_diagnostic_agent_time_rows"] == 5 * 2 * (2+6) * 48
    assert counts["collection_team_ticks"] == 5 * 3 * 48
    assert counts["evaluation_team_ticks"] == 5 * 4 * 48
    assert counts["calibration_fits"] == 5 * 4
    assert counts["calibration_moves"] == 5 * 4 * 4
    assert counts["model_branch_transition_upper"] == (5*3*48 + 5*48) * 2 * 2 * 32
    assert counts["model_branch_transitions"] <= counts["model_branch_transition_upper"]
    assert len(summary["fits"]) == 10 and len(summary["endpoint_diagnostics"]) == 20
    assert len(summary["formal_confirmation"]["integer_total_differences"]) == 5
    assert len(summary["descriptive_full_utility"]["blocks"]) == 5
    assert len(json.loads((out / "per_context.json").read_text())) == 5
    assert all(fit["parameter_movement_l2"] > 0 for fit in summary["fits"])
    for block in range(5):
        pair = [fit for fit in summary["fits"] if fit["block"] == block]
        assert pair[0]["initial_state_sha256"] == pair[1]["initial_state_sha256"]
        assert all(fit["updates"] == 4 for fit in pair)
        for arm in ("BC", "WBC"):
            first = torch.load(out / "raw" / f"block{block}_{arm}_stage1.pt", weights_only=False)
            final = torch.load(out / "raw" / f"block{block}_{arm}_final.pt", weights_only=False)
            assert {int(value["step"]) for value in first["optimizer"]["state"].values()} == {1}
            assert {int(value["step"]) for value in final["optimizer"]["state"].values()} == {4}
        with np.load(out / "raw" / f"block{block}_training.npz") as data:
            assert data["x"].shape == (6, 48, 35)
            assert data["mask"].any()
        costs = [cost for cost in summary["batch_costs"] if cost["block"] == block]
        for arm in ("BC", "WBC", "AF"):
            deployed = [cost for cost in costs if cost["arm"] == arm]
            assert len(deployed) == 1
            assert deployed[0]["model"] == {} and deployed[0]["filter"] == {}
        assert any(cost["arm"] == "P_k4_M32" and cost["model"]["model_root_decisions"] > 0
                   for cost in costs)
        with np.load(out / "raw" / f"block{block}_calibration_train.npz") as data:
            assert data["ids"].tolist() == [0, 1, 2]
        with np.load(out / "raw" / f"block{block}_calibration_eval.npz") as data:
            assert data["ids"].tolist() == [0]
        assert (out / "raw" / f"block{block}_evaluation_AF_0000.episodes.json").is_file()
    worlds = [Worlds.make(seed, 81, (0,), 48, .75).advances for seed in tiny.evaluation_seeds]
    assert any(not np.array_equal(worlds[0], world) for world in worlds[1:])
    # Every arm in a block used identical native exogenous addresses and theta.
    episodes = json.loads((out / "episodes.json").read_text())
    for block in range(5):
        assert {row["arm"] for row in episodes if row["block"] == block} == {"BC", "WBC", "P_k4_M32", "AF"}
        assert len({row["theta"] for row in episodes if row["block"] == block}) == 1
    assert all(sha256(out / item["path"]) == item["sha256"] for item in summary["artifacts"])
    training_states = []
    for block in range(5):
        with np.load(out / "raw" / f"block{block}_training.npz") as data:
            training_states.append(data["x"].copy())
    assert all(not np.array_equal(training_states[0], other) for other in training_states[1:])
    with pytest.raises(FileExistsError):
        run_study(out, "fixture-sha", tiny)


def test_partial_failure_no_formal_verdict(tmp_path, tiny, monkeypatch):
    import experiments.candidates.planning_policy_compression.b01.study as b01
    real_query = b01.paired_values
    calls = [0]
    def fail_second(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 2:
            raise RuntimeError("fixture query failure")
        return real_query(*args, **kwargs)
    monkeypatch.setattr(b01, "paired_values", fail_second)
    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="fixture query failure"):
        run_study(out, "fixture-sha", tiny)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "FAILED"
    assert "formal_confirmation" not in summary
    assert summary["status"]["blocks_completed"] == 0
    assert summary["status"]["executed_collection_team_ticks"] == 1
    path = out / "raw" / "block0_initial_TEACHER_0000.npz"
    with np.load(path) as trace:
        assert int(trace["observed_ticks"]) == 2
        assert int(trace["executed_ticks"]) == 1
        assert trace["mask"].sum() == 1
    assert any(item["path"] == "raw/block0_initial_TEACHER_0000.npz"
               for item in summary["artifacts"])


def test_later_evaluation_failure_preserves_completed_method_costs(tmp_path, tiny, monkeypatch):
    import experiments.candidates.planning_policy_compression.b01.study as b01
    import experiments.candidates.planning_policy_compression.b02.study as b02
    real_batch, real_query = b02.episode_batch, b01.paired_values
    calls = [0]
    def fail_second_query(*args, **kwargs):
        calls[0] += 1
        if calls[0] == 2:
            raise RuntimeError("later-arm query failure")
        return real_query(*args, **kwargs)
    def fail_in_teacher_arm(*args, **kwargs):
        if kwargs["arm"] == "P_k4_M32":
            monkeypatch.setattr(b01, "paired_values", fail_second_query)
        return real_batch(*args, **kwargs)
    monkeypatch.setattr(b02, "episode_batch", fail_in_teacher_arm)
    out = tmp_path / "failed-evaluation"
    with pytest.raises(RuntimeError, match="later-arm query failure"):
        run_study(out, "fixture-sha", tiny)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["state"] == "FAILED" and "formal_confirmation" not in summary
    assert summary["status"]["evaluation_team_ticks"] == 2 * 48
    assert summary["status"]["executed_evaluation_team_ticks"] == 2 * 48 + 1
    block = summary["block_timing"]["0"]
    assert block["state"] == "FAILED_PARTIAL"
    for arm in ("BC", "WBC"):
        complete = block["deployment_costs"][arm]
        assert complete["state"] == "COMPLETE"
        assert complete["conditional_total_seconds"] >= complete["batched_deployment_seconds"] > 0
    attempted = block["deployment_costs"]["P_k4_M32"]
    assert attempted["state"] == "FAILED_DEPLOYMENT"
    assert attempted["attempted_batched_deployment_seconds"] > 0
    assert "conditional_total_seconds" not in attempted
    with np.load(out / "raw" / "block0_evaluation_P_k4_M32_0000.npz") as trace:
        assert int(trace["executed_ticks"]) == 1
        assert int(trace["observed_ticks"]) == 2


def test_entry_refuses_before_science(tmp_path):
    root = Path(__file__).resolve().parents[5]
    out = tmp_path / "b02_confirm_s925951_20260925"
    env = os.environ.copy()
    env.pop("HMASD_LAUNCH_ADMISSION", None)
    process = subprocess.run([sys.executable, str(root / "scripts/run_ppc_b02.py"),
        "--out", str(out), "--launch-sha", "unadmitted"],
        cwd=root, env=env, capture_output=True, text=True)
    assert process.returncode != 0
    assert not out.exists()
