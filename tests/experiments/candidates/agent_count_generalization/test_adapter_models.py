from __future__ import annotations

import numpy as np
import pytest
import torch

from experiments.candidates.agent_count_generalization.adapter import (
    MAX_UAVS,
    STATE_DIM,
    CountAdapter,
    make_envs,
)
from experiments.candidates.agent_count_generalization.configuration import (
    DEFAULT_SPEC,
    FitSpec,
    make_config,
)
from experiments.candidates.agent_count_generalization.models import (
    SetActorBase,
    StateSetEncoder,
    build_agent,
    strict_sync,
)


TINY = FitSpec(
    horizon=10,
    train_lanes=1,
    eval_lanes=1,
    rollouts=1,
    panels=(0, 1),
    hidden_size=32,
    n_heads=4,
    n_layers=1,
    ppo_epochs=1,
    sequence_batch_size=1,
    coordinator_batch_size=10,
    torch_threads=1,
)


def _config(arm, n, seed=17):
    envs = make_envs(1, seed, n, TINY.horizon)
    return envs, make_config(arm, envs, seed, TINY)


@pytest.mark.parametrize("n", [4, 6, 8])
def test_real_s1_adapter_shapes_scaling_step_and_reward_identity(n):
    env = make_envs(1, 101, n, 10)[0]
    assert isinstance(env, CountAdapter)
    obs, info = env.reset(seed=202)
    assert obs.shape == (n, 104)
    assert info["state"].shape == (STATE_DIM,)
    np.testing.assert_array_equal(info["state"][24:32], [1.0] * n + [0.0] * (8 - n))
    assert np.all((info["state"][:24].reshape(8, 3)[:n] >= 0.0))
    assert np.all((info["state"][:24].reshape(8, 3)[:n] <= 1.0))

    next_obs, reward, terminated, truncated, step_info = env.step(
        np.zeros((n, 3), dtype=np.float32)
    )
    assert next_obs.shape == (n, 104)
    assert step_info["next_state"].shape == (STATE_DIM,)
    reward_info = step_info["reward_components"]["reward_info"]
    expected = (
        0.7 * reward_info["coverage_reward"]
        + 0.3 * reward_info["quality_reward"]
        - reward_info["energy_penalty"]
    )
    assert n * reward == pytest.approx(expected, rel=1e-6, abs=1e-7)
    assert not terminated
    assert not truncated
    env.close()


def test_state_set_encoder_ignores_invalid_padding_and_is_uav_permutation_invariant():
    env = make_envs(1, 303, 4, 10)[0]
    _, info = env.reset(seed=404)
    state = torch.as_tensor(info["state"]).unsqueeze(0)
    encoder = StateSetEncoder(17)
    reference = encoder(state)

    perturbed = state.clone()
    perturbed[:, 4 * 3 : 8 * 3] = torch.randn(1, 12) * 1e6
    torch.testing.assert_close(encoder(perturbed), reference)

    permutation = torch.tensor([2, 0, 3, 1, 4, 5, 6, 7])
    permuted = state.clone()
    permuted[:, :24] = state[:, :24].reshape(1, 8, 3)[:, permutation].reshape(1, 24)
    permuted[:, 24:32] = state[:, 24:32][:, permutation]
    torch.testing.assert_close(encoder(permuted), reference, rtol=1e-6, atol=1e-6)

    zero_real = state.clone()
    zero_real[:, :3] = 0.0
    assert torch.isfinite(encoder(zero_real)).all()
    env.close()


def _optimizer_parameter_ids(optimizer):
    return [id(p) for group in optimizer.param_groups for p in group["params"]]


@pytest.mark.parametrize("arm", ["H6", "SET"])
def test_count_modules_are_registered_once_in_their_update_optimizers(tmp_path, arm):
    envs, config = _config(arm, 6)
    agent = build_agent(config, str(tmp_path / arm))
    coordinator_ids = _optimizer_parameter_ids(agent.coordinator_optimizer)
    critic_ids = _optimizer_parameter_ids(agent.discoverer_critic_optimizer)
    assert len(coordinator_ids) == len(set(coordinator_ids))
    assert len(critic_ids) == len(set(critic_ids))
    assert {id(p) for p in agent.skill_coordinator.state_embedding.parameters()} <= set(coordinator_ids)
    assert {id(p) for p in agent.skill_discoverer.critic.base.parameters()} <= set(critic_ids)

    if arm == "SET":
        actor_ids = _optimizer_parameter_ids(agent.discoverer_actor_optimizer)
        assert len(actor_ids) == len(set(actor_ids))
        assert isinstance(agent.skill_discoverer.actor.base, SetActorBase)
        assert {id(p) for p in agent.skill_discoverer.actor.base.parameters()} <= set(actor_ids)
    else:
        team_ids = _optimizer_parameter_ids(agent.team_discriminator_optimizer)
        assert len(team_ids) == len(set(team_ids))
        team_encoders = [m for m in agent.team_discriminator.modules() if isinstance(m, StateSetEncoder)]
        assert len(team_encoders) == 1
        assert {id(p) for p in team_encoders[0].parameters()} <= set(team_ids)
    for env in envs:
        env.close()


@pytest.mark.parametrize("arm", ["H6", "SET"])
def test_strict_cross_n_sync_has_count_independent_keys_and_valid_actions(tmp_path, arm):
    source_envs, source_config = _config(arm, 6, seed=51)
    target_envs, target_config = _config(arm, 4, seed=52)
    source = build_agent(source_config, str(tmp_path / arm / "source"))
    target = build_agent(target_config, str(tmp_path / arm / "target"))

    source_keys = source.skill_coordinator.state_dict()
    target_keys = target.skill_coordinator.state_dict()
    assert source_keys.keys() == target_keys.keys()
    assert all(source_keys[k].shape == target_keys[k].shape for k in source_keys)
    value_keys = [k for k in source_keys if k.startswith("value_heads_obs.")]
    assert value_keys == ["value_heads_obs.head.weight", "value_heads_obs.head.bias"]
    strict_sync(target, source)
    assert not target.training

    obs, info = target_envs[0].reset(seed=52)
    actions, _, _ = target.step(
        info["state"][None, :],
        obs[None, :, :],
        np.zeros(1, dtype=np.int64),
        np.zeros(1, dtype=bool),
        deterministic=True,
        return_step_data=True,
        build_infos=False,
    )
    assert actions.shape == (1, 4, 3)
    assert np.isfinite(actions).all()
    for env in source_envs + target_envs:
        env.close()


def test_set_actor_selects_exact_held_ego_row_in_acting_and_replay(tmp_path):
    envs, config = _config("SET", 4, seed=61)
    agent = build_agent(config, str(tmp_path / "set"))
    base = agent.skill_discoverer.actor.base
    assert isinstance(base, SetActorBase)
    obs, info = envs[0].reset(seed=61)
    current = torch.as_tensor(obs[1] + 7.0).reshape(1, -1)
    state = torch.as_tensor(info["state"]).reshape(1, -1)
    held = torch.as_tensor(obs).reshape(1, 4, 104)
    ego = torch.nn.functional.one_hot(torch.tensor([2]), num_classes=4).float()
    actor_input = torch.cat([current, state, held.reshape(1, -1), ego], dim=-1)

    captured = []
    handle = base.fusion.register_forward_pre_hook(
        lambda _module, args: captured.append(args[0].detach().clone())
    )
    base(actor_input)
    row_width = base.row_encoder[0].out_features
    ego_start = 2 * row_width + 1
    current_start = ego_start + 104
    torch.testing.assert_close(captured[-1][..., ego_start : ego_start + 104], held[:, 2, :])
    torch.testing.assert_close(
        captured[-1][..., current_start : current_start + 104], current
    )

    replay_central = agent._central_actor_input_from_replay(
        state.reshape(1, 1, STATE_DIM),
        held.reshape(1, 1, 4, 104),
        torch.tensor([2]),
    )
    replay_input = agent.skill_discoverer._apply_central_input(
        current.reshape(1, 1, 104), replay_central
    )
    base(replay_input)
    torch.testing.assert_close(
        captured[-1][..., ego_start : ego_start + 104], held[:, 2, :].reshape(1, 1, 104)
    )
    torch.testing.assert_close(
        captured[-1][..., current_start : current_start + 104], current.reshape(1, 1, 104)
    )
    handle.remove()
    for env in envs:
        env.close()


def test_real_set_snapshot_is_held_stored_raw_and_replayed_with_ego_indices(tmp_path):
    envs, config = _config("SET", 4, seed=66)
    env = envs[0]
    agent = build_agent(config, str(tmp_path / "snapshot"))
    obs, info = env.reset(seed=66)
    states = info["state"][None, :]
    observations = obs[None, :, :]
    held_state = states.copy()
    held_obs = observations.copy()
    env_steps = np.zeros(1, dtype=np.int64)
    dones = np.zeros(1, dtype=bool)

    for t in range(2):
        actions, _, step_data = agent.step(
            states,
            observations,
            env_steps,
            dones,
            deterministic=True,
            return_step_data=True,
            build_infos=False,
        )
        next_obs, reward, terminated, truncated, step_info = env.step(actions[0])
        next_states = step_info["next_state"][None, :]
        next_observations = next_obs[None, :, :]
        next_dones = np.asarray([terminated or truncated], dtype=bool)
        agent.store_transition_batch(
            states=states,
            next_states=next_states.copy(),
            observations=observations,
            next_observations=next_observations.copy(),
            actions=actions,
            rewards=np.asarray([reward]),
            dones=next_dones,
            infos_batch=None,
            rollout_step_idx=t,
            step_data=step_data,
        )
        states, observations, dones = next_states, next_observations, next_dones
        env_steps += 1

    np.testing.assert_array_equal(agent.rollout_buffer.central_snapshot_mask[:2], True)
    np.testing.assert_allclose(
        agent.rollout_buffer.central_snapshot_states[:2, 0],
        np.repeat(held_state, 2, axis=0),
    )
    np.testing.assert_allclose(
        agent.rollout_buffer.central_snapshot_obs[:2, 0],
        np.repeat(held_obs, 2, axis=0),
    )
    assert not np.array_equal(states, held_state)

    batches = list(
        agent.rollout_buffer.get_discoverer_sampler(
            ppo_epochs=1,
            num_sequences_per_batch=4,
            chunk_length=2,
            device=torch.device("cpu"),
            cache_tensors=True,
        )
    )
    assert len(batches) == 1
    batch = batches[0]
    assert batch["central_snapshot_states"].shape == (2, 4, STATE_DIM)
    assert batch["central_snapshot_obs"].shape == (2, 4, 4, 104)
    assert sorted(batch["central_ego_indices"].tolist()) == [0, 1, 2, 3]
    for sequence in range(4):
        np.testing.assert_allclose(
            batch["central_snapshot_states"][:, sequence].numpy(),
            np.repeat(held_state, 2, axis=0),
        )
        np.testing.assert_allclose(
            batch["central_snapshot_obs"][:, sequence].numpy(),
            np.repeat(held_obs, 2, axis=0),
        )
    for owned_env in envs:
        owned_env.close()


def test_full_width_set_actor_uses_corrected_721_feature_contract():
    envs = make_envs(1, 71, 6, DEFAULT_SPEC.horizon)
    config = make_config("SET", envs, 71, DEFAULT_SPEC)
    base = SetActorBase(config)
    assert config.obs_dim == 104
    assert base.concat_dim == 721
    obs, info = envs[0].reset(seed=71)
    ego = torch.nn.functional.one_hot(torch.tensor([3]), num_classes=6).float()
    actor_input = torch.cat(
        [
            torch.as_tensor(obs[3]).reshape(1, -1),
            torch.as_tensor(info["state"]).reshape(1, -1),
            torch.as_tensor(obs).reshape(1, -1),
            ego,
        ],
        dim=-1,
    )
    assert base(actor_input).shape == (1, 256)
    for env in envs:
        env.close()
