from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06 import production_source_factored_preflight as preflight_module
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_contract import (
    CLAIM_ROWS, OBJECT_ID, PRODUCTION_REQUEST_SCHEMA, PRODUCTION_STATUS, RUN_MODE, RUNNER_MASTER_POLICY,
    SourceFactoredNotReady, canonical_json_bytes, complete_contract, production_readiness_gap_inventory,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_preflight import run_preflight
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_process import run_two_owner_one_tick_pathwise_oracle
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_source_factored_runner import (
    main as runner_main, refuse_run,
)


def _not_ready_request_header() -> dict[str, object]:
    return {
        "schema": PRODUCTION_REQUEST_SCHEMA,
        "master_policy": RUNNER_MASTER_POLICY,
        "caller_master_allowed": False,
    }


def test_source_factored_preflight_is_measured_result_blind_and_discloses_native_setup(tmp_path: Path) -> None:
    run_two_owner_one_tick_pathwise_oracle()  # build outside the read-only preflight
    run_root = tmp_path / "preflight-receipt-root"
    receipt = run_preflight(repository_root=Path.cwd(), run_root=run_root)
    assert receipt["schema"] == "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_PREFLIGHT_RECEIPT_V2"
    assert receipt["passed"] is False and receipt["status"] == "NOT_READY"
    assert receipt["master_created"] is False and receipt["scientific_master_created"] is False
    assert receipt["checkpoint_created"] is False
    assert receipt["scientific_coordinate_executed"] is False
    assert run_root.is_dir()
    assert (run_root / "preflight-receipt.json").is_file()
    assert {path.name for path in run_root.iterdir()} == {"preflight-receipt.json"}
    assert (run_root / "preflight-receipt.json").read_bytes() == canonical_json_bytes(receipt)
    assert receipt["exact_ledgers"]["claim_rows"] == CLAIM_ROWS == 6_912
    assert receipt["exact_ledgers"]["updates"] == 24_576
    assert receipt["exact_ledgers"]["training_transitions"] == 100_663_296
    assert receipt["exact_ledgers"]["prevalence_inference"] == {
        "roots": 24, "root_bytes": 32, "tests": 4,
        "per_test_alpha": {"numerator": 1, "denominator": 80},
        "rejection_threshold": 18,
        "exact_null_tail": {"numerator": 190051, "denominator": 16777216},
    }
    assert "inference_resamples" not in receipt["exact_ledgers"]
    assert receipt["measured_process"]["device"] == "cpu"
    assert receipt["measured_process"]["gpu_count"] == 0
    dynamic_probe = receipt["native_probe"]["dynamic_test_clone_executed"]
    assert receipt["fixed_test_master_used"] is dynamic_probe
    assert receipt["fixed_test_reset_instantiated"] is dynamic_probe
    if dynamic_probe:
        assert receipt["native_probe"]["ordinary_mode0_clone_rejected"] is True
        assert receipt["native_probe"]["ordinary_mode0_clone_rejection_code"] == 2
    assert receipt["native_probe"]["static_test_predicate_explicitly_rejects_mode0"] is True
    assert receipt["native_probe"]["test_source_factored_sidecar_abi_present"] is True
    assert receipt["native_probe"]["test_post_arrival_observation_conformance"] is True
    assert receipt["native_probe"]["production_mode_reachable"] is False
    oracle = receipt["two_owner_one_tick_oracle"]
    assert oracle == {
        "schema": "DISH_PSF_R01_TWO_OWNER_ONE_TICK_ORACLE_V1",
        "test_only": True,
        "passed": True,
        "owners": [0, 1],
        "owner_history_explicit": True,
        "pre_application_promotion_count": 0,
        "actor_fields_compared": 1296,
        "critic_fields_compared": 348,
        "native_causal_vector_equal": True,
        "source_specific_masked_welford_equal": True,
        "live_replay_hidden_equal": True,
        "live_replay_logits_equal": True,
        "live_replay_old_log_probability_equal": True,
        "behavior_policy_ratio_exactly_one": True,
        "snapshot_assimilation_before_cas": True,
        "branch_observation_before_single_forward": True,
        "question_relevant_output": False,
    }
    assert receipt["measured_process"]["scope"] == "single_process_read_only_cache_and_sentinel_scope"
    assert receipt["measured_process"]["process_tree_measurement_complete"] is True
    accounting = receipt["side_effect_accounting"]
    assert accounting["total_filesystem_effects_claimed_receipt_only"] is True
    assert accounting["requested_root_contains_only_canonical_receipt"] is True
    assert accounting["preexisting_native_cache_read_only"] is True
    cache = accounting["native_cache"]
    assert cache["toolchain_discovery_called"] is False
    assert cache["compiler_called"] is False
    assert cache["cache_write_attempted"] is False
    assert receipt["gap_inventory"]["resource_ceilings"] == {
        "workers_max": 8, "cpu_cores_max": 8, "torch_threads_per_worker": 1,
        "gpu_count": 0, "device": "cpu", "cpu_hours": 40.0, "wall_hours": 10.0,
        "rss_gib": 6.61, "scratch_gib": 1.66, "durable_gib": 0.83, "io_gib": 68.14,
    }
    assert receipt["gap_inventory"] == production_readiness_gap_inventory()
    assert receipt["gap_inventory"]["scientific_holds"] == []
    assert len(receipt["gap_inventory"]["gaps"]) == 10
    assert "PROSPECTIVE_INFERENCE_HOLD" not in receipt["gap_inventory"]["gaps"]
    assert "FINITE_SAMPLE_INFERENCE_LAW_UNRESOLVED" not in receipt["gap_inventory"]["gaps"]
    assert receipt["gap_inventory"]["test_conformance_closed"] == [
        "TEST_PHASED_SIDECAR_ABI_V1",
        "TEST_VALIDATED_RECURRENT_HANDOFF_V1",
        "TEST_TWO_OWNER_ONE_TICK_NATIVE_CAUSAL_54_58_ORACLE",
        "TEST_SOURCE_SPECIFIC_MASKED_PER_DIMENSION_WELFORD",
        "TEST_TYPED_OWNER_HISTORY_LIVE_REPLAY_RATIO_ONE",
    ]
    assert "SOURCE_FACTORED_PHASED_SIDECAR_ABI_AND_BEGIN_TICK_TOKEN_ABSENT" not in receipt["gap_inventory"]["gaps"]
    assert receipt["gap_inventory"]["scientific_inference_object"] == OBJECT_ID
    with pytest.raises(ValueError, match="must be absent"):
        run_preflight(repository_root=Path.cwd(), run_root=run_root)


def test_source_factored_preflight_cold_cache_skips_native_and_writes_only_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cold_cache = tmp_path / "absent-native-cache"
    receipt_root = tmp_path / "cold-cache-receipt"
    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("native toolchain/compile path must not be called")
    monkeypatch.setattr(preflight_module, "_native_cache_root", lambda: cold_cache)
    monkeypatch.setattr(preflight_module._production_backend, "_build_material", forbidden)
    monkeypatch.setattr(preflight_module._production_backend, "_compile", forbidden)
    monkeypatch.setattr(preflight_module._production_backend, "_configure", forbidden)
    monkeypatch.setattr(preflight_module._production_backend, "_toolchain", forbidden)
    monkeypatch.setattr(
        preflight_module._production_backend,
        "require_cpp_batched_production_backend",
        forbidden,
    )
    receipt = run_preflight(repository_root=Path.cwd(), run_root=receipt_root)
    assert receipt["status"] == "NOT_READY"
    assert receipt["side_effect_accounting"]["native_cache"]["status"] == "CACHE_ABSENT"
    assert receipt["preflight_gaps"] == [
        "PREEXISTING_SOURCE_MATCHED_TEST_NATIVE_CACHE_ABSENT",
    ]
    assert receipt["native_probe"]["dynamic_test_clone_executed"] is False
    assert receipt["native_probe"]["accepted_test_clone_branches"] == []
    assert receipt["native_probe"]["test_source_factored_sidecar_abi_present"] is True
    assert receipt["two_owner_one_tick_oracle"]["passed"] is True
    assert receipt["fixed_test_master_used"] is False
    assert receipt["fixed_test_reset_instantiated"] is False
    assert not cold_cache.exists()
    assert {path.name for path in tmp_path.iterdir()} == {receipt_root.name}
    assert {path.name for path in receipt_root.iterdir()} == {"preflight-receipt.json"}
    assert (receipt_root / "preflight-receipt.json").read_bytes() == canonical_json_bytes(receipt)


def test_source_factored_preflight_cold_sidecar_cache_never_compiles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cold_sidecar = tmp_path / "absent-sidecar-cache"
    receipt_root = tmp_path / "cold-sidecar-receipt"

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("sidecar compile/toolchain path must not be called by preflight")

    monkeypatch.setattr(
        preflight_module._source_factored_backend,
        "_sidecar_cache_root",
        lambda: cold_sidecar,
    )
    monkeypatch.setattr(preflight_module._source_factored_backend, "_compile", forbidden)
    monkeypatch.setattr(preflight_module._source_factored_backend, "_vs_installation", forbidden)
    receipt = run_preflight(repository_root=Path.cwd(), run_root=receipt_root)

    cache = receipt["side_effect_accounting"]["source_factored_sidecar_cache"]
    assert cache["status"] == "CACHE_ABSENT"
    assert cache["compile_called"] is False and cache["cache_write_attempted"] is False
    assert receipt["two_owner_one_tick_oracle"] == {
        "schema": "DISH_PSF_R01_TWO_OWNER_ONE_TICK_ORACLE_V1",
        "test_only": True,
        "passed": False,
        "executed": False,
        "status": "CACHE_ABSENT",
        "question_relevant_output": False,
    }
    assert receipt["native_probe"]["test_source_factored_sidecar_abi_present"] is False
    assert "PREEXISTING_CURRENT_TEST_SIDECAR_CACHE_ABSENT" in receipt["preflight_gaps"]
    assert not cold_sidecar.exists()
    assert {path.name for path in receipt_root.iterdir()} == {"preflight-receipt.json"}


def test_source_factored_preflight_pins_loaded_sidecar_across_source_key_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_two_owner_one_tick_pathwise_oracle()  # ensure the current TEST cache exists
    receipt_root = tmp_path / "source-key-race-receipt"
    backend = preflight_module._source_factored_backend
    original_key = backend._source_stat_key()
    calls = 0

    def changing_key() -> str:
        nonlocal calls
        calls += 1
        return original_key if calls == 1 else original_key + "-changed-during-probe"

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("read-only preflight must not compile after a source-key change")

    original_oracle = preflight_module.run_two_owner_one_tick_pathwise_oracle

    def changed_source_oracle() -> object:
        assert backend._source_stat_key() != original_key
        return original_oracle()

    monkeypatch.setattr(backend, "_source_stat_key", changing_key)
    monkeypatch.setattr(backend, "_compile", forbidden)
    monkeypatch.setattr(
        preflight_module,
        "run_two_owner_one_tick_pathwise_oracle",
        changed_source_oracle,
    )
    receipt = run_preflight(repository_root=Path.cwd(), run_root=receipt_root)

    assert calls >= 2
    assert receipt["two_owner_one_tick_oracle"]["passed"] is True
    assert receipt["native_probe"]["test_source_factored_sidecar_abi_present"] is True
    assert receipt["status"] == "NOT_READY" and receipt["passed"] is False


def test_source_factored_runner_refuses_before_run_root_or_master(tmp_path: Path) -> None:
    request = tmp_path / "request.json"; request.write_text(json.dumps(_not_ready_request_header()), encoding="ascii")
    run_root = tmp_path / "scientific-run"
    with pytest.raises(SourceFactoredNotReady, match="NOT READY"):
        refuse_run(repository_root=Path.cwd(), request=request, run_root=run_root)
    assert not run_root.exists()


def test_source_factored_runner_cli_emits_structured_not_ready(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    request = tmp_path / "request.json"; request.write_text(json.dumps(_not_ready_request_header()), encoding="ascii")
    run_root = tmp_path / "scientific-run"
    assert runner_main([
        "--repository-root", str(Path.cwd()), "--request", str(request), "--run-root", str(run_root),
    ]) == 2
    value = json.loads(capsys.readouterr().out)
    assert value["schema"] == "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_RUN_REFUSAL_V2"
    assert value["status"] == "NOT_READY" and value["exit_code"] == 2
    assert value["reason"] == "READINESS_GAPS"
    assert value["master_created"] is False and value["result_created"] is False
    assert value["run_root_preexisting"] is False
    assert value["run_root_created_by_runner"] is False
    assert not run_root.exists()
    request.write_text(json.dumps({**_not_ready_request_header(), "seed": 7}), encoding="ascii")
    assert runner_main([
        "--repository-root", str(Path.cwd()), "--request", str(request), "--run-root", str(run_root),
    ]) == 2
    invalid = json.loads(capsys.readouterr().out)
    assert invalid["status"] == "NOT_READY" and invalid["reason"] == "INVALID_OR_UNAVAILABLE_REQUEST"
    assert "master/seed" in invalid["message"]
    assert not run_root.exists()
    request.write_text(json.dumps({**_not_ready_request_header(), "nested": {"candidate_seed_alias": 7}}), encoding="ascii")
    assert runner_main([
        "--repository-root", str(Path.cwd()), "--request", str(request), "--run-root", str(run_root),
    ]) == 2
    nested = json.loads(capsys.readouterr().out)
    assert nested["reason"] == "INVALID_OR_UNAVAILABLE_REQUEST" and "master/seed" in nested["message"]
    assert not run_root.exists()


@pytest.mark.parametrize("change", [
    {"master_policy": "CALLER_VALUE"},
    {"caller_master_allowed": True},
    {"nested": {"master_policy": RUNNER_MASTER_POLICY}},
    {"nested": {"caller_master_allowed": False}},
])
def test_source_factored_runner_rejects_policy_value_and_nested_aliases(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], change: dict[str, object],
) -> None:
    request_value = {**_not_ready_request_header(), **change}
    request = tmp_path / "request.json"; request.write_text(json.dumps(request_value), encoding="ascii")
    run_root = tmp_path / "scientific-run"
    assert runner_main([
        "--repository-root", str(Path.cwd()), "--request", str(request), "--run-root", str(run_root),
    ]) == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["reason"] == "INVALID_OR_UNAVAILABLE_REQUEST"
    assert receipt["run_root_created_by_runner"] is False
    assert not run_root.exists()


def test_source_factored_runner_structures_request_read_race_and_preexisting_root(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = tmp_path / "request.json"; request.write_text(json.dumps(_not_ready_request_header()), encoding="ascii")
    run_root = tmp_path / "scientific-run"
    original_read_text = Path.read_text
    def race_read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == request.resolve():
            raise OSError("simulated request replacement")
        return original_read_text(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", race_read_text)
    assert runner_main([
        "--repository-root", str(Path.cwd()), "--request", str(request), "--run-root", str(run_root),
    ]) == 2
    raced = json.loads(capsys.readouterr().out)
    assert raced["reason"] == "INVALID_OR_UNAVAILABLE_REQUEST"
    assert "became unavailable" in raced["message"]
    assert raced["run_root_created_by_runner"] is False
    monkeypatch.setattr(Path, "read_text", original_read_text)
    run_root.mkdir()
    assert runner_main([
        "--repository-root", str(Path.cwd()), "--request", str(request), "--run-root", str(run_root),
    ]) == 2
    preexisting = json.loads(capsys.readouterr().out)
    assert preexisting["run_root_preexisting"] is True
    assert preexisting["run_root_present_at_refusal"] is True
    assert preexisting["run_root_created_by_runner"] is False


def test_source_factored_contract_and_thin_wrappers_cannot_route_to_full_r06() -> None:
    assert RUN_MODE == "TEST_ONLY"
    assert PRODUCTION_STATUS == "PRODUCTION_NOT_READY"
    contract = complete_contract()
    assert contract["run_mode"] == "TEST_ONLY" and contract["question_relevant_output"] is False
    assert contract["transaction_branches"] == [
        "RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW",
    ]
    assert production_readiness_gap_inventory()["transfer_replay"] == {
        "name": "TRANSFER_REPLAY", "certificate_only": True,
        "population_arm": False, "confirmatory_test_member": False,
    }
    for path in (
        Path("tools/experiments/run_dish_rbhr_source_factored_preflight.py"),
        Path("tools/experiments/run_dish_rbhr_source_factored_fork.py"),
        Path("experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_source_factored_preflight.py"),
        Path("experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_source_factored_runner.py"),
    ):
        source = path.read_text(encoding="utf-8")
        assert "run_dish_rbhr_r06_full_panel" not in source
        assert "production_full_panel" not in source
        assert "production_real_sham" not in source
        assert "secrets." not in source and "os.urandom" not in source and "token_bytes" not in source
        assert "99_999" not in source and "INFERENCE_RESAMPLES" not in source
        assert "PROSPECTIVE_INFERENCE_HOLD" not in source


def test_legacy_r06_full_panel_cli_refuses_before_loading_lease_or_creating_run_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from tools.experiments import run_dish_rbhr_r06_full_panel as legacy_cli

    lease = tmp_path / "lease.json"
    request = tmp_path / "request.json"
    lease.write_text("{}", encoding="ascii")
    request.write_text("{}", encoding="ascii")
    run_root = tmp_path / "legacy-scientific-run"

    def forbidden_import(_name: str) -> object:
        raise AssertionError("legacy lease loader must not be imported during inference hold")

    monkeypatch.setattr(legacy_cli.importlib, "import_module", forbidden_import)
    monkeypatch.setattr(sys, "argv", [
        "run_dish_rbhr_r06_full_panel",
        "--repository-root", str(Path.cwd()),
        "--lease-loader", "forbidden.module:load",
        "--lease", str(lease),
        "--request", str(request),
        "--run-root", str(run_root),
        "--max-units", "1",
    ])

    assert legacy_cli.main() == 2
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {
        "schema": "DISH_RBHR_R06_FULL_PANEL_HOLD_REFUSAL_V1",
        "status": "NOT_READY",
        "exit_code": 2,
        "reason": "LEGACY_R06_OBJECT_NOT_CURRENT_SOURCE_FACTORED_PATH_ONLY",
        "legacy_object": "DISH_RBHR_R06_FULL_PANEL",
        "current_object": "DISH-BLOCK-CERTIFICATE-PREVALENCE-R02",
        "legacy_24_block_bootstrap_allowed": False,
        "lease_loader_imported": False,
        "run_root_created": False,
        "master_created": False,
        "checkpoint_created": False,
        "result_created": False,
    }
    assert not run_root.exists()
