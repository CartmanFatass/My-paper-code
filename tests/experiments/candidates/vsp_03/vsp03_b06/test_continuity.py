"""Exercise orchestration with literal fake work; no scientific construction."""
import json
from types import SimpleNamespace
import numpy as np
import pytest
from experiments.candidates.vsp_03.vsp03_b06 import b06


def test_paired_change_uses_world_pairing():
    early = [{"world": i, "phase_zero_identity": i % 2, "G_greedy-R0": float(i)}
             for i in range(1024)]
    late = [{**r, "G_greedy-R0": r["G_greedy-R0"] + (i % 2)} for i, r in enumerate(early)]
    rows, result = b06.paired_budget_change(early, late)
    assert result["mean"] == .5
    assert result["conditional_world_sd"] == pytest.approx(np.sqrt(256 / 1023))
    assert result["conditional_world_se"] == result["conditional_world_sd"] / 32
    assert rows[1]["b"] == 1


@pytest.mark.parametrize("fail_at", [None, 129])
def test_continuous_driver_and_partial_publication(monkeypatch, tmp_path, fail_at):
    calls, panels, saved = [], [], {}
    state = SimpleNamespace(step=0, backward=0, model_count=0, optim_count=0)
    class Tensor:
        def __init__(self, value): self.value = value
        def detach(self): return self
        def clone(self): return Tensor(self.value)
    class Model:
        def __init__(self, seed, arm):
            assert (seed, arm) == (10801, "G")
            state.model_count += 1
        def parameters(self): return self
        def state_dict(self): return {"w": Tensor(state.step)}
    class Optimizer:
        def __init__(self, model, **kwargs):
            state.optim_count += 1
            self.model = model
            assert kwargs == dict(lr=.001, betas=(.9,.999), eps=1e-8, weight_decay=0)
        def zero_grad(self, **kwargs): pass
        def step(self): state.step += 1
    class Loss:
        def backward(self): state.backward += 1
    def worlds(seed, split, first, count):
        calls.append((seed, split, first, count))
        return (split, first, count), np.zeros(count, dtype=int)
    def actions(seed, split, mode, arm, first, count):
        return (seed, split, mode, arm, first, count)
    def rollout(draws, phase, model=None, uniforms=None, rule="R0", **kwargs):
        assert kwargs["deadline"] == 50
        if draws[0] == 100:
            assert draws[1] == state.step * 128
            assert uniforms == (10801,100,0,1,state.step*128,128)
            if state.step + 1 == fail_at: raise RuntimeError("literal injected failure")
        else:
            assert not b06.torch.is_grad_enabled()
            assert state.step in (128,512)
            assert saved[f"G_{state.step}.pt"]["w"].value == state.step
            panels.append((state.step, id(draws), id(phase), id(model), uniforms, rule))
        n = draws[2]
        return {"rows": [{"return": float(state.step if model else 0)} for _ in range(n)],
                "decision_rows": n}
    def objective(model, batch, update):
        assert update == state.step + 1
        return Loss(), {}
    monkeypatch.setattr(b06, "peak_rss", lambda: 0)
    monkeypatch.setattr(b06, "Model", Model)
    monkeypatch.setattr(b06.torch.optim, "Adam", Optimizer)
    for name, function in [("worlds",worlds),("action_tapes",actions),("rollout",rollout),
                           ("objective",objective),("vectors",lambda m: None),
                           ("scales",lambda m,i: {"step":state.step}),
                           ("metrics",lambda rows: {"episodes":len(rows)})]:
        monkeypatch.setattr(b06,name,function)
    monkeypatch.setattr(b06.torch,"set_num_threads",lambda n: None)
    monkeypatch.setattr(b06.torch,"set_num_interop_threads",lambda n: None)
    monkeypatch.setattr(b06.torch,"save",lambda s,p: saved.update({p.name:s}))
    monkeypatch.setattr(b06.torch,"load",lambda p,**kwargs: saved[p.name])
    monkeypatch.setattr(b06.torch,"equal",lambda a,b: a.value == b.value)
    monkeypatch.setattr(b06.time,"perf_counter",lambda: 0)
    if fail_at:
        with pytest.raises(RuntimeError,match="literal injected failure"):
            b06.run(10801,tmp_path,"sha",0,"wsl_4070","literal")
    else:
        b06.run(10801,tmp_path,"sha",0,"wsl_4070","literal")
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert state.model_count == state.optim_count == 1
    assert state.step == state.backward == (128 if fail_at else 512)
    assert len((tmp_path / "G_curve.jsonl").read_text().splitlines()) == state.step
    assert json.loads((tmp_path / "checkpoint_128.json").read_text())["status"] == "complete"
    assert saved["G_128.pt"]["w"].value == 128
    assert len(panels) == (4 if fail_at else 8)
    assert len({p[1] for p in panels}) == len({p[2] for p in panels}) == 1
    assert len({p[3] for p in panels if p[5] == "R0" and p[4] is not None}) == 1
    assert calls[0] == (10801,200,0,1024)
    if fail_at:
        assert summary["status"] == "incomplete" and "primary" not in summary
    else:
        assert saved["G_512.pt"]["w"].value == 512
        assert summary["primary"]["mean"] == 512
        assert summary["budget_change"]["mean"] == 384
        assert summary["budget_change"]["conditional_world_sd"] == 0
        assert summary["arms"]["G"]["evaluation_episodes"] == 8192
        assert panels[1][4] == panels[5][4] == (10801,200,1,1,0,1024)
