"""Scientific branch, credit and bounded publication checks using synthetic worlds."""
import json
import math

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.reactive_renewal_b01 import reactive, study
from experiments.candidates.ucope.uav_motion_prefix_b01 import learner
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import (
    arm_copy, generator, snapshot, tanh_log_prob, templates,
)
from experiments.candidates.ucope.uav_motion_prefix_b01.study import new_counts


def models():
    return arm_copy(templates(9901), True, duration_head_seed=990100012)


def set_branch(actor, branch):
    with torch.no_grad():
        actor.duration[-1].bias.fill_(-1000)
        actor.duration[-1].bias[branch] = 0


def test_per_owner_phase_and_command_copy_without_unused_draws():
    actor, _ = models()
    mean, recurrent = torch.zeros(5, 3), torch.zeros(5, 64)
    previous = np.linspace(-.9, .9, 15, dtype=np.float32).reshape(5, 3)
    vrng, grng = generator(11), generator(12)
    gate_before = grng.get_state().clone()
    forced = reactive.draw_commands(actor, mean, recurrent, previous, np.zeros(5, bool), vrng, grng)
    assert forced[3].all() and forced[5].all()
    assert torch.equal(gate_before, grng.get_state())
    reference = generator(11)
    expected = torch.stack([torch.randn(3, generator=reference) for _ in range(5)])
    torch.testing.assert_close(forced[1], expected)
    assert torch.equal(vrng.get_state(), reference.get_state())

    set_branch(actor, reactive.KEEP)
    velocity_before = vrng.get_state().clone()
    kept = reactive.draw_commands(actor, mean + 3, recurrent, forced[0], forced[5], vrng, grng)
    np.testing.assert_array_equal(kept[0], forced[0])
    assert not kept[3].any() and not kept[5].any()
    assert torch.equal(velocity_before, vrng.get_state())
    # A KEEP cannot follow a KEEP: each owner is forced fresh next tick.
    renewed = reactive.draw_commands(actor, mean, recurrent, kept[0], kept[5], vrng, grng)
    assert renewed[3].all() and renewed[5].all()

    set_branch(actor, reactive.END)
    ended = reactive.draw_commands(actor, mean, recurrent, renewed[0], renewed[5], vrng, grng)
    assert (ended[2] == reactive.END).all()
    assert ended[3].all() and ended[5].all()
    # END starts a new first tick, so the next tick is eligible again.
    set_branch(actor, reactive.KEEP)
    mixed = np.array([True, False, True, False, True])
    result = reactive.draw_commands(actor, mean, recurrent, previous, mixed, vrng, grng)
    np.testing.assert_array_equal(result[0][mixed], previous[mixed])
    np.testing.assert_array_equal(result[5], ~mixed)
    assert torch.equal(result[3], torch.from_numpy(~mixed))


def test_recorded_multidimensional_branch_density_and_gradients():
    actor, _ = models()
    mean = torch.zeros(2, 4, 5, 3, requires_grad=True)
    recurrent = torch.zeros(2, 4, 5, 64)
    previous = torch.ones(2, 4, 5, 3, requires_grad=True)
    u = torch.full_like(mean, .2)
    eligible = torch.tensor([False, True, True, False, True]).expand(2, 4, 5)
    branches = torch.tensor([0, 0, 1, 0, 1]).expand(2, 4, 5)
    fresh = ~eligible | (branches == reactive.END)
    logp = reactive.row_log_probs(actor, mean, recurrent, previous, eligible, branches, u, fresh)
    expected = torch.where(fresh, tanh_log_prob(u, mean, actor.log_std), 0)
    expected = expected - eligible * math.log(2)
    torch.testing.assert_close(logp, expected)
    logp.sum().backward()
    assert not mean.grad[~fresh].any()
    assert mean.grad[fresh].abs().sum() > 0
    assert previous.grad is None
    assert actor.duration[-1].bias.grad.abs().sum() > 0


def test_replay_identity_and_keep_credit_including_final_reward(monkeypatch):
    torch.set_num_threads(1)
    actor, critic = models()
    counts, emitted = new_counts(renewal=True, short=True), []
    episodes = []
    for e in range(2):
        episodes.append(reactive.collect_episode(SyntheticAdapter(19, 8), actor, critic, 8,
            90 + e, generator(21 + e), generator(31 + e),
            dict(arm="R", phase="train", episode=e), lambda: None, counts, emitted.append))
    rollout = {key: torch.stack([ep[key] for ep in episodes]) for key in episodes[0]}
    mean, recurrent = learner.recurrent_outputs(actor, rollout, 4)
    replayed = reactive.row_log_probs(actor, mean, recurrent, rollout["previous"],
        rollout["eligible"], rollout["branches"], rollout["u"], rollout["fresh"])
    torch.testing.assert_close(replayed, rollout["logp"], rtol=2e-5, atol=2e-6)
    assert (rollout["eligible"] & ~rollout["fresh"]).any()
    assert rollout["eligible"][:, -1].any()
    targets = learner.returns_to_go(rollout["reward"])
    torch.testing.assert_close(targets[:, -1], rollout["reward"][:, -1])
    expected = targets - rollout["value"]
    expected = (expected - expected.mean()) / (expected.std(unbiased=False) + 1e-8)
    observed = []
    original = reactive.clipped_policy_loss

    def capture(new_logp, old_logp, advantage, mask):
        torch.testing.assert_close(advantage, expected)
        assert mask.all()  # Includes eligible KEEP and final eligible rows.
        observed.append(mask.clone())
        return original(new_logp, old_logp, advantage, mask)

    monkeypatch.setattr(reactive, "clipped_policy_loss", capture)
    before = snapshot(actor, critic)
    reactive.update(actor, critic, learner.optimizer_for(actor, critic), episodes, 4,
                    lambda: None, counts)
    assert len(observed) == counts["optimizer_steps"] == 4
    assert not torch.equal(before["duration"], snapshot(actor, critic)["duration"])
    assert counts["final_gate_credit_decisions"] == int(rollout["eligible"][:, -1].sum())


def test_complete_fixture_exposure_pairing_and_evaluation_isolation(tmp_path):
    torch.set_num_threads(1)
    result = study.run(study.Config.engineering(), tmp_path / "complete")
    assert result["status"] == "COMPLETE"
    counts = result["counts"]
    assert counts["train_team_steps"] == 96
    assert counts["eval_team_steps"] == 96
    assert counts["team_steps"] == counts["step_calls"] == 192
    assert counts["optimizer_steps"] == 24
    assert counts["train_episodes"] == counts["eval_episodes"] == 12
    assert result["panel"]["all_panels_complete"]
    assert len(result["panel"]["R_minus_F"]["differences"]) == 3
    for arm in ("R", "F", "G"):
        record = result["arms"][arm]
        assert record["training_generators_unchanged_by_evaluation"]
        assert record["evaluation_parameter_exposure"]["total"]["displacement"] == 0
        assert record["exposure"]["common_actor"]["displacement"] > 0
        assert record["exposure"]["critic"]["displacement"] > 0
    assert result["arms"]["F"]["exposure"]["duration"]["displacement"] == 0
    assert result["arms"]["R"]["exposure"]["duration"]["displacement"] > 0
    assert result["arms"]["R"]["trainable_parameters"] == 68553
    assert result["arms"]["F"]["trainable_parameters"] == 66311
    rows = [json.loads(line) for line in (tmp_path / "complete/episodes.jsonl").read_text().splitlines()]
    expected = list(range(990120000, 990120003))
    for arm in study.LABELS:
        assert [r["reset_seed"] for r in rows if r["arm"] == arm and r["phase"] == "eval"] == expected


def test_failed_attempt_retains_counts_without_result_polarity(tmp_path):
    class Broken(SyntheticAdapter):
        def step(self, action):
            raise RuntimeError("fixture step failure")

    result = study.run(study.Config.engineering(), tmp_path / "failed",
                       factory=lambda seed: Broken(seed, 8))
    assert result["status"] == "INCOMPLETE"
    assert result["error"]["message"] == "fixture step failure"
    assert result["counts"]["step_calls"] == 1
    assert result["counts"]["team_steps"] == 0
    assert not result["panel"]["complete"]
    assert result["panel"]["reading"] is None
    assert (tmp_path / "failed/summary.json").is_file()


@pytest.mark.parametrize("failure", ("G_constructor", "after_all_panels"))
def test_late_failure_preserves_partial_primary_without_polarity(tmp_path, failure):
    constructed = 0

    class LateFailure(SyntheticAdapter):
        def __init__(self, seed, is_g):
            super().__init__(seed, 8)
            self.is_g = is_g

        def close(self):
            if self.is_g and failure == "after_all_panels":
                raise RuntimeError("late fixture close failure")

    def factory(seed):
        nonlocal constructed
        constructed += 1
        if constructed == 3 and failure == "G_constructor":
            raise RuntimeError("late fixture constructor failure")
        return LateFailure(seed, constructed == 3)

    result = study.run(study.Config.engineering(), tmp_path / failure, factory=factory)
    assert result["status"] == "INCOMPLETE"
    panel = result["panel"]
    assert panel["R_minus_F"]["complete"]
    assert len(panel["R_minus_F"]["differences"]) == 3
    assert panel["all_panels_complete"] == (failure == "after_all_panels")
    assert not panel["complete"]
    assert panel["reading"] is None
