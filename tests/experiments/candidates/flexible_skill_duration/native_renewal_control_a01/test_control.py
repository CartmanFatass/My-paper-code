"""Bounded A01 engineering checks: fake trajectories, synthetic state, fake clock."""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location("fsd_a01", ROOT / "scripts/run_fsd_native_renewal_control_a01.py")
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


class Adapter:
    num_envs = 2
    n_agents = 2
    config = SimpleNamespace(horizon=3, n_roles=2, delta=1.)

    def __init__(self):
        self.resets = 0
        self.applied = []
        self.host = SimpleNamespace(
            change_flag=np.zeros((2, 2), dtype=int), region_of_agent=np.arange(2),
            zone_of_agent=np.arange(2), cue=np.zeros((2, 2), dtype=int),
            n_roles=2, batch_size=2, n_agents=2)

    def reset(self):
        self.resets += 1
        self.t = 0
        return np.full((2, 2, 1), 7.), {"state": np.full((2, 1), 11.)}

    def step(self, actions, renew_mask):
        self.applied.append(renew_mask.copy())
        fresh = np.array([[True, True], [False, True]])
        correct = np.array([[True, False], [True, False]])
        reward = ((~renew_mask) & fresh & correct).sum(1) / 2.
        self.t += 1
        self.host.change_flag[:] = [1, 0] if self.t == 1 else [0, 0]
        future = renew_mask.sum(1).astype(float) + self.t
        return np.broadcast_to(future[:, None, None], (2, 2, 1)).copy(), reward, self.t == 3, False, {
            "state": future[:, None], "shared_reward": reward, "renew_mask": renew_mask.copy(),
            "lease_fresh": fresh, "role_correct": correct,
            "state_info": {"lease_fresh": ~fresh},  # Deliberately wrong scoring source.
        }


class Controller:
    def __init__(self):
        self.inputs = []
        self.resets = []
        self.clears = 0
        self.data = []

    def train(self, mode):
        assert mode is False

    def clear_buffers(self):
        self.clears += 1

    def reset_env_state(self, lane):
        self.resets.append(lane)

    def step(self, states, observations, env_steps, dones, **kwargs):
        assert kwargs == dict(deterministic=True, return_step_data=True, build_infos=False)
        assert states.dtype == np.float64 and observations.dtype == np.float32
        assert not dones.any()
        self.inputs.append((states.copy(), observations.copy(), env_steps.copy()))
        step = {"d2_sampled_mask": np.full((2, 2), len(self.inputs) == 1)}
        self.data.append(step)
        return np.zeros((2, 2, 2)), None, step


def run_fake(policy):
    adapter = Adapter()
    controller = r.GreedyOnPublicState() if policy == "G" else Controller()
    config = r.RelayCorridorConfig(n_agents=2, horizon=3, delta=1.)
    summary = r.base_summary(policy, config, 2, 770103, "TEST", True)
    r.evaluate(policy, adapter, controller, summary, r.time.perf_counter(), fixture=True)
    return summary, adapter, controller


def test_mask_copy_and_step_data():
    internal = np.array([[True, False]])
    public = ~internal
    for policy, t, expected in (("C", 0, internal), ("C", 2, internal),
                                ("H", 0, internal), ("H", 2, public)):
        result = r.apply_renew_mask(policy, internal, public, t)
        np.testing.assert_array_equal(result, expected)
        assert not np.shares_memory(result, internal) and not np.shares_memory(result, public)
        result[:] = False
    np.testing.assert_array_equal(internal, [[True, False]])
    np.testing.assert_array_equal(public, [[False, True]])


def test_fresh_state_feedback_and_scoring():
    c, ca, cc = run_fake("C")
    h, ha, hc = run_fake("H")
    for adapter, controller in ((ca, cc), (ha, hc)):
        assert adapter.resets == controller.clears == 1
        assert controller.resets == [0, 1]
        np.testing.assert_array_equal(controller.inputs[0][0], [[11.], [11.]])
        np.testing.assert_array_equal(controller.inputs[0][1], np.full((2, 2, 1), 7.))
        assert [x[2].tolist() for x in controller.inputs] == [[0, 0], [1, 1], [2, 2]]
        assert [d["d2_sampled_mask"].all() for d in controller.data] == [True, False, False]
    # H acts on flag at t=1, before this step changes it to zero.
    np.testing.assert_array_equal(ha.applied[1], [[True, False], [True, False]])
    assert not ha.applied[2].any()
    assert not np.array_equal(cc.inputs[2][0], hc.inputs[2][0])
    assert not np.array_equal(cc.inputs[2][1], hc.inputs[2][1])
    np.testing.assert_allclose(c["return_full"], [1/3, 0])
    np.testing.assert_allclose(c["return_post"], [.5, 0])
    assert c["eligible_full"] == c["eligible_post"] == [4, 2]
    assert c["wrong_full"] == c["wrong_post"] == [2, 2]
    np.testing.assert_allclose(c["role_loss_full"], [1/3, 1/3])
    np.testing.assert_allclose(c["role_loss_post"], [.5, .5])
    assert c["wrong_rate_post"] == [.5, 1.]
    assert h["eligible_post"] == [3, 2]
    assert h["internal_renew_full"] == [2, 2]
    assert h["applied_renew_full"] == [3, 3]
    assert h["internal_renew_post"] == [0, 0]
    assert h["applied_renew_post"] == [1, 1]


def test_g_reset_null_rate_and_pairing(monkeypatch):
    resets = []
    original = r.GreedyOnPublicState.reset
    def reset(self, host):
        resets.append(host)
        original(self, host)
    monkeypatch.setattr(r.GreedyOnPublicState, "reset", reset)
    g, adapter, _ = run_fake("G")
    assert len(resets) == 1 and not adapter.applied[0].any()
    assert g["internal_renew_full"] is None
    assert g["return_full"] == [1/3, 0]
    assert g["return_post"] == [.25, 0]
    class AlwaysRenew(Controller):
        def step(self, *args, **kwargs):
            actions, infos, data = super().step(*args, **kwargs)
            data["d2_sampled_mask"][:] = True
            return actions, infos, data
    c = copy.deepcopy(g)
    c["policy"] = "C"
    c["counts"] = dict.fromkeys(r.COUNT_KEYS, 0)
    r.evaluate("C", Adapter(), AlwaysRenew(), c, r.time.perf_counter(), fixture=True)
    assert c["wrong_rate_full"] == c["wrong_rate_post"] == [None, None]
    h = copy.deepcopy(g)
    h["policy"] = "H"
    c["return_full"], h["return_full"], g["return_full"] = [0., .2], [.2, .6], [.6, .8]
    c["return_post"], h["return_post"], g["return_post"] = [.1, .2], [.4, .3], [.5, .9]
    policies = dict(G=g, C=c, H=h)
    panel = r.summarize_panel(policies)
    for key, expected in {"h_minus_c_full": [.2, .4], "h_minus_c_post": [.3, .1],
                          "g_minus_h_full": [.4, .2], "g_minus_h_post": [.1, .6]}.items():
        np.testing.assert_allclose(panel["paired"][key]["differences"], expected)
        assert panel["paired"][key]["mean"] == pytest.approx(np.mean(expected))
        assert panel["paired"][key]["stderr"] == pytest.approx(abs(expected[1] - expected[0]) / 2)
    for key, bad in (("episode_ids", [1, 0]), ("master_seed", 99), ("host", {"H": 99}),
                     ("status", "incomplete")):
        mismatched = copy.deepcopy(policies)
        mismatched["H"][key] = bad
        with pytest.raises(ValueError):
            r.summarize_panel(mismatched)
    mismatched = copy.deepcopy(policies)
    mismatched["H"]["counts"]["scoring_steps"] -= 1
    with pytest.raises(ValueError):
        r.summarize_panel(mismatched)


@pytest.fixture
def synthetic(monkeypatch):
    config = SimpleNamespace(num_envs=16, use_obsnorm=False, use_statenorm=False,
                             use_valuenorm=True, n_Z=6, d2_setting="unchanged")
    payload = {"config": config}
    for name in r.MODULES:
        payload[name] = {"weight": torch.full((1, 1), 3.)}
    payload["valuenorm_state"] = {name: {"mean": np.array([.3], dtype=np.float64),
        "var": np.array([.7], dtype=np.float64), "count": np.float64(43.)}
        for name in ("coordinator", "discoverer")}
    made, loads = [], []
    class Agent:
        def __init__(self, config, device, log_dir):
            self.config = config
            self.device = device
            self.log_dir = log_dir
            for name in r.MODULES:
                setattr(self, name, torch.nn.Linear(1, 1, bias=False))
            self.ha_ctse_editor = None
            for name in ("coordinator", "discoverer"):
                setattr(self, "value_norm_" + name,
                        SimpleNamespace(mean=np.zeros(1), var=np.ones(1), count=np.float64(0)))
            self.optimizer = SimpleNamespace(step=lambda: pytest.fail("optimizer.step called"))
            made.append(self)
        def train(self, mode):
            assert mode is False
    def load(path, **kwargs):
        loads.append((path, kwargs))
        return payload
    monkeypatch.setitem(sys.modules, "run_flexible_skill_duration_e2", SimpleNamespace(E2CorridorConfig=type(config)))
    monkeypatch.setitem(sys.modules, "hmasd.agent", SimpleNamespace(HMASDAgent=Agent))
    monkeypatch.setattr(torch, "load", load)
    return payload, made, loads


def test_strict_restore(synthetic, tmp_path):
    payload, made, loads = synthetic
    before = copy.deepcopy(payload)
    counts = dict.fromkeys(r.COUNT_KEYS, 0)
    agent, facts = r.load_controller(tmp_path / "synthetic.pt", tmp_path, 32, r.time.perf_counter(), counts)
    assert len(loads) == len(made) == 1
    assert loads[0][1] == {"map_location": "cpu", "weights_only": False}
    assert vars(agent.config) == {**vars(before["config"]), "num_envs": 32}
    assert vars(payload["config"]) == vars(before["config"])
    assert agent.config is not payload["config"] and agent.device.type == "cpu"
    assert agent.log_dir == str(tmp_path / "agent")
    assert agent.ha_ctse_editor is None and "ha_ctse_editor" not in facts["restored_modules"]
    for name in facts["restored_modules"]:
        assert torch.equal(getattr(agent, name).weight, payload[name]["weight"])
    for name in ("coordinator", "discoverer"):
        for field in ("mean", "var", "count"):
            actual = getattr(getattr(agent, "value_norm_" + name), field)
            expected = before["valuenorm_state"][name][field]
            np.testing.assert_array_equal(actual, expected)
            assert np.asarray(actual).dtype == np.asarray(expected).dtype
    assert counts["checkpoint_loads"] == counts["model_constructions"] == 1
    assert counts["optimizer_steps"] == 0


@pytest.mark.parametrize("broken", ["network_missing", "network_shape", "stats_missing", "stat_missing", "stat_shape"])
def test_restore_rejects_required_missing_or_mismatch(synthetic, tmp_path, broken):
    payload, _, _ = synthetic
    if broken == "network_missing":
        del payload["skill_coordinator"]
    elif broken == "network_shape":
        payload["skill_discoverer"]["weight"] = torch.zeros(2, 1)
    elif broken == "stats_missing":
        del payload["valuenorm_state"]["discoverer"]
    elif broken == "stat_missing":
        del payload["valuenorm_state"]["coordinator"]["count"]
    else:
        payload["valuenorm_state"]["coordinator"]["var"] = np.ones(2)
    with pytest.raises((KeyError, RuntimeError, ValueError)):
        r.load_controller(tmp_path / "synthetic.pt", tmp_path, 32, r.time.perf_counter(), dict.fromkeys(r.COUNT_KEYS, 0))


def test_load_uses_entry_deadline(synthetic, tmp_path, monkeypatch):
    payload, made, _ = synthetic
    clock = [100.]
    monkeypatch.setattr(r.time, "perf_counter", lambda: clock[0])
    def slow_load(*args, **kwargs):
        clock[0] = 281.
        return payload
    monkeypatch.setattr(torch, "load", slow_load)
    with pytest.raises(TimeoutError):
        r.load_controller(tmp_path / "synthetic.pt", tmp_path, 32, 100., dict.fromkeys(r.COUNT_KEYS, 0))
    assert made == []


@pytest.mark.parametrize("stage", ["load", "publication"])
def test_main_budget_includes_load_and_closed_publication(monkeypatch, tmp_path, capsys, stage):
    clock = [100.]
    monkeypatch.setattr(r, "ROOT", tmp_path)
    monkeypatch.setattr(r, "PROCESS_START", 100.)
    monkeypatch.setattr(r.time, "perf_counter", lambda: clock[0])
    # No host episodes or real controller are run in these clock tests.
    monkeypatch.setattr(r, "RelayCorridorAdapter", lambda *a, **k: None)
    def evaluate(*args, **kwargs):
        r.check_deadline(args[4])
        args[3]["status"] = "complete"
    monkeypatch.setattr(r, "evaluate", evaluate)
    def slow_load(*args):
        clock[0] = 281.
        r.check_deadline(args[3])
    monkeypatch.setattr(r, "load_controller", slow_load)
    write = r.write_summary
    def publish(out, summary):
        write(out, summary)
        if stage == "publication":
            clock[0] = 281.
    monkeypatch.setattr(r, "write_summary", publish)
    out = tmp_path / "temp/directions/flexible_skill_duration/exp/clock"
    argv = ["--policy", "C" if stage == "load" else "G", "--seed", "770103",
            "--launch-sha", "TEST", "--out", str(out)]
    if stage == "load":
        argv += ["--checkpoint", "synthetic.pt"]
    assert r.main(argv) == 1
    final = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert final["status"] == "incomplete" and final["cap_breached"]
    assert final["complete_wall_seconds"] == 181.
    assert (out / "summary.json").exists()
    if stage == "load":
        assert json.loads((out / "summary.json").read_text())["counts"]["scoring_steps"] == 0
