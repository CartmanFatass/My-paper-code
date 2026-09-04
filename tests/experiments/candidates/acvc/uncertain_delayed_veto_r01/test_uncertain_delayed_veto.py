"""Host, result-rule, and one toy end-to-end test for ACVC R01."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments.candidates.acvc.uncertain_delayed_veto_r01 import experiment as EXP  # noqa: E402


def test_host_order_information_and_fixed_rules():
    bp = EXP.Blueprints(
        calibrated=np.array([True]),
        issuance_unsafe=np.array([[False] * 12]),
        current_unsafe=np.array([[True, False] + [False] * 10]),
        confidence=np.array([[0.9] * 12], dtype=np.float32),
        age=np.array([[0] * 12], dtype=np.int8),
        verdict=np.array([[True, False] + [False] * 10]),
    )
    execute_reward, execute_reveal = EXP._reward_and_reveal(
        EXP.torch.tensor([0]), EXP.torch.tensor([True]))
    probe_reward, probe_reveal = EXP._reward_and_reveal(
        EXP.torch.tensor([1]), EXP.torch.tensor([False]))
    veto_reward, veto_reveal = EXP._reward_and_reveal(
        EXP.torch.tensor([2]), EXP.torch.tensor([True]))
    assert (float(execute_reward[0]), bool(execute_reveal[0])) == (-4.0, True)
    assert float(probe_reward[0]) == pytest.approx(0.4)
    assert bool(probe_reveal[0]) is True
    assert (float(veto_reward[0]), bool(veto_reveal[0])) == (0.0, False)
    auth = EXP.fixed_actions("AUTH-PROBE", bp)
    assert tuple(auth[0, :2]) == (1, 0)
    det = EXP.det_cf_actions(bp)
    assert tuple(det[0, :2]) == (1, 0)
    balance = EXP.torch.zeros(1)
    count = EXP.torch.zeros(1)
    balance, count = EXP._update_summary(bp, 0, EXP.torch.tensor([False]), balance, count)
    assert float(balance[0]) == 0.0 and float(count[0]) == 0.0
    balance, count = EXP._update_summary(bp, 0, EXP.torch.tensor([True]), balance, count)
    assert float(balance[0]) == pytest.approx(0.8)
    raw = EXP._raw_inputs(
        bp, 1, EXP.torch.tensor([2]), EXP.torch.tensor([True]), EXP.torch.tensor([True]))
    assert raw.shape == (1, 10)
    assert raw[0, 4:8].tolist() == [0.0, 0.0, 1.0, 0.0]
    assert raw[0, 8:].tolist() == [1.0, 1.0]


def _arm(mean, unsafe=0.0, clean=0.0, episodes=8):
    return {
        "episode_return": {"mean": mean, "sd": 0.0, "all": [mean] * episodes},
        "unsafe_execution_rate": unsafe,
        "clean_opportunity_loss": clean,
    }


@pytest.mark.parametrize(("treatment", "gru", "unsafe_a", "unsafe_g", "branch"), [
    (1.30, 1.10, 0.0, 0.0, "B2-A / STRUCTURED_GATE_SIGNAL"),
    (1.00, 1.30, 0.0, 0.0, "B2-B / GENERIC_RECURRENCE_ONLY"),
    (1.30, 1.00, 0.03, 0.0, "B2-C / FIXED_RULE_CONTAINS"),
    (1.15, 1.00, 0.0, 0.0, "B2-D / LEARNING_UNRESOLVED"),
])
def test_result_rule(treatment, gru, unsafe_a, unsafe_g, branch):
    arms = {
        "DET-CF": _arm(1.0), "AUTH-PROBE": _arm(0.9),
        "ACVC-HISTORY-GATE": _arm(treatment, unsafe_a),
        "RAW-GRU": _arm(gru, unsafe_g),
    }
    assert EXP.apply_result_rule(arms)["branch"] == branch


def test_formal_run_rejects_a_false_arm_cost_before_launch_sha(tmp_path, monkeypatch):
    receipt = tmp_path / "admission.json"
    receipt.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
    }), encoding="utf-8")
    learned = {arm: {"within_cap": True} for arm in EXP.LEARNED_ARMS}
    fixed = {arm: {"within_cap": True} for arm in EXP.FIXED_ARMS}
    learned[EXP.LEARNED_ARMS[0]]["within_cap"] = False
    cost = tmp_path / "cost.json"
    cost.write_text(json.dumps({
        "object_id": EXP.OBJECT_ID, "command": "project-cost", "result_blind": True,
        "all_within_caps": False, "discarded_work": {}, "formula": {}, "exposure_line": {},
        "learned_arms": learned, "fixed_arms": fixed,
    }), encoding="utf-8")
    monkeypatch.setattr(
        EXP, "_launch_sha", lambda _root: pytest.fail("launch SHA captured before cost refusal"),
    )
    with pytest.raises(RuntimeError, match="does not admit every frozen arm"):
        EXP.run_object(
            tmp_path / "run", admission_receipt=receipt, project_cost_path=cost,
        )


def test_train_arm_rejects_an_expired_deadline_at_update_boundary():
    with pytest.raises(RuntimeError, match="optimizer update boundary"):
        EXP.train_arm(
            "ACVC-HISTORY-GATE", updates=1, batch_size=2,
            deadline=time.perf_counter() - 1.0,
        )


def test_toy_runner_is_complete_paired_and_under_sixty_seconds(tmp_path):
    receipt = tmp_path / "admission.json"
    receipt.write_text(json.dumps({
        "passed": True, "physical_floor_pass": True, "effective_floor_pass": True,
        "available_physical_bytes": 8 << 30, "effective_available_bytes": 8 << 30,
    }), encoding="utf-8")
    output = tmp_path / "run"
    started = time.perf_counter()
    completed = subprocess.run([
        sys.executable, str(PROJECT_ROOT / "scripts/run_acvc_uncertain_delayed_veto_r01.py"),
        "run", "--output-root", str(output), "--admission-receipt", str(receipt), "--toy",
    ], cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    record = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert elapsed < 60.0
    assert json.loads(completed.stdout)["summary"] == str(output / "summary.json")
    assert record["complete"] is False and record["toy"] is True
    assert record["result_bearing"] is False
    assert record["technical_only"] is True
    assert record["evidence_class"] is None
    assert record["result_rule"] is None
    assert record["project_cost"] is None
    assert record["counts"]["optimizer_updates_per_learned_arm"] == 2
    assert record["counts"]["evaluation_episodes_per_arm"] == 32
    assert set(record["arms"]) == set(EXP.ARMS)
    assert all(len(record["arms"][arm]["episode_return"]["all"]) == 32 for arm in EXP.ARMS)
    assert all(record["arms"][arm]["actual_total_wall_seconds"] > 0.0 for arm in EXP.ARMS)
    assert all(record["arms"][arm]["wall_cap_enforced"] is False for arm in EXP.ARMS)
    assert record["arms"]["ACVC-HISTORY-GATE"]["training"]["nonzero_gradient_update_count"] == 2
    assert record["arms"]["RAW-GRU"]["training"]["nonzero_gradient_update_count"] == 2
    assert record["resources"]["wall_seconds"] > 0.0
