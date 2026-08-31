import numpy as np

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.calibration import (
    assess_calibration,
    fit_calibration_from_examples,
    slot_calibration_diagnostics,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.packets import (
    CalibrationTable,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import (
    PredictorExample,
)


def _example(index: int, *, horizon: int, target: np.ndarray) -> PredictorExample:
    return PredictorExample(
        episode_index=index,
        commitment_time=0,
        target_age=horizon,
        agent=0,
        option=0,
        k=16,
        origin_history=np.zeros((1, 42), dtype=np.float32),
        target=np.asarray(target, dtype=np.float32),
    )


def _identity_forecast(
    _history: np.ndarray, _option: int, _k: int, _horizon: int,
) -> tuple[np.ndarray, np.ndarray]:
    return np.zeros(8, dtype=np.float32), np.eye(8, dtype=np.float32)


def test_calibration_table_uses_every_supplied_all_horizon_example() -> None:
    examples = (
        _example(10, horizon=4, target=np.full(8, -1.0, dtype=np.float32)),
        _example(11, horizon=16, target=np.full(8, +1.0, dtype=np.float32)),
    )

    table, audit = fit_calibration_from_examples(examples, _identity_forecast)

    assert table.sorted_residuals.shape == (8, 2)
    np.testing.assert_array_equal(
        table.sorted_residuals,
        np.tile(np.asarray((-1.0, 1.0), dtype=np.float32), (8, 1)),
    )
    assert audit == {
        "example_count": 2,
        "episode_indices": [10, 11],
        "horizon_counts": {"4": 1, "8": 0, "12": 0, "16": 1},
        "pooled_k_values": [16],
        "table_record": table.canonical_record,
    }


def test_fixed_k16_calibration_is_replicate_balanced_and_switches_are_descriptive() -> None:
    support = np.tile(
        np.linspace(-1.3, 1.3, 99, dtype=np.float32), (8, 1),
    )
    table = CalibrationTable(support)
    values = np.concatenate((
        np.linspace(-1.2, 1.2, 30, dtype=np.float32),
        np.asarray((1.3, 1.3), dtype=np.float32),
    ))
    reports = []
    for slot in range(8):
        examples = tuple(
            _example(
                1000 * slot + 100 * horizon + index,
                horizon=horizon,
                target=np.full(8, value, dtype=np.float32),
            )
            for horizon in (4, 8, 12, 16)
            for index, value in enumerate(values)
        )
        reports.append(slot_calibration_diagnostics(
            table,
            {"K16": examples, "K4_TO_16": (), "K16_TO_4": ()},
            _identity_forecast,
            replicate=slot,
        ))

    result = assess_calibration(reports)

    assert result["passed"] is True
    assert result["issues"] == []
    assert result["switch_regimes_are_admission_gates"] is False
    for horizon in ("4", "8", "12", "16"):
        row = result["k16"][horizon]
        assert row["slot_target_counts"] == [32] * 8
        assert row["replicate_balanced_coverage"] == 30 / 32
        assert row["max_replicate_balanced_pit_ece"] <= 0.10
        assert row["replicate_balanced_clip_saturation"] == 0.0


def test_fixed_k16_calibration_fails_closed_on_missing_horizon_support() -> None:
    reports = []
    for slot in range(8):
        regimes = {
            regime: {
                str(horizon): {
                    "target_count": 0 if slot == 7 and horizon == 16 else 32,
                    "coverage": None if slot == 7 and horizon == 16 else 0.9,
                    "pit_frequencies": None if slot == 7 and horizon == 16 else (
                        np.full((8, 10), 0.1, dtype=np.float64).tolist()
                    ),
                    "pit_ece_by_coordinate": None if slot == 7 and horizon == 16 else [0.0] * 8,
                    "clip_saturation": None if slot == 7 and horizon == 16 else 0.0,
                }
                for horizon in (4, 8, 12, 16)
            }
            for regime in ("K16", "K4_TO_16", "K16_TO_4")
        }
        reports.append({"replicate": slot, "regimes": regimes})

    result = assess_calibration(reports)

    assert result["passed"] is False
    assert any("horizon 16" in issue for issue in result["issues"])
