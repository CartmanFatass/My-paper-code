"""Native update inheritance and synthetic candidate learning checks."""

import numpy as np
import torch

from experiments.candidates.vap_folr_core.entity_history_b01.learner import (
    Learner as HistoricalLearner,
)
from experiments.candidates.vap_folr_core.last_sighting_a01.learner import Learner
from experiments.candidates.vap_folr_core.public_lifecycle_b01.learner import (
    Learner as EpisodicLearner,
)

def complete_batch(batch_size=2):
    steps = 21
    continuation = torch.ones(batch_size, steps, 5, dtype=torch.bool)
    continuation[:, 0] = False
    visible = torch.eye(5, dtype=torch.bool)[None, None].repeat(
        batch_size, steps, 1, 1
    )
    batch = {
        "entities": torch.rand(batch_size, steps, 5, 4),
        "previous_action": torch.zeros(batch_size, steps, 5, 5),
        "entity_mask": torch.zeros(batch_size, steps, 5, dtype=torch.bool),
        "visible": visible,
        "obs_mask": ~visible,
        "seen": visible.clone(),
        "age": torch.zeros(batch_size, steps, 5, 5, dtype=torch.int16),
        "birth": ~continuation,
        "continuation": continuation,
        "departure": torch.zeros_like(continuation),
        "event": torch.zeros(batch_size, steps, dtype=torch.bool),
    }
    generator = torch.Generator().manual_seed(4571)
    batch.update(
        actions=torch.randint(0, 5, (batch_size, 20, 5), generator=generator),
        reward=torch.randn(batch_size, 20, generator=generator),
        terminated=torch.zeros(batch_size, 20),
    )
    batch["terminated"][:, -1] = 1
    return batch


def assert_state_equal(first, second):
    assert first.keys() == second.keys()
    for name, value in first.items():
        if torch.is_tensor(value):
            assert torch.equal(value, second[name])
        elif isinstance(value, dict):
            assert_state_equal(value, second[name])
        elif isinstance(value, list):
            assert len(value) == len(second[name])
            for left, right in zip(value, second[name]):
                if isinstance(left, dict):
                    assert_state_equal(left, right)
                else:
                    assert left == right
        else:
            assert value == second[name]


def test_generic_wrapper_is_exact_historical_update_and_target_sync():
    assert Learner.update is EpisodicLearner.update
    assert Learner.save is EpisodicLearner.save
    batch = complete_batch()
    torch.manual_seed(4511)
    historical = HistoricalLearner("GENERIC_RETAIN")
    after_historical_init = torch.random.get_rng_state().clone()
    torch.manual_seed(4511)
    wrapper = Learner("GENERIC_RETAIN")
    assert torch.equal(after_historical_init, torch.random.get_rng_state())

    historical_loss = historical.update(batch, 200)
    wrapper_loss = wrapper.update(batch, 200)
    assert wrapper_loss == historical_loss
    for left, right in (
        (historical.actor, wrapper.actor),
        (historical.mixer, wrapper.mixer),
        (historical.target_actor, wrapper.target_actor),
        (historical.target_mixer, wrapper.target_mixer),
    ):
        assert_state_equal(left.state_dict(), right.state_dict())
    assert_state_equal(historical.optimiser.state_dict(), wrapper.optimiser.state_dict())
    assert wrapper.last_target_update_episode == historical.last_target_update_episode == 200


def test_candidate_and_generic_have_identical_initial_trainable_state_and_rng():
    torch.manual_seed(4521)
    generic = Learner("GENERIC_RETAIN")
    after_generic = torch.random.get_rng_state().clone()
    torch.manual_seed(4521)
    cached = Learner("LAST_SIGHTING")
    assert torch.equal(after_generic, torch.random.get_rng_state())
    assert_state_equal(generic.actor.state_dict(), cached.actor.state_dict())
    assert_state_equal(generic.mixer.state_dict(), cached.mixer.state_dict())
    assert_state_equal(generic.target_actor.state_dict(), cached.target_actor.state_dict())
    assert_state_equal(generic.target_mixer.state_dict(), cached.target_mixer.state_dict())
    assert_state_equal(generic.optimiser.state_dict(), cached.optimiser.state_dict())
    assert [parameter.shape for parameter in generic.params] == [
        parameter.shape for parameter in cached.params
    ]


def test_candidate_real_loss_moves_actor_and_preserves_target_ownership(tmp_path):
    torch.manual_seed(4531)
    learner = Learner("LAST_SIGHTING")
    before = learner.actor.rnn.weight_ih.detach().clone()
    target_before = learner.target_actor.rnn.weight_ih.detach().clone()
    loss = learner.update(complete_batch(), 1)
    assert np.isfinite(loss) and learner.updates == 1
    assert not torch.equal(before, learner.actor.rnn.weight_ih)
    torch.testing.assert_close(
        target_before, learner.target_actor.rnn.weight_ih, rtol=0, atol=0
    )
    assert (
        learner.actor.rnn.weight_ih.data_ptr()
        != learner.target_actor.rnn.weight_ih.data_ptr()
    )
    checkpoint = tmp_path / "final.pt"
    learner.save(checkpoint)
    saved = torch.load(checkpoint, weights_only=True)
    assert saved["arm"] == "LAST_SIGHTING" and saved["updates"] == 1
    assert saved["optimiser"]["state"]
