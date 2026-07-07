import torch

from ha_ctse_process.team_conditioned_qd import (
    TEAM_CONDITIONED_QD_METRIC_FIELDS,
    TeamConditionedQDConfig,
    TeamConditionedQDProbe,
    empty_team_conditioned_qd_metrics,
)


def _synthetic_split(
    n=512,
    num_skills=6,
    effect_dim=14,
    condition_dim=5,
    seed=0,
    effect_carries_label=True,
):
    generator = torch.Generator().manual_seed(seed)
    effect_means = torch.randn(num_skills, effect_dim, generator=generator)

    def make(count, gen):
        labels = torch.randint(0, num_skills, (count,), generator=gen)
        condition = torch.randn(count, condition_dim, generator=gen)
        if effect_carries_label:
            effect = effect_means[labels] + 0.35 * torch.randn(count, effect_dim, generator=gen)
        else:
            effect = torch.randn(count, effect_dim, generator=gen)
        return effect, condition, labels

    train = make(n, generator)
    eval_ = make(n, torch.Generator().manual_seed(seed + 1000))
    return train, eval_


def _train(probe, batch, steps=250, lr=5e-3):
    effect, condition, labels = batch
    optimizer = torch.optim.Adam(probe.parameters(), lr=lr)
    for _ in range(steps):
        optimizer.zero_grad()
        terms = probe.losses(effect, condition, labels)
        (terms["loss_full"] + terms["loss_prior"]).backward()
        optimizer.step()


def test_full_classifier_beats_prior_when_effect_carries_skill_label():
    torch.manual_seed(10)
    train, eval_ = _synthetic_split(effect_carries_label=True, seed=11)
    probe = TeamConditionedQDProbe(effect_dim=14, condition_dim=5, num_skills=6, hidden_dim=48)

    _train(probe, train)
    terms = probe.losses(*eval_)

    assert terms["acc_full"].item() > terms["acc_prior"].item() + 0.20
    assert terms["residual_gain"].item() > 0.0
    assert terms["residual_mean"].item() > 0.0
    assert terms["positive_frac"].item() > 0.60


def test_full_classifier_does_not_strongly_beat_prior_when_effect_is_noise():
    torch.manual_seed(20)
    train, eval_ = _synthetic_split(effect_carries_label=False, seed=21)
    probe = TeamConditionedQDProbe(effect_dim=14, condition_dim=5, num_skills=6, hidden_dim=48)

    _train(probe, train)
    terms = probe.losses(*eval_)

    assert terms["acc_full"].item() < terms["acc_prior"].item() + 0.12
    assert terms["residual_gain"].item() < 0.12


def test_losses_detach_effect_condition_and_labels_from_policy_graph():
    torch.manual_seed(30)
    effect, condition, labels = _synthetic_split(seed=31)[0]
    effect = effect.clone().requires_grad_(True)
    condition = condition.clone().requires_grad_(True)
    probe = TeamConditionedQDProbe(effect_dim=14, condition_dim=5, num_skills=6, hidden_dim=32)

    terms = probe.losses(effect, condition, labels)
    (terms["loss_full"] + terms["loss_prior"]).backward()

    assert effect.grad is None
    assert condition.grad is None


def test_metric_field_names_are_r24_qd_prefixed_and_empty_metrics_match():
    assert TEAM_CONDITIONED_QD_METRIC_FIELDS
    assert all(name.startswith("r24_qd_") for name in TEAM_CONDITIONED_QD_METRIC_FIELDS)

    metrics = empty_team_conditioned_qd_metrics()

    assert set(metrics) == set(TEAM_CONDITIONED_QD_METRIC_FIELDS)
    assert all(value == 0.0 for value in metrics.values())


def test_default_config_is_probe_off():
    class EmptyConfig:
        pass

    cfg = TeamConditionedQDConfig.from_config(EmptyConfig())

    assert not cfg.probe_on

