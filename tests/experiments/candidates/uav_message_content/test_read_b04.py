import hashlib
from pathlib import Path

import numpy as np
import pytest

from experiments.candidates.uav_message_content.read_b04 import (
    MASTERS, conditional_contrast, error_summary, merge_error_summaries,
    ordinary_by_steps, read_trace, validate_exposure,
)


def test_ordinary_reference_clips_known_first_action_before_reversing():
    result = ordinary_by_steps([.99, .01, .5], [1, -1, 1], [-1, 1, -1], 3)
    np.testing.assert_allclose(result, [.94, .06, .2], rtol=0, atol=1e-14)
    np.testing.assert_array_equal(ordinary_by_steps([.99, .01, .5], [1, -1, 1], [0, 0, 0], 1),
                                  [1., 0., .8])


def test_contrast_keeps_continuations_as_units_and_all_adverse_worlds():
    first, second = {}, {}
    for master, value in zip(MASTERS, (-1., 0., 2.)):
        first[master] = [dict(episode=e, J=value + e - 15.5) for e in range(32)]
        second[master] = [dict(episode=e, J=0.) for e in range(32)]
    reading = conditional_contrast(first, second, "J")
    assert reading["per_continuation_mean"] == [-1., 0., 2.]
    assert reading["mean"] == pytest.approx(1 / 3)
    half_width = 4.302652729911275 * np.std([-1, 0, 2], ddof=1) / np.sqrt(3)
    assert reading["descriptive_t95_df2"] == pytest.approx([1 / 3 - half_width, 1 / 3 + half_width])
    assert len(reading["per_world_differences"][str(MASTERS[0])]) == 32
    assert reading["adverse_worlds"][str(MASTERS[0])] == list(range(17))
    first[MASTERS[0]].reverse()
    with pytest.raises(AssertionError):
        conditional_contrast(first, second, "J")


def test_forecast_errors_separate_horizontal_height_and_empty_weights():
    prediction = np.array([[.03, .04, .1], [0, 0, -.2]])
    target = np.zeros_like(prediction)
    result = error_summary(prediction, target, [1, 3])
    assert result["count"] == 4
    assert result["horizontal_mean_m"] == 12.5
    assert result["horizontal_rms_m"] == 25.
    assert result["height_mae_m"] == 17.5
    assert result["height_rms_m"] == pytest.approx(np.sqrt(325))
    empty = error_summary(prediction, target, [0, 0])
    assert empty == dict(count=0, horizontal_mean_m=None, horizontal_rms_m=None,
                         height_mae_m=None, height_rms_m=None)


def synthetic_trace(tmp_path, arm):
    augmented = arm != "B0"
    rng = np.random.default_rng(9001)
    good = bool(rng.integers(2))
    shape = (256, 5, 186 if augmented else 171)
    arrays = dict(actor_input=np.zeros(shape, dtype=np.float32),
                  critic_input=np.zeros((256, 526 if augmented else 451), dtype=np.float32),
                  pre_tanh_motion=np.zeros((256, 5, 3), dtype=np.float32),
                  action=np.zeros((256, 5, 3), dtype=np.float32),
                  central_motion=np.full((256, 5, 3), .1, dtype=np.float32),
                  shadow_central_motion=np.full((256, 5, 3), .11, dtype=np.float32),
                  position=np.full((257, 5, 3), .5, dtype=np.float32),
                  initial_state=np.zeros(116, dtype=np.float32),
                  user_positions=np.full((50, 2), 100., dtype=np.float64),
                  connected_users=np.zeros((256, 50), dtype=np.uint8),
                  packet=np.zeros((256, 10 if augmented else 7), dtype=np.float32),
                  ordinary_endpoint=np.zeros((256, 3), dtype=np.float32),
                  sampled_cv_endpoint=np.zeros((256, 3), dtype=np.float32),
                  forecast_endpoint=np.zeros((256, 3), dtype=np.float32),
                  records=np.zeros((256, 5, 5, 13 if augmented else 10), dtype=np.float32),
                  cache_age=np.full((256, 5, 5), -1, dtype=np.int64),
                  cache_remaining_lead=np.zeros((256, 5, 5), dtype=np.int64),
                  pending_after_send=np.zeros((256, 5), dtype=bool))
    arrays.update({key: np.zeros(256, dtype=np.int64) for key in ("sender", "due", "good", "deliveries")})
    arrays.update(reward_physical=np.full(256, .13), reward_net=np.full(256, .129),
                  served_users=np.full(256, 5), Q=np.full(256, .2))
    arrays["connected_users"][:, :5] = 1
    arrays["initial_state"][:15] = np.tile([500., 500., 100.], 5)
    arrays["initial_state"][15:115] = 100.
    pending = np.zeros(5, dtype=bool)
    sent_at = np.full((5, 5), -1, dtype=np.int64)
    record = np.zeros((5, 5, 10), dtype=np.float32)
    forecast = np.zeros((5, 5, 3), dtype=np.float32)
    for t in range(256):
        arrivals = np.flatnonzero(arrays["due"][:t] == t)
        for sent in arrivals:
            sender = sent % 5
            peers = np.arange(5) != sender
            record[peers, sender, :7] = arrays["packet"][sent, :7]
            record[peers, sender, 7:9] = [1, sent / 256]
            if augmented:
                forecast[peers, sender] = arrays["packet"][sent, 7:]
            sent_at[peers, sender] = sent
            pending[sender] = False
        valid = sent_at >= 0
        record[..., 9] = np.where(valid, (t - sent_at) / 256, 0)
        arrays["cache_age"][t] = np.where(valid, t - sent_at, -1)
        arrays["cache_remaining_lead"][t] = np.where(valid, np.minimum(sent_at + 10, 256) - t, 0)
        arrays["records"][t, ..., :10] = record
        obs = arrays["actor_input"][t]
        obs[:, :3] = arrays["position"][t]
        obs[:, 103] = t / 256
        if t:
            obs[:, 104:107] = arrays["action"][t - 1]
        obs[:, 108:110] = np.eye(2)[int(good)]
        obs[:, 110:115] = np.eye(5)
        obs[:, 115:120] = np.eye(5)[t % 5]
        obs[:, 120] = pending
        obs[:, 121:171] = record.reshape(5, 50)
        if augmented:
            obs[:, 171:] = forecast.reshape(5, 15)
            arrays["records"][t, ..., 10:] = forecast
        critic = arrays["critic_input"][t]
        critic[:15] = arrays["position"][t].ravel()
        critic[15:115] = .1
        critic[115] = t / 256
        critic[116:136] = obs[:, 104:108].ravel()
        critic[136:451] = obs[:, 108:171].ravel()
        if augmented:
            critic[451:] = obs[:, 171:].ravel()
        arrays["sender"][t] = sender = t % 5
        arrays["due"][t] = t + (1 if good else 5)
        arrays["good"][t] = int(good)
        arrays["deliveries"][t] = len(arrivals)
        arrays["packet"][t, :3] = .5
        if arm in ("O", "F"):
            k = min(10, 256 - t)
            ordinary = ordinary_by_steps([.5] * 3, np.zeros(3), [.1] * 3, k)
            arrays["ordinary_endpoint"][t] = ordinary
            arrays["sampled_cv_endpoint"][t] = .5
            actual = ordinary.copy()
            if arm == "F" and k > 1:
                actual[:2] += .01
            arrays["forecast_endpoint"][t] = actual
            arrays["packet"][t, 7:] = actual
        pending[sender] = True
        arrays["pending_after_send"][t] = pending
        if rng.random() >= .95:
            good = not good
    path = tmp_path / f"{arm}.npz"
    np.savez_compressed(path, **arrays)
    row = dict(raw=str(path), raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               channel_seed=9001, delivered_packets=int(arrays["deliveries"].sum()),
               pending_at_end=int(pending.sum()),
               initial_scene_sha256=hashlib.sha256(arrays["actor_input"][0, :, :104].tobytes()
                                                  + arrays["initial_state"].tobytes()).hexdigest(),
               channel_sequence_sha256=hashlib.sha256(bytes(arrays["good"].tolist())).hexdigest())
    return arrays, row


@pytest.mark.parametrize("arm", ["B0", "G", "O", "F"])
def test_complete_array_reader_reconstructs_channel_and_dated_endpoint(tmp_path, arm):
    arrays, row = synthetic_trace(tmp_path, arm)
    reading = read_trace(row, arm)
    assert reading["delivered"] + reading["censored"] == 256
    assert reading["levels"]["served_users_per_tick"] == 5
    assert reading["connected_bits_bytes"] == 256 * 50
    assert sum(reading["cache_age_counts"]) == reading["cache_uses"]
    if arm in ("O", "F"):
        assert reading["forecast_error"]["actual"]["delivered_sends"]["count"] == reading["delivered"]
        assert reading["forecast_error"]["ordinary"]["cache_uses"]["count"] == reading["cache_uses"]
        assert reading["response_rms"] == pytest.approx(.01, abs=1e-8)
    arrays["connected_users"][-1, 49] = 1
    np.savez_compressed(row["raw"], **arrays)
    row["raw_sha256"] = hashlib.sha256(Path(row["raw"]).read_bytes()).hexdigest()
    with pytest.raises(AssertionError):
        read_trace(row, arm)


@pytest.mark.parametrize("field", ["ordinary_endpoint", "cache_remaining_lead", "records", "due", "position"])
def test_reader_rejects_corrupted_forecast_or_clock_with_updated_file_hash(tmp_path, field):
    arrays, row = synthetic_trace(tmp_path, "F")
    arrays[field].reshape(len(arrays[field]), -1)[-1, 0] += 1
    np.savez_compressed(row["raw"], **arrays)
    row["raw_sha256"] = hashlib.sha256(Path(row["raw"]).read_bytes()).hexdigest()
    with pytest.raises(AssertionError):
        read_trace(row, "F")


def test_error_pooling_weights_actual_uses_and_handles_empty_group():
    first = error_summary(np.array([[.03, .04, .1]]), np.zeros((1, 3)), [1])
    second = error_summary(np.array([[0., 0., -.2]]), np.zeros((1, 3)), [3])
    empty = error_summary(np.zeros((1, 3)), np.zeros((1, 3)), [0])
    merged = merge_error_summaries([first, empty, second])
    assert merged["count"] == 4 and merged["horizontal_mean_m"] == 12.5
    assert merged["horizontal_rms_m"] == 25
    assert merged["height_rms_m"] == pytest.approx(np.sqrt(325))


def exposure_cell(master, arm):
    train = 0 if arm == "B0" else 512
    steps = (train + 32) * 256
    labels = 254 * train if arm == "F" else 0
    counts = dict(constructors=1, explicit_resets=train + 32,
                  fit_started=int(arm != "B0"), train_episodes=train,
                  final_eval_episodes=32, train_team_steps=train * 256,
                  final_eval_team_steps=8192, team_steps=steps,
                  native_step_calls=steps, motion_samples=steps * 5,
                  broadcasts=steps, attempts=steps, rollouts=train // 2,
                  optimizer_steps=train * 2, replayed_actor_rows=train * 5120,
                  predictor_forwards=steps if arm == "F" else 0,
                  predictor_updates=train * 2 if arm == "F" else 0,
                  eligible_labels=labels, predictor_rows=4 * labels,
                  evaluation_optimizer_steps=0,
                  diagnostic_forward_calls=8192 if arm in ("O", "F") else 0,
                  delivered_packets=254 * (train + 32), censored_packets=2 * (train + 32),
                  behavior_actor_forward_calls=steps, behavior_actor_forward_rows=5 * steps,
                  behavior_critic_forward_calls=steps, behavior_critic_forward_rows=steps,
                  ppo_actor_forward_calls=2 * train, ppo_actor_forward_rows=5120 * train,
                  ppo_critic_forward_calls=2 * train, ppo_critic_forward_rows=1024 * train)
    return dict(master=master, arm=arm, status="COMPLETE", counts=counts)


@pytest.mark.parametrize("key", ["team_steps", "predictor_updates", "predictor_rows", "evaluation_optimizer_steps",
                                 "ppo_actor_forward_rows", "final_eval_episodes"])
def test_exposure_includes_b0_extra_predictor_work_and_zero_evaluation_updates(key):
    cells = [exposure_cell(master, arm) for master in MASTERS for arm in ("G", "O", "F")]
    b0 = exposure_cell(19451, "B0")
    actual = {name: sum(cell["counts"][name] for cell in [*cells, b0]) for name in b0["counts"]}
    validate_exposure(cells, b0, actual)
    actual[key] += 1
    with pytest.raises(AssertionError):
        validate_exposure(cells, b0, actual)
