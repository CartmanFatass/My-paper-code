"""Supplied-output check of real CLI/seed wiring and final primary publication."""
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
import torch
from experiments.candidates.roster_consistent_latent_exploration_tbcfv_b03 import study


@pytest.mark.parametrize("seed,updates,label,wrapper_name,root_hex", [
    (20, 200, "RCLE-TBCFV-B03-ACTOR100-S20", "run_rcle_tbcfv_b03_s20.sh",
     "065798a1a4115ac244accada16fc267f814deb622cfd05b9657418892c656e3b"),
    (21, 1000, "RCLE-TBCFV-B03-ACTOR100-FRESH1000-S21", "run_rcle_tbcfv_b03_fresh1000.sh",
     "f6a8584fe1948509b3501011e27178e8914f63fc794731e5d92b328415c7b6d8"),
])
def test_seed_and_new_control_publication(monkeypatch, tmp_path, seed, updates, label,
                                         wrapper_name, root_hex):
    path = Path(__file__).resolve().parents[4] / "scripts/run_rcle_tbcfv_b03.py"
    spec = importlib.util.spec_from_file_location("s20_cli_fixture", path)
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda n: None)
    monkeypatch.setattr(cli.signal, "signal", lambda *a: None)
    monkeypatch.setattr(cli.signal, "SIGALRM", 14, raising=False)
    monkeypatch.setattr(cli.signal, "ITIMER_REAL", 0, raising=False)
    monkeypatch.setattr(cli.signal, "setitimer", lambda *a: None, raising=False)
    seen = []
    def supplied_rng(authority, block, now):
        rng = SimpleNamespace(block_index=block, key=authority.root_digest)
        seen.append(rng)
        return rng
    monkeypatch.setattr(study, "SemanticRNG", supplied_rng)
    monkeypatch.setattr(study.host, "native_certificate_payload", lambda: {"fixture": True})
    def rows(u):
        return [dict(cell=cell, index=i, U=u, Y=1-u, tau=40., F=.1)
                for cell in study.host.HELDOUT_CELLS for i in range(2)]
    monkeypatch.setattr(study.host, "evaluate_scripted", lambda rng, n: rows(.1))
    def invoke(tag, arm="reference", seed=None, label=None, control=None, requested_updates=None):
        out = tmp_path / tag
        argv = [str(path), "--arm", arm, "--out", str(out), "--launch-sha", tag,
                "--admission-receipt", str(tmp_path / "supplied-no-admission")]
        if seed is not None: argv += ["--seed", str(seed)]
        if label is not None: argv += ["--reporting-object", label]
        if control is not None: argv += ["--control-summary", str(control)]
        if requested_updates is not None: argv += ["--updates", str(requested_updates)]
        monkeypatch.setattr(sys, "argv", argv)
        assert cli.main() == 0
        return json.loads((out / "summary.json").read_text())
    old = invoke("default19")
    explicit = invoke("explicit19", seed=19)
    fresh = invoke("fresh", seed=seed, label=label, requested_updates=updates)
    relabeled = invoke("different-sha-and-label", seed=seed, label="metadata-only")
    assert old["object"] == study.OBJECT_ID and old["seed"] == 19
    assert old["root_key_hex"] == explicit["root_key_hex"] == "4b17629c25d71afceed93bbe657c0b5799d468d1f5673d90a7ceee644ec474c5"
    assert fresh["root_key_hex"] == relabeled["root_key_hex"] == root_hex
    assert all(r["updates_per_fit"] == 0 for r in (old, explicit, fresh, relabeled))
    for result, rng in zip((old, explicit, fresh, relabeled), seen):
        expected = study.host.block_digest_hex(bytes.fromhex(result["root_key_hex"]), study.OBJECT_ID, 0)
        assert result["block_digest_hex"] == rng.key == expected
    assert seen[0].key == seen[1].key != seen[2].key == seen[3].key
    initialized, trained, evaluated = [], [], []
    model = SimpleNamespace(state_dict=lambda: {"supplied": torch.tensor([0.], dtype=torch.float64)})
    def initializer(rng):
        initialized.append(rng.key)
        return {study.FLEX: model}
    monkeypatch.setattr(study, "initialize_block_models", initializer)
    monkeypatch.setattr(study.host, "flat_parameters", lambda model: torch.zeros(1, dtype=torch.float64))
    def update(model, rng, update, baselines, weight):
        trained.append((rng.key, weight, update))
        assert baselines.tolist() == [0.] * 8
        return baselines, dict(update=update, training_episodes=64, nonzero=True)
    monkeypatch.setattr(study, "training_update", update)
    def evaluate(model, package, rng, n, **kwargs):
        evaluated.append((package, rng.key, n))
        return rows((.8, .6, .2)[len(evaluated)-1]), []
    monkeypatch.setattr(study.host, "evaluate_learned", evaluate)
    # The old pair omits the new argument, exercising the actual 200-update default.
    requested = None if updates == 200 else updates
    w1 = invoke("W1", "W1", seed, label, requested_updates=requested)
    old_control = dict(w1, seed=19, scenarios=rows(.9))
    (tmp_path / "old-W1.json").write_text(json.dumps(old_control))
    w100 = invoke("W100", "W100", seed, label, tmp_path / "W1/summary.json", requested)
    assert w1["seed"] == w100["seed"] == seed
    assert w1["updates_per_fit"] == w100["updates_per_fit"] == updates
    assert w1["object"] == w100["object"] == label
    assert initialized == [seen[2].key] * 2
    assert all(key == seen[2].key for key, weight, update in trained)
    assert [weight for key, weight, update in trained] == [1.] * updates + [100.] * updates
    assert [update for key, weight, update in trained] == list(range(updates)) * 2
    assert evaluated == [(study.FLEX, seen[2].key, 256)] * 3
    assert abs(w100["paired_primary"]["Delta_U"] - .4) < 1e-12
    wrong = study.primary(old_control["initialization_panel"], old_control["scenarios"], w100["scenarios"])
    assert abs(wrong["Delta_U"] - .7) < 1e-12
    assert w1["counts"]["backward_step_calls"] == w100["counts"]["backward_step_calls"] == updates
    for arm in ("W1", "W100"):
        blocks = [json.loads(line) for line in (tmp_path / arm / "completed_blocks.jsonl").read_text().splitlines()]
        assert [block["update"] for block in blocks] == list(range(updates))
    wrapper = (path.parent / wrapper_name).read_text()
    commands = [line for line in wrapper.splitlines() if "admit-memory" in line]
    assert len(commands) == 3
    for line, arm, cap in zip(commands, ("W1", "W100", "reference"), (600, 600, 30)):
        assert "&&" in line and "|| exit $?" in line
        assert f"--arm {arm} " in line and f"timeout {cap} " in line
        endpoint_arg = "" if updates == 200 else f"--updates {updates} "
        assert f"--seed {seed} {endpoint_arg}--reporting-object {label}" in line
    assert '--control-summary "$root/W1/summary.json"' in commands[1]
    assert sum("--control-summary" in line for line in commands) == 1
