from __future__ import annotations

import argparse
from copy import deepcopy
import inspect
import json
import math
from pathlib import Path
import random
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.vsp_02 import vsp02_b3_lifecycle_credit_sign_bridge as b3
from scripts import run_vsp02_b3_lifecycle_credit_sign_bridge as runner


@pytest.fixture(scope="module")
def manifest() -> dict[str, object]:
    return b3.build_manifest(source_revision="TECHNICAL-PROOF-ONLY", run_id="vsp02-b3-proof", technical_only=True)


@pytest.fixture(scope="module")
def preflight(manifest: dict[str, object]) -> dict[str, object]:
    return b3.preflight_report(manifest)


def test_manifest_freezes_two_arms_five_fresh_roots_and_activity(manifest: dict[str, object]) -> None:
    assert b3.validate_manifest(manifest) == ()
    assert manifest["arms"] == ["RL_ORIGINAL", "CREDIT_SIGN_BRIDGE"]
    assert [(item["unit_id"], item["decimal_root"]) for item in manifest["units"]] == list(b3.B3_UNITS)
    assert manifest["expected_activity"] == {
        "real_training_episodes": 5_120,
        "optimizer_updates": 1_280,
        "evaluation_episodes": 1_280,
        "checkpoints_total": 10,
    }
    assert manifest["result_bearing_runs"] == 0
    assert manifest["retry_rescue_sweep_extra_arm_seed_checkpoint"] == 0


def test_initial_parameters_and_adam_are_byte_identical() -> None:
    models, optimizers = b3._new_learners(*b3.B3_UNITS[0])
    assert len({b3.digest(b3.model_payload(model)) for model in models.values()}) == 1
    assert len({b3.digest(b3.optimizer_payload(optimizer)) for optimizer in optimizers.values()}) == 1
    assert all(model.gru.input_size == 10 and model.gru.hidden_size == 16 for model in models.values())
    assert all(next(model.parameters()).dtype == torch.float64 for model in models.values())


def test_schedule_and_seed_namespace_are_fresh_and_exact() -> None:
    report = b3.seed_report()
    assert report["all_b3_seeds_unique"] is True
    assert report["collision_with_b1v2_seed_values"] == []
    assert report["collision_with_b2_seed_values"] == []
    assert report["identity_collision_with_predecessors"] is False
    for unit, root in b3.B3_UNITS:
        rows, terminal = b3._schedule_with_receipt(unit, root)
        assert b3._schedule_contract(rows)
        assert terminal == b3._schedule_with_receipt(unit, root)[1]


def test_credit_sign_truth_table_and_abs_advantage_route() -> None:
    assert b3.correctness_sign("HOLD", 0) == 1.0
    assert b3.correctness_sign("RELEASE", 1) == 1.0
    assert b3.correctness_sign("RELEASE", 0) == -1.0
    assert b3.correctness_sign("HOLD", 1) == -1.0
    models, _ = b3._new_learners(*b3.B3_UNITS[0])
    batch = b3._proof_batch(models["RL_ORIGINAL"])
    _, route = b3._loss_terms("CREDIT_SIGN_BRIDGE", models["CREDIT_SIGN_BRIDGE"], batch)
    assert route["actor_route"] == b3.BRIDGE_ACTOR_ROUTE
    assert route["advantage_count"] == 8
    assert route["max_abs_magnitude_error"] == 0.0
    assert route["correctness_class_counts"] == {"-1": 4, "+1": 4}
    assert route["actual_sign_change_count"] > 0
    assert all(abs(abs(coefficient) - abs(advantage)) == 0.0 for coefficient, advantage in zip(route["actor_coefficients"], route["advantages"]))


def test_zero_advantage_has_zero_actor_credit() -> None:
    models, _ = b3._new_learners(*b3.B3_UNITS[0])
    batch = b3._proof_batch(models["RL_ORIGINAL"], zero_advantage=True)
    _, route = b3._loss_terms("CREDIT_SIGN_BRIDGE", models["CREDIT_SIGN_BRIDGE"], batch)
    assert route["zero_advantage_count"] == 8
    assert route["nonzero_advantage_count"] == 0
    assert route["actor_coefficients"] == [0.0] * 8


@pytest.mark.parametrize(
    "mutator",
    [
        lambda row: row.pop("G"),
        lambda row: row.__setitem__("M_valid", [0, 0]),
        lambda row: row.__setitem__("M_lifecycle", [0, 0]),
        lambda row: row.__setitem__("G", float("nan")),
        lambda row: row.__setitem__("G", float("inf")),
    ],
)
def test_missing_masked_or_nonfinite_advantage_fails_closed(mutator: object) -> None:
    models, _ = b3._new_learners(*b3.B3_UNITS[0])
    batch = b3._proof_batch(models["RL_ORIGINAL"])
    mutator(batch[0])  # type: ignore[operator]
    with pytest.raises(ValueError, match="advantage|return"):
        b3._loss_terms("CREDIT_SIGN_BRIDGE", models["CREDIT_SIGN_BRIDGE"], batch)


def test_oracle_is_bridge_only_and_accessed_after_forward(monkeypatch: pytest.MonkeyPatch) -> None:
    models, _ = b3._new_learners(*b3.B3_UNITS[0])
    batch = b3._proof_batch(models["RL_ORIGINAL"])
    calls = 0
    original = b3.correctness_sign
    def counted(action: str, cue: int) -> float:
        nonlocal calls
        calls += 1
        return original(action, cue)
    monkeypatch.setattr(b3, "correctness_sign", counted)
    b3._loss_terms("RL_ORIGINAL", models["RL_ORIGINAL"], batch)
    assert calls == 0
    b3._loss_terms("CREDIT_SIGN_BRIDGE", models["CREDIT_SIGN_BRIDGE"], batch)
    assert calls == 8
    source = inspect.getsource(b3._loss_terms)
    assert source.index("_forward(model, observations)") < source.index("metadata = row.get")
    assert "correctness_sign" not in inspect.getsource(b3._collect_batch)
    assert "correctness_sign" not in inspect.getsource(b3._evaluate_arm_unit)


def test_bridge_gradient_computation_cannot_mutate_original_generator() -> None:
    models, optimizers = b3._new_learners(*b3.B3_UNITS[0])
    proof = b3._gradient_and_noninterference_proof(models, optimizers)
    assert proof["before"] == proof["after"]
    assert proof["hash_identity"] is True
    assert proof["finite_nonzero_actor_composite_gradient"] is True
    assert proof["activity"] == b3._zero_activity()


def test_bounded_diagnostic_uses_original_as_sole_generator_and_same_rows_order() -> None:
    unit_id, root = b3.B3_UNITS[0]
    models, optimizers = b3._new_learners(unit_id, root)
    schedule, _ = b3._schedule_with_receipt(unit_id, root)
    event_rng = random.Random(b3.b3_seed(unit_id, root, "train_environment_event"))
    action_rng = random.Random(b3.b3_seed(unit_id, root, "train_action_uniform"))
    batch, transitions = b3._collect_batch(
        unit_id=unit_id,
        update_index=0,
        rows=schedule[:8],
        original_model=models["RL_ORIGINAL"],
        event_rng=event_rng,
        action_rng=action_rng,
    )
    assert len(batch) == 8 and transitions > 0
    assert all(b3._immutable_row_contract(row) for row in batch)
    order_rngs = {
        arm: random.Random(b3.b3_seed(unit_id, root, "train_minibatch_order"))
        for arm in b3.B3_ARMS
    }
    orders: dict[str, list[int]] = {}
    for arm in b3.B3_ARMS:
        order = list(range(8)); order_rngs[arm].shuffle(order); orders[arm] = order
    assert orders["RL_ORIGINAL"] == orders["CREDIT_SIGN_BRIDGE"]
    ordered = [batch[index] for index in orders["RL_ORIGINAL"]]
    original_update = b3._optimizer_step(
        "RL_ORIGINAL", models["RL_ORIGINAL"], optimizers["RL_ORIGINAL"], ordered
    )
    successor = {"unit_id": unit_id, "next_update": 1, "event_rng": b3.rng_digest(event_rng), "action_rng": b3.rng_digest(action_rng)}
    before = b3._rl_state_hashes(models["RL_ORIGINAL"], optimizers["RL_ORIGINAL"], action_rng, successor, batch)
    bridge_update = b3._optimizer_step(
        "CREDIT_SIGN_BRIDGE", models["CREDIT_SIGN_BRIDGE"], optimizers["CREDIT_SIGN_BRIDGE"], ordered
    )
    after = b3._rl_state_hashes(models["RL_ORIGINAL"], optimizers["RL_ORIGINAL"], action_rng, successor, batch)
    assert before == after
    assert original_update["actor_route"] == b3.ORIGINAL_ACTOR_ROUTE
    assert bridge_update["actor_route"] == b3.BRIDGE_ACTOR_ROUTE
    assert bridge_update["max_abs_magnitude_error"] == 0.0


def test_preflight_is_zero_activity_and_artifact_mutation_fails(manifest: dict[str, object], preflight: dict[str, object]) -> None:
    assert preflight["all_passed"] is True
    assert b3.validate_preflight_evidence(manifest, preflight) == ()
    assert preflight["activity"] == b3._zero_activity()
    changed = deepcopy(preflight)
    changed["initial_parameter_hashes"]["RL_ORIGINAL"] = "fabricated"
    assert "preflight artifact mutation or evidence digest mismatch" in b3.validate_preflight_evidence(manifest, changed)


def test_branch_literals_are_ordered_and_total() -> None:
    assert b3.B3_BRANCH_PRECEDENCE == (
        "B3_INCONCLUSIVE_OR_INVALID",
        "B3_SIGN_BRIDGE_LOCAL_SUFFICIENCY",
        "B3_SIGN_ONLY_INSUFFICIENT",
    )
    original = {"exact_correct_units": 0, "mean_j_eval": 1.0, "mean_kappa": 0.0}
    bridge_good = {"exact_correct_units": 5, "mean_j_eval": 1.1, "mean_kappa": 0.7}
    bridge_bad = {"exact_correct_units": 0, "mean_j_eval": 1.0, "mean_kappa": 0.0}
    assert b3.classify_b3(valid=True, aggregates={"RL_ORIGINAL": original, "CREDIT_SIGN_BRIDGE": bridge_good}, bridge_exposure_valid=True) == "B3_SIGN_BRIDGE_LOCAL_SUFFICIENCY"
    assert b3.classify_b3(valid=True, aggregates={"RL_ORIGINAL": original, "CREDIT_SIGN_BRIDGE": bridge_bad}, bridge_exposure_valid=True) == "B3_SIGN_ONLY_INSUFFICIENT"
    assert b3.classify_b3(valid=False, aggregates={"RL_ORIGINAL": original, "CREDIT_SIGN_BRIDGE": bridge_good}, bridge_exposure_valid=True) == "B3_INCONCLUSIVE_OR_INVALID"


def _failed_construction_result(manifest: dict[str, object], preflight: dict[str, object]) -> dict[str, object]:
    failed = deepcopy(preflight)
    failed["gates"]["P0"] = {"passed": False, "issues": ["source mismatch"]}
    failed["all_passed"] = False
    failed.pop("evidence_digest")
    failed["evidence_digest"] = b3.digest(failed)
    result = {
        "artifact_kind": "vsp02_b3_result", "assignment_id": b3.B3_ASSIGNMENT_ID,
        "candidate": b3.B3_CANDIDATE, "manifest": manifest,
        "manifest_identity": b3.manifest_identity(manifest), "preflight": failed,
        "branch": "B3_INCONCLUSIVE_OR_INVALID", "activity": b3._zero_activity(),
        "activity_valid": False, "bridge_exposure_valid": False,
        "runtime_contract": None, "units": [], "aggregates": None,
        "evaluation": None,
    }
    result["evidence_digest"] = b3.digest(result)
    return result


def test_retained_validator_has_no_runtime_call_surface(monkeypatch: pytest.MonkeyPatch, manifest: dict[str, object], preflight: dict[str, object]) -> None:
    result = _failed_construction_result(manifest, preflight)
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("retained validation invoked runtime")
    monkeypatch.setattr(b3, "run_treatment", forbidden)
    monkeypatch.setattr(b3, "B3LifecycleHost", forbidden)
    monkeypatch.setattr(b3, "_new_learners", forbidden)
    monkeypatch.setattr(b3, "_optimizer_step", forbidden)
    monkeypatch.setattr(b3, "_evaluate_arm_unit", forbidden)
    monkeypatch.setattr(torch.optim, "Adam", forbidden)
    rng_before = torch.get_rng_state().clone()
    assert b3.validate_result(manifest, result) == ()
    assert torch.equal(torch.get_rng_state(), rng_before)
    changed = deepcopy(result); changed["activity"]["optimizer_updates"] = 1
    assert "retained artifact mutation or evidence digest mismatch" in b3.validate_result(manifest, changed)
    assert "run_treatment(" not in inspect.getsource(b3.validate_result)


def test_runner_write_once_exclusive_claim_source_binding_and_no_retry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.json"
    runner._write_once(artifact, {"value": 1})
    with pytest.raises(FileExistsError): runner._write_once(artifact, {"value": 2})
    claim = tmp_path / "claim.json"
    runner._exclusive_claim(claim, {"result_bearing_runs": 1})
    with pytest.raises(FileExistsError): runner._exclusive_claim(claim, {})
    monkeypatch.setattr(runner, "_source_revision", lambda: "BOUND")
    with pytest.raises(ValueError, match="source_revision"):
        runner._manifest_command(argparse.Namespace(source_revision="WRONG", run_id="x", technical_only=True, output=tmp_path / "manifest.json"))
    source = inspect.getsource(runner._registered_full_command)
    assert source.count("run_treatment(") == 1
    assert "_exclusive_claim" in source and source.index("_exclusive_claim") < source.index("run_treatment(")
    assert '"retry_rescue_sweep_extra_arm_seed_checkpoint": 0' in source
    assert "while " not in source and "except " not in source


def test_runner_rejects_every_noncanonical_matching_run_root(tmp_path: Path) -> None:
    assert runner._require_root(runner.CANONICAL_RUN_ROOT) == runner.CANONICAL_RUN_ROOT
    sibling = tmp_path / "another_vsp02_b3_lifecycle_credit_sign_bridge_root"
    with pytest.raises(ValueError, match="canonical assignment root"):
        runner._require_root(sibling)
    with pytest.raises(ValueError, match="canonical assignment root"):
        runner._require_root(runner.CANONICAL_RUN_ROOT / "nested")


def test_dirty_runtime_dependency_rejected_without_touching_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_paths = b3.B3_CLAIM_PATHS + b3.B3_DEPENDENCY_PATHS
    assert b3.B3_RUNTIME_PATHS == runtime_paths
    assert set(b3.B3_DEPENDENCY_PATHS) <= set(runtime_paths)
    dirty_dependency = b3.B3_DEPENDENCY_PATHS[0]

    def fake_git(*arguments: str) -> str:
        if arguments[0] == "ls-files":
            assert tuple(arguments[2:]) == runtime_paths
            return "\n".join(runtime_paths)
        if arguments[0] == "status":
            assert tuple(arguments[4:]) == runtime_paths
            return f" M {dirty_dependency}"
        raise AssertionError(f"unexpected Git query: {arguments}")

    monkeypatch.setattr(runner, "_git", fake_git)
    with pytest.raises(ValueError, match="runtime dependency sources differ from HEAD"):
        runner._require_clean_claim_sources()

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        arguments = command[1:]
        if arguments == ["rev-parse", "HEAD"]:
            return SimpleNamespace(stdout="BOUND\n", returncode=0)
        if arguments[:2] == ["ls-files", "--"]:
            assert tuple(arguments[2:]) == runtime_paths
            return SimpleNamespace(stdout="\n".join(runtime_paths) + "\n", returncode=0)
        if arguments[:4] == ["status", "--porcelain=v1", "--untracked-files=all", "--"]:
            assert tuple(arguments[4:]) == runtime_paths
            return SimpleNamespace(stdout=f" M {dirty_dependency}\n", returncode=0)
        if arguments[:3] == ["merge-base", "--is-ancestor", b3.B3_ACCEPTED_B2_SOURCE]:
            return SimpleNamespace(stdout="", returncode=0)
        raise AssertionError(f"unexpected Git subprocess: {arguments}")

    monkeypatch.setattr(b3.subprocess, "run", fake_run)
    assert "B3 claim or runtime dependency paths differ from HEAD" in b3._git_binding(Path.cwd(), "BOUND")
