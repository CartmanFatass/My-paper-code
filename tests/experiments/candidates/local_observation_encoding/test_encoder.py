import random
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from experiments.candidates.local_observation_encoding import b01
from experiments.candidates.local_observation_encoding.encoder import (
    DenseObservationEncoder,
    NEIGHBOR_SLICE,
    OBS_DIM,
    SELF_SLICE,
    TIME_SLICE,
    USER_SLICE,
    install_actor_encoder,
)


def test_slot_layout_shapes_gradients_and_zero_slots_participate():
    encoder = DenseObservationEncoder()
    observation = torch.arange(OBS_DIM, dtype=torch.float32)
    own, users, neighbors, step = encoder.split_observation(observation)
    torch.testing.assert_close(own, observation[SELF_SLICE])
    torch.testing.assert_close(users.reshape(-1), observation[USER_SLICE])
    torch.testing.assert_close(neighbors.reshape(-1), observation[NEIGHBOR_SLICE])
    torch.testing.assert_close(step, observation[TIME_SLICE])

    assert encoder(observation).shape == (256,)
    assert encoder(observation.repeat(3, 1)).shape == (3, 256)
    sequential = torch.zeros(2, 3, OBS_DIM, requires_grad=True)
    output = encoder(sequential)
    assert output.shape == (2, 3, 256)
    output.square().mean().backward()
    assert sequential.grad is not None and torch.isfinite(sequential.grad).all()
    # All-zero slots still receive rank embeddings and enter dense attention/means.
    assert encoder.user_rank.weight.grad is not None
    assert encoder.neighbor_rank.weight.grad is not None
    assert torch.count_nonzero(encoder.user_rank.weight.grad).item() > 0
    assert torch.count_nonzero(encoder.neighbor_rank.weight.grad).item() > 0


def _model_state(agent):
    modules = {
        "coordinator": agent.skill_coordinator,
        "discoverer": agent.skill_discoverer,
        "team_discriminator": agent.team_discriminator,
        "individual_discriminator": agent.individual_discriminator,
    }
    return {
        f"{module_name}.{key}": value.detach().clone()
        for module_name, module in modules.items() if module is not None
        for key, value in module.state_dict().items()
    }


def _agent(seed, arm, log_dir):
    shared = b01.native.shared
    shared.seed_rng(seed)
    envs = shared.e0._make_envs(1, seed, shared.N_UAVS, shared.N_USERS, 10)
    with b01.scoped_native_bindings():
        config = b01.native.make_config(arm, envs, seed)
    agent = shared.HMASDAgent(config, log_dir=str(log_dir), device=torch.device("cpu"))
    before_install = _model_state(agent)
    rng_before = torch.random.get_rng_state().clone()
    installation = install_actor_encoder(agent, arm)
    return agent, before_install, rng_before, installation


def test_dense_install_preserves_rng_nonencoder_state_and_optimizer_updates(tmp_path):
    original, original_before, _, original_install = _agent(92101, "ORIGINAL", tmp_path / "original")
    dense, dense_before, rng_before, dense_install = _agent(92101, "DENSE", tmp_path / "dense")
    assert original_install["active_base_type"] == "MLPBase"
    assert dense_install["active_base_type"] == "DenseObservationEncoder"
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    assert original_before.keys() == dense_before.keys()
    for key in original_before:
        torch.testing.assert_close(original_before[key], dense_before[key], rtol=0, atol=0)
    original_nonbase = {key: value for key, value in _model_state(original).items()
                        if "discoverer.actor.base." not in key}
    dense_nonbase = {key: value for key, value in _model_state(dense).items()
                     if "discoverer.actor.base." not in key}
    assert original_nonbase.keys() == dense_nonbase.keys()
    for key in original_nonbase:
        torch.testing.assert_close(original_nonbase[key], dense_nonbase[key], rtol=0, atol=0)

    encoder = dense.skill_discoverer.actor.base
    parameters = list(encoder.parameters())
    before = [parameter.detach().clone() for parameter in parameters]
    dense.discoverer_actor_optimizer.zero_grad()
    encoder(torch.linspace(-1, 1, OBS_DIM).repeat(4, 1)).square().mean().backward()
    dense.discoverer_actor_optimizer.step()
    assert any(not torch.equal(old, new) for old, new in zip(before, parameters))
    owned = {id(parameter) for group in dense.discoverer_actor_optimizer.param_groups
             for parameter in group["params"]}
    assert all(id(parameter) in owned for parameter in parameters)


def test_dense_evaluator_sync_is_separate_and_rng_neutral(tmp_path):
    learner, _, _, _ = _agent(92101, "DENSE", tmp_path / "learner")
    evaluator_agent, _, _, _ = _agent(93101, "DENSE", tmp_path / "evaluator")
    with torch.no_grad():
        learner.skill_discoverer.actor.base.output_projection.bias.add_(1.25)

    wrapper = object.__new__(b01.native.shared.e0.Evaluator)
    wrapper.agent = evaluator_agent
    wrapper.lanes = 1
    py_state = random.getstate()
    np_state = np.random.get_state()
    torch_state = torch.random.get_rng_state().clone()
    wrapper._sync(learner)

    for key, value in learner.skill_discoverer.state_dict().items():
        torch.testing.assert_close(value, evaluator_agent.skill_discoverer.state_dict()[key])
    assert evaluator_agent.training is False
    assert random.getstate() == py_state
    after_np = np.random.get_state()
    assert after_np[0] == np_state[0] and np.array_equal(after_np[1], np_state[1])
    assert after_np[2:] == np_state[2:]
    assert torch.equal(torch.random.get_rng_state(), torch_state)
    assert all(len(state) == 0 for state in evaluator_agent.discoverer_actor_optimizer.state.values())


def test_scoped_bindings_restore_frozen_runner():
    native = b01.native
    saved = (native.OBJECT_ID, native.make_config, native.build_learner,
             native.shared.base_summary)
    with b01.scoped_native_bindings():
        assert native.OBJECT_ID == b01.OBJECT_ID
        assert native.make_config is b01.make_config
        assert native.build_learner is b01.build_learner
        assert native.shared.base_summary is b01.base_summary
    assert saved == (native.OBJECT_ID, native.make_config, native.build_learner,
                     native.shared.base_summary)
