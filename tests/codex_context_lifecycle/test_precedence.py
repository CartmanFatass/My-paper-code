from tools.codex_context_lifecycle.models import ContextSourceKind, PrecedenceLayer
from tools.codex_context_lifecycle.precedence import (
    can_create_authority,
    can_create_state_transition,
    precedence_for_kind,
    source_effects,
)


def test_automatic_memory_is_lowest_and_hint_only():
    layer = precedence_for_kind(ContextSourceKind.AUTOMATIC_MEMORY)
    assert layer is PrecedenceLayer.P9_AUTOMATIC_MEMORY
    assert can_create_authority(layer) is False
    assert can_create_state_transition(layer) is False


def test_compaction_summary_cannot_override_typed_packet():
    assert precedence_for_kind(ContextSourceKind.COMPACTION_SUMMARY).rank > (
        precedence_for_kind(ContextSourceKind.TYPED_PACKET).rank
    )


def test_role_contract_outranks_plan_epoch():
    assert precedence_for_kind(ContextSourceKind.ROLE_CONTRACT).rank < (
        precedence_for_kind(ContextSourceKind.PLAN_EPOCH).rank
    )


def test_navigation_and_procedure_are_references_not_decisions():
    for kind in (ContextSourceKind.NAVIGATION, ContextSourceKind.PROCEDURE):
        layer = precedence_for_kind(kind)
        assert can_create_authority(layer) is False
        assert can_create_state_transition(layer) is False
        effects = source_effects(kind)
        assert effects["may_create_owner_decision"] is False
        assert effects["may_serve_as_retrieval_hint"] is True
