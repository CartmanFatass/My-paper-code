"""B06 branch boundaries, result-blind projection and one toy learner publication."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options.raw_exposure_b06 import experiment as e
from scripts import run_crto_raw_exposure_b06 as runner


@pytest.mark.parametrize("d,before,after,branch", [
    (-.0006251, True, True, "B06-MATERIAL-REGRET-COST"),
    (-.0006251, False, False, "B06-MATERIAL-REGRET-COST"),
    (.01, True, False, "B06-COMPARATOR-STILL-WEAK"),
    (.01, True, True, "B06-COMPETENCE-ALREADY-PRESENT"),
    (.0006251, False, True, "B06-COMPETENCE-RECOVERED-WITH-GAIN"),
    (.000625, False, True, "B06-COMPETENCE-RECOVERED-WITHIN-MEI"),
    (-.000625, False, True, "B06-COMPETENCE-RECOVERED-WITHIN-MEI"),
])
def test_first_match_and_inclusive_mei(d, before, after, branch):
    assert e.result_rule(d, before, after) == branch


def test_aggregate_preserves_weak_cost_and_partial_results():
    cost, weak, recovered, already = ("B06-MATERIAL-REGRET-COST", "B06-COMPARATOR-STILL-WEAK",
                                    "B06-COMPETENCE-RECOVERED-WITH-GAIN", "B06-COMPETENCE-ALREADY-PRESENT")
    assert e.aggregate_rule({1: cost, 2: weak}) == "B06-COST-PRESENT"
    assert e.aggregate_rule({1: recovered, 2: weak}) == "B06-COMPARATOR-LIMITED"
    assert e.aggregate_rule({1: recovered, 2: "B06-COMPETENCE-RECOVERED-WITHIN-MEI"}) == "B06-COMPETENCE-RECOVERED-BOTH"
    assert e.aggregate_rule({1: recovered, 2: already}) == "B06-ALREADY-PRESENT-OR-MIXED"
    assert e.aggregate_rule({1: recovered}) is None
    assert e.aggregate_rule({1: recovered, 2: None}) is None


def test_projection_is_model_free_and_seed_specific(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("projection must not create a learner")
    monkeypatch.setattr(e.base, "CommonHistoryGate", forbidden)
    projections = []
    for seed, expected in ((1, 470.19725153406034), (2, 466.55938091395365)):
        cost = e.project_cost(seed)
        assert cost["projected_seconds_by_update"]["516"] == pytest.approx(expected, abs=1e-10)
        assert cost["projected_seconds_by_update"]["516"] < cost["arm_cap_seconds"] == 1200
        assert [p["recipient_occurrences"] for p in cost["exposure_plan"]] == [172, 344]
        assert cost["work_plan"]["calibration_examples"] == cost["work_plan"]["derangement_packets"] == 0
        projections.append(cost["projected_seconds_by_update"]["516"])
    assert sum(projections) == pytest.approx(936.756632448014)


def test_full_panel_changed_actions_and_recipient_exposure(tmp_path):
    labels = json.loads((Path(__file__).parents[1] / "raw_cycle_readout_b02" / "native_labels.json").read_text())["rows"]
    train = [SimpleNamespace(key=SimpleNamespace(text=f"synthetic-train-{i}")) for i in range(48)]
    predictions = {u: np.zeros((16, 8), dtype=np.float32) for u in e.ENDPOINTS}
    # Deliberately synthetic before/after choices: change exactly one legal action.
    for i, row in enumerate(labels):
        legal = np.flatnonzero(row["legal_mask"])
        predictions[258][i, legal[0]] = 1
        predictions[516][i, legal[0]] = 1
    first_legal = np.flatnonzero(labels[0]["legal_mask"])
    predictions[516][0, first_legal[0]] = 0
    predictions[516][0, first_legal[1]] = 1
    exposures = [e.base._exposure_line(u, e.base.INITIAL_ANCHOR, {
        "parameter_displacement_l2_over_initial_l2": .1,
        "parameter_displacement_linf_over_initial_linf": .2}) for u in e.ENDPOINTS]
    summary = e.paired_readout(labels, predictions, exposures, train)
    summary["engineering_only"] = "synthetic predictions/exposure/TRAIN keys; accepted native EVAL labels"
    e.raw.publish_summary(tmp_path, summary)
    loaded = json.loads((tmp_path / "summary.json").read_text())
    assert sum(len(p["rows"]) for p in loaded["endpoints"].values()) == 32
    assert len(loaded["changed_actions"]) == 1
    changed = loaded["changed_actions"][0]
    assert changed["row_key"] == labels[0]["row_key"]
    assert loaded["D"] == pytest.approx(changed["paired_regret_difference"] / 16, abs=1e-15)
    for u, expected in ((258, 172), (516, 344)):
        point = loaded["endpoints"][str(u)]
        assert set(point["recipient_counts"].values()) == {expected}
        assert len(point["recipient_counts"]) == 48
        assert point["exposure"]["processed_examples"] == u * 32
        assert all(s["row_count"] == 8 for s in point["sides"].values())


def test_one_toy_smoke_shared_path_and_raw_only(tmp_path, monkeypatch):
    stages = []
    original_train, original_forward = e.b04.train_path, e.raw.forward_snapshots
    def forbidden(*args, **kwargs):
        raise AssertionError("RAW-only path must not prepare calibration or derangement")
    def train(*args, **kwargs):
        assert kwargs["seed"] == 1 and kwargs["representation"] == "RAW"
        assert kwargs["trace_updates"] == (3, 6)
        result = original_train(*args, **kwargs)
        stages.append("trained")
        return result
    def forward(*args, **kwargs):
        assert stages == ["trained"]
        stages.append("evaluated")
        return original_forward(*args, **kwargs)
    monkeypatch.setattr(e.b01, "canonical_calibration_tapes", forbidden)
    monkeypatch.setattr(e.b01, "fit_calibration_from_examples", forbidden)
    monkeypatch.setattr(e.b01, "derange_packets", forbidden)
    monkeypatch.setattr(e.b04, "train_path", train)
    monkeypatch.setattr(e.raw, "forward_snapshots", forward)
    assert runner.main(["--seed", "1", "--toy", "--execution-node", "local-engineering-smoke", "--output-dir", str(tmp_path)]) == 0
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert stages == ["trained", "evaluated"]
    assert summary["result_branch"] is None
    assert summary["thread_contract"]["matches"]
    assert summary["resources"]["wall_seconds"] < 60
    assert summary["work_counts"]["calibration_tapes"] == summary["work_counts"]["derangement_packets"] == 0
    assert summary["work_counts"]["gate_updates"] == 6
    assert summary["work_counts"]["network_forward_rows"] == summary["work_counts"]["scored_decisions"] == 12
