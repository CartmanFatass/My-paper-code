"""C01 semantic checks on fixed fixtures; no research score is read from tests."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import torch

from experiments.candidates.skill_information_refresh.c01.host import (
    APPROACH, CROSSING, DONE, SHARED, BYPASS, CrossingHost, FRAME, LocalView, OBS_SIZE, PERIODS,
    Worlds, choose_route, gate, predecision_slot, project, simple_requests,
)
from experiments.candidates.skill_information_refresh.c01.learner import (
    Rollout, advantages, build_scheduler, collect, flat_parameters, update,
)
from experiments.candidates.skill_information_refresh.c01.study import Config, run_study


def fixture_worlds(batch=2, horizon=48):
    return Worlds.make(17, 4, range(batch), horizon)


def test_no_unsent_peer_input_and_fixed_feature_shape():
    host = CrossingHost(fixture_worlds())
    before = host.view().features()
    assert before.shape == (2, OBS_SIZE)
    host.distance[:, 1] = 0
    host.stage[:, 1] = CROSSING
    host.cross_left[:, 1] = 1
    np.testing.assert_array_equal(host.view().features(), before)
    assert not host.view().peer_valid.any()


def test_snapshot_is_copied_before_motion_and_delivered_next_tick():
    host = CrossingHost(fixture_worlds(batch=1))
    host.distance[0, 0] = 5
    host.step(np.array([True]))
    assert host.t == 1
    assert host.cache[0, 1, 1] == 5
    assert host.cache_time[0, 1] == 0
    host.distance[0, 0] = 1
    assert host.cache[0, 1, 1] == 5
    assert host.view().peer_valid[0]
    assert host.view().peer_age[0] == 1


@pytest.mark.parametrize("should_send", [True, False])
def test_exact_budget_fixed_clocks_and_pending_accounting(should_send):
    host = CrossingHost(fixture_worlds(batch=1))
    sends = []
    while host.t < host.horizon:
        before = host.metrics["packets"].copy()
        host.step(np.array([should_send]))
        sends.append(int((host.metrics["packets"] - before)[0]))
    assert host.metrics["packets"][0] == 12
    for start in range(0, 48, FRAME):
        assert sum(sends[start:start + FRAME:2]) == 1
        assert sum(sends[start + 1:start + FRAME:2]) == 1
    row = host.rows()[0]
    assert row["jobs_started"] == 48 // 12 + 48 // 16
    assert row["delivered"] + row["pending_at_end"] == row["packets"]
    assert row["bytes"] == 96
    assert row["timing_slot_bits"] == 48
    assert len(row["send_clock_phase"]) == 48


def test_controller_collision_and_priority_fixtures():
    host = CrossingHost(fixture_worlds(batch=1))
    host.distance.fill(0)
    reward = host.step(np.array([False]))
    assert reward[0] == 0
    assert host.metrics["conflicts"][0] == 1
    assert (host.stage == DONE).all()

    host = CrossingHost(fixture_worlds(batch=1))
    host.distance.fill(0)
    host.cache = host.payloads()[:, ::-1].copy()
    host.cache_time.fill(0)
    host.step(np.array([False]))
    assert host.stage[0, 0] == CROSSING
    assert host.stage[0, 1] == APPROACH
    assert host.metrics["conflicts"][0] == 0
    assert host.metrics["wait_ticks"][0] == 1


def test_projection_expiry_and_crossing_complete():
    packet = np.array([[APPROACH, 7, 0, 12, SHARED], [CROSSING, 0, 2, 4, SHARED]])
    projected, valid, age = project(packet, np.array([0, 0]), 2)
    assert projected[0, 1] == 6
    assert projected[1, 0] == DONE
    assert valid.all()
    assert (age == 2).all()
    assert not project(packet, np.array([0, 0]), 12)[1].any()


def test_predecision_accounts_for_delay_and_recipient_not_sender_clock():
    assert predecision_slot(8, 1) == 11  # Delivery exactly at recipient 0's tick-12 boundary.
    assert predecision_slot(8, 0) == 14  # Last sender-0 slot arriving before recipient 1's tick 16.
    assert predecision_slot(16, 1) == 23
    assert predecision_slot(0, 0) == 6


def test_event_baseline_can_hold_past_first_slot_on_lawful_history():
    # Robot 0 sent its near-gate snapshot at t=6, crossed at 6/7, and is DONE at t=8.
    # Robot 1's t=7 snapshot is DONE; robot 0's packet (crossing) changed, but neither
    # robot can act now, so a disabled/12 age rule retains the t=8 frame token.
    view = LocalView(t=8, horizon=48, sender=0,
        own=np.array([[DONE, 0, 0, 4, SHARED]]),
        last_sent=np.array([[APPROACH, 0, 0, 6, SHARED]]), last_sent_time=np.array([6]),
        peer=np.array([[DONE, 0, 0, 8, SHARED]]), peer_valid=np.array([True]), peer_age=np.array([1]),
        available=np.array([True]))
    assert simple_requests(view, "POLL")[0]
    assert not simple_requests(view, "AGE_CHANGE", 1, None)[0]
    assert not simple_requests(view, "AGE_CHANGE", 1, 12)[0]
    # A packet exactly eight ticks old shows the originally problematic age-law distinction.
    older = replace(view, last_sent_time=np.array([0]))
    assert simple_requests(older, "AGE_CHANGE", 1, 8)[0]
    assert not simple_requests(older, "AGE_CHANGE", 1, 12)[0]


def test_exogenous_worlds_do_not_depend_on_actor_requests():
    one, two = CrossingHost(fixture_worlds()), CrossingHost(fixture_worlds())
    for _ in range(12):
        one.step(np.ones(2, dtype=bool))
        two.step(np.zeros(2, dtype=bool))
    np.testing.assert_array_equal(one.worlds.jobs, two.worlds.jobs)
    np.testing.assert_array_equal(one.worlds.advances, two.worlds.advances)
    other = Worlds.make(17, 5, range(2), 48)
    assert not np.array_equal(one.worlds.advances, other.advances)


def test_fixed_skill_choice_uses_delivered_cache_and_affordability():
    peer = np.array([[APPROACH, 2, 0, 10, SHARED]])
    assert choose_route(np.array([2]), 12, peer, np.array([True]))[0] == BYPASS
    assert choose_route(np.array([2]), 12, peer, np.array([False]))[0] == SHARED
    peer[0, 4] = BYPASS
    assert choose_route(np.array([2]), 12, peer, np.array([True]))[0] == SHARED
    peer[:] = [APPROACH, 7, 0, 12, SHARED]
    assert choose_route(np.array([7]), 12, peer, np.array([True]))[0] == SHARED


def test_boundary_choice_depends_on_cache_not_current_unsent_peer():
    one, two = CrossingHost(fixture_worlds(batch=1)), CrossingHost(fixture_worlds(batch=1))
    for host in (one, two):
        host.t = 12
        own_distance = host.worlds.jobs[0, 12, 0]
        host.cache[0, 0] = [APPROACH, own_distance, 0, 5, SHARED]
        host.cache_time[0, 0] = 11
    two.stage[0, 1] = CROSSING
    two.route[0, 1] = BYPASS
    one._prepare_tick()
    two._prepare_tick()
    assert one.route[0, 0] == two.route[0, 0]
    assert one.metrics["route_choices_with_valid_peer"][0] == 1


def test_bypass_is_committed_four_tick_skill_and_never_collides():
    host = CrossingHost(fixture_worlds(batch=1))
    host.distance.fill(0)
    host.route[0] = [SHARED, BYPASS]
    fixed = host.route.copy()
    for tick in range(4):
        host.step(np.array([False]))
        np.testing.assert_array_equal(host.route, fixed)
        assert host.metrics["conflicts"][0] == 0
        if tick < 3:
            assert host.stage[0, 1] == CROSSING
    assert host.stage[0, 1] == DONE
    assert host.metrics["completed_jobs"][0] == 2


def test_packet_arrives_before_and_can_change_actual_boundary_skill_choice():
    worlds = fixture_worlds(batch=1)
    worlds.jobs[0, 12, 0] = 2
    refreshed, stale = CrossingHost(worlds), CrossingHost(worlds)
    for host in (refreshed, stale):
        host.t = 11
        host.stage[0] = [DONE, APPROACH]
        host.distance[0] = [0, 2]
    refreshed.step(np.array([True]))
    stale.step(np.array([False]))
    assert refreshed.t == stale.t == 12
    assert refreshed.cache_time[0, 0] == 11
    assert refreshed.route[0, 0] == BYPASS
    assert stale.route[0, 0] == SHARED


def test_later_packet_changes_feedback_without_changing_committed_skill():
    worlds = fixture_worlds(batch=1)
    worlds.advances[0, 4, 1] = True
    refreshed, stale = CrossingHost(worlds), CrossingHost(worlds)
    for host in (refreshed, stale):
        host.t = 4
        host.stage[0] = [CROSSING, APPROACH]
        host.distance[0] = [0, 1]
        host.cross_left[0] = [2, 0]
    refreshed.step(np.array([True]))
    stale.step(np.array([False]))
    assert refreshed.t == stale.t == 5
    refreshed.step(np.array([False]))
    stale.step(np.array([False]))
    assert refreshed.metrics["wait_ticks"][0] == 1
    assert refreshed.metrics["conflicts"][0] == 0
    assert stale.metrics["conflicts"][0] == 1
    assert (refreshed.route == stale.route).all()
    assert (refreshed.route == SHARED).all()


def test_gae_and_actor_mask_have_independent_meaning():
    torch.set_num_threads(1)
    model = build_scheduler(17)
    x = torch.randn(3, 2, OBS_SIZE, generator=torch.Generator().manual_seed(22))
    with torch.no_grad():
        logits, values = model(x)
    rollout = Rollout(x, torch.zeros(3, 2), -torch.nn.functional.softplus(logits),
        values, torch.ones(3, 2), torch.zeros(3, 2, dtype=torch.bool))
    adv, target = advantages(rollout, gamma=1, lam=1)
    np.testing.assert_allclose(target.numpy(), np.array([[3, 3], [2, 2], [1, 1]]), atol=1e-6)
    before = flat_parameters(model.actor)
    critic_before = flat_parameters(model.critic)
    records = update(model, torch.optim.Adam(model.parameters(), lr=3e-4), rollout, epochs=1)
    torch.testing.assert_close(flat_parameters(model.actor), before, rtol=0, atol=0)
    assert not torch.equal(flat_parameters(model.critic), critic_before)
    assert records[0]["actor_samples"] == 0


def test_stochastic_collection_has_actual_trainable_choices():
    torch.set_num_threads(1)
    model = build_scheduler(17)
    before = flat_parameters(model.actor)
    rows, rollout, _ = collect(CrossingHost(fixture_worlds()), model=model,
        rng=torch.Generator().manual_seed(123), stochastic=True)
    assert rollout.mask.any()
    records = update(model, torch.optim.Adam(model.parameters(), lr=3e-4), rollout, epochs=1)
    assert records[0]["transitions"] == 96
    assert not torch.equal(flat_parameters(model.actor), before)
    assert all(r["packets"] == 12 for r in rows)


def test_complete_small_fixture_preserves_counts_and_outputs(tmp_path):
    config = Config(seed=19, horizon=48, train_episodes=4, initial_episodes=2,
        selection_episodes=2, final_episodes=2, batch=2, epochs=1)
    summary = run_study(tmp_path / "run", "a" * 40, config)
    assert summary["status"] == "COMPLETE"
    counts = summary["counts"]
    assert counts["train_transitions"] == 192
    assert counts["initial_transitions"] == 96
    assert counts["selection_transitions"] == 9 * 2 * 48
    assert counts["eval_transitions"] == 4 * 2 * 48
    assert counts["optimizer_steps"] == 2
    assert counts["evaluation_optimizer_steps"] == 0
    assert counts["started_fits"] == 1
    assert summary["learner"]["actor_displacement"] > 0
    assert len(summary["selection"]) == 9
    assert len(summary["primary"]["per_world_difference"]) == 2
    assert json.loads((tmp_path / "run" / "summary.json").read_text())["launch_sha"] == "a" * 40
    with np.load(tmp_path / "run" / "final_trace_LEARNED.npz") as trace:
        assert trace["features"].shape == (2, 48, OBS_SIZE)
        assert trace["sent"].sum(axis=1).tolist() == [12, 12]
        assert trace["state"].shape == (2, 48, 2, 5)
        assert trace["delivered_cache"].shape == (2, 48, 2, 5)
    assert (tmp_path / "run" / "initial.pt").is_file()
    assert (tmp_path / "run" / "final.pt").is_file()
    with pytest.raises(FileExistsError):
        run_study(tmp_path / "run", "a" * 40, config)


def test_production_entry_refuses_without_admission_before_outputs(tmp_path):
    root = Path(__file__).resolve().parents[5]
    out = tmp_path / "refused"
    result = subprocess.run([sys.executable, str(root / "scripts" / "run_sir_c01.py"),
        "--out", str(out), "--launch-sha", "a" * 40], cwd=root,
        text=True, capture_output=True, check=False)
    assert result.returncode != 0
    assert "missing HMASD admission" in result.stderr
    assert not out.exists()


def test_partial_optimizer_failure_retains_actual_counts(tmp_path, monkeypatch):
    config = Config(seed=19, horizon=48, train_episodes=2, initial_episodes=2,
        selection_episodes=2, final_episodes=2, batch=2, epochs=2)
    original_step = torch.optim.Adam.step
    calls = 0

    def fail_second_step(optimizer, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fixture optimizer failure")
        return original_step(optimizer, *args, **kwargs)

    monkeypatch.setattr(torch.optim.Adam, "step", fail_second_step)
    with pytest.raises(RuntimeError, match="fixture optimizer failure"):
        run_study(tmp_path / "failed", "b" * 40, config)
    summary = json.loads((tmp_path / "failed" / "summary.json").read_text())
    assert summary["status"] == "TECHNICAL_FAILURE"
    assert summary["counts"]["optimizer_steps"] == 1
    assert summary["counts"]["train_transitions"] == 96
    assert summary["counts"]["eval_transitions"] == 0
    assert summary["learner"]["actor_displacement"] > 0
    assert len((tmp_path / "failed" / "updates.jsonl").read_text().splitlines()) == 1
