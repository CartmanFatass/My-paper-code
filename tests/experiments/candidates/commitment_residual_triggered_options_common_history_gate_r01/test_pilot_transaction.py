import numpy as np
import ast
import json
from pathlib import Path
import subprocess
import sys

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.config import (
    PILOT_LAUNCH_RUN_ID,
    RNG_NAMESPACE,
    counter_seed,
    counter_seed_for_namespace,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.pilot import (
    PILOT_CONFIG,
    assess_pilot_structural_scan,
    assess_pilot_competence,
    run_raw_only_pilot,
    retain_pilot_supported_rows,
    publish_pilot_result_create_only,
    route_pilot_execution_evidence,
    execute_pilot_slots_two_phase,
    pilot_material_stratum_support_failures,
    PilotSlotMaterialization,
    PilotWorkLedger,
    validate_pilot_result,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    Budget,
    Representation,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.evaluation import (
    EvaluationSummary,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import (
    BoundaryScanRow,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.ledger import (
    ResourceLimitExceeded,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    PanelRow,
    RowKey,
    Split,
)


def test_pilot_registration_is_fixed_and_rng_disjoint_from_confirmation() -> None:
    PILOT_CONFIG.validate()
    assert PILOT_CONFIG.object_id == "CRTO-COMMON-HISTORY-RAW-PILOT-20260831-01"
    assert PILOT_CONFIG.rng_namespace == 2026083191
    assert PILOT_CONFIG.slots == (0, 1)
    assert PILOT_CONFIG.representation == "RAW"
    assert PILOT_CONFIG.checkpoint == "LONG"
    assert PILOT_CONFIG.updates == 2048
    assert PILOT_CONFIG.evaluation_regimes == ("K8",)
    assert PILOT_CONFIG.evaluation_episodes_per_slot == 64
    assert PILOT_CONFIG.feasibility_only is True
    assert PILOT_CONFIG.rng_namespace != RNG_NAMESPACE
    assert counter_seed_for_namespace(
        PILOT_CONFIG.rng_namespace, "panel_tape", 0, 3, 1,
    ) != counter_seed("panel_tape", 0, 3, 1)


def test_pilot_launcher_import_is_torch_free_before_worker_admission() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import experiments.candidates."
                "commitment_residual_triggered_options_common_history_gate_r01.pilot; "
                "assert 'torch' not in sys.modules; "
                "assert not any(k.endswith('.training') or k.endswith('.evaluation') "
                "or k.endswith('.packets') or k.endswith('.models') for k in sys.modules)"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr

    import experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.pilot as pilot_module
    tree = ast.parse(Path(pilot_module.__file__).read_text(encoding="utf-8"))
    forbidden = {"torch", "training", "evaluation", "packets", "models"}
    top_level = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level.extend(alias.name.rsplit(".", 1)[-1] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level.append(node.module.rsplit(".", 1)[-1])
    assert forbidden.isdisjoint(top_level)


def _raw_long_summary(
    slot: int,
    *,
    keep_count: int = 8,
    replan_count: int = 8,
    keep_regret: float = 0.01,
    replan_regret: float = 0.009,
) -> EvaluationSummary:
    counts = {"KEEP_MATERIAL": keep_count, "REPLAN_MATERIAL": replan_count}
    regrets = {"KEEP_MATERIAL": keep_regret, "REPLAN_MATERIAL": replan_regret}
    scripts = {"KEEP_MATERIAL": 0.02, "REPLAN_MATERIAL": 0.02}
    return EvaluationSummary(
        replicate=slot,
        representation=Representation.RAW,
        budget=Budget.LONG,
        regime_mean_regret={"K8": 0.0095},
        target_equal_weight_regret=0.0095,
        row_count_by_regime={"K8": 64},
        keep_optimal_count=32,
        zero_regret_oracle_count=32,
        logged_action_count=32,
        logged_scripted_regret_by_regime={"K8": 0.02},
        oracle_regret_max_abs=0.0,
        keep_optimal_by_regime={"K8": 32},
        material_stratum_count_by_regime={"K8": counts},
        mean_regret_by_regime_and_material_stratum={"K8": regrets},
        logged_scripted_mean_regret_by_regime_and_material_stratum={"K8": scripts},
    )


def _serialized_summary(summary: EvaluationSummary) -> dict[str, object]:
    return {
        "slot": summary.replicate,
        "representation": summary.representation.value,
        "checkpoint": summary.budget.value,
        "regime_mean_regret": dict(summary.regime_mean_regret),
        "row_count_by_regime": dict(summary.row_count_by_regime),
        "material_stratum_count_by_regime": {
            regime: dict(values)
            for regime, values in summary.material_stratum_count_by_regime.items()
        },
        "mean_regret_by_regime_and_material_stratum": {
            regime: dict(values)
            for regime, values in summary.mean_regret_by_regime_and_material_stratum.items()
        },
        "logged_scripted_mean_regret_by_regime_and_material_stratum": {
            regime: dict(values)
            for regime, values
            in summary.logged_scripted_mean_regret_by_regime_and_material_stratum.items()
        },
    }


def _memory_receipt() -> dict[str, object]:
    return {
        "schema_version": 1,
        "minimum_available_bytes": 4 * 1024**3,
        "available_physical_bytes": 8 * 1024**3,
        "effective_available_bytes": 8 * 1024**3,
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "passed": True,
        "failure_reasons": [],
    }


def _run_receipt() -> dict[str, object]:
    return {
        "workers": 1,
        "threads_per_worker": 1,
        "minimum_available_bytes": 4 * 1024**3,
        "estimate": {"wall_seconds": 7200.0, "peak_memory_gib": 2.0},
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "memory_floor_pass": True,
        "memory_safe": True,
    }


def _material_count_records(
    slot0: tuple[int, int] = (8, 8),
    slot1: tuple[int, int] = (8, 8),
    *,
    observed: bool = True,
) -> list[dict[str, object]]:
    return [
        {
            "slot": slot,
            "stratum": stratum,
            "observed": observed,
            "row_count": counts[slot][index] if observed else None,
        }
        for slot in (0, 1)
        for index, stratum in enumerate(("KEEP_MATERIAL", "REPLAN_MATERIAL"))
        for counts in ({0: slot0, 1: slot1},)
    ]


def test_pilot_competence_requires_all_four_fixed_slot_stratum_cells() -> None:
    feasible = assess_pilot_competence((_raw_long_summary(0), _raw_long_summary(1)))
    assert feasible["disposition"] == "PILOT_FEASIBLE"
    assert feasible["claim_ceiling"] == "TWO_SLOT_RAW_LONG_DEVELOPMENT_FEASIBILITY_ONLY"
    assert [(cell["slot"], cell["stratum"]) for cell in feasible["cells"]] == [
        (0, "KEEP_MATERIAL"), (0, "REPLAN_MATERIAL"),
        (1, "KEEP_MATERIAL"), (1, "REPLAN_MATERIAL"),
    ]
    assert all(cell["raw_mean_regret"] <= 0.01 for cell in feasible["cells"])

    unsupported = assess_pilot_competence((
        _raw_long_summary(0, keep_count=7), _raw_long_summary(1),
    ))
    assert unsupported["disposition"] == "NONIDENTIFYING_PILOT_K8_SUPPORT"
    assert unsupported["cells"] == []

    incompetent = assess_pilot_competence((
        _raw_long_summary(0), _raw_long_summary(1, replan_regret=0.0100001),
    ))
    assert incompetent["disposition"] == "PILOT_RAW_LONG_INCOMPETENT"
    assert len(incompetent["cells"]) == 4


def _pilot_scan_rows() -> list[BoundaryScanRow]:
    rows: list[BoundaryScanRow] = []
    for slot in (0, 1):
        for split, first, count in ((Split.TRAIN, 320, 512), (Split.EVALUATION, 832, 64)):
            for offset in range(count):
                rows.append(BoundaryScanRow(
                    slot, split, "K8", first + offset, True, 60, 0,
                    (4, 8, 12, 16)[offset % 4], (0.25, 4.0)[offset % 2], 2, 60,
                ))
    return rows


def test_pilot_structural_scan_is_two_slot_k8_only_and_result_blind() -> None:
    rows = _pilot_scan_rows()
    report = assess_pilot_structural_scan(rows)
    assert report["passed"] is True
    assert report["support_passed"] is True
    assert report["retained_row_count"] == 1_152
    assert report["expected_common_future_branch_count"] == 2_304
    assert report["work"]["formula"] == "2*(256+512+64)*256 + 16*actual_common_future_branch_count"
    assert report["work"]["within_ceiling"] is True
    assert report["activity"]["true_residual_training"] == 0
    assert report["activity"]["deranged_training"] == 0
    assert report["activity"]["final_namespace_reads"] == 0
    assert report["activity"]["models_constructed"] == 0

    permuted = rows[576:] + rows[:576]
    failed = assess_pilot_structural_scan(permuted)
    assert failed["passed"] is False
    assert any("canonical slot-major order" in issue for issue in failed["issues"])


def test_pilot_scan_binds_missing_and_unsupported_rows_as_support_not_engineering() -> None:
    rows = _pilot_scan_rows()
    # Preserve every assigned key but leave only ten slot-0 TRAIN boundaries,
    # split 5/5 across cells. Neither cell reaches the frozen count of eight.
    for index in range(512):
        row = rows[index]
        present = index < 10
        rows[index] = BoundaryScanRow(
            row.replicate, row.split, row.regime, row.episode_index,
            present, 60 if present else None, 0 if present else None,
            4 if index < 5 else 8 if present else None,
            0.25, 2 if present else 0, 60,
        )
    report = assess_pilot_structural_scan(rows)
    assert report["passed"] is True
    assert report["support_passed"] is False
    assert report["supported_fixed_denominator_counts"]["0/TRAIN"] == {
        "supported": 0, "retained_denominator": 10,
    }
    assert any("slot 0 TRAIN supported-cell rows 0/10" in failure
               for failure in report["support_failures"])


def _panel_row(index: int, horizon: int, cost: float) -> PanelRow:
    return PanelRow(
        RowKey(0, Split.TRAIN, "K8", index, 60, 0),
        cost,
        horizon,
        np.ones((2, 42), dtype=np.float32),
        np.zeros(8, dtype=np.float32),
        np.zeros(8, dtype=np.float32),
        np.eye(8, dtype=np.float32),
        np.ones(8, dtype=bool),
        np.arange(8, dtype=np.float64),
        0,
        ("pilot-tape", index),
    )


def test_pilot_raw_training_rows_exclude_every_unsupported_cell() -> None:
    supported = _panel_row(320, 4, 0.25)
    unsupported = _panel_row(321, 8, 4.0)
    keys = frozenset({(0, "TRAIN", "K8", 4, 0.25)})
    retained = retain_pilot_supported_rows((supported, unsupported), keys)
    assert retained == (supported,)


def test_one_slot_support_failure_suppresses_all_partial_raw_outcomes() -> None:
    visible, competence = route_pilot_execution_evidence(
        (_raw_long_summary(0),),
        ("slot 1 EVALUATION supported-cell rows 40/64 (<80%)",),
    )
    assert visible == ()
    assert competence["disposition"] == "NONIDENTIFYING_PILOT_K8_SUPPORT"
    assert competence["cells"] == []


def _material_row(index: int, *, keep_material: bool) -> PanelRow:
    g16 = np.zeros(8, dtype=np.float64)
    if keep_material:
        g16[0] = 1.0
    else:
        g16[1:] = 1.0
    return PanelRow(
        RowKey(1, Split.EVALUATION, "K8", 832 + index, 60, 0),
        0.25,
        4,
        np.ones((2, 42), dtype=np.float32),
        np.zeros(8, dtype=np.float32),
        np.zeros(8, dtype=np.float32),
        np.eye(8, dtype=np.float32),
        np.ones(8, dtype=bool),
        g16,
        0,
        ("pilot-material", index),
    )


def test_phase1_material_support_failure_prevents_both_raw_gates(monkeypatch) -> None:
    rows = tuple(
        [_material_row(index, keep_material=True) for index in range(7)]
        + [_material_row(7 + index, keep_material=False) for index in range(8)]
    )
    failures = pilot_material_stratum_support_failures(1, rows)
    assert any("KEEP_MATERIAL has 7 rows" in failure for failure in failures)

    train_calls = 0
    import experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.pilot as pilot_module

    def materialize(slot, _ledger, _cells):
        state = PilotSlotMaterialization(
            slot, (), (), (8, 8) if slot == 0 else (7, 8),
        )
        return state, () if slot == 0 else tuple(failures)

    def train(_state, _ledger):
        nonlocal train_calls
        train_calls += 1
        raise AssertionError("RAW phase must not start")

    monkeypatch.setattr(pilot_module, "_materialize_slot", materialize)
    monkeypatch.setattr(pilot_module, "_train_evaluate_slot", train)
    summaries, routed_failures, material_counts = execute_pilot_slots_two_phase(
        object(), frozenset(),
    )
    assert summaries == () and routed_failures
    assert material_counts == tuple(_material_count_records(slot1=(7, 8)))
    assert train_calls == 0


def test_pilot_launcher_is_create_only_before_worker_or_receipt_activity(tmp_path) -> None:
    output = tmp_path / "existing-root"
    output.mkdir()
    result = tmp_path / "result.json"
    memory = tmp_path / "memory.json"
    launch_memory = tmp_path / "launch-memory.json"
    launch_assessment = tmp_path / "launch-assessment.json"
    import pytest
    with pytest.raises(FileExistsError, match="fresh create-only"):
        run_raw_only_pilot(
            output_root=output,
            result_path=result,
            resource_receipt_path=memory,
            launch_resource_receipt_path=launch_memory,
            launch_run_resource_receipt_path=launch_assessment,
        )
    assert not result.exists() and not memory.exists()
    assert not launch_memory.exists() and not launch_assessment.exists()
    with pytest.raises(TypeError):
        run_raw_only_pilot(
            output_root=tmp_path / "old-root",
            result_path=tmp_path / "old-result.json",
            resource_receipt_path=tmp_path / "old-memory.json",
        )


def test_pilot_receipt_rejects_nonraw_or_final_namespace_activity() -> None:
    import pytest

    structural = assess_pilot_structural_scan(_pilot_scan_rows())
    typed_summaries = (_raw_long_summary(0), _raw_long_summary(1))
    competence = assess_pilot_competence(typed_summaries)
    payload = {
        "format": "CRTO_RAW_ONLY_DEVELOPMENT_PILOT_V1",
        "object_id": PILOT_CONFIG.object_id,
        "rng_namespace": PILOT_CONFIG.rng_namespace,
        "slots": [0, 1],
        "claim_ceiling": PILOT_CONFIG.claim_ceiling,
        "feasibility_only": True,
        "final_namespace": RNG_NAMESPACE,
        "final_namespace_untouched": True,
        "representations": {
            "registered": ["RAW"], "trained": ["RAW"], "evaluated": ["RAW"],
        },
        "registered_checkpoint": "LONG",
        "checkpoints": ["LONG"],
        "competence": competence,
        "material_support_counts": _material_count_records(),
        "summaries": [_serialized_summary(summary) for summary in typed_summaries],
        "structural_scan": structural,
        "work": {
            "formula": "2*(256+512+64)*256 + 16*actual_common_future_branch_count",
            "prospective": structural["work"],
            "actual": {
                **structural["work"],
                "execution_started": True,
                "branch_count_matches_scan": True,
            },
            "within_ceiling": True,
        },
        "resource": {
            "prescan_memory": _memory_receipt(),
            "launch_memory": _memory_receipt(),
            "launch_assess_run": _run_receipt(),
        },
        "activity": {
            "predictor_models": 2, "raw_gate_models": 2,
            "raw_gate_optimizer_updates": 4096,
            "true_residual_training": 0, "true_residual_evaluation": 0,
            "deranged_training": 0, "deranged_evaluation": 0,
            "short_checkpoint_exposed": 0, "final_namespace_reads": 0,
            "final_artifact_reads": 0,
        },
    }
    validate_pilot_result(payload)
    import copy
    missing_counts = copy.deepcopy(payload)
    missing_counts["material_support_counts"].pop()
    with pytest.raises(ValueError, match="exact four material-support"):
        validate_pilot_result(missing_counts)
    tampered_counts = copy.deepcopy(payload)
    tampered_counts["material_support_counts"][0]["row_count"] = 9
    with pytest.raises(ValueError, match="durable material support disagrees"):
        validate_pilot_result(tampered_counts)
    payload["activity"]["final_namespace_reads"] = 1
    with pytest.raises(ValueError, match="final-namespace activity"):
        validate_pilot_result(payload)
    payload["activity"]["final_namespace_reads"] = 0

    payload["summaries"][0]["row_count_by_regime"]["K16"] = 64
    with pytest.raises(ValueError, match="frozen K8 support mappings"):
        validate_pilot_result(payload)
    del payload["summaries"][0]["row_count_by_regime"]["K16"]
    payload["summaries"][0]["row_count_by_regime"]["K8"] = 65
    with pytest.raises(ValueError, match="frozen K8 support mappings"):
        validate_pilot_result(payload)
    payload["summaries"][0]["row_count_by_regime"]["K8"] = 64

    payload["summaries"][0]["mean_regret_by_regime_and_material_stratum"]["K8"][
        "KEEP_MATERIAL"
    ] = 0.008
    with pytest.raises(ValueError, match="summaries and competence cells disagree"):
        validate_pilot_result(payload)
    payload["summaries"][0]["mean_regret_by_regime_and_material_stratum"]["K8"][
        "KEEP_MATERIAL"
    ] = 0.01

    support_tamper = copy.deepcopy(payload)
    support_tamper["competence"] = {
        "status": "NONIDENTIFYING",
        "disposition": "NONIDENTIFYING_PILOT_K8_SUPPORT",
        "failures": ["support failure"],
        "cells": [],
    }
    with pytest.raises(ValueError, match="cannot serialize RAW outcomes or activity"):
        validate_pilot_result(support_tamper)

    first_cell = payload["competence"]["cells"][0]
    original_raw = first_cell["raw_mean_regret"]
    original_difference = first_cell["raw_minus_script"]
    first_cell["raw_mean_regret"] = 0.0101
    first_cell["raw_minus_script"] = 0.0101 - first_cell["script_mean_regret"]
    payload["summaries"][0]["mean_regret_by_regime_and_material_stratum"]["K8"][
        "KEEP_MATERIAL"
    ] = 0.0101
    with pytest.raises(ValueError, match="PILOT_FEASIBLE.*above 0.01"):
        validate_pilot_result(payload)
    first_cell["raw_mean_regret"] = original_raw
    first_cell["raw_minus_script"] = original_difference
    payload["summaries"][0]["mean_regret_by_regime_and_material_stratum"]["K8"][
        "KEEP_MATERIAL"
    ] = original_raw

    payload["competence"]["disposition"] = "PILOT_RAW_LONG_INCOMPETENT"
    payload["competence"]["status"] = "FAIL"
    payload["competence"]["failures"] = ["tampered numeric failure"]
    with pytest.raises(ValueError, match="lacks a RAW regret above 0.01"):
        validate_pilot_result(payload)
    payload["competence"]["disposition"] = "PILOT_FEASIBLE"
    payload["competence"]["status"] = "PASS"
    payload["competence"]["failures"] = []

    payload["work"]["actual"]["actual_common_future_branch_count"] -= 1
    payload["work"]["actual"]["branch_count_matches_scan"] = False
    with pytest.raises(ValueError, match="branch work disagrees"):
        validate_pilot_result(payload)
    payload["work"]["actual"]["actual_common_future_branch_count"] += 1
    payload["work"]["actual"]["branch_count_matches_scan"] = True

    payload["resource"]["launch_memory"]["effective_available_bytes"] = 4 * 1024**3 - 1
    with pytest.raises(ValueError, match="resource or one-worker"):
        validate_pilot_result(payload)


def test_executed_pilot_branch_mismatch_is_an_incomplete_attempt() -> None:
    import pytest
    ledger = PilotWorkLedger(expected_common_future_branches=1)
    ledger.record_base_episodes(2 * (256 + 512 + 64))
    with pytest.raises(ResourceLimitExceeded, match="G16 count disagrees"):
        ledger.receipt(require_exact_branches=True)


def test_support_receipt_predictor_activity_matches_execution_phase() -> None:
    import copy
    import pytest

    structural = assess_pilot_structural_scan(_pilot_scan_rows())
    base = {
        "format": "CRTO_RAW_ONLY_DEVELOPMENT_PILOT_V1",
        "object_id": PILOT_CONFIG.object_id,
        "rng_namespace": PILOT_CONFIG.rng_namespace,
        "slots": [0, 1],
        "claim_ceiling": PILOT_CONFIG.claim_ceiling,
        "feasibility_only": True,
        "final_namespace": RNG_NAMESPACE,
        "final_namespace_untouched": True,
        "representations": {"registered": ["RAW"], "trained": [], "evaluated": []},
        "registered_checkpoint": "LONG",
        "checkpoints": [],
        "competence": {
            "status": "NONIDENTIFYING",
            "disposition": "NONIDENTIFYING_PILOT_K8_SUPPORT",
            "failures": ["support failure"],
            "cells": [],
        },
        "material_support_counts": _material_count_records(slot1=(7, 8)),
        "summaries": [],
        "structural_scan": structural,
        "work": {
            "formula": "2*(256+512+64)*256 + 16*actual_common_future_branch_count",
            "prospective": structural["work"],
            "actual": {
                **structural["work"],
                "execution_started": True,
                "branch_count_matches_scan": True,
            },
            "within_ceiling": True,
        },
        "resource": {
            "prescan_memory": _memory_receipt(),
            "launch_memory": _memory_receipt(),
            "launch_assess_run": _run_receipt(),
        },
        "activity": {
            "predictor_models": 2,
            "raw_gate_models": 0,
            "raw_gate_optimizer_updates": 0,
            "true_residual_training": 0,
            "true_residual_evaluation": 0,
            "deranged_training": 0,
            "deranged_evaluation": 0,
            "short_checkpoint_exposed": 0,
            "final_namespace_reads": 0,
            "final_artifact_reads": 0,
        },
    }
    validate_pilot_result(base)
    assert base["material_support_counts"] == _material_count_records(slot1=(7, 8))
    phase1_tamper = copy.deepcopy(base)
    phase1_tamper["activity"]["predictor_models"] = 0
    with pytest.raises(ValueError, match="predictor activity disagrees"):
        validate_pilot_result(phase1_tamper)

    scan_stop = copy.deepcopy(base)
    scan_stop["structural_scan"]["support_passed"] = False
    scan_stop["structural_scan"]["support_failures"] = ["scan support failure"]
    scan_stop["work"]["actual"] = {
        "execution_started": False,
        "base_episode_count": 0,
        "base_primitive_team_steps": 0,
        "actual_common_future_branch_count": 0,
        "actual_common_future_steps": 0,
        "actual_total_steps": 0,
        "within_ceiling": True,
    }
    scan_stop["material_support_counts"] = _material_count_records(
        observed=False,
    )
    scan_stop["activity"]["predictor_models"] = 0
    validate_pilot_result(scan_stop)
    unobserved_tamper = copy.deepcopy(scan_stop)
    unobserved_tamper["material_support_counts"][0]["row_count"] = 0
    with pytest.raises(ValueError, match="unobserved pilot material count must be null"):
        validate_pilot_result(unobserved_tamper)
    scan_tamper = copy.deepcopy(scan_stop)
    scan_tamper["activity"]["predictor_models"] = 2
    with pytest.raises(ValueError, match="predictor activity disagrees"):
        validate_pilot_result(scan_tamper)


def test_pilot_three_receipt_order_precedes_scan_and_torch_root(
    tmp_path, monkeypatch,
) -> None:
    import pytest
    import experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.pilot as pilot_module

    class StopBeforeTorch(Exception):
        pass

    output = tmp_path / "output"
    result = tmp_path / "result.json"
    prescan = tmp_path / "prescan-memory.json"
    launch = tmp_path / "launch-memory.json"
    assessment = tmp_path / "launch-assess.json"
    events: list[str] = []

    def memory_receipt(path):
        events.append("prescan-memory" if Path(path) == prescan else "launch-memory")
        return _memory_receipt()

    def scan():
        events.append("scan")
        return tuple(_pilot_scan_rows())

    def run_receipt(path, *, run_id):
        assert Path(path) == assessment
        assert run_id == PILOT_LAUNCH_RUN_ID
        events.append("launch-assess")
        return _run_receipt()

    def configure():
        events.append("configure-torch")
        assert not output.exists() and not result.exists()
        raise StopBeforeTorch

    monkeypatch.setenv("HMASD_CRTO_PILOT_WORKER", PILOT_CONFIG.object_id)
    monkeypatch.setattr(pilot_module, "create_shared_resource_receipt", memory_receipt)
    monkeypatch.setattr(pilot_module, "scan_pilot_histories", scan)
    monkeypatch.setattr(pilot_module, "create_shared_run_assessment", run_receipt)
    monkeypatch.setattr(pilot_module, "_configure_one_worker_one_thread", configure)
    with pytest.raises(StopBeforeTorch):
        pilot_module._run_raw_only_pilot_worker(
            output_root=output,
            result_path=result,
            resource_receipt_path=prescan,
            launch_resource_receipt_path=launch,
            launch_run_resource_receipt_path=assessment,
        )
    assert events == [
        "prescan-memory", "scan", "launch-memory", "launch-assess", "configure-torch",
    ]
    assert not output.exists() and not result.exists()


def test_pilot_launch_run_id_passes_real_shared_validator_and_command_shape(
    tmp_path, monkeypatch,
) -> None:
    from scripts import hmasd_resource_preflight as shared_resource
    from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01 import (
        preflight as preflight_module,
    )

    observed_command: list[str] = []

    def execute_shared_assessment(command, **kwargs):
        observed_command.extend(map(str, command))

        def option(name: str) -> str:
            return str(command[command.index(name) + 1])

        receipt = shared_resource.assess_snapshot(
            {
                "memory": {
                    "total_bytes": 32 * shared_resource.GIB,
                    "available_bytes": 16 * shared_resource.GIB,
                    "cgroup_memory_max_raw": "max",
                },
            },
            direction_id=option("--direction"),
            run_id=option("--run-id"),
            workers=option("--workers"),
            threads_per_worker=option("--threads-per-worker"),
            estimated_wall_seconds=option("--estimated-wall-seconds"),
            estimated_peak_gib=option("--estimated-peak-gib"),
            basis=option("--basis"),
        )
        Path(option("--out")).write_text(
            json.dumps(receipt, allow_nan=False), encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(preflight_module.subprocess, "run", execute_shared_assessment)
    receipt = preflight_module.create_shared_run_assessment(
        tmp_path / "launch-assess.json",
        run_id=PILOT_LAUNCH_RUN_ID,
    )

    assert observed_command[:3] == [
        sys.executable, str(preflight_module.RESOURCE_SCRIPT), "assess-run",
    ]
    assert observed_command[observed_command.index("--run-id") + 1] == (
        "crto_common_history_raw_pilot_20260831_01_launch"
    )
    assert receipt["run_id"] == PILOT_LAUNCH_RUN_ID


def test_pilot_dual_publish_result_collision_exposes_no_output_root(tmp_path) -> None:
    stage = tmp_path / ".stage"
    stage.mkdir()
    (stage / "pilot_receipt.json").write_text("{}\n", encoding="utf-8")
    output = tmp_path / "public-root"
    result = tmp_path / "result.json"
    result.write_text("occupied\n", encoding="utf-8")
    import pytest
    with pytest.raises(FileExistsError, match="fresh public targets"):
        publish_pilot_result_create_only(stage, output, result, {"unused": True})
    assert stage.exists()
    assert not output.exists()
    assert result.read_text(encoding="utf-8") == "occupied\n"


def test_pilot_dual_publish_rolls_back_output_when_result_rename_fails(
    tmp_path, monkeypatch,
) -> None:
    import os
    import experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.pilot as pilot_module

    stage = tmp_path / ".stage"
    stage.mkdir()
    (stage / "pilot_receipt.json").write_text("{}\n", encoding="utf-8")
    output = tmp_path / "public-root"
    result = tmp_path / "result.json"
    real_rename = os.rename
    calls = 0

    def fail_second_rename(source, target):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected result publication failure")
        return real_rename(source, target)

    monkeypatch.setattr(pilot_module.os, "rename", fail_second_rename)
    import pytest
    with pytest.raises(OSError, match="injected result publication failure"):
        publish_pilot_result_create_only(stage, output, result, {"receipt": "test"})
    assert calls == 4
    assert stage.exists()
    assert not output.exists() and not result.exists()


def test_pilot_late_runtime_limit_failure_rolls_back_both_public_targets(tmp_path) -> None:
    import pytest

    stage = tmp_path / ".stage"
    stage.mkdir()
    (stage / "pilot_receipt.json").write_text("{}\n", encoding="utf-8")
    output = tmp_path / "public-root"
    result = tmp_path / "result.json"
    checks = 0

    def fail_after_output_rename() -> None:
        nonlocal checks
        checks += 1
        if checks == 4:
            raise RuntimeError("late runtime ceiling failure")

    with pytest.raises(RuntimeError, match="late runtime ceiling failure"):
        publish_pilot_result_create_only(
            stage,
            output,
            result,
            {"receipt": "test"},
            limit_check=fail_after_output_rename,
        )
    assert checks == 4
    assert stage.exists()
    assert not output.exists() and not result.exists()
