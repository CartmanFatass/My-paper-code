"""Direction-private original-role update view over a physical N6 trajectory."""
from __future__ import annotations

from typing import Any

import numpy as np

from hmasd.utils import RolloutBuffer

LEARNER_ROLES = slice(0, 3)
PHYSICAL_N = 6
LEARNER_N = 3


def learner_buffer(agent: Any, *, horizon: int, lanes: int) -> RolloutBuffer:
    c = agent.config
    if (int(c.n_agents) != PHYSICAL_N or int(c.n_uavs) != PHYSICAL_N or
        int(c.state_dim) != 133 or int(c.obs_dim) != 104 or int(c.action_dim) != 3 or
        bool(c.use_obsnorm) or bool(c.use_statenorm) or not bool(c.use_valuenorm) or
        bool(agent.use_central_snapshot) or bool(agent.use_low_level_compact)):
        raise ValueError("B02 requires physical N6 LOCAL1 task-only model and full critic state")
    return RolloutBuffer(
        num_steps=horizon, num_envs=lanes, n_agents=LEARNER_N,
        obs_dim=104, action_dim=3, gru_hidden_size=int(c.gru_hidden_size),
        n_Z=1, n_z=1, state_dim=133,
        action_space_type="continuous", sampler_seed=int(agent.rollout_sampler_seed),
    )


def store_learner_step(buffer: RolloutBuffer, agent: Any, *, t: int,
                       states: np.ndarray, observations: np.ndarray,
                       raw_actions: np.ndarray, step_data: dict,
                       scalar_rewards: np.ndarray, dones: np.ndarray) -> None:
    """Capture only executed learner rows, before any GAE/normalizer/sampler sees data."""
    lanes = buffer.num_envs
    if (buffer.n_agents != LEARNER_N or states.shape != (lanes, 133) or
        observations.shape != (lanes, PHYSICAL_N, 104) or
        raw_actions.shape != (lanes, PHYSICAL_N, 3) or
        np.asarray(step_data["action_logprobs"]).shape != (lanes, PHYSICAL_N) or
        np.asarray(step_data["values"]).shape != (lanes, PHYSICAL_N) or
        np.asarray(step_data["agent_skills"]).shape != (lanes, PHYSICAL_N) or
        np.asarray(scalar_rewards).shape != (lanes,) or np.asarray(dones).shape != (lanes,)):
        raise ValueError("B02 physical collector/learner update shapes differ")
    if not all(np.isfinite(value).all() for value in (
        states, observations, raw_actions, step_data["action_logprobs"],
        step_data["values"], scalar_rewards,
    )):
        raise ValueError("B02 nonfinite collector input")
    if not (agent.config.disable_discriminator_rewards and float(agent.config.lambda_e) == 1.0):
        raise ValueError("B02 reward must be the native physical N6 scalar")
    for lane in range(lanes):
        okay = buffer.add(
            t=t, env_idx=lane, state=states[lane], obs=observations[lane, LEARNER_ROLES],
            action=raw_actions[lane, LEARNER_ROLES],
            reward=np.full(LEARNER_N, scalar_rewards[lane], dtype=np.float32),
            done=np.full(LEARNER_N, dones[lane], dtype=bool),
            value=np.asarray(step_data["values"])[lane, LEARNER_ROLES],
            log_prob=np.asarray(step_data["action_logprobs"])[lane, LEARNER_ROLES],
            gru_hidden_state=agent.get_prev_actor_hidden_np(lane, n_agents=PHYSICAL_N)[LEARNER_ROLES],
            critic_gru_hidden_state=agent.get_prev_critic_hidden_np(lane, n_agents=PHYSICAL_N)[LEARNER_ROLES],
            team_skill=int(np.asarray(step_data["team_skills"])[lane]),
            agent_skills=np.asarray(step_data["agent_skills"])[lane, LEARNER_ROLES],
            reward_env=np.full(LEARNER_N, scalar_rewards[lane], dtype=np.float32),
        )
        if not okay:
            raise ValueError(f"B02 learner buffer refused lane {lane} step {t}")
    if not np.array_equal(buffer.actions[t], raw_actions[:, LEARNER_ROLES]):
        raise ValueError("B02 raw executed learner actions changed in storage")
    if not np.array_equal(buffer.log_probs[t], np.asarray(step_data["action_logprobs"])[:, LEARNER_ROLES]):
        raise ValueError("B02 learner old log-probabilities changed in storage")


def update_learner(agent: Any, buffer: RolloutBuffer, terminal_dones: np.ndarray) -> tuple[Any, dict]:
    """Call the genuine low-level update with a preselected, compact learner view."""
    if buffer.n_agents != LEARNER_N or int(agent.config.n_agents) != PHYSICAL_N:
        raise ValueError("B02 update changed physical/learner roster contract")
    terminal_dones = np.asarray(terminal_dones, dtype=bool)
    if terminal_dones.shape != (buffer.num_envs,) or not terminal_dones.all():
        raise ValueError("B02 requires complete terminal native episodes before update")
    steps = int(buffer._get_full_rollout_data()["num_actual_steps"])
    if (steps != buffer.num_steps or steps % int(agent.config.k) or
        not np.all(buffer.masks[:steps]) or not np.all(buffer.dones[steps - 1])):
        raise ValueError("B02 learner update view has missing rows")
    expected_chunks = max(1, steps // int(agent.config.k))
    expected_sequences = expected_chunks * buffer.num_envs * LEARNER_N
    expected_per_epoch = (expected_sequences + int(agent.config.sequence_batch_size) - 1) // int(agent.config.sequence_batch_size)
    audit = {"time_steps": steps, "expected_sequences_per_epoch": expected_sequences,
             "minibatches": 0, "sampled_sequences": 0, "batch_sizes": [], "chunk_lengths": [],
             "learner_roles": [0, 1, 2], "physical_n": PHYSICAL_N, "update_n": LEARNER_N}
    original_buffer = agent.rollout_buffer
    original_sampler = buffer.get_discoverer_sampler
    def counted_sampler(*args: Any, **kwargs: Any):
        for batch in original_sampler(*args, **kwargs):
            size = int(batch["observations"].shape[1])
            audit["minibatches"] += 1
            audit["sampled_sequences"] += size
            audit["batch_sizes"].append(size)
            audit["chunk_lengths"].append(int(batch["observations"].shape[0]))
            if batch["global_states"].shape[-1] != 133 or batch["observations"].shape[-1] != 104:
                raise ValueError("B02 sampler lost full physical critic/private actor inputs")
            yield batch
    buffer.get_discoverer_sampler = counted_sampler
    agent.rollout_buffer = buffer
    try:
        losses = agent.update_discoverer_from_rollout(
            np.zeros((buffer.num_envs, LEARNER_N), dtype=np.float32),
            np.asarray(terminal_dones, dtype=bool).copy(),
        )
    finally:
        agent.rollout_buffer = original_buffer
        buffer.get_discoverer_sampler = original_sampler
    expected_batches = expected_per_epoch * int(agent.config.ppo_epochs)
    if (audit["minibatches"] != expected_batches or
        audit["sampled_sequences"] != expected_sequences * int(agent.config.ppo_epochs) or
        any(length != min(steps, int(agent.config.k)) for length in audit["chunk_lengths"])):
        raise ValueError(f"B02 learner sequence exposure differs from fixed sampler: {audit}")
    return losses, audit
