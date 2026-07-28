from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44
    as g44,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as g43,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from scripts import (
    run_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44
    as runner,
)


ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)


def _load_anchor() -> g40.G40NativeSixPolicy:
    return g41.load_accepted_g40_anchor_checkpoint(
        torch.load(ANCHOR_FIXTURE, map_location="cpu", weights_only=False),
        accepted_anchor_replicate=0,
    )


def _proof_worker_runtime() -> dict[str, object]:
    return {
        "pid": 1,
        "wall_time_seconds": 0.1,
        "process_cpu_seconds": 0.1,
        "python_peak_traced_bytes": 1,
        "torch_intraop_threads": 1,
        "thread_environment": dict(runner.WORKER_THREAD_ENV),
    }


def _proof_cpu_execution(configuration: dict[str, object]) -> dict[str, object]:
    return {
        **runner._resolve_cpu_execution(
            int(configuration["cpu_budget"]),
            int(configuration["process_workers"]),
        ),
        "hardware_logical_cpu_count": 16,
        "effective_parent_torch_intraop_threads": 1,
    }


def _first_update() -> tuple[
    dict[str, g41.G41NoSlowProjection],
    dict[str, torch.optim.Optimizer],
    dict[str, object],
]:
    anchor = _load_anchor()
    models = g44.project_g44_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    seeds = runner.seed_block(0, formal=False)
    trajectory = runner._collect_trajectory(
        models[g44.INDEPENDENT_ARM],
        episode_ids=tuple(range(8)),
        ledger_seed=seeds["branch_gradient_probe"],
        action_seed=seeds["branch_gradient_probe"],
    )
    record = runner._apply_matched_update(
        models,
        optimizers,
        {arm: trajectory for arm in g44.ARMS},
        update_index=0,
        ledger_seed=seeds["branch_gradient_probe"],
        action_seed=seeds["branch_gradient_probe"],
    )
    return models, optimizers, record


def test_isolated_orchestration_does_not_mutate_g43_module() -> None:
    assert g43.ALGORITHM_ID.endswith("G43")
    assert g43.ARMS == (g43.DBNORM_ARM, g43.MEAN_ARM)
    assert runner._backend is not __import__(
        "scripts.run_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43",
        fromlist=["*"],
    )
    assert runner._backend.source is g44
    assert runner._backend.ALGORITHM_ID == g44.ALGORITHM_ID
    assert runner._backend.ALIGNED_IMPLEMENTATION_COMMIT == (
        "1a6e046801ab3d83830d4c9f6e9724c8c47659da"
    )


def test_configuration_seed_budget_and_cpp_contract() -> None:
    nonformal = runner._configuration(formal=False)
    formal = runner._configuration(formal=True)
    assert nonformal["replicates"] == 1
    assert nonformal["branch_updates_per_arm"] == 10
    assert nonformal["total_cells"] == 24
    assert nonformal["training_transitions"] == 7_680
    assert nonformal["evaluation_transitions"] == 6_912
    assert nonformal["total_real_transitions"] == 14_592
    assert nonformal["optimizer_steps"] == 40
    assert formal["replicates"] == 3
    assert formal["branch_updates_per_arm"] == 100
    assert formal["total_cells"] == 72
    assert formal["training_transitions"] == 230_400
    assert formal["evaluation_transitions"] == 165_888
    assert formal["total_real_transitions"] == 396_288
    assert formal["optimizer_steps"] == 1_200
    assert formal["environment_backend"] == "ContinuousRosterToyBatch_CPU_CPP_required"
    assert formal["environment_python_fallback"] is False
    assert formal["normalization_rows"] == 384
    assert formal["channel_composition"] == "literal_equal_mean_0.5"
    assert formal["aligned_g44_implementation_commit"] == (
        "1a6e046801ab3d83830d4c9f6e9724c8c47659da"
    )
    assert formal["accepted_g43_source_commit"] == g44.ACCEPTED_G43_SOURCE_COMMIT
    assert formal["cpu_budget"] == 2
    assert formal["process_workers"] == 2
    assert formal["worker_thread_controls"] == {
        **runner.WORKER_THREAD_ENV,
        "torch_intraop_threads": 1,
    }
    with pytest.raises(ValueError, match="closed interval"):
        runner._configuration(formal=True, cpu_budget=7, process_workers=6)
    with pytest.raises(ValueError, match="cannot exceed"):
        runner._configuration(formal=True, cpu_budget=2, process_workers=3)
    assert runner.seed_block(2, formal=True) == {
        "branch_ledger": 10_441_002,
        "branch_action": 10_442_002,
        "branch_gradient_probe": 10_443_002,
        "evaluation_ledger": 10_444_002,
        "evaluation_process": 10_445_002,
        "evaluation_action": 10_446_002,
    }
    assert runner.bootstrap_seed(formal=True) == 10_447_044
    assert runner.bootstrap_seed(formal=False) == 11_347_044


def test_formal_authority_is_bound_to_independent_alignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    aligned_commit = "1a6e046801ab3d83830d4c9f6e9724c8c47659da"
    alignment_stage = "b55578a8e57f444895da59efe9268ebe31edf511"
    assert runner.ALIGNED_IMPLEMENTATION_COMMIT == aligned_commit
    assert runner.ALIGNMENT_STAGE_COMMIT == alignment_stage
    assert runner._backend.ALIGNED_IMPLEMENTATION_COMMIT == aligned_commit
    assert runner._backend.ALIGNMENT_STAGE_COMMIT == alignment_stage
    assert runner._configuration(formal=True)[
        "aligned_g44_implementation_commit"
    ] == aligned_commit
    assert runner.source_controls()[
        "aligned_g44_implementation_commit"
    ] == aligned_commit
    accepted_root = runner.PROJECT_ROOT / runner.ACCEPTED_ANCHOR_ROOT_RELATIVE
    with pytest.raises(ValueError, match="authorization token mismatch"):
        runner.train(
            run_root=tmp_path / "formal-token",
            source_commit="a" * 40,
            formal=True,
            authorization_token="wrong",
            accepted_anchor_root=accepted_root,
        )

    def _unexpected_preflight_read(_: Path) -> dict[str, object]:
        raise AssertionError("invalid alignment identity reached preflight read")

    monkeypatch.setattr(runner._backend, "_read_json", _unexpected_preflight_read)
    with pytest.raises(ValueError, match="registered ALIGNED source"):
        runner.train(
            run_root=tmp_path / "formal-wrong-source",
            source_commit="a" * 40,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=accepted_root,
            preflight_root=tmp_path / "not-read",
            alignment_disposition="ALIGNED",
            aligned_source_commit="0" * 40,
            alignment_stage_commit=alignment_stage,
        )
    with pytest.raises(ValueError, match="registered ALIGNED source"):
        runner.train(
            run_root=tmp_path / "formal-wrong-stage",
            source_commit="a" * 40,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=accepted_root,
            preflight_root=tmp_path / "not-read",
            alignment_disposition="ALIGNED",
            aligned_source_commit=aligned_commit,
            alignment_stage_commit="1" * 40,
        )

    class _ReachedExactPreflightRead(Exception):
        pass

    def _exact_preflight_read(_: Path) -> dict[str, object]:
        raise _ReachedExactPreflightRead

    monkeypatch.setattr(runner._backend, "_read_json", _exact_preflight_read)
    with pytest.raises(_ReachedExactPreflightRead):
        runner.train(
            run_root=tmp_path / "formal-exact-binding",
            source_commit="a" * 40,
            formal=True,
            authorization_token=runner.AUTHORIZATION_TOKEN,
            accepted_anchor_root=accepted_root,
            preflight_root=tmp_path / "exact-preflight",
            alignment_disposition="ALIGNED",
            aligned_source_commit=aligned_commit,
            alignment_stage_commit=alignment_stage,
        )
    assert not (tmp_path / "formal-token").exists()
    assert not (tmp_path / "formal-wrong-source").exists()
    assert not (tmp_path / "formal-wrong-stage").exists()
    assert not (tmp_path / "formal-exact-binding").exists()


def test_isolated_worker_backend_is_spawn_safe_and_bitwise_equivalent(
    tmp_path: Path,
) -> None:
    report = runner.benchmark_cpu_process_parallelism(
        benchmark_root=tmp_path / "parallel-benchmark",
        worker_counts=(1, 2),
        task_count=2,
        batch_size=2,
        repeats=1,
    )
    assert report["all_worker_counts_bitwise_equivalent"] is True
    assert report["artifact_reload_valid"] is True
    assert [row["process_workers"] for row in report["matrix"]] == [1, 2]
    assert all(
        row["correctness_disposition"] == "BITWISE_EQUIVALENT"
        and row["worker_thread_controls_valid"] is True
        and row["deterministic_preassigned_merge"] is True
        for row in report["matrix"]
    )


def test_two_process_g44_update_parameters_adam_and_evidence_are_bitwise(
    tmp_path: Path,
) -> None:
    report = runner.prove_two_process_update_equivalence(
        proof_root=tmp_path / "g44-update-proof",
        accepted_anchor_root=runner._expected_anchor_root(),
    )
    assert report["passed"] is True
    assert report["worker_count"] == 2
    assert report["distinct_processes"] is True
    assert report["single_thread_workers"] is True
    assert report["deterministic_preassigned_index_merge"] is True
    assert report["parameters_adam_evidence_bitwise_equivalent"] is True
    assert report["scientific_iteration_cost"] == 0
    semantic = report["semantic"]
    assert semantic["passed"] is True
    assert semantic["branch_update_order"] == list(g44.ARMS)
    assert set(semantic["model_state_digests"]) == set(g44.ARMS)
    assert set(semantic["adam_state_digests"]) == set(g44.ARMS)
    assert len(semantic["evidence_sha256"]) == 64


def test_proof_only_readiness_lifecycle_reload_and_tamper_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_commit = "a" * 40
    run_root = tmp_path / "execution-readiness"

    def proof_only_parallel_report(
        *, proof_root: Path, accepted_anchor_root: Path
    ) -> dict[str, object]:
        assert accepted_anchor_root == runner._expected_anchor_root()
        report: dict[str, object] = {
            "proof_kind": "two_process_single_g44_update_equivalence",
            "worker_count": 2,
            "distinct_processes": True,
            "single_thread_workers": True,
            "deterministic_preassigned_index_merge": True,
            "parameters_adam_evidence_bitwise_equivalent": True,
            "semantic": {"proof_fixture": True},
            "scientific_iteration_cost": 0,
            "formal": False,
            "proof_sized_updates_per_worker": 1,
            "passed": True,
        }
        runner._write_json(
            proof_root / "two_process_update_equivalence.json", report
        )
        return report

    monkeypatch.setattr(
        runner,
        "prove_two_process_update_equivalence",
        proof_only_parallel_report,
    )
    smoke = runner.readiness_interface_smoke(
        source_commit=source_commit,
        accepted_anchor_root=runner._expected_anchor_root(),
    )
    assert smoke["production_entry"] == "train"
    assert smoke["formal"] is False
    assert smoke["scientific_iteration_cost"] == 0
    training = runner.readiness_train(
        run_root=run_root,
        source_commit=source_commit,
        accepted_anchor_root=runner._expected_anchor_root(),
    )
    assert training["artifact_kind"] == "execution_readiness_proof_only"
    assert training["conclusion_bearing"] is False
    assert (
        training["aligned_source_commit"]
        == "1a6e046801ab3d83830d4c9f6e9724c8c47659da"
    )
    assert training["proof_inventory"]["branch_updates_per_arm"] == 1
    assert runner.readiness_training_errors(run_root, training) == []
    reloaded = runner.reload_readiness_artifacts(run_root)
    assert reloaded["passed"] is True
    assert all(
        row["phase"] == "credit_branch"
        and row["standalone_slow_critic_present"] is False
        for row in reloaded["arms"].values()
    )
    evaluation = runner.readiness_evaluate(run_root=run_root)
    assert evaluation["conclusion_bearing"] is False
    assert runner.readiness_evaluation_errors(
        run_root, training, evaluation
    ) == []
    analysis = runner.readiness_analyze(run_root=run_root)
    assert analysis["branch"] == runner.READINESS_BRANCH
    assert analysis["science_disposition"] is None
    assert runner.validate_readiness_artifacts(run_root) == []

    tampered = copy.deepcopy(analysis)
    tampered["scientific_iteration_cost"] = 1
    runner._write_json(run_root / "analysis_result.json", tampered)
    assert "G44 readiness analysis identity mismatch" in (
        runner.validate_readiness_artifacts(run_root)
    )


def test_runner_first_update_calls_g44_kernel_and_keeps_adam_exposure() -> None:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        models, optimizers, record = _first_update()
        assert record["algorithm_id"] == g44.ALGORITHM_ID
        assert record["passed"] is True
        assert record["paired_source_audit"]["passed"] is True
        assert record["branch_update_order"] == list(g44.ARMS)
        assert record["actor_head_optimizer_steps"] == {
            arm: 2.0 for arm in g44.ARMS
        }
        seeds = runner.seed_block(0, formal=False)
        trajectory = runner._collect_trajectory(
            models[g44.INDEPENDENT_ARM],
            episode_ids=tuple(range(8)),
            ledger_seed=seeds["branch_ledger"],
            action_seed=seeds["branch_action"],
        )
        continuation = runner._apply_matched_update(
            models,
            optimizers,
            {arm: trajectory for arm in g44.ARMS},
            update_index=1,
            ledger_seed=seeds["branch_ledger"],
            action_seed=seeds["branch_action"],
        )
        assert continuation["actor_head_optimizer_steps"] == {
            arm: 4.0 for arm in g44.ARMS
        }
        assert continuation["branch_boundary"]["continuation"] is True
    finally:
        torch.set_num_threads(prior_threads)


def test_artifact_roundtrip_final_only_and_schedule_tamper_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        models, _, record = _first_update()
        configuration = runner._configuration(formal=False)
        seeds = runner.seed_block(0, formal=False)
        records: list[dict[str, object]] = []
        for update_index in range(int(configuration["branch_updates_per_arm"])):
            serialized = json.loads(g44.serialize_diagnostics(record))
            serialized["update_index"] = update_index
            serialized["paired_source_audit"]["update_index"] = update_index
            serialized["paired_source_audit"]["ledger_seed"] = (
                seeds["branch_gradient_probe"]
                if update_index == 0
                else seeds["branch_ledger"]
            )
            serialized["paired_source_audit"]["action_seed"] = (
                seeds["branch_gradient_probe"]
                if update_index == 0
                else seeds["branch_action"]
            )
            records.append(serialized)
        conclusion = g44.build_conclusion_evidence(records, formal=False)
        assert g44.validate_conclusion_evidence(conclusion)
        accepted_root = ANCHOR_FIXTURE.parent.resolve()
        anchor_digests = {ANCHOR_FIXTURE.name: "proof-sized-fixture"}
        monkeypatch.setattr(runner._backend, "_bind_anchor_root", lambda _: accepted_root)
        monkeypatch.setattr(
            runner._backend, "_validate_anchor_manifest", lambda _: anchor_digests
        )
        expected_steps = int(configuration["branch_updates_per_arm"]) * 2
        arms: dict[str, dict[str, object]] = {}
        for arm in g44.ARMS:
            reference = runner._checkpoint_reference(0, arm)
            payload = runner._save_checkpoint(
                tmp_path / reference,
                source_commit="a" * 40,
                aligned_source_commit=runner.ALIGNED_IMPLEMENTATION_COMMIT,
                formal=False,
                replicate=0,
                arm=arm,
                configuration=configuration,
                seeds=seeds,
                model=models[arm],
                final_update_record=records[-1],
                conclusion_evidence=conclusion,
            )
            arms[arm] = {
                "final_checkpoint": reference,
                "final_checkpoint_file_digest": runner._artifact_digest(
                    tmp_path / reference
                ),
                "final_state_digest": payload["model_state_digest"],
                "completed_branch_updates": 10,
                "actor_head_optimizer_steps": expected_steps,
                "actor_parameter_departure": True,
                "shared_baseline_parameter_departure": True,
            }
        row = {
            "replicate": 0,
            "seeds": seeds,
            "accepted_anchor": g41.accepted_g40_anchor_identity(0),
            "accepted_anchor_state_digest": g41.accepted_g40_anchor_authority(
                0
            ).complete_state_digest,
            "branch_boundary_audit": {"passed": True},
            "paired_collection_before_update": True,
            "branch_update_order": list(g44.ARMS),
            "lifecycle_contract_valid": {arm: True for arm in g44.ARMS},
            "actor_parameter_departure": {arm: True for arm in g44.ARMS},
            "shared_baseline_parameter_departure": {
                arm: True for arm in g44.ARMS
            },
            "actor_head_optimizer_steps": {
                arm: float(expected_steps) for arm in g44.ARMS
            },
            "worker_execution": {
                "index": 0,
                "replicate": 0,
                "configured_process_workers": 2,
                "output_path": str(tmp_path / "consumed.pt"),
                "output_digest": "0" * 64,
                "output_transport_consumed": True,
                "runtime": _proof_worker_runtime(),
            },
            "update_records": records,
            "arms": arms,
        }
        manifest = {
            "schema_version": runner.SCHEMA_VERSION,
            "algorithm": runner.ALGORITHM_ID,
            "source_id": g44.SOURCE_ID,
            "stage": "train",
            "status": "COMPLETE",
            "formal": False,
            "source_commit": "a" * 40,
            "authorization_token": None,
            "alignment_audit_id": None,
            "alignment_disposition": None,
            "aligned_source_commit": runner.ALIGNED_IMPLEMENTATION_COMMIT,
            "alignment_stage_commit": None,
            "preflight_root": None,
            "preflight_artifact_digests": None,
            "accepted_anchor_root": str(accepted_root),
            "accepted_anchor_root_mode": "read_only_input_no_writes",
            "accepted_anchor_artifact_digests": anchor_digests,
            "runtime": {},
            "cpu_execution": _proof_cpu_execution(configuration),
            "native_backend": {
                "kind": "ContinuousRosterToyBatch_CPU_CPP",
                "required": True,
                "python_fallback": False,
            },
            "configuration": configuration,
            "source_controls": runner.source_controls(),
            "conclusion_evidence": conclusion,
            "replicate_results": [row],
        }
        assert runner._training_errors(tmp_path, manifest) == []
        tampered = copy.deepcopy(manifest)
        tampered["replicate_results"][0]["update_records"][0][
            "pass_records"
        ][0]["channel_scale_schedule"]["q_scale"] = 0.0
        assert "G44 update evidence mismatch" in runner._training_errors(
            tmp_path, tampered
        )
        tampered_mask = copy.deepcopy(manifest)
        tampered_mask["replicate_results"][0]["update_records"][0][
            "pass_records"
        ][0]["channel_scale_schedule"]["normalization_mask_digest"] = "0" * 64
        assert "G44 update evidence mismatch" in runner._training_errors(
            tmp_path, tampered_mask
        )
        pooled_tamper = copy.deepcopy(manifest)
        reference_schedule = copy.deepcopy(
            pooled_tamper["replicate_results"][0]["update_records"][0][
                "pass_records"
            ][0]["channel_scale_schedule"]
        )
        pooled_tamper["replicate_results"][0]["update_records"][0][
            "pass_records"
        ][0]["normalization_by_arm"][g44.POOLED_ARM][
            "normalization_mask_digest"
        ] = "0" * 64
        assert pooled_tamper["replicate_results"][0]["update_records"][0][
            "pass_records"
        ][0]["channel_scale_schedule"] == reference_schedule
        assert "G44 update evidence mismatch" in runner._training_errors(
            tmp_path, pooled_tamper
        )
        route_tamper = copy.deepcopy(manifest)
        route_tamper["replicate_results"][0]["update_records"][0][
            "pass_records"
        ][0]["normalization_by_arm"][g44.POOLED_ARM]["arm"] = (
            g44.INDEPENDENT_ARM
        )
        assert "G44 update evidence mismatch" in runner._training_errors(
            tmp_path, route_tamper
        )
        conclusion_tamper = copy.deepcopy(manifest)
        conclusion_tamper["conclusion_evidence"]["replicate_rows"][0][
            "reconstructed_passes"
        ][0]["normalization_by_arm"][g44.POOLED_ARM][
            "normalization_mask_digest"
        ] = "0" * 64
        assert "G44 conclusion treatment-activation evidence mismatch" in (
            runner._training_errors(tmp_path, conclusion_tamper)
        )
        checkpoint_tamper = copy.deepcopy(manifest)
        arm = g44.POOLED_ARM
        reference = checkpoint_tamper["replicate_results"][0]["arms"][arm][
            "final_checkpoint"
        ]
        checkpoint_path = tmp_path / reference
        payload = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
        payload["source_final_checkpoint_certificate"][
            "final_update_evidence"
        ]["pass_records"][0]["normalization_by_arm"][arm][
            "normalization_mask_digest"
        ] = "0" * 64
        torch.save(payload, checkpoint_path)
        checkpoint_tamper["replicate_results"][0]["arms"][arm][
            "final_checkpoint_file_digest"
        ] = runner._artifact_digest(checkpoint_path)
        assert (
            "G44 accepted-source checkpoint normalization evidence mismatch"
            in runner._training_errors(tmp_path, checkpoint_tamper)
        )
        extra = tmp_path / "checkpoints" / "replicate_0_intermediate.pt"
        extra.touch()
        assert "G44 checkpoint inventory is not final-only" in runner._training_errors(
            tmp_path, manifest
        )
    finally:
        torch.set_num_threads(prior_threads)


def test_first_match_branch_order_is_exact() -> None:
    assert runner.INVALID_BRANCH == (
        "INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_"
        "CHANNEL_SCALE_ATTRIBUTION_G44"
    )
    base: dict[str, Any] = {
        "operational_valid": True,
        "source_valid": True,
        "independent_access_confident_fail": False,
        "independent_access_pass": True,
        "pooled_access_pass": True,
        "pooled_access_confident_fail": False,
        "pooled_noninferior": True,
        "material_independent_advantage": False,
    }
    assert runner.select_g44_result_branch(
        {**base, "operational_valid": False}
    ) == runner.INVALID_BRANCH
    assert runner.select_g44_result_branch(
        {**base, "source_valid": False}
    ) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g44_result_branch(base) == runner.POOLED_SUFFICIENT_BRANCH
    assert runner.select_g44_result_branch(
        {
            **base,
            "pooled_access_pass": False,
            "pooled_noninferior": False,
            "material_independent_advantage": True,
        }
    ) == runner.INDEPENDENT_ADVANTAGE_BRANCH
    assert runner.select_g44_result_branch(
        {
            **base,
            "independent_access_pass": False,
            "pooled_access_pass": False,
            "pooled_noninferior": False,
        }
    ) == runner.UNDERPOWERED_BRANCH
