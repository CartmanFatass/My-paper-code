from __future__ import annotations

from dataclasses import fields, replace
from fractions import Fraction
import json

import pytest

from experiments.candidates.recct_lite import dependency_noninterference as recct


F = Fraction


def _raw(gate):
    return {field.name: getattr(gate, field.name) for field in fields(recct.GateInput)}


def _evaluations(decision):
    return {item.mask: item for item in decision.evaluations}


def test_registered_zero_return_audit_passes_narrow_contract_and_is_byte_stable():
    first = recct.run_noninterference_audit()
    second = recct.run_noninterference_audit()

    assert first.terminal == "PASS_DEPENDENCY_NONINTERFERENCE_D0"
    assert first.selected_mask is recct.Mask.E1
    assert first.feasible_masks == (recct.Mask.ZERO, recct.Mask.E1)
    assert first.g_sd_selected_mask is recct.Mask.ZERO
    assert first.g_sd_feasible_masks == (recct.Mask.ZERO,)
    assert first.orientation_swapped_mask is recct.Mask.E2
    assert first.rho_values == (F(3, 5), F(3, 5))
    assert dict(first.q_values) == {
        "00": F(0),
        "10": F(39, 20),
        "01": F(-21, 20),
        "11": F(9, 10),
    }
    assert all(value for _, value in first.invariants)
    assert first.to_bytes() == second.to_bytes()
    assert json.loads(first.to_bytes())["selected_mask"] == "10"


def test_audit_seed_record_and_owner_key_never_enter_primary_gate_or_update():
    world = recct.build_world()
    base = recct.build_gate_input(world)
    variants = (
        recct.build_gate_input(world, audit_seed=1),
        recct.build_gate_input(world, audit_seed=999),
        recct.build_gate_input(world, audit_record={"record_type": "audit"}),
        recct.build_gate_input(world, owner_keys=("renamed-1", "renamed-2")),
    )
    base_decision = recct.decide(base, world)

    for gate in variants:
        decision = recct.decide(gate, world)
        assert recct.gate_input_bytes(gate) == recct.gate_input_bytes(base)
        assert decision.selected_mask == base_decision.selected_mask
        assert decision.selected_state_bytes == base_decision.selected_state_bytes


@pytest.mark.parametrize(
    "field_name",
    (
        "owner_key",
        "owner_embedding",
        "audit_seed",
        "audit_outcome",
        "psi",
        "return",
        "future_state",
        "prior_oracle",
        "global_rng",
        "cache",
    ),
)
def test_undeclared_primary_gate_inputs_fail_closed(field_name):
    raw = _raw(recct.build_gate_input(recct.build_world()))
    raw[field_name] = object()
    with pytest.raises(ValueError, match="undeclared gate input"):
        recct.bind_gate_input(raw)


@pytest.mark.parametrize("stage", ("fit", "normalize", "threshold"))
def test_audit_typed_records_are_rejected_by_every_pretreatment_pipeline(stage):
    clean = ({"record_type": "training", "value": "1/4"},)
    contaminated = clean + ({"record_type": "audit", "value": "99"},)

    assert recct.fit_pretreatment_records(clean, stage) == F(1, 4)
    with pytest.raises(ValueError, match="audit-typed"):
        recct.fit_pretreatment_records(contaminated, stage)


def test_invalid_equality_epoch_rng_and_ancestry_fail_before_optimizer_evaluation():
    world = recct.build_world()
    gate = recct.build_gate_input(world)

    for invalid in (replace(gate, equality_valid=False), replace(gate, epoch_valid=False),
                    replace(gate, rng_counters=gate.rng_counters + (("global", 1),))):
        with pytest.raises(ValueError):
            recct.decide(invalid, world)

    ancestry = gate.ancestry
    negatives = (
        replace(ancestry, edges=ancestry.edges[:-1]),
        replace(ancestry, edges=ancestry.edges + (("mutable_live", "learner_checkpoint"),),
                mutable_nodes=("mutable_live",)),
        replace(ancestry, edges=ancestry.edges + (("shared", "sealed_fold"),
                                                  ("shared", "learner_checkpoint"))),
        replace(ancestry, edges=ancestry.edges + ((recct.SHADOW_NODES[0], "learner_checkpoint"),)),
        replace(ancestry, mutable_nodes=(recct.FITTED_NODES[0],)),
        replace(ancestry, fitted_nodes=ancestry.fitted_nodes + ("extra_fitted",)),
        replace(ancestry, evaluation_nodes=ancestry.evaluation_nodes + ("shadow-extra",)),
        replace(ancestry, fitted_nodes=()),
        replace(ancestry, evaluation_nodes=ancestry.evaluation_nodes[:-1]),
    )
    for invalid in negatives:
        assert not recct.validate_ancestry(invalid)
        with pytest.raises(ValueError, match="ancestry graph"):
            recct.decide(replace(gate, ancestry=invalid), world)


def test_rho_q_derived_credit_and_support_threshold_cells_are_exact():
    config = recct.Config()
    probe = recct.Probe("e1", True, F(0), F(3, 4), F(1))

    assert "signed_credit" not in {field.name for field in fields(recct.Probe)}
    assert recct.rho(probe, config) == F(3, 5)
    assert recct.edge_feasible_values(True, F(1, 2), F(1, 4), config)
    assert not recct.edge_feasible_values(True, F(1, 2) - F(1, 100), F(1, 4), config)
    assert not recct.edge_feasible_values(True, F(1, 2), F(1, 4) - F(1, 100), config)
    assert not recct.edge_feasible_values(False, F(1), F(1), config)
    assert recct.truth_table_complete(config)
    with pytest.raises(ValueError, match="denominator"):
        recct.rho(replace(probe, sigma=-config.epsilon), config)


def test_hysteresis_has_no_lexicographic_tie_and_requires_strict_gap():
    config = recct.Config()
    tie = {recct.Mask.ZERO: F(1), recct.Mask.E1: F(1), recct.Mask.E2: F(0), recct.Mask.BOTH: F(-1)}
    at = {
        recct.Mask.ZERO: F(0),
        recct.Mask.E1: config.eta,
        recct.Mask.E2: F(-1),
        recct.Mask.BOTH: F(-2),
    }
    above = at | {recct.Mask.E1: config.eta + F(1, 100)}
    nonleader_tie = {
        recct.Mask.ZERO: F(0), recct.Mask.E1: F(2), recct.Mask.E2: F(2), recct.Mask.BOTH: F(1)
    }

    assert recct.choose_mask(recct.Mask.ZERO, recct.MASKS, tie, config.eta) is recct.Mask.ZERO
    assert recct.choose_mask(recct.Mask.ZERO, recct.MASKS, at, config.eta) is recct.Mask.ZERO
    assert recct.choose_mask(recct.Mask.ZERO, recct.MASKS, above, config.eta) is recct.Mask.E1
    assert recct.choose_mask(
        recct.Mask.E1,
        (recct.Mask.ZERO, recct.Mask.E2),
        tie,
        config.eta,
    ) is recct.Mask.ZERO
    assert recct.choose_mask(
        recct.Mask.BOTH, recct.MASKS, nonleader_tie, config.eta
    ) is recct.Mask.BOTH


def test_literal_zero_initialization_and_complete_four_mask_enumeration_fail_closed():
    world = recct.build_world()
    gate = recct.build_gate_input(world)

    with pytest.raises(ValueError, match="literal 00"):
        recct.decide(replace(gate, current_mask=recct.Mask.E1), world)
    with pytest.raises(ValueError, match="exactly once"):
        recct.evaluate_masks(world, gate, (recct.Mask.ZERO,) * 4)


def test_each_mask_restores_one_identical_world_and_one_optimizer_transition():
    world = recct.build_world()
    source = recct.world_bytes(world)
    gate = recct.build_gate_input(world)
    forward = recct.evaluate_masks(world, gate)
    reverse = recct.evaluate_masks(world, gate, tuple(reversed(recct.MASKS)))

    assert world.roster_roles == ("r0", "r1", "k")
    assert {node for edge in gate.ancestry.edges for node in edge} >= {
        "preprocessor",
        "fitted_learner",
    }
    assert set(recct.REQUIRED_ANCESTRY_EDGES) <= set(gate.ancestry.edges)
    for family in recct.STATE_FAMILIES:
        assert (f"{family}_checkpoint", f"{family}_state") in gate.ancestry.edges
        assert all((f"{family}_state", shadow) in gate.ancestry.edges
                   for shadow in recct.SHADOW_NODES)
    assert recct.world_bytes(world) == source
    assert len({item.clone_id for item in forward}) == 4
    assert len({item.source_digest for item in forward}) == 1
    assert {item.mask: item.state_bytes for item in forward} == {
        item.mask: item.state_bytes for item in reverse
    }
    for item in forward:
        clone = recct.restore_world(item.state_bytes)
        assert clone.optimizer.scheduler_step == 1
        assert clone.optimizer.scaler == world.optimizer.scaler
        assert clone.optimizer.clip_limit == world.optimizer.clip_limit
        assert clone.optimizer.accumulation == (F(0), F(0))
        assert replace(clone, optimizer=world.optimizer) == world


def test_exact_optimizer_states_costs_and_q_values_use_one_frozen_evaluator():
    world = recct.build_world()
    gate = recct.build_gate_input(world)
    decision = recct.decide(gate, world)
    rows = _evaluations(decision)

    parameters = {
        mask: recct.restore_world(rows[mask].state_bytes).optimizer.parameters
        for mask in recct.MASKS
    }
    assert parameters == {
        recct.Mask.ZERO: (F(0), F(0)),
        recct.Mask.E1: (F(1, 4), F(0)),
        recct.Mask.E2: (F(0), F(1, 4)),
        recct.Mask.BOTH: (F(1, 4), F(1, 4)),
    }
    assert {mask: rows[mask].q for mask in recct.MASKS} == {
        recct.Mask.ZERO: F(0),
        recct.Mask.E1: F(39, 20),
        recct.Mask.E2: F(-21, 20),
        recct.Mask.BOTH: F(9, 10),
    }
    assert decision.feasible_masks == (recct.Mask.ZERO, recct.Mask.E1)
    assert decision.selected_mask is recct.Mask.E1


def test_owner_bijection_and_orientation_swap_are_equivariant():
    world = recct.build_world()
    gate = recct.build_gate_input(world, owner_keys=("alice", "bob"))
    renamed = recct.build_gate_input(world, owner_keys=("u7", "u2"))
    base = recct.decide(gate, world)
    swapped_world = replace(
        world,
        gradients=(world.gradients[0], world.gradients[2], world.gradients[1]),
    )
    swapped_gate = replace(
        recct.build_gate_input(swapped_world),
        proposals=tuple(reversed(gate.proposals)),
    )
    swapped = recct.decide(swapped_gate, swapped_world)

    assert recct.gate_input_bytes(gate) == recct.gate_input_bytes(renamed)
    assert base.selected_mask is recct.Mask.E1
    assert swapped.selected_mask is recct.Mask.E2
    base_rows, swapped_rows = _evaluations(base), _evaluations(swapped)
    assert base_rows[recct.Mask.ZERO].q == swapped_rows[recct.Mask.ZERO].q
    assert base_rows[recct.Mask.BOTH].q == swapped_rows[recct.Mask.BOTH].q
    assert base_rows[recct.Mask.E1].q == swapped_rows[recct.Mask.E2].q
    assert base_rows[recct.Mask.E2].q == swapped_rows[recct.Mask.E1].q


def test_real_shadow_bytes_semantic_firewall_and_reporting_sink_are_closed():
    world = recct.build_world()
    source = recct.world_bytes(world)
    gate = recct.build_gate_input(world)
    first = recct.g_sc(gate, world, "psi-left")
    second = recct.g_sc(gate, world, "psi-right")
    selected = _evaluations(first)[first.selected_mask]

    assert first.selected_mask == second.selected_mask
    assert first.selected_state_bytes == second.selected_state_bytes
    assert first.selected_state_bytes == selected.state_bytes
    assert recct.world_bytes(recct.restore_world(selected.state_bytes)) == selected.state_bytes

    receipt = {"authenticated": True, "confirmation": True, "support_stratum": "s0"}
    assert recct.g_sem(receipt) != recct.g_pi(receipt)
    assert recct.world_bytes(world) == source
    sd = recct.g_sd(gate, world, (-1, 1))
    assert sd.evaluations == first.evaluations
    assert sd.feasible_masks == (recct.Mask.ZERO,)
    assert sd.selected_mask is recct.Mask.ZERO


def test_world_mismatch_semantic_schema_and_sign_contract_fail_closed():
    world = recct.build_world()
    gate = recct.build_gate_input(world)

    with pytest.raises(ValueError, match="world differ"):
        recct.decide(gate, replace(world, owner_epoch=6))
    with pytest.raises(ValueError, match="schema"):
        recct.g_sem({"authenticated": True})
    with pytest.raises(ValueError, match="signs"):
        recct.g_sd(gate, world, (0, 1))
