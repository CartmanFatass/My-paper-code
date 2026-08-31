from pathlib import Path

import pytest

from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.analysis import (
    AnalysisPolicy, SimultaneousInterval, _first_match, analyze,
)
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.contracts import Budget
from experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run import (
    _atomic_publish_with_executor, result_skeleton, validate_result,
)


def _analysis():
    return {
        "status": "NONIDENTIFYING", "interpretation": "UNRESOLVED",
        "failures": ["test admission"], "intervals": [],
    }


def test_missing_numeric_authority_routes_nonidentifying() -> None:
    result = analyze([], policy=AnalysisPolicy())
    assert result["status"] == "NONIDENTIFYING"
    assert any("MISSING_INTERVAL_POLICY" in failure for failure in result["failures"])


def _intervals(bounds):
    keys = (
        ("RAW_MINUS_TRUE", Budget.SHORT), ("RAW_MINUS_TRUE", Budget.LONG),
        ("DERANGED_MINUS_TRUE", Budget.SHORT), ("DERANGED_MINUS_TRUE", Budget.LONG),
        ("RAW_MINUS_DERANGED", Budget.SHORT), ("RAW_MINUS_DERANGED", Budget.LONG),
    )
    return tuple(
        SimultaneousInterval(label, budget, (lower + upper) / 2, lower, upper, 8, "test", 0.01)
        for (label, budget), (lower, upper) in zip(keys, bounds)
    )


def test_first_match_orientation_and_full_equivalence_width() -> None:
    assert _first_match(_intervals(((.01,.02),(.01,.02),(.01,.02),(.01,.02),(-.001,.001),(-.001,.001)))) == "PERSISTENT_ALIGNED_BIAS"
    assert _first_match(_intervals(((.01,.02),(.01,.02),(-.001,.001),(-.001,.001),(.01,.02),(.01,.02)))) == "GENERIC_PREPROCESSING"
    # Mere overlap with +/- delta is not equivalence.
    assert _first_match(_intervals(((.01,.02),(-.10,.10),(-.10,.10),(-.10,.10),(-.10,.10),(-.10,.10)))) == "UNRESOLVED"


def test_schema_rejects_legacy_registration_and_atomic_fresh_publication(tmp_path: Path) -> None:
    payload = result_skeleton(
        analysis=_analysis(), replicates=tuple({"replicate": index} for index in range(8)),
    )
    validate_result(payload)
    legacy = dict(payload)
    legacy["schema_version"] = "CRTO-B1-RESULT-v4"
    with pytest.raises(Exception):
        validate_result(legacy)
    tampered = dict(payload)
    tampered["unexpected"] = True
    with pytest.raises(Exception):
        validate_result(tampered)

    output = tmp_path / "fresh-root"
    result = tmp_path / "fresh-result.json"
    def executor(stage: Path):
        (stage / "receipt.txt").write_text("non-result test", encoding="utf-8")
        return payload
    published = _atomic_publish_with_executor(output, result, executor=executor)
    assert published == payload and (output / "receipt.txt").exists() and result.exists()
    with pytest.raises(FileExistsError):
        _atomic_publish_with_executor(output, tmp_path / "other.json", executor=executor)

    identifying = result_skeleton(
        analysis={
            "status": "IDENTIFYING", "interpretation": "UNRESOLVED",
            "failures": [], "intervals": [],
        },
        replicates=tuple({"replicate": index} for index in range(8)),
    )
    blocked_root = tmp_path / "blocked-root"
    blocked_result = tmp_path / "blocked-result.json"
    with pytest.raises(PermissionError, match="NONIDENTIFYING fixtures"):
        _atomic_publish_with_executor(
            blocked_root, blocked_result, executor=lambda _stage: identifying,
        )
    assert not blocked_root.exists() and not blocked_result.exists()

    race_root = tmp_path / "race-root"
    race_result = tmp_path / "race-result.json"
    def concurrent_creator() -> None:
        race_result.write_text("user-owned", encoding="utf-8")
    with pytest.raises(FileExistsError):
        _atomic_publish_with_executor(
            race_root, race_result, executor=executor, before_publish=concurrent_creator,
        )
    assert race_result.read_text(encoding="utf-8") == "user-owned"
    assert not race_root.exists()
