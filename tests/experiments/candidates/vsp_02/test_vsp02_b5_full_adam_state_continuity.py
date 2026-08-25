from __future__ import annotations

from copy import deepcopy
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.candidates.vsp_02 import learned_cue_conditioned_lifecycle_control_v2 as b1
from experiments.candidates.vsp_02 import vsp02_b5_full_adam_state_continuity as b5


@pytest.fixture(scope="module")
def manifest() -> dict[str, object]:
    return b5.build_manifest(source_revision="a" * 40, run_id="B5-TECHNICAL", technical_only=True)


@pytest.fixture(scope="module")
def preflight(manifest: dict[str, object]) -> dict[str, object]:
    return b5.preflight_report(manifest)


def test_fresh_exact_namespace_roots_streams_and_no_predecessor_collision(manifest: dict[str, object], preflight: dict[str, object]) -> None:
    assert b5.B5_UNITS == tuple((f"VSP02-B5-U{i:02d}", 22_050_000 + i) for i in range(1, 6))
    assert manifest["seed_prefix"] == "VSP02-B5-V1\0"
    assert manifest["seed_streams"] == [
        "parameter_initialization", "optimizer_initialization", "training_address_tape",
        "learner_stochasticity", "minibatch_order", "evaluation_address_tape",
    ]
    report = preflight["seed_and_tape"]
    assert report["all_b5_roots_unique"] is True
    assert report["collision_with_predecessor_values"] == []
    assert report["identity_collision_with_predecessors"] is False
    assert report["predecessor_or_g52_state_reuse"] is False


def test_fresh_address_tape_is_pure_immutable_and_reproducible() -> None:
    unit, root = b5.B5_UNITS[0]
    tape = b5.B5AddressTape(unit, root)
    receipt = b5._update_tape_receipt(tape, 1)
    assert receipt == b5._update_tape_receipt(b5.B5AddressTape(unit, root), 1)
    assert tape.address("environment_randomness", 1, 0)["treatment"] == b5.B5_ASSIGNMENT_ID
    with pytest.raises(Exception):
        tape.unit_id = "mutated"  # type: ignore[misc]


def test_source_uses_only_stable_b1_a1_primitives_and_defines_fresh_host_and_tape() -> None:
    source = Path(b5.__file__).read_text(encoding="utf-8")
    assert "self_generated_closed_loop_feedback" not in source
    assert "vsp02_b3_lifecycle_credit_sign_bridge" not in source
    assert "vsp02_b2_paired_shadow_learner_localization" not in source
    assert "import G52" not in source and "from G52" not in source
    assert "class B5LifecycleHost" in source and "class B5AddressTape" in source
    host = b5.B5LifecycleHost()
    host.reset(lifecycle_id="B5-HOST-PROOF", owner_epoch="E0", true_cue=0, presented_cue=0)
    episode = host.step(b1.Action.HOLD, action_probabilities=(0.5, 0.5))
    assert episode["reward_sequence"] == [2, 0]
    assert episode["environment_transitions"] == 5
    assert episode["physical_tape_ids"][0].startswith(f"{b5.B5_PHYSICAL_TAPE_PREFIX}/")


def test_complete_adam_fork_reset_update1_and_q_are_proven_for_every_root(preflight: dict[str, object]) -> None:
    assert preflight["all_passed"] is True
    assert b5.validate_preflight_evidence(preflight={**preflight}, manifest=preflight_manifest(preflight)) == ()
    assert len(preflight["boundary_proofs"]) == 5
    for proof in preflight["boundary_proofs"]:
        reset = proof["reset_receipt"]
        adam = reset["post_update0_adam_state"]
        assert reset["pre_reset_complete_state_byte_identical"] is True
        assert reset["reset_slots_canonical_fresh_empty"] is True
        assert reset["carry_slots_retained_exactly"] is True
        assert reset["parameter_groups_identical_before_after"] is True
        assert adam["all_steps_exactly_one"] is True
        assert adam["all_slots_finite"] is True
        assert adam["globally_at_least_one_moment_nonzero"] is True
        assert proof["update1_batches_frozen_before_updates"] is True
        assert proof["update1_batch_byte_identical"] is True
        assert proof["update1_prepared_byte_identical"] is True
        assert proof["q_finite_positive"] is True and proof["q_r"] > 0.0
        assert proof["parameter_hashes_differ_after_update1"] is True


def preflight_manifest(preflight: dict[str, object]) -> dict[str, object]:
    # The fixture uses this exact immutable manifest identity.
    value = b5.build_manifest(source_revision="a" * 40, run_id="B5-TECHNICAL", technical_only=True)
    assert b5.manifest_identity(value) == preflight["manifest_identity"]
    return value


def test_update1_equality_covers_forward_loss_raw_and_clipped_gradients_norm_factor(preflight: dict[str, object]) -> None:
    required = {
        "forward_values", "loss", "loss_components", "raw_gradients", "raw_gradient_digest",
        "clipped_gradients", "clipped_gradient_digest", "gradient_norm_before_clip", "clip_factor",
    }
    for proof in preflight["boundary_proofs"]:
        payloads = proof["update1_prepared_payloads"]
        assert required <= set(payloads["ADAM_CARRY"])
        assert b5.canonical_bytes(payloads["ADAM_CARRY"]) == b5.canonical_bytes(payloads["ADAM_RESET"])
        receipt = {
            "both_batches_frozen_before_either_update": True,
            "batch_byte_identical": True,
            "ordered_rows_byte_identical": True,
            "forward_loss_raw_clipped_gradient_norm_factor_byte_identical": True,
            "prepared_comparison_payloads": deepcopy(payloads),
            "q_r": proof["q_r"], "q_finite_positive": True,
            "parameter_hashes": deepcopy(proof["parameter_hashes_after_update1"]),
            "parameter_hashes_differ": True,
        }
        assert b5._validate_retained_update1_receipt("PROOF", receipt) == ()
        payload_tamper = deepcopy(receipt)
        payload_tamper["prepared_comparison_payloads"]["ADAM_RESET"]["loss"] += 1.0
        assert any("prepared payload equality" in issue for issue in b5._validate_retained_update1_receipt("PROOF", payload_tamper))
        hash_tamper = deepcopy(receipt)
        hash_tamper["parameter_hashes"]["ADAM_RESET"] = hash_tamper["parameter_hashes"]["ADAM_CARRY"]
        assert any("parameter hashes" in issue for issue in b5._validate_retained_update1_receipt("PROOF", hash_tamper))
        extra_arm_tamper = deepcopy(receipt)
        extra_arm_tamper["parameter_hashes"]["EXTRA_ARM"] = "unexpected"
        assert b5._validate_retained_update1_receipt("PROOF", extra_arm_tamper)


def test_common_update0_and_later_fixed_order_noninterference_with_immutable_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    unit, root = b5.B5_UNITS[0]
    monkeypatch.setattr(b5, "B5_UPDATES_PER_ARM", 3)
    original_schedule = b5._schedule
    monkeypatch.setattr(b5, "_schedule", lambda u, r: original_schedule(u, r)[:24])
    monkeypatch.setattr(b5, "_schedule_contract", lambda rows: len(rows) == 24)
    trained = b5._train_unit(unit, root)["training"]
    assert trained["real_training_episodes"] == 2_040  # registered accounting remains frozen
    assert trained["common_update0_receipt"]["update"]["oracle_scalar_only"] is True
    assert trained["fixed_update_order"] == ["ADAM_CARRY", "ADAM_RESET"]
    assert trained["later_differences_are_unmatched_descendants"] is True
    assert trained["update1_q_receipt"]["both_batches_frozen_before_either_update"] is True
    for receipt in trained["barrier_receipts"]:
        assert receipt["frozen_before"] == receipt["frozen_after"]
        assert receipt["carry_update_preserved_reset"] is True
        assert receipt["reset_update_preserved_carry"] is True


def test_oracle_firewall_sign_magnitude_detach_and_no_direct_label_loss(monkeypatch: pytest.MonkeyPatch) -> None:
    model, optimizer = b5._new_common_learner(*b5.B5_UNITS[0])
    batch = b5._proof_batch(model, tag="ORACLE-FIREWALL")
    calls: list[tuple[str, int]] = []
    original = b5.correctness_sign
    monkeypatch.setattr(b5, "correctness_sign", lambda action, cue: calls.append((action, cue)) or original(action, cue))
    prepared = b5._prepare_update(model, optimizer, batch)
    assert len(calls) == 8
    assert prepared["oracle_scalar_only"] is True and prepared["oracle_access_after_forward"] is True
    assert all(abs(coefficient) == pytest.approx(abs(advantage), abs=1e-12)
               for coefficient, advantage in zip(prepared["actor_coefficients"], prepared["advantages"]))
    assert b5.build_manifest(source_revision="a", run_id="x", technical_only=True)["loss_contract"]["direct_label_or_cross_entropy"] is False


def test_manifest_freezes_counts_caps_complexity_no_retry_and_nonclaims(manifest: dict[str, object]) -> None:
    assert manifest["expected_activity"] == {"real_training_episodes": 10_200, "optimizer_updates": 1_275, "evaluation_episodes": 1_280, "checkpoints_total": 10}
    assert manifest["caps"] == b5.B5_CAPS
    assert manifest["evidence_complexity"] == {"H": 4, "K_search": 0, "hypothetical_transitions": 0}
    assert manifest["retry_rescue_sweep_extra_root_checkpoint_threshold_boundary"] == 0
    assert manifest["result_bearing_runs"] == 0
    joined = " ".join(manifest["nonclaims"])
    for phrase in ("B4", "G52", "component attribution", "population", "branch 2", "branch 5", "branch 6"):
        assert phrase in joined


def test_retained_evaluation_metric_recomputes_exact_panel_and_rejects_row_or_summary_tampering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("pure retained evaluation derivation called runtime")

    monkeypatch.setattr(b5, "B5LifecycleHost", forbidden)
    monkeypatch.setattr(b5, "_evaluate_arm_unit", forbidden)
    monkeypatch.setattr(b5, "_new_common_learner", forbidden)
    monkeypatch.setattr(b1, "GRUActorCritic", forbidden)
    unit_id, root = b5.B5_UNITS[0]
    arm = "ADAM_CARRY"
    final_hash = "retained-final-model-hash"
    panel = b5._evaluation_panel(unit_id, root)
    records: list[dict[str, object]] = []
    releases: dict[int, list[float]] = {0: [], 1: []}
    transitions = 0
    for row in panel:
        cue = int(row["true_cue"])
        logits = [0.0, 1.0] if cue == 0 else [1.0, 0.0]
        exponentials = [math.exp(value - max(logits)) for value in logits]
        raw = [value / sum(exponentials) for value in exponentials]
        probabilities = [0.8 * value + 0.1 for value in raw]
        choice = "HOLD" if cue == 0 else "RELEASE"
        row_transitions = 5 if cue == 0 else 4
        releases[cue].append(raw[0])
        transitions += row_transitions
        records.append({
            "clone_id": row["clone_id"], "owner_epoch": row["owner_epoch"],
            "event_tape_token": row["event_tape_token"], "true_cue": cue,
            "logits": logits, "raw_softmax": raw, "behavior_probabilities": probabilities,
            "argmax_action": choice, "environment_transitions": row_transitions,
        })
    q0, q1 = sum(releases[0]) / 64, sum(releases[1]) / 64
    metric = {
        "unit_id": unit_id, "arm": arm,
        "checkpoint_id": f"{b5.B5_ASSIGNMENT_ID}/{unit_id}/{arm}/FINAL-128",
        "panel_digest": b5.digest(panel), "episodes": 128, "cue_counts": {"0": 64, "1": 64},
        "environment_transitions": transitions, "finite_logits": True, "argmax_ties": 0,
        "exact_correct_unit": True, "q_0": q0, "q_1": q1,
        **b5._mixture_metrics_from_raw_q(q0=q0, q1=q1),
        "evaluation_updates": 0, "stochastic_action_draws": 0,
        "final_model_hash": final_hash, "clone_records": records,
    }
    derived, issues = b5._derive_retained_evaluation_metric(
        unit_id=unit_id, root=root, arm=arm, metric=metric, expected_final_hash=final_hash)
    assert issues == [] and derived is not None
    assert derived["episodes"] == 128 and derived["cue_counts"] == {"0": 64, "1": 64}
    assert derived["argmax_ties"] == 0 and derived["exact_correct_unit"] is True
    assert derived["q_0"] == pytest.approx(q0, abs=1e-12)
    assert derived["q_1"] == pytest.approx(q1, abs=1e-12)
    assert derived["j_eval"] == pytest.approx(metric["j_eval"], abs=1e-12)
    assert derived["kappa"] == pytest.approx(metric["kappa"], abs=1e-12)
    row_tamper = deepcopy(metric)
    row_tamper["clone_records"][0]["argmax_action"] = "RELEASE" if row_tamper["clone_records"][0]["argmax_action"] == "HOLD" else "HOLD"
    assert b5._derive_retained_evaluation_metric(
        unit_id=unit_id, root=root, arm=arm, metric=row_tamper, expected_final_hash=final_hash)[1]
    summary_tamper = deepcopy(metric)
    summary_tamper["exact_correct_unit"] = False
    summary_tamper["argmax_ties"] = 1
    summary_issues = b5._derive_retained_evaluation_metric(
        unit_id=unit_id, root=root, arm=arm, metric=summary_tamper, expected_final_hash=final_hash)[1]
    assert any("exact_correct_unit projection mismatch" in issue for issue in summary_issues)
    assert any("argmax_ties projection mismatch" in issue for issue in summary_issues)


@pytest.mark.parametrize(
    ("carry", "reset", "branch"),
    [
        (set(), set(), "B5_NEITHER_ARM_EXACT_SUCCESS_ON_PANEL"),
        ({"U1"}, set(), "B5_CARRY_DIRECTION_DISCORDANCE_ONLY"),
        (set(), {"U1"}, "B5_RESET_DIRECTION_DISCORDANCE_ONLY"),
        ({"U1"}, {"U1"}, "B5_NO_EXACT_ENDPOINT_LOCALIZATION_ON_PANEL"),
        ({"U1"}, {"U2"}, "B5_BIDIRECTIONAL_PAIRED_ROOT_TAPE_DISCORDANCE"),
    ],
)
def test_six_branch_first_match_precedence_is_total(carry: set[str], reset: set[str], branch: str) -> None:
    assert b5.classify_b5(valid=False, carry_success=carry, reset_success=reset) == "B5_INVALID_OR_INACTIVE"
    assert b5.classify_b5(valid=True, carry_success=carry, reset_success=reset) == branch


def test_retained_validators_have_no_runtime_call_surface(monkeypatch: pytest.MonkeyPatch, manifest: dict[str, object], preflight: dict[str, object]) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("pure retained validation called runtime")
    for name in ("preflight_report", "run_treatment", "train_registered_full", "evaluate_registered_full", "analyze_registered_full",
                 "_train_unit", "_evaluate_arm_unit", "_new_common_learner"):
        monkeypatch.setattr(b5, name, forbidden)
    assert b5.validate_preflight_evidence(manifest, preflight) == ()
    mutated = deepcopy(preflight)
    mutated["activity"]["optimizer_updates"] = 1
    assert b5.validate_preflight_evidence(manifest, mutated)


def _load_runner():
    path = Path(__file__).resolve().parents[4] / "scripts" / "run_vsp02_b5_full_adam_state_continuity.py"
    spec = importlib.util.spec_from_file_location("b5_runner_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_write_once_claim_source_binding_and_zero_runtime_readiness(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = _load_runner()
    payload = {"hello": "B5"}
    path = tmp_path / "once.json"
    runner._write_once(path, payload)
    with pytest.raises(FileExistsError):
        runner._write_once(path, payload)
    claim = tmp_path / "claim.json"
    runner._exclusive_claim(claim, payload)
    with pytest.raises(FileExistsError):
        runner._exclusive_claim(claim, payload)
    monkeypatch.setattr(runner, "CANONICAL_RUN_ROOT", tmp_path.resolve())
    monkeypatch.setattr(runner, "_require_frozen_handoff", lambda: None)
    monkeypatch.setattr(runner, "_source_revision", lambda: "a" * 40)
    entry_calls = {"evaluate": 0, "analyze": 0}
    original_evaluate = runner.evaluate_registered_full
    original_analyze = runner.analyze_registered_full
    def observed_evaluate(*args: object, **kwargs: object) -> object:
        entry_calls["evaluate"] += 1
        return original_evaluate(*args, **kwargs)
    def observed_analyze(*args: object, **kwargs: object) -> object:
        entry_calls["analyze"] += 1
        return original_analyze(*args, **kwargs)
    monkeypatch.setattr(runner, "evaluate_registered_full", observed_evaluate)
    monkeypatch.setattr(runner, "analyze_registered_full", observed_analyze)
    phases = (
        "readiness-interface-smoke", "readiness-bounded-exercise", "readiness-artifact-validation",
        "readiness-artifact-reload", "readiness-evaluate-entry", "readiness-analyze-entry",
    )
    observations: dict[str, dict[str, object]] = {}
    for command in phases:
        assert runner._readiness_command(SimpleNamespace(command=command, run_root=tmp_path)) == 0
        emitted = runner.json.loads(capsys.readouterr().out.strip())
        assert emitted["result_bearing_runs"] == 0
        observations[emitted["phase"]] = emitted["observation"]
    retained = runner._read_json(tmp_path / runner.READINESS_NAME)
    bounded = runner._read_json(tmp_path / runner.READINESS_BOUNDED_NAME)
    assert retained["activity"]["result_bearing_runs"] == 0
    assert retained["activity"]["environment_transitions"] == 0
    assert bounded["phase"] == "bounded_exercise"
    assert bounded["source_revision"] == "a" * 40
    bounded_unsigned = dict(bounded)
    bounded_digest = bounded_unsigned.pop("evidence_digest")
    assert bounded_digest == runner.digest(bounded_unsigned)
    assert observations["artifact_validation"] == {
        "validated_artifact": runner.READINESS_BOUNDED_NAME,
        "validated_phase": "bounded_exercise",
        "validated_source_revision": "a" * 40,
        "validated_evidence_digest": bounded_digest,
    }
    assert observations["artifact_reload"] == {
        "reloaded_artifact": runner.READINESS_BOUNDED_NAME,
        "reloaded_phase": "bounded_exercise",
        "reloaded_source_revision": "a" * 40,
        "reloaded_evidence_digest": bounded_digest,
        "byte_stable": True,
    }
    assert entry_calls == {"evaluate": 1, "analyze": 1}
    assert observations["evaluate_entry"]["entry_called"] == "evaluate_registered_full"
    assert observations["evaluate_entry"]["expected_full_only_rejection"] == "evaluate is full-only and requires the in-process registered train phase"
    assert observations["evaluate_entry"]["evaluation_activity"] == 0
    assert observations["analyze_entry"]["entry_called"] == "analyze_registered_full"
    assert observations["analyze_entry"]["expected_full_only_rejection"] == "analyze is full-only and requires ordered train then evaluate phases"
    assert observations["analyze_entry"]["analysis_activity"] == 0
    assert observations["analyze_entry"]["classifier_total"] is True
    assert observations["analyze_entry"]["classifier_branches_observed"] == sorted(b5.B5_BRANCH_PRECEDENCE)
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "ordered_lifecycle" in source and '["train", "evaluate", "analyze"]' in source
    assert "retry_rescue_sweep_extra_root_checkpoint_threshold_boundary" in source


def test_reserved_repo_result_remains_absent() -> None:
    root = Path(__file__).resolve().parents[4]
    assert not (root / "docs/research/candidates/vsp_02/VSP02_B5_FULL_ADAM_STATE_CONTINUITY_RESULT.json").exists()
