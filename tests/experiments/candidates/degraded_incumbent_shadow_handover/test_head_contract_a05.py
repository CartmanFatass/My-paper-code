import json
import time

from experiments.candidates.degraded_incumbent_shadow_handover import head_contract_a05 as probe
from scripts import run_dish_prediction_head_contract_a05 as runner


def test_mapping_reading_thresholds_and_alternatives():
    assert probe.mapping_rule(True, False, 0, 0.5) == "RAW_LOGIT_PASS_THROUGH"
    assert probe.mapping_rule(False, True, 0.5, 0) == "LINKED_PROBABILITY_MAPPING"
    assert probe.mapping_rule(True, False, 0, 1e-6) == "OTHER_MAPPING_READOUT"
    assert probe.mapping_rule(False, False, 0.5, 0.5) == "OTHER_MAPPING_READOUT"


def test_graph_connection_is_distinct_from_zero_gradient():
    names = ("prediction_cholesky.weight", "prediction_cholesky.bias")
    absent = {name: {"grad_none": True, "finite": None, "l1": None} for name in names}
    control = {name: {"grad_none": False, "finite": True, "l1": 1.0} for name in names}
    assert probe.graph_rule(absent, control, True) == "CHOLESKY_OMITTED_FROM_TRAINING_HEAD_GRAPH"
    zero = {name: {"grad_none": False, "finite": True, "l1": 0.0} for name in names}
    assert probe.graph_rule(zero, control, True) == "OTHER_TRAINING_HEAD_CONNECTION"
    assert probe.graph_rule(absent, zero, True) == "OTHER_TRAINING_HEAD_CONNECTION"
    assert probe.graph_rule(absent, control, False) == "OTHER_TRAINING_HEAD_CONNECTION"


def test_native_consumer_reading_preserves_all_alternatives():
    cases = [{"q95": {"raw": 0.2, "clipped": 0.2, "sigmoid": 0.25}}] * 3
    assert probe.consumer_rule(cases) == "NATIVE_CLIP_CONTRAST_REPRODUCED"
    same = [{"q95": {"raw": 0.2, "clipped": 0.2, "sigmoid": 0.2}}] * 3
    assert probe.consumer_rule(same) == "NO_DISCRIMINATING_CONSUMER_CONTRAST"
    different = [{"q95": {"raw": 0.2, "clipped": 0.25, "sigmoid": 0.2}}] * 3
    assert probe.consumer_rule(different) == "OTHER_NATIVE_CONSUMER_READOUT"


def test_noncard_genuine_toy_publication(tmp_path):
    started = time.perf_counter()
    result = runner.run(tmp_path / "external-admission.json", tmp_path / "published",
                        seed=50512, levels=(-1.0, 0.5, 1.0))
    summary = json.loads((tmp_path / "published" / "summary.json").read_text(encoding="utf-8"))
    assert 0 < result.pop("completed_runner_wall_seconds") < 60
    assert result.pop("completed_peak_rss_bytes") > 0
    assert result.pop("resources_unmeasured") is False
    assert result == summary
    assert summary["synthetic_seed"] == 50512 and not summary["model_training_mode"]
    assert [case["level"] for case in summary["native_cases"]] == [-1.0, 0.5, 1.0]
    assert summary["parameter_change"]["l2_displacement"] == 0
    assert summary["parameter_change"]["initial_norm"] == summary["parameter_change"]["final_norm"]
    assert [row["standby_shadow_copy"] for row in summary["mapping_rows"]] == [3, 1]
    assert len(summary["raw_service_q_fp32"]) == 2
    assert all(len(row) == 4 and len(row[0]) == 20 for row in summary["raw_service_q_fp32"])
    assert summary["training_hidden_gradient"]["finite"]
    assert summary["control_hidden_gradient"]["finite"]
    assert summary["exposure"]["native_helper_calls"] == 9
    assert summary["exposure"]["backward_passes"] == 2
    assert summary["exposure"]["native_state_initializations"] == 0
    assert (tmp_path / "published" / "head_contract_a05.so").is_file()
    assert runner.project_cost()["projected_seconds"] == 25.5
    assert time.perf_counter() - started < 60
