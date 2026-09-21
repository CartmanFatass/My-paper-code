"""Native literal accounting and admission/orchestration, without research fits."""

import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.candidates.vsp_03.opportunity_b08 import study
from experiments.candidates.vsp_03.vsp03_b02.b02 import rollout


def test_final_clock_blocking_and_failed_occupancy():
    tapes = np.full((2, 40, 2), .99)
    tapes[0, 24, 0] = 0.  # A service failure still occupies through t32.
    phase = np.array([0, 1])
    batch = rollout(tapes, phase, scripted=lambda ids, t, own, x: np.full(len(ids), t == 24),
                    trace=True)
    rows, _ = study.annotate_rows(batch, phase)
    for row in rows:
        assert row["submit_blocks_partner_next_clock"] == 1
        assert row["submit_blocks_partner_last_clock"] == 1
        assert row["blocked_final_clocks"] == 1
        assert row["jobs"][1 - row["phase_zero_identity"]]["non_submission"] == 1
    assert sum(j["success"] for j in rows[0]["jobs"]) == 0
    assert sum(j["success"] for j in rows[1]["jobs"]) == 1
    assert rows[0]["return"] == (-10 - 24 - 40) / 400
    assert rows[1]["return"] == (200 - 10 - 24 - 40) / 400


def test_own_last_clock_expiry_and_t32_no_future_partner():
    tapes = np.full((1, 40, 2), .99)
    tapes[0, 31, 0] = 0.
    batch = rollout(tapes, np.array([0]),
                    scripted=lambda ids, t, own, x: np.full(len(ids), t == 32), trace=True)
    rows, _ = study.annotate_rows(batch, np.array([0]))
    assert rows[0]["expired_at_own_clock"] == 1
    assert rows[0]["submit_when_not_ready"] == 1
    assert rows[0]["submit_blocks_partner_next_clock"] == 0
    assert rows[0]["submit_blocks_partner_last_clock"] == 0


def test_admission_refuses_before_science_or_output(tmp_path):
    root = Path(__file__).resolve().parents[5]
    output = tmp_path / "refused"
    proc = subprocess.run([sys.executable, str(root / "scripts/run_vsp03_opportunity_b08.py"),
                           "--seeds", "21801", "21802", "21803", "--launch-sha", "a" * 40,
                           "--out", str(output)], cwd=root, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "admission" in proc.stderr.lower()
    assert not output.exists()


def test_first_disagreement_uses_common_prefix_and_retains_both_directions():
    x = np.zeros((4, 14), dtype=np.float32)
    x[:, 11] = 1
    base = {"x": x, "episode_ids": np.array([0, 1, 0, 1]), "times": np.array([0, 0, 2, 2])}
    joint = {**base, "actions": np.array([0, 0, 0, 1])}
    alone = {**base, "actions": np.array([0, 0, 1, 0])}
    rows = [{"return": .1}, {"return": .2}]
    result = study.first_coupling_disagreements(joint, alone, rows, rows)
    assert result[0]["first_disagreement"]["direction"] == "joint_WAIT_self_SUBMIT"
    assert result[1]["first_disagreement"]["direction"] == "joint_SUBMIT_self_WAIT"
    assert all(r["first_disagreement"]["t"] == 2 for r in result)
    corrupted = {**alone, "x": x.copy()}
    corrupted["x"][0, 1] = 1
    with pytest.raises(AssertionError, match="before first"):
        study.first_coupling_disagreements(joint, corrupted, rows, rows)


@pytest.mark.parametrize("fail_at", [None, 3])
def test_driver_preserves_g_and_separates_fit_eval(monkeypatch, tmp_path, fail_at):
    state = SimpleNamespace(step=0, backward=0, models=0, fits=0, evals=0)
    class Tensor:
        def __init__(self, value): self.value = value
        def detach(self): return self
        def clone(self): return Tensor(self.value)
    class Model:
        def __init__(self, seed, arm):
            assert (seed, arm) == (21801, "G")
            state.models += 1
        def parameters(self): return self
        def state_dict(self): return {"w": Tensor(state.step)}
    class Optimizer:
        def __init__(self, model, **kwargs):
            assert kwargs == dict(lr=.001, betas=(.9,.999), eps=1e-8, weight_decay=0)
        def zero_grad(self, **kwargs): pass
        def step(self): state.step += 1
    class Loss:
        def backward(self): state.backward += 1
    class Counts:
        counts = np.zeros((41, 42, 42), dtype=np.int64)
        def add_batch(self, batch):
            assert set(batch) == {"x", "episode_ids", "times"}
    def fit_model(counts):
        assert state.step == 512 and state.evals == 0
        state.fits += 1
        return {"c": 5., "p": .4, "metadata": {"success": True, "message": "synthetic"}}
    def worlds(seed, split, first, count):
        if split == 200:
            assert state.step == 512 and state.fits == 1
        return np.array([split, first, count]), np.zeros(count, dtype=int)
    def fake_rollout(draws, phase, model=None, uniforms=None, **kwargs):
        split, first, n = draws
        if split == 100:
            assert first == state.step * 128
            assert uniforms == (21801,100,0,1,first,128)
            if state.step + 1 == fail_at:
                raise RuntimeError("literal injected failure")
        else:
            assert state.step == 512
            state.evals += 1
        active = kwargs["activity"]
        active["episodes_started"] += int(n)
        active["episodes_completed"] += int(n)
        active["team_ticks"] += int(n) * 40
        active["target_transitions"] += int(n) * 80
        return {"rows": [{"return": float(model is not None)} for _ in range(n)],
                "decision_rows": int(n), "x": None, "actions": None, "episode_ids": None, "times": None}
    saved = {}
    for name, value in (("Model", Model), ("EndpointCounts", Counts), ("fit_model", fit_model),
                        ("worlds", worlds), ("rollout", fake_rollout),
                        ("action_tapes", lambda *args: args),
                        ("objective", lambda *args: (Loss(), {})),
                        ("vectors", lambda m: None), ("scales", lambda m, i: {"step": state.step}),
                        ("metrics", lambda rows: {"episodes": len(rows)}),
                        ("Planner", lambda c, p: SimpleNamespace(
                            solo=np.zeros((33,42)), joint=np.zeros((33,42,42)))),
                        ("first_coupling_disagreements", lambda *args: []),
                        ("save_panel", lambda out, name, batch, phase: (batch["rows"], {}))):
        monkeypatch.setattr(study, name, value)
    monkeypatch.setattr(study.torch.optim, "Adam", Optimizer)
    monkeypatch.setattr(study.torch, "save", lambda s, p: saved.update({p.name: s}))
    monkeypatch.setattr(study.torch, "load", lambda p, **kw: saved[p.name])
    monkeypatch.setattr(study.torch, "equal", lambda a, b: a.value == b.value)
    target = tmp_path / "block"
    if fail_at:
        with pytest.raises(RuntimeError, match="literal injected failure"):
            study.train_and_evaluate(21801, target, "sha")
    else:
        study.train_and_evaluate(21801, target, "sha")
    summary = json.loads((target / "summary.json").read_text())
    assert state.models == 1
    assert state.step == state.backward == (2 if fail_at else 512)
    assert len((target / "G_curve.jsonl").read_text().splitlines()) == state.step
    assert summary["fits_started"] == {"G": 1, "O": 0 if fail_at else 1}
    assert summary["status"] == ("incomplete" if fail_at else "complete")
    assert state.evals == (0 if fail_at else 7)
