import copy

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.entity_history_augmentation_b01.learner import (
    Learner as NativeLearner,
)
from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor
from experiments.candidates.vap_folr_core.predictive_aux_a01.learner import (
    Learner,
    prediction_targets,
)


@pytest.fixture(scope="module", autouse=True)
def one_thread():
    torch.set_num_threads(1)


def synthetic_batch(batch_size=2):
    generator = torch.Generator().manual_seed(713)
    visible = torch.eye(5, dtype=torch.bool)[None, None].repeat(batch_size, 21, 1, 1)
    visible[:, :, 0, 1] = True
    continuation = torch.ones(batch_size, 21, 5, dtype=torch.bool)
    continuation[:, 0] = False
    entity_mask = torch.zeros(batch_size, 21, 5, dtype=torch.bool)
    batch = {
        "entities": torch.rand(batch_size, 21, 5, 4, generator=generator),
        "previous_action": torch.zeros(batch_size, 21, 5, 5),
        "entity_mask": entity_mask,
        "visible": visible,
        "obs_mask": ~visible,
        "seen": visible.clone(),
        "age": torch.zeros_like(visible, dtype=torch.int16),
        "birth": ~continuation,
        "continuation": continuation,
        "departure": torch.zeros_like(continuation),
        "event": torch.zeros(batch_size, 21, dtype=torch.bool),
        "actions": torch.randint(0, 5, (batch_size, 20, 5), generator=generator),
        "reward": torch.randn(batch_size, 20, generator=generator, dtype=torch.float32),
        "terminated": torch.zeros(batch_size, 20),
    }
    batch["terminated"][:, -1] = 1
    return batch


def assert_nested_equal(first, second):
    if torch.is_tensor(first):
        assert torch.equal(first, second)
    elif isinstance(first, dict):
        assert first.keys() == second.keys()
        for key in first:
            assert_nested_equal(first[key], second[key])
    elif isinstance(first, (list, tuple)):
        assert len(first) == len(second)
        for left, right in zip(first, second):
            assert_nested_equal(left, right)
    else:
        assert first == second


def test_detached_exact_native_update_optimizer_rng_and_target_sync():
    batch = synthetic_batch()
    torch.manual_seed(911)
    native = NativeLearner("GENERIC_RETAIN")
    native_after_init_rng = torch.random.get_rng_state().clone()
    torch.manual_seed(911)
    detached = Learner("DETACHED")
    assert type(detached.actor) is Actor
    assert detached.actor.fc1.in_features == 14 and detached.actor.fc2.in_features == 160
    assert torch.equal(native_after_init_rng, torch.random.get_rng_state())

    predictor_before = copy.deepcopy(detached.predictor.state_dict())
    torch.random.set_rng_state(native_after_init_rng)
    native_loss = native.update(batch, 200)
    native_after_update_rng = torch.random.get_rng_state().clone()
    torch.random.set_rng_state(native_after_init_rng)
    metrics = detached.update(batch, 200)
    assert torch.equal(native_after_update_rng, torch.random.get_rng_state())
    assert metrics["native_loss"] == native_loss

    for native_module, detached_module in (
        (native.actor, detached.actor),
        (native.mixer, detached.mixer),
        (native.target_actor, detached.target_actor),
        (native.target_mixer, detached.target_mixer),
    ):
        assert_nested_equal(native_module.state_dict(), detached_module.state_dict())
    assert_nested_equal(native.optimiser.state_dict(), detached.optimiser.state_dict())
    assert native.last_target_update_episode == detached.last_target_update_episode == 200
    assert detached.predictor_updates == detached.updates == 1
    assert any(
        not torch.equal(value, detached.predictor.state_dict()[name])
        for name, value in predictor_before.items()
    )


@pytest.mark.parametrize("arm", ["DETACHED", "COUPLED"])
def test_predictor_has_owned_optimizer_clip_and_checkpoint(monkeypatch, tmp_path, arm):
    torch.manual_seed(917)
    learner = Learner(arm)
    predictor_before = copy.deepcopy(learner.predictor.state_dict())
    calls = []
    original_clip = torch.nn.utils.clip_grad_norm_

    def recording_clip(parameters, bound):
        rows = list(parameters)
        calls.append(({id(value) for value in rows}, bound))
        return original_clip(rows, bound)

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", recording_clip)
    metrics = learner.update(synthetic_batch(), 1)
    assert np.isfinite(metrics["prediction_mse"]) and metrics["prediction_count"] == 180
    assert calls == [
        ({id(value) for value in learner.params}, 10),
        ({id(value) for value in learner.predictor_params}, 10),
    ]
    assert any(
        not torch.equal(value, learner.predictor.state_dict()[name])
        for name, value in predictor_before.items()
    )
    assert learner.predictor_optimiser.state

    path = tmp_path / "final.pt"
    learner.save(path)
    saved = torch.load(path, weights_only=True)
    assert saved["arm"] == arm and saved["native_actor_arm"] == "GENERIC_RETAIN"
    assert saved["updates"] == saved["predictor_updates"] == 1
    assert saved["optimiser"]["state"] and saved["predictor_optimiser"]["state"]
    assert set(saved) >= {
        "actor", "mixer", "target_actor", "target_mixer", "predictor",
        "optimiser", "predictor_optimiser",
    }


def test_coupled_adds_backbone_gradient_but_not_predictor_exposure():
    batch = synthetic_batch()
    torch.manual_seed(919)
    detached = Learner("DETACHED")
    torch.manual_seed(919)
    coupled = Learner("COUPLED")
    detached.update(batch, 1)
    coupled.update(batch, 1)
    assert_nested_equal(detached.predictor.state_dict(), coupled.predictor.state_dict())
    assert_nested_equal(
        detached.predictor_optimiser.state_dict(), coupled.predictor_optimiser.state_dict()
    )
    assert not torch.equal(detached.actor.rnn.weight_ih, coupled.actor.rnn.weight_ih)
    assert detached.predictor_updates == coupled.predictor_updates == 1


def test_prediction_windows_use_active_at_t_only_and_keep_future_departures():
    rewards = torch.arange(20, dtype=torch.float32)[None]
    entity_mask = torch.ones(1, 21, 5, dtype=torch.bool)
    entity_mask[:, :18, 0] = False
    entity_mask[:, 5, 1] = False
    entity_mask[:, 17, 2] = False
    targets, eligible = prediction_targets({"reward": rewards, "entity_mask": entity_mask})
    assert targets.dtype == torch.float32 and targets.shape == (1, 18, 5)
    assert targets[0, 0, 0].item() == 1.0
    assert targets[0, 17, 2].item() == 18.0
    assert eligible.sum().item() == 20
    assert eligible[0, 5, 1] and eligible[0, 17, 2]
    assert not eligible[0, 6, 1]
    with pytest.raises(ValueError, match="FP32"):
        prediction_targets({"reward": rewards.double(), "entity_mask": entity_mask})

