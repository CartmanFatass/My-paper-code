"""Engineering fixtures are synthetic scores, never new empirical observations."""

import inspect
import json
from pathlib import Path
import time

import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options.raw_cycle_readout_b02 import experiment as e
from scripts import run_crto_raw_cycle_readout_b02 as runner


def test_mean_precision_order_and_legal_tie():
    predictions = {u: np.zeros((1, 8), dtype=np.float32) for u in (253, 254, 255)}
    predictions[253][0, :2] = (2**24, 2**24)
    predictions[254][0, :2] = (1, 1)
    predictions[255][0, :2] = (-2**24, -2**24)
    mean = e.cycle_mean(predictions, 255)
    assert mean.dtype == np.float64
    assert mean[0, 0] == 1 / 3
    # A large illegal score cannot beat two exactly tied legal scores.
    mean[0, 7] = 1e10
    legal = np.array([True, True] + [False] * 6)
    assert e.base.select_printed_action(mean[0], legal) == 0
    predictions[253][0, 0] = 2**60
    predictions[254][0, 0] = -(2**60)
    predictions[255][0, 0] = 1
    assert e.cycle_mean(predictions, 255)[0, 0] == 1 / 3


@pytest.mark.parametrize("d,cycle,endpoint,branch", [
    ([-0.0025001, 0.1, 0.1], True, False, "B02-MATERIAL-REGRET-LOSS"),
    ([-0.0025, 0, 0], True, False, "B02-CYCLE-COMPETENCE-STABILIZED"),
    ([0, 0, 0], True, True, "B02-BOTH-READOUTS-COMPETENT"),
    ([0, 0, 0], False, True, "B02-CYCLE-COMPETENCE-NOT-STABILIZED"),
])
def test_rule_precedence_and_exact_mei(d, cycle, endpoint, branch):
    assert e.apply_result_rule(d, cycle, endpoint) == branch


def test_shared_training_semantics_and_budget():
    # Pin every source statement in the copied loop to the accepted helper.
    old = inspect.getsource(e.base._train)
    new = inspect.getsource(e.train_raw).replace("base.", "")
    new = new.replace("def train_raw(", "def _train(").replace("check_wall(started)", "_check_wall(started)")
    assert new == old
    started = time.perf_counter()
    with pytest.raises(TimeoutError, match="600-second"):
        e.check_wall(started - 601)
    e.base._check_wall(started - 601)  # historical globals have not been changed
    cost = e.project_cost()
    assert abs(cost["projected_arm_seconds"] - 240.3031404289761) < 1e-9
    assert cost["prospective_work_counts"]["raw_processed_examples"] == 8224
    assert cost["prospective_work_counts"]["network_forward_rows"] == 80
    assert cost["prospective_work_counts"]["scored_decisions"] == 96
    for ending in e.ENDINGS:
        order = np.resize(np.arange(48), ending * 32)
        assert np.array_equal(np.bincount(order[-96:]), np.full(48, 2))


def test_formal_publication_with_native_labels_and_synthetic_predictions(tmp_path):
    labels = json.loads(Path(__file__).with_name("native_labels.json").read_text())["rows"]
    # This deliberately arbitrary deterministic score family is not trained or historical.
    predictions = {u: np.array([[((i * 7 + a * 3 + u) % 11) / 10
                                for a in range(8)] for i in range(16)], dtype=np.float32)
                   for u in e.SNAPSHOTS}
    copies = {u: p.copy() for u, p in predictions.items()}
    exposures = [e.base._exposure_line(u, e.base.INITIAL_ANCHOR, None) for u in e.SNAPSHOTS]
    summary = e.readout_summary(labels, predictions, exposures)
    summary["engineering_only"] = "synthetic predictions, existing native labels; no learner or empirical claim"
    e.publish_summary(tmp_path, summary)
    loaded = json.loads((tmp_path / "summary.json").read_text())
    assert len(loaded["snapshots"]) == 5
    assert sum(len(s["rows"]) for s in loaded["snapshots"].values()) == 80
    assert len(loaded["endings"]) == 3
    assert sum(len(p[a]["rows"]) for p in loaded["endings"].values()
               for a in ("ENDPOINT", "CYCLE")) == 96
    assert any(v < 0 for row in labels for v in row["g16"] if v is not None)
    for u, pair in loaded["endings"].items():
        assert pair["exposure"]["processed_examples"] == 32 * int(u)
        assert pair["window_updates"] == list(range(int(u) - 2, int(u) + 1))
        assert pair["ENDPOINT"]["sides"]["KEEP"]["row_count"] == 8
        assert pair["ENDPOINT"]["sides"]["REPLAN"]["row_count"] == 8
        for i, (endpoint, cycle) in enumerate(zip(pair["ENDPOINT"]["rows"], pair["CYCLE"]["rows"])):
            assert endpoint["row_key"] == cycle["row_key"] == labels[i]["row_key"]
            assert endpoint["legal_g16"] == cycle["legal_g16"]
            for action, value in cycle["legal_prediction"].items():
                source = [loaded["snapshots"][str(v)]["rows"][i]["legal_prediction"][action]
                          for v in pair["window_updates"]]
                assert value == ((source[0] + source[1]) + source[2]) / 3
            for row in (endpoint, cycle):
                values = row["legal_g16"]
                assert row["native_regret"] == max(values.values()) - values[row["selected_action"]]
    assert all(np.array_equal(predictions[u], copies[u]) for u in e.SNAPSHOTS)
    corrupt = {**predictions, 253: predictions[253].copy()}
    corrupt[253][0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        e.readout_summary(labels, corrupt, exposures)


def test_one_toy_runner_smoke(tmp_path, monkeypatch, capsys):
    # Count the single learner path and ensure every forward follows its completion.
    original_train, original_forward = e.train_raw, e.forward_snapshots
    calls = []
    def train(*args, **kwargs):
        result = original_train(*args, **kwargs)
        assert len({id(v) for v in result[0].values()}) == 5
        assert all(not v.training for v in result[0].values())
        calls.append("train_completed")
        return result
    def forward(*args, **kwargs):
        assert calls == ["train_completed"]
        calls.append("forward")
        return original_forward(*args, **kwargs)
    monkeypatch.setattr(e, "train_raw", train)
    monkeypatch.setattr(e, "forward_snapshots", forward)
    assert runner.main(["run", "--toy", "--output-dir", str(tmp_path),
                        "--execution-node", "local-engineering-smoke"]) == 0
    capsys.readouterr()
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert calls == ["train_completed", "forward"]
    assert summary["result_branch"] is None
    assert summary["work_counts"]["raw_gate_updates"] == 5
    assert summary["work_counts"]["network_forward_rows"] == 30
    assert summary["work_counts"]["scored_decisions"] == 36
    assert summary["resources"]["wall_seconds"] < 60
    assert all(s["exposure"]["parameter_displacement_l2_over_initial_l2"] > 0
               for s in summary["snapshots"].values())
