"""Changed-contract support checks; never a native scientific pilot."""

import json
import math
import time

import numpy as np
import pytest
import torch

from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.channel import Channel, payloads
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.model import (
    build_arm, action_terms, sample_actions, snapshot,
)
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.learner import collect_episode
from experiments.candidates.contention_aware_decentralized_communication.cadc_b01.study import run_arm, paired_primary, new_counts
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.learner import recurrent_outputs
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import generator

torch.set_num_threads(1)


def raw_observation():
    raw = np.zeros((5, 104), dtype=np.float32)
    raw[:, :3] = [.4, .6, .5]
    raw[0, 3:9] = [.1, -.1, .4, -.2, .2, .8]
    return raw


def test_local_payload_and_delivery_order():
    raw = raw_observation()
    payload = payloads(raw)
    np.testing.assert_allclose(payload[0], [.4, .6, .5, .35, .65, 0, .1])
    np.testing.assert_array_equal(payload[1, 3:], np.zeros(4))
    channel = Channel(31)
    channel.good = False
    before = channel.features().copy()
    assert channel.resolve([1, 0, 0, 0, 0], raw) == .001
    assert channel.pending[0]
    assert not channel.records.any()
    raw[:] = 99  # In-transit payload is frozen send-time own information.
    channel.good = True  # Does not change the already selected five-tick delay.
    for _ in range(4):
        channel.advance()
        channel.begin_tick()
        assert channel.pending[0] and not channel.records.any()
    channel.advance()
    channel.begin_tick()
    assert not channel.pending[0]
    np.testing.assert_allclose(channel.records[1, 0, :7], payload[0])
    assert channel.records[1, 0, 7] == 1
    assert channel.records[1, 0, 8] == 0
    assert channel.records[1, 0, 9] == 5/256
    assert not channel.records[0, 0].any()
    assert before.shape == (5, 63)
    assert Channel(31).features().shape == before.shape
    assert not Channel(31).pending.any()


def test_collision_charge_pending_mask_and_exogenous_rng():
    raw = raw_observation()
    channel, other = Channel(91), Channel(91)
    assert channel.resolve([1, 1, 1, 0, 0], raw) == .003
    assert channel.collisions == 3 and not channel.inflight
    assert channel.resolve([1, 0, 0, 0, 0], raw) == .001
    assert channel.resolve([1, 0, 0, 0, 0], raw) == 0
    assert channel.attempts == 4
    for _ in range(20):
        channel.advance()
        other.advance()
        assert channel.good == other.good
    # A reset owns new private arrays/RNG and carries no old deliveries.
    fresh = Channel(91)
    assert not fresh.inflight and not fresh.records.any() and not fresh.pending.any()


def test_common_parameters_masked_density_and_round_robin():
    learned, lc = build_arm(31, "LEARNED")
    rr, rc = build_arm(31, "RR")
    for name, value in rr.state_dict().items():
        torch.testing.assert_close(value, learned.state_dict()[name], rtol=0, atol=0)
        assert value.data_ptr() != learned.state_dict()[name].data_ptr()
    for name, value in rc.state_dict().items():
        torch.testing.assert_close(value, lc.state_dict()[name], rtol=0, atol=0)
    eligible = torch.tensor([True, False, True, False, True])
    mean, recurrent = torch.zeros(5, 3), torch.zeros(5, 64)
    with torch.no_grad():
        learned.send.bias.fill_(math.log(3))
    u, sends = sample_actions(rr, mean, recurrent, eligible, 2, generator(1), generator(2))
    assert sends.tolist() == [False, False, True, False, False]
    _, pending_schedule = sample_actions(rr, mean, recurrent, eligible, 1, generator(1), generator(2))
    assert not pending_schedule.any()
    ones, zeros = torch.ones(5, dtype=torch.bool), torch.zeros(5, dtype=torch.bool)
    lp1, _ = action_terms(learned, mean, recurrent, u, ones, eligible)
    lp0, _ = action_terms(learned, mean, recurrent, u, zeros, eligible)
    torch.testing.assert_close(lp1-lp0, eligible.float()*math.log(3))
    rp1, _ = action_terms(rr, mean, recurrent, u, ones, eligible)
    rp0, _ = action_terms(rr, mean, recurrent, u, zeros, eligible)
    torch.testing.assert_close(rp1, rp0)
    _, sampled = sample_actions(learned, mean, recurrent, eligible, 0, generator(1), generator(2))
    assert not sampled[~eligible].any()


class Fixture(SyntheticAdapter):
    def _obs(self):
        obs = raw_observation()
        obs[:, :2] = self.positions[:, :2]/1000
        obs[:, 2] = (self.positions[:, 2]-50)/100
        obs[:, -1] = self.t/self.horizon
        return obs


def test_behavior_replay_equal_and_evaluator_no_updates():
    actor, critic = build_arm(21, "LEARNED")
    before = snapshot(actor, critic)
    counts, rows = new_counts(), []
    ep = collect_episode(Fixture(42), actor, critic, 8, 42, 43, generator(44), generator(45),
                         dict(phase="eval", episode=0), counts, rows.append, lambda: None)
    rollout = {k: v[None] for k, v in ep.items()}
    mean, recurrent = recurrent_outputs(actor, rollout, 4)
    logp, _ = action_terms(actor, mean, recurrent, rollout["u"], rollout["sends"], rollout["eligible"])
    torch.testing.assert_close(logp, rollout["logp"], atol=2e-5, rtol=1e-5)
    assert counts["optimizer_steps"] == 0 and counts["eval_team_steps"] == 8
    assert rows[0]["communication_charge"] == pytest.approx(.001*rows[0]["attempts"])
    assert rows[0]["J_net"] == pytest.approx(rows[0]["J_physical"]-rows[0]["charge_per_tick"])
    assert rows[0]["max_pending"] <= 5
    for k, value in before.items():
        torch.testing.assert_close(value, snapshot(actor, critic)[k], rtol=0, atol=0)


def test_synthetic_learner_to_primary_publication(tmp_path):
    summaries = [run_arm(23, arm, tmp_path/arm, time.monotonic(), factory=Fixture,
                         horizon=8, train=2, final=2, chunk=4) for arm in ("LEARNED", "RR")]
    for s in summaries:
        assert s["status"] == "COMPLETE" and s["publication_readback"]
        assert not s["scientific_invocation"]
        assert s["counts"]["optimizer_steps"] == 4
        assert s["counts"]["eval_team_steps"] == 16
        assert s["exposure"]["actor"]["displacement"] > 0
        stored = json.loads((tmp_path/s["arm"]/"summary.json").read_text())
        assert stored["counts"] == s["counts"]
        checkpoint = torch.load(tmp_path/s["arm"]/"final.pt", weights_only=True)
        assert checkpoint["input_size"] == 171 and checkpoint["critic_size"] == 451
    assert summaries[0]["exposure"]["send"]["displacement"] > 0
    assert paired_primary(summaries, expected=2)["complete"]
    summaries[1]["rows"][-1]["channel_seed"] += 1
    assert not paired_primary(summaries, expected=2)["complete"]


@pytest.mark.parametrize("delta,reading", [(.02,"ABOVE_MEI"),(.01,"INSIDE_MEI"),(-.01,"INSIDE_MEI"),(-.02,"ADVERSE")])
def test_exact_reading_boundaries(delta, reading):
    summaries = []
    for arm in ("LEARNED", "RR"):
        row = dict(arm=arm, phase="eval", episode=0, master=31, reset_seed=11, channel_seed=12,
                   steps=256, J_net=delta if arm=="LEARNED" else 0, J_physical=0., charge_per_tick=0.)
        summaries.append(dict(arm=arm, status="COMPLETE", rows=[row]))
    assert paired_primary(summaries, expected=1)["reading"] == reading
