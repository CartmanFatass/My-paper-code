from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.energy_relay_benchmark.b01 import native
from experiments.candidates.energy_relay_benchmark.b01.feedback import FeedbackParams
from scripts import run_energy_relay_benchmark_b01 as entry

N_LABEL = "central-state skill conditioning (HMASD coordinator) + local low-level actors"
LOCAL_LABEL = "legal-observation pooled central planner (station-1 ring search prior)"
JITTER = ("station 1 is a jittered anchor: reset user centroid + uniform ±0.12·area_size per axis "
          "(configs/config_1.py line 529; energy_aware.py lines 393–398)")
MECHANISM_TRACE = {"own_xyz": ((8, 3), np.float32), "return_margin": ((8,), np.float32),
                   "nearest_station": ((8,), np.int8),
                   "nearest_station_distance_m": ((8,), np.float32),
                   "guard_checked": ((), np.int32), "guard_blocked": ((), np.int32),
                   "station_occupancy": ((2,), np.int8), "station_queue": ((2,), np.int8)}
MECHANISM_ROW = ("station_xy", "mean_nearest_station_distance_m",
                 "post_exit_recapture_distances_m", "post_exit_recapture_count",
                 "post_exit_recapture_median_m")


def _assert_mechanism_trace(trace, steps, heuristic):
    for key, (shape, dtype) in MECHANISM_TRACE.items():
        array = trace[f"world_0_{key}"]
        assert array.shape == (steps, *shape) and array.dtype == dtype, key
    if heuristic:
        target = trace["world_0_target_xy"]
        assert target.shape == (steps, 8, 2) and target.dtype == np.float32
    else:
        assert "world_0_target_xy" not in trace.files


def test_fixed_spec_worlds_grid_and_phases():
    spec = native.B01Spec()
    assert spec.worlds == tuple(range(955001, 955033)) and len(spec.worlds) == 32
    assert spec.dev_worlds == tuple(range(956001, 956009)) and len(spec.dev_worlds) == 8
    assert spec.null_worlds == tuple(range(953001, 953033))
    assert spec.equivalence_worlds == (952001, 952002, 952003, 952004)
    assert set(native.B10_O_REFERENCE) == set(spec.null_worlds)
    roles = native.world_roles(spec)
    assert roles["null_worlds"] == list(spec.null_worlds) and "dev_worlds only" in roles["exposure_note"]
    assert not hasattr(spec, "enter_margins") and not hasattr(spec, "exit_margins")
    assert (spec.policy_seed, spec.replan_period) == (925031, 30)
    assert spec.controllers is None and spec.heuristic == "H1" and spec.horizon == 3000
    assert native.grid_controllers(spec) == ("N", "H1")
    assert native.grid_controllers(replace(spec, heuristic="H3")) == ("N", "H3")
    grid = native.feedback_grid(spec)
    assert [(p.enter_margin, p.exit_margin) for p in grid] == [
        (0.0, 0.05), (0.0, 0.25), (0.0, 0.45), (0.0, 0.85), (0.20, 0.25), (0.20, 0.45), (0.20, 0.65)]
    record = native.grid_record(spec)
    assert [r["width"] for r in record] == [0.05, 0.25, 0.45, 0.85, 0.05, 0.25, 0.45]
    assert [r["matched_pair_id"] for r in record] == [
        "w0.05", "w0.25", "w0.45", None, "w0.05", "w0.25", "w0.45"]
    assert native.matched_pair_id(FeedbackParams(0.10, 0.15), spec) is None   # not in the grid
    assert native.PHASES == ("equivalence", "null", "heuristic-dev", "reference", "grid", "all")
    assert len(native.phase_panels("grid", spec)) == 14
    assert len(native.phase_panels("grid", spec, ("N", "H3"))) == 14
    dev = native.phase_panels("heuristic-dev", spec)
    assert [c for c, _, _ in dev] == ["H1", "H2", "H3"] and dev[0][2] == spec.dev_worlds
    assert native.phase_panels("equivalence", spec)[0][2] == spec.equivalence_worlds
    assert native.phase_panels("null", spec) == [("N", native.PRODUCTION_PARAMS, spec.null_worlds)]
    assert native.phase_panels("reference", spec) == [
        ("Hlocal", native.PRODUCTION_PARAMS, spec.worlds)]
    assert native.heuristic_params("H3", spec).cruise_mps == 10.0
    local = native.heuristic_params("Hlocal", spec, "H3")
    assert local == replace(native.heuristic_params("H3", spec), information="local")
    assert native.panel_name("Hlocal", native.PRODUCTION_PARAMS) == "Hlocal_e0.00_x0.05"
    assert native.controller_information("H2", spec) == "central-positions"
    assert native.controller_information("N", spec) == N_LABEL
    assert native.controller_information("Hlocal", spec) == LOCAL_LABEL
    assert not hasattr(native, "heuristics_blocked")
    assert native.planned_episodes(spec, "all") == 540 == 4 + 32 + 24 + 32 + 2 * 7 * 32
    assert [native.planned_episodes(spec, phase) for phase in native.RUN_PHASES] == [
        4, 32, 24, 32, 448]
    assert native.planned_episodes(replace(spec, controllers=("N",)), "grid") == 224


def test_null_block_percentiles():
    rows = [{"seed": 953001 + i, "raw_native_J": native.B10_O_REFERENCE[953001 + i][0] + d,
             "qos_per_step": native.B10_O_REFERENCE[953001 + i][1] - d / 100, "actual_length": 3}
            for i, d in enumerate((1.0, -3.0, 2.0, 0.0))]
    rows.append({"seed": 999999, "raw_native_J": 1.0, "qos_per_step": 0.1, "actual_length": 3})
    block = native.null_block(rows)
    assert block["compared_worlds"] == 4 and block["gate"] is None
    assert block["reference_sha256"] == native.B10_O_REFERENCE_SHA256
    np.testing.assert_allclose([w["delta_J"] for w in block["worlds"][:4]], (1.0, -3.0, 2.0, 0.0))
    assert block["worlds"][4]["delta_J"] is None and "b10_J" not in block["worlds"][4]
    assert block["abs_delta_J_p50"] == pytest.approx(np.percentile([1, 3, 2, 0], 50))
    assert block["abs_delta_J_p95"] == pytest.approx(np.percentile([1, 3, 2, 0], 95))
    assert block["abs_delta_J_max"] == pytest.approx(3.0)
    assert block["abs_delta_qos_per_step_max"] == pytest.approx(0.03)


def test_b10_reference_constant_matches_the_tracked_file():
    root = Path(__file__).resolve().parents[5]
    path = root / native.B10_O_REFERENCE_PATH
    assert native.sha256_file(path) == native.B10_O_REFERENCE_SHA256
    worlds = json.loads(path.read_text())["panels"]["O"]["worlds"]
    assert {w["seed"]: (w["raw_native_J"], w["qos_per_actual_step"]) for w in worlds} == \
        native.B10_O_REFERENCE


def test_thread_defaults_and_oversubscription_refusal(tmp_path, monkeypatch):
    spec = native.B01Spec()
    cpus = os.cpu_count()
    assert spec.threads == 2 == entry.DEFAULT_THREADS
    assert spec.workers == min(8, cpus // 2) == entry.default_workers()
    assert entry.parse_args(["--out", "o", "--launch-sha", "s", "--phase", "all"]).workers == spec.workers
    native.check_resources(spec)
    native.check_resources(replace(spec, workers=4, threads=4), cpu_count=16)
    with pytest.raises(ValueError, match="exceeds"):
        native.check_resources(replace(spec, workers=5, threads=4), cpu_count=16)
    for fake in (1, 2, 3, 64):
        monkeypatch.setattr(native.os, "cpu_count", lambda fake=fake: fake)
        assert native.default_workers() == max(1, min(8, fake // 2))
    monkeypatch.undo()
    out = tmp_path / "never"
    with pytest.raises(ValueError, match="exceeds"):
        native.run_native(out=out, launch_sha="fixture", checkpoint=None, phase="all",
                          spec=replace(spec, workers=cpus, threads=2))
    assert not out.exists()


def tiny_spec(**changes):
    values = dict(worlds=(955001,), dev_worlds=(956001,), null_worlds=(953001,),
                  equivalence_worlds=(952001,), controllers=("N",),
                  grid_settings=((0.0, 0.05), (0.0, 0.25)), horizon=20, workers=1,
                  threads=1, checkpoint_sha256=None, policy_fingerprint=None)
    return replace(native.B01Spec(), **(values | changes))


def _keys(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from _keys(value)


PHASE_SPLIT = ("qos_per_step_pre_entry", "qos_per_step_entry_to_input", "qos_per_step_post_input",
               "steps_pre_entry", "steps_entry_to_input", "steps_post_input",
               "first_entry_step", "first_input_step", "mode_uav_step_fraction")


def test_tiny_grid_run_writes_records(tmp_path, fresh_checkpoint):
    spec = tiny_spec()
    out = tmp_path / "grid"
    summary = native.run_native(out=out, launch_sha="fixture", checkpoint=fresh_checkpoint,
                                phase="grid", spec=spec, argv=["fixture"])
    assert summary["status"] == "COMPLETE"
    assert summary["counts"]["episodes_completed"] == 2 and summary["counts"]["steps"] == 40
    config = json.loads((out / "config.json").read_text())
    assert config["checkpoint_sha256"] and config["spec"]["horizon"] == 20
    assert config["observation_layout"]["offsets"]["energy_uavs"] == [245, 349]
    assert [p["name"] for p in config["planned_panels"]["grid"]] == ["N_e0.00_x0.05", "N_e0.00_x0.25"]
    written = json.loads((out / "summary.json").read_text())
    assert set(written["panels"]) == {"grid/N_e0.00_x0.05", "grid/N_e0.00_x0.25"}
    assert written["peak_rss_kib"]["runner"] > 0 and written["wall_seconds"] > 0
    panel = json.loads((out / "grid" / "panels" / "N_e0.00_x0.25.json").read_text())
    row = panel["worlds"][0]
    assert row["seed"] == 955001 and all(key in row for key in PHASE_SPLIT)
    assert (row["width"], row["matched_pair_id"]) == (0.25, None)   # tiny grid has no pairs
    assert not [key for key in _keys(written) if "presen" in key]
    with np.load(out / "grid" / "traces" / "N_e0.00_x0.25.npz") as trace:
        assert trace["world_0_reward"].dtype == np.float32
        assert trace["world_0_battery"].shape == (20, 8)
        _assert_mechanism_trace(trace, 20, heuristic=False)
    assert all(key in row for key in MECHANISM_ROW)
    assert row["controller_information"] == panel["controller_information"] == N_LABEL
    assert config["planned_episodes"] == written["planned_episodes"] == 2
    assert config["controller_information"]["N"] == N_LABEL
    assert "decision time" in config["trace_timing"]
    with pytest.raises(FileExistsError):
        native.run_native(out=out, launch_sha="fixture", checkpoint=fresh_checkpoint,
                          phase="grid", spec=spec)


def test_phase_all_end_to_end(tmp_path, fresh_checkpoint):
    spec = tiny_spec(horizon=30, grid_settings=((0.0, 0.05), (0.20, 0.25), (0.0, 0.85)),
                     workers=2)
    out = tmp_path / "all"
    summary = native.run_native(out=out, launch_sha="fixture", checkpoint=fresh_checkpoint,
                                phase="all", spec=spec, argv=["fixture"])
    assert summary["status"] == "COMPLETE"
    selected = summary["selected_heuristic"]
    scores = summary["heuristic_dev_mean_J"]
    assert selected == max(("H1", "H2", "H3"), key=lambda n: (scores[n], -int(n[1])))
    written = json.loads((out / "summary.json").read_text())
    config = json.loads((out / "config.json").read_text())
    assert written["selected_heuristic"] == selected
    for record in (written, config):
        roles = record["world_roles"]
        assert (roles["worlds"], roles["dev_worlds"], roles["null_worlds"],
                roles["equivalence_worlds"]) == ([955001], [956001], [953001], [952001])
        assert roles["exposure_note"].startswith("955xxx/956xxx unexposed")
    assert [r["matched_pair_id"] for r in config["grid_settings"]] == ["w0.05", "w0.05", None]
    assert set(written["panels"]) == {
        "equivalence/N_e0.00_x0.05", "null/N_e0.00_x0.05",
        "heuristic-dev/H1_e0.00_x0.05", "heuristic-dev/H2_e0.00_x0.05",
        "heuristic-dev/H3_e0.00_x0.05", "reference/Hlocal_e0.00_x0.05",
        "grid/N_e0.00_x0.05", "grid/N_e0.20_x0.25", "grid/N_e0.00_x0.85",
        f"grid/{selected}_e0.00_x0.05", f"grid/{selected}_e0.20_x0.25",
        f"grid/{selected}_e0.00_x0.85"}
    assert written["counts"]["episodes_completed"] == 12 and written["counts"]["steps"] == 360
    assert config["planned_episodes"] == written["planned_episodes"] == 12
    boundary = config["controller_boundary"]
    assert JITTER in boundary and N_LABEL in boundary and LOCAL_LABEL in boundary
    assert "central-positions" in boundary
    for record in (written, config):
        assert record["controller_information"] == {
            "N": N_LABEL, "H1": "central-positions", "H2": "central-positions",
            "H3": "central-positions", "Hlocal": LOCAL_LABEL}
    assert written["counts"]["failed_worlds"] == 0
    null = written["null"]
    assert null["worlds"][0]["seed"] == 953001 and null["compared_worlds"] == 1
    for label in ("J", "qos_per_step"):
        for suffix in ("p50", "p95", "max"):
            assert isinstance(null[f"abs_delta_{label}_{suffix}"], float)
    assert null["worlds"][0]["b10_J"] == native.B10_O_REFERENCE[953001][0]
    assert written["panels"]["null/N_e0.00_x0.05"]["b10_reference"] == null
    for name, panel in written["panels"].items():
        row = panel["worlds"][0]
        assert all(key in row for key in PHASE_SPLIT), name
        for key in ("guard_checked_actions", "guard_blocked_actions"):
            assert isinstance(row[key], int) and row[key] >= 0, (name, key)
        assert row["guard_blocked_actions"] <= row["guard_checked_actions"]
        assert row["failed"] is False
        assert all(f"observed_{key}" in panel["aggregate"] for key in PHASE_SPLIT[:3])
        assert all(key in row for key in MECHANISM_ROW), name
        assert row["post_exit_recapture_count"] == len(row["post_exit_recapture_distances_m"])
        assert len(row["station_xy"]) == 2
        phase_dir, panel_file = name.split("/")
        with np.load(out / phase_dir / "traces" / f"{panel_file}.npz") as trace:
            _assert_mechanism_trace(trace, 30, heuristic=panel["controller"].startswith("H"))
        if name.startswith("grid/"):
            assert (row["width"], row["matched_pair_id"]) == (
                panel["width"], panel["matched_pair_id"])
            expected = {"e0.00_x0.05": (0.05, "w0.05"), "e0.20_x0.25": (0.05, "w0.05"),
                        "e0.00_x0.85": (0.85, None)}[name.split("_", 1)[1]]
            assert (row["width"], row["matched_pair_id"]) == expected
        if panel["controller"] == "Hlocal":
            assert panel["controller_information"] == LOCAL_LABEL
            assert row["controller_information"] == panel["controller_information"]
            assert panel["plan_source"] == "legal-observation" and row["plan_input_steps"] == 0
            assert panel["params_from_variant"] == selected
            assert panel["heuristic_params"]["information"] == "local"
            assert panel["heuristic_params"]["n_service"] == native.VARIANTS[selected].n_service
        elif panel["controller"].startswith("H"):
            assert panel["controller_information"] == "central-positions"
            assert row["controller_information"] == panel["controller_information"]
            assert panel["plan_source"] == "env-ground-truth"
            assert row["plan_input_steps"] == 1
        else:
            assert panel["controller_information"] == N_LABEL
            assert row["controller_information"] == N_LABEL
    assert not [key for key in _keys(written) if "presen" in key]
    for phase in native.RUN_PHASES:
        for kind in ("panels", "traces"):
            assert sorted(p.name for p in (out / phase / kind).iterdir()), (phase, kind)
        for path in (out / phase / "panels").iterdir():
            assert not [key for key in _keys(json.loads(path.read_text())) if "presen" in key]
    assert len(list((out / "heuristic-dev" / "panels").iterdir())) == 3
    equivalence = written["panels"]["equivalence/N_e0.00_x0.05"]["b09_reference"][0]
    assert equivalence["seed"] == 952001 and equivalence["b09_J"] is not None
    assert isinstance(equivalence["delta_J"], float)
    events = [json.loads(line) for line in (out / "progress.jsonl").read_text().splitlines()]
    kinds = [event["event"] for event in events]
    assert all("phase" in event for event in events)
    assert kinds[0] == "run_start" and kinds[-1] == "run_end" and events[-1]["status"] == "COMPLETE"
    assert [e["phase"] for e in events if e["event"] == "phase_start"] == list(native.RUN_PHASES)
    assert kinds.count("panel_start") == kinds.count("panel_end") == 12
    assert kinds.count("world_end") == 12 and kinds.count("selected_heuristic") == 1
    starts = [i for i, e in enumerate(events) if e["event"] == "phase_start"]
    assert starts[2] < kinds.index("selected_heuristic") < starts[3]


def test_reference_phase_alone_uses_heuristic_flag_without_checkpoint(tmp_path):
    spec = tiny_spec(heuristic="H2", horizon=10)
    out = tmp_path / "reference"
    summary = native.run_native(out=out, launch_sha="fixture", checkpoint=None,
                                phase="reference", spec=spec, argv=["fixture"])
    assert summary["status"] == "COMPLETE" and summary["selected_heuristic"] == "H2"
    panel = summary["panels"]["reference/Hlocal_e0.00_x0.05"]
    assert panel["heuristic_params"]["n_service"] == 5 and panel["params_from_variant"] == "H2"
    assert panel["worlds"][0]["search_replans"] == 1   # nothing visible at reset: ring prior


def test_entry_refuses_without_admission_and_parses(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    def refuse(*args, **kwargs):
        raise RuntimeError("no admission")

    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    target = tmp_path / "never-created"
    with pytest.raises(RuntimeError, match="no admission"):
        entry.main(["--out", str(target), "--launch-sha", "abc", "--phase", "grid"])
    assert not target.exists()

    args = entry.parse_args([
        "--out", str(target), "--launch-sha", "abc", "--checkpoint", "x/agent.pt",
        "--phase", "equivalence", "--controllers", "N,H2,H3", "--workers", "3",
        "--threads", "2", "--device", "cpu"])
    assert args.controllers == ("N", "H2", "H3") and args.workers == 3 and args.threads == 2
    assert entry.parse_args(["--out", "o", "--launch-sha", "s", "--phase", "all"]).phase == "all"
    assert args.checkpoint == Path("x/agent.pt") and args.phase == "equivalence"
    default = entry.parse_args(["--out", "o", "--launch-sha", "s", "--phase", "grid"])
    assert default.controllers is None and default.heuristic == "H1"
    assert entry.PHASES == native.PHASES
    for phase in native.PHASES:
        assert entry.parse_args(["--out", "o", "--launch-sha", "s", "--phase", phase]).phase == phase
    with pytest.raises(SystemExit):
        entry.parse_args(["--out", "o", "--launch-sha", "s", "--phase", "reference",
                          "--heuristic", "Hlocal"])
    with pytest.raises(SystemExit):
        entry.parse_args(["--out", "o", "--launch-sha", "s", "--phase", "grid", "--controllers", "Z"])

    calls = {}
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda script, direction: calls.setdefault("admission", (script, direction)) and {"sha": "abc"})
    from experiments.candidates.energy_relay_benchmark.b01 import native as native_module
    monkeypatch.setattr(native_module, "run_native", lambda **kwargs: calls.setdefault("run", kwargs))
    entry.main(["--out", str(target), "--launch-sha", "abc", "--phase", "grid",
                "--controllers", "N", "--workers", "2", "--threads", "1"])
    assert calls["admission"][1] == "energy_relay_benchmark"
    assert Path(calls["admission"][0]).name == "run_energy_relay_benchmark_b01.py"
    spec = calls["run"]["spec"]
    assert (spec.controllers, spec.workers, spec.threads) == (("N",), 2, 1)
    calls.pop("run")
    entry.main(["--out", str(target), "--launch-sha", "abc", "--phase", "reference",
                "--heuristic", "H3"])
    spec = calls["run"]["spec"]
    assert (spec.heuristic, spec.controllers, calls["run"]["phase"]) == ("H3", None, "reference")
    assert native_module.grid_controllers(spec) == ("N", "H3")
    with pytest.raises(RuntimeError, match="launch SHA"):
        monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "zzz"})
        entry.main(["--out", str(target), "--launch-sha", "abc", "--phase", "grid"])
