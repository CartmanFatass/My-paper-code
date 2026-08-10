from __future__ import annotations

from dataclasses import replace
import io
import inspect
import json
from pathlib import Path

import pytest

from experiments.candidates.recct_lite import (
    common_one_port_update_bank_noninterference as a3,
)
from scripts import run_recct_a3_common_one_port_update_bank_noninterference as runner


@pytest.fixture
def technical_pair() -> a3.ProspectiveOrientationPair:
    return runner.build_technical_pair()


@pytest.fixture(scope="module")
def technical_result() -> a3.A3Result:
    # This is a direction-local deterministic implementation fixture, not the
    # registered one-shot audit invocation or a published result.
    result = a3.run_common_bank_audit((runner.build_technical_pair(),))
    a3.validate_a3_result(result)
    return result


def test_technical_preflight_selects_structurally_before_opening_credit(
    technical_pair: a3.ProspectiveOrientationPair,
) -> None:
    selected, receipt = a3.select_first_structural_pair((technical_pair,))
    assert selected is technical_pair
    assert receipt.selected_key == min(receipt.ordering_keys)
    assert receipt.prohibited_value_reads == 0
    assert selected.plus.credit_source.content_open_count == 0
    assert selected.minus.credit_source.content_open_count == 0
    assert receipt.credit_content_open_counts_before_selection == (0,)
    assert receipt.credit_content_open_counts_after_selection == (0,)
    assert receipt.credit_content_decode_counts_before_selection == (0,)
    assert receipt.credit_content_decode_counts_after_selection == (0,)
    assert receipt.manifest_access_counts_before_selection == (0,)
    assert receipt.manifest_access_counts_after_selection == (2,)
    fixture = runner._technical_fixture_receipt(runner.build_technical_pair())
    assert fixture["technical_fixture_only"] is True
    assert fixture["claim_bearing_calls"] == 0
    assert fixture["credit_open_calls"] == 0
    assert fixture["credit_content_decode_calls"] == 0
    assert len(set(fixture["capsule_digests"])) == 2


def test_exact_common_bank_fixture_preserves_every_frozen_cap_and_boundary(
    technical_result: a3.A3Result,
) -> None:
    assert technical_result.branch == a3.A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS
    assert technical_result.first_failure is None
    assert all(technical_result.checks.values())
    assert len(technical_result.call_ledgers) == 8
    assert [
        (row["orientation"], row["port"], row["stored_or_recomputed"])
        for row in technical_result.call_ledgers
    ] == [
        ("PLUS", "LR", "STORED"),
        ("PLUS", "RL", "STORED"),
        ("MINUS", "LR", "STORED"),
        ("MINUS", "RL", "STORED"),
        ("MINUS", "RL", "RECOMPUTED"),
        ("MINUS", "LR", "RECOMPUTED"),
        ("PLUS", "RL", "RECOMPUTED"),
        ("PLUS", "LR", "RECOMPUTED"),
    ]
    assert [row["mask"] for row in technical_result.call_ledgers] == [
        "10", "01", "10", "01", "01", "10", "01", "10"
    ]
    assert all(row["active_port_count"] == 1 for row in technical_result.call_ledgers)
    assert all(row["clip_threshold"] is None for row in technical_result.call_ledgers)
    assert all(row["clip_coefficient"] == 1.0 for row in technical_result.call_ledgers)
    assert all(not row["clip_event"] for row in technical_result.call_ledgers)
    assert all(row["componentwise_bitwise_equal"] for row in technical_result.cell_equalities)
    assert technical_result.bank["sealed_cell_count"] == 4
    assert technical_result.bank["hidden_from_selectors"] is True
    assert len(technical_result.selector_records) == 6
    assert len(technical_result.reverse_selector_records) == 6
    assert len(technical_result.sentinel_records) == 36
    assert all(row["passed"] for row in technical_result.sentinel_records)
    assert technical_result.counts["learner_backward_shadow_calls"] == 8
    assert technical_result.counts["optimizer_transition_shadow_calls"] == 8
    assert technical_result.counts["00_or_11_shadow_calls"] == 0
    for key in (
        "environment_episodes",
        "environment_transitions",
        "policy_calls",
        "trainer_calls",
        "evaluation_calls",
        "committed_live_updates",
        "retries_sweeps_rescues_replacement_capsules",
        "pool_units",
    ):
        assert technical_result.counts[key] == 0


def test_selector_interface_is_narrow_and_forbidden_access_fails_closed() -> None:
    assert tuple(inspect.signature(a3.signed_directed).parameters) == ("view",)
    assert tuple(inspect.signature(a3.sign_destroyed).parameters) == ("view",)
    assert tuple(inspect.signature(a3.balanced_direction_blind).parameters) == ("view",)
    view = a3.AccessTrapSelectorView((1.0,) * 4, (0.0,) * 4, "LR")
    with pytest.raises(PermissionError, match="forbidden field"):
        getattr(view, "bank_digest")
    assert view.forbidden_attempts == ["bank_digest"]
    blind = a3.AccessTrapSelectorView((9.0,) * 4, (-9.0,) * 4, "RL")
    assert a3.balanced_direction_blind(blind) == "RL"
    assert blind.accesses == ["tie"]


def test_mutated_a1_binding_and_involution_fail_before_shadow_calls(
    technical_pair: a3.ProspectiveOrientationPair,
) -> None:
    bad_binding = replace(a3.A1Binding(), source_commit="0" * 40)
    binding_result = a3.run_common_bank_audit(
        (technical_pair,), a1_binding=bad_binding
    )
    assert (
        binding_result.branch
        == a3.A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE
    )
    assert binding_result.counts["learner_backward_shadow_calls"] == 0

    broken_minus = replace(technical_pair.minus, lr_role=("LEFT", "RIGHT"))
    bad_pair = replace(technical_pair, minus=broken_minus)
    pair_result = a3.run_common_bank_audit((bad_pair,))
    assert (
        pair_result.branch
        == a3.A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE
    )
    assert pair_result.counts["learner_backward_shadow_calls"] == 0

    foreign_handle_plus = replace(
        technical_pair.plus, lr_handle=technical_pair.minus.lr_handle
    )
    handle_result = a3.run_common_bank_audit(
        (replace(technical_pair, plus=foreign_handle_plus),)
    )
    assert (
        handle_result.branch
        == a3.A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE
    )
    assert handle_result.counts["learner_backward_shadow_calls"] == 0

    swapped_plus = replace(
        technical_pair.plus,
        lr_handle=technical_pair.plus.rl_handle,
        rl_handle=technical_pair.plus.lr_handle,
        lr_role=technical_pair.plus.rl_role,
        rl_role=technical_pair.plus.lr_role,
    )
    swapped_minus = replace(
        technical_pair.minus,
        lr_handle=technical_pair.minus.rl_handle,
        rl_handle=technical_pair.minus.lr_handle,
        lr_role=technical_pair.minus.rl_role,
        rl_role=technical_pair.minus.lr_role,
    )
    coordinated_result = a3.run_common_bank_audit(
        (replace(technical_pair, plus=swapped_plus, minus=swapped_minus),)
    )
    assert coordinated_result.branch == (
        a3.A3_A1_AUTHENTICATED_PORT_VERSION_ROLE_OR_MASK_BINDING_FAILURE
    )
    assert coordinated_result.counts["learner_backward_shadow_calls"] == 0


def test_credit_fixture_rejects_misordered_or_unbound_source(
    technical_pair: a3.ProspectiveOrientationPair,
) -> None:
    rows = runner._credit_rows("PLUS")
    lineage = technical_pair.plus.credit_source.lineage
    with pytest.raises(ValueError, match="exact ordered"):
        a3.SealedCreditSource.from_technical_observations(
            technical_pair.plus.capsule.digest,
            tuple(reversed(rows)),
            lineage,
        )
    bad = a3.SealedCreditSource.from_technical_observations(
        "not-the-capsule", rows, lineage
    )
    bad_plus = replace(technical_pair.plus, credit_source=bad)
    result = a3.run_common_bank_audit((replace(technical_pair, plus=bad_plus),))
    assert (
        result.branch
        == a3.A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE
    )
    assert result.counts["learner_backward_shadow_calls"] == 0

    tampered = a3.SealedCreditSource.from_technical_observations(
        technical_pair.plus.capsule.digest, rows, lineage
    )
    object.__setattr__(
        tampered,
        "_SealedCreditSource__encoded_content",
        b'{"tampered":true}',
    )
    tampered_plus = replace(technical_pair.plus, credit_source=tampered)
    selected, receipt = a3.select_first_structural_pair(
        (replace(technical_pair, plus=tampered_plus),)
    )
    assert selected.plus.credit_source.content_open_count == 0
    assert selected.plus.credit_source.content_decode_count == 0
    assert receipt.prohibited_value_reads == 0
    tampered_result = a3.run_common_bank_audit(
        (replace(technical_pair, plus=tampered_plus),)
    )
    assert (
        tampered_result.branch
        == a3.A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE
    )
    assert tampered_result.pair_selection[
        "credit_content_decode_counts_after_selection"
    ] == [0]
    pair_frozen = next(
        row for row in tampered_result.activity_events if row["event"] == "PAIR_FROZEN"
    )
    assert pair_frozen["credit_content_decode_counts"] == (0, 0)


def test_result_validator_rejects_identity_count_and_evidence_mutations(
    technical_result: a3.A3Result,
) -> None:
    serialized = json.loads(technical_result.to_bytes())
    assert serialized["branch"] == a3.A3_FACTORIZED_ONE_PORT_CONSTRUCTION_PASS
    assert len(serialized["call_ledgers"]) == 8
    with pytest.raises(ValueError, match="identity"):
        a3.validate_a3_result(replace(technical_result, treatment_id="wrong"))
    mutated_counts = dict(technical_result.counts)
    mutated_counts["committed_live_updates"] = 1
    with pytest.raises(ValueError, match="count|complete evidence"):
        a3.validate_a3_result(replace(technical_result, counts=mutated_counts))
    with pytest.raises(ValueError, match="rederive|complete evidence"):
        a3.validate_a3_result(replace(technical_result, sentinel_records=()))


def test_sentinel_manifest_has_exact_formula_ties_swaps_and_sign_invariance() -> None:
    records = a3.run_sentinel_manifest()
    by_key = {(row.case_id, row.selector): row for row in records}
    assert len(records) == 36
    assert by_key[("S01_BASE", "SIGN_DESTROYED")].output == by_key[
        ("S02_GLOBAL_NEGATION", "SIGN_DESTROYED")
    ].output
    assert by_key[("S01_BASE", "SIGNED_DIRECTED")].output == "LR"
    assert by_key[("S04_CANDIDATE_SWAP", "SIGNED_DIRECTED")].output == "RL"
    assert by_key[("S05_BOTH_TIE_LR", "SIGNED_DIRECTED")].output == "LR"
    assert by_key[("S06_BOTH_TIE_RL", "SIGNED_DIRECTED")].output == "RL"
    assert by_key[("S09_ABSOLUTE_TIE_LR", "SIGN_DESTROYED")].output == "LR"
    assert by_key[("S10_ABSOLUTE_TIE_RL", "SIGN_DESTROYED")].output == "RL"
    assert by_key[("S11_ACCESS_TRAP_ONE", "BALANCED_DIRECTION_BLIND")].output == "LR"
    assert by_key[("S12_ACCESS_TRAP_TWO", "BALANCED_DIRECTION_BLIND")].output == "LR"
    assert (
        by_key[("S11_ACCESS_TRAP_ONE", "SIGNED_DIRECTED")].forbidden_payload_digest
        != by_key[("S12_ACCESS_TRAP_TWO", "SIGNED_DIRECTED")].forbidden_payload_digest
    )
    assert all(row.passed for row in records)


def test_mutated_recomputation_is_rejected_by_componentwise_bank_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = a3.a1.DirectedEdgeMaskedUpdate
    calls = 0

    def altered_recomputation(*args, **kwargs):
        nonlocal calls
        calls += 1
        receipt = original(*args, **kwargs)
        if calls == 5:
            return replace(receipt, loss=receipt.loss + 1.0)
        return receipt

    monkeypatch.setattr(a3.a1, "DirectedEdgeMaskedUpdate", altered_recomputation)
    result = a3.run_common_bank_audit((runner.build_technical_pair(),))
    assert calls == 8
    assert (
        result.branch
        == a3.A3_BANK_COMPONENTWISE_RECOMPUTATION_IMMUTABILITY_OR_CALL_LEDGER_FAILURE
    )
    assert "componentwise equality" in (result.first_failure or "")
    assert len(result.call_ledgers) == 8
    assert len(result.cell_equalities) == 4
    assert result.counts["learner_backward_shadow_calls"] == 8
    assert result.counts["optimizer_transition_shadow_calls"] == 8
    assert result.counts["verified_stored_cells"] == 3
    a3.validate_a3_result(result)


def test_midstream_call_failure_retains_partial_activity_and_ledgers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = a3.a1.DirectedEdgeMaskedUpdate
    calls = 0

    def fail_fifth(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 5:
            raise RuntimeError("injected fifth-call failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(a3.a1, "DirectedEdgeMaskedUpdate", fail_fifth)
    result = a3.run_common_bank_audit((runner.build_technical_pair(),))
    assert result.branch == (
        a3.A3_BANK_COMPONENTWISE_RECOMPUTATION_IMMUTABILITY_OR_CALL_LEDGER_FAILURE
    )
    assert result.counts["learner_backward_shadow_calls"] == 5
    assert result.counts["optimizer_transition_shadow_calls"] == 4
    assert result.counts["indeterminate_optimizer_transition_attempts"] == 1
    assert len(result.call_ledgers) == 4
    assert result.activity_events[-1]["status"] == "FAILED_INDETERMINATE"
    a3.validate_a3_result(result)


def test_runner_refuses_existing_output_before_building_claim_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = Path("already-present.json")

    def forbidden_build():
        raise AssertionError("claim fixture must not be built for an occupied output")

    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)

    def occupied_open(self, mode, *args, **kwargs):
        assert self == output
        assert mode == "xb"
        raise FileExistsError("reserved output exists")

    monkeypatch.setattr(Path, "open", occupied_open)
    monkeypatch.setattr(runner, "build_registered_pair", forbidden_build)
    with pytest.raises(FileExistsError):
        runner.main(["--output", str(output)])


def test_registered_runner_without_existing_source_dto_fails_provenance_pre_shadow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = Path("new-result.json")

    class RetainedSink(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    sink = RetainedSink()
    registered_source = inspect.getsource(runner.build_registered_pair)
    loader_source = inspect.getsource(runner._load_registered_credit_sources)
    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(Path, "open", lambda self, mode: sink)

    def forbidden(*args, **kwargs):
        raise AssertionError("registered pair/A1 binding must not run without a DTO")

    monkeypatch.setattr(runner, "build_registered_pair", forbidden)
    monkeypatch.setattr(runner, "_validate_public_a1_result", forbidden)
    assert runner.main(["--output", str(output)]) == 2
    payload = json.loads(sink.getvalue())
    assert payload["branch"] == (
        a3.A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE
    )
    assert payload["counts"]["named_audits"] == 1
    assert payload["counts"]["learner_backward_shadow_calls"] == 0
    assert payload["call_ledgers"] == []
    assert "_credit_rows" not in registered_source
    assert "encoded_content_base64" in loader_source
    assert '"observations" in row' in loader_source
    assert "CreditObservation(" not in loader_source
    assert "detached_predictions" not in loader_source
    assert "observed_four_step_team_rewards" not in loader_source
