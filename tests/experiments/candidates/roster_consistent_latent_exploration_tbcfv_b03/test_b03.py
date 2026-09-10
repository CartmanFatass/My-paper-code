"""One no-simulation fixture for the changed learning and publication boundary."""
from types import SimpleNamespace
import torch
import pytest

from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b03 import study
from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import (
    exact_advantage_loss, make_conformance_fixture_model,
)


def test_weighted_learning_and_primary(monkeypatch, tmp_path):
    torch.set_num_threads(1)
    model = make_conformance_fixture_model()  # one non-scientific model, no RNG/native state
    old = torch.ones(4, dtype=torch.float64, requires_grad=True)
    noise = torch.ones(4, dtype=torch.float64, requires_grad=True)
    event, _, _ = model.event_plan(study.FLEX, old, torch.ones(68, dtype=torch.float64),
                                  torch.ones(5, dtype=torch.float64), noise)
    plan = model.manager_mean.bias.sum().reshape(1)
    claim = event.sum().reshape(1)
    y = torch.linspace(.1, .9, 64, dtype=torch.float64, requires_grad=True)
    base = torch.zeros(8, dtype=torch.float64, requires_grad=True)
    cells = torch.arange(8).repeat_interleave(8)
    p, a = [plan] * 64, [claim] * 64
    loss1 = study.weighted_loss(y, cells, base, p, a, 1)
    torch.testing.assert_close(loss1, exact_advantage_loss(y, cells, base, p, a))
    loss100 = study.weighted_loss(y, cells, base, p, a, 100)
    expected = -(y.detach() * (plan.mean() + 100 * claim.mean())).mean()
    torch.testing.assert_close(loss100, expected)
    loss100.backward()
    assert y.grad is None and base.grad is None and old.grad is None and noise.grad is None
    assert model.common_update_final.weight.grad.abs().sum() > 0
    assert model.agent_update_final.weight.grad.abs().sum() > 0
    # Observe real joint step before stopped baseline computation in reused helper.
    before = study.host.flat_parameters(model).clone()
    audit = study.apply_b02_block_update(model, base, y, cells, .02)
    assert torch.linalg.vector_norm(study.host.flat_parameters(model) - before).item() == pytest.approx(.02)
    torch.testing.assert_close(audit.block.updated_baselines, .05 * y.detach().reshape(8, 8).mean(1))
    assert not audit.block.updated_baselines.requires_grad
    # Exercise actual training caller with supplied score graphs: no scenario/RNG draw.
    calls = []
    def supplied(model, arm, rng, coords, training):
        calls.append((arm, coords, training))
        return [SimpleNamespace(Y=.5, U=.4, tau=40., F=0., agent_ticks=1, claim_decisions=1,
                                plan_scores=[model.manager_mean.bias.sum()],
                                claim_scores=[model.pointer_score.bias.sum()]) for _ in coords]
    monkeypatch.setattr(study, "execute_learned_batch", supplied)
    baseline, curve = study.training_update(model, SimpleNamespace(block_index=0), 0,
                                             torch.zeros(8, dtype=torch.float64), 100)
    assert [c[0] for c in calls] == [study.FLEX, study.FLEX]
    assert len({x.cell for c in calls for x in c[1]}) == 8
    assert curve["event_order"] == ["parameter_update", "baseline_update"]
    assert curve["training_episodes"] == 64
    assert curve["raw_gradient_norm"] == pytest.approx((4 * .5 ** 2 + 50 ** 2) ** .5)
    assert study.host.seed_root_key(f"{study.OBJECT_ID}/seed/{study.SEED}").hex() == "4b17629c25d71afceed93bbe657c0b5799d468d1f5673d90a7ceee644ec474c5"
    rows = [[dict(cell=cell, index=i, U=u + i*.01, Y=.5, tau=40., F=0.)
             for cell in study.host.HELDOUT_CELLS for i in range(4)] for u in (.8, .7, .5)]
    result = study.primary(rows[0], list(reversed(rows[1])), rows[2])
    assert result["Delta_U"] == pytest.approx(.2)
    assert result["G_U_W1"] == pytest.approx(.1)
    assert result["G_U_W100"] == pytest.approx(.3)
    assert len(result["active_paths"]) == 2
    study.host.write_json(tmp_path / "summary.json", dict(primary=result, **study.panel_summary(rows[1])))
    assert study.host.load_control_summary(tmp_path / "summary.json")["primary"]["positive_favors"] == "W100"
    damaged = [dict(r) for r in rows[2]]
    damaged[8]["index"] = 999
    # Explicit mismatch in a primary cell.
    for r in damaged:
        if r["cell"] == study.host.PRIMARY_CELLS[0]:
            r["index"] += 100
    with pytest.raises(ValueError, match="paired indices"):
        study.primary(rows[0], rows[1], damaged)
