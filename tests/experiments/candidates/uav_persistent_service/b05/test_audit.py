import copy

import numpy as np
import pytest

from experiments.candidates.uav_persistent_service.b05.audit import HORIZON, QOS, world_reading


def evidence():
    scheduler = {"fallback": None, "weights": [0.] * 8, "q0": 1.,
                 "candidate_scores": [{"action": 0, "score": [0., -1., -1200., 1.]},
                                      {"action": 1, "score": [0., -1., -1200., 0.]}],
                 "executed_action": 0, "r_action": 0,
                 "defer": {"transfer_access_now": False, "predicted_access_loss": False},
                 "chosen_forecast": {"qhat": [1.], "release": [None] * 8,
                                     "readiness": [None] * 8}}
    macros = [{"macro_start": step, "choice": {"scheduler": copy.deepcopy(scheduler)}}
              for step in range(0, HORIZON, 30)]
    # Only the first clock selects a new commitment, with reserve as the decisive score.
    first = macros[0]["choice"]
    first["member"] = 0
    first["scheduler"]["executed_action"] = 1
    first["scheduler"]["chosen_forecast"]["release"][0] = 300
    first["scheduler"]["chosen_forecast"]["readiness"][0] = 360
    commitment = {"start": 0, "member": 0, "end_kind": "release", "stop": 270,
                  "release_reason": "dwell", "allocated_charging_steps": 120,
                  "first_geometric_arrival": 150, "assignment_restored": 280,
                  "first_post_release_connected_load": 271}
    raw = {"metrics": np.full((HORIZON, QOS+1), .5)}
    return {"complete": True, "macros": macros, "commitments": [commitment]}, raw


def test_score_and_event_semantics():
    decisions, raw = evidence()
    result = world_reading(decisions, raw)
    assert result["counts"]["all_zero_weight_clocks"] == 400
    assert result["counts"]["multiple_candidate_service_score_tied_clocks"] == 400
    assert result["changed_choice_first_decisive_score"] == {"reserve": 1}
    assert result["release_prediction_minus_observed_seconds"]["mean"] == 30
    assert result["one_clock_qhat_minus_native_qos"]["mean"] == .5
    assert result["starts"][0]["observed_assignment_step"] == 280


def test_missing_release_not_imputed_and_incomplete_refused():
    decisions, raw = evidence()
    decisions["macros"][0]["choice"]["scheduler"]["chosen_forecast"]["release"][0] = None
    result = world_reading(decisions, raw)
    assert result["counts"]["predicted_release_missing"] == 1
    assert result["release_prediction_minus_observed_seconds"]["count"] == 0
    decisions["complete"] = False
    with pytest.raises(ValueError, match="complete recorded"):
        world_reading(decisions, raw)
