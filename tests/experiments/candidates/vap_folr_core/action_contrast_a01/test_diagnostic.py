import copy

import numpy as np
import pytest
import torch

from experiments.candidates.vap_folr_core.action_contrast_a01 import diagnostic
from experiments.candidates.vap_folr_core.entity_history_b01.environment import EntityHistoryEnv


def activity():
    return {
        "actor_forward_calls": 0,
        "full_forward_calls": 0,
        "reset_forward_calls": 0,
        "factual_transition_calls": 0,
        "counterfactual_transition_calls": 0,
        "observation_boundaries_verified": 0,
        "active_action_checks": 0,
        "factual_reward_checks": 0,
        "native_return_checks": 0,
        "replayed_episodes": 0,
        "selected_rows": 0,
        "rows_written": 0,
    }


def rng_equal(first, second):
    return first[0] == second[0] and np.array_equal(first[1], second[1]) and first[2:] == second[2:]


def geometry_observation():
    entities = np.zeros((5, 4), dtype=np.float32)
    entities[0, 2:4] = np.asarray((3, 3), dtype=np.float32) / 7
    entities[1, 2:4] = np.asarray((3, 1), dtype=np.float32) / 7
    seen = np.zeros((5, 5), dtype=bool)
    seen[0, 1] = True
    return {
        "entities": entities,
        "entity_mask": np.asarray([False, False, True, True, True]),
        "seen": seen,
        "visible": np.zeros((5, 5), dtype=bool),
    }


def test_selected_predicate_is_active_seen_hidden_axis_distance_two():
    observation = geometry_observation()
    assert diagnostic.selected_observers(observation).tolist() == [True, False, False, False, False]
    observation["visible"][0, 1] = True
    assert not diagnostic.selected_observers(observation).any()
    observation = geometry_observation()
    observation["entity_mask"][1] = True
    assert not diagnostic.selected_observers(observation).any()
    observation = geometry_observation()
    observation["entities"][1, 2] = np.float32(3.2 / 7)
    with pytest.raises(diagnostic.DiagnosticMismatch, match="coordinate reconstruction"):
        diagnostic.selected_observers(observation)


def analytic_env(b_position):
    env = EntityHistoryEnv(difficulty="easy", vision=1, seed=71)
    env.reset()
    env.entity_mask = np.ones(5)
    env.entity_mask[:2] = 0
    env.cars_pos = np.zeros((5, 2), dtype=float)
    env.cars_pos[0] = (3, 3)
    env.cars_pos[1] = b_position
    env.last_cars_pos = env.cars_pos.copy()
    env.cars_target = np.zeros((5, 2), dtype=float)
    env.cars_target[0] = (3, 6)
    env.cars_target[1] = (0, 3)
    env.wait = np.zeros(5)
    env.wait[:2] = 7
    env.t = 7
    env.collision_times = 0
    env.time_penalty = 0
    env.target_close_reward = 0
    env.exist_car_num_list = [2]
    env.add_rate = 0
    env.birth = np.zeros(5, dtype=bool)
    env.departure = np.zeros(5, dtype=bool)
    env.continuation = np.asarray([True, True, False, False, False])
    env.event = False
    env.seen = np.zeros((5, 5), dtype=bool)
    env.age = np.zeros((5, 5), dtype=np.int16)
    env._observe_boundary()
    return env


@pytest.mark.parametrize(
    "b_position,b_action,expected",
    [
        ((3, 1), 1, [0.84, 1.84, -10.16, -0.16, -0.16]),
        ((3, 5), 2, [0.84, -8.16, -0.16, -0.16, -0.16]),
    ],
)
def test_native_analytic_reward_vectors_and_branch_global_rng_isolation(
    b_position, b_action, expected
):
    env = analytic_env(b_position)
    recorded = np.asarray([0, b_action, 0, 0, 0], dtype=np.int64)
    np.random.seed(5107)
    before = copy.deepcopy(np.random.get_state())
    counts = activity()
    rewards, collisions = diagnostic.nonfactual_action_values(
        env, recorded, focal_agent=0, factual_action=0, activity=counts
    )
    assert rng_equal(before, np.random.get_state())
    assert counts["counterfactual_transition_calls"] == 4
    assert env.t == 7 and env.collision_times == 0
    factual_reward, _, _ = env.step(recorded)
    rewards[0] = float(factual_reward)
    collisions[0] = int(env.collision_times)
    assert rewards == pytest.approx(expected, abs=1e-12)
    assert max(collisions) != min(collisions)


class SyntheticEnv:
    max_steps = 20

    def reset(self):
        self.t = 0
        self.collision_times = 0
        self.previous = np.zeros(5, dtype=np.int64)

    def observation(self, previous):
        continuation = np.ones(5, dtype=bool)
        if self.t == 0:
            continuation[:] = False
        return {
            "entities": np.zeros((5, 4), dtype=np.float32),
            "obs_mask": np.zeros((5, 5), dtype=bool),
            "entity_mask": np.zeros(5, dtype=bool),
            "birth": ~continuation,
            "continuation": continuation,
            "event": np.asarray(False),
            "previous_action": np.eye(5, dtype=np.float32)[previous],
            "departure": np.zeros(5, dtype=bool),
            "visible": np.ones((5, 5), dtype=bool),
            "seen": np.ones((5, 5), dtype=bool),
            "age": np.zeros((5, 5), dtype=np.int16),
        }

    def step(self, actions):
        self.t += 1
        return np.float64(actions.sum()), self.t == 20, {}


class SyntheticActor(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.scale = torch.nn.Parameter(torch.ones(()))

    def forward(self, batch, hidden=None):
        b, t = batch["entities"].shape[:2]
        q = torch.zeros(b, t, 5, 5)
        q[..., 0] = self.scale
        state = torch.zeros(b, t, 5, 1) if hidden is None else hidden[:, None] + 1
        return q, state


def synthetic_panel():
    env = SyntheticEnv()
    episodes = []
    returns = []
    for _ in range(1):
        env.reset()
        previous = np.zeros(5, dtype=np.int64)
        observations = []
        actions, rewards, terminals = [], [], []
        for time_index in range(21):
            observations.append(env.observation(previous))
            if time_index == 20:
                break
            action = np.zeros(5, dtype=np.int64)
            reward, done, _ = env.step(action)
            actions.append(action)
            rewards.append(reward)
            terminals.append(done)
            previous = action
        panel = {
            key: np.stack([row[key] for row in observations])[None]
            for key in observations[0]
        }
        panel.update(
            actions=np.asarray(actions, dtype=np.int64)[None],
            reward=np.asarray(rewards, dtype=np.float32)[None],
            terminated=np.asarray(terminals, dtype=np.float32)[None],
        )
        episodes.append(panel)
        returns.append(float(sum(rewards)))
    return episodes[0], returns


def test_serial_replay_checks_all_active_actions_and_keeps_parameters(monkeypatch):
    monkeypatch.setattr(diagnostic, "PANEL_EPISODES", 1)
    panel, returns = synthetic_panel()
    actor = SyntheticActor()
    before = diagnostic.actor_state_sha256(actor)
    rows = []
    counts = activity()
    diagnostic.replay_panel(
        SyntheticEnv(), actor, panel, returns, "SYNTHETIC", rows.append, counts
    )
    assert not rows
    assert counts["actor_forward_calls"] == 42
    assert counts["active_action_checks"] == 100
    assert counts["factual_transition_calls"] == 20
    assert diagnostic.actor_state_sha256(actor) == before

    broken = {key: value.copy() for key, value in panel.items()}
    broken["actions"][0, 3, 0] = 1
    with pytest.raises(diagnostic.DiagnosticMismatch, match="full greedy action mismatch"):
        diagnostic.replay_panel(
            SyntheticEnv(), actor, broken, returns, "SYNTHETIC", rows.append, activity()
        )


def test_summary_marks_nonadditive_rows_and_empty_collision_subset_null(monkeypatch):
    monkeypatch.setattr(diagnostic, "PANEL_EPISODES", 2)
    row = {
        "episode": 0,
        "action_changed": True,
        "nonflat_action_contrast": True,
        "collision_sensitive": False,
        "factual_full_regret": 0.5,
        "reset_regret": 1.0,
        "full_minus_reset_immediate_reward": 0.5,
    }
    result = diagnostic.summarize_rows([row])
    assert result["selected_row_count"] == result["nonflat_action_contrast_count"] == 1
    assert result["factual_full_positive_regret_count"] == 1
    assert result["collision_sensitive_count"] == 0
    assert result["collision_sensitive_regret"] is None
    assert result["per_episode"][0]["nonadditive_local_factual_full_regret_sum"] == 0.5
    assert result["per_episode"][1]["nonadditive_local_factual_full_regret_sum"] is None
    assert "not potential episode returns" in result["per_episode"][0]["scope"]

