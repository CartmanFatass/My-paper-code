"""Closed-form plan arithmetic and clustered-statistic tests without rollout."""
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.uav_fleet_adaptation.b06_count_development.contract import FROZEN, COUNTS, FITS, FINAL_COUNTS
from experiments.candidates.uav_fleet_adaptation.b06_count_development.reading import METRICS, comparisons


def test_complete_plan_counts_are_computed_from_the_declared_schedule():
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.read import _planned_rows
    rows = _planned_rows(FROZEN)
    assert len(rows) == 2661
    acquisition = [r for r in rows if r[0] == "acquisition"]
    evaluation = [r for r in rows if r[0] == "evaluation"]
    fixture = [r for r in rows if r[0] == "fixture"]
    assert (len(acquisition), len(evaluation), len(fixture)) == (1024, 1632, 5)
    assert sum(256 for r in acquisition + evaluation) == 679936
    assert sum(256 * r[3] for r in acquisition + evaluation) == 3399680
    assert sum(64 * r[3] for r in acquisition) == 327680
    actor_rows = sum(64 * r[3] for r in acquisition if r[5] in (1, 2))
    actor_rows += sum(64 * r[3] for r in evaluation if r[2] in ("P", "F", "M", "Bstar"))
    assert actor_rows == 593920
    c_rows = sum(64 * r[3] for r in acquisition)
    c_rows += sum(64 * r[3] for r in evaluation if r[2] in ("C", "Q"))
    c_rows += sum(2 * r[3] for r in fixture)
    assert c_rows == 419890
    native_slots = sum((256 + 2) * r[3] * (50 + r[3]) for r in acquisition + evaluation)
    native_slots += sum((8 + 2) * r[3] * (50 + r[3]) for r in fixture)
    native_slots += sum(n * (50 + n) for n in COUNTS)
    assert native_slots == FROZEN.expected()["native_dense_slots"] == 189267523
    for lineage in (0, 1):
        for arm in FITS:
            for phase, expected in enumerate((40960, 20480, 20480)):
                block = [r for r in acquisition if r[1] == lineage and r[2] == arm and r[5] == phase]
                assert sum(64 * r[3] for r in block) == expected
                if arm == "M":
                    assert sum(r[3] == 3 for r in block) == sum(r[3] == 7 for r in block)
                    assert sum(64 * r[3] for r in block if r[3] == 3) * 10 == 3 * expected


def artificial_panel():
    from experiments.candidates.uav_fleet_adaptation.b06_count_development.read import _planned_rows
    small = SimpleNamespace(evaluation_worlds=(21, 22), fixture_world=99,
                            phase_worlds=lambda lineage, phase: (), acquisition_count=lambda arm, j: 5)
    plans = [r for r in _planned_rows(small) if r[0] == "evaluation"]
    small.expected = lambda: {"evaluation_episodes": len(plans)}
    gains = {(0, 4): 100., (0, 5): -300., (0, 6): -20.,
             (1, 4): 8., (1, 5): 500., (1, 6): 12.}
    rows = []
    for kind, lineage, arm, n, world, phase, tape in plans:
        value = gains.get((lineage, n), 0.) if arm == "M" else 0.
        # The tape effects cancel after their within-world average.
        value += 9. if tape == 0 else -9. if tape == 1 else 0.
        value += world - 21
        row = dict(kind=kind, lineage=lineage, arm=arm, n=n, world=world, phase=phase, tape=tape,
                   id=str((lineage, arm, n, world, tape)), zero_service_ticks=[])
        row.update({key: value for key in METRICS})
        row["zero_service_steps"] = 0
        rows.append(row)
    return small, rows


def test_primary_is_equal_count_equal_lineage_with_world_clusters():
    protocol, rows = artificial_panel()
    result = comparisons(rows, protocol)
    primary = result["primary_equal_N4_N6_both_lineages"]["J"]
    assert primary["mean"] == 25.
    assert primary["n"] == 2 and primary["differences"] == [25., 25.]
    assert result["lineage_targets"]["0"]["J"]["mean"] == 40.
    assert result["lineage_targets"]["1"]["J"]["mean"] == 10.
    assert result["by_lineage"]["0"]["5"]["paired"]["M-F"]["J"]["mean"] == -300.
    assert result["by_lineage"]["1"]["5"]["paired"]["M-F"]["J"]["mean"] == 500.
    assert result["by_lineage"]["1"]["4"]["paired"]["Bstar-P"]["J"]["differences"] == [0., 0.]
    with pytest.raises(ValueError):
        comparisons(rows[:-1], protocol)
    with pytest.raises(ValueError):
        comparisons(rows[:-1] + rows[:1], protocol)


def test_protocol_rejects_overlapping_or_changed_exposure():
    from dataclasses import replace
    with pytest.raises(ValueError):
        replace(FROZEN, epochs=(40, 20, 20)).validate()
    with pytest.raises(ValueError):
        replace(FROZEN, fixture_world=FROZEN.evaluation_worlds[0]).validate()
    assert FROZEN.from_dict(FROZEN.to_dict()) == FROZEN
    total = sum(n * e for n, e in zip((40960, 61440, 81920), FROZEN.epochs))
    assert total * 4 == 16384000


def test_reader_reserves_once_before_any_priced_work(tmp_path, monkeypatch):
    import json
    from experiments.candidates.uav_fleet_adaptation.b06_count_development import read
    calls = []

    def artificial_read(out, repo, work):
        calls.append(1)
        assert json.loads((out / "reading.json").read_text())["status"] == "INCOMPLETE"
        with pytest.raises(FileExistsError, match="already attempted"):
            read.read_result(out, repo)
        work["student_rows"] = 3
        return dict(status="VERIFIED", object=read.OBJECT)

    monkeypatch.setattr(read, "_read", artificial_read)
    result = read.read_result(tmp_path, tmp_path)
    assert calls == [1] and result["reader_work"]["student_rows"] == 3
    assert json.loads((tmp_path / "reading.json").read_text())["status"] == "VERIFIED"
    with pytest.raises(FileExistsError, match="already attempted"):
        read.read_result(tmp_path, tmp_path)
    assert calls == [1]


def test_reader_retains_failed_partial_exposure_and_refuses_repeat(tmp_path, monkeypatch):
    import json
    from experiments.candidates.uav_fleet_adaptation.b06_count_development import read

    def artificial_read(out, repo, work):
        work["C_requests"] = 2
        raise ArithmeticError("synthetic failed read")

    monkeypatch.setattr(read, "_read", artificial_read)
    with pytest.raises(ArithmeticError, match="synthetic failed read"):
        read.read_result(tmp_path, tmp_path)
    saved = json.loads((tmp_path / "reading.json").read_text())
    assert saved["status"] == "FAILED" and saved["reader_work"]["C_requests"] == 2
    assert "synthetic failed read" in saved["failure"]
    with pytest.raises(FileExistsError, match="already attempted"):
        read.read_result(tmp_path, tmp_path)
