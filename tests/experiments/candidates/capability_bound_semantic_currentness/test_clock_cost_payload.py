from fractions import Fraction

from experiments.candidates.capability_bound_semantic_currentness.factorial import construct_world
from experiments.candidates.capability_bound_semantic_currentness.policies import action_ledger, action_vector, cbsc_rule_action, solve_policy
from experiments.candidates.capability_bound_semantic_currentness.registered import registered_spec
from experiments.candidates.capability_bound_semantic_currentness.schema import (
    AccessState,
    Action,
    BindingState,
    NuisanceCoordinate,
    OwnerState,
    PayloadState,
    PolicyArm,
    SemanticState,
)


def _world(owner=OwnerState.LIVE, semantic=SemanticState.PERSIST, payload=PayloadState.RECEIVER_CORRECT):
    return construct_world(
        owner,
        semantic,
        BindingState.AUTHENTIC,
        AccessState.BINDING_GATED,
        payload,
        NuisanceCoordinate(0, 0, 1, 1, 0, 0, 0),
    )


def test_exact_net_endpoints_and_no_terminal_double_charge():
    current = _world()
    stale = _world(semantic=SemanticState.REFRESH)
    unauthorized = _world(owner=OwnerState.BROKEN)
    swapped = _world(payload=PayloadState.SWAPPED)
    assert action_ledger(current, PolicyArm.CBSC_RULE, Action.SERVE).net_return == Fraction(3, 4)
    assert action_ledger(current, PolicyArm.CBSC_RULE, Action.REFRESH).net_return == Fraction(1, 8)
    assert action_ledger(current, PolicyArm.CBSC_RULE, Action.SAFE_FALLBACK).net_return == Fraction(-1, 4)
    assert action_ledger(unauthorized, PolicyArm.CBSC_RULE, Action.SERVE).net_return == Fraction(-3, 4)
    assert action_ledger(stale, PolicyArm.CBSC_RULE, Action.SERVE).net_return == Fraction(-5, 4)
    assert action_ledger(swapped, PolicyArm.CBSC_RULE, Action.SERVE).net_return == Fraction(-5, 4)
    assert action_ledger(current, PolicyArm.RESET_EXACT, Action.REFRESH).net_return == Fraction(1, 4)
    for action in Action:
        ledger = action_ledger(current, PolicyArm.CBSC_RULE, action)
        assert sum(entry.amount for entry in ledger.entries) == ledger.net_return
        assert sum(entry.name == "padded_terminal_service_actuation" for entry in ledger.entries) == 1
    assert action_ledger(current, PolicyArm.CBSC_RULE, Action.SERVE).terminal_clock == 0
    assert action_ledger(current, PolicyArm.CBSC_RULE, Action.REFRESH).terminal_clock == 1


def test_neutral_fallback_is_uniquely_optimal_and_stale_or_swapped_never_direct():
    neutral = _world(payload=PayloadState.NATIVE_NEUTRAL)
    neutral_values = action_vector(neutral, PolicyArm.CBSC_RULE)
    assert neutral_values.safe_fallback > max(neutral_values.serve, neutral_values.refresh)
    for world in (_world(semantic=SemanticState.REFRESH), _world(payload=PayloadState.SWAPPED)):
        values = action_vector(world, PolicyArm.CBSC_RULE)
        assert values.serve < max(values.refresh, values.safe_fallback)


def test_named_scientific_contrasts_clear_delta_but_owner_blind_action_gap_need_only_be_positive():
    spec = registered_spec()
    live = _world()
    broken = _world(owner=OwnerState.BROKEN)
    stale = _world(semantic=SemanticState.REFRESH)
    swapped = _world(payload=PayloadState.SWAPPED)
    cbsc_live = action_ledger(live, PolicyArm.CBSC_RULE, cbsc_rule_action(live)).net_return
    cbsc_broken = action_ledger(broken, PolicyArm.CBSC_RULE, cbsc_rule_action(broken)).net_return
    cbsc_stale = action_ledger(stale, PolicyArm.CBSC_RULE, cbsc_rule_action(stale)).net_return
    cbsc_swapped = action_ledger(swapped, PolicyArm.CBSC_RULE, cbsc_rule_action(swapped)).net_return
    owner_blind = solve_policy((live, broken), PolicyArm.OWNER_BLIND_OPTIMUM).decisions[0]
    owner_value = ((cbsc_live - owner_blind.action_values.for_action(owner_blind.action)) + (cbsc_broken - owner_blind.action_values.for_action(owner_blind.action))) / 2
    retained = cbsc_live - action_ledger(live, PolicyArm.RESET_EXACT, Action.REFRESH).net_return
    currentness = cbsc_live - cbsc_stale
    correct_swapped = cbsc_live - cbsc_swapped
    gated_index = solve_policy((live,), PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL).decisions[0]
    capability = cbsc_live - gated_index.action_values.for_action(gated_index.action)
    assert (capability, owner_value, retained, currentness, correct_swapped) == (
        Fraction(5, 8), Fraction(5, 16), Fraction(1, 2), Fraction(5, 8), Fraction(5, 8)
    )
    assert all(value >= spec.material_margin for value in (capability, owner_value, retained, currentness, correct_swapped))
    assert owner_blind.unique and owner_blind.margin == Fraction(1, 8) < spec.material_margin
