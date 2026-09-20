"""The D-state probe's construction, its attention recomputation and its two state versions.

No environment and no learner: a real `SkillCoordinator` built from the real D1280 configuration,
and the recorded configuration of the published stage-1 D1280 fits. Technical checks only; nothing
here asserts the direction or the size of any measured quantity.
"""
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import probe_fsd_d_state_scale_b06 as probe  # noqa: E402
import run_fsd_baseline_interruption_b01 as b01  # noqa: E402
import run_fsd_flat_input_scale_b05 as scale  # noqa: E402
import run_fsd_uav_individual_renewal_b01 as production_shared  # noqa: E402
from hmasd.networks import SkillCoordinator, SkillDiscoverer  # noqa: E402

SEEDS = sorted(probe.BLOCKS)
STATE_DIM, OBS_DIM = 119, 104
N_UAVS, N_USERS, AREA, HEIGHTS = 6, 50, 1000., (50., 150.)


def lanes(count):
    return [SimpleNamespace(state_dim=STATE_DIM, obs_dim=OBS_DIM) for _ in range(count)]


def d1280_config(seed, count):
    probe.bind()
    return b01.make_config(probe.D_ARM, lanes(count), seed)


def affine():
    offset, values = scale.state_affine_from_bounds(N_UAVS, N_USERS, AREA, HEIGHTS, STATE_DIM)
    return {"offset": offset, "scale": values}


def metre_rows(count=2, rows=3, seed=11):
    """Captured-shaped rows with a plausible metre state and arbitrary observations."""
    generator = torch.Generator().manual_seed(seed)
    captured = []
    for _ in range(count):
        state = torch.rand(rows, STATE_DIM, generator=generator)
        for uav in range(N_UAVS):
            state[:, 3 * uav] *= AREA
            state[:, 3 * uav + 1] *= AREA
            state[:, 3 * uav + 2] = HEIGHTS[0] + state[:, 3 * uav + 2] * (HEIGHTS[1] - HEIGHTS[0])
        state[:, 3 * N_UAVS:STATE_DIM - 1] *= AREA
        captured.append({"state": state,
                         "observations": torch.randn(rows, N_UAVS, OBS_DIM, generator=generator)})
    return captured


def coordinator(seed=SEEDS[0]):
    config = d1280_config(seed, 16)
    torch.manual_seed(seed)
    built = SkillCoordinator(config)
    built.eval()
    return built


def close(left, right, *, tolerance=0.):
    """Recursive comparison of two readings; strings and ints must be equal exactly."""
    if isinstance(left, dict):
        assert isinstance(right, dict) and set(left) == set(right)
        for key in left:
            close(left[key], right[key], tolerance=tolerance)
    elif isinstance(left, list):
        assert isinstance(right, list) and len(left) == len(right)
        for one, other in zip(left, right):
            close(one, other, tolerance=tolerance)
    elif isinstance(left, float):
        assert left == pytest.approx(right, rel=tolerance, abs=tolerance)
    else:
        assert left == right


# ---------------------------------------------------------------------------
# the construction is the recorded stage-1 D1280 fit's
# ---------------------------------------------------------------------------


def test_the_construction_is_the_recorded_d1280_fit_of_every_block():
    for seed in SEEDS:
        recorded = json.loads(probe.RECORDED_FITS[seed].read_text(encoding="utf-8"))
        assert recorded["object_id"] == probe.REFERENCE_OBJECT_ID
        assert recorded["factorial_arm"] == probe.D_ARM and recorded["status"] == "complete"
        learner = production_shared.config_snapshot(d1280_config(seed, 16))
        evaluation = production_shared.config_snapshot(
            d1280_config(probe.BLOCKS[seed], 32))
        assert learner == recorded["learner_config"]
        assert evaluation == recorded["evaluation_config"]
        assert probe.config_differences(learner, recorded["learner_config"]) == {}
        assert probe.config_differences(evaluation, recorded["evaluation_config"]) == {}
        assert learner["policy_interruption_mode"] == "d2" and learner["k"] == 10
        assert learner["coordinator_batch_size"] == 1280 and learner["n_Z"] == learner["n_z"] == 6
        assert learner["use_central_snapshot_in_flat_actor"] is False
        assert learner["use_statenorm"] is False and learner["use_obsnorm"] is False


def test_the_probe_refuses_a_construction_the_host_geometry_does_not_explain():
    recorded = json.loads(probe.RECORDED_FITS[SEEDS[0]].read_text(encoding="utf-8"))
    config = production_shared.config_snapshot(d1280_config(SEEDS[0], 16))
    assert probe.host_geometry() == probe.FROZEN_GEOMETRY
    assert probe.require_recorded_construction(config, recorded["learner_config"], "learner") == {}
    # A real difference is refused whatever the host is.
    changed = dict(config, k=7)
    with pytest.raises(ValueError, match="not the recorded D1280 fit's"):
        probe.require_recorded_construction(changed, recorded["learner_config"], "learner")
    # On the frozen host the lane count and horizon are not an excuse either.
    smaller = dict(config, num_envs=2)
    with pytest.raises(ValueError, match="not the recorded D1280 fit's"):
        probe.require_recorded_construction(smaller, recorded["learner_config"], "learner")
    assert set(probe.config_differences(smaller, recorded["learner_config"])) == {"num_envs"}


def test_the_probe_refuses_an_unplanned_block(tmp_path):
    with pytest.raises(SystemExit):
        probe.run_probe(772603, tmp_path / "refused")
    assert not (tmp_path / "refused").exists()
    with pytest.raises(SystemExit):
        probe.main(["probe", "--seed", str(SEEDS[0]), "--launch-sha", "not-the-head",
                    "--output-root", str(tmp_path / "wrong-sha")])
    assert not (tmp_path / "wrong-sha").exists()


# ---------------------------------------------------------------------------
# (b): the recomputed first-layer attention
# ---------------------------------------------------------------------------


def test_the_recomputed_attention_equals_multihead_attentions_own_weights():
    built = coordinator()
    layer = built.encoder.layers[0]
    assert layer.norm_first is False  # a default nn.TransformerEncoderLayer: post-norm
    assert layer.self_attn.num_heads == 8 and layer.self_attn.batch_first is True
    tokens = torch.randn(5, 1 + N_UAVS, built.state_embedding.out_features,
                         generator=torch.Generator().manual_seed(3))
    with torch.no_grad():
        mine = probe.first_layer_attention_weights(built, tokens)
        _output, theirs = layer.self_attn(tokens, tokens, tokens, need_weights=True,
                                          average_attn_weights=False)
    assert mine.shape == theirs.shape == (5, 8, 1 + N_UAVS, 1 + N_UAVS)
    assert torch.allclose(mine, theirs, atol=1e-5, rtol=0.)
    assert torch.allclose(mine.sum(-1), torch.ones_like(mine.sum(-1)), atol=1e-6)

    # The pre-norm branch reads `norm1` of the same sequence.
    layer.norm_first = True
    try:
        with torch.no_grad():
            pre = probe.first_layer_attention_weights(built, tokens)
            _output, expected = layer.self_attn(layer.norm1(tokens), layer.norm1(tokens),
                                                layer.norm1(tokens), need_weights=True,
                                                average_attn_weights=False)
        assert torch.allclose(pre, expected, atol=1e-5, rtol=0.)
        assert not torch.allclose(pre, mine, atol=1e-5, rtol=0.)
    finally:
        layer.norm_first = False


# ---------------------------------------------------------------------------
# the two state versions
# ---------------------------------------------------------------------------


def test_the_metre_move_is_applied_before_the_affine():
    values = affine()
    transform = probe.prescale_transform(values)
    state = metre_rows(count=1)[0]["state"]
    moved = probe.move_metres(state, N_UAVS)
    assert torch.equal(moved[:, 1:], state[:, 1:])  # only UAV 0's x entry moves
    assert torch.allclose(moved[:, 0], state[:, 0] + probe.MOVE_METRES)
    # In the pre-scaled version the same physical move is 50 / area_size after the affine.
    step = probe.MOVE_METRES / values["scale"][0]
    assert torch.allclose(transform(moved)[:, 0], transform(state)[:, 0] + step, atol=1e-6)
    assert torch.equal(transform(moved)[:, 1:], transform(state)[:, 1:])
    assert transform(state).abs().max() <= 1.0001  # every entry is on the observations' scale
    with pytest.raises(ValueError, match="has no x entry"):
        probe.move_metres(state, N_UAVS, uav=N_UAVS)


def test_the_prescaled_reading_is_the_raw_reading_of_a_prescaled_state():
    """Only the state input differs: the same weights on a manually pre-scaled state agree."""
    built = coordinator()
    captured = metre_rows()
    values = affine()
    offset = torch.as_tensor(values["offset"], dtype=torch.float32)
    scaling = torch.as_tensor(values["scale"], dtype=torch.float32)
    with torch.no_grad():
        prescaled = probe.coordinator_reading(
            built, captured, probe.prescale_transform(values), n_uavs=N_UAVS)
        raw = probe.coordinator_reading(
            built, captured, probe.identity_transform, n_uavs=N_UAVS)
        # (i) the fully pre-scaled state, fed with no transform at all.
        manual = probe.coordinator_reading(
            built, [{"state": (row["state"] - offset) / scaling,
                     "observations": row["observations"]} for row in captured],
            probe.identity_transform, n_uavs=N_UAVS)
        # (ii) the same, with the metre move still applied before the division.
        shifted = probe.coordinator_reading(
            built, [{"state": row["state"] - offset, "observations": row["observations"]}
                    for row in captured],
            probe.prescale_transform({"offset": [0.] * STATE_DIM, "scale": values["scale"]}),
            n_uavs=N_UAVS)
    for key in ("token_embedding_norms", "first_encoder_layer_attention", "skill_distributions"):
        close(prescaled[key], manual[key])
        assert prescaled[key] != raw[key]
    for name in ("own_observation_agent0_relative", "swap_observations_agents_0_and_1"):
        close(prescaled["skill_sensitivity"][name], manual["skill_sensitivity"][name])
    # (i) moves UAV 0 by 50 in the pre-scaled units, which is not the same physical move; (ii) does.
    assert (prescaled["skill_sensitivity"]["uav0_plus_50m_x"]
            != manual["skill_sensitivity"]["uav0_plus_50m_x"])
    close(prescaled, shifted)
    assert prescaled["rows"] == raw["rows"] == sum(row["state"].shape[0] for row in captured)


def test_the_critic_reading_follows_the_same_two_state_versions():
    """(e) uses the same rule: the move is in metres, before the affine."""
    config = d1280_config(SEEDS[0], 16)
    torch.manual_seed(SEEDS[0])
    discoverer = SkillDiscoverer(config, device=torch.device("cpu"))
    discoverer.eval()
    values = affine()
    offset = torch.as_tensor(values["offset"], dtype=torch.float32)
    rows = 4
    generator = torch.Generator().manual_seed(5)
    captured = [{"cent_obs": metre_rows(count=1, rows=rows, seed=7)[0]["state"],
                 "hidden": torch.randn(rows, 256, generator=generator),
                 "masks": torch.ones(rows, 1),
                 "team_skill": torch.zeros(rows, dtype=torch.long)}]
    shifted = [dict(row, cent_obs=row["cent_obs"] - offset) for row in captured]
    with torch.no_grad():
        raw = probe.critic_reading(discoverer.critic, captured, probe.identity_transform,
                                   n_uavs=N_UAVS, use_valuenorm=True)
        prescaled = probe.critic_reading(discoverer.critic, captured,
                                         probe.prescale_transform(values), n_uavs=N_UAVS,
                                         use_valuenorm=True)
        manual = probe.critic_reading(
            discoverer.critic, shifted,
            probe.prescale_transform({"offset": [0.] * STATE_DIM, "scale": values["scale"]}),
            n_uavs=N_UAVS, use_valuenorm=True)
    close(prescaled, manual)
    assert raw["rows"] == prescaled["rows"] == rows
    assert raw["gru_gate_saturation"] != prescaled["gru_gate_saturation"]
    assert raw["mean_absolute_value_change_uav0_plus_50m_x"] != pytest.approx(
        prescaled["mean_absolute_value_change_uav0_plus_50m_x"])
    for gate in ("update", "reset"):
        entry = prescaled["gru_gate_saturation"][gate]
        assert entry["total_units"] == rows * 256
        assert 0. <= entry["fraction_saturated"] <= 1.


def test_the_reading_conditions_on_the_unperturbed_deterministic_chain():
    built = coordinator()
    with torch.no_grad():
        reading = probe.coordinator_reading(
            built, metre_rows(), probe.identity_transform, n_uavs=N_UAVS)
    conditioning = reading["conditioning"]
    assert conditioning["held_replay_reproduces_assign_and_value"] is True
    assert conditioning["max_absolute_logit_difference"] == 0.
    distributions = reading["skill_distributions"]
    assert distributions["ln_n_Z"] == pytest.approx(math.log(6))
    assert 0. <= distributions["team_skill_entropy_nats"] <= distributions["ln_n_Z"] + 1e-9
    assert len(distributions["agent_skill_entropy_nats_per_agent"]) == N_UAVS
    attention = reading["first_encoder_layer_attention"]
    assert len(attention["mean_max_weight_per_head"]) == 8
    assert attention["uniform_mass_on_state_token"] == pytest.approx(1. / (1 + N_UAVS))
    for name, entry in reading["skill_sensitivity"].items():
        if name == "definition":
            continue
        assert 0. <= entry["team_skill_total_variation"] <= 1.
        assert all(0. <= value <= 1. for value in entry["agent_skill_total_variation_per_agent"])
