from experiments.candidates.capability_bound_semantic_currentness.factorial import construct_world
from experiments.candidates.capability_bound_semantic_currentness.policies import (
    action_vector,
    cbsc_rule_action,
    controller_view,
    solve_policy,
)
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


def _make(owner=OwnerState.LIVE, binding=BindingState.AUTHENTIC, access=AccessState.OPEN):
    return construct_world(
        owner,
        SemanticState.PERSIST,
        binding,
        access,
        PayloadState.RECEIVER_CORRECT,
        NuisanceCoordinate(0, 0, 1, 1, 0, 1, 0),
    )


def test_raw_view_containment_and_predictive_open_equivalence():
    for binding in BindingState:
        world = _make(binding=binding)
        assert controller_view(world, PolicyArm.CBSC_RULE) == controller_view(world, PolicyArm.RAW_EXACT_OPTIMUM)
        assert controller_view(world, PolicyArm.CBSC_RULE) == controller_view(world, PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL)
        assert action_vector(world, PolicyArm.CBSC_RULE) == action_vector(world, PolicyArm.RAW_EXACT_OPTIMUM)
        assert action_vector(world, PolicyArm.CBSC_RULE) == action_vector(world, PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL)


def test_open_binding_is_pathwise_invariant_but_gated_authorization_is_not_leaked():
    authentic = _make(binding=BindingState.AUTHENTIC, access=AccessState.OPEN)
    reassociated = _make(binding=BindingState.WHOLE_CARRIER_REASSOCIATED, access=AccessState.OPEN)
    assert action_vector(authentic, PolicyArm.CBSC_RULE) == action_vector(reassociated, PolicyArm.CBSC_RULE)
    gated = _make(binding=BindingState.WHOLE_CARRIER_REASSOCIATED, access=AccessState.BINDING_GATED)
    names = {name for name, _ in controller_view(gated, PolicyArm.CBSC_RULE).primitives}
    assert "authorization_result" not in names
    assert "authorized" not in names
    assert action_vector(gated, PolicyArm.CBSC_RULE).serve != action_vector(authentic, PolicyArm.CBSC_RULE).serve


def test_owner_blind_twins_share_one_optimized_decision():
    worlds = (_make(owner=OwnerState.LIVE, access=AccessState.BINDING_GATED), _make(owner=OwnerState.BROKEN, access=AccessState.BINDING_GATED))
    assert controller_view(worlds[0], PolicyArm.OWNER_BLIND_OPTIMUM) == controller_view(worlds[1], PolicyArm.OWNER_BLIND_OPTIMUM)
    exact = solve_policy(worlds, PolicyArm.OWNER_BLIND_OPTIMUM)
    assert len(exact.decisions) == 1
    assert exact.decisions[0].unique


def test_cbsc_frozen_route_is_derived_independently_from_raw_optimization():
    current = _make(access=AccessState.BINDING_GATED)
    broken = _make(owner=OwnerState.BROKEN, access=AccessState.BINDING_GATED)
    neutral = construct_world(
        OwnerState.LIVE,
        SemanticState.PERSIST,
        BindingState.AUTHENTIC,
        AccessState.BINDING_GATED,
        PayloadState.NATIVE_NEUTRAL,
        NuisanceCoordinate(0, 0, 1, 1, 0, 1, 0),
    )
    assert cbsc_rule_action(current) is Action.SERVE
    assert cbsc_rule_action(broken) is Action.REFRESH
    assert cbsc_rule_action(neutral) is Action.SAFE_FALLBACK
    for world in (current, broken, neutral):
        cbsc = solve_policy((world,), PolicyArm.CBSC_RULE).decisions[0]
        raw = solve_policy((world,), PolicyArm.RAW_EXACT_OPTIMUM).decisions[0]
        assert cbsc.action is cbsc_rule_action(world)
        assert raw.action_values == cbsc.action_values
        assert raw.action is max(
            Action,
            key=lambda action: raw.action_values.for_action(action),
        )
        assert cbsc.unique


def test_reset_masks_entire_cache_and_neutrality_is_public_need_status():
    coordinate = NuisanceCoordinate(0, 0, 1, 1, 0, 1, 0)
    correct = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.BINDING_GATED, PayloadState.RECEIVER_CORRECT, coordinate)
    swapped = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.BINDING_GATED, PayloadState.SWAPPED, coordinate)
    neutral = construct_world(OwnerState.LIVE, SemanticState.PERSIST, BindingState.AUTHENTIC, AccessState.BINDING_GATED, PayloadState.NATIVE_NEUTRAL, coordinate)
    correct_view = dict(controller_view(correct, PolicyArm.RESET_EXACT).primitives)
    swapped_view = dict(controller_view(swapped, PolicyArm.RESET_EXACT).primitives)
    neutral_view = dict(controller_view(neutral, PolicyArm.RESET_EXACT).primitives)
    assert correct_view == swapped_view
    assert correct_view["body_native_neutral"] == neutral_view["body_native_neutral"] == "CACHE_REMOVED"
    differing = {key for key in correct_view if correct_view[key] != neutral_view[key]}
    assert differing == {"focal_need_active"}
    assert correct_view["focal_need_active"] is True
    assert neutral_view["focal_need_active"] is False
