from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from experiments.candidates.vsp_05.lifecycle_phase_support_discrimination import (
    CONTROL_RAW_SHA256,
    FULL_CONFIG,
    KNOWN_CELL,
    KNOWN_EPISODE_ID,
    KNOWN_LIFECYCLE_KEY,
    KNOWN_TASK_SEED,
    MASK_FIELDS,
    NEAR_MISS_DOMAIN,
    SMOKE_CONFIG,
    TERMINAL_LABELS,
    TRUTH_SET_DOMAIN,
    _config_identity,
    _expected_configuration,
    _frozen_identity,
    _roster,
    _schedule_rows,
    _validate_equivalence_receipt,
    _validate_exact_raw_contract,
    _validate_raw,
    analyze_treatment,
    classify_terminal_label,
    evaluate_treatment,
    load_accepted_control,
    main,
    run_treatment_probe,
)
from experiments.candidates.vsp_05.support_map import (
    CELLS,
    FULL_TASK_SEEDS,
    OPPORTUNITY_CATEGORIES,
    make_clean_process_dynamic_roster_ledger,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _control_path() -> Path:
    configured = os.environ.get("HMASD_VSP05_A1_CONTROL")
    candidate = (
        Path(configured)
        if configured
        else PROJECT_ROOT
        / "logs"
        / "vsp05_a1_truth_reachability_1a09bccf_r1"
        / "raw_result.json"
    )
    if not candidate.is_file():
        pytest.skip("accepted A1 raw requires HMASD_VSP05_A1_CONTROL in a clean worktree")
    return candidate


@pytest.fixture(scope="module")
def accepted_control():
    return load_accepted_control(_control_path())


@pytest.fixture(scope="module")
def smoke_raw():
    return run_treatment_probe(
        SMOKE_CONFIG,
        control_path=_control_path(),
        code_revision="WORKTREE",
        run_id="VSP05_A2_FOCUSED_SMOKE",
    )


@pytest.fixture(scope="module")
def smoke_analysis(smoke_raw, accepted_control):
    return analyze_treatment(smoke_raw, accepted_control)


def test_registered_full_configuration_and_schedule_are_exact():
    assert FULL_CONFIG.counts() == {
        "cells": 6,
        "task_seeds": 3,
        "episodes": 432,
        "environment_transitions": 34_560,
    }
    assert FULL_CONFIG.cells == CELLS
    assert FULL_CONFIG.task_seeds == FULL_TASK_SEEDS == (68101, 68102, 68103)
    schedule = _schedule_rows(FULL_CONFIG)
    assert len(schedule) == 864
    assert len(
        {
            (row["cell"], row["task_seed"], row["episode_id"], row["lifecycle_key"])
            for row in schedule
        }
    ) == 864
    assert all(row["control_leave_time"] == 20 for row in schedule)
    assert all(row["treatment_leave_time"] == 19 for row in schedule)
    assert all(row["control_rejoin_time"] == row["treatment_rejoin_time"] == 40 for row in schedule)
    assert all(row["leave_shift"] == -1 for row in schedule)
    assert not any(row["other_membership_delta"] or row["event_collision"] for row in schedule)


def test_frozen_identity_binds_config_and_rejects_unfrozen_full_source():
    identity = _frozen_identity(
        FULL_CONFIG,
        code_revision="a" * 40,
        run_id="vsp05_a2_fixed_r1",
    )
    assert identity == {
        "source_revision": "a" * 40,
        "configuration_sha256": _config_identity(FULL_CONFIG),
        "run_id": "vsp05_a2_fixed_r1",
    }
    with pytest.raises(ValueError, match="40-hex"):
        _frozen_identity(FULL_CONFIG, code_revision="WORKTREE", run_id="bad")


def test_exact_accepted_control_binding_and_known_t19_lineage(accepted_control):
    assert accepted_control["_bound_sha256"] == CONTROL_RAW_SHA256
    ledger = make_clean_process_dynamic_roster_ledger(
        KNOWN_EPISODE_ID, master_seed=KNOWN_TASK_SEED
    )
    assert int(KNOWN_LIFECYCLE_KEY) in ledger.temporary_leave
    rows = [
        row
        for row in accepted_control["real_frontier_rows"]
        if row["cell"] == KNOWN_CELL
        and row["task_seed"] == KNOWN_TASK_SEED
        and row["episode_id"] == KNOWN_EPISODE_ID
        and row["environment_step"] == 19
        and row["lifecycle_key"] == KNOWN_LIFECYCLE_KEY
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["different_successor"] is True
    assert row["actual_proposal_gate"] is True
    assert row["actual_proposal_strict_truth"] is False


def test_cli_entrypoint_and_exact_82_transition_equivalence_smoke():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_vsp05_a2_lifecycle_phase_support.py",
            "--phase",
            "equivalence-smoke",
            "--control",
            str(_control_path()),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout.strip().splitlines()[-1])
    assert summary["artifact_kind"] == "VSP05_A2_EQUIVALENCE_SMOKE"
    assert summary["all_checks_passed"] is True
    assert "terminal_label" not in summary


def test_cli_acquisition_requires_explicit_config():
    with pytest.raises(ValueError, match="requires explicit --config"):
        main(["--phase", "probe", "--control", str(_control_path())])


def test_smoke_uses_real_runtime_and_only_the_declared_schedule_delta(smoke_raw):
    assert smoke_raw["actual_counts"] == {
        "cells": 1,
        "task_seeds": 1,
        "episodes": 1,
        "environment_transitions": 41,
    }
    assert smoke_raw["scientific_delta"] == {
        "control_leave_time": 20,
        "treatment_leave_time": 19,
        "rejoin_time": 40,
        "changed_fields": ["temporary_leave_physical_time"],
        "K_search": 0,
        "hypothetical_environment_transitions": 0,
    }
    assert smoke_raw["control_binding"]["sha256"] == CONTROL_RAW_SHA256
    assert smoke_raw["stage"] == "technical_validation"
    assert smoke_raw["evidence_level"] == "TECHNICAL_ONLY"
    assert smoke_raw["scientific_terminal_admitted"] is False
    assert smoke_raw["configuration"]["episode_namespace_unchanged"] is True
    assert smoke_raw["call_counts"]["environment_transition"] == 41
    assert smoke_raw["call_counts"]["supplied_executor"] == 41
    assert smoke_raw["call_counts"]["variable_roster_event_core_transaction"] == 41
    assert smoke_raw["call_counts"]["proposal_policy"] == len(smoke_raw["real_frontier_rows"])
    for name in ("learner", "trainer", "optimizer_update", "hypothetical_environment_transition"):
        assert smoke_raw["call_counts"][name] == 0


def test_lineage_audit_proves_skip_absence_and_no_rejoin_reset(smoke_raw):
    assert len(smoke_raw["schedule_delta_rows"]) == 2
    assert len(smoke_raw["lineage_runtime_audits"]) == 1
    audit = smoke_raw["lineage_runtime_audits"][0]
    assert set(audit["leave"]) == set(audit["rejoin"])
    for key, leave in audit["leave"].items():
        rejoin = audit["rejoin"][key]
        assert leave["active_steps"] == leave["primitive_actions_before_leave"] == 19
        assert rejoin["active_steps"] == 19
        assert rejoin["state_unchanged_while_absent"] is True
        assert rejoin["incumbent_not_reset"] is True
        assert rejoin["skipped_primitives_relative_to_control"] == 1
        assert rejoin["absent_transition_times"] == list(range(19, 40))


def test_complete_masks_and_zero_tables_are_retained(smoke_raw):
    rows = smoke_raw["real_frontier_rows"]
    assert rows
    assert all(set(row["complete_mask"]) == set(MASK_FIELDS) for row in rows)
    assert all(set(row["all_skill_classification"]) == {"0", "1", "2"} for row in rows)
    tables = smoke_raw["predicate_tables"]
    assert len(tables["complete_mask_histogram"]) == 256
    assert sum(row["count"] for row in tables["complete_mask_histogram"]) == len(rows)
    assert any(row["count"] == 0 for row in tables["complete_mask_histogram"])
    assert len(tables["by_semantic_near_miss"]) == len(NEAR_MISS_DOMAIN) == 64
    assert len(tables["by_truth_skill_set"]) == len(TRUTH_SET_DOMAIN) == 8
    assert len(tables["by_lifecycle_category"]) == len(OPPORTUNITY_CATEGORIES)


def test_smoke_analysis_has_exact_pairing_and_distinguishes_skips_from_proposals(smoke_analysis):
    assert smoke_analysis["artifact_kind"] == "VSP05_A2_TECHNICAL_SMOKE_ANALYSIS"
    assert smoke_analysis["stage"] == "technical_validation"
    assert smoke_analysis["evidence_level"] == "TECHNICAL_ONLY"
    assert smoke_analysis["scientific_terminal_admitted"] is False
    assert len(smoke_analysis["paired_t40_rejoin_rows"]) == 2
    receipt = smoke_analysis["technical_lineage_receipt"]
    assert receipt["primitive_skips"] == 2
    assert receipt["suppressed_control_t19_proposals"] == 0
    assert receipt["all_treatment_state_frozen_while_absent"] is True
    assert receipt["all_treatment_incumbents_preserved_at_rejoin"] is True
    forbidden = {
        "terminal_label",
        "historical_control_reuse_passed",
        "clean_two_sided_real_support_opened",
        "toy_route_must_park",
        "scientific_disposition",
        "decision_boundary",
    }
    assert forbidden.isdisjoint(smoke_analysis)
    for row in smoke_analysis["paired_t40_rejoin_rows"]:
        assert set(row) >= {
            "cell", "task_seed", "episode_id", "lifecycle_key", "control",
            "treatment", "state_delta", "incumbent_lineage_match",
            "incumbent_mismatch_due_to_suppression",
        }
        assert set(row["control"]) == set(row["treatment"]) == {
            "position", "velocity", "incumbent", "proposal", "truth_skill_set", "complete_mask"
        }


def test_evaluation_is_compact_but_preserves_decision_receipts(smoke_raw, accepted_control):
    receipt = evaluate_treatment(smoke_raw, accepted_control)
    assert receipt["artifact_kind"] == "VSP05_A2_TECHNICAL_SMOKE_EVALUATION_RECEIPT"
    assert receipt["evidence_level"] == "TECHNICAL_ONLY"
    assert receipt["scientific_terminal_admitted"] is False
    assert receipt["technical_lineage_receipt"]["paired_t40_rejoins"] == 2
    assert {
        "terminal_label",
        "historical_control_reuse_passed",
        "clean_two_sided_real_support_opened",
        "toy_route_must_park",
        "scientific_disposition",
    }.isdisjoint(receipt)
    assert "real_frontier_rows" not in receipt


def _row(*, eligible: bool, alias: bool, lineage=("CELL", 1, 2, "0")):
    cell, seed, episode, key = lineage
    return {
        "cell": cell,
        "task_seed": seed,
        "episode_id": episode,
        "lifecycle_key": key,
        "incumbent_skill": 0,
        "truth_skill_set": [1] if eligible else [0],
        "complete_mask": {
            "frontier_present": True,
            "incumbent_present": True,
            "different_successor": bool(eligible or alias),
            "actual_proposal_gate": bool(eligible or alias),
            "truth_any_skill": True,
            "truth_non_incumbent_skill": bool(eligible),
            "truth_actual_proposal": bool(eligible),
            "eligible_strict_truth": bool(eligible),
        },
    }


def _separating_pair():
    mask = {name: False for name in MASK_FIELDS}
    return {
        "state_delta": {"position": 1.0, "velocity": 0.0},
        "incumbent_lineage_match": True,
        "control": {"proposal": 0, "complete_mask": mask},
        "treatment": {"proposal": 0, "complete_mask": mask},
    }


def test_mismatch_only_favorable_evidence_fails_closed_and_join_cannot_open():
    favorable_lineage = ("CELL", 1, 2, "0")
    rows = [_row(eligible=True, alias=False), _row(eligible=False, alias=True, lineage=("CELL", 1, 2, "1"))]
    with pytest.raises(ValueError, match="exact full admission"):
        classify_terminal_label(
            rows,
            [_separating_pair()],
            {favorable_lineage},
            admission=None,
        )

    join = _row(eligible=False, alias=False)
    join["incumbent_skill"] = None
    join["truth_skill_set"] = [1]
    join["complete_mask"].update(
        incumbent_present=False,
        different_successor=False,
        truth_non_incumbent_skill=False,
        truth_actual_proposal=True,
        eligible_strict_truth=False,
    )
    with pytest.raises(ValueError, match="exact full admission"):
        classify_terminal_label([join], [], set(), admission=None)


def test_clean_two_sided_label_requires_both_real_classes_and_clean_lineage():
    eligible = _row(eligible=True, alias=False)
    alias = _row(eligible=False, alias=True, lineage=("CELL", 1, 2, "1"))
    for rows in ([eligible, alias], [eligible]):
        with pytest.raises(ValueError, match="exact full admission"):
            classify_terminal_label(rows, [_separating_pair()], set(), admission=None)


def test_zero_episode_smoke_cannot_emit_any_scientific_terminal(smoke_raw, accepted_control):
    wrong = deepcopy(smoke_raw)
    wrong["declared_counts"] = {
        "cells": 0,
        "task_seeds": 0,
        "episodes": 0,
        "environment_transitions": 0,
    }
    wrong["actual_counts"] = deepcopy(wrong["declared_counts"])
    wrong["episode_roster"] = []
    wrong["schedule_delta_rows"] = []
    wrong["lineage_runtime_audits"] = []
    wrong["membership_event_coverage"] = []
    wrong["real_frontier_rows"] = []
    wrong["call_counts"] = {name: 0 for name in wrong["call_counts"]}
    with pytest.raises(ValueError, match="activity counts"):
        analyze_treatment(wrong, accepted_control)


def test_full_config_count_roster_schedule_and_lineage_drift_fail_closed(smoke_raw):
    candidate = deepcopy(smoke_raw)
    with pytest.raises(ValueError, match="configuration"):
        _validate_exact_raw_contract(candidate, FULL_CONFIG)

    candidate["configuration"] = _expected_configuration(FULL_CONFIG)
    with pytest.raises(ValueError, match="activity counts"):
        _validate_exact_raw_contract(candidate, FULL_CONFIG)

    candidate["declared_counts"] = FULL_CONFIG.counts()
    candidate["actual_counts"] = FULL_CONFIG.counts()
    with pytest.raises(ValueError, match="episode roster"):
        _validate_exact_raw_contract(candidate, FULL_CONFIG)

    candidate["episode_roster"] = list(_roster(FULL_CONFIG))
    with pytest.raises(ValueError, match="schedule rows"):
        _validate_exact_raw_contract(candidate, FULL_CONFIG)

    candidate["schedule_delta_rows"] = _schedule_rows(FULL_CONFIG)
    with pytest.raises(ValueError, match="lineage audit episode coverage"):
        _validate_exact_raw_contract(candidate, FULL_CONFIG)


def test_full_equivalence_receipt_is_mandatory_and_fail_closed():
    with pytest.raises(ValueError, match="requires the separate 82-transition"):
        _validate_equivalence_receipt(None)
    with pytest.raises(ValueError, match="artifact_kind"):
        _validate_equivalence_receipt({"artifact_kind": "NOT_A2"})


def test_raw_validation_rejects_namespace_activity_and_protected_count_drift(smoke_raw, accepted_control):
    wrong = deepcopy(smoke_raw)
    wrong["call_counts"]["proposal_policy"] += 1
    with pytest.raises(ValueError, match="proposal/frontier"):
        _validate_raw(wrong, accepted_control)
    wrong = deepcopy(smoke_raw)
    wrong["call_counts"]["learner"] = 1
    with pytest.raises(ValueError, match="learner"):
        _validate_raw(wrong, accepted_control)
    wrong = deepcopy(smoke_raw)
    wrong["control_binding"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="control SHA"):
        _validate_raw(wrong, accepted_control)
