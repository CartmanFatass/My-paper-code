import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.vsp_c1.k4_reactive_queues_b01 import experiment as ex
from experiments.candidates.vsp_c1.k4_reactive_queues_b01.reporting import auc, compare, reading

torch.set_num_threads(1)
ROOT = Path(__file__).resolve().parents[5]


def test_tick_old_h_service_conservation_and_overflow():
    q = np.array([[2, 2], [2, 2], [0, 0], [4, 4]])
    h, a = np.array([0, 1, 1, 0]), np.array([1, 1, 0, 1])
    arrivals = np.ones((4, 2), dtype=int)
    nxt, next_h, served, overflow, partner = ex.tick(q, h, a, arrivals)
    assert partner.tolist() == [1, 0, 0, 1]
    assert served.tolist() == [1, 2, 0, 1]
    assert overflow.tolist() == [0, 0, 0, 1]
    np.testing.assert_array_equal(next_h, a)
    np.testing.assert_array_equal(q.sum(1) + arrivals.sum(1), nxt.sum(1) + served + overflow)
    assert np.all((nxt >= 0) & (nxt <= 4))


class ZeroPolicy:
    def __init__(self):
        self.times = []

    def both(self, state, period):
        self.times.extend(state[:, 3].tolist())
        return torch.zeros((len(state), 2))


def test_holding_and_actual_segment_successor():
    policy = ZeroPolicy()
    tape = {"h": np.array([0]), "arrivals": np.zeros((1, 48, 2), dtype=bool),
            "coin": None, "action": None}
    batch, desc = ex.collect(policy, 6, tape, 0)
    assert policy.times == list(range(0, 48, 6))
    # First tick serves both, second both, then no work; no arrivals.
    assert batch["reward"][0].item() == pytest.approx(4 / 96)
    assert batch["next_state"][0].tolist() == [0, 0, 0, 6]
    assert batch["action"].tolist() == [0] * 8
    assert batch["terminal"].tolist() == [False] * 7 + [True]
    assert desc == {"J": [4 / 96], "overflow": [0], "final_backlog": [0], "unused_service": [92]}


def test_features_and_initialization_counts():
    feature = ex.features(torch.tensor([[4., 2., 1., 24.]]), torch.tensor([0]))
    assert feature.tolist() == [[1, 0.5, 0.5, 0, 1, 1, 0]]
    for arm, count in (("FACTOR", 300), ("GENERIC", 309)):
        model = ex.QNetwork(arm, 9401)
        assert sum(p.numel() for p in model.parameters()) == count
        assert all(p.dtype == torch.float32 for p in model.parameters())
        assert torch.equal(ex.parameters(model), ex.parameters(ex.QNetwork(arm, 9401)))
        assert not torch.equal(ex.parameters(model), ex.parameters(ex.QNetwork(arm, 9402)))
        assert model.hidden.bias.count_nonzero() == 0
        assert model.output.bias.count_nonzero() == 0


def test_rng_pairing_separation_and_primitive_slots():
    first = ex.tapes(9401, 2, 4, 1)
    second = ex.tapes(9401, 2, 4, 1)
    for key in first:
        np.testing.assert_array_equal(first[key], second[key])
    assert not np.array_equal(first["arrivals"], ex.tapes(9401, 2, 4, 2)["arrivals"])
    evaluation = ex.tapes(9401, 2, 4, evaluation=True)
    assert not np.array_equal(first["arrivals"], evaluation["arrivals"])
    assert not np.array_equal(evaluation["arrivals"], ex.tapes(9401, 6, 4, evaluation=True)["arrivals"])
    policy = ZeroPolicy()
    first["coin"][:] = 0
    first["action"][:] = np.arange(48)[None, :] % 3 == 0
    batch, _ = ex.collect(policy, 2, first, 1)
    assert batch["action"].reshape(4, 24)[0].tolist() == first["action"][0, ::2].tolist()
    assert len(policy.times) == 4 * 24  # Exploration still scored both actions.


def test_double_q_detached_and_terminal_not_scored():
    class Online:
        def both(self, state, period):
            assert len(state) == 1 and state[0, 3] == 6
            return torch.tensor([[1., 3.]], requires_grad=True)
    class Target:
        def __call__(self, state, action, period):
            assert action.tolist() == [1]
            return torch.tensor([7.], requires_grad=True)
    batch = {"reward": torch.tensor([0.25, 0.5]), "terminal": torch.tensor([False, True]),
             "next_state": torch.tensor([[1., 2., 0., 6.], [0., 0., 1., 48.]]),
             "period": torch.tensor([6, 6])}
    y = ex.targets(Online(), Target(), batch)
    assert y.tolist() == [7.25, 0.5]
    assert not y.requires_grad


def test_equal_episode_period_loss_not_row_weighted():
    class Scalar(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.value = torch.nn.Parameter(torch.tensor(0.))
        def forward(self, state, action, period):
            return self.value.expand(len(state))
    model = Scalar()
    batches = []
    for d, rewards in ((2, [1.] * 24 + [3.] * 24), (6, [2.] * 8 + [4.] * 8)):
        n = len(rewards)
        batches.append({"state": torch.zeros(n, 4), "action": torch.zeros(n, dtype=torch.long),
                        "period": torch.full((n,), d), "reward": torch.tensor(rewards),
                        "terminal": torch.ones(n, dtype=torch.bool), "next_state": torch.zeros(n, 4), "episodes": 2})
    losses = ex.update(model, None, torch.optim.SGD(model.parameters(), lr=0), batches)
    assert losses == {"2": 5, "6": 10}
    # derivative of equal-period/equal-episode mean is -5, not row-weighted -4.5.
    assert model.value.grad.item() == pytest.approx(-5, abs=2e-6)


def test_budget_and_rule_boundaries():
    c = ex.counts(ex.Budget())
    assert c == {"training_episodes": 4096, "training_joint_steps": 196608,
                 "training_renewal_rows": 65536, "optimizer_steps": 256,
                 "training_nonterminal_rows": 61440, "evaluation_episodes": 2304,
                 "evaluation_joint_steps": 110592, "evaluation_decisions": 36864,
                 "all_focal_decisions": 102400, "scalar_q_predictions": 454656,
                 "target_copies": 17, "model_selection_steps": 0}
    assert reading(0.025, {"2": 0.025, "6": 0.025}) == "favorable_local_signal"
    assert reading(-0.025, {"2": -0.025, "6": -0.025}) == "favors_GENERIC_this_instance"
    assert reading(0.03, {"2": 0.085, "6": -0.025}) == "period_tradeoff"
    assert reading(0, {"2": 0.03, "6": -0.03}) == "period_tradeoff"
    assert reading(-0.024, {"2": -0.024, "6": -0.024}) == "insufficient_practical_gain"
    assert compare({"status": "running"}, {"status": "complete"})["reading"] == "no_dependent_performance_conclusion"
    assert auc({"budget": {"updates": 256}, "curve": [
        {"update": 0, "period_means": {"2": 0, "6": 1}},
        {"update": 128, "period_means": {"2": 1, "6": 0}},
        {"update": 256, "period_means": {"2": 0, "6": 1}}]}) == {"2": 0.5, "6": 0.5}


def test_real_runner_publication_smoke(tmp_path):
    summaries = []
    for arm in ("FACTOR", "GENERIC"):
        out = tmp_path / arm
        result = subprocess.run([sys.executable, str(ROOT / "scripts/run_vspc1_k4_reactive_queues_b01.py"),
                        "--arm", arm, "--technical-fixture", "--out", str(out)], cwd=ROOT,
                       timeout=60, capture_output=True, text=True)
        (tmp_path / (arm + ".stdout.txt")).write_text(result.stdout)
        (tmp_path / (arm + ".stderr.txt")).write_text(result.stderr)
        assert result.returncode == 0, result.stderr
        s = json.loads((out / "summary.json").read_text())
        assert s["status"] == "complete" and s["seed"] == 9401
        assert s["counts"] == s["observed_counts"]
        assert s["completed_updates"] == 16 and s["target_copy_updates"] == [0, 16]
        assert len(s["td_losses"]) == 16 and len(s["curve"]) == 2
        assert s["final_parameter_displacement"] > 0
        assert s["initial_parameter_norm"] > 0
        assert s["resources"]["peak_rss_bytes"] is None or s["resources"]["peak_rss_bytes"] > 0
        assert len(s["endpoint_episodes"]["2"]) == 2
        summaries.append(s)
    report = compare(*summaries)
    expected = {d: np.array([x["J"] - y["J"] for x, y in zip(
        summaries[0]["endpoint_episodes"][d], summaries[1]["endpoint_episodes"][d])]) for d in ("2", "6")}
    assert report["delta"] == pytest.approx(np.mean([x.mean() for x in expected.values()]))
    assert report["conditional_evaluation_SE"] == pytest.approx(0.5 * np.sqrt(sum(x.var(ddof=1) / 2 for x in expected.values())))
