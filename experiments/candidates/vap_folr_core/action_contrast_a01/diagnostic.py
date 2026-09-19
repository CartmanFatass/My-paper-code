"""Serial replay and selected one-step action contrasts for frozen A01 panels."""

import copy
import hashlib

import numpy as np
import torch


PANEL_SEED = 1783101
PANEL_EPISODES = 128
HORIZON = 20
AGENTS = 5
ACTIONS = 5
NONFLAT_TOLERANCE = 1e-12

INPUTS = {
    "DETACHED": {
        "tag": "predictive_aux_a01_detached_783101",
        "checkpoint_sha256": "6c59f47535e6887c58c5bd4484044077e6acf1cde7b60181baf8334a136aed6e",
        "panel_sha256": "6e140a6c23feb25481d3fb5705a26bed1acbbd5de85428408759b15f48cc7e7d",
        "selected_rows": 718,
        "active_action_checks": 7281,
    },
    "COUPLED": {
        "tag": "predictive_aux_a01_coupled_783101",
        "checkpoint_sha256": "b8ccb717c22ce11254436d8873e26be25d14882b9a0f82c4179ab47dce28c7b0",
        "panel_sha256": "8a5f7b110fc027a86feef17810846d43d590909883be924ccc44d07556fd683f",
        "selected_rows": 180,
        "active_action_checks": 7591,
    },
}

OBSERVATION_KEYS = (
    "entities",
    "obs_mask",
    "entity_mask",
    "birth",
    "continuation",
    "event",
    "previous_action",
    "departure",
    "visible",
    "seen",
    "age",
)


class DiagnosticMismatch(RuntimeError):
    """A frozen input failed replay or identity validation."""


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor_state_sha256(actor):
    digest = hashlib.sha256()
    for name, value in sorted(actor.state_dict().items()):
        row = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(str(row.dtype).encode("ascii") + b"\0")
        digest.update(np.asarray(row.shape, dtype=np.int64).tobytes())
        digest.update(row.numpy().tobytes())
    return digest.hexdigest()


def _exact_array(label, actual, expected):
    actual = np.asarray(actual)
    expected = np.asarray(expected)
    if (
        actual.shape != expected.shape
        or actual.dtype != expected.dtype
        or not np.array_equal(actual, expected)
    ):
        raise DiagnosticMismatch(f"{label} does not match retained panel bytes")


def selected_observers(observation):
    """Return the fixed seen/hidden active axis-distance-two observer mask."""
    scaled = np.asarray(observation["entities"], dtype=np.float64)[:, 2:4] * 7
    positions = np.rint(scaled)
    rounding_error = float(np.max(np.abs(scaled - positions)))
    if rounding_error > 1e-6:
        raise DiagnosticMismatch(
            f"native coordinate reconstruction error {rounding_error} exceeds tolerance"
        )
    difference = np.abs(positions[:, None, :] - positions[None, :, :])
    axis_distance_two = (difference.sum(axis=-1) == 2) & (difference.max(axis=-1) == 2)
    active = ~np.asarray(observation["entity_mask"], dtype=bool)
    eligible_subject = (
        active[:, None]
        & active[None, :]
        & np.asarray(observation["seen"], dtype=bool)
        & ~np.asarray(observation["visible"], dtype=bool)
        & axis_distance_two
    )
    return eligible_subject.any(axis=1)


def _rng_state_equal(first, second):
    return (
        first[0] == second[0]
        and np.array_equal(first[1], second[1])
        and first[2:] == second[2:]
    )


def nonfactual_action_values(env, recorded_actions, focal_agent, factual_action, activity):
    """Evaluate four deep-copied native branches without moving factual global RNG."""
    rewards = [None] * ACTIONS
    collision_deltas = [None] * ACTIONS
    collision_before = int(env.collision_times)
    for action in range(ACTIONS):
        if action == factual_action:
            continue
        rng_before = copy.deepcopy(np.random.get_state())
        branch = copy.deepcopy(env)
        branch_actions = np.asarray(recorded_actions, dtype=np.int64).copy()
        branch_actions[focal_agent] = action
        activity["counterfactual_transition_calls"] += 1
        try:
            reward, _, _ = branch.step(branch_actions)
        finally:
            np.random.set_state(rng_before)
        if not _rng_state_equal(rng_before, np.random.get_state()):
            raise DiagnosticMismatch("counterfactual branch did not restore global NumPy RNG")
        rewards[action] = float(reward)
        collision_deltas[action] = int(branch.collision_times) - collision_before
    return rewards, collision_deltas


def _serial_actor_call(actor, observation, incoming_hidden, activity, kind):
    batch = {
        key: torch.as_tensor(value)[None, None]
        for key, value in observation.items()
    }
    with torch.no_grad():
        q_values, states = actor(batch, incoming_hidden)
    activity["actor_forward_calls"] += 1
    activity[f"{kind}_forward_calls"] += 1
    actions = q_values[0, 0].argmax(dim=-1).cpu().numpy()
    return actions, states[:, -1]


def _post_event_window(events, time_index):
    first = max(1, time_index - 2)
    return any(bool(events[index]) for index in range(first, time_index + 1))


def _validate_panel_shapes(panel, expected_returns):
    expected = {
        "entities": (PANEL_EPISODES, 21, AGENTS, 4),
        "actions": (PANEL_EPISODES, HORIZON, AGENTS),
        "reward": (PANEL_EPISODES, HORIZON),
        "terminated": (PANEL_EPISODES, HORIZON),
    }
    for key in OBSERVATION_KEYS:
        if key not in panel:
            raise DiagnosticMismatch(f"retained panel is missing observation field {key}")
    for key, shape in expected.items():
        if key not in panel or tuple(panel[key].shape) != shape:
            raise DiagnosticMismatch(f"retained panel field {key} has wrong shape")
    if len(expected_returns) != PANEL_EPISODES:
        raise DiagnosticMismatch("retained summary does not have 128 final returns")


def replay_panel(env, actor, panel, expected_returns, arm, emit_row, activity):
    """Replay one frozen panel and emit only prespecified geometry-row contrasts."""
    _validate_panel_shapes(panel, expected_returns)
    for episode_index in range(PANEL_EPISODES):
        env.reset()
        previous_actions = np.zeros(AGENTS, dtype=np.int64)
        full_hidden = None
        native_rewards = []
        for time_index in range(21):
            observation = env.observation(previous_actions)
            for key in OBSERVATION_KEYS:
                _exact_array(
                    f"episode {episode_index} boundary {time_index} {key}",
                    observation[key],
                    panel[key][episode_index, time_index],
                )
            activity["observation_boundaries_verified"] += 1

            full_actions, full_hidden = _serial_actor_call(
                actor, observation, full_hidden, activity, "full"
            )
            reset_actions, _ = _serial_actor_call(
                actor, observation, None, activity, "reset"
            )
            if time_index == HORIZON:
                continue

            recorded_actions = np.asarray(panel["actions"][episode_index, time_index])
            active = ~np.asarray(observation["entity_mask"], dtype=bool)
            activity["active_action_checks"] += int(active.sum())
            if not np.array_equal(full_actions[active], recorded_actions[active]):
                mismatches = np.flatnonzero(active & (full_actions != recorded_actions)).tolist()
                raise DiagnosticMismatch(
                    f"{arm} full greedy action mismatch at episode {episode_index}, "
                    f"time {time_index}, agents {mismatches}"
                )

            selected = selected_observers(observation)
            pending = []
            for focal_agent in np.flatnonzero(selected):
                factual_action = int(recorded_actions[focal_agent])
                activity["selected_rows"] += 1
                rewards, collision_deltas = nonfactual_action_values(
                    env, recorded_actions, int(focal_agent), factual_action, activity
                )
                pending.append(
                    (
                        int(focal_agent),
                        factual_action,
                        int(full_actions[focal_agent]),
                        int(reset_actions[focal_agent]),
                        rewards,
                        collision_deltas,
                    )
                )

            collision_before = int(env.collision_times)
            activity["factual_transition_calls"] += 1
            factual_reward, done, _ = env.step(recorded_actions)
            factual_reward = float(factual_reward)
            factual_collision_delta = int(env.collision_times) - collision_before
            native_rewards.append(factual_reward)
            _exact_array(
                f"episode {episode_index} transition {time_index} reward",
                np.asarray(factual_reward, dtype=np.float32),
                panel["reward"][episode_index, time_index],
            )
            _exact_array(
                f"episode {episode_index} transition {time_index} termination",
                np.asarray(float(done), dtype=np.float32),
                panel["terminated"][episode_index, time_index],
            )
            activity["factual_reward_checks"] += 1

            for (
                focal_agent,
                factual_action,
                full_action,
                reset_action,
                rewards,
                collision_deltas,
            ) in pending:
                rewards[factual_action] = factual_reward
                collision_deltas[factual_action] = factual_collision_delta
                if any(value is None or not np.isfinite(value) for value in rewards):
                    raise DiagnosticMismatch("five-action native reward vector is incomplete")
                if any(value is None for value in collision_deltas):
                    raise DiagnosticMismatch("five-action collision delta vector is incomplete")
                oracle_reward = max(rewards)
                full_regret = oracle_reward - rewards[full_action]
                reset_regret = oracle_reward - rewards[reset_action]
                reward_range = max(rewards) - min(rewards)
                collision_sensitive = max(collision_deltas) != min(collision_deltas)
                in_post_event_window = _post_event_window(
                    panel["event"][episode_index], time_index
                )
                row = {
                    "arm": arm,
                    "episode": episode_index,
                    "time": time_index,
                    "agent": focal_agent,
                    "native_rewards_by_action": rewards,
                    "native_collision_deltas_by_action": collision_deltas,
                    "factual_action": factual_action,
                    "full_action": full_action,
                    "reset_action": reset_action,
                    "factual_full_regret": full_regret,
                    "reset_regret": reset_regret,
                    "full_minus_reset_immediate_reward": (
                        rewards[full_action] - rewards[reset_action]
                    ),
                    "action_changed": full_action != reset_action,
                    "native_reward_range": reward_range,
                    "nonflat_action_contrast": reward_range > NONFLAT_TOLERANCE,
                    "collision_sensitive": collision_sensitive,
                    "event_at_boundary": bool(observation["event"]),
                    "in_post_event_window": in_post_event_window,
                    "public_event_stratum": (
                        "POST_EVENT_WINDOW" if in_post_event_window else "OUTSIDE_POST_EVENT_WINDOW"
                    ),
                }
                emit_row(row)
                activity["rows_written"] += 1
            previous_actions = recorded_actions.copy()

        replay_return = float(sum(native_rewards))
        if replay_return != float(expected_returns[episode_index]):
            raise DiagnosticMismatch(
                f"{arm} native float64 return mismatch in episode {episode_index}"
            )
        activity["native_return_checks"] += 1
        activity["replayed_episodes"] += 1


def _mean(rows, key):
    return sum(float(row[key]) for row in rows) / len(rows) if rows else None


def _regret_reading(rows):
    if not rows:
        return None
    return {
        "count": len(rows),
        "mean_factual_full_regret": _mean(rows, "factual_full_regret"),
        "mean_reset_regret": _mean(rows, "reset_regret"),
        "factual_full_positive_regret_count": sum(
            row["factual_full_regret"] > NONFLAT_TOLERANCE for row in rows
        ),
        "reset_positive_regret_count": sum(
            row["reset_regret"] > NONFLAT_TOLERANCE for row in rows
        ),
    }


def summarize_rows(rows):
    """Summarize selected local deviations without treating them as episode returns."""
    collision_rows = [row for row in rows if row["collision_sensitive"]]
    per_episode = []
    for episode_index in range(PANEL_EPISODES):
        episode_rows = [row for row in rows if row["episode"] == episode_index]
        count = len(episode_rows)

        def local_sum(key):
            return sum(float(row[key]) for row in episode_rows) if count else None

        per_episode.append(
            {
                "episode": episode_index,
                "selected_row_count": count,
                "action_changed_count": sum(row["action_changed"] for row in episode_rows),
                "nonflat_action_contrast_count": sum(
                    row["nonflat_action_contrast"] for row in episode_rows
                ),
                "collision_sensitive_count": sum(
                    row["collision_sensitive"] for row in episode_rows
                ),
                "nonadditive_local_factual_full_regret_sum": local_sum(
                    "factual_full_regret"
                ),
                "nonadditive_local_reset_regret_sum": local_sum("reset_regret"),
                "nonadditive_local_full_minus_reset_reward_sum": local_sum(
                    "full_minus_reset_immediate_reward"
                ),
                "mean_factual_full_regret": _mean(
                    episode_rows, "factual_full_regret"
                ),
                "mean_reset_regret": _mean(episode_rows, "reset_regret"),
                "scope": (
                    "Overlapping one-step local deviations on factual later states; "
                    "sums are not potential episode returns."
                ),
            }
        )
    return {
        "selected_row_count": len(rows),
        "action_changed_count": sum(row["action_changed"] for row in rows),
        "changed_action_fraction": (
            sum(row["action_changed"] for row in rows) / len(rows) if rows else None
        ),
        "nonflat_tolerance": NONFLAT_TOLERANCE,
        "nonflat_action_contrast_count": sum(
            row["nonflat_action_contrast"] for row in rows
        ),
        "mean_factual_full_regret": _mean(rows, "factual_full_regret"),
        "mean_reset_regret": _mean(rows, "reset_regret"),
        "factual_full_positive_regret_count": sum(
            row["factual_full_regret"] > NONFLAT_TOLERANCE for row in rows
        ),
        "reset_positive_regret_count": sum(
            row["reset_regret"] > NONFLAT_TOLERANCE for row in rows
        ),
        "mean_full_minus_reset_immediate_reward": _mean(
            rows, "full_minus_reset_immediate_reward"
        ),
        "all_selected_regret": _regret_reading(rows),
        "collision_sensitive_count": len(collision_rows),
        "collision_sensitive_regret": _regret_reading(collision_rows),
        "per_episode": per_episode,
        "scope": (
            "Selected actual one-step factual regret is primary; zero-incoming-hidden reset is "
            "secondary. No value is assigned outside selected rows, and per-episode sums are "
            "nonadditive overlapping local deviations."
        ),
    }

