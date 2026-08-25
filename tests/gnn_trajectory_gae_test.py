from types import SimpleNamespace
import random

import numpy as np
import pytest
import torch
from torch import nn

from gnn_hmasd.agent import GNNHMASDAgent
from gnn_hmasd.networks import GNNRoleAssigner, TaskExecutor
from hmasd.utils import ReplayBuffer


class _ValueOnlyExecutor(nn.Module):
    def forward(self, observations, roles, deterministic=False):
        del roles, deterministic
        batch = observations.shape[0]
        return (
            torch.zeros((batch, 1), device=observations.device),
            torch.zeros(batch, device=observations.device),
            observations[:, 0],
        )

    def get_value(self, observations, roles):
        del roles
        return observations[:, 0]


class _IdentityGraphLayer(nn.Module):
    def forward(self, x, edge_index):
        del edge_index
        return x


def _agent():
    agent = GNNHMASDAgent.__new__(GNNHMASDAgent)
    agent.config = SimpleNamespace(
        n_agents=1,
        obs_dim=1,
        action_dim=1,
        num_roles=1,
        node_feature_dim=3,
        hidden_size=8,
        role_embedding_dim=2,
        lambda_e=1.0,
        batch_size=2,
        high_level_batch_size=2,
        replay_gae_segment_length=2,
        gamma=1.0,
        gae_lambda=1.0,
        k=100,
    )
    agent.device = torch.device("cpu")
    agent.task_executor = _ValueOnlyExecutor()
    agent.low_level_buffer = ReplayBuffer(8)
    agent.high_level_buffer = []
    agent.env_reward_sums = {0: 0.0}
    agent._pending_high_samples = {}
    agent._pending_low_segments = {}
    agent._unbootstrapped_low_rows = {}
    agent._pending_high_segments = {0: []}
    agent._low_episode_ids = {0: 0}
    agent._low_timesteps = {}
    agent._low_segment_ids = {}
    agent._high_episode_ids = {0: 0}
    agent._high_timesteps = {0: 0}
    agent._high_segment_ids = {0: 0}
    agent._low_rows_since_update = 0
    agent._high_rows_since_update = 0
    agent._collection_tokens = {}
    agent._collection_frontiers = {}
    agent._collection_token_counter = 0
    return agent


def _attach_token(agent, obs, actions, info):
    token = agent._register_collection_token(
        info['env_id'], obs, actions, info['roles'], info['action_logprobs'],
        info['low_level_values'], info['skill_timer'],
    )
    info = dict(info)
    info['collection_token'] = token
    return info


def test_gnn_low_gae_is_frozen_on_ordered_segment_before_sampling():
    agent = _agent()
    base_info = {
        'env_id': 0,
        'roles': np.array([0]),
        'action_logprobs': np.array([-0.1]),
        'low_level_values': np.array([0.0]),
        'skill_timer': 0,
    }
    first_obs = np.array([[0.0]])
    first_actions = np.array([[0.0]])
    first_info = _attach_token(agent, first_obs, first_actions, base_info)
    agent.store_transition(
        first_obs,
        np.array([[1.0]]),
        first_actions,
        np.array([1.0]),
        np.array([False]),
        first_info,
    )
    agent._complete_low_bootstraps(0, torch.tensor([1.0]))
    second_info = dict(base_info)
    second_info['low_level_values'] = np.array([1.0])
    second_obs = np.array([[1.0]])
    second_actions = np.array([[0.0]])
    second_info = _attach_token(agent, second_obs, second_actions, second_info)
    agent.store_transition(
        second_obs,
        np.array([[2.0]]),
        second_actions,
        np.array([2.0]),
        np.array([False]),
        second_info,
    )
    agent._complete_low_bootstraps(0, torch.tensor([2.0]))

    rows = list(agent.low_level_buffer.buffer)
    assert [row['timestep'] for row in rows] == [0, 1]
    np.testing.assert_allclose([row['advantage'] for row in rows], [5.0, 3.0])
    np.testing.assert_allclose([row['return'] for row in rows], [5.0, 4.0])
    assert not agent._pending_low_segments

    sample = agent.low_level_buffer.sample_torch(2, torch.device("cpu"))
    sampled_advantages = sorted(sample[-2].tolist())
    assert sampled_advantages == [3.0, 5.0]


def test_task_executor_collection_replay_old_logp_parity():
    torch.manual_seed(9081)
    config = SimpleNamespace(
        obs_dim=3,
        action_dim=2,
        hidden_size=8,
        num_roles=2,
        role_embedding_dim=4,
    )
    executor = TaskExecutor(config)
    observations = torch.randn(5, 3)
    roles = torch.tensor([0, 1, 0, 1, 1])
    actions, collected_logp, collected_values = executor(observations, roles)
    replay_logp, _entropy, replay_values = executor.evaluate_actions(
        observations, roles, actions
    )
    torch.testing.assert_close(replay_logp, collected_logp, rtol=0, atol=1e-7)
    torch.testing.assert_close(replay_values, collected_values, rtol=0, atol=1e-7)


def test_gnn_step_token_rejects_mismatch_and_storage_is_immutable():
    agent = _agent()
    agent.task_executor = TaskExecutor(agent.config)
    agent.env_roles = {0: np.array([0])}
    agent.env_timers = {0: 0}

    class Env:
        agents = ["uav-0"]
        observation = np.array([1.25], dtype=np.float32)

        def _get_observation(self, _agent_id):
            return {'obs': self.observation}

    env = Env()
    actions, info = agent.step(env, ep_t=1, env_id=0)
    collected_obs = np.array([[1.25]], dtype=np.float32)
    bad_obs = collected_obs.copy()
    bad_obs[0, 0] = 99.0
    with pytest.raises(ValueError, match="does not match exact collection input"):
        agent.store_transition(
            bad_obs, np.array([[2.0]], dtype=np.float32), actions,
            np.array([1.0]), np.array([False]), info,
        )

    next_obs = np.array([[2.0]], dtype=np.float32)
    rewards = np.array([1.0], dtype=np.float32)
    dones = np.array([False])
    stored_actions = actions.copy()
    stored_info = {key: clone.copy() if isinstance(clone, np.ndarray) else clone for key, clone in info.items()}
    agent.store_transition(collected_obs, next_obs, actions, rewards, dones, info)
    row = agent._pending_low_segments[(0, 0)][0]
    replay_logp, _entropy, _value = agent.task_executor.evaluate_actions(
        torch.as_tensor(row['obs']).reshape(1, -1),
        torch.as_tensor([row['role']]),
        torch.as_tensor(row['action']).reshape(1, -1),
    )
    torch.testing.assert_close(
        replay_logp, torch.as_tensor([row['old_log_prob']]), rtol=0, atol=1e-7
    )

    env.observation[...] = -50
    collected_obs[...] = -51
    next_obs[...] = -52
    actions[...] = -53
    rewards[...] = -54
    dones[...] = True
    info['roles'][...] = 99
    info['action_logprobs'][...] = 99
    info['low_level_values'][...] = 99
    np.testing.assert_array_equal(row['obs'], [1.25])
    np.testing.assert_array_equal(row['next_obs'], [2.0])
    np.testing.assert_array_equal(row['action'], stored_actions[0])
    assert row['old_log_prob'] == stored_info['action_logprobs'][0]
    with pytest.raises(ValueError, match="stale, or reused"):
        agent.store_transition(
            np.array([[1.25]]), np.array([[2.0]]), stored_actions,
            np.array([1.0]), np.array([False]), stored_info,
        )


def test_role_assigner_evaluates_stored_roles_and_pools_values_per_graph():
    torch.manual_seed(9082)
    assigner = GNNRoleAssigner.__new__(GNNRoleAssigner)
    nn.Module.__init__(assigner)
    assigner.conv1 = _IdentityGraphLayer()
    assigner.conv2 = _IdentityGraphLayer()
    assigner.role_head = nn.Linear(3, 2)
    assigner.value_head = nn.Linear(3, 1)
    assigner.train()
    graph = SimpleNamespace(
        x=torch.randn(4, 3),
        edge_index=torch.empty((2, 0), dtype=torch.long),
        uav_mask=torch.tensor([0, 2, 3]),
        batch=torch.tensor([0, 0, 1, 1]),
    )
    roles, collected_logp, _logits, values = assigner(graph)
    replay_logp, _entropy, replay_values, uav_batch = assigner.evaluate_roles(
        graph, roles
    )
    torch.testing.assert_close(replay_logp, collected_logp, rtol=0, atol=1e-7)
    torch.testing.assert_close(replay_values, values, rtol=0, atol=1e-7)
    assert values.shape == (2,)
    encoded = torch.relu(graph.x)
    expected_values = assigner.value_head(
        torch.stack([encoded[:2].mean(dim=0), encoded[2:].mean(dim=0)])
    ).squeeze(-1)
    torch.testing.assert_close(values, expected_values, rtol=0, atol=1e-7)
    torch.testing.assert_close(uav_batch, torch.tensor([0, 1, 1]))


def _checkpoint_agent(populate=False):
    agent = GNNHMASDAgent.__new__(GNNHMASDAgent)
    agent.config = SimpleNamespace(
        n_agents=1,
        obs_dim=1,
        action_dim=1,
        hidden_size=8,
        num_roles=2,
        role_embedding_dim=2,
        node_feature_dim=3,
        replay_gae_segment_length=1,
        batch_size=2,
        high_level_replay_gae_segment_length=2,
        high_level_batch_size=2,
        gamma=1.0,
        gae_lambda=1.0,
        lambda_e=1.0,
        k=100,
    )
    agent.device = torch.device("cpu")
    agent.role_assigner = GNNRoleAssigner.__new__(GNNRoleAssigner)
    nn.Module.__init__(agent.role_assigner)
    agent.role_assigner.conv1 = _IdentityGraphLayer()
    agent.role_assigner.conv2 = _IdentityGraphLayer()
    agent.role_assigner.role_head = nn.Linear(3, 2)
    agent.role_assigner.value_head = nn.Linear(3, 1)
    agent.role_assigner.num_roles = 2
    agent.role_assigner.node_feature_dim = 3
    agent.task_executor = TaskExecutor(agent.config)
    agent.assigner_optimizer = torch.optim.Adam(agent.role_assigner.parameters())
    agent.executor_optimizer = torch.optim.Adam(agent.task_executor.parameters())
    agent.low_level_buffer = ReplayBuffer(8, rng_seed=101)
    agent._high_replay_rng = np.random.default_rng(202)
    agent.high_level_buffer = []
    agent._pending_high_samples = {}
    agent._pending_low_segments = {}
    agent._unbootstrapped_low_rows = {}
    agent._pending_high_segments = {0: []}
    agent._low_episode_ids = {0: 3}
    agent._low_timesteps = {}
    agent._low_segment_ids = {}
    agent._high_episode_ids = {0: 3}
    agent._high_timesteps = {0: 0}
    agent._high_segment_ids = {0: 0}
    agent._low_rows_since_update = 0
    agent._high_rows_since_update = 0
    agent.env_roles = {0: np.array([0])}
    agent.env_timers = {0: 2}
    agent.env_reward_sums = {0: 1.5}
    agent.high_level_obs = None
    agent.global_step = 11
    agent._collection_tokens = {}
    agent._collection_frontiers = {}
    agent._collection_token_counter = 0
    if populate:
        for index in range(4):
            agent.low_level_buffer.push({
                'obs': np.array([float(index)]),
                'next_obs': np.array([float(index + 1)]),
                'action': np.array([0.0]),
                'reward': 1.0,
                'done': True,
                'old_log_prob': -0.1,
                'role': 0,
                'old_value': 0.0,
                'advantage': 1.0,
                'return': 1.0,
                'trajectory_id': f'complete:{index}',
                'timestep': 0,
            })
        pending = {
            'obs': np.array([9.0]),
            'next_obs': np.array([10.0]),
            'action': np.array([0.0]),
            'reward': 2.0,
            'done': False,
            'old_log_prob': -0.2,
            'role': 0,
            'old_value': 1.0,
            'trajectory_id': 'gnn-low:0:3:0:0',
            'timestep': 0,
        }
        agent._pending_low_segments[(0, 0)] = [pending]
        agent._unbootstrapped_low_rows[(0, 0)] = pending
        agent._low_timesteps[(0, 0)] = 1
        agent._low_segment_ids[(0, 0)] = 0
    return agent


def test_gnn_checkpoint_strictly_restores_independent_replay_rngs(tmp_path):
    source = _checkpoint_agent(populate=True)
    token_obs = np.array([[7.0]])
    token_actions = np.array([[0.5]])
    token_info = {
        'env_id': 2, 'roles': np.array([0]), 'action_logprobs': np.array([-0.7]),
        'low_level_values': np.array([0.25]), 'skill_timer': 0,
    }
    source.env_reward_sums[2] = 0.0
    source._low_episode_ids[2] = 0
    token_info = _attach_token(source, token_obs, token_actions, token_info)
    checkpoint_path = tmp_path / "gnn.pt"
    source.save_model(checkpoint_path)
    sample_graph = SimpleNamespace(
        x=torch.tensor([[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]]),
        edge_index=torch.empty((2, 0), dtype=torch.long),
        uav_mask=torch.tensor([True, False]),
    )
    expected_next_role = source.role_assigner(sample_graph)[0]
    expected_next_action = source.task_executor(
        torch.tensor([[0.25]]), torch.tensor([1])
    )[0]
    expected_low = source.low_level_buffer.sample(4)
    expected_high = source._high_replay_rng.choice(20, 5, replace=False)
    source._complete_low_bootstraps(0, torch.tensor([3.0]))
    expected_final = list(source.low_level_buffer.buffer)[-1]
    token_next_obs = np.array([[8.0]])
    source.store_transition(
        token_obs, token_next_obs, token_actions, np.array([2.0]),
        np.array([True]), token_info,
    )
    expected_token_row = list(source.low_level_buffer.buffer)[-1]

    restored = _checkpoint_agent(populate=False)
    restored.load_model(checkpoint_path)
    actual_next_role = restored.role_assigner(sample_graph)[0]
    actual_next_action = restored.task_executor(
        torch.tensor([[0.25]]), torch.tensor([1])
    )[0]
    torch.testing.assert_close(actual_next_role, expected_next_role)
    torch.testing.assert_close(actual_next_action, expected_next_action)
    assert restored.low_level_buffer.sample(4) == expected_low
    np.testing.assert_array_equal(
        restored._high_replay_rng.choice(20, 5, replace=False), expected_high
    )
    assert (0, 0) in restored._unbootstrapped_low_rows
    assert (
        restored._unbootstrapped_low_rows[(0, 0)]
        is restored._pending_low_segments[(0, 0)][-1]
    )
    restored._complete_low_bootstraps(0, torch.tensor([3.0]))
    restored_final = list(restored.low_level_buffer.buffer)[-1]
    assert restored_final['trajectory_id'] == expected_final['trajectory_id']
    assert restored_final['advantage'] == expected_final['advantage']
    assert restored_final['return'] == expected_final['return']
    restored.store_transition(
        token_obs, token_next_obs, token_actions, np.array([2.0]),
        np.array([True]), token_info,
    )
    restored_token_row = list(restored.low_level_buffer.buffer)[-1]
    for name in ('obs', 'next_obs', 'action'):
        np.testing.assert_array_equal(restored_token_row[name], expected_token_row[name])
    assert restored_token_row['old_log_prob'] == expected_token_row['old_log_prob']

    invalid_path = tmp_path / "gnn-invalid.pt"
    torch.save({'role_assigner': source.role_assigner.state_dict()}, invalid_path)
    with pytest.raises(ValueError, match="missing strict state"):
        restored.load_model(invalid_path)

    topology_path = tmp_path / "gnn-topology-invalid.pt"
    invalid_topology = torch.load(checkpoint_path, weights_only=False)
    invalid_topology['topology']['n_agents'] = 2
    torch.save(invalid_topology, topology_path)
    with pytest.raises(ValueError, match="topology does not match"):
        restored.load_model(topology_path)

    device_path = tmp_path / "gnn-device-invalid.pt"
    invalid_device = torch.load(checkpoint_path, weights_only=False)
    invalid_device['topology']['policy_device'] = {'type': 'cuda', 'index': 0}
    torch.save(invalid_device, device_path)
    with pytest.raises(ValueError, match="policy parameter device"):
        restored.load_model(device_path)

    rng_path = tmp_path / "gnn-rng-invalid.pt"
    invalid_rng = torch.load(checkpoint_path, weights_only=False)
    invalid_rng['torch_sampling_rng_state']['cuda_initialized'] = False
    invalid_rng['torch_sampling_rng_state']['cuda'] = []
    invalid_rng['torch_sampling_rng_state']['cuda_device_count'] = 1
    torch.save(invalid_rng, rng_path)
    before_failed_load = torch.get_rng_state().clone()
    with pytest.raises(ValueError, match="CUDA RNG states without initialization"):
        restored.load_model(rng_path)
    torch.testing.assert_close(torch.get_rng_state(), before_failed_load)


def test_gnn_legacy_warm_start_is_explicit_weights_only_and_fail_closed(tmp_path):
    source = _checkpoint_agent(populate=True)
    legacy = {
        'role_assigner': source.role_assigner.state_dict(),
        'task_executor': source.task_executor.state_dict(),
    }
    legacy_path = tmp_path / 'gnn-legacy.pt'
    torch.save(legacy, legacy_path)

    target = _checkpoint_agent(populate=True)
    target._collection_tokens['token'] = {
        'env_id': 8, 'observations': np.zeros((1, 1)), 'actions': np.zeros((1, 1)),
        'roles': np.zeros(1), 'old_log_probs': np.zeros(1),
        'old_values': np.zeros(1), 'skill_timer': 0,
    }
    target._collection_frontiers[8] = 'token'
    with torch.no_grad():
        for parameter in target.role_assigner.parameters():
            parameter.zero_()
        for parameter in target.task_executor.parameters():
            parameter.zero_()
    target.load_warm_start(legacy_path)
    for name, tensor in source.role_assigner.state_dict().items():
        torch.testing.assert_close(target.role_assigner.state_dict()[name], tensor)
    for name, tensor in source.task_executor.state_dict().items():
        torch.testing.assert_close(target.task_executor.state_dict()[name], tensor)
    assert len(target.low_level_buffer) == 0
    assert not target.high_level_buffer
    assert not target._pending_low_segments
    assert not target._collection_tokens
    assert target.global_step == 0
    assert not target.assigner_optimizer.state
    assert not target.executor_optimizer.state
    assert target.low_level_buffer.get_rng_state() == random.Random(1701).getstate()
    expected_high_rng = np.random.default_rng(1702).choice(20, 4, replace=False)
    np.testing.assert_array_equal(
        target._high_replay_rng.choice(20, 4, replace=False), expected_high_rng
    )

    with pytest.raises(ValueError, match="missing strict state"):
        target.load_model(legacy_path)
    for name, payload in {
        'partial': {'role_assigner': legacy['role_assigner']},
        'mixed': {**legacy, 'checkpoint_version': 1},
        'wrong': {
            'role_assigner': {'weight': torch.zeros(99)},
            'task_executor': legacy['task_executor'],
        },
    }.items():
        path = tmp_path / f'gnn-legacy-{name}.pt'
        torch.save(payload, path)
        with pytest.raises(ValueError, match="legacy GNN"):
            target.load_warm_start(path)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_gnn_strict_checkpoint_restores_cuda_distribution_rng(tmp_path):
    cpu_source = _checkpoint_agent(populate=False)
    cpu_path = tmp_path / 'gnn-cpu-for-cuda.pt'
    cpu_source.save_model(cpu_path)

    source = _checkpoint_agent(populate=False)
    source.device = torch.device('cuda')
    source.role_assigner = source.role_assigner.cuda()
    source.task_executor = source.task_executor.cuda()
    path = tmp_path / 'gnn-cuda.pt'
    source.save_model(path)
    expected = torch.distributions.Normal(
        torch.zeros(4, device='cuda'), torch.ones(4, device='cuda')
    ).sample()

    restored = _checkpoint_agent(populate=False)
    restored.device = torch.device('cuda')
    restored.role_assigner = restored.role_assigner.cuda()
    restored.task_executor = restored.task_executor.cuda()
    with pytest.raises(ValueError, match="policy parameter device"):
        restored.load_model(cpu_path)
    restored.load_model(path)
    actual = torch.distributions.Normal(
        torch.zeros(4, device='cuda'), torch.ones(4, device='cuda')
    ).sample()
    torch.testing.assert_close(actual, expected)

    malformed = torch.load(path, map_location='cpu', weights_only=False)
    malformed['torch_sampling_rng_state']['cuda_device_count'] += 1
    malformed_path = tmp_path / 'gnn-cuda-mismatch.pt'
    torch.save(malformed, malformed_path)
    with pytest.raises(ValueError, match="device-count/state mismatch"):
        restored.load_model(malformed_path)

    if torch.cuda.device_count() >= 2:
        different_index = _checkpoint_agent(populate=False)
        different_index.device = torch.device('cuda:1')
        different_index.role_assigner = different_index.role_assigner.to('cuda:1')
        different_index.task_executor = different_index.task_executor.to('cuda:1')
        with pytest.raises(ValueError, match="policy parameter device"):
            different_index.load_model(path)
