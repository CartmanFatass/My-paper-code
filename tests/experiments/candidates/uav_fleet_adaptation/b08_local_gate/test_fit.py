"""Small algebraic fixtures for fixed gate features and ridge artifacts."""
import numpy as np
import pytest

from experiments.candidates.uav_fleet_adaptation.b08_local_gate.fit import (
    audit_ridge, capped_count, fit_ridge, gate_features, predict,
)


@pytest.mark.parametrize("visible", [0, 1, 10, 11, 20])
def test_count_input_provenance_and_feature_order(visible):
    features = np.zeros(114, dtype=np.float32)
    features[3:63].reshape(20, 3)[:visible, 2] = .001  # Visible even below threshold.
    features[3:63].reshape(20, 3)[:, :2] = .9
    features[63:103] = .8  # Peers never count as user slots.
    features[103:] = 1.  # Navigation/fallback never count.
    hidden = np.arange(128, dtype=np.float32)
    answer = dict(features=features, hidden=hidden, n_current=0, served=np.zeros(27))
    assert capped_count(answer) == capped_count(features) == min(visible, 10)
    raw, expanded = gate_features(answer, "RAW"), gate_features(answer, "HIDDEN")
    assert raw.dtype == expanded.dtype == np.float64
    assert raw.shape == (125,) and expanded.shape == (253,)
    np.testing.assert_array_equal(raw[:114], features)
    np.testing.assert_array_equal(raw[114:], np.eye(11)[min(visible, 10)])
    np.testing.assert_array_equal(expanded[:125], raw)
    np.testing.assert_array_equal(expanded[125:], hidden)
    answer["hidden"] = np.full(128, np.nan, dtype=np.float32)
    np.testing.assert_array_equal(gate_features(answer, "RAW"), raw)
    with pytest.raises(ValueError):
        gate_features(answer, "HIDDEN")


def test_hand_algebra_sum_penalty_unpenalized_intercept_and_constants():
    x = np.array([[-1., .1], [1., .1]])
    y = np.array([1., 5.])
    params, diagnostics = fit_ridge(x, y, name="synthetic")
    np.testing.assert_array_equal(params["constant"], [False, True])
    np.testing.assert_array_equal(params["scale"], [1., 1.])
    np.testing.assert_array_equal(params["mean"], [0., .1])
    np.testing.assert_allclose(params["coefficients"], [4 / 3, 0], rtol=0, atol=1e-15)
    assert params["intercept"] == 3  # Penalty never shrinks the intercept.
    np.testing.assert_allclose(predict(params, x), [5 / 3, 13 / 3], rtol=0, atol=1e-15)
    assert diagnostics["objective"] == pytest.approx(8 / 3)
    assert params["coefficients"][0] != 1.  # Mean-SSE would instead give 1.
    constant_params, _ = fit_ridge(np.full((3, 2), .1), np.full(3, 7.), name="constant")
    np.testing.assert_array_equal(constant_params["coefficients"], [0, 0])
    assert constant_params["intercept"] == 7


def test_independent_augmented_system_and_training_only_scaler():
    x = np.array([[3., 2., .1], [4., 8., .1], [-1., 9., .1], [2., 2., .1]])
    y = np.array([1., -2., 3., 0.])
    params, diagnostics = fit_ridge(x, y, name="small")
    expected_mean = np.array([2., 5.25, .1])
    expected_scale = np.sqrt(np.array([3.5, 10.6875, 1.]))
    np.testing.assert_array_equal(params["mean"], expected_mean)
    np.testing.assert_array_equal(params["scale"], expected_scale)
    design = np.column_stack(((x - expected_mean) / expected_scale, np.ones(4)))
    expected = np.linalg.solve(design.T @ design + np.diag([1., 1., 1., 0.]), design.T @ y)
    np.testing.assert_allclose(np.r_[params["coefficients"], params["intercept"]], expected, rtol=2e-15, atol=2e-15)
    heldout = np.array([100., -20., .1])
    expected_prediction = ((heldout - expected_mean) / expected_scale) @ expected[:3] + expected[3]
    assert predict(params, heldout) == pytest.approx(expected_prediction)
    assert diagnostics["normal_condition_number"] >= 1.
    assert diagnostics["normal_equation_relative_residual"] <= diagnostics["residual_tolerance"]


def test_audit_never_solves_and_rejects_tampering(monkeypatch, tmp_path):
    x = np.array([[1., 2.], [2., 4.], [3., 6.], [4., 8.]])
    y = np.array([2., 0., 1., -1.])
    params, diagnostics = fit_ridge(x, y, name="collinear")
    artifact = tmp_path / "ridge.npz"
    np.savez(artifact, **params)
    with np.load(artifact, allow_pickle=False) as loaded:
        restored = {key: loaded[key] for key in loaded.files}
    np.testing.assert_array_equal(predict(restored, x), predict(params, x))
    def forbidden(*args, **kwargs):
        raise AssertionError("reader cannot solve or refit")
    monkeypatch.setattr(np.linalg, "solve", forbidden)
    monkeypatch.setattr(np.linalg, "lstsq", forbidden)
    audit = audit_ridge(x, y, restored)
    assert audit == {k: v for k, v in diagnostics.items() if k not in ("name", "fits", "optimizer_steps")}
    assert audit["refits"] == 0
    for key in ("mean", "scale"):
        bad = {k: v.copy() for k, v in restored.items()}
        bad[key][0] += .01
        with pytest.raises(ValueError, match="scaler"):
            audit_ridge(x, y, bad)
    for key in ("coefficients", "intercept"):
        bad = {k: v.copy() for k, v in restored.items()}
        bad[key] += .01
        with pytest.raises(FloatingPointError, match="stationarity"):
            audit_ridge(x, y, bad)


def test_zero_tie_on_and_strict_positive_off():
    params, _ = fit_ridge(np.array([[-1.], [1.]]), np.array([-1., 1.]), name="tie")
    predictions = predict(params, np.array([[-1.], [0.], [1.]]))
    np.testing.assert_array_equal(predictions > 0., [False, False, True])


@pytest.mark.parametrize("x,y", [(np.empty((0, 2)), np.empty(0)), ([[1., np.nan]], [0.]), ([[1.]], [np.inf]), ([[1.]], [1., 2.]), ([[1j]], [0.])])
def test_invalid_training_is_rejected(x, y):
    with pytest.raises(ValueError):
        fit_ridge(x, y, name="invalid")


def test_feature_contract_rejects_wrong_shape_dtype_and_unknown_kind():
    for features in (np.zeros(113, dtype=np.float32), np.full(114, np.nan, dtype=np.float32), np.zeros(114, dtype=np.float64)):
        with pytest.raises(ValueError):
            gate_features(dict(features=features), "RAW")
    with pytest.raises(ValueError):
        gate_features(dict(features=np.zeros(114, dtype=np.float32)), "OTHER")
