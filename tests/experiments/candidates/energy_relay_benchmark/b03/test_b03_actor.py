"""B03 actor input: width 3605, all-FREE = SET input + [0,0,0,0,0,1], hand-computed block,
label cross-check, construction (RNG statement, optimizers, buffer), refusals."""

from __future__ import annotations

import copy
import random

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b02 import configuration as c2
from experiments.candidates.energy_relay_benchmark.b03 import agent as ag
from experiments.candidates.energy_relay_benchmark.b03.anchors import FREE_LABEL, anchors_from_state
from experiments.candidates.energy_relay_benchmark.b03.configuration import make_b03_config
from experiments.candidates.uav_service_auxiliary.b01.native import seed_everything
from hmasd.agent import HMASDAgent
from hmasd.networks import SkillDiscoverer

CPU = torch.device("cpu")


@pytest.fixture(scope="module")
def gas_agent(tmp_path_factory, tiny_config):
    seed_everything(11, CPU)
    return ag.build_agent(copy.deepcopy(tiny_config), tmp_path_factory.mktemp("gas") / "logs", CPU)


@pytest.fixture(scope="module")
def set_agent(tmp_path_factory, tiny_spec):
    config = c2.make_b02_config(tiny_spec())
    seed_everything(11, CPU)
    return HMASDAgent(config, log_dir=str(tmp_path_factory.mktemp("set") / "logs"), device=CPU)


def _snapshot(agent, frames, labels):
    """Hold two lanes' snapshots decided at frames[0] / frames[1] with ``labels`` (2, 8)."""
    states = np.stack([frames[0]["state"], frames[1]["state"]])
    observations = np.stack([frames[0]["obs"], frames[1]["obs"]])
    if isinstance(agent, ag.GASHMASDAgent):
        agent.env_timers = {0: 0, 1: 0}
        agent.env_agent_skills = {0: np.asarray(labels[0]), 1: np.asarray(labels[1])}
    agent._refresh_central_snapshots(states, observations, np.ones(2, dtype=bool))
    return torch.as_tensor(agent._central_actor_input(np.arange(2), 8))


def test_all_free_equals_set_input_plus_constant_block(gas_agent, set_agent, live_frames):
    frames = [live_frames[0], live_frames[13]]
    current = np.stack([live_frames[5]["obs"], live_frames[18]["obs"]]).reshape(16, 365)
    current = torch.as_tensor(current)
    free = np.full((2, 8), FREE_LABEL)
    gas_central = _snapshot(gas_agent, frames, free)
    set_central = _snapshot(set_agent, frames, free)
    assert gas_central.shape == (16, 3253) and set_central.shape == (16, 3234)
    # The GAS central input carries SET's central input around the anchors and the label.
    torch.testing.assert_close(torch.cat([gas_central[:, :306], gas_central[:, 325:]], dim=1),
                               set_central, rtol=0, atol=0)
    gas_input = gas_agent.skill_discoverer._apply_central_input(current, gas_central)
    set_input = SkillDiscoverer._apply_central_input(set_agent.skill_discoverer, current,
                                                     set_central)
    assert gas_input.shape == (16, 3605) and set_input.shape == (16, 3599)
    block = torch.tensor([0, 0, 0, 0, 0, 1], dtype=torch.float32).expand(16, 6)
    assert torch.equal(gas_input, torch.cat([set_input, block], dim=1))


def test_block_equals_hand_computed_values(gas_agent, live_frames):
    frames = [live_frames[0], live_frames[13]]
    labels = np.asarray([[0, 1, 2, 3, 4, 5, 6, 7], [8, 7, 7, 2, 0, 8, 1, 3]])
    central = _snapshot(gas_agent, frames, labels)
    current_np = np.stack([live_frames[9]["obs"], live_frames[21]["obs"]]).reshape(16, 365)
    current = torch.as_tensor(current_np)
    gas_input = gas_agent.skill_discoverer._apply_central_input(
        current, central, torch.as_tensor(labels.reshape(-1)))
    assert gas_input.shape == (16, 3605)
    torch.testing.assert_close(gas_input[:, :365], current, rtol=0, atol=0)
    for lane in range(2):
        anchors = anchors_from_state(frames[lane]["state"]).astype(np.float32)
        for agent_index in range(8):
            row = lane * 8 + agent_index
            label = labels[lane, agent_index]
            block = gas_input[row, -6:].numpy()
            if label == FREE_LABEL:
                assert block.tolist() == [0, 0, 0, 0, 0, 1]
                continue
            own = current_np[row, 0:2]
            rel = anchors[label] - own
            expected = np.asarray([anchors[label][0], anchors[label][1], rel[0], rel[1],
                                   np.sqrt(rel[0] * rel[0] + rel[1] * rel[1]), 0.0],
                                  dtype=np.float32)
            np.testing.assert_array_equal(block[[0, 1, 2, 3, 5]], expected[[0, 1, 2, 3, 5]])
            # float32 sqrt: numpy's and torch's kernels may differ by one ulp.
            np.testing.assert_allclose(block[4], expected[4], rtol=0, atol=2e-7)
    # One forward of the actor on this input; a label that differs from the stored one is refused.
    hidden = torch.zeros(16, gas_agent.config.gru_hidden_size)
    actions, log_probs, _, _ = gas_agent.skill_discoverer(
        current, torch.as_tensor(labels.reshape(-1)), hidden, central_input=central)
    assert actions.shape == (16, 4) and torch.isfinite(log_probs).all()
    wrong = torch.as_tensor(labels.reshape(-1)).clone()
    wrong[3] = (wrong[3] + 1) % 9
    with pytest.raises(RuntimeError, match="differs"):
        gas_agent.skill_discoverer(current, wrong, hidden, central_input=central)


def test_refresh_without_a_decision_is_refused(gas_agent, live_frames):
    states = np.stack([live_frames[0]["state"]] * 2)
    observations = np.stack([live_frames[0]["obs"]] * 2)
    gas_agent.env_timers = {0: 0, 1: 3}
    gas_agent.env_agent_skills = {0: np.zeros(8, dtype=int), 1: np.zeros(8, dtype=int)}
    with pytest.raises(RuntimeError, match="without a team decision"):
        gas_agent._refresh_central_snapshots(states, observations, np.ones(2, dtype=bool))


def _rng():
    return random.getstate(), np.random.get_state()[1].copy(), torch.random.get_rng_state()


def test_construction_rng_optimizers_and_buffer(tmp_path, tiny_config):
    seed_everything(5, CPU)
    plain = HMASDAgent(copy.deepcopy(tiny_config), log_dir=str(tmp_path / "plain"), device=CPU)
    after_plain = _rng()
    seed_everything(5, CPU)
    gas = ag.build_agent(copy.deepcopy(tiny_config), tmp_path / "gas", CPU)
    after_gas = _rng()
    # Coordinator identical to HMASDAgent(config) at the same seed; python/numpy untouched.
    for (name, a), (_, b) in zip(plain.skill_coordinator.state_dict().items(),
                                 gas.skill_coordinator.state_dict().items(), strict=True):
        assert torch.equal(a, b), name
    assert after_plain[0] == after_gas[0] and np.array_equal(after_plain[1], after_gas[1])
    # The GAS discoverer is drawn after the discarded base one: the torch stream is shifted.
    assert not torch.equal(after_plain[2], after_gas[2])
    assert isinstance(gas.skill_discoverer, ag.GASSkillDiscoverer)
    first = gas.skill_discoverer.actor.base.mlp[0]
    assert first.in_features == 3605 and gas.skill_discoverer.central_input_dim == 3240
    assert gas.skill_discoverer.actor.film_generator.in_features == 9
    assert gas.skill_coordinator is not None and gas.collects_high_level_samples
    assert gas.team_discriminator is None and gas.individual_discriminator is None
    optimized = {id(p) for opt in (gas.discoverer_actor_optimizer, gas.discoverer_critic_optimizer)
                 for group in opt.param_groups for p in group["params"]}
    assert optimized == {id(p) for p in gas.skill_discoverer.parameters()}
    assert isinstance(gas.rollout_buffer, ag.GASRolloutBuffer)
    assert gas.rollout_buffer.central_snapshot_states.shape[-1] == 332
    assert gas.rollout_buffer.get_sampler_rng_state() == plain.rollout_buffer.get_sampler_rng_state()
    assert gas._central_snapshot_states.shape[-1] == 332


def test_configuration_refusals(tmp_path, tiny_config):
    for change in (dict(use_statenorm=True), dict(n_z=6), dict(ordinary_completed_segments=False),
                   dict(disable_high_level_training=True), dict(use_lr_decay=True)):
        config = copy.deepcopy(tiny_config)
        for key, value in change.items():
            setattr(config, key, value)
        with pytest.raises(ValueError, match="GAS configuration refused"):
            ag.build_agent(config, tmp_path / "refused", CPU)


def test_make_b03_config_accepts_tiny_specs(tiny_spec):
    config = make_b03_config(tiny_spec())
    assert config.high_level_buffer_size == 2 * (20 // 10) and config.total_timesteps == 80
