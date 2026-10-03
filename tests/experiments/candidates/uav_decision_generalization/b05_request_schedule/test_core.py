"""Synthetic-only checks: no host, native/RF, training or scientific world."""
from dataclasses import FrozenInstanceError, replace
from itertools import permutations

import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b05_request_schedule import contract
from experiments.candidates.uav_decision_generalization.b05_request_schedule.features import (
    FEATURE_SLICES, candidate_features)
from experiments.candidates.uav_decision_generalization.b05_request_schedule.ordinary import (
    g_values, greedy_action)
from experiments.candidates.uav_decision_generalization.b05_request_schedule.task import (
    PublicState, QueueLedger, candidate_slots, initial_assignment, pack_command,
    pack_report, pack_reset, slot_positions, steer, unpack_command, unpack_report,
    unpack_reset, validate_slots)


G_WORK = []


@pytest.fixture(scope="module", autouse=True)
def billed_work():
    yield
    keys = ("queries", "candidate_values", "candidate_ticks", "cluster_recurrences",
            "kinematic_uav_steps", "future_arrival_cluster_additions", "radio_calls")
    print("\nsynthetic_G_work:", {k: sum(c[k] for c in G_WORK) for k in keys})


def query(state):
    result = g_values(state)
    G_WORK.append(result.counters)
    return result


def synthetic_users():
    centres = np.array([[2500, 2500], [500, 500], [4500, 500],
                        [4500, 4500], [500, 4500]], dtype=np.int32)
    return np.repeat(centres, 10, axis=0)


def state_at(tick=0, counts=(0, 0, 0, 0), progress=(0, 0, 0, 0), offset=0):
    users = synthetic_users()
    rates = np.array([6, 3, 2, 1], dtype=np.uint8)
    slots = np.arange(6, dtype=np.uint8)
    positions = slot_positions(users, slots) + np.array([offset, -offset, 0.0])
    return PublicState(123, tick, users, rates, positions, np.zeros(50, bool),
                       np.array(counts), np.array(progress), slots, ((0, 1), (2, 3), (4, 5)))


def test_public_is_copy_safe_and_validated():
    state = state_at(counts=(1, 0, 0, 0))
    original = state.positions.copy()
    copied = replace(state, positions=original)
    original[:] = 0
    np.testing.assert_array_equal(copied.positions, state.positions)
    with pytest.raises(ValueError):
        copied.positions.setflags(write=True)
    with pytest.raises(ValueError):
        copied.counts[0] = 0
    with pytest.raises(FrozenInstanceError):
        copied.tick = 20
    for changes in ({"progress": np.array([1, 0, 0, 0]), "counts": np.zeros(4, int)},
                    {"rate_codes": np.array([6, 3, 2, 2])},
                    {"active_slots": np.array([0, 1, 2, 3, 2, 3])},
                    {"pairs": ((0, 1), (2, 3), (4, 4))},
                    {"users": state.users.astype(float)},
                    {"positions": np.full((6, 3), np.nan)}, {"tick": True}):
        with pytest.raises(ValueError):
            replace(state, **changes)


def test_slots_initial_targets_and_lexicographic_assignment():
    users = synthetic_users()
    targets = slot_positions(users)
    np.testing.assert_allclose(targets[0], [2500-2000/3, 2500-2000/3, 100])
    positions = np.tile([2500.0, 2500.0, 100.0], (6, 1))
    before = positions.copy()
    slots, pairs = initial_assignment(users, np.array([1, 6, 3, 2]), positions)
    np.testing.assert_array_equal(slots, [2, 3, 4, 5, 6, 7])
    assert pairs == ((0, 1), (2, 3), (4, 5))
    np.testing.assert_array_equal(positions, before)
    positions = targets[[7, 4, 5, 2, 3, 6]] + np.array([20.0, -10.0, 30.0])
    slots, pairs = initial_assignment(users, np.array([1, 6, 3, 2]), positions)
    selected = [2, 3, 4, 5, 6, 7]
    scores = []
    for order in permutations(range(6)):
        distance = [float(np.linalg.norm(positions[u] - targets[s])) for u, s in zip(order, selected)]
        scores.append((sum(int(np.ceil(d/30)) for d in distance), sum(distance), order))
    chosen = min(scores)[2]
    assert tuple(u for pair in pairs for u in pair) == chosen
    assert tuple(slots[list(chosen)]) == tuple(selected)


def test_candidates_keep_legal_orientation_and_current_position():
    state = state_at()
    candidates = candidate_slots(state)
    np.testing.assert_array_equal(candidates[0], state.active_slots)
    for action in range(1, 4):
        validate_slots(candidates[action], state.pairs)
        pair = state.pairs[action-1]
        assert set(candidates[action, list(pair)]) == {6, 7}
        unmoved = [u for u in range(6) if u not in pair]
        np.testing.assert_array_equal(candidates[action, unmoved], state.active_slots[unmoved])
    # Reported destination positions reverse pair 0's orientation; activation
    # positions are deliberately unavailable to this pure mapping.
    positions = state.positions.copy()
    positions[:2] = slot_positions(state.users, np.array([7, 6]))
    moved = candidate_slots(replace(state, positions=positions))
    np.testing.assert_array_equal(moved[1, :2], [7, 6])
    positions[:2] = [2500.0, 2500.0, 100.0]
    tied = candidate_slots(replace(state, positions=positions, pairs=((1, 0), (2, 3), (4, 5))))
    np.testing.assert_array_equal(tied[1, :2], [6, 7])


def test_steer_exact_old_arithmetic_and_bounded_distance():
    from experiments.candidates.uav_decision_generalization.b03_joint_window.ordinary import steer as old
    positions = np.zeros((6, 3))
    targets = np.array([[0, 0, 0], [1, 0, 0], [30, 0, 0], [31, 0, 0],
                        [-10, 20, 40], [3000, -2000, 100]], dtype=float)
    action = steer(positions, targets)
    np.testing.assert_array_equal(action, old(positions, targets))
    assert np.all(np.linalg.norm(action, axis=1) <= 1.0)
    np.testing.assert_array_equal(30 * action[:3], targets[:3])


def test_payload_layout_roundtrip_and_padding():
    state = state_at(1180, (1, 2, 3, 4), (0, 5, 10, 19))
    state = replace(state, ack=np.arange(50) % 3 == 0)
    reset = pack_reset(state.users, state.rate_codes)
    assert len(reset) == 404
    assert reset[:4] == int(state.users[0, 0]).to_bytes(4, "little", signed=True)
    users, rates = unpack_reset(reset)
    np.testing.assert_array_equal(users, state.users)
    np.testing.assert_array_equal(rates, state.rate_codes)
    report = pack_report(state)
    assert len(report) == 171 and report[150] & 0b11111100 == 0
    restored = unpack_report(report, world=state.world, users=users, rate_codes=rates, pairs=state.pairs)
    for field in ("positions", "ack", "counts", "progress", "active_slots"):
        np.testing.assert_array_equal(getattr(state, field), getattr(restored, field))
    assert restored.tick == 1180
    malformed = bytearray(report)
    malformed[150] |= 4
    with pytest.raises(ValueError):
        unpack_report(malformed, world=123, users=users, rate_codes=rates, pairs=state.pairs)
    command = pack_command(candidate_slots(state)[1], state.pairs)
    assert len(command) == 6
    np.testing.assert_array_equal(unpack_command(command, state.pairs), candidate_slots(state)[1])
    for payload, fn in ((reset[:-1], unpack_reset), (command[:-1], lambda p: unpack_command(p, state.pairs))):
        with pytest.raises(ValueError):
            fn(payload)


def tick(ledger, t, bits=(False, False, False, False), qualified=(True, True, True, True)):
    cost = ledger.start_tick(t, np.array(bits, dtype=bool))
    return cost, ledger.finish_tick(t, np.array(qualified, dtype=bool))


def test_ledger_arrival_before_service_twentieth_completion_and_fifo():
    ledger = QueueLedger()
    for t in range(40):
        _, completions = tick(ledger, t, bits=(t in (0, 20), False, False, False))
        if t in (19, 39):
            assert len(completions) == 1
            assert completions[0].completion_tick == t+1
            assert completions[0].request.arrival_tick == t-19
            assert ledger.progress[0] == 0
        else:
            assert not completions
    assert [c.request.request_id for c in ledger.completions] == [0, 1]
    assert ledger.area_cost == ledger.total_cost == 40
    assert ledger.tick == 40


def test_ledger_interruption_ack_threshold_and_next_head_reset():
    ledger = QueueLedger()
    ack = np.zeros(50, bool)
    ack[10:17] = True
    ledger.start_tick(0, np.array([True, False, False, False]))
    ledger.finish_tick(0, ack)
    assert ledger.progress[0] == 0
    ack[17] = True
    for t in range(1, 10):
        ledger.start_tick(t, np.zeros(4, bool))
        ledger.finish_tick(t, ack)
    assert ledger.progress[0] == 9
    tick(ledger, 10, qualified=(False, True, True, True))
    assert ledger.progress[0] == 0
    for t in range(11, 31):
        tick(ledger, t, bits=(t == 20, False, False, False))
    assert ledger.counts[0] == 1 and ledger.progress[0] == 0
    assert ledger.completions[0].completion_tick == 31
    tick(ledger, 31)
    assert ledger.progress[0] == 1


def test_ledger_conservation_terminal_single_charge_and_no_overrun():
    ledger = QueueLedger()
    for t in range(1200):
        tick(ledger, t, bits=(t in (0, 20, 940), t == 940, False, False),
             qualified=(t < 30, False, False, False))
    completion_age = sum(c.completion_tick - c.request.arrival_tick for c in ledger.completions)
    unfinished_age = sum(1200-r.arrival_tick for q in ledger.unfinished for r in q)
    assert ledger.area_cost == completion_age + unfinished_age
    terminal = ledger.terminal_cost()
    assert terminal == 240*int(ledger.counts.sum())
    assert ledger.total_cost == ledger.area_cost + terminal
    assert ledger.terminal_charge == terminal
    with pytest.raises(ValueError):
        ledger.terminal_cost()
    with pytest.raises(ValueError):
        tick(ledger, 1200)


def test_ledger_rejects_invalid_order_and_arrival_without_mutation():
    ledger = QueueLedger()
    with pytest.raises(ValueError):
        ledger.finish_tick(0, np.zeros(4, bool))
    with pytest.raises(ValueError):
        ledger.start_tick(1, np.zeros(4, bool))
    ledger.start_tick(0, np.zeros(4, bool))
    with pytest.raises(ValueError):
        ledger.start_tick(0, np.ones(4, bool))
    ledger.finish_tick(0, np.zeros(4, bool))
    with pytest.raises(ValueError):
        ledger.start_tick(1, np.array([True, False, False, False]))
    assert ledger.area_cost == 0 and not ledger.arrivals
    ledger = QueueLedger.from_public(np.array([1, 2, 0, 0]), np.array([19, 4, 0, 0]), 940)
    assert not ledger.arrivals
    assert all(r.arrival_tick is None and r.request_id is None for q in ledger.unfinished for r in q)
    _, completed = tick(ledger, 940)
    assert completed[0].request.arrival_tick is None
    assert completed[0].completion_tick == 941
    with pytest.raises(ValueError):
        ledger.start_tick(941, np.ones(4, bool))


def scalar_reference(state):
    """Separately implemented scalar recurrence; no candidate G helper call."""
    outputs = []
    candidates = candidate_slots(state)
    targets = slot_positions(state.users)
    for candidate in candidates:
        positions = state.positions.copy()
        n = [int(x) for x in state.counts]
        r = [int(x) for x in state.progress]
        f = [0.0]*4
        cost = 0.0
        for offset in range(min(240, 1200-state.tick)):
            t = state.tick+offset
            assigned = state.active_slots if offset < 20 else candidate
            if t > state.tick and t <= 940 and t % 20 == 0:
                for c in range(4):
                    f[c] += float(state.rate_codes[c])/10
            cost += sum(n[c]+f[c] for c in range(4))
            for u in range(6):
                difference = targets[assigned[u]]-positions[u]
                length = float(np.sqrt(sum(float(v)*float(v) for v in difference)))
                for axis in range(3):
                    positions[u, axis] += difference[axis]*min(1.0, 30.0/max(length, 30.0))
            availability = [False]*4
            for pair in state.pairs:
                c = int(assigned[pair[0]]//2)
                availability[c] = all(np.sqrt(sum(float(v)*float(v) for v in positions[u]-targets[assigned[u]])) <= 1 for u in pair)
            for c in range(4):
                if not availability[c]:
                    r[c] = 0
                elif n[c]:
                    r[c] += 1
                    if r[c] == 20:
                        n[c] -= 1
                        r[c] = 0
                else:
                    r[c] = 0
                    f[c] -= min(f[c], .05)
        cost += 240*sum(n[c]+f[c] for c in range(4))
        outputs.append(cost)
    return np.array(outputs, dtype=np.float64)


@pytest.mark.parametrize("t,offset", [(0, 0), (20, 170), (920, 400), (940, 0), (1180, 31), (1199, 0)])
def test_g_scalar_recurrence_and_actual_counters(t, offset):
    state = state_at(t, (2, 1, 3, 2), (19, 4, 10, 0), offset)
    prediction = query(state)
    # Summation order differs; 1e-10 request-ticks is below float32 feature
    # precision and cannot conceal a head completion or 0.05 fluid-service tick.
    np.testing.assert_allclose(prediction.costs, scalar_reference(state), rtol=0, atol=1e-10)
    assert prediction.costs.dtype == np.float64
    assert prediction.counters["candidate_ticks"] == 4*min(240, 1200-t)
    assert prediction.counters["cluster_recurrences"] == 16*min(240, 1200-t)
    assert prediction.counters["radio_calls"] == 0


def test_g_known_completion_no_discount_tail_terminal_and_delay():
    state = state_at(1180, (1, 0, 0, 0), (19, 0, 0, 0))
    prediction = query(state)
    # First postmove tick completes the known head; all four first20 targets
    # are current. No future arrivals, fluid drain or terminal pending action.
    np.testing.assert_array_equal(prediction.costs, np.ones(4))
    assert prediction.counters["future_arrival_boundaries"] == 0
    state = state_at(1199, (0, 0, 0, 2), (0, 0, 0, 19))
    np.testing.assert_array_equal(query(state).costs, np.full(4, 482.0))
    assert greedy_action(np.array([10.0, 1.0, 1.0, 5.0])) == 1
    with pytest.raises(ValueError):
        g_values(state_at(1200))


def test_features_exact_order_dtypes_raw_preservation_without_clipping():
    state = state_at(940, (48, 2, 3, 4), (19, 0, 1, 2))
    state = replace(state, ack=np.arange(50) % 2 == 0)
    raw = np.array([0.0, 1.0, 1200.0, 1e9], dtype=np.float64)
    x, kept = candidate_features(state, raw)
    raw[:] = -1
    assert x.shape == (4, 303) and x.dtype == np.float32 and kept.dtype == np.float64
    np.testing.assert_array_equal(kept, [0.0, 1.0, 1200.0, 1e9])
    expected_common = {
        "users": state.users.ravel()/5000, "rates": state.probabilities,
        "positions": np.column_stack((state.positions[:, :2]/5000, (state.positions[:, 2]-50)/100)).ravel(),
        "ack": state.ack, "counts": state.counts/48, "progress": state.progress/20,
        "pairs": np.eye(3)[[0, 0, 1, 1, 2, 2]].ravel(),
        "active_slots": np.eye(8)[state.active_slots].ravel(),
        "time": [940/1200], "g_values": kept/1200,
    }
    for name, expected in expected_common.items():
        np.testing.assert_array_equal(x[:, FEATURE_SLICES[name]], np.tile(np.asarray(expected, dtype=np.float32), (4, 1)))
    np.testing.assert_array_equal(x[:, FEATURE_SLICES["action"]], np.eye(4, dtype=np.float32))
    np.testing.assert_array_equal(x[:, FEATURE_SLICES["candidate_slots"]], np.eye(8, dtype=np.float32)[candidate_slots(state)].reshape(4, 48))
    assert x[0, -1] > 800000


def test_literal_seeds_and_no_domain_draw():
    assert [worlds[0] for worlds in contract.TRAIN_WORLDS] == [109250000, 109251000, 109252000]
    assert all(len(worlds) == 512 for worlds in contract.TRAIN_WORLDS)
    assert contract.MAIN_WORLDS == tuple(range(109253000, 109253032))
    assert contract.AUDIT_WORLDS == (109253900, 109253901, 109253902)
    assert contract.TORCH_INIT_SEEDS == (109254101, 109254102, 109254103)
    assert contract.rng_domain("rates", 123) == (109259999, 20, 123)
    assert contract.rng_domain("actual_arrivals", 123) == (109259999, 21, 123)
    assert contract.rng_domain("R", 123, 59, 3) == (109259999, 30, 123, 59, 3)
    assert contract.rng_domain("exploration", 2) == (109259999, 10, 2)
    assert contract.rng_domain("replay", 2) == (109259999, 11, 2)
    for name, values in (("R", (123, 60, 0)), ("rates", (-1,)),
                         ("replay", (3,)), ("rates", (True,)), ("rates", ())):
        with pytest.raises(ValueError):
            contract.rng_domain(name, *values)
