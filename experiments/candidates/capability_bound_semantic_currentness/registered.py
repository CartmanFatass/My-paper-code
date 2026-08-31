"""Prospectively frozen CBSC host registration."""

from __future__ import annotations

from fractions import Fraction

from .rng import NUISANCE_VERSION
from .schema import (
    AccessState,
    Action,
    BindingState,
    CompleteResult,
    OwnerState,
    PayloadState,
    PolicyArm,
    RegisteredSpec,
    ResultRow,
    SemanticState,
    SpecAudit,
    to_jsonable,
)


SPEC_SCHEMA = "cbsc_host_spec_v1"
RESULT_SCHEMA = "cbsc_exact_factorial_result_v1"
PROTOCOL_ID = "CBSC-EXACT-FACTORIAL-V1"

_COSTS = (
    ("common_validation_read", Fraction(1, 8)),
    ("padded_terminal_service_actuation", Fraction(1, 8)),
    ("refresh_scan", Fraction(1, 4)),
    ("refresh_delay", Fraction(1, 4)),
    ("new_content_ingestion", Fraction(1, 8)),
    ("gross_correct_service", Fraction(1)),
    ("gross_wrong_service", Fraction(-1)),
    ("gross_unauthorized_attempt", Fraction(-1, 2)),
    ("gross_safe_fallback", Fraction(0)),
)

_INTERPRETATION_BOUNDARY = (
    "Exact one-opportunity protocol value of current receiver-addressed content plus a current "
    "execution capability only; no representation, learning, security, proactive acquisition, "
    "MARL, variable-population/lifetime, UAV, safety, or deployment claim."
)

_PROTOCOL_ORDER = (
    "COMMIT_NEED_RECEIVER_OLD_CONTENT_PHASE",
    "ISSUE_ALL_IMMUTABLE_BODIES_AND_WHOLE_CARRIERS",
    "COMMIT_OWNER_AND_SEMANTIC_EPOCH",
    "COMMIT_ACCESS_LAW",
    "CHOOSE_ONCE_AT_T0_WITHOUT_AUTHORIZATION_RESULT",
    "TERMINATE_T0_OR_REFRESH_AND_CORRECT_SERVICE_T1",
)
_BRANCH_ORDER = (
    "VALID_NARROW_PROTOCOL_VALUE",
    "INDEX_ABSORBS",
    "RAW_MISMATCH_OR_TIE",
    "NO_CAPABILITY_EDGE",
    "NO_CONTENT_EDGE",
    "INVALID",
)


def registered_spec() -> RegisteredSpec:
    return RegisteredSpec(
        schema=SPEC_SCHEMA,
        direction_id="capability_bound_semantic_currentness",
        protocol_id=PROTOCOL_ID,
        nuisance_version=NUISANCE_VERSION,
        owner_levels=(OwnerState.LIVE, OwnerState.BROKEN),
        semantic_levels=(SemanticState.PERSIST, SemanticState.REFRESH),
        binding_levels=(BindingState.AUTHENTIC, BindingState.WHOLE_CARRIER_REASSOCIATED),
        access_levels=(AccessState.OPEN, AccessState.BINDING_GATED),
        payload_levels=(
            PayloadState.RECEIVER_CORRECT,
            PayloadState.SWAPPED,
            PayloadState.NATIVE_NEUTRAL,
        ),
        policies=tuple(PolicyArm),
        actions=(Action.SERVE, Action.REFRESH, Action.SAFE_FALLBACK),
        nuisance_fields=(
            "physical_receiver",
            "old_bit",
            "current_bit",
            "donor_bit",
            "z0",
            "z1",
            "presentation_permutation",
        ),
        costs=_COSTS,
        material_margin=Fraction(1, 4),
        protocol_order=_PROTOCOL_ORDER,
        all_payload_issuance_law="CORRECT_SWAPPED_NEUTRAL_IMMUTABLE_INVENTORY_BEFORE_PAYLOAD_SELECTION",
        phase_currentness_law="RECEIVER_KEYED_BASE_BIT_XOR_PUBLIC_Z;_REFRESH_MISMATCH_HIDES_NEW_CONTENT_UNTIL_T1",
        reassociation_law="FIXED_POINT_FREE_SWAP_OF_INTACT_CARRIERS_WITHIN_PRETREATMENT_STRATUM",
        authorization_information_law="NO_PREACTION_RESULT;GATED_REQUIRES_LIVE_OWNER_AUTHENTIC_ASSOCIATION_RECEIVER_ADDRESSED_NONNEUTRAL_BODY;OPEN_REMOVES_EDGE;INDEX_NULL_MATCHES_OPEN",
        action_clock_law=(("SERVE", 0), ("SAFE_FALLBACK", 0), ("REFRESH", 1)),
        determinism_law=(
            "EXHAUSTIVE_FACTORS_AND_NUISANCE",
            "CBSC_F0_V1_COUNTER_ADDRESSED_NUISANCE_ONLY",
            "NO_GLOBAL_PYTHON_NUMPY_TORCH_RNG",
            "CANONICAL_WORLD_THEN_POLICY_ROW_ORDER",
            "ZERO_OPTIMIZER_SEEDS_CHECKPOINTS",
        ),
        publication_law=("COMPLETE_ONLY", "ATOMIC", "CREATE_ONLY", "REJECT_PREEXISTING_TARGET"),
        branch_order=_BRANCH_ORDER,
        cbsc_fixed_rule=(
            ("FOCAL_NEED_INACTIVE", "SAFE_FALLBACK"),
            ("DIRECT_EXECUTABLE_AND_CURRENT_AND_RECEIVER_SOURCE_CORRECT", "SERVE"),
            ("OTHERWISE", "REFRESH"),
        ),
        owner_blind_law=("MASK_OWNER_PREDECESSOR_HISTORY", "OPTIMIZE_UNIFORM_LIVE_BROKEN_MIXTURE"),
        reset_law=("REMOVE_ALL_CACHED_BODY_AND_CARRIER_FIELDS", "KEEP_PUBLIC_FOCAL_NEED_ACTIVE", "WAIVE_COMMON_VALIDATION_READ_ONLY", "SINGLE_REACTIVE_REFRESH"),
        hard_open_law=("FIXED_NOT_OPTIMIZED", "ACTIVE_NEED_SERVE_CACHED_BODY", "INACTIVE_NEED_SAFE_FALLBACK", "NO_CURRENTNESS_OR_ADDRESS_CONDITIONING"),
        policy_capability_law=(
            ("CBSC_RULE", "OPEN_ROUTED_OR_GATED_CURRENT_NONFUNGIBLE_CAPABILITY"),
            ("RAW_EXACT_OPTIMUM", "SAME_CAPABILITY_AND_PRIMITIVES_AS_CBSC"),
            ("OWNER_BLIND_OPTIMUM", "SAME_CAPABILITY_WITH_OWNER_MASK"),
            ("PREDICTIVE_INDEX_CAPABILITY_NULL", "OPEN_EQUIVALENT_GATED_NO_NONFUNGIBLE_DIRECT_CAPABILITY"),
            ("RESET_EXACT", "NO_CACHED_DIRECT_CAPABILITY"),
            ("HARD_OPEN", "DIAGNOSTIC_FIXED_CACHED_BODY_USE"),
        ),
        action_ledger_incidence=(
            ("SERVE", ("COMMON_READ_UNLESS_RESET_T0", "ONE_OF_CORRECT_WRONG_UNAUTHORIZED_GROSS_T0", "PADDED_TERMINAL_ACTUATION_T0")),
            ("SAFE_FALLBACK", ("COMMON_READ_UNLESS_RESET_T0", "ZERO_GROSS_T0", "PADDED_TERMINAL_ACTUATION_T0")),
            ("REFRESH", ("COMMON_READ_UNLESS_RESET_T0", "SCAN_T0", "DELAY_T0", "INGESTION_T1", "ACTIVE_CORRECT_OR_INACTIVE_ZERO_GROSS_T1", "PADDED_TERMINAL_ACTUATION_T1")),
        ),
        contrast_laws=(
            ("CAPABILITY_DID", "(CBSC-INDEX)_GATED_USABLE-(CBSC-INDEX)_OPEN_USABLE"),
            ("OWNER_INFORMATION", "MEAN_LIVE_BROKEN(CBSC-OWNER_BLIND)_GATED_AUTHENTIC_CORRECT_PERSIST"),
            ("RETAINED_CONTENT", "CBSC-RESET_GATED_LIVE_AUTHENTIC_CORRECT_PERSIST"),
            ("CURRENTNESS", "CBSC_PERSIST-CBSC_REFRESH_GATED_LIVE_AUTHENTIC_CORRECT"),
            ("CORRECT_VS_SWAPPED", "CBSC_CORRECT-CBSC_SWAPPED_GATED_LIVE_AUTHENTIC_PERSIST"),
        ),
        delta_comparator="NAMED_FIVE_CONTRAST_ACCEPT_IF_GREATER_THAN_OR_EQUAL_TO_MATERIAL_MARGIN;ACTION_GAPS_STRICTLY_POSITIVE_ONLY",
        branch_witness_law="REGISTERED_PRECEDENCE;FIRST_FALSE_AUDIT;CANONICAL_WORLD_OR_PAIR_FOR_ROWWISE_FAILURE",
        interpretation_boundary=_INTERPRETATION_BOUNDARY,
    )


def validate_registered_spec(spec: RegisteredSpec) -> SpecAudit:
    expected = registered_spec()
    checks = (
        ("schema", spec.schema == expected.schema),
        ("direction_identity", spec.direction_id == expected.direction_id),
        ("protocol_identity", spec.protocol_id == expected.protocol_id),
        ("nuisance_identity", spec.nuisance_version == expected.nuisance_version),
        ("factor_levels", (
            spec.owner_levels,
            spec.semantic_levels,
            spec.binding_levels,
            spec.access_levels,
            spec.payload_levels,
        ) == (
            expected.owner_levels,
            expected.semantic_levels,
            expected.binding_levels,
            expected.access_levels,
            expected.payload_levels,
        )),
        ("arms", spec.policies == expected.policies),
        ("actions", spec.actions == expected.actions),
        ("nuisance_coordinates", spec.nuisance_fields == expected.nuisance_fields),
        ("fraction_cost_law", spec.costs == expected.costs),
        ("material_margin", spec.material_margin == Fraction(1, 4)),
        ("protocol_order", spec.protocol_order == expected.protocol_order),
        ("all_payload_issuance_law", spec.all_payload_issuance_law == expected.all_payload_issuance_law),
        ("phase_currentness_law", spec.phase_currentness_law == expected.phase_currentness_law),
        ("reassociation_law", spec.reassociation_law == expected.reassociation_law),
        ("authorization_information_law", spec.authorization_information_law == expected.authorization_information_law),
        ("action_clock_law", spec.action_clock_law == expected.action_clock_law),
        ("determinism_law", spec.determinism_law == expected.determinism_law),
        ("publication_law", spec.publication_law == expected.publication_law),
        ("branch_order", spec.branch_order == expected.branch_order),
        ("cbsc_fixed_rule", spec.cbsc_fixed_rule == expected.cbsc_fixed_rule),
        ("owner_blind_law", spec.owner_blind_law == expected.owner_blind_law),
        ("reset_law", spec.reset_law == expected.reset_law),
        ("hard_open_law", spec.hard_open_law == expected.hard_open_law),
        ("policy_capability_law", spec.policy_capability_law == expected.policy_capability_law),
        ("action_ledger_incidence", spec.action_ledger_incidence == expected.action_ledger_incidence),
        ("contrast_laws", spec.contrast_laws == expected.contrast_laws),
        ("delta_comparator", spec.delta_comparator == expected.delta_comparator),
        ("branch_witness_law", spec.branch_witness_law == expected.branch_witness_law),
        ("cell_count_48", spec.scientific_cell_count == 48),
        ("nuisance_count_128", spec.nuisance_count == 128),
        ("world_count_6144", spec.world_count == 6144),
        ("interpretation_boundary", spec.interpretation_boundary == expected.interpretation_boundary),
    )
    errors = tuple(name for name, passed in checks if not passed)
    return SpecAudit(
        valid=not errors,
        scientific_cell_count=spec.scientific_cell_count,
        nuisance_count_per_cell=spec.nuisance_count,
        world_count_per_arm=spec.world_count,
        checks=checks,
        errors=errors,
    )


def _build_complete_result(spec: RegisteredSpec, worlds: tuple) -> CompleteResult:
    """Pure exact semantic builder shared by evaluation and result validation."""

    from .factorial import world_inventory_record
    from .policies import action_ledger, action_vector, controller_view, solve_policy

    audit = validate_registered_spec(spec)
    if not audit.valid:
        raise ValueError(f"registered spec failed validation: {', '.join(audit.errors)}")
    if len(worlds) != spec.world_count or len({world.world_id for world in worlds}) != spec.world_count:
        raise ValueError("complete builder requires the exact distinct registered world support")
    policies = {arm: solve_policy(worlds, arm) for arm in spec.policies}
    decision_maps = {
        arm: {decision.observation: decision for decision in exact.decisions}
        for arm, exact in policies.items()
    }
    rows: list[ResultRow] = []
    by_world_arm: dict[tuple[str, PolicyArm], ResultRow] = {}
    for world in worlds:
        for arm in spec.policies:
            observation = controller_view(world, arm)
            decision = decision_maps[arm][observation]
            vector = action_vector(world, arm, spec)
            ledger = action_ledger(world, arm, decision.action, spec)
            row = ResultRow(world.world_id, world.nuisance_id, arm, observation, vector, decision.action, ledger)
            rows.append(row)
            by_world_arm[(world.world_id, arm)] = row
    rows.sort(key=lambda row: (row.world_id, row.policy.value))

    def full_row_semantics_equal(left: ResultRow, right: ResultRow) -> bool:
        return (
            left.observation == right.observation
            and left.action_values == right.action_values
            and left.decision == right.decision
            and left.ledger == right.ledger
        )

    def action_value_effect_equal(left: ResultRow, right: ResultRow) -> bool:
        return (
            left.action_values == right.action_values
            and left.decision == right.decision
            and left.ledger == right.ledger
        )

    raw_containment = all(full_row_semantics_equal(
        by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)],
        by_world_arm[(world.world_id, PolicyArm.RAW_EXACT_OPTIMUM)],
    ) for world in worlds)
    cbsc_decisions = policies[PolicyArm.CBSC_RULE].decisions
    optimized_decisions = tuple(
        decision for arm, exact in policies.items()
        if arm not in (PolicyArm.CBSC_RULE, PolicyArm.HARD_OPEN)
        for decision in exact.decisions
    )
    cbsc_selected_unique = all(decision.unique for decision in cbsc_decisions)
    optimized_unique = all(decision.unique for decision in optimized_decisions)
    cbsc_min_margin = min(decision.margin for decision in cbsc_decisions)
    optimized_min_margin = min(decision.margin for decision in optimized_decisions)
    neutral_never_serves = all(
        by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)].decision is not Action.SERVE
        for world in worlds if world.payload is PayloadState.NATIVE_NEUTRAL
    )
    open_index_equivalence = all(full_row_semantics_equal(
        by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)],
        by_world_arm[(world.world_id, PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL)],
    ) for world in worlds if world.access is AccessState.OPEN)

    def binding_pair_key(world) -> tuple:
        return (
            world.owner.value,
            world.semantic.value,
            world.access.value,
            world.payload.value,
            world.nuisance.address(),
        )

    open_authentic = {
        binding_pair_key(world): world for world in worlds
        if world.access is AccessState.OPEN and world.binding is BindingState.AUTHENTIC
    }
    open_reassociated = {
        binding_pair_key(world): world for world in worlds
        if world.access is AccessState.OPEN and world.binding is BindingState.WHOLE_CARRIER_REASSOCIATED
    }
    open_zero_binding_effect = open_authentic.keys() == open_reassociated.keys() and all(
        action_value_effect_equal(
            by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)],
            by_world_arm[(open_reassociated[key].world_id, PolicyArm.CBSC_RULE)],
        )
        for key, world in open_authentic.items()
    )
    gated_usable = [
        world for world in worlds
        if world.access is AccessState.BINDING_GATED and world.owner_continuity
        and world.association_authentic and world.payload is PayloadState.RECEIVER_CORRECT
        and world.semantic is SemanticState.PERSIST
    ]
    gated_usable_mixture = [
        world for world in worlds
        if world.access is AccessState.BINDING_GATED and world.association_authentic
        and world.payload is PayloadState.RECEIVER_CORRECT
        and world.semantic is SemanticState.PERSIST
    ]
    open_usable = [
        world for world in worlds
        if world.access is AccessState.OPEN and world.owner_continuity
        and world.association_authentic and world.payload is PayloadState.RECEIVER_CORRECT
        and world.semantic is SemanticState.PERSIST
    ]

    def mean(values: list[Fraction]) -> Fraction:
        return sum(values, Fraction(0)) / len(values) if values else Fraction(0)

    def arm_gap(material: list, left: PolicyArm, right: PolicyArm) -> Fraction:
        return mean([
            by_world_arm[(world.world_id, left)].ledger.net_return
            - by_world_arm[(world.world_id, right)].ledger.net_return
            for world in material
        ])

    capability_did = arm_gap(gated_usable, PolicyArm.CBSC_RULE, PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL) - arm_gap(open_usable, PolicyArm.CBSC_RULE, PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL)
    owner_information = arm_gap(gated_usable_mixture, PolicyArm.CBSC_RULE, PolicyArm.OWNER_BLIND_OPTIMUM)
    retained_content = arm_gap(gated_usable, PolicyArm.CBSC_RULE, PolicyArm.RESET_EXACT)
    correct_current = mean([by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)].ledger.net_return for world in gated_usable])
    swapped_current = mean([
        by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)].ledger.net_return
        for world in worlds
        if world.access is AccessState.BINDING_GATED and world.owner_continuity
        and world.association_authentic and world.payload is PayloadState.SWAPPED
        and world.semantic is SemanticState.PERSIST
    ])
    refreshed_correct = mean([
        by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)].ledger.net_return
        for world in worlds
        if world.access is AccessState.BINDING_GATED and world.owner_continuity
        and world.association_authentic and world.payload is PayloadState.RECEIVER_CORRECT
        and world.semantic is SemanticState.REFRESH
    ])
    currentness_contrast = correct_current - refreshed_correct
    correct_swapped_contrast = correct_current - swapped_current
    audits = {
        "raw_rowwise_identity": raw_containment,
        "cbsc_selected_is_unique_optimum": cbsc_selected_unique,
        "cbsc_selected_margin_positive": cbsc_min_margin > 0,
        "optimized_policy_decisions_unique_excluding_fixed_arms": optimized_unique,
        "optimized_selected_margin_positive_excluding_fixed_arms": optimized_min_margin > 0,
        "hard_open_is_fixed_diagnostic": True,
        "open_predictive_index_equivalence": open_index_equivalence,
        "open_zero_binding_action_value_effect": open_zero_binding_effect,
        "currentness_clears_material_margin": currentness_contrast >= spec.material_margin,
        "correct_swapped_clears_material_margin": correct_swapped_contrast >= spec.material_margin,
        "neutral_payload_never_direct": neutral_never_serves,
        "capability_did_clears_material_margin": capability_did >= spec.material_margin,
        "owner_information_clears_material_margin": owner_information >= spec.material_margin,
        "retained_content_clears_material_margin": retained_content >= spec.material_margin,
        "no_preaction_authorization_result": all(
            all("authorization_result" not in name for name, _ in row.observation.primitives) for row in rows
        ),
    }
    if not raw_containment or not cbsc_selected_unique or cbsc_min_margin <= 0 or not optimized_unique or optimized_min_margin <= 0:
        branch = "RAW_MISMATCH_OR_TIE"
    elif not open_index_equivalence or not open_zero_binding_effect:
        branch = "INVALID"
    elif capability_did < spec.material_margin:
        branch = "NO_CAPABILITY_EDGE"
    elif (
        correct_swapped_contrast < spec.material_margin
        or currentness_contrast < spec.material_margin
        or retained_content < spec.material_margin
    ):
        branch = "NO_CONTENT_EDGE"
    elif owner_information < spec.material_margin:
        branch = "INDEX_ABSORBS"
    elif all(audits.values()):
        branch = "VALID_NARROW_PROTOCOL_VALUE"
    else:
        branch = "INVALID"
    first_false = next((name for name, passed in audits.items() if not passed), None)
    witness = first_false
    canonical_worlds = sorted(worlds, key=lambda item: item.world_id)
    if first_false == "raw_rowwise_identity":
        failed = next(world for world in canonical_worlds if not full_row_semantics_equal(
            by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)],
            by_world_arm[(world.world_id, PolicyArm.RAW_EXACT_OPTIMUM)],
        ))
        witness = f"raw_rowwise_identity|world={failed.world_id}"
    elif first_false == "open_predictive_index_equivalence":
        failed = next(world for world in canonical_worlds if world.access is AccessState.OPEN and not full_row_semantics_equal(
            by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)],
            by_world_arm[(world.world_id, PolicyArm.PREDICTIVE_INDEX_CAPABILITY_NULL)],
        ))
        witness = f"open_predictive_index_equivalence|world={failed.world_id}"
    elif first_false == "open_zero_binding_action_value_effect":
        failed_key = next(key for key in sorted(open_authentic) if not action_value_effect_equal(
            by_world_arm[(open_authentic[key].world_id, PolicyArm.CBSC_RULE)],
            by_world_arm[(open_reassociated[key].world_id, PolicyArm.CBSC_RULE)],
        ))
        witness = (
            "open_zero_binding_action_value_effect|world_pair="
            f"{open_authentic[failed_key].world_id},{open_reassociated[failed_key].world_id}"
        )
    elif first_false == "neutral_payload_never_direct":
        failed = next(world for world in canonical_worlds if world.payload is PayloadState.NATIVE_NEUTRAL and by_world_arm[(world.world_id, PolicyArm.CBSC_RULE)].decision is Action.SERVE)
        witness = f"neutral_payload_never_direct|world={failed.world_id}"
    elif first_false == "no_preaction_authorization_result":
        failed = next(row for row in rows if any("authorization_result" in name for name, _ in row.observation.primitives))
        witness = f"no_preaction_authorization_result|world={failed.world_id}|policy={failed.policy.value}"
    world_inventory = [world_inventory_record(world) for world in sorted(worlds, key=lambda item: item.world_id)]
    return CompleteResult(
        schema=RESULT_SCHEMA,
        complete=True,
        identity={"direction_id": spec.direction_id, "protocol_id": spec.protocol_id, "nuisance_version": spec.nuisance_version},
        manifests={
            "registered_spec": to_jsonable(spec),
            "row_order": {
                "law": "LEXICOGRAPHIC_WORLD_ID_THEN_POLICY",
                "row_count": len(rows),
                "first_key": [rows[0].world_id, rows[0].policy.value],
                "last_key": [rows[-1].world_id, rows[-1].policy.value],
            },
            "inventory": {
                "policies": [arm.value for arm in spec.policies],
                "actions": [action.value for action in spec.actions],
                "terminal_clocks": [0, 1],
                "ledger_components": [
                    "common_validation_read",
                    "padded_terminal_service_actuation",
                    "refresh_scan",
                    "refresh_delay",
                    "new_content_ingestion",
                    "gross_correct_service",
                    "gross_wrong_service",
                    "gross_unauthorized_attempt",
                    "gross_safe_fallback",
                ],
            },
            "world_inventory": world_inventory,
        },
        support={
            "scientific_cell_count": spec.scientific_cell_count,
            "nuisance_count_per_cell": spec.nuisance_count,
            "world_count_per_arm": len(worlds),
            "policy_count": len(spec.policies),
            "row_count": len(rows),
        },
        pairing={
            "nuisance_version": spec.nuisance_version,
            "distinct_nuisance_ids": len({world.nuisance_id for world in worlds}),
            "worlds_per_nuisance_id": spec.scientific_cell_count,
            "controller_or_action_in_address": False,
        },
        rows=tuple(rows),
        contrasts={
            "capability_difference_in_differences": capability_did,
            "owner_information_value_usable_cell": owner_information,
            "retained_content_value_usable_cell": retained_content,
            "correct_current_value": correct_current,
            "swapped_current_value": swapped_current,
            "currentness_persist_minus_refresh": currentness_contrast,
            "receiver_correct_minus_swapped": correct_swapped_contrast,
            "cbsc_min_selected_margin": cbsc_min_margin,
            "optimized_min_selected_margin_excluding_fixed_arms": optimized_min_margin,
        },
        audits=audits,
        interpretation_boundary=spec.interpretation_boundary,
        branch=branch,
        first_failing_witness=witness,
    )


def evaluate_registered(spec: RegisteredSpec) -> CompleteResult:
    """Cross the sole result-bearing exhaustive registered-evaluation seam."""

    from .factorial import enumerate_worlds

    audit = validate_registered_spec(spec)
    if not audit.valid:
        raise ValueError(f"registered spec failed validation: {', '.join(audit.errors)}")
    return _build_complete_result(spec, enumerate_worlds(spec))


__all__ = [
    "PROTOCOL_ID", "RESULT_SCHEMA", "SPEC_SCHEMA", "evaluate_registered", "registered_spec", "validate_registered_spec",
]
