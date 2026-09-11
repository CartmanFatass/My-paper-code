"""Mathematical loss checks, fixed-evidence joining and one toy publication smoke."""

from copy import deepcopy
import inspect
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options.raw_centered_loss_b07 import experiment as e
from scripts import run_crto_raw_centered_loss_b07 as runner


def test_centering_pooled_denominator_illegal_entries_and_gradient():
    p = e.torch.tensor([[0., 2., 900.], [0., 0., 3.]], requires_grad=True)
    y = e.torch.tensor([[0., 0., -700.], [0., 0., 0.]])
    legal = e.torch.tensor([[True, True, False], [True, True, True]])
    loss = e.centered_loss(p, y, legal)
    assert loss.dtype == e.torch.float32
    assert float(loss.detach()) == pytest.approx(8 / 5)
    loss.backward()
    assert e.torch.allclose(p.grad, e.torch.tensor([[-.4, .4, 0.], [-.4, -.4, .8]]), atol=1e-7)
    shifted_p = p.detach() + e.torch.tensor([[9.], [-4.]])
    shifted_y = y + e.torch.tensor([[-6.], [8.]])
    assert e.torch.equal(e.centered_loss(shifted_p, shifted_y, legal), loss.detach())


def test_separate_fp32_means_and_prediction_mean_autograd():
    # FP32 rounding makes centered residual sum nonzero: detach/error-first variants differ.
    p = e.torch.tensor([[16777216., 0.]], requires_grad=True)
    y = e.torch.tensor([[16777218., 1.]])
    loss = e.centered_loss(p, y, e.torch.ones_like(p, dtype=e.torch.bool))
    assert float(loss.detach()) == .5
    loss.backward()
    assert e.torch.equal(p.grad, e.torch.tensor([[-.5, .5]]))
    error = p.detach() - y
    assert not e.torch.equal(loss.detach(), ((error - error.mean(dim=1, keepdim=True)) ** 2).mean())


def test_loop_only_changes_loss_call():
    observed = inspect.getsource(e.train_path).replace("centered_loss(prediction, target, legal)",
                                                    "base.legal_masked_mse(prediction, target, legal)")
    assert observed == inspect.getsource(e.b04.train_path)
    assert e.check_wall is e.b04.check_wall


@pytest.mark.parametrize("d,competent,branch", [
    (-.0006251, True, "B07-MATERIAL-NATIVE-COST"),
    (-.0006251, False, "B07-MATERIAL-NATIVE-COST"),
    (.1, False, "B07-COMPARATOR-STILL-WEAK"),
    (.0006251, True, "B07-COMPETENCE-WITH-NATIVE-GAIN"),
    (.000625, True, "B07-COMPETENCE-WITHIN-MEI"),
    (-.000625, True, "B07-COMPETENCE-WITHIN-MEI"),
])
def test_first_matching_rule(d, competent, branch):
    assert e.result_rule(d, competent) == branch


def test_aggregate_and_cost_projection():
    cost, weak, good = "B07-MATERIAL-NATIVE-COST", "B07-COMPARATOR-STILL-WEAK", "B07-COMPETENCE-WITHIN-MEI"
    assert e.aggregate_rule({1: cost, 2: weak}) == "B07-COST-PRESENT"
    assert e.aggregate_rule({1: good, 2: weak}) == "B07-COMPARATOR-LIMITED"
    assert e.aggregate_rule({1: good, 2: good}) == "B07-COMPETENT-BOTH"
    assert e.aggregate_rule({1: good}) is None
    assert e.aggregate_rule({1: good, 2: None}) is None
    assert e.project_cost(1)["projected_arm_seconds"] == pytest.approx(268.05648790193663)
    assert e.project_cost(2)["projected_arm_seconds"] == pytest.approx(260.2336904819822)


def test_formal_baseline_join_and_publication(tmp_path):
    baseline_path = Path(__file__).parents[5] / "docs/research/candidates/commitment_residual_triggered_options/CRTO_RAW_EXPOSURE_B06_SEED01_RESULT_20260905.json"
    baseline = json.loads(baseline_path.read_text())["endpoints"]["516"]
    labels = [{k: r[k] for k in ("row_key", "material_side", "legal_mask", "g16")} for r in baseline["rows"]]
    treatment = e.raw.score_readout(labels, np.zeros((16, 8), dtype=np.float32))
    shuffled = deepcopy(baseline)
    shuffled["rows"].reverse()
    summary = e.compare_readouts(shuffled, treatment)
    summary["engineering_only"] = "fixed B06 baseline with synthetic untrained treatment predictions"
    e.raw.publish_summary(tmp_path, summary)
    loaded = json.loads((tmp_path / "summary.json").read_text())
    assert len(loaded["baseline"]["rows"]) == len(loaded["treatment"]["rows"]) == 16
    assert len(loaded["native_alignment"]) == 16
    assert all(r["identity_aligned"] and r["native_labels_aligned"] for r in loaded["native_alignment"])
    assert loaded["D"] == pytest.approx(sum(r["paired_regret_difference"] for r in loaded["changed_actions"]) / 16)
    mismatched = deepcopy(treatment)
    row = mismatched["rows"][0]
    first_action = next(iter(row["legal_g16"]))
    row["legal_g16"][first_action] += .001
    with pytest.raises(ValueError, match="native labels"):
        e.compare_readouts(baseline, mismatched)


def test_one_toy_smoke_only_final_snapshot(tmp_path, monkeypatch):
    _, evaluation, metadata = e.base._toy_population()
    prior = e.raw.score_readout(e.raw.panel_labels(evaluation, metadata), np.zeros((6, 8), dtype=np.float32))
    baseline_path = tmp_path / "synthetic_baseline.json"
    baseline_path.write_text(json.dumps({"seed": 1, "endpoints": {"516": prior}, "engineering_only": True}))
    original_train, original_forward = e.train_path, e.raw.forward_snapshots
    stages = []
    def train(*args, **kwargs):
        assert kwargs["trace_updates"] == (6,)
        assert kwargs["seed"] == 1
        result = original_train(*args, **kwargs)
        stages.append("train")
        return result
    def forward(*args, **kwargs):
        assert stages == ["train"]
        assert len(args[0]) == 1
        stages.append("forward")
        return original_forward(*args, **kwargs)
    monkeypatch.setattr(e, "train_path", train)
    monkeypatch.setattr(e.raw, "forward_snapshots", forward)
    output = tmp_path / "output"
    assert runner.main(["--seed", "1", "--toy", "--execution-node", "local-engineering-smoke",
                        "--baseline-summary", str(baseline_path), "--output-dir", str(output)]) == 0
    summary = json.loads((output / "summary.json").read_text())
    assert stages == ["train", "forward"]
    assert summary["result_branch"] is None and summary["thread_contract"]["matches"]
    assert summary["resources"]["wall_seconds"] < 60
    assert summary["work_counts"]["gate_updates"] == 6
    assert summary["work_counts"]["new_forward_rows"] == summary["work_counts"]["new_scored_decisions"] == 6
    assert summary["work_counts"]["historical_decisions_read"] == 6
    assert len(summary["native_alignment"]) == 6
