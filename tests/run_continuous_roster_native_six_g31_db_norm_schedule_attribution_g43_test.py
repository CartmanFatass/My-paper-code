from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest
import torch

from ha_ctse_process import continuous_roster_native_six_credit_reduction_g40 as g40
from ha_ctse_process import (
    continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as g43,
)
from ha_ctse_process import (
    continuous_roster_native_six_g31_slow_critic_reduction_g41 as g41,
)
from scripts import (
    run_continuous_roster_native_six_g31_db_norm_schedule_attribution_g43 as runner,
)


ANCHOR_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "docs/research/cdc/EVIDENCE_NOTES/fixtures/"
    "CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40/"
    "replicate_0_common_native6_fast_anchor.pt"
)


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


def _load_anchor() -> g40.G40NativeSixPolicy:
    payload = torch.load(ANCHOR_FIXTURE, map_location="cpu", weights_only=False)
    return g41.load_accepted_g40_anchor_checkpoint(
        payload, accepted_anchor_replicate=0
    )


def _proof_cpu_execution(
    configuration: Mapping[str, object],
) -> dict[str, object]:
    return {
        **runner._resolve_cpu_execution(
            int(configuration["cpu_budget"]),
            int(configuration["process_workers"]),
        ),
        "hardware_logical_cpu_count": 1,
        "effective_parent_torch_intraop_threads": 1,
    }


def _proof_worker_runtime() -> dict[str, object]:
    return {
        "pid": 1,
        "wall_time_seconds": 0.0,
        "process_cpu_seconds": 0.0,
        "python_peak_traced_bytes": 0,
        "torch_intraop_threads": 1,
        "thread_environment": {
            name: "1" for name in runner.WORKER_THREAD_ENV
        },
    }


def _wrong_index_worker(task: Mapping[str, object]) -> dict[str, object]:
    path = Path(str(task["output_path"]))
    runner._write_json(path, {"unexpected": True})
    return {
        "index": int(task["index"]) + 1,
        "output_path": str(path),
        "output_digest": runner._artifact_digest(path),
    }


def _first_runner_update() -> tuple[
    dict[str, g41.G41NoSlowProjection],
    dict[str, torch.optim.Optimizer],
    dict[str, object],
]:
    anchor = _load_anchor()
    models = g43.project_g43_arms(anchor, accepted_anchor_replicate=0)
    for model in models.values():
        model.begin_credit_branch_phase()
    optimizers = {
        arm: g41.make_actor_head_optimizer(model)
        for arm, model in models.items()
    }
    seeds = runner.seed_block(0, formal=False)
    trajectory = runner._collect_trajectory(
        models[g43.DBNORM_ARM],
        episode_ids=tuple(range(8)),
        ledger_seed=seeds["branch_gradient_probe"],
        action_seed=seeds["branch_gradient_probe"],
    )
    record = runner._apply_matched_update(
        models,
        optimizers,
        {arm: trajectory for arm in g43.ARMS},
        update_index=0,
        ledger_seed=seeds["branch_gradient_probe"],
        action_seed=seeds["branch_gradient_probe"],
    )
    return models, optimizers, record


def test_configuration_seeds_cpp_and_inventory_are_exact() -> None:
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
    assert formal["environment_backend"] == (
        "ContinuousRosterToyBatch_CPU_CPP_required"
    )
    assert formal["environment_python_fallback"] is False
    assert formal["intrinsic_K_search"] == 0
    assert formal["hypothetical_trajectory_count"] == 0
    assert formal["hypothetical_transitions"] == 0
    assert nonformal["cpu_budget"] == 2
    assert nonformal["process_workers"] == 2
    assert formal["cpu_parallelism_fixed_at_launch"] is True
    assert formal["cpu_continuous_adaptation"] is False
    assert formal["worker_start_method"] == "spawn"
    assert formal["training_parallel_unit"] == "formal_replicate_only"
    assert formal["evaluation_parallel_unit"] == "replicate_capacity_cell"
    assert formal["deterministic_worker_merge"] == (
        "preassigned_index_not_completion_order"
    )
    assert formal["worker_thread_controls"] == {
        **runner.WORKER_THREAD_ENV,
        "torch_intraop_threads": 1,
    }
    assert runner._configuration(
        formal=True, cpu_budget=6, process_workers=6
    )["process_workers"] == 6
    with pytest.raises(ValueError, match="closed interval"):
        runner._configuration(formal=True, cpu_budget=7, process_workers=6)
    with pytest.raises(ValueError, match="cannot exceed"):
        runner._configuration(formal=True, cpu_budget=2, process_workers=3)
    assert runner.seed_block(2, formal=True) == {
        "branch_ledger": 10_431_002,
        "branch_action": 10_432_002,
        "branch_gradient_probe": 10_433_002,
        "evaluation_ledger": 10_434_002,
        "evaluation_process": 10_435_002,
        "evaluation_action": 10_436_002,
    }
    assert runner.bootstrap_seed(formal=True) == 10_437_043
    assert runner.bootstrap_seed(formal=False) == 11_337_043
    for formal_scope, episodes, expected in ((False, 6, 2), (True, 48, 16)):
        _, inventory = runner._source_inventory(
            replicate=0,
            capacity=8,
            episode_count=episodes,
            formal=formal_scope,
        )
        assert set(inventory["order_counts"].values()) == {expected}
        assert set(inventory["profile_counts"].values()) == {expected}


def test_fixed_worker_pool_is_bitwise_equivalent_and_fail_closed(
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
    assert report["phase_evidence"] == {
        "artifact_validation": "digest_bound_indexed_worker_outputs",
        "artifact_reload": "exact_json_reload_before_merge",
        "evaluate_entry": "ContinuousRosterToyBatch_CPU_CPP",
        "analyze_entry": "serial_reference_semantic_digest_comparison",
    }
    matrix = report["matrix"]
    assert [row["process_workers"] for row in matrix] == [1, 2]
    assert all(
        row["correctness_disposition"] == "BITWISE_EQUIVALENT"
        and row["worker_thread_controls_valid"] is True
        and row["deterministic_preassigned_merge"] is True
        for row in matrix
    )
    report_path = (
        tmp_path / "parallel-benchmark" / "cpu_parallel_benchmark.json"
    )
    assert runner._read_json(report_path) == report

    with pytest.raises(ValueError, match="index/output inventory"):
        runner._run_indexed_worker_tasks(
            [{"index": 1, "output_path": str(tmp_path / "missing.json")}],
            _wrong_index_worker,
            process_workers=1,
        )
    with pytest.raises(RuntimeError, match="index/output mismatch"):
        runner._run_indexed_worker_tasks(
            [{"index": 0, "output_path": str(tmp_path / "wrong.json")}],
            _wrong_index_worker,
            process_workers=1,
        )


def test_formal_authority_is_bound_to_independent_alignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    aligned_commit = "45e16f71d171228135b6444bee1678b157d79abe"
    alignment_stage = "889c0b4e3d68a8d74f811ae9ecfe7b5213abfa76"
    assert runner.ALIGNED_IMPLEMENTATION_COMMIT == aligned_commit
    assert runner.ALIGNMENT_STAGE_COMMIT == alignment_stage
    assert runner._configuration(formal=True)[
        "aligned_g43_implementation_commit"
    ] == aligned_commit
    assert runner.source_controls()[
        "aligned_g43_implementation_commit"
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

    monkeypatch.setattr(runner, "_read_json", _unexpected_preflight_read)
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

    monkeypatch.setattr(runner, "_read_json", _exact_preflight_read)
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


def test_runner_first_update_is_source_kernel_and_adam_continues() -> None:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        anchor = _load_anchor()
        source_models = g43.project_g43_arms(
            anchor, accepted_anchor_replicate=0
        )
        runner_models = g43.project_g43_arms(
            anchor, accepted_anchor_replicate=0
        )
        for model in (*source_models.values(), *runner_models.values()):
            model.begin_credit_branch_phase()
        source_optimizers = {
            arm: g41.make_actor_head_optimizer(model)
            for arm, model in source_models.items()
        }
        runner_optimizers = {
            arm: g41.make_actor_head_optimizer(model)
            for arm, model in runner_models.items()
        }
        seeds = runner.seed_block(0, formal=False)
        trajectory = runner._collect_trajectory(
            source_models[g43.DBNORM_ARM],
            episode_ids=tuple(range(8)),
            ledger_seed=seeds["branch_gradient_probe"],
            action_seed=seeds["branch_gradient_probe"],
        )
        source_record = g43.optimize_norm_schedule_update(
            source_models,
            source_optimizers,
            {arm: trajectory for arm in g43.ARMS},
            update_index=0,
        )
        runner_record = runner._apply_matched_update(
            runner_models,
            runner_optimizers,
            {arm: trajectory for arm in g43.ARMS},
            update_index=0,
            ledger_seed=seeds["branch_gradient_probe"],
            action_seed=seeds["branch_gradient_probe"],
        )
        assert runner_record["passed"] is True
        assert runner_record["pass_records"] == source_record["pass_records"]
        assert runner_record["paired_source_audit"]["passed"] is True
        for arm in g43.ARMS:
            assert g40.state_bytes(source_models[arm]) == g40.state_bytes(
                runner_models[arm]
            )
            _assert_nested_equal(
                source_optimizers[arm].state_dict(),
                runner_optimizers[arm].state_dict(),
            )
        continuation = runner._apply_matched_update(
            runner_models,
            runner_optimizers,
            {arm: trajectory for arm in g43.ARMS},
            update_index=1,
            ledger_seed=seeds["branch_ledger"],
            action_seed=seeds["branch_action"],
        )
        assert continuation["actor_head_optimizer_steps"] == {
            g43.DBNORM_ARM: 4.0,
            g43.MEAN_ARM: 4.0,
        }
        assert continuation["branch_boundary"]["continuation"] is True
        assert continuation["actor_head_optimizer_step_delta"] == 2
    finally:
        torch.set_num_threads(prior_threads)


def test_artifact_roundtrip_final_only_and_tamper_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        models, _, record = _first_runner_update()
        configuration = runner._configuration(formal=False)
        seeds = runner.seed_block(0, formal=False)
        records: list[dict[str, object]] = []
        for update_index in range(int(configuration["branch_updates_per_arm"])):
            serialized = json.loads(g43.serialize_diagnostics(record))
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
        conclusion = g43.build_conclusion_evidence(records, formal=False)
        assert g43.validate_conclusion_evidence(conclusion)

        accepted_root = ANCHOR_FIXTURE.parent.resolve()
        anchor_digests = {ANCHOR_FIXTURE.name: "proof-sized-fixture"}
        monkeypatch.setattr(runner, "_bind_anchor_root", lambda _: accepted_root)
        monkeypatch.setattr(
            runner, "_validate_anchor_manifest", lambda _: anchor_digests
        )
        arms: dict[str, dict[str, object]] = {}
        expected_steps = int(configuration["branch_updates_per_arm"]) * int(
            configuration["ppo_passes"]
        )
        for arm in g43.ARMS:
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
                "completed_branch_updates": int(
                    configuration["branch_updates_per_arm"]
                ),
                "actor_head_optimizer_steps": expected_steps,
                "actor_parameter_departure": True,
                "shared_baseline_parameter_departure": True,
            }
        row = {
            "replicate": 0,
            "seeds": seeds,
            "accepted_anchor": g41.accepted_g40_anchor_identity(0),
            "accepted_anchor_state_digest": (
                g41.accepted_g40_anchor_authority(0).complete_state_digest
            ),
            "branch_boundary_audit": {"passed": True},
            "paired_collection_before_update": True,
            "branch_update_order": list(g43.ARMS),
            "lifecycle_contract_valid": {arm: True for arm in g43.ARMS},
            "actor_parameter_departure": {arm: True for arm in g43.ARMS},
            "shared_baseline_parameter_departure": {
                arm: True for arm in g43.ARMS
            },
            "actor_head_optimizer_steps": {
                arm: float(expected_steps) for arm in g43.ARMS
            },
            "worker_execution": {
                "index": 0,
                "replicate": 0,
                "configured_process_workers": int(
                    configuration["process_workers"]
                ),
                "output_path": str(tmp_path / "consumed-worker-result.pt"),
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
            "source_id": g43.SOURCE_ID,
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
        tampered = json.loads(json.dumps(manifest))
        tampered["replicate_results"][0]["update_records"][0][
            "paired_source_audit"
        ]["action_seed"] += 1
        assert runner._training_errors(tmp_path, tampered) == [
            "G43 update evidence mismatch"
        ]
        extra = tmp_path / "checkpoints" / "replicate_0_intermediate.pt"
        extra.touch()
        assert runner._training_errors(tmp_path, manifest) == [
            "G43 checkpoint inventory is not final-only"
        ]
    finally:
        torch.set_num_threads(prior_threads)


def test_retained_projection_evaluation_uses_exact_no_slow_interface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prior_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        deployed = g43.project_g43_arms(
            _load_anchor(), accepted_anchor_replicate=0
        )[g43.DBNORM_ARM]
        with pytest.raises(ValueError, match="retained no-slow branch"):
            runner._G43RetainedEvaluationPolicy(deployed)
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
            arm=g43.DBNORM_ARM,
            name=runner.FINAL_RANDOM_DET,
            processes=processes[:1],
            action_seed=runner.seed_block(0, formal=False)["evaluation_action"],
            deployed=deployed,
        )
        assert row["lifecycle_valid"] is True
        assert len(row["episodes"]) == 1
        assert row["state_before"] == row["state_after"]
        assert retained_calls == [deployed] * runner.g32.HORIZON
    finally:
        torch.set_num_threads(prior_threads)


def test_first_match_branch_order_is_exact() -> None:
    base = {
        "operational_valid": True,
        "source_valid": True,
        "dbnorm_access_confident_fail": False,
        "dbnorm_access_pass": True,
        "mean_access_pass": True,
        "mean_access_confident_fail": False,
        "mean_noninferior": True,
        "material_dbnorm_advantage": False,
    }
    assert runner.select_g43_result_branch(
        {**base, "operational_valid": False}
    ) == runner.INVALID_BRANCH
    assert runner.select_g43_result_branch(
        {**base, "source_valid": False}
    ) == runner.SOURCE_FAILURE_BRANCH
    assert runner.select_g43_result_branch(base) == runner.MEAN_SUFFICIENT_BRANCH
    assert runner.select_g43_result_branch(
        {
            **base,
            "mean_access_pass": False,
            "mean_noninferior": False,
            "material_dbnorm_advantage": True,
        }
    ) == runner.DBNORM_ADVANTAGE_BRANCH
    assert runner.select_g43_result_branch(
        {
            **base,
            "dbnorm_access_pass": False,
            "mean_access_pass": False,
            "mean_noninferior": False,
        }
    ) == runner.UNDERPOWERED_BRANCH
