import json
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest
import torch

from experiments.candidates.ucope.native_return_acquisition_b01 import learner as l
from experiments.candidates.ucope.native_return_acquisition_b01 import evaluation as e
from experiments.candidates.ucope.conditioning_discriminator_r01 import host, rng
from scripts import run_ucope_native_return_acquisition_b01 as runner


def test_initialization_stream_and_categorical_boundary():
    global_state = torch.random.get_rng_state().clone()
    actor = l.Actor(9006301)
    assert sum(p.numel() for p in actor.parameters()) == 468
    assert torch.equal(global_state, torch.random.get_rng_state())
    generator = torch.Generator().manual_seed(9006301)
    for actual in (actor.w1, actor.w2):
        expected = torch.empty_like(actual)
        torch.nn.init.xavier_uniform_(expected, generator=generator)
        assert torch.equal(expected, actual)
    assert actor.root.count_nonzero() == 0
    assert actor.b1.count_nonzero() == actor.b2.count_nonzero() == 0
    assert l.categorical(torch.tensor([[.25, .25, .25, .249]]).repeat(3, 1),
                         torch.tensor([0., .25, .9999])).tolist() == [0, 1, 3]


def test_loss_leave_one_out_all_row_denominator():
    returns = torch.arange(256, dtype=torch.float32).requires_grad_()
    roots = torch.zeros(256, requires_grad=True)
    tails = torch.zeros(256, requires_grad=True)
    loss = l.score_loss(returns, roots, tails)
    loss.backward()
    expected = []
    for c in range(8):
        values = list(range(32 * c, 32 * (c + 1)))
        expected.extend([-(value - sum(other for j, other in enumerate(values) if j != i) / 31) / 256
                         for i, value in enumerate(values)])
    torch.testing.assert_close(roots.grad, torch.tensor(expected))
    torch.testing.assert_close(tails.grad, roots.grad)
    assert returns.grad is None


def test_collector_selected_terms_rng_and_addresses(monkeypatch):
    actor = l.Actor(9006301)
    root_generator = torch.Generator().manual_seed(10006301)
    tail_generator = torch.Generator().manual_seed(11006301)
    expected_root = torch.Generator().manual_seed(10006301)
    expected_tail = torch.Generator().manual_seed(11006301)
    roots = (torch.rand(256, generator=expected_root) >= .5).long()
    uniforms = torch.rand(256, generator=expected_tail)
    calls, chosen = [], {}

    def fake_host(context, **kw):
        row = len(calls)
        calls.append(kw)
        assert kw["ancestry"] == l.ancestry(9006301, context)
        assert kw["episode_index"] == 96 + row % 32
        assert kw["support"] == (2, 4, 6, 8)
        assert not kw.get("evaluation", False)
        probe = bool(roots[row])
        assert kw["root_action"] == ("PROBE" if probe else "IMMEDIATE")
        count = row % 7 if probe else None
        period = kw["tail_selector"](count) if probe else kw["immediate_period"]
        chosen[row] = (count, period)
        return host.Execution(count, kw["root_action"], period, (row % 5) / 5, -.09 if probe else 0.,
                              .3, 8 if probe else 2)

    monkeypatch.setattr(host, "execute_episode", fake_host)
    counts = l.new_counts()
    loss, returns, probes = l.collect_batch(actor, 9006301, 3, root_generator, tail_generator, counts)
    actual_grad = torch.autograd.grad(loss, tuple(actor.parameters()), retain_graph=True)
    reference_terms = []
    for row in range(256):
        c = row // 32
        value = actor.root[c].log_softmax(-1)[roots[row]]
        if roots[row]:
            count, period = chosen[row]
            logits = actor.tail(torch.tensor([c]), torch.tensor([count]))[0]
            expected = int(l.categorical(logits.detach().softmax(-1), uniforms[row]))
            assert period == l.K_EVAL[expected]
            value = value + logits.log_softmax(-1)[expected]
        reference_terms.append(value)
    grouped = returns.reshape(8, 32)
    advantage = (grouped - (grouped.sum(1, keepdim=True) - grouped) / 31).flatten()
    expected_loss = -(advantage * torch.stack(reference_terms)).mean()
    expected_grad = torch.autograd.grad(expected_loss, tuple(actor.parameters()))
    for actual, expected in zip(actual_grad, expected_grad):
        torch.testing.assert_close(actual, expected, atol=2e-7, rtol=2e-5)
    assert torch.equal(root_generator.get_state(), expected_root.get_state())
    assert torch.equal(tail_generator.get_state(), expected_tail.get_state())
    assert counts["episodes"] == 256
    assert counts["transitions"] == 512 + 6 * probes
    assert counts["probe_time_units"] == 2 * probes
    assert counts["committed_period_units"] == sum(period for _, period in chosen.values())


def test_severed_callback_precedes_actual_marks_and_native_payment(monkeypatch):
    events = []
    def coin(probability, namespace, *keys, counter=0):
        events.append(namespace)
        return True
    monkeypatch.setattr(host, "bernoulli", coin)
    context = l.CONTEXTS[4]
    def select(count):
        assert count == 6
        assert "mark" not in events and "tail-service" not in events
        return 2
    paid = host.execute_episode(context, ancestry=l.ancestry(9006301, context), episode_index=0,
                                root_action="PROBE", support=l.K_EVAL, tail_selector=select)
    assert paid.probe_primitive == pytest.approx(.08 - float(context[2]))
    assert paid.external_return == pytest.approx(1 - .02 - .004 + .08 - float(context[2]))
    assert paid.transition_count == 8
    events.clear()
    immediate = host.execute_episode(context, ancestry=l.ancestry(9006301, context), episode_index=0,
                                     root_action="IMMEDIATE", support=l.K_EVAL, immediate_period=4)
    assert immediate.external_return == pytest.approx(.944)
    assert immediate.probe_primitive == 0 and immediate.transition_count == 2
    assert events == ["regime", "tail-service"]
    address = l.ancestry(9006301, context)
    assert rng._payload("regime", (*address, 0), 0) != rng._payload("eval-regime", (*address, 0), 0)
    assert address != l.ancestry(6301, context)
    assert address != l.ancestry(9006301, l.CONTEXTS[5])


def test_modal_evaluation_pairing_float64_and_no_grad(monkeypatch):
    actor = l.Actor(9006301)
    with torch.no_grad():
        actor.root[0, 1] = 1
        actor.w2.zero_()
        actor.b2.zero_()
    calls = []
    def fake_host(context, **kw):
        assert not torch.is_grad_enabled()
        calls.append((context, kw))
        probe = kw["root_action"] == "PROBE"
        period = kw["tail_selector"](3) if probe else kw["immediate_period"]
        assert period == (2 if probe else 4)
        value = 1. + (1e-8 * (kw["episode_index"] + 1) if probe else 0.)
        return host.Execution(3 if probe else None, kw["root_action"], period, value, -.02 if probe else 0., 1., 8 if probe else 2)
    monkeypatch.setattr(host, "execute_episode", fake_host)
    output = {}
    e.evaluate(actor, 9006301, 2, output, lambda: None)
    for first, second in zip(calls[::2], calls[1::2]):
        assert first[0] == second[0]
        for key in ("ancestry", "episode_index", "evaluation", "support"):
            assert first[1][key] == second[1][key]
        assert first[1]["evaluation"] is True
    assert output["delta"] == pytest.approx(1.5e-8 / 8, abs=1e-16)
    assert output["conditional_mc_se"] == pytest.approx(5e-9 / 8, abs=1e-16)
    assert output["actor_counts"]["episodes"] == output["reference_counts"]["episodes"] == 16
    assert output["actor_probe_frequency"] == 1 / 8
    assert all(p.grad is None for p in actor.parameters())


@pytest.mark.parametrize("delta,branch", [(.0011, "NR-A"), (.001, "NR-B"), (0., "NR-B"), (-.001, "NR-B"), (-.0011, "NR-C")])
def test_primary_rule(delta, branch):
    rows = [dict(seed=s, profile="science", status="COMPLETE", evaluation={"delta": delta}) for s in (6301, 6302)]
    assert e.reading_rule(rows)["branch"] == branch
    rows[1]["status"] = "INCOMPLETE"
    assert e.reading_rule(rows)["branch"] == "INCOMPLETE"


def test_partial_summary_without_new_exposure(tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _: None)
    monkeypatch.setattr(l, "Actor", lambda _: (_ for _ in ()).throw(RuntimeError("synthetic initialization failure")))
    assert runner.run(SimpleNamespace(out=str(tmp_path), seed=9006301, profile="technical")) == 1
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["status"] == "INCOMPLETE"
    assert summary["training_counts"]["episodes"] == summary["joint_optimizer_steps"] == 0
    assert "synthetic initialization failure" in summary["error"]


def test_real_technical_smoke(tmp_path):
    # Run once via the admitted detached command; this check reads that exact output.
    if "UCOPE_TECHNICAL_OUTPUT" not in os.environ:
        pytest.skip("set UCOPE_TECHNICAL_OUTPUT to the single admitted technical smoke output")
    tmp_path = Path(os.environ["UCOPE_TECHNICAL_OUTPUT"])
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["status"] == "TECHNICAL_COMPLETE"
    assert summary["joint_optimizer_steps"] == 2
    assert summary["training_counts"]["episodes"] == 512
    assert summary["evaluation"]["actor_counts"]["episodes"] == 128
    assert summary["evaluation"]["reference_counts"]["episodes"] == 128
    assert len((tmp_path / "training.jsonl").read_text().splitlines()) == 2
    state = torch.load(tmp_path / "final_parameters.pt", weights_only=True)
    assert sum(t.numel() for t in state.values()) == 468
    assert summary["exposure"]["root"]["initial_l2"] == 0
    assert summary["exposure"]["tail"]["initial_l2"] > 0
    assert summary["wall_seconds"] < 60
