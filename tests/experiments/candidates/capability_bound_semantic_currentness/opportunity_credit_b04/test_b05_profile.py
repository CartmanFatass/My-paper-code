"""Inert profile plumbing: no real host, model, optimizer or policy evaluation."""
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from experiments.candidates.capability_bound_semantic_currentness.opportunity_credit_b04 import run, learner
from experiments.candidates.capability_bound_semantic_currentness.omrc_b01.ppo import PPOCounters


@dataclass
class FixtureRecord:
    value: int = 0


@pytest.mark.parametrize("b05,engineering,seed", [(False, False, 21217), (False, True, 21211), (True, False, 21223)])
def test_profile_reaches_both_arms_and_publication(tmp_path, monkeypatch, b05, engineering, seed):
    calls = {key: [] for key in ("host", "model", "uniform", "rollout", "order", "minibatch", "native")}
    updates, panel = (1, 1) if engineering else (48, 32)

    class Host:
        def __init__(self, namespace, actual_seed):
            calls["host"].append((namespace, actual_seed))
        def build_stochastic(self, partition, episode):
            return SimpleNamespace(identity=[partition, episode], episode=episode,
                public_tokens=[SimpleNamespace(request_active=False) for _ in range(152)])

    class Model:
        active_parameter_count = 121349
        initialization_digest = "inert-model"
        def __init__(self, actual_seed, *, address_u64):
            calls["model"].append(actual_seed)
            assert address_u64 is run.addressing.u64
            self.parameter = torch.ones(1)
        def parameters(self):
            return [self.parameter]
        def state_dict(self):
            return {"fixture": self.parameter}

    actual_order = learner.ordered_episode_indices
    def order(namespace, actual_seed, update, epoch, **kwargs):
        calls["order"].append((namespace, actual_seed, update, epoch))
        return actual_order(namespace, actual_seed, update, epoch, **kwargs)

    class Trainer(learner.OpportunityTrainer):
        def __init__(self, model, *, run_name, seed, address_u64):
            self.model, self.run_name, self.seed = model, run_name, seed
            self.address_u64 = address_u64
            self.config = learner.OpportunityConfig()
            self.counters = PPOCounters()
            self._order_digest = "0" * 64
            self.optimizer = SimpleNamespace(state_dict=lambda: {"fixture": 0})
        def _train_minibatch(self, rollout, advantages, epoch, minibatch, selected):
            calls["minibatch"].append((self.seed, self.counters.rollout_updates, epoch, minibatch, selected))
            return FixtureRecord()

    def uniforms(tapes, namespace, actual_seed):
        calls["uniform"].append((namespace, actual_seed, len(tapes)))
        return None, "inert-uniforms", None

    def rollout(tapes, observations, model, *, run_name, seed):
        calls["rollout"].append((run_name, seed, [t.episode for t in tapes]))
        batch = SimpleNamespace(episode_ids=torch.tensor([t.episode for t in tapes]),
            rewards=torch.zeros(8, 152), old_values=torch.zeros(8, 152))
        evidence = {"actions": [{"decision_actions": ["SAFE_FALLBACK"] * 24} for _ in tapes],
            "rewards": [{"decision_rewards": [0.0] * 24, "settlement_rewards": [0.0] * 24} for _ in tapes]}
        return batch, evidence, "inert-uniforms"

    def native(tape, names):
        calls["native"].append(tape.identity)
        zero = {"numerator": 0, "denominator": 1, "float": 0.0}
        return {"identity": tape.identity, "actions": names, "native_return": zero,
            "decision_sum": zero, "settlement_sum": zero, "action_counts": {"SAFE_FALLBACK": 24}}

    monkeypatch.setattr(run, "DynamicHost", Host)
    monkeypatch.setattr(run, "CommonRecurrentActorCritic", Model)
    monkeypatch.setattr(run, "OpportunityTrainer", Trainer)
    monkeypatch.setattr(learner, "ordered_episode_indices", order)
    monkeypatch.setattr(run, "native_record", native)
    monkeypatch.setattr(run.engine, "_training_action_uniforms", uniforms)
    monkeypatch.setattr(run.engine, "_tape_primitive_digest", lambda tapes: str([t.identity for t in tapes]))
    monkeypatch.setattr(run.engine, "_project_panel", lambda tapes, adapter: (torch.zeros(len(tapes), 152, 168), FixtureRecord()))
    monkeypatch.setattr(run.engine, "_optimizer_digest", lambda trainer: "inert-optimizer")
    monkeypatch.setattr(run.engine, "_evaluate_heldout", lambda tapes, obs, model:
        ([{"decision_actions": ["SAFE_FALLBACK"] * 24} for _ in tapes], {}))
    monkeypatch.setattr(run.engine, "_rollout_from_panel", rollout)
    old_threads = torch.get_num_threads()
    try:
        raw = run.run_arm(arm=run.ARMS[0], seed=seed, output=tmp_path / "raw",
                          launch_sha="fixture-sha", engineering=engineering, b05=b05)
        raw_native_calls = len(calls["native"])
        structured = run.run_arm(arm=run.ARMS[1], seed=seed, output=tmp_path / "struct",
            launch_sha="fixture-sha", raw_result=tmp_path / "raw/summary.json", engineering=engineering, b05=b05)
    finally:
        torch.set_num_threads(old_threads)
    expected_object = run.B05_OBJECT if b05 else run.OBJECT
    assert calls["host"] == [(run.B1_RUN_NAME, seed)] * 2
    assert calls["model"] == [seed] * 2
    assert calls["uniform"] == [(run.B1_RUN_NAME, seed, updates * 8)] * 2
    assert len(calls["rollout"]) == 2 * updates
    assert all(namespace == run.B1_RUN_NAME and value == seed for namespace, value, _ in calls["rollout"])
    assert [ids for _, _, ids in calls["rollout"]] == [list(range(8*u, 8*u+8)) for u in range(updates)] * 2
    assert calls["order"] == [(run.B1_RUN_NAME, seed, u, e) for u in range(updates) for e in range(4)] * 2
    assert len(calls["minibatch"]) == 2 * updates * 16
    assert calls["minibatch"][:updates*16] == calls["minibatch"][updates*16:]
    assert raw_native_calls == 5 * panel  # three rules plus two evaluations
    assert len(calls["native"]) - raw_native_calls == 2 * panel  # STRUCT reuses rules
    for label, summary in (("raw", raw), ("struct", structured)):
        assert summary["object"] == expected_object and summary["seed"] == seed
        assert summary["counters"] == dict(rollout_updates=updates, adam_steps=updates*16,
            train_episodes=updates*8, train_transitions=updates*8*152, train_decisions=updates*192)
        assert summary["evaluation_executions"] == 2 * panel
        assert [x["update"] for x in summary["evaluations"]] == [0, updates]
        assert sum(summary["training_action_counts"].values()) == updates * 192
        assert ("python_executable" in summary["execution"]) == b05
        for update in (0, updates):
            snap = torch.load(tmp_path / label / f"update-{update}.pt", weights_only=True)
            assert (snap["object"], snap["seed"], snap["rng_namespace"]) == (expected_object, seed, run.B1_RUN_NAME)
            assert ("runtime" in snap["metadata"]) == b05
    pair = json.loads((tmp_path / "struct/paired_summary.json").read_text())
    assert (pair["object"], pair["seed"], pair["endpoint_update"]) == (expected_object, seed, updates)
    assert len(pair["differences"]) == panel
    assert pair["context"] == raw["context"] == structured["context"]
    for key, value in (("seed", seed + 1), ("object", "wrong-object"), ("evaluation_tape_digest", "wrong-tape")):
        with pytest.raises(ValueError, match=key):
            run.pair_results(raw, {**structured, key: value})


@pytest.mark.parametrize("engineering,b05,seed", [(False, False, 21223), (True, False, 21217), (False, True, 21217), (True, True, 21211)])
def test_arm_rejects_wrong_profile(tmp_path, engineering, b05, seed):
    # All rejection paths precede any host/model call; restore process-local threads.
    old_threads = torch.get_num_threads()
    try:
        with pytest.raises(ValueError):
            run.run_arm(arm=run.ARMS[0], seed=seed, output=tmp_path / "bad",
                        launch_sha="fixture", engineering=engineering, b05=b05)
    finally:
        torch.set_num_threads(old_threads)


@pytest.mark.parametrize("b05,engineering,seed,valid", [(False, False, 21217, True), (False, True, 21211, True),
    (True, False, 21223, True), (False, False, 21223, False), (True, False, 21217, False), (True, True, 21211, False)])
def test_cli_profile_dispatch(tmp_path, monkeypatch, capsys, b05, engineering, seed, valid):
    root = Path(__file__).resolve().parents[5]
    spec = importlib.util.spec_from_file_location("fixture_cli", root / "scripts/run_cbsc_opportunity_credit_b04.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    argv = ["fixture", "--seed", str(seed), "--output", str(tmp_path / "result")]
    argv += ["--engineering"] if engineering else ["--arm", run.ARMS[0]]
    if b05:
        argv.append("--b05")
    seen = []
    def fake_arm(**kw):
        seen.append(kw)
        return {"profile": "fixture", "counters": {"adam_steps": 16, "train_transitions": 1216}, "evaluation_transitions": 304}
    monkeypatch.setattr(cli.sys, "argv", argv)
    monkeypatch.setattr(cli, "run_arm", fake_arm)
    monkeypatch.setattr(cli.subprocess, "check_output", lambda *a, **k: "fixture-sha")
    monkeypatch.setattr(cli.runpy, "run_path", lambda *a: {"test_constructed_credit": lambda: None})
    if not valid:
        with pytest.raises(SystemExit) as error:
            cli.main()
        assert error.value.code == 2 and not seen
    else:
        cli.main()
        assert all(call["seed"] == seed for call in seen)
        assert all(call.get("b05", False) == b05 for call in seen)
        assert json.loads(capsys.readouterr().out)["object"] == (run.B05_OBJECT if b05 else run.OBJECT)
