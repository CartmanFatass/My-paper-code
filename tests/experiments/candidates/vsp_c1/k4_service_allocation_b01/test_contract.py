"""Synthetic fixtures only: no run(), runner main(), or selected seed-402 invocation."""
from copy import deepcopy
import json
from pathlib import Path
import statistics

import numpy as np
import pytest
import torch

from experiments.candidates.vsp_c1.k4_service_allocation_b01 import experiment as ex
from experiments.candidates.vsp_c1.k4_service_allocation_b01 import reporting as rep

torch.set_num_threads(1)
ROOT = Path(__file__).resolve().parents[5]


def test_changed_partner_service_and_rule_ties():
    q = np.array([[2, 2, 2], [2, 2, 2], [2, 2, 2], [4, 1, 4], [0, 0, 0], [4, 4, 4]])
    old_h = np.array([0, 1, 2, 0, 2, 1])
    action = np.array([1, 0, 2, 2, 1, 2])
    arrivals = np.ones_like(q)
    nxt, h, served, overflow, partner = ex.tick(q, old_h, action, arrivals)
    assert partner.tolist() == [1, 2, 0, 2, 0, 2]
    assert served.tolist() == [1, 2, 2, 1, 0, 1]
    assert overflow.tolist() == [0, 0, 0, 1, 0, 2]
    np.testing.assert_array_equal(q.sum(1) + arrivals.sum(1), nxt.sum(1) + served + overflow)
    np.testing.assert_array_equal(h, action)
    assert np.all((nxt >= 0) & (nxt <= 4))
    assert ex.lq_exclude(q, old_h).tolist() == [0, 0, 1, 0, 1, 0]


def test_features_models_and_source_counts(tmp_path):
    selected = json.loads((ROOT / "docs/research/candidates/vsp_c1/VSPC1_K4_SERVICE_ALLOCATION_B01_COUNTS_20260907.json").read_text())
    assert ex.Budget().seed == selected["root_seed"] == 402
    state = torch.tensor([[4., 2., 0., 2., 24.], [2., 4., 0., 1., 0.]])
    assert ex.features(state[:1], torch.tensor([1])).tolist() == [[1, 0.5, 0, 0.5, 0, 0, 1, 0, 1, 0]]
    config = {}
    before_rng = torch.random.get_rng_state().clone()
    for arm in ("FACTOR", "GENERIC"):
        model = ex.QNetwork(arm, 9402)
        config[arm] = ex.configuration(model, ex.Budget(seed=9402))
        assert config[arm]["online_parameters"] == selected["online_parameters"][arm]
        assert all(p.dtype == torch.float32 for p in model.parameters())
        assert model.hidden.bias.count_nonzero() == model.output.bias.count_nonzero() == 0
        period = torch.tensor([2, 6])
        scores = model.all_actions(state, period)
        expected = torch.stack([model(state, torch.full((2,), a), period) for a in range(3)], dim=1)
        torch.testing.assert_close(scores, expected, atol=1e-6, rtol=1e-5)
        assert scores.shape == (2, 3)
    assert torch.equal(before_rng, torch.random.get_rng_state())
    c = ex.counts(ex.Budget())
    expected = selected["learner_per_arm"]
    for key in ("training_episodes", "training_joint_ticks", "training_renewal_rows", "nonterminal_rows",
                "optimizer_steps", "evaluation_episodes", "evaluation_joint_ticks", "evaluation_decisions",
                "target_copies", "all_joint_ticks", "scalar_Q_predictions"):
        assert c[key] == expected[key]
    for use, n in expected["scalar_Q_predictions_by_use"].items():
        assert c[use + "_Q_predictions"] == n
    assert list(ex.Budget().checkpoints) == expected["evaluation_checkpoints"]
    assert ex.rule_counts(ex.Budget()) == selected["fixed_policy_reference"]
    assert 2*c["all_joint_ticks"] + ex.rule_counts(ex.Budget())["evaluation_joint_ticks"] == selected["total_joint_ticks"]
    assert 2*c["scalar_Q_predictions"] == selected["total_scalar_Q_predictions"]
    rep.write_read(tmp_path / "configuration_exposure.json", {
        "exposure_class": "synthetic_model_initializations_only_seed9402",
        "selected_counts_match": True, "configuration": config})


def test_rng_exact_namespace_slots_and_separation():
    train = ex.tapes(9402, 2, 2, update=1)
    for name, namespace in (("arrivals", 21), ("h", 22), ("coin", 23), ("action", 24)):
        generator = np.random.Generator(np.random.PCG64(np.random.SeedSequence([9402, namespace, 2, 1])))
        expected = {"arrivals": lambda: generator.random((2, 48, 3)) < 0.5,
                    "h": lambda: generator.integers(0, 3, 2),
                    "coin": lambda: generator.random((2, 48)),
                    "action": lambda: generator.integers(0, 3, (2, 48))}[name]()
        np.testing.assert_array_equal(train[name], expected)
        np.testing.assert_array_equal(train[name], ex.tapes(9402, 2, 2, update=1)[name])
    eval2 = ex.tapes(9402, 2, 2, evaluation=True)
    eval6 = ex.tapes(9402, 6, 2, evaluation=True)
    assert not np.array_equal(train["arrivals"], eval2["arrivals"])
    assert not np.array_equal(eval2["arrivals"], eval6["arrivals"])
    assert not np.array_equal(train["arrivals"], ex.tapes(9402, 2, 2, update=2)["arrivals"])
    assert eval2["coin"] is eval2["action"] is None


class FixedPolicy:
    def __init__(self, action=0):
        self.action = action
        self.times = []
        self.scored = 0

    def all_actions(self, state, period):
        self.times.extend(state[:, 4].tolist())
        self.scored += 3 * len(state)
        scores = torch.zeros(len(state), 3)
        scores[:, self.action] = 1
        return scores


def test_held_three_action_exploration_and_actual_successor():
    model = FixedPolicy()
    tape = {"h": np.array([0]), "arrivals": np.zeros((1, 48, 3), dtype=bool),
            "coin": np.zeros((1, 48)), "action": ((2 + np.arange(48)//2) % 3)[None, :]}
    batch, desc = ex.collect(model, 2, tape, 1)
    assert model.times == list(range(0, 48, 2)) and model.scored == 72
    assert batch["action"].tolist() == tape["action"][0, ::2].tolist()
    assert batch["next_state"][0].tolist() == [1, 1, 0, 2, 2]
    assert batch["reward"][0].item() == pytest.approx(4/96)
    assert batch["terminal"].tolist() == [False]*23 + [True]
    assert desc == {"J": [6/96], "overflow": [0], "final_backlog": [0], "unused_service": [90]}


def scalar_rule(tape, period):
    """Independent scalar test oracle for one hand-built tape, no policy search."""
    q, h = [2, 2, 2], int(tape["h"][0])
    states, actions, partners = [], [], []
    served = overflow = 0
    for t in range(48):
        order = [(h+1) % 3, (h+2) % 3, h]
        partner = max(order, key=lambda j: q[j])
        if t % period == 0:
            states.append(q[:] + [h, t])
            action = min((j for j in range(3) if j != partner), key=lambda j: (-q[j], j))
            actions.append(action)
        partners.append(partner)
        for j in {action, partner}:
            if q[j]:
                q[j] -= 1
                served += 1
        for j in range(3):
            q[j] += int(tape["arrivals"][0, t, j])
            overflow += max(q[j]-4, 0)
            q[j] = min(q[j], 4)
        h = action
    return states, actions, partners, {"J": served/96, "overflow": overflow,
                                      "final_backlog": sum(q), "unused_service": 96-served}


def test_rule_evaluation_owns_state_and_only_renews(monkeypatch):
    tape = {"h": np.array([1]), "arrivals": ((np.arange(48)[:, None] + np.arange(3)) % 4 == 0)[None, :],
            "coin": None, "action": None}
    original_tape = deepcopy(tape)
    real_collect = ex.collect
    batches, calls = {}, []

    def fixture_tapes(seed, d, episodes, update=0, evaluation=False):
        assert seed == 9402 and episodes == 1 and update == 0 and evaluation
        calls.append(d)
        return tape

    def capture(model, d, supplied_tape, epsilon):
        assert model is None and epsilon == 0
        batch, desc = real_collect(model, d, supplied_tape, epsilon)
        batches[d] = batch
        return batch, desc

    monkeypatch.setattr(ex, "tapes", fixture_tapes)
    monkeypatch.setattr(ex, "collect", capture)
    result = ex.evaluate_rule(ex.Budget(seed=9402, eval_per_period=1))
    assert calls == [2, 6]
    assert result["counts"] == result["observed_counts"]
    expected_states, expected_actions, partners, expected_endpoint = scalar_rule(tape, 6)
    assert batches[6]["state"].tolist() == expected_states
    assert batches[6]["action"].tolist() == expected_actions
    assert len(set(partners[:6])) > 1  # Partner responds inside a held focal segment.
    assert result["endpoint_episodes"]["6"][0] == {"episode": 0, **expected_endpoint}
    learned_batch, _ = real_collect(FixedPolicy(2), 6, tape, 0)
    assert not torch.equal(learned_batch["next_state"], batches[6]["next_state"])
    for key in ("h", "arrivals"):
        np.testing.assert_array_equal(tape[key], original_tape[key])


def test_detached_double_q_uses_third_action_and_skips_terminal():
    class Online:
        def all_actions(self, state, period):
            assert state.shape == (1, 5) and state[0, 4] == 6
            return torch.tensor([[1., 3., 5.]], requires_grad=True)

    class Target:
        def __call__(self, state, action, period):
            assert action.tolist() == [2]
            return torch.tensor([7.], requires_grad=True)

    batch = {"reward": torch.tensor([3/96, 4/96]), "terminal": torch.tensor([False, True]),
             "next_state": torch.tensor([[1., 2., 0., 0., 6.], [0., 0., 0., 1., 48.]]),
             "period": torch.tensor([6, 6])}
    y = ex.targets(Online(), Target(), batch)
    assert y.tolist() == pytest.approx([7+3/96, 4/96], abs=1e-6)
    assert not y.requires_grad


def loss_batches():
    batches = []
    for d, rewards in ((2, [0.1]*24 + [0.3]*24), (6, [0.2]*8 + [0.4]*8)):
        n = len(rewards)
        batches.append({"state": torch.tensor([[2., 2., 2., 0., 0.]]).repeat(n, 1),
                        "action": torch.arange(n) % 3, "period": torch.full((n,), d),
                        "reward": torch.tensor(rewards), "terminal": torch.ones(n, dtype=torch.bool),
                        "next_state": torch.zeros(n, 5), "episodes": 2})
    return batches


def test_equal_period_episode_loss_and_synthetic_adam_path():
    class Scalar(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.value = torch.nn.Parameter(torch.tensor(0.))
        def forward(self, state, action, period):
            return self.value.expand(len(state))

    scalar = Scalar()
    losses = ex.update(scalar, None, torch.optim.SGD(scalar.parameters(), lr=0), loss_batches())
    assert losses == pytest.approx({"2": 0.05, "6": 0.10})
    assert scalar.value.grad.item() == pytest.approx(-0.5)  # Row weighting would give -0.45.
    online = ex.QNetwork("FACTOR", 9402)
    target = deepcopy(online).requires_grad_(False)
    before, frozen = ex.parameters(online).clone(), ex.parameters(target).clone()
    losses = ex.update(online, target, torch.optim.Adam(online.parameters(), lr=0.01,
                       betas=(0.9, 0.999), eps=1e-8, weight_decay=0), loss_batches())
    assert all(np.isfinite(list(losses.values())))
    assert not torch.equal(before, ex.parameters(online))
    assert torch.equal(frozen, ex.parameters(target))


def synthetic_summary(arm, endpoint, points=None):
    consequences = {d: {"J": scores, "overflow": [0]*len(scores), "final_backlog": [2]*len(scores),
                        "unused_service": [96*(1-v) for v in scores]} for d, scores in endpoint.items()}
    summary = {"status": "complete", "arm": arm, "seed": 9402,
               "endpoint_episodes": ex.endpoint_episodes(consequences), **ex.evaluation_result(consequences)}
    if points is not None:
        summary["budget"] = {"seed": 9402, "updates": 256}
        summary["curve"] = [{"update": u, "period_means": {"2": p[0], "6": p[1]}, "mean_J": sum(p)/2}
                            for u, p in zip((0, 64, 128, 192, 256), points)]
    return summary


def test_primary_publication_three_contrasts_auc_initial_and_missing_rule(tmp_path):
    factor = synthetic_summary("FACTOR", {"2": [0.8, 0.6], "6": [0.6, 0.4]},
                               [(0.72, 0.56), (0.8, 0.58), (0.62, 0.45), (0.74, 0.6), (0.7, 0.5)])
    generic = synthetic_summary("GENERIC", {"2": [0.7, 0.4], "6": [0.5, 0.45]},
                                [(0.5, 0.4), (0.58, 0.5), (0.7, 0.55), (0.6, 0.51), (0.55, 0.475)])
    rule = synthetic_summary("LQ-EXCLUDE", {"2": [0.6, 0.55], "6": [0.55, 0.3]})
    factor, generic, rule = [rep.write_read(tmp_path / (s["arm"] + ".json"), s) for s in (factor, generic, rule)]
    partial = rep.publish_comparison(tmp_path / "pair_without_rule.json", factor, generic)
    full = rep.publish_comparison(tmp_path / "pair.json", factor, generic, rule)
    assert partial["status"] == "learner_contrast_only" and full["status"] == "complete"
    assert partial["contrasts"]["FACTOR-GENERIC"] == full["contrasts"]["FACTOR-GENERIC"]
    assert full["readings"] == ["local_FACTOR_gain_over_both_comparators"]
    for name, left, right in (("FACTOR-GENERIC", factor, generic),
                               ("FACTOR-LQ-EXCLUDE", factor, rule), ("GENERIC-LQ-EXCLUDE", generic, rule)):
        differences = {d: [a["J"]-b["J"] for a, b in zip(left["endpoint_episodes"][d], right["endpoint_episodes"][d])]
                       for d in ("2", "6")}
        c = full["contrasts"][name]
        assert c["mean"] == pytest.approx(statistics.mean(statistics.mean(v) for v in differences.values()))
        assert c["conditional_evaluation_SE"] == pytest.approx(0.5*np.sqrt(sum(statistics.variance(v)/2 for v in differences.values())))
    contrasts = full["contrasts"]
    assert contrasts["FACTOR-LQ-EXCLUDE"]["mean"] - contrasts["GENERIC-LQ-EXCLUDE"]["mean"] == pytest.approx(contrasts["FACTOR-GENERIC"]["mean"])
    for arm, s in (("FACTOR", factor), ("GENERIC", generic)):
        for d in ("2", "6"):
            values = [point["period_means"][d] for point in s["curve"]]
            assert full["auc_by_arm_period"][arm][d] == pytest.approx((0.5*values[0] + sum(values[1:4]) + 0.5*values[4])/4)
    assert full["initial_to_final"]["FACTOR"]["mean"] == pytest.approx(-0.04)
    assert full["initial_relative_to_rule"]["FACTOR"]["mean"] > 0
    assert set(full["endpoint_episodes"]) == {"FACTOR", "GENERIC", "LQ-EXCLUDE"}
    assert rep.compare(factor, {"status": "running"})["status"] == "incomplete"


def c(mean, d2=None, d6=None):
    return {"mean": mean, "period_means": {"2": mean if d2 is None else d2, "6": mean if d6 is None else d6}}


def test_overlapping_card_branches_and_material_period_costs():
    assert rep.readings(c(0.025), c(0.025), c(0)) == ["local_FACTOR_gain_over_both_comparators"]
    assert rep.readings(c(0.03), c(-0.01), c(-0.04)) == ["learner_ranking_gain_both_below_rule"]
    assert rep.readings(c(0.01), c(0.03), c(0.02)) == ["local_learned_policy_usefulness_not_factorization"]
    assert rep.readings(c(0), c(0), c(0)) == ["no_practical_continuation_reason"]
    assert "favors_GENERIC_this_instance" in rep.readings(c(-0.025), c(0.025), c(0.05))
    assert "primary_period_loss" in rep.readings(c(0.03, -0.025, 0.085), c(0.03), c(0))
    assert "local_FACTOR_gain_over_both_comparators" not in rep.readings(c(0.03), c(0.03, -0.025, 0.085), c(0))
    assert rep.readings(c(0)) == ["rule_relative_value_unresolved"]
