"""Synthetic publication/reading checks; no scientific model or trajectory."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from experiments.candidates.acvc.fresh_dense_package_c01 import protocol as p


def synthetic_units():
    return [{"master": master, "evaluation_namespace": namespace, "complete": True,
             "contrasts": {name: {"mean_J": value, "conditional_SE_J": 1000.0}
                           for name, value in (("F-C", .05 + i * .01),
                                               ("F-dwell", .01 + i * .01),
                                               ("dwell-C", .04))}}
            for i, (master, namespace) in enumerate(p.UNITS)]


def test_complete_fit_panel_variance_and_two_primary_conjunction():
    result = p.aggregate(synthetic_units())
    assert result["complete"]
    assert result["t_quantile"] == {"probability": .9875, "df": 4,
                                    "value": pytest.approx(3.49540593, abs=1e-7)}
    for contrast, expected_mean in (("F-C", .07), ("F-dwell", .03)):
        observed = result["primary"][contrast]
        assert observed["mean_J"] == pytest.approx(expected_mean)
        assert observed["fit_panel_SE_J"] == pytest.approx(math.sqrt(.00005))
        assert observed["lower_J"] == pytest.approx(expected_mean - 3.49540593 * math.sqrt(.00005))
    assert result["primary"]["F-C"]["reading"] == "ABOVE_MEI"
    assert result["primary"]["F-dwell"]["reading"] == "UNRESOLVED"
    assert result["joint_reading"] == "JOINT_NOT_ESTABLISHED"
    assert result["secondary_dwell_C_mean_J"] == pytest.approx(.04)
    assert "actual neural-training calibration is not established" in result["qualification"]
    favorable = synthetic_units()
    for unit in favorable:
        unit["contrasts"]["F-dwell"]["mean_J"] += .04
    assert p.aggregate(favorable)["joint_reading"] == "JOINT_ABOVE_MEI"
    extreme = synthetic_units()
    extreme[0]["contrasts"]["F-C"]["mean_J"] = -1.0
    retained = p.aggregate(extreme)
    assert retained["primary"]["F-C"]["unit_means_J"][0] == -1.0
    assert retained["joint_reading"] == "JOINT_NOT_ESTABLISHED"


@pytest.mark.parametrize("lower,upper,reading", [
    (-.03, -.001, "BELOW_ZERO"), (-.03, 0.0, "AT_OR_BELOW_MEI"),
    (-.01, .01, "AT_OR_BELOW_MEI"), (.01, .04, "UNRESOLVED"),
    (.0100001, .04, "ABOVE_MEI"), (-.01, .04, "UNRESOLVED"),
])
def test_strict_frozen_interval_boundaries(lower, upper, reading):
    assert p.interval_reading(lower, upper) == reading


def test_no_four_fit_duplicate_or_successful_survivor_interval():
    units = synthetic_units()
    duplicate = copy.deepcopy(units)
    duplicate[4] = duplicate[0]
    incomplete = copy.deepcopy(units)
    incomplete[0]["complete"] = False
    for candidate in (units[:4], duplicate, incomplete, list(reversed(units))):
        result = p.aggregate(candidate)
        assert not result["complete"]
        assert result["primary"] is None and result["joint_reading"] == "INCOMPLETE"
        assert result["units"] == candidate


def write_synthetic_unit(root):
    master, namespace = p.UNITS[0]
    unit_path = root / f"unit_{master}"
    unit_path.mkdir()
    summary = {"object": p.OBJECT, "master": master, "evaluation_namespace": namespace,
               "status": "complete", "fit_complete": True, "checkpoint_complete": True,
               "counts": {"train_episodes": 512, "eval_episodes": 192,
                          "train_team_steps": 131072, "eval_team_steps": 49152,
                          "optimizer_steps": 1024, "update_records": 1024,
                          "new_fits": 1, "post_fit_loads": 3}}
    (unit_path / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    rows = [{"phase": "train", "master": master, "base": master, "episode": e,
             "reset_seed": 100000 * master + 1000 + e, "steps": 256,
             "S": float(e), "J": float(e) / 256} for e in range(512)]
    for arm, offset in (("C", 0.0), ("F", .0625), ("dwell", .03125)):
        for e in range(64):
            value = e / 256 + offset - (.125 if arm == "F" and e == 0 else 0)
            rows.append({"phase": "eval", "base": master, "evaluation_namespace": namespace,
                         "arm": arm, "episode": e, "steps": 256,
                         "reset_seed": 100000 * namespace + 2000 + e,
                         "S": value * 256, "J": value})
    updates = [{"master": master, "rollout": k // 4, "epoch": k % 4,
                "episodes": [2 * (k // 4), 2 * (k // 4) + 1]} for k in range(1024)]
    for name, records in (("episodes.jsonl", rows), ("updates.jsonl", updates)):
        (unit_path / name).write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    return unit_path, rows


def test_byte_reader_pairs_worlds_preserves_adverse_and_limits_missing_units(tmp_path):
    unit_path, rows = write_synthetic_unit(tmp_path)
    unit = p.read_unit(tmp_path, *p.UNITS[0])
    assert unit["complete"] and unit["resources"] == "resources_unmeasured"
    assert unit["contrasts"]["F-C"]["mean_J"] == pytest.approx(.0625 - .125 / 64)
    assert unit["contrasts"]["F-C"]["adverse_episode_ids"] == [0]
    assert unit["contrasts"]["F-C"]["minimum_J"] == -.0625
    assert len(unit["training_curve_J"]) == 512
    missing = p.analyze(tmp_path)
    assert not missing["complete"] and missing["primary"] is None
    assert missing["units"][0]["complete"]
    rows[512 + 64]["reset_seed"] += 1
    (unit_path / "episodes.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    broken = p.read_unit(tmp_path, *p.UNITS[0])
    assert not broken["complete"]
    assert not broken["contrasts"]["F-C"]["panel_complete"]
    assert broken["contrasts"]["dwell-C"]["panel_complete"]
    rows[512 + 64]["reset_seed"] -= 1
    rows.append(rows[-1])
    (unit_path / "episodes.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    duplicate = p.read_unit(tmp_path, *p.UNITS[0])
    assert not duplicate["complete"]
    assert any("duplicate" in issue for issue in duplicate["issues"])


def test_all_five_cli_bindings_call_only_full_fitter(tmp_path, monkeypatch):
    calls = []
    def record(*args, **kwargs):
        calls.append((args, kwargs))
        return 0
    monkeypatch.setitem(sys.modules, "scripts.run_acvc_fresh_dense_reuse_b01", SimpleNamespace(run=record))
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_fresh_dense_package_c01.py"
    spec = importlib.util.spec_from_file_location("c01_runner", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for master, namespace in p.UNITS:
        output = tmp_path / str(master)
        monkeypatch.setattr(sys, "argv", [str(script), "--seed", str(master), "--output", str(output),
                                         "--launch-sha", "synthetic", "--execution-seconds", "260"])
        assert module.main() == 0
        args, kwargs = calls[-1]
        assert args == (output, "synthetic", module.PROCESS_START, 260.0)
        assert kwargs == {"master": master, "evaluation_namespace": namespace,
                          "object_name": p.OBJECT, "card_path": p.CARD,
                          "mode": "PROVISIONAL_SINGLE_TASK_C_BENCH_UNIT", "allocation_seconds": p.CAPS}
        assert not output.exists()
    assert len(calls) == 5
