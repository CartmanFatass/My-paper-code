from __future__ import annotations

import argparse
from copy import deepcopy
import inspect
import math
from pathlib import Path

import pytest
import torch

from experiments.candidates.vsp_02 import (
    vsp02_b2_paired_shadow_learner_localization as b2,
)
from scripts import run_vsp02_b2_paired_shadow_learner_localization as runner


@pytest.fixture(scope="module")
def manifest() -> dict[str, object]:
    return b2.build_manifest(
        source_revision="TECHNICAL-PROOF-ONLY",
        run_id="vsp02-b2-proof",
        technical_only=True,
    )


@pytest.fixture(scope="module")
def preflight(manifest: dict[str, object]) -> dict[str, object]:
    return b2.preflight_report(manifest)


@pytest.fixture(scope="module")
def bounded_replay() -> dict[str, object]:
    return b2.bounded_deterministic_replay_fixture()


def test_p0_p8_zero_activity_preflight_is_complete(
    manifest: dict[str, object], preflight: dict[str, object]
) -> None:
    assert b2.validate_manifest(manifest) == ()
    assert preflight["all_passed"] is True
    assert tuple(sorted(preflight["gates"])) == tuple(f"P{i}" for i in range(9))
    assert b2.validate_preflight_evidence(manifest, preflight) == ()
    assert preflight["activity"] == {
        "result_bearing_runs": 0,
        "host_resets": 0,
        "episodes": 0,
        "environment_transitions": 0,
        "optimizer_updates": 0,
        "checkpoints": 0,
    }


@pytest.mark.parametrize(
    ("gate", "mutator"),
    [
        ("P0", lambda value: value.__setitem__("accepted_precursor_source", "wrong")),
        ("P1", lambda value: value["units"][0].__setitem__("decimal_root", 1)),
        ("P2", lambda value: value.__setitem__("arms", ["RL_ORIGINAL"])),
        (
            "P4",
            lambda value: value["loss_contract"].__setitem__(
                "rl_actor", "UNDETACHED_ADVANTAGE"
            ),
        ),
        (
            "P6",
            lambda value: value["training"].__setitem__("episodes_per_update", 32),
        ),
        (
            "P7",
            lambda value: value["evaluation"].__setitem__(
                "stochastic_action_draws", 1
            ),
        ),
        (
            "P8",
            lambda value: value.__setitem__(
                "rng_streams", value["rng_streams"][:-1]
            ),
        ),
    ],
)
def test_manifest_mutations_fail_the_registered_gate(
    manifest: dict[str, object], gate: str, mutator: object
) -> None:
    changed = deepcopy(manifest)
    mutator(changed)  # type: ignore[operator]
    assert b2._manifest_literal_issues(changed)[gate]


def test_preflight_rejects_p2_and_p3_fabrication(
    manifest: dict[str, object], preflight: dict[str, object]
) -> None:
    changed = deepcopy(preflight)
    changed["initial_parameter_hashes"]["RL_ORIGINAL"] = "fabricated"
    assert "P2 parameter equality evidence mismatch" in b2.validate_preflight_evidence(
        manifest, changed
    )
    changed = deepcopy(preflight)
    changed["p3_noninterference"]["after"]["rl_parameters"] = "mutated"
    assert "P3 pre/post hash identity mismatch" in b2.validate_preflight_evidence(
        manifest, changed
    )


def test_loss_detach_and_label_firewall_are_structural(
    manifest: dict[str, object], preflight: dict[str, object]
) -> None:
    changed = deepcopy(preflight)
    changed["p3_noninterference"][
        "rl_actor_advantage_detached_from_critic_head"
    ] = False
    assert "P4 stop-gradient evidence mismatch" in b2.validate_preflight_evidence(
        manifest, changed
    )
    history = b2._synthetic_history(1, owner_epoch="FIREWALL")
    history[1]["optimal_action"] = "RELEASE"
    assert not b2._observation_firewall(history)


def test_schedule_and_seed_derivation_are_exact() -> None:
    unit_id, root = b2.B2_UNITS[0]
    rows, terminal = b2._schedule_with_receipt(unit_id, root)
    assert b2._schedule_contract(rows)
    assert len(rows) == 1_024
    assert terminal == b2._schedule_with_receipt(unit_id, root)[1]
    report = b2.seed_report()
    assert report["all_b2_seeds_unique"] is True
    assert report["collision_with_b1v2_seed_values"] == []
    assert report["derived"][unit_id]["parameter_initialization"] == 206_494_240


def _unit_metric(
    *, q0: float, q1: float, exact_correct: bool, exact_inverse: bool
) -> dict[str, object]:
    projected = b2._mixture_metrics_from_raw_q(q0=q0, q1=q1)
    return {
        "q_0": q0,
        "q_1": q1,
        **projected,
        "cue_counts": {"0": 64, "1": 64},
        "episodes": 128,
        "evaluation_updates": 0,
        "stochastic_action_draws": 0,
        "q_is_raw_softmax": True,
        "argmax_mixture_equivalent": True,
        "exact_correct_unit": exact_correct,
        "exact_inverse_unit": exact_inverse,
    }


def test_raw_q_once_mixed_gates_are_reachable_and_double_mix_fails() -> None:
    direct = b2._arm_aggregate(
        [_unit_metric(q0=0.01, q1=0.99, exact_correct=True, exact_inverse=False)] * 5
    )
    flipped = b2._arm_aggregate(
        [_unit_metric(q0=0.99, q1=0.01, exact_correct=False, exact_inverse=True)] * 5
    )
    original = b2._arm_aggregate(
        [_unit_metric(q0=0.5, q1=0.5, exact_correct=False, exact_inverse=False)] * 5
    )
    assert direct["mean_kappa"] >= 0.70
    assert flipped["mean_kappa"] <= -0.70
    assert (
        b2.classify_b2(
            preflight_valid=True,
            runtime_valid=True,
            activity_valid=True,
            aggregates={
                "RL_ORIGINAL": original,
                "SUP_TRUE": direct,
                "SUP_FLIP": flipped,
            },
        )
        == "B2_DIRECT_SUCCEEDED_ORIGINAL_FAILED"
    )
    metric = _unit_metric(
        q0=0.01, q1=0.99, exact_correct=True, exact_inverse=False
    )
    metric["p_0"] = 0.1 + 0.8 * float(metric["p_0"])
    metric["p_1"] = 0.1 + 0.8 * float(metric["p_1"])
    assert "evaluation metric p_0 mismatch" in b2._metric_issues(metric)


def test_forward_separates_training_mixture_from_raw_evaluation_q() -> None:
    unit_id, root = b2.B2_UNITS[0]
    models, _ = b2._new_learners(unit_id, root)
    observations = b2._synthetic_history(1, owner_epoch="RAW-Q-PROOF")
    _, raw_q, behavior, _, _ = b2._forward(models["RL_ORIGINAL"], observations)
    assert raw_q.tolist() == pytest.approx([0.5, 0.5], abs=1e-15)
    assert behavior.tolist() == pytest.approx(
        [0.1 + 0.8 * value for value in raw_q.tolist()], abs=1e-15
    )


@pytest.mark.parametrize(
    ("preflight_valid", "runtime_valid", "activity_valid", "flip", "direct", "original", "expected"),
    [
        (False, True, True, True, True, False, "B2_NO_CONSTRUCTION"),
        (True, False, True, True, True, False, "B2_INVALID_RUNTIME_CONTRACT"),
        (True, True, False, True, True, False, "B2_ACTIVITY_SUPPORT_OR_CAP_INVALID"),
        (True, True, True, False, True, False, "B2_SUPERVISION_CONTROL_UNCALIBRATED"),
        (True, True, True, True, True, False, "B2_DIRECT_SUCCEEDED_ORIGINAL_FAILED"),
        (True, True, True, True, True, True, "B2_BOTH_SUCCEEDED"),
        (True, True, True, True, False, True, "B2_DIRECT_FAILED_ORIGINAL_SUCCEEDED"),
        (True, True, True, True, False, False, "B2_BOTH_FAILED"),
    ],
)
def test_branch_precedence_is_total_and_ordered(
    preflight_valid: bool,
    runtime_valid: bool,
    activity_valid: bool,
    flip: bool,
    direct: bool,
    original: bool,
    expected: str,
) -> None:
    aggregates = {
        "SUP_FLIP": {
            "mean_kappa": -0.8 if flip else 0.0,
            "exact_inverse_units": 5 if flip else 0,
            "correct_arm_pass": False,
        },
        "SUP_TRUE": {"correct_arm_pass": direct},
        "RL_ORIGINAL": {"correct_arm_pass": original},
    }
    assert b2.classify_b2(
        preflight_valid=preflight_valid,
        runtime_valid=runtime_valid,
        activity_valid=activity_valid,
        aggregates=aggregates,
    ) == expected


def test_no_construction_result_requires_zero_activity(
    manifest: dict[str, object], preflight: dict[str, object]
) -> None:
    failed = deepcopy(preflight)
    failed["gates"]["P0"] = {"passed": False, "issues": ["source mismatch"]}
    failed["all_passed"] = False
    result = {
        "artifact_kind": "vsp02_b2_result",
        "assignment_id": b2.B2_ASSIGNMENT_ID,
        "candidate": b2.B2_CANDIDATE,
        "manifest": manifest,
        "manifest_identity": b2.manifest_identity(manifest),
        "preflight": failed,
        "branch": "B2_NO_CONSTRUCTION",
        "activity": b2._zero_activity(),
        "units": [],
        "aggregates": None,
    }
    assert b2.validate_result(manifest, result) == ()
    result["activity"]["optimizer_updates"] = 1
    assert "no-construction branch has result-bearing activity" in b2.validate_result(
        manifest, result
    )


def test_runtime_branch_rejects_technical_only_and_missing_units(
    manifest: dict[str, object], preflight: dict[str, object]
) -> None:
    result = {
        "artifact_kind": "vsp02_b2_result",
        "assignment_id": b2.B2_ASSIGNMENT_ID,
        "candidate": b2.B2_CANDIDATE,
        "manifest": manifest,
        "manifest_identity": b2.manifest_identity(manifest),
        "preflight": preflight,
        "branch": "B2_BOTH_FAILED",
        "activity": {},
        "units": [],
        "evaluation": {arm: [] for arm in b2.B2_ARMS},
    }
    assert any(
        "post-preflight branch requires technical_only=false" in issue
        for issue in b2.validate_result(manifest, result)
    )
    full_manifest = b2.build_manifest(
        source_revision="FRESH", run_id="vsp02-b2-missing", technical_only=False
    )
    result["manifest"] = full_manifest
    result["manifest_identity"] = b2.manifest_identity(full_manifest)
    result["preflight"] = deepcopy(preflight)
    result["preflight"]["manifest_identity"] = b2.manifest_identity(full_manifest)
    assert any(
        "exactly five unit/root records" in issue
        for issue in b2.validate_result(full_manifest, result)
    )


def test_bounded_fixture_is_produced_and_validated_by_deterministic_replay(
    bounded_replay: dict[str, object]
) -> None:
    assert bounded_replay["registered_fulls"] == 0
    assert bounded_replay["result_bearing_runs"] == 0
    assert bounded_replay["training_episodes"] == 16
    assert bounded_replay["optimizer_updates"] == 6
    assert bounded_replay["evaluation_episodes"] == 384
    assert b2.validate_bounded_deterministic_replay_fixture(bounded_replay) == ()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda value: value["batches"][0]["rows"][0]["metadata"].__setitem__(
            "event_tape_token", "fabricated"
        ),
        lambda value: value["batches"][0]["rows"][0].__setitem__(
            "A_behavior", "HOLD"
            if value["batches"][0]["rows"][0]["A_behavior"] == "RELEASE"
            else "RELEASE"
        ),
        lambda value: value["batches"][0]["rows"][0].__setitem__("O", []),
        lambda value: value["batches"][0]["rows"][0]["R"].__setitem__(0, 999.0),
        lambda value: value["batches"][0]["rows"][0][
            "behavior_probabilities"
        ].__setitem__(0, 0.123),
        lambda value: value["batches"][0]["rows"][0].__setitem__(
            "environment_transitions", 99
        ),
        lambda value: value["updates"]["RL_ORIGINAL"][0].__setitem__(
            "loss", 999.0
        ),
        lambda value: value["updates"]["RL_ORIGINAL"][0].__setitem__(
            "gradient_norm_before_clip", 999.0
        ),
        lambda value: value["updates"]["RL_ORIGINAL"][0].__setitem__(
            "parameters_after", "fabricated"
        ),
        lambda value: value["updates"]["RL_ORIGINAL"][0].__setitem__(
            "optimizer_after", "fabricated"
        ),
        lambda value: value["final_model_states"]["SUP_TRUE"].__setitem__(
            "actor.bias", {"dtype": "torch.float64", "shape": [2], "values": [9.0, 9.0]}
        ),
        lambda value: value["final_optimizer_states"].__setitem__(
            "SUP_TRUE", {"fabricated": True}
        ),
        lambda value: value["evaluations"]["SUP_TRUE"]["clone_records"][0].__setitem__(
            "logits", [9.0, -9.0]
        ),
        lambda value: value["terminal_rng_hashes"].__setitem__(
            "train_action_uniform", "fabricated"
        ),
    ],
)
def test_bounded_replay_rejects_host_batch_gradient_adam_checkpoint_and_rng_fabrication(
    bounded_replay: dict[str, object], mutator: object
) -> None:
    changed = deepcopy(bounded_replay)
    mutator(changed)  # type: ignore[operator]
    assert b2.validate_bounded_deterministic_replay_fixture(changed) == (
        "bounded fixture differs from deterministic seed/host/Adam replay",
    )


def test_retained_validation_and_validate_cli_have_zero_runtime_call_surface(
    monkeypatch: pytest.MonkeyPatch,
    manifest: dict[str, object],
    preflight: dict[str, object],
    bounded_replay: dict[str, object],
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("retained validation invoked a forbidden runtime surface")

    monkeypatch.setattr(b2, "run_treatment", forbidden)
    monkeypatch.setattr(b2, "B2LifecycleHost", forbidden)
    monkeypatch.setattr(b2, "_optimizer_step", forbidden)
    monkeypatch.setattr(b2, "_evaluate_arm_unit", forbidden)
    monkeypatch.setattr(b2.b1, "GRUActorCritic", forbidden)
    monkeypatch.setattr(torch.optim, "Adam", forbidden)
    monkeypatch.setattr(runner, "run_treatment", forbidden)

    rng_before_bounded = torch.get_rng_state().clone()
    assert b2.validate_bounded_deterministic_replay_fixture(bounded_replay) == ()
    assert torch.equal(torch.get_rng_state(), rng_before_bounded)
    failed = deepcopy(preflight)
    failed["gates"]["P0"] = {"passed": False, "issues": ["source mismatch"]}
    failed["all_passed"] = False
    no_construction = {
        "artifact_kind": "vsp02_b2_result",
        "assignment_id": b2.B2_ASSIGNMENT_ID,
        "candidate": b2.B2_CANDIDATE,
        "manifest": manifest,
        "manifest_identity": b2.manifest_identity(manifest),
        "preflight": failed,
        "branch": "B2_NO_CONSTRUCTION",
        "activity": b2._zero_activity(),
        "units": [],
        "aggregates": None,
    }
    rng_before_result = torch.get_rng_state().clone()
    assert b2.validate_result(manifest, no_construction) == ()
    assert torch.equal(torch.get_rng_state(), rng_before_result)

    run_root = Path(f"C:/{runner.ROOT_MARKER}/validation-call-trap")
    monkeypatch.setattr(runner, "_require_root", lambda path: run_root)
    monkeypatch.setattr(
        runner,
        "_read_json",
        lambda path: manifest if path.name == runner.MANIFEST_NAME else no_construction,
    )
    rng_before_cli = torch.get_rng_state().clone()
    assert runner._validate_command(argparse.Namespace(run_root=run_root)) == 0
    assert torch.equal(torch.get_rng_state(), rng_before_cli)
    assert "run_treatment(" not in inspect.getsource(b2.validate_result)
    assert "run_treatment(" not in inspect.getsource(runner._validate_command)
