from __future__ import annotations

import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.ucope import persistent_count_state_learned_utility as b1
from experiments.candidates.ucope.persistent_count_state_host import (
    L,
    PERSISTENT,
    S,
    THETA_L,
    THETA_S,
    TRIAL5_REDRAW,
    Generation,
    PersistentCountStateHost,
    generation_for_block,
    history_probability,
    uniform_for_mark,
)


def _complete_prefix(host, generation, bits, regime):
    records = []
    for bit, period in zip(bits, (S, S, L, L)):
        records.append(
            host.step_prefix(
                uniform=uniform_for_mark(
                    hit=bool(bit), hazard=b1.HAZARDS[(regime, period)]
                ),
                generation=generation,
            )
        )
    return records


def test_host_executes_exact_five_real_transitions_and_freezes_count_before_policy():
    generation = Generation(7, 11, 13)
    host = PersistentCountStateHost(
        stratum=PERSISTENT,
        prefix_regime=THETA_S,
        trial5_regime=THETA_S,
        generation=generation,
    )
    prefix = _complete_prefix(host, generation, (1, 1, 0, 0), THETA_S)
    assert [row.period for row in prefix] == [S, S, L, L]
    assert [row.cell for row in prefix] == ["c1", "c2", "c1", "c2"]
    assert [row.physical_auc for row in prefix] == [0, 0, 0, 0]
    d, ledger = host.freeze_count(generation=generation)
    assert d == -2
    action, before, after = host.policy_call(
        lambda visible_d: S if visible_d <= 0 else L,
        visible_d=d,
        generation=generation,
    )
    assert action == S and before == after == ledger
    record = host.step_trial5(
        action=action,
        uniform=Fraction(1, 20),
        generation=generation,
        task_reward_placeholder={"cannot": "enter-ledger"},
    )
    assert record.hit and record.physical_auc == 2
    assert record.ledger_before_sha == record.ledger_after_sha
    host.close_block()
    assert host.transition_count == 5


def test_host_rejects_mixed_or_midblock_versions_before_policy_and_discards_ledger():
    generation = generation_for_block(1)
    wrong = generation_for_block(2)
    host = PersistentCountStateHost(
        stratum=TRIAL5_REDRAW,
        prefix_regime=THETA_S,
        trial5_regime=THETA_L,
        generation=generation,
    )
    with pytest.raises(ValueError, match="mixed or mid-block"):
        host.step_prefix(uniform=Fraction(1, 20), generation=wrong)
    _complete_prefix(host, generation, (0, 1, 1, 0), THETA_S)
    host.freeze_count(generation=generation)
    with pytest.raises(ValueError, match="mixed or mid-block"):
        host.policy_call(lambda _d: S, visible_d=0, generation=wrong)
    host.policy_call(lambda _d: S, visible_d=0, generation=generation)
    host.step_trial5(action=S, uniform=Fraction(19, 20), generation=generation)
    host.close_block()
    with pytest.raises(RuntimeError, match="closed"):
        host.freeze_count(generation=generation)


def test_controller_arms_are_exactly_matched_and_count_access_is_sole_delta():
    count = b1.TabularQController()
    blind = b1.TabularQController()
    assert count.to_json() == blind.to_json()
    assert count.to_json()["shape"] == [5, 2]
    assert count.to_json()["parameter_count"] == 10
    assert count.to_json()["dtype"] == "float64"
    assert count.to_json()["hidden_state"] == {}
    assert b1.observation(b1.COUNT, -2)["d"] == -2
    assert b1.observation(b1.COUNT, 2)["d"] == 2
    blind_bytes = {
        b1.canonical_bytes(b1.observation(b1.BLIND, d)) for d in b1.D_VALUES
    }
    assert len(blind_bytes) == 1
    assert all(name not in b1.observation(b1.COUNT, 1) for name in b1.FORBIDDEN_INPUTS)


def test_incremental_update_equals_logged_real_return_empirical_mean():
    controller = b1.TabularQController()
    returns = [2, 0, 2, 1, 0, 2]
    for reward in returns:
        controller.update(1, L, reward)
    assert controller.visits[3, 1] == len(returns)
    assert controller.return_sum[3, 1] == sum(returns)
    assert abs(controller.q[3, 1] - np.mean(returns)) <= 1e-12
    restored = b1.TabularQController.from_json(controller.to_json())
    assert np.array_equal(restored.visits, controller.visits)
    assert np.array_equal(restored.q, controller.q)
    tampered = copy.deepcopy(controller.to_json())
    tampered["shape"] = [10]
    with pytest.raises(ValueError, match="schema"):
        b1.TabularQController.from_json(tampered)


def test_registered_training_tape_is_seed_deterministic_balanced_and_count_independent():
    config = b1.registered_config()
    first = b1._training_plan(config, 1103, PERSISTENT)
    second = b1._training_plan(config, 1103, PERSISTENT)
    assert first == second
    actions = [row["exploration_action"] for row in first]
    assert actions.count(S) == actions.count(L) == 2048
    assert all(row["exploration_action"] in (S, L) for row in first)
    assert all(len(row["prefix_uniforms"]) == 4 for row in first)
    assert b1._training_plan(config, 2207, PERSISTENT) != first


def test_registered_and_smoke_activity_caps_are_exact():
    full = b1.registered_config().to_json()
    assert b1.expected_training_counts(full) == {
        "learned_replicas": 16,
        "training_blocks": 65536,
        "training_environment_transitions": 327680,
        "training_policy_calls": 65536,
        "learner_calls": 65536,
        "trainer_calls": 65536,
        "optimizer_updates": 65536,
        "k_search": 0,
        "hypothetical_transitions": 0,
    }
    assert b1.expected_evaluation_counts(full) == {
        "learned_persistent_evaluation_blocks": 768,
        "learned_redraw_evaluation_blocks": 1536,
        "oracle_evaluation_blocks": 288,
        "evaluation_blocks": 2592,
        "evaluation_environment_transitions": 12960,
        "evaluation_policy_calls": 2592,
        "learner_calls": 0,
        "trainer_calls": 0,
        "optimizer_updates": 0,
    }
    total = b1.total_activity_counts(full)
    assert total["total_complete_blocks"] == 68128
    assert total["total_environment_transitions"] == 340640
    assert total["total_policy_calls"] == 68128
    assert total["learner_calls"] == total["trainer_calls"] == total["optimizer_updates"] == 65536
    smoke = b1.total_activity_counts(b1.technical_smoke_config().to_json())
    assert smoke["full_runs"] == 0 and smoke["total_complete_blocks"] < 2000


def test_exact_panels_are_complete_normalized_and_oracle_matches_a1_boundary_values():
    oracle_j = {}
    always_s = {}
    row_index = 0
    for stratum, expected_rows in ((PERSISTENT, 96), (TRIAL5_REDRAW, 192)):
        rows = []
        for prefix_regime, trial5_regime, history, uniform_id, uniform, weight in b1._iter_panel_specs(stratum):
            rows.append(
                b1._execute_panel_row(
                    arm=b1.ORACLE,
                    stratum=stratum,
                    prefix_regime=prefix_regime,
                    trial5_regime=trial5_regime,
                    history=history,
                    uniform_id=uniform_id,
                    trial5_uniform=uniform,
                    weight=weight,
                    row_index=row_index,
                    controller=None,
                    master_seed=None,
                )
            )
            row_index += 1
        assert len(rows) == expected_rows
        assert sum((b1.parse_fraction(row["weight"]) for row in rows), Fraction()) == 1
        assert all(row["environment_transitions"] == 5 for row in rows)
        assert all(row["generated_prefix_marks"] == [int(bit) for bit in row["prefix_history"]] for row in rows)
        oracle_j[stratum] = b1._exact_j(rows)
        always_s[stratum] = b1._exact_always_s(rows)
        by_history = {history: {row["action"] for row in rows if row["prefix_history"] == history} for history in ("1100", "0011")}
        if stratum == PERSISTENT:
            assert by_history == {"1100": {S}, "0011": {L}}
        else:
            assert by_history == {"1100": {S}, "0011": {S}}
    assert oracle_j == {PERSISTENT: Fraction(26571, 20000), TRIAL5_REDRAW: Fraction(1)}
    assert always_s == {PERSISTENT: Fraction(1), TRIAL5_REDRAW: Fraction(1)}


def test_evaluation_policy_is_called_exactly_once_inside_host_without_action_injection():
    class SpyController(b1.TabularQController):
        def __init__(self):
            super().__init__()
            self.calls = []
            self.q[4, 1] = 1.0

        def policy_call(self, visible_d, forced_action=None):
            self.calls.append((visible_d, forced_action))
            return super().policy_call(visible_d, forced_action)

    controller = SpyController()
    row = b1._execute_panel_row(
        arm=b1.COUNT,
        stratum=PERSISTENT,
        prefix_regime=THETA_L,
        trial5_regime=THETA_L,
        history=(0, 0, 1, 1),
        uniform_id="LOW",
        trial5_uniform=Fraction(1, 20),
        weight=Fraction(1),
        row_index=9,
        controller=controller,
        master_seed=1103,
    )
    assert controller.calls == [(2, None)]
    assert row["action"] == L
    assert row["policy_calls"] == 1


def test_panel_history_weights_are_generated_from_exact_registered_hazards():
    for regime in (THETA_S, THETA_L):
        total = sum((history_probability(history, regime) for history in b1.CANONICAL_HISTORIES), Fraction())
        assert total == 1
    specs = list(b1._iter_panel_specs(PERSISTENT))
    assert {weight.denominator for *_, weight in specs}
    assert all(isinstance(weight, Fraction) for *_, weight in specs)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"contract_valid": False, "leakage_free": False}, b1.BRANCHES[0]),
        ({"leakage_free": False, "calibrated": False}, b1.BRANCHES[1]),
        ({"calibrated": False, "visit_floors_pass": False}, b1.BRANCHES[2]),
        ({"visit_floors_pass": False}, b1.BRANCHES[7]),
        ({"persistent_maps_complete": False}, b1.BRANCHES[3]),
        ({"persistent_deltas_positive": False}, b1.BRANCHES[4]),
        ({"redraw_maps_constant": False}, b1.BRANCHES[5]),
        ({}, b1.BRANCHES[6]),
    ],
)
def test_frozen_branch_precedence(overrides, expected):
    values = {
        "technical_only": False,
        "contract_valid": True,
        "leakage_free": True,
        "calibrated": True,
        "visit_floors_pass": True,
        "persistent_maps_complete": True,
        "persistent_deltas_positive": True,
        "redraw_maps_constant": True,
        "redraw_deltas_zero": True,
    }
    values.update(overrides)
    assert b1.select_branch(**values) == expected
    values["technical_only"] = True
    assert b1.select_branch(**values) is None


def test_manifest_is_total_source_bound_and_tamper_evident():
    config = b1.technical_smoke_config()
    manifest = b1.build_manifest(
        config=config,
        source_commit="1" * 40,
        run_id="technical_manifest_unit",
    )
    assert manifest["source_paths"] == list(b1.SOURCE_PATHS)
    assert manifest["controller_contract"]["shape"] == [5, 2]
    content = dict(manifest)
    declared = content.pop("content_sha256")
    assert declared == b1.hashlib.sha256(b1.canonical_bytes(content)).hexdigest()
    drift = copy.deepcopy(content)
    drift["config"]["blocks_per_replica"] += 1
    assert declared != b1.hashlib.sha256(b1.canonical_bytes(drift)).hexdigest()
    with pytest.raises(ValueError, match="source commit"):
        b1.build_manifest(config=config, source_commit="dirty", run_id="x")


@pytest.mark.parametrize(
    "mutation",
    ["action", "uniform", "count", "reward", "generation", "witness"],
)
def test_training_row_reconstruction_rejects_independent_producer_tamper(mutation):
    config = b1.technical_smoke_config()
    plan = b1._training_plan(config, 1103, PERSISTENT)[0]
    row = b1._execute_training_block(
        controller=b1.TabularQController(),
        arm=b1.COUNT,
        stratum=PERSISTENT,
        plan=plan,
    )
    row["master_seed"] = 1103
    b1.validate_training_row_reconstruction(
        row,
        plan=plan,
        master_seed=1103,
        stratum=PERSISTENT,
        arm=b1.COUNT,
    )
    changed = copy.deepcopy(row)
    if mutation == "action":
        changed["action"] = L if row["action"] == S else S
    elif mutation == "uniform":
        changed["plan"]["trial5_uniform"] = "1/2"
    elif mutation == "count":
        changed["N_L"] += 1
    elif mutation == "reward":
        changed["return_auc"] = (int(row["return_auc"]) + 1) % 3
    elif mutation == "generation":
        changed["generation"]["scheduler"] += 1
    else:
        changed["ledger_unchanged_by_trial5"] = False
    with pytest.raises(ValueError, match="independent manifest/host reconstruction"):
        b1.validate_training_row_reconstruction(
            changed,
            plan=plan,
            master_seed=1103,
            stratum=PERSISTENT,
            arm=b1.COUNT,
        )


def _accepted_retained_audit():
    return {
        "issues": {"contract": [], "leakage": [], "calibration": []},
        "persistent_count_maps_complete_by_seed": [True] * 4,
        "blind_constant_s_all_strata_by_replica": [True] * 8,
        "redraw_count_constant_s_by_seed": [True] * 4,
        "persistent_delta_positive_by_seed": [True] * 4,
        "redraw_delta_zero_by_seed": [True] * 4,
        "visit_floors_by_replica": [True] * 16,
        "matching_and_information": {
            "controller_shape_parameter_initialization_update_reward_checkpoint_match": True,
            "count_access_sole_treatment_delta": True,
        },
    }


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("contract", b1.BRANCHES[0]),
        ("leakage", b1.BRANCHES[1]),
        ("calibration", b1.BRANCHES[2]),
    ],
)
def test_integrated_retained_audit_artifact_reaches_each_early_branch(category, expected):
    audit = _accepted_retained_audit()
    audit["issues"][category] = [f"retained {category} witness failed"]
    assert b1.select_branch_from_retained_audit(
        technical_only=False, audit=audit
    ) == expected
    assert b1.select_branch_from_retained_audit(
        technical_only=True, audit=audit
    ) is None


def _full_envelope_payloads():
    config = b1.registered_config().to_json()
    source = "2" * 40
    run_id = "ucope_b1_full_envelope_unit"
    train_summary = {
        "source_commit": source,
        "run_id": run_id,
        "technical_only": False,
        "config": config,
    }
    evaluation_summary = copy.deepcopy(train_summary)
    claim = {
        "artifact_kind": "UCOPE_B1_REGISTERED_RUN_CLAIM",
        "assignment_id": b1.ASSIGNMENT_ID,
        "candidate": b1.CANDIDATE,
        "source_commit": source,
        "run_id": run_id,
        "technical_only": False,
        "canonical_result_name": "raw_result.json",
    }
    artifacts = {
        "manifest": {"sha256": "m"},
        "train_sidecar": {"sha256": "t"},
        "evaluation_sidecar": {"sha256": "e"},
        "train_summary_sha256": "ts",
        "evaluation_summary_sha256": "es",
        "registered_claim": {"sha256": "c"},
        "checkpoints": [],
    }
    result = {
        "artifact_kind": "UCOPE_B1_RESULT",
        "raw_output_binding": b1.RAW_OUTPUT_BINDING,
        "assignment_id": b1.ASSIGNMENT_ID,
        "candidate": b1.CANDIDATE,
        "source_commit": source,
        "run_id": run_id,
        "technical_only": False,
        "scientific_terminal_admitted": True,
        "branch": b1.BRANCHES[0],
        "branch_precedence": list(b1.BRANCHES),
        "config": config,
        "artifacts": artifacts,
        "forbidden_inputs": list(b1.FORBIDDEN_INPUTS),
        "claim_boundary": b1.CLAIM_BOUNDARY,
    }
    return result, train_summary, evaluation_summary, claim, artifacts


@pytest.mark.parametrize(
    "mutation",
    ["terminal", "branch_null", "source", "run", "claim", "artifact", "assignment"],
)
def test_default_mode_result_envelope_rejects_terminal_identity_claim_and_artifact_drift(mutation):
    result, train_summary, evaluation_summary, claim, artifacts = _full_envelope_payloads()
    b1.validate_result_envelope_payload(
        result=result,
        train_summary=train_summary,
        evaluation_summary=evaluation_summary,
        claim=claim,
        expected_artifacts=artifacts,
        require_full=True,
    )
    changed_result = copy.deepcopy(result)
    changed_claim = copy.deepcopy(claim)
    if mutation == "terminal":
        changed_result["scientific_terminal_admitted"] = False
    elif mutation == "branch_null":
        changed_result["branch"] = None
    elif mutation == "source":
        changed_result["source_commit"] = "3" * 40
    elif mutation == "run":
        changed_result["run_id"] = "drift"
    elif mutation == "claim":
        changed_claim["canonical_result_name"] = "alternate.json"
    elif mutation == "artifact":
        changed_result["artifacts"]["manifest"] = {"sha256": "drift"}
    else:
        changed_result["assignment_id"] = "OTHER"
    with pytest.raises(ValueError):
        b1.validate_result_envelope_payload(
            result=changed_result,
            train_summary=train_summary,
            evaluation_summary=evaluation_summary,
            claim=changed_claim,
            expected_artifacts=artifacts,
            require_full=True,
        )


def _load_runner(module_name):
    path = Path(__file__).resolve().parents[4] / "scripts" / "run_ucope_b1_persistent_count_state_learned_utility.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_full_later_phases_reapply_clean_source_identity_but_technical_skips(monkeypatch, tmp_path):
    runner = _load_runner("ucope_b1_runner_source_unit")
    calls = []
    (tmp_path / "train_summary.json").write_text(
        json.dumps({"technical_only": False, "source_commit": "4" * 40}),
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "_require_frozen_clean_source", calls.append)
    runner._require_retained_phase_source(str(tmp_path))
    assert calls == ["4" * 40]
    (tmp_path / "train_summary.json").write_text(
        json.dumps({"technical_only": True, "source_commit": "5" * 40}),
        encoding="utf-8",
    )
    runner._require_retained_phase_source(str(tmp_path))
    assert calls == ["4" * 40]


def test_gzip_lossless_rows_and_file_binding_reject_tamper(tmp_path):
    path = tmp_path / "rows.jsonl.gz"
    rows = [{"x": 1, "q": "1/3"}, {"x": 2, "q": "2/3"}]
    with b1._GzipWriter(path) as writer:
        for row in rows:
            writer.write(row)
    assert list(b1._read_jsonl(path)) == rows
    binding = b1._binding(path, rows=2)
    assert b1._validate_binding(tmp_path, binding) == path
    path.write_bytes(path.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="drift"):
        b1._validate_binding(tmp_path, binding)
