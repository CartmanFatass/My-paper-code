from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import shutil

import numpy as np
import pytest
import torch

from scripts import run_uav_temp_loss_g1 as runner


def _predicates(**changes: object) -> dict[str, object]:
    values: dict[str, object] = {
        "operational_valid": True,
        "source_identifiable": True,
        "access_lcb": 1.0,
        "access_ucb": 1.1,
        "fixed_access_lcb": 1.0,
        "open_access_lcb": 1.0,
        "g_svc_lcb": 0.0,
        "g_svc_ucb": runner.SERVICE_GAIN_MARGIN,
        "g_rejoin_lcb": 0.0,
        "g_rejoin_ucb": runner.REJOIN_GAIN_MARGIN,
        "g_ordinary_lcb": 0.0,
        "g_ordinary_ucb": 0.0,
    }
    values.update(changes)
    return values


def _pruning_test_config() -> runner.RunConfig:
    return runner.RunConfig(
        replicates=1,
        updates=1,
        num_envs=1,
        horizon=500,
        ppo_passes=1,
        evaluation_episodes=1,
        evaluation_batch_size=1,
        bootstrap_resamples=8,
    )


def _install_synthetic_source_controls(
    monkeypatch: pytest.MonkeyPatch, *, constructive_disturbed: float
) -> dict[str, int]:
    counters = {"chunks_written": 0}

    def ensure(
        root: Path,
        *,
        run_identity: dict[str, object],
        config: runner.RunConfig,
        identity: dict[str, object],
        replicate: int,
    ) -> tuple[list[dict[str, object]], int, int, int]:
        rows: list[dict[str, object]] = []
        reused = written = ignored_total = 0
        keys = [
            key
            for key in runner._expected_evaluation_chunk_keys(
                config, exercise=False, control_only=True
            )
            if key["replicate"] == replicate
        ]
        seeds = runner._replicate_seeds(replicate)
        for key in keys:
            existing, ignored = runner._latest_evaluation_chunk(
                root, key=key, identity=identity, registered={}
            )
            ignored_total += ignored
            if existing is not None:
                rows.extend(existing)
                reused += 1
                continue
            cell = runner.LossCell(key["cell"])
            control = str(key["subject"])
            start = int(key["start_episode"])
            chunk_rows: list[dict[str, object]] = []
            for episode_id in range(start, start + int(key["episode_count"])):
                ledger = runner.make_uav_loss_ledger(
                    cell, episode_id, ledger_seed=seeds["evaluation_ledger"]
                )
                no_disturbance = cell is runner.LossCell.NO_DISTURBANCE
                event = (
                    1.0
                    if no_disturbance
                    else (
                        constructive_disturbed
                        if control == "constructive"
                        else 0.5
                    )
                )
                metrics = {
                    "J_event": event,
                    "J_rejoin": None if no_disturbance else event,
                    "Q_ordinary": 0.95,
                }
                for mode in runner.ACTION_MODES:
                    chunk_rows.append(
                        runner._evaluation_row(
                            manifest=run_identity,
                            subject=control,
                            replicate=replicate,
                            cell=cell,
                            mode=mode,
                            episode_id=episode_id,
                            ledger=ledger,
                            metrics=metrics,
                            checkpoint_reference=None,
                        )
                    )
            committed = runner._commit_evaluation_chunk(
                root,
                key=key,
                identity=identity,
                registered={},
                rows=chunk_rows,
            )
            runner._after_evaluation_chunk_commit(key=key)
            rows.extend(committed)
            written += 1
            counters["chunks_written"] += 1
        return rows, reused, written, ignored_total

    monkeypatch.setattr(runner, "_ensure_control_chunks_for_replicate", ensure)
    return counters


def test_formal_token_counts_strata_and_seed_offsets_are_frozen() -> None:
    assert (
        runner.FORMAL_AUTHORIZATION_TOKEN
        == "AUTHORIZE_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_CPU_V1"
    )
    assert asdict(runner.FORMAL_CONFIG) == {
        "replicates": 3,
        "updates": 200,
        "num_envs": 16,
        "horizon": 500,
        "ppo_passes": 4,
        "evaluation_episodes": 128,
        "evaluation_batch_size": 16,
        "bootstrap_resamples": 10_000,
        "checkpoint_selection": "final_only",
    }
    assert len(runner.STRATA) == 8
    assert runner.ACCESS_CELL_COUNT == 4
    assert set(runner.STRATA) == {
        (cell.value, mode)
        for cell in runner.EVALUATION_CELLS
        for mode in runner.ACTION_MODES
    }
    assert runner._replicate_seeds(1) == {
        name: value + 1000 for name, value in asdict(runner.SeedRegistry()).items()
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
            _predicates(source_identifiable=False, access_ucb=0.5),
            runner.SOURCE_NON_IDENTIFIABLE_RESULT,
        ),
        (
            _predicates(access_lcb=0.5, access_ucb=float(np.nextafter(1.0, 0.0))),
            runner.NO_ACCESS_RESULT,
        ),
        (
            _predicates(access_lcb=float(np.nextafter(1.0, 0.0)), access_ucb=1.0),
            runner.UNDERPOWERED_RESULT,
        ),
        (_predicates(), runner.MASK_SUFFICIENT_RESULT),
        (
            _predicates(
                fixed_access_lcb=0.99,
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
                fixed_access_lcb=0.99,
                g_svc_lcb=runner.SERVICE_GAIN_MARGIN,
                g_svc_ucb=0.10,
                g_rejoin_lcb=0.10,
                g_rejoin_ucb=0.10,
            ),
            runner.MIXED_RESULT,
        ),
    ],
)
def test_exact_first_match_boundaries_and_precedence(
    inputs: dict[str, object], expected: str
) -> None:
    assert runner.select_result_branch(inputs) == expected


def test_hierarchical_bootstrap_resamples_whole_episode_ids_across_strata() -> None:
    shape = (1, len(runner.STRATA), 4)
    values: dict[str, dict[str, np.ndarray]] = {}
    complementary = np.array([0.4, 0.0, 0.4, 0.0])
    gains = np.stack(
        [complementary if index % 2 == 0 else complementary[::-1] for index in range(shape[1])]
    )[None]
    disturbed = np.array(
        [cell != runner.LossCell.NO_DISTURBANCE.value for cell, _ in runner.STRATA]
    )
    for subject in runner.SUBJECT_NAMES:
        base_j = np.full(shape, 0.4)
        base_q = np.full(shape, 0.95)
        rejoin = np.full(shape, 0.6)
        rejoin[:, ~disturbed] = np.nan
        if subject == runner.PREFIX_NORMALIZED_OPEN_ROSTER:
            base_j = base_j + gains
            rejoin[:, disturbed] = rejoin[:, disturbed] + gains[:, disturbed]
        if subject == "constructive":
            base_j.fill(1.0)
        if subject == "no_reallocation":
            base_j.fill(0.7)
        values[subject] = {
            "J_event": base_j,
            "J_rejoin": rejoin,
            "Q_ordinary": base_q,
        }
    intervals = runner.hierarchical_stratified_intervals(
        values, resamples=512, seed=1234
    )
    # Each episode's complementary cross-stratum gains average to exactly 0.2.
    # This interval widens if episode IDs are sampled independently by stratum.
    assert intervals["g_svc"]["lcb95"] == pytest.approx(0.2)
    assert intervals["g_svc"]["mean"] == pytest.approx(0.2)
    assert intervals["g_svc"]["ucb95"] == pytest.approx(0.2)


def test_source_screen_estimator_is_exact_analysis_projection() -> None:
    config = runner.RunConfig(
        replicates=2,
        updates=1,
        num_envs=1,
        horizon=500,
        ppo_passes=1,
        evaluation_episodes=3,
        evaluation_batch_size=1,
        bootstrap_resamples=257,
    )
    shape = (config.replicates, len(runner.STRATA), config.evaluation_episodes)
    rng = np.random.default_rng(91)
    values: dict[str, dict[str, np.ndarray]] = {}
    rows: list[dict[str, object]] = []
    for subject in runner.SUBJECT_NAMES:
        event = rng.uniform(0.2, 1.0, size=shape)
        ordinary = rng.uniform(0.8, 1.0, size=shape)
        rejoin = rng.uniform(0.2, 1.0, size=shape)
        values[subject] = {
            "J_event": event,
            "J_rejoin": rejoin,
            "Q_ordinary": ordinary,
        }
        if subject in runner.CONTROL_NAMES:
            for replicate in range(config.replicates):
                for stratum, (cell, mode) in enumerate(runner.STRATA):
                    for episode_id in range(config.evaluation_episodes):
                        rows.append(
                            {
                                "subject": subject,
                                "replicate": replicate,
                                "cell": cell,
                                "action_mode": mode,
                                "episode_id": episode_id,
                                "J_event": float(event[replicate, stratum, episode_id]),
                            }
                        )
    full = runner.hierarchical_stratified_intervals(
        values, resamples=config.bootstrap_resamples, seed=182_800
    )
    screen = runner.source_control_intervals(
        rows,
        config=config,
        resamples=config.bootstrap_resamples,
        seed=182_800,
    )
    assert screen == {
        name: full[name]
        for name in (
            "constructive_j_event",
            "constructive_minus_no_reallocation",
        )
    }


def test_source_screen_boundaries_keep_mean_equality_and_reject_lcb_equality() -> None:
    identification = runner._source_identification(
        {
            "constructive_j_event": {"mean": runner.CONSTRUCTIVE_FLOOR},
            "constructive_minus_no_reallocation": {
                "lcb95": runner.LOAD_BEARING_MARGIN
            },
        }
    )
    assert identification["constructive_feasibility_pass"] is True
    assert identification["disturbed_load_bearing_pass"] is False
    assert runner._source_identification(
        {
            "constructive_j_event": {
                "mean": float(np.nextafter(runner.CONSTRUCTIVE_FLOOR, 0.0))
            },
            "constructive_minus_no_reallocation": {
                "lcb95": float(np.nextafter(runner.LOAD_BEARING_MARGIN, 1.0))
            },
        }
    )["constructive_feasibility_pass"] is False


def test_access_averages_modes_within_exactly_four_cells_and_retains_imbalance() -> None:
    shape = (1, len(runner.STRATA), 4)
    disturbed = np.array(
        [cell != runner.LossCell.NO_DISTURBANCE.value for cell, _ in runner.STRATA]
    )
    values: dict[str, dict[str, np.ndarray]] = {}
    for subject in runner.SUBJECT_NAMES:
        j_event = np.full(shape, 0.8)
        q_ordinary = np.full(shape, 0.9)
        j_rejoin = np.full(shape, 0.8)
        j_rejoin[:, ~disturbed] = np.nan
        if subject in runner.ARM_NAMES:
            # IID_SINGLE deterministic passes event access, stochastic fails it.
            j_event[:, 2, :] = 0.8
            j_event[:, 3, :] = 0.0
        if subject == "constructive":
            j_event.fill(1.0)
        if subject == "no_reallocation":
            j_event.fill(0.7)
        values[subject] = {
            "J_event": j_event,
            "J_rejoin": j_rejoin,
            "Q_ordinary": q_ordinary,
        }
    intervals = runner.hierarchical_stratified_intervals(
        values, resamples=128, seed=55
    )
    fixed_cell_keys = [
        key for key in intervals if key.startswith("fixed_access_cell:")
    ]
    assert len(fixed_cell_keys) == 4
    assert intervals["fixed_access_cell:IID_SINGLE"]["mean"] == pytest.approx(0.5)
    assert intervals["fixed_access_stratum:IID_SINGLE:deterministic"][
        "mean"
    ] == pytest.approx(1.0)
    assert intervals["fixed_access_stratum:IID_SINGLE:stochastic"][
        "mean"
    ] == pytest.approx(0.0)
    assert intervals["fixed_access"]["mean"] == pytest.approx(0.5)


def test_failed_source_screen_skips_all_learning_and_closes_registered_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _pruning_test_config()
    monkeypatch.setattr(runner, "FORMAL_CONFIG", config)
    counters = _install_synthetic_source_controls(
        monkeypatch, constructive_disturbed=0.8
    )

    def learned_model_forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("learned model constructed after failed source screen")

    monkeypatch.setattr(
        runner, "MatchedContinuousRecurrentPolicy", learned_model_forbidden
    )
    root = tmp_path / "source_screen_fail"
    manifest_path = runner.train_run(
        root,
        source_commit="0" * 40,
        formal=True,
        authorization_token=runner.FORMAL_AUTHORIZATION_TOKEN,
    )
    manifest = runner._read_json(manifest_path)
    assert manifest["status"] == runner.TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE
    assert manifest["training_results"] == []
    assert manifest["checkpoint_references"] == []
    assert not (root / "checkpoints").exists()
    assert not (root / "resume").exists()
    writes_before_evaluation = counters["chunks_written"]

    runner.evaluate_run(root)
    torch.set_num_threads(2)
    analysis = runner._read_json(runner.analyze_run(root))
    assert torch.get_num_threads() == 1
    assert counters["chunks_written"] == writes_before_evaluation
    assert analysis["result"] == runner.SOURCE_NON_IDENTIFIABLE_RESULT
    assert analysis["source_identifiable"] is False
    assert analysis["learned_gates_evaluated"] is False
    assert analysis["predicate_inputs"]["operational_valid"] is True
    rows = runner._read_jsonl(root / "evaluation_rows.jsonl")
    assert {row["subject"] for row in rows} == set(runner.CONTROL_NAMES)
    assert len(rows) == (
        config.replicates
        * len(runner.CONTROL_NAMES)
        * len(runner.EVALUATION_CELLS)
        * len(runner.ACTION_MODES)
        * config.evaluation_episodes
    )
    torch.set_num_threads(2)
    runner.validate_formal_result(root)
    assert torch.get_num_threads() == 1

    tampered = tmp_path / "source_screen_tamper"
    shutil.copytree(root, tampered)
    chunk_path = next(
        (tampered / "evaluation_chunks" / "control").rglob("attempt_0000.json")
    )
    chunk = runner._read_json(chunk_path)
    chunk["rows"][0]["J_event"] = 0.75
    runner._write_json(chunk_path, chunk)
    with pytest.raises(ValueError, match="completion marker is malformed"):
        runner.validate_formal_result(tampered)


def test_passing_source_screen_enters_learning_and_reuses_control_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _pruning_test_config()
    monkeypatch.setattr(runner, "FORMAL_CONFIG", config)
    counters = _install_synthetic_source_controls(
        monkeypatch, constructive_disturbed=1.0
    )

    def learned_training_reached(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("learned training reached")

    monkeypatch.setattr(runner, "collect_uav_trajectory", learned_training_reached)
    root = tmp_path / "source_screen_pass"
    with pytest.raises(RuntimeError, match="learned training reached"):
        runner.train_run(
            root,
            source_commit="1" * 40,
            formal=True,
            authorization_token=runner.FORMAL_AUTHORIZATION_TOKEN,
        )
    screen = runner._read_json(root / "source_screen.json")
    assert screen["source_identifiable"] is True
    writes_after_screen = counters["chunks_written"]
    launch = runner._read_json(root / "launch_identity.json")
    identity = runner._source_screen_identity(launch, config=config)
    rows, reused, written, _ignored = runner._ensure_control_chunks_for_replicate(
        root,
        run_identity=launch,
        config=config,
        identity=identity,
        replicate=0,
    )
    assert len(rows) == len(runner.CONTROL_NAMES) * len(runner.STRATA)
    assert reused == len(
        runner._expected_evaluation_chunk_keys(
            config, exercise=False, control_only=True
        )
    )
    assert written == 0
    assert counters["chunks_written"] == writes_after_screen

    (root / "source_screen.complete.json").write_text(
        '{"schema":', encoding="utf-8"
    )
    (root / "source_screen.json").write_text('{"partial":', encoding="utf-8")
    with pytest.raises(RuntimeError, match="learned training reached"):
        runner.train_run(
            root,
            source_commit="1" * 40,
            formal=True,
            authorization_token=runner.FORMAL_AUTHORIZATION_TOKEN,
        )
    rebuilt = runner._read_json(root / "source_screen.json")
    assert rebuilt["source_identifiable"] is True
    assert counters["chunks_written"] == writes_after_screen


@pytest.fixture(scope="module")
def exercise_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("uav_g1") / "exercise"
    analysis_path = runner.exercise(root)
    analysis = runner._read_json(analysis_path)
    assert analysis["formal"] is False
    assert analysis["exercise"] is True
    assert analysis["operational_valid"] is True
    assert analysis["result"] == runner.NONFORMAL_RESULT
    assert analysis["metrics"]["observed_steps"] == runner.EXERCISE_CONFIG.horizon
    runner.validate_run_artifacts(root, require_formal=False)
    return root


def test_bounded_nonformal_pipeline_is_rejected_as_formal(
    exercise_root: Path,
) -> None:
    with pytest.raises(ValueError, match="rejects nonformal"):
        runner.validate_formal_result(exercise_root)


def test_artifact_source_tamper_is_rejected(
    exercise_root: Path, tmp_path: Path
) -> None:
    tampered = tmp_path / "source_tamper"
    shutil.copytree(exercise_root, tampered)
    evaluation = runner._read_json(tampered / "evaluation_manifest.json")
    evaluation["source_commit"] = "tampered"
    runner._write_json(tampered / "evaluation_manifest.json", evaluation)
    with pytest.raises(ValueError, match="exercise evaluation manifest"):
        runner.validate_run_artifacts(tampered, require_formal=False)


def test_training_manifest_audit_field_mutation_breaks_terminal_binding(
    exercise_root: Path, tmp_path: Path
) -> None:
    tampered = tmp_path / "training_audit_tamper"
    shutil.copytree(exercise_root, tampered)
    manifest_path = tampered / "train_manifest.json"
    manifest = runner._read_json(manifest_path)
    manifest["training_results"][0]["finite_updates"] = False
    runner._write_json(manifest_path, manifest)
    with pytest.raises(ValueError, match="training completion marker conflicts"):
        runner.validate_run_artifacts(tampered, require_formal=False)


def test_exact_subject_inventory_and_metric_support_reject_tamper(
    exercise_root: Path, tmp_path: Path
) -> None:
    tampered = tmp_path / "subject_tamper"
    shutil.copytree(exercise_root, tampered)
    path = tampered / "evaluation_rows.jsonl"
    rows = runner._read_jsonl(path)
    rows[-1]["subject"] = rows[0]["subject"]
    rows[-1]["checkpoint_reference"] = rows[0]["checkpoint_reference"]
    runner._write_jsonl(path, rows)
    with pytest.raises(ValueError, match="terminal rows differ from committed chunk assembly"):
        runner.validate_run_artifacts(tampered, require_formal=False)


def test_checkpoint_inventory_and_references_fail_closed(
    exercise_root: Path, tmp_path: Path
) -> None:
    duplicate = tmp_path / "duplicate_pair"
    shutil.copytree(exercise_root, duplicate)
    manifest = runner._read_json(duplicate / "train_manifest.json")
    manifest["training_results"][1] = dict(manifest["training_results"][0])
    runner._write_training_terminal(duplicate, manifest)
    with pytest.raises(ValueError, match="duplicate or misdirected"):
        runner.validate_run_artifacts(duplicate, require_formal=False)

    misdirected = tmp_path / "misdirected_evaluation"
    shutil.copytree(exercise_root, misdirected)
    rows = runner._read_jsonl(misdirected / "evaluation_rows.jsonl")
    learned = [row for row in rows if row["subject"] in runner.ARM_NAMES]
    learned[0]["checkpoint_reference"] = learned[1]["checkpoint_reference"]
    runner._write_jsonl(misdirected / "evaluation_rows.jsonl", rows)
    with pytest.raises(ValueError, match="terminal rows differ from committed chunk assembly"):
        runner.validate_run_artifacts(misdirected, require_formal=False)

    escaping = tmp_path / "escaping_reference"
    shutil.copytree(exercise_root, escaping)
    manifest = runner._read_json(escaping / "train_manifest.json")
    manifest["training_results"][0]["checkpoint"] = "../outside.pt"
    runner._write_training_terminal(escaping, manifest)
    with pytest.raises(ValueError, match="canonical registered path"):
        runner.validate_run_artifacts(escaping, require_formal=False)

    missing = tmp_path / "missing_checkpoint"
    shutil.copytree(exercise_root, missing)
    manifest = runner._read_json(missing / "train_manifest.json")
    (missing / manifest["checkpoint_references"][0]).unlink()
    with pytest.raises(ValueError, match="file is missing"):
        runner.validate_run_artifacts(missing, require_formal=False)

    tensor_tamper = tmp_path / "tensor_tamper"
    shutil.copytree(exercise_root, tensor_tamper)
    manifest = runner._read_json(tensor_tamper / "train_manifest.json")
    checkpoint = tensor_tamper / manifest["checkpoint_references"][0]
    bundle = torch.load(checkpoint, map_location="cpu", weights_only=False)
    first = next(iter(bundle["model_state"]))
    bundle["model_state"][first] = bundle["model_state"][first].clone()
    bundle["model_state"][first].view(-1)[0] += 1.0
    torch.save(bundle, checkpoint)
    with pytest.raises(ValueError, match="SHA-256 content binding"):
        runner.validate_run_artifacts(tensor_tamper, require_formal=False)


def _resume_test_config() -> runner.RunConfig:
    return runner.RunConfig(
        replicates=1,
        updates=2,
        num_envs=1,
        horizon=8,
        ppo_passes=1,
        evaluation_episodes=1,
        evaluation_batch_size=1,
        bootstrap_resamples=8,
    )


def _scientific_training_manifest(path: Path) -> dict[str, object]:
    value = runner._read_json(path)
    value.pop("wall_seconds")
    value.pop("resume_telemetry")
    return value


def _scientific_evaluation_manifest(path: Path) -> dict[str, object]:
    value = runner._read_json(path)
    value.pop("wall_seconds")
    value.pop("resume_telemetry")
    return value


def test_same_command_resume_is_exact_and_ignores_incomplete_fragments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _resume_test_config()
    resumed_root = tmp_path / "resumed"
    uninterrupted_root = tmp_path / "uninterrupted"

    def interrupt_after_fixed_survives(
        *, replicate: int, arm: str, completed_updates: int
    ) -> None:
        if (
            replicate == 0
            and arm == runner.PREFIX_NORMALIZED_OPEN_ROSTER
            and completed_updates == 1
        ):
            raise RuntimeError("injected interruption")

    monkeypatch.setattr(runner, "_after_resume_commit", interrupt_after_fixed_survives)
    with pytest.raises(RuntimeError, match="injected interruption"):
        runner.train_run(
            resumed_root,
            source_commit="NONFORMAL_RESUME_TEST",
            formal=False,
            config=config,
        )
    fixed_final = resumed_root / runner._checkpoint_reference(0, runner.FIXED_MASK_REC)
    assert fixed_final.is_file()
    fixed_bytes = fixed_final.read_bytes()

    incomplete = runner._resume_references(
        resumed_root,
        0,
        runner.PREFIX_NORMALIZED_OPEN_ROSTER,
        2,
        0,
    )["checkpoint"]
    incomplete_path = resumed_root / incomplete
    incomplete_path.parent.mkdir(parents=True, exist_ok=True)
    incomplete_path.write_bytes(b"interrupted direct write")

    monkeypatch.setattr(runner, "_after_resume_commit", lambda **_kwargs: None)
    resumed_manifest = runner.train_run(
        resumed_root,
        source_commit="NONFORMAL_RESUME_TEST",
        formal=False,
        config=config,
    )
    uninterrupted_manifest = runner.train_run(
        uninterrupted_root,
        source_commit="NONFORMAL_RESUME_TEST",
        formal=False,
        config=config,
    )
    assert fixed_final.read_bytes() == fixed_bytes
    assert not incomplete_path.exists()
    assert _scientific_training_manifest(resumed_manifest) == _scientific_training_manifest(
        uninterrupted_manifest
    )
    for arm in runner.ARM_NAMES:
        resumed_bundle = torch.load(
            resumed_root / runner._checkpoint_reference(0, arm),
            map_location="cpu",
            weights_only=False,
        )
        uninterrupted_bundle = torch.load(
            uninterrupted_root / runner._checkpoint_reference(0, arm),
            map_location="cpu",
            weights_only=False,
        )
        assert runner._nested_tensor_equal(resumed_bundle, uninterrupted_bundle)
    before = resumed_manifest.read_bytes()
    assert runner.train_run(
        resumed_root,
        source_commit="NONFORMAL_RESUME_TEST",
        formal=False,
        config=config,
    ) == resumed_manifest
    assert resumed_manifest.read_bytes() == before


def test_resume_identity_and_newest_complete_pair_tamper_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exercise_root: Path
) -> None:
    config = _resume_test_config()
    root = tmp_path / "tampered_resume"

    def interrupt_first_update(
        *, replicate: int, arm: str, completed_updates: int
    ) -> None:
        if replicate == 0 and arm == runner.FIXED_MASK_REC and completed_updates == 1:
            raise RuntimeError("injected interruption")

    monkeypatch.setattr(runner, "_after_resume_commit", interrupt_first_update)
    with pytest.raises(RuntimeError, match="injected interruption"):
        runner.train_run(
            root,
            source_commit="NONFORMAL_RESUME_TAMPER",
            formal=False,
            config=config,
        )
    monkeypatch.setattr(runner, "_after_resume_commit", lambda **_kwargs: None)
    marker, _ignored = runner._latest_resume_commit(root, 0, runner.FIXED_MASK_REC)
    assert marker is not None
    resume_checkpoint = root / marker["references"]["checkpoint"]
    original_resume = resume_checkpoint.read_bytes()
    mixed_checkpoint = exercise_root / runner._checkpoint_reference(
        0, runner.PREFIX_NORMALIZED_OPEN_ROSTER
    )
    resume_checkpoint.write_bytes(mixed_checkpoint.read_bytes())
    with pytest.raises(ValueError, match="resume completion marker is malformed"):
        runner.train_run(
            root,
            source_commit="NONFORMAL_RESUME_TAMPER",
            formal=False,
            config=config,
        )
    resume_checkpoint.write_bytes(original_resume)
    metadata_path = root / marker["references"]["metadata"]
    metadata = runner._read_json(metadata_path)
    metadata["next_episode_id"] += 1
    runner._write_json(metadata_path, metadata)
    with pytest.raises(ValueError, match="resume completion marker is malformed"):
        runner.train_run(
            root,
            source_commit="NONFORMAL_RESUME_TAMPER",
            formal=False,
            config=config,
        )
    with pytest.raises(ValueError, match="launch identity mismatch"):
        runner.train_run(
            root,
            source_commit="DIFFERENT_SOURCE",
            formal=False,
            config=config,
        )


def test_evaluation_chunk_resume_is_exact_and_ignores_incomplete_fragment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = tmp_path / "evaluation_base"
    runner.train_run(
        base,
        source_commit="NONFORMAL_EVALUATION_RESUME",
        formal=False,
        config=runner.EXERCISE_CONFIG,
    )
    resumed = tmp_path / "evaluation_resumed"
    uninterrupted = tmp_path / "evaluation_uninterrupted"
    shutil.copytree(base, resumed)
    shutil.copytree(base, uninterrupted)

    def interrupt_first_chunk(*, key: dict[str, object]) -> None:
        if key["subject"] == runner.FIXED_MASK_REC:
            raise RuntimeError("injected evaluation interruption")

    monkeypatch.setattr(runner, "_after_evaluation_chunk_commit", interrupt_first_chunk)
    with pytest.raises(RuntimeError, match="injected evaluation interruption"):
        runner.evaluate_run(resumed)
    incomplete_key = runner._evaluation_chunk_key(
        kind="exercise",
        replicate=0,
        subject=runner.PREFIX_NORMALIZED_OPEN_ROSTER,
        cell=runner.LossCell.NO_DISTURBANCE,
        mode="deterministic",
        start=0,
        count=1,
    )
    incomplete_reference = runner._evaluation_chunk_references(
        resumed, incomplete_key, 0
    )["chunk"]
    incomplete_path = resumed / incomplete_reference
    incomplete_path.parent.mkdir(parents=True, exist_ok=True)
    incomplete_path.write_bytes(b"interrupted evaluation direct write")

    monkeypatch.setattr(runner, "_after_evaluation_chunk_commit", lambda **_kwargs: None)
    resumed_manifest = runner.evaluate_run(resumed)
    uninterrupted_manifest = runner.evaluate_run(uninterrupted)
    assert not incomplete_path.exists()
    assert (resumed / "evaluation_rows.jsonl").read_bytes() == (
        uninterrupted / "evaluation_rows.jsonl"
    ).read_bytes()
    assert _scientific_evaluation_manifest(
        resumed_manifest
    ) == _scientific_evaluation_manifest(uninterrupted_manifest)
    before_manifest = resumed_manifest.read_bytes()
    before_rows = (resumed / "evaluation_rows.jsonl").read_bytes()
    assert runner.evaluate_run(resumed) == resumed_manifest
    assert resumed_manifest.read_bytes() == before_manifest
    assert (resumed / "evaluation_rows.jsonl").read_bytes() == before_rows


def test_newest_complete_evaluation_chunk_tamper_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "evaluation_chunk_tamper"
    runner.train_run(
        root,
        source_commit="NONFORMAL_EVALUATION_TAMPER",
        formal=False,
        config=runner.EXERCISE_CONFIG,
    )

    def interrupt_first_chunk(*, key: dict[str, object]) -> None:
        raise RuntimeError("injected evaluation interruption")

    monkeypatch.setattr(runner, "_after_evaluation_chunk_commit", interrupt_first_chunk)
    with pytest.raises(RuntimeError, match="injected evaluation interruption"):
        runner.evaluate_run(root)
    monkeypatch.setattr(runner, "_after_evaluation_chunk_commit", lambda **_kwargs: None)
    key = runner._evaluation_chunk_key(
        kind="exercise",
        replicate=0,
        subject=runner.FIXED_MASK_REC,
        cell=runner.LossCell.NO_DISTURBANCE,
        mode="deterministic",
        start=0,
        count=1,
    )
    chunk_path = root / runner._evaluation_chunk_references(root, key, 0)["chunk"]
    chunk = runner._read_json(chunk_path)
    chunk["rows"][0]["mean_qos"] = 0.5
    runner._write_json(chunk_path, chunk)
    with pytest.raises(ValueError, match="completion marker is malformed"):
        runner.evaluate_run(root)


def test_formal_metric_validator_rejects_values_above_one() -> None:
    config = runner.RunConfig(
        replicates=1,
        updates=1,
        num_envs=1,
        horizon=500,
        ppo_passes=1,
        evaluation_episodes=1,
        evaluation_batch_size=1,
        bootstrap_resamples=1,
    )
    manifest = {
        "source_commit": "0" * 40,
        "formal": True,
    }
    ledger = runner.make_uav_loss_ledger(
        runner.LossCell.NO_DISTURBANCE,
        0,
        ledger_seed=runner._replicate_seeds(0)["evaluation_ledger"],
    )
    row = {
        "schema": runner.EVALUATION_ROW_SCHEMA,
        "source_family": runner.SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": True,
        "subject": runner.FIXED_MASK_REC,
        "checkpoint_reference": runner._checkpoint_reference(0, runner.FIXED_MASK_REC),
        "replicate": 0,
        "cell": runner.LossCell.NO_DISTURBANCE.value,
        "action_mode": "deterministic",
        "episode_id": 0,
        **runner._ledger_payload(ledger),
        "J_event": 1.0,
        "J_rejoin": None,
        "Q_ordinary": float(np.nextafter(1.0, 2.0)),
    }
    with pytest.raises(ValueError, match="outside support"):
        runner._validate_evaluation_row(
            row,
            manifest=manifest,
            config=config,
            registered={(0, runner.FIXED_MASK_REC): runner._checkpoint_reference(0, runner.FIXED_MASK_REC)},
        )
