"""Synthetic small-horizon checks; no native environment or canonical assets."""
import copy

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import make_student
from experiments.candidates.uav_fleet_adaptation.b04_native_development.learning import (
    fresh_critic, make_optimizers, update_group,
)


@pytest.fixture(autouse=True)
def one_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def fixture_group(actor, critic, horizon=12):
    rng = np.random.default_rng(91)
    clocks = horizon // 4
    episodes = []
    for episode in range(2):
        x = (rng.normal(size=(clocks, 5, 114)) * 8).astype(np.float32)
        # The inherited feature is fallback=1 (ineligible); neither state masks rows.
        x[..., -1] = (np.arange(clocks * 5).reshape(clocks, 5) + episode) % 2
        cx = rng.normal(size=(clocks, 136)).astype(np.float32)
        with torch.no_grad():
            logits = np.stack([actor(torch.from_numpy(row)[None])[0].numpy()
                               for row in x.reshape(-1, 114)]).reshape(clocks, 5, 27)
            values = critic(torch.from_numpy(cx)).numpy().copy()
        z = logits.astype(np.float64)
        weights = np.exp(z - z.max(axis=-1, keepdims=True))
        p = weights / weights.sum(axis=-1, keepdims=True, dtype=np.float64)
        actions = ((np.arange(clocks * 5) + episode * clocks * 5) % 27).reshape(clocks, 5).astype(np.int64)
        chosen = np.take_along_axis(p, actions[..., None], axis=-1)[..., 0]
        episodes.append(dict(features=x, logits=logits.copy(), probabilities=p,
                             action_index=actions, logp=np.log(chosen), critic_features=cx,
                             values=values, macro_rewards=(np.arange(clocks) + 1 + 10 * episode).astype(np.float64)))
    return episodes


def reference_targets(episodes, horizon):
    # Independently enumerate each suffix, resetting at the episode boundary.
    return np.array([[sum(ep["macro_rewards"][t:].astype(np.float32)) / horizon
                      for t in range(horizon // 4)] for ep in episodes], dtype=np.float32)


def test_fresh_critic_rng_architecture_and_adam():
    before = torch.random.get_rng_state().clone()
    critic = fresh_critic(81)
    assert torch.equal(before, torch.random.get_rng_state())
    other = fresh_critic(81)
    assert all(torch.equal(x, y) for x, y in zip(critic.parameters(), other.parameters()))
    assert sum(p.numel() for p in critic.parameters()) == 34177
    assert [type(layer).__name__ for layer in critic.network] == ["Linear", "Tanh", "Linear", "Tanh", "Linear"]
    actor = make_student(72)
    actor_optimizer, critic_optimizer = make_optimizers(actor, critic)
    for optimizer in (actor_optimizer, critic_optimizer):
        assert optimizer.state == {}
        for key, value in dict(lr=3e-4, betas=(.9, .999), eps=1e-8, weight_decay=0,
                               amsgrad=False, foreach=False, fused=False).items():
            assert optimizer.defaults[key] == value
    assert actor_optimizer is not critic_optimizer


def test_four_epochs_individual_loss_fixed_targets_counts_and_continuity():
    actor, critic = make_student(72), fresh_critic(81)
    aopt, copt = make_optimizers(actor, critic)
    episodes = fixture_group(actor, critic)
    original = copy.deepcopy(episodes)
    targets = reference_targets(episodes, 12)
    saved_values = np.stack([ep["values"] for ep in episodes])
    raw = targets - saved_values
    advantage = (raw - raw.mean()) / (raw.std(ddof=0) + np.float32(1e-8))
    assert targets[0, -1] == .25
    assert targets[1, 0] == 3.0  # No suffix crosses the reset.
    old_p = np.stack([ep["probabilities"] for ep in episodes])
    actions = np.stack([ep["action_index"] for ep in episodes])
    assert set(actions.ravel()) == set(range(27))
    assert set(np.stack([ep["features"][..., -1] for ep in episodes]).ravel()) == {0., 1.}
    old_chosen = np.take_along_axis(old_p, actions[..., None], axis=-1)[..., 0]
    replayed, predicted, step_order = [], [], []
    hook = actor.register_forward_hook(lambda module, inputs, output: replayed.append(
        (tuple(inputs[0].shape), output.detach().numpy().copy())))
    critic_hook = critic.register_forward_hook(lambda module, inputs, output: predicted.append(output.detach().numpy().copy()))
    real_a_step, real_c_step = aopt.step, copt.step
    aopt.step = lambda: (step_order.append("actor"), real_a_step())[1]
    copt.step = lambda: (step_order.append("critic"), real_c_step())[1]
    counts = dict(actor_optimizer_steps=11, critic_optimizer_steps=17,
                  actor_replay_rows=23, critic_replay_rows=29, density_identity_rows=31,
                  unrelated=101)
    result = update_group(actor, critic, aopt, copt, episodes, counts, horizon=12)
    hook.remove()
    critic_hook.remove()
    assert counts == dict(actor_optimizer_steps=15, critic_optimizer_steps=21,
                          actor_replay_rows=143, critic_replay_rows=53,
                          density_identity_rows=61, unrelated=101)
    assert len(replayed) == 120 and all(shape == (1, 114) for shape, _ in replayed)
    assert len(predicted) == 4
    assert step_order == ["actor", "critic"] * 4
    assert result["initial_identity"]["logits_exact"]
    assert result["initial_identity"]["max_probability_abs"] <= 5e-14
    assert result["initial_identity"]["max_chosen_logp_abs"] <= 1e-10
    assert result["initial_identity"]["max_ratio_from_one"] <= 1e-10
    assert result["target_summary"]["dtype"] == "torch.float32"
    assert result["target_summary"]["mean"] == pytest.approx(float(targets.mean()), abs=1e-6)
    assert result["advantage_summary"]["std"] == pytest.approx(1, abs=1e-6)
    joint_differences = []
    for epoch, record in enumerate(result["epochs"]):
        z = np.concatenate([output for _, output in replayed[epoch * 30:(epoch + 1) * 30]]).astype(np.float64).reshape(2, 3, 5, 27)
        p = np.exp(z - z.max(axis=-1, keepdims=True))
        p /= p.sum(axis=-1, keepdims=True)
        ratio = np.take_along_axis(p, actions[..., None], axis=-1)[..., 0] / old_chosen
        expected = -np.minimum(ratio * advantage[..., None], np.clip(ratio, .8, 1.2) * advantage[..., None]).sum(axis=-1).mean()
        joint_ratio = ratio.prod(axis=-1)
        joint = -np.minimum(joint_ratio * advantage, np.clip(joint_ratio, .8, 1.2) * advantage).mean()
        joint_differences.append(abs(expected - joint))
        assert record["actor_loss"] == pytest.approx(expected, abs=2e-6)
        assert record["critic_loss"] == pytest.approx(.5 * np.square(predicted[epoch] - targets).mean(), abs=1e-6)
        assert record["clip_fraction"] == np.mean((ratio < .8) | (ratio > 1.2))
        assert record["actor_clipped_grad_norm"] <= .500001
        assert record["critic_clipped_grad_norm"] <= .500001
        assert record["actor_optimizer_step_values"] == [epoch + 1] * len(list(actor.parameters()))
    assert max(joint_differences[1:]) > 1e-3
    assert any(row["clip_fraction"] > 0 for row in result["epochs"][1:])
    assert result["epochs"][-1]["actor_movement_l2"] > 0
    assert result["epochs"][-1]["critic_movement_l2"] > 0
    for ep, old in zip(episodes, original):
        for key in ep:
            np.testing.assert_array_equal(ep[key], old[key])
    # The same Adam objects/moments continue into a newly collected group.
    old_moment = aopt.state[next(actor.parameters())]["exp_avg"].clone()
    result2 = update_group(actor, critic, aopt, copt, fixture_group(actor, critic), counts, horizon=12)
    assert result2["actor_optimizer_step_values"] == [8] * len(list(actor.parameters()))
    assert result2["critic_optimizer_step_values"] == [8] * len(list(critic.parameters()))
    assert not torch.equal(old_moment, aopt.state[next(actor.parameters())]["exp_avg"])
    assert counts["actor_optimizer_steps"] == 19 and counts["critic_optimizer_steps"] == 25


def test_first_gradient_matches_independent_log_density_score():
    actor, critic = make_student(72), fresh_critic(81)
    episodes = fixture_group(actor, critic, horizon=8)
    reference = copy.deepcopy(actor)
    x = torch.tensor(np.stack([ep["features"] for ep in episodes]))
    logits = torch.stack([reference(row[None])[0] for row in x.reshape(-1, 114)]).reshape(2, 2, 5, 27).double()
    actions = torch.tensor(np.stack([ep["action_index"] for ep in episodes]))
    old_lp = torch.tensor(np.stack([ep["logp"] for ep in episodes]))
    new_lp = torch.log_softmax(logits, dim=-1).gather(-1, actions[..., None]).squeeze(-1)
    target = torch.tensor(reference_targets(episodes, 8))
    raw = target - torch.tensor(np.stack([ep["values"] for ep in episodes]))
    advantage = (raw - raw.mean()) / (raw.std(unbiased=False) + 1e-8)
    # At initial identity the independent log-density score has no clipping.
    loss = -((new_lp - old_lp).exp() * advantage[..., None]).sum(-1).mean()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(reference.parameters(), .5, foreach=False)
    aopt, copt = make_optimizers(actor, critic)
    actual_gradients = []
    original_step = aopt.step
    def capture_step():
        if not actual_gradients:
            actual_gradients.extend(p.grad.clone() for p in actor.parameters())
        return original_step()
    aopt.step = capture_step
    update_group(actor, critic, aopt, copt, episodes, {}, horizon=8)
    for observed, p in zip(actual_gradients, reference.parameters()):
        assert observed.dtype == torch.float32
        torch.testing.assert_close(observed, p.grad, rtol=2e-5, atol=2e-7)


@pytest.mark.parametrize("corruption", ["logit", "probability", "logp", "dtype", "shape", "action", "nan"])
def test_invalid_rollout_or_initial_density_never_updates(corruption):
    actor, critic = make_student(72), fresh_critic(81)
    aopt, copt = make_optimizers(actor, critic)
    episodes = fixture_group(actor, critic, horizon=8)
    ep = episodes[0]
    if corruption == "logit":
        ep["logits"][0, 0, 0] = np.nextafter(ep["logits"][0, 0, 0], np.float32(np.inf))
    elif corruption == "probability":
        ep["probabilities"][0, 0, 25] += 1e-12
        ep["probabilities"][0, 0, 26] -= 1e-12
    elif corruption == "logp":
        ep["logp"][0, 0] += 1e-7
    elif corruption == "dtype":
        ep["probabilities"] = ep["probabilities"].astype(np.float32)
    elif corruption == "shape":
        ep["features"] = ep["features"][:1]
    elif corruption == "action":
        ep["action_index"][0, 0] = 27
    else:
        ep["macro_rewards"][0] = np.nan
    counts = {}
    with pytest.raises((ValueError, FloatingPointError)):
        update_group(actor, critic, aopt, copt, episodes, counts, horizon=8)
    assert not aopt.state and not copt.state
    assert counts.get("actor_optimizer_steps", 0) == counts.get("critic_optimizer_steps", 0) == 0
    if corruption in ("logit", "probability"):
        assert counts["actor_replay_rows"] == counts["density_identity_rows"] == 20
        assert counts.get("critic_replay_rows", 0) == 0


def test_nonfinite_gradient_rejected_with_paid_replay_counts():
    actor, critic = make_student(72), fresh_critic(81)
    aopt, copt = make_optimizers(actor, critic)
    episodes = fixture_group(actor, critic, horizon=8)
    hook = next(actor.parameters()).register_hook(lambda gradient: gradient * float("inf"))
    counts = {}
    with pytest.raises(RuntimeError, match="non-finite"):
        update_group(actor, critic, aopt, copt, episodes, counts, horizon=8)
    hook.remove()
    assert counts == dict(actor_replay_rows=20, density_identity_rows=20)
    assert not aopt.state and not copt.state


def test_saved_tensors_are_detached_and_fixed():
    actor, critic = make_student(72), fresh_critic(81)
    aopt, copt = make_optimizers(actor, critic)
    episodes = fixture_group(actor, critic, horizon=8)
    differentiable = []
    for episode in episodes:
        for key in episode:
            episode[key] = torch.tensor(episode[key])
            if episode[key].is_floating_point():
                episode[key].requires_grad_(True)
                differentiable.append(episode[key])
    update_group(actor, critic, aopt, copt, episodes, {}, horizon=8)
    assert all(value.grad is None for value in differentiable)


def test_rewards_round_to_fp32_before_suffix_accumulation():
    actor, critic = make_student(72), fresh_critic(81)
    aopt, copt = make_optimizers(actor, critic)
    episodes = fixture_group(actor, critic, horizon=8)
    episodes[0]["macro_rewards"] = np.array([1 + 2**-24, 2**-24], dtype=np.float64)
    episodes[1]["macro_rewards"] = np.zeros(2, dtype=np.float64)
    result = update_group(actor, critic, aopt, copt, episodes, {}, horizon=8)
    assert result["target_summary"]["max"] == .125
    # FP64 accumulation followed by FP32 casting would instead yield this value.
    wrong = np.float32(episodes[0]["macro_rewards"].sum() / 8)
    assert wrong > result["target_summary"]["max"]


@pytest.mark.parametrize("case", ["single", "triple", "partial", "horizon", "count"])
def test_group_contract_rejection_before_replay(case):
    actor, critic = make_student(72), fresh_critic(81)
    aopt, copt = make_optimizers(actor, critic)
    episodes = fixture_group(actor, critic, horizon=8)
    horizon, counts = 8, {}
    if case == "single":
        episodes = episodes[:1]
    elif case == "triple":
        episodes = episodes + [episodes[0]]
    elif case == "partial":
        episodes[1]["macro_rewards"] = episodes[1]["macro_rewards"][:1]
    elif case == "horizon":
        horizon = 6
    else:
        counts["critic_optimizer_steps"] = float("nan")
    with pytest.raises(ValueError):
        update_group(actor, critic, aopt, copt, episodes, counts, horizon=horizon)
    assert "actor_replay_rows" not in counts
    assert not aopt.state and not copt.state
