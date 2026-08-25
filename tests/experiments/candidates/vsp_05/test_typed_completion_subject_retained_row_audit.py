from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from experiments.candidates.vsp_05 import typed_completion_subject_retained_row_audit as audit_module
from experiments.candidates.vsp_05.typed_completion_subject_retained_row_audit import (
    ContractViolation,
    SourceBinding,
    audit_retained_rows,
    load_bound_input,
    run_registered_audit,
    validate_audit_result,
    validate_retained_population,
    write_result_once,
)


def _row(
    identity: str,
    *,
    i: int | None,
    q: int,
    i_gate: bool = False,
    i_truth: bool = False,
    q_gate: bool = False,
    q_truth: bool = False,
    lifecycle_key: str | None = None,
    event_rank: int = 1,
    step: int = 0,
) -> dict:
    classifications = {
        "0": {"gate": False, "strict_truth": False},
        "1": {"gate": False, "strict_truth": False},
        "2": {"gate": False, "strict_truth": False},
    }
    if i is not None:
        classifications[str(i)] = {"gate": i_gate, "strict_truth": i_truth}
    classifications[str(q)] = {"gate": q_gate, "strict_truth": q_truth}
    incumbent_present = i is not None
    different = incumbent_present and q != i
    return {
        "real_frontier_id": identity,
        "capture_boundary": "POST_MEMBERSHIP_PRE_POLICY",
        "cell": "REFERENCE",
        "task_seed": 68101,
        "episode_index": 0,
        "episode_id": 20000000,
        "environment_step": step,
        "physical_time": step,
        "completed_primitive_transitions_at_capture": step,
        "lifecycle_key": lifecycle_key or identity,
        "event_rank": event_rank,
        "lifecycle_category": "JOIN" if i is None else "SURVIVOR",
        "committed_record_present": True,
        "incumbent_present": incumbent_present,
        "incumbent_skill": i,
        "actual_proposal": q,
        "different_successor": different,
        "actual_proposal_gate": classifications[str(q)]["gate"],
        "actual_proposal_strict_truth": classifications[str(q)]["strict_truth"],
        "all_skill_classification": classifications,
        "complete_mask": {
            "incumbent_present": incumbent_present,
            "different_successor": different,
            "actual_proposal_gate": classifications[str(q)]["gate"],
            "truth_actual_proposal": classifications[str(q)]["strict_truth"],
        },
        "real_reachable_evidence": True,
    }


def _raw(rows: list[dict]) -> dict:
    return {
        "real_frontier_rows": rows,
        # Deliberately poisonous bookkeeping: the audit must never consume it.
        "static_hypothetical_incumbent_rows": [
            {"eligible_if_incumbent": True, "proposal_strict_truth": True}
            for _ in range(11)
        ],
    }


def _audit(rows: list[dict]) -> dict:
    return audit_retained_rows(
        _raw(rows),
        source_binding=SourceBinding("fixture.json", "f" * 64, 123),
        expected_rows=len(rows),
        strict_accepted_identity=False,
    )


def _strict_validator_fixture() -> dict:
    """Promote a tiny row fixture into a self-consistent accepted-size receipt."""

    result = _audit([
        _row("positive", i=2, q=0, i_gate=True, i_truth=True, lifecycle_key="epoch"),
        _row(
            "alias", i=2, q=1, i_gate=True, i_truth=False,
            lifecycle_key="epoch", event_rank=2, step=1,
        ),
    ])
    counts = {
        "complete_population": 15_971,
        "eligible": 13_379,
        "target_positive": 12_939,
        "target_typed_alias": 217,
        "target_gate_negative": 223,
        "sham_positive": 0,
        "sham_typed_alias": 141,
        "sham_gate_negative": 13_238,
        "ineligible": 2_592,
        "ineligible_join": 2_592,
    }
    result["source_binding"] = {
        "path": str(audit_module.EXPECTED_INPUT_PATH),
        "sha256": audit_module.EXPECTED_INPUT_SHA256,
        "bytes_read": 123,
        "source_commit": audit_module.EXPECTED_SOURCE_COMMIT,
        "accepted_result_commit": audit_module.EXPECTED_RESULT_COMMIT,
        "real_rows_read": audit_module.EXPECTED_REAL_ROWS,
        "static_hypothetical_rows_used_as_reachable_evidence": 0,
    }
    result["descriptive_counts"] = counts
    result["expected_count_receipt"] = {
        "accepted_expectation_applied": True,
        "expected": audit_module.EXPECTED_DESCRIPTIVE_COUNTS,
        "finite_categorical_reduction_observed_after_epoch_derivation": {
            "group_count": 2,
            "mixed_group_count": 1,
        },
        "matched": True,
        "failures": [],
        "q_subject_alias_141_preserved_not_relabelled": True,
    }

    target_totals = {
        "INELIGIBLE": counts["ineligible"],
        "TARGET_GATE_NEGATIVE": counts["target_gate_negative"],
        "TARGET_POSITIVE": counts["target_positive"],
        "TARGET_TYPED_ALIAS": counts["target_typed_alias"],
    }
    sham_totals = {
        "INELIGIBLE": counts["ineligible"],
        "SHAM_GATE_NEGATIVE": counts["sham_gate_negative"],
        "SHAM_POSITIVE": counts["sham_positive"],
        "SHAM_TYPED_ALIAS": counts["sham_typed_alias"],
    }

    def marginal(fields: tuple[str, ...], domain: tuple[tuple[object, ...], ...]) -> list[dict]:
        table = []
        for index, values in enumerate(domain):
            populated = index == 0
            table.append({
                **dict(zip(fields, values)),
                "rows": counts["complete_population"] if populated else 0,
                "target_classes": target_totals if populated else {
                    name: 0 for name in audit_module.TARGET_CLASSES
                },
                "sham_classes": sham_totals if populated else {
                    name: 0 for name in audit_module.SHAM_CLASSES
                },
            })
        return table

    remaining_target = dict(target_totals)
    remaining_sham = dict(sham_totals)
    joint = []
    for target in audit_module.TARGET_CLASSES:
        for sham in audit_module.SHAM_CLASSES:
            cell = min(remaining_target[target], remaining_sham[sham])
            remaining_target[target] -= cell
            remaining_sham[sham] -= cell
            joint.append({"target_class": target, "sham_class": sham, "count": cell})
    lifecycle = [
        {
            "lifecycle_category": "JOIN",
            "rows": counts["ineligible_join"],
            "target_classes": {
                name: counts["ineligible_join"] if name == "INELIGIBLE" else 0
                for name in audit_module.TARGET_CLASSES
            },
            "sham_classes": {
                name: counts["ineligible_join"] if name == "INELIGIBLE" else 0
                for name in audit_module.SHAM_CLASSES
            },
        },
        {
            "lifecycle_category": "REJOIN",
            "rows": counts["eligible"],
            "target_classes": {
                name: value if name != "INELIGIBLE" else 0
                for name, value in target_totals.items()
            },
            "sham_classes": {
                name: value if name != "INELIGIBLE" else 0
                for name, value in sham_totals.items()
            },
        },
        {
            "lifecycle_category": "SURVIVOR",
            "rows": 0,
            "target_classes": {name: 0 for name in audit_module.TARGET_CLASSES},
            "sham_classes": {name: 0 for name in audit_module.SHAM_CLASSES},
        },
    ]
    result["zero_bearing_tables"] = {
        "by_cell": marginal(("cell",), tuple((x,) for x in audit_module.CELLS)),
        "by_seed": marginal(("task_seed",), tuple((x,) for x in audit_module.TASK_SEEDS)),
        "by_cell_seed": marginal(
            ("cell", "task_seed"),
            tuple((cell, seed) for cell in audit_module.CELLS for seed in audit_module.TASK_SEEDS),
        ),
        "by_lifecycle_category": lifecycle,
        "by_incumbent_i": marginal(("incumbent_skill",), ((None,), (0,), (1,), (2,))),
        "by_proposal_q": marginal(
            ("actual_proposal",), tuple((x,) for x in audit_module.SKILLS),
        ),
        "joint_target_sham_class": joint,
    }
    result["target_sham_partitions_identical"] = False

    positive_alias_counts = {
        "INELIGIBLE": 0,
        "TARGET_GATE_NEGATIVE": 0,
        "TARGET_POSITIVE": counts["target_positive"],
        "TARGET_TYPED_ALIAS": counts["target_typed_alias"],
    }
    gate_negative_counts = {
        "INELIGIBLE": 0,
        "TARGET_GATE_NEGATIVE": counts["target_gate_negative"],
        "TARGET_POSITIVE": 0,
        "TARGET_TYPED_ALIAS": 0,
    }
    canonical_rows = [
        {
            "i": 2, "q": 0, "current_membership_category": "SURVIVOR", "D": True,
            "G_i": True, "gate_derived_completion_latch": True,
            "gate_derived_pending_q": 0, "controller_output": "RETAIN_I_QUEUE_Q_LATCHED",
            "target_classes": positive_alias_counts, "mixed_target_partition": True,
            "row_identity_witnesses": ["positive", "alias"],
        },
        {
            "i": 2, "q": 1, "current_membership_category": "SURVIVOR", "D": True,
            "G_i": False, "gate_derived_completion_latch": True,
            "gate_derived_pending_q": 0, "controller_output": "RETAIN_I_QUEUE_Q_LATCHED",
            "target_classes": gate_negative_counts, "mixed_target_partition": False,
            "row_identity_witnesses": ["negative"],
        },
    ]
    result["canonical_gate_controller_null"]["output_partition"] = canonical_rows
    result["canonical_gate_controller_null"]["reproduces_complete_target_partition"] = False
    groups = []
    for canonical_row in canonical_rows:
        groups.append({
            "i": canonical_row["i"],
            "q": canonical_row["q"],
            "current_membership_category": canonical_row["current_membership_category"],
            "D": canonical_row["D"],
            "G_i": canonical_row["G_i"],
            "G_q": False,
            "gate_derived_target_latch": canonical_row["gate_derived_completion_latch"],
            "gate_derived_target_pending_q": canonical_row["gate_derived_pending_q"],
            "gate_derived_sham_latch": False,
            "gate_derived_sham_pending_q": None,
            "rows": sum(canonical_row["target_classes"].values()),
            "target_classes": canonical_row["target_classes"],
            "mixed_target_partition": canonical_row["mixed_target_partition"],
            "row_identity_witnesses": canonical_row["row_identity_witnesses"],
        })
    reduction = result["finite_categorical_reduction"]
    reduction["groups"] = groups
    reduction["group_count"] = 2
    reduction["mixed_group_count"] = 1
    reduction["reproduces_complete_target_partition"] = False
    validate_audit_result(result)
    return result


def test_same_subject_labels_recompute_i_and_q_without_relabelling_q_alias() -> None:
    rows = [
        _row("join", i=None, q=2, q_gate=True, q_truth=True),
        _row("target-positive", i=2, q=0, i_gate=True, i_truth=True),
        _row("target-alias", i=2, q=0, i_gate=True, i_truth=False),
        _row("q-only-alias", i=2, q=0, i_gate=False, i_truth=False, q_gate=True),
    ]
    result = _audit(rows)
    assert result["descriptive_counts"] == {
        "complete_population": 4,
        "eligible": 3,
        "target_positive": 1,
        "target_typed_alias": 1,
        "target_gate_negative": 1,
        "sham_positive": 0,
        "sham_typed_alias": 1,
        "sham_gate_negative": 2,
        "ineligible": 1,
        "ineligible_join": 1,
    }
    assert result["label_definition"]["q_subject_aliases_relabelled_as_i_subject"] == 0
    assert result["source_binding"]["static_hypothetical_rows_used_as_reachable_evidence"] == 0


def test_categorical_reduction_excludes_truth_and_retains_mixed_witnesses() -> None:
    result = _audit([
        _row("positive", i=2, q=0, i_gate=True, i_truth=True, lifecycle_key="a"),
        _row("alias", i=2, q=0, i_gate=True, i_truth=False, lifecycle_key="b"),
    ])
    reduction = result["finite_categorical_reduction"]
    assert "strict truth" in reduction["excluded_fields"]
    assert reduction["group_count"] == 1
    assert reduction["mixed_group_count"] == 1
    assert reduction["reproduces_complete_target_partition"] is False
    assert set(reduction["groups"][0]["row_identity_witnesses"]) == {"positive", "alias"}


def test_nulls_retain_first_pending_q_when_q_changes_within_incumbent_epoch() -> None:
    result = _audit([
        _row(
            "first-q", i=2, q=0, i_gate=True, i_truth=True, q_gate=True,
            lifecycle_key="same-epoch", event_rank=1, step=0,
        ),
        _row(
            "changed-q", i=2, q=1, i_gate=False, i_truth=False, q_gate=True,
            lifecycle_key="same-epoch", event_rank=2, step=1,
        ),
    ])
    canonical_changed = next(
        row for row in result["canonical_gate_controller_null"]["output_partition"]
        if row["q"] == 1
    )
    assert canonical_changed["G_i"] is False
    assert canonical_changed["gate_derived_completion_latch"] is True
    assert canonical_changed["gate_derived_pending_q"] == 0
    categorical_changed = next(
        row for row in result["finite_categorical_reduction"]["groups"]
        if row["q"] == 1
    )
    assert categorical_changed["gate_derived_target_pending_q"] == 0
    assert categorical_changed["gate_derived_sham_pending_q"] == 0
    observed = result["expected_count_receipt"][
        "finite_categorical_reduction_observed_after_epoch_derivation"
    ]
    assert observed == {
        "group_count": result["finite_categorical_reduction"]["group_count"],
        "mixed_group_count": result["finite_categorical_reduction"]["mixed_group_count"],
    }


def test_missing_retained_behavior_objects_fail_closed_before_passive_branch() -> None:
    result = _audit([
        _row("positive", i=2, q=0, i_gate=True, i_truth=True),
        _row("alias", i=2, q=0, i_gate=True, i_truth=False),
    ])
    assert result["terminal_branch"] == "A3_INVALID_CONTRACT"
    missing = result["behavioral_addressability"]["missing_object_witnesses"]
    assert set(missing) == {
        "observed_pending_q",
        "observed_completion_latch",
        "actual_commit_to_q",
        "post_commit_incumbent_q",
        "first_supplied_executor_q_input_and_primitive",
        "necessary_latch_input_witness",
    }
    assert result["behavioral_addressability"]["derived_latch_is_observed_witness"] is False


def test_strict_truth_without_same_subject_gate_is_rejected() -> None:
    bad = _row("bad", i=2, q=0, i_gate=True, i_truth=True)
    bad["all_skill_classification"]["2"]["gate"] = False
    with pytest.raises(ContractViolation, match="strict truth must imply"):
        validate_retained_population(
            _raw([bad]), expected_rows=1, strict_accepted_identity=False
        )


def test_temporal_order_and_event_rank_fail_closed() -> None:
    rows = [
        _row("first", i=2, q=0, lifecycle_key="key0", event_rank=1, step=4),
        _row("second", i=2, q=0, lifecycle_key="key0", event_rank=3, step=5),
    ]
    with pytest.raises(ContractViolation, match="event rank"):
        validate_retained_population(
            _raw(rows), expected_rows=2, strict_accepted_identity=False
        )


def test_future_and_outcome_fields_do_not_change_labels() -> None:
    baseline = _row("row", i=2, q=0, i_gate=True, i_truth=True)
    altered = deepcopy(baseline)
    altered["reward"] = 10**9
    altered["future_outcome"] = "FAVORABLE"
    altered["future_action"] = {"skill": 2}
    assert _audit([baseline])["descriptive_counts"] == _audit([altered])["descriptive_counts"]
    assert _audit([altered])["label_definition"]["future_or_outcome_fields_used"] == []


def test_source_loader_binds_bytes_before_json_and_rejects_hash_drift(tmp_path: Path) -> None:
    path = tmp_path / "fixture.json"
    encoded = json.dumps(_raw([]), sort_keys=True).encode("utf-8")
    path.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    loaded, binding = load_bound_input(
        path, expected_sha256=digest, enforce_registered_path=False
    )
    assert loaded == _raw([])
    assert binding.sha256 == digest
    with pytest.raises(ContractViolation, match="SHA mismatch"):
        load_bound_input(
            path, expected_sha256="0" * 64, enforce_registered_path=False
        )


def test_result_validator_rejects_hidden_activity_and_writer_is_one_shot(tmp_path: Path) -> None:
    result = _audit([_row("row", i=2, q=0, i_gate=True, i_truth=True)])
    bad = deepcopy(result)
    bad["audit_activity"]["executor_calls"] = 1
    with pytest.raises(ContractViolation, match="executor_calls"):
        validate_audit_result(bad, expected_rows=1, strict_accepted_identity=False)
    output = tmp_path / "result.json"
    write_result_once(output, result)
    assert json.loads(output.read_text(encoding="utf-8"))["terminal_branch"] == "A3_INVALID_CONTRACT"
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        write_result_once(output, result)


def test_unavailable_registered_input_returns_invalid_contract_without_recovery(tmp_path: Path) -> None:
    result = run_registered_audit(tmp_path / "missing" / "raw_result.json")
    assert result["terminal_branch"] == "A3_INVALID_CONTRACT"
    assert result["audit_activity"]["retries_or_recoveries"] == 0
    assert result["audit_activity"]["new_trace_passes"] == 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("path", "logs/wrong/raw_result.json", "source path"),
        ("sha256", "0" * 64, "source SHA"),
        ("real_rows_read", 15_970, "retained-row count"),
    ],
)
def test_result_validator_rejects_source_binding_mutations(
    field: str, value: object, message: str
) -> None:
    bad = _strict_validator_fixture()
    bad["source_binding"][field] = value
    with pytest.raises(ContractViolation, match=message):
        validate_audit_result(bad)


@pytest.mark.parametrize(
    ("receipt", "field", "message"),
    [
        ("same_subject_truth_gate_integrity", "all_strict_truth_implies_same_subject_gate", "truth/gate"),
        ("same_subject_truth_gate_integrity", "fresh_i_subject_labels_recomputed_from_all_skill_classification", "truth/gate"),
        ("derived_bookkeeping", "idempotent_within_epoch", "idempotence"),
        ("behavioral_addressability", "derived_latch_is_observed_witness", "derived latch"),
    ],
)
def test_result_validator_rejects_integrity_derived_and_observed_flag_mutations(
    receipt: str, field: str, message: str
) -> None:
    bad = _strict_validator_fixture()
    bad[receipt][field] = False if bad[receipt][field] is True else True
    with pytest.raises(ContractViolation, match=message):
        validate_audit_result(bad)


def test_result_validator_rejects_empty_zero_table_and_stale_null_count_receipt() -> None:
    empty = _strict_validator_fixture()
    empty["zero_bearing_tables"]["by_cell"] = []
    with pytest.raises(ContractViolation, match="domain size"):
        validate_audit_result(empty)

    stale = _strict_validator_fixture()
    stale["expected_count_receipt"][
        "finite_categorical_reduction_observed_after_epoch_derivation"
    ]["group_count"] += 1
    with pytest.raises(ContractViolation, match="post-derivation categorical count"):
        validate_audit_result(stale)


def test_result_validator_rejects_controller_text_and_pending_q_mutations() -> None:
    controller = _strict_validator_fixture()
    controller["canonical_gate_controller_null"]["controller"] += " mutated"
    with pytest.raises(ContractViolation, match="canonical controller text"):
        validate_audit_result(controller)

    canonical_pending = _strict_validator_fixture()
    canonical_pending["canonical_gate_controller_null"]["output_partition"][0][
        "gate_derived_pending_q"
    ] = 1
    with pytest.raises(ContractViolation, match="categorical-to-canonical projection fields"):
        validate_audit_result(canonical_pending)

    categorical_pending = _strict_validator_fixture()
    categorical_pending["finite_categorical_reduction"]["groups"][0][
        "gate_derived_target_pending_q"
    ] = 1
    with pytest.raises(ContractViolation, match="categorical-to-canonical projection fields"):
        validate_audit_result(categorical_pending)


def test_result_validator_reconciles_join_and_cell_seed_marginals() -> None:
    join_count = _strict_validator_fixture()
    join_count["descriptive_counts"]["ineligible_join"] = 0
    with pytest.raises(ContractViolation, match="JOIN lifecycle stratum"):
        validate_audit_result(join_count)

    moved_cell = _strict_validator_fixture()
    by_cell = moved_cell["zero_bearing_tables"]["by_cell"]
    for field in ("rows", "target_classes", "sham_classes"):
        by_cell[0][field], by_cell[1][field] = by_cell[1][field], by_cell[0][field]
    with pytest.raises(ContractViolation, match="by_cell does not reconcile"):
        validate_audit_result(moved_cell)


def test_result_validator_recomputes_precedence_with_contract_failure() -> None:
    bad = _strict_validator_fixture()
    bad["contract_failures"].append({"kind": "PROTECTED_MUTATION_WITNESS"})
    bad["terminal_branch"] = "A3_NO_TWO_SIDED_TARGET_SUPPORT"
    with pytest.raises(ContractViolation, match="terminal branch precedence"):
        validate_audit_result(bad)
