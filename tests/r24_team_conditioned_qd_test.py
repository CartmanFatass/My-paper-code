import torch

from ha_ctse_process.team_conditioned_qd import (
    TEAM_CONDITIONED_QD_METRIC_FIELDS,
    TeamConditionedQDProbe,
    empty_team_conditioned_qd_metrics,
)


def _split(
    n: int = 512,
    num_skills: int = 6,
    effect_dim: int = 12,
    cond_dim: int = 10,
    seed: int = 3,
    effect_carries_skill: bool = True,
):
    g = torch.Generator().manual_seed(seed)
    means = torch.randn(num_skills, effect_dim, generator=g)

    def make(gen):
        labels = torch.randint(0, num_skills, (n,), generator=gen)
        condition = torch.randn(n, cond_dim, generator=gen)
        if effect_carries_skill:
            effect = means[labels] + 0.3 * torch.randn(n, effect_dim, generator=gen)
        else:
            effect = torch.randn(n, effect_dim, generator=gen)
        return effect, condition, labels

    return make(g), make(torch.Generator().manual_seed(seed + 999))


def _train(model, batch, steps: int = 300):
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    effect, cond, labels = batch
    for _ in range(steps):
        opt.zero_grad()
        losses = model.losses(effect, cond, labels)
        (losses["loss_full"] + losses["loss_prior"]).backward()
        opt.step()


def test_full_beats_prior_when_effect_carries_skill():
    train, eval_batch = _split(effect_carries_skill=True)
    model = TeamConditionedQDProbe(effect_dim=12, cond_dim=10, num_skills=6, hidden_dim=64)
    _train(model, train)
    out = model.losses(*eval_batch)
    assert out["acc_full"].item() > out["acc_prior"].item() + 0.15
    assert out["residual_gain"].item() > 0.0
    assert out["residual"].mean().item() > 0.0


def test_full_matches_prior_when_effect_is_noise():
    train, eval_batch = _split(effect_carries_skill=False)
    model = TeamConditionedQDProbe(effect_dim=12, cond_dim=10, num_skills=6, hidden_dim=64)
    _train(model, train)
    out = model.losses(*eval_batch)
    assert out["acc_full"].item() < out["acc_prior"].item() + 0.10


def test_inputs_are_detached_from_policy_graph():
    effect, cond, labels = _split(effect_carries_skill=True)[0]
    effect = effect.requires_grad_(True)
    cond = cond.requires_grad_(True)
    model = TeamConditionedQDProbe(effect_dim=12, cond_dim=10, num_skills=6, hidden_dim=64)
    out = model.losses(effect, cond, labels)
    (out["loss_full"] + out["loss_prior"]).backward()
    assert effect.grad is None
    assert cond.grad is None


def test_metric_fields_present():
    metrics = empty_team_conditioned_qd_metrics()
    assert "r24_qd_residual_gain" in TEAM_CONDITIONED_QD_METRIC_FIELDS
    assert all(k in metrics for k in TEAM_CONDITIONED_QD_METRIC_FIELDS)
