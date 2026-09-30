"""B04 source/admission, complete evidence and single-charge cost checks; no native steps."""
from copy import deepcopy
import json

import numpy as np
import pytest

from experiments.candidates.uav_fleet_transmission.b02.controller import empty_counts
from experiments.candidates.uav_fleet_transmission.b04 import reader, run, study
from experiments.candidates.uav_fleet_transmission.b04.host import WORLD_IDS, seed
from experiments.candidates.uav_fleet_transmission.study import artifact, write_json
from scripts import hmasd_admission


def metadata(out):
    config = dict(study.fixed_config(), launch_sha="a" * 40, admission_command_sha256="f" * 64,
                  versions={"python": "fixture", "numpy": "fixture", "torch": "fixture"})
    write_json(out / "config.json", config)
    write_json(out / "launch-manifest.json", {"acceptance": "accepted", "sha": "a" * 40,
        "direction": study.DIRECTION, "command_sha256": "f" * 64})
    rows = [{"arm": study.ARMS[(i + j) % 3], "world_id": world, "n": 8, "steps": 500,
             "complete": True, "runtime_seed": seed(world, 3, 8)}
            for i, world in enumerate(WORLD_IDS) for j in range(3)]
    return {"worker_status": "complete", "status": "collected", "new_fits": 0, "updates": 0,
            "launch_sha": "a" * 40, "config": config,
            "config_artifact": artifact(out / "config.json", out), "episodes": rows}


def test_fixed_source_panel_and_admission_binding(tmp_path):
    summary = metadata(tmp_path)
    assert tuple(reader.validate_worker(summary, tmp_path)) == WORLD_IDS
    changes = [lambda s: s["episodes"].pop(), lambda s: s["episodes"].reverse(),
               lambda s: s["episodes"][0].update(steps=499),
               lambda s: s["episodes"][0].update(runtime_seed=0),
               lambda s: s.update(new_fits=1), lambda s: s.update(status="failed"),
               lambda s: s["config"].update(cycle_reuse=True),
               lambda s: s["config"]["spec"].update(second_t=121),
               lambda s: s["config"]["source_bindings"].pop(next(iter(s["config"]["source_bindings"])))]
    for change in changes:
        bad = deepcopy(summary)
        change(bad)
        with pytest.raises(ValueError):
            reader.validate_worker(bad, tmp_path)
    manifest = json.loads((tmp_path / "launch-manifest.json").read_text())
    write_json(tmp_path / "launch-manifest.json", dict(manifest, command_sha256="e" * 64))
    with pytest.raises(ValueError, match="admission differs"):
        reader.validate_worker(summary, tmp_path)


def test_runner_admission_and_source_gate_precede_collection(monkeypatch, tmp_path):
    calls = []
    def denied(*args, **kwargs):
        raise RuntimeError("fixture admission denied")
    monkeypatch.setattr(hmasd_admission, "require_admission", denied)
    monkeypatch.setattr(study, "run_study", lambda *args: calls.append(args))
    argv = ["--out", str(tmp_path), "--launch-sha", "a" * 40]
    with pytest.raises(RuntimeError, match="admission denied"):
        run.main(argv)
    assert calls == []
    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "b" * 40})
    with pytest.raises(ValueError, match="source SHA"):
        run.main(argv)
    with pytest.raises(ValueError, match="namespace"):
        run.main(argv + ["--seed", "7"])
    assert calls == []


def count(value):
    return {key: value for key in study.COUNT_KEYS}


def test_query_ledger_prices_unique_banks_once_and_each_physical_model_tick():
    native, model = empty_counts(), empty_counts()
    native["motion"] = count(3)
    native["option"] = count(10000)  # A retained copy, not another enumeration.
    model["motion"] = count(5)
    model["option"] = count(10000)
    catalog = {"model_branches": [{"summary": {
        "model_transitions": 460, "ordinary_candidate_position_predictions": 17,
        "controller_counts": model, "reward_counts": count(7)}}],
        "banks": {"one": {"counts": dict(count(11), model_ticks=20), "candidate_count": 9}},
        "candidate_banks": [{"id": "one"}]}
    costs = study.episode_costs(catalog, native, 13)
    assert costs["worker_state_mask_requests"] == 3 + 5 + 7 + 11
    assert costs["model_physical_transitions"] == 460
    assert costs["candidate_transit_ticks"] == 20
    assert costs["stationary_candidate_rows"] == 9
    assert costs["ordinary_candidate_position_predictions"] == 30
    broken = deepcopy(catalog)
    broken["candidate_banks"] = []
    with pytest.raises(ValueError, match="bank ledger"):
        study.episode_costs(broken, native, 13)
    for value in (-1, True, 1.5):
        bad = deepcopy(native)
        bad["motion"]["requested_candidates"] = value
        with pytest.raises(ValueError, match="query counter"):
            study.episode_costs(catalog, bad, 13)


def test_catalog_rejects_duplicate_branch_and_missing_actual_selection(tmp_path):
    row = {"arm": "A2"}
    base = {"plans": {"40": {}, "120": {}}, "selections": {"40": {}, "120": {}},
            "banks": {}, "model_branches": [{"id": "a2/first/stay/inner/stay"}],
            "candidate_banks": []}
    def check(value):
        path = tmp_path / f"catalog{len(list(tmp_path.iterdir()))}.json.gz"
        study.write_catalog(path, value)
        row["evidence_catalog"] = artifact(path, tmp_path)
        return reader.evidence_catalog(row, tmp_path)
    assert check(base) == base
    bad = deepcopy(base)
    bad["model_branches"] *= 2
    with pytest.raises(ValueError, match="duplicated branch"):
        check(bad)
    bad = deepcopy(base)
    bad["selections"].pop("120")
    with pytest.raises(ValueError, match="scheduled selection"):
        check(bad)
    for name in ("../escape", "/absolute", "a//b", "a/./b", "a\\b"):
        with pytest.raises(ValueError, match="identifier"):
            study.identifier_path(name)


def test_worker_failure_preserves_collected_prefix_and_refuses_retry(monkeypatch, tmp_path):
    monkeypatch.setattr(study.torch, "set_num_threads", lambda n: None)
    monkeypatch.setattr(study.torch, "set_num_interop_threads", lambda n: None)
    monkeypatch.setattr(study, "bound_worlds", lambda: {w: None for w in WORLD_IDS})
    calls = []
    def evaluate(arm, scene, runtime_seed, out):
        calls.append(arm)
        if len(calls) == 2:
            raise RuntimeError("constructed second-cell failure")
        return {"arm": arm, "world_id": WORLD_IDS[0], "steps": 500}
    monkeypatch.setattr(study, "evaluate_episode", evaluate)
    with pytest.raises(RuntimeError, match="second-cell failure"):
        study.run_study(tmp_path, "a" * 40, {"command_sha256": "f" * 64})
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert calls == ["T", "G2"] and len(summary["episodes"]) == 1
    assert summary["failure_stage"] == "worker" and summary["status"] == "failed"
    with pytest.raises(ValueError, match="not completed"):
        reader.validate_worker(summary, tmp_path)
    with pytest.raises(FileExistsError, match="existing attempt"):
        study.run_study(tmp_path, "a" * 40, {"command_sha256": "f" * 64})
