from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json

import pytest

from experiments.candidates.scope_1s import instance_certificate as scope


F = Fraction


def test_synthetic_unit_certificate_passes_and_canonical_bytes_are_stable():
    first = scope.run_instance_certificate()
    second = scope.run_instance_certificate()

    assert first.terminal == "PASS_SYNTHETIC_UNIT_CERTIFICATE"
    assert first.actual_instance_status == "ABSENT_ACTIVE_Q16_OBJECTS"
    assert first.actor_tv == 1
    assert first.crossover_gaps == (64, 64)
    assert first.correct_value == 60
    assert first.reset_value == first.current_only_value == 32
    assert first.deranged_value == 28
    assert first.current_only_maps == 9
    assert first.donor_table == (("00", 2), ("01", 2), ("10", 2), ("11", 2))
    assert all(value for _, value in first.invariants)
    assert first.to_bytes() == second.to_bytes()
    assert json.loads(first.to_bytes())["terminal"] == first.terminal


def test_byte_manifest_is_complete_contiguous_and_X_excludes_history_audit_and_post():
    manifest = scope.build_manifest()
    x = scope.current_x(manifest)

    assert scope.validate_manifest(manifest)
    assert len(manifest.source_bytes) == 38
    assert len(x) == 10
    assert {field.category for field in manifest.fields} == set(scope.Category)
    assert x == manifest.source_bytes[:10]

    gap = replace(manifest.fields[1], start=5)
    with pytest.raises(ValueError, match="ancestry"):
        scope.current_x(replace(manifest, fields=(manifest.fields[0], gap) + manifest.fields[2:]))
    leaking = replace(
        manifest,
        actor_edges=manifest.actor_edges + (("q16_atom", "current_state"),),
    )
    assert not scope.validate_manifest(leaking)


def test_two_registered_cells_freeze_X_and_complete_compatibility_keys():
    s0, s1 = scope.build_cells()

    assert s0.name == "s0" and s1.name == "s1"
    assert s0.weight == s1.weight == F(1, 2)
    assert s0.x == s1.x
    assert (s0.key.roster_n, s0.key.anonymous_role, s0.key.absence) == (3, 0, 4)
    assert (s1.key.roster_n, s1.key.anonymous_role, s1.key.absence) == (3, 1, 8)
    assert s0.key.task_hash == s1.key.task_hash == "task-v1"
    assert s0.key.environment_hash == s1.key.environment_hash == "env-v1"
    assert s0.key.reader_hash == s1.key.reader_hash == "reader-v1"
    assert s0.key.import_adapter_hash == s1.key.import_adapter_hash == "adapter-v1"
    with pytest.raises(ValueError, match="role/absence"):
        scope.build_key(0, 8)


def test_source_owner_and_epoch_are_not_compatibility_or_actor_inputs():
    carriers = scope.build_carriers(scope.build_cells()[0])

    assert tuple(carrier.target_bit for carrier in carriers) == scope.TARGET_BITS
    assert sum(carrier.target_bit for carrier in carriers) == 4
    assert len({carrier.source_owner for carrier in carriers}) == 3
    assert len({carrier.source_epoch for carrier in carriers}) == 8
    assert len({carrier.key for carrier in carriers}) == 1
    assert len({carrier.x for carrier in carriers}) == 1


def test_complete_Q16_atoms_and_frozen_actor_have_registered_TV():
    z0, z1 = scope.q16_atom(0), scope.q16_atom(1)

    assert z0.name == "z0" and z0.payload == b"\x00" * 16
    assert z1.name == "z1" and z1.payload == b"\x01" * 16
    assert scope.actor_kernel(scope.Choice.Z0) == (1, 0)
    assert scope.actor_kernel(scope.Choice.Z1) == (0, 1)
    assert scope.total_variation(
        scope.actor_kernel(scope.Choice.Z0),
        scope.actor_kernel(scope.Choice.Z1),
    ) == 1
    with pytest.raises(ValueError, match="binary"):
        scope.q16_atom(2)


def test_crossover_runner_has_exact_common_tape_values_and_gaps():
    assert scope.value(0, scope.Choice.Z0) == 60
    assert scope.value(0, scope.Choice.Z1) == -4
    assert scope.value(1, scope.Choice.Z1) == 60
    assert scope.value(1, scope.Choice.Z0) == -4
    assert scope.value(0, scope.Choice.RESET) == 64
    assert scope.value(1, scope.Choice.RESET) == 0
    assert scope.value(0, scope.Choice.Z0) - scope.value(0, scope.Choice.Z1) == 64
    assert scope.value(1, scope.Choice.Z1) - scope.value(1, scope.Choice.Z0) == 64


def test_all_nine_current_only_extreme_maps_are_enumerated_and_bounded_by_32():
    rows = scope.enumerate_current_only_maps(scope.build_cells())
    by_map = {tuple(choice.value for choice in mapping): score for mapping, score in rows}

    assert len(rows) == len(by_map) == 9
    assert max(by_map.values()) == 32
    assert by_map[("Reset", "Reset")] == 32
    assert by_map[("z0", "z0")] == 28
    assert by_map[("z1", "z1")] == 28
    assert all(score <= 32 for score in by_map.values())


def test_fixed_whole_payload_donors_are_deranged_balanced_and_within_cell():
    cell = scope.build_cells()[0]
    carriers = scope.build_carriers(cell)
    rows = scope.donor_rows(carriers)
    table = {
        pair: sum(
            target.target_bit == pair[0] and donor.target_bit == pair[1]
            for target, donor in rows
        )
        for pair in ((0, 0), (0, 1), (1, 0), (1, 1))
    }

    assert tuple(donor.unit for _, donor in rows) == scope.DONOR_PERMUTATION
    assert all(target.unit != donor.unit for target, donor in rows)
    assert all(target.cell_name == donor.cell_name for target, donor in rows)
    assert all(target.x == donor.x and target.key == donor.key for target, donor in rows)
    assert table == {(0, 0): 2, (0, 1): 2, (1, 0): 2, (1, 1): 2}
    assert scope.verify_donors(rows)


def test_donor_validator_rejects_fixed_point_partial_payload_and_cross_cell():
    s0, s1 = scope.build_cells()
    rows = list(scope.donor_rows(scope.build_carriers(s0)))

    rows[0] = (rows[0][0], rows[0][0])
    assert not scope.verify_donors(rows)

    rows = list(scope.donor_rows(scope.build_carriers(s0)))
    target, donor = rows[0]
    rows[0] = (target, replace(donor, atom=replace(donor.atom, payload=b"partial")))
    assert not scope.verify_donors(rows)

    rows = list(scope.donor_rows(scope.build_carriers(s0)))
    rows[0] = (rows[0][0], scope.build_carriers(s1)[1])
    assert not scope.verify_donors(rows)
    with pytest.raises(ValueError, match="eight"):
        scope.donor_rows(scope.build_carriers(s0)[:-1])


def test_H64_interference_and_zero_generation_distance_certificate_is_strict():
    certificate = scope.cluster_certificate(scope.build_cells())

    assert certificate.horizons == (64, 64)
    assert certificate.cross_cluster_edges == ()
    assert scope.validate_cluster(certificate)
    assert not scope.validate_cluster(replace(certificate, horizons=(64, 63)))
    assert not scope.validate_cluster(
        replace(certificate, cross_cluster_edges=(("cluster-s0", "cluster-s1"),))
    )
    assert not scope.validate_cluster(replace(certificate, evaluated_actor_hash="actor-v2"))


@pytest.mark.parametrize(
    ("change", "issue"),
    (
        ({"x_closed": False}, "incomplete_X"),
        ({"prior_epoch_descendants_in_x": True}, "incomplete_X"),
        ({"distinct_complete_atoms": 1}, "insufficient_complete_atoms"),
        ({"same_x_k_outcome_divergent": False}, "missing_same_X_K_pair"),
        ({"tv": F(1, 5)}, "actor_TV_below_1/4"),
        ({"crossover_gaps": (F(7), F(8))}, "crossover_gap_below_8"),
        ({"current_only_gap": F(4)}, "current_only_gap_not_above_4"),
        ({"donor_valid": False}, "invalid_donor"),
        ({"h64_closed": False}, "H64_interference_leak"),
        ({"zero_policy_generation_distance": False}, "nonzero_policy_generation_distance"),
    ),
)
def test_actual_cell_validator_exercises_each_stop_branch(change, issue):
    unit = scope.unit_bound_cell()

    assert scope.validate_bound_cell(unit) == ()
    assert issue in scope.validate_bound_cell(replace(unit, **change))


def test_actual_binding_reports_absence_without_turning_it_into_scientific_failure():
    status, missing = scope.bind_actual_instances(())

    assert status == "ABSENT_ACTIVE_Q16_OBJECTS"
    assert missing == (
        "registered_complete_Q16_atom_schema_writer_reader_actor_binding",
        "supported_same_X_K_outcome_divergent_pair",
        "H64_cluster_and_zero_generation_distance_certificate",
    )
    assert scope.bind_actual_instances((scope.unit_bound_cell(),)) == (
        "BOUND_ACTUAL_INSTANCE_PASS",
        (),
    )
    invalid = replace(scope.unit_bound_cell(), current_only_gap=F(4))
    status, issues = scope.bind_actual_instances((invalid,))
    assert status == "BOUND_ACTUAL_INSTANCE_INVALID"
    assert issues == ("synthetic-unit-cell:current_only_gap_not_above_4",)
