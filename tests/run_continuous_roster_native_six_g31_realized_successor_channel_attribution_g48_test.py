from __future__ import annotations

import copy
import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
import torch

from ha_ctse_process import (
    continuous_roster_native_six_g31_realized_successor_channel_attribution_g48
    as source,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_shadow_baseline_module_reduction_g47 as g47,
)
from scripts import (
    run_continuous_roster_native_six_g31_realized_successor_channel_attribution_g48
    as runner,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANCHOR_ROOT = PROJECT_ROOT / (
    "logs/formal_continuous_roster_native_six_credit_reduction_g40_cpu_"
    "20260727_97a8b23_r1"
)
TEST_SOURCE_COMMIT = "8" * 40


@pytest.fixture(scope="module")
def readiness_bundle(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[Path, dict[str, object], dict[str, object], dict[str, object]]]:
    root = tmp_path_factory.mktemp("g48_readiness") / "proof"
    training = runner.readiness_train(
        run_root=root,
        source_commit=TEST_SOURCE_COMMIT,
        accepted_anchor_root=ANCHOR_ROOT,
    )
    assert runner.validate_readiness_training_artifacts(root) == []
    assert not (root / "evaluation_manifest.json").exists()
    evaluation = runner.readiness_evaluate(run_root=root)
    analysis = runner.readiness_analyze(run_root=root)
    yield root, training, evaluation, analysis


def test_configuration_seeds_workers_and_formal_admission_are_fail_closed(
    tmp_path: Path,
) -> None:
    nonformal = runner._configuration(formal=False)
    formal = runner._configuration(formal=True)
    assert (
        nonformal["training_transitions"],
        nonformal["evaluation_transitions"],
        nonformal["total_real_transitions"],
        nonformal["optimizer_steps"],
    ) == (7680, 6912, 14592, 40)
    assert (
        formal["training_transitions"],
        formal["evaluation_transitions"],
        formal["total_real_transitions"],
        formal["optimizer_steps"],
    ) == (230400, 165888, 396288, 1200)
    assert formal["branch_update_order"] == list(source.ARMS)
    assert formal["environment_backend"] == "ContinuousRosterToyBatch_CPU_CPP_required"
    assert formal["environment_python_fallback"] is False
    assert formal["cpu_parallelism_fixed_at_launch"] is True
    assert formal["worker_thread_controls"] == {
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "torch_intraop_threads": 1,
    }
    assert runner.seed_block(2, formal=True) == {
        **{name: value + 2 for name, value in runner.SEED_BASES.items()},
    }
    assert runner.bootstrap_seed(formal=True) == runner.BOOTSTRAP_SEED
    assert runner.seed_block(0, formal=False) == {
        **{
            name: value + runner.NONFORMAL_SEED_OFFSET
            for name, value in runner.SEED_BASES.items()
        },
    }
    assert runner.bootstrap_seed(formal=False) == (
        runner.BOOTSTRAP_SEED + runner.NONFORMAL_SEED_OFFSET
    )
    for workers in (0, 7):
        with pytest.raises(ValueError, match="process_workers"):
            runner._configuration(
                formal=True, cpu_budget=2, process_workers=workers
            )

    assert runner.ALIGNED_IMPLEMENTATION_COMMIT is None
    assert runner.ALIGNMENT_STAGE_COMMIT is None
    with pytest.raises(ValueError, match="independently archived ALIGNED source"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit=TEST_SOURCE_COMMIT,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=ANCHOR_ROOT,
            preflight_root=tmp_path / "missing_preflight",
            alignment_disposition="ALIGNED",
            aligned_source_commit="9" * 40,
            alignment_stage_commit="a" * 40,
        )


def test_readiness_proves_two_process_artifact_reload_and_evaluate_entry(
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
) -> None:
    root, training, evaluation, analysis = readiness_bundle
    parallel = training["two_process_update_equivalence"]
    assert parallel["passed"] is True
    assert parallel["worker_count"] == 2
    assert parallel["distinct_processes"] is True
    assert parallel["single_thread_workers"] is True
    assert parallel["parameters_adam_evidence_bitwise_equivalent"] is True
    assert training["formal"] is False
    assert training["scientific_iteration_cost"] == 0
    assert training["conclusion_bearing"] is False
    assert source._update_evidence_valid(training["update_evidence"])
    assert evaluation["status"] == "COMPLETE"
    assert all(cell["optimizer_steps"] == 0 for cell in evaluation["cells"])
    assert analysis["branch"] == runner.READINESS_BRANCH
    assert analysis["science_disposition"] is None
    assert runner.validate_readiness_artifacts(root) == []
    reloaded = runner.reload_readiness_artifacts(root)
    assert reloaded["passed"] is True
    assert all(
        row["baseline_module_present"] is False
        for row in reloaded["arms"].values()
    )


def test_null_checkpoint_tamper_and_first_match_priority_fail_closed(
    readiness_bundle: tuple[
        Path, dict[str, object], dict[str, object], dict[str, object]
    ],
    tmp_path: Path,
) -> None:
    root, _, _, _ = readiness_bundle
    tampered = tmp_path / "tampered"
    shutil.copytree(root, tampered)
    manifest_path = tampered / "train_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = manifest["checkpoints"][source.NULL_ARM]
    checkpoint_path = tampered / row["reference"]
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    payload["target_route_certificate"]["realized_successor_actor_credit_reads"] = 1
    torch.save(payload, checkpoint_path)
    row["file_digest"] = runner._artifact_digest(checkpoint_path)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    errors = runner.readiness_training_errors(tampered, manifest)
    assert any("null route mismatch" in error for error in errors)

    base = {
        "operational_valid": True,
        "source_valid": True,
        "reference_access_confident_fail": False,
        "reference_access_pass": True,
        "null_access_pass": True,
        "null_access_confident_fail": False,
        "duplicated_immediate_noninferior": True,
        "material_realized_successor_advantage": False,
    }
    assert runner.select_g48_result_branch(base) == runner.NULL_SUFFICIENT_BRANCH
    invalid = copy.deepcopy(base)
    invalid["operational_valid"] = False
    invalid["null_access_confident_fail"] = True
    assert runner.select_g48_result_branch(invalid) == runner.INVALID_BRANCH
    source_failure = copy.deepcopy(base)
    source_failure["source_valid"] = False
    assert runner.select_g48_result_branch(source_failure) == runner.SOURCE_FAILURE_BRANCH
    advantage = copy.deepcopy(base)
    advantage["null_access_pass"] = False
    advantage["duplicated_immediate_noninferior"] = False
    advantage["null_access_confident_fail"] = True
    assert runner.select_g48_result_branch(advantage) == runner.REFERENCE_ADVANTAGE_BRANCH
    underpowered = copy.deepcopy(base)
    underpowered["null_access_pass"] = False
    underpowered["duplicated_immediate_noninferior"] = False
    assert runner.select_g48_result_branch(underpowered) == runner.UNDERPOWERED_BRANCH


def test_g48_isolated_backend_does_not_mutate_g47_source_identity() -> None:
    assert g47.ARMS == (
        "NATIVE6_G31_RAW_NORM_SHADOW_BASELINE",
        "NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE",
    )
    assert source.ARMS == (
        "NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR",
        "NATIVE6_G31_DUPLICATED_IMMEDIATE",
    )
    assert runner._backend.source is source
    assert g47.SOURCE_ID.endswith("_G47_P0")
