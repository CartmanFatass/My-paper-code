from __future__ import annotations

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01 import addressing
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_runtime_audit import (
    B1RuntimeAuditError,
    ModelResetObserver,
    observe_learner_visibility,
    observe_active_modes,
    require_frozen_execution_modes,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.model import (
    INPUT_DIM,
    CommonRecurrentActorCritic,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.contract import (
    EPISODE_TRANSITIONS,
)


def _model() -> CommonRecurrentActorCritic:
    return CommonRecurrentActorCritic(21101, address_u64=addressing.u64)


def test_execution_mode_observation_is_empty_only_for_frozen_fp32_cpu(
    monkeypatch,
) -> None:
    model = _model()
    assert observe_active_modes(model) == []
    assert require_frozen_execution_modes(model) == []

    monkeypatch.setattr(torch, "get_default_dtype", lambda: torch.float64)
    modes = observe_active_modes(model)
    assert "default-dtype:torch.float64" in modes
    with pytest.raises(B1RuntimeAuditError, match="active execution modes"):
        require_frozen_execution_modes(model)


def test_model_reset_observer_records_actual_zero_bits_and_rejects_carry(
    monkeypatch,
) -> None:
    model = _model()
    observations = torch.zeros((2, EPISODE_TRANSITIONS, INPUT_DIM), dtype=torch.float32)
    records: list[dict[str, object]] = []
    with ModelResetObserver(model, name="train-boundary", records=records):
        model.forward_episode(observations)
    assert len(records) == 1
    assert set(records[0]) == {"name", "expected_fp32_bits", "observed_fp32_bits"}
    assert len(records[0]["expected_fp32_bits"]) == 2 * 128
    assert records[0]["expected_fp32_bits"] == ["00000000"] * (2 * 128)
    assert records[0]["observed_fp32_bits"] == records[0]["expected_fp32_bits"]

    original = model.initial_hidden

    def carried(batch_size, *, device=None):
        return torch.ones((batch_size, 128), dtype=torch.float32, device=device)

    monkeypatch.setattr(model, "initial_hidden", carried)
    contaminated: list[dict[str, object]] = []
    with pytest.raises(B1RuntimeAuditError, match="nonzero recurrent reset"):
        with ModelResetObserver(model, name="eval-boundary", records=contaminated):
            model.forward_episode(observations)
    assert contaminated
    assert contaminated[0]["observed_fp32_bits"] != contaminated[0]["expected_fp32_bits"]
    monkeypatch.setattr(model, "initial_hidden", original)


def test_learner_visibility_is_observed_at_tensor_boundary_and_rejects_extension() -> None:
    observations = torch.zeros((8, EPISODE_TRANSITIONS, INPUT_DIM), dtype=torch.float32)
    record = observe_learner_visibility(
        "train-observation-boundary",
        observations,
        episode_count=8,
        visible_fields=("primitive_token", "adapter_emission"),
    )
    assert record == {
        "name": "train-observation-boundary",
        "visible_fields": ["primitive_token", "adapter_emission"],
        "allowed_fields": ["primitive_token", "adapter_emission"],
    }
    with pytest.raises(B1RuntimeAuditError, match="learner visibility"):
        observe_learner_visibility(
            "contaminated-boundary",
            observations,
            episode_count=8,
            visible_fields=("primitive_token", "adapter_emission", "evaluator_truth"),
        )
