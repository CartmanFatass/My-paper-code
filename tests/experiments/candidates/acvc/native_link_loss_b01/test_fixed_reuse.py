import importlib.util
import json
from pathlib import Path
import time

import numpy as np
import pytest
import torch

from test_link_loss import PrivateFixture
from experiments.candidates.acvc.native_link_loss_b01.model import base_architecture, action_generators
from experiments.candidates.acvc.native_link_loss_b01.report import fixed_panel
from experiments.candidates.acvc.native_link_loss_b01 import learner


def test_fixed_commands_streams_and_publication(tmp_path, monkeypatch):
    for arm, index in (("C", 2), ("F", 3), ("dwell", 4)):
        assert action_generators(8911, arm, "eval", 7)[0].initial_seed() == 891130000 + 100 * index + 7
    base = base_architecture(8911).requires_grad_(False)
    monkeypatch.setattr(learner, "proposal_sample", lambda *args: (torch.ones(5, 3), torch.full((5, 3), .5)))
    for arm in ("F", "dwell"):
        env = PrivateFixture(1, horizon=4)
        inputs, commands, rows = [], [], []
        hook = base.register_forward_pre_hook(lambda module, args: inputs.append(args[0].clone()))
        step = env.step
        def capture(sent):
            commands.append(sent.copy())
            return step(sent)
        env.step = capture
        counts = dict.fromkeys(("explicit_resets", "base_agent_forwards", "learned_gate_agent_forwards", "step_calls", "team_steps", "eval_episodes"), 0)
        learner.collect(env, base, None, None, 8911, arm, "eval", 0, 4, lambda: None, counts, rows.append)
        hook.remove()
        for t in range(1, 4):
            np.testing.assert_array_equal(inputs[t][0, :, 104:107], commands[t-1])
        assert rows[0]["opportunities"] > 0
        if arm == "dwell":
            assert rows[0]["dwell"] == rows[0]["opportunities"] and rows[0]["retrace"] == 0
            assert any(np.all(command == 0) for command in commands)
        else:
            assert rows[0]["retrace"] == rows[0]["opportunities"]
            assert any(np.any(command < 0) for command in commands)
    monkeypatch.undo()
    rows = [dict(base=b, arm=a, episode=e, J=v + e * (0 if a == "C" else .02))
            for b in (8201, 8202) for a, v in (("C", 0), ("F", .03), ("dwell", .01)) for e in range(2)]
    result = fixed_panel(rows)
    assert result["8201"]["contrasts"]["F-C"]["mean_J"] == pytest.approx(.04)
    assert result["8201"]["contrasts"]["F-C"]["conditional_SE_J"] == pytest.approx(.01)
    assert result["8202"]["contrasts"]["F-dwell"]["mean_S"] == pytest.approx(5.12)
    script = Path(__file__).resolve().parents[5] / "scripts/run_acvc_fixed_retrace_reuse_e01.py"
    spec = importlib.util.spec_from_file_location("fixed_reuse_runner", script)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _: None)
    spec.loader.exec_module(module)
    checkpoint = tmp_path / "synthetic.pt"
    torch.save({"actor": base.state_dict()}, checkpoint)
    constructors = []
    def make_env(seed):
        constructors.append(seed)
        return PrivateFixture(seed, horizon=4)
    out = tmp_path / "output"
    assert module.run(out, {8201: checkpoint, 8202: checkpoint}, "synthetic", time.monotonic(), 20,
                      make_env=make_env, episodes=2, horizon=4) == 0
    saved = json.loads((out / "summary.json").read_text())
    assert constructors == [m * 100000 + 60 + a for m in (8911, 8912) for a in (2, 3, 4)]
    assert saved["counts"]["team_steps"] == 48 and saved["counts"]["eval_episodes"] == 12
    assert saved["counts"]["new_fits"] == saved["counts"]["optimizer_updates"] == 0
    assert saved["parameter_displacement_during_evaluation"] == 0
    assert len(saved["exposure_by_base_rule"]) == 6
    published = [json.loads(line) for line in (out / "episodes.jsonl").read_text().splitlines()]
    assert len(published) == 12
    for row in published:
        assert row["reset_seed"] == row["evaluation_namespace"] * 100000 + 2000 + row["episode"]
        assert row["J"] == pytest.approx(row["S"] / 4)
