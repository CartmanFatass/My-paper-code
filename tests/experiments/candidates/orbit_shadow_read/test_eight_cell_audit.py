from __future__ import annotations

from dataclasses import fields, replace
import inspect
import json

import pytest

from experiments.candidates.orbit_shadow_read import eight_cell_audit as orbit


def _find(result, b, role, q):
    return next(
        cell for cell in result.cells if (cell.b, cell.role, cell.q) == (b, role, q)
    )


def test_exact_eight_cell_audit_reaches_logit_and_first_action_kernel():
    result = orbit.run_eight_cell_audit()

    assert result.valid is True
    assert result.terminal is orbit.Terminal.LOGIT_AND_KERNEL
    assert result.theta_logit == pytest.approx(2.8284271247461903)
    assert result.theta_kernel == pytest.approx(0.9242343145200196)
    assert result.theta_logit > result.calibration.delta_logit
    assert result.theta_kernel > result.calibration.delta_kernel
    assert result.strict_theta_logit == 0.0
    assert result.strict_theta_kernel == 0.0
    assert all(passed for _, passed in result.invariants)
    assert result.owner_agnostic_null_reproduces is True


def test_whole_block_uses_eight_independent_equal_state_clones_and_q_aliases():
    result = orbit.run_eight_cell_audit()
    expected = tuple(
        (b, role, q)
        for b in (0, 1)
        for role in (0, 1)
        for q in (0, 1)
    )

    assert tuple((cell.b, cell.role, cell.q) for cell in result.cells) == expected
    assert len({cell.clone_id for cell in result.cells}) == 8
    assert len({cell.snapshot_digest for cell in result.cells}) == 1
    assert all(cell.support for cell in result.cells)
    for b in (0, 1):
        for role in (0, 1):
            assert _find(result, b, role, 0).actor_input == _find(
                result, b, role, 1
            ).actor_input
            assert _find(result, b, role, 0).logits == _find(
                result, b, role, 1
            ).logits
            assert _find(result, b, role, 0).kernel == _find(
                result, b, role, 1
            ).kernel


def test_sibling_writer_changes_only_b_input_and_authenticates_ancestry():
    snapshot = orbit.build_snapshot()
    zero = orbit.write_sibling(snapshot, 0)
    one = orbit.write_sibling(snapshot, 1)

    assert replace(zero.writer_input, b=1) == one.writer_input
    assert zero.payload == b"\x00"
    assert one.payload == b"\x01"
    assert orbit.verify_sibling(zero)
    assert orbit.verify_sibling(one)
    assert not orbit.verify_sibling(replace(zero, payload=b"\x01"))
    assert not orbit.verify_sibling(replace(one, auth_digest="0" * 64))
    with pytest.raises(ValueError, match="binary"):
        orbit.write_sibling(snapshot, 2)


def test_snapshot_restore_is_byte_equivalent_and_rejects_noncanonical_clone_source():
    snapshot = orbit.build_snapshot()
    source = orbit.serialize_snapshot(snapshot)
    clone = orbit.restore_clone(source, "clone-test")

    assert clone.snapshot == snapshot
    assert orbit.serialize_snapshot(clone.snapshot) == source
    with pytest.raises(ValueError, match="byte equivalent"):
        orbit.restore_clone(b" " + source, "noncanonical")


def test_strict_temporal_null_has_no_payload_or_b_input_and_is_b_blind():
    signature = inspect.signature(orbit.strict_temporal_null)
    assert tuple(signature.parameters) == ("snapshot", "role", "age")
    assert "payload" not in signature.parameters
    assert "b" not in signature.parameters

    snapshot = orbit.build_snapshot()
    for role in (0, 1):
        first = orbit.strict_temporal_null(snapshot, role, 0)
        second = orbit.strict_temporal_null(snapshot, role, 0)
        assert first == second

    result = orbit.run_eight_cell_audit()
    assert result.strict_theta_logit == result.strict_theta_kernel == 0.0


def test_centered_interaction_has_zero_margins_and_owner_agnostic_null_replays():
    result = orbit.run_eight_cell_audit()

    assert orbit._zero_marginal(result.cells)
    assert orbit._interaction(result.cells, "logits", center=True) == (2.0, -2.0)
    assert all(
        orbit.owner_agnostic_payload_null(cell.actor_input) == cell.logits
        for cell in result.cells
    )
    assert "owner" not in {field.name for field in fields(orbit.ActorInput)}


def test_disjoint_duplicate_calibration_freezes_thresholds_from_zero_noise():
    calibration = orbit.calibrate()
    source_digest = orbit._digest(orbit.serialize_snapshot(orbit.build_snapshot()))
    calibration_snapshot = orbit.Snapshot(
        snapshot_id="disjoint-calibration-s0",
        owner_epoch=3,
        current_state=(0.125, -0.125),
        legal_actions=("hold", "advance"),
        recurrent_state=(0.125, -0.125),
    )

    assert calibration.manifest_ids[0] != calibration.manifest_ids[1]
    assert calibration.calibration_snapshot_digest != source_digest
    assert calibration.calibration_snapshot_digest == orbit._digest(
        orbit.serialize_snapshot(calibration_snapshot)
    )
    assert calibration.eta_logit == calibration.eta_kernel == 0.0
    assert calibration.tau_logit == 8.0 * calibration.one_ulp_logit
    assert calibration.tau_kernel == 8.0 * calibration.one_ulp_kernel
    assert calibration.delta_logit == 4.0 * calibration.tau_logit
    assert calibration.delta_kernel == 4.0 * calibration.tau_kernel


@pytest.mark.parametrize(
    ("valid", "theta_logit", "theta_kernel", "expected"),
    (
        (False, 10.0, 10.0, orbit.Terminal.INVALID),
        (True, 2.0, 2.0, orbit.Terminal.LOGIT_AND_KERNEL),
        (True, 2.0, 0.0, orbit.Terminal.LOGIT_ONLY),
        (True, 0.0, 2.0, orbit.Terminal.KERNEL_ONLY),
        (True, 0.0, 0.0, orbit.Terminal.NONE),
    ),
)
def test_terminal_classification_is_branch_complete(
    valid, theta_logit, theta_kernel, expected
):
    assert orbit.classify(valid, theta_logit, theta_kernel, 1.0, 1.0) is expected


def test_schema_and_canonical_result_are_complete_and_byte_stable():
    first = orbit.run_eight_cell_audit()
    second = orbit.run_eight_cell_audit()

    assert tuple(name for name, _ in orbit.SCHEMAS) == (
        "F_match",
        "F_TQ",
        "F_ORBIT",
        "F_audit",
    )
    assert first.to_bytes() == second.to_bytes()
    payload = json.loads(first.to_bytes())
    assert payload["terminal"] == (
        "PASS_LOGIT_INTERACTION_REACHES_FIRST_ACTION_KERNEL"
    )
    assert payload["valid"] is True
    assert payload["strict_theta_logit"] == 0.0
    assert payload["strict_theta_kernel"] == 0.0
    assert len(payload["cells"]) == 8
    assert all(payload["invariants"].values())


def test_adapter_rejects_unregistered_role_or_q_alias():
    snapshot = orbit.build_snapshot()
    clone = orbit.restore_clone(orbit.serialize_snapshot(snapshot), "clone")
    write = orbit.write_sibling(snapshot, 0)

    with pytest.raises(ValueError, match="binary"):
        orbit.q_adapter(clone, write, 2, 0)
    with pytest.raises(ValueError, match="binary"):
        orbit.q_adapter(clone, write, 0, 2)
    with pytest.raises(ValueError, match="provenance"):
        orbit.q_adapter(clone, replace(write, auth_digest="0" * 64), 0, 0)

    other = replace(snapshot, snapshot_id="unrelated-source")
    with pytest.raises(ValueError, match="source snapshots differ"):
        orbit.q_adapter(clone, orbit.write_sibling(other, 0), 0, 0)
