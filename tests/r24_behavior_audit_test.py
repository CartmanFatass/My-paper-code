import numpy as np
import pytest

from ha_ctse_process.r24_behavior_audit import (
    R24AuditRecord,
    action_feature_kl,
    between_within_ratio,
    summarize_audit_records,
)


def test_action_feature_kl_matches_manual_discrete_kl():
    p = np.asarray([[0.75, 0.25], [0.50, 0.50]], dtype=np.float32)
    q = np.asarray([[0.50, 0.50], [0.25, 0.75]], dtype=np.float32)
    out = action_feature_kl(p, q)
    expected = np.sum(p * (np.log(p + 1e-8) - np.log(q + 1e-8)), axis=-1)
    assert np.allclose(out, expected, atol=1e-6)


def test_action_feature_kl_raises_on_shape_mismatch():
    p = np.asarray([0.75, 0.25], dtype=np.float32)
    q = np.asarray([[0.50, 0.50], [0.25, 0.75]], dtype=np.float32)
    with pytest.raises(ValueError, match=r"shape mismatch"):
        action_feature_kl(p, q)


def test_between_within_ratio_detects_cluster_separation():
    features = np.asarray(
        [
            [0.0, 0.0],
            [0.1, 0.0],
            [5.0, 5.0],
            [5.1, 5.0],
        ],
        dtype=np.float32,
    )
    labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
    assert between_within_ratio(features, labels) > 20.0


def test_between_within_ratio_raises_on_row_mismatch():
    features = np.asarray([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    labels = np.asarray([0, 1, 2], dtype=np.int64)
    with pytest.raises(ValueError, match=r"row mismatch"):
        between_within_ratio(features, labels)


def test_between_within_ratio_returns_zero_for_tiny_label_support():
    features = np.asarray([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]], dtype=np.float32)
    labels = np.asarray([0, 0, 1], dtype=np.int64)
    assert between_within_ratio(features, labels) == 0.0


def test_between_within_ratio_returns_zero_for_single_label():
    features = np.asarray([[0.0], [1.0], [2.0]], dtype=np.float32)
    labels = np.asarray([0, 0, 0], dtype=np.int64)
    assert between_within_ratio(features, labels) == 0.0


def test_summarize_audit_records_reports_horizon_metrics():
    records = [
        R24AuditRecord(horizon=10, forced_kind="z", action_kl=0.2, effect_distance=1.0, label=0),
        R24AuditRecord(horizon=10, forced_kind="z", action_kl=0.4, effect_distance=3.0, label=1),
        R24AuditRecord(horizon=20, forced_kind="xi", action_kl=0.8, effect_distance=5.0, label=1),
    ]
    out = summarize_audit_records(records)
    assert out["r24_audit_records"] == 3.0
    assert out["r24_z_action_kl_h10"] == 0.3
    assert out["r24_z_effect_distance_h10"] == 2.0
    assert out["r24_xi_action_kl_h20"] == 0.8
