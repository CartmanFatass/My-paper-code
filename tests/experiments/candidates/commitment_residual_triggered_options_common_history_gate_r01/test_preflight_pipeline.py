from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.commitment_residual_triggered_options.host import (
    EventClass, Regime, ScenarioSpec, build_scenario_tape,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    PanelRow, Representation, RowKey, Split,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.host_bridge import (
    BoundaryScanRow, materialize_common_history_row, materialize_episode_observables,
    materialize_predictor_examples, scan_common_history_boundary,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.ledger import (
    BASE_POPULATION_EPISODES, PrimitiveTeamStepLedger, prospective_ledger_report,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.packets import (
    PacketDataset,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.preflight import (
    assess_structural_scan, canonical_population_schedule, prospective_preflight,
    validate_population_schedule, validate_resource_receipt, validate_run_resource_receipt,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run import (
    _run_official_preflight, build_parser, run_registered, source_check,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.training import (
    train_one_path,
)


FOUR_GIB = 4 * 1024**3


def _memory_receipt() -> dict[str, object]:
    return {
        "schema_version": 1,
        "minimum_available_bytes": FOUR_GIB,
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
        "minimum_available_bytes": FOUR_GIB,
        "estimate": {"wall_seconds": 7200.0, "peak_memory_gib": 2.0},
        "physical_floor_pass": True,
        "effective_floor_pass": True,
        "memory_floor_pass": True,
        "memory_safe": True,
    }


def _scan_rows() -> list[BoundaryScanRow]:
    rows: list[BoundaryScanRow] = []
    for slot in range(8):
        for episode in range(320, 832):
            offset = episode - 320
            rows.append(BoundaryScanRow(
                slot, Split.TRAIN, "K8", episode, True, 60, 0,
                (4, 8, 12, 16)[offset % 4], (0.25, 4.0)[offset % 2], 2, 60,
            ))
        for regime, first in (
            ("K8", 832), ("K16", 896), ("K4_TO_16", 960), ("K16_TO_4", 1024),
        ):
            for episode in range(first, first + 64):
                offset = episode - first
                rows.append(BoundaryScanRow(
                    slot, Split.EVALUATION, regime, episode, True, 60, 0,
                    (4, 8, 12, 16)[offset % 4], (0.25, 4.0)[offset % 2], 2, 60,
                ))
    return rows


def _training_row(index: int) -> PanelRow:
    return PanelRow(
        RowKey(0, Split.TRAIN, "K8", index, 60, 0), 0.25, 4,
        np.ones((2, 42), dtype=np.float32), np.zeros(8, dtype=np.float32),
        np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32),
        np.ones(8, dtype=bool), np.arange(8, dtype=np.float64), 0, ("tape", index),
    )


def test_canonical_schedule_calibration_formula_and_exact_ledger() -> None:
    blocks = canonical_population_schedule()
    assert not validate_population_schedule()
    assert blocks[0].first_episode_index == 0 and blocks[-1].last_episode_index == 1087
    report = prospective_ledger_report(12_288)
    assert report["charged_full_tape_primitive_team_steps"] == 8 * 1088 * 256
    assert report["actual_common_future_steps"] == 12_288 * 16
    assert report["actual_total_steps"] == 2_424_832
    assert report["within_ceiling"] is True and report["blocker"] is None
    over = prospective_ledger_report(23_041)
    assert over["within_ceiling"] is False
    assert "EXCEEDS_CEILING" in str(over["blocker"])


def test_structural_scan_is_slot_ordered_and_slots_cannot_supply_each_other() -> None:
    rows = _scan_rows()
    assert assess_structural_scan(rows)["passed"] is True
    permuted = rows[768:1536] + rows[:768] + rows[1536:]
    assert assess_structural_scan(permuted)["passed"] is False
    assert any("exactly ordered 0..7" in issue for issue in assess_structural_scan(permuted)["issues"])

    sparse = list(rows)
    # Slot 0 TRAIN retains ten rows in one supported cell. The 80% denominator
    # is those ten otherwise-eligible rows, not all 512 assigned episodes.
    for index in range(512):
        row = sparse[index]
        sparse[index] = BoundaryScanRow(
            row.replicate, row.split, row.regime, row.episode_index,
            index < 10, 60 if index < 10 else None, 0 if index < 10 else None,
            4 if index < 10 else None, 0.25, 2 if index < 10 else 0, 60,
        )
    sparse_report = assess_structural_scan(sparse)
    assert not any("slot 0 TRAIN supported-cell" in issue for issue in sparse_report["issues"])

    uncompensated = list(rows)
    # Make each slot-0 TRAIN row its own unsupported horizon/cost pattern by
    # retaining only seven rows; abundant slot 1 support must not rescue it.
    for index in range(512):
        row = uncompensated[index]
        uncompensated[index] = BoundaryScanRow(
            row.replicate, row.split, row.regime, row.episode_index,
            index < 7, 60 if index < 7 else None, 0 if index < 7 else None,
            4 if index < 7 else None, 0.25, 2 if index < 7 else 0, 60,
        )
    report = assess_structural_scan(uncompensated)
    assert any("slot 0 TRAIN supported-cell" in issue for issue in report["issues"])


def test_dry_scan_branch_count_equals_g16_enumerator_action_count() -> None:
    tape = build_scenario_tape(ScenarioSpec(
        7, 654, Regime.K8, EventClass.NONE, 50, 0.25,
    ))
    structural = scan_common_history_boundary(tape, replicate=0, split=Split.TRAIN)
    assert structural.row_present

    class AuditLedger:
        def __init__(self) -> None:
            self.required = None
            self.actual = 0

        def require_common_future_headroom(self, branch_count: int) -> None:
            self.required = branch_count

        def record_common_future_branch(self, executed_steps: int) -> None:
            assert executed_steps == 16
            self.actual += 1

    ledger = AuditLedger()
    row = materialize_common_history_row(
        tape, replicate=0, split=Split.TRAIN,
        forecast=lambda *_: (np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32)),
        ledger=ledger,
    )
    assert row is not None
    assert ledger.required == ledger.actual == structural.legal_common_future_branches


def test_resource_receipts_and_preflight_are_fail_closed_without_activity(tmp_path: Path) -> None:
    assert not validate_resource_receipt(_memory_receipt())
    assert not validate_run_resource_receipt(_run_receipt())
    malformed = _memory_receipt()
    malformed["effective_available_bytes"] = FOUR_GIB - 1
    assert validate_resource_receipt(malformed)

    output = tmp_path / "scientific-root"
    result = tmp_path / "result.json"
    report = prospective_preflight(
        resource_receipt=malformed,
        run_resource_receipt=_run_receipt(),
        output_root=output,
        result_path=result,
        structural_scan=_scan_rows(),
    )
    assert report["ready_for_optimizer"] is False
    assert report["activity"]["optimizer_updates"] == 0
    assert report["activity"]["results"] == 0
    assert not output.exists() and not result.exists()

    output.mkdir()
    fresh_failure = prospective_preflight(
        resource_receipt=_memory_receipt(), run_resource_receipt=_run_receipt(),
        output_root=output, result_path=result, structural_scan=_scan_rows(),
    )
    assert fresh_failure["gates"]["fresh_scientific_targets"]["passed"] is False

    clean_report = prospective_preflight(
        resource_receipt=_memory_receipt(), run_resource_receipt=_run_receipt(),
        output_root=tmp_path / "clean-output", result_path=tmp_path / "clean-result.json",
        structural_scan=_scan_rows(),
    )
    failed_gates = [name for name, gate in clean_report["gates"].items() if not gate["passed"]]
    assert failed_gates == ["single_pass_production_pipeline"]
    blocker = clean_report["gates"]["single_pass_production_pipeline"]["issues"]
    assert len(blocker) == 1 and "SECOND" not in blocker[0]
    assert "second fresh 4-GiB/assess-run recheck" in blocker[0]
    assert clean_report["ready_for_optimizer"] is False


def test_single_pass_observables_and_calibration_path_never_call_g16() -> None:
    tape = build_scenario_tape(ScenarioSpec(
        900, 600, Regime.K16, EventClass.NONE, 50, 0.25,
    ))

    class AuditLedger:
        def __init__(self) -> None:
            self.calls = 0

        def require_common_future_headroom(self, _branch_count: int) -> None:
            self.calls += 1

        def record_common_future_branch(self, executed_steps: int) -> None:
            assert executed_steps == 16
            self.calls += 1

    production_ledger = AuditLedger()
    combined = materialize_episode_observables(
        tape, replicate=0, split=Split.EVALUATION,
        forecast=lambda *_: (np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32)),
        collect_common_history=True, ledger=production_ledger,
    )
    assert combined.structural_boundary.scripted_history_transitions == 256
    assert combined.common_history_row is not None
    reference = materialize_predictor_examples((tape,))
    assert tuple(example.canonical_key for example in combined.predictor_examples) == tuple(
        example.canonical_key for example in reference
    )
    assert all(
        np.array_equal(left.target, right.target)
        for left, right in zip(combined.predictor_examples, reference)
    )
    assert production_ledger.calls > 0

    calibration_tape = build_scenario_tape(ScenarioSpec(
        256, 654, Regime.K8, EventClass.NONE, 50, 0.25,
    ))
    calibration_ledger = AuditLedger()
    calibration = materialize_episode_observables(
        calibration_tape, replicate=0, split=Split.CALIBRATION, forecast=None,
        collect_common_history=False, ledger=calibration_ledger,
    )
    assert calibration.structural_boundary.scripted_history_transitions == 256
    assert calibration.common_history_row is None
    calibration_reference = materialize_predictor_examples((calibration_tape,))
    assert tuple(example.canonical_key for example in calibration.predictor_examples) == tuple(
        example.canonical_key for example in calibration_reference
    )
    assert all(
        np.array_equal(left.target, right.target)
        for left, right in zip(calibration.predictor_examples, calibration_reference)
    )
    assert calibration_ledger.calls == 0


def test_runtime_ledger_global_populations_and_optimizer_monitor(tmp_path: Path) -> None:
    ledger = PrimitiveTeamStepLedger(expected_common_future_branches=0)
    for name, episodes in BASE_POPULATION_EPISODES.items():
        ledger.charge_base_population(name, episodes)
        ledger.record_physically_executed_base_steps(name, 8 * episodes * 256)
    with pytest.raises(ValueError, match="already recorded"):
        ledger.charge_base_population("TRAIN", 512)
    ledger.assert_complete()

    rows = (_training_row(0), _training_row(1))
    packets = PacketDataset(
        tuple(row.key.text for row in rows), np.zeros((2, 52), dtype=np.float32),
    )
    calls = 0

    def monitor() -> None:
        nonlocal calls
        calls += 1

    train_one_path(
        rows, packets, replicate=0, representation=Representation.RAW,
        order=np.resize(np.asarray((0, 1), dtype=np.int64), 64),
        short_updates=1, long_updates=1, resource_monitor=monitor,
    )
    assert calls == 3

    parser = build_parser()
    parsed = parser.parse_args([
        "preflight", "--output-root", "o", "--result", "r",
        "--resource-receipt", "m", "--run-resource-receipt", "a", "--receipt", "p",
    ])
    assert parsed.action == "preflight"
    blocked_root = tmp_path / "blocked"
    blocked_result = tmp_path / "blocked.json"
    with pytest.raises(PermissionError, match="MISSING_PREFLIGHT"):
        run_registered(blocked_root, blocked_result)
    assert not blocked_root.exists() and not blocked_result.exists()
    with pytest.raises(ValueError, match="outside the scientific output root"):
        _run_official_preflight(
            output_root=blocked_root,
            result_path=blocked_result,
            resource_receipt_path=blocked_root / "memory.json",
            run_resource_receipt_path=tmp_path / "assess.json",
            preflight_receipt_path=tmp_path / "preflight.json",
        )
    assert not blocked_root.exists() and not blocked_result.exists()
    assert source_check()["status"] == "PASS"
