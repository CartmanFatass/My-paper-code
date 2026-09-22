from __future__ import annotations

import copy
import importlib
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _rng_state, make_config, seed_everything, sha256_file,
)
from experiments.candidates.uav_service_auxiliary.b03.endpoint_replay import run_replay
from experiments.candidates.uav_service_auxiliary.b03.facts import evaluate
from experiments.candidates.uav_service_auxiliary.b03.native import B03Spec, production_spec, run_native
from hmasd.agent import HMASDAgent


def _small_spec(*, native_dimensions=False):
    return B03Spec(lanes=4 if native_dimensions else 1, rollouts=1, rollout_length=12, episode_length=12,
                   window=3, threads=1, eval_seeds=(920001,), fact_seeds=(932201,),
                   endpoint_fact_seeds=(933201,), final_seeds=(936001,), eval_rollouts=(0, 1),
                   ppo_epochs=1, hidden_size=None if native_dimensions else 32,
                   gru_hidden_size=None if native_dimensions else 32)


@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_real_s7_dsg_collection_update_checkpoint_and_common_endpoint_replay(tmp_path, device_name):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA path requires an actual CUDA runtime")
    spec = _small_spec(native_dimensions=device_name == "cuda")
    results = {}
    for arm in ("D", "S", "G"):
        extra = {} if arm == "D" else {
            "facts": tmp_path / "D/facts.npz", "facts_sha256": results["D"]["facts_sha256"],
            "calibration": tmp_path / "D/calibration.json", "calibration_sha256": results["D"]["calibration_sha256"],
        }
        results[arm] = run_native(arm=arm, out=tmp_path / arm, launch_sha="ENGINEERING-CORRECTNESS",
                                  device_name=device_name, threads=1, spec=spec, **extra)
        result = results[arm]
        assert result["status"] == "COMPLETE"
        assert result["counts"]["transitions"] == 12 * spec.lanes
        assert result["counts"]["evaluation_transitions"] == 36
        assert result["counts"]["fact_transitions"] == (24 if arm == "D" else 12)
        assert result["counts"]["reused_fact_transitions"] == (0 if arm == "D" else 12)
        assert all(step > 0 for step in result["optimizer_steps"].values())
        assert all(distance > 0 for distance in result["initialization_displacement_l2"].values())
        assert result["evaluations"]["0"]["initial_common_fact"]["observation_mse"] is not None
        assert result["first_rollout_checks"] == results["D"]["first_rollout_checks"]
        assert result["calibration_sha256"] == results["D"]["calibration_sha256"]
        assert result["facts_sha256"] == results["D"]["facts_sha256"]
        world = result["final_evaluation"]["worlds"][0]
        assert world["episode_minimum_battery_ratio"] <= world["battery_min_ratio_per_step"]
        assert world["delivered_end_to_end_throughput_mbps_per_step"] == pytest.approx(
            30 * world["qos_satisfaction_ratio_per_step"], rel=1e-6)
        with np.load(tmp_path / arm / "endpoint_facts.npz", allow_pickle=False) as facts:
            assert facts["episode_0_actions"].shape == (12, 8, 4)
            assert facts["episode_0_dones"].tolist() == [False] * 11 + [True]
    inputs = {arm: (tmp_path / arm, sha256_file(tmp_path / arm / "summary.json")) for arm in ("D", "S", "G")}
    # The production default must refuse valid but shortened engineering artifacts.
    with pytest.raises(ValueError, match="fixed B03 production specification"):
        run_replay(inputs=inputs, seed=spec.seed, out=tmp_path / "refused-replay", launch_sha="ENGINEERING-CORRECTNESS",
                    training_sha="ENGINEERING-CORRECTNESS", device_name=device_name, threads=1)
    replay = run_replay(inputs=inputs,
                        seed=spec.seed, out=tmp_path / "replay", launch_sha="ENGINEERING-CORRECTNESS",
                        training_sha="ENGINEERING-CORRECTNESS", device_name=device_name, threads=1, spec=spec)
    assert replay["status"] == "COMPLETE"
    assert replay["new_fits"] == replay["new_environment_transitions"] == replay["new_optimizer_updates"] == 0
    for arm in ("D", "S", "G"):
        assert replay["arms"][arm]["aggregate"]["service_mse_episodes"] == 3
        assert replay["arms"][arm]["policy_sha256_before_after"] == results[arm]["final_policy_sha256"]
    persisted = json.loads((tmp_path / "replay/summary.json").read_text())
    assert persisted["status"] == "COMPLETE"


def test_fact_collection_preserves_rng_normalizers_and_records_real_commands(tmp_path):
    spec = _small_spec()
    device = torch.device("cpu")
    seed_everything(spec.seed, device)
    config = make_config(spec)
    agent = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=device)
    before = _rng_state()
    normalizers = copy.deepcopy((agent.obs_norm, agent.state_norm))
    panel = evaluate(agent, config, spec.fact_seeds, device, policy_seed=spec.seed,
                      log_dir=tmp_path / "evaluator", fact_path=tmp_path / "facts.npz",
                      fact_metadata={"kind": "initial", "block_seed": spec.seed, "source_arm": "D"})
    after = _rng_state()
    assert before["python"] == after["python"]
    assert torch.equal(before["torch"], after["torch"])
    np.testing.assert_array_equal(before["numpy"][1], after["numpy"][1])
    assert before["numpy"][2:] == after["numpy"][2:]
    assert (agent.obs_norm, agent.state_norm) == normalizers  # native B03 has these disabled
    assert panel["new_optimizer_updates"] == 0


@pytest.mark.parametrize("seed", (912211, 912347))
@pytest.mark.parametrize("arm", ("D", "S", "G"))
def test_production_entry_admits_before_science_and_binds_all_inputs(monkeypatch, tmp_path, seed, arm):
    entry = importlib.import_module("scripts.run_uav_service_auxiliary_b03")
    events = []
    admission = types.ModuleType("scripts.hmasd_admission")
    def admit(*args, **kwargs):
        events.append("admission")
        return {"sha": "source"}
    admission.require_admission = admit
    monkeypatch.setitem(sys.modules, "scripts.hmasd_admission", admission)
    candidate_name = "experiments.candidates.uav_service_auxiliary.b03.native"
    candidate = types.ModuleType(candidate_name)
    candidate.production_spec = production_spec
    def run(**kwargs):
        assert events == ["admission"]
        return kwargs
    candidate.run_native = run
    monkeypatch.setitem(sys.modules, candidate_name, candidate)
    argv = ["--arm", arm, "--seed", str(seed), "--out", str(tmp_path / "run"), "--launch-sha", "source"]
    if arm != "D":
        argv += ["--facts", str(tmp_path / "f"), "--facts-sha256", "fd", "--calibration", str(tmp_path / "c"), "--calibration-sha256", "cd"]
    result = entry.main(argv)
    spec = result["spec"]
    assert spec.seed == seed and spec.transitions == 180000
    assert tuple(spec.final_seeds) == tuple(range(936001, 936033))
    assert spec.fact_seeds == ((932201, 932202) if seed == 912211 else (932211, 932212))
    assert result["device_name"] == "cuda"


def test_first_run_cannot_import_test_derived_scale_or_missing_artifacts(tmp_path):
    entry = importlib.import_module("scripts.run_uav_service_auxiliary_b03")
    basic = ["--seed", "912211", "--out", str(tmp_path), "--launch-sha", "s"]
    with pytest.raises(SystemExit):
        entry.parse_args(["--arm", "D", *basic, "--calibration", "unexpected"])
    with pytest.raises(SystemExit):
        entry.parse_args(["--arm", "G", *basic])
