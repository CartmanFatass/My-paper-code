from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.vsp_02 import owner_action_responsive_lifecycle as lifecycle


ROOT = Path(__file__).resolve().parents[4]
CLI = ROOT / "scripts" / "run_vsp02_a1_owner_action_responsive_lifecycle.py"


def _claimed():
    token = lifecycle.default_owner()
    world = lifecycle.default_world()
    result = lifecycle.claim(
        lifecycle.LifecycleRecord("test", slot_id=3),
        token,
        world,
        physical_clock=0,
    )
    assert result.accepted
    return result.record, token, world


def _boundary(record, token, world, **overrides):
    values = {
        "contract": lifecycle.candidate_contract(),
        "action": lifecycle.OwnerAction.RELEASE,
        "command_token": token,
        "world": world,
        "boundary_index": 1,
        "physical_clock": 1,
        "tape": lifecycle.PairedTape("VSP02-A1-PAIRED-TAPE-1"),
        "release_id": "release-test",
    }
    values.update(overrides)
    return lifecycle.apply_boundary(record, **values)


def test_phase_schema_and_supported_separator_are_exact():
    report = lifecycle.run_lifecycle_certificate()
    assert report["phase_schema"] == [phase.value for phase in lifecycle.Phase]
    assert len(report["phase_schema"]) == 8
    assert report["separator"] == {
        "CANDIDATE|RELEASE": "ENDED_RELEASE",
        "CANDIDATE|HOLD": "ACTIVE",
        "Z0|RELEASE": "ACTIVE",
        "Z0|HOLD": "ACTIVE",
    }
    assert report["branch"] == "A1_OWNER_ACTION_RESPONSIVE_LIFECYCLE_SUPPORTED"


def test_claim_is_immutable_idempotent_and_conflicts_fail_closed():
    record, token, world = _claimed()
    duplicate = lifecycle.claim(record, token, world, physical_clock=1)
    assert duplicate.accepted is False
    assert duplicate.record == record
    conflict = lifecycle.claim(
        duplicate.record,
        replace(token, owner_epoch=token.owner_epoch + 1),
        world,
        physical_clock=1,
    )
    assert conflict.accepted is False
    assert conflict.record == record


@pytest.mark.parametrize(
    "mutator",
    [
        lambda token, world: (replace(token, owner_id="other"), world),
        lambda token, world: (replace(token, owner_epoch=token.owner_epoch + 1), world),
        lambda token, world: (
            replace(token, behavior_version=token.behavior_version - 1),
            world,
        ),
    ],
    ids=["wrong-owner", "wrong-epoch", "stale-version"],
)
def test_release_authority_uses_immutable_member_epoch_not_slot_or_visibility(mutator):
    record, token, world = _claimed()
    command_token, command_world = mutator(token, world)
    result = _boundary(record, command_token, command_world)
    assert result.accepted is False
    assert result.record.phase is lifecycle.Phase.ACTIVE
    assert result.record.release_ledger == ()


def test_authoritative_owner_departure_interrupts_while_visibility_loss_does_not():
    record, token, world = _claimed()
    departed = replace(world, authoritative_membership=frozenset())
    result = _boundary(record, token, departed)
    assert result.record.phase is lifecycle.Phase.ENDED_INTERRUPT
    assert result.record.end_cause is lifecycle.EndCause.INTERRUPT

    record, token, world = _claimed()
    hidden = replace(world, visible_roster=("partner-B",))
    result = _boundary(record, token, hidden)
    assert result.record.phase is lifecycle.Phase.ENDED_RELEASE


def test_visibility_is_not_authority_in_either_direction():
    record, token, world = _claimed()
    hidden = replace(world, visible_roster=("partner-B",))
    assert _boundary(record, token, hidden).record.phase is lifecycle.Phase.ENDED_RELEASE

    record, token, world = _claimed()
    attacker = replace(token, owner_id="attacker")
    attacker_visible = replace(world, visible_roster=world.visible_roster + ("attacker",))
    assert _boundary(record, attacker, attacker_visible).record.phase is lifecycle.Phase.ACTIVE


def test_release_without_claim_or_before_eligibility_is_rejected():
    token = lifecycle.default_owner()
    world = lifecycle.default_world()
    unclaimed = lifecycle.LifecycleRecord("unclaimed", slot_id=3)
    assert _boundary(unclaimed, token, world).record.phase is lifecycle.Phase.UNCLAIMED
    record, token, world = _claimed()
    early = _boundary(
        record,
        token,
        world,
        boundary_index=0,
        physical_clock=0,
    )
    assert early.record.phase is lifecycle.Phase.ACTIVE
    assert early.record.release_ledger == ()


def test_hold_never_closes_and_z0_release_is_log_only():
    record, token, world = _claimed()
    hold = _boundary(record, token, world, action=lifecycle.OwnerAction.HOLD)
    assert hold.record.phase is lifecycle.Phase.ACTIVE
    assert hold.record.primitive_clock == 1

    record, token, world = _claimed()
    z0_release = _boundary(
        record,
        token,
        world,
        contract=lifecycle.z0_contract(),
    )
    assert z0_release.record.phase is lifecycle.Phase.ACTIVE
    assert "RELEASE" in z0_release.record.command_log
    assert "RELEASE_LOGGED_NO_EDGE" in z0_release.record.acknowledgements
    assert z0_release.record.release_ledger == ()


def test_terminal_interrupt_release_natural_horizon_precedence():
    expected = [
        (dict(terminal=True, interrupt=True, natural=True, horizon=True), lifecycle.Phase.ENDED_TERMINAL),
        (dict(interrupt=True, natural=True, horizon=True), lifecycle.Phase.ENDED_INTERRUPT),
        (dict(natural=True, horizon=True), lifecycle.Phase.ENDED_RELEASE),
    ]
    for tape_flags, phase in expected:
        record, token, world = _claimed()
        tape = lifecycle.PairedTape("VSP02-A1-PAIRED-TAPE-1", **tape_flags)
        assert _boundary(record, token, world, tape=tape).record.phase is phase

    record, token, world = _claimed()
    natural = _boundary(
        record,
        token,
        world,
        action=lifecycle.OwnerAction.HOLD,
        tape=lifecycle.PairedTape(
            "VSP02-A1-PAIRED-TAPE-1", natural=True, horizon=True
        ),
    )
    assert natural.record.phase is lifecycle.Phase.ENDED_NATURAL

    record, token, world = _claimed()
    horizon = _boundary(
        record,
        token,
        world,
        action=lifecycle.OwnerAction.HOLD,
        tape=lifecycle.PairedTape("VSP02-A1-PAIRED-TAPE-1", horizon=True),
    )
    assert horizon.record.phase is lifecycle.Phase.ENDED_HORIZON


def test_release_and_target_close_ledgers_are_idempotent_and_version_closed():
    record, token, world = _claimed()
    ended = _boundary(record, token, world).record
    duplicate_release = _boundary(
        ended, token, world, boundary_index=2, physical_clock=2
    ).record
    assert duplicate_release == ended
    assert ended.release_ledger == ("release-test",)

    closed = lifecycle.close_target_score(
        ended,
        command_token=token,
        target=lifecycle.FROZEN_TARGET,
        score=lifecycle.FROZEN_SCORE,
        close_clock=2,
    )
    assert closed.accepted
    assert closed.record.phase is lifecycle.Phase.TARGET_CLOSED_TOMBSTONE
    assert not lifecycle.version_can_advance(
        (ended,), new_version=lifecycle.CURRENT_BEHAVIOR_VERSION + 1
    )
    assert lifecycle.version_can_advance(
        (closed.record,), new_version=lifecycle.CURRENT_BEHAVIOR_VERSION + 1
    )
    duplicate = lifecycle.close_target_score(
        closed.record,
        command_token=token,
        target=lifecycle.FROZEN_TARGET,
        score=lifecycle.FROZEN_SCORE,
        close_clock=99,
    )
    assert duplicate.record == closed.record


def test_target_tombstone_mismatch_and_stale_version_cannot_mutate_record():
    record, token, world = _claimed()
    ended = _boundary(record, token, world).record
    mismatch = lifecycle.close_target_score(
        ended,
        command_token=token,
        target=Fraction(99),
        score=lifecycle.FROZEN_SCORE,
        close_clock=2,
    )
    assert not mismatch.accepted and mismatch.record == ended

    stale = replace(token, behavior_version=token.behavior_version - 1)
    stale_result = lifecycle.close_target_score(
        ended,
        command_token=stale,
        target=lifecycle.FROZEN_TARGET,
        score=lifecycle.FROZEN_SCORE,
        close_clock=2,
    )
    assert not stale_result.accepted and stale_result.record == ended


def test_observation_firewall_excludes_authority_future_and_precommit_outcomes():
    record, _, world = _claimed()
    observation = lifecycle.predecision_observation(
        record, world, opaque_post_claim_cue="opaque"
    )
    assert lifecycle.observation_firewall_valid(observation)

    @dataclass(frozen=True)
    class LeakyObservation:
        committed_phase: str
        precommit_outcome: str

    assert not lifecycle.observation_firewall_valid(
        LeakyObservation("ACTIVE", "ENDED_RELEASE")
    )


def test_candidate_and_z0_contract_mismatch_controls_fail_exact_match():
    candidate = lifecycle.candidate_contract()
    z0 = lifecycle.z0_contract()
    assert lifecycle._matched_arm_contracts(candidate, z0)
    assert not lifecycle._matched_arm_contracts(
        candidate, replace(z0, tape_id="different")
    )
    assert not lifecycle._matched_arm_contracts(
        candidate, replace(z0, information_fields=("committed_phase",))
    )
    assert not lifecycle._matched_arm_contracts(
        candidate, replace(z0, command_bandwidth_bits=2)
    )


def test_every_terminal_branch_is_reachable_in_registered_precedence():
    expected = {
        "invalid_contract": "A1_INVALID_CONTRACT",
        "no_positive_survival": "A1_POSITIVE_SURVIVAL_SUPPORT_ABSENT",
        "owner_authorization": "A1_OWNER_AUTHORIZATION_FAILED",
        "ledger_closure": "A1_LEDGER_OR_CLOSURE_FAILED",
        "release_not_causal": "A1_RELEASE_NOT_CAUSAL",
        "z0_release_responsive": "A1_Z0_RELEASE_RESPONSIVE",
    }
    for fault, branch in expected.items():
        assert lifecycle.run_lifecycle_certificate(technical_fault=fault)["branch"] == branch


def test_missing_2x2_cell_fails_closed():
    report = lifecycle.run_lifecycle_certificate()
    report = deepcopy(report)
    del report["separator"]["CANDIDATE|RELEASE"]
    assert lifecycle.classify_a1(report) == "A1_INVALID_CONTRACT"


def test_exact_z0_mapping_and_named_controls_have_no_stochastic_draws():
    mappings = lifecycle.enumerate_z0_claim_time_mappings()
    assert len(mappings) == len(set(mappings)) == 4
    report = lifecycle.run_lifecycle_certificate()
    assert report["z0_claim_time_enumeration"]["post_claim_release_is_log_only_for_every_mapping"]
    assert all(report["named_tabular_controls"].values())


def test_manifest_artifact_and_zero_activity_are_deterministic_and_tamper_evident():
    manifest = lifecycle.build_a1_manifest(
        source_revision="a" * 40,
        run_id="technical-test",
        technical_only=True,
    )
    assert lifecycle.validate_a1_manifest(manifest) == ()
    first = lifecycle.run_a1_probe(manifest)
    second = lifecycle.run_a1_probe(manifest)
    assert first == second
    assert lifecycle.validate_a1_artifact(first) == ()
    round_tripped = json.loads(json.dumps(lifecycle.json_ready(first), sort_keys=True))
    assert lifecycle.validate_a1_artifact(round_tripped) == ()
    assert first["activity"]["registered_a_invocations"] == 0
    for field in lifecycle.ACTIVITY_ZERO_FIELDS:
        assert first["activity"][field] == 0
    tampered = deepcopy(first)
    tampered["report"]["separator"]["Z0|RELEASE"] = "ENDED_RELEASE"
    tampered["report"]["branch"] = "A1_Z0_RELEASE_RESPONSIVE"
    tampered["branch"] = "A1_Z0_RELEASE_RESPONSIVE"
    assert "artifact differs from deterministic canonical reconstruction" in lifecycle.validate_a1_artifact(tampered)


def test_cli_help_is_available_without_consuming_registered_invocation():
    completed = subprocess.run(
        [sys.executable, "-B", str(CLI), "--help"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "registered-probe" in completed.stdout
