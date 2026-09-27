"""Stage 2-0 trace reader: the clock-aligned split and target diagnostics on a synthetic run."""

from __future__ import annotations

import json

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b03 import read_stake_traces as rd


def _write_run(tmp_path, qos, entries, targets):
    """qos[mode] (W, T); entries[mode] per-world first_entry_step; targets[mode] (W, T, n, 2)."""
    (tmp_path / "panels").mkdir()
    (tmp_path / "traces").mkdir()
    worlds = [955001 + k for k in range(next(iter(qos.values())).shape[0])]
    for m in rd.MODES:
        rows = [{"seed": w, "qos_per_step": float(qos[m][k].mean()), "first_entry_step": int(entries[m][k]),
                 "first_input_step": int(entries[m][k]) + 2, "zero_service": bool(np.all(qos[m][k] == 0)),
                 "first_service_step": (int(np.flatnonzero(qos[m][k] > 0)[0]) if np.any(qos[m][k] > 0) else None)}
                for k, w in enumerate(worlds)]
        (tmp_path / "panels" / f"{m}.json").write_text(json.dumps({"rows": rows}), encoding="utf-8")
        arrays = {}
        for k, w in enumerate(worlds):
            arrays[f"world_{k}_seed"] = np.int64(w)
            arrays[f"world_{k}_qos"] = qos[m][k].astype(np.float32)
            arrays[f"world_{k}_target_xy"] = targets[m][k].astype(np.float32)
        np.savez(tmp_path / "traces" / f"{m}.npz", **arrays)
    return worlds


def test_split_and_diagnostics_on_synthetic_run(tmp_path):
    T, n = 20, 2
    # hungarian: 1.0 before its entry (step 10), .5 after; identity: .8 flat; nearest: .2 flat.
    h = np.concatenate([np.ones(10), np.full(10, 0.5)])
    qos = {"hungarian": np.stack([h, h]), "identity": np.full((2, T), 0.8), "independent_nearest": np.full((2, T), 0.2)}
    entries = {"hungarian": [10, 10], "identity": [5, 5], "independent_nearest": [15, 15]}
    # targets: hungarian two distinct fixed points; identity a 70.7 m drift at t=10 for UAV 0 and a 1.9 km
    # jump at t=15 for UAV 1; nearest both on one point.
    tg_h = np.tile(np.array([[0.0, 0.0], [100.0, 0.0]]), (2, T, 1, 1))
    tg_i = tg_h.copy(); tg_i[:, 10:, 0, :] = [50.0, 50.0]; tg_i[:, 15:, 1, :] = [2000.0, 0.0]
    tg_n = np.tile(np.array([[0.0, 0.0], [0.0, 0.0]]), (2, T, 1, 1))
    tg_n[:, 18:, :, :] = np.nan
    targets = {"hungarian": tg_h, "identity": tg_i, "independent_nearest": tg_n}
    worlds = _write_run(tmp_path, qos, entries, targets)
    report = rd.read_stake_traces(tmp_path)
    assert report["worlds"] == worlds and report["steps"] == T
    assert report["trace_panel_consistency"]["problems"] == []
    a = report["A_hungarian_world_clock"]
    assert a["boundaries"] == [10, 10]
    assert a["per_mode_per_step_mean"]["hungarian"] == {"pre": 1.0, "post": 0.5}
    pre = a["differences"]["hungarian_minus_identity_pre"]
    post = a["differences"]["hungarian_minus_identity_post"]
    assert pre["paired_mean"] == pytest.approx(0.2) and pre["worlds_hungarian_leads"] == 2 and pre["paired_se"] == pytest.approx(0.0)
    assert post["paired_mean"] == pytest.approx(-0.3) and post["worlds_hungarian_leads"] == 0
    mass = a["differences"]["pre_window_mass_share_identity"]
    assert mass["pre_mass"] == pytest.approx(2 * 10 * 0.2) and mass["total_mass"] == pytest.approx(2 * (10 * 0.2 - 10 * 0.3))
    assert mass["share"] == pytest.approx(4.0 / -2.0)
    b = report["B_common_step"]
    assert b["boundaries"] == [10, 10] and b["differences"]["hungarian_minus_independent_nearest_pre"]["paired_mean"] == pytest.approx(0.8)
    d = report["trace_diagnostics"]
    assert d["hungarian"]["mean_target_position_changes_per_uav_per_1000_steps"] == 0.0
    assert d["hungarian"]["mean_target_jumps_over_500m_per_uav_per_1000_steps"] == 0.0
    assert d["identity"]["mean_target_position_changes_per_uav_per_1000_steps"] == pytest.approx(2 / n / (T / 1000.0))
    assert d["identity"]["mean_target_jumps_over_500m_per_uav_per_1000_steps"] == pytest.approx(1 / n / (T / 1000.0))
    assert d["hungarian"]["mean_distinct_targets_sampled"] == 2.0 and d["hungarian"]["mean_duplicate_uav_share_sampled"] == 0.0
    assert d["independent_nearest"]["mean_distinct_targets_sampled"] == pytest.approx(1.0)  # sampled t = 0, 10 (finite)
    assert d["independent_nearest"]["mean_target_jumps_over_500m_per_uav_per_1000_steps"] == 0.0
    assert d["independent_nearest"]["mean_duplicate_uav_share_sampled"] == pytest.approx(1.0)
    assert d["independent_nearest"]["mean_finite_target_share"] == pytest.approx(18 / 20)
    assert report["collapse_worlds"] == {"identity": [], "independent_nearest": []}


def test_reader_refuses_mismatched_worlds(tmp_path):
    qos = {m: np.full((1, 4), 0.5) for m in rd.MODES}
    entries = {m: [2] for m in rd.MODES}
    targets = {m: np.zeros((1, 4, 1, 2)) for m in rd.MODES}
    _write_run(tmp_path, qos, entries, targets)
    bad = json.loads((tmp_path / "panels" / "identity.json").read_text())
    bad["rows"][0]["seed"] = 1
    (tmp_path / "panels" / "identity.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        rd.read_stake_traces(tmp_path)


def test_main_writes_json(tmp_path, capsys):
    qos = {m: np.full((1, 4), 0.5) for m in rd.MODES}
    entries = {m: [2] for m in rd.MODES}
    targets = {m: np.zeros((1, 4, 1, 2)) for m in rd.MODES}
    _write_run(tmp_path, qos, entries, targets)
    out = tmp_path / "readings.json"
    assert rd.main(["--out", str(tmp_path), "--json", str(out)]) == 0
    assert json.loads(out.read_text())["steps"] == 4
    assert "A_hungarian_world_clock" in capsys.readouterr().out
