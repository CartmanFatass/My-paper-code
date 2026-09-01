"""Typed dynamic host and literal token law for CBSC-OMRC-B01.

The host generates exogenous, action-independent episode tapes.  Native
actions are interpreted only through the evaluator ledger, so choosing SERVE,
REFRESH, or SAFE_FALLBACK can never alter a later public token or host state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Sequence

from .addressing import (
    EVAL_MOTIF,
    EVAL_STOCHASTIC,
    OPPORTUNITY_DRAW_LABELS,
    RUN_NAMES,
    SPLITS,
    TRAIN,
    AuditedCounterPRF,
    env_address,
)
from .contract import (
    AccessMode,
    Action,
    BodySlot,
    Carrier,
    EventKind,
    OPPORTUNITY_COUNT,
    PayloadRole,
    Receiver,
)
from .ledger import NativeLedger, evaluator_oracle_action, evaluator_valid, native_ledger
from .state import (
    CarrierState,
    DecisionPrimitive,
    HostState,
    ReceiverState,
    make_decision,
    transition_body,
    transition_capability,
    transition_owner,
    transition_semantic,
)
from .tapes import (
    EpisodeTape,
    MotifDescriptor,
    TapeGenerationAudit,
    TapeIdentity,
    motif_descriptor,
)
from .token import (
    ABSENT_BYTE,
    NEUTRAL_PAYLOAD_SOURCE,
    LITERAL_TOKEN_CODEC,
    LearnerProjection,
    PrimitiveToken,
)


class HostValidationError(ValueError):
    """Raised when a token or generated episode violates the bound host law."""


class EventFamily(str, Enum):
    OWNER = "OWNER"
    SEMANTIC = "SEMANTIC"
    CAPABILITY = "CAPABILITY"
    BODY = "BODY"


NOOP_CODE = {
    EventFamily.OWNER: EventKind.NOOP_OWNER,
    EventFamily.SEMANTIC: EventKind.NOOP_SEMANTIC,
    EventFamily.CAPABILITY: EventKind.NOOP_CAPABILITY,
    EventFamily.BODY: EventKind.NOOP_BODY,
}


@dataclass(frozen=True)
class DecisionTruth:
    """Evaluator-only pre-action state and decision semantics."""

    state: HostState
    decision: DecisionPrimitive
    preaction_codes: tuple[EventKind, EventKind, EventKind, EventKind]
    motif_family: int | None = None
    motif_side: str | None = None
    designated_comparison: bool = False

    @property
    def valid(self) -> bool:
        return evaluator_valid(self.state, self.decision)

    @property
    def oracle_action(self) -> Action:
        return evaluator_oracle_action(self.state, self.decision)

    def ledger(self, action: Action) -> NativeLedger:
        return native_ledger(self.state, self.decision, action)


@dataclass(frozen=True)
class _StochasticPotential:
    order: tuple[EventFamily, EventFamily, EventFamily, EventFamily]
    owner_occurs: bool
    owner_subject: Receiver
    semantic_occurs: bool
    semantic_subject: Receiver
    semantic_new_need: bool
    capability_occurs: bool
    capability_carrier: Carrier
    capability_receiver: Receiver
    body_occurs: bool
    body_slot: BodySlot
    body_address: Receiver
    body_carrier: Carrier
    body_role: PayloadRole
    decision_slot: BodySlot
    target_matches: bool
    access_mode: AccessMode
    request_active: bool


@dataclass
class _Pools:
    owner: tuple[int, ...]
    epoch: tuple[int, ...]
    owner_cursor: int = 2
    epoch_cursor: int = 2

    def next_owner(self) -> int:
        if self.owner_cursor >= len(self.owner):
            raise HostValidationError("OWNER opaque-token pool exhausted")
        value = self.owner[self.owner_cursor]
        self.owner_cursor += 1
        return value

    def next_epoch(self) -> int:
        if self.epoch_cursor >= len(self.epoch):
            raise HostValidationError("epoch opaque-token pool exhausted")
        value = self.epoch[self.epoch_cursor]
        self.epoch_cursor += 1
        return value


@dataclass(frozen=True)
class _Directive:
    family: EventFamily
    operation: str
    args: tuple[object, ...] = ()


def _binary(value: Fraction, enum_type: type[Receiver] | type[Carrier] | type[BodySlot]):
    return enum_type(0 if value < Fraction(1, 2) else 1)


def _role(value: Fraction) -> PayloadRole:
    if value < Fraction(1, 2):
        return PayloadRole.CORRECT
    if value < Fraction(3, 4):
        return PayloadRole.SWAPPED
    return PayloadRole.NEUTRAL


def _other(receiver: Receiver) -> Receiver:
    return Receiver.R1 if receiver is Receiver.R0 else Receiver.R0


class DynamicHost:
    """Build stochastic and fixed-motif tapes for one run/seed identity."""

    def __init__(self, run_name: str, seed: int) -> None:
        if run_name not in RUN_NAMES:
            raise HostValidationError("run_name is not a frozen B0/B1/B2 identity")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise HostValidationError("seed must be int")
        self.run_name = run_name
        self.seed = seed

    def _address(
        self,
        split: str,
        episode_id: int,
        opportunity_id: int,
        family: str,
        label: str,
        draw_index: int = 0,
        retry: int = 0,
    ):
        return env_address(
            self.run_name,
            self.seed,
            split,
            episode_id,
            opportunity_id,
            family,
            label,
            draw_index,
            retry,
        )

    def _u(
        self,
        prf: AuditedCounterPRF,
        split: str,
        episode_id: int,
        opportunity_id: int,
        family: str,
        label: str,
    ) -> Fraction:
        return prf.u(
            self._address(split, episode_id, opportunity_id, family, label, 0, 0)
        )

    def _permutation(
        self,
        prf: AuditedCounterPRF,
        values: Sequence,
        split: str,
        episode_id: int,
        opportunity_id: int,
        family: str,
        label: str,
    ) -> tuple:
        return prf.permutation(
            values,
            lambda position, retry: self._address(
                split,
                episode_id,
                opportunity_id,
                family,
                label,
                position,
                retry,
            ),
        )

    def _initial_state(
        self, prf: AuditedCounterPRF, split: str, episode_id: int
    ) -> tuple[HostState, _Pools, list[PrimitiveToken]]:
        owner_pool = self._permutation(
            prf, tuple(range(16, 64)), split, episode_id, -1, "OWNER", "OWNER_PERM"
        )
        epoch_pool = self._permutation(
            prf, tuple(range(16, 64)), split, episode_id, -1, "SEMANTIC", "EPOCH_PERM"
        )
        needs = tuple(
            self._u(prf, split, episode_id, -1, "SEMANTIC", f"NEED_{r}")
            < Fraction(1, 2)
            for r in range(2)
        )
        capabilities = tuple(
            _binary(
                self._u(prf, split, episode_id, -1, "CAPABILITY", f"CAPABILITY_{c}"),
                Receiver,
            )
            for c in range(2)
        )
        state = HostState(
            receivers=(
                ReceiverState(owner_pool[0], epoch_pool[0], needs[0]),
                ReceiverState(owner_pool[1], epoch_pool[1], needs[1]),
            ),
            bodies=(None, None),
            carriers=(CarrierState(capabilities[0]), CarrierState(capabilities[1])),
        )
        tokens = [
            PrimitiveToken(
                event_kind=EventKind.INIT_OWNER,
                subject_receiver=0,
                owner_new=owner_pool[0],
                event_order_position=0,
            ),
            PrimitiveToken(
                event_kind=EventKind.INIT_OWNER,
                subject_receiver=1,
                owner_new=owner_pool[1],
                event_order_position=1,
            ),
            PrimitiveToken(
                event_kind=EventKind.INIT_SEMANTIC,
                subject_receiver=0,
                epoch_new=epoch_pool[0],
                event_order_position=2,
                new_need=needs[0],
            ),
            PrimitiveToken(
                event_kind=EventKind.INIT_SEMANTIC,
                subject_receiver=1,
                epoch_new=epoch_pool[1],
                event_order_position=3,
                new_need=needs[1],
            ),
            PrimitiveToken(
                event_kind=EventKind.INIT_CAPABILITY,
                carrier=0,
                capability_receiver=capabilities[0],
                event_order_position=4,
            ),
            PrimitiveToken(
                event_kind=EventKind.INIT_CAPABILITY,
                carrier=1,
                capability_receiver=capabilities[1],
                event_order_position=5,
            ),
        ]
        for slot_index in range(2):
            address = _binary(
                self._u(
                    prf, split, episode_id, -1, "BODY", f"BODY_{slot_index}_ADDRESS"
                ),
                Receiver,
            )
            carrier = _binary(
                self._u(
                    prf, split, episode_id, -1, "BODY", f"BODY_{slot_index}_CARRIER"
                ),
                Carrier,
            )
            role = _role(
                self._u(prf, split, episode_id, -1, "BODY", f"BODY_{slot_index}_ROLE")
            )
            state, _ = transition_body(state, BodySlot(slot_index), address, carrier, role)
            tokens.append(self._body_token(state, BodySlot(slot_index), True, -1, 6 + slot_index))
        return state, _Pools(owner_pool, epoch_pool), tokens

    @staticmethod
    def _body_token(
        state: HostState,
        slot: BodySlot,
        initial: bool,
        opportunity: int,
        position: int,
    ) -> PrimitiveToken:
        body = state.body(slot)
        return PrimitiveToken(
            event_kind=EventKind.INIT_BODY if initial else EventKind.BODY,
            slot=slot,
            carrier=body.carrier,
            body_owner=body.issuance_owner,
            body_epoch=body.issuance_epoch,
            body_addressed_receiver=body.addressed_receiver,
            payload_source_receiver=(
                NEUTRAL_PAYLOAD_SOURCE
                if body.payload_source_receiver is None
                else int(body.payload_source_receiver)
            ),
            opportunity_index=ABSENT_BYTE if initial else opportunity,
            event_order_position=position,
            body_content=body.content,
            body_native_neutral=body.native_neutral,
        )

    def _potential(
        self,
        prf: AuditedCounterPRF,
        split: str,
        episode_id: int,
        opportunity: int,
    ) -> _StochasticPotential:
        order = self._permutation(
            prf,
            tuple(EventFamily),
            split,
            episode_id,
            opportunity,
            "EVENT_ORDER",
            "EVENT_PERM",
        )

        def u(family: str, label: str) -> Fraction:
            return self._u(prf, split, episode_id, opportunity, family, label)

        potential = _StochasticPotential(
            order=order,
            owner_occurs=u("OWNER", "OWNER_OCCURS") < Fraction(1, 5),
            owner_subject=_binary(u("OWNER", "OWNER_SUBJECT"), Receiver),
            semantic_occurs=u("SEMANTIC", "SEMANTIC_OCCURS") < Fraction(1, 5),
            semantic_subject=_binary(u("SEMANTIC", "SEMANTIC_SUBJECT"), Receiver),
            semantic_new_need=u("SEMANTIC", "SEMANTIC_NEW_NEED") < Fraction(1, 2),
            capability_occurs=u("CAPABILITY", "CAPABILITY_OCCURS") < Fraction(1, 4),
            capability_carrier=_binary(u("CAPABILITY", "CAPABILITY_CARRIER"), Carrier),
            capability_receiver=_binary(
                u("CAPABILITY", "CAPABILITY_RECEIVER"), Receiver
            ),
            body_occurs=u("BODY", "BODY_OCCURS") < Fraction(1, 2),
            body_slot=_binary(u("BODY", "BODY_SLOT"), BodySlot),
            body_address=_binary(u("BODY", "BODY_ADDRESS"), Receiver),
            body_carrier=_binary(u("BODY", "BODY_CARRIER"), Carrier),
            body_role=_role(u("BODY", "BODY_ROLE")),
            decision_slot=_binary(u("DECISION", "DECISION_SLOT"), BodySlot),
            target_matches=u("DECISION", "DECISION_TARGET_MATCH") < Fraction(13, 20),
            access_mode=(
                AccessMode.GATED
                if u("DECISION", "DECISION_GATED") < Fraction(1, 2)
                else AccessMode.OPEN
            ),
            request_active=u("DECISION", "DECISION_ACTIVE") < Fraction(17, 20),
        )
        # This guards accidental omission even when an event is unrealized.
        labels = {
            record.address[-3]
            for record in prf.records
            if record.address[6] == opportunity
        }
        if not set(OPPORTUNITY_DRAW_LABELS) <= labels:
            raise AssertionError("a fixed potential draw label was omitted")
        return potential

    @staticmethod
    def _noop(family: EventFamily, opportunity: int, position: int) -> PrimitiveToken:
        return PrimitiveToken(
            event_kind=NOOP_CODE[family],
            opportunity_index=opportunity,
            event_order_position=position,
        )

    def _apply_directive(
        self,
        state: HostState,
        pools: _Pools,
        opportunity: int,
        position: int,
        directive: _Directive,
    ) -> tuple[HostState, PrimitiveToken]:
        family = directive.family
        if directive.operation == "noop":
            return state, self._noop(family, opportunity, position)
        if directive.operation == "owner":
            receiver = directive.args[0]
            state, event = transition_owner(state, receiver, pools.next_owner())
            return state, PrimitiveToken(
                event_kind=EventKind.OWNER,
                subject_receiver=receiver,
                owner_old=event.old_owner,
                owner_new=event.new_owner,
                opportunity_index=opportunity,
                event_order_position=position,
            )
        if directive.operation == "semantic":
            receiver = directive.args[0]
            new_need = (
                not state.receiver(receiver).current_need
                if len(directive.args) == 1
                else directive.args[1]
            )
            state, event = transition_semantic(
                state, receiver, pools.next_epoch(), bool(new_need)
            )
            return state, PrimitiveToken(
                event_kind=EventKind.SEMANTIC,
                subject_receiver=receiver,
                epoch_old=event.old_epoch,
                epoch_new=event.new_epoch,
                opportunity_index=opportunity,
                event_order_position=position,
                old_need=event.old_need,
                new_need=event.new_need,
            )
        if directive.operation == "capability":
            carrier, receiver = directive.args
            state, event = transition_capability(state, carrier, receiver)
            return state, PrimitiveToken(
                event_kind=EventKind.CAPABILITY,
                carrier=event.carrier,
                capability_receiver=event.permitted_receiver,
                opportunity_index=opportunity,
                event_order_position=position,
            )
        if directive.operation == "body":
            slot, carrier, receiver, role = directive.args
            state, _ = transition_body(state, slot, receiver, carrier, role)
            return state, self._body_token(state, slot, False, opportunity, position)
        raise HostValidationError(f"unknown scripted operation {directive.operation!r}")

    def _decision_token(self, state: HostState, decision: DecisionPrimitive) -> PrimitiveToken:
        body = state.body(decision.presented_slot)
        return PrimitiveToken(
            event_kind=EventKind.DECISION,
            target_receiver=decision.target_receiver,
            slot=decision.presented_slot,
            carrier=body.carrier,
            body_owner=body.issuance_owner,
            body_epoch=body.issuance_epoch,
            body_addressed_receiver=body.addressed_receiver,
            payload_source_receiver=(
                NEUTRAL_PAYLOAD_SOURCE
                if body.payload_source_receiver is None
                else int(body.payload_source_receiver)
            ),
            capability_receiver=state.carrier(body.carrier).permitted_receiver,
            opportunity_index=decision.opportunity_index,
            event_order_position=4,
            body_content=body.content,
            body_native_neutral=body.native_neutral,
            access_gated=decision.access_mode is AccessMode.GATED,
            request_active=decision.request_active,
            request_need=decision.request_need,
        )

    @staticmethod
    def _settlement(opportunity: int) -> PrimitiveToken:
        return PrimitiveToken(
            event_kind=EventKind.SETTLEMENT,
            opportunity_index=opportunity,
            event_order_position=5,
        )

    def _finish(
        self,
        split: str,
        episode_id: int,
        tokens: list[PrimitiveToken],
        truth: list[DecisionTruth],
        pools: _Pools,
        prf: AuditedCounterPRF,
        motif: MotifDescriptor | None = None,
    ) -> EpisodeTape:
        packed = tuple(LITERAL_TOKEN_CODEC.pack(token) for token in tokens)
        audit = TapeGenerationAudit(
            owner_tokens_consumed=pools.owner_cursor,
            epoch_tokens_consumed=pools.epoch_cursor,
            draw_count=len(prf.addresses),
            draw_digest=prf.audit_digest(),
            draw_addresses=prf.addresses,
        )
        return EpisodeTape(
            TapeIdentity(self.run_name, self.seed, split, episode_id),
            tuple(tokens),
            packed,
            tuple(truth),
            audit,
            motif,
        )

    def build_stochastic(self, split: str, episode_id: int) -> EpisodeTape:
        if split not in {TRAIN, EVAL_STOCHASTIC}:
            raise HostValidationError("stochastic tapes require TRAIN or EVAL_STOCHASTIC")
        if split not in SPLITS:
            raise HostValidationError("unknown split")
        prf = AuditedCounterPRF()
        state, pools, tokens = self._initial_state(prf, split, episode_id)
        truth: list[DecisionTruth] = []
        for opportunity in range(OPPORTUNITY_COUNT):
            potential = self._potential(prf, split, episode_id, opportunity)
            preaction_codes: list[EventKind] = []
            for position, family in enumerate(potential.order):
                if family is EventFamily.OWNER and potential.owner_occurs:
                    directive = _Directive(family, "owner", (potential.owner_subject,))
                elif family is EventFamily.SEMANTIC and potential.semantic_occurs:
                    directive = _Directive(
                        family,
                        "semantic",
                        (potential.semantic_subject, potential.semantic_new_need),
                    )
                elif family is EventFamily.CAPABILITY and potential.capability_occurs:
                    directive = _Directive(
                        family,
                        "capability",
                        (potential.capability_carrier, potential.capability_receiver),
                    )
                elif family is EventFamily.BODY and potential.body_occurs:
                    directive = _Directive(
                        family,
                        "body",
                        (
                            potential.body_slot,
                            potential.body_carrier,
                            potential.body_address,
                            potential.body_role,
                        ),
                    )
                else:
                    directive = _Directive(family, "noop")
                state, token = self._apply_directive(
                    state, pools, opportunity, position, directive
                )
                tokens.append(token)
                preaction_codes.append(EventKind(token.event_kind))
            body = state.body(potential.decision_slot)
            target = body.addressed_receiver if potential.target_matches else _other(body.addressed_receiver)
            decision = make_decision(
                state,
                opportunity_index=opportunity,
                presented_slot=potential.decision_slot,
                target_receiver=target,
                access_mode=potential.access_mode,
                request_active=potential.request_active,
            )
            tokens.extend((self._decision_token(state, decision), self._settlement(opportunity)))
            truth.append(DecisionTruth(state, decision, tuple(preaction_codes)))
        return self._finish(split, episode_id, tokens, truth, pools, prf)

    @staticmethod
    def _d(family: EventFamily, operation: str, *args: object) -> _Directive:
        return _Directive(family, operation, args)

    def _motif_plan(
        self, family: int, receiver: Receiver, slot: BodySlot, opportunity: int
    ) -> tuple[tuple[_Directive, ...], AccessMode, bool, str, bool]:
        owner = EventFamily.OWNER
        semantic = EventFamily.SEMANTIC
        capability = EventFamily.CAPABILITY
        body = EventFamily.BODY
        noop_o = self._d(owner, "noop")
        noop_s = self._d(semantic, "noop")
        noop_c = self._d(capability, "noop")
        noop_b = self._d(body, "noop")
        side_b = bool(opportunity % 2)
        q = opportunity // 2
        carrier = Carrier(q % 2)
        cap_ok = self._d(capability, "capability", carrier, receiver)
        body_correct = self._d(body, "body", slot, carrier, receiver, PayloadRole.CORRECT)

        if family == 0:
            owner_event = self._d(owner, "owner", receiver) if side_b else noop_o
            plan = (body_correct, owner_event, cap_ok, noop_s)
        elif family == 1:
            semantic_event = self._d(semantic, "semantic", receiver) if side_b else noop_s
            plan = (body_correct, semantic_event, cap_ok, noop_o)
        elif family == 2:
            mismatch = self._d(capability, "capability", carrier, _other(receiver))
            plan = (noop_o, noop_s, mismatch, body_correct)
        elif family == 3:
            role = PayloadRole.SWAPPED if side_b else PayloadRole.CORRECT
            role_body = self._d(body, "body", slot, carrier, receiver, role)
            plan = (noop_o, noop_s, cap_ok, role_body)
        elif family == 4:
            plan = (noop_o, noop_s, cap_ok, body_correct)
        elif family == 5:
            owner_event = self._d(owner, "owner", receiver)
            plan = (
                (owner_event, body_correct, cap_ok, noop_s)
                if not side_b
                else (body_correct, owner_event, cap_ok, noop_s)
            )
        elif family == 6:
            semantic_event = self._d(semantic, "semantic", receiver)
            plan = (
                (semantic_event, body_correct, cap_ok, noop_o)
                if not side_b
                else (body_correct, semantic_event, cap_ok, noop_o)
            )
        elif family == 7:
            offset = opportunity % 8
            block = opportunity // 8
            carrier = Carrier(block % 2)
            if offset == 0:
                plan = (
                    noop_o,
                    noop_s,
                    self._d(capability, "capability", carrier, receiver),
                    self._d(body, "body", slot, carrier, receiver, PayloadRole.CORRECT),
                )
                return plan, AccessMode.GATED, False, "SETUP", False
            active = offset in {1, 6}
            side = "GAP1" if offset == 1 else "GAP6" if offset == 6 else "FILLER"
            return (noop_o, noop_s, noop_c, noop_b), AccessMode.GATED, active, side, active
        else:  # pragma: no cover - descriptor validation makes this unreachable.
            raise HostValidationError("unknown motif family")

        mode = AccessMode.OPEN if family == 2 and not side_b else AccessMode.GATED
        active = not (family == 4 and side_b)
        return plan, mode, active, "B" if side_b else "A", True

    def build_motif(self, tape_id: int) -> EpisodeTape:
        descriptor = motif_descriptor(tape_id)
        receiver = Receiver(descriptor.target_receiver)
        slot = BodySlot(descriptor.presented_slot)
        prf = AuditedCounterPRF()
        state, pools, tokens = self._initial_state(prf, EVAL_MOTIF, tape_id)
        truth: list[DecisionTruth] = []
        for opportunity in range(OPPORTUNITY_COUNT):
            plan, mode, active, side, designated = self._motif_plan(
                descriptor.family, receiver, slot, opportunity
            )
            codes: list[EventKind] = []
            for position, directive in enumerate(plan):
                state, token = self._apply_directive(
                    state, pools, opportunity, position, directive
                )
                tokens.append(token)
                codes.append(EventKind(token.event_kind))
            decision = make_decision(
                state,
                opportunity_index=opportunity,
                presented_slot=slot,
                target_receiver=receiver,
                access_mode=mode,
                request_active=active,
            )
            tokens.extend((self._decision_token(state, decision), self._settlement(opportunity)))
            truth.append(
                DecisionTruth(
                    state,
                    decision,
                    tuple(codes),
                    motif_family=descriptor.family,
                    motif_side=side,
                    designated_comparison=designated,
                )
            )
        return self._finish(
            EVAL_MOTIF, tape_id, tokens, truth, pools, prf, descriptor
        )
