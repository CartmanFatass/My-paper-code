"""B01 learner, calibration, orchestration and runner (sequential_coordinator_credit)."""

from __future__ import annotations

import json
import sys
import time

import numpy as np
import pytest

from experiments.candidates.sequential_coordinator_credit.b01 import calibration as cal
from experiments.candidates.sequential_coordinator_credit.b01 import chain_bandit as cb
from experiments.candidates.sequential_coordinator_credit.b01 import estimators as est
from experiments.candidates.sequential_coordinator_credit.b01 import first_cell as fc
from experiments.candidates.sequential_coordinator_credit.b01 import learner as ln
from scripts import run_sequential_coordinator_credit_b01 as entry

CORNER = cb.config_index(cb.BINDING_CORNER)
HOST = (0.9, 2, 0.2)
PACKAGE = "experiments.candidates.sequential_coordinator_credit"


def test_declared_learner_constants():
    assert (ln.SAMPLES_PER_CONTEXT, ln.PPO_EPOCHS, ln.MINIBATCH) == (64, 4, 256)
    assert (ln.LEARNING_RATE, ln.CLIP_EPS, ln.VALUE_RATE, ln.UPDATES) == (0.05, 0.2, 0.1, 300)
    assert ln.ENTROPY_SETTINGS == (("constant", 0.00125, 0.00125), ("annealed", 0.2, 0.01))
    assert ln.entropy_coefficient(1, 0, 300) == pytest.approx(0.2)
    assert ln.entropy_coefficient(1, 150, 300) == pytest.approx(0.105)
    assert ln.entropy_coefficient(0, 299, 300) == 0.00125
    assert (est.RIDGE_LAMBDA, est.N_CONTINUATIONS) == (0.01, 8)
    assert est.ARMS == ("E1", "E3", "E4", "E3*", "E4*")


def test_joint_normalisation_matches_hand_computation():
    A = np.array([[[1.0, 2.0], [3.0, 4.0]]])                                  # (1, 2, 2)
    team = np.array([[0.0, 5.0]])
    values = [1.0, 2.0, 3.0, 4.0, 0.0, 5.0]
    mean = sum(values) / 6                                                   # 2.5
    std = (sum((v - mean) ** 2 for v in values) / 5) ** 0.5 + 1e-8           # ddof = 1
    a_norm, t_norm, m, s = ln.joint_normalise(A, team)
    assert m == pytest.approx(2.5) and s == pytest.approx(std, rel=1e-15)
    np.testing.assert_allclose(a_norm, (A - 2.5) / std)
    np.testing.assert_allclose(t_norm, (team - 2.5) / std)


def test_ppo_gradient_matches_finite_differences():
    rng = np.random.default_rng(1)
    mask = cb.capability_mask(2)
    pmask = cb.prefix_mask(mask)
    theta = rng.normal(size=(3, cb.N_PREFIXES, cb.N_LABELS))
    P_old = cb.masked_softmax(theta, pmask)
    z = cb.sample_joints(P_old, 20, rng)                                       # (3, 20, K)
    x = np.repeat(np.arange(3), 20)
    rows = cb.prefix_rows(z).reshape(-1, cb.K)
    zf = z.reshape(-1, cb.K)
    adv = rng.normal(size=zf.shape)
    logp_old = ln.executed_log_probs(P_old, z).reshape(-1, cb.K)
    theta_new = theta + rng.normal(scale=0.3, size=theta.shape)               # some ratios clip
    for lam in (0.0, 0.2):
        _, grad = ln.ppo_loss_grad(theta_new, pmask, x, rows, zf, adv, logp_old, lam)
        allowed = np.argwhere(np.broadcast_to(pmask, theta.shape))
        touched = [tuple(a) for a in allowed if np.abs(grad[tuple(a)]) > 0][:30]
        assert touched
        for index in touched:
            h = 1e-6
            plus, minus = theta_new.copy(), theta_new.copy()
            plus[index] += h
            minus[index] -= h
            fd = (ln.ppo_loss_grad(plus, pmask, x, rows, zf, adv, logp_old, lam)[0]
                  - ln.ppo_loss_grad(minus, pmask, x, rows, zf, adv, logp_old, lam)[0]) / (2 * h)
            assert grad[index] == pytest.approx(fd, abs=1e-7)
        assert (grad[:, ~pmask] == 0).all()


def test_adam_matches_the_torch_update_rule():
    adam = ln.Adam((2,), lr=0.1)
    param = np.array([1.0, -1.0])
    grads = [np.array([0.5, -2.0]), np.array([0.1, 0.3])]
    m = v = np.zeros(2)
    expected = param.copy()
    for t, g in enumerate(grads, start=1):
        adam.step(param, g)
        m = 0.9 * m + 0.1 * g
        v = 0.999 * v + 0.001 * g * g
        expected = expected - (0.1 / (1 - 0.9 ** t)) * m / (np.sqrt(v) / np.sqrt(1 - 0.999 ** t)
                                                            + 1e-8)
    np.testing.assert_allclose(param, expected, rtol=0, atol=1e-15)


def test_training_is_bitwise_deterministic_and_uses_common_noise():
    task = ln.TrainingTask(CORNER, 1, 0, 3, 4, (0, 4))
    first, second = ln.train(task), ln.train(task)
    assert np.array_equal(first["J"], second["J"])
    assert all(np.array_equal(first["snapshots"][k], second["snapshots"][k]) for k in (0, 4))
    assert (first["regret"], first["final_J"]) == (second["regret"], second["final_J"])
    # same contexts across arms: J at update 0 (uniform policy) and J* agree across arms
    other = ln.train(ln.TrainingTask(CORNER, 2, 1, 3, 1))
    assert other["J"][0] == first["J"][0] and other["J_star"] == first["J_star"]
    assert (first["snapshots"][0] == 0).all()


def test_e1_regret_decreases_on_the_binding_s1_configuration():
    index = cb.config_index((0.9, 1, 0.0))
    result = ln.train(ln.TrainingTask(index, 0, 0, 1, 60))
    gap = result["J_star"] - result["J"]
    assert gap[-10:].mean() < 0.5 * gap[:10].mean()
    assert gap[-1] < gap[0]


def test_batch_e4_matches_the_exact_removal_difference():
    contexts, _ = cb.make_contexts(CORNER, 2)
    P = cb.masked_softmax(np.random.default_rng(3).normal(size=(16, 85, 4)),
                          cb.prefix_mask(contexts.mask))
    rng = np.random.default_rng(4)
    z = cb.sample_joints(P, 8, rng)
    d = cb.noisy_demands(contexts.d[:, None], rng.standard_normal((16, 8, 2)), 0.2)
    R = cb.reward(d, contexts.q[:, None], z, contexts.mask, contexts.b0)
    e4 = ln.batch_advantages("E4", P, contexts, z, d, R, None, rng)
    rtab = cb.reward_table(d, contexts.q, contexts.mask, contexts.b0)
    exact = est.removal_difference(rtab, cb.joint_index(z)[..., None])[:, :, 0]
    np.testing.assert_allclose(e4, exact, atol=1e-15)
    e3s = ln.batch_advantages("E3*", P, contexts, z, d, R, None, rng)
    np.testing.assert_allclose(e3s.sum(-1), R - cb.prefix_values(cb.suffix_products(P),
                                                                  rtab)[0][..., 0], atol=1e-12)


def test_calibration_sweep_structure():
    sweep = cal.calibration_sweep()
    assert len(sweep["table"]) == 24 and sweep["seed"] == cal.CALIBRATION_SEED
    for row in sweep["table"]:
        assert row["noise_draws"] == (32 if row["sigma"] > 0 else 1)
        if row["delta"] is not None:
            assert row["delta"] == pytest.approx(sum(r["scaled_squared"]
                                                     for r in row["residuals"].values()))
        assert set(row["pairwise"]) == set(cal.PAIR_CLASSES)
    for policy in cal.POLICIES:
        best = sweep["argmin"][policy]
        rows = [r for r in sweep["table"] if r["policy"] == policy and r["delta"] is not None]
        assert best["delta"] == min(r["delta"] for r in rows)
    # beta = 0: a relay never changes R, so its removal difference is 0
    zero = [r for r in sweep["table"] if r["beta"] == 0.0 and r["policy"] == "uniform"]
    assert all(r["S4"] == 0.0 for r in zero)


# ----------------------------------------------------------------------------- runner

def test_runner_arguments():
    args = entry.parse_args(["first-cell", "--out", "o", "--launch-sha", "s",
                             "--host-matched", "0.9,2,0.2"])
    assert (args.seeds, args.updates, args.workers, args.host_matched) == (100, 300, 8,
                                                                            (0.9, 2, 0.2))
    assert entry.parse_args(["calibrate", "--out", "o", "--launch-sha", "s"]).command == \
        "calibrate"
    for bad in (["first-cell", "--out", "o", "--launch-sha", "s"],
                ["first-cell", "--out", "o", "--launch-sha", "s", "--host-matched", "0.9,2"],
                ["calibrate", "--out", "o"], ["calibrate", "--launch-sha", "s"]):
        with pytest.raises(SystemExit):
            entry.parse_args(bad)


def test_runner_admission_precedes_candidate_imports(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    def refuse(*args, **kwargs):
        raise RuntimeError("no admission")

    for name in [name for name in sys.modules if name.startswith(PACKAGE)]:
        monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    target = tmp_path / "never-created"
    for argv in (["calibrate", "--out", str(target), "--launch-sha", "s"],
                 ["first-cell", "--out", str(target), "--launch-sha", "s",
                  "--host-matched", "0.9,2,0.2"]):
        with pytest.raises(RuntimeError, match="no admission"):
            entry.main(argv)
    assert not target.exists()
    assert not [name for name in sys.modules if name.startswith(PACKAGE)]
    order = []
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *args, **kwargs: order.append(("admission", kwargs)) or {"sha": "s"})
    monkeypatch.setattr(fc, "run_first_cell", lambda **kwargs: order.append(kwargs) or {})
    monkeypatch.setitem(sys.modules, fc.__name__, fc)
    entry.main(["first-cell", "--out", str(target), "--launch-sha", "s", "--seeds", "3",
                "--updates", "7", "--workers", "2", "--host-matched", "0.9,2,0.2"])
    assert order[0] == ("admission", {"direction": "sequential_coordinator_credit"})
    assert {k: v for k, v in order[1].items() if k != "argv"} == {
        "out": target, "launch_sha": "s", "seeds": 3, "updates": 7, "workers": 2,
        "host_matched": (0.9, 2, 0.2)}
    with pytest.raises(RuntimeError, match="admission"):
        entry.main(["first-cell", "--out", str(target), "--launch-sha", "other",
                    "--host-matched", "0.9,2,0.2"])


def test_first_cell_refuses_bad_configurations_and_existing_output(tmp_path):
    for host in ((0.9, 1, 0.2), (0.7, 1, 0.2)):
        target = tmp_path / f"bad_{host[0]}_{host[1]}"
        with pytest.raises(ValueError):
            fc.run_first_cell(out=target, launch_sha="s", seeds=1, updates=1, workers=1,
                              host_matched=host)
        assert not target.exists()
    with pytest.raises(ValueError):
        fc.run_first_cell(out=tmp_path / "w", launch_sha="s", seeds=1, updates=1, workers=10 ** 4,
                          host_matched=HOST)
    existing = tmp_path / "run"
    (existing / fc.PHASE).mkdir(parents=True)
    (existing / fc.PHASE / "summary.json").write_text("{}")
    with pytest.raises(FileExistsError):
        fc.run_first_cell(out=existing, launch_sha="s", seeds=1, updates=1, workers=1,
                          host_matched=HOST)


def _arrays(path):
    with np.load(path) as data:
        return {key: data[key] for key in data.files if key != "training_wall_seconds"}


def test_seed_reproduces_in_isolation_and_across_pool(tmp_path):
    one = fc.run_first_cell(out=tmp_path / "one", launch_sha="s", seeds=1, updates=2, workers=1,
                            host_matched=HOST)
    two = fc.run_first_cell(out=tmp_path / "two", launch_sha="s", seeds=2, updates=2, workers=2,
                            host_matched=HOST)
    assert one["status"] == two["status"] == "COMPLETE"
    a, b = _arrays(tmp_path / "one" / fc.PHASE / "regret.npz"), \
        _arrays(tmp_path / "two" / fc.PHASE / "regret.npz")
    assert set(a) == set(b)
    for key, value in a.items():
        if key in ("seeds", "config_indices", "snapshots"):
            continue
        if key == "J_curve":
            other = b[key][:, :, :, :1]
        elif key == "J_star":
            other = b[key][:, :1]
        else:                                    # seed is the last axis
            other = b[key][..., :1]
        assert np.array_equal(value, other, equal_nan=True), key


def test_tiny_end_to_end_through_the_runner(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "sha-e2e"})
    out = tmp_path / "e2e"
    started = time.perf_counter()
    summary = entry.main(["first-cell", "--out", str(out), "--launch-sha", "sha-e2e",
                          "--seeds", "2", "--updates", "5", "--workers", "2",
                          "--host-matched", "0.9,2,0.2"])
    print(f"tiny end-to-end wall {time.perf_counter() - started:.1f} s")
    root = out / fc.PHASE
    for name in ("config.json", "summary.json", "progress.jsonl", "regret.npz"):
        assert (root / name).is_file(), name
    written = json.loads((root / "summary.json").read_text())
    config = json.loads((root / "config.json").read_text())
    assert summary["status"] == written["status"] == "COMPLETE" and written["failure"] is None
    counts = written["counts"]
    assert (counts["started_trainings"], counts["completed_trainings"]) == (40, 40)
    assert (counts["updates_per_training"], counts["seeds"], counts["snapshot_readings"]) == \
        (5, 2, 8)
    assert counts["training_wall_seconds_total"] > 0 and counts["reading_wall_seconds_total"] > 0
    assert written["snapshots_read"] == [0] and written["snapshots_absent"] == [40, 200]
    for key in ("readings", "regret", "E4_minus_E3_binding_corner", "artifacts",
                "configurations", "seeds"):
        assert key in written, key
    rule = written["E4_minus_E3_binding_corner"]
    assert set(rule) == {"constant", "annealed"}
    assert all(set(rule[label]["regret"]) == {"mean", "se", "n"} and rule[label]["regret"]["n"]
               == 2 for label in rule)
    reading = written["readings"]["binding_corner"]["constant"]["update_0"]
    assert set(reading["arms"]) == set(est.ARMS)
    assert set(reading["arms"]["E3"]["native"]) >= {"cosine", "projection", "variance",
                                                    "cosine_se", "projection_se"}
    regret = written["regret"]["host_matched"]
    assert (regret["beta"], regret["s"], regret["sigma"]) == (0.9, 2, 0.2)
    assert set(regret["entropy"]["annealed"]["arms"]) == set(est.ARMS)
    assert "E4-E3" in regret["entropy"]["annealed"]["paired_differences"]
    assert config["launch_sha"] == "sha-e2e" and config["seeds"] == [1, 2]
    assert [c["config_index"] for c in config["training_configurations"]] == \
        [CORNER, cb.config_index(HOST)]
    events = [json.loads(line)["event"] for line in (root / "progress.jsonl").read_text()
              .splitlines()]
    assert events[0] == "run_start" and events[-1] == "run_end"
    assert events.count("seed_end") == 2 and "readings_start" in events and \
        "readings_end" in events
    import hashlib
    assert written["artifacts"]["regret.npz"] == hashlib.sha256(
        (root / "regret.npz").read_bytes()).hexdigest()
    with np.load(root / "regret.npz") as data:
        assert data["J_curve"].shape == (2, 5, 2, 2, 6)
        assert data["reading__native__cosine"].shape == (2, 2, 1, 5, 2)
        assert np.isfinite(data["regret"]).all()


def test_calibrate_end_to_end_through_the_runner(tmp_path, monkeypatch):
    from scripts import hmasd_admission

    monkeypatch.setattr(hmasd_admission, "require_admission", lambda *a, **k: {"sha": "sha-c"})
    out = tmp_path / "cal"
    summary = entry.main(["calibrate", "--out", str(out), "--launch-sha", "sha-c"])
    written = json.loads((out / "calibrate" / "summary.json").read_text())
    assert summary["status"] == written["status"] == "COMPLETE"
    assert written["counts"]["started_trainings"] == 0
    assert set(written) >= {"table", "argmin", "pairwise", "targets", "scales"}
    assert (out / "calibrate" / "config.json").is_file()
