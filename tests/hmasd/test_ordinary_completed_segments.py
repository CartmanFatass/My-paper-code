"""Real-path checks for opt-in ordinary completed high segments."""

from __future__ import annotations

import copy
import random

import numpy as np
import pytest
import torch

from configs.config_1 import Config
from hmasd.agent import HMASDAgent
from hmasd.utils import RolloutBuffer


def _config(*, lanes=2, rollout_length=12):
    config = Config()
    config.seed = 20260924
    config.num_envs = lanes
    config.rollout_length = rollout_length
    config.episode_length = 24
    config.max_steps = 24
    config.k = 4
    config.n_Z = 3
    config.n_z = 3
    config.action_dim = 2
    config.hidden_size = 32
    config.embedding_dim = 32
    config.n_heads = 4
    config.n_encoder_layers = 1
    config.n_decoder_layers = 1
    config.gru_hidden_size = 32
    config.ppo_epochs = 2
    config.sequence_batch_size = 4
    config.coordinator_batch_size = 4
    config.discriminator_batch_size = 16
    config.use_obsnorm = False
    config.use_statenorm = False
    config.use_valuenorm = True
    config.ordinary_completed_segments = True
    config.update_env_dims(state_dim=5, obs_dim=3, n_agents=2)
    return config


def _parameters(module):
    return [parameter.detach().clone() for parameter in module.parameters()]


def _moved(before, module):
    return any(
        not torch.equal(old, new.detach())
        for old, new in zip(before, module.parameters(), strict=True)
    )


def _record(rows, start, lane=0):
    return next(
        row for row in rows
        if row["start_interaction_index"] == start and row["lane_id"] == lane
    )


def _current_team_value(agent, state, observations):
    with torch.no_grad():
        value, _agent_values, _ = agent.skill_coordinator.get_value(
            torch.as_tensor(state, dtype=torch.float32),
            torch.as_tensor(observations, dtype=torch.float32),
        )
        if agent.config.use_valuenorm:
            value = agent._denormalize_values(value, agent.value_norm_coordinator)
    return value.squeeze(-1).cpu().numpy()


def test_k4_two_lane_two_phase_real_updates_terminal_defer_and_final_censor(tmp_path):
    torch.set_num_threads(1)
    np.random.seed(20260924)
    torch.manual_seed(20260924)
    config = _config()
    agent = HMASDAgent(config, log_dir=str(tmp_path / "logs"), device=torch.device("cpu"))

    phase_seen_low_rows = {0: [], 1: []}
    phase_box = {"value": 0}
    original_sampler = agent.rollout_buffer.get_discoverer_sampler

    def observed_sampler(*args, **kwargs):
        for batch in original_sampler(*args, **kwargs):
            states = batch["global_states"].detach().cpu().numpy()
            masks = batch["masks"].detach().cpu().numpy()
            phase_seen_low_rows[phase_box["value"]].extend(
                states[..., 0][masks].astype(int).tolist()
            )
            yield batch

    agent.rollout_buffer.get_discoverer_sampler = observed_sampler

    states = np.zeros((2, 5), dtype=np.float32)
    observations = np.zeros((2, 2, 3), dtype=np.float32)
    env_steps = np.zeros(2, dtype=np.int64)
    previous_done = np.ones(2, dtype=bool)
    phase_snapshots = []
    initial_high = _parameters(agent.skill_coordinator)
    initial_low = _parameters(agent.skill_discoverer)
    row10_before_update = None

    for phase in range(2):
        phase_box["value"] = phase
        for local_row in range(12):
            row = phase * 12 + local_row
            states[:, 0] = row
            observations[:, :, 0] = row
            actions, _infos, step_data = agent.step(
                states,
                observations,
                env_steps,
                previous_done,
                return_step_data=True,
                build_infos=False,
            )
            next_states = states.copy()
            next_observations = observations.copy()
            next_states[:, 1] = row + 1
            next_observations[:, :, 1] = row + 1
            dones = np.asarray((row == 5, False), dtype=bool)
            rewards = np.asarray((row + 1, row + 2), dtype=np.float32)
            agent.store_transition_batch(
                states,
                next_states,
                observations,
                next_observations,
                actions,
                rewards,
                dones,
                rollout_step_idx=local_row,
                step_data=step_data,
            )
            for lane in range(2):
                if dones[lane]:
                    agent.reset_env_state(lane)
                    env_steps[lane] = 0
                else:
                    env_steps[lane] += 1
            states = next_states.copy()
            observations = next_observations.copy()
            previous_done = dones

        before_update = agent.ordinary_high_level_snapshot()
        if phase == 0:
            row10_before_update = copy.deepcopy(
                _record(before_update["pending_records"], 10)
            )
            assert row10_before_update["duration"] == 2
            assert row10_before_update["end_interaction_index"] == 11
            assert row10_before_update["close_reason"] is None
            assert row10_before_update["end_phase_version"] is None
            boundary_value = _current_team_value(agent, states, observations)[0]
            assert row10_before_update["team_value"] != pytest.approx(boundary_value)
            live_timer = agent.env_timers[0]
            live_skill = int(agent.env_team_skills[0])
            live_actor_hidden = agent.actor_hidden_np[0].copy()

        high_before = _parameters(agent.skill_coordinator)
        low_before = _parameters(agent.skill_discoverer)
        result = agent.update(
            last_values=np.zeros((2, 2), dtype=np.float32),
            dones=previous_done.copy(),
            steps_in_buffer=12,
            last_state=states.copy(),
            last_observations=observations.copy(),
        )
        assert np.isfinite(result["coordinator_loss"])
        assert np.isfinite(result["discoverer_loss"])
        exposure = result["ordinary_completed_segments_metrics"]
        assert exposure["completed_high_records"] == 6
        assert exposure["coordinator_sample_presentations"] == 12
        assert exposure["coordinator_optimizer_steps"] == 4
        assert exposure["low_valid_sample_presentations"] == 96
        assert exposure["low_optimizer_steps"] == 6
        assert exposure["discriminator_team_records"] == 24
        assert exposure["discriminator_individual_records"] == 48
        assert exposure["discriminator_epochs"] == 2
        assert exposure["discriminator_team_sample_presentations"] == 48
        assert exposure["discriminator_individual_sample_presentations"] == 96
        assert exposure["discriminator_team_optimizer_steps"] == 4
        assert exposure["discriminator_individual_optimizer_steps"] == 6
        assert _moved(high_before, agent.skill_coordinator)
        assert _moved(low_before, agent.skill_discoverer)
        after_update = agent.ordinary_high_level_snapshot(final=phase == 1)
        phase_snapshots.append(after_update)
        lane_one = [
            row for row in after_update["consumed_records"]
            if row["lane_id"] == 1
        ]
        assert [row["start_interaction_index"] for row in lane_one] == [
            phase * 12, phase * 12 + 4, phase * 12 + 8
        ]
        assert all(row["duration"] == 4 for row in lane_one)
        assert all(not row["terminal"] for row in lane_one)

        if phase == 0:
            consumed = after_update["consumed_records"]
            row0 = _record(consumed, 0)
            row4 = _record(consumed, 4)
            row6 = _record(consumed, 6)
            gamma4 = config.gamma ** 4
            terminal_advantage = row4["reward_sum"] - row4["team_value"]
            expected_row0 = (
                row0["reward_sum"] + gamma4 * row4["team_value"]
                - row0["team_value"]
                + gamma4 * config.gae_lambda * terminal_advantage
            )
            expected_row6 = (
                row6["reward_sum"] + gamma4 * row10_before_update["team_value"]
                - row6["team_value"]
            )
            assert row4["terminal"] is True
            assert row4["duration"] == 2
            assert row4["successor_kind"] == "terminal"
            assert row4["team_advantage"] == pytest.approx(terminal_advantage)
            assert row0["team_advantage"] == pytest.approx(expected_row0, rel=1e-6)
            assert row6["successor_kind"] == "pending"
            assert row6["bootstrap_team_value"] == pytest.approx(
                row10_before_update["team_value"]
            )
            assert row6["team_advantage"] == pytest.approx(expected_row6, rel=1e-6)
            expected_agent0 = (
                row6["reward_sum"]
                + gamma4 * row10_before_update["agent_values"][0]
                - row6["agent_values"][0]
            )
            assert row6["agent_advantages"][0] == pytest.approx(
                expected_agent0, rel=1e-6
            )
            assert not any(row["start_interaction_index"] == 10 for row in consumed)

            with torch.no_grad():
                replay = agent.skill_coordinator.evaluate_training_batch(
                    torch.as_tensor([row10_before_update["state"]], dtype=torch.float32),
                    torch.as_tensor(
                        [row10_before_update["observations"]], dtype=torch.float32
                    ),
                    torch.as_tensor([row10_before_update["team_skill"]]),
                    torch.as_tensor([row10_before_update["agent_skills"]]),
                )
            current = np.concatenate((
                replay["team_log_probs"].cpu().numpy().reshape(-1),
                replay["agent_log_probs"].cpu().numpy().reshape(-1),
            ))
            behavior = np.asarray([
                row10_before_update["team_log_prob"],
                *row10_before_update["agent_log_probs"],
            ])
            assert np.max(np.abs(current - behavior)) > 1e-7

            agent.clear_buffers()
            assert agent.env_timers[0] == live_timer
            assert int(agent.env_team_skills[0]) == live_skill
            np.testing.assert_array_equal(agent.actor_hidden_np[0], live_actor_hidden)
            pending_after_clear = agent.ordinary_high_level_snapshot()["pending_records"]
            assert _record(pending_after_clear, 10) == row10_before_update
            assert not agent.rollout_buffer.masks.any()
        else:
            consumed = after_update["consumed_records"]
            row10 = _record(consumed, 10)
            for field in (
                "decision_id", "state", "observations", "team_skill", "agent_skills",
                "team_log_prob", "agent_log_probs", "team_value", "agent_values",
            ):
                assert row10[field] == row10_before_update[field]
            assert row10["duration"] == 4
            assert row10["reward_sum"] == pytest.approx(11 + 12 + 13 + 14)
            assert row10["behavior_version"] == 0
            assert row10["low_policy_versions"] == [0, 1]
            assert row10["crosses_policy_version"] is True
            assert row10["consumed_phase_version"] == 2

            row14 = _record(consumed, 14)
            row18 = _record(consumed, 18)
            pending22 = _record(after_update["pending_records"], 22)
            gamma4 = config.gamma ** 4
            a18 = (
                row18["reward_sum"] + gamma4 * pending22["team_value"]
                - row18["team_value"]
            )
            a14 = (
                row14["reward_sum"] + gamma4 * row18["team_value"]
                - row14["team_value"] + gamma4 * config.gae_lambda * a18
            )
            a10 = (
                row10["reward_sum"] + gamma4 * row14["team_value"]
                - row10["team_value"] + gamma4 * config.gae_lambda * a14
            )
            assert row18["successor_kind"] == "pending"
            assert row10["team_advantage"] == pytest.approx(a10, rel=1e-6)
            assert pending22["duration"] == 2
            assert pending22["reward_sum"] == pytest.approx(23 + 24)
            assert pending22["budget_censored"] is True
            assert after_update["counters"]["final_censored"] == 1
            assert after_update["counters"]["cross_version_completions"] == 1

    assert _moved(initial_high, agent.skill_coordinator)
    assert _moved(initial_low, agent.skill_discoverer)
    assert set(phase_seen_low_rows[0]) == set(range(12))
    assert set(phase_seen_low_rows[1]) == set(range(12, 24))
    assert len(phase_seen_low_rows[0]) == 12 * 2 * 2 * config.ppo_epochs
    assert len(phase_seen_low_rows[1]) == 12 * 2 * 2 * config.ppo_epochs


def test_exact_boundary_terminal_closes_once_before_reset(tmp_path):
    torch.set_num_threads(1)
    np.random.seed(17)
    torch.manual_seed(17)
    config = _config(lanes=1, rollout_length=4)
    agent = HMASDAgent(config, log_dir=str(tmp_path / "logs"), device=torch.device("cpu"))
    states = np.zeros((1, 5), dtype=np.float32)
    observations = np.zeros((1, 2, 3), dtype=np.float32)
    done = np.ones(1, dtype=bool)
    for row in range(4):
        actions, _infos, step_data = agent.step(
            states, observations, np.asarray([row]), done,
            return_step_data=True, build_infos=False,
        )
        next_states = states + 1.0
        next_observations = observations + 1.0
        done = np.asarray([row == 3])
        agent.store_transition_batch(
            states, next_states, observations, next_observations, actions,
            np.asarray([1.0]), done, rollout_step_idx=row, step_data=step_data,
        )
        states, observations = next_states, next_observations
    snapshot = agent.ordinary_high_level_snapshot()
    assert len(snapshot["completed_records"]) == 1
    record = snapshot["completed_records"][0]
    assert record["duration"] == 4
    assert record["terminal"] is True
    assert record["close_reason"] == "native_terminal"
    assert snapshot["pending_records"] == []
    agent.reset_env_state(0)
    agent.global_step = 199
    result = agent.update(
        last_values=np.zeros((1, 2), dtype=np.float32),
        dones=done,
        steps_in_buffer=4,
        last_state=states,
        last_observations=observations,
    )
    assert result["ordinary_completed_segments_metrics"][
        "completed_high_records"
    ] == 1
    assert not any(agent.force_high_level_collection.values())


def test_completed_segments_boundary_query_fails_closed(tmp_path, monkeypatch):
    config = _config(lanes=1, rollout_length=4)
    agent = HMASDAgent(config, log_dir=str(tmp_path / "logs"), device=torch.device("cpu"))
    with pytest.raises(ValueError, match="requires last_state and last_observations"):
        agent.update(
            last_values=np.zeros((1, 2), dtype=np.float32),
            dones=np.zeros(1, dtype=bool),
            steps_in_buffer=0,
        )
    assert agent.global_step == 0

    def broken_value_query(*_args, **_kwargs):
        raise ArithmeticError("malformed boundary")

    monkeypatch.setattr(agent.skill_coordinator, "get_value", broken_value_query)
    with pytest.raises(RuntimeError, match="boundary value query failed"):
        agent.update(
            last_values=np.zeros((1, 2), dtype=np.float32),
            dones=np.zeros(1, dtype=bool),
            steps_in_buffer=0,
            last_state=np.zeros((1, 5), dtype=np.float32),
            last_observations=np.zeros((1, 2, 3), dtype=np.float32),
        )
    assert agent.global_step == 0


def test_same_label_decisions_remain_distinct_and_default_clear_is_unchanged():
    buffer = RolloutBuffer(
        4, 1, 2, 3, 2, 4, 3, 3, 5, ordinary_completed_segments=True
    )
    decision_ids = []
    for start in (0, 1):
        decision_ids.append(buffer.ordinary_begin_high_level_record(
            0,
            state=np.full(5, start, dtype=np.float32),
            observations=np.full((2, 3), start, dtype=np.float32),
            team_skill=1,
            agent_skills=np.asarray((2, 2)),
            team_log_prob=-0.5,
            agent_log_probs=np.asarray((-0.7, -0.7)),
            team_value=1.0,
            agent_values=np.asarray((1.0, 1.0)),
        ))
        buffer.ordinary_advance_high_level_record(
            0, reward=1.0, last_state=np.ones(5),
            last_observations=np.ones((2, 3)),
        )
        buffer.ordinary_close_high_level_record(
            0, terminal=False, reason="skill_interval"
        )
    assert decision_ids[0] != decision_ids[1]
    assert len(buffer.ordinary_high_level_snapshot()["completed_records"]) == 2

    default = RolloutBuffer(4, 1, 1, 3, 1, 2, 2, 2, 3)
    assert default.ordinary_completed_segments is False
    default.reset()
    assert not default.masks.any()


def _run_default_aligned(config, log_dir):
    random.seed(8821)
    np.random.seed(8821)
    torch.manual_seed(8821)
    agent = HMASDAgent(config, log_dir=str(log_dir), device=torch.device("cpu"))
    high_presentations = []
    original_high_sampler = agent.rollout_buffer.get_coordinator_sampler

    def observed_high_sampler(*args, **kwargs):
        for batch in original_high_sampler(*args, **kwargs):
            high_presentations.append({
                key: value.detach().cpu().numpy().copy()
                for key, value in batch.items()
                if key in {
                    "states", "observations", "team_skills", "agent_skills",
                    "old_team_log_probs", "old_agent_log_probs",
                    "high_level_elapsed_steps", "high_level_terminal",
                    "team_advantages", "agent_advantages", "team_returns",
                    "agent_returns", "values",
                }
            })
            yield batch

    agent.rollout_buffer.get_coordinator_sampler = observed_high_sampler
    states = np.zeros((2, 5), dtype=np.float32)
    observations = np.zeros((2, 2, 3), dtype=np.float32)
    env_steps = np.zeros(2, dtype=np.int64)
    previous_done = np.ones(2, dtype=bool)
    for row in range(4):
        states[:, 0] = row
        observations[:, :, 0] = row
        actions, _infos, step_data = agent.step(
            states, observations, env_steps, previous_done,
            return_step_data=True, build_infos=False,
        )
        next_states = states.copy()
        next_observations = observations.copy()
        next_states[:, 1] = row + 1
        next_observations[:, :, 1] = row + 1
        dones = np.zeros(2, dtype=bool)
        agent.store_transition_batch(
            states, next_states, observations, next_observations, actions,
            np.asarray((row + 1, row + 2), dtype=np.float32), dones,
            rollout_step_idx=row, step_data=step_data,
        )
        env_steps += 1
        states = next_states
        observations = next_observations
        previous_done = dones
    result = agent.update(
        last_values=np.zeros((2, 2), dtype=np.float32),
        dones=previous_done,
        steps_in_buffer=4,
        last_state=states,
        last_observations=observations,
    )
    parameters = {
        f"{module_name}.{name}": tensor.detach().clone()
        for module_name, module in (
            ("high", agent.skill_coordinator),
            ("low", agent.skill_discoverer),
            ("team_disc", agent.team_discriminator),
            ("agent_disc", agent.individual_discriminator),
        )
        for name, tensor in module.state_dict().items()
    }
    numeric_result = {
        key: float(value) for key, value in result.items()
        if isinstance(value, (int, float, np.integer, np.floating))
    }
    presentation_facts = {
        key: np.concatenate([batch[key] for batch in high_presentations], axis=0)
        for key in high_presentations[0]
    }
    return parameters, numeric_result, presentation_facts


def test_default_false_real_aligned_update_is_exactly_compatible(tmp_path):
    implicit = _config(lanes=2, rollout_length=4)
    del implicit.ordinary_completed_segments
    explicit = _config(lanes=2, rollout_length=4)
    explicit.ordinary_completed_segments = False

    implicit_parameters, implicit_result, implicit_high = _run_default_aligned(
        implicit, tmp_path / "implicit"
    )
    explicit_parameters, explicit_result, explicit_high = _run_default_aligned(
        explicit, tmp_path / "explicit"
    )
    assert implicit_result == explicit_result
    assert implicit_parameters.keys() == explicit_parameters.keys()
    for name in implicit_parameters:
        torch.testing.assert_close(
            implicit_parameters[name], explicit_parameters[name], rtol=0, atol=0
        )
    assert implicit_high.keys() == explicit_high.keys()
    for name in implicit_high:
        np.testing.assert_array_equal(implicit_high[name], explicit_high[name])


def test_completed_segments_true_matches_aligned_default_phase(tmp_path):
    default = _config(lanes=2, rollout_length=4)
    default.ordinary_completed_segments = False
    completed = _config(lanes=2, rollout_length=4)
    completed.ordinary_completed_segments = True

    default_parameters, default_result, default_high = _run_default_aligned(
        default, tmp_path / "default"
    )
    completed_parameters, completed_result, completed_high = _run_default_aligned(
        completed, tmp_path / "completed"
    )

    assert default_high.keys() == completed_high.keys()
    exact_facts = {
        "states", "observations", "team_skills", "agent_skills",
        "old_team_log_probs", "old_agent_log_probs",
        "high_level_elapsed_steps", "high_level_terminal", "values",
    }
    for name in exact_facts:
        np.testing.assert_array_equal(default_high[name], completed_high[name])

    float32_tolerance = 8 * np.finfo(np.float32).eps
    target_facts = {
        "team_advantages", "agent_advantages", "team_returns", "agent_returns"
    }
    for name in target_facts:
        np.testing.assert_allclose(
            default_high[name], completed_high[name],
            rtol=float32_tolerance, atol=float32_tolerance,
        )

    assert default_result.keys() == completed_result.keys()
    for name in default_result:
        assert completed_result[name] == pytest.approx(
            default_result[name], rel=float32_tolerance, abs=float32_tolerance
        )

    assert default_parameters.keys() == completed_parameters.keys()
    for name in default_parameters:
        torch.testing.assert_close(
            default_parameters[name], completed_parameters[name],
            rtol=float32_tolerance, atol=float32_tolerance,
        )


@pytest.mark.parametrize("field", ("use_obsnorm", "use_statenorm"))
def test_completed_segments_reject_input_normalizer_replay(field, tmp_path):
    config = _config(lanes=1, rollout_length=4)
    setattr(config, field, True)
    with pytest.raises(ValueError, match="input normalization"):
        HMASDAgent(config, log_dir=str(tmp_path / field), device=torch.device("cpu"))
