import torch

from experiments.candidates.vsp_02.teammate_policy_change_b01.host import HandoffEnv


def test_service_order_script_switch_and_round_history():
    # Two parallel worlds: matched receiver and opposite endpoint receiver.
    env = HandoffEnv(2)
    obs = env.reset(torch.ones(2, 16, dtype=torch.int64), False)
    assert obs.shape == (2, 18) and obs.dtype == torch.float32
    assert torch.count_nonzero(obs[:, 7:17]) == 0
    obs, reward, done = env.step(torch.tensor([1, 0]))
    assert not done and reward.tolist() == [0, 0]
    assert obs[:, 8].tolist() == [1, 1]  # Prior RIGHT visible from initial positions.
    assert obs[:, 11].tolist() == [1, 1]
    obs, reward, _ = env.step(torch.tensor([1, 0]))
    assert reward.tolist() == [0, 0]
    assert obs[:, 11].tolist() == [1, 0]  # Visibility at start of prior step.
    assert obs[:, 4].tolist() == [0, 0]
    obs, reward, done = env.step(torch.tensor([3, 3]))
    assert reward.tolist() == [1, 0] and not done
    assert obs[:, 0].tolist() == [0, 0] and obs[:, 2].tolist() == [1, 1]
    assert obs[:, 1].tolist() == [0, 0]
    assert obs[:, 15].tolist() == [1, 1] and obs[:, 16].tolist() == [1, 0]
    assert obs[:, 10].tolist() == [1, 0]
    assert obs[:, 11].tolist() == [1, 0]
    obs = env.reset(torch.tensor([[-1] * 16, [1] * 16]), True)
    assert obs[:, 17].tolist() == [1, 1]
    assert torch.count_nonzero(obs[:, 7:17]) == 0
    obs, _, _ = env.step(torch.tensor([1, 0]))
    assert env.courier.tolist() == [1, -1]
    env.step(torch.tensor([1, 0]))
    _, reward, _ = env.step(torch.tensor([3, 3]))
    assert reward.tolist() == [1, 1]


def test_ineffective_actions_clipping_and_simultaneous_no_transfer():
    env = HandoffEnv(3)
    env.reset(torch.ones(3, 16, dtype=torch.int64), False)
    env.step(torch.tensor([1, 1, 3]))
    env.step(torch.tensor([1, 2, 2]))
    # Already at endpoint but moving, arriving now, and receiving at midpoint: all zero.
    _, reward, _ = env.step(torch.tensor([1, 1, 3]))
    assert reward.tolist() == [0, 0, 0]
    env.receiver[:] = torch.tensor([-2, 2, 0])
    env.step(torch.tensor([0, 1, 3]))
    assert env.receiver.tolist() == [-2, 2, 0]


def test_hidden_fields_and_no_current_or_future_action_leak():
    env = HandoffEnv(1)
    env.reset(torch.ones(1, 16, dtype=torch.int64), False)
    env.receiver[:] = -2
    env.courier[:] = 1
    first = env.observation()
    env.courier[:] = 2
    env.lights[:] = -1
    second = env.observation()
    assert torch.equal(first, second)
    assert second[0, 3:12].tolist() == [0] * 9
    env.receiver.zero_()
    env.courier.zero_()
    first = env.observation()
    env.lights[:, 1:] *= -1
    assert torch.equal(first, env.observation())
    # Same public bit and observation history; a current script action has no observation field.
    assert first[0, 7:12].tolist() == [0] * 5


def test_full_episode_has_sixteen_services_and_only_terminal_at_48():
    env = HandoffEnv(1)
    env.reset(torch.ones(1, 16, dtype=torch.int64), False)
    total = 0
    for t in range(48):
        obs, reward, done = env.step(torch.tensor([3 if t % 3 == 2 else 1]))
        total += reward.item()
        assert done == (t == 47)
        assert (obs is None) == done
    assert total == 16
