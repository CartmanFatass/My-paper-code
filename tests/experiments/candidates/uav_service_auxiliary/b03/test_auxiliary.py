import copy
import json

import pytest
import torch
from torch import nn

from experiments.candidates.uav_service_auxiliary.b01.auxiliary import AuxiliaryReplay
from experiments.candidates.uav_service_auxiliary.b03.auxiliary import B03AuxiliaryReplay
from hmasd.r_mappo_utils import RNNLayer


class ToyActor(nn.Module):
    def __init__(self, obs_dim=3, hidden_size=5, n_skills=3):
        super().__init__()
        self.hidden_size = hidden_size
        self.base = nn.Sequential(nn.Linear(obs_dim, hidden_size), nn.Tanh())
        self.film_generator = nn.Linear(n_skills, 2 * hidden_size)
        self.rnn = RNNLayer(hidden_size, hidden_size, 1, False)
        self.act = nn.Linear(hidden_size, 2)
        with torch.no_grad():
            self.film_generator.weight.zero_()
            self.film_generator.bias[:hidden_size].fill_(1.0)
            self.film_generator.bias[hidden_size:].zero_()


def make_actor(seed=17):
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        return ToyActor()


def make_replay(T=8, E=1, N=2, D=3):
    generator = torch.Generator().manual_seed(29)
    observations = torch.randn(T, E, N, D, generator=generator)
    skills = torch.arange(T * E * N).reshape(T, E, N) % 3
    dones = torch.zeros(T, E, dtype=torch.bool)
    qos = torch.linspace(0.1, 0.9, T).unsqueeze(1).expand(T, E).clone()
    actions = torch.randn(T, E, N, 4, generator=generator)
    return observations, skills, dones, qos, actions


def make_learner(actor, arm, service_seed=41, generic_seed=71, **kwargs):
    return B03AuxiliaryReplay(
        actor,
        arm,
        initialization_seed=service_seed,
        generic_initialization_seed=generic_seed,
        observation_dim=3,
        window=2,
        chunk_length=3,
        **kwargs,
    )


def clone_state(module):
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def assert_state_equal(left, right):
    right_state = right.state_dict() if isinstance(right, nn.Module) else right
    assert left.keys() == right_state.keys()
    for name in left:
        torch.testing.assert_close(left[name], right_state[name], rtol=0, atol=0)


def state_moved(before, module):
    return any(not torch.equal(before[name], value) for name, value in module.state_dict().items())


def calibrate(learner, observations, dones, qos, normalized=None):
    return learner.calibrate(
        observations,
        dones,
        qos,
        normalized_observations=normalized,
    )


def test_calibration_is_float64_w10_next_row_exact_json_and_immutable():
    actor = make_actor()
    learner = make_learner(actor, "D")
    observations, _, dones, qos, _ = make_replay(T=6, E=1, N=2)
    normalized = observations.double() * 2.0 + 0.25

    payload = calibrate(learner, observations, dones, qos, normalized)
    selected = normalized[1:]
    expected_mu = selected.mean(dim=(0, 1, 2))
    expected_scale = torch.clamp(
        torch.sqrt((selected * selected).mean(dim=(0, 1, 2))), min=1.0
    )
    assert set(payload) == {
        "version",
        "observation_dim",
        "window",
        "mu",
        "scale",
        "service_target_mean",
        "valid_team_rows",
        "valid_agent_samples",
    }
    torch.testing.assert_close(
        torch.tensor(payload["mu"], dtype=torch.float64), expected_mu, rtol=0, atol=0
    )
    torch.testing.assert_close(
        torch.tensor(payload["scale"], dtype=torch.float64), expected_scale, rtol=0, atol=0
    )
    assert payload["service_target_mean"] == pytest.approx(float(qos.unfold(0, 2, 1).mean(-1).mean()))
    assert payload["valid_team_rows"] == 5
    assert payload["valid_agent_samples"] == 10
    json.dumps(payload)

    imported = make_learner(make_actor(), "G")
    imported.load_calibration(payload)
    assert imported.calibrate(
        observations, dones, qos, normalized_observations=normalized.clone()
    ) == payload
    changed = normalized.clone()
    changed[1, 0, 0, 0] += 1.0
    with pytest.raises(ValueError, match="immutable"):
        imported.calibrate(observations, dones, qos, normalized_observations=changed)
    assert imported.calibration_state() == payload
    malformed = copy.deepcopy(payload)
    malformed["scale"][0] = 0.99
    with pytest.raises(ValueError, match="at least one"):
        make_learner(make_actor(), "S").load_calibration(malformed)


def test_head_rng_isolated_service_matches_frozen_and_labels_are_uppercase():
    actor = make_actor()
    torch.manual_seed(991)
    rng_before = torch.random.get_rng_state().clone()
    first = make_learner(actor, "D", service_seed=43, generic_seed=101)
    torch.testing.assert_close(torch.random.get_rng_state(), rng_before, rtol=0, atol=0)
    second = make_learner(make_actor(), "D", service_seed=43, generic_seed=103)
    assert_state_equal(clone_state(first.service_head), second.service_head)
    assert any(
        not torch.equal(left, right)
        for left, right in zip(first.generic_head.parameters(), second.generic_head.parameters())
    )
    old = AuxiliaryReplay(make_actor(), "detach", initialization_seed=43, window=2, chunk_length=3)
    assert_state_equal(clone_state(old.head), first.service_head)
    with pytest.raises(ValueError, match="arm"):
        make_learner(make_actor(), "d")


@pytest.mark.parametrize(("arm", "old_arm"), [("D", "detach"), ("S", "joint")])
def test_d_and_s_service_path_is_bit_exact_to_frozen_b01(arm, old_arm):
    actor_old = make_actor()
    actor_new = make_actor()
    observations, skills, dones, qos, actions = make_replay()
    old = AuxiliaryReplay(
        actor_old, old_arm, initialization_seed=47, window=2, chunk_length=3
    )
    new = make_learner(actor_new, arm, service_seed=47)
    calibrate(new, observations, dones, qos)

    old_result = old.update(actor_old, observations, skills, dones, qos)
    new_result = new.update(
        actor_new, observations, skills, dones, qos, actions=actions
    )

    assert_state_equal(clone_state(actor_old), actor_new)
    assert_state_equal(clone_state(old.head), new.service_head)
    assert old_result.loss == new_result["service"]["loss"]
    assert old_result.supervised_team_rows == new_result["supervised_team_rows"]
    assert old_result.supervised_agent_samples == new_result["supervised_agent_samples"]
    assert old_result.optimizer_steps == new_result["service"]["optimizer_steps"]
    assert old_result.head_gradient_norm == new_result["service"]["preclip_gradient_norm_max"]
    assert (
        old_result.representation_gradient_norm
        == new_result["representation"]["preclip_gradient_norm_max"]
    )


@pytest.mark.parametrize(
    ("arm", "base_moves", "generic_drives"),
    [("D", False, False), ("S", True, False), ("G", True, True)],
)
def test_all_routes_train_both_heads_and_only_selected_loss_updates_representation(
    arm, base_moves, generic_drives
):
    actor = make_actor()
    observations, skills, dones, qos, actions = make_replay()
    actions.requires_grad_()
    learner = make_learner(actor, arm)
    calibrate(learner, observations, dones, qos)
    service_before = clone_state(learner.service_head)
    generic_before = clone_state(learner.generic_head)
    base_before = clone_state(actor.base)
    rnn_before = clone_state(actor.rnn)
    film_before = clone_state(actor.film_generator)
    action_before = clone_state(actor.act)
    rng_before = torch.random.get_rng_state().clone()

    observed = learner.update(
        actor, observations, skills, dones, qos, actions=actions
    )

    torch.testing.assert_close(torch.random.get_rng_state(), rng_before, rtol=0, atol=0)
    assert state_moved(service_before, learner.service_head)
    assert state_moved(generic_before, learner.generic_head)
    assert state_moved(base_before, actor.base) is base_moves
    assert state_moved(rnn_before, actor.rnn) is base_moves
    assert_state_equal(film_before, actor.film_generator)
    assert_state_equal(action_before, actor.act)
    assert actions.grad is None
    assert all(parameter.grad is None for parameter in actor.film_generator.parameters())
    assert all(parameter.grad is None for parameter in actor.act.parameters())
    assert observed["service"]["optimizer_steps"] == 3
    assert observed["observation"]["optimizer_steps"] == 3
    assert observed["service"]["used_loss"] == observed["service"]["loss"]
    assert observed["observation"]["used_loss"] == observed["observation"]["loss"]
    assert observed["service"]["loss_coefficient"] == 1.0
    assert observed["observation"]["loss_coefficient"] == 1.0
    assert observed["representation"]["optimizer_steps"] == (3 if base_moves else 0)
    assert (observed["representation"]["base_parameter_movement_l2"] > 0) is base_moves
    assert (observed["representation"]["gru_parameter_movement_l2"] > 0) is base_moves
    if generic_drives:
        assert observed["observation"]["loss"] > 0
    json.dumps(observed)


def test_generic_targets_use_t_plus_one_across_chunk_and_shifted_done_resets_hidden():
    actor = make_actor()
    observations, skills, dones, qos, actions = make_replay(T=7, E=1, N=2)
    learner = make_learner(actor, "G")
    payload = calibrate(learner, observations, dones, qos)
    diagnostics = learner.update(
        actor, observations, skills, dones, qos, actions=actions
    )
    expected = (observations[1:] - torch.tensor(payload["mu"])) / torch.tensor(payload["scale"])
    expected_rows = expected.reshape(-1, 3).double()
    expected_variance = expected_rows.var(dim=0, correction=0)
    target = diagnostics["observation"]["target"]
    assert target["count"] == 12
    torch.testing.assert_close(
        torch.tensor(target["mean"], dtype=torch.float64),
        expected_rows.mean(0),
        rtol=1e-12,
        atol=1e-12,
    )
    torch.testing.assert_close(
        torch.tensor(target["variance_per_dimension"], dtype=torch.float64),
        expected_variance,
        rtol=1e-12,
        atol=1e-12,
    )

    reset_dones = torch.zeros_like(dones)
    reset_dones[2] = True
    zero = torch.zeros(1, 2, actor.hidden_size)
    anchored = torch.full_like(zero, 2.0)
    zero_prediction = learner.predict_all(
        actor, observations, skills, reset_dones, actions=actions, initial_hidden=zero
    )["features"]
    anchored_prediction = learner.predict_all(
        actor, observations, skills, reset_dones, actions=actions, initial_hidden=anchored
    )["features"]
    assert not torch.equal(zero_prediction[:3], anchored_prediction[:3])
    torch.testing.assert_close(zero_prediction[3:], anchored_prediction[3:], rtol=0, atol=0)


def test_predict_all_before_calibration_stays_raw_and_preserves_everything():
    actor = make_actor()
    observations, skills, dones, qos, actions = make_replay()
    learner = make_learner(actor, "D")
    actor.eval()
    learner.service_head.train(False)
    learner.generic_head.train(True)
    actor_before = clone_state(actor)
    service_before = clone_state(learner.service_head)
    generic_before = clone_state(learner.generic_head)
    torch.manual_seed(1999)
    rng_before = torch.random.get_rng_state().clone()

    raw = learner.predict_all(actor, observations, skills, dones, actions=actions)
    assert set(raw) == {"service", "observation", "features"}
    assert raw["service"].shape == (8, 1, 2)
    assert raw["observation"].shape == (8, 1, 2, 3)
    assert raw["features"].shape == (8, 1, 2, 5)
    payload = calibrate(learner, observations, dones, qos)
    scaled = learner.predict_all(actor, observations, skills, dones, actions=actions)

    assert payload["scale"]
    torch.testing.assert_close(scaled["observation"], raw["observation"], rtol=0, atol=0)
    torch.testing.assert_close(scaled["service"], raw["service"], rtol=0, atol=0)
    torch.testing.assert_close(scaled["features"], raw["features"], rtol=0, atol=0)
    torch.testing.assert_close(torch.random.get_rng_state(), rng_before, rtol=0, atol=0)
    assert actor.training is False
    assert learner.service_head.training is False
    assert learner.generic_head.training is True
    assert_state_equal(actor_before, actor)
    assert_state_equal(service_before, learner.service_head)
    assert_state_equal(generic_before, learner.generic_head)


@pytest.mark.parametrize("arm", ["D", "S", "G"])
def test_checkpoint_round_trip_restores_heads_optimizers_calibration_and_counters(arm, tmp_path):
    actor = make_actor()
    observations, skills, dones, qos, actions = make_replay()
    learner = make_learner(actor, arm)
    calibrate(learner, observations, dones, qos)
    learner.update(actor, observations, skills, dones, qos, actions=actions)
    prediction = learner.predict_all(actor, observations, skills, dones, actions=actions)
    actor_state = copy.deepcopy(actor.state_dict())
    checkpoint_path = tmp_path / "auxiliary.pt"
    torch.save(learner.checkpoint_state(), checkpoint_path)
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)

    restored_actor = make_actor(seed=999)
    restored_actor.load_state_dict(actor_state)
    restored = make_learner(restored_actor, arm)
    restored.load_checkpoint_state(checkpoint)
    restored_prediction = restored.predict_all(
        restored_actor, observations, skills, dones, actions=actions
    )
    for name in prediction:
        torch.testing.assert_close(prediction[name], restored_prediction[name], rtol=0, atol=0)
    restored_checkpoint = restored.checkpoint_state()
    assert restored_checkpoint["updates"] == 1
    assert restored_checkpoint["service_steps"] == 3
    assert restored_checkpoint["generic_steps"] == 3
    assert restored_checkpoint["representation_steps"] == (0 if arm == "D" else 3)
    assert restored.calibration_state() == learner.calibration_state()
    assert restored_checkpoint["service_optimizer"]["state"]
    assert restored_checkpoint["generic_optimizer"]["state"]
    assert (restored_checkpoint["representation_optimizer"] is None) is (arm == "D")

    wrong = make_learner(make_actor(), "D" if arm != "D" else "S")
    with pytest.raises(ValueError, match="arm mismatch"):
        wrong.load_checkpoint_state(checkpoint)
