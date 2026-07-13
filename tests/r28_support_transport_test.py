import numpy as np

from ha_ctse_process import r27_g2_runtime as runtime
from ha_ctse_process import r28_support_transport as transport
from ha_ctse_process.r27_g2_analysis import late_action_features
from ha_ctse_process.r28_g1_reward import R28G1SupportEvaluation
from ha_ctse_process.r28_support_transport import (
    R28SupportTransportArtifact,
    collect_support_transport_reset,
)
from r27_g2_collector_test import FakeAdapter, FakeAgent
from scripts.audit_r28_support_transport import classify_transport


class AllSupportScorer:
    def evaluate_support(self, post, labels, durations):
        features = np.asarray(post, dtype=np.float32)
        rows = int(features.shape[0])
        distances = np.sum(np.square(features), axis=1, dtype=np.float64)
        thresholds = np.full(rows, 1.0e6, dtype=np.float64)
        return R28G1SupportEvaluation(
            support=np.ones(rows, dtype=np.bool_),
            distances=distances,
            thresholds=thresholds,
            distance_ratio=distances / thresholds,
            abs_z=np.abs(features).astype(np.float64),
            ood_fraction=0.0,
        )


def test_transport_pairs_execution_mode_without_changing_support_features(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(transport, "validate_agent_source_contract", lambda _agent: None)
    monkeypatch.setattr(
        transport,
        "capture_global_rng_state",
        lambda: runtime.capture_global_rng_state(
            require_cuda=False, include_cuda=False
        ),
    )
    agent = FakeAgent()
    artifact = collect_support_transport_reset(
        env_factory=FakeAdapter,
        agent=agent,
        scorer=AllSupportScorer(),
        reset_id=0,
    )

    assert artifact.focal_agent == 0
    assert artifact.epsilon.shape == (50, 6, 4)
    assert artifact.replay_equal.shape == (2, 4)
    assert artifact.replay_equal.all()
    assert artifact.step_valid.all()
    assert artifact.feature_valid.all()
    assert artifact.support.all()
    assert artifact.module_state_equal
    assert artifact.value_norm_state_equal

    np.testing.assert_array_equal(
        artifact.executed_action[0], artifact.deterministic_action[0]
    )
    assert not np.array_equal(
        artifact.executed_action[1], artifact.deterministic_action[1]
    )
    reconstructed = np.tanh(
        artifact.pre_tanh_mean[1]
        + np.exp(artifact.log_standard_deviation[1])
        * artifact.epsilon[None, :, :, :]
    ).astype(np.float32)
    np.testing.assert_allclose(
        artifact.executed_action[1], reconstructed, atol=1e-6, rtol=1e-6
    )

    expected = late_action_features(
        artifact.deterministic_action[1, 2, 10:20, artifact.focal_agent]
    )
    np.testing.assert_allclose(artifact.features[1, 2, 1], expected)

    path = artifact.write(tmp_path / "transport_reset_0000.npz")
    loaded = R28SupportTransportArtifact.read(path)
    np.testing.assert_array_equal(loaded.epsilon, artifact.epsilon)
    np.testing.assert_array_equal(loaded.support, artifact.support)


def test_transport_classification_routes_only_the_measured_edge():
    def metrics(deterministic_ood, stochastic_ood):
        return {
            "deterministic": {
                "ood_fraction": deterministic_ood,
                "cells": {"cell": {"ood_fraction": deterministic_ood}},
            },
            "stochastic": {
                "ood_fraction": stochastic_ood,
                "cells": {"cell": {"ood_fraction": stochastic_ood}},
            },
        }

    assert classify_transport(metrics(0.0, 0.0), 48)[1] == (
        "PASS_STOCHASTIC_SUPPORT_TRANSPORT"
    )
    assert classify_transport(metrics(0.0, 1.0), 48)[1] == (
        "FAIL_STOCHASTIC_SUPPORT_TRANSPORT"
    )
    assert classify_transport(metrics(1.0, 1.0), 48)[1] == (
        "INVALID_DETERMINISTIC_SOURCE_REPLICATION"
    )
    assert classify_transport(metrics(0.0, 0.0), 47)[1] == (
        "UNDERPOWERED_PAIRED_SUPPORT"
    )
