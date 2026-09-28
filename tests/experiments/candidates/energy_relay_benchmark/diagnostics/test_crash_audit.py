"""Opt-in crash audit: off by default, records when on, bitwise inert for the b05 collector."""

from __future__ import annotations

import copy
import gc
import json
import sys
from dataclasses import replace

import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b02 import configuration as cfg
from experiments.candidates.energy_relay_benchmark.b05 import training as tr
from experiments.candidates.energy_relay_benchmark.diagnostics import crash_audit as ca

ON = {ca.ENV_VAR: "1", ca.INTERVAL_VAR: "0", ca.WATCHDOG_VAR: "0"}
TIMING = {"collection_seconds", "update_seconds"}
MODULES = ("skill_coordinator", "skill_discoverer", "team_discriminator",
           "individual_discriminator")


@pytest.fixture(autouse=True)
def _clean_audit():
    ca.uninstall()
    yield
    ca.uninstall()


def _records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_off_unless_exactly_one(tmp_path):
    callbacks, hook = list(gc.callbacks), sys.excepthook
    for environ in ({}, {ca.ENV_VAR: "0"}, {ca.ENV_VAR: ""}, {ca.ENV_VAR: "true"}):
        assert ca.install_from_environment(tmp_path, environ=environ) is None
    assert gc.callbacks == callbacks and sys.excepthook is hook
    assert not any(tmp_path.iterdir())


def test_on_samples_refcounts_and_chains_the_excepthook(tmp_path, monkeypatch, capfd):
    seen = []
    monkeypatch.setattr(sys, "excepthook", lambda *exc: seen.append(exc[0]))
    import envs.pettingzoo.relay.energy_aware  # noqa: F401  (the path objects resolve lazily)
    import numpy.core.fromnumeric  # noqa: F401

    config = ca.install_from_environment(tmp_path, environ=ON)
    assert config["interval_s"] == 0 and config["watchdog_s"] == 0 and not config["force_gc"]
    gc.collect()
    sys.excepthook(SystemError, SystemError("probe"), None)
    assert seen == [SystemError]
    ca.uninstall()
    assert sys.excepthook is not ca._excepthook
    side = tmp_path / "logs" / "crash-audit"
    records = _records(side / "audit.jsonl")
    events = [row["event"] for row in records]
    assert events[0] == "install" and "periodic" in events and events[-1] == "uncaught_exception"
    periodic = next(row for row in records if row["event"] == "periodic")
    names = set(periodic["refcounts"])
    assert "numpy.core.fromnumeric._wrapit" in names
    assert any(name.startswith("_spectral_efficiency.co_consts") and "-40.0" in name
               for name in names)
    assert periodic["allocated_blocks"] > 0 and len(periodic["gc_collections"]) == 3
    assert records[-1]["type"] == "SystemError" and records[-1]["message"] == "probe"
    assert "Current thread" in (side / "faulthandler.log").read_text(encoding="utf-8") or \
        "Thread" in (side / "faulthandler.log").read_text(encoding="utf-8")
    capfd.readouterr()   # _debugmallocstats went to the C stderr


def test_watchdog_must_exceed_interval(tmp_path):
    with pytest.raises(ValueError, match="must exceed"):
        ca.install(tmp_path, environ={ca.INTERVAL_VAR: "300", ca.WATCHDOG_VAR: "60"})
    assert not ca._STATE


def _tiny():
    spec = tr.B05Spec(seed=317763, rollouts=2, rollout_length=25, episode_length=40,
                      hidden_size=32, gru_hidden_size=32, ppo_epochs=1,
                      checkpoint_every_transitions=50, canonical="sw")
    config = cfg.make_b02_config(spec)
    config.initial_battery_ratio_range = (0.03, 0.03)
    return spec, config


def test_audit_on_is_bitwise_inert_for_the_b05_collector(tmp_path):
    torch.set_num_threads(1)
    spec, config = _tiny()
    outputs = []
    for label in ("off", "on"):
        if label == "on":
            ca.install(tmp_path / "audit", environ={**ON, ca.FORCE_GC_VAR: "0"})
        agent, _ = tr.b02_training.new_agent(copy.deepcopy(config), device=torch.device("cpu"),
                                             log_dir=tmp_path / label / "logs", seed=spec.seed)
        result = tr.collect_and_train_canonical(agent, agent.config, spec, feedback=True)
        outputs.append((agent, result))
        if label == "on":
            samples = ca._STATE["samples"]
            ca.uninstall()
    assert samples > 0
    (off_agent, off), (on_agent, on) = outputs
    for name in MODULES:
        left, right = getattr(off_agent, name), getattr(on_agent, name)
        assert (left is None) == (right is None)
        if left is None:
            continue
        for key, value in left.state_dict().items():
            torch.testing.assert_close(value, right.state_dict()[key], rtol=0, atol=0)
    assert off["counts"] == on["counts"]
    strip = lambda rows: [{k: v for k, v in row.items() if k not in TIMING} for row in rows]
    assert strip(off["rollouts"]) == strip(on["rollouts"])


def test_runner_hook_is_gated_by_the_environment(tmp_path, monkeypatch):
    import scripts.hmasd_admission
    from experiments.candidates.energy_relay_benchmark.b05 import run_b05

    calls = []
    monkeypatch.setattr(scripts.hmasd_admission, "require_admission",
                        lambda *a, **k: {"sha": "abc"})
    monkeypatch.setattr(tr, "production_spec", lambda seed: "spec")
    monkeypatch.setattr(tr, "run_training", lambda **kwargs: kwargs["out"])
    monkeypatch.setattr(ca, "install_from_environment", lambda out: calls.append(out))
    argv = ["train", "--seed", "925031", "--launch-sha", "abc", "--out", str(tmp_path / "t")]
    for value in (None, "0", "yes"):
        if value is None:
            monkeypatch.delenv(ca.ENV_VAR, raising=False)
        else:
            monkeypatch.setenv(ca.ENV_VAR, value)
        assert run_b05.main(argv) == tmp_path / "t"
    assert calls == []
    monkeypatch.setenv(ca.ENV_VAR, "1")
    run_b05.main(argv)
    assert calls == [tmp_path / "t"]
    assert not any(tmp_path.iterdir())


def test_defaults_sample_every_300_s_without_watchdog(tmp_path):
    config = ca.install_from_environment(tmp_path, environ={ca.ENV_VAR: "1"})
    assert (config["interval_s"], config["watchdog_s"], config["force_gc"]) == (300.0, 0.0, False)
