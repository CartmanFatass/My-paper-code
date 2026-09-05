import copy
import json
import math
import time

import pytest

from experiments.candidates.degraded_incumbent_shadow_handover import certificate_a04 as certificate
from scripts import run_dish_origin_certificate_a04 as runner


def synthetic_pair(tick):
    covariance = [0.0] * 32
    for index in (0, 5, 16, 21):
        covariance[index] = 1.0
    prepared = {"p": [0.0, 0.0, 30.0, 0.0], "a": [100.0] * 4,
                "handover_used": 0, "terminal": 0, "source_exists": [1, 1],
                "source_sequence": [7, 7], "owner": 0, "initial_owner": 0,
                "countdown": 0, "prepare_latched": 0, "warmup": 0, "invalid_commit": 3}
    completed = {"p": [0.0] * 4, "a": [1.7999999999999998, 2.4, 0.0, 0.0],
                 "prepare_latched": 1, "warmup": 10, "intent_owner": 0,
                 "intent_origin_tick": tick, "intent_certificate": 0}
    origin = {"host": certificate.HOST, "action_tick": tick, "arrivals": {"renewal": True},
              "prepared": prepared, "completion": {"native": completed},
              "policy_output": {"prediction_mean": [0.0] * 8, "prediction_covariance": covariance,
                                "service_q": [0.5] * 20, "raw_action": [3.0, 4.0, 0.0, 0.0]}}
    following = {"host": certificate.HOST, "action_tick": tick + 1,
                 "prepared": {"invalid_commit": 3},
                 "completion": {"native": {"application_reason": 2, "invalid_commit": 4}}}
    return origin, following


def test_scalar_dp_all_tails_and_threshold_clipping():
    result = certificate.predictive_q95([0.5] * 20)
    expected = [sum(math.comb(20, k) for k in range(m, 21)) / 2**20 for m in range(21)]
    assert len(result["tails_descending_m"]) == 21
    for tail in result["tails_descending_m"]:
        assert tail["tail"] == expected[tail["m"]]
        assert tail["passes"] == (expected[tail["m"]] >= 0.95)
        assert tail["signed_distance"] == expected[tail["m"]] - 0.95
    assert result["q95"] == 0.3
    assert certificate.predictive_q95([-1.0] * 20)["clipped_probabilities"] == [1e-6] * 20
    assert certificate.predictive_q95([2.0] * 20)["clipped_probabilities"] == [1 - 1e-6] * 20
    close = certificate.predictive_q95([0.95**(1 / 20)] * 20)
    assert close["tails_descending_m"][0]["numerically_close"]


def test_full_predicates_use_prepared_positions_but_post_projection_commands():
    origin, following = synthetic_pair(340)
    saved = copy.deepcopy(origin)
    result = certificate.reconstruct(origin, following)
    assert origin == saved
    assert len(result["predicates_native_order"]) == 14
    assert result["failed_predicates"] == ["predictive_q95"]
    assert result["following_native_rejection"] == {"application_reason": 2, "invalid_commit_delta": 1}
    assert result["commands"][0]["norm"] <= 1e-12
    origin["prepared"]["source_exists"][0] = 0
    result = certificate.reconstruct(origin, following)
    assert result["failed_predicates"] == ["source_u0_exists", "predictive_q95"]
    assert len(result["predictive_service"]["tails_descending_m"]) == 21
    assert result["predicates_native_order"][-1]["name"] == "command_u1"


def test_mahalanobis_order_named_infinity_and_close_comparison():
    mean = [2.0, -1.0, 0, 0, -0.5, 0.25, 0, 0]
    covariance = [0.0] * 32
    covariance[0] = 2; covariance[16] = 3
    covariance[1] = 0.1; covariance[17] = -0.2
    covariance[5] = 4; covariance[21] = 1
    dm, details = certificate.mahalanobis_position(mean, covariance)
    dx, dy, s00, s01, s11 = 2.5, -1.25, 5.000001, -0.1, 5.000001
    expected = (dx * dx * s11 - 2 * dx * dy * s01 + dy * dy * s00) / (s00 * s11 - s01 * s01)
    assert dm == expected and details["value"] == expected
    origin, following = synthetic_pair(364)
    origin["policy_output"]["prediction_covariance"] = [0.0] * 32
    origin["policy_output"]["prediction_covariance"][1] = 1
    result = certificate.reconstruct(origin, following)
    assert result["mahalanobis"]["value"] == "positive_infinity"
    assert "mahalanobis_finite" in result["non_close_failed_predicates"]
    json.dumps(result, allow_nan=False)
    row = certificate.comparison("limit", "physical/action", 15 - 5e-11, 15.0, ">=")
    assert row["numerically_close"] and not row["passes"]


def test_synthetic_four_origin_publication_smoke(tmp_path, capsys):
    started = time.perf_counter()
    records = [{"host": "LITERAL", "action_tick": 340},
               {"host": certificate.HOST, "action_tick": 1}]
    for tick in certificate.ORIGINS:
        records.extend(synthetic_pair(tick))
    trace = tmp_path / "synthetic.jsonl"
    trace.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    output = tmp_path / "published"
    assert runner.main(["run", "--seed", "11", "--trace", str(trace),
                        "--admission", str(tmp_path / "external-receipt.json"), "--out", str(output)]) == 0
    published = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    peak = printed.pop("completed_peak_rss_bytes")
    assert peak is None or peak >= published["peak_rss_bytes"]
    assert printed.pop("completed_runner_wall_seconds") >= published["wall_seconds"]
    assert printed.pop("summary_publication_seconds") >= 0
    assert printed == published
    assert published["result"] == "A04-RECORDED-REJECTION-RECONSTRUCTED"
    assert [row["origin_tick"] for row in published["origins"]] == list(certificate.ORIGINS)
    assert published["new_exposure"]["models_initialized"] == 0
    assert runner.project_cost()["projected_seconds"] == 19.5
    assert time.perf_counter() - started < 60


def test_boolean_discrepancy_and_close_only_rejection(tmp_path):
    records = []
    for tick in certificate.ORIGINS:
        origin, following = synthetic_pair(tick)
        if tick == certificate.ORIGINS[0]:
            origin["policy_output"]["service_q"] = [1.0] * 20
            origin["completion"]["native"]["a"][2] = 1.5 + 1e-12 + 5e-11
        records.extend((origin, following))
    trace = tmp_path / "close.jsonl"
    trace.write_text("".join(json.dumps(row) + "\n" for row in records))
    result = certificate.read_trace(trace, time.perf_counter() + 10)
    assert result["result"] == "A04-RECONSTRUCTION-DISCREPANCY"
    assert result["discrepancy"]["only_close_boundary_support"]
    records[0]["completion"]["native"]["intent_certificate"] = 1
    trace.write_text("".join(json.dumps(row) + "\n" for row in records))
    assert certificate.read_trace(trace, time.perf_counter() + 10)["discrepancy"]["boolean_mismatch"]
    trace.write_text("".join(json.dumps(row) + "\n" for row in records[:-1]))
    with pytest.raises(KeyError):
        certificate.read_trace(trace, time.perf_counter() + 10)
