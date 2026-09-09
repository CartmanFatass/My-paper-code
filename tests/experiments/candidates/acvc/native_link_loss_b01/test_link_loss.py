import importlib.util
import json
from pathlib import Path
import time

import numpy as np
import pytest
import torch

from experiments.candidates.acvc.native_link_loss_b01.binding import Binding
from experiments.candidates.acvc.native_link_loss_b01.model import (
    build_learned, base_architecture, action_generators, gate_terms, snapshot)
from experiments.candidates.acvc.native_link_loss_b01.learner import collect, recurrent_logits, update, optimizer_for
from experiments.candidates.acvc.native_link_loss_b01.report import panel, reading
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import clipped_policy_loss
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter


def observation(coords=((.5, .5),), values=None, own=(.5, .5, .5)):
    obs = np.zeros((5, 104), dtype=np.float32)
    obs[:, :3] = own
    rows = obs[:, 3:63].reshape(5, 20, 3)
    for j, coordinate in enumerate(coords):
        rows[:, j, :2] = np.asarray(coordinate) - np.asarray(own[:2])
        rows[:, j, 2] = .3 if values is None else values[j]
    return obs


def test_binding_zero_relative_ties_reset_and_realized_retrace():
    binding = Binding()
    z, opportunity, _ = binding.observe(observation(), np.ones((5, 3)))
    assert not opportunity.any() and not z[:, 0].any()
    assert binding.valid.all()  # Relative XY zero is an eligible user.
    current = observation(((.8, .8),), own=(.51, .5, .6))
    z, opportunity, c = binding.observe(current, np.ones((5, 3)))
    assert opportunity.all()
    np.testing.assert_allclose(c[0], [-1/3, 0, -1/3], atol=2e-6)
    np.testing.assert_allclose(z[0, 3:5], [-.01, 0], atol=1e-7)
    assert z[0, 12] > 0
    # Anchor is replaced with current .8,.8, never retained across a second loss.
    z, _, _ = binding.observe(observation(((.9, .9),)), np.ones((5, 3)))
    np.testing.assert_allclose(z[0, 3:5], [.3, .3], atol=1e-7)
    fresh = Binding()
    fresh.observe(observation(((.4, .4), (.7, .7)), [.3, .3]), np.ones((5, 3)))
    np.testing.assert_allclose(fresh.anchor, np.full((5, 2), .4), atol=1e-7)


@pytest.mark.parametrize("coords", [(), tuple((.6 + i * .01, .6) for i in range(20)),
                                     ((.5, .5),), ((.5000015, .5),),
                                     ((.5, .5), (.500001, .5))])
def test_empty_saturated_present_and_ambiguous_skip(coords):
    binding = Binding()
    binding.observe(observation(), np.ones((5, 3)))
    _, opportunity, _ = binding.observe(observation(coords, own=(.51, .5, .5)), np.ones((5, 3)))
    assert not opportunity.any()


def test_ambiguous_previous_and_towards_proposal_skip():
    binding = Binding()
    binding.observe(observation(((.5, .5), (.5000015, .5))), np.ones((5, 3)))
    assert not binding.valid.any()
    _, mask, _ = binding.observe(observation(((.8, .8),), own=(.51, .5, .5)), np.ones((5, 3)))
    assert not mask.any()
    binding = Binding()
    binding.observe(observation(), np.ones((5, 3)))
    _, mask, _ = binding.observe(observation(((.8, .8),), own=(.51, .5, .5)), -np.ones((5, 3)))
    assert not mask.any()


def test_private_initialization_containment_parameter_counts_and_streams():
    before = torch.random.get_rng_state().clone()
    t, tc = build_learned(8901, "T")
    g, gc = build_learned(8901, "G")
    assert torch.equal(before, torch.random.get_rng_state())
    assert sum(p.numel() for p in t.parameters()) == 11425
    assert sum(p.numel() for p in g.parameters()) == 26306
    assert sum(p.numel() for p in tc.parameters()) == 34177
    for key, value in t.common.state_dict().items():
        assert torch.equal(value, g.common.state_dict()[key])
    for key, value in tc.state_dict().items():
        assert torch.equal(value, gc.state_dict()[key])
    with torch.no_grad():
        t.common.head[-1].weight.fill_(.2)
        g.common.load_state_dict(t.common.state_dict())
    x, b, z = torch.randn(7, 5, 108), torch.randn(7, 5, 3), torch.randn(7, 5, 13)
    ty, _ = t(x, b, z, t.initial_state())
    gy, _ = g(x, b, z, g.initial_state())
    torch.testing.assert_close(ty, gy)
    isolated_x = x.clone()
    isolated_x[:, 3] += 12
    changed, _ = t(isolated_x, b, z, t.initial_state())
    torch.testing.assert_close(ty[:, [0, 1, 2, 4]], changed[:, [0, 1, 2, 4]])
    seeds = []
    for phase, arms, n in (("train", ("T", "G"), 512), ("eval", ("T", "G", "C", "F"), 32)):
        for arm in arms:
            for e in range(n):
                p, r = action_generators(8901, arm, phase, e)
                seeds.append(p.initial_seed())
                if arm in ("T", "G"):
                    seeds.append(r.initial_seed())
    assert len(seeds) == len(set(seeds)) == 2240


def test_masked_gate_credit_entropy_and_all_row_denominator():
    logits = torch.zeros(2, 5, requires_grad=True)
    mask = torch.zeros(2, 5, dtype=torch.bool)
    mask[0, 0] = True
    choices = torch.ones(2, 5)
    logp, entropy = gate_terms(logits, choices, mask)
    loss = clipped_policy_loss(logp, logp.detach(), torch.ones(2), velocity_mask=mask)
    assert float(loss) == -.5
    loss.backward()
    assert logits.grad[0, 0] != 0 and torch.count_nonzero(logits.grad) == 1
    assert float(entropy[1]) == 0
    assert float(entropy[0]) == pytest.approx(np.log(2))


class PrivateFixture(SyntheticAdapter):
    def _obs(self):
        # Alternate visible user coordinates; every fixture is non-native.
        obs = np.zeros((5, 104), np.float32)
        obs[:, :2] = self.positions[:, :2] / 1000
        obs[:, 2] = (self.positions[:, 2] - 50) / 100
        obs[:, 3:5] = ((.1, .1) if self.t % 2 == 0 else (.9, .9)) - obs[:, :2]
        obs[:, 5] = .3
        return obs


def test_collection_actual_command_replay_and_update(monkeypatch):
    import experiments.candidates.acvc.native_link_loss_b01.learner as learner
    monkeypatch.setattr(learner, "gate_sample", lambda logits, mask, rng: mask.float())
    gate, critic = build_learned(8901, "G")
    with torch.no_grad():
        gate.common.head[-1].weight.fill_(.17)
        gate.residual.head[-1].weight.fill_(-.23)
    base = base_architecture(8901).requires_grad_(False)
    base_inputs, sent_commands = [], []
    base.register_forward_pre_hook(lambda module, args: base_inputs.append(args[0].clone()))
    env = PrivateFixture(1, horizon=64)
    native_step = env.step
    def step(sent):
        sent_commands.append(sent.copy())
        return native_step(sent)
    env.step = step
    counts = {k: 0 for k in ("explicit_resets", "base_agent_forwards", "learned_gate_agent_forwards", "step_calls", "team_steps", "train_episodes", "optimizer_steps")}
    rows = []
    episodes = [collect(env, base, gate, critic, 8901, "G", "train", e, 64, lambda: None, counts, rows.append) for e in range(2)]
    for j in range(1, 64):
        np.testing.assert_array_equal(base_inputs[j][0, :, 104:107], sent_commands[j-1])
    assert not base_inputs[64][0, :, 104:].any()
    assert rows[0]["retrace"] > 0 and env.index_calls == 0
    rollout = {k: torch.stack([e[k] for e in episodes]) for k in episodes[0]}
    assert torch.equal(rollout["u"].tanh(), rollout["b"])
    logits = recurrent_logits(gate, rollout)
    lp, _ = gate_terms(logits, rollout["choice"], rollout["mask"])
    torch.testing.assert_close(lp, rollout["logp"])
    base_before = {k: v.clone() for k, v in base.state_dict().items()}
    update(gate, critic, optimizer_for(gate, critic), episodes, lambda: None, counts)
    assert counts["optimizer_steps"] == 4
    assert all(p.grad is None for p in base.parameters())
    assert all(torch.equal(base_before[k], v) for k, v in base.state_dict().items())


def test_primary_rules_and_complete_synthetic_publication(tmp_path):
    assert [reading(x) for x in (.011, .01, -.01, -.011)] == ["UP", "WITHIN", "WITHIN", "DOWN"]
    rows = [dict(arm=a, phase="eval", episode=e, J=v[e]) for a, v in
            {"T": [.03, .03], "G": [.04, .04], "C": [.04, 0], "F": [0, .04]}.items() for e in range(2)]
    result = panel(rows)
    assert result["primary_min_of_means_J"] == pytest.approx(.01)
    assert result["primary_summary_SE"] is None
    assert result["contrasts"]["T-G"]["mean_J"] < 0
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_native_link_loss_b01.py"
    spec = importlib.util.spec_from_file_location("acvc_runner_test", script)
    module = importlib.util.module_from_spec(spec)
    # Already fixed before this suite; avoid resetting interop after Torch work.
    original = torch.set_num_interop_threads
    torch.set_num_interop_threads = lambda _: None
    try:
        spec.loader.exec_module(module)
    finally:
        torch.set_num_interop_threads = original
    checkpoint = tmp_path / "synthetic_base.pt"
    torch.save({"actor": base_architecture(8901).state_dict()}, checkpoint)
    out = tmp_path / "panel"
    code = module.run(out, checkpoint, 8901, 0, time.monotonic(), "synthetic-only",
                      make_env=lambda seed: PrivateFixture(seed, horizon=32), train_episodes=2, horizon=32, eval_episodes=2)
    assert code == 0
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "complete"
    assert saved["counts"]["team_steps"] == 384
    assert saved["counts"]["optimizer_steps"] == 8
    assert saved["counts"]["explicit_resets"] == 12
    assert len((out / "episodes.jsonl").read_text().splitlines()) == 12
    assert set(saved["primary"]["contrasts"]) == {"T-C", "T-F", "T-G", "G-C", "G-F"}
    assert (out / "final_T.pt").exists() and (out / "final_G.pt").exists()
