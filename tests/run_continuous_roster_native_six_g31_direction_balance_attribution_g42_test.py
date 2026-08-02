from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_direction_balance_attribution_g42 as g42,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from scripts import (
    run_continuous_roster_native_six_g31_direction_balance_attribution_g42 as runner,
)
from envs.continuous_roster import runtime_capacity as roster_env


ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)
SOURCE_6B_COMMIT = "6b8ea82d8fdbc76c14a414ff2b042a126f945dfb"
SOURCE_6B_ALIGNMENT_STAGE = "309858dca06af66f13857f94773bcef37527d821"
EXECUTION_SOURCE_53B_COMMIT = "53b0cd74487187a3b0618f4fbc04a19c744808e8"
SOURCE_6B_ALIGNMENT_AUDIT_ID = (
    "CONTINUOUS_ROSTER_NATIVE_SIX_G31_DIRECTION_BALANCE_ATTRIBUTION_G42_"
    "CODE_SCIENCE_ALIGNMENT_AUDIT_SOURCE_6B"
)
PRIOR_ALIGNED_COMMIT = "e21a1464e186260878649ad170bc3f32b8b9496d"
PRIOR_ALIGNMENT_STAGE = "9dc84d3372a8e41ead9a5a349689586dc8e772b5"


def _assert_nested_equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert torch.equal(left, right)
    elif isinstance(left, Mapping):
        assert isinstance(right, Mapping)
        assert tuple(left) == tuple(right)
        for name in left:
            _assert_nested_equal(left[name], right[name])
    elif isinstance(left, (tuple, list)):
        assert isinstance(right, type(left))
        assert len(left) == len(right)
        for left_row, right_row in zip(left, right):
            _assert_nested_equal(left_row, right_row)
    else:
        assert left == right


def _assert_roundtripped_training_artifact_valid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record: Mapping[str, object],
    models: Mapping[str, g41.G41NoSlowProjection],
) -> None:
    configuration = runner._configuration(formal=False)
    records: list[dict[str, object]] = []
    for update_index in range(int(configuration["branch_updates_per_arm"])):
        serialized = json.loads(g42.serialize_diagnostics(record))
        serialized["update_index"] = update_index
        assert g42._update_gradient_evidence_valid(serialized) is True
        records.append(serialized)
    conclusion_evidence = g42.build_conclusion_evidence(records, formal=False)
    assert g42.validate_conclusion_evidence(conclusion_evidence) is True

    accepted_anchor_root = ANCHOR_FIXTURE.parent.resolve()
    anchor_digests = {ANCHOR_FIXTURE.name: "proof-sized-fixture"}
    monkeypatch.setattr(runner, "_bind_anchor_root", lambda _: accepted_anchor_root)
    monkeypatch.setattr(
        runner, "_validate_anchor_manifest", lambda _: anchor_digests
    )
    seeds = runner.seed_block(0, formal=False)
    source_commit = "a" * 40
    arms: dict[str, dict[str, object]] = {}
    for arm in g42.ARMS:
        reference = runner._checkpoint_reference(0, arm)
        payload = runner._save_checkpoint(
            tmp_path / reference,
            source_commit=source_commit,
            aligned_source_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
            formal=False,
            replicate=0,
            arm=arm,
            configuration=configuration,
            seeds=seeds,
            model=models[arm],
            final_update_record=records[-1],
            conclusion_evidence=conclusion_evidence,
        )
        arms[arm] = {
            "final_checkpoint": reference,
            "final_checkpoint_file_digest": runner._artifact_digest(
                tmp_path / reference
            ),
            "final_state_digest": payload["model_state_digest"],
            "completed_branch_updates": int(
                configuration["branch_updates_per_arm"]
            ),
            "actor_head_optimizer_steps": int(
                configuration["branch_updates_per_arm"]
            )
            * int(configuration["ppo_passes"]),
            "actor_parameter_departure": True,
            "shared_baseline_parameter_departure": True,
        }
    expected_steps = int(configuration["branch_updates_per_arm"]) * int(
        configuration["ppo_passes"]
    )
    row = {
        "replicate": 0,
        "seeds": seeds,
        "accepted_anchor": g41.accepted_g40_anchor_identity(0),
        "accepted_anchor_state_digest": (
            g41.accepted_g40_anchor_authority(0).complete_state_digest
        ),
        "branch_boundary_audit": {"passed": True},
        "paired_collection_before_update": True,
        "branch_update_order": list(g42.ARMS),
        "lifecycle_contract_valid": {arm: True for arm in g42.ARMS},
        "actor_parameter_departure": {arm: True for arm in g42.ARMS},
        "shared_baseline_parameter_departure": {
            arm: True for arm in g42.ARMS
        },
        "actor_head_optimizer_steps": {
            arm: float(expected_steps) for arm in g42.ARMS
        },
        "update_records": records,
        "arms": arms,
    }
    manifest = {
        "schema_version": runner.SCHEMA_VERSION,
        "algorithm": runner.ALGORITHM_ID,
        "source_id": g42.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": False,
        "source_commit": source_commit,
        "authorization_token": None,
        "alignment_audit_id": None,
        "alignment_disposition": None,
        "aligned_source_commit": runner.ALIGNED_IMPLEMENTATION_COMMIT,
        "alignment_stage_commit": None,
        "preflight_root": None,
        "preflight_artifact_digests": None,
        "accepted_anchor_root": str(accepted_anchor_root),
        "accepted_anchor_root_mode": "read_only_input_no_writes",
        "accepted_anchor_artifact_digests": anchor_digests,
        "runtime": {},
        "native_backend": {
            "kind": "ContinuousRosterToyBatch_CPU_CPP",
            "required": True,
            "python_fallback": False,
        },
        "configuration": configuration,
        "source_controls": runner.source_controls(),
        "conclusion_evidence": conclusion_evidence,
        "replicate_results": [row],
    }
    runner._write_json(tmp_path / "train_manifest.json", manifest)
    roundtripped = runner._read_json(tmp_path / "train_manifest.json")
    assert runner._training_errors(tmp_path, roundtripped) == []
    expected_files = {
        Path(runner._checkpoint_reference(0, arm)).name for arm in g42.ARMS
    }
    assert (
        runner._expected_final_checkpoint_files(roundtripped["replicate_results"])
        == expected_files
    )

    invalid_update = json.loads(json.dumps(roundtripped))
    invalid_update["replicate_results"][0]["update_records"][0]["passed"] = False
    assert runner._training_errors(tmp_path, invalid_update) == [
        "G42 update evidence mismatch"
    ]

    extra_checkpoint = tmp_path / "checkpoints" / "replicate_0_intermediate.pt"
    extra_checkpoint.touch()
    assert runner._training_errors(tmp_path, roundtripped) == [
        "G42 checkpoint inventory is not final-only"
    ]


def test_configuration_seeds_cpp_and_balanced_evaluation_inventory() -> None:
    nonformal = runner._configuration(formal=False)
    formal = runner._configuration(formal=True)
    assert nonformal["replicates"] == 1
    assert nonformal["branch_updates_per_arm"] == 10
    assert nonformal["evaluation_episodes_per_cell"] == 6
    assert nonformal["bootstrap_resamples"] == 250
    assert nonformal["training_transitions"] == 7_680
    assert nonformal["evaluation_transitions"] == 6_912
    assert nonformal["total_real_transitions"] == 14_592
    assert nonformal["optimizer_steps"] == 40
    assert formal["replicates"] == 3
    assert formal["accepted_common_anchor_updates"] == 100
    assert formal["accepted_common_anchor_optimizer_steps"] == 200
    assert formal["branch_updates_per_arm"] == 100
    assert formal["num_envs"] == 8
    assert formal["ppo_passes"] == 2
    assert formal["evaluation_episodes_per_cell"] == 48
    assert formal["bootstrap_resamples"] == 10_000
    assert formal["total_cells"] == 72
    assert formal["training_transitions"] == 230_400
    assert formal["evaluation_transitions"] == 165_888
    assert formal["total_real_transitions"] == 396_288
    assert formal["optimizer_steps"] == 1_200
    assert formal["environment_backend"] == "ContinuousRosterToyBatch_CPU_CPP_required"
    assert formal["environment_python_fallback"] is False
    assert formal["intrinsic_K_search"] == 0
    assert formal["hypothetical_transitions"] == 0
    assert runner.seed_block(2, formal=True) == {
        "branch_ledger": 10_421_002,
        "branch_action": 10_422_002,
        "branch_gradient_probe": 10_423_002,
        "evaluation_base_ledger": 10_424_002,
        "evaluation_process": 10_425_002,
        "evaluation_action": 10_426_002,
    }
    assert runner.bootstrap_seed(formal=True) == 10_427_042
    assert runner.bootstrap_seed(formal=False) == 11_327_042
    for formal_scope, episode_count, expected in ((False, 6, 2), (True, 48, 16)):
        _, inventory = runner._source_inventory(
            replicate=0,
            capacity=8,
            episode_count=episode_count,
            formal=formal_scope,
        )
        assert set(inventory["order_counts"].values()) == {expected}
        assert set(inventory["profile_counts"].values()) == {expected}


def test_authority_and_anchor_binding_fail_before_compute(tmp_path: Path) -> None:
    accepted_root = runner.PROJECT_ROOT / runner.ACCEPTED_ANCHOR_ROOT_RELATIVE
    with pytest.raises(ValueError, match="authorization token mismatch"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit="a" * 40,
            formal=True,
            authorization_token="wrong",
            accepted_anchor_root=accepted_root,
        )
    assert not (tmp_path / "formal").exists()
    with pytest.raises(ValueError, match="bounded preflight root"):
        runner.train(
            run_root=tmp_path / "formal",
            source_commit=SOURCE_6B_COMMIT,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=accepted_root,
            alignment_disposition="ALIGNED",
            aligned_source_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
            alignment_stage_commit=runner.ALIGNMENT_STAGE_COMMIT,
        )
    with pytest.raises(ValueError, match="immutable registered root"):
        runner._bind_anchor_root(tmp_path / "substitute")
    with pytest.raises(ValueError, match="cannot carry formal authority"):
        runner.train(
            run_root=tmp_path / "nonformal",
            source_commit="a" * 40,
            formal=False,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=accepted_root,
        )


def test_formal_authority_separates_execution_source_from_audited_source(
    tmp_path: Path,
) -> None:
    assert runner.ALIGNED_IMPLEMENTATION_COMMIT == SOURCE_6B_COMMIT
    assert runner.ALIGNMENT_STAGE_COMMIT == SOURCE_6B_ALIGNMENT_STAGE
    assert runner.ALIGNMENT_AUDIT_ID == SOURCE_6B_ALIGNMENT_AUDIT_ID
    accepted_root = runner.PROJECT_ROOT / runner.ACCEPTED_ANCHOR_ROOT_RELATIVE
    with pytest.raises(ValueError, match="registered ALIGNED source"):
        runner._validate_formal_preflight(
            tmp_path / "missing-prior-pair-preflight",
            source_commit=EXECUTION_SOURCE_53B_COMMIT,
            alignment_disposition="ALIGNED",
            aligned_source_commit=PRIOR_ALIGNED_COMMIT,
            alignment_stage_commit=PRIOR_ALIGNMENT_STAGE,
            accepted_anchor_root=accepted_root.resolve(),
        )
    with pytest.raises(FileNotFoundError):
        runner._validate_formal_preflight(
            tmp_path / "missing-current-source-preflight",
            source_commit=EXECUTION_SOURCE_53B_COMMIT,
            alignment_disposition="ALIGNED",
            aligned_source_commit=SOURCE_6B_COMMIT,
            alignment_stage_commit=SOURCE_6B_ALIGNMENT_STAGE,
            accepted_anchor_root=accepted_root.resolve(),
        )
    execution_source_manifest = {
        "schema_version": runner.SCHEMA_VERSION,
        "algorithm": runner.ALGORITHM_ID,
        "source_id": g42.SOURCE_ID,
        "stage": "train",
        "status": "COMPLETE",
        "formal": True,
        "configuration": runner._configuration(formal=True),
        "source_controls": runner.source_controls(),
        "source_commit": EXECUTION_SOURCE_53B_COMMIT,
        "aligned_source_commit": SOURCE_6B_COMMIT,
        "authorization_token": runner.AUTHORIZATION_TOKEN,
        "alignment_audit_id": runner.ALIGNMENT_AUDIT_ID,
        "alignment_disposition": "ALIGNED",
        "alignment_stage_commit": SOURCE_6B_ALIGNMENT_STAGE,
        "preflight_artifact_digests": {},
    }
    assert "G42 training identity mismatch" not in runner._training_errors(
        tmp_path, execution_source_manifest
    )


def test_retained_projection_evaluation_has_exact_forward_interface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        payload = torch.load(ANCHOR_FIXTURE, map_location="cpu", weights_only=False)
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            payload, accepted_anchor_replicate=0
        )
        deployed = g42.project_g42_arms(
            anchor, accepted_anchor_replicate=0
        )[g42.DB_ARM]
        with pytest.raises(ValueError, match="retained no-slow branch"):
            runner._G42RetainedEvaluationPolicy(deployed)
        deployed.begin_credit_branch_phase()
        retained_calls: list[g41.G41NoSlowProjection] = []
        retained_actor_step = g41.retained_actor_step

        def traced_retained_actor_step(
            model: g41.G41NoSlowProjection, **arguments: Any
        ) -> g41.G41ActorStep:
            retained_calls.append(model)
            return retained_actor_step(model, **arguments)

        monkeypatch.setattr(g41, "retained_actor_step", traced_retained_actor_step)
        processes, _ = runner._source_inventory(
            replicate=0,
            capacity=8,
            episode_count=6,
            formal=False,
        )
        row = runner._evaluate_cell(
            replicate=0,
            capacity=8,
            arm=g42.DB_ARM,
            name=runner.FINAL_RANDOM_DET,
            processes=processes[:1],
            action_seed=runner.seed_block(0, formal=False)["evaluation_action"],
            deployed=deployed,
        )
        assert row["lifecycle_valid"] is True
        assert len(row["episodes"]) == 1
        assert row["state_before"] == row["state_after"]
        assert retained_calls == [deployed] * roster_env.HORIZON
    finally:
        torch.set_num_threads(prior_threads)


def test_runner_first_update_is_accepted_kernel_and_adam_continues(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        payload = torch.load(ANCHOR_FIXTURE, map_location="cpu", weights_only=False)
        anchor = g41.load_accepted_g40_anchor_checkpoint(
            payload, accepted_anchor_replicate=0
        )
        accepted_models = g42.project_g42_arms(
            anchor, accepted_anchor_replicate=0
        )
        runner_models = g42.project_g42_arms(
            anchor, accepted_anchor_replicate=0
        )
        for model in (*accepted_models.values(), *runner_models.values()):
            model.begin_credit_branch_phase()
        accepted_optimizers = {
            arm: g41.make_actor_head_optimizer(model)
            for arm, model in accepted_models.items()
        }
        runner_optimizers = {
            arm: g41.make_actor_head_optimizer(model)
            for arm, model in runner_models.items()
        }
        trajectory = runner._collect_trajectory(
            accepted_models[g42.DB_ARM],
            episode_ids=tuple(range(8)),
            ledger_seed=10_423_000,
            action_seed=10_423_000,
        )
        accepted_record = g42.optimize_matched_direction_attribution_update(
            accepted_models,
            accepted_optimizers,
            trajectory,
            ppo_passes=2,
        )
        runner_record = runner._apply_matched_update(
            runner_models,
            runner_optimizers,
            {g42.DB_ARM: trajectory, g42.NO_DB_ARM: trajectory},
            update_index=0,
            ledger_seed=10_423_000,
            action_seed=10_423_000,
        )
        assert runner_record["passed"] is True
        for arm in g42.ARMS:
            assert g40.state_bytes(accepted_models[arm]) == g40.state_bytes(
                runner_models[arm]
            )
            _assert_nested_equal(
                accepted_optimizers[arm].state_dict(),
                runner_optimizers[arm].state_dict(),
            )
        assert runner_record["pass_records"] == accepted_record["pass_records"]
        continuation = runner._apply_matched_update(
            runner_models,
            runner_optimizers,
            {g42.DB_ARM: trajectory, g42.NO_DB_ARM: trajectory},
            update_index=1,
            ledger_seed=10_421_000,
            action_seed=10_422_000,
        )
        assert continuation["actor_head_optimizer_steps"] == {
            g42.DB_ARM: 4.0,
            g42.NO_DB_ARM: 4.0,
        }
        assert continuation["branch_boundary"]["continuation"] is True
        assert continuation["actor_head_optimizer_step_delta"] == 2
        _assert_roundtripped_training_artifact_valid(
            tmp_path, monkeypatch, runner_record, runner_models
        )
    finally:
        torch.set_num_threads(prior_threads)


def test_first_match_branch_order_is_exact() -> None:
    base = {
        "operational_valid": True,
        "source_valid": True,
        "db_access_confident_fail": False,
        "db_access_pass": True,
        "no_db_access_pass": True,
        "no_db_access_confident_fail": False,
        "no_db_noninferior": True,
        "material_db_advantage": False,
    }
    assert runner.select_g42_result_branch({**base, "operational_valid": False}) == runner.INVALID_BRANCH
    assert runner.select_g42_result_branch({**base, "source_valid": False}) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g42_result_branch(base) == runner.NO_DB_SUFFICIENT_BRANCH
    advantage = {**base, "no_db_access_pass": False, "no_db_noninferior": False, "material_db_advantage": True}
    assert runner.select_g42_result_branch(advantage) == runner.DB_ADVANTAGE_BRANCH
    underpowered = {**base, "db_access_pass": False, "no_db_access_pass": False, "no_db_noninferior": False}
    assert runner.select_g42_result_branch(underpowered) == runner.UNDERPOWERED_BRANCH
