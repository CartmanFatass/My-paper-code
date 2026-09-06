"""Witness A01 focused checks; no learner, no development panel, no host library."""

from io import BytesIO
import json

import numpy as np
import torch

from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02.study import (
    EvaluationCoordinate, _reset_row,
)
from experiments.candidates.degraded_incumbent_shadow_handover.init_witness_a01 import study
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy, RecurrentRolloutState, build_master_addressed_initial_state,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import (
    WelfordState,
)

B03_MASTER_HEX = "b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a"
COORDS = (
    "TARGET_VISUAL_MASK/K8",
    "TARGET_VISUAL_MASK/K4_TO_K12",
    "TERRAIN_RELAY_MASK/K8",
    "TERRAIN_RELAY_MASK/K4_TO_K12",
)


def test_master_hex_is_b03_seed_73():
    assert study.master().hex() == B03_MASTER_HEX
    assert study.master().hex() == "b938a93e7b41bec6c1b0df8761649fda2e0779f05d6610de5ed5ba71f780543a"


def test_initializer_determinism_empty_welford_and_norm():
    torch.set_num_threads(1)
    first = build_master_addressed_initial_state(master=study.master(), block=0, arm="STRUCTURED")
    second = build_master_addressed_initial_state(master=study.master(), block=0, arm="STRUCTURED")
    assert first == second
    loaded = [torch.load(BytesIO(payload), map_location="cpu", weights_only=False) for payload in (first, second)]
    assert loaded[0]["model"].keys() == loaded[1]["model"].keys()
    for name, tensor in loaded[0]["model"].items():
        torch.testing.assert_close(tensor, loaded[1]["model"][name], rtol=0, atol=0)
    for payload in loaded:
        assert payload["update"] == 0
        for name in ("actor", "snapshot", "critic"):
            assert isinstance(payload["welford"][name], WelfordState)
            assert payload["welford"][name].count == 0
    reconstructed, facts = study.reconstruct_initial()
    assert reconstructed == first
    assert facts["initializer_calls"] == 1
    assert facts["helper_constructed_objects"] == ["model", "optimizer"]
    assert facts["welford_counts"] == {"actor": 0, "snapshot": 0, "critic": 0}
    assert facts["update"] == 0
    assert abs(facts["initial_model_norm"] - study.EXPECTED_INITIAL_NORM) <= 1e-9
    assert facts["norm_matches"] is True
    assert facts["initialization_source"] == "reconstructed_from_master"


def test_recorded_reset_round_trip():
    loaded = study.load_b03_rows(study.B03_ROOT)
    expected = study.coordinate_keys()
    assert expected == tuple(loaded["CONTROL"])
    assert expected == tuple(loaded["FORECAST_PACKAGE"])
    control_summary = (study.B03_ROOT / "control" / "summary.json")
    package_summary = (study.B03_ROOT / "forecast_package" / "summary.json")
    control_rows = json.loads(control_summary.read_text(encoding="utf8"))["evaluation_rows"]
    package_rows = json.loads(package_summary.read_text(encoding="utf8"))["evaluation_rows"]
    assert len(control_rows) == 4
    for row, package_row in zip(control_rows, package_rows):
        coordinate = EvaluationCoordinate(row["block"], row["regime"], row["schedule"], "SPEED_4", row["slot"])
        recomputed = dict(_reset_row(study.master(), coordinate))
        assert row["reset"] == recomputed
        assert package_row["reset"] == recomputed
        assert package_row["coordinate"] == row["coordinate"] == coordinate.canonical_key()
        assert loaded["CONTROL"][row["coordinate"]]["reset"] == recomputed
        assert loaded["FORECAST_PACKAGE"][row["coordinate"]]["reset"] == recomputed


def test_two_views_on_initializer_head():
    torch.set_num_threads(1)
    initial, facts = study.reconstruct_initial()
    assert facts["welford_counts"]["actor"] == 0
    hidden = torch.full((1, 4, 128), 0.125)
    observation = {
        "actor": np.full((1, 4, 54), 0.02, np.float32),
        "owner": np.array([0]), "renew": np.ones(1, bool),
        "snapshot_payload": np.zeros((1, 18), np.float32),
        "snapshot_delivery_mask": np.zeros(1, bool),
    }
    outputs = []
    for package in (False, True):
        state = RecurrentRolloutState.fresh("STRUCTURED", width=1)
        state.hidden = hidden.clone()
        policy = BatchedRecurrentPolicy(
            arm="STRUCTURED", checkpoint_bytes=initial, state=state, forecast_package=package,
        )
        assert policy.state.actor_welford.count == 0
        with torch.no_grad():
            raw = policy.model.heads(hidden)["service_q"]
            viewed = torch.sigmoid(raw) if package else raw
        rows = policy.step_rows(observation, sampler=None, global_tick=0, deterministic=True)
        outputs.append((policy, raw, viewed, rows))
        assert policy.state.actor_welford.count == 0
    torch.testing.assert_close(outputs[0][1], outputs[1][1], rtol=0, atol=0)
    torch.testing.assert_close(outputs[1][2], torch.sigmoid(outputs[0][1]), rtol=0, atol=0)
    copy = 3
    torch.testing.assert_close(
        torch.as_tensor(outputs[1][3]["service_q"][0]),
        torch.sigmoid(torch.as_tensor(outputs[0][3]["service_q"][0])),
        rtol=0, atol=1e-6,
    )
    with torch.no_grad():
        raw_after = outputs[0][0].model.service_q(outputs[0][0].state.hidden)
    np.testing.assert_allclose(
        outputs[0][3]["service_q"][0], raw_after[0, copy].double().numpy(), atol=1e-6,
    )
    np.testing.assert_allclose(
        outputs[1][3]["service_q"][0], torch.sigmoid(raw_after[0, copy]).double().numpy(), atol=1e-6,
    )


def _new_rows(view, values, coordinates=COORDS):
    return [
        {"coordinate": key, "view": view, "source": f"new:zero_update:{view}", "service_ticks": value}
        for key, value in zip(coordinates, values)
    ]


def _reused(values, coordinates=COORDS):
    return {key: {"coordinate": key, "service_ticks": value} for key, value in zip(coordinates, values)}


def test_witness_result_patterns_and_incomplete():
    provenance = study.REUSED_PAIR_PROVENANCE
    cases = (
        ("D_C<=-24", [100, 100, 100, 100], [70, 70, 70, 70], [100, 100, 100, 100], [100, 100, 100, 100], -30.0, 0.0),
        ("D_C>-24 and D_P<=-24", [100, 100, 100, 100], [100, 100, 100, 100], [200, 200, 200, 200], [100, 100, 100, 100], 0.0, -100.0),
        ("both>=+24", [100, 100, 100, 100], [130, 130, 130, 130], [50, 50, 50, 50], [80, 80, 80, 80], 30.0, 30.0),
        ("inside_or_heterogeneous", [100, 100, 100, 100], [100, 100, 100, 100], [100, 100, 100, 100], [110, 90, 100, 100], 0.0, 0.0),
    )
    for pattern, j0_c, j16_c, j0_p, j16_p, d_c, d_p in cases:
        new_rows = _new_rows("CONTROL", j0_c) + _new_rows("FORECAST_PACKAGE", j0_p)
        b03_rows = {"CONTROL": _reused(j16_c), "FORECAST_PACKAGE": _reused(j16_p)}
        result = study.witness_result(new_rows, b03_rows)
        assert result["pattern"] == pattern
        assert result["scale_ticks"] == 24
        assert result["reused_pair_provenance"] == provenance
        assert result["CONTROL"]["D"] == d_c
        assert result["FORECAST_PACKAGE"]["D"] == d_p
        assert result["CONTROL"]["initial_view_mean"] == sum(j0_c) / 4
        assert result["CONTROL"]["final_mean"] == sum(j16_c) / 4
        assert result["FORECAST_PACKAGE"]["initial_view_mean"] == sum(j0_p) / 4
        assert result["FORECAST_PACKAGE"]["final_mean"] == sum(j16_p) / 4
        assert [row["difference"] for row in result["CONTROL"]["rows"]] == [b - a for a, b in zip(j0_c, j16_c)]
        assert [row["source_new"] for row in result["CONTROL"]["rows"]] == ["new:zero_update:CONTROL"] * 4
        assert [row["source_reused"] for row in result["CONTROL"]["rows"]] == ["reused:b03/CONTROL/summary.json"] * 4
        assert [row["source_new"] for row in result["FORECAST_PACKAGE"]["rows"]] == ["new:zero_update:FORECAST_PACKAGE"] * 4
        assert [row["source_reused"] for row in result["FORECAST_PACKAGE"]["rows"]] == ["reused:b03/FORECAST_PACKAGE/summary.json"] * 4
    partial = _new_rows("CONTROL", [1, 2], COORDS[:2]) + _new_rows("FORECAST_PACKAGE", [3, 4, 5, 6])
    b03_rows = {"CONTROL": _reused([10, 20, 30, 40]), "FORECAST_PACKAGE": _reused([11, 21, 31, 41])}
    incomplete = study.witness_result(partial, b03_rows)
    assert incomplete["pattern"] == "incomplete"
    assert incomplete["CONTROL"]["D"] is None
    assert len(incomplete["CONTROL"]["rows"]) == 2
    assert incomplete["FORECAST_PACKAGE"]["D"] == ((11 - 3) + (21 - 4) + (31 - 5) + (41 - 6)) / 4
    empty = study.witness_result([], b03_rows)
    assert empty["pattern"] == "incomplete"
    assert empty["CONTROL"]["D"] is None
    assert empty["FORECAST_PACKAGE"]["D"] is None
    assert empty["reused_pair_provenance"] == provenance
