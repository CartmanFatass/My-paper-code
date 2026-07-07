from pathlib import Path

import numpy as np
import pytest

from ha_ctse_process.r24_behavior_audit import (
    R24AuditRecord,
    action_feature_distance,
    action_feature_kl,
    between_within_ratio,
    effect_distance,
    summarize_audit_records,
    write_audit_csv,
)


def test_action_feature_kl_matches_manual_discrete_kl():
    p = np.asarray([[0.75, 0.25], [0.50, 0.50]], dtype=np.float32)
    q = np.asarray([[0.50, 0.50], [0.25, 0.75]], dtype=np.float32)
    out = action_feature_kl(p, q)
    expected = np.sum(p * (np.log(p + 1e-8) - np.log(q + 1e-8)), axis=-1)
    assert np.allclose(out, expected, atol=1e-6)


def test_action_feature_kl_raises_on_shape_mismatch():
    with pytest.raises(ValueError, match="shape mismatch"):
        action_feature_kl(np.asarray([0.75, 0.25]), np.asarray([[0.5, 0.5], [0.5, 0.5]]))


def test_action_feature_distance_uses_kl_for_probability_rows():
    p = np.asarray([[0.75, 0.25]], dtype=np.float32)
    q = np.asarray([[0.50, 0.50]], dtype=np.float32)
    assert np.isclose(action_feature_distance(p, q), float(action_feature_kl(p, q).mean()))


def test_action_feature_distance_uses_euclidean_for_continuous_rows():
    forced = np.asarray([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    base = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.float32)
    expected = np.mean(np.linalg.norm(forced - base, axis=-1))
    assert np.isclose(action_feature_distance(forced, base), expected)


def test_effect_distance_is_euclidean_delta_distance():
    assert np.isclose(
        effect_distance(
            np.asarray([0.0, 0.0], dtype=np.float32),
            np.asarray([1.0, 0.0], dtype=np.float32),
            np.asarray([0.0, 0.0], dtype=np.float32),
            np.asarray([1.0, 2.0], dtype=np.float32),
        ),
        2.0,
    )


def test_between_within_ratio_detects_cluster_separation():
    features = np.asarray([[0.0, 0.0], [0.1, 0.0], [5.0, 5.0], [5.1, 5.0]], dtype=np.float32)
    labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
    assert between_within_ratio(features, labels) > 20.0


def test_between_within_ratio_raises_on_row_mismatch():
    with pytest.raises(ValueError, match="row mismatch"):
        between_within_ratio(np.asarray([[0.0], [1.0]], dtype=np.float32), np.asarray([0, 1, 2]))


def test_between_within_ratio_returns_zero_for_tiny_label_support():
    features = np.asarray([[0.0], [1.0], [2.0]], dtype=np.float32)
    labels = np.asarray([0, 0, 1], dtype=np.int64)
    assert between_within_ratio(features, labels) == 0.0


def test_summarize_audit_records_reports_horizon_metrics():
    records = [
        R24AuditRecord(horizon=10, forced_kind="z", action_distance=0.2, effect_distance=1.0, label=0),
        R24AuditRecord(horizon=10, forced_kind="z", action_distance=0.4, effect_distance=3.0, label=1),
        R24AuditRecord(horizon=20, forced_kind="xi", action_distance=0.8, effect_distance=5.0, label=1),
    ]
    out = summarize_audit_records(records)
    assert out["r24_audit_records"] == 3.0
    assert out["r24_z_action_distance_h10"] == 0.3
    assert out["r24_z_effect_distance_h10"] == 2.0
    assert out["r24_xi_action_distance_h20"] == 0.8


def test_write_audit_csv_roundtrip(tmp_path: Path):
    metrics = {"r24_audit_records": 2.0, "r24_z_action_distance_h10": 0.25}
    path = tmp_path / "r24_behavior_audit.csv"
    write_audit_csv(path, metrics)
    text = path.read_text(encoding="utf-8")
    assert "r24_audit_records" in text
    assert "0.25" in text
