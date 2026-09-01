"""Evaluator-only validity and exact native decision/settlement ledger."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .contract import AccessMode, Action, ContractValidationError
from .state import DecisionPrimitive, HostState


ZERO = Fraction(0)
SERVE_VALID_REWARD = Fraction(1)
SERVE_INVALID_REWARD = Fraction(-3, 10)
SERVE_INACTIVE_REWARD = Fraction(-1, 10)
REFRESH_DECISION_REWARD = Fraction(-2, 5)
REFRESH_ACTIVE_SETTLEMENT_REWARD = Fraction(1)
SAFE_ACTIVE_REWARD = Fraction(1, 5)


@dataclass(frozen=True)
class NativeLedger:
    decision_reward: Fraction
    settlement_reward: Fraction

    def __post_init__(self) -> None:
        if not isinstance(self.decision_reward, Fraction) or not isinstance(
            self.settlement_reward, Fraction
        ):
            raise ContractValidationError("native ledger rewards must be exact Fraction values")

    @property
    def undiscounted_total(self) -> Fraction:
        return self.decision_reward + self.settlement_reward


def _validate_public_request(state: HostState, decision: DecisionPrimitive) -> None:
    current_need = state.receiver(decision.target_receiver).current_need
    if decision.request_need is not current_need:
        raise ContractValidationError(
            "decision request_need must expose the target's current need"
        )


def evaluator_valid(state: HostState, decision: DecisionPrimitive) -> bool:
    """Compute frozen VALID strictly on the evaluator side.

    The return value and its component predicates must never be inserted into a
    primitive token, recurrent input, adapter, mask, critic state, or loss.
    """

    if not isinstance(state, HostState) or not isinstance(decision, DecisionPrimitive):
        raise ContractValidationError("VALID requires HostState and DecisionPrimitive")
    _validate_public_request(state, decision)
    body = state.body(decision.presented_slot)
    receiver = state.receiver(decision.target_receiver)
    capability_ok = (
        decision.access_mode is AccessMode.OPEN
        or state.carrier(body.carrier).permitted_receiver is decision.target_receiver
    )
    return bool(
        decision.request_active
        and not body.native_neutral
        and body.addressed_receiver is decision.target_receiver
        and body.payload_source_receiver is decision.target_receiver
        and body.content is receiver.current_need
        and body.issuance_owner == receiver.current_owner
        and body.issuance_epoch == receiver.current_epoch
        and capability_ok
    )


# Scientific prose uses the upper-case mathematical name; keep it as a direct
# alias without constructing a second fact source.
VALID = evaluator_valid


def native_ledger(
    state: HostState, decision: DecisionPrimitive, action: Action
) -> NativeLedger:
    """Return exact decision and delayed settlement rewards with no state effect."""

    if not isinstance(action, Action):
        raise ContractValidationError("action must be Action")
    if action is Action.WAIT:
        raise ContractValidationError("WAIT is illegal at a decision transition")
    _validate_public_request(state, decision)
    if action is Action.SERVE:
        if not decision.request_active:
            decision_reward = SERVE_INACTIVE_REWARD
        elif evaluator_valid(state, decision):
            decision_reward = SERVE_VALID_REWARD
        else:
            decision_reward = SERVE_INVALID_REWARD
        return NativeLedger(decision_reward, ZERO)
    if action is Action.REFRESH:
        settlement = REFRESH_ACTIVE_SETTLEMENT_REWARD if decision.request_active else ZERO
        return NativeLedger(REFRESH_DECISION_REWARD, settlement)
    reward = SAFE_ACTIVE_REWARD if decision.request_active else ZERO
    return NativeLedger(reward, ZERO)


def apply_native_action(
    state: HostState, decision: DecisionPrimitive, action: Action
) -> tuple[HostState, NativeLedger]:
    """Apply a decision while proving all actions, including REFRESH, are nonpersistent."""

    return state, native_ledger(state, decision, action)


def evaluator_oracle_action(state: HostState, decision: DecisionPrimitive) -> Action:
    """Unique immediate oracle, evaluator-only and never a learner projection."""

    _validate_public_request(state, decision)
    if not decision.request_active:
        return Action.SAFE_FALLBACK
    return Action.SERVE if evaluator_valid(state, decision) else Action.REFRESH
