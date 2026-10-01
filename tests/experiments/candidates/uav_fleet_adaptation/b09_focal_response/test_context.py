"""Synthetic visible rows only; no native environment or planning requests."""
import numpy as np
import pytest

from experiments.candidates.uav_fleet_adaptation.b09_focal_response.context import PeerHistory, pack_context


def row(peers=(), tick=0, own=(.5, .5, .5)):
    result = np.zeros(104, dtype=np.float32)
    result[:3] = own
    for i, xyz in enumerate(peers):
        result[63+4*i:67+4*i] = (*xyz, 1.)
    result[-1] = tick / 256
    return result


@pytest.fixture(scope="module", autouse=True)
def cost_report():
    original = PeerHistory.ingest
    counts = dict(tracker_ingest_attempts=0, tracker_ingests=0, pair_gates=0)
    def counted(self, *args, **kwargs):
        counts["tracker_ingest_attempts"] += 1
        before = self.counters["pair_gates"]
        result = original(self, *args, **kwargs)
        counts["tracker_ingests"] += 1
        counts["pair_gates"] += self.counters["pair_gates"] - before
        return result
    PeerHistory.ingest = counted
    yield
    PeerHistory.ingest = original
    print("B09 context check costs:", counts, "Student/head/critic/native/C requests=0")


def test_current_rank_motion_and_defensive_diagnostics():
    tracker = PeerHistory()
    first = tracker.ingest(row(((.1, 0, 0), (-.1, 0, 0))), 0)
    assert first["descriptor"].dtype == np.float32
    assert not first["descriptor"].any()
    answer = tracker.ingest(row(((-.09, .02, .1), (.12, -.01, -.1)), 1), 1)
    np.testing.assert_array_equal(answer["matches"], [1, 0, -1, -1])
    np.testing.assert_allclose(answer["descriptor"].reshape(4, 4)[:2],
                               [[10/30, 20/30, 10/30, 1], [20/30, -10/30, -10/30, 1]], atol=1e-6)
    np.testing.assert_array_equal(answer["gate_counts"], [1, 1, 0, 0])
    assert answer["counters"] == dict(ingests=2, adjacent_updates=1, pair_gates=4,
                                    matched_rows=2, moving_rows=2)
    answer["matches"][:] = 999
    answer["delta"][:] = 999
    answer["gate_counts"][:] = 999
    answer["counters"]["ingests"] = 999
    assert tracker.matches[0] == 1 and tracker.delta.max() < 21
    assert tracker.gate_counts[0] == 1 and tracker.counters["ingests"] == 2


def test_mutual_ambiguity_disappearance_and_reset():
    tracker = PeerHistory()
    tracker.ingest(row(((.1, 0, 0), (.11, 0, 0))), 0)
    ambiguous = tracker.ingest(row(((.105, 0, 0),), 1), 1)
    assert ambiguous["gate_counts"][0] == 2 and not ambiguous["descriptor"].any()
    reverse = tracker.ingest(row(((.1, 0, 0), (.11, 0, 0)), 2), 2)
    assert reverse["gate_counts"][:2].tolist() == [1, 1]
    assert not reverse["descriptor"].any()  # Shared previous row prevents either match.
    tracker.ingest(row(tick=3), 3)
    returned = tracker.ingest(row(((.1, 0, 0),), 4), 4)
    assert returned["matches"].tolist() == [-1]*4
    tracker.reset()
    assert not any(tracker.counters.values())
    assert tracker._previous_peers.shape == (0, 3)
    assert not tracker.ingest(row(((.1, 0, 0),)), 0)["descriptor"].any()


def test_absolute_coordinates_gate_roundoff_and_stationary_validity():
    tracker = PeerHistory()
    tracker.ingest(row(((0, 0, 0),)), 0)
    # Own movement plus relative peer movement: absolute x displacement30.0005,
    # tiny y displacement is zeroed, and x is clipped back to30.
    answer = tracker.ingest(row(((.0200005, .0000005, 0),), 1, own=(.51, .5, .5)), 1)
    np.testing.assert_array_equal(answer["delta"][0], [30., 0., 0.])
    assert answer["descriptor"].tolist()[:4] == [1., 0., 0., 1.]
    same = tracker.ingest(row(((.0200005, .0000005, 0),), 2, own=(.51, .5, .5)), 2)
    assert same["descriptor"].tolist()[:4] == [0., 0., 0., 1.]
    far = tracker.ingest(row(((.05001, .0000005, 0),), 3, own=(.51, .5, .5)), 3)
    assert not far["descriptor"].any()


@pytest.mark.parametrize("case", ["skip", "bool", "clock", "nan", "dtype", "shape", "too_many", "end"])
def test_bad_ingest_does_not_mutate_private_state(case):
    tracker = PeerHistory()
    value, tick = row(), 0
    if case == "skip": tick = 1
    elif case == "bool": tick = True
    elif case == "clock": value[-1] = .1
    elif case == "nan": value[0] = np.nan
    elif case == "dtype": value = value.astype(np.float64)
    elif case == "shape": value = value[:103]
    elif case == "too_many": value = row([(0, 0, 0)]*5)
    else: tick = 256
    with pytest.raises((ValueError, FloatingPointError)):
        tracker.ingest(value, tick)
    assert tracker._clock == -1 and not any(tracker.counters.values())


def test_packing_exact_coordinates_zeros_and_private_storage():
    f = np.linspace(-2, 3, 114, dtype=np.float32)
    h = np.linspace(0, 8, 128, dtype=np.float32)
    d = np.arange(16, dtype=np.float32)
    current, history = pack_context(f, h, 255), pack_context(f, h, 255, d)
    assert history.shape == (259,) and history.dtype == np.float32
    assert history[:114].tobytes() == f.tobytes()
    assert history[114:242].tobytes() == h.tobytes()
    assert history[242] == np.float32(255/256)
    assert not current[243:].any()
    assert history[243:].tobytes() == d.tobytes()
    f[:] = h[0] = d[0] = 99
    assert history[0] == -2 and history[114] == history[243] == 0
    with pytest.raises(ValueError): pack_context(f.astype(np.float64), h, 0)
    with pytest.raises(ValueError): pack_context(f, h, 0, np.zeros(15, dtype=np.float32))
    h[0] = np.inf
    with pytest.raises(FloatingPointError): pack_context(f, h, 0)
