from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.skill_information_refresh.c05.host import (
    FixedHost, RESTRICTED, RULES, Worlds, rule,
)
from experiments.candidates.skill_information_refresh.c05.study import Config, run_study


def test_context_is_charged_delivered_and_future_draw_is_not_in_view():
    worlds = Worlds.exact()
    host = FixedHost(worlds)
    view = host.prepare()
    altered = FixedHost(replace(worlds, flip_draw=9 - worlds.flip_draw))
    other_view = altered.prepare()
    assert np.array_equal(view.features(), other_view.features())
    assert np.array_equal(view.received_weight, host.context_packet[:, 0])
    assert view.features().shape == (180, 3)
    assert np.array_equal(host.context_packet[:, 1:], np.tile([4, 2, 4, 0, 0, 0], (180, 1)))
    assert (host.context_arrival == 1).all()
    for name in RULES:
        assert np.array_equal(rule(name, view), rule(name, other_view))


@pytest.mark.parametrize("early", [True, False])
def test_exact_packet_bytes_delay_budget_and_fixed_receiver_actions(early):
    worlds = Worlds.exact()
    host = FixedHost(worlds)
    host.prepare()
    reward, trace = host.rollout(np.full(180, early, dtype=bool))
    assert (trace["packets"] == 2).all() and (trace["bytes"] == 11).all()
    assert (trace["sent"][:, 0, 0]).all() and (trace["delivered"][:, 1, 0]).all()
    assert (trace["data_packet"][:, 1] == (1 if early else 3)).all()
    assert (trace["data_arrival"] == (2 if early else 4)).all()
    assert (trace["receiver_cache"][:, :2] == 0).all()
    future = worlds.condition ^ (worlds.flip_draw < worlds.risk_tenths)
    assert np.array_equal(trace["receiver_actions"][:, 0], worlds.condition if early else np.zeros(180))
    assert np.array_equal(trace["receiver_actions"][:, 1], worlds.condition if early else future)
    expected = worlds.weight + 4 * (worlds.flip_draw >= worlds.risk_tenths) if early else (
        worlds.weight * (worlds.condition == 0) + 4)
    assert np.array_equal(reward, expected)
    with pytest.raises(RuntimeError):
        host.rollout(np.full(180, early, dtype=bool))


def test_exhaustive_values_and_matched_information_value_reversal():
    worlds = Worlds.exact()
    scores, results = {}, {}
    for name in RULES:
        host = FixedHost(worlds)
        view = host.prepare()
        reward, trace = host.rollout(rule(name, view))
        scores[name] = reward.mean()
        results[name] = reward.reshape(18, 10).mean(axis=1)
    assert max(scores[name] for name in RESTRICTED) == pytest.approx(5.)
    assert scores["VOI"] == pytest.approx(5 + 5.8 / 18)
    assert np.allclose(results["VOI"], np.maximum(results["PRE_FIRST"], results["PRE_LAST"]))
    assert np.allclose(results["PRE_FIRST"] - results["PRE_LAST"], view.delta_tenths()[::10] / 10)
    choices = rule("VOI", view)
    assert not choices[(worlds.condition == 1) & (worlds.weight == 1) & (worlds.risk_tenths == 5)].any()
    assert choices[(worlds.condition == 1) & (worlds.weight == 3) & (worlds.risk_tenths == 5)].all()
    # Exactly the same cache innovation can therefore require opposite transmission times.
    assert all(np.unique(rule(name, view)[worlds.condition == 1]).size == 1 for name in RESTRICTED)


def test_zero_obsolescence_falsifier_removes_value_residual():
    worlds = Worlds.exact(zero_risk=True)
    scores = {}
    for name in RULES:
        host = FixedHost(worlds)
        view = host.prepare()
        scores[name] = host.rollout(rule(name, view))[0].mean()
    assert scores["VOI"] == scores["AGE_CHANGE"] == 6.
    assert scores["VOI"] - max(scores[name] for name in RESTRICTED) == 0


def test_worlds_are_seeded_and_phase_separated():
    first, same, other = Worlds.make(73160, 0, 128), Worlds.make(73160, 0, 128), Worlds.make(73160, 2, 128)
    for field in ("condition", "weight", "risk_tenths", "flip_draw"):
        assert np.array_equal(getattr(first, field), getattr(same, field))
        assert not np.array_equal(getattr(first, field), getattr(other, field))
    assert np.array_equal(first.take(7, 20).ids, np.arange(7, 20))


def test_small_fixture_training_counts_primary_and_exact_output(tmp_path):
    out = tmp_path / "result"
    config = Config(seed=5, train_cycles=32, batch=16, epochs=2, final_cycles=8)
    summary = run_study(out, "a" * 40, config)
    assert summary["status"] == "COMPLETE"
    assert summary["counts"] == dict(started_fits=1, train_cycles=32, train_transitions=192,
        optimizer_steps=4, eval_cycles=1668, eval_transitions=10008, evaluation_optimizer_steps=0)
    assert summary["parameters"]["displacement"] > 0
    assert summary["parameters"]["evaluation_displacement"] == 0
    assert summary["primary_reference"] == "VOI"
    assert summary["comparisons"]["final_exact"]["voi_minus_best_restricted"] == pytest.approx(5.8 / 18)
    assert summary["comparisons"]["zero_risk_exact"]["voi_minus_best_restricted"] == 0
    rows = [json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()]
    assert len(rows) == 1668 and all(r["packets"] == 2 and r["bytes"] == 11 for r in rows)
    assert len((out / "updates.jsonl").read_text().splitlines()) == 4
    training = np.load(out / "training_LEARNED.npz")
    assert np.array_equal(training["world_ids"], np.arange(32))
    assert (training["bytes"] == 11).all() and (training["packets"] == 2).all()
    checkpoint = torch.load(out / "final.pt", weights_only=True)
    assert checkpoint["launch_sha"] == "a" * 40 and checkpoint["config"] == summary["config"]
    assert len(summary["contexts"]) == 18
    for phase in ("final", "final_exact", "zero_risk_exact"):
        learned = np.load(out / f"{phase}_LEARNED.npz")
        baseline = np.load(out / f"{phase}_VOI.npz")
        assert np.array_equal(learned["world_ids"], baseline["world_ids"])
        assert np.array_equal(learned["flip_draw"], baseline["flip_draw"])
        difference = learned["utility"] - baseline["utility"]
        assert summary["comparisons"][phase]["learned_minus_voi"] == float(difference.mean())
        assert summary["comparisons"][phase]["learned_minus_voi_total"] == int(difference.sum())
    with pytest.raises(FileExistsError):
        run_study(out, "a" * 40, config)


def test_cli_refuses_without_admission(tmp_path):
    root = Path(__file__).resolve().parents[5]
    out = tmp_path / "unadmitted"
    result = subprocess.run([sys.executable, str(root / "scripts/run_sir_c05.py"),
        "--out", str(out), "--launch-sha", "a" * 40], cwd=root,
        capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "missing HMASD admission" in result.stderr
    assert not out.exists()
