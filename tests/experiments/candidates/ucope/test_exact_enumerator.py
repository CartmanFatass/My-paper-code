from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction
import importlib.util
from itertools import product
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.candidates.ucope import exact_enumerator as ucope


def _find(rows, bits):
    return next(row for row in rows if row.bits == bits)


def _scalar_signature(rows):
    return tuple(
        (
            row.bits,
            row.rho,
            row.hazard_s,
            row.hazard_l,
            row.ucope_s,
            row.ucope_l,
            row.cb_auc_action,
            row.sg_rate_action,
            row.action,
            row.expected_auc,
        )
        for row in rows
    )


def test_registered_audit_passes_exact_narrow_count_state_contract():
    result = ucope.run_registered_audit()

    assert result.terminal is ucope.Terminal.PASS
    assert len(result.rows) == 16
    assert result.expected_ucope_auc == Fraction(26571, 20000)
    assert result.expected_cb_auc == 1
    assert result.delta_auc == Fraction(6571, 20000)
    assert all(passed for _, passed in result.invariants)
    assert tuple(name for name, _ in result.invariants) == (
        "effective_period_quotient",
        "matched_history_h_s",
        "matched_history_h_l",
        "h_s_margin",
        "h_l_margin",
        "cb_auc_matched_actions",
        "exact_expected_auc",
        "exact_delta_auc",
        "homogeneous_boundary",
        "independent_redraw_boundary",
        "alias_split_merge",
        "censor_is_unknown",
        "pre_outcome_tape",
        "state_clone_order",
        "recurrence_version_closure",
        "partner_label_permutation",
    )


def test_matched_histories_have_exact_posterior_hazards_actions_and_margins():
    rows = ucope.enumerate_histories(ucope.build_family())
    h_s = _find(rows, (1, 1, 0, 0))
    h_l = _find(rows, (0, 0, 1, 1))

    assert h_s.ledger.opportunities == (1, 1, 1, 1)
    assert h_s.ledger.hits == (1, 1, 0, 0)
    assert h_s.outcomes == ("c1", "c2", None, None)
    assert h_s.rho == Fraction(6561, 6562)
    assert (h_s.hazard_s, h_s.hazard_l) == (
        Fraction(5905, 6562),
        Fraction(657, 6562),
    )
    assert h_s.action == ucope.S
    assert h_s.margin == Fraction(11153, 6562)

    assert h_l.ledger.hits == (0, 0, 1, 1)
    assert h_l.rho == Fraction(1, 6562)
    assert (h_l.hazard_s, h_l.hazard_l) == (
        Fraction(657, 6562),
        Fraction(5905, 6562),
    )
    assert h_l.action == ucope.L
    assert h_l.margin == Fraction(4591, 6562)
    assert h_s.cb_auc_action == h_l.cb_auc_action == ucope.S
    assert h_s.sg_rate_action == ucope.S
    assert h_l.sg_rate_action == ucope.S


def test_all_histories_are_exact_complete_and_canonical_output_is_byte_stable():
    family = ucope.build_family()
    rows = ucope.enumerate_histories(family)
    result = ucope.run_registered_audit()

    assert tuple(row.bits for row in rows) == tuple(product((0, 1), repeat=4))
    assert sum(row.prior_probability for row in rows) == 1
    assert all(row.cb_auc_action == ucope.S for row in rows)
    assert result.to_bytes() == ucope.run_registered_audit().to_bytes()

    payload = json.loads(result.to_bytes())
    assert payload["terminal"] == "PASS_NARROW_COUNT_STATE_RELEVANCE"
    assert payload["expected_ucope_auc"] == "26571/20000"
    assert payload["expected_cb_auc"] == "1"
    assert payload["delta_auc"] == "6571/20000"
    assert len(payload["rows"]) == 16
    assert set(payload["rows"][0]) == {
        "CB_AUC",
        "CB_AUC_action",
        "E",
        "N",
        "SG_RATE_action",
        "UCOPE",
        "action",
        "expected_fifth_trial_AUC",
        "hazards",
        "history",
        "history_bits",
        "margin",
        "prior_probability",
        "rho",
    }


def test_effective_period_alias_split_and_merge_are_execution_equivalent():
    split = ucope.build_family(split_long_alias=True)
    merged = ucope.build_family(split_long_alias=False)

    assert ucope.validate_family(split) == ()
    assert split.nominal("ell").effective == split.nominal("ell_prime").effective == ucope.L
    assert split.nominal("ell").duration == split.nominal("ell_prime").duration == 2
    assert split.nominal("ell").execution_law == split.nominal("ell_prime").execution_law
    assert _scalar_signature(ucope.enumerate_histories(split)) == _scalar_signature(
        ucope.enumerate_histories(merged)
    )

    broken_alias = replace(
        split.nominal("ell_prime"), execution_law=b"different-execution-law"
    )
    malformed = replace(split, nominals=(*split.nominals[:2], broken_alias))
    assert any("execution-law aliases" in issue for issue in ucope.validate_family(malformed))


def test_censoring_is_unknown_and_ledgers_are_immutable_and_version_closed():
    family = ucope.build_family()
    empty = ucope.Ledger.empty(family.version)
    censored = ucope.update_ledger(family, empty, family.trials[0], None)
    miss = ucope.update_ledger(family, empty, family.trials[0], False)
    hit = ucope.update_ledger(family, empty, family.trials[0], True)

    assert censored is empty
    assert empty.opportunities == empty.hits == (0, 0, 0, 0)
    assert miss.opportunities == (1, 0, 0, 0)
    assert miss.hits == (0, 0, 0, 0)
    assert hit.opportunities == hit.hits == (1, 0, 0, 0)
    with pytest.raises(ValueError, match="version mismatch"):
        ucope.update_ledger(
            family,
            ucope.Ledger.empty("other-version"),
            family.trials[0],
            True,
        )


def test_homogeneous_and_independent_redraw_boundaries_are_exact_zero_effect():
    homogeneous = ucope.enumerate_histories(
        ucope.build_family(homogeneous_hazards=True)
    )
    family = ucope.build_family()
    redraw = ucope.enumerate_histories(family, independent_redraw=True)

    for rows in (homogeneous, redraw):
        assert all(row.rho == Fraction(1, 2) for row in rows)
        assert all(row.hazard_s == row.hazard_l == Fraction(1, 2) for row in rows)
        assert all(row.action == ucope.S for row in rows)
        assert sum(row.prior_probability * row.expected_auc for row in rows) == 1
        assert sum(
            row.prior_probability * row.cb_auc_s for row in rows
        ) == 1


def test_pre_outcome_tape_state_clone_and_partner_labels_cannot_change_result():
    family = ucope.build_family()
    histories = tuple(product((0, 1), repeat=4))
    forward = ucope.enumerate_histories(family, history_order=histories)
    reverse = ucope.enumerate_histories(
        family, history_order=tuple(reversed(histories))
    )
    renamed = ucope.enumerate_histories(
        ucope.build_family(cells=("anonymous_y", "anonymous_x"))
    )

    assert _scalar_signature(forward) == _scalar_signature(reverse)
    assert _scalar_signature(forward) == _scalar_signature(renamed)
    assert tuple(trial.forced_nominal for trial in family.trials) == (
        "s",
        "s",
        "long_a",
        "long_b",
        None,
    )
    assert all(
        row.ledger.version == family.version and row.ledger.opportunities == (1, 1, 1, 1)
        for row in forward
    )


@pytest.mark.parametrize(
    "malformed",
    (
        replace(ucope.build_family(), version=""),
        replace(ucope.build_family(), weights=(Fraction(1), Fraction(0))),
        replace(ucope.build_family(), structural_support=()),
        replace(ucope.build_family(), persistent_theta=False),
        replace(
            ucope.build_family(),
            trials=(
                replace(ucope.build_family().trials[0], limit=0),
                *ucope.build_family().trials[1:],
            ),
        ),
    ),
)
def test_family_contract_failures_stop_before_enumeration(malformed):
    assert ucope.validate_family(malformed)
    with pytest.raises(ValueError):
        ucope.enumerate_histories(malformed)


def _a1_manifest(*, technical_only=False):
    return ucope.build_a1_manifest(
        source_revision="a" * 40,
        run_id="ucope_a1_unit_contract",
        technical_only=technical_only,
    )


def test_a1_manifest_is_total_exact_and_rejects_float_or_literal_drift():
    manifest = _a1_manifest()
    assert ucope.validate_a1_manifest(manifest) == ()
    assert manifest["family"]["cell_weights"] == ["1", "1"]
    assert manifest["family"]["raw_periods"] == ["s", "long_a", "long_b"]
    assert manifest["modes"] == ["primary", "homogeneous", "independent_redraw"]
    assert manifest["caps"]["regime_conditioned_rational_cells"] == 96

    malformed = copy.deepcopy(manifest)
    malformed["family"]["prior"]["THETA_S"] = 0.5
    issues = ucope.validate_a1_manifest(malformed)
    assert "manifest contains float/epsilon arithmetic" in issues
    assert any("frozen A1 literal" in issue for issue in issues)


def test_a1_primary_table_has_all_exact_joint_weights_and_named_aggregates():
    evidence = ucope._build_a1_evidence()
    assert ucope._validate_evidence(evidence) == ()
    rows = evidence["primary"]["rows"]
    assert [row["history_bits"] for row in rows] == [
        "".join(map(str, bits)) for bits in product((0, 1), repeat=4)
    ]
    row_0000 = rows[0]
    row_hl = next(row for row in rows if row["history_bits"] == "0011")
    row_hs = next(row for row in rows if row["history_bits"] == "1100")
    assert row_0000["joint_regime_weights"] == {
        "THETA_S": "81/20000",
        "THETA_L": "81/20000",
    }
    assert row_hl["joint_regime_weights"] == {
        "THETA_S": "1/20000",
        "THETA_L": "6561/20000",
    }
    assert row_hs["joint_regime_weights"] == {
        "THETA_S": "6561/20000",
        "THETA_L": "1/20000",
    }
    assert row_hl["UCOPE_action"] == ucope.L
    assert row_hs["UCOPE_action"] == ucope.S
    assert all(
        row["SG_RATE_scores"] == {ucope.S: "1", ucope.L: "1/2"}
        and row["SG_RATE_action"] == ucope.S
        for row in rows
    )
    assert evidence["primary"]["aggregates"] == {
        "UCOPE_expected_auc": "26571/20000",
        "CB_AUC_expected_auc": "1",
        "AUC_gain_over_CB_AUC": "6571/20000",
        "UCOPE_terminal_coverage": "1097/1250",
        "CB_AUC_terminal_coverage": "1/2",
        "terminal_coverage_gain": "236/625",
        "UCOPE_conditional_auc_by_regime": {
            "THETA_S": "179371/100000",
            "THETA_L": "86339/100000",
        },
    }


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "order"))
def test_a1_validator_rejects_history_missing_duplicate_and_order_drift(mutation):
    evidence = ucope._build_a1_evidence()
    rows = evidence["primary"]["rows"]
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    else:
        rows[0], rows[1] = rows[1], rows[0]
    issues = ucope._validate_evidence(evidence)
    assert any("history set/order" in issue for issue in issues)


@pytest.mark.parametrize(
    "mutation",
    (
        "joint_weight",
        "per_trial_redraw_primary",
        "censor_as_failure",
        "outcome_derived_exposure",
        "alias_split",
        "identity_leakage",
        "version_mixing",
        "wrong_comparator",
        "float_epsilon",
    ),
)
def test_a1_validator_rejects_frozen_semantic_corruptions(mutation):
    evidence = ucope._build_a1_evidence()
    if mutation == "joint_weight":
        evidence["primary"]["rows"][0]["joint_regime_weights"]["THETA_S"] = "82/20000"
    elif mutation == "per_trial_redraw_primary":
        evidence["primary"]["rows"] = copy.deepcopy(
            evidence["boundaries"]["independent_redraw"]["rows"]
        )
    elif mutation == "censor_as_failure":
        evidence["boundaries"]["censor"]["L_binary_denominator_increment"] = 1
    elif mutation == "outcome_derived_exposure":
        evidence["primary"]["rows"][0]["E"][ucope.S] = 0
    elif mutation == "alias_split":
        evidence["invariants"]["S06_alias_split_merge_invariant"] = False
    elif mutation == "identity_leakage":
        evidence["primary"]["rows"][0]["partner_id"] = "leaked-label"
    elif mutation == "version_mixing":
        evidence["invariants"]["S02_version_pooling_rejected"] = False
    elif mutation == "wrong_comparator":
        evidence["primary"]["rows"][0]["CB_AUC_action"] = ucope.L
    elif mutation == "float_epsilon":
        evidence["primary"]["rows"][0]["rho"] = 0.5
    assert ucope._validate_evidence(evidence)


def test_a1_boundaries_alias_identity_tape_state_and_censor_are_explicit():
    evidence = ucope._build_a1_evidence()
    for name in ("homogeneous", "independent_redraw"):
        mode = evidence["boundaries"][name]
        assert len(mode["rows"]) == 16
        assert all(row["UCOPE_action"] == row["CB_AUC_action"] == ucope.S for row in mode["rows"])
        assert all(
            row["SG_RATE_scores"] == {ucope.S: "1", ucope.L: "1/2"}
            and row["SG_RATE_action"] == ucope.S
            for row in mode["rows"]
        )
        assert mode["aggregates"]["AUC_gain_over_CB_AUC"] == "0"
    redraw_0011 = evidence["boundaries"]["independent_redraw"]["rows"][3]
    assert redraw_0011["history_weight"] == "3281/10000"
    assert redraw_0011["joint_regime_weights"] == {
        "THETA_S": "3281/20000",
        "THETA_L": "3281/20000",
    }
    censor = evidence["boundaries"]["censor"]
    assert censor["L_binary_denominator_increment"] == 0
    assert censor["S_binary_denominator_increment"] == 1
    assert censor["primary_before_canonical_json"] == censor[
        "primary_after_canonical_json"
    ]
    assert censor["primary_bytes_equal"] is True
    assert all(evidence["invariants"].values())
    assert evidence["resource_accounting"] == {
        "history_rows": 48,
        "unique_histories_reused": 16,
        "regime_conditioned_rational_cells": 96,
    }


def test_a1_branch_precedence_and_lowest_scientific_failure_are_frozen():
    branch, failure = ucope.select_a1_branch(
        manifest_errors=("bad",),
        enumeration_errors=("also bad",),
        stop_failures=(ucope.A1_STOP_IDS[0],),
    )
    assert branch is ucope.A1Branch.INVALID_MANIFEST and failure is None
    branch, failure = ucope.select_a1_branch(
        enumeration_errors=("bad",), stop_failures=(ucope.A1_STOP_IDS[0],)
    )
    assert branch is ucope.A1Branch.INVALID_ENUMERATION and failure is None
    branch, failure = ucope.select_a1_branch(
        stop_failures=(ucope.A1_STOP_IDS[10], ucope.A1_STOP_IDS[3])
    )
    assert branch is ucope.A1Branch.SCIENTIFIC_STOP
    assert failure == ucope.A1_STOP_IDS[3]
    assert ucope.select_a1_branch() == (ucope.A1Branch.SUPPORTED, None)


def test_a1_zero_activity_is_total_and_nonzero_activity_fails_closed():
    assert ucope._validate_activity(ucope.zero_activity()) == ()
    nonzero = ucope.zero_activity()
    nonzero["policy_calls"] = 1
    assert ucope._validate_activity(nonzero) == (
        "registered A1 requires every activity counter to equal zero",
    )
    missing = ucope.zero_activity()
    missing.pop("evaluation_calls")
    assert ucope._validate_activity(missing) == (
        "activity counters are incomplete or contain unknown keys",
    )


def test_a1_technical_only_exercise_never_materializes_or_admits_a_branch():
    artifact = ucope.run_a1_probe(_a1_manifest(technical_only=True))
    assert artifact["branch"] is None
    assert artifact["first_failure_id"] is None
    assert artifact["scientific_terminal_admitted"] is False
    assert "primary" not in artifact and "boundaries" not in artifact
    assert ucope.validate_a1_artifact(artifact) == ()

    corrupted = copy.deepcopy(artifact)
    corrupted["branch"] = ucope.A1Branch.SUPPORTED.value
    corrupted["scientific_terminal_admitted"] = True
    issues = ucope.validate_a1_artifact(corrupted)
    assert any("technical-only artifact admitted" in issue for issue in issues)


def test_a1_registered_cli_enumerates_exactly_three_modes_and_validator_never_reruns(
    monkeypatch,
):
    runner_path = (
        Path(__file__).resolve().parents[4]
        / "scripts"
        / "run_ucope_a1_count_state_exact_enumeration.py"
    )
    spec = importlib.util.spec_from_file_location("ucope_a1_runner_unit", runner_path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    calls = []
    real_enumerate = ucope.enumerate_histories

    def counted_enumerate(*args, **kwargs):
        rows = real_enumerate(*args, **kwargs)
        calls.append(len(rows))
        return rows

    captured = {}
    monkeypatch.setattr(ucope, "enumerate_histories", counted_enumerate)
    monkeypatch.setattr(runner, "_read_json", lambda _path: _a1_manifest())
    monkeypatch.setattr(runner, "_require_current_source", lambda _manifest: None)
    monkeypatch.setattr(runner, "_require_clean_claim_sources", lambda: None)
    monkeypatch.setattr(
        runner,
        "_claim_registered_run",
        lambda _root, _manifest: Path("raw_result.json"),
    )
    monkeypatch.setattr(
        runner, "_write_once", lambda path, payload: captured.update({str(path): payload})
    )
    assert runner._registered_probe_command(
        SimpleNamespace(manifest=Path("manifest.json"), run_root=Path("run"))
    ) == 0
    assert calls == [16, 16, 16]
    artifact = captured["raw_result.json"]
    assert artifact["resource_accounting"] == {
        "history_rows": 48,
        "unique_histories_reused": 16,
        "regime_conditioned_rational_cells": 96,
    }

    def forbidden_generation(*_args, **_kwargs):
        raise AssertionError("retained-payload validator attempted a forbidden rerun")

    monkeypatch.setattr(ucope, "run_a1_probe", forbidden_generation)
    monkeypatch.setattr(ucope, "_build_a1_evidence", forbidden_generation)
    monkeypatch.setattr(ucope, "enumerate_histories", forbidden_generation)
    assert ucope.validate_a1_artifact(artifact) == ()


def test_a1_matched_state_identity_and_forbidden_dependency_witnesses_are_tamper_evident():
    evidence = ucope._build_a1_evidence()
    witness = evidence["matched_noncount_state_witness"]
    hs_state = witness["HS"]["noncount_state"]
    hl_state = witness["HL"]["noncount_state"]
    assert hs_state == hl_state
    assert witness["HS"]["N"] != witness["HL"]["N"]
    assert witness["HS"]["E"] == witness["HL"]["E"] == {ucope.S: 2, ucope.L: 2}
    assert witness["HS"]["rho"] != witness["HL"]["rho"]
    assert set(hs_state) == {
        "current_opportunity",
        "uncovered_set",
        "horizon",
        "Q_str",
        "costs",
        "censor_law",
        "exposure_ledger",
        "forced_action_sequence",
        "executor_generation",
        "partner_policy_generation",
        "noncount_recurrent_state",
        "noncount_policy_state",
    }
    identity = evidence["identity_projection_witness"]
    assert identity["byte_equal"] is True
    assert identity["identity_fields_absent"] is True
    assert identity["base_projection_canonical_json"] == identity[
        "permuted_projection_canonical_json"
    ]
    alias = evidence["alias_projection_witness"]
    assert alias["split_projection"] == alias["merged_projection"]
    assert alias["split_projection"]["downstream_primary_canonical_json"] == json.dumps(
        evidence["primary"], ensure_ascii=True, separators=(",", ":"), sort_keys=True
    )
    dependency = evidence["forbidden_dependency_witness"]
    assert dependency["all_required_activity_zero"] is True
    assert dependency["postoutcome_filter_absent"] is True
    assert dependency["forbidden_surface_absent"] is True
    assert dependency["observed_imports"]
    assert dependency["observed_calls"]
    assert dependency["forbidden_imports_present"] == []
    assert dependency["forbidden_calls_present"] == []

    drifted_state = copy.deepcopy(evidence)
    drifted_state["matched_noncount_state_witness"]["HS"]["noncount_state"][
        "horizon"
    ] = 4
    assert any(
        "matched non-count state witness" in issue
        for issue in ucope._validate_evidence(drifted_state)
    )

    leaked_identity = copy.deepcopy(evidence)
    leaked_identity["identity_projection_witness"]["projected_row_fields"].append(
        "partner_id"
    )
    assert any(
        "identity-free canonical byte projection" in issue
        for issue in ucope._validate_evidence(leaked_identity)
    )

    nonzero_dependency = copy.deepcopy(evidence)
    nonzero_dependency["forbidden_dependency_witness"]["activity"]["policy_calls"] = 1
    assert any(
        "forbidden-dependency/zero-activity witness" in issue
        for issue in ucope._validate_evidence(nonzero_dependency)
    )

    drifted_alias = copy.deepcopy(evidence)
    drifted_alias["alias_projection_witness"]["merged_projection"][
        "downstream_primary_canonical_json"
    ] = "{}"
    assert any(
        "alias split/merge structural projection" in issue
        for issue in ucope._validate_evidence(drifted_alias)
    )

    drifted_ast = copy.deepcopy(evidence)
    drifted_ast["forbidden_dependency_witness"]["observed_calls"].append(
        "policy_forward"
    )
    assert any(
        "forbidden-dependency/zero-activity witness" in issue
        for issue in ucope._validate_evidence(drifted_ast)
    )


def _load_a1_runner(module_name):
    runner_path = (
        Path(__file__).resolve().parents[4]
        / "scripts"
        / "run_ucope_a1_count_state_exact_enumeration.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, runner_path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_a1_invalid_and_scientific_stop_artifacts_are_self_consistent_and_cli_writable(
    monkeypatch,
):
    manifest = _a1_manifest()
    activity = ucope.zero_activity()

    invalid_evidence = ucope._build_a1_evidence()
    invalid_evidence["primary"]["rows"][0]["joint_regime_weights"][
        "THETA_S"
    ] = "82/20000"
    invalid_evidence["invariants"] = ucope._derive_a1_invariants(
        invalid_evidence, activity
    )
    invalid_artifact = ucope._assemble_a1_result(
        manifest=manifest, evidence=invalid_evidence, activity=activity
    )
    assert invalid_artifact["branch"] == ucope.A1Branch.INVALID_ENUMERATION.value
    assert invalid_artifact["enumeration_errors"]
    assert invalid_artifact["stop_failures"] == []
    assert ucope.validate_a1_artifact(invalid_artifact) == ()

    stop_evidence = ucope._build_a1_evidence()
    stop_evidence["version_closure_witness"]["mixed_version_update"] = "ACCEPTED"
    stop_evidence["invariants"] = ucope._derive_a1_invariants(stop_evidence, activity)
    stop_artifact = ucope._assemble_a1_result(
        manifest=manifest, evidence=stop_evidence, activity=activity
    )
    assert stop_artifact["branch"] == ucope.A1Branch.SCIENTIFIC_STOP.value
    assert stop_artifact["enumeration_errors"] == []
    assert stop_artifact["stop_failures"] == [
        "S02_SWITCH_REQUIRES_VERSION_POOLING"
    ]
    assert stop_artifact["first_failure_id"] == "S02_SWITCH_REQUIRES_VERSION_POOLING"
    assert ucope.validate_a1_artifact(stop_artifact) == ()

    runner = _load_a1_runner("ucope_a1_runner_branch_unit")
    current = {"artifact": invalid_artifact}
    writes = []
    monkeypatch.setattr(runner, "_read_json", lambda _path: manifest)
    monkeypatch.setattr(runner, "_require_current_source", lambda _manifest: None)
    monkeypatch.setattr(runner, "_require_clean_claim_sources", lambda: None)
    monkeypatch.setattr(
        runner,
        "_claim_registered_run",
        lambda _root, _manifest: Path("raw_result.json"),
    )
    monkeypatch.setattr(
        runner, "run_a1_probe", lambda *_args, **_kwargs: current["artifact"]
    )
    monkeypatch.setattr(
        runner, "_write_once", lambda path, payload: writes.append((path, payload))
    )
    args = SimpleNamespace(manifest=Path("manifest.json"), run_root=Path("run"))
    assert runner._registered_probe_command(args) == 0
    current["artifact"] = stop_artifact
    assert runner._registered_probe_command(args) == 0
    assert [payload["branch"] for _, payload in writes] == [
        ucope.A1Branch.INVALID_ENUMERATION.value,
        ucope.A1Branch.SCIENTIFIC_STOP.value,
    ]


def test_a1_registered_preflight_and_claim_fail_closed_before_enumeration(
    monkeypatch, tmp_path
):
    runner = _load_a1_runner("ucope_a1_runner_claim_unit")
    expected = tuple(sorted(runner.CLAIM_PATHS))
    without_runner = tuple(
        path
        for path in expected
        if path != "scripts/run_ucope_a1_count_state_exact_enumeration.py"
    )

    monkeypatch.setattr(
        runner, "_git_claim_source_state", lambda: (without_runner, ())
    )
    with pytest.raises(ValueError, match="untracked or absent"):
        runner._require_clean_claim_sources()

    monkeypatch.setattr(
        runner,
        "_git_claim_source_state",
        lambda: (expected, (" M scripts/run_ucope_a1_count_state_exact_enumeration.py",)),
    )
    with pytest.raises(ValueError, match="differs from HEAD"):
        runner._require_clean_claim_sources()

    manifest = _a1_manifest()
    result_path = runner._claim_registered_run(tmp_path, manifest)
    assert result_path == tmp_path / "raw_result.json"
    claim = json.loads((tmp_path / "registered_claim.json").read_text("utf-8"))
    assert claim == {
        "artifact_kind": "ucope_a1_registered_run_claim",
        "assignment_id": ucope.A1_ASSIGNMENT_ID,
        "candidate": ucope.A1_CANDIDATE,
        "run_id": manifest["run_id"],
        "source_revision": manifest["source_revision"],
        "canonical_result_name": "raw_result.json",
    }
    with pytest.raises(FileExistsError, match="already claimed"):
        runner._claim_registered_run(tmp_path, manifest)

    with pytest.raises(SystemExit):
        runner._parser().parse_args(
            [
                "registered-probe",
                "--manifest",
                "manifest.json",
                "--run-root",
                "run",
                "--output",
                "alternate.json",
            ]
        )
