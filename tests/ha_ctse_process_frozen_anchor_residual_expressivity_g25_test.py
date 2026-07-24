"""Proof-sized acceptance for the G25 residual expressivity diagnostic."""

from __future__ import annotations

import torch

from ha_ctse_process import delayed_battery_roster_g18 as source
from ha_ctse_process.anchored_residual_g19 import maximum_state_difference
from scripts import probe_frozen_anchor_residual_expressivity_g25 as probe


def test_constructive_dataset_closes_exact_source_rows() -> None:
    dataset = probe.constructive_dataset()
    controls = probe.dataset_contract(dataset)
    assert controls == {
        "row_count": 36,
        "row_count_exact": True,
        "slot_order_counts_exact": True,
        "time_coverage_exact": True,
        "finite": True,
        "inactive_targets_exact_zero": True,
    }
    assert dataset["observations"].shape == (
        36,
        source.CAPACITY,
        source.OBSERVATION_DIM,
    )
    assert dataset["actions"].shape == (36, source.CAPACITY, source.ACTION_DIM)
    assert source.run_information_gate()["branch"] == source.PASS_BRANCH


def test_fit_step_owns_only_residual_and_preserves_anchor() -> None:
    probe.runtime.configure_runtime(probe.MODEL_SEED)
    model = probe.make_model()
    model.begin_delayed_phase()
    dataset = probe.constructive_dataset()
    optimizer = probe.residual_optimizer(model)
    assert probe.optimizer_owns_only_residual(model, optimizer)
    anchor = probe.frozen_state(model)
    residual_before = tuple(
        parameter.detach().clone() for parameter in model.residual_parameters()
    )
    loss, actions = probe.pointwise_loss(model, dataset, torch.arange(36))
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.residual_parameters(), probe.GRADIENT_CLIP)
    optimizer.step()
    assert maximum_state_difference(anchor, probe.frozen_state(model)) == 0.0
    assert any(
        not torch.equal(before, after.detach())
        for before, after in zip(residual_before, model.residual_parameters())
    )
    inactive = torch.where(
        dataset["active_mask"].unsqueeze(-1), torch.zeros_like(actions), actions
    )
    assert torch.count_nonzero(inactive) == 0


def test_result_precedence_is_fail_closed() -> None:
    passing = {
        "operational_valid": True,
        "final_mse": 0.0009,
        "final_to_initial_ratio": 0.09,
        "final_utility": 0.96,
        "gain_over_anchor": 0.11,
        "spike_utility": 0.91,
        "rotating_effort_share": 0.76,
    }
    assert probe.select_result_branch(passing) == probe.PASS_BRANCH
    assert (
        probe.select_result_branch(passing | {"operational_valid": False})
        == probe.INVALID_BRANCH
    )
    assert (
        probe.select_result_branch(passing | {"final_mse": 0.0010001})
        == probe.NO_POINTWISE_BRANCH
    )
    assert (
        probe.select_result_branch(passing | {"final_to_initial_ratio": 0.100001})
        == probe.NO_POINTWISE_BRANCH
    )
    assert (
        probe.select_result_branch(passing | {"spike_utility": 0.899999})
        == probe.NO_CLOSED_LOOP_BRANCH
    )


def test_probe_contract_is_nonformal_and_reuses_registered_g18_gates() -> None:
    assert probe.FIT_STEPS == 200
    assert probe.FIT_BATCH_SIZE == 36
    assert probe.LEARNING_RATE == 1e-3
    assert probe.ABSOLUTE_MSE_CEILING == 1e-3
    assert probe.RELATIVE_MSE_CEILING == 0.10
    assert probe.g19.G18_UTILITY_FLOOR == 0.95
    assert probe.g19.G18_SPIKE_UTILITY_FLOOR == 0.90
    assert "constructive" not in probe.make_model().policy.__class__.__module__
