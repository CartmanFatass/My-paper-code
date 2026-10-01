"""Declared complete fake-environment integration; no native/canonical query."""
from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.model import Student, make_student
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import scalar_state
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.study import load_raw
from experiments.candidates.uav_fleet_adaptation.b10_joint_control import audit, reference
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.contract import FROZEN, PROGRAMS, CONTRASTS, OBJECT
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.learning import JointActor, Critic146
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.read import _read_all, read_result
from experiments.candidates.uav_fleet_adaptation.b10_joint_control.study import _execute, run_batch


@pytest.fixture(scope="module", autouse=True)
def paid_checks():
    counts = dict(student_rows=0, joint_rows=0, reader_joint_rows=0, critic_rows=0,
                  actor_steps=0, critic_steps=0, fake_scalar_states=0, reader_scalar_states=0, fake_steps=0)
    saved = []
    def wrap(owner, key, count, amount):
        original = getattr(owner, key); saved.append((owner, key, original))
        def call(*args, **kwargs):
            result = original(*args, **kwargs); counts[count] += amount(result); return result
        setattr(owner, key, call)
    wrap(Student, "forward", "student_rows", lambda x: x.shape[0])
    wrap(JointActor, "forward", "joint_rows", lambda x: x.shape[0])
    wrap(Critic146, "forward", "critic_rows", lambda x: x.numel())
    wrap(reference, "joint_forward", "reader_joint_rows", lambda x: 1)
    wrap(audit, "scalar_state", "reader_scalar_states", lambda x: 1)
    step = torch.optim.Adam.step
    def counted_step(self, *args, **kwargs):
        result = step(self, *args, **kwargs)
        counts["actor_steps" if self.param_groups[0]["params"][-1].numel() == 54 else "critic_steps"] += 1
        return result
    torch.optim.Adam.step = counted_step
    threads = torch.get_num_threads(); torch.set_num_threads(1)
    yield counts
    for owner, key, original in reversed(saved): setattr(owner, key, original)
    torch.optim.Adam.step = step; torch.set_num_threads(threads)
    print("B10 ACTUAL fake pipeline exposure:", json.dumps(counts, sort_keys=True), "native/canonical=0")


class FakeEnv:
    def __init__(self, seed, counts, horizon=8):
        self.env, self.n_uavs, self.horizon, self.counts = self, 5, horizon, counts
        self._path_loss_cache_generation = 0
        self.reset(seed)

    def _refresh(self, physical=True):
        self.radio = scalar_state(self.uav_positions, self.user_positions, self.transmitter_mask, self.current_step, self.horizon)
        self.counts["fake_scalar_states"] += 1
        self.sinr_matrix, self.uav_sinr_matrix, self.connections = (self.radio[key].copy() for key in ("sinr", "peer_sinr", "connections"))
        if physical:
            self._path_loss_cache_generation += 1
            self._path_loss_cache_misses = 260

    def _state(self):
        return np.r_[self.uav_positions.ravel(), self.user_positions.ravel(), self.current_step / self.horizon].astype(np.float32)

    def _info(self, initial):
        return {"state" if initial else "next_state": self._state(),
                "state_info": dict(uav_positions=self.uav_positions.copy(), user_positions=self.user_positions.copy()),
                "rewards_dict": {f"uav_{i}": self.radio["reward"] / 5. for i in range(5)},
                "infos_dict": {"uav_0": {"global": dict(connections=self.connections.copy(), sinr_matrix=self.sinr_matrix.copy(),
                                                         served_users=self.radio["served"])}}}

    def reset(self, seed):
        self.current_step = 0
        self.uav_positions, self.user_positions = original_layout(seed)
        self.transmitter_mask = np.ones(5, dtype=bool)
        self._refresh()
        return self.radio["observations"].copy(), self._info(True)

    def set_transmitter_mask(self, mask):
        self.transmitter_mask = mask.copy(); self._refresh(physical=False)
        return self.radio["observations"].copy()

    def _dict_to_array(self, rows):
        return rows.copy()

    def step(self, commands):
        self.uav_positions = np.clip(self.uav_positions + commands.astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        self.current_step += 1; self.counts["fake_steps"] += 1; self._refresh()
        return self.radio["observations"].copy(), self.radio["reward"], self.current_step == self.horizon, False, self._info(False)


@pytest.fixture(scope="module")
def tiny(tmp_path_factory, paid_checks):
    out = tmp_path_factory.mktemp("b10_complete_fake")
    for folder in ("raw", "assets"): (out / folder).mkdir()
    protocol = replace(FROZEN, training_worlds=((95001, 95002, 95003, 95004), (95005, 95006, 95007, 95008)),
                       worlds=(95009, 95010), horizon=8, bootstrap_resamples=11).validate()
    parent = make_student(95031).eval().requires_grad_(False)
    gate = dict(mean=np.zeros(253), scale=np.ones(253), constant=np.zeros(253, dtype=bool),
                coefficients=np.zeros(253), intercept=np.asarray(.1))
    env = FakeEnv(95033, paid_checks)
    counts = dict(constructor_calls=1, constructor_resets=1, native_dense_power_slots=275,
                  native_unique_distance_pairs=260, gate_draws=0)
    batch = dict(launch_sha="synthetic-b10", actual=counts, inflight={}, rows=[], fits=[])
    _execute(out, parent, gate, env, protocol, batch, lambda **kwargs: None)
    report = dict(actual=dict(native_steps=0, optimizer_steps=0, refits=0), inflight={}, policy_costs={})
    _read_all(batch, out, parent, gate, protocol, report, lambda **kwargs: None)
    print("B10 fake policy/reader work:", json.dumps(dict(worker=batch["costs"], reader=report["policy_costs"]), sort_keys=True))
    return out, protocol, parent, gate, batch, report


def test_fixed_complete_bill_has_no_query():
    expected = FROZEN.expected()
    for key, value in dict(fits=2, complete_episodes=1376, native_steps=352256, evaluation_episodes=864,
                           motion_requests=440320, motion_draws=409600, mask_installs=88064,
                           joint_collection_rows=225280, frozen_forward_ceiling=188416, helper_requests=327680,
                           C_family_requests=112640, controller_link_ceiling=300646400,
                           native_dense_power_slots=97249075, mask_refresh_dense_sinr_slots=24217600,
                           reader_scalar_states=441696, reader_local_rows=2208480, reader_scalar_power_links=119257920).items():
        assert expected[key] == value
    assert len(PROGRAMS) == 15 and len(CONTRASTS) == 32 and len(FROZEN.episode_order(0)) == 27


def test_complete_training_masked_collection_and_reader(tiny, paid_checks):
    out, protocol, parent, gate, batch, report = tiny
    assert len(batch["rows"]) == 62 and len(batch["fits"]) == 2
    assert batch["actual"]["native_steps"] == 496  # Fake transition ledger only.
    assert batch["actual"]["actor_optimizer_steps"] == batch["actual"]["critic_optimizer_steps"] == 16
    assert report["actual"]["saved_update_groups"] == 4
    assert report["actual"]["scalar_states"] == 682 and report["actual"]["scalar_power_links"] == 184140
    assert report["actual"]["native_steps"] == report["actual"]["optimizer_steps"] == report["actual"]["refits"] == 0
    assert len(report["comparisons"]["levels"]) == 15 and len(report["comparisons"]["contrasts"]) == 32
    assert paid_checks["fake_steps"] == 496 and paid_checks["fake_scalar_states"] == 683
    assert all(row["noneligible_off_requests"] == 0 for row in batch["rows"])
    assert len(list((out / "assets").glob("*_group*.pt"))) == 4
    assert all(p.grad is None and not p.requires_grad for p in parent.parameters())
    assert batch["costs"]["all_policy"]["initial_fidelity_rows"] == 16


def test_schema_and_execution_order_tamper_rejected_without_queries(tiny):
    out, protocol, parent, gate, batch, report = tiny
    row = next(row for row in batch["rows"] if row["program"] == "C_A")
    raw = load_raw(out / row["raw"]["path"])
    raw["eligible"] = raw["eligible"].astype(np.int64)
    with pytest.raises(AssertionError, match="dtype"):
        audit.audit_episode(raw, row, protocol, parent, gate)
    bad = deepcopy(batch); bad["rows"][0], bad["rows"][1] = bad["rows"][1], bad["rows"][0]
    with pytest.raises(AssertionError, match="execution order"):
        _read_all(bad, out, parent, gate, protocol, dict(actual={}, inflight={}), lambda **kwargs: None)


def test_production_refuses_unadmitted_or_incomplete_result(tmp_path):
    with pytest.raises(ValueError, match="admission"):
        run_batch(tmp_path / "untouched", "none", admission=None, asset_paths={})
    assert not (tmp_path / "untouched").exists()
    out = tmp_path / "invalid"; out.mkdir()
    (out / "summary.json").write_text(json.dumps(dict(object=OBJECT, state="FAILED", scientific_execution=True)))
    with pytest.raises(AssertionError, match="production result"):
        read_result(out, tmp_path)
    saved = json.loads((out / "reading.json").read_text())
    assert saved["status"] == "FAILED" and saved["actual"] == dict(native_steps=0, optimizer_steps=0, refits=0)
    with pytest.raises(FileExistsError): read_result(out, tmp_path)
