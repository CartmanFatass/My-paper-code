"""Supplied-output check of W100 publication against a separate retained W1 file."""
import json
from pathlib import Path
import time
from types import SimpleNamespace
import torch
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b03 import study


def test_fresh_w100_uses_retained_control(monkeypatch, tmp_path):
    root = tmp_path / "new-attempt"
    control_path = tmp_path / "retained-W1.json"
    def rows(u):
        return [dict(cell=cell, index=i, U=u, Y=1-u, tau=40., F=.1)
                for cell in study.host.HELDOUT_CELLS for i in range(2)]
    control = dict(seed=22, launch_sha="original-source", status="COMPLETE",
                   initialization_panel=rows(.8), scenarios=rows(.6))
    control_path.write_text(json.dumps(control))
    retained_bytes = control_path.read_bytes()
    # A distinguishable local control must not replace the explicitly retained input.
    (root / "W1").mkdir(parents=True)
    (root / "W1/summary.json").write_text(json.dumps(dict(control, scenarios=rows(.9))))
    seeds, initialized, updates = [], [], []
    rng = SimpleNamespace(block_index=0)
    authority = SimpleNamespace(root_digest="supplied", certificate={"native": "not invoked"})
    def make_rng(seed):
        seeds.append(seed)
        return authority, rng
    monkeypatch.setattr(study, "make_rng", make_rng)
    model = SimpleNamespace(state_dict=lambda: {"supplied": torch.zeros(1, dtype=torch.float64)})
    def initialize(given_rng):
        initialized.append(given_rng)
        return {study.FLEX: model}
    monkeypatch.setattr(study, "initialize_block_models", initialize)
    monkeypatch.setattr(study.host, "flat_parameters", lambda model: torch.zeros(1, dtype=torch.float64))
    def update(model, given_rng, index, baselines, weight):
        assert given_rng is rng and weight == 100.
        assert baselines.tolist() == [float(index)] * 8
        updates.append(index)
        return baselines + 1, dict(update=index, training_episodes=64, nonzero=True)
    monkeypatch.setattr(study, "training_update", update)
    monkeypatch.setattr(study.host, "evaluate_learned", lambda *a, **k: (rows(.2), []))
    label = "RCLE-TBCFV-B03-ACTOR100-FRESH1000-S22-RECOVERY"
    result = study.run("W100", root / "W100", "new-source", tmp_path / "no-admission",
                       time.perf_counter(), 600, control_path, seed=22, updates=1000,
                       reporting_object=label)
    assert seeds == [22] and initialized == [rng] and updates == list(range(1000))
    assert result["status"] == "COMPLETE" and result["object"] == label
    assert result["counts"] == dict(training_episodes=64000, backward_step_calls=1000,
                                     nonzero_steps=1000, zero_steps=0, final_episodes=16,
                                     init_episodes=0)
    assert abs(result["paired_primary"]["Delta_U"] - .4) < 1e-12
    assert abs(result["paired_primary"]["G_U_W100"] - .6) < 1e-12
    assert control_path.read_bytes() == retained_bytes
    assert json.loads((root / "W100/summary.json").read_text()) == result
    wrapper = Path(__file__).resolve().parents[4] / "scripts/run_rcle_tbcfv_b03_fresh1000_s22_recovery.sh"
    commands = [line for line in wrapper.read_text().splitlines() if "admit-memory" in line]
    assert len(commands) == 2
    for command, arm, cap in zip(commands, ("W100", "reference"), (600, 30)):
        assert f"--arm {arm} " in command and f"timeout {cap} " in command
        assert "&&" in command and "|| exit $?" in command
        assert f"--seed 22 --updates 1000 --reporting-object {label}" in command
        assert "--arm W1 " not in command
    assert '--control-summary "$control"' in commands[0]
    assert "--control-summary" not in commands[1]
