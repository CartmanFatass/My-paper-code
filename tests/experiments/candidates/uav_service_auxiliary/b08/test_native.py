"""Binding, identity, evaluator, and admission checks for B08's bounded pieces."""

from __future__ import annotations

import subprocess
import sys
import types
from dataclasses import replace

import numpy as np
import pytest
import torch
from torch import nn

from experiments.candidates.uav_service_auxiliary.b04.evaluation import TRACE_FIELDS
from experiments.candidates.uav_service_auxiliary.b01.native import make_config
from experiments.candidates.uav_service_auxiliary.b08 import native
from scripts import run_uav_service_auxiliary_b08 as entry


class _FakeAgent:
    def __init__(self):
        self.skill_coordinator = nn.Linear(2, 2)
        self.skill_discoverer = nn.Linear(2, 2)
        self.team_discriminator = nn.Linear(2, 2)
        self.individual_discriminator = nn.Linear(2, 2)
        self.obs_norm = self.state_norm = None
        self.value_norm_coordinator = self.value_norm_discoverer = None
        self.training = True
        self.env_pending_high_level = {}
        self.env_timers = {}
        self.env_reward_sums = {}


def _world(seed):
    return {"seed": seed}


def _panel_arrays(seed):
    prefix = "episode_0_"
    arrays = {
        prefix + "seed": np.asarray(seed),
        prefix + "metrics": np.zeros((2, len(TRACE_FIELDS)), dtype=np.float64),
    }
    for key in ("mode_before", "mode", "entry", "exit"):
        arrays[prefix + key] = np.zeros((2, 8), dtype=bool)
    for key in ("charger_input_wh", "signed_stored_energy_delta_wh"):
        arrays[prefix + key] = np.zeros((2, 8), dtype=np.float64)
    throughput_column = TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")
    arrays[prefix + "metrics"][:, throughput_column] = (2.0, 3.0)
    return arrays


def test_fixed_production_binding_and_training_rights():
    spec = native.production_spec(915031)
    config = native.make_b08_config(spec)
    record = native.fixed_config_record(spec, config)
    assert spec.transitions == 180000
    assert spec.lanes == 2 and spec.rollout_length == spec.episode_length == 3000
    assert spec.eval_seeds == tuple(range(941001, 941009))
    assert spec.final_seeds == tuple(range(942001, 942033))
    assert record["arm_order"] == ["N", "A"]
    assert record["training_feedback"] == {"N": False, "A": True}
    assert record["lane_initial_seeds"] == [915031, 915032]
    assert record["transitions_per_phase"] == 6000
    assert record["training_return_coefficient"] == 2.0
    assert record["extra_training_cost_coefficient"] == 0.0
    with pytest.raises(ValueError, match="unplanned"):
        native.production_spec(915032)


def test_initialization_identity_includes_buffers_normalizers_and_eval_state():
    torch.manual_seed(7)
    first = _FakeAgent()
    torch.manual_seed(7)
    second = _FakeAgent()
    identity = native.initialization_identity(first)
    native.assert_common_initialization(identity, native.initialization_identity(second))
    with torch.no_grad():
        second.skill_coordinator.bias.add_(1.0)
    with pytest.raises(RuntimeError, match="initialization identity mismatch"):
        native.assert_common_initialization(identity, native.initialization_identity(second))
    assert set(identity["components"]) == {
        "skill_coordinator", "skill_discoverer", "team_discriminator",
        "individual_discriminator", "normalizers", "evaluation_state", "rng_state",
    }


def test_real_agents_from_same_seed_have_identical_actual_initial_artifacts(tmp_path):
    spec = replace(
        native.production_spec(915031), lanes=1, rollouts=1,
        rollout_length=10, episode_length=10, hidden_size=32, gru_hidden_size=32,
        eval_seeds=(941001,), final_seeds=(942001,),
    )
    config = make_config(spec)
    first, first_identity = native.new_initialized_agent(
        config, device=torch.device("cpu"), log_dir=tmp_path / "first"
    )
    second, second_identity = native.new_initialized_agent(
        config, device=torch.device("cpu"), log_dir=tmp_path / "second"
    )
    native.assert_common_initialization(first_identity, second_identity)
    assert first_identity["sha256"] == second_identity["sha256"]
    assert first.rollout_buffer.get_sampler_rng_state() == second.rollout_buffer.get_sampler_rng_state()


def test_feedback_evaluation_is_f_only_and_adds_anchor(monkeypatch, tmp_path):
    agent = _FakeAgent()
    calls = []
    def fake_evaluate(agent_arg, config, seeds, device, **kwargs):
        calls.append((tuple(seeds), kwargs["mode"], kwargs["policy_seed"]))
        return {
            "worlds": [_world(seeds[0])], "aggregate": {},
            "actual_transitions": 2, "new_optimizer_updates": 0, "new_fits": 0,
            "trace_sha256": "fixture",
        }, _panel_arrays(seeds[0])
    monkeypatch.setattr(native, "evaluate_panel", fake_evaluate)
    config = types.SimpleNamespace(time_step=2.0)
    result, _ = native.evaluate_feedback_panel(
        agent, config, (941001,), torch.device("cpu"),
        trace_path=tmp_path / "trace.npz", log_dir=tmp_path / "logs",
    )
    assert calls == [((941001,), "F", 915031)]
    assert result["full_state_immutable"] is True
    assert result["new_optimizer_updates"] == 0
    assert result["worlds"][0]["recovery_opportunity"]["first_qualifying_exit_anchor"] is None
    assert result["worlds"][0]["actual_delivered_megabits"] == 10.0
    assert result["worlds"][0]["actual_delivered_megabytes"] == 1.25
    assert result["aggregate"]["mean_actual_delivered_megabits"] == 10.0
    assert result["aggregate"]["total_actual_delivered_megabits"] == 10.0
    assert result["aggregate"]["mean_actual_delivered_megabytes"] == 1.25
    assert result["aggregate"]["total_actual_delivered_megabytes"] == 1.25
    assert result["recovery_opportunity_aggregate"]["worlds"] == 1


def test_boundary_evidence_names_stale_pending_rows_without_mutation():
    agent = _FakeAgent()
    agent.env_pending_high_level[1] = {"time_step": 2997, "state_value": 1.0}
    agent.env_timers[1] = 2
    agent.env_reward_sums[1] = 3.5
    result = native.unresolved_boundary_evidence(agent, np.asarray((True, False)))
    assert result == {
        "live_lanes": [1],
        "live_lanes_with_pending_high_level_sample": {
            "1": {
                "time_step": 2997,
                "fields": ["state_value", "time_step"],
                "timer": 2,
                "accumulated_reward": 3.5,
            }
        },
        "supported_safe_clear": False,
    }
    assert agent.env_pending_high_level[1]["time_step"] == 2997

    # A completed skill does not end its native episode or recurrent history.
    agent.env_pending_high_level.clear()
    live_without_pending = native.unresolved_boundary_evidence(
        agent, np.asarray((True, False))
    )
    assert live_without_pending["live_lanes_with_pending_high_level_sample"] == {}
    assert live_without_pending["supported_safe_clear"] is False
    ended = native.unresolved_boundary_evidence(agent, np.asarray((True, True)))
    assert ended["supported_safe_clear"] is True


def test_endpoint_comparison_uses_common_worlds_and_keeps_all_signed_effects():
    opportunity = {
        "first_qualifying_exit_anchor": None,
        "intervals": [],
        "denominators": {},
    }
    def panel(offset):
        worlds = []
        for seed in (942001, 942002):
            row = {
                "seed": seed,
                **{field: float(offset) for field in native.ENDPOINT_FIELDS},
                "recovery_opportunity": opportunity,
            }
            worlds.append(row)
        return {"worlds": worlds}
    result = native.endpoint_comparison(panel(1.0), panel(0.0), panel(3.0))
    for row in result["worlds"]:
        assert all(value == 3.0 for value in row["effects_A_minus_N"].values())
        assert all(value == -1.0 for value in row["effects_N_minus_initial"].values())
        assert all(value == 2.0 for value in row["effects_A_minus_initial"].values())
    assert result["aggregate"]["effects_A_minus_N"]["raw_native_J"] == {
        "mean": 3.0, "median": 3.0, "min": 3.0, "max": 3.0,
    }
    mismatched = panel(3.0)
    mismatched["worlds"][1]["seed"] = 999999
    with pytest.raises(RuntimeError, match="not aligned"):
        native.endpoint_comparison(panel(1.0), panel(0.0), mismatched)


def test_entry_admits_before_candidate_and_forwards_fixed_arguments(monkeypatch, tmp_path):
    events = []
    admission = types.ModuleType("scripts.hmasd_admission")
    admission.require_admission = lambda *args, **kwargs: events.append("admission") or {"sha": "source"}
    monkeypatch.setitem(sys.modules, admission.__name__, admission)
    monkeypatch.setattr(native, "run_native", lambda **kwargs: (events.append("run"), kwargs)[1])
    result = entry.main([
        "--seed", "915031", "--launch-sha", "source", "--out", str(tmp_path / "run")
    ])
    assert events == ["admission", "run"]
    assert result["spec"] == native.production_spec(915031)
    assert result["device_name"] == "cuda" and result["threads"] == 4
    with pytest.raises(SystemExit):
        entry.parse_args(["--seed", "915032", "--launch-sha", "source", "--out", "x"])
    with pytest.raises(RuntimeError, match="launch SHA"):
        entry.main(["--launch-sha", "other", "--out", str(tmp_path / "other")])


def test_production_binding_refuses_changed_spec_before_output(tmp_path):
    out = tmp_path / "never-created"
    with pytest.raises(ValueError, match="prospectively fixed"):
        native.run_native(out=out, launch_sha="fixture", spec=replace(native.B08Spec(), rollouts=1))
    assert not out.exists()


def test_direct_entry_refuses_before_any_scientific_output(tmp_path):
    out = tmp_path / "never-created"
    result = subprocess.run(
        [sys.executable, entry.__file__, "--seed", "915031", "--out", str(out),
         "--launch-sha", "0" * 40],
        cwd=entry.ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0 and "missing HMASD admission" in result.stderr
    assert not out.exists()
