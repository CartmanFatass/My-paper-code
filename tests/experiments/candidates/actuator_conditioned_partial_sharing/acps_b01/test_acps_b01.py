import copy
import json

import numpy as np
import pytest
import torch

from experiments.candidates.actuator_conditioned_partial_sharing.acps_b01.environment import CapabilityAdapter
from experiments.candidates.actuator_conditioned_partial_sharing.acps_b01.policy import build_arm
from experiments.candidates.actuator_conditioned_partial_sharing.acps_b01.study import MASTER, primary
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import make_real
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import collect_episode, recurrent_outputs
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator, joint_terms
from experiments.candidates.ucope.uav_motion_prefix_b01.study import new_counts


def test_physical_integration_public_information_and_clipping():
    env = CapabilityAdapter(7001)
    ordinary = make_real(7001)
    obs, _ = env.reset(seed=7001)
    base_obs, _ = ordinary.reset(seed=7001)
    np.testing.assert_array_equal(obs[:, :104], base_obs)
    np.testing.assert_array_equal(env.env.user_positions, ordinary.env.user_positions)
    np.testing.assert_array_equal(obs[:, 104:109], np.broadcast_to(env.env.capabilities, (5, 5)))
    np.testing.assert_array_equal(obs[:, 109:114], np.eye(5))
    assert sorted(env.env.capabilities) == [.5, .75, 1., 1.25, 1.5]
    env.env.uav_positions[:] = [[998, 2, 149], [2, 998, 51], [500, 500, 100],
                                [500, 500, 100], [500, 500, 100]]
    before = env.env.uav_positions.copy()
    command = np.array([[1, -1, 1], [-1, 1, -1], [.2, .4, -.1], [.8, -.2, .3], [-.4, .6, -.7]], dtype=np.float32)
    unchanged = command.copy()
    expected = before + command * env.env.capabilities[:, None] * 30
    expected = np.clip(expected, [0, 0, 50], [1000, 1000, 150])
    caps = env.env.capabilities.copy()
    env.step(command)
    np.testing.assert_allclose(env.env.uav_positions, expected, rtol=1e-6, atol=2e-6)
    np.testing.assert_array_equal(command, unchanged)
    np.testing.assert_array_equal(env.env.capabilities, caps)
    assert env.env.max_speed == ordinary.env.max_speed == 30
    env.reset(seed=7001)
    np.testing.assert_array_equal(env.env.capabilities, caps)


def test_common_initialization_public_lookup_and_replay_gradients():
    torch.set_num_threads(1)
    torch.manual_seed(51)
    before = torch.random.get_rng_state().clone()
    shared, cs = build_arm(MASTER, "SHARED")
    adaptive, ca = build_arm(MASTER, "ACPS")
    assert torch.equal(before, torch.random.get_rng_state())
    for name, value in shared.state_dict().items():
        assert torch.equal(value, adaptive.state_dict()[name])
    for x, y in zip(cs.parameters(), ca.parameters()):
        assert torch.equal(x, y) and x.data_ptr() != y.data_ptr()
    assert sum(p.numel() for p in adaptive.parameters()) - sum(p.numel() for p in shared.parameters()) == 1340
    x = torch.zeros(2, 8, 5, 118)
    x[..., 104:109] = torch.tensor([1.5, .5, 1.25, 1., .75])
    x[..., 109:114] = torch.eye(5)
    rollout = {"obs": x, "hidden": torch.zeros(2, 8, 5, 64)}
    ms, _ = recurrent_outputs(shared, rollout, 4)
    ma, _ = recurrent_outputs(adaptive, rollout, 4)
    torch.testing.assert_close(ma, ms)
    with torch.no_grad():
        adaptive.adapter_a.fill_(.2)
    ma, recurrent = recurrent_outputs(adaptive, rollout, 4)
    explicit = torch.empty_like(ms)
    order = [4, 0, 3, 2, 1]
    for i, c in enumerate(order):
        explicit[..., i, :] = ms[..., i, :] + torch.nn.functional.linear(
            torch.nn.functional.linear(recurrent[..., i, :], adaptive.adapter_b[c]).tanh(),
            adaptive.adapter_a[c])
    torch.testing.assert_close(ma, explicit)
    logp, _ = joint_terms(adaptive, ma, recurrent, torch.zeros_like(ma),
                         torch.zeros(2, 8, 5, dtype=torch.long), torch.ones(2, 8, 5, dtype=torch.bool),
                         torch.zeros(2, 8, 5, dtype=torch.bool), "agent_compound")
    (-logp.mean()).backward()
    assert adaptive.adapter_a.grad.abs().sum() > 0
    assert adaptive.adapter_b.grad.abs().sum() > 0
    assert adaptive.encoder.raw.weight.grad.abs().sum() > 0


def test_source_collector_keeps_proposal_and_unscaled_history():
    class FixedActor:
        duration = None
        duration_conditioned = False
        log_std = torch.full((3,), -3.)

        def __call__(self, x, hidden):
            return torch.zeros(1, 5, 3), torch.zeros(1, 5, 64), hidden

    env = CapabilityAdapter(7002)
    rows, limits = [], []
    episode = collect_episode(env, FixedActor(), lambda x: torch.tensor(0.), 2, 7002,
                              generator(7), generator(8), dict(phase="eval", episode=0),
                              lambda: None, new_counts(), rows.append, lambda row: None,
                              limits, diagnostics=False, ratio_grouping="agent_compound")
    torch.testing.assert_close(episode["obs"][1, :, 114:117], episode["u"][0].tanh())
    assert not torch.allclose(episode["obs"][1, :, 114:117],
                              episode["u"][0].tanh() * torch.from_numpy(env.env.capabilities[:, None]))
    assert episode["obs"].shape == (2, 5, 118)
    assert rows[0]["steps"] == 2 and not limits


def summaries(delta, master=MASTER):
    return [dict(arm=arm, seed=master, complete=True,
                 counts=dict(train_episodes=512, train_team_steps=131072, eval_episodes=32,
                             eval_team_steps=8192, optimizer_steps=1024, rollouts=256),
                 rows=[dict(phase="eval", episode=e, steps=256, pair_master=master, arm=arm,
                            reset_seed=100000 * master + 2000 + e, J=delta if arm == "ACPS" else 0.)
                       for e in range(32)]) for arm in ("SHARED", "ACPS")]


@pytest.mark.parametrize("delta,reading", [(.02, "ABOVE_MEI"), (.01, "INSIDE_MEI"),
                                           (-.01, "INSIDE_MEI"), (-.02, "ADVERSE")])
def test_primary_rule_and_serialized_consumer(delta, reading, tmp_path):
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(summaries(delta)))
    result = primary(json.loads(path.read_text()))
    assert result["reading"] == reading
    assert result["mean"] == delta and len(result["differences"]) == 32
    assert result["conditional_se"] == 0
    broken = copy.deepcopy(summaries(delta))
    broken[0]["rows"].pop()
    assert primary(broken)["reading"] == "INCOMPLETE"
    broken = copy.deepcopy(summaries(delta))
    broken[0]["counts"]["optimizer_steps"] = 0
    assert primary(broken)["reading"] == "INCOMPLETE"


@pytest.mark.parametrize("master", [9101, 9102])
@pytest.mark.parametrize("delta,reading", [(.02, "ABOVE_MEI"), (.01, "INSIDE_MEI"),
                                           (-.01, "INSIDE_MEI"), (-.02, "ADVERSE")])
def test_primary_explicit_master_rejects_foreign_or_mixed_binding(master, delta, reading):
    bound = json.loads(json.dumps(summaries(delta, master)))
    result = primary(bound, master=master)
    assert result["complete"] and result["reading"] == reading
    assert result["mean"] == delta and len(result["differences"]) == 32
    assert primary(bound)["complete"] is (master == MASTER)
    foreign = 9102 if master == 9101 else 9101
    assert not primary(bound, master=foreign)["complete"]
    for field in ("pair_master", "reset_seed"):
        broken = copy.deepcopy(bound)
        broken[1]["rows"][17][field] += 1
        assert not primary(broken, master=master)["complete"]
    broken = copy.deepcopy(bound)
    broken[0]["seed"] = foreign
    assert not primary(broken, master=master)["complete"]
