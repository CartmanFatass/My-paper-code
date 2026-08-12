from __future__ import annotations

import inspect
import copy
import ast
from pathlib import Path

import pytest
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_common_entropy_attribution_g53 as g53,
)


def test_exact_identity_budget_seeds_and_zero_g52_dependency() -> None:
    certificate = g53.static_configuration_certificate(formal=False)
    assert certificate["entropy_coefficients_hex"] == {
        g53.REFERENCE_ARM: "0x1.47ae147ae147bp-7",
        g53.NULL_ARM: "0x0.0p+0",
    }
    assert certificate["training_transition_formula"] == "(2*(10+10)-1)*8*48"
    assert certificate["training_transitions"] == 14_976
    assert certificate["evaluation_transitions"] == 6_912
    assert certificate["total_real_transitions"] == 21_888
    assert certificate["optimizer_steps"] == 80
    assert certificate["physical_training_collection_count"] == 39
    assert certificate["post_treatment_arm_local_physical_collections_per_root"] == 38
    assert certificate["bootstrap_resamples"] == 250
    assert certificate["seed_bases"] == {
        "initialization": 10_541_000,
        "phase_A_ledger": 10_542_000,
        "phase_A_action": 10_543_000,
        "phase_A_gradient_probe": 10_544_000,
        "phase_B_ledger": 10_545_000,
        "phase_B_action": 10_546_000,
        "phase_B_gradient_probe": 10_547_000,
        "evaluation_ledger": 10_548_000,
        "evaluation_process": 10_549_000,
        "evaluation_action": 10_550_000,
    }
    assert certificate["bootstrap_seed_base"] == 10_551_053
    assert certificate["nonformal_seed_offset"] == 900_000
    assert certificate["G52_CARRY_state_count"] == 0
    with pytest.raises(ValueError, match="formal runtime"):
        g53.static_configuration_certificate(formal=True)


def test_fresh_factory_projects_once_before_optimizer_and_is_storage_disjoint() -> None:
    text = inspect.getsource(g53.make_phase_A_models)
    assert text.count("g40.make_model") == 1
    assert text.count("g51.G51NoBaselinePhaseAProjection") == 1
    assert "g51.make_phase_A_models" not in text
    models = g53.make_phase_A_models(member_capacity=8, initialization_seed=10_541_000)
    assert tuple(models) == g53.ARMS
    assert all(not hasattr(model, "credit_baselines") for model in models.values())
    assert all(hasattr(model, "slow_critic") for model in models.values())
    assert g53.g40.shared_tensor_storage_count(tuple(models.values())) == 0
    optimizers = g53.make_phase_A_optimizers(models)
    boundary = g53.phase_A_boundary_audit(models, optimizers)
    assert boundary["passed"] is True
    assert boundary["fresh_G50_null_source_count"] == 1
    assert boundary["G51_NoBaselinePhaseAProjection_count"] == 1
    assert boundary["G52_CARRY_state_count"] == 0


def test_static_gate_binds_raw_entropy_and_exact_log_std_support() -> None:
    original = g53.g40.ENTROPY_COEFFICIENT
    certificate = g53.reconstruct_static_certificate()
    assert g53.validate_static_certificate(certificate)
    assert certificate["synthetic_raw_entropy_gradient_support"] == ["policy.log_std"]
    assert certificate["actor_parameter_name_count"] == 17
    assert certificate["initial_log_std_exact_zero"] is True
    assert certificate["coefficient_read_outside_plan_execution"] == {
        "construction": False,
        "collection": False,
        "evaluation": False,
        "result_selection": False,
    }
    altered = dict(certificate); altered["unregistered"] = True
    assert not g53.validate_static_certificate(altered)
    assert g53.g40.ENTROPY_COEFFICIENT == original == 0.01


def test_same_raw_entropy_graph_scales_exact_zero_without_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    models = g53.make_phase_A_models(member_capacity=8, initialization_seed=10_541_000)
    shape = (48, 8, 8)
    trajectory = g53.g47.G47ActorTrajectory(
        observations=torch.zeros((*shape, 6)),
        active_mask=torch.ones(shape, dtype=torch.bool),
        rewards=torch.arange(384, dtype=torch.float32).reshape(48, 8) / 384.0,
        hidden_before=torch.zeros((*shape, models[g53.REFERENCE_ARM].hidden_dim)),
        terminal_hidden_reset_mask=torch.zeros(shape, dtype=torch.bool),
        pre_tanh_actions=torch.zeros((*shape, 2)),
        actions=torch.zeros((*shape, 2)),
        old_log_probs=torch.zeros(shape),
    )
    normalized = g53._normalized_reward(trajectory).normalized
    plans = {
        arm: g53._phase_A_plan(
            models[arm], trajectory, normalized,
            coefficient=g53.entropy_coefficient(arm),
        )
        for arm in g53.ARMS
    }
    assert g53._rows_equal(
        plans[g53.REFERENCE_ARM].raw_entropy_gradients,
        plans[g53.NULL_ARM].raw_entropy_gradients,
    )
    assert all(
        torch.equal(row, torch.zeros_like(row))
        for row in plans[g53.NULL_ARM].scaled_entropy_gradients
    )
    names = g53._parameter_names(models[g53.REFERENCE_ARM], models[g53.REFERENCE_ARM].full_actor_parameters())
    support = [name for name, row in zip(names, plans[g53.REFERENCE_ARM].scaled_entropy_gradients) if torch.count_nonzero(row)]
    assert support == ["policy.log_std"]
    optimizers = g53.make_phase_A_optimizers(models)
    ids = tuple(range(8))
    observed: list[tuple[str, str]] = []
    original = g53.entropy_coefficient
    def observed_coefficient(
        arm: str, *, audit: list[tuple[str, str]] | None = None, phase: str = ""
    ) -> float:
        observed.append((phase, arm))
        return original(arm, audit=audit, phase=phase)
    monkeypatch.setattr(g53, "entropy_coefficient", observed_coefficient)
    update = g53.optimize_phase_A_update(
        models, optimizers, trajectory, update_index=0,
        episode_ids={arm: ids for arm in g53.ARMS},
    )
    activation = update["first_batch_activation_certificate"]
    assert activation["same_stored_trajectory_object"] is True
    assert activation["coefficient_is_sole_graph_delta"] is True
    assert activation["null_scaled_gradient_finite_bytewise_zero"] is True
    assert activation["post_step_actor_or_Adam_state_differs"] is True
    assert activation["activation"]["q_H"] > 0.0
    assert activation["activation"]["active_iff_q_H_gt_0"] is True
    assert observed == [("A", arm) for _ in range(2) for arm in g53.ARMS]


def test_update_zero_requires_one_shared_object_and_later_updates_reject_it() -> None:
    models = g53.make_phase_A_models(member_capacity=8, initialization_seed=10_541_000)
    optimizers = g53.make_phase_A_optimizers(models)
    shape = (48, 8, 8)
    trajectory = g53.g47.G47ActorTrajectory(
        observations=torch.zeros((*shape, 6)), active_mask=torch.ones(shape, dtype=torch.bool),
        rewards=torch.zeros((48, 8)), hidden_before=torch.zeros((*shape, models[g53.REFERENCE_ARM].hidden_dim)),
        terminal_hidden_reset_mask=torch.zeros(shape, dtype=torch.bool),
        pre_tanh_actions=torch.zeros((*shape, 2)), actions=torch.zeros((*shape, 2)), old_log_probs=torch.zeros(shape),
    )
    with pytest.raises(g53.G53InvariantError, match="update0_not_same"):
        g53.optimize_phase_A_update(
            models, optimizers,
            {g53.REFERENCE_ARM: trajectory, g53.NULL_ARM: copy.deepcopy(trajectory)},
            update_index=0,
        )
    with pytest.raises(g53.G53InvariantError, match="forced_equal"):
        g53.optimize_phase_A_update(models, optimizers, trajectory, update_index=1)


def test_phase_boundary_deletes_slow_critic_and_makes_fresh_phase_b_adam() -> None:
    models = g53.make_phase_A_models(member_capacity=8, initialization_seed=10_541_000)
    projected, certificate = g53.project_phase_B_models(models, completed_phase_A_updates=10)
    assert all(row["passed"] is True for row in certificate.values())
    assert all(not hasattr(model, "slow_critic") for model in projected.values())
    assert all(not hasattr(model, "credit_baselines") for model in projected.values())
    optimizers = g53.make_phase_B_optimizers(projected)
    assert all(not optimizer.state for optimizer in optimizers.values())


def _valid_checkpoint() -> dict[str, object]:
    phase_A = g53.make_phase_A_models(member_capacity=8, initialization_seed=10_541_000)
    models, boundary = g53.project_phase_B_models(
        phase_A, completed_phase_A_updates=10
    )
    optimizers = g53.make_phase_B_optimizers(models)
    arm = g53.REFERENCE_ARM
    for parameter in models[arm].full_actor_parameters():
        optimizers[arm].state[parameter] = {
            "step": torch.tensor(20.0),
            "exp_avg": torch.zeros_like(parameter),
            "exp_avg_sq": torch.zeros_like(parameter),
        }
    return g53.build_final_checkpoint(
        model=models[arm], optimizer=optimizers[arm], source_commit="a" * 40,
        arm=arm, phase_boundary_certificate=boundary[arm],
    )


def test_checkpoint_validator_rejects_nan_scalar_shape_dtype_and_boundary_tampering() -> None:
    checkpoint = _valid_checkpoint()
    assert g53.validate_final_checkpoint(checkpoint)
    actor_name = next(iter(checkpoint["actor_state"]))
    adam_name = next(iter(checkpoint["actor_Adam_state"]))
    mutations = []
    row = copy.deepcopy(checkpoint); row["actor_state"][actor_name] = torch.tensor(0.0); mutations.append(row)
    row = copy.deepcopy(checkpoint); row["actor_state"][actor_name] = row["actor_state"][actor_name].to(torch.float64); mutations.append(row)
    row = copy.deepcopy(checkpoint); row["log_std"] = torch.full_like(row["log_std"], float("nan")); mutations.append(row)
    row = copy.deepcopy(checkpoint); row["actor_Adam_state"][adam_name]["exp_avg"] = torch.tensor(float("nan")); mutations.append(row)
    row = copy.deepcopy(checkpoint); row["actor_Adam_state"][adam_name]["step"] = torch.tensor(19.0); mutations.append(row)
    row = copy.deepcopy(checkpoint); row["actor_Adam_state"][adam_name]["step"] = torch.tensor(20.0, dtype=torch.float64); mutations.append(row)
    row = copy.deepcopy(checkpoint); row["phase_boundary_certificate"]["baseline_absent"] = False; mutations.append(row)
    row = copy.deepcopy(checkpoint); row["actor_state"]["foreign"] = torch.zeros(1); mutations.append(row)
    assert all(not g53.validate_final_checkpoint(row) for row in mutations)


def test_coefficient_callable_is_not_read_by_construction_or_checkpoint_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkpoint = _valid_checkpoint()
    monkeypatch.setattr(
        g53, "entropy_coefficient",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected read")),
    )
    models = g53.make_phase_A_models(member_capacity=8, initialization_seed=10_541_000)
    assert tuple(models) == g53.ARMS
    assert g53.static_configuration_certificate(formal=False)["entropy_coefficients_hex"][g53.NULL_ARM] == "0x0.0p+0"
    assert g53.validate_final_checkpoint(checkpoint)


def test_no_g52_import_in_source_ast() -> None:
    tree = ast.parse(Path(g53.__file__).read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not [name for name in imports if "g52" in name.lower()]
