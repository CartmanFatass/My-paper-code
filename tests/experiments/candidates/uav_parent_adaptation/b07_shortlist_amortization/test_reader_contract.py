"""Synthetic reader/admission/retention checks; no host or model invocation."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from experiments.candidates.uav_parent_adaptation.b07_shortlist_amortization import contract, host, outcomes, reader, run


def shortlist_fixture(monkeypatch):
    monkeypatch.setattr(reader, "scalar_features", lambda *args: np.zeros((2, 12)))
    candidates = [dict(member=i, site=1, predicted_total_J=10., predicted_total_served=20.+i,
                       path=10., duration=10, predicted_mask=3) for i in range(2)]
    branches = [dict(id="stay", physical_identity="stay", stationary_candidate=None,
                     summary=dict(total_J=5., total_served=50.))]
    for i in (1, 0):
        branches.append(dict(id=f"m{i}_s1", physical_identity=f"physical{i}",
            stationary_candidate=candidates[i], summary=dict(total_J=6.+i, total_served=50.)))
    selection = dict(champion_candidates=candidates, champion_ids=["m0_s1", "m1_s1"],
        learner=dict(features=[[0.]*12]*2, standardized_features=[[0.]*12]*2,
            predicted_residuals=[-1.,-1.], predicted_advantages=[-1.,-1.],
            zero_beta_fallback=False, feature_distance_pairs=302, coefficient_products=26),
        ordered_champion_indices=[1,0], ordered_champion_ids=["m1_s1","m0_s1"],
        shortlist_indices=[1,0], shortlist_ids=["m1_s1","m0_s1"], branches=branches,
        selected_branch="m1_s1", selected_physical_identity="physical1", initiated=True)
    fitted = dict(beta=[-1.]+[0.]*12, means=[0.]*12, scales=[1.]*12)
    return selection, fitted


def test_independent_reader_preserves_negative_scores_and_menu(monkeypatch):
    s, fitted = shortlist_fixture(monkeypatch)
    result = reader.verify_shortlist(None, 3, s, None, fitted)
    assert result["modeled_branches"] == 3 and result["all_predicted_advantages_negative"]
    assert result["shortlist_ids"] == ["m1_s1", "m0_s1"]
    assert result["maximum_scalar_score_error"] == 0.


@pytest.mark.parametrize("corruption", ["features", "nonfinite", "scores", "order", "menu", "winner", "work"])
def test_independent_reader_rejects_changed_evidence(monkeypatch, corruption):
    s, fitted = shortlist_fixture(monkeypatch)
    s = deepcopy(s)
    if corruption == "features": s["learner"]["features"][0][0] = .1
    if corruption == "nonfinite": s["learner"]["features"][0][0] = float("nan")
    if corruption == "scores": s["learner"]["predicted_advantages"][0] = 0.
    if corruption == "order": s["ordered_champion_indices"] = [0,1]
    if corruption == "menu": s["branches"].pop()
    if corruption == "winner": s["selected_branch"] = "m0_s1"
    if corruption == "work": s["learner"]["feature_distance_pairs"] -= 1
    with pytest.raises(ValueError): reader.verify_shortlist(None, 3, s, None, fitted)


def test_independent_reader_final_J_tie_requires_stay(monkeypatch):
    s, fitted = shortlist_fixture(monkeypatch)
    for b in s["branches"]: b["summary"]["total_J"] = 5.
    s["branches"][1]["summary"]["total_served"] = 100.
    with pytest.raises(ValueError, match="exact final"):
        reader.verify_shortlist(None, 3, s, None, fitted)
    s.update(selected_branch="stay", selected_physical_identity="stay", initiated=False)
    assert reader.verify_shortlist(None, 3, s, None, fitted)["selected_branch"] == "stay"


def test_suffix_begins_after_action40_excluding_pre_action_snapshot():
    connections = np.zeros((501,8,50), dtype=bool)
    connections[:41] = True
    connections[42:,0,0] = True
    result = outcomes.suffix_metrics(connections)
    assert result["suffix_t40_served"] == 459/460
    assert result["suffix_t40_zero_steps"] == result["suffix_t40_longest_zero_run"] == 1
    assert result["suffix_t40_served_min"] == 0 and result["suffix_t40_served_p05"] == 1.
    with pytest.raises(ValueError): outcomes.suffix_metrics(connections[1:])


def test_fresh_bound_panel_source_and_complete_fit_provenance():
    config = contract.fixed_config()
    fitted, old_summary = reader.validate_fit(config)
    assert config["new_fits"] == config["updates"] == config["new_training_acquisition"] == 0
    assert config["fit_artifact"]["sha256"] == contract.FIT_SHA256
    assert old_summary["new_fits"] == 1 and fitted["diagnostics"]["solve_count"] == 1
    assert set(host.bound_worlds()) == set(range(29367000,29367016))
    assert all(host.seed(w,3,8) != host.seed(w,1) for w in host.WORLD_IDS)
    assert config["source_bindings"] == contract.source_bindings()
    assert config["ceilings"]["worker_state_mask_requests"] == 16*(210479+1083573+539613*2)
    assert config["ceilings"]["model_physical_transitions"] == 224*460
    with pytest.raises(ValueError): contract.fixed_config("0"*64)


def test_admission_precedes_scientific_entry(monkeypatch, tmp_path):
    import scripts.hmasd_admission as admission
    from experiments.candidates.uav_parent_adaptation.b07_shortlist_amortization import study
    calls = []
    monkeypatch.setattr(sys, "argv", [str(Path(run.__file__)), "--out", str(tmp_path/contract.TAG),
        "--seed", str(contract.BOOTSTRAP_SEED), "--launch-sha", "a"*40, "--fit-sha256", contract.FIT_SHA256])
    def reject(*args, **kwargs):
        calls.append("admission")
        raise ValueError("no admission")
    monkeypatch.setattr(admission, "require_admission", reject)
    monkeypatch.setattr(study, "run_study", lambda *args: calls.append("science"))
    with pytest.raises(ValueError, match="no admission"): run.main()
    assert calls == ["admission"] and not (tmp_path/contract.TAG).exists()


def test_saved_operation_binds_config_and_manifest(monkeypatch, tmp_path):
    from experiments.candidates.uav_fleet_transmission.study import artifact
    base = {"direction":contract.DIRECTION, "new_fits":0}
    monkeypatch.setattr(contract, "fixed_config", lambda: base)
    config = dict(base, launch_sha="a"*40, admission_command_sha256="b"*64, versions={})
    (tmp_path/"config.json").write_text(json.dumps(config))
    manifest = dict(acceptance="accepted", sha="a"*40, direction=contract.DIRECTION, command_sha256="b"*64)
    (tmp_path/"launch-manifest.json").write_text(json.dumps(manifest))
    summary = dict(config=config, launch_sha="a"*40, config_artifact=artifact(tmp_path/"config.json",tmp_path))
    contract.validate_operation(summary,tmp_path)
    manifest["command_sha256"] = "c"*64
    (tmp_path/"launch-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="manifest"): contract.validate_operation(summary,tmp_path)


@pytest.mark.parametrize("reader_fails", [False, True])
def test_collector_completes_fixed_panel_before_reader_and_preserves_failure(monkeypatch, tmp_path, reader_fails):
    from experiments.candidates.uav_parent_adaptation.b07_shortlist_amortization import study
    calls = []
    monkeypatch.setattr(study.torch, "set_num_threads", lambda n: None)
    monkeypatch.setattr(study.torch, "set_num_interop_threads", lambda n: None)
    monkeypatch.setattr(reader, "validate_fit", lambda config: ({"fixed":"artifact"}, {}))
    def episode(arm, scene, runtime_seed, out, fitted):
        assert fitted == {"fixed":"artifact"}
        calls.append((arm,scene.world_id,runtime_seed))
        return dict(arm=arm,world_id=scene.world_id,steps=500)
    monkeypatch.setattr(study, "evaluate_episode", episode)
    monkeypatch.setattr(study, "verify_prefixes", lambda out, rows: None)
    def read(out):
        saved = json.loads((out/"summary.json").read_text())
        assert saved["status"] == "collected" and saved["worker_status"] == "complete"
        assert len(saved["episodes"]) == len(calls) == 64
        assert saved["new_fits"] == saved["updates"] == saved["new_training_acquisition"] == 0
        if reader_fails: raise ValueError("synthetic full reader failure")
        (out/"reading.json").write_text('{"status":"complete"}\n')
    monkeypatch.setattr(reader, "read_run", read)
    if reader_fails:
        with pytest.raises(ValueError, match="full reader failure"):
            study.run_study(tmp_path,"a"*40,{"command_sha256":"b"*64},contract.FIT_SHA256)
    else:
        study.run_study(tmp_path,"a"*40,{"command_sha256":"b"*64},contract.FIT_SHA256)
    saved = json.loads((tmp_path/"summary.json").read_text())
    assert calls == [(contract.ARMS[(i+j)%4],w,host.seed(w,3,8))
                     for i,w in enumerate(host.WORLD_IDS) for j in range(4)]
    assert saved["status"] == ("failed" if reader_fails else "complete")
    if reader_fails: assert saved["failure_stage"] == "reader" and "reading" not in saved
    else: assert saved["reading"]["path"] == "reading.json" and saved["total_timing"]["cpu_seconds"] >= 0
