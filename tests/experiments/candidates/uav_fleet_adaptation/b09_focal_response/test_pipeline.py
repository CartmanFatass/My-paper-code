"""Synthetic private-state and complete H8 pipeline; no native/canonical assets."""
from copy import deepcopy
from dataclasses import replace
import json

import numpy as np
import pytest
import torch

from experiments.candidates.uav_fleet_adaptation.b02.controllers import MemoC, initial_nav
from experiments.candidates.uav_fleet_adaptation.b02.model import Student, make_student, state_digest
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.environment import original_layout
from experiments.candidates.uav_fleet_adaptation.b08_local_gate.physics import scalar_state
from experiments.candidates.uav_fleet_adaptation.b09_focal_response import audit, reference
from experiments.candidates.uav_fleet_adaptation.b09_focal_response.assets import load_parents
from experiments.candidates.uav_fleet_adaptation.b09_focal_response.contract import EGOS, FROZEN, OBJECT, SLOT_PAIRS, assignment
from experiments.candidates.uav_fleet_adaptation.b09_focal_response.learning import Critic, ResponseHead
from experiments.candidates.uav_fleet_adaptation.b09_focal_response.policies import Member
from experiments.candidates.uav_fleet_adaptation.b09_focal_response.read import _read_all, read_result
from experiments.candidates.uav_fleet_adaptation.b09_focal_response.study import _execute, load_raw, run_batch
from experiments.candidates.uav_local_peer_forecast.controller import MotionController


@pytest.fixture(scope="module", autouse=True)
def paid_checks():
    counts = dict(student_rows=0, head_rows=0, reader_head_rows=0, critic_rows=0,
                  head_steps=0, critic_steps=0, C_rankings=0, V_R_rankings=0,
                  reader_V_R_rankings=0, fake_scalar_states=0, reader_scalar_states=0, fake_steps=0)
    originals = {}
    def wrap(owner, key, count, amount):
        original = getattr(owner, key)
        originals[owner, key] = original
        def call(*args, **kwargs):
            result = original(*args, **kwargs)
            counts[count] += amount(args, result)
            return result
        setattr(owner, key, call)
    wrap(Student, "forward", "student_rows", lambda args, result: result.shape[0])
    wrap(ResponseHead, "forward", "head_rows", lambda args, result: 1)
    wrap(Critic, "forward", "critic_rows", lambda args, result: result.numel())
    wrap(MemoC, "_miss", "C_rankings", lambda args, result: 1)
    wrap(MotionController, "_decide", "V_R_rankings", lambda args, result: 1)
    wrap(reference, "ranking", "reader_V_R_rankings", lambda args, result: 1)
    wrap(reference, "focal_logits", "reader_head_rows", lambda args, result: 1)
    wrap(audit, "focal_logits", "reader_head_rows", lambda args, result: 1)
    wrap(audit, "scalar_state", "reader_scalar_states", lambda args, result: 1)
    step = torch.optim.Adam.step
    def paid_step(self, *args, **kwargs):
        result = step(self, *args, **kwargs)
        counts["head_steps" if len(self.param_groups[0]["params"]) == 2 else "critic_steps"] += 1
        return result
    torch.optim.Adam.step = paid_step
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    yield counts
    for (owner, key), original in originals.items():
        setattr(owner, key, original)
    torch.optim.Adam.step = step
    torch.set_num_threads(threads)
    print("B09 pipeline synthetic costs:", json.dumps(counts, sort_keys=True), "native/canonical-asset calls=0")


class FakeEnv:
    """Array-generating fixture with no native environment import/construction."""
    def __init__(self, seed, counts, horizon=8):
        self.env, self.n_uavs, self.horizon, self.counts = self, 5, horizon, counts
        self._path_loss_cache_generation = 0
        self.reset(seed)

    def _refresh(self):
        self.transmitter_mask = np.ones(5, dtype=bool)
        self.radio = scalar_state(self.uav_positions, self.user_positions, self.transmitter_mask, self.current_step, 256)
        self.counts["fake_scalar_states"] += 1
        self.sinr_matrix, self.uav_sinr_matrix, self.connections = (self.radio[key].copy() for key in ("sinr", "peer_sinr", "connections"))
        self._path_loss_cache_generation += 1
        self._path_loss_cache_misses = 260

    def _state(self):
        return np.concatenate((self.uav_positions.ravel(), self.user_positions.ravel(), [self.current_step / 256.])).astype(np.float32)

    def _info(self, initial):
        return {"state" if initial else "next_state": self._state(),
                "state_info": dict(uav_positions=self.uav_positions.copy(), user_positions=self.user_positions.copy()),
                "rewards_dict": {f"uav_{i}": self.radio["reward"] / 5. for i in range(5)},
                "infos_dict": {"uav_0": {"global": dict(connections=self.connections.copy(), sinr_matrix=self.sinr_matrix.copy(),
                                                            served_users=self.radio["served"])}}}

    def reset(self, seed):
        self.current_step = 0
        self.uav_positions, self.user_positions = original_layout(seed)
        self._refresh()
        return self.radio["observations"].copy(), self._info(True)

    def step(self, commands):
        self.uav_positions = np.clip(self.uav_positions + commands.astype(np.float64) * 30., [0., 0., 50.], [1000., 1000., 150.])
        self.current_step += 1
        self.counts["fake_steps"] += 1
        self._refresh()
        return self.radio["observations"].copy(), self.radio["reward"], self.current_step == self.horizon, False, self._info(False)


@pytest.fixture(scope="module")
def tiny(tmp_path_factory, paid_checks):
    out = tmp_path_factory.mktemp("b09_complete_fake")
    for folder in ("assets", "raw", "diagnostics"):
        (out / folder).mkdir()
    protocol = replace(FROZEN, training_worlds=((91901, 91902), (91903, 91904)), worlds=(91905,),
                       evaluation_roots=(91923,), horizon=8, bootstrap_resamples=11).validate()
    actors = {"P0": make_student(91931).eval().requires_grad_(False), "P1": make_student(91932).eval().requires_grad_(False)}
    env = FakeEnv(91933, paid_checks)
    counts = dict(constructor_calls=1, constructor_resets=1, native_dense_power_slots=275, native_unique_distance_pairs=260)
    batch = dict(launch_sha="synthetic-b09", actual=counts, inflight={}, rows=[], fits=[])
    _execute(out, actors, env, protocol, batch, lambda **kwargs: None)
    report = dict(actual=dict(native_steps=0, optimizer_steps=0, refits=0), inflight={}, policy_costs={})
    _read_all(batch, out, actors, protocol, report, lambda **kwargs: None)
    return out, protocol, actors, batch, report


def test_source_counts_match_selected_bill_without_queries():
    expected = FROZEN.expected()
    for key, value in dict(fits=4, training_episodes=1024, evaluation_episodes=1536, complete_episodes=2560,
                           native_steps=655360, motion_requests=819200, motion_draws=565248,
                           frozen_forward_ceiling=450560, helper_request_ceiling=442368, C_ranking_ceiling=376832,
                           collected_head_rows=98304, reader_head_rows=114688, reader_critic_rows=65536,
                           motion_tracker_ingests=262144, motion_pair_gate_ceiling=4177920,
                           roster_draws=2560, roster_unique_addresses=640, reader_scalar_links=177638400).items():
        assert expected[key] == value
    assert len(FROZEN.episode_order(0)) == 48


def test_assignment_six_slots_pairing_and_rng_isolation():
    before = np.random.get_state()
    indices = set()
    for world in range(80):
        index, roster = assignment(711, world, 0, "T")
        indices.add(index)
        assert tuple(i + 1 for i, law in enumerate(roster) if law == "C") == SLOT_PAIRS[index]
        assert roster.count("C") == roster.count("P0") == 2
        assert (index, roster) == assignment(711, world, 0, "T")
    assert indices == set(range(6))
    after = np.random.get_state()
    assert all(np.array_equal(a, b) for a, b in zip(before, after))
    with pytest.raises(ValueError):
        assignment(711, 1, 0, "Y")


def test_zero_focal_laws_private_caches_and_paired_action(tiny):
    _, _, actors, batch, _ = tiny
    # A synthetic empty local row; never query a production checkpoint/world.
    obs = np.zeros(104, dtype=np.float32)
    obs[:3] = (.5, .5, .5)
    head = ResponseHead().eval()
    focal = Member("F", actors, world=9991, agent=0, root=991, head=head)
    fixed = Member("P0", actors, world=9991, agent=0, root=991)
    nav = initial_nav(obs)
    left, right = focal.query(obs, 0, nav), fixed.query(obs, 0, nav)
    for key in ("logits", "probabilities", "action_index", "innovation", "command"):
        np.testing.assert_array_equal(left[key], right[key])
    peer1 = Member("P0", actors, world=9991, agent=1, root=991)
    peer2 = Member("P0", actors, world=9991, agent=2, root=991)
    first = peer1.query(obs, 0, nav)
    second = peer2.query(obs, 0, nav)
    assert peer1.base.base.cache is not peer2.base.base.cache
    first["features"][:] = 99
    assert (peer2.query(obs, 4, nav)["features"] < 99).all()
    assert first["innovation"] != second["innovation"]
    obs[-1] = 4 / 256
    assert focal.query(obs, 4, nav)["memo_hit"]
    with torch.no_grad():
        head.b[0] = 1
    changed = focal.query(obs, 8, nav)
    assert changed["memo_hit"] and not np.array_equal(changed["logits"], left["logits"])


def test_complete_collector_training_reader_and_full_panel(tiny, paid_checks):
    out, protocol, actors, batch, report = tiny
    assert len(batch["rows"]) == 32 and len(batch["fits"]) == 4
    assert batch["actual"]["native_steps"] == 256  # Fake transition ledger only.
    assert batch["actual"]["head_optimizer_steps"] == batch["actual"]["critic_optimizer_steps"] == 16
    assert report["actual"]["saved_update_groups"] == 4
    assert report["actual"]["scalar_states"] == 288 and report["actual"]["scalar_power_links"] == 77760
    assert report["actual"]["native_steps"] == report["actual"]["optimizer_steps"] == report["actual"]["refits"] == 0
    assert len(report["comparisons"]["levels"]) == 24 and len(report["comparisons"]["contrasts"]) == 68
    assert len(report["history_sensitivity"]) == 4 and report["actual"]["history_zero_head_rows"] == 8
    assert paid_checks["fake_steps"] == 256 and paid_checks["fake_scalar_states"] == 289
    assert {row["ego"] for row in batch["rows"] if row["kind"] == "evaluation"} == set(EGOS)
    for name, actor in actors.items():
        assert state_digest(actor.state_dict()) == batch["initial_parent_states"][name]
        assert all(parameter.grad is None and not parameter.requires_grad for parameter in actor.parameters())
    assert len(list((out / "assets").glob("*_group*.pt"))) == 4


def test_roster_and_state_schema_tamper_rejected_before_policy(tiny):
    out, protocol, actors, batch, _ = tiny
    row = next(row for row in batch["rows"] if row["ego"] == "C" and row["kind"] == "evaluation")
    raw = load_raw(out / row["raw"]["path"])
    bad_row = deepcopy(row)
    bad_row["laws"][1] = "Q10"
    with pytest.raises(AssertionError, match="assignment"):
        audit.audit_episode(raw, bad_row, protocol, actors)
    bad = deepcopy(raw)
    bad["logits"] = bad["logits"].astype(np.float64)
    with pytest.raises(AssertionError, match="dtype"):
        audit.audit_episode(bad, row, protocol, actors)


def test_complete_order_refuses_duplicate_or_swapped_rows_without_queries(tiny):
    out, protocol, actors, batch, _ = tiny
    bad = deepcopy(batch)
    bad["rows"][0], bad["rows"][1] = bad["rows"][1], bad["rows"][0]
    with pytest.raises(AssertionError, match="execution order"):
        _read_all(bad, out, actors, protocol, dict(actual={}, inflight={}), lambda **kwargs: None)


def test_reader_failure_retains_ranking_before_history_validation(tiny):
    out, protocol, actors, batch, _ = tiny
    row = next(row for row in batch["rows"] if row["ego"] == "V" and row["kind"] == "evaluation")
    raw = load_raw(out / row["raw"]["path"])
    raw["history_descriptor"][0, 0] += 1.
    counts, inflight = {}, {}
    with pytest.raises(AssertionError, match="private ego history descriptor"):
        audit.audit_episode(raw, row, protocol, actors, counts=counts, inflight=inflight)
    assert inflight["id"] == row["id"] and inflight["tick"] == 0
    assert counts["scalar_states"] == 1
    paid = inflight["policy_agents"][0]
    assert paid["requests"] == paid["tracker_ingests"] == 1
    assert paid["trajectories"] == 27 and paid["model_ticks"] == 108
    assert all(member["requests"] == 0 for member in inflight["policy_agents"][1:])


def test_reader_failure_retains_frozen_forward_before_head_exception(tiny, monkeypatch):
    out, protocol, actors, batch, _ = tiny
    row = next(row for row in batch["rows"] if row["ego"] == "F0" and row["kind"] == "evaluation")
    raw = load_raw(out / row["raw"]["path"])
    def fail_head(*args, **kwargs):
        raise RuntimeError("injected focal failure")
    monkeypatch.setattr(reference, "focal_logits", fail_head)
    counts, inflight = {}, {}
    with pytest.raises(RuntimeError, match="injected focal failure"):
        audit.audit_episode(raw, row, protocol, actors, head_state=ResponseHead().state_dict(),
                            counts=counts, inflight=inflight)
    assert counts["scalar_states"] == 1 and inflight["tick"] == 0
    paid = inflight["policy_agents"][0]
    assert paid["requests"] == paid["neural_rows"] == paid["helper_calls"] == 1
    assert paid["head_rows"] == paid["sampled_draws"] == 0
    assert all(member["requests"] == 0 for member in inflight["policy_agents"][1:])


def test_production_refusals_and_failure_evidence(tmp_path):
    with pytest.raises(ValueError, match="admission"):
        run_batch(tmp_path / "untouched", "no", admission=None, parent_paths={})
    assert not (tmp_path / "untouched").exists()
    out = tmp_path / "invalid"
    out.mkdir()
    (out / "summary.json").write_text(json.dumps(dict(object=OBJECT, state="FAILED", scientific_execution=True)))
    with pytest.raises(AssertionError, match="production result"):
        read_result(out, tmp_path)
    saved = json.loads((out / "reading.json").read_text())
    assert saved["status"] == "FAILED" and saved["actual"] == dict(native_steps=0, optimizer_steps=0, refits=0)
    with pytest.raises(FileExistsError):
        read_result(out, tmp_path)
    with pytest.raises(ValueError, match="both exact"):
        load_parents({})
