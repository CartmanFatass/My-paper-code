import json
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.metric_ground_transport_allocation.mgtap_late_exposure_b01 import protocol as p
from experiments.candidates.metric_ground_transport_allocation.mgtap_late_exposure_b01 import study as s


def panel_rows(early=.02, late=-.02):
    return [dict(object=p.OBJECT, pair_master=p.MASTER, learning_rate=p.LEARNING_RATE,
                 phase="eval", arm=arm, episode=e, steps=256, train_endpoint=endpoint,
                 J=delta if arm == "COND" else 0., **p.randomization("eval", e))
            for endpoint, delta in ((256, early), (512, late)) for arm in p.ARMS for e in range(32)]


@pytest.mark.parametrize("late,reading", [(.02, "COND_ABOVE_MEI"), (-.02, "COND_ADVERSE"),
                                        (.01, "INSIDE_MEI"), (-.01, "INSIDE_MEI")])
def test_final512_primary_never_chooses_favorable_midpoint(late, reading):
    result = p.primary(panel_rows(.2, late))
    assert result["delta_J"] == late
    assert result["reading"] == reading
    assert result["secondary_late_minus_early_delta_J"] == pytest.approx(late - .2)
    assert p.planned_exposure()["total"]["total_team_ticks"] == 294912
    assert p.planned_exposure()["total"]["adam_calls"] == 2048


@pytest.mark.parametrize("damage", ["missing_mid", "duplicate_final", "wrong_master", "wrong_rng", "unknown_endpoint"])
def test_primary_rejects_mixed_or_missing_observations(damage):
    rows = panel_rows()
    if damage == "missing_mid":
        rows.pop(0)
    elif damage == "duplicate_final":
        rows.append(rows[-1].copy())
    elif damage == "wrong_master":
        rows[-1]["pair_master"] = 8253
    elif damage == "wrong_rng":
        rows[-1]["velocity_seed"] += 1
    else:
        rows[-1]["train_endpoint"] = 384
    with pytest.raises(ValueError):
        p.primary(rows)


def install_synthetic_path(monkeypatch, fail_final=False):
    envs, optimizers, train_draws, eval_draws, identities = [], [], [], [], []

    def make_env(seed):
        env = SimpleNamespace(seed=seed)
        envs.append(env)
        return env

    def optimizer(actor, critic, lr):
        opt = torch.optim.Adam([*actor.parameters(), *critic.parameters()], lr=lr)
        optimizers.append(opt)
        return opt

    def collect(env, actor, critic, horizon, reset_seed, velocity_rng, duration_rng,
                metadata, check, counts, emit_episode, emit_diagnostic, limits, **kwargs):
        phase, e = metadata["phase"], metadata["episode"]
        identities.append((phase, id(env), id(velocity_rng), metadata.get("train_endpoint")))
        draw = torch.rand((), generator=velocity_rng).item()
        (train_draws if phase == "train" else eval_draws).append(draw)
        counts[f"{phase}_episodes"] += 1
        counts[f"{phase}_team_steps"] += horizon
        counts["team_steps"] += horizon
        if fail_final and metadata.get("train_endpoint") == 512 and e == 10:
            raise RuntimeError("synthetic final collector interruption")
        emit_episode(dict(metadata, reset_seed=reset_seed, steps=horizon, J=actor.weight.item()))
        return {"synthetic": True}

    def update(actor, critic, opt, episodes, chunk, check, counts, **kwargs):
        for _ in range(4):
            opt.zero_grad()
            ((actor.weight - 1).square().sum() + (critic.weight - 2).square().sum()).backward()
            opt.step()
            counts["optimizer_steps"] += 1
        return [{"synthetic": True}] * 4

    monkeypatch.setattr(s.base, "make_real", make_env)
    monkeypatch.setattr(s.base, "_optimizer", optimizer)
    monkeypatch.setattr(s.base, "collect_episode", collect)
    monkeypatch.setattr(s.base, "update", update)
    monkeypatch.setattr(s.base, "geometry_snapshot", lambda a, c: a.weight.detach().clone())
    monkeypatch.setattr(s.base, "geometry_exposure", lambda initial, a, c: {
        "synthetic_displacement": (a.weight.detach() - initial).norm().item()})
    return envs, optimizers, train_draws, eval_draws, identities


def models():
    a, c = torch.nn.Linear(1, 1, bias=False), torch.nn.Linear(1, 1, bias=False)
    with torch.no_grad():
        a.weight.zero_()
        c.weight.zero_()
    return a, c


def test_midpoint_preserves_optimizer_training_stream_and_publication(monkeypatch, tmp_path):
    envs, opts, train, evaluation, identities = install_synthetic_path(monkeypatch)
    rows, rollouts, partial = [], [], []
    fit = s.native_fit("COND", models(), tmp_path, rows.append, rollouts.append,
                       s.time.monotonic(), partial.append)
    assert len(envs) == 2 and len(opts) == 1 and not partial
    assert {record[1] for record in identities if record[0] == "train"} == {id(envs[0])}
    assert {record[1] for record in identities if record[0] == "eval"} == {id(envs[1])}
    expected_rng = s.base.generator(100000 * p.MASTER + 21)
    assert train == [torch.rand((), generator=expected_rng).item() for _ in range(512)]
    assert evaluation[:32] == evaluation[32:]
    assert [ep["train_endpoint"] for ep in fit["endpoints"]] == [256, 512]
    assert fit["counts"]["optimizer_steps"] == 1024
    assert fit["counts"]["train_episodes"] == 512 and fit["counts"]["eval_episodes"] == 64
    for endpoint, steps in ((256, 512), (512, 1024)):
        checkpoint = torch.load(tmp_path / f"COND_{endpoint}.pt", weights_only=True)
        assert checkpoint["train_endpoint"] == endpoint
        assert all(value["step"].item() == steps for value in checkpoint["optimizer"]["state"].values())
        assert checkpoint["optimizer"]["param_groups"][0]["lr"] == 1e-4


def test_partial_final_keeps_midpoint_and_counts_without_starting_dense(monkeypatch, tmp_path):
    envs, opts, *_ = install_synthetic_path(monkeypatch, fail_final=True)
    summary = s.run_study(tmp_path, "a" * 40, pair_factory=lambda master: {arm: models() for arm in p.ARMS})
    assert summary["status"] == "INCOMPLETE" and summary["primary"] is None
    assert len(opts) == 1 and len(envs) == 2
    partial = summary["partial_fits"][0]
    assert partial["counts"]["optimizer_steps"] == 1024
    assert partial["counts"]["train_episodes"] == 512 and partial["counts"]["eval_episodes"] == 43
    assert partial["phase"] == "evaluation512"
    assert partial["endpoints"][0]["checkpoint"] == "COND_256.pt"
    assert (tmp_path / "COND_256.pt").exists() and not (tmp_path / "DENSE_256.pt").exists()
    assert json.loads((tmp_path / "summary.json").read_text()) == summary


def test_complete_two_arm_output_roundtrip(monkeypatch, tmp_path):
    install_synthetic_path(monkeypatch)
    summary = s.run_study(tmp_path, "b" * 40, pair_factory=lambda master: {arm: models() for arm in p.ARMS})
    assert summary["status"] == "COMPLETE" and not summary["limits"]
    assert summary["raw_episode_rows"] == 1152 and summary["raw_rollout_rows"] == 512
    assert summary["primary"]["primary_endpoint"] == 512
    assert summary["primary"]["reading"] == "INSIDE_MEI"
    assert len(list(tmp_path.glob("*.pt"))) == 4
    assert json.loads((tmp_path / "summary.json").read_text()) == summary
