from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import mock

import pytest


ROOT = Path(__file__).resolve().parents[4]
DRIVER = ROOT / "tools" / "benchmarks" / "measure_risp_g_init_r01_eval_cost.py"
MANIFEST = (
    ROOT
    / "experiments"
    / "candidates"
    / "renewal_indexed_score_plasticity"
    / "RISP_G_INIT_REACH_R01_EVAL_MEASUREMENT_COMPONENT_MANIFEST_20260823.json"
)


def _load_driver():
    spec = importlib.util.spec_from_file_location("risp_eval_measurement_component_test", DRIVER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_import_is_inert_and_component_is_unarmed() -> None:
    before = set(sys.modules)
    module = _load_driver()
    newly_loaded = set(sys.modules) - before
    assert "g_init_r01_experiment" not in newly_loaded
    assert "g_init_r01_native_backend" not in newly_loaded
    assert "torch" not in newly_loaded
    assert "envs.native.production_backend" not in newly_loaded
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["armed"] is False
    assert manifest["measurement_authority"] is False
    assert callable(module.run_authorized_measurement)


def test_manifest_retains_exact_twenty_strata_forty_fixtures_and_caps() -> None:
    module = _load_driver()
    manifest, digest = module.load_component_manifest()
    assert len(digest) == 64
    assert len(manifest["strata"]) == 20
    assert sum(len(row["fixture_seeds"]) for row in manifest["strata"]) == 40
    assert {(row["schedule_id"], row["cell"]) for row in manifest["strata"]} == {
        (schedule, cell) for schedule in range(5) for cell in module.CELLS
    }
    assert manifest["grouped_eval"]["episode_groups"] == [[0, 16], [16, 32], [32, 48], [48, 64]]
    assert manifest["limits"] == {
        "maximum_batches": 20,
        "maximum_fixture_units": 40,
        "maximum_incremental_cpu_seconds": 28800,
        "maximum_foreground_wall_seconds": 13800,
        "workers": 2,
        "cpu_cores": 2,
        "gpu": False,
        "per_worker_rss_limit_bytes": 1073741824,
        "process_group_rss_limit_bytes": 2684354560,
        "scratch_limit_bytes": 1073741824,
        "durable_output_limit_bytes": 67108864,
        "dispatches": 1,
        "automatic_relaunch": False,
    }


def test_protected_current_bytes_match_frozen_hashes_without_loading_payloads() -> None:
    module = _load_driver()
    manifest, _ = module.load_component_manifest()
    for relative, expected in manifest["protected_files"].items():
        if relative != "envs/native/production_backend.py":
            assert module._sha256(ROOT / relative) == expected
    native = manifest["accepted_native"]
    assert module._sha256(Path(native["artifact_path"])) == (
        "3b20ba9e5a55c2cc0df9ad5582bb957155931856fc2e643422104ca8d56c7709"
    )
    registry = ROOT / "envs" / "native" / "production_backend.py"
    frozen_registry_hash = manifest["protected_files"]["envs/native/production_backend.py"]
    if module._sha256(registry) == frozen_registry_hash:
        assert module._protected_snapshot(manifest)["envs/native/production_backend.py"]["sha256"] == frozen_registry_hash
    else:
        with pytest.raises(module.MeasurementRefused, match="envs/native/production_backend.py"):
            module._protected_snapshot(manifest)


def test_authorization_is_closed_separate_and_path_bound() -> None:
    module = _load_driver()
    manifest, component_sha = module.load_component_manifest()
    output = (ROOT / "temp" / "risp_eval_measurement_authorized_output.json").resolve()
    authorization = {
        "schema": module.AUTHORIZATION_SCHEMA,
        "authorization_id": "a" * 64,
        "authorized": True,
        "authorized_activity": "ONE_RESULT_BLIND_GROUPED_EVAL_MEASUREMENT",
        "component_manifest_sha256": component_sha,
        "output_path": str(output),
        "dispatches": 1,
        "automatic_relaunch": False,
        "limits": manifest["limits"],
    }
    module.validate_authorization(
        authorization, component_sha256=component_sha,
        output_path=output, limits=manifest["limits"],
    )
    for forbidden in (
        "coordinate_path", "frontier_root", "checkpoint_path", "result_path",
        "partial_path", "unit_path", "commit_path", "receipt_path",
    ):
        rejected = dict(authorization)
        rejected[forbidden] = "x"
        with pytest.raises(module.MeasurementRefused):
            module.validate_authorization(
                rejected, component_sha256=component_sha,
                output_path=output, limits=manifest["limits"],
            )
    wrong_schema = dict(authorization)
    wrong_schema["extra"] = "RISP-G-INIT-REACH-R01-EVALUATION-UNIT-20260821-01"
    with pytest.raises(module.MeasurementRefused):
        module.validate_authorization(
            wrong_schema, component_sha256=component_sha,
            output_path=output, limits=manifest["limits"],
        )


def test_worker_payloads_are_path_free_test_only_and_nonregistered() -> None:
    module = _load_driver()
    manifest, component_sha = module.load_component_manifest()
    payloads = module.worker_payloads_for_stratum(manifest, manifest["strata"][0], component_sha)
    assert len(payloads) == 2
    assert [payload["lane"] for payload in payloads] == [0, 1]
    for payload in payloads:
        assert payload["namespace_class"] == "TEST_ONLY"
        assert payload["fixture_seed"] not in range(16)
        assert not any("path" in key or "frontier" in key or "checkpoint" in key for key in payload)
        assert not any(isinstance(value, Path) for value in payload.values())


class _FakeAudit:
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}


class _FakeSummary:
    def __init__(self) -> None:
        self.decisions = 0
        self.updates = 0
        self.direct_tv_max_residual = 0.0
        self.tv_values: list[float] = []
        self.delta_values: list[float] = []


def test_grouped_fixture_calls_only_exact_four_episode_groups() -> None:
    module = _load_driver()
    calls: list[tuple[int, ...]] = []

    def grouped(**kwargs):
        import torch
        assert torch.is_grad_enabled() is False
        episodes = tuple(kwargs["episodes"])
        calls.append(episodes)
        summary = kwargs["summary"]
        audit = kwargs["audit"]
        summary.decisions += len(episodes) * 2
        audit.calls["INIT_SECTOR"] = audit.calls.get("INIT_SECTOR", 0) + len(episodes) * 2
        for name in ("ACTION", "MOTION", "ACK"):
            audit.calls[name] = audit.calls.get(name, 0) + len(episodes) * 2

    fake = SimpleNamespace(
        _cell_parts=lambda cell: (None, cell),
        SamplerAudit=_FakeAudit,
        EvalSummary=_FakeSummary,
        schedule_rows=lambda schedule_id: ((0, 4, True),),
        _evaluate_episode_group_native=grouped,
    )
    payload = {
        "fixture_seed": 100,
        "schedule_id": 0,
        "cell": "UNIFORM",
        "lane": 0,
        "foreground_deadline_monotonic": module.time.perf_counter() + 60.0,
        "per_worker_rss_limit_bytes": 2**63,
    }
    digest = module._run_grouped_fixture({"experiment": fake}, payload, None)
    assert len(digest) == 64
    assert calls == [tuple(range(start, stop)) for start, stop in module.GROUPS]


def test_nested_timer_is_exclusive_and_closes_exactly() -> None:
    module = _load_driver()
    ledger = module.StageLedger()
    with mock.patch.object(module, "_rss_bytes", return_value=100), mock.patch.object(
        module.time, "perf_counter_ns", side_effect=[0, 10, 30, 50]
    ), mock.patch.object(module.time, "process_time_ns", side_effect=[0, 10, 25, 45]):
        with ledger.measure("PYTHON_INTERACTIVE_EVENT_ADAPTER"):
            with ledger.measure("EXACT_INTERVAL_AND_ADDRESSING"):
                pass
    assert ledger.wall_ns["EXACT_INTERVAL_AND_ADDRESSING"] == 20
    assert ledger.wall_ns["PYTHON_INTERACTIVE_EVENT_ADAPTER"] == 30
    assert ledger.cpu_ns["EXACT_INTERVAL_AND_ADDRESSING"] == 15
    assert ledger.cpu_ns["PYTHON_INTERACTIVE_EVENT_ADAPTER"] == 30
    assert ledger.rss_max_bytes["EXACT_INTERVAL_AND_ADDRESSING"] == 100


def test_projection_uses_only_uninstrumented_pass_a() -> None:
    module = _load_driver()
    batch = {
        "pass_a_batch": {"wall_ns": 100, "parent_cpu_ns": 5},
        "fixtures": [
            {"pass_a": {"worker_cpu_ns": 20, "worker_wall_ns": 80}, "pass_b": {"worker_cpu_ns": 9999}},
            {"pass_a": {"worker_cpu_ns": 30, "worker_wall_ns": 90}, "pass_b": {"worker_cpu_ns": 8888}},
        ],
    }
    baseline = module._projection([batch], 8)
    batch["fixtures"][0]["pass_b"]["worker_cpu_ns"] = 1
    batch["fixtures"][1]["pass_b"]["worker_cpu_ns"] = 2
    assert module._projection([batch], 8) == baseline
    assert baseline["cpu_ns_central"] == 8 * (5 + 20 + 30)
    assert baseline["wall_ns_central"] == 8 * 100


def test_output_redaction_rejects_payload_values_but_allows_resource_facts() -> None:
    module = _load_driver()
    module._assert_redacted_output({"cpu_ns": 4, "structural_equivalence_sha256": "b" * 64})
    for key in ("actions", "ack_values", "reward", "belief_rows", "offline", "qualification", "tensor", "packet"):
        with pytest.raises(module.MeasurementRefused):
            module._assert_redacted_output({key: [1]})


def test_driver_has_exact_spawn_two_worker_and_no_compile_implementation() -> None:
    module = _load_driver()
    source = DRIVER.read_text(encoding="utf-8")
    batch_source = module.inspect.getsource(module._run_batch)
    runtime_source = module.inspect.getsource(module._load_runtime)
    assert 'multiprocessing.get_context("spawn")' in batch_source
    assert "ProcessPoolExecutor(max_workers=2" in batch_source
    assert "native._compiled_path = strict_compiled_path" in runtime_source
    assert "cache.mkdir" not in source
    assert "subprocess" not in source


def test_existing_output_refuses_relaunch_before_any_runtime_load() -> None:
    module = _load_driver()
    output = MANIFEST
    with mock.patch.object(module, "_load_runtime") as runtime:
        with pytest.raises(module.MeasurementRefused, match="relaunch"):
            module.run_authorized_measurement(ROOT / "temp" / "absent-auth.json", output)
    runtime.assert_not_called()
