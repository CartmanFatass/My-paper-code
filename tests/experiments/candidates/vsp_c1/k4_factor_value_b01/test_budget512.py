"""Focused B02 checks: no model construction, training loop or evaluation smoke."""
import ast
import importlib.util
from pathlib import Path
import sys

import pytest

from experiments.candidates.vsp_c1.k4_factor_value_b01.budget512 import epsilon_at
from experiments.candidates.vsp_c1.k4_factor_value_b01.reporting import budget512_metrics, curve_metrics

ROOT = Path(__file__).resolve().parents[5]


def test_epsilon_schedule_matches_b01_prefix_then_constant():
    for update in range(128):
        assert epsilon_at(update) == 1 - 0.9 * update / 127
    # Real-arithmetic 0.1; B01 evaluates 1 - 0.9 * 127/127 as 1 - 0.9, not the binary of 0.1.
    assert epsilon_at(127) == 1 - 0.9
    for update in range(128, 512):
        assert epsilon_at(update) == 0.1


def test_budget512_metrics_three_windows_on_synthetic_curve():
    curve = [{"update": 16 * i, "mean_return": 1 - i / 32} for i in range(33)]
    metrics = budget512_metrics(curve)
    assert metrics["initial_return"] == 1
    assert metrics["return_128"] == 0.75
    assert metrics["return_512"] == 0
    assert metrics["learning_gain_0_512"] == -1
    assert metrics["learning_gain_128_512"] == -0.75
    assert metrics["auc_0_128"] == 0.875
    assert metrics["auc_0_512"] == 0.5
    assert metrics["auc_128_512"] == 0.375
    assert metrics["auc_0_128"] == curve_metrics(curve[:9])["normalized_auc"]


def test_card_arithmetic_without_a_model_or_rollout():
    cycles, batch, horizon, checkpoints, eval_episodes = 512, 32, 6, 33, 8
    p2_episodes = p6_episodes = 16
    training = {
        "episodes": cycles * batch,
        "joint_steps": cycles * batch * horizon,
        "renewals": cycles * (p2_episodes * 3 + p6_episodes * 1),
        "legal_decisions": cycles * (p2_episodes * 3 + p6_episodes * 1),
        "renewals_p2": cycles * p2_episodes * 3,
        "renewals_p6": cycles * p6_episodes * 1,
    }
    evaluation = {
        "episodes": checkpoints * eval_episodes,
        "joint_steps": checkpoints * eval_episodes * horizon,
        "renewals": checkpoints * (4 * 3 + 4 * 1),
        "legal_decisions": checkpoints * (4 * 3 + 4 * 1),
        "renewals_p2": checkpoints * 4 * 3,
        "renewals_p6": checkpoints * 4 * 1,
    }
    assert training == {"episodes": 16384, "joint_steps": 98304, "renewals": 32768,
                        "legal_decisions": 32768, "renewals_p2": 24576, "renewals_p6": 8192}
    assert evaluation == {"episodes": 264, "joint_steps": 1584, "renewals": 528,
                          "legal_decisions": 528, "renewals_p2": 396, "renewals_p6": 132}
    assert cycles == 512
    assert (6 * 16 + 16) + (16 * 4 + 4) + 2 * 4 == 188
    assert (8 * 19 + 19) + (19 + 1) == 191


def test_source_parses_and_imports_without_scientific_path():
    paths = [ROOT / "scripts/run_vspc1_k4_factor_value_b02_budget512.py",
             ROOT / "experiments/candidates/vsp_c1/k4_factor_value_b01/budget512.py",
             ROOT / "experiments/candidates/vsp_c1/k4_factor_value_b01/reporting.py"]
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    import experiments.candidates.vsp_c1.k4_factor_value_b01.budget512 as budget512
    import experiments.candidates.vsp_c1.k4_factor_value_b01.reporting as reporting
    assert callable(budget512.run)
    assert callable(reporting.budget512_metrics)


def test_runner_refuses_seeds_other_than_3(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "run_vspc1_k4_factor_value_b02_budget512",
        ROOT / "scripts/run_vspc1_k4_factor_value_b02_budget512.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for seed in (0, 1, 2, 4):
        monkeypatch.setattr(sys, "argv", [
            "run_vspc1_k4_factor_value_b02_budget512.py",
            "--arm", "FACTOR", "--seed", str(seed), "--out", "x",
        ])
        with pytest.raises(SystemExit) as raised:
            mod.main()
        assert raised.value.code != 0
