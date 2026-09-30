"""Outcome-blind composition integration; synthetic actor/host, no production data."""
import copy
import json
from pathlib import Path
import shutil

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers, model
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_radio_activation.b01 import protocol as ep
from experiments.candidates.uav_radio_activation.b01.read import observed_rows, radio
from experiments.candidates.uav_radio_activation.b01.scheduler import Scheduler as EScheduler
from experiments.candidates.uav_radio_activation.b03.scheduler import Scheduler as JointScheduler
from experiments.candidates.uav_parent_adaptation.b05_radio_composition import collection, study
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.contract import ASSET, ASSET_PATH, FROZEN, Protocol, new_counts
from experiments.candidates.uav_parent_adaptation.b05_radio_composition.verify_coordinator import (
    coordinator_counts, verify_coordinator,
)

SMALL = Protocol(worlds=(71101,), horizon=8)


class SyntheticRadioHost:
    """Pure NumPy fixture reproduces the interface, including in-place radio refresh."""
    def __init__(self, seed):
        self.env = self
        self.agents = [f"uav_{i}" for i in range(5)]
        self.transmitter_mask = np.ones(5, bool)
        self.sinr = np.empty((5, 50))
        self.connections = np.zeros((5, 50), bool)
        self.reset(seed)

    def reset(self, seed):
        rng = np.random.RandomState(seed)
        self.positions = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000), rng.uniform(50, 150)]
                                   for _ in range(5)])
        self.users = np.array([[rng.uniform(0, 1000), rng.uniform(0, 1000)] for _ in range(50)])
        self.tick = 0
        self.transmitter_mask[:] = True
        self.refresh()
        return self.observations.copy(), self.info()

    def refresh(self):
        mask = int(np.sum(self.transmitter_mask * (1 << np.arange(5))))
        sinr, connections, self.metrics = radio(self.positions, self.users, mask)
        self.sinr[:] = sinr
        self.connections[:] = connections
        self.observations = observed_rows(self.positions, self.users, mask, self.tick)
        self.observations[:, -1] = self.tick / SMALL.horizon

    def set_transmitter_mask(self, mask):
        self.transmitter_mask[:] = mask
        self.refresh()

    def _get_observation(self, agent):
        return self.observations[int(agent.split("_")[-1])].copy()

    def _dict_to_array(self, values):
        return np.asarray([values[agent] for agent in self.agents], np.float32)

    def info(self):
        return dict(state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(sinr_matrix=self.sinr, connections=self.connections)}},
                    rewards_dict={agent: self.metrics["J"] / 5 for agent in self.agents})

    def step(self, commands):
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30., ep.LOW, ep.HIGH)
        self.tick += 1
        self.refresh()
        return self.observations.copy(), 0., False, self.tick == SMALL.horizon, self.info()


@pytest.fixture(scope="module")
def fixture_batch(tmp_path_factory):
    previous_threads, old_horizon = torch.get_num_threads(), ep.HORIZON
    torch.set_num_threads(1)
    ep.HORIZON = SMALL.horizon  # Source E protocol has its original fixed global horizon.
    root = tmp_path_factory.mktemp("b05-pure-radio-fixture")
    actor = model.make_student(71201)
    state, asset = actor.state_dict(), root / "synthetic.pt"
    digest = model.state_digest(state)
    torch.save(dict(architecture=[114, 128, 128, 27], dtype="float32", activation="relu",
                    state_dict=state, state_sha256=digest), asset)
    binding = dict(file_identity(asset), state_sha256=digest)
    out = root / "result"
    try:
        batch = study.run_batch(out, "synthetic-only", protocol=SMALL, asset_path=asset,
                                fixture_binding=binding, factory=SyntheticRadioHost)
        yield out, batch, asset, binding
    finally:
        ep.HORIZON = old_horizon
        torch.set_num_threads(previous_threads)


def load_raw(out, row):
    with np.load(out / row["raw"]["path"], allow_pickle=False) as archive:
        return {k: archive[k] for k in archive.files}


def test_frozen_costs_and_admission_guards(tmp_path, monkeypatch):
    from experiments.candidates.uav_parent_adaptation.b05_radio_composition import run
    from scripts import hmasd_admission
    expected = FROZEN.expected()
    assert expected["complete_episodes"] == 512 and expected["native_steps"] == 131072
    assert expected["c_requests"] == 102400 and expected["s_requests"] == 61440
    assert expected["sampling_decisions"] == 122880 and expected["private_integer_reads"] == 245760
    assert expected["unique_tape_integers"] == 45056 and expected["unique_tape_bytes"] == 360448
    assert expected["e_state_reductions_ceiling"] == 1264800
    assert expected["s2_state_reductions_ceiling"] == 4551680
    assert expected["t2_state_reductions_ceiling"] == 6803136
    assert expected["reader_candidate_state_reductions_ceiling"] == 1508640
    assert expected["reader_native_observation_formula_checks"] == 164352
    assert len(list(FROZEN.schedule())) == len(set(FROZEN.schedule())) == 512
    assert list(FROZEN.schedule())[:3] == [("C_all", 29347000, -1), ("Q_I_all", 29347000, 0), ("Q_I_all", 29347000, 1)]
    with pytest.raises(ValueError, match="admitted"):
        study.run_batch(tmp_path / "no-native", "bad")
    with pytest.raises(ValueError, match="nonproduction"):
        study.run_batch(tmp_path / "no-fixture", "bad", factory=SyntheticRadioHost)
    def refuse(*args, **kwargs):
        raise RuntimeError("fixture admission refusal")
    monkeypatch.setattr(hmasd_admission, "require_admission", refuse)
    with pytest.raises(RuntimeError, match="admission refusal"):
        run.main(["--out", str(tmp_path / "b05_radio_composition_a01"), "--seed", "29347091", "--launch-sha", "bad"])
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("identity", ["path", "file", "tensors"])
def test_fixture_cannot_forward_original_asset_under_synthetic_label(tmp_path, monkeypatch, identity):
    called = []
    monkeypatch.setattr(study, "load_asset", lambda *args: called.append("load"))
    binding = dict(sha256="different", state_sha256="different")
    path = tmp_path / "synthetic.pt"
    if identity == "path":
        path = ASSET_PATH
    elif identity == "file":
        binding["sha256"] = ASSET["sha256"]
    else:
        binding["state_sha256"] = ASSET["state_sha256"]
    with pytest.raises(ValueError, match="synthetic fixture must not load"):
        study.run_batch(tmp_path / "blocked", "fixture", protocol=SMALL, asset_path=path,
                        factory=lambda seed: called.append("construct"), fixture_binding=binding)
    assert not called and not list(tmp_path.iterdir())


def test_full_synthetic_collection_and_bounded_reader(fixture_batch, monkeypatch):
    from experiments.candidates.uav_parent_adaptation.b05_radio_composition import read
    out, batch, asset, binding = fixture_batch
    assert batch["status"] == "COMPLETE"
    assert batch["actual"]["native_steps"] == 128 and batch["actual"]["complete_episodes"] == 16
    assert batch["actual"]["explicit_resets"] == 16 and batch["actual"]["constructor_resets"] == 1
    assert batch["actual"]["private_integer_reads"] == 240
    assert batch["asset"]["state_sha256"] == batch["asset_after_state_sha256"]
    def forbidden(*args, **kwargs):
        raise AssertionError("reader bought undeclared native/full-C/optimizer work")
    monkeypatch.setattr(SyntheticRadioHost, "step", forbidden)
    monkeypatch.setattr(controllers.MemoC, "query", forbidden)
    monkeypatch.setattr(torch.optim, "Adam", forbidden)
    result = read.read_batch(out, permit_fixture=True)
    assert result["status"] == "VERIFIED"
    assert result["reader_calls"]["S_forward_attempts"] == result["reader_calls"]["S_forward_completed"] == 60
    assert result["reader_calls"]["S_helper_completed"] == 60
    assert result["reader_calls"]["native_formula_completed"] == 176
    assert result["reader_calls"]["candidate_reduction_completed"] <= SMALL.expected()["reader_candidate_state_reductions_ceiling"]
    assert result["comparisons"] == batch["comparisons"]
    assert len(result["audits"]) == 16
    with pytest.raises(FileExistsError, match="reconcile paid reading"):
        read.read_batch(out, permit_fixture=True)
    with pytest.raises(FileExistsError, match="repeat/resume"):
        study.run_batch(out, "synthetic-only", protocol=SMALL, asset_path=asset,
                        factory=SyntheticRadioHost, fixture_binding=binding)


@pytest.mark.parametrize("arm", ["C_E", "Q_I_S2", "C_T2"])
@pytest.mark.parametrize("field", ["coord_due", "coord_commands", "coord_mask", "coord_scores", "coord_order"])
def test_coordinator_corruption_rejected(fixture_batch, arm, field):
    out, batch, _, _ = fixture_batch
    row = next(r for r in batch["rows"] if r["arm"] == arm)
    raw = load_raw(out, row)
    if field == "coord_scores":
        finite = np.flatnonzero(np.isfinite(raw[field]))
        raw[field].flat[finite[0]] += .1
    else:
        raw[field].flat[0] += 1
    with pytest.raises(AssertionError):
        verify_coordinator(raw, row, SMALL, coordinator_counts(), lambda: None)


@pytest.mark.parametrize("coordinator", ["E", "S2", "T2"])
@pytest.mark.parametrize("clock_calls_before_late", [0, 120])
def test_source_deadline_misses_partial_search_and_startup_are_readable(tmp_path, monkeypatch, coordinator, clock_calls_before_late):
    monkeypatch.setattr(ep, "HORIZON", SMALL.horizon)
    out = tmp_path / "partial"
    (out / "raw").mkdir(parents=True)
    def factory(kind, packet, horizon):
        assert kind == coordinator
        scheduler = (EScheduler("E", packet) if kind == "E" else JointScheduler(kind, packet, horizon=horizon))
        original = scheduler.decide
        def decide(*args, **kwargs):
            base = kwargs.get("started", 0.)
            count = [0]
            def clock():
                count[0] += 1
                # E first reads its own start; joint starts before the local block.
                first = 1 if kind == "E" else 0
                return base + (10. if count[0] > first + clock_calls_before_late else 0.)
            scheduler.clock = clock
            return original(*args, **kwargs)
        scheduler.decide = decide
        return scheduler
    row = collection.collect_episode(SyntheticRadioHost(71103), arm="C_" + coordinator,
                                     world=71103, tape=-1, bundle=None, out=out, protocol=SMALL,
                                     counts=new_counts(), actor=None, policy_sha="synthetic", inflight={},
                                     check=lambda: None, coordinator_factory=factory)
    raw = load_raw(out, row)
    assert not raw["coord_timely"].any()
    assert not raw["coord_has_command"].any()
    assert raw["transmitter_mask"].all()
    result = verify_coordinator(raw, row, SMALL, coordinator_counts(), lambda: None)
    assert len(result["rounds"]) == 2
    if coordinator != "E":
        np.testing.assert_array_equal(raw["commands"], np.broadcast_to(raw["proposals"][0], (8, 5, 3)))
    if clock_calls_before_late:
        assert raw["coord_state_reductions"].sum() > 0


def test_native_failure_preserves_attempts_partial_raw_and_no_repeat(fixture_batch, tmp_path):
    class Failing(SyntheticRadioHost):
        def step(self, commands):
            if self.tick == 2:
                raise RuntimeError("synthetic transition failure")
            return super().step(commands)
    out = tmp_path / "failed"
    with pytest.raises(RuntimeError, match="synthetic transition"):
        study.run_batch(out, "synthetic-only", protocol=SMALL, asset_path=fixture_batch[2],
                        factory=Failing, fixture_binding=fixture_batch[3])
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "INCOMPLETE"
    assert result["actual"]["native_step_calls"] == 3 and result["actual"]["native_steps"] == 2
    assert result["actual"]["complete_episodes"] == 0
    with np.load(out / result["inflight"]["raw"]["path"]) as raw:
        assert not raw["episode_complete"] and int(raw["completed_steps"]) == 2
    assert result["inflight"]["policy_counts"]["requests"] == 5


def test_binding_and_cpu_stops_precede_construction(fixture_batch, tmp_path, monkeypatch):
    called = []
    def factory(seed):
        called.append(seed)
        raise AssertionError("must not construct")
    wrong = dict(fixture_batch[3], sha256="0" * 64)
    with pytest.raises(ValueError, match="asset file identity"):
        study.run_batch(tmp_path / "bad-asset", "fixture", protocol=SMALL, asset_path=fixture_batch[2],
                        factory=factory, fixture_binding=wrong)
    def expired(self):
        raise RuntimeError("fixture CPU envelope exhausted")
    monkeypatch.setattr(study.CpuBudget, "check", expired)
    with pytest.raises(RuntimeError, match="CPU envelope"):
        study.run_batch(tmp_path / "expired", "fixture", protocol=SMALL, asset_path=fixture_batch[2],
                        factory=factory, fixture_binding=fixture_batch[3])
    assert not called
    for name in ("bad-asset", "expired"):
        result = json.loads((tmp_path / name / "summary.json").read_text())
        assert result["actual"]["constructor_calls"] == result["actual"]["native_step_calls"] == 0


def test_reader_failure_preserves_paid_attempt_and_forbids_retry(fixture_batch, tmp_path, monkeypatch):
    from experiments.candidates.uav_parent_adaptation.b05_radio_composition import read
    out = tmp_path / "failed-reader"
    shutil.copytree(fixture_batch[0], out, ignore=shutil.ignore_patterns("reading.json", "reader-progress.json"))
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic forward failure")
    monkeypatch.setattr(model.Student, "forward", fail)
    with pytest.raises(RuntimeError, match="synthetic forward failure"):
        read.read_batch(out, permit_fixture=True)
    result = json.loads((out / "reader-progress.json").read_text())
    assert result["status"] == "INCOMPLETE" and result["completed_rows"] == 3
    assert result["reader_calls"]["S_forward_attempts"] == 1 and result["reader_calls"]["S_forward_completed"] == 0
    assert result["reader_calls"]["S_helper_completed"] == 1
    with pytest.raises(FileExistsError, match="reconcile paid reading"):
        read.read_batch(out, permit_fixture=True)


def test_synthetic_reader_rejects_production_binding_before_load(fixture_batch, tmp_path, monkeypatch):
    from experiments.candidates.uav_parent_adaptation.b05_radio_composition import read
    out = tmp_path / "reader-original-forbidden"
    shutil.copytree(fixture_batch[0], out, ignore=shutil.ignore_patterns("reading.json", "reader-progress.json"))
    for name in ("summary.json", "config.json"):
        path = out / name
        data = json.loads(path.read_text())
        data["asset"].update(ASSET, path=str(ASSET_PATH))
        path.write_text(json.dumps(data))
    called = []
    monkeypatch.setattr(read, "load_asset", lambda *args: called.append("load"))
    with pytest.raises(AssertionError, match="synthetic reading must not load"):
        read.read_batch(out, permit_fixture=True)
    assert not called
