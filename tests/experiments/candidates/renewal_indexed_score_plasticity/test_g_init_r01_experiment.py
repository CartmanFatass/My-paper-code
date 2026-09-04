from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import torch


CANDIDATE = Path(__file__).resolve().parents[4] / "experiments" / "candidates" / "renewal_indexed_score_plasticity"
sys.path.insert(0, str(CANDIDATE))

import g_init_r01_experiment as experiment  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _bind_synthetic_test_root() -> None:
    assert experiment.coordinate_root() is None
    assert experiment.fixture_root() is None
    assert experiment.configure_test_fixture_root("a" * 64) == "a" * 64


def test_unbound_stochastic_entry_points_fail_closed_in_fresh_process() -> None:
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(CANDIDATE)!r}); "
        "import g_init_r01_experiment as e; "
        "assert e.coordinate_root() is None; "
        "\ntry:\n e.run_evaluation_unit(0, 'UNIFORM', 0, {}, episodes=1)\n"
        "except RuntimeError as x:\n assert 'unbound' in str(x)\n"
        "else:\n raise AssertionError('stochastic entry point did not fail closed')\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True, cwd=CANDIDATE)


def test_test_fixture_binding_is_exactly_once_and_never_appears_as_production_root() -> None:
    assert experiment.coordinate_root() is None
    assert experiment.fixture_root() == "a" * 64
    with pytest.raises(RuntimeError, match="already configured"):
        experiment.configure_test_fixture_root("b" * 64)


def test_production_binder_requires_validation_and_rejects_all_three_forbidden_values() -> None:
    with pytest.raises(RuntimeError, match="validated production binding"):
        experiment.configure_production_coordinate_root("c" * 64, validated_production_binding=False)
    for forbidden in experiment.FORBIDDEN_PRODUCTION_ROOTS:
        with pytest.raises(RuntimeError, match="permanently excluded"):
            experiment.configure_production_coordinate_root(forbidden, validated_production_binding=True)


def test_exact_frozen_registry_and_schedules() -> None:
    assert experiment.SCIENCE_REVISION == "RISP-G-INIT-REACH-SCIENCE-20260821-01"
    assert experiment.ALGORITHM_SEEDS == tuple(range(16))
    assert experiment.ARMS == ("G-START/ZERO-CENTER", "ZERO-START/ZERO-CENTER")
    assert experiment.CELL_FAMILIES == (
        "G-START/ZERO-CENTER-INTACT",
        "ZERO-START/ZERO-CENTER-INTACT",
        "UNIFORM",
        "STATE-ORACLE",
    )
    assert experiment.CHECKPOINT_UPDATES == (0, 64, 128, 256, 512)
    assert [(len(experiment.schedule_rows(i)), sum(not row[2] for row in experiment.schedule_rows(i))) for i in range(5)] == [
        (48, 47), (24, 23), (16, 15), (32, 31), (32, 31)
    ]
    assert experiment.schedule_rows(3)[24][:2] == (96, 12)
    assert experiment.schedule_rows(4)[8][:2] == (96, 4)


def test_only_e_initialization_differs_and_both_decay_centers_are_zero() -> None:
    certificate = experiment.structural_certificate()
    assert certificate["passed"] is True
    assert certificate["schema"] == experiment.TEST_STRUCTURAL_SCHEMA
    assert certificate["science_revision"] == experiment.TEST_FIXTURE_REVISION
    assert certificate["test_fixture"] is True
    assert certificate["initialization_only_arm_difference"] is True
    assert certificate["zero_decay_center_both_arms"] is True
    slow = {
        "w1": torch.zeros((8, 2), dtype=torch.float64),
        "w2": torch.zeros((4, 8), dtype=torch.float64),
        "w3": torch.zeros((3, 4), dtype=torch.float64),
    }
    g_arm = experiment.TrackModel(0, experiment.ARMS[0], slow_arrays=slow)
    zero_arm = experiment.TrackModel(0, experiment.ARMS[1], slow_arrays=slow)
    for name in ("w1", "b1", "w2", "b2", "w3", "b3"):
        assert torch.equal(getattr(g_arm, name), getattr(zero_arm, name))
    assert torch.equal(g_arm.E, experiment.g_matrix())
    assert torch.equal(zero_arm.E, torch.zeros_like(zero_arm.E))
    assert torch.equal(g_arm.E_center, torch.zeros_like(g_arm.E_center))
    assert torch.equal(zero_arm.E_center, torch.zeros_like(zero_arm.E_center))
    assert sum(p.numel() for p in g_arm.ordered_parameters()) == 114
    assert sum(p.numel() for p in zero_arm.ordered_parameters()) == 114


def test_paired_slow_and_event_identities_are_arm_independent_and_test_namespaced() -> None:
    first = experiment.slow_initialization(5)
    second = experiment.slow_initialization(5)
    assert all(torch.equal(first[name], second[name]) for name in first)
    identity = experiment.event_identity(5, "TRAIN", 7, 3, 1, 2, "ACTION")
    identity_packet = json.loads(experiment._identity_bytes(identity).decode("ascii"))
    assert identity_packet == {
        "coordinate_schema": "RISP-G-INIT-REACH-TEST-CERTIFICATE-V1",
        "fixture_root": "a" * 64,
        "identity": list(identity),
        "namespace": "TEST/RISP-G-INIT-REACH/CERTIFICATE-FIXTURE/V1",
        "namespace_class": "TEST_ONLY",
        "test_fixture_revision": "RISP-G-INIT-REACH-TEST-FIXTURE-20260821-01",
    }
    assert "coordinate_root" not in identity_packet
    assert experiment.SCIENCE_REVISION not in experiment._identity_bytes(identity).decode("ascii")
    probabilities = tuple(experiment.interval_ratio(1, 3) for _ in range(3))
    audit_a = experiment.SamplerAudit()
    audit_b = experiment.SamplerAudit()
    assert experiment.exact_cat(probabilities, identity, "ACTION", audit_a) == experiment.exact_cat(probabilities, identity, "ACTION", audit_b)
    assert audit_a.calls == audit_b.calls == {"ACTION": 1}


def test_reduced_training_and_uniform_evaluation_paths() -> None:
    training = experiment.run_training_unit(31, experiment.ARMS[0], updates=1, episodes=2)
    paired_training = experiment.run_training_unit(31, experiment.ARMS[1], updates=1, episodes=2)
    assert training["registered"] is False
    assert training["schema"] == experiment.TEST_TRAINING_SCHEMA
    assert training["science_revision"] == experiment.TEST_FIXTURE_REVISION
    assert training["binding_class"] == "TEST_ONLY"
    assert training["test_fixture"] is True
    assert training["arm"] == experiment.ARMS[0]
    assert training["updates"] == 1
    assert training["conclusion_update"] == 512
    assert training["sampler_audit"]["calls"] == {
        "ACK": 144,
        "ACTION": 144,
        "INIT_MODEL": 60,
        "INIT_SECTOR": 4,
        "MOTION": 144,
    }
    assert training["initial_slow_tensor_sha256"] == paired_training["initial_slow_tensor_sha256"]
    assert training["sampler_audit"]["calls"] == paired_training["sampler_audit"]["calls"]
    assert torch.tensor(training["final_state"]["E_center"], dtype=torch.float64).count_nonzero() == 0
    assert torch.tensor(paired_training["final_state"]["E_center"], dtype=torch.float64).count_nonzero() == 0

    evaluation = experiment.run_evaluation_unit(31, "UNIFORM", 2, {}, episodes=1)
    assert evaluation["registered"] is False
    assert evaluation["schema"] == experiment.TEST_EVALUATION_SCHEMA
    assert evaluation["science_revision"] == experiment.TEST_FIXTURE_REVISION
    assert evaluation["binding_class"] == "TEST_ONLY"
    assert evaluation["test_fixture"] is True
    assert evaluation["result"]["decisions"] == 32
    assert evaluation["result"]["updates"] == 0
    assert evaluation["result"]["diagnostic"] is None
    assert evaluation["result"]["min_support"] == pytest.approx(1 / 3)


def _fake_training(seed: int, arm: str) -> dict:
    return {
        "schema": experiment.TEST_TRAINING_SCHEMA,
        "science_revision": experiment.TEST_FIXTURE_REVISION,
        "binding_class": "TEST_ONLY",
        "test_fixture": True,
        "algorithm_seed": seed,
        "arm": arm,
        "registered": False,
        "updates": 512,
        "episodes_per_batch": 16,
        "conclusion_update": 512,
        "initial_slow_tensor_sha256": hashlib.sha256(f"TEST-SLOW-{seed}".encode("ascii")).hexdigest(),
        "treatment_fence": {
            "initial_e": "G" if arm == "G-START/ZERO-CENTER" else "ZERO",
            "e_center": "ZERO",
            "zero_optimizer_moments": True,
            "trainable_scalars": 114,
            "slow_initialization_identity": [seed, "INIT_MODEL"],
            "paired_event_identity_excludes_arm": True,
        },
    }


def _fake_evaluation(seed: int, cell: str, schedule: int, g_ok: bool, zero_ok: bool) -> dict:
    learned = cell.endswith("-INTACT")
    if cell == "UNIFORM":
        q, support, diagnostic = 0.20, 1 / 3, None
    elif cell == "STATE-ORACLE":
        q, support, diagnostic = 0.80, 1 / 60, None
    else:
        q, support = 0.50, 0.10
        arm_ok = g_ok if cell.startswith("G-START") else zero_ok
        diagnostic = {
            "rows": {0: 47, 1: 23, 2: 15, 3: 7, 4: 23}[schedule] * 128,
            "tv_ge_001_fraction": 0.30 if arm_ok else 0.25,
            "delta_positive_fraction": 0.60,
            "delta_mean": 0.006,
            "tv_mean": 0.10,
        }
    decisions = len(experiment.schedule_rows(schedule)) * 128
    updates = (len(experiment.schedule_rows(schedule)) - 1) * 128 if learned else 0
    return {
        "schema": experiment.TEST_EVALUATION_SCHEMA,
        "science_revision": experiment.TEST_FIXTURE_REVISION,
        "binding_class": "TEST_ONLY",
        "test_fixture": True,
        "algorithm_seed": seed,
        "cell": cell,
        "schedule_id": schedule,
        "registered": False,
        "episodes": 64,
        "conclusion_update": 512,
        "evaluation_fence": {
            "actual_completed_recipient_ack_primary_rows": True,
            "offline_belief_does_not_enter_policy": True,
            "offline_scores_do_not_enter_loss_or_optimizer": True,
            "control": cell if cell in ("UNIFORM", "STATE-ORACLE") else None,
            "paired_event_identity_excludes_cell": True,
        },
        "result": {
            "q": q,
            "q_full": q,
            "decisions": decisions,
            "updates": updates,
            "min_support": support,
            "action_counts": [decisions, 0, 0],
            "ack_success_rate": 0.5,
            "direct_tv_max_residual": 0.0,
            "diagnostic": diagnostic,
        },
    }


@pytest.mark.parametrize(
    ("g_ok", "zero_ok", "expected"),
    [
        (True, False, "G_START_ONLY_ANSWERABILITY_QUALIFIED"),
        (True, True, "BOTH_STARTS_ANSWERABILITY_QUALIFIED"),
        (False, False, "NEITHER_START_ANSWERABILITY_QUALIFIED"),
        (False, True, "ZERO_START_ONLY_ANSWERABILITY_QUALIFIED"),
    ],
)
def test_complete_analyzer_uses_exact_30_arm_local_bounds_and_fixed_psi_map(g_ok: bool, zero_ok: bool, expected: str) -> None:
    training = [_fake_training(seed, arm) for seed in experiment.ALGORITHM_SEEDS for arm in experiment.ARMS]
    evaluation = [
        _fake_evaluation(seed, cell, schedule, g_ok, zero_ok)
        for seed in experiment.ALGORITHM_SEEDS
        for cell in experiment.CELL_FAMILIES
        for schedule in range(5)
    ]
    result = experiment.analyze_test_fixture_complete(training, evaluation)
    assert result["schema"] == experiment.TEST_RESULT_SCHEMA
    assert result["science_revision"] == experiment.TEST_FIXTURE_REVISION
    assert result["test_fixture"] is True
    assert all(result["validity"].values())
    assert result["registered_one_sided_bound_count"] == 30
    assert result["psi"] == [int(g_ok), int(zero_ok)]
    assert result["branch"] == expected
    assert result["continuous_arm_contrast_selects_branch"] is False
    assert result["partial_scientific_values_exposed"] is False
    for arm in experiment.ARMS:
        assert tuple(result["arm_local_statistics"][arm]) == ("k=4", "k=8", "TARGET")


def test_analyzer_rejects_partial_panel_before_exposing_values() -> None:
    training = [_fake_training(seed, arm) for seed in experiment.ALGORITHM_SEEDS for arm in experiment.ARMS]
    evaluation = [
        _fake_evaluation(seed, cell, schedule, True, False)
        for seed in experiment.ALGORITHM_SEEDS
        for cell in experiment.CELL_FAMILIES
        for schedule in range(5)
    ]
    with pytest.raises(RuntimeError, match="exactly 32 training and 320 evaluation"):
        experiment.analyze_test_fixture_complete(training, evaluation[:-1])


def test_production_analyzer_rejects_test_packets() -> None:
    training = [_fake_training(seed, arm) for seed in experiment.ALGORITHM_SEEDS for arm in experiment.ARMS]
    evaluation = [
        _fake_evaluation(seed, cell, schedule, True, False)
        for seed in experiment.ALGORITHM_SEEDS
        for cell in experiment.CELL_FAMILIES
        for schedule in range(5)
    ]
    with pytest.raises(RuntimeError, match="production analyzer requires"):
        experiment.analyze_complete(training, evaluation)
    with pytest.raises(RuntimeError, match="schema or revision"):
        experiment._checkpoint_state_from_training_packet(training[0], training[0]["arm"], "PRODUCTION", training[0]["algorithm_seed"])


def test_checkpoint_consumer_rejects_wrong_seed_before_final_state_read() -> None:
    packet = _fake_training(3, experiment.ARMS[0])
    assert "final_state" not in packet
    with pytest.raises(RuntimeError, match="algorithm seed mismatch"):
        experiment._checkpoint_state_from_training_packet(packet, experiment.ARMS[0], "TEST_ONLY", 4)


def test_paired_slow_digest_tamper_selects_no_branch() -> None:
    training = [_fake_training(seed, arm) for seed in experiment.ALGORITHM_SEEDS for arm in experiment.ARMS]
    training[1]["initial_slow_tensor_sha256"] = "f" * 64
    evaluation = [
        _fake_evaluation(seed, cell, schedule, True, False)
        for seed in experiment.ALGORITHM_SEEDS
        for cell in experiment.CELL_FAMILIES
        for schedule in range(5)
    ]
    result = experiment.analyze_test_fixture_complete(training, evaluation)
    assert result["validity"]["paired_initial_slow_tensor_digest"] is False
    assert result["psi"] is None
    assert result["branch"] == "NO_BRANCH_SELECTED_INVALID_PANEL"
    assert result["registered_one_sided_bound_count"] == 0


def test_expected_ledger_and_atomic_json_surface(tmp_path: Path) -> None:
    assert experiment.expected_complete_ledger() == {
        "INIT_MODEL": 960,
        "INIT_SECTOR": 565248,
        "ACTION": 20119552,
        "MOTION": 20119552,
        "ACK": 20119552,
    }
    target = tmp_path / "packet.json"
    experiment.atomic_write_json(target, {"schema": "TEST-ONLY", "finite": True})
    assert json.loads(target.read_text(encoding="utf-8")) == {"finite": True, "schema": "TEST-ONLY"}
    fingerprints = experiment.source_fingerprint([target])
    assert list(fingerprints) == [str(target.resolve())]
    assert len(next(iter(fingerprints.values()))) == 64
