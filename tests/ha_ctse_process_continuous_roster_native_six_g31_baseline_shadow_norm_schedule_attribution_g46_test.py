from __future__ import annotations

import copy
import hashlib
import io
import math
import pickle
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch
from torch import nn

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_baseline_shadow_norm_schedule_attribution_g46
    as g46,
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
    models = g46.project_g46_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    record = g46.optimize_baseline_shadow_norm_update(
        models,
        optimizers,
        {arm: trajectory for arm in g46.ARMS},
        update_index=0,
    )
    return models, optimizers, record


def test_projection_preserves_g45_chain_and_disjoint_retained_state(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, _ = accepted_anchor_batch
    rng_before = torch.random.get_rng_state().clone()
    models = g46.project_g46_arms(anchor, accepted_anchor_replicate=0)
    assert tuple(models) == g46.ARMS
    assert torch.equal(rng_before, torch.random.get_rng_state())
    assert g40.state_bytes(models[g46.SHADOW_NORM_ARM]) == g40.state_bytes(
        models[g46.RAW_NORM_ARM]
    )
    assert g40.shared_tensor_storage_count(tuple(models.values())) == 0
    assert all(not hasattr(model, "slow_critic") for model in models.values())
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    boundary = g46.branch_boundary_audit(models, optimizers)
    assert boundary["passed"] is True, boundary
    assert boundary["accepted_g45_formal_source_commit"] == (
        "d2502f4d1732601aa1249a1df7627690d51a9954"
    )
    assert boundary["accepted_g45_aligned_implementation_commit"] == (
        "a42da997712d9c941ac9a6ca08992f4c5de033a2"
    )
    assert boundary["shared_parameter_buffer_gradient_optimizer_storage_count"] == 0

    aliased = {
        g46.SHADOW_NORM_ARM: models[g46.SHADOW_NORM_ARM],
        g46.RAW_NORM_ARM: models[g46.SHADOW_NORM_ARM],
    }
    assert not g46.branch_boundary_audit(aliased, optimizers)["passed"]


def test_corrected_q_norm_piecewise_strict_activation_and_pickle() -> None:
    assert g46.corrected_q_norm(0.0, 0.0) == 0.0
    assert g46.corrected_q_norm(2.0, 2.0) == 0.0
    assert g46.corrected_q_norm(0.0, 3.0) == 1.0
    assert g46.corrected_q_norm(3.0, 2.0) == pytest.approx(1.0 / 3.0)
    assert g46.corrected_q_norm(1_000_000.0, 999_999.0) == (
        g46.ACTIVATION_TOLERANCE
    )
    assert not (
        g46.corrected_q_norm(1_000_000.0, 999_999.0)
        > g46.ACTIVATION_TOLERANCE
    )
    assert (
        g46.corrected_q_norm(1_000_000.0, 999_998.0)
        > g46.ACTIVATION_TOLERANCE
    )
    with pytest.raises(
        g46.G46GradientGateError,
        match="positive_baseline_norm_with_zero_raw_direction",
    ):
        g46.corrected_q_norm(1.0, 0.0)
    for left, right in ((math.nan, 1.0), (1.0, math.inf), (-1.0, 1.0)):
        with pytest.raises(g46.G46GradientGateError):
            g46.corrected_q_norm(left, right)

    error = g46.G46GradientGateError("probe", {"arm": "RAW"})
    restored = pickle.loads(pickle.dumps(error))
    assert isinstance(restored, g46.G46GradientGateError)
    assert restored.reason == error.reason
    assert restored.diagnostics == error.diagnostics
    assert str(restored) == str(error)
    assert restored.to_record() == error.to_record()


def test_reference_and_raw_schedule_zero_cancellation_and_direction_rules() -> None:
    parameter = nn.Parameter(torch.zeros(2, dtype=torch.float64))
    raw = (torch.tensor([3.0, 4.0], dtype=torch.float64),)
    assigned, record = g46._reference_schedule(
        raw, (parameter,), baseline_counterfactual_norm=2.5
    )
    assert torch.equal(assigned[0], torch.tensor([1.5, 2.0], dtype=torch.float64))
    assert record["assigned_credit_norm"] == 2.5
    assert record["baseline_counterfactual_calls"] == 1
    assert "counterfactual_vector" not in record

    zero, zero_record = g46._reference_schedule(
        raw, (parameter,), baseline_counterfactual_norm=0.0
    )
    assert torch.equal(zero[0], torch.zeros_like(parameter))
    assert zero_record["actor_credit_gradients_exact_zero"] is True
    with pytest.raises(
        g46.G46GradientGateError,
        match="positive_baseline_norm_with_zero_reference_raw_direction",
    ):
        g46._reference_schedule(
            (torch.zeros_like(parameter),),
            (parameter,),
            baseline_counterfactual_norm=1.0,
        )

    raw_assigned, raw_record = g46._raw_schedule(raw, (parameter,))
    assert torch.equal(raw_assigned[0], raw[0])
    assert raw_record["baseline_counterfactual_calls"] == 0
    assert raw_record["learned_or_tunable_scale"] == 0
    same = g46._unit_direction_record(assigned, raw_assigned)
    assert same["direction_rule_evaluated"] is True
    assert same["unit_direction_distance"] <= g46.DIRECTION_TOLERANCE
    skipped = g46._unit_direction_record(zero, raw_assigned)
    assert skipped["direction_rule_evaluated"] is False
    assert skipped["unit_direction_distance"] is None
    zero_vs_raw = g46._activation_record(
        zero, raw_assigned, baseline_counterfactual_norm=0.0
    )
    assert zero_vs_raw["q_norm"] == 1.0
    assert zero_vs_raw["strict_treatment_activation_observed"] is True
    assert zero_vs_raw["direction_rule_evaluated"] is False
    both_zero = g46._activation_record(
        zero, zero, baseline_counterfactual_norm=0.0
    )
    assert both_zero["q_norm"] == 0.0
    assert both_zero["strict_treatment_activation_observed"] is False
    with pytest.raises(g46.G46GradientGateError, match="unit_direction_mismatch"):
        g46._unit_direction_record(
            (torch.tensor([1.0, 0.0]),),
            (torch.tensor([0.0, 1.0]),),
        )

    inclusive = {
        "baseline_read_counterfactual_credit_norm": 1.0,
        "raw_equal_mean_credit_norm": 1.0,
        "q_norm": 0.0,
        "activation_threshold": g46.ACTIVATION_TOLERANCE,
        "strict_treatment_activation_observed": False,
        "evidence_source_arms": list(g46.ARMS),
        "direction_evidence_source_arm": g46.SHADOW_NORM_ARM,
        "reference_local_raw_counterfactual": True,
        "raw_arm_gradient_read_count": 0,
        "reference_baseline_counterfactual_calls": 1,
        "raw_arm_baseline_counterfactual_calls": 0,
        "q_norm_reconstructed_not_caller_flag": True,
        "direction_rule_evaluated": True,
        "reference_assigned_credit_norm": 1.0,
        "raw_assigned_credit_norm": 1.0,
        "reference_raw_unit_dot_product": 1.0,
        "unit_direction_delta_sum_square": 1e-12,
        "unit_direction_distance": 1e-6,
        "direction_tolerance": 1e-6,
        "passed": True,
    }
    assert g46.validate_activation_record(inclusive)
    over = copy.deepcopy(inclusive)
    over["unit_direction_delta_sum_square"] = math.nextafter(1e-12, math.inf)
    over["unit_direction_distance"] = float(
        torch.sqrt(
            torch.as_tensor(
                over["unit_direction_delta_sum_square"], dtype=torch.float64
            )
        )
    )
    assert not g46.validate_activation_record(over)


def test_first_update_binds_target_only_routes_schedule_and_final_only_evidence(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, optimizers, record = _project_update(anchor, trajectory)
    assert record["passed"] is True
    assert record["branch_update_order"] == list(g46.ARMS)
    assert record["actor_head_optimizer_steps"] == {
        arm: 2.0 for arm in g46.ARMS
    }
    assert record["first_paired_direct_treatment_audit"]["passed"] is True
    assert record["order_swap_guard"]["passed"] is True
    active = False
    for pass_record in record["pass_records"]:
        for arm in g46.ARMS:
            gradients = pass_record["gradient_evidence"][arm]
            assert g46.validate_registered_gradient_evidence(gradients)
            assert g46.validate_baseline_gradient_group_evidence(
                gradients["baseline_gradient_groups"]
            )
            residual = pass_record["residual_evidence_by_arm"][arm]
            assert g46.validate_arm_credit_evidence(residual, arm)
            assert residual["residual_law_id"] == g46.TARGET_ONLY_RESIDUAL_LAW
            assert residual["actual_residual_baseline_read_count"] == 0
        reference = pass_record["composition"][g46.SHADOW_NORM_ARM]
        raw = pass_record["composition"][g46.RAW_NORM_ARM]
        assert g46._valid_composition(reference, g46.SHADOW_NORM_ARM)
        assert g46._valid_composition(raw, g46.RAW_NORM_ARM)
        assert reference["baseline_counterfactual_calls"] == 1
        assert raw["baseline_counterfactual_calls"] == 0
        assert raw["baseline_read_into_actual_scalar_norm"] == 0
        activation = pass_record["baseline_shadow_norm_activation"]
        assert g46.validate_activation_record(activation)
        assert activation["direction_evidence_source_arm"] == (
            g46.SHADOW_NORM_ARM
        )
        assert activation["reference_local_raw_counterfactual"] is True
        assert activation["raw_arm_gradient_read_count"] == 0
        assert activation["raw_equal_mean_credit_norm"] == reference[
            "raw_credit_norm"
        ]
        active |= activation["strict_treatment_activation_observed"]
    assert active

    conclusion = g46.build_conclusion_evidence([record], formal=False)
    assert g46.validate_conclusion_evidence(conclusion)
    assert len(g46.serialize_diagnostics(record)) > 1_000
    checkpoint = g46.build_final_checkpoint(
        g46.RAW_NORM_ARM,
        models[g46.RAW_NORM_ARM],
        record,
        conclusion,
        formal=False,
    )
    assert checkpoint["kind"] == "final_only"
    assert checkpoint["standalone_slow_present"] is False
    assert checkpoint["no_read_certificate"]["baseline_counterfactual_calls"] == 0
    assert g46.validate_baseline_gradient_groups_by_arm(
        checkpoint["baseline_gradient_groups_by_arm"]
    )
    assert all(
        min(
            g46._optimizer_step_value(optimizers[arm], parameter)
            for parameter in models[arm].actor_credit_parameters()
        )
        == 2.0
        for arm in g46.ARMS
    )


def test_update_conclusion_and_checkpoint_tampering_fail_closed(
    accepted_anchor_batch: tuple[
        g40.G40NativeSixPolicy, g40.AnchoredRosterTrajectory
    ],
) -> None:
    anchor, trajectory = accepted_anchor_batch
    models, _, record = _project_update(anchor, trajectory)
    conclusion = g46.build_conclusion_evidence([record], formal=False)

    leaked = copy.deepcopy(record)
    leaked["pass_records"][0]["composition"][g46.RAW_NORM_ARM][
        "baseline_counterfactual_calls"
    ] = 1
    assert not g46._update_evidence_valid(leaked)

    wrong_residual = copy.deepcopy(record)
    wrong_residual["pass_records"][0]["residual_evidence_by_arm"][
        g46.SHADOW_NORM_ARM
    ]["actual_residual_baseline_read_count"] = 1
    assert not g46._update_evidence_valid(wrong_residual)

    dead_baseline = copy.deepcopy(record)
    dead_baseline["pass_records"][0]["gradient_evidence"][g46.RAW_NORM_ARM][
        "baseline_gradient_groups"
    ]["shared_trunk_union_gradient_norm"] = 0.0
    assert not g46._update_evidence_valid(dead_baseline)

    forged = copy.deepcopy(conclusion)
    activation = forged["replicate_rows"][0]["reconstructed_passes"][0][
        "activation"
    ]
    activation["q_norm"] = 1.0
    activation["strict_treatment_activation_observed"] = True
    assert not g46.validate_conclusion_evidence(forged)

    with pytest.raises(ValueError, match="update evidence invalid"):
        g46.build_final_checkpoint(
            g46.RAW_NORM_ARM,
            models[g46.RAW_NORM_ARM],
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
    for replicate in g46.ACCEPTED_G40_ANCHOR_REPLICATES:
        record = copy.deepcopy(template)
        record["accepted_g40_anchor_replicate"] = replicate
        record["branch_boundary"]["accepted_g40_anchor_authority"] = (
            g41.accepted_g40_anchor_identity(replicate)
        )
        records.append(record)
    conclusion = g46.build_conclusion_evidence(records, formal=True)
    assert g46.validate_conclusion_evidence(conclusion)

    missing = copy.deepcopy(conclusion)
    missing["replicate_rows"].pop()
    assert not g46.validate_conclusion_evidence(missing)

    inactive = copy.deepcopy(conclusion)
    row = inactive["replicate_rows"][1]
    for item in row["reconstructed_passes"]:
        activation = item["activation"]
        activation["baseline_read_counterfactual_credit_norm"] = 1.0
        activation["raw_equal_mean_credit_norm"] = 1.0
        activation["q_norm"] = 0.0
        activation["strict_treatment_activation_observed"] = False
        activation["reference_assigned_credit_norm"] = 1.0
        activation["raw_assigned_credit_norm"] = 1.0
        item["active"] = False
    row["strict_activation_observed"] = False
    inactive["passed"] = False
    assert not g46.validate_conclusion_evidence(inactive)
