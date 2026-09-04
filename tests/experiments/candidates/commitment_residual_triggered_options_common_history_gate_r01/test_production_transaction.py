from __future__ import annotations

from dataclasses import dataclass
import base64
import json
import os
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import production
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    Budget,
    Representation,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import preflight as preflight_module
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.analysis import analyze
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import FIXED_CENSUS_METHOD
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run import (
    result_skeleton,
    validate_result,
)


@pytest.fixture(autouse=True)
def _isolated_worker_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(production.PRODUCTION_WORKER_ENV, production.PRODUCTION_WORKER_SENTINEL)


def _passed_preflight(branches: int = 19_295) -> dict[str, object]:
    return {
        "format": "CRTO_COMMON_HISTORY_PROSPECTIVE_PREFLIGHT_V1",
        "object_id": "CRTO-COMMON-HISTORY-GATE-20260830-01",
        "rng_namespace": 2_026_083_001,
        "replicates": list(range(8)),
        "production_capability": production.production_capability(),
        "ready_for_optimizer": True,
        "gates": {"all": {"passed": True, "issues": []}},
        "structural_scan": {"ledger": {
            "actual_common_future_branch_count": branches,
            "pre_result_exact": True,
            "within_ceiling": True,
        }},
    }


def _frozen_withhold_preflight(branches: int = 19_295) -> dict[str, object]:
    report = _passed_preflight(branches)
    report["ready_for_optimizer"] = False
    report["gates"] = {
        name: {"passed": True, "issues": []}
        for name in production._PREFLIGHT_GATE_KEYS
        if name != "long_production_efficiency_review"
    }
    report["gates"]["long_production_efficiency_review"] = {
        "passed": False,
        "issues": [production._LONG_PRODUCTION_WITHHOLD_ISSUE],
    }
    return report


def test_capability_declaration_is_exact_and_torch_free() -> None:
    assert production.PRODUCTION_CAPABILITY_VERSION == "CRTO_SINGLE_PASS_PRODUCTION_V1"
    assert production.production_capability() == {
        "version": "CRTO_SINGLE_PASS_PRODUCTION_V1",
        "single_pass_population_traversal": True,
        "second_launch_admission_before_science": True,
        "raw_long_k8_staged_gate": True,
        "residual_evaluation_only_after_competence": True,
        "validated_create_only_publication": True,
    }


def test_direct_in_process_thread_environment_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in production._THREAD_ENVIRONMENT:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    with pytest.raises(RuntimeError, match="isolated one-thread CPU worker"):
        production._configure_one_thread_environment()
    for name in production._THREAD_ENVIRONMENT:
        monkeypatch.setenv(name, "1")
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    production._configure_one_thread_environment()


def test_second_admission_precedes_thread_binding_import_and_scientific_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    memory = {
        "passed": True,
        "available_physical_bytes": 5 * 1024**3,
        "effective_available_bytes": 5 * 1024**3,
    }
    run = {"memory_floor_pass": True, "memory_safe": True}

    def admit(path: Path):
        events.append("second-memory")
        assert not (tmp_path / "scientific-root").exists()
        return memory

    def assess(path: Path, *, run_id: str):
        events.append("second-assess-run")
        assert run_id.endswith("_launch")
        assert not (tmp_path / "scientific-root").exists()
        return run

    monkeypatch.setattr(preflight_module, "create_shared_resource_receipt", admit)
    monkeypatch.setattr(preflight_module, "create_shared_run_assessment", assess)
    monkeypatch.setattr(
        production, "_configure_one_thread_environment", lambda: events.append("thread-bind")
    )
    monkeypatch.setattr(production, "_load_components", lambda: events.append("imports") or object())

    def publish(output: Path, result: Path, *, transaction: object):
        events.append("root")
        assert events == ["second-memory", "second-assess-run", "thread-bind", "imports", "root"]
        return {"status": "TEST_ONLY"}

    monkeypatch.setattr(production, "_publish_create_only", publish)
    value = production._execute_admitted_pipeline(
        output_root=tmp_path / "scientific-root",
        result_path=tmp_path / "result.json",
        preflight=_passed_preflight(),
        launch_resource_receipt_path=tmp_path / "memory.json",
        launch_run_resource_receipt_path=tmp_path / "assess.json",
        expected_branches=19_295,
    )
    assert value == {"status": "TEST_ONLY"}


def test_nonpassing_first_preflight_creates_no_second_receipt_or_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched: list[Path] = []
    monkeypatch.setattr(
        preflight_module, "create_shared_resource_receipt", lambda path: touched.append(path)
    )
    report = _frozen_withhold_preflight()
    with pytest.raises(PermissionError, match="WITHHOLD_LONG_PRODUCTION"):
        production.execute_fresh_pipeline(
            output_root=tmp_path / "root",
            result_path=tmp_path / "result.json",
            preflight=report,
            launch_resource_receipt_path=tmp_path / "memory.json",
            launch_run_resource_receipt_path=tmp_path / "assess.json",
        )
    assert touched == []
    assert not (tmp_path / "root").exists()


def test_stale_passing_capability_receipt_is_rejected_before_second_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _frozen_withhold_preflight()
    touched: list[Path] = []
    monkeypatch.setattr(
        preflight_module,
        "create_shared_resource_receipt",
        lambda path: touched.append(path),
    )
    monkeypatch.setattr(
        production,
        "production_capability",
        lambda: {**report["production_capability"], "raw_long_k8_staged_gate": False},
    )
    with pytest.raises(PermissionError, match="capability"):
        production.execute_fresh_pipeline(
            output_root=tmp_path / "root",
            result_path=tmp_path / "result.json",
            preflight=report,
            launch_resource_receipt_path=tmp_path / "memory.json",
            launch_run_resource_receipt_path=tmp_path / "assess.json",
        )
    assert touched == []


def test_missing_gate_and_forged_all_pass_are_withheld_before_second_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched: list[Path] = []
    monkeypatch.setattr(
        preflight_module,
        "create_shared_resource_receipt",
        lambda path: touched.append(path),
    )
    missing = _frozen_withhold_preflight()
    del missing["gates"]["runtime_envelope"]
    with pytest.raises(PermissionError, match="WITHHOLD_LONG_PRODUCTION"):
        production.execute_fresh_pipeline(
            output_root=tmp_path / "missing-root",
            result_path=tmp_path / "missing.json",
            preflight=missing,
            launch_resource_receipt_path=tmp_path / "missing-memory.json",
            launch_run_resource_receipt_path=tmp_path / "missing-assess.json",
        )
    forged = _frozen_withhold_preflight()
    forged["ready_for_optimizer"] = True
    forged["gates"]["long_production_efficiency_review"] = {
        "passed": True, "issues": [],
    }
    with pytest.raises(PermissionError, match="WITHHOLD_LONG_PRODUCTION"):
        production.execute_fresh_pipeline(
            output_root=tmp_path / "forged-root",
            result_path=tmp_path / "forged.json",
            preflight=forged,
            launch_resource_receipt_path=tmp_path / "forged-memory.json",
            launch_run_resource_receipt_path=tmp_path / "forged-assess.json",
        )
    assert touched == []


def test_direct_call_without_worker_marker_creates_no_second_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(production.PRODUCTION_WORKER_ENV, raising=False)
    touched: list[Path] = []
    monkeypatch.setattr(
        preflight_module,
        "create_shared_resource_receipt",
        lambda path: touched.append(path),
    )
    with pytest.raises(PermissionError, match="isolated worker"):
        production.execute_fresh_pipeline(
            output_root=tmp_path / "root",
            result_path=tmp_path / "result.json",
            preflight=_passed_preflight(),
            launch_resource_receipt_path=tmp_path / "memory.json",
            launch_run_resource_receipt_path=tmp_path / "assess.json",
        )
    assert touched == []


@dataclass(frozen=True)
class _Key:
    regime: str
    text: str


@dataclass(frozen=True)
class _Row:
    key: _Key


class _Packets:
    def __init__(self, row_keys, values):
        self.row_keys = tuple(row_keys)
        self.values = np.asarray(values, dtype=np.float32)


def _states() -> list[production._SlotState]:
    states = []
    for replicate in range(8):
        rows = tuple(
            _Row(_Key(regime, f"{replicate}/{regime}/{index}"))
            for regime in ("K8", "K16", "K4_TO_16", "K16_TO_4")
            for index in range(2)
        )
        packets = _Packets(
            tuple(row.key.text for row in rows), np.zeros((len(rows), 52), dtype=np.float32)
        )
        paths = {
            representation: SimpleNamespace(checkpoints={budget: f"{replicate}/{representation}/{budget}" for budget in Budget})
            for representation in Representation
        }
        states.append(production._SlotState(
            replicate=replicate,
            predictor_audit=object(),
            calibration_table=object(),
            calibration_report={},
            training_rows=(),
            evaluation_rows=rows,
            paths=paths,
            evaluation_packets={representation: packets for representation in Representation},
        ))
    return states


@pytest.mark.parametrize("competence_status,expected_calls,expected_cells", [
    ("STOP", 8, 1),
    ("NONIDENTIFYING", 8, 1),
    ("PASS", 56, 6),
])
def test_raw_long_k8_gate_precedes_every_residual_or_short_evaluation(
    competence_status: str, expected_calls: int, expected_cells: int,
) -> None:
    calls: list[tuple[Representation, Budget, tuple[str, ...]]] = []
    analyzed: list[object] = []

    def evaluate(model, rows, packets, *, representation, budget, target_regimes=("K16", "K4_TO_16", "K16_TO_4")):
        calls.append((representation, budget, tuple(target_regimes)))
        return SimpleNamespace(representation=representation, budget=budget)

    def assess(values):
        assert len(values) == 8
        assert calls == [(Representation.RAW, Budget.LONG, ("K8",))] * 8
        return {"status": competence_status}

    def analyze(value):
        analyzed.append(value)
        return {"status": "NONIDENTIFYING"}

    components = SimpleNamespace(
        Representation=Representation,
        Budget=Budget,
        evaluate_checkpoint=evaluate,
        assess_raw_long_competence=assess,
        analyze=analyze,
    )
    summaries, competence, _ = production._route_staged_evaluation(_states(), components)
    assert competence["status"] == competence_status
    assert len(calls) == expected_calls
    assert all(len(slot) == expected_cells for slot in summaries)
    if competence_status != "PASS":
        assert all(
            set(slot) == {(Representation.RAW, Budget.LONG)} for slot in summaries
        )
        assert all(call[0] is Representation.RAW for call in calls)


def test_each_assigned_tape_is_traversed_once() -> None:
    calls: list[int] = []

    def materialize(tape, **kwargs):
        calls.append(tape)
        return SimpleNamespace(predictor_examples=(), common_history_row=None)

    ledger = SimpleNamespace(check_limits=lambda: None)
    components = SimpleNamespace(materialize_episode_observables=materialize)
    examples, rows = production._collect_batch(
        (1, 2, 3), replicate=0, split="TRAIN", forecast=object(),
        collect_common_history=True, ledger=ledger, components=components,
    )
    assert calls == [1, 2, 3]
    assert examples == () and rows == ()


def test_derangement_plan_serialization_waits_for_competence_pass() -> None:
    calls: list[str] = []

    class Plan:
        def __init__(self, label: str):
            self.label = label

        def to_json(self):
            calls.append(self.label)
            return {"label": self.label}

    views = SimpleNamespace(
        raw_dataset="raw", true_residual_dataset="true",
    )
    plans = iter((Plan("TRAIN"), Plan("EVALUATION")))
    components = SimpleNamespace(
        construct_packet_views=lambda rows, table: views,
        build_derangement=lambda rows, packets, *, replicate: ("deranged", next(plans)),
        Representation=Representation,
        train_matched_paths=lambda *args, **kwargs: {},
    )
    state = production._SlotState(0, object(), object(), {}, (), ())
    production._prepare_matched_paths(
        state, components, SimpleNamespace(check_limits=lambda: None),
    )
    assert calls == []
    assert production._serialize_derangements(state) == {
        "TRAIN": {"label": "TRAIN"},
        "EVALUATION": {"label": "EVALUATION"},
    }
    assert calls == ["TRAIN", "EVALUATION"]


def _stop_payload() -> dict[str, object]:
    cells = [
        {
            "slot": slot,
            "stratum": stratum,
            "row_count": 8,
            "raw_mean_regret": 0.02,
            "script_mean_regret": 0.01,
            "raw_minus_script": 0.01,
        }
        for slot in range(8)
        for stratum in ("KEEP_MATERIAL", "REPLAN_MATERIAL")
    ]
    analysis = {
        "status": "NONIDENTIFYING",
        "interpretation": "STOP_RAW_LONG_INCOMPETENT",
        "failures": ["RAW-LONG competence failed"],
        "effect_hulls": [],
        "trajectory_hulls": [],
        "raw_long_competence": {
            "cells": cells,
            "c_raw": 0.02,
            "max_raw_minus_script": 0.01,
            "script_is_qualification_gate": False,
        },
        "close_budget_descriptions": None,
        "inference_method": FIXED_CENSUS_METHOD,
        "target_population": "FIXED_ADDRESSES_0_TO_7_NO_SEED_SUPERPOPULATION",
    }
    replicates = [
        {
            "replicate": slot,
            "evaluations": [{
                "replicate": slot,
                "representation": "RAW",
                "budget": "LONG",
                "regime_mean_regret": {"K8": 0.02},
                "row_count_by_regime": {"K8": 64},
            }],
        }
        for slot in range(8)
    ]
    return result_skeleton(
        analysis=analysis,
        replicates=replicates,
        resource={
            "memory_floor_pass": True,
            "available_physical_bytes": 5 * 1024**3,
            "effective_available_bytes": 5 * 1024**3,
        },
        ledger={
            "formula": "8*1088*256 + 16*actual_common_future_branch_count",
            "charged_full_tape_primitive_team_steps": 2_228_224,
            "common_future_steps_per_actual_branch": 16,
            "expected_common_future_branch_count": 1,
            "actual_common_future_branch_count": 1,
            "actual_common_future_steps": 16,
            "pre_result_exact": True,
            "within_ceiling": True,
            "actual_total_steps": 2_228_240,
            "ceiling": 2_596_864,
        },
        runtime={
            "workers": 1, "threads_per_worker": 1,
            "peak_rss_bytes": 1, "wall_seconds": 1.0,
        },
        admission={name: False for name in (
            "disjoint_panels", "matched_inputs", "derangement_valid", "common_future_valid",
            "raw_long_competent", "resource_valid", "ledger_valid", "runtime_valid",
            "calibration_valid", "k8_competence_support_valid",
        )},
    )


def test_stop_result_rejects_derangement_or_non_raw_long_evaluation_tampering() -> None:
    payload = _stop_payload()
    validate_result(payload)
    payload["replicates"][0]["derangements"] = {"TRAIN": {}}
    with pytest.raises(ValueError, match="derangement"):
        validate_result(payload)
    payload = _stop_payload()
    payload["replicates"][0]["evaluations"].append({
        "replicate": 0,
        "representation": "CALIBRATED_DERANGEMENT",
        "budget": "LONG",
        "regime_mean_regret": {"K8": 0.0},
        "row_count_by_regime": {"K8": 64},
    })
    with pytest.raises(ValueError, match="RAW-LONG K8"):
        validate_result(payload)


def test_support_failure_is_data_not_an_exception() -> None:
    evaluation = SimpleNamespace(value="EVALUATION")
    components = SimpleNamespace(Split=SimpleNamespace(EVALUATION=evaluation))
    retained, failures = production._retain_supported_rows(
        (), split=components.Split.EVALUATION, components=components,
    )
    assert retained == ()
    assert failures == ("EVALUATION retained no common-history rows",)


def test_support_failure_publishes_valid_nonidentifying_without_training_or_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    support_failure = "slot 0 EVALUATION/K8 retained 47/64 (<48)"
    states = [
        production._SlotState(
            replicate=replicate,
            predictor_audit=SimpleNamespace(examples=1, updates=400, processed_examples=102_400),
            calibration_table=object(),
            calibration_report={"diagnostics": {"replicate": replicate}},
            training_rows=(),
            evaluation_rows=(),
            support_failures=(support_failure,) if replicate == 0 else (),
        )
        for replicate in range(8)
    ]

    class Ledger:
        def charge_base_population(self, name, count):
            pytest.fail("empty fake population ledger cannot be charged")

        def assert_complete(self):
            return None

        def snapshot(self):
            return SimpleNamespace(
                common_future_branches=1,
                common_future_steps=16,
                actual_total_steps=2_228_240,
                ceiling=2_596_864,
                charged_base_steps_by_population={},
                physically_executed_base_steps_by_population={},
                workers=1,
                threads_per_worker=1,
                peak_rss_bytes=1,
                wall_seconds=1.0,
            )

    monkeypatch.setattr(production, "_collect_slot", lambda replicate, **kwargs: states[replicate])
    monkeypatch.setattr(
        production,
        "_prepare_matched_paths",
        lambda *args, **kwargs: pytest.fail("support failure reached matched training"),
    )
    monkeypatch.setattr(
        production,
        "_route_staged_evaluation",
        lambda *args, **kwargs: pytest.fail("support failure reached gate evaluation"),
    )
    components = SimpleNamespace(
        PrimitiveTeamStepLedger=lambda **kwargs: Ledger(),
        BASE_POPULATION_EPISODES={},
        REPLICATES=tuple(range(8)),
        assess_calibration=lambda reports: {"passed": True, "issues": []},
        analyze=analyze,
        result_skeleton=result_skeleton,
        validate_result=validate_result,
    )
    payload = production._run_scientific_transaction(
        tmp_path,
        preflight=_passed_preflight(branches=1),
        launch_resource={
            "passed": True,
            "available_physical_bytes": 5 * 1024**3,
            "effective_available_bytes": 5 * 1024**3,
        },
        launch_run_resource={"memory_floor_pass": True, "memory_safe": True},
        expected_branches=1,
        components=components,
    )
    validate_result(payload)
    assert payload["status"] == "NONIDENTIFYING"
    assert payload["analysis"]["interpretation"] == "UNRESOLVED"
    assert payload["analysis"]["effect_hulls"] == []
    assert payload["analysis"]["trajectory_hulls"] == []
    assert payload["replicates"][0]["support_failures"] == [support_failure]


def test_terminal_runtime_snapshot_is_after_final_result_fsync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    class Ledger:
        def check_limits(self):
            events.append("check")

        def snapshot(self):
            events.append("snapshot")
            return SimpleNamespace(
                workers=1, threads_per_worker=1, peak_rss_bytes=1, wall_seconds=1.0,
            )

    monkeypatch.setattr(os, "fsync", lambda descriptor: events.append("fsync"))
    output, result = tmp_path / "output", tmp_path / "result.json"
    payload = production._publish_create_only(
        output,
        result,
        transaction=lambda stage: production._TransactionPayload({"value": 1}, Ledger()),
    )
    assert payload == {"value": 1}
    assert events[:events.index("snapshot")].count("fsync") == 2
    terminal = json.loads((output / "terminal-runtime.json").read_text(encoding="utf-8"))
    assert terminal["boundary"] == "AFTER_FINAL_RESULT_ENCODE_AND_FSYNC_BEFORE_PUBLICATION"
    assert result.exists()


def test_serialization_failure_exposes_neither_publication_target(tmp_path: Path) -> None:
    output, result = tmp_path / "output", tmp_path / "result.json"

    def transaction(stage: Path):
        (stage / "private-work").write_text("not published", encoding="utf-8")
        return {"not_json": object()}

    with pytest.raises(TypeError):
        production._publish_create_only(output, result, transaction=transaction)
    assert not output.exists() and not result.exists()


def test_terminal_runtime_failure_after_result_fsync_exposes_neither_target(tmp_path: Path) -> None:
    class Ledger:
        def check_limits(self):
            raise RuntimeError("wall ceiling crossed during final result fsync")

        def snapshot(self):
            pytest.fail("failing terminal check cannot produce a receipt")

    output, result = tmp_path / "output", tmp_path / "result.json"
    with pytest.raises(RuntimeError, match="wall ceiling"):
        production._publish_create_only(
            output,
            result,
            transaction=lambda stage: production._TransactionPayload({"value": 1}, Ledger()),
        )
    assert not output.exists() and not result.exists()




def test_real_calibration_canonical_record_is_json_serializable_without_hash() -> None:
    raw = bytes(range(32))
    encoded = production._jsonable({
        "table_record": ("<f4", (8, 1), raw),
    })

    text = json.dumps(encoded, allow_nan=False, sort_keys=True)
    restored = json.loads(text)["table_record"]
    assert restored[0] == "<f4"
    assert restored[1] == [8, 1]
    assert restored[2]["encoding"] == "base64"
    assert base64.b64decode(restored[2]["data"]) == raw
