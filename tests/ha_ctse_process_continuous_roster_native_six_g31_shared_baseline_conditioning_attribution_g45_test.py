from __future__ import annotations

import copy
import hashlib
import inspect
import io
import pickle
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
import torch
from torch import nn

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_shared_baseline_conditioning_attribution_g45
    as g45,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)


ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)
ANCHOR_BYTES = 81_017
ANCHOR_SHA256 = "d6920e8ab958b776ee0b25a5d2a1b120528b69abc87d4eacc2a6deee2351b521"


@pytest.fixture(scope="module")
def accepted_anchor_batch() -> Iterator[
    tuple[g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory]
]:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        fixture = ANCHOR_FIXTURE.read_bytes()
        assert len(fixture) == ANCHOR_BYTES
        assert hashlib.sha256(fixture).hexdigest() == ANCHOR_SHA256
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            torch.load(
                io.BytesIO(fixture), map_location="cpu", weights_only=False
            ),
            accepted_anchor_replicate=0,
        )
        trajectory = g40.collect_g40_trajectory(
            anchor,
            episode_ids=range(8),
            ledger_seed=11_453_000,
            action_seed=11_453_000,
            device=torch.device("cpu"),
        )
        assert trajectory.rewards.numel() == 384
        yield anchor, trajectory
    finally:
        torch.set_num_threads(prior_threads)


def _project_update(
    anchor: g40.G40NativeSixPolicy,
    trajectory: g40.AnchoredRosterTrajectory,
) -> tuple[
    dict[str, g41.G41NoSlowProjection],
    dict[str, torch.optim.Optimizer],
    dict[str, object],
]:
    models = g45.project_g45_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    record = g45.optimize_baseline_conditioning_update(
        models,
        optimizers,
        {arm: trajectory for arm in g45.ARMS},
        update_index=0,
    )
    return models, optimizers, record


def _synthetic_baseline_gradient_rows(
    model: g41.G41NoSlowProjection,
    *,
    trunk_live: bool,
    immediate_output_live: bool,
    successor_output_live: bool,
) -> tuple[tuple[torch.Tensor, ...], tuple[torch.Tensor, ...]]:
    immediate: list[torch.Tensor] = []
    successor: list[torch.Tensor] = []
    for name, parameter in model.credit_baselines.named_parameters():
        immediate_row = torch.zeros_like(parameter)
        successor_row = torch.zeros_like(parameter)
        if name in ("0.weight", "0.bias") and trunk_live:
            immediate_row.fill_(1.0)
            successor_row.fill_(1.0)
        elif name == "2.weight":
            if immediate_output_live:
                immediate_row[0].fill_(1.0)
            if successor_output_live:
                successor_row[1].fill_(1.0)
        elif name == "2.bias":
            if immediate_output_live:
                immediate_row[0] = 1.0
            if successor_output_live:
                successor_row[1] = 1.0
        immediate.append(immediate_row)
        successor.append(successor_row)
    return tuple(immediate), tuple(successor)


def test_projection_preserves_g44_chain_and_disjoint_retained_state(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = accepted_anchor_batch
    rng_before = torch.random.get_rng_state().clone()
    models = g45.project_g45_arms(anchor, accepted_anchor_replicate=0)
    assert tuple(models) == g45.ARMS
    assert torch.equal(rng_before, torch.random.get_rng_state())
    assert g40.state_bytes(models[g45.BASELINE_READ_ARM]) == g40.state_bytes(
        models[g45.BASELINE_SHADOW_NO_READ_ARM]
    )
    assert g40.shared_tensor_storage_count(tuple(models.values())) == 0
    assert all(not hasattr(model, "slow_critic") for model in models.values())
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    boundary = g45.branch_boundary_audit(models, optimizers)
    assert boundary["passed"] is True, boundary
    assert boundary["baseline_schema_equal"] is True
    assert boundary["optimizer_states_empty_and_separate"] is True
    assert boundary["shared_parameter_buffer_gradient_optimizer_storage_count"] == 0
    assert boundary["accepted_g44_formal_source_commit"] == (
        "96e35ddf55de71e56c6bcace4746c408909480dd"
    )

    aliased_models = {
        g45.BASELINE_READ_ARM: models[g45.BASELINE_READ_ARM],
        g45.BASELINE_SHADOW_NO_READ_ARM: models[g45.BASELINE_READ_ARM],
    }
    assert not g45.branch_boundary_audit(aliased_models, optimizers)["passed"]
    aliased_optimizers = {
        arm: optimizers[g45.BASELINE_READ_ARM] for arm in g45.ARMS
    }
    assert not g45.branch_boundary_audit(models, aliased_optimizers)["passed"]


def test_no_read_credit_has_no_baseline_input_or_output_dependency(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    _, trajectory = accepted_anchor_batch
    assert tuple(inspect.signature(g45._no_read_credit).parameters) == (
        "trajectory",
    )
    implementation = inspect.getsource(g45._no_read_credit)
    assert "old_immediate_baselines" not in implementation
    assert "old_successor_baselines" not in implementation
    original = g45._no_read_credit(trajectory)
    changed = replace(
        trajectory,
        old_immediate_baselines=trajectory.old_immediate_baselines + 17.0,
        old_successor_baselines=trajectory.old_successor_baselines - 23.0,
    )
    counterfactual = g45._no_read_credit(changed)
    assert torch.equal(original.returns, counterfactual.returns)
    assert torch.equal(original.successor_targets, counterfactual.successor_targets)
    assert torch.equal(original.immediate_advantage, trajectory.rewards)
    assert torch.equal(original.successor_advantage, original.successor_targets)


def test_local_counterfactual_scalar_norm_gate_zero_and_pickle() -> None:
    parameter = nn.Parameter(torch.zeros(2, dtype=torch.float64))
    raw = (torch.tensor([3.0, 4.0], dtype=torch.float64),)
    assigned, record = g45._scale_to_counterfactual_norm(
        raw, (parameter,), counterfactual_norm=2.5
    )
    assert torch.equal(assigned[0], torch.tensor([1.5, 2.0], dtype=torch.float64))
    assert record["raw_credit_norm"] == 5.0
    assert record["assigned_credit_norm"] == 2.5
    assert record["counterfactual_shadow_output_type"] == (
        "one_detached_scalar_credit_norm"
    )
    assert record["counterfactual_vector_serialized"] is False
    assert record["actual_residual_baseline_read_count"] == 0
    assert record["actual_direction_baseline_coordinate_read_count"] == 0
    zero, zero_record = g45._scale_to_counterfactual_norm(
        raw, (parameter,), counterfactual_norm=0.0
    )
    assert torch.equal(zero[0], torch.zeros_like(parameter))
    assert zero_record["actor_credit_gradients_exact_zero"] is True
    with pytest.raises(
        g45.G45GradientGateError,
        match="positive_counterfactual_norm_with_zero_no_read_direction",
    ):
        g45._scale_to_counterfactual_norm(
            (torch.zeros_like(parameter),),
            (parameter,),
            counterfactual_norm=1.0,
        )
    error = g45.G45GradientGateError("probe", {"arm": "NO_READ"})
    restored = pickle.loads(pickle.dumps(error))
    assert isinstance(restored, g45.G45GradientGateError)
    assert restored.reason == error.reason
    assert restored.diagnostics == error.diagnostics
    assert str(restored) == str(error)
    assert restored.to_record() == error.to_record()


def test_first_update_binds_both_residual_laws_and_activation(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, optimizers, record = _project_update(anchor, trajectory)
    assert record["passed"] is True
    assert record["branch_update_order"] == list(g45.ARMS)
    assert record["actor_head_optimizer_steps"] == {
        arm: 2.0 for arm in g45.ARMS
    }
    assert record["first_paired_direct_treatment_audit"]["passed"] is True
    assert record["order_swap_guard"]["passed"] is True
    for pass_record in record["pass_records"]:
        assert set(pass_record["gradient_evidence"]) == set(g45.ARMS)
        for arm in g45.ARMS:
            gradients = pass_record["gradient_evidence"][arm]
            assert g45.validate_registered_gradient_evidence(gradients)
            groups = gradients["baseline_gradient_groups"]
            assert g45.validate_baseline_gradient_group_evidence(groups)
            assert groups["immediate_output_row_gradient_norm"] > 1e-12
            assert groups["successor_output_row_gradient_norm"] > 1e-12
            assert groups["shared_trunk_union_gradient_norm"] > 1e-12
        assert tuple(pass_record["residual_evidence_by_arm"]) == g45.ARMS
        read = pass_record["residual_evidence_by_arm"][g45.BASELINE_READ_ARM]
        no_read = pass_record["residual_evidence_by_arm"][
            g45.BASELINE_SHADOW_NO_READ_ARM
        ]
        assert g45.validate_arm_credit_evidence(read, g45.BASELINE_READ_ARM)
        assert g45.validate_arm_credit_evidence(
            no_read, g45.BASELINE_SHADOW_NO_READ_ARM
        )
        assert read["residual_law_id"] == g45.READ_RESIDUAL_LAW
        assert no_read["residual_law_id"] == g45.NO_READ_RESIDUAL_LAW
        assert read["actual_residual_baseline_read_count"] == 2
        assert no_read["actual_residual_baseline_read_count"] == 0
        for field in (
            "episode_id_digest",
            "true_current_state_input_digest",
            "immediate_target_digest",
            "successor_target_digest",
            "immediate_baseline_output_digest",
            "successor_baseline_output_digest",
        ):
            assert read[field] == no_read[field]
        certificate = pass_record["composition"][
            g45.BASELINE_SHADOW_NO_READ_ARM
        ]
        assert g45._valid_composition(
            certificate, g45.BASELINE_SHADOW_NO_READ_ARM
        )
        assert "counterfactual_vector" not in certificate
        activation = pass_record["baseline_conditioning_activation"]
        assert g45.validate_activation_record(activation)
        assert activation["evidence_source_arm"] == g45.BASELINE_READ_ARM
        assert activation["no_read_arm_evidence_read_count"] == 0
        assert activation["strict_activation_observed"] is True
    conclusion = g45.build_conclusion_evidence([record], formal=False)
    assert g45.validate_conclusion_evidence(conclusion)
    assert g45.validate_baseline_gradient_groups_by_arm(
        conclusion["replicate_rows"][0]["reconstructed_passes"][0][
            "baseline_gradient_groups_by_arm"
        ]
    )
    assert len(g45.serialize_diagnostics(record)) > 1_000
    checkpoint = g45.build_final_checkpoint(
        g45.BASELINE_READ_ARM,
        models[g45.BASELINE_READ_ARM],
        record,
        conclusion,
        formal=False,
    )
    assert checkpoint["kind"] == "final_only"
    assert checkpoint["baseline_checkpoint_selection_read_count"] == 0
    assert checkpoint["baseline_evaluation_metric_read_count"] == 0
    assert g45.validate_baseline_gradient_groups_by_arm(
        checkpoint["baseline_gradient_groups_by_arm"]
    )
    assert checkpoint["standalone_slow_present"] is False
    assert all(
        min(
            g45._optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].actor_credit_parameters()
        )
        == 2.0
        for arm in g45.ARMS
    )


def test_residual_shadow_and_activation_tampering_fails_closed(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, _, record = _project_update(anchor, trajectory)
    conclusion = g45.build_conclusion_evidence([record], formal=False)

    leaked = copy.deepcopy(record)
    leaked["pass_records"][0]["residual_evidence_by_arm"][
        g45.BASELINE_SHADOW_NO_READ_ARM
    ]["actual_residual_baseline_read_count"] = 1
    assert not g45._update_evidence_valid(leaked)

    vector_shadow = copy.deepcopy(record)
    vector_shadow["pass_records"][0]["composition"][
        g45.BASELINE_SHADOW_NO_READ_ARM
    ]["counterfactual_vector"] = [1.0]
    assert not g45._update_evidence_valid(vector_shadow)

    stale = copy.deepcopy(record)
    stale["pass_records"][1]["residual_evidence_by_arm"][
        g45.BASELINE_READ_ARM
    ]["normalization_recomputed_between_passes"] = True
    assert not g45._update_evidence_valid(stale)

    dead_trunk_evidence = copy.deepcopy(record)
    dead_trunk_evidence["pass_records"][0]["gradient_evidence"][
        g45.BASELINE_READ_ARM
    ]["baseline_gradient_groups"]["shared_trunk_union_gradient_norm"] = 0.0
    assert not g45._update_evidence_valid(dead_trunk_evidence)

    forged = copy.deepcopy(conclusion)
    row = forged["replicate_rows"][0]["reconstructed_passes"][0]
    row["reference_credit_dot_product"] = (
        row["reference_READ_credit_norm"]
        * row["reference_NO_READ_counterfactual_credit_norm"]
    )
    row["q_direction"] = 0.0
    row["active"] = True
    assert not g45.validate_conclusion_evidence(forged)

    dead_conclusion_group = copy.deepcopy(conclusion)
    dead_conclusion_group["replicate_rows"][0]["reconstructed_passes"][0][
        "baseline_gradient_groups_by_arm"
    ][g45.BASELINE_SHADOW_NO_READ_ARM][
        "successor_output_row_gradient_norm"
    ] = 0.0
    assert not g45.validate_conclusion_evidence(dead_conclusion_group)

    with pytest.raises(ValueError, match="update evidence invalid"):
        g45.build_final_checkpoint(
            g45.BASELINE_SHADOW_NO_READ_ARM,
            models[g45.BASELINE_SHADOW_NO_READ_ARM],
            leaked,
            conclusion,
            formal=False,
        )


def test_formal_activation_requires_every_accepted_anchor_replicate(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    _, _, template = _project_update(anchor, trajectory)
    records = []
    for replicate in g45.ACCEPTED_G40_ANCHOR_REPLICATES:
        record = copy.deepcopy(template)
        record["accepted_g40_anchor_replicate"] = replicate
        record["branch_boundary"]["accepted_g40_anchor_authority"] = (
            g41.accepted_g40_anchor_identity(replicate)
        )
        records.append(record)
    conclusion = g45.build_conclusion_evidence(records, formal=True)
    assert g45.validate_conclusion_evidence(conclusion)

    missing = copy.deepcopy(conclusion)
    missing["replicate_rows"].pop()
    assert not g45.validate_conclusion_evidence(missing)

    inactive = copy.deepcopy(conclusion)
    row = inactive["replicate_rows"][1]
    for item in row["reconstructed_passes"]:
        item["q_baseline"] = 0.0
        item["centered_immediate_baseline_RMS"] = 0.0
        item["centered_successor_baseline_RMS"] = 0.0
        item["active"] = False
    row["strict_activation_observed"] = False
    assert not g45.validate_conclusion_evidence(inactive)


def test_dead_actor_or_baseline_group_and_wrong_arm_inventory_fail_closed(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models = g45.project_g45_arms(anchor, accepted_anchor_replicate=0)
    model = models[g45.BASELINE_READ_ARM]
    actor = model.full_actor_parameters()
    baseline = tuple(model.credit_baselines.parameters())
    live_actor = tuple(torch.ones_like(parameter) for parameter in actor)
    dead_actor = tuple(torch.zeros_like(parameter) for parameter in actor)
    live_baseline = tuple(torch.ones_like(parameter) for parameter in baseline)
    assert not g45.validate_registered_gradient_evidence(
        g45.registered_gradient_evidence(
            model, dead_actor, live_actor, live_baseline, live_baseline
        )
    )
    dead_trunk, dead_trunk_successor = _synthetic_baseline_gradient_rows(
        model,
        trunk_live=False,
        immediate_output_live=True,
        successor_output_live=True,
    )
    inherited_dead_trunk = g45.g43.registered_gradient_evidence(
        model,
        live_actor,
        live_actor,
        dead_trunk,
        dead_trunk_successor,
    )
    assert g45.g43.validate_registered_gradient_evidence(inherited_dead_trunk)
    dead_trunk_evidence = g45.registered_gradient_evidence(
        model,
        live_actor,
        live_actor,
        dead_trunk,
        dead_trunk_successor,
    )
    assert dead_trunk_evidence["baseline_gradient_groups"][
        "shared_trunk_union_gradient_norm"
    ] == 0.0
    assert not g45.validate_registered_gradient_evidence(dead_trunk_evidence)

    for immediate_live, successor_live, missing_field in (
        (False, True, "immediate_output_row_gradient_norm"),
        (True, False, "successor_output_row_gradient_norm"),
    ):
        immediate_rows, successor_rows = _synthetic_baseline_gradient_rows(
            model,
            trunk_live=True,
            immediate_output_live=immediate_live,
            successor_output_live=successor_live,
        )
        inherited = g45.g43.registered_gradient_evidence(
            model,
            live_actor,
            live_actor,
            immediate_rows,
            successor_rows,
        )
        assert g45.g43.validate_registered_gradient_evidence(inherited)
        grouped = g45.registered_gradient_evidence(
            model,
            live_actor,
            live_actor,
            immediate_rows,
            successor_rows,
        )
        assert grouped["baseline_gradient_groups"][missing_field] == 0.0
        assert not g45.validate_registered_gradient_evidence(grouped)
    for item in models.values():
        item.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(item)
        for arm, item in models.items()
    }
    reversed_trajectories = {
        g45.BASELINE_SHADOW_NO_READ_ARM: trajectory,
        g45.BASELINE_READ_ARM: trajectory,
    }
    with pytest.raises(ValueError, match="paired 8x48"):
        g45.optimize_baseline_conditioning_update(
            models, optimizers, reversed_trajectories, update_index=0
        )
