import torch

from ha_ctse_process.assignment_actionability import (
    AssignmentActionabilityConfig,
    AssignmentActionabilityDiscriminator,
    empty_assignment_actionability_metrics,
    ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS,
)


def _synthetic_split(n=512, C=8, xi_dim=20, ctx_dim=6, seed=0, xi_carries_Z=True):
    """Train/eval split from a shared generative model so a noise-only prior cannot
    generalize (it can only memorize the train batch). Context is independent of Z."""
    g = torch.Generator().manual_seed(seed)
    code_means = torch.randn(C, xi_dim, generator=g)

    def make(m, gen):
        labels = torch.randint(0, C, (m,), generator=gen)
        context = torch.randn(m, ctx_dim, generator=gen)  # independent of labels
        if xi_carries_Z:
            xi = code_means[labels] + 0.5 * torch.randn(m, xi_dim, generator=gen)
        else:
            xi = torch.randn(m, xi_dim, generator=gen)  # carries no Z
        return xi, context, labels

    xi_tr, ctx_tr, y_tr = make(n, g)
    xi_ev, ctx_ev, y_ev = make(n, torch.Generator().manual_seed(seed + 999))
    prior = torch.full((C,), 1.0 / C)
    return (xi_tr, ctx_tr, y_tr), (xi_ev, ctx_ev, y_ev), prior


def _train(disc, tr, prior, steps=400, lr=1e-2):
    xi, ctx, y = tr
    opt = torch.optim.Adam(disc.parameters(), lr=lr)
    for _ in range(steps):
        opt.zero_grad()
        t = disc.losses(xi, ctx, y, prior)
        (t["loss_full"] + t["loss_prior"]).backward()
        opt.step()


def test_q_a_full_beats_prior_when_xi_carries_Z():
    tr, ev, prior = _synthetic_split(xi_carries_Z=True)
    disc = AssignmentActionabilityDiscriminator(xi_dim=20, context_dim=6, num_team_codes=8)
    _train(disc, tr, prior)
    t = disc.losses(*ev, prior)  # evaluate on held-out batch
    assert t["acc_full"].item() > t["acc_prior"].item() + 0.15
    assert t["residual_gain"].item() > 0.0
    assert float(t["residual"].mean()) > 0.0


def test_q_a_full_equals_prior_when_xi_is_noise():
    tr, ev, prior = _synthetic_split(xi_carries_Z=False)
    disc = AssignmentActionabilityDiscriminator(xi_dim=20, context_dim=6, num_team_codes=8)
    _train(disc, tr, prior)
    t = disc.losses(*ev, prior)  # held-out: neither head can recover Z
    assert t["acc_full"].item() < t["acc_prior"].item() + 0.10


def test_reward_is_clipped_and_nograd():
    (xi, ctx, labels), _ev, prior = _synthetic_split()
    disc = AssignmentActionabilityDiscriminator(xi_dim=20, context_dim=6, num_team_codes=8)
    r = disc.reward(xi, ctx, labels, prior, coef=0.05, clip=1.0)
    assert r.shape == (xi.shape[0],)
    assert not r.requires_grad
    assert float(r.abs().max()) <= 0.05 * 1.0 + 1e-6


def test_losses_inputs_are_detached_no_policy_grad():
    # xi/context arriving with grad must not receive gradient through the discriminator.
    (xi, ctx, labels), _ev, prior = _synthetic_split()
    xi = xi.clone().requires_grad_(True)
    ctx = ctx.clone().requires_grad_(True)
    disc = AssignmentActionabilityDiscriminator(xi_dim=20, context_dim=6, num_team_codes=8)
    t = disc.losses(xi, ctx, labels, prior)
    (t["loss_full"] + t["loss_prior"]).backward()
    assert xi.grad is None
    assert ctx.grad is None


def test_zero_context_dim_is_handled():
    n, C = 128, 8
    xi = torch.randn(n, 12)
    ctx = torch.zeros(n, 0)
    labels = torch.randint(0, C, (n,))
    prior = torch.full((C,), 1.0 / C)
    disc = AssignmentActionabilityDiscriminator(xi_dim=12, context_dim=0, num_team_codes=C)
    t = disc.losses(xi, ctx, labels, prior)
    assert torch.isfinite(t["loss_full"]) and torch.isfinite(t["loss_prior"])


def test_metric_fields_present():
    assert "q_a_residual_gain" in ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS
    m = empty_assignment_actionability_metrics()
    assert all(k in m for k in ASSIGNMENT_ACTIONABILITY_METRIC_FIELDS)


def test_config_from_config_reward_implies_probe():
    class C:
        enable_assignment_actionability_reward = True
    cfg = AssignmentActionabilityConfig.from_config(C())
    assert cfg.reward_on and cfg.probe_on
