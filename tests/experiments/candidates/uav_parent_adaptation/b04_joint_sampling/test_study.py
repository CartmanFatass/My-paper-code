"""Synthetic-only collection/reconstruction checks: no native trajectory or fit."""
import copy
import json
import shutil

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02 import controllers, model
from experiments.candidates.uav_local_history.b01.study import file_identity
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling import study, read
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.collection import collect_episode
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.contract import FROZEN, Protocol, new_counts
from experiments.candidates.uav_parent_adaptation.b04_joint_sampling.sampling import make_bundle


SMALL = Protocol(worlds=(7101, 7102), horizon=8)


class Synthetic:
    """Analytic motion/service fixture; its geometry is not scientific evidence."""
    def __init__(self, seed):
        self.env = self
        self.transmitter_mask = np.ones(5, dtype=bool)
        self.reset(seed)

    def reset(self, seed):
        rng = np.random.default_rng(seed)
        self.positions = rng.uniform([100., 100., 60.], [900., 900., 140.], (5, 3))
        self.users = rng.uniform(0., 1000., (50, 2))
        self.tick = 0
        self.transmitter_mask[:] = True
        return self.obs(), self.info()

    def obs(self):
        result = np.zeros((5, 104), dtype=np.float32)
        for i, own in enumerate(self.positions):
            result[i, :3] = own / [1000., 1000., 100.] - [0., 0., .5]
            result[i, 3:5] = (self.users[i] - own[:2]) / 1000.
            result[i, 5] = .4
            for j, peer in enumerate(np.delete(self.positions, i, axis=0)):
                result[i, 63 + j * 4:66 + j * 4] = (peer - own) / [1000., 1000., 100.]
                result[i, 66 + j * 4] = 1.
            result[i, -1] = self.tick / 8.
        return result

    def info(self):
        sinr = np.full((5, 50), -5., dtype=np.float64)
        connections = np.zeros((5, 50), dtype=bool)
        for i in range(5):
            sinr[i, i] = 4. + self.positions[i, 0] / 1000.
            connections[i, i] = True
        q = float(np.clip((sinr[connections] - 3.) / 30., 0., 1.).mean())
        reward = .7 * 5 / 50. + .3 * q
        return dict(state_info=dict(uav_positions=self.positions.copy(), user_positions=self.users.copy()),
                    infos_dict={"uav_0": {"global": dict(connections=connections, sinr_matrix=sinr, served_users=5)}},
                    rewards_dict={f"uav_{i}": reward / 5. for i in range(5)})

    def step(self, commands):
        self.positions = np.clip(self.positions + commands.astype(np.float64) * 30.,
                                 [0., 0., 50.], [1000., 1000., 150.])
        self.tick += 1
        return self.obs(), 0., False, self.tick == 8, self.info()


def write_json(path, data):
    path.write_text(json.dumps(data))


@pytest.fixture(scope="module")
def fixture_batch(tmp_path_factory):
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    root = tmp_path_factory.mktemp("b04-synthetic")
    actor = model.make_student(7111)
    state = actor.state_dict()
    digest = model.state_digest(state)
    asset = root / "fixture.pt"
    torch.save(dict(architecture=[114, 128, 128, 27], dtype="float32", activation="relu",
                    state_dict=state, state_sha256=digest), asset)
    binding = dict(file_identity(asset), state_sha256=digest)
    out = root / "result"
    result = study.run_batch(out, "synthetic-fixture", protocol=SMALL, asset_path=asset,
                             factory=Synthetic, fixture_binding=binding)
    yield out, result, asset, binding
    torch.set_num_threads(previous)


def test_fixed_exposure_and_native_bypass_guards(tmp_path):
    e = FROZEN.expected()
    assert e["native_steps"] == 106496 and e["complete_episodes"] == 416
    assert e["controller_requests"] == 133120
    assert e["c_requests"] == 71680 and e["s_requests"] == 61440
    assert e["unique_tape_integers"] == 45056 and e["unique_tape_bytes"] == 360448
    assert e["combined_power_ceiling"] == 199999475
    assert e["fits"] == e["optimizer_steps"] == e["expert_labels"] == 0
    with pytest.raises(ValueError, match="admitted"):
        study.run_batch(tmp_path / "no-native", "bad")
    with pytest.raises(ValueError, match="nonproduction"):
        study.run_batch(tmp_path / "no-fixture", "bad", factory=Synthetic)
    assert list(tmp_path.iterdir()) == []


def test_complete_synthetic_collection_and_independent_reader(fixture_batch, monkeypatch):
    out, result, _, _ = fixture_batch
    assert result["status"] == "COMPLETE"
    actual = result["actual"]
    assert actual["native_steps"] == actual["native_step_calls"] == 208
    assert actual["constructors"] == actual["constructor_calls"] == actual["constructor_resets"] == 1
    assert actual["explicit_resets"] == actual["explicit_reset_calls"] == 26
    assert actual["sampling_decisions"] == 240
    assert result["asset"]["state_sha256"] == result["asset_after_state_sha256"]
    assert [(r["arm"], r["world"], r["tape"]) for r in result["rows"]] == list(SMALL.schedule())
    forwards = []
    original_forward = model.Student.forward

    def forward(self, features):
        forwards.append(tuple(features.shape))
        return original_forward(self, features)

    def forbidden(*args, **kwargs):
        raise AssertionError("reader purchased native/helper/optimizer work")

    monkeypatch.setattr(model.Student, "forward", forward)
    monkeypatch.setattr(Synthetic, "step", forbidden)
    monkeypatch.setattr(controllers.MemoC, "query", forbidden)
    monkeypatch.setattr(torch.optim, "Adam", forbidden)
    reading = read.read_batch(out, permit_fixture=True)
    assert reading["status"] == "VERIFIED" and forwards == [(1, 114)] * 120
    assert reading["reader_calls"]["S_forward_rows"] == 120
    assert reading["reader_calls"]["actual_motion_agent_ticks"] == 1040
    assert reading["reader_calls"]["modal_alias_motion_steps"] == 960
    assert reading["comparisons"] == result["comparisons"]
    assert len(reading["comparisons"]["paired"]) == 13
    joint = reading["joint_diagnostics"]
    assert len(joint["index"]) == 24
    with np.load(out / joint["path"], allow_pickle=False) as z:
        assert z["expected_joint"].shape == (24, 2, 4)
        assert z["requested_departure"].shape == z["physical_departure"].shape == (24, 2, 5)
        for i, identity in enumerate(joint["index"]):
            if identity["arm"].startswith("Q_"):
                np.testing.assert_array_equal(z["expected_joint"][i, :, 2], 0.)
            if identity["arm"] == "Q_A":
                assert np.all(z["requested_departure"][i].sum(axis=-1) <= 1)
        assert np.all(~z["physical_departure"] | z["requested_departure"])
    assert json.loads((out / "reader-progress.json").read_text())["completed_rows"] == 26
    with pytest.raises(FileExistsError, match="reconcile paid replay"):
        read.read_batch(out)
    with pytest.raises(FileExistsError, match="repeat/resume"):
        study.run_batch(out, "synthetic-fixture", protocol=SMALL, asset_path=fixture_batch[2],
                        factory=Synthetic, fixture_binding=fixture_batch[3])


@pytest.mark.parametrize("field", ["public_integer", "commands", "features", "departure_threshold",
                                    "probabilities", "logits"])
def test_reader_rejects_rehashed_corrupt_raw(fixture_batch, tmp_path, field):
    out = tmp_path / "corrupt"
    shutil.copytree(fixture_batch[0], out)
    summary = copy.deepcopy(fixture_batch[1])
    arm = "S_I" if field == "logits" else "Q_I"
    row = next(r for r in summary["rows"] if r["arm"] == arm)
    path = out / row["raw"]["path"]
    with np.load(path, allow_pickle=False) as z:
        raw = {k: z[k] for k in z.files}
    raw[field].flat[0] += 1
    np.savez_compressed(path, **raw)
    row["raw"].update(file_identity(path))
    write_json(out / "summary.json", summary)
    with pytest.raises(AssertionError):
        read.read_batch(out, permit_fixture=True)
    progress = json.loads((out / "reader-progress.json").read_text())
    assert progress["status"] == "FAILED" and progress["current_row"]["arm"] == arm
    if field == "commands":
        assert progress["reader_calls"]["actual_motion_agent_ticks"] == (progress["completed_rows"] + 1) * SMALL.horizon * 5


def test_reader_rejects_corrupt_exposure_before_replay(fixture_batch, tmp_path):
    out = tmp_path / "exposure"
    shutil.copytree(fixture_batch[0], out)
    for name in ("summary.json", "config.json"):
        path = out / name
        data = json.loads(path.read_text())
        data["expected"]["fits"] = 1
        write_json(path, data)
    with pytest.raises(AssertionError, match="exposure tampering"):
        read.read_batch(out, permit_fixture=True)
    assert json.loads((out / "reader-progress.json").read_text())["reader_calls"]["S_forward_rows"] == 0


@pytest.mark.parametrize("case", ["nondecision", "decision_and_feature", "terminal"])
def test_reader_binds_every_saved_sensor_position_to_motion(fixture_batch, tmp_path, case):
    out = tmp_path / "corrupt-position"
    shutil.copytree(fixture_batch[0], out)
    summary = copy.deepcopy(fixture_batch[1])
    row = summary["rows"][0]
    path = out / row["raw"]["path"]
    with np.load(path, allow_pickle=False) as z:
        raw = {k: z[k] for k in z.files}
    if case == "terminal":
        raw["terminal_observation"][0, 0] += .125
    elif case == "decision_and_feature":
        raw["observations"][0, 0, 0] += .125
        raw["features"][0, 0, 0] += .125
    else:
        raw["observations"][1, 0, 0] += .125
    np.savez_compressed(path, **raw)
    row["raw"].update(file_identity(path))
    write_json(out / "summary.json", summary)
    with pytest.raises(AssertionError, match="own position"):
        read.read_batch(out, permit_fixture=True)


def test_binding_failures_precede_constructor(fixture_batch, tmp_path, monkeypatch):
    called = []
    def factory(seed):
        called.append(seed)
        raise AssertionError("construction must not occur")
    bad = dict(fixture_batch[3], sha256="0" * 64)
    with pytest.raises(ValueError, match="asset file identity"):
        study.run_batch(tmp_path / "asset", "fixture", protocol=SMALL, asset_path=fixture_batch[2],
                        factory=factory, fixture_binding=bad)
    def source_error(root):
        raise ValueError("bound source drift fixture")
    monkeypatch.setattr(study, "source_identities", source_error)
    with pytest.raises(ValueError, match="source drift"):
        study.run_batch(tmp_path / "source", "fixture", protocol=SMALL, asset_path=fixture_batch[2],
                        factory=factory, fixture_binding=fixture_batch[3])
    assert called == []
    for name in ("asset", "source"):
        summary = json.loads((tmp_path / name / "summary.json").read_text())
        assert summary["actual"]["constructor_calls"] == summary["actual"]["native_step_calls"] == 0


def test_failed_step_keeps_attempted_and_completed_work(fixture_batch, tmp_path):
    class Failing(Synthetic):
        def step(self, commands):
            if self.tick == 2:
                raise RuntimeError("synthetic native failure")
            return super().step(commands)
    out = tmp_path / "failed-step"
    with pytest.raises(RuntimeError, match="synthetic native failure"):
        study.run_batch(out, "fixture", protocol=SMALL, asset_path=fixture_batch[2],
                        factory=Failing, fixture_binding=fixture_batch[3])
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "INCOMPLETE"
    assert summary["actual"]["native_step_calls"] == 3 and summary["actual"]["native_steps"] == 2
    assert summary["actual"]["complete_episodes"] == 0
    assert sum(c["requests"] for c in summary["inflight"]["policy_agents"]) == 5


def test_failed_reader_keeps_attempted_forward_cost(fixture_batch, tmp_path, monkeypatch):
    out = tmp_path / "failed-reader"
    shutil.copytree(fixture_batch[0], out)
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic actor failure")
    monkeypatch.setattr(model.Student, "forward", fail)
    with pytest.raises(RuntimeError, match="synthetic actor failure"):
        read.read_batch(out, permit_fixture=True)
    progress = json.loads((out / "reader-progress.json").read_text())
    assert progress["status"] == "FAILED" and progress["completed_rows"] == 2
    assert progress["reader_calls"]["S_forward_rows"] == 1
    assert progress["current_row"]["arm"] == "S_I"
    assert json.loads((out / "summary.json").read_text())["status"] == "COMPLETE"


def test_collector_cache_hits_still_sample_fresh_clock_entries(fixture_batch, tmp_path):
    class RepeatedMeasurements(Synthetic):
        """Deliberately static synthetic observations isolate cache/sampler wiring."""
        def obs(self):
            if not hasattr(self, "fixed"):
                self.fixed = super().obs()
            return self.fixed.copy()
    actor, _ = study.load_asset(fixture_batch[2], fixture_batch[3])
    (tmp_path / "raw").mkdir()
    counts = new_counts()
    bundle = make_bundle(7101, 0, horizon=8)
    row = collect_episode(RepeatedMeasurements(7101), arm="S_I", world=7101, tape=0,
                          bundle=bundle, out=tmp_path, protocol=SMALL, counts=counts, actor=actor,
                          policy_sha=fixture_batch[3]["state_sha256"], inflight={})
    assert row["policy_counts"]["neural_rows"] == 5 and counts["sampling_decisions"] == 10
    with np.load(tmp_path / row["raw"]["path"], allow_pickle=False) as raw:
        assert not raw["memo_hit"][0].any() and raw["memo_hit"][1].all()
        np.testing.assert_array_equal(raw["probabilities"][0], raw["probabilities"][1])
        np.testing.assert_array_equal(raw["private_depart_integer"], bundle["private_depart"])
        np.testing.assert_array_equal(raw["private_tail_integer"], bundle["private_tail"])
        assert np.any(raw["action_index"][0] != raw["action_index"][1])
