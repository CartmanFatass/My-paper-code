from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import run_uav_charge_rotation_g2 as runner


def _predicates(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "operational_valid": True,
        "source_identifiable": True,
        "fixed_access_pass": True,
        "fixed_access_fail": False,
        "open_access_pass": True,
        "open_access_fail": False,
        "g_svc_lcb": 0.0,
        "g_svc_ucb": runner.SERVICE_GAIN_MARGIN,
        "g_rejoin_lcb": 0.0,
        "g_rejoin_ucb": runner.REJOIN_GAIN_MARGIN,
        "g_ordinary_lcb": 0.0,
    }
    values.update(changes)
    return values


def test_formal_contract_token_schedule_profiles_and_fresh_seeds() -> None:
    assert runner.FORMAL_AUTHORIZATION_TOKEN == (
        "AUTHORIZE_UAV_CHARGE_ROTATION_ROSTER_G2_FORMAL_CPU_V1"
    )
    assert asdict(runner.FORMAL_CONFIG) == {
        "replicates": 3,
        "updates": 128,
        "num_envs": 8,
        "horizon": 1500,
        "ppo_passes": 4,
        "evaluation_episodes": 128,
        "evaluation_batch_size": 16,
        "control_episodes": 128,
        "bootstrap_resamples": 10_000,
        "checkpoint_selection": "final_update_128_only",
    }
    assert runner.EVALUATION_PROFILES == (
        runner.EnergyProfile.IID,
        runner.EnergyProfile.LOW_ENERGY,
        runner.EnergyProfile.SYNCHRONIZED_PRESSURE,
    )
    assert len(runner.STRATA) == 6
    assert len({value for value in asdict(runner.SeedRegistry()).values()}) == len(
        asdict(runner.SeedRegistry())
    )
    assert min(asdict(runner.SeedRegistry()).values()) >= 2_000_000
    assert runner._replicate_seeds(1) == {
        name: value + 10_000
        for name, value in asdict(runner.SeedRegistry()).items()
    }
    runner._validate_launch(
        formal=True,
        authorization_token=runner.FORMAL_AUTHORIZATION_TOKEN,
        config=runner.FORMAL_CONFIG,
    )
    with pytest.raises(ValueError, match="authorization token"):
        runner._validate_launch(
            formal=True, authorization_token="wrong", config=runner.FORMAL_CONFIG
        )


def test_launch_recovery_requires_truncated_identity_to_be_sole_entry(
    tmp_path: Path,
) -> None:
    identity = {"schema": runner.LAUNCH_SCHEMA, "token": "expected"}
    recoverable = tmp_path / "recoverable"
    recoverable.mkdir()
    (recoverable / "launch_identity.json").write_text(
        '{"partial":', encoding="utf-8"
    )
    assert runner._open_launch(recoverable, identity) is True
    assert runner._read_json(recoverable / "launch_identity.json") == identity

    poisoned = tmp_path / "poisoned"
    poisoned.mkdir()
    (poisoned / "launch_identity.json").write_text('{"partial":', encoding="utf-8")
    (poisoned / "later_artifact.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="cannot be recovered"):
        runner._open_launch(poisoned, identity)
    with pytest.raises(ValueError, match="frozen contract"):
        runner._validate_launch(
            formal=True,
            authorization_token=runner.FORMAL_AUTHORIZATION_TOKEN,
            config=runner.EXERCISE_CONFIG,
        )


@pytest.mark.parametrize(
    ("inputs", "expected"),
    [
        (
            _predicates(operational_valid=False, source_identifiable=False),
            runner.INVALID_RESULT,
        ),
        (
            _predicates(source_identifiable=False, fixed_access_fail=True),
            runner.SOURCE_NON_IDENTIFIABLE_RESULT,
        ),
        (
            _predicates(
                fixed_access_pass=False,
                fixed_access_fail=True,
                open_access_pass=False,
                open_access_fail=True,
            ),
            runner.NO_ACCESS_RESULT,
        ),
        (
            _predicates(
                fixed_access_pass=False,
                fixed_access_fail=False,
                open_access_pass=False,
                open_access_fail=True,
            ),
            runner.UNDERPOWERED_RESULT,
        ),
        (_predicates(), runner.MASK_SUFFICIENT_RESULT),
        (
            _predicates(
                fixed_access_pass=False,
                g_svc_lcb=float(np.nextafter(runner.SERVICE_GAIN_MARGIN, 1.0)),
                g_svc_ucb=0.10,
                g_rejoin_lcb=float(np.nextafter(runner.REJOIN_GAIN_MARGIN, 1.0)),
                g_rejoin_ucb=0.10,
                g_ordinary_lcb=runner.ORDINARY_NONINFERIORITY_MARGIN,
            ),
            runner.DYNAMIC_SUPPORTED_RESULT,
        ),
        (
            _predicates(
                fixed_access_pass=False,
                g_svc_lcb=runner.SERVICE_GAIN_MARGIN,
                g_svc_ucb=0.10,
                g_rejoin_lcb=0.10,
                g_rejoin_ucb=0.10,
            ),
            runner.MIXED_RESULT,
        ),
    ],
)
def test_exact_seven_branch_precedence(
    inputs: dict[str, object], expected: str
) -> None:
    assert runner.select_result_branch(inputs) == expected


def test_source_predicate_exact_floors_and_strict_performance() -> None:
    intervals = {
        profile.value: {
            "constructive_phi": {"mean": runner.CONSTRUCTIVE_FLOOR},
            "constructive_minus_no_rotation": {
                "lcb95": runner.LOAD_BEARING_MARGIN
            },
        }
        for profile in runner.EVALUATION_PROFILES
    }
    support = {
        "constructive_cutoff_events": 0,
        "constructive_depletion_events": 0,
        "constructive_positive_return_cost_rows": 0,
        "iid_complete_cycles_per_replicate": [128, 128, 128],
        "low_energy_complete_cycles_per_replicate": [256, 256, 256],
        "synchronized_pressure_complete_cycles_per_replicate": [256, 256, 256],
        "late_rejoin_count": 0,
        "episodes_without_station_use": 0,
        "synchronized_concurrent_episode_counts": [64, 64, 64],
        "no_rotation_pressure_counts": {
            profile.value: [96, 96, 96] for profile in runner.EVALUATION_PROFILES
        },
        "physical_consistency": True,
        "energy_profile_law": True,
        "control_behavior": True,
        "no_future_leakage": True,
        "source_pressure": True,
    }
    result = runner.source_identification(intervals, support)
    assert result["constructive_feasibility_pass"] is True
    assert result["load_bearing_pass"] is False
    assert result["source_identifiable"] is False

    for profile in runner.EVALUATION_PROFILES:
        intervals[profile.value]["constructive_minus_no_rotation"]["lcb95"] = float(
            np.nextafter(runner.LOAD_BEARING_MARGIN, 1.0)
        )
    result = runner.source_identification(intervals, support)
    assert result["support_pass"] is True
    assert result["source_identifiable"] is True

    support["synchronized_concurrent_episode_counts"] = [64, 63, 64]
    assert runner.source_identification(intervals, support)["source_identifiable"] is False


def test_source_pressure_uses_initial_projection_and_all_audits_must_pass() -> None:
    config = runner.RunConfig(
        replicates=1,
        updates=1,
        num_envs=1,
        horizon=4,
        ppo_passes=1,
        evaluation_episodes=1,
        evaluation_batch_size=1,
        control_episodes=1,
        bootstrap_resamples=16,
        checkpoint_selection="final_update_1_only",
    )
    rows = runner.synthetic_control_rows(
        replicates=1,
        episodes=1,
        constructive_phi=1.0,
        no_rotation_phi=0.5,
    )
    for row in rows:
        evidence = row["source_evidence"]
        evidence["candidate_order"] = []
        evidence["projected_terminal_margins"] = [0.1] * 8
    _intervals, support = runner._source_intervals_and_support(
        rows, config=config, bootstrap_seed=7
    )
    assert support["source_pressure"] is True
    assert support["control_behavior"] is True

    failed = dict(rows[0]["source_evidence"]["projection_audit_history"][0])
    failed["trigger"] = "REJOIN"
    failed["strict_nearest_station_assignment"] = False
    rows[0]["source_evidence"]["projection_audit_history"].append(failed)
    rows[0]["source_evidence"]["projection_audit_count"] = 2
    rows[0]["source_evidence"]["all_projection_audits_pass"] = False
    _intervals, support = runner._source_intervals_and_support(
        rows, config=config, bootstrap_seed=7
    )
    assert support["control_behavior"] is False


def test_arm_safety_equality_pass_fail_and_underpowered() -> None:
    access = {"lcb95": 1.0, "ucb95": 1.0}
    exact = {
        key: {
            "catastrophe_fraction": {"lcb95": 0.05, "ucb95": 0.05},
            "return_cost_burden": {"lcb95": 0.05, "ucb95": 0.05},
        }
        for key in runner.STRATUM_KEYS
    }
    assert runner.classify_arm_access(access, exact) == {
        "access_pass": True,
        "access_fail": False,
        "access_underpowered": False,
        "safe_pass": True,
        "safe_fail": False,
    }
    first = exact[runner.STRATUM_KEYS[0]]["catastrophe_fraction"]
    first["ucb95"] = 0.06
    assert runner.classify_arm_access(access, exact)["access_underpowered"] is True
    first["lcb95"] = float(np.nextafter(0.05, 1.0))
    assert runner.classify_arm_access(access, exact)["access_fail"] is True


def test_hierarchical_bootstrap_pairs_arms_and_whole_episode_ids() -> None:
    shape = (2, len(runner.STRATA), 4)
    fixed = np.zeros(shape, dtype=np.float64)
    complementary = np.array([0.4, 0.0, 0.4, 0.0])
    gain = np.stack(
        [complementary if index % 2 == 0 else complementary[::-1] for index in range(shape[1])]
    )
    opened = np.stack([fixed[0] + gain, fixed[1] + gain])
    interval = runner.hierarchical_paired_interval(
        opened - fixed, resamples=512, seed=1234
    )
    assert interval["mean"] == pytest.approx(0.2)
    assert interval["lcb95"] == pytest.approx(0.2)
    assert interval["ucb95"] == pytest.approx(0.2)


def test_learned_intervals_preserves_six_strata_and_whole_episode_pairing() -> None:
    config = runner.RunConfig(
        replicates=2,
        updates=1,
        num_envs=1,
        horizon=4,
        ppo_passes=1,
        evaluation_episodes=4,
        evaluation_batch_size=2,
        control_episodes=4,
        bootstrap_resamples=128,
        checkpoint_selection="final_update_1_only",
    )
    fixed_by_stratum = np.asarray([0.80, 0.72, 0.64, 0.56, 0.48, 0.40])
    complementary = np.asarray(
        [
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.08, 0.0, 0.08, 0.0],
            [0.0, 0.08, 0.0, 0.08],
            [0.08, 0.0, 0.08, 0.0],
            [0.0, 0.08, 0.0, 0.08],
        ]
    )
    rows: list[dict[str, object]] = []
    for arm in runner.ARM_NAMES:
        for replicate in range(config.replicates):
            action_seed = runner._replicate_seeds(replicate)["evaluation_action"]
            for stratum, (profile, mode) in enumerate(runner.STRATA):
                for episode_id in range(config.evaluation_episodes):
                    gain = (
                        complementary[stratum, episode_id]
                        if arm == runner.PREFIX_NORMALIZED_OPEN_ROSTER
                        else 0.0
                    )
                    rows.append(
                        {
                            "arm": arm,
                            "replicate": replicate,
                            "profile": profile,
                            "action_mode": mode,
                            "episode_id": episode_id,
                            "ledger_id": f"{replicate}:{profile}:{episode_id}",
                            "action_seed": action_seed,
                            "deterministic": mode == "deterministic",
                            "J_event": float(fixed_by_stratum[stratum] + gain),
                            "J_rejoin": float(0.70 + gain),
                            "Q_ordinary": 0.90,
                            "catastrophe_episode": 0,
                            "return_cost_burden": 0.0,
                        }
                    )

    intervals = runner.learned_intervals(rows, config=config, seed=8103)
    assert intervals["access"][runner.FIXED_MASK_REC]["mean"] == pytest.approx(
        0.5
    )
    assert intervals["access"][runner.FIXED_MASK_REC]["lcb95"] == pytest.approx(
        0.5
    )
    assert intervals["gains"]["g_svc"]["mean"] == pytest.approx(0.04)
    assert intervals["gains"]["g_svc"]["lcb95"] == pytest.approx(0.04)
    assert intervals["gains"]["g_svc"]["ucb95"] == pytest.approx(0.04)


def test_source_screen_failure_prunes_learning_before_model_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called = {"models": 0}

    def source_rows(*_args: object, **_kwargs: object) -> list[dict[str, object]]:
        return runner.synthetic_control_rows(
            replicates=1,
            episodes=2,
            constructive_phi=0.8,
            no_rotation_phi=0.7,
        )

    def model_forbidden(*_args: object, **_kwargs: object) -> None:
        called["models"] += 1
        raise AssertionError("model created after failed source screen")

    monkeypatch.setattr(runner, "_collect_source_rows", source_rows)
    monkeypatch.setattr(runner, "MatchedChargeRotationPolicy", model_forbidden)
    config = runner.RunConfig(
        replicates=1,
        updates=1,
        num_envs=1,
        horizon=4,
        ppo_passes=1,
        evaluation_episodes=2,
        evaluation_batch_size=1,
        control_episodes=2,
        bootstrap_resamples=32,
        checkpoint_selection="final_update_1_only",
    )
    manifest_path = runner.train_run(
        tmp_path,
        source_commit="NONFORMAL_SOURCE_SCREEN_TEST",
        formal=False,
        config=config,
    )
    manifest = runner._read_json(manifest_path)
    assert manifest["status"] == runner.TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE
    assert manifest["training_results"] == []
    assert called["models"] == 0
    assert not (tmp_path / "checkpoints").exists()
    assert not (tmp_path / "resume").exists()


def test_source_screen_chunk_journal_resumes_after_committed_interruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = runner.RunConfig(
        replicates=1,
        updates=1,
        num_envs=1,
        horizon=4,
        ppo_passes=1,
        evaluation_episodes=2,
        evaluation_batch_size=1,
        control_episodes=2,
        bootstrap_resamples=32,
        checkpoint_selection="final_update_1_only",
    )
    monkeypatch.setattr(
        runner,
        "_collect_source_rows",
        lambda **_kwargs: runner.synthetic_control_rows(
            replicates=1,
            episodes=2,
            constructive_phi=0.8,
            no_rotation_phi=0.7,
        ),
    )
    interruptions = {"count": 0}

    def interrupt_first(**_kwargs: object) -> None:
        interruptions["count"] += 1
        if interruptions["count"] == 1:
            raise RuntimeError("source chunk interruption")

    monkeypatch.setattr(runner, "_after_source_chunk_commit", interrupt_first)
    root = tmp_path / "source_resume"
    with pytest.raises(RuntimeError, match="source chunk interruption"):
        runner.train_run(
            root,
            source_commit="NONFORMAL_SOURCE_RESUME",
            formal=False,
            config=config,
        )
    first_binding = (
        root
        / "source_chunks/replicate_00/IID/CONSTRUCTIVE_CHARGE_ROTATION/"
        "batch_0000.binding.json"
    )
    first_bytes = first_binding.read_bytes()
    first_binding.write_text('{"partial":', encoding="utf-8")
    incomplete = first_binding.with_name("batch_0000.attempt_9999.json")
    incomplete.write_text('{"partial":', encoding="utf-8")

    monkeypatch.setattr(runner, "_after_source_chunk_commit", lambda **_kwargs: None)
    manifest_path = runner.train_run(
        root,
        source_commit="NONFORMAL_SOURCE_RESUME",
        formal=False,
        config=config,
    )
    assert runner._read_json(manifest_path)["status"] == (
        runner.TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE
    )
    assert first_binding.read_bytes() == first_bytes
    assert len(list((root / "source_chunks").rglob("*.binding.json"))) == 12

    tampered_binding = runner._read_json(first_binding)
    tampered_binding["sha256"] = "f" * 64
    runner._write_json(first_binding, tampered_binding)
    with pytest.raises(ValueError, match="binding|SHA-256"):
        runner._load_source_chunk(
            root,
            launch=runner._read_json(root / "launch_identity.json"),
            config=config,
            replicate=0,
            profile=runner.EnergyProfile.IID,
            control=runner.CONSTRUCTIVE_CHARGE_ROTATION,
            start=0,
        )


def test_training_resume_restores_rng_model_optimizer_and_ignores_fragment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = runner.RunConfig(
        replicates=1,
        updates=2,
        num_envs=1,
        horizon=4,
        ppo_passes=1,
        evaluation_episodes=1,
        evaluation_batch_size=1,
        control_episodes=1,
        bootstrap_resamples=16,
        checkpoint_selection="final_update_2_only",
    )
    resumed = tmp_path / "resumed"
    uninterrupted = tmp_path / "uninterrupted"

    def interrupt_first(**kwargs: object) -> None:
        if (
            kwargs["arm"] == runner.FIXED_MASK_REC
            and kwargs["completed_updates"] == 1
        ):
            raise RuntimeError("resume interruption")

    monkeypatch.setattr(runner, "_after_resume_commit", interrupt_first)
    with pytest.raises(RuntimeError, match="resume interruption"):
        runner.train_run(
            resumed,
            source_commit="NONFORMAL_TRAIN_RESUME",
            formal=False,
            config=config,
        )
    committed_marker = next(
        (resumed / "resume/replicate_00/FIXED_MASK_REC").glob(
            "update_0001.attempt_*.complete.json"
        )
    )
    committed_marker.write_text('{"partial":', encoding="utf-8")
    fragment = (
        resumed
        / "resume/replicate_00/FIXED_MASK_REC/update_0002.attempt_9999.pt"
    )
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_bytes(b"incomplete")

    monkeypatch.setattr(runner, "_after_resume_commit", lambda **_kwargs: None)
    resumed_manifest = runner._read_json(
        runner.train_run(
            resumed,
            source_commit="NONFORMAL_TRAIN_RESUME",
            formal=False,
            config=config,
        )
    )
    fixed_checkpoint = next(
        row
        for row in resumed_manifest["checkpoint_references"]
        if row["arm"] == runner.FIXED_MASK_REC
    )
    (resumed / fixed_checkpoint["complete_reference"]).write_text(
        '{"partial":', encoding="utf-8"
    )
    for name in (
        "train_manifest.binding.json",
        "train_manifest.json.complete.json",
        "train_manifest.json",
    ):
        (resumed / name).unlink()
    resumed_manifest = runner._read_json(
        runner.train_run(
            resumed,
            source_commit="NONFORMAL_TRAIN_RESUME",
            formal=False,
            config=config,
        )
    )
    uninterrupted_manifest = runner._read_json(
        runner.train_run(
            uninterrupted,
            source_commit="NONFORMAL_TRAIN_RESUME",
            formal=False,
            config=config,
        )
    )
    for arm in runner.ARM_NAMES:
        resumed_checkpoint = next(
            row for row in resumed_manifest["checkpoint_references"] if row["arm"] == arm
        )
        uninterrupted_checkpoint = next(
            row
            for row in uninterrupted_manifest["checkpoint_references"]
            if row["arm"] == arm
        )
        resumed_payload = runner._torch_load(resumed / resumed_checkpoint["reference"])
        uninterrupted_payload = runner._torch_load(
            uninterrupted / uninterrupted_checkpoint["reference"]
        )
        assert runner._nested_equal(resumed_payload, uninterrupted_payload)


def test_evaluation_chunk_resume_reuses_commit_and_ignores_fragment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "evaluation_resume"
    runner.train_run(root, source_commit="NONFORMAL_EVAL_RESUME", formal=False)
    count = {"value": 0}

    def interrupt_first(**_kwargs: object) -> None:
        count["value"] += 1
        if count["value"] == 1:
            raise RuntimeError("evaluation interruption")

    monkeypatch.setattr(runner, "_after_evaluation_chunk_commit", interrupt_first)
    with pytest.raises(RuntimeError, match="evaluation interruption"):
        runner.evaluate_run(root)
    first_binding = (
        root
        / "evaluation_chunks/replicate_00/FIXED_MASK_REC/IID/"
        "deterministic/batch_0000.json.binding.json"
    )
    first_bytes = first_binding.read_bytes()
    first_binding.write_text('{"partial":', encoding="utf-8")
    logical_dir = first_binding.parent
    (logical_dir / "batch_0001.attempt_9999.json").write_text(
        '{"partial":', encoding="utf-8"
    )

    monkeypatch.setattr(
        runner, "_after_evaluation_chunk_commit", lambda **_kwargs: None
    )
    evaluation_path = runner.evaluate_run(root)
    assert runner._read_json(evaluation_path)["status"] == "EVALUATION_COMPLETE"
    assert first_binding.read_bytes() == first_bytes


def test_bounded_nonformal_exercise_is_complete_and_rejected_as_formal(
    tmp_path: Path,
) -> None:
    root = tmp_path / "exercise"
    result_path = runner.exercise(root, source_commit="NONFORMAL_WORKTREE")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["result"] == runner.NONFORMAL_RESULT
    runner.validate_run_artifacts(root, require_formal=False)
    with pytest.raises(ValueError, match="formal"):
        runner.validate_formal_result(root)


def test_artifact_closure_rejects_identity_and_row_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "exercise"
    runner.train_run(root, source_commit="NONFORMAL_WORKTREE", formal=False)
    runner.evaluate_run(root)
    monkeypatch.setattr(
        runner,
        "_after_analysis_commit",
        lambda: (_ for _ in ()).throw(RuntimeError("analysis interruption")),
    )
    with pytest.raises(RuntimeError, match="analysis interruption"):
        runner.analyze_run(root)
    assert not (root / "result.json").exists()
    (root / "result.json").write_text('{"partial":', encoding="utf-8")
    analysis_binding = root / "analysis.binding.json"
    analysis_bytes = analysis_binding.read_bytes()
    analysis_binding.write_text('{"partial":', encoding="utf-8")
    monkeypatch.setattr(runner, "_after_analysis_commit", lambda: None)
    runner.analyze_run(root)
    assert analysis_binding.read_bytes() == analysis_bytes

    evaluation_path = root / "evaluation.json"
    evaluation = runner._read_json(evaluation_path)
    original = dict(evaluation)
    evaluation["source_commit"] = "tampered"
    runner._write_json(evaluation_path, evaluation)
    with pytest.raises(ValueError, match="identity|binding|source"):
        runner.validate_run_artifacts(root, require_formal=False)
    runner._write_json(evaluation_path, original)

    chunk_path = next(
        path
        for path in (root / "evaluation_chunks").rglob("*.attempt_*.json")
        if not path.name.endswith(".complete.json")
    )
    chunk = runner._read_json(chunk_path)
    chunk["rows"][0]["action_path_sha256"] = "f" * 64
    runner._write_json(chunk_path, chunk)
    with pytest.raises(ValueError, match="binding|SHA-256"):
        runner.validate_run_artifacts(root, require_formal=False)
