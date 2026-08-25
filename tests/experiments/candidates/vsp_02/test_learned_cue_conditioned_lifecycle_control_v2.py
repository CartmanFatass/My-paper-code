from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import tempfile

import pytest
import torch

from experiments.candidates.vsp_02 import learned_cue_conditioned_lifecycle_control_v2 as b1


ROOT = Path(__file__).resolve().parents[4]
CLI = ROOT / "scripts" / "run_vsp02_b1v2_learned_cue_conditioned_lifecycle_control.py"


def _runner_module():
    spec = importlib.util.spec_from_file_location("vsp02_b1v2_runner", CLI)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _host_episode(true_cue: int, action: b1.Action, probabilities=(0.5, 0.5)):
    host = b1.LifecycleHost()
    cue = host.reset(
        lifecycle_id=f"test/{true_cue}/{action.value}",
        owner_epoch="EV-00",
        true_cue=true_cue,
        presented_cue=true_cue,
    )
    decide = host.decision_observation()
    return cue, decide, host.step(action, action_probabilities=probabilities)


def test_rng_derivation_is_exact_first_eight_big_endian_sha256_bytes():
    seed_id = b1.B1_SEED_IDS[0]
    for stream in b1.B1_RNG_STREAMS:
        expected = int.from_bytes(
            hashlib.sha256(f"{seed_id}/{stream}".encode()).digest()[:8], "big"
        )
        assert b1.stream_seed(seed_id, stream) == expected
    with pytest.raises(ValueError):
        b1.stream_seed(seed_id, "invented")


def test_schedule_has_exact_true_balance_and_independent_shuffle_crossing():
    schedule = b1.training_schedule(b1.B1_SEED_IDS[0])
    assert len(schedule) == 1024
    assert {row["owner_epoch"] for row in schedule} == set(b1.B1_TRAIN_EPOCHS)
    for block in range(16):
        rows = [row for row in schedule if row["block"] == block]
        assert len(rows) == 64
        assert [sum(row["true_cue"] == cue for row in rows) for cue in (0, 1)] == [32, 32]
        for true_cue in (0, 1):
            for presented_cue in (0, 1):
                assert sum(
                    row["true_cue"] == true_cue
                    and row["shuffled_presented_cue"] == presented_cue
                    for row in rows
                ) == 16


def test_real_host_forced_returns_and_lifecycle_paths_are_exact():
    assert b1._terminal_precedence_behavior_valid()
    expected = {
        (1, b1.Action.RELEASE): ([1], 1.0, "RELEASE"),
        (1, b1.Action.HOLD): ([-1, 0], -1.0, "NATURAL"),
        (0, b1.Action.RELEASE): ([1], 1.0, "RELEASE"),
        (0, b1.Action.HOLD): ([2, 0], 2.0, "NATURAL"),
    }
    for (cue, action), (rewards, physical_return, end_cause) in expected.items():
        _, _, episode = _host_episode(cue, action)
        assert episode["reward_sequence"] == rewards
        assert episode["physical_return"] == physical_return
        assert episode["escrow"]["end_cause"] == end_cause
        assert episode["escrow"]["consumption_count"] == 1
        assert episode["escrow"]["tombstone_phase"] == "TARGET_CLOSED_TOMBSTONE"
        assert episode["escrow"]["version_advance_permitted"] is True
        assert b1._episode_issues(episode) == []


def test_cue_observe_to_decide_has_no_clock_reward_or_unmasked_cue_change():
    cue_zero, decide_zero, _ = _host_episode(0, b1.Action.RELEASE)
    cue_one, decide_one, _ = _host_episode(1, b1.Action.RELEASE)
    assert cue_zero.cue_mask == cue_one.cue_mask == 1
    assert (cue_zero.cue_value, cue_one.cue_value) == (0, 1)
    assert decide_zero == decide_one
    assert decide_zero.cue_mask == decide_zero.cue_value == 0
    for field in ("physical_clock", "primitive_clock", "own_boundary_clock"):
        assert getattr(cue_zero, field) == getattr(decide_zero, field) == 0


def test_action_score_escrow_is_write_once_and_target_close_is_required():
    host = b1.LifecycleHost()
    host.reset(
        lifecycle_id="escrow-test",
        owner_epoch="EV-00",
        true_cue=1,
        presented_cue=1,
    )
    episode = host.step(b1.Action.RELEASE, action_probabilities=(0.8, 0.2))
    assert episode["selected_likelihood"] == 0.8
    assert episode["escrow"]["owner_epoch"] == "EV-00"
    assert episode["escrow"]["behavior_version"] == 8
    with pytest.raises(RuntimeError):
        host.step(b1.Action.HOLD, action_probabilities=(0.2, 0.8))


def test_neural_initialization_and_memory_controls_match_frozen_contract():
    seed = b1.stream_seed(b1.B1_SEED_IDS[0], "init")
    first = b1.GRUActorCritic(init_seed=seed)
    second = b1.GRUActorCritic(init_seed=seed)
    assert b1.serialize_model(first) == b1.serialize_model(second)
    assert first.gru.hidden_size == 16
    assert all(parameter.dtype == torch.float64 for parameter in first.parameters())
    assert torch.count_nonzero(first.actor.weight) == 0
    assert torch.count_nonzero(first.actor.bias) == 0

    cue_zero, decide, _ = _host_episode(0, b1.Action.RELEASE)
    cue_one, _, _ = _host_episode(1, b1.Action.RELEASE)
    histories = [
        [b1.asdict(cue_zero), b1.asdict(decide)],
        [b1.asdict(cue_one), b1.asdict(decide)],
    ]
    with torch.no_grad():
        first.actor.weight[0].fill_(1.0)
        first.actor.weight[1].fill_(-1.0)
        full = [first.distribution(history, reset_before_decide=False)[0] for history in histories]
        current = [first.distribution(history, reset_before_decide=True)[0] for history in histories]
    assert not torch.equal(full[0], full[1])
    assert torch.equal(current[0], current[1])


def test_one_component_neural_batch_executes_one_clipped_adam_step():
    schedule = b1.training_schedule(b1.B1_SEED_IDS[0], blocks=1)[:32]
    fit = b1.train_neural_arm(
        "FULL_LIFECYCLE_GRU_ACTOR_CRITIC", b1.B1_SEED_IDS[0], schedule
    )
    assert len(fit["episodes"]) == 32
    assert len(fit["optimizer"]["updates"]) == 1
    assert fit["optimizer"]["updates"][0]["clip_threshold"] == 1.0
    assert sum(row["activity"]["optimizer_updates"] for row in fit["episodes"]) == 1
    assert all(row["gradient_clip"] is not None for row in fit["episodes"])
    assert len(fit["parameter_snapshots"]) == 2
    assert all(
        row["learner_state"]["before_update"] in fit["parameter_snapshots"]
        and row["learner_state"]["after_update"] in fit["parameter_snapshots"]
        for row in fit["episodes"]
    )
    assert b1._validate_neural_fit_replay(fit) == []


def test_tabular_policy_is_sample_mean_with_release_tie_and_unseen_uniform():
    assert b1._tabular_distribution({"0": [0.0, 0.0]}, key="0") == (0.9, 0.1)
    assert b1._tabular_distribution({"0": [1.0, 2.0]}, key="0") == (0.1, 0.9)
    assert b1._tabular_distribution({}, key="unseen") == (0.9, 0.1)
    assert b1._tabular_distribution({}, key="unseen", unseen_uniform=True) == (0.5, 0.5)
    # The frozen exploratory mixture implies 1.35 for a correct table; the
    # implementation must not silently convert evaluation to a greedy oracle.
    j_eval = ((0.9 * 1 + 0.1 * -1) + (0.1 * 1 + 0.9 * 2)) / 2
    assert j_eval == pytest.approx(1.35)
    fit = b1.train_tabular_arm(
        "X_MEMORY_TABULAR_MONTE_CARLO",
        b1.B1_SEED_IDS[0],
        b1.training_schedule(b1.B1_SEED_IDS[0], blocks=1)[:8],
    )
    assert fit["initial_state"] == {
        "table": {"0": [0.0, 0.0], "1": [0.0, 0.0]},
        "counts": {"0": [0, 0], "1": [0, 0]},
    }
    assert b1._validate_tabular_fit_replay(fit) == []


def test_amended_thresholds_and_table_exactness_are_closed_at_registered_bounds():
    correct = {"mapping_all_clones": True, "j_eval": 1.30}
    assert b1._positive_control_seed_passes(correct)
    assert not b1._positive_control_seed_passes(
        {"mapping_all_clones": True, "j_eval": 1.30 - 1e-12}
    )
    assert not b1._positive_control_seed_passes(
        {"mapping_all_clones": False, "j_eval": 1.35}
    )
    assert b1._correct_table_seed_is_exact(
        {"mapping_all_clones": True, "j_eval": 1.350000000001}
    )
    assert not b1._correct_table_seed_is_exact(
        {"mapping_all_clones": True, "j_eval": 1.3500000000011}
    )
    assert b1._full_candidate_gate(psi=0.05 + 1e-12, kappa=0.70, mapping_seeds=4)
    assert not b1._full_candidate_gate(psi=0.05, kappa=0.70, mapping_seeds=4)
    assert not b1._full_candidate_gate(psi=0.06, kappa=0.70 - 1e-12, mapping_seeds=4)
    assert not b1._full_candidate_gate(psi=0.06, kappa=0.70, mapping_seeds=3)
    support = {
        f"{cue}|{action.value}": 32 for cue in (0, 1) for action in b1.Action
    }
    assert b1._support_counts_meet_floor(support)
    support["1|HOLD"] = 31
    assert not b1._support_counts_meet_floor(support)


def test_evaluation_argmax_ties_fail_the_heldout_mapping():
    rows = []
    for true_cue in (0, 1):
        for action in b1.Action:
            _, _, episode = _host_episode(true_cue, action, probabilities=(0.5, 0.5))
            rows.append(episode)
    summary = b1.summarize_evaluation_rows(rows)
    assert summary["argmax_ties"] == 2
    assert summary["mapping_all_clones"] is False


def _classification_payload() -> dict[str, object]:
    return {
        "gates": {
            "host_information_contract": True,
            "activity_nonzero": True,
            "support_floor": True,
            "x_memory_positive_control": True,
            "x_memory_table_exactness": True,
            "full_gate": True,
        },
        "arm_mean_j_eval": {
            "FULL_LIFECYCLE_GRU_ACTOR_CRITIC": 1.40,
            "X_MEMORY_TABULAR_MONTE_CARLO": 1.40,
            "CUE_BLIND_GRU": 0.75,
            "CUE_SHUFFLED_GRU": 0.75,
            "CURRENT_ONLY_GRU": 0.75,
            "RAW_HISTORY_TABULAR_MEMORIZER": 0.75,
        },
    }


def test_terminal_branch_precedence_is_exhaustive_and_exact():
    expected_faults = (
        ("host_information_contract", "B1V2_INVALID_HOST_OR_INFORMATION_LEAK"),
        ("activity_nonzero", "B1V2_ACTIVITY_OR_SUPPORT_INSUFFICIENT"),
        ("support_floor", "B1V2_ACTIVITY_OR_SUPPORT_INSUFFICIENT"),
        ("x_memory_positive_control", "B1V2_LEARNING_PIPELINE_UNCALIBRATED"),
        ("x_memory_table_exactness", "B1V2_LEARNING_PIPELINE_UNCALIBRATED"),
        ("full_gate", "B1V2_FULL_LEARNER_FAILED"),
    )
    for gate, branch in expected_faults:
        payload = _classification_payload()
        payload["gates"][gate] = False
        assert b1.classify_b1v2(payload) == branch

    payload = _classification_payload()
    payload["arm_mean_j_eval"]["CUE_BLIND_GRU"] = 1.35
    assert b1.classify_b1v2(payload) == "B1V2_CUE_ATTRIBUTION_FAILED"
    payload = _classification_payload()
    payload["arm_mean_j_eval"]["CURRENT_ONLY_GRU"] = 1.35
    assert b1.classify_b1v2(payload) == "B1V2_CURRENT_ONLY_SHORTCUT_SUFFICIENT"
    payload = _classification_payload()
    payload["arm_mean_j_eval"]["RAW_HISTORY_TABULAR_MEMORIZER"] = 1.35
    assert b1.classify_b1v2(payload) == "B1V2_RAW_MEMORIZATION_NOT_EXCLUDED"
    payload = _classification_payload()
    payload["arm_mean_j_eval"]["X_MEMORY_TABULAR_MONTE_CARLO"] = 1.46
    assert b1.classify_b1v2(payload) == "B1V2_CUE_LEARNING_PARTIAL_TABULAR_STRONGER"
    assert b1.classify_b1v2(_classification_payload()) == (
        "B1V2_CUE_CONDITIONED_LIFECYCLE_LEARNING_TABULAR_SUFFICIENT"
    )
    payload = _classification_payload()
    payload["arm_mean_j_eval"]["X_MEMORY_TABULAR_MONTE_CARLO"] = 1.30
    assert b1.classify_b1v2(payload) == "B1V2_EVALUATION_DOMINANCE_INVARIANT_VIOLATED"


@pytest.mark.parametrize(
    ("x_memory", "branch"),
    [
        (1.450000000001, "B1V2_CUE_LEARNING_PARTIAL_TABULAR_STRONGER"),
        (1.45, "B1V2_CUE_CONDITIONED_LIFECYCLE_LEARNING_TABULAR_SUFFICIENT"),
        (1.399999999999, "B1V2_CUE_CONDITIONED_LIFECYCLE_LEARNING_TABULAR_SUFFICIENT"),
        (1.3999999999989, "B1V2_EVALUATION_DOMINANCE_INVARIANT_VIOLATED"),
    ],
)
def test_amended_dominance_branches_use_exact_asymmetric_boundaries(x_memory, branch):
    payload = _classification_payload()
    payload["arm_mean_j_eval"]["X_MEMORY_TABULAR_MONTE_CARLO"] = x_memory
    assert b1.classify_b1v2(payload) == branch


def test_manifest_freezes_exact_roster_counts_rng_and_nonadmitted_exercise():
    manifest = b1.build_manifest(
        source_revision="a" * 40, run_id="registered-test", technical_only=False
    )
    assert b1.validate_manifest(manifest) == ()
    assert manifest["seed_ids"] == list(b1.B1_SEED_IDS)
    assert manifest["training_blocks"] == 16
    assert manifest["caps"]["training_episodes_exact"] == 30_720
    assert manifest["caps"]["neural_optimizer_updates_exact"] == 640
    assert manifest["caps"]["tabular_updates_exact"] == 10_240
    assert manifest["a2_table_role"] == "EVALUATOR_CALIBRATION_ONLY_NOT_IMPORTED"
    assert manifest["assignment_id"] == b1.B1_ASSIGNMENT_ID
    assert manifest["artifact_kind"] == "vsp02_b1v2_frozen_manifest"
    assert all("FINITE_BUDGET" not in branch for branch in manifest["branch_precedence"])

    exercise = b1.build_manifest(
        source_revision="a" * 40, run_id="technical-test", technical_only=True
    )
    assert exercise["admitted"] is False
    assert exercise["pool_units"] == 0
    assert exercise["training_blocks"] == 1
    assert exercise["seed_ids"] == [b1.B1_SEED_IDS[0]]


def test_old_v1_ids_artifact_kinds_and_root_are_rejected():
    manifest = b1.build_manifest(
        source_revision="a" * 40, run_id="old-id-test", technical_only=True
    )
    old_manifest = deepcopy(manifest)
    old_manifest["assignment_id"] = "VSP02-B1-LEARNED-CUE-CONDITIONED-LIFECYCLE-CONTROL"
    old_manifest["artifact_kind"] = "vsp02_b1_frozen_manifest"
    assert b1.validate_manifest(old_manifest)

    old_training = {
        "artifact_kind": "vsp02_b1_training",
        "manifest_identity": b1.manifest_identity(manifest),
        "fits": [],
    }
    assert "training artifact kind mismatch" in b1.validate_training_artifact(
        manifest, old_training
    )

    old_evaluation = {
        "artifact_kind": "vsp02_b1_evaluation",
        "manifest_identity": b1.manifest_identity(manifest),
        "evaluations": [],
        "activity": {},
    }
    assert "evaluation artifact kind mismatch" in b1.validate_evaluation_artifact(
        manifest, {"fits": []}, old_evaluation
    )

    runner = _runner_module()
    result = runner._result_payload(
        manifest, {"admission": "NONADMITTED_TECHNICAL_ONLY", "branch": None}
    )
    assert result["artifact_kind"] == "vsp02_b1v2_result"
    assert "vsp02_b1_registered_full_claim" not in inspect.getsource(runner)
    with tempfile.TemporaryDirectory(prefix="vsp02_b1_learned_cue_conditioned_lifecycle_control_") as directory:
        with pytest.raises(ValueError, match="vsp02_b1v2"):
            runner._require_root(Path(directory))


def test_source_reuses_a1_without_importing_a2_evaluator():
    source = inspect.getsource(b1)
    assert "owner_action_responsive_lifecycle as a1" in source
    assert "crossed_physical_value_support" not in source


def test_runner_artifacts_and_claims_are_exclusive():
    runner = _runner_module()
    with tempfile.TemporaryDirectory(prefix="vsp02-b1v2-test-") as directory:
        temporary = Path(directory)
        output = temporary / "artifact.json"
        runner._write_once(output, {"first": True})
        with pytest.raises(FileExistsError):
            runner._write_once(output, {"second": True})
        claim = temporary / "claim.json"
        runner._exclusive_claim(claim, {"claim": 1})
        with pytest.raises(FileExistsError):
            runner._exclusive_claim(claim, {"claim": 2})
        assert json.loads(output.read_text()) == {"first": True}


def test_episode_validator_rejects_reward_or_escrow_tampering():
    _, _, episode = _host_episode(1, b1.Action.HOLD)
    tampered = deepcopy(episode)
    tampered["reward_sequence"] = [2, 0]
    assert "physical reward mismatch" in b1._episode_issues(tampered)
    tampered = deepcopy(episode)
    tampered["escrow"]["consumption_count"] = 2
    assert "escrow/closure mismatch" in b1._episode_issues(tampered)
