"""One real tiny-host execution of the D-state probe, against the frozen route without it.

Two lanes, twenty-step episodes, the real Scenario 1 environment and the real D1280 agent, through
the frozen runner's own learner construction, evaluator construction and evaluation panel.
Technical checks, no result: nothing here asserts the direction or the size of any measured
quantity. Kept apart from the environment-free tests of the same object.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import probe_fsd_d_state_scale_b06 as probe  # noqa: E402
import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_matched_information_baseline_b01 as matched  # noqa: E402

SEED = sorted(probe.BLOCKS)[0]
LANES, HORIZON = 2, 20
N_UAVS, SKILL_PERIOD = 6, 10


@pytest.fixture
def tiny(monkeypatch):
    shared = b01.shared
    monkeypatch.setattr(shared, "TRAIN_LANES", LANES)
    monkeypatch.setattr(shared, "EVAL_LANES", LANES)
    monkeypatch.setattr(shared, "HORIZON", HORIZON)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())
    return shared


def frozen_route_scores(out, seed):
    """The same construction and the same panel, with none of the probe's capture attached."""
    probe.bind()
    shared = b01.shared
    evaluation_seed = probe.BLOCKS[seed]
    summary = shared.base_summary(matched.ARMS[probe.D_ARM][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=probe.OBJECT_ID,
                                  card=probe.CARD, caps=None)
    summary.update(panels=[], rollouts=0, panel_rollouts=[])
    out.mkdir(parents=True, exist_ok=True)
    _envs, learner, _theta0, _counters = b01.build_learner(probe.D_ARM, summary, out, seed)
    evaluator = b01.build_evaluator(probe.D_ARM, summary, out, evaluation_seed)
    b01.evaluate_panel(learner, evaluator, summary, out, 0)
    panel = summary["panels"][-1]
    assert panel["status"] == "complete"
    return panel["native_scores_J"], summary["learner_config"]


def test_the_probe_completes_with_zero_optimizer_steps_and_the_frozen_panel(tmp_path, tiny):
    out = tmp_path / "probe"
    head = probe.shared.e0._git("rev-parse", "HEAD")
    assert probe.main(["probe", "--seed", str(SEED), "--launch-sha", head,
                       "--output-root", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())

    assert summary["status"] == "complete" and summary["failure"] is None
    assert summary["object_id"] == "FSD_D_STATE_PROBE_B06" and summary["command"] == "probe"
    assert summary["arm"] == "D1280" and summary["block_seed"] == SEED
    assert summary["evaluation_seed"] == probe.BLOCKS[SEED]
    assert summary["launch_sha"] == head == summary["requested_launch_sha"]
    assert summary["optimizer_steps"] == 0
    assert not any(summary["optimizer_calls"].values())
    assert not any(summary["evaluator_optimizer_calls"].values())
    assert summary["evaluation_episodes"] == LANES
    assert summary["evaluation_steps"] == LANES * HORIZON
    assert summary["evaluation_lanes"] == LANES and summary["horizon"] == HORIZON
    assert summary["evaluation_deterministic"] is True
    assert summary["wall_seconds"] > 0.
    assert summary["coordinator_dropout"] == 0. and summary["coordinator_training_mode"] is False
    assert len(summary["J_init_world_scores"]) == LANES
    assert summary["J_init_mean"] == pytest.approx(float(np.mean(summary["J_init_world_scores"])))

    # The construction is the recorded D1280 fit's up to the shrunken host geometry.
    assert summary["frozen_host_geometry"] is False
    assert set(summary["learner_config_differences_from_recorded_d1280"]) == set(
        probe.GEOMETRY_FIELDS)
    assert set(summary["evaluation_config_differences_from_recorded_d1280"]) == set(
        probe.GEOMETRY_FIELDS)
    assert summary["learner_config"]["seed"] == SEED
    assert summary["evaluation_config"]["seed"] == probe.BLOCKS[SEED]
    assert summary["learner_config"]["use_central_snapshot_in_flat_actor"] is False

    # The affine is B05's, from the actual lanes of this host.
    assert summary["state_affine_bounds"] == {"area_size": 1000., "height_range": [50., 150.],
                                              "n_uavs": 6, "n_users": 50}
    offset, scaling = summary["state_affine"]["offset"], summary["state_affine"]["scale"]
    assert len(offset) == len(scaling) == 119
    assert offset[:3] == [0., 0., 50.] and scaling[:3] == [1000., 1000., 100.]
    assert offset[-1] == 0. and scaling[-1] == 1.

    # The capture saw the D route's own calls and nothing else.
    coordinator = summary["capture"]["coordinator"]
    assert coordinator["decision_calls"] == HORIZON // SKILL_PERIOD  # reset, then the skill cap
    assert coordinator["gap_pass_calls"] == HORIZON - 1  # every step but the reset step
    assert coordinator["sampling_path_calls"] == 0  # `assign_and_value_batch` is not the D route
    assert coordinator["captured_calls"] == coordinator["decision_calls"]
    assert coordinator["captured_rows"] == coordinator["captured_calls"] * LANES
    assert coordinator["capture_stride"] == 1
    critic = summary["capture"]["low_level_critic"]
    assert critic["critic_calls"] == HORIZON  # once per step, every (lane, agent) row
    assert critic["captured_calls"] == HORIZON and critic["capture_stride"] == 1
    assert critic["captured_rows"] == HORIZON * LANES * N_UAVS

    # The panel is the frozen one: the same construction without the probe reproduces its scores.
    reference, learner_config = frozen_route_scores(tmp_path / "frozen", SEED)
    assert reference == summary["J_init_world_scores"]
    assert learner_config == summary["learner_config"]


def test_the_measurements_carry_both_state_versions_and_their_definitions(tmp_path, tiny):
    out = tmp_path / "probe"
    head = probe.shared.e0._git("rev-parse", "HEAD")
    assert probe.main(["probe", "--seed", str(SEED), "--launch-sha", head,
                       "--output-root", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    measurements = summary["measurements"]
    assert set(measurements) == {"raw", "prescaled"}
    differing = []
    for label, entry in measurements.items():
        coordinator = entry["coordinator"]
        assert coordinator["rows"] == summary["capture"]["coordinator"]["captured_rows"]
        assert coordinator["conditioning"]["held_replay_reproduces_assign_and_value"] is True
        assert coordinator["conditioning"]["max_absolute_logit_difference"] == 0.

        norms = coordinator["token_embedding_norms"]
        assert norms["state_token"] > 0. and norms["observation_token"] > 0.
        assert norms["state_over_observation"] == pytest.approx(
            norms["state_token"] / norms["observation_token"])
        assert isinstance(norms["definition"], str)

        attention = coordinator["first_encoder_layer_attention"]
        assert attention["heads"] == 8 and attention["norm_first"] is False
        assert len(attention["mean_max_weight_per_head"]) == 8
        assert 1. / 7 <= attention["mean_max_weight"] <= 1.
        assert 0. <= attention["mean_entropy_nats"] <= math.log(7) + 1e-9
        assert 0. <= attention["mean_mass_on_state_token"] <= 1.
        assert attention["uniform_entropy_nats"] == pytest.approx(math.log(7))

        distributions = coordinator["skill_distributions"]
        assert distributions["ln_n_Z"] == distributions["ln_n_z"] == pytest.approx(math.log(6))
        assert 0. <= distributions["team_skill_entropy_nats"] <= math.log(6) + 1e-9
        assert len(distributions["agent_skill_entropy_nats_per_agent"]) == N_UAVS

        sensitivity = coordinator["skill_sensitivity"]
        assert set(sensitivity) == {"own_observation_agent0_relative", "uav0_plus_50m_x",
                                    "swap_observations_agents_0_and_1", "definition"}
        for name, values in sensitivity.items():
            if name == "definition":
                continue
            assert 0. <= values["team_skill_total_variation"] <= 1.
            assert values["team_logit_mean_absolute_change"] >= 0.
            assert len(values["agent_skill_total_variation_per_agent"]) == N_UAVS

        critic = entry["low_level_critic"]
        assert critic["rows"] == summary["capture"]["low_level_critic"]["captured_rows"]
        assert critic["value_norm"]["use_valuenorm"] is True
        assert critic["mean_absolute_value_change_uav0_plus_50m_x"] >= 0.
        for gate in ("update", "reset"):
            saturation = critic["gru_gate_saturation"][gate]
            assert 0. <= saturation["fraction_saturated"] <= 1.
            assert saturation["total_units"] == critic["rows"] * 256
        assert "hmasd/networks.py:1811-1815" in critic["input"]  # the cited critic input
        differing.append((norms["state_token"],
                          critic["mean_absolute_value_change_uav0_plus_50m_x"]))
    # The same weights on two different state inputs: the readings are not the same numbers.
    assert differing[0] != differing[1]
