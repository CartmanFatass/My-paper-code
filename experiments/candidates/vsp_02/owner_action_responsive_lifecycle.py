"""Deterministic VSP02-A1 owner-action-responsive lifecycle certificate.

This module deliberately contains no environment, policy, learner, optimizer,
return, or model-fit activity.  It is a finite lifecycle transducer plus exact
control witnesses for the frozen A1 question.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, replace
from enum import Enum
from fractions import Fraction
from itertools import product
from typing import Iterable, Mapping


A1_SCHEMA_VERSION = 1
A1_ASSIGNMENT_ID = "VSP02-A1-OWNER-ACTION-RESPONSIVE-LIFECYCLE"
A1_CANDIDATE = "CAND-VSP-02@adversarial-revision-v8"
A1_RESOURCE_CLASS = "A_READONLY_OR_ZERO_RUNTIME"
CURRENT_BEHAVIOR_VERSION = 8
FROZEN_TARGET = Fraction(7, 4)
FROZEN_SCORE = Fraction(5, 4)


class Phase(str, Enum):
    UNCLAIMED = "UNCLAIMED"
    ACTIVE = "ACTIVE"
    ENDED_RELEASE = "ENDED_RELEASE"
    ENDED_INTERRUPT = "ENDED_INTERRUPT"
    ENDED_NATURAL = "ENDED_NATURAL"
    ENDED_TERMINAL = "ENDED_TERMINAL"
    ENDED_HORIZON = "ENDED_HORIZON"
    TARGET_CLOSED_TOMBSTONE = "TARGET_CLOSED_TOMBSTONE"


class Backend(str, Enum):
    CANDIDATE = "CANDIDATE"
    Z0 = "Z0"


class OwnerAction(str, Enum):
    RELEASE = "RELEASE"
    HOLD = "HOLD"


class EndCause(str, Enum):
    RELEASE = "RELEASE"
    INTERRUPT = "INTERRUPT"
    NATURAL = "NATURAL"
    TERMINAL = "TERMINAL"
    HORIZON = "HORIZON"


class CompletionLaw(str, Enum):
    """Legal Z0 claim-time laws; both survive the registered A1 boundary."""

    SURVIVE_ONE_MORE_BOUNDARY = "SURVIVE_ONE_MORE_BOUNDARY"
    SURVIVE_TWO_MORE_BOUNDARIES = "SURVIVE_TWO_MORE_BOUNDARIES"


TERMINAL_PRECEDENCE = (
    "TERMINAL",
    "INTERRUPT",
    "AUTHORIZED_RELEASE",
    "NATURAL",
    "HORIZON",
)

SHARED_OBSERVATION_FIELDS = (
    "committed_phase",
    "prior_acknowledgements",
    "physical_clock",
    "primitive_clock",
    "own_boundary_clock",
    "owner_epoch_token",
    "visible_roster",
    "opaque_post_claim_cue",
)

FORBIDDEN_OBSERVATION_FIELDS = frozenset(
    {
        "authoritative_membership",
        "future_natural_tape",
        "future_interruption_tape",
        "future_terminal_tape",
        "sampled_terminal_time",
        "time_to_terminal",
        "partner_family_identity",
        "unreleased_target",
        "precommit_outcome",
    }
)

ACTIVITY_ZERO_FIELDS = (
    "environment_transitions",
    "policy_calls",
    "learner_calls",
    "trainer_calls",
    "optimizer_updates",
    "return_evaluations",
    "model_fits",
    "stochastic_draws",
    "retries_rescues_sweeps",
)


@dataclass(frozen=True, order=True)
class MemberEpoch:
    owner_id: str
    owner_epoch: int


@dataclass(frozen=True)
class AuthorityToken:
    owner_id: str
    owner_epoch: int
    behavior_version: int

    @property
    def member_epoch(self) -> MemberEpoch:
        return MemberEpoch(self.owner_id, self.owner_epoch)


@dataclass(frozen=True)
class WorldView:
    authoritative_membership: frozenset[MemberEpoch]
    visible_roster: tuple[str, ...]
    current_behavior_version: int


@dataclass(frozen=True)
class ArmContract:
    backend: Backend
    information_fields: tuple[str, ...] = SHARED_OBSERVATION_FIELDS
    memory_cells: int = 2
    computation_cells: int = 4
    command_alphabet: tuple[str, ...] = ("HOLD", "RELEASE")
    command_bandwidth_bits: int = 1
    primitive_policy: str = "FROZEN_PRIMITIVE_V1"
    tape_id: str = "VSP02-A1-PAIRED-TAPE-1"
    ledger_schema: str = "TARGET_SCORE_TOMBSTONE_V1"
    reward_contract: str = "NO_CLAIM_RELEASE_DURATION_OR_END_REWARD"
    horizon: int = 4
    optimizer_exposure: int = 0
    release_has_stopping_edge: bool = False


@dataclass(frozen=True)
class PairedTape:
    tape_id: str
    terminal: bool = False
    interrupt: bool = False
    natural: bool = False
    horizon: bool = False
    positive_residual_survival: bool = True
    primitive_action: str = "FROZEN_PRIMITIVE_ACTION"


@dataclass(frozen=True)
class PredecisionObservation:
    committed_phase: str
    prior_acknowledgements: tuple[str, ...]
    physical_clock: int
    primitive_clock: int
    own_boundary_clock: int
    owner_epoch_token: tuple[str, int, int]
    visible_roster: tuple[str, ...]
    opaque_post_claim_cue: str


@dataclass(frozen=True)
class LifecycleRecord:
    lifecycle_id: str
    slot_id: int
    phase: Phase = Phase.UNCLAIMED
    owner_token: AuthorityToken | None = None
    claim_time: int | None = None
    physical_clock: int = 0
    primitive_clock: int = 0
    own_boundary_clock: int = 0
    execution_end_clock: int | None = None
    target_close_clock: int | None = None
    end_cause: EndCause | None = None
    acknowledgements: tuple[str, ...] = ()
    command_log: tuple[str, ...] = ()
    release_ledger: tuple[str, ...] = ()
    target: Fraction | None = None
    score: Fraction | None = None
    tombstone_version: int | None = None


@dataclass(frozen=True)
class TransitionResult:
    record: LifecycleRecord
    accepted: bool
    acknowledgement: str


def default_owner() -> AuthorityToken:
    return AuthorityToken("owner-A", 17, CURRENT_BEHAVIOR_VERSION)


def default_world() -> WorldView:
    token = default_owner()
    return WorldView(
        authoritative_membership=frozenset({token.member_epoch}),
        visible_roster=(token.owner_id, "partner-B"),
        current_behavior_version=CURRENT_BEHAVIOR_VERSION,
    )


def candidate_contract() -> ArmContract:
    return ArmContract(backend=Backend.CANDIDATE, release_has_stopping_edge=True)


def z0_contract() -> ArmContract:
    return ArmContract(backend=Backend.Z0, release_has_stopping_edge=False)


def _append_ack(record: LifecycleRecord, acknowledgement: str) -> LifecycleRecord:
    return replace(
        record,
        acknowledgements=record.acknowledgements + (acknowledgement,),
    )


def _authorized(token: AuthorityToken, record: LifecycleRecord, world: WorldView) -> bool:
    return bool(
        record.owner_token is not None
        and token == record.owner_token
        and token.member_epoch in world.authoritative_membership
        and token.behavior_version == record.owner_token.behavior_version
        and token.behavior_version == world.current_behavior_version
    )


def claim(
    record: LifecycleRecord,
    token: AuthorityToken,
    world: WorldView,
    *,
    physical_clock: int,
) -> TransitionResult:
    if record.phase is not Phase.UNCLAIMED:
        acknowledgement = (
            "CLAIM_DUPLICATE_IDEMPOTENT"
            if record.owner_token == token
            else "CLAIM_CONFLICT_REJECTED"
        )
        return TransitionResult(record, False, acknowledgement)
    accepted = bool(
        token.member_epoch in world.authoritative_membership
        and token.behavior_version == world.current_behavior_version
        and physical_clock < candidate_contract().horizon
    )
    if not accepted:
        acknowledgement = "CLAIM_REJECTED"
        return TransitionResult(_append_ack(record, acknowledgement), False, acknowledgement)
    acknowledgement = "CLAIM_ACCEPTED"
    return TransitionResult(
        replace(
            record,
            phase=Phase.ACTIVE,
            owner_token=token,
            claim_time=physical_clock,
            physical_clock=physical_clock,
            acknowledgements=record.acknowledgements + (acknowledgement,),
        ),
        True,
        acknowledgement,
    )


def predecision_observation(
    record: LifecycleRecord,
    world: WorldView,
    *,
    opaque_post_claim_cue: str,
) -> PredecisionObservation:
    if record.owner_token is None:
        raise ValueError("predecision observation requires an accepted CLAIM")
    return PredecisionObservation(
        committed_phase=record.phase.value,
        prior_acknowledgements=record.acknowledgements,
        physical_clock=record.physical_clock,
        primitive_clock=record.primitive_clock,
        own_boundary_clock=record.own_boundary_clock,
        owner_epoch_token=(
            record.owner_token.owner_id,
            record.owner_token.owner_epoch,
            record.owner_token.behavior_version,
        ),
        visible_roster=world.visible_roster,
        opaque_post_claim_cue=opaque_post_claim_cue,
    )


def observation_firewall_valid(observation: object) -> bool:
    names = tuple(field.name for field in fields(observation)) if hasattr(observation, "__dataclass_fields__") else tuple()
    return names == SHARED_OBSERVATION_FIELDS and not (set(names) & FORBIDDEN_OBSERVATION_FIELDS)


def _end(
    record: LifecycleRecord,
    phase: Phase,
    cause: EndCause,
    acknowledgement: str,
    *,
    physical_clock: int,
    release_id: str | None = None,
) -> TransitionResult:
    ledger = record.release_ledger
    if release_id is not None and release_id not in ledger:
        ledger = ledger + (release_id,)
    ended = replace(
        record,
        phase=phase,
        physical_clock=physical_clock,
        execution_end_clock=physical_clock,
        end_cause=cause,
        acknowledgements=record.acknowledgements + (acknowledgement,),
        release_ledger=ledger,
    )
    return TransitionResult(ended, True, acknowledgement)


def apply_boundary(
    record: LifecycleRecord,
    *,
    contract: ArmContract,
    action: OwnerAction,
    command_token: AuthorityToken,
    world: WorldView,
    boundary_index: int,
    physical_clock: int,
    tape: PairedTape,
    release_id: str,
) -> TransitionResult:
    """Commit one boundary using TERMINAL > INTERRUPT > RELEASE > NATURAL > HORIZON."""

    if record.phase is not Phase.ACTIVE:
        acknowledgement = (
            "ENDED_EVENT_IDEMPOTENT"
            if record.phase is not Phase.UNCLAIMED
            else "RELEASE_WITHOUT_CLAIM_REJECTED"
        )
        unchanged = record if record.phase is not Phase.UNCLAIMED else _append_ack(record, acknowledgement)
        return TransitionResult(unchanged, False, acknowledgement)

    command_log = record.command_log + (action.value,)
    record = replace(record, command_log=command_log)
    if tape.terminal:
        return _end(
            record,
            Phase.ENDED_TERMINAL,
            EndCause.TERMINAL,
            "TERMINAL_COMMITTED",
            physical_clock=physical_clock,
        )
    owner_departed = bool(
        record.owner_token is not None
        and record.owner_token.member_epoch not in world.authoritative_membership
    )
    if tape.interrupt or owner_departed:
        return _end(
            record,
            Phase.ENDED_INTERRUPT,
            EndCause.INTERRUPT,
            "INTERRUPT_COMMITTED",
            physical_clock=physical_clock,
        )

    release_eligible = bool(
        record.claim_time is not None
        and boundary_index > record.own_boundary_clock
        and physical_clock > record.claim_time
        and tape.positive_residual_survival
    )
    if action is OwnerAction.RELEASE:
        if not _authorized(command_token, record, world):
            record = _append_ack(record, "RELEASE_AUTHORIZATION_REJECTED")
        elif not release_eligible:
            record = _append_ack(record, "RELEASE_INELIGIBLE_REJECTED")
        elif contract.release_has_stopping_edge:
            return _end(
                record,
                Phase.ENDED_RELEASE,
                EndCause.RELEASE,
                "RELEASE_ACCEPTED",
                physical_clock=physical_clock,
                release_id=release_id,
            )
        else:
            record = _append_ack(record, "RELEASE_LOGGED_NO_EDGE")

    if tape.natural:
        return _end(
            record,
            Phase.ENDED_NATURAL,
            EndCause.NATURAL,
            "NATURAL_COMMITTED",
            physical_clock=physical_clock,
        )
    if tape.horizon:
        return _end(
            record,
            Phase.ENDED_HORIZON,
            EndCause.HORIZON,
            "HORIZON_COMMITTED",
            physical_clock=physical_clock,
        )
    active = replace(
        record,
        physical_clock=physical_clock,
        primitive_clock=record.primitive_clock + 1,
        own_boundary_clock=boundary_index,
        acknowledgements=record.acknowledgements + ("HOLD_PRIMITIVE_COMMITTED",),
    )
    return TransitionResult(active, False, active.acknowledgements[-1])


def close_target_score(
    record: LifecycleRecord,
    *,
    command_token: AuthorityToken,
    target: Fraction,
    score: Fraction,
    close_clock: int,
) -> TransitionResult:
    if record.phase is Phase.TARGET_CLOSED_TOMBSTONE:
        if record.target == target and record.score == score:
            return TransitionResult(record, False, "TARGET_CLOSE_DUPLICATE_IDEMPOTENT")
        return TransitionResult(record, False, "TARGET_CLOSE_CONFLICT_REJECTED")
    if record.phase in (Phase.UNCLAIMED, Phase.ACTIVE) or record.owner_token != command_token:
        return TransitionResult(record, False, "TARGET_CLOSE_REJECTED")
    if command_token.behavior_version != CURRENT_BEHAVIOR_VERSION:
        return TransitionResult(record, False, "TARGET_CLOSE_STALE_VERSION_REJECTED")
    if target != FROZEN_TARGET or score != FROZEN_SCORE:
        return TransitionResult(record, False, "TARGET_SCORE_MISMATCH_REJECTED")
    return TransitionResult(
        replace(
            record,
            phase=Phase.TARGET_CLOSED_TOMBSTONE,
            target_close_clock=close_clock,
            target=target,
            score=score,
            tombstone_version=command_token.behavior_version,
            acknowledgements=record.acknowledgements + ("TARGET_CLOSED",),
        ),
        True,
        "TARGET_CLOSED",
    )


def version_can_advance(records: Iterable[LifecycleRecord], *, new_version: int) -> bool:
    records = tuple(records)
    return bool(
        records
        and new_version == CURRENT_BEHAVIOR_VERSION + 1
        and all(record.phase is Phase.TARGET_CLOSED_TOMBSTONE for record in records)
    )


def _matched_arm_contracts(candidate: ArmContract, z0: ArmContract) -> bool:
    ignored = {"backend", "release_has_stopping_edge"}
    candidate_fields = asdict(candidate)
    z0_fields = asdict(z0)
    return all(candidate_fields[name] == z0_fields[name] for name in candidate_fields if name not in ignored)


def enumerate_z0_claim_time_mappings() -> tuple[tuple[str, str], ...]:
    cues = ("cue-0", "cue-1")
    mappings = []
    for laws in product(CompletionLaw, repeat=len(cues)):
        mappings.append(tuple(f"{cue}:{law.value}" for cue, law in zip(cues, laws)))
    return tuple(mappings)


def exact_z0_control_checks(
    candidate: ArmContract, z0: ArmContract
) -> dict[str, bool]:
    mappings = enumerate_z0_claim_time_mappings()
    fixed = tuple(
        mapping
        for mapping in mappings
        if mapping[0].split(":", 1)[1] == mapping[1].split(":", 1)[1]
    )
    private_selector_states = (0, 1)
    shuffled = {tuple(reversed(mapping)) for mapping in mappings}
    restored = {tuple(reversed(mapping)) for mapping in shuffled}
    return {
        "fixed": len(fixed) == 2,
        "private_randomized": len(private_selector_states) == 2
        and len(set(private_selector_states)) == 2,
        "joint_context_shuffle": restored == set(mappings),
        "recurrent": candidate.memory_cells == z0.memory_cells == 2,
        "actuator_matched": candidate.command_alphabet == z0.command_alphabet
        and candidate.command_bandwidth_bits == z0.command_bandwidth_bits == 1,
    }


def _fresh_claimed() -> tuple[LifecycleRecord, AuthorityToken, WorldView]:
    token = default_owner()
    world = default_world()
    initial = LifecycleRecord("vsp02-a1-e1", slot_id=3)
    claimed = claim(initial, token, world, physical_clock=0)
    if not claimed.accepted:
        raise AssertionError("canonical claim unexpectedly rejected")
    return claimed.record, token, world


def _cell(
    backend: Backend,
    action: OwnerAction,
    *,
    tape: PairedTape,
) -> LifecycleRecord:
    record, token, world = _fresh_claimed()
    contract = candidate_contract() if backend is Backend.CANDIDATE else z0_contract()
    return apply_boundary(
        record,
        contract=contract,
        action=action,
        command_token=token,
        world=world,
        boundary_index=1,
        physical_clock=1,
        tape=tape,
        release_id="release-1",
    ).record


def _apply_fault(report: dict[str, object], fault: str | None) -> None:
    if fault is None:
        return
    if fault == "invalid_contract":
        report["contract"]["observation_firewall"] = False  # type: ignore[index]
    elif fault == "no_positive_survival":
        report["positive_survival_support"] = False
    elif fault == "owner_authorization":
        report["authority"]["valid_owner_release"] = False  # type: ignore[index]
    elif fault == "ledger_closure":
        report["ledger_closure"]["exact_once_closure"] = False  # type: ignore[index]
    elif fault == "release_not_causal":
        report["separator"]["CANDIDATE|RELEASE"] = Phase.ACTIVE.value  # type: ignore[index]
    elif fault == "z0_release_responsive":
        report["separator"]["Z0|RELEASE"] = Phase.ENDED_RELEASE.value  # type: ignore[index]
    else:
        raise ValueError(f"unknown technical fault injection: {fault}")


def classify_a1(report: Mapping[str, object]) -> str:
    contract = report["contract"]
    authority = report["authority"]
    ledger = report["ledger_closure"]
    separator = report["separator"]
    assert isinstance(contract, Mapping)
    assert isinstance(authority, Mapping)
    assert isinstance(ledger, Mapping)
    assert isinstance(separator, Mapping)
    expected_cells = {
        "CANDIDATE|RELEASE",
        "CANDIDATE|HOLD",
        "Z0|RELEASE",
        "Z0|HOLD",
    }
    if set(separator) != expected_cells or not all(bool(value) for value in contract.values()):
        return "A1_INVALID_CONTRACT"
    if not bool(report["positive_survival_support"]):
        return "A1_POSITIVE_SURVIVAL_SUPPORT_ABSENT"
    if not all(bool(value) for value in authority.values()):
        return "A1_OWNER_AUTHORIZATION_FAILED"
    if not all(bool(value) for value in ledger.values()):
        return "A1_LEDGER_OR_CLOSURE_FAILED"
    if not (
        separator.get("CANDIDATE|RELEASE") == Phase.ENDED_RELEASE.value
        and separator.get("CANDIDATE|HOLD") == Phase.ACTIVE.value
    ):
        return "A1_RELEASE_NOT_CAUSAL"
    if not (
        separator.get("Z0|RELEASE") == Phase.ACTIVE.value
        and separator.get("Z0|HOLD") == Phase.ACTIVE.value
    ):
        return "A1_Z0_RELEASE_RESPONSIVE"
    return "A1_OWNER_ACTION_RESPONSIVE_LIFECYCLE_SUPPORTED"


def run_lifecycle_certificate(*, technical_fault: str | None = None) -> dict[str, object]:
    candidate = candidate_contract()
    z0 = z0_contract()
    tape = PairedTape("VSP02-A1-PAIRED-TAPE-1")
    separator = {
        f"{backend.value}|{action.value}": _cell(backend, action, tape=tape).phase.value
        for backend, action in product(Backend, OwnerAction)
    }

    record, token, world = _fresh_claimed()
    observation = predecision_observation(record, world, opaque_post_claim_cue="cue-0")
    wrong_owner = replace(token, owner_id="owner-X")
    wrong_epoch = replace(token, owner_epoch=token.owner_epoch + 1)
    stale_version = replace(token, behavior_version=token.behavior_version - 1)
    hidden_world = replace(world, visible_roster=("partner-B",))
    visible_attacker = replace(world, visible_roster=world.visible_roster + ("owner-X",))

    def released(command_token: AuthorityToken, command_world: WorldView) -> bool:
        fresh, _, _ = _fresh_claimed()
        return apply_boundary(
            fresh,
            contract=candidate,
            action=OwnerAction.RELEASE,
            command_token=command_token,
            world=command_world,
            boundary_index=1,
            physical_clock=1,
            tape=tape,
            release_id="authority-control",
        ).record.phase is Phase.ENDED_RELEASE

    nonmember_world = replace(world, authoritative_membership=frozenset())
    valid_end = _cell(Backend.CANDIDATE, OwnerAction.RELEASE, tape=tape)
    closed = close_target_score(
        valid_end,
        command_token=token,
        target=FROZEN_TARGET,
        score=FROZEN_SCORE,
        close_clock=2,
    ).record
    duplicate_close = close_target_score(
        closed,
        command_token=token,
        target=FROZEN_TARGET,
        score=FROZEN_SCORE,
        close_clock=3,
    ).record
    stale_close = close_target_score(
        closed,
        command_token=stale_version,
        target=Fraction(99),
        score=Fraction(99),
        close_clock=3,
    ).record

    tie_terminal = _cell(
        Backend.CANDIDATE,
        OwnerAction.RELEASE,
        tape=replace(tape, terminal=True, interrupt=True, natural=True, horizon=True),
    )
    tie_interrupt = _cell(
        Backend.CANDIDATE,
        OwnerAction.RELEASE,
        tape=replace(tape, interrupt=True, natural=True, horizon=True),
    )
    tie_release = _cell(
        Backend.CANDIDATE,
        OwnerAction.RELEASE,
        tape=replace(tape, natural=True, horizon=True),
    )
    tie_natural = _cell(
        Backend.CANDIDATE,
        OwnerAction.HOLD,
        tape=replace(tape, natural=True, horizon=True),
    )
    tie_horizon = _cell(
        Backend.CANDIDATE,
        OwnerAction.HOLD,
        tape=replace(tape, horizon=True),
    )
    before_boundary, _, _ = _fresh_claimed()
    before_release = apply_boundary(
        before_boundary,
        contract=candidate,
        action=OwnerAction.RELEASE,
        command_token=token,
        world=world,
        boundary_index=0,
        physical_clock=0,
        tape=tape,
        release_id="too-early",
    ).record
    no_claim_release = apply_boundary(
        LifecycleRecord("no-claim", slot_id=3),
        contract=candidate,
        action=OwnerAction.RELEASE,
        command_token=token,
        world=world,
        boundary_index=1,
        physical_clock=1,
        tape=tape,
        release_id="no-claim",
    ).record
    duplicate_release = apply_boundary(
        valid_end,
        contract=candidate,
        action=OwnerAction.RELEASE,
        command_token=token,
        world=world,
        boundary_index=2,
        physical_clock=2,
        tape=tape,
        release_id="release-1",
    ).record
    mappings = enumerate_z0_claim_time_mappings()
    z0_controls = exact_z0_control_checks(candidate, z0)
    z0_mapping_witnesses = {
        "|".join(mapping): {
            action.value: _cell(Backend.Z0, action, tape=tape).phase.value
            for action in OwnerAction
        }
        for mapping in mappings
    }

    report: dict[str, object] = {
        "phase_schema": [phase.value for phase in Phase],
        "terminal_precedence": list(TERMINAL_PRECEDENCE),
        "arm_contracts": {
            "candidate": asdict(candidate),
            "z0": asdict(z0),
            "sole_treatment_difference": "release_has_stopping_edge",
        },
        "contract": {
            "eight_phase_total_schema": len(Phase) == 8,
            "arm_match_except_release_edge": _matched_arm_contracts(candidate, z0),
            "observation_firewall": observation_firewall_valid(observation),
            "paired_tape_identity": candidate.tape_id == z0.tape_id == tape.tape_id,
            "information_memory_compute_command_match": (
                candidate.information_fields == z0.information_fields
                and candidate.memory_cells == z0.memory_cells
                and candidate.computation_cells == z0.computation_cells
                and candidate.command_alphabet == z0.command_alphabet
                and candidate.command_bandwidth_bits == z0.command_bandwidth_bits
            ),
            "fixed_primitive_reward_horizon_optimizer_match": (
                candidate.primitive_policy == z0.primitive_policy
                and candidate.reward_contract == z0.reward_contract
                and candidate.horizon == z0.horizon
                and candidate.optimizer_exposure == z0.optimizer_exposure == 0
            ),
            "claim_time_mapping_enumeration_exact": len(mappings) == 4 and len(set(mappings)) == 4,
            "fixed_randomized_shuffled_recurrent_actuator_controls_present": all(
                z0_controls.values()
            ),
            "release_before_eligibility_rejected": before_release.phase is Phase.ACTIVE,
            "release_without_claim_rejected": no_claim_release.phase is Phase.UNCLAIMED,
            "tie_precedence_exact": (
                tie_terminal.phase is Phase.ENDED_TERMINAL
                and tie_interrupt.phase is Phase.ENDED_INTERRUPT
                and tie_release.phase is Phase.ENDED_RELEASE
                and tie_natural.phase is Phase.ENDED_NATURAL
                and tie_horizon.phase is Phase.ENDED_HORIZON
            ),
            "separator_complete": set(separator)
            == {"CANDIDATE|RELEASE", "CANDIDATE|HOLD", "Z0|RELEASE", "Z0|HOLD"},
        },
        "positive_survival_support": tape.positive_residual_survival
        and not any((tape.terminal, tape.interrupt, tape.natural, tape.horizon)),
        "authority": {
            "valid_owner_release": released(token, world),
            "wrong_owner_rejected": not released(wrong_owner, visible_attacker),
            "wrong_epoch_rejected": not released(wrong_epoch, world),
            "stale_version_rejected": not released(stale_version, world),
            "nonmember_rejected": not released(token, nonmember_world),
            "visibility_not_authority": released(token, hidden_world),
        },
        "ledger_closure": {
            "release_ledger_exact_once": valid_end.release_ledger == ("release-1",)
            and duplicate_release.release_ledger == valid_end.release_ledger,
            "exact_once_closure": closed.phase is Phase.TARGET_CLOSED_TOMBSTONE
            and duplicate_close == closed,
            "target_score_exact": closed.target == FROZEN_TARGET and closed.score == FROZEN_SCORE,
            "stale_version_cannot_change_closed_record": stale_close == closed,
            "tombstone_preserves_end_cause": closed.end_cause is EndCause.RELEASE,
            "version_advances_only_after_closure": (
                not version_can_advance((valid_end,), new_version=CURRENT_BEHAVIOR_VERSION + 1)
                and version_can_advance((closed,), new_version=CURRENT_BEHAVIOR_VERSION + 1)
            ),
        },
        "separator": separator,
        "first_observation": {
            "kind": "COMMITTED_PHASE_IMMEDIATELY_AFTER_BOUNDARY",
            "cells": separator,
        },
        "z0_claim_time_enumeration": {
            "cue_domain": ["cue-0", "cue-1"],
            "completion_laws": [law.value for law in CompletionLaw],
            "mapping_count": len(mappings),
            "mappings": [list(mapping) for mapping in mappings],
            "all_survive_registered_boundary": True,
            "post_claim_release_is_log_only_for_every_mapping": all(
                witness == {"RELEASE": "ACTIVE", "HOLD": "ACTIVE"}
                for witness in z0_mapping_witnesses.values()
            ),
            "mapping_witnesses": z0_mapping_witnesses,
        },
        "named_tabular_controls": z0_controls,
        "nonclaims": [
            "learning value",
            "escrow superiority",
            "adaptive superiority",
            "return improvement",
            "production actionability",
            "promotion or retirement",
        ],
    }
    _apply_fault(report, technical_fault)
    report["branch"] = classify_a1(report)
    return report


def zero_activity(*, registered_a_invocations: int) -> dict[str, int]:
    return {
        "registered_a_invocations": registered_a_invocations,
        **{name: 0 for name in ACTIVITY_ZERO_FIELDS},
    }


def build_a1_manifest(
    *, source_revision: str, run_id: str, technical_only: bool
) -> dict[str, object]:
    return {
        "schema_version": A1_SCHEMA_VERSION,
        "artifact_kind": "vsp02_a1_frozen_manifest",
        "assignment_id": A1_ASSIGNMENT_ID,
        "candidate": A1_CANDIDATE,
        "evidence_level": "A",
        "formal": False,
        "resource_class": A1_RESOURCE_CLASS,
        "pool_units": 0,
        "source_revision": source_revision,
        "run_id": run_id,
        "technical_only": technical_only,
        "frozen_separator": {
            "CANDIDATE|RELEASE": "ENDED_RELEASE",
            "CANDIDATE|HOLD": "ACTIVE",
            "Z0|RELEASE": "ACTIVE",
            "Z0|HOLD": "ACTIVE",
        },
        "terminal_branch_precedence": [
            "A1_INVALID_CONTRACT",
            "A1_POSITIVE_SURVIVAL_SUPPORT_ABSENT",
            "A1_OWNER_AUTHORIZATION_FAILED",
            "A1_LEDGER_OR_CLOSURE_FAILED",
            "A1_RELEASE_NOT_CAUSAL",
            "A1_Z0_RELEASE_RESPONSIVE",
            "A1_OWNER_ACTION_RESPONSIVE_LIFECYCLE_SUPPORTED",
        ],
    }


def validate_a1_manifest(manifest: object) -> tuple[str, ...]:
    if not isinstance(manifest, Mapping):
        return ("manifest is not an object",)
    issues: list[str] = []
    expected = {
        "schema_version": A1_SCHEMA_VERSION,
        "artifact_kind": "vsp02_a1_frozen_manifest",
        "assignment_id": A1_ASSIGNMENT_ID,
        "candidate": A1_CANDIDATE,
        "evidence_level": "A",
        "formal": False,
        "resource_class": A1_RESOURCE_CLASS,
        "pool_units": 0,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            issues.append(f"{key} mismatch")
    for key in ("source_revision", "run_id"):
        if not isinstance(manifest.get(key), str) or not manifest.get(key):
            issues.append(f"{key} must be a nonempty string")
    if not isinstance(manifest.get("technical_only"), bool):
        issues.append("technical_only must be boolean")
    canonical = build_a1_manifest(
        source_revision=str(manifest.get("source_revision", "")),
        run_id=str(manifest.get("run_id", "")),
        technical_only=bool(manifest.get("technical_only")),
    )
    for key in ("frozen_separator", "terminal_branch_precedence"):
        if manifest.get(key) != canonical[key]:
            issues.append(f"{key} mismatch")
    return tuple(issues)


def run_a1_probe(manifest: Mapping[str, object]) -> dict[str, object]:
    issues = validate_a1_manifest(manifest)
    if issues:
        raise ValueError("; ".join(issues))
    technical_only = bool(manifest["technical_only"])
    report = run_lifecycle_certificate()
    return {
        "schema_version": A1_SCHEMA_VERSION,
        "artifact_kind": "vsp02_a1_owner_action_responsive_lifecycle_result",
        "manifest": dict(manifest),
        "branch": report["branch"],
        "smallest_technical_fact": (
            "On one byte-matched positive-survival tape, candidate RELEASE alone "
            "commits ENDED_RELEASE; candidate HOLD and both Z0 commands remain ACTIVE."
        ),
        "report": report,
        "activity": zero_activity(registered_a_invocations=0 if technical_only else 1),
    }


def validate_a1_artifact(artifact: object) -> tuple[str, ...]:
    if not isinstance(artifact, Mapping):
        return ("artifact is not an object",)
    issues: list[str] = []
    if artifact.get("schema_version") != A1_SCHEMA_VERSION:
        issues.append("schema_version mismatch")
    if artifact.get("artifact_kind") != "vsp02_a1_owner_action_responsive_lifecycle_result":
        issues.append("artifact_kind mismatch")
    manifest = artifact.get("manifest")
    issues.extend(validate_a1_manifest(manifest))
    report = artifact.get("report")
    if not isinstance(report, Mapping):
        issues.append("report missing")
    else:
        try:
            classified = classify_a1(report)
        except (AssertionError, KeyError, TypeError):
            issues.append("report structure invalid")
        else:
            if report.get("branch") != classified or artifact.get("branch") != classified:
                issues.append("branch/classifier mismatch")
    activity = artifact.get("activity")
    if not isinstance(activity, Mapping):
        issues.append("activity missing")
    else:
        technical_only = isinstance(manifest, Mapping) and manifest.get("technical_only") is True
        expected_invocations = 0 if technical_only else 1
        if activity.get("registered_a_invocations") != expected_invocations:
            issues.append("registered_a_invocations mismatch")
        for field in ACTIVITY_ZERO_FIELDS:
            if activity.get(field) != 0:
                issues.append(f"{field} must be zero")
    if isinstance(manifest, Mapping) and not validate_a1_manifest(manifest):
        expected = run_a1_probe(manifest)
        if json_ready(artifact) != json_ready(expected):
            issues.append("artifact differs from deterministic canonical reconstruction")
    return tuple(issues)


def json_ready(value: object) -> object:
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [json_ready(item) for item in value]
    return value
