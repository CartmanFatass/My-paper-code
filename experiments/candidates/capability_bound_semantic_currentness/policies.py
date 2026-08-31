"""Pre-action views, exact ledgers, and finite policy optimization."""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from typing import Iterable

from .registered import registered_spec
from .rng import canonical_dumps
from .schema import (
    AccessState,
    Action,
    ActionLedger,
    ActionVector,
    ExactPolicy,
    LedgerEntry,
    ObservationKey,
    PolicyArm,
    PolicyDecision,
    RegisteredSpec,
    World,
)


_ACTION_ORDER = (Action.SERVE, Action.REFRESH, Action.SAFE_FALLBACK)


def _public_primitives(world: World) -> dict[str, object]:
    associated_carrier = world.focal_carrier
    carrier = world.execution_carrier
    body = carrier.body
    return {
        "physical_receiver": world.physical_receiver,
        "focal_need_active": world.focal_need_active,
        "owner_predecessor_live": world.owner_continuity,
        "public_epoch_match": world.epoch_match,
        "access_binding_gated": world.access is AccessState.BINDING_GATED,
        "carrier_association_authentic": world.association_authentic,
        "associated_carrier_issued_to_receiver": associated_carrier.issued_to_receiver,
        "execution_carrier_issued_to_receiver": carrier.issued_to_receiver,
        "body_addressed_receiver": body.addressed_receiver,
        "body_address_match": world.body_address_match,
        "payload_source_receiver": body.payload_source_receiver,
        "payload_source_match": world.payload_source_match,
        "body_content_bit": body.content_bit,
        "body_native_neutral": body.native_neutral,
        "body_epoch": body.epoch,
        "body_public_phase": body.public_phase,
        "focal_need_value": world.focal_need_value,
        "public_z0": world.nuisance.z0,
        "public_z1": world.nuisance.z1,
        "presentation_permutation": world.nuisance.presentation_permutation,
        "presented_carrier_ids": tuple(carrier.carrier_id for carrier in world.presented_carriers),
    }


def controller_view(world: World, policy: PolicyArm) -> ObservationKey:
    """Return a pre-action observation; authorization outcome is never a field."""

    if not isinstance(policy, PolicyArm):
        policy = PolicyArm(policy)
    primitives = _public_primitives(world)
    if policy is PolicyArm.OWNER_BLIND_OPTIMUM:
        primitives["owner_predecessor_live"] = "MASKED"
    elif policy is PolicyArm.RESET_EXACT:
        for name in (
            "carrier_association_authentic",
            "associated_carrier_issued_to_receiver",
            "execution_carrier_issued_to_receiver",
            "body_addressed_receiver",
            "body_address_match",
            "payload_source_receiver",
            "payload_source_match",
            "body_content_bit",
            "body_native_neutral",
            "body_epoch",
            "body_public_phase",
            "presented_carrier_ids",
        ):
            primitives[name] = "CACHE_REMOVED"
    elif policy is PolicyArm.HARD_OPEN:
        for name in (
            "owner_predecessor_live",
            "public_epoch_match",
            "carrier_association_authentic",
            "associated_carrier_issued_to_receiver",
            "execution_carrier_issued_to_receiver",
            "body_addressed_receiver",
            "body_address_match",
            "payload_source_receiver",
            "payload_source_match",
            "body_content_bit",
            "body_epoch",
            "body_public_phase",
            "focal_need_value",
            "presented_carrier_ids",
        ):
            primitives[name] = "UNCONDITIONED"
    # CBSC, RAW, and the predictive-index null receive byte/timing-identical
    # primitives.  The null changes execution capability, not information.
    return ObservationKey(tuple(sorted(primitives.items())))


def _cached_direct_permitted(world: World, policy: PolicyArm) -> bool:
    if policy is PolicyArm.RESET_EXACT:
        return False
    if policy is PolicyArm.HARD_OPEN:
        return world.focal_need_active and not world.native_neutral
    if world.access is AccessState.OPEN:
        return world.focal_need_active and not world.native_neutral
    if policy is PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL:
        return False
    return (
        world.owner_continuity
        and world.association_authentic
        and world.body_address_match
        and world.focal_need_active
        and not world.native_neutral
    )


def _direct_correct(world: World) -> bool:
    return (
        not world.native_neutral
        and world.body_address_match
        and world.payload_source_match
        and world.direct_content_current
    )


def cbsc_rule_action(world: World) -> Action:
    """Frozen CBSC pre-action rule, independently of payoff optimization."""

    if not world.focal_need_active:
        return Action.SAFE_FALLBACK
    if _cached_direct_permitted(world, PolicyArm.CBSC_RULE) and _direct_correct(world):
        return Action.SERVE
    return Action.REFRESH


def action_ledger(
    world: World,
    policy: PolicyArm,
    action: Action,
    spec: RegisteredSpec | None = None,
) -> ActionLedger:
    """Execute one exact action without exposing its authorization result in advance."""

    spec = registered_spec() if spec is None else spec
    if not isinstance(policy, PolicyArm):
        policy = PolicyArm(policy)
    if not isinstance(action, Action):
        action = Action(action)
    entries: list[LedgerEntry] = []
    if policy is not PolicyArm.RESET_EXACT:
        entries.append(LedgerEntry("common_validation_read", 0, -spec.cost("common_validation_read")))

    if action is Action.SERVE:
        if _cached_direct_permitted(world, policy):
            gross_name = "gross_correct_service" if _direct_correct(world) else "gross_wrong_service"
        else:
            gross_name = "gross_unauthorized_attempt"
        entries.append(LedgerEntry(gross_name, 0, spec.cost(gross_name)))
        entries.append(LedgerEntry(
            "padded_terminal_service_actuation",
            0,
            -spec.cost("padded_terminal_service_actuation"),
        ))
        terminal_clock = 0
    elif action is Action.SAFE_FALLBACK:
        entries.append(LedgerEntry("gross_safe_fallback", 0, spec.cost("gross_safe_fallback")))
        entries.append(LedgerEntry(
            "padded_terminal_service_actuation",
            0,
            -spec.cost("padded_terminal_service_actuation"),
        ))
        terminal_clock = 0
    else:
        entries.extend((
            LedgerEntry("refresh_scan", 0, -spec.cost("refresh_scan")),
            LedgerEntry("refresh_delay", 0, -spec.cost("refresh_delay")),
            LedgerEntry("new_content_ingestion", 1, -spec.cost("new_content_ingestion")),
        ))
        # A neutral opportunity has nothing productive to refresh and therefore
        # receives no service gross; this makes fallback uniquely optimal.
        if world.focal_need_active:
            entries.append(LedgerEntry("gross_correct_service", 1, spec.cost("gross_correct_service")))
        else:
            entries.append(LedgerEntry("gross_safe_fallback", 1, spec.cost("gross_safe_fallback")))
        entries.append(LedgerEntry(
            "padded_terminal_service_actuation",
            1,
            -spec.cost("padded_terminal_service_actuation"),
        ))
        terminal_clock = 1

    net = sum((entry.amount for entry in entries), Fraction(0))
    return ActionLedger(action, terminal_clock, tuple(entries), net)


def action_vector(
    world: World,
    policy: PolicyArm,
    spec: RegisteredSpec | None = None,
) -> ActionVector:
    spec = registered_spec() if spec is None else spec
    return ActionVector(
        action_ledger(world, policy, Action.SERVE, spec).net_return,
        action_ledger(world, policy, Action.REFRESH, spec).net_return,
        action_ledger(world, policy, Action.SAFE_FALLBACK, spec).net_return,
    )


def _average(values: Iterable[Fraction]) -> Fraction:
    material = tuple(values)
    if not material:
        raise ValueError("cannot average empty exact support")
    return sum(material, Fraction(0)) / len(material)


def solve_policy(worlds: tuple[World, ...], policy: PolicyArm) -> ExactPolicy:
    if not worlds:
        raise ValueError("exact policy requires nonempty world support")
    if not isinstance(policy, PolicyArm):
        policy = PolicyArm(policy)
    grouped: dict[ObservationKey, list[World]] = defaultdict(list)
    for world in worlds:
        grouped[controller_view(world, policy)].append(world)
    decisions: list[PolicyDecision] = []
    for observation in sorted(grouped, key=lambda item: canonical_dumps(item)):
        support = grouped[observation]
        values = {
            action: _average(action_ledger(world, policy, action).net_return for world in support)
            for action in _ACTION_ORDER
        }
        maximum = max(values.values())
        winners = tuple(action for action in _ACTION_ORDER if values[action] == maximum)
        ordered_values = sorted(values.values(), reverse=True)
        if policy is PolicyArm.CBSC_RULE:
            selected_actions = {cbsc_rule_action(world) for world in support}
            if len(selected_actions) != 1:
                raise RuntimeError("CBSC observation aliases distinct frozen-rule actions")
            selected = next(iter(selected_actions))
            unique = len(winners) == 1 and selected is winners[0]
            margin = values[selected] - max(
                value for action, value in values.items() if action is not selected
            )
        elif policy is PolicyArm.HARD_OPEN:
            # HARD_OPEN is a diagnostic fixed cached-body-use rule, not another
            # optimized comparator.  It conditions only on neutral opportunity.
            selected = Action.SAFE_FALLBACK if not support[0].focal_need_active else Action.SERVE
            unique = len(winners) == 1 and selected is winners[0]
            margin = values[selected] - max(value for action, value in values.items() if action is not selected)
        else:
            selected = winners[0]
            unique = len(winners) == 1
            margin = ordered_values[0] - ordered_values[1]
        vector = ActionVector(
            values[Action.SERVE], values[Action.REFRESH], values[Action.SAFE_FALLBACK]
        )
        decisions.append(PolicyDecision(observation, vector, selected, unique, margin))
    return ExactPolicy(policy, tuple(decisions))


__all__ = ["action_ledger", "action_vector", "cbsc_rule_action", "controller_view", "solve_policy"]
