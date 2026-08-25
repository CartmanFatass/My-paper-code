from __future__ import annotations

from fractions import Fraction
import copy
import gzip
import io
import json
import os
from pathlib import Path
import shutil
import tempfile

import pytest

import experiments.candidates.ucope.endogenous_paid_count_acquisition as b2

from experiments.candidates.ucope.endogenous_paid_count_acquisition_host import (
    BUY_SL,
    COMMIT_L,
    COMMIT_S,
    L,
    PERSISTENT_POSITIVE,
    PERSISTENT_TARGET,
    REDRAW_AFTER_TWO,
    S,
    THETA_L,
    THETA_S,
    EndogenousPaidCountHost,
    Generation,
    canonical_bytes,
)
from experiments.candidates.ucope.endogenous_paid_count_acquisition import (
    ARMS,
    BLIND,
    BRANCHES,
    COUNT,
    D_VALUES,
    MASTER_SEEDS,
    NineValueController,
    RetainedValidationError,
    _assert_sample_means,
    _assert_visit_floors,
    _binding,
    _checkpoint_lookup,
    _execute_episode,
    _GzipWriter,
    _full_panel_specs,
    _information_witnesses,
    _panel_row,
    _registered_panel_values,
    _retained_audit,
    _training_plan,
    _training_row,
    _training_generation,
    build_manifest,
    expected_evaluation_counts,
    expected_training_counts,
    registered_config,
    root_observation,
    select_branch_from_audit,
    tail_observation,
    technical_smoke_config,
    total_activity_counts,
    validate_evaluation,
    validate_result,
    validate_result_envelope_payload,
)


def _uniforms(*values: str) -> list[str]:
    return list(values or ("1/20", "19/20", "1/20", "1/20", "1/20"))


def test_host_executes_paid_buy_on_exact_five_transition_shared_clock():
    generation = Generation(1, 1, 1)
    controller = NineValueController(COUNT)
    episode = _execute_episode(
        controller=controller, arm=COUNT, stratum=PERSISTENT_TARGET,
        prefix_regime=THETA_S, tail_regime=THETA_S,
        uniforms=_uniforms(), generation=generation, root_action=BUY_SL,
        tail_action=S,
    )
    assert episode["transition_count"] == 5
    assert [row["action"] for row in episode["records"]] == [S, L, S, S, S]
    assert sum(3 for _ in episode["records"]) == 15
    assert episode["acquisition_auc"] == 2
    assert episode["total_return"] == episode["acquisition_auc"] + episode["tail_return"]
    assert episode["policy_calls"] == 2


def test_host_rejects_root_action_injection_and_mixed_generation_before_policy():
    host = EndogenousPaidCountHost(
        stratum=PERSISTENT_TARGET, prefix_regime=THETA_S,
        tail_regime=THETA_S, generation=Generation(1, 1, 1),
    )
    with pytest.raises(ValueError, match="mixed generation"):
        host.root_policy_call(lambda _obs: COMMIT_S, generation=Generation(2, 2, 2))
    with pytest.raises(ValueError, match="invalid root"):
        host.root_policy_call(lambda _obs: S, generation=Generation(1, 1, 1))
    assert host.transition_count == 0


def test_free_count_and_wrong_clock_are_impossible():
    generation = Generation(3, 3, 3)
    host = EndogenousPaidCountHost(
        stratum=PERSISTENT_TARGET, prefix_regime=THETA_S,
        tail_regime=THETA_S, generation=generation,
    )
    host.force_root(BUY_SL, generation=generation)
    with pytest.raises(RuntimeError, match="after exactly two"):
        host.freeze_count(generation=generation)
    with pytest.raises(RuntimeError, match="three committed tail"):
        host.execute_remaining(uniforms=(Fraction(0),) * 3, generation=generation)


def test_redraw_lifecycle_changes_only_after_trial_two():
    episode = _execute_episode(
        controller=NineValueController(BLIND), arm=BLIND,
        stratum=REDRAW_AFTER_TWO, prefix_regime=THETA_S, tail_regime=THETA_L,
        uniforms=["1/20"] * 5, generation=Generation(4, 4, 4),
        root_action=COMMIT_S, tail_action=None,
    )
    assert [row["regime"] for row in episode["records"]] == [THETA_S, THETA_S, THETA_L, THETA_L, THETA_L]


def test_count_is_frozen_before_tail_and_postdecision_reward_cannot_mutate_it():
    generation = Generation(5, 5, 5)
    host = EndogenousPaidCountHost(
        stratum=PERSISTENT_TARGET, prefix_regime=THETA_S,
        tail_regime=THETA_S, generation=generation,
    )
    host.force_root(BUY_SL, generation=generation)
    host.execute_acquisition(uniforms=(Fraction(1, 20), Fraction(19, 20)), generation=generation)
    d, before = host.freeze_count(generation=generation)
    action, observation, at_call = host.tail_policy_call(lambda _obs: S, visible_d=d, generation=generation)
    assert action == S and before == at_call
    assert json.loads(observation) == {"phase": "TAIL", "remaining_trials": 3, "d": d}
    host.execute_remaining(uniforms=(Fraction(1, 20),) * 3, generation=generation, task_reward_placeholder={"reward": 10**9})
    assert all(row.ledger_before_sha == row.ledger_after_sha for row in host.records[2:])


def test_controller_is_exactly_nine_stateless_float64_values_with_frozen_ties():
    for arm in ARMS:
        controller = NineValueController(arm)
        assert len(controller.flat_values()) == 9
        assert len(controller.value_bytes()) == 72
        assert controller.call_root(root_observation()) == COMMIT_S
        assert all(controller.call_tail(tail_observation(arm, d)) == S for d in D_VALUES)
        assert controller.to_json()["stateless"] is True


def test_count_access_is_sole_arm_delta_and_blind_cannot_leak_true_d():
    assert root_observation() == root_observation()
    assert tail_observation(COUNT, -1) != tail_observation(COUNT, 1)
    assert tail_observation(BLIND, -1) == tail_observation(BLIND, 0) == tail_observation(BLIND, 1)
    assert set(json.loads(tail_observation(COUNT, 1))) == {"phase", "remaining_trials", "d"}


def test_histories_00_and_11_collapse_to_identical_d0_observation_and_action():
    controller = NineValueController(COUNT)
    controller.tail_values[1] = [0.25, 0.5]
    obs_00 = canonical_bytes({"phase": "TAIL", "remaining_trials": 3, "d": 0})
    obs_11 = canonical_bytes({"phase": "TAIL", "remaining_trials": 3, "d": 0})
    assert obs_00 == obs_11
    assert controller.call_tail(obs_00) == controller.call_tail(obs_11) == L
    common = dict(
        controller=controller, arm=COUNT, stratum=PERSISTENT_TARGET,
        prefix_regime=THETA_S, tail_regime=THETA_S, root_action=BUY_SL,
        tail_action=None,
    )
    history_00 = _execute_episode(
        **common, uniforms=["19/20", "11/20", "1/20", "1/20", "1/20"],
        generation=Generation(60, 60, 60),
    )
    history_11 = _execute_episode(
        **common, uniforms=["1/20", "1/20", "1/20", "1/20", "1/20"],
        generation=Generation(61, 61, 61),
    )
    assert history_00["true_d"] == history_11["true_d"] == 0
    assert history_00["acquisition_auc"] == 0 and history_11["acquisition_auc"] == 3
    assert history_00["tail_observation_hex"] == history_11["tail_observation_hex"]
    assert history_00["tail_action"] == history_11["tail_action"] == L


def test_running_means_update_only_the_selected_table_and_cell():
    controller = NineValueController(COUNT)
    root_before = controller.root_values.copy()
    controller.update_tail(-1, L, 3.0)
    controller.update_tail(-1, L, 1.0)
    assert controller.tail_values[0] == [0.0, 2.0]
    assert controller.root_values == root_before
    tail_before = [row.copy() for row in controller.tail_values]
    controller.update_root(BUY_SL, 7.0)
    controller.update_root(BUY_SL, 3.0)
    assert controller.root_values == [0.0, 0.0, 5.0]
    assert controller.tail_values == tail_before


@pytest.mark.parametrize("stratum", [PERSISTENT_TARGET, PERSISTENT_POSITIVE, REDRAW_AFTER_TWO])
@pytest.mark.parametrize("seed", MASTER_SEEDS)
def test_tail_action_tapes_are_balanced_deterministic_and_arm_independent(stratum, seed):
    config = registered_config()
    first = _training_plan(config, seed, stratum)
    second = _training_plan(config, seed, stratum)
    assert first == second
    tail = [row for row in first if row["phase"] == "TAIL_FIT"]
    assert len(tail) == 1536
    assert sum(row["tail_action"] == S for row in tail) == 768
    assert sum(row["tail_action"] == L for row in tail) == 768
    assert all("d" not in row for row in tail)


def test_root_triads_share_exact_environment_tape_and_are_balanced():
    plan = _training_plan(registered_config(), MASTER_SEEDS[0], PERSISTENT_TARGET)
    rows = [row for row in plan if row["phase"] == "ROOT_FIT"]
    assert len(rows) == 2304
    for offset in range(0, len(rows), 3):
        triad = rows[offset:offset + 3]
        assert [row["root_action"] for row in triad] == [COMMIT_S, COMMIT_L, BUY_SL]
        assert len({json.dumps({k: row[k] for k in ("prefix_regime", "tail_regime", "uniforms")}, sort_keys=True) for row in triad}) == 1


def test_count_and_blind_training_rows_share_generation_and_noncount_tape():
    spec = _training_plan(technical_smoke_config(), 1709, PERSISTENT_TARGET)[0]
    generation = _training_generation(1709, PERSISTENT_TARGET, 0)
    count_row = _training_row(
        controller=NineValueController(COUNT), arm=COUNT,
        stratum=PERSISTENT_TARGET, seed=1709, spec=spec,
        generation_index=generation,
    )
    blind_row = _training_row(
        controller=NineValueController(BLIND), arm=BLIND,
        stratum=PERSISTENT_TARGET, seed=1709, spec=spec,
        generation_index=generation,
    )
    assert count_row["generation"] == blind_row["generation"]
    assert count_row["plan"] == blind_row["plan"]
    assert count_row["episode"]["records"] == blind_row["episode"]["records"]


def test_registered_activity_caps_and_fixed_reference_policy_calls_are_frozen():
    train_counts = expected_training_counts(registered_config().to_json())
    eval_counts = expected_evaluation_counts(registered_config().to_json())
    total = total_activity_counts(registered_config().to_json())
    assert train_counts == {
        "learned_replicas": 12, "training_episodes": 46080,
        "training_env_transitions": 230400, "training_policy_calls": 55296,
        "training_learner_updates": 46080, "training_trainer_updates": 46080,
        "training_optimizer_updates": 46080, "final_checkpoints": 12,
    }
    assert eval_counts == {
        "learned_rows": 1552, "fixed_reference_rows": 388,
        "evaluation_episodes": 1940, "evaluation_env_transitions": 9700,
        "evaluation_policy_call_cap": 3492,
    }
    assert (total["total_episodes"], total["total_env_transitions"], total["total_policy_call_cap"]) == (48020, 240100, 58788)


def test_technical_activity_is_small_and_terminal_inadmissible_by_config():
    total = total_activity_counts(technical_smoke_config().to_json())
    assert total["training_episodes"] == 576
    assert total["evaluation_episodes"] == 260
    assert total["total_episodes"] == 836
    assert total["full_runs"] == 0


def test_exact_full_panel_cardinalities_are_frozen():
    assert len(_full_panel_specs(PERSISTENT_TARGET)) == 64
    assert len(_full_panel_specs(REDRAW_AFTER_TWO)) == 128
    assert len(_full_panel_specs(PERSISTENT_POSITIVE)) == 2


@pytest.mark.parametrize("regime", [THETA_S, THETA_L])
@pytest.mark.parametrize("mode", ["GREEDY_ROOT", "FORCED_BUY", f"FIXED_{COMMIT_S}", f"FIXED_{COMMIT_L}"])
def test_positive_panel_derives_all_deterministic_marks_after_adaptive_tail(regime, mode):
    controller = NineValueController(COUNT)
    controller.tail_values[0] = [1.0, 0.0]
    controller.tail_values[2] = [0.0, 1.0]
    if mode == "GREEDY_ROOT":
        controller.root_values[2] = 1.0
    arm = COUNT if not mode.startswith("FIXED_") else "FIXED_REFERENCE"
    row = _panel_row(
        controller=controller, arm=arm, stratum=PERSISTENT_POSITIVE, seed=1709,
        mode=mode, prefix_regime=regime, tail_regime=regime, marks=None,
        generation_index=123,
    )
    assert row["episode"]["transition_count"] == 5
    assert row["weight"] == "1/2"


def test_full_exact_real_panels_reproduce_all_registered_values_with_ideal_maps():
    rows = []
    generation = 5000
    for stratum in (PERSISTENT_TARGET, PERSISTENT_POSITIVE, REDRAW_AFTER_TWO):
        specs = _full_panel_specs(stratum)
        for seed in MASTER_SEEDS:
            for arm in ARMS:
                controller = NineValueController(arm)
                if arm == COUNT and stratum != REDRAW_AFTER_TWO:
                    controller.tail_values[0] = [1.0, 0.0]
                    controller.tail_values[1] = [1.0, 0.0]
                    controller.tail_values[2] = [0.0, 1.0]
                    controller.root_values[2] = 1.0
                for mode in ("GREEDY_ROOT", "FORCED_BUY"):
                    for prefix, tail, marks in specs:
                        rows.append(_panel_row(
                            controller=controller, arm=arm, stratum=stratum, seed=seed,
                            mode=mode, prefix_regime=prefix, tail_regime=tail, marks=marks,
                            generation_index=generation,
                        ))
                        generation += 1
        for root_action in (COMMIT_S, COMMIT_L):
            controller = NineValueController(BLIND)
            for prefix, tail, marks in specs:
                rows.append(_panel_row(
                    controller=controller, arm="FIXED_REFERENCE", stratum=stratum,
                    seed=None, mode=f"FIXED_{root_action}", prefix_regime=prefix,
                    tail_regime=tail, marks=marks, generation_index=generation,
                ))
                generation += 1
    values = _registered_panel_values(rows)
    for stratum, expected in {
        PERSISTENT_POSITIVE: {"B": "5", "A_C": "6", "A_B": "9/2", "U": "3/2", "Gamma": "1"},
        PERSISTENT_TARGET: {"B": "5", "A_C": "213/40", "A_B": "9/2", "U": "33/40", "Gamma": "13/40"},
        REDRAW_AFTER_TWO: {"B": "5", "A_C": "9/2", "A_B": "9/2", "U": "0", "Gamma": "-1/2"},
    }.items():
        for seed in MASTER_SEEDS:
            assert {key: values[stratum][str(seed)][key] for key in expected} == expected


def test_manifest_binds_source_claim_caps_and_pairing_without_training_targets():
    manifest = build_manifest(config=registered_config(), source_commit="abc", run_id="run")
    assert manifest["source_commit"] == "abc"
    assert manifest["activity_caps"]["total_env_transitions"] == 240100
    assert manifest["matching"]["count_access_sole_arm_delta"] is True
    assert "registered_estimands_evaluation_only" in manifest
    assert len(manifest["plans"]) == 6


@pytest.mark.parametrize(
    "audit,expected",
    [
        ({"contract_valid": False}, BRANCHES[0]),
        ({"contract_valid": True, "calibration_pass": False}, BRANCHES[1]),
        ({"contract_valid": True, "calibration_pass": True, "visit_floor_pass": True, "all_target_tail_and_u": True, "all_target_decline_or_no_net": True}, BRANCHES[2]),
        ({"contract_valid": True, "calibration_pass": True, "visit_floor_pass": True, "all_target_positive_net": True, "any_redraw_specificity_failure": True}, BRANCHES[3]),
        ({"contract_valid": True, "calibration_pass": True, "visit_floor_pass": True, "full_support": True}, BRANCHES[4]),
        ({"contract_valid": True, "calibration_pass": True, "visit_floor_pass": False, "full_support": True}, BRANCHES[5]),
        ({"contract_valid": True, "calibration_pass": True, "visit_floor_pass": True}, BRANCHES[5]),
    ],
)
def test_frozen_branch_precedence_is_fail_closed(audit, expected):
    assert select_branch_from_audit(audit) == expected


def _full_visit_controller(arm: str, stratum: str) -> NineValueController:
    controller = NineValueController(arm)
    controller.root_visits = [768, 768, 768]
    if arm == BLIND:
        controller.tail_visits = [[0, 0], [768, 768], [0, 0]]
    elif stratum == PERSISTENT_POSITIVE:
        controller.tail_visits = [[384, 384], [0, 0], [384, 384]]
    else:
        controller.tail_visits = [[256, 256], [256, 256], [256, 256]]
    return controller


def _checkpoint_artifacts(root: Path, mutation=None):
    summary = {"source_commit": "source", "run_id": "run", "technical_only": False}
    checkpoint_dir = root / "checkpoints"
    checkpoint_dir.mkdir(parents=True)
    bindings = []
    index = 0
    for seed in MASTER_SEEDS:
        for stratum in (PERSISTENT_TARGET, PERSISTENT_POSITIVE, REDRAW_AFTER_TWO):
            for arm in ARMS:
                controller = _full_visit_controller(arm, stratum)
                value = {
                    "schema_version": 1,
                    "artifact_kind": "UCOPE_B2_FINAL_CHECKPOINT",
                    "source_commit": "source",
                    "run_id": "run",
                    "technical_only": False,
                    "seed": seed,
                    "stratum": stratum,
                    "arm": arm,
                    "controller": controller.to_json(),
                }
                filename = f"{stratum.lower()}_{arm.lower()}_{seed}_final.json"
                if mutation is not None and index == 0:
                    filename, value = mutation(filename, value, controller)
                path = checkpoint_dir / filename
                path.write_bytes(canonical_bytes(value) + b"\n")
                bindings.append(_binding(path))
                index += 1
    summary["checkpoints"] = bindings
    return summary


@pytest.mark.parametrize(
    "field,bad",
    [
        ("schema_version", 2),
        ("artifact_kind", "OTHER"),
        ("source_commit", "other"),
        ("run_id", "other"),
        ("technical_only", True),
        ("seed", 999),
        ("stratum", REDRAW_AFTER_TWO),
        ("arm", BLIND),
    ],
)
def test_checkpoint_loader_rejects_every_identity_field_mutation(field, bad):
    with tempfile.TemporaryDirectory(prefix="ucope_b2_checkpoint_", dir=Path.cwd()) as temporary:
        def mutate(filename, value, _controller):
            value[field] = bad
            return filename, value

        summary = _checkpoint_artifacts(Path(temporary), mutate)
        with pytest.raises(ValueError, match="checkpoint"):
            _checkpoint_lookup(Path(temporary), summary)


def test_checkpoint_loader_rejects_filename_binding_controller_arm_and_extra_field():
    mutations = (
        lambda _filename, value, _controller: ("substituted.json", value),
        lambda filename, value, _controller: (filename, {**value, "controller": NineValueController(BLIND).to_json()}),
        lambda filename, value, _controller: (filename, {**value, "extra": True}),
    )
    for mutation in mutations:
        with tempfile.TemporaryDirectory(prefix="ucope_b2_checkpoint_", dir=Path.cwd()) as temporary:
            summary = _checkpoint_artifacts(Path(temporary), mutation)
            with pytest.raises(ValueError, match="checkpoint"):
                _checkpoint_lookup(Path(temporary), summary)


def _ideal_classification_metrics():
    maps = {}
    panels = {}
    for stratum in (PERSISTENT_TARGET, PERSISTENT_POSITIVE, REDRAW_AFTER_TWO):
        panels[stratum] = {}
    for seed in MASTER_SEEDS:
        maps[str(seed)] = {}
        for stratum in (PERSISTENT_TARGET, PERSISTENT_POSITIVE, REDRAW_AFTER_TWO):
            count_tail = {"-1": S, "0": S, "1": L} if stratum != REDRAW_AFTER_TWO else {"-1": S, "0": S, "1": S}
            maps[str(seed)][stratum] = {
                COUNT: {"root": BUY_SL if stratum != REDRAW_AFTER_TWO else COMMIT_S, "tail": count_tail},
                BLIND: {"root": COMMIT_S, "tail": {"-1": S, "0": S, "1": S}},
            }
            registered = {
                PERSISTENT_POSITIVE: {"B": "5", "A_C": "6", "A_B": "9/2", "U": "3/2", "Gamma": "1", "J_COUNT": "6", "J_BLIND": "5"},
                PERSISTENT_TARGET: {"B": "5", "A_C": "213/40", "A_B": "9/2", "U": "33/40", "Gamma": "13/40", "J_COUNT": "213/40", "J_BLIND": "5"},
                REDRAW_AFTER_TWO: {"B": "5", "A_C": "9/2", "A_B": "9/2", "U": "0", "Gamma": "-1/2", "J_COUNT": "5", "J_BLIND": "5"},
            }[stratum]
            panels[stratum][str(seed)] = registered
    return {"policy_maps": maps, "exact_panels": panels, "information_witnesses": {"all": True}}


@pytest.mark.parametrize(
    "mutation,expected_branch,issue_key",
    [
        ("sample_mean", BRANCHES[1], "calibration_issues"),
        ("visit_floor", BRANCHES[5], "visit_floor_issues"),
    ],
)
def test_retained_checkpoint_artifact_failures_keep_typed_branch_classification(monkeypatch, mutation, expected_branch, issue_key):
    with tempfile.TemporaryDirectory(prefix="ucope_b2_typed_", dir=Path.cwd()) as temporary:
        def mutate(_filename, value, controller):
            if mutation == "sample_mean":
                controller.root_values[0] = 1.0
            else:
                controller.root_visits[0] = 767
            value["controller"] = controller.to_json()
            return _filename, value

        root = Path(temporary)
        summary = _checkpoint_artifacts(root, mutate)

        def retained_train(_root, require_full=None):
            assert require_full is True
            loaded = _checkpoint_lookup(root, summary)
            for (_seed, stratum, _arm), controller in loaded.items():
                _assert_sample_means(controller)
                _assert_visit_floors(controller, stratum, require_full=True)
            return summary

        monkeypatch.setattr(b2, "validate_train", retained_train)
        monkeypatch.setattr(b2, "validate_evaluation", lambda *_args, **_kwargs: {})
        audit = _retained_audit(root, _ideal_classification_metrics())
        assert audit["contract_valid"] is True
        assert audit[issue_key]
        assert select_branch_from_audit(audit) == expected_branch


def _envelope_fixture():
    config = technical_smoke_config().to_json()
    train = {
        "source_commit": "source", "run_id": "run", "technical_only": True,
        "config": config, "activity_counts": expected_training_counts(config),
    }
    evaluation_counts = expected_evaluation_counts(config)
    evaluation_counts["evaluation_policy_calls"] = 300
    evaluation = {
        "source_commit": "source", "run_id": "run", "technical_only": True,
        "activity_counts": evaluation_counts,
    }
    metrics = {"metric": True}
    audit = {"technical_only": True, "contract_valid": True}
    artifacts = {
        "registered_claim": {"path": "registered_claim.json"},
        "frozen_manifest": {"path": "frozen_manifest.json"},
        "train_summary": {"path": "train_summary.json"},
        "evaluation_summary": {"path": "evaluation_summary.json"},
        "train_rows": {"path": "train_rows.jsonl.gz"},
        "evaluation_rows": {"path": "evaluation_rows.jsonl.gz"},
        "checkpoints": [{"path": "one.json"}],
    }
    result = {
        "schema_version": 1, "artifact_kind": "UCOPE_B2_RESULT",
        "assignment_id": "UCOPE-B2-ENDOGENOUS-PAID-COUNT-ACQUISITION",
        "candidate": "CAND-VSP-07-UCOPE@adversarial-revision-v6",
        "host_id": "ucope_paid_count_five_trial_fifteen_unit_host_v1",
        "raw_output_binding": "ucope.endogenous_paid_count_acquisition.v1",
        "source_commit": "source", "run_id": "run", "technical_only": True,
        "scientific_terminal_admitted": False, "branch_precedence": list(BRANCHES),
        "branch": None, "config": config,
        "activity_counts": b2.analyze_activity(train, evaluation),
        "metrics": metrics, "retained_audit": audit, "artifacts": artifacts,
    }
    return result, train, evaluation, metrics, audit, artifacts


@pytest.mark.parametrize(
    "field,bad",
    [
        ("schema_version", 2), ("artifact_kind", "OTHER"),
        ("assignment_id", "OTHER"), ("candidate", "OTHER"),
        ("host_id", "OTHER"), ("raw_output_binding", "OTHER"),
        ("source_commit", "OTHER"), ("run_id", "OTHER"),
        ("technical_only", False), ("scientific_terminal_admitted", True),
        ("branch_precedence", list(reversed(BRANCHES))), ("branch", BRANCHES[0]),
        ("config", {}), ("activity_counts", {}), ("metrics", {}),
        ("retained_audit", {}),
    ],
)
def test_result_envelope_rejects_every_identity_and_bound_payload_mutation(field, bad):
    result, train, evaluation, metrics, audit, artifacts = _envelope_fixture()
    result[field] = bad
    with pytest.raises(ValueError, match="result"):
        validate_result_envelope_payload(
            result, train_summary=train, evaluation_summary=evaluation,
            expected_metrics=metrics, expected_audit=audit, expected_branch=None,
            expected_artifacts=artifacts,
        )


def test_result_envelope_rejects_missing_substituted_and_extra_artifact_entries():
    for mutate in (
        lambda value: value.pop("registered_claim"),
        lambda value: value.update({"train_rows": {"path": "substitute.gz"}}),
        lambda value: value.update({"extra": {"path": "extra.json"}}),
    ):
        result, train, evaluation, metrics, audit, artifacts = _envelope_fixture()
        result["artifacts"] = copy.deepcopy(artifacts)
        mutate(result["artifacts"])
        with pytest.raises(ValueError, match="artifacts"):
            validate_result_envelope_payload(
                result, train_summary=train, evaluation_summary=evaluation,
                expected_metrics=metrics, expected_audit=audit, expected_branch=None,
                expected_artifacts=artifacts,
            )


def test_result_envelope_rejects_missing_or_extra_top_level_key():
    for mutate in (
        lambda value: value.pop("schema_version"),
        lambda value: value.update({"extra": True}),
    ):
        result, train, evaluation, metrics, audit, artifacts = _envelope_fixture()
        mutate(result)
        with pytest.raises(ValueError, match="key set"):
            validate_result_envelope_payload(
                result, train_summary=train, evaluation_summary=evaluation,
                expected_metrics=metrics, expected_audit=audit, expected_branch=None,
                expected_artifacts=artifacts,
            )


def test_evaluation_summary_rejects_technical_mode_drift_before_rows(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="ucope_b2_eval_identity_", dir=Path.cwd()) as temporary:
        root = Path(temporary)
        train = {"source_commit": "source", "run_id": "run", "technical_only": True}
        monkeypatch.setattr(b2, "validate_train", lambda *_args, **_kwargs: train)
        (root / "evaluation_summary.json").write_bytes(canonical_bytes({
            "schema_version": 1, "artifact_kind": "UCOPE_B2_EVALUATION_SUMMARY",
            "source_commit": "source", "run_id": "run", "technical_only": False,
        }) + b"\n")
        with pytest.raises(ValueError, match="identity"):
            validate_evaluation(root, require_full=False)


def test_information_witnesses_are_complete_and_boolean():
    dummy = {
        str(seed): {
            stratum: {
                arm: {
                    "tail": {str(d): S for d in D_VALUES},
                    "controller": NineValueController(arm).to_json(),
                }
                for arm in ARMS
            }
            for stratum in (PERSISTENT_TARGET, PERSISTENT_POSITIVE, REDRAW_AFTER_TWO)
        }
        for seed in MASTER_SEEDS
    }
    witnesses = _information_witnesses(dummy)
    assert len(witnesses) == 8
    assert all(value is True for value in witnesses.values())


def _retained_root() -> Path:
    value = os.environ.get("UCOPE_B2_RETAINED_TECHNICAL_ROOT")
    if not value:
        pytest.skip("retained technical lifecycle is checked only after its unique authorized execution")
    return Path(value)


def test_retained_technical_result_rejects_claim_result_and_checkpoint_tamper():
    source = _retained_root()
    with tempfile.TemporaryDirectory(prefix="ucope_b2_retained_", dir=Path.cwd()) as temporary:
        clean = Path(temporary) / "clean"
        shutil.copytree(source, clean)
        result = clean / "raw_result.json"
        accepted = validate_result(result, require_full=False, output_root=clean)
        assert accepted["technical_only"] is True
        assert accepted["scientific_terminal_admitted"] is False
        assert accepted["branch"] is None

        claim = json.loads((clean / "registered_claim.json").read_text())
        claim["candidate"] = "tampered"
        (clean / "registered_claim.json").write_text(json.dumps(claim), encoding="utf-8")
        with pytest.raises(ValueError):
            validate_result(result, require_full=False, output_root=clean)

        shutil.rmtree(clean)
        shutil.copytree(source, clean)
        result = clean / "raw_result.json"
        payload = json.loads(result.read_text())
        payload["scientific_terminal_admitted"] = True
        result.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ValueError, match="terminal"):
            validate_result(result, require_full=False, output_root=clean)

        shutil.rmtree(clean)
        shutil.copytree(source, clean)
        extra = clean / "checkpoints" / "extra.json"
        extra.write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError, match="checkpoint set"):
            validate_result(clean / "raw_result.json", require_full=False, output_root=clean)


def test_gzip_row_sidecar_is_lossless_canonical_json():
    with tempfile.TemporaryDirectory(prefix="ucope_b2_gzip_", dir=Path.cwd()) as temporary:
        path = Path(temporary) / "rows.jsonl.gz"
        value = {"z": [1, 2], "a": "x"}
        with path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as stream:
                    stream.write(canonical_bytes(value).decode() + "\n")
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            assert json.loads(stream.readline()) == value


def test_production_gzip_writer_is_fully_closed_before_binding():
    with tempfile.TemporaryDirectory(prefix="ucope_b2_writer_", dir=Path.cwd()) as temporary:
        path = Path(temporary) / "rows.jsonl.gz"
        writer = _GzipWriter(path)
        writer.write({"row": 1})
        writer.close()
        size = path.stat().st_size
        with path.open("ab") as stream:
            assert stream.tell() == size
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            assert json.loads(stream.readline()) == {"row": 1}
