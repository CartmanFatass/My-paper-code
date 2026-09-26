"""Input identity and unchanged-world checks for the fixed B05 recurrence."""

from __future__ import annotations

from dataclasses import asdict, replace
import json
import subprocess
import sys
import types

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import make_config, make_env
from experiments.candidates.uav_service_auxiliary.b04 import native as b04
from experiments.candidates.uav_service_auxiliary.b04.evaluation import evaluate
from experiments.candidates.uav_service_auxiliary.b05 import native
from hmasd.agent import HMASDAgent
from scripts import run_uav_service_auxiliary_b05 as entry


def short_spec(cuda=False):
    return replace(native.production_spec(914173), lanes=4 if cuda else 2, rollouts=1,
                   rollout_length=20, episode_length=20, eval_seeds=(937001,),
                   final_seeds=(938001,), eval_rollouts=(0, 1), ppo_epochs=1, threads=1,
                   hidden_size=None if cuda else 32, gru_hidden_size=None if cuda else 32)


def test_fixed_binding_changes_only_training_seed():
    new, old = native.production_spec(914173), b04.production_spec(914021)
    assert asdict(new) == {**asdict(old), "seed": 914173}
    assert make_config(new).seed == new.seed == 914173
    assert new.transitions == 180000
    assert new.final_seeds == tuple(range(938001, 938033))
    with pytest.raises(ValueError, match="unplanned"):
        native.production_spec(914021)
    with pytest.raises(ValueError, match="unplanned"):
        b04.production_spec(914173)


@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_real_new_seed_reaches_initialization_lanes_and_outputs(tmp_path, monkeypatch, device_name):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("requires actual CUDA")
    spec = short_spec(device_name == "cuda")
    lane_seeds = []
    original_make_env = b04.make_env
    def tracked_env(config, seed):
        lane_seeds.append((config.seed, seed))
        return original_make_env(config, seed)
    monkeypatch.setattr(b04, "make_env", tracked_env)
    results = {}
    for arm in ("N", "R"):
        out = tmp_path / arm
        results[arm] = native.run_native(arm=arm, out=out, launch_sha="ENGINEERING-CHECK",
                                         device_name=device_name, threads=1, spec=spec)
        config = json.loads((out / "config.json").read_text())
        assert config["spec"]["seed"] == config["active"]["seed"] == 914173
        assert results[arm]["object_id"] == "UAV-SERVICE-RISK-B05"
        assert results[arm]["status"] == "COMPLETE"
        assert results[arm]["counts"]["transitions"] == 20 * spec.lanes
        assert all(v > 0 for v in results[arm]["optimizer_steps"].values())
        assert all(v > 0 for v in results[arm]["initialization_displacement_l2"].values())
        assert results[arm]["final_evaluation"]["new_optimizer_updates"] == 0
        with np.load(out / "first_rollout_audit.npz") as audit:
            np.testing.assert_allclose(audit["training_reward"], audit["native_reward"]
                                       - b04.EXTRA_COST[arm] * audit["return_cost"])
    assert lane_seeds == [(914173, 914173+i) for i in range(spec.lanes)] * 2
    assert results["N"]["initialization_sha256"] == results["R"]["initialization_sha256"]
    assert results["N"]["first_collection_sha256"] == results["R"]["first_collection_sha256"]
    # Identical short conditions with the old seed, not a production fit.
    old = b04.run_native(arm="N", out=tmp_path / "old", launch_sha="ENGINEERING-CHECK",
                         device_name=device_name, threads=1, spec=replace(spec, seed=914021))
    assert old["object_id"] == "UAV-SERVICE-RISK-B04"
    assert old["initialization_sha256"] != results["N"]["initialization_sha256"]
    assert old["first_collection_sha256"] != results["N"]["first_collection_sha256"]


def test_exposed_worlds_keep_actual_initial_conditions_and_policy_rng_independence(tmp_path):
    torch.set_num_threads(1)
    new = make_config(short_spec())
    old = make_config(replace(short_spec(), seed=914021))
    panels = native.production_spec(914173)
    for seed in (*panels.eval_seeds, *panels.final_seeds):
        initial = []
        for config in (old, new):
            env = make_env(config, seed)
            try:
                obs, info = env.reset(seed=seed)
                initial.append((obs.copy(), info["state"].copy()))
            finally:
                env.close()
        np.testing.assert_array_equal(initial[0][0], initial[1][0])
        np.testing.assert_array_equal(initial[0][1], initial[1][1])
    device = torch.device("cpu")
    agent = HMASDAgent(new, log_dir=str(tmp_path / "agent"), device=device)
    for policy_seed in (914021, 914173):
        evaluate(agent, new, (937001, 938001), device, policy_seed=policy_seed,
                 log_dir=tmp_path / f"eval-{policy_seed}", trace_path=tmp_path / f"{policy_seed}.npz")
    with np.load(tmp_path / "914021.npz") as a, np.load(tmp_path / "914173.npz") as b:
        assert a.files == b.files
        for key in a.files:
            np.testing.assert_array_equal(a[key], b[key])


@pytest.mark.parametrize("arm", ("N", "R"))
def test_entry_requires_admission_and_forwards_selected_seed(monkeypatch, tmp_path, arm):
    events = []
    admission = types.ModuleType("scripts.hmasd_admission")
    def admit(*args, **kwargs):
        events.append("admission")
        return {"sha": "source"}
    admission.require_admission = admit
    monkeypatch.setitem(sys.modules, admission.__name__, admission)
    def run(**kwargs):
        assert events == ["admission"]
        return kwargs
    monkeypatch.setattr(native, "run_native", run)
    argv = ["--arm", arm, "--seed", "914173", "--out", str(tmp_path / "run"), "--launch-sha", "source"]
    result = entry.main(argv)
    assert result["spec"] == native.production_spec(914173)
    assert result["device_name"] == "cuda" and result["threads"] == 4
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--seed", "914021"])
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--extra-cost", "3"])
    with pytest.raises(RuntimeError, match="SHA"):
        entry.main([*argv, "--launch-sha", "other"])


def test_direct_entry_refuses_before_any_scientific_output(tmp_path):
    out = tmp_path / "never-created"
    result = subprocess.run([sys.executable, entry.__file__, "--arm", "N", "--seed", "914173",
                             "--out", str(out), "--launch-sha", "0" * 40],
                            cwd=entry.ROOT, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0 and "missing HMASD admission" in result.stderr
    assert not out.exists()
