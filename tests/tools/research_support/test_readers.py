"""Reader tests: supported schemas parse, unsupported ones are refused, gaps stay visible.

Every fixture is generated under ``tmp_path``.  No CSV fixture is committed (``*.csv`` is
gitignored and no ``paper_eval_episodes_step_*.csv`` exists anywhere in the checkout), and
the one test that reads a real ``logs/`` run directory skips with a stated reason when that
local evidence is absent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# ``tests/tools/`` shadows the checkout's ``tools`` namespace package: pytest prepends both
# ``tests/`` and ``tests/tools/`` to ``sys.path``, and the pre-existing
# ``tests/tools/research_support/__init__.py`` makes this directory a *regular* package that
# wins the name ``tools.research_support``.  Put the checkout root first, and drop anything
# already imported out of the tests tree, so ``tools.research_support.*`` means the
# implementation under test.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_TESTS_TOOLS = str(Path(__file__).resolve().parents[1])
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT))
for _name in [n for n in list(sys.modules) if n == "tools" or n.startswith("tools.")]:
    _origin = getattr(sys.modules[_name], "__file__", None)
    if _origin and _origin.startswith(_TESTS_TOOLS):
        del sys.modules[_name]

from tools.research_support.readers import (  # noqa: E402
    FIELD_ALGORITHM,
    FIELD_CHECKPOINT_SELECTION,
    FIELD_EVALUATION_WORLD,
    FIELD_EVENT_REALIZATION,
    FIELD_HORIZON,
    FIELD_METRIC_SEMANTICS,
    FIELD_SOURCE_SHA,
    FIELD_STATISTICAL_UNIT,
    FIELD_TERMINATION_DECLARED,
    FIELD_TERMINATION_OBSERVED,
    RUN_IDENTITY_FIELDS,
    EpisodeIdentityError,
    UnsupportedSourceError,
    detect_reader,
    read_run,
)
from tools.research_support.records import (  # noqa: E402
    AggregationLevel,
    Phase,
    Validity,
    XKind,
    file_hash,
    loads,
)

# --------------------------------------------------------------------------------------
# Fixture builders
# --------------------------------------------------------------------------------------

REAL_PROCESS_CORE_RUN = (
    _REPO_ROOT
    / "logs"
    / (
        "formal_continuous_roster_native_six_g31_channel_scale_normalization_"
        "attribution_g44_cpu_20260727_96e35dd_r1"
    )
)


def write_legacy_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(header)]
    lines.extend(",".join(row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_legacy_tree(root: Path) -> Path:
    """Two presets: one with two seeds and an invalid cell, one with a single episode."""

    header = ["preset", "episode", "reward", "coverage_ratio_final", "note"]
    write_legacy_csv(
        root / "alpha" / "seed_1" / "paper_eval_episodes_step_1000.csv",
        header,
        [
            ["alpha", "0", "0.10", "0.50", "ok"],
            ["alpha", "1", "not_a_number", "0.60", "bad"],
            ["alpha", "2", "0.30", "0.70", "ok"],
        ],
    )
    write_legacy_csv(
        root / "alpha" / "seed_2" / "paper_eval_episodes_step_1000.csv",
        header,
        [
            ["alpha", "0", "0.20", "0.55", "ok"],
            ["alpha", "1", "0.40", "0.65", "ok"],
            ["alpha", "2", "0.60", "0.75", "ok"],
        ],
    )
    write_legacy_csv(
        root / "beta" / "seed_9" / "paper_eval_episodes_step_1000.csv",
        header,
        [["beta", "0", "0.50", "0.80", "ok"]],
    )
    return root


def build_process_core(
    root: Path,
    *,
    source_commit: str = "a" * 40,
    algorithm: str = "TOY_ALGORITHM_G99",
    channel_composition: str = "literal_equal_mean_0.5",
    signatures: tuple[str, ...] = (
        "((6, 17), ('L', 'R'), 'small_4_2', (1, 3))",
        "((8, 21), ('R', 'L'), 'small_4_2', (1, 3))",
    ),
    boundary_declared: bool | None = None,
    boundary_runtime: dict[str, float] | None = None,
    schema_version: int = 2,
    with_evaluation: bool = True,
    with_analysis: bool = True,
    n_updates: int = 2,
    seed_bases: dict[str, int] | None = None,
) -> Path:
    """Minimal directory mirroring the real process-core manifest keys."""

    root.mkdir(parents=True, exist_ok=True)
    seed_bases = seed_bases or {
        "branch_action": 10442000,
        "branch_ledger": 10441000,
        "evaluation_action": 10446000,
        "evaluation_ledger": 10444000,
    }
    configuration = {
        "horizon": 48,
        "replicates": 1,
        "checkpoint_selection": "final_only",
        "environment_backend": "ContinuousRosterToyBatch_CPU_CPP_required",
        "training_transitions": 230400,
        "optimizer_steps": 1200,
        "total_real_transitions": 396288,
        "evaluation_episodes_per_cell": len(signatures),
        "evaluation_capacities": [6, 8],
        "training_capacity": 8,
        "channel_composition": channel_composition,
        "normalization_unit": "one_team_residual_row_per_primitive_step",
        "normalization_rows": 384,
        "stored_training_observation_dim": 6,
        "num_envs": 8,
        "learning_rate": 0.001,
    }
    if boundary_declared is not None:
        configuration["legacy_truncation_as_termination"] = boundary_declared

    update_records = []
    for index in range(n_updates):
        record = {
            "update_index": index,
            "algorithm_id": algorithm,
            "real_transitions": 768,
            "normalization_count": 1,
            "passed": True,
        }
        if boundary_runtime is not None:
            record.update(boundary_runtime)
        update_records.append(record)

    train = {
        "schema_version": schema_version,
        "stage": "train",
        "status": "COMPLETE",
        "formal": True,
        "algorithm": algorithm,
        "source_commit": source_commit,
        "aligned_source_commit": source_commit,
        "alignment_stage_commit": "b" * 40,
        "alignment_disposition": "ALIGNED",
        "authorization_token": f"{algorithm}_FORMAL_AUTHORIZATION_V1",
        "source_id": f"{algorithm}_P0",
        "configuration": configuration,
        "runtime": {
            "backend": "cpu",
            "python": "python.exe",
            "torch": "2.7.0+cpu",
            "torch_threads": 1,
        },
        "native_backend": {
            "build_identity": "80dca0e353c5677ebd73",
            "kind": "ContinuousRosterToyBatch_CPU_CPP",
            "module": "hmasd_continuous_roster_toy_80dca0e353c5677ebd73",
            "python_fallback": False,
            "required": True,
        },
        "source_controls": {
            "training_source": "G32 capacity-8 fixed paired source",
            "evaluation_source": "G34 fixed/random capacities 6|8",
            "seed_bases": seed_bases,
            "horizon": 48,
        },
        "accepted_anchor_artifact_digests": {"checkpoint_0": "d" * 64, "manifest": "e" * 64},
        "replicate_results": [
            {
                "replicate": 0,
                "seeds": dict(seed_bases),
                "accepted_anchor": {
                    "checkpoint_kind": "common_native6_fast_anchor",
                    "checkpoint_reference": "logs/anchor/checkpoints/replicate_0.pt",
                    "complete_state_digest": "f" * 64,
                },
                "accepted_anchor_state_digest": "f" * 64,
                "paired_collection_before_update": True,
                "update_records": update_records,
            }
        ],
        "stage_wall_time_seconds": 12.5,
    }
    (root / "train_manifest.json").write_text(json.dumps(train), encoding="utf-8")

    if with_evaluation:
        episodes = []
        for index, signature in enumerate(signatures):
            episodes.append(
                {
                    "count_trajectory": [4, 2],
                    "episode_id": 60000 + index,
                    "event_order": ["L", "R"],
                    "event_times": [6, 17],
                    "event_window_utility": {"L": 0.97, "R": 0.94},
                    "local_episode_id": index,
                    "minimum_event_window_utility": 0.94,
                    "minimum_process_segment_utility": 0.946,
                    "minimum_step_utility": 0.918,
                    "process_segment_utility": [0.96, 0.97],
                    "profile": "small_4_2",
                    "reward_trace": [0.96, 0.97, 0.95],
                    "roster_size_trace": [4, 4, 2],
                    "roster_sizes_valid": True,
                    "signature": signature,
                    "utility": 0.968 + 0.001 * index,
                }
            )
        evaluation = {
            "schema_version": schema_version,
            "stage": "evaluate",
            "status": "COMPLETE",
            "algorithm": algorithm,
            "source_commit": source_commit,
            "configuration": configuration,
            "source_controls": train["source_controls"],
            "training_manifest_digest": "1" * 64,
            "direct_source_validation": True,
            "cells": [
                {
                    "arm": f"{algorithm}_ARM_A",
                    "capacity": 6,
                    "cell": "FINAL_FIXED_DET",
                    "checkpoint": "final",
                    "deterministic": True,
                    "lifecycle_valid": True,
                    "optimizer_steps": 0,
                    "process": "fixed",
                    "replicate": 0,
                    "state_after": "3" * 64,
                    "state_before": "3" * 64,
                    "episodes": episodes,
                }
            ],
        }
        (root / "evaluation_manifest.json").write_text(json.dumps(evaluation), encoding="utf-8")

    if with_analysis:
        analysis = {
            "schema_version": schema_version,
            "stage": "analyze",
            "status": "COMPLETE",
            "algorithm": algorithm,
            "source_commit": source_commit,
            "branch": "TOY_BRANCH",
            "evaluation_manifest_digest": "2" * 64,
            "training_manifest_digest": "1" * 64,
            "operational_valid": True,
            "operational_errors": [],
            "metrics": {
                "arm_access": {"access_pass": True, "pooled_ci95": [0.90, 0.91, 0.92]},
                "material_independent_advantage": 0.5,
                "source_valid": True,
            },
            "thresholds": {"utility_floor": 0.9},
        }
        (root / "analysis_result.json").write_text(json.dumps(analysis), encoding="utf-8")
    return root


def build_service_restoration(
    root: Path,
    *,
    per_episode: bool = True,
    controllers: tuple[str, ...] = ("static_hover", "greedy_backhaul"),
    recovered: bool = False,
) -> Path:
    """Minimal ``evaluate_baselines`` report mirroring ``evaluate_rollout`` record keys."""

    root.mkdir(parents=True, exist_ok=True)
    seeds = [0, 1]

    def episode_record(index: int, seed: int) -> dict:
        return {
            "episode": {
                "episode_id": f"ep-{index}",
                "split": "test",
                "dataset_hash": "sha256:dataset-abc",
                "is_real_activity_data": False,
                "provenance": "fixture_based",
            },
            "exogenous_events": [
                {
                    "event_type": "site_radio_loss",
                    "site_index": 2,
                    "start_s": 120.0,
                    "end_s": None,
                    "repaired_within_episode": False,
                    "access_capacity_scale": 0.0,
                    "backhaul_capacity_scale": 1.0,
                    "event_source": "sampled",
                }
            ],
            "references": {
                "healthy_no_uav_delivered_mbit": 100.0,
                "failed_no_uav_delivered_mbit": 60.0,
                "controller_delivered_mbit": 80.0,
                "offered_mbit": 120.0,
                "healthy_satisfaction": 0.83,
                "failed_satisfaction": 0.5,
                "controller_satisfaction": 0.66 + 0.01 * index,
            },
            "affected_points": [1, 4, 7],
            "recovery": {
                "applicable": True,
                "recovery_fraction_rho": 0.8,
                "recovery_sustain_s": 30.0,
                "failure_start_s": 120.0,
                "first_repair_s": None,
                "recovery_time_s": 180.0 if recovered else None,
                "time_to_recovery_s": 60.0 if recovered else None,
                "censored": not recovered,
                "censoring_reason": None if recovered else "threshold_not_reached_within_episode",
                "n_affected_points": 3,
                "not_applicable_instants": 0,
                "controller_delivered_mbit_affected": 40.0,
                "failed_no_uav_delivered_mbit_affected": 20.0,
                "healthy_delivered_mbit_affected": 50.0,
                "improvement_over_no_uav_mbit": 20.0,
                "fraction_of_lost_service_restored": 0.66,
            },
            "episode_summary": {
                "total_time_s": 600.0,
                "offered_mbit_total": 120.0,
                "delivered_mbit_total": 80.0,
                "unmet_mbit_total": 40.0,
                "mean_offered_mbps": 0.2,
                "mean_delivered_mbps": 0.133,
                "peak_unmet_mbps": 0.5,
                "satisfaction_all": 0.66,
                "energy_joules": None,
                "energy_status": "unavailable: v0 implements no battery or hover-power model",
                "flight_distance_m_per_uav": [10.0, 20.0, 30.0],
                "flight_distance_m_total": 60.0,
                "motion_effort_integral_s": 5.0,
                "max_constraint_residual": 0.0,
                "scheduler_path_signature_changes": 3,
            },
            "calibration_summary": {
                "empirically_calibrated": ["network.radio_models[access]"],
                "engineering_assumptions": ["episode.duration_s", "uav.speed_mps"],
            },
            "controller": {
                "name": "controller",
                "information_condition": "delayed_partial",
                "reward_sum": -1.5,
                "reward_mean": -0.25,
                "optimizer_updates": 0,
            },
            "episode_seed": seed,
        }

    report = {
        "tool": "evaluate_baselines",
        "config": "configs/uav_service_restoration/v0.json",
        "environment_id": "uav_service_restoration_v0",
        "training_fits_performed": 0,
        "optimizer_updates": 0,
        "information_condition": "delayed_partial",
        "data_status": "NOT_REAL_DATA",
        "episode_seeds": seeds,
        "episode_seed_provenance": "seed:0+index",
        "controller_seed": 0,
        "recovery_definition": {
            "recovery_fraction_rho": 0.8,
            "recovery_sustain_s": 30.0,
            "affected_set_rule": "demand points harmed in the failed no-UAV reference",
        },
        "controllers": {
            name: {
                "n_episodes": len(seeds),
                "controller_satisfaction_mean": 0.665,
                "controller_satisfaction_min": 0.66,
                "controller_satisfaction_max": 0.67,
                "fraction_of_lost_service_restored_mean": 0.66,
                "n_recovered": len(seeds) if recovered else 0,
                "time_to_recovery_s_mean_over_recovered": 60.0 if recovered else None,
                "n_censored": 0 if recovered else len(seeds),
                "censoring_reasons": {}
                if recovered
                else {"threshold_not_reached_within_episode": len(seeds)},
                "n_not_applicable": 0,
                "aggregation_rule": (
                    "means are over episodes; a censored episode contributes no recovery time"
                ),
            }
            for name in controllers
        },
        "wall_clock_s": 3.5,
        "interpretation_note": (
            "These controllers characterise the environment and the evaluator. They are "
            "untuned rules, not a research baseline."
        ),
    }
    if per_episode:
        report["per_episode"] = {
            name: [episode_record(index, seed) for index, seed in enumerate(seeds)]
            for name in controllers
        }
    (root / "evaluate_baselines.json").write_text(json.dumps(report), encoding="utf-8")
    return root


# --------------------------------------------------------------------------------------
# Detection and refusal
# --------------------------------------------------------------------------------------


def test_unrecognised_directory_is_not_a_run(tmp_path: Path) -> None:
    root = tmp_path / "formal_looks_like_a_run_cpu_20260727_abc1234_r1"
    root.mkdir()
    (root / "notes.txt").write_text("not a run", encoding="utf-8")
    (root / "results.json").write_text(json.dumps({"score": 1.0}), encoding="utf-8")

    assert detect_reader(root) is None
    with pytest.raises(UnsupportedSourceError) as error:
        read_run(root)
    assert "recognised by any reader" in str(error.value)


def test_readers_are_static_only() -> None:
    """No reader may import torch, unpickle, or execute discovered content."""

    banned = ("import torch", "torch.load", "import pickle", "pickle.load", "allow_pickle=True")
    package = _REPO_ROOT / "tools" / "research_support" / "readers"
    for path in sorted(package.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for needle in banned:
            assert needle not in text, f"{path.name} contains {needle!r}"


# --------------------------------------------------------------------------------------
# Legacy paper CSV
# --------------------------------------------------------------------------------------


def test_legacy_csv_counts_invalid_cells_and_reports_n1_uncertainty_as_absent(
    tmp_path: Path,
) -> None:
    root = build_legacy_tree(tmp_path / "paper_root")
    reader = detect_reader(root)
    assert reader is not None and reader.name == "legacy_paper_csv"

    result = read_run(root)
    coverage = result.coverage
    assert coverage["rows_parsed"] == 7
    assert coverage["group_columns"] == ["preset"]
    assert coverage["episode_column"] == "episode"
    assert set(coverage["metric_columns"]) == {"reward", "coverage_ratio_final"}
    # A column with no numeric cell at all is metadata, not an all-invalid metric.
    assert coverage["non_numeric_columns"] == ["note"]
    assert coverage["invalid_value_counts"]["reward"] == 1

    # The invalid row is counted, not dropped: 7 rows x 2 metrics.
    reward_records = [r for r in result.metric_records if r.metric_name == "reward"]
    assert len(reward_records) == 7
    invalid = [r for r in reward_records if r.value.validity is Validity.INVALID]
    assert len(invalid) == 1
    assert invalid[0].value.value is None
    assert "not_numeric" in (invalid[0].value.reason or "")
    assert invalid[0].source_path.endswith("paper_eval_episodes_step_1000.csv")
    assert invalid[0].source_row_or_key == "row=1;column=reward"
    assert invalid[0].x_kind is XKind.CHECKPOINT_STEP and invalid[0].x_value == 1000
    assert invalid[0].aggregation_level is AggregationLevel.EPISODE
    assert invalid[0].phase is Phase.EVALUATION

    per_seed = coverage["legacy_reproduction"]["per_seed"]
    alpha_seed_1 = [
        row for row in per_seed if row["metric"] == "reward" and str(row["run_seed"]) == "1"
    ]
    assert len(alpha_seed_1) == 1
    row = alpha_seed_1[0]
    # Legacy arithmetic: the invalid cell is excluded from the mean...
    assert row["episode_count"] == 2
    assert row["mean"] == pytest.approx(0.2)
    # ...but the exclusion is now recorded.
    assert row["n_invalid_dropped"] == 1
    assert row["n_missing_dropped"] == 0
    assert row["std"]["validity"] == "ok"

    beta = [
        row
        for row in per_seed
        if row["metric"] == "reward" and str(row.get("preset")) == "beta"
    ]
    assert len(beta) == 1
    assert beta[0]["episode_count"] == 1
    # The legacy value is preserved for reproduction...
    assert beta[0]["legacy_std"] == 0.0
    assert beta[0]["legacy_ci95"] == 0.0
    # ...and the honest value is an explicit absence, never a zero error bar.
    assert beta[0]["std"]["value"] is None
    assert beta[0]["std"]["validity"] == Validity.NOT_APPLICABLE.value
    assert "n=1" in beta[0]["std"]["reason"]
    assert beta[0]["ci95"]["value"] is None
    assert beta[0]["ci95"]["validity"] == Validity.NOT_APPLICABLE.value

    overall = coverage["legacy_reproduction"]["overall"]
    alpha_overall = [
        row
        for row in overall
        if row["metric"] == "reward" and str(row.get("preset")) == "alpha"
    ][0]
    assert alpha_overall["n_seeds"] == 2
    assert alpha_overall["mean"] == pytest.approx(0.3)
    assert alpha_overall["legacy_std"] == pytest.approx(0.1414213562, rel=1e-6)
    assert alpha_overall["std"]["validity"] == "ok"
    assert alpha_overall["n_invalid_dropped"] == 1
    beta_overall = [
        row for row in overall if row["metric"] == "reward" and str(row.get("preset")) == "beta"
    ][0]
    assert beta_overall["n_seeds"] == 1
    assert beta_overall["legacy_ci95"] == 0.0
    assert beta_overall["ci95"]["validity"] == Validity.NOT_APPLICABLE.value


def test_legacy_csv_run_record_states_what_is_absent(tmp_path: Path) -> None:
    root = build_legacy_tree(tmp_path / "paper_root")
    result = read_run(root)
    assert len(result.run_records) == 1
    run = result.run_records[0]

    # Every identity field is answered, even when the answer is "not recorded".
    for name in RUN_IDENTITY_FIELDS:
        assert name in run.fields, name
        assert name in run.field_status, name

    assert run.get(FIELD_SOURCE_SHA).validity is Validity.NOT_RECORDED
    # Two presets under one root: the root does not identify one algorithm.
    assert run.get(FIELD_ALGORITHM).validity is Validity.UNKNOWN
    assert run.get(FIELD_EVALUATION_WORLD).validity is Validity.NOT_RECORDED
    assert "pairing_unverified" in (run.get(FIELD_EVALUATION_WORLD).reason or "")
    assert run.get(FIELD_TERMINATION_OBSERVED).validity is Validity.UNKNOWN
    assert run.get("training_exposure").value == 1000
    assert "filename_derived" in run.field_status["training_exposure"]
    assert "run_seed" in run.get(FIELD_STATISTICAL_UNIT).value

    # Every file read is hashed.
    assert len(run.source_paths) == 3
    assert all(digest.startswith("sha256:") for digest in run.source_hashes.values())
    assert sorted(run.source_hashes) == sorted(run.source_paths)


def test_legacy_csv_refuses_duplicate_episode_identity(tmp_path: Path) -> None:
    root = tmp_path / "paper_root"
    write_legacy_csv(
        root / "alpha" / "seed_1" / "paper_eval_episodes_step_1000.csv",
        ["preset", "episode", "reward"],
        [["alpha", "0", "0.10"], ["alpha", "0", "0.30"]],
    )
    with pytest.raises(EpisodeIdentityError) as error:
        read_run(root)
    assert "duplicate paper episode identities" in str(error.value)


def test_legacy_csv_refuses_rows_without_a_method_label(tmp_path: Path) -> None:
    root = tmp_path / "paper_root"
    write_legacy_csv(
        root / "seed_1" / "paper_eval_episodes_step_1000.csv",
        ["episode", "reward"],
        [["0", "0.10"]],
    )
    with pytest.raises(EpisodeIdentityError) as error:
        read_run(root)
    assert "preset or scenario_label" in str(error.value)


# --------------------------------------------------------------------------------------
# Process core
# --------------------------------------------------------------------------------------


def test_process_core_fixture_reads_manifest_identity(tmp_path: Path) -> None:
    root = build_process_core(tmp_path / "run")
    reader = detect_reader(root)
    assert reader is not None and reader.name == "process_core"

    result = read_run(root)
    run = result.run_records[0]
    assert run.get(FIELD_SOURCE_SHA).value == "a" * 40
    assert run.get(FIELD_ALGORITHM).value == "TOY_ALGORITHM_G99"
    assert run.get(FIELD_HORIZON).value == 48
    assert run.get(FIELD_HORIZON).unit == "decision_steps"
    assert run.get(FIELD_CHECKPOINT_SELECTION).value == "final_only"
    assert "channel_composition=literal_equal_mean_0.5" in run.get(FIELD_METRIC_SEMANTICS).value
    assert run.get("completion_status").value == "train=COMPLETE;evaluate=COMPLETE;analyze=COMPLETE"
    # A declared source label is not a content hash, so the dataset identity stays absent.
    assert run.get("dataset_identity").validity is Validity.NOT_RECORDED
    assert run.get("training_source").value == "G32 capacity-8 fixed paired source"
    # The evaluation manifest does evidence an event realisation.
    assert run.get(FIELD_EVENT_REALIZATION).validity is Validity.OK
    assert run.get("episode_interval").value.startswith("episode_id=[60000..60001]")
    assert run.get("evaluation_policy_mode").value.startswith("cells=['FINAL_FIXED_DET']")
    assert "optimizer_steps=['0']" in run.get("evaluation_policy_mode").value
    assert run.get("checkpoint_identity").validity is Validity.OK

    files = {Path(entry["path"]).name: entry for entry in result.coverage["files"]}
    assert files["train_manifest.json"]["status"] == "parsed"
    assert files["evaluation_manifest.json"]["status"] == "parsed"
    assert files["analysis_result.json"]["status"] == "parsed"
    assert all(entry["sha256"].startswith("sha256:") for entry in files.values())

    episode_metrics = [
        record
        for record in result.metric_records
        if record.aggregation_level is AggregationLevel.EPISODE
    ]
    utilities = [record for record in episode_metrics if record.metric_name == "utility"]
    assert len(utilities) == 2
    assert utilities[0].world_id == "((6, 17), ('L', 'R'), 'small_4_2', (1, 3))"
    assert utilities[0].source_row_or_key.startswith("cells[0](cell=FINAL_FIXED_DET,capacity=6)")
    assert utilities[0].x_kind is XKind.EPISODE_INDEX

    update_metrics = [
        record for record in result.metric_records if record.x_kind is XKind.UPDATE_INDEX
    ]
    assert {record.x_value for record in update_metrics} == {0, 1}
    assert all(
        record.training_replicate_id == "replicate_0" for record in update_metrics
    )
    assert any(record.metric_name == "real_transitions" for record in update_metrics)

    method_metrics = [
        record
        for record in result.metric_records
        if record.aggregation_level is AggregationLevel.METHOD
    ]
    assert any(record.metric_name == "material_independent_advantage" for record in method_metrics)
    # Confidence triples are not flattened into three unlabelled scalars.
    assert "arm_access.pooled_ci95[3]" in result.coverage["analysis_non_scalar_leaves"]
    # Per-step traces are reported, not silently averaged.
    assert any(
        key.startswith("reward_trace")
        for key in result.coverage["evaluation_episode_non_scalar_keys"]
    )


def test_process_core_declared_boundary_without_runtime_flags_is_unverified(
    tmp_path: Path,
) -> None:
    root = build_process_core(tmp_path / "run", boundary_declared=True, boundary_runtime=None)
    result = read_run(root)
    semantics = result.coverage["boundary_semantics"]

    assert semantics["declared"]["value"] is True
    assert semantics["declared"]["semantics"] == "collapsed_truncation_as_termination"
    assert semantics["declared"]["evidence"].endswith(
        "configuration.legacy_truncation_as_termination"
    )
    assert semantics["observed"]["semantics"] is None
    assert semantics["observed"]["unverified"] is True
    assert semantics["unverified"] is True
    assert semantics["agreement"] == "unverified"
    assert semantics["observed"]["truncation_rows_status"] == Validity.NOT_RECORDED.value

    run = result.run_records[0]
    assert run.get(FIELD_TERMINATION_DECLARED).value == "collapsed_truncation_as_termination"
    assert run.get(FIELD_TERMINATION_OBSERVED).validity is Validity.UNKNOWN
    assert "unverified" in run.field_status["termination_semantics_observed"]
    assert any("UNVERIFIED" in warning for warning in result.warnings)


def test_process_core_runtime_flags_make_boundary_semantics_observed(tmp_path: Path) -> None:
    root = build_process_core(
        tmp_path / "run",
        boundary_declared=False,
        boundary_runtime={
            "low_boundary_flags_resolved": 1.0,
            "low_boundary_legacy_collapse": 0.0,
            "low_truncation_rows": 3.0,
        },
    )
    result = read_run(root)
    semantics = result.coverage["boundary_semantics"]
    assert semantics["declared"]["semantics"] == "separate_termination_and_truncation"
    assert semantics["observed"]["semantics"] == "separate_termination_and_truncation"
    assert semantics["unverified"] is False
    assert semantics["agreement"] == "declared_matches_observed"
    # Summed across the two update records of the fixture.
    assert semantics["observed"]["truncation_rows"] == 6.0
    assert semantics["scan"]["updates_with_flags"] == 2


def test_process_core_declared_correct_but_observed_collapsed_is_reported(
    tmp_path: Path,
) -> None:
    root = build_process_core(
        tmp_path / "run",
        boundary_declared=False,
        boundary_runtime={
            "low_boundary_flags_resolved": 0.0,
            "low_boundary_legacy_collapse": 0.0,
            "low_truncation_rows": 0.0,
        },
    )
    result = read_run(root)
    semantics = result.coverage["boundary_semantics"]
    assert semantics["observed"]["semantics"] == "collapsed_fallback_flags_unresolved"
    assert semantics["agreement"] == "declared_contradicts_observed"
    assert any("fell back to the collapsed reading" in note for note in semantics["notes"])


def test_process_core_without_evaluation_manifest_keeps_world_identity_absent(
    tmp_path: Path,
) -> None:
    root = build_process_core(tmp_path / "run", with_evaluation=False, with_analysis=False)
    result = read_run(root)
    run = result.run_records[0]
    assert run.get(FIELD_EVENT_REALIZATION).validity is Validity.NOT_RECORDED
    assert run.get("initial_world_config").validity is Validity.NOT_RECORDED
    skipped = {
        Path(entry["path"]).name
        for entry in result.coverage["files"]
        if entry["status"] == "skipped"
    }
    assert skipped == {"evaluation_manifest.json", "analysis_result.json"}


@pytest.mark.skipif(
    not (REAL_PROCESS_CORE_RUN / "train_manifest.json").is_file(),
    reason=(
        "local-only evidence: logs/ is gitignored, so the real process-core run directory "
        f"{REAL_PROCESS_CORE_RUN.name} is absent in this checkout"
    ),
)
def test_process_core_reads_the_real_run_directory() -> None:
    result = read_run(REAL_PROCESS_CORE_RUN)
    run = result.run_records[0]
    assert run.get(FIELD_SOURCE_SHA).value == "96e35ddf55de71e56c6bcace4746c408909480dd"
    assert run.get(FIELD_ALGORITHM).value == (
        "CONTINUOUS_ROSTER_NATIVE_SIX_G31_CHANNEL_SCALE_NORMALIZATION_ATTRIBUTION_G44"
    )
    assert run.get(FIELD_HORIZON).value == 48
    assert run.get(FIELD_CHECKPOINT_SELECTION).value == "final_only"
    assert run.get("completion_status").value == "train=COMPLETE;evaluate=COMPLETE;analyze=COMPLETE"
    assert run.get("schema_version").value == 2
    # The real manifests record no boundary flag at all: execution is unverified.
    semantics = result.coverage["boundary_semantics"]
    assert semantics["declared"]["status"] == Validity.NOT_RECORDED.value
    assert semantics["unverified"] is True
    assert semantics["scan"]["update_count"] == 300
    assert semantics["scan"]["updates_with_flags"] == 0
    cells = result.coverage["evaluation_cells"]
    assert cells["n_cells"] == 72
    assert cells["cell_names"] == [
        "FINAL_FIXED_DET",
        "FINAL_FIXED_STOCH",
        "FINAL_RANDOM_DET",
        "FINAL_RANDOM_STOCH",
    ]
    assert cells["n_episodes"] == 72 * 48
    assert result.metric_records


# --------------------------------------------------------------------------------------
# Service restoration
# --------------------------------------------------------------------------------------


def test_service_restoration_records_are_labelled_diagnostic_rollouts(tmp_path: Path) -> None:
    root = build_service_restoration(tmp_path / "diag")
    reader = detect_reader(root)
    assert reader is not None and reader.name == "service_restoration_eval"

    result = read_run(root)
    assert len(result.run_records) == 2
    assert result.coverage["controllers"] == ["greedy_backhaul", "static_hover"]

    # Not one RL fit anywhere: every record is a diagnostic rollout of a fixed rule.
    assert all(record.phase is Phase.DIAGNOSTIC_ROLLOUT for record in result.metric_records)
    assert all(record.training_replicate_id is None for record in result.metric_records)
    assert all(
        record.method_id.startswith("rule_controller:") for record in result.metric_records
    )

    run = {record.run_id: record for record in result.run_records}[
        "service_restoration_eval:diag:static_hover"
    ]
    assert "not_an_independent_training_replicate" in run.get(FIELD_STATISTICAL_UNIT).value
    assert run.get("evaluation_policy_mode").value.startswith("rule_controller_forward_only")
    assert "training_fits_performed=0" in run.get("evaluation_policy_mode").value
    assert run.get("training_exposure").validity is Validity.NOT_APPLICABLE
    assert run.get("checkpoint_identity").validity is Validity.NOT_APPLICABLE
    assert run.get("dataset_identity").value == "sha256:dataset-abc"
    assert run.get("dataset_split").value == "test"
    assert run.get("information_condition").value == "delayed_partial"
    assert run.get("agent_count").value == 3
    assert run.get("simulated_horizon").value == 600.0
    assert run.get("completion_status").value == "complete;n_episodes=2"
    # The configuration path is not a content hash, so pairing evidence stays incomplete.
    assert run.get("initial_world_config").validity is Validity.NOT_RECORDED

    aggregate = [
        record
        for record in result.metric_records
        if record.aggregation_level is AggregationLevel.METHOD
        and record.metric_name == "time_to_recovery_s_mean_over_recovered"
    ]
    assert len(aggregate) == 2
    # Nothing recovered: an absent recovery time is never a recovery of zero seconds.
    assert all(record.value.value is None for record in aggregate)
    assert all(record.value.validity is Validity.NOT_APPLICABLE for record in aggregate)

    satisfaction = [
        record
        for record in result.metric_records
        if record.metric_name == "references.controller_satisfaction"
    ]
    assert len(satisfaction) == 4
    assert satisfaction[0].unit is None
    assert satisfaction[0].source_row_or_key.startswith("per_episode.")
    mbit = [
        record
        for record in result.metric_records
        if record.metric_name == "references.controller_delivered_mbit"
    ]
    assert mbit and mbit[0].unit == "Mbit"


def test_service_restoration_aggregate_only_report_states_the_gap(tmp_path: Path) -> None:
    root = build_service_restoration(tmp_path / "diag", per_episode=False)
    result = read_run(root)
    run = result.run_records[0]
    assert run.get("dataset_identity").validity is Validity.NOT_RECORDED
    assert run.get("completion_status").validity is Validity.UNKNOWN
    assert any("aggregates only" in warning for warning in result.warnings)
    assert all(
        record.aggregation_level is AggregationLevel.METHOD for record in result.metric_records
    )


def test_service_restoration_requires_its_own_marker(tmp_path: Path) -> None:
    root = tmp_path / "diag"
    root.mkdir()
    (root / "evaluate_baselines.json").write_text(
        json.dumps({"tool": "something_else", "controllers": {}}), encoding="utf-8"
    )
    assert detect_reader(root) is None


# --------------------------------------------------------------------------------------
# Result serialisation
# --------------------------------------------------------------------------------------


def test_read_result_json_is_strict_json(tmp_path: Path) -> None:
    from tools.research_support.records import dumps

    root = build_legacy_tree(tmp_path / "paper_root")
    result = read_run(root)
    payload = loads(dumps(result.to_json()))
    assert payload["coverage"]["rows_parsed"] == 7
    assert payload["run_records"][0]["reader"] == "legacy_paper_csv"
    assert payload["metric_records"][0]["schema"] == "research_support.metric.1"


def test_every_metric_record_keeps_its_source_location(tmp_path: Path) -> None:
    """A number that cannot be traced back to a file and a row is not evidence."""

    roots = [
        build_legacy_tree(tmp_path / "paper_root"),
        build_process_core(tmp_path / "process_run"),
        build_service_restoration(tmp_path / "diag"),
    ]
    for root in roots:
        result = read_run(root)
        assert result.metric_records, root
        for record in result.metric_records:
            assert record.source_path, (root, record.metric_name)
            assert record.source_row_or_key, (root, record.metric_name)
            assert Path(record.source_path).is_file()
        for run in result.run_records:
            assert run.source_paths
            assert sorted(run.source_hashes) == sorted(run.source_paths)
            for path, digest in run.source_hashes.items():
                assert digest == file_hash(path)


def test_explicit_reader_override_wins(tmp_path: Path) -> None:
    root = build_process_core(tmp_path / "run")
    result = read_run(root, reader="process_core")
    assert result.coverage["reader_selection"] == "explicit_override"
    with pytest.raises(UnsupportedSourceError):
        read_run(root, reader="legacy_paper_csv")
