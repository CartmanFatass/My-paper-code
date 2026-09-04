from __future__ import annotations

import hashlib
from dataclasses import replace
import json

import pytest

from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.addressing import (
    B1_RUN,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_shared_tables import (
    B1SharedTableError,
    build_b1_shared_truth_tables,
)
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.host import (
    DynamicHost,
)


SPEC_SHA256 = "7" * 64


def test_shared_transition_rows_are_canonical_and_exactly_byte_recoverable() -> None:
    tape = DynamicHost(B1_RUN, 21101).build_motif(0)

    result = build_b1_shared_truth_tables(
        [tape],
        attempt_id="attempt-shared-table-test",
        literal_binding_spec_sha256=SPEC_SHA256,
    )

    assert set(result) == {
        "schema", "object_id", "literal_binding_spec_sha256", "run_name", "attempt_id",
        "shared_tape_transitions", "evaluator_decision_truth", "motif_twin_index",
        "support_signature_counts", "motif_pair_support_counts", "table_counts",
        "table_sha256",
    }
    assert result["table_sha256"]["shared_tape_transitions"] == hashlib.sha256(
        json.dumps(
            result["shared_tape_transitions"],
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()

    rows = result["shared_tape_transitions"]
    assert len(rows) == 152
    assert [(row["tape_id"], row["transition_index"]) for row in rows] == [
        (0, index) for index in range(152)
    ]
    assert rows[0] == {
        "run_order": 0,
        "seed": 21101,
        "split_order": 2,
        "object_id": "CBSC-OMRC-B01",
        "literal_binding_spec_sha256": SPEC_SHA256,
        "run_name": B1_RUN,
        "attempt_id": "attempt-shared-table-test",
        "split": "EVAL_MOTIF",
        "episode_id": 0,
        "tape_id": 0,
        "tape_sha256": "a665622a69ea07e5aa905eb39f2fa01accde00a931e29458217e762ce6c8378b",
        "motif_family": 0,
        "motif_receiver": 0,
        "motif_slot": 0,
        "transition_index": 0,
        "opportunity_id": -1,
        "event_order_position": 0,
        "event_kind": 1,
        "primitive_token_bytes": [
            1, 0, 255, 255, 255, 255, 57, 255, 255,
            255, 255, 255, 255, 255, 255, 0, 0,
        ],
        "primitive_token_sha256": hashlib.sha256(
            bytes.fromhex("0100ffffffff39ffffffffffffffff0000")
        ).hexdigest(),
    }
    recovered = b"".join(bytes(row["primitive_token_bytes"]) for row in rows)
    assert hashlib.sha256(recovered).hexdigest() == tape.primitive_digest


def test_evaluator_truth_rows_publish_full_state_predicates_ledgers_and_event_provenance() -> None:
    tape = DynamicHost(B1_RUN, 21101).build_motif(0)

    row = build_b1_shared_truth_tables(
        [tape],
        attempt_id="attempt-shared-table-test",
        literal_binding_spec_sha256=SPEC_SHA256,
    )["evaluator_decision_truth"][0]

    assert (row["run_order"], row["seed"], row["split_order"], row["tape_id"], row["opportunity_id"]) == (
        0,
        21101,
        2,
        0,
        0,
    )
    assert {name: row[name] for name in (
        "target_receiver", "presented_slot",
        "current_owner_0", "current_owner_1", "current_epoch_0", "current_epoch_1",
        "current_need_0", "current_need_1", "carrier_0_receiver", "carrier_1_receiver",
    )} == {
        "target_receiver": 0, "presented_slot": 0,
        "current_owner_0": 57, "current_owner_1": 54,
        "current_epoch_0": 35, "current_epoch_1": 44,
        "current_need_0": True, "current_need_1": True,
        "carrier_0_receiver": 0, "carrier_1_receiver": 1,
    }
    assert {name: row[name] for name in (
        "nonneutral_truth", "address_match_truth", "payload_source_match_truth",
        "content_match_truth", "owner_match_truth", "epoch_match_truth",
        "capability_match_truth", "overall_valid_truth",
    )} == {
        "nonneutral_truth": True, "address_match_truth": True,
        "payload_source_match_truth": True, "content_match_truth": True,
        "owner_match_truth": True, "epoch_match_truth": True,
        "capability_match_truth": True, "overall_valid_truth": True,
    }
    assert row["serve_total_value"] == {"numerator": 1, "denominator": 1}
    assert row["refresh_total_value"] == {"numerator": 3, "denominator": 5}
    assert row["safe_fallback_total_value"] == {"numerator": 1, "denominator": 5}
    assert row["oracle_action"] == 0
    assert row["oracle_value"] == {"numerator": 1, "denominator": 1}
    assert {name: row[name] for name in (
        "owner_event_realized", "owner_event_subject", "owner_event_position",
        "semantic_event_realized", "semantic_event_subject", "semantic_event_position",
        "capability_event_realized", "capability_event_carrier", "capability_event_position",
        "body_event_realized", "body_event_slot", "body_event_position",
        "presented_body_issue_opportunity", "presented_body_issue_event_position",
        "presented_body_age_opportunities", "last_target_owner_change_opportunity",
        "last_target_semantic_change_opportunity",
    )} == {
        "owner_event_realized": False, "owner_event_subject": None, "owner_event_position": 1,
        "semantic_event_realized": False, "semantic_event_subject": None, "semantic_event_position": 3,
        "capability_event_realized": True, "capability_event_carrier": 0, "capability_event_position": 2,
        "body_event_realized": True, "body_event_slot": 0, "body_event_position": 0,
        "presented_body_issue_opportunity": 0, "presented_body_issue_event_position": 0,
        "presented_body_age_opportunities": 0,
        "last_target_owner_change_opportunity": -1,
        "last_target_semantic_change_opportunity": -1,
    }


def test_motif_twin_index_and_support_counts_are_complete_mechanical_censuses() -> None:
    tape = DynamicHost(B1_RUN, 21101).build_motif(0)

    result = build_b1_shared_truth_tables(
        [tape],
        attempt_id="attempt-shared-table-test",
        literal_binding_spec_sha256=SPEC_SHA256,
    )

    motif_rows = result["motif_twin_index"]
    assert len(motif_rows) == 24
    assert motif_rows[0] == {
        "run_order": 0,
        "run_name": B1_RUN,
        "seed": 21101,
        "tape_id": 0,
        "motif_family": 0,
        "motif_receiver": 0,
        "motif_slot": 0,
        "pair_id": "21101:0:0",
        "member_role": "A",
        "member_tape_id": 0,
        "member_opportunity_id": 0,
        "counterpart_tape_id": 0,
        "counterpart_opportunity_id": 1,
        "intervention_family": "OWNER_CHANGE",
        "intervention_side": "A",
        "designated_diagnostic_member": True,
        "pair_complete": True,
    }
    assert motif_rows[1]["member_role"] == "B"
    assert motif_rows[1]["counterpart_opportunity_id"] == 0

    support_rows = result["support_signature_counts"]
    assert sum(row["support_count"] for row in support_rows) == 24
    assert {row["split_order"] for row in support_rows} == {2}
    assert all(set(row) == {
        "run_order", "run_name", "seed", "split_order", "split", "motif_family_or_null",
        "motif_side_or_null", "request_active", "access_gated",
        "presented_body_native_neutral", "address_match_truth",
        "payload_source_match_truth", "content_match_truth", "owner_match_truth",
        "epoch_match_truth", "capability_match_truth", "overall_valid_truth",
        "oracle_action", "presented_body_age_opportunities", "support_count",
    } for row in support_rows)

    pair_counts = result["motif_pair_support_counts"]
    assert len(pair_counts) == 8
    assert pair_counts[0] == {
        "run_order": 0,
        "run_name": B1_RUN,
        "seed": 21101,
        "motif_family": 0,
        "expected_pair_count": 48,
        "complete_pair_count": 12,
        "missing_pair_count": 36,
        "duplicate_member_count": 0,
    }
    assert pair_counts[7]["expected_pair_count"] == 12
    assert pair_counts[7]["complete_pair_count"] == 0
    assert pair_counts[7]["missing_pair_count"] == 12


@pytest.mark.parametrize(
    "mutation", ["summary", "duplicate", "nonfinite", "tampered_truth"]
)
def test_shared_tables_reject_noncanonical_duplicate_or_nonfinite_inputs(mutation: str) -> None:
    tape = DynamicHost(B1_RUN, 21101).build_motif(0)
    if mutation == "summary":
        tapes = [{"tape_sha256": tape.primitive_digest}]
    elif mutation == "duplicate":
        tapes = [tape, tape]
    elif mutation == "nonfinite":
        tapes = [replace(tape, identity=replace(tape.identity, seed=float("nan")))]
    else:
        truth = tape.evaluator().truth(0)
        tapes = [
            replace(
                tape,
                _decision_truth=(
                    replace(truth, designated_comparison=False),
                    *tuple(tape.evaluator().truth(index) for index in range(1, 24)),
                ),
            )
        ]

    with pytest.raises(B1SharedTableError):
        build_b1_shared_truth_tables(
            tapes,
            attempt_id="attempt-shared-table-test",
            literal_binding_spec_sha256=SPEC_SHA256,
        )


def test_complete_motif_panel_has_every_expected_pair_once() -> None:
    host = DynamicHost(B1_RUN, 21101)
    result = build_b1_shared_truth_tables(
        [host.build_motif(tape_id) for tape_id in range(32)],
        attempt_id="attempt-shared-table-test",
        literal_binding_spec_sha256=SPEC_SHA256,
    )

    assert len(result["evaluator_decision_truth"]) == 32 * 24
    assert len(result["motif_twin_index"]) == 7 * 4 * 24 + 4 * 6
    assert sum(row["support_count"] for row in result["support_signature_counts"]) == 32 * 24
    assert [
        (row["expected_pair_count"], row["complete_pair_count"], row["missing_pair_count"], row["duplicate_member_count"])
        for row in result["motif_pair_support_counts"]
    ] == [(48, 48, 0, 0)] * 7 + [(12, 12, 0, 0)]
